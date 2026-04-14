from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import geopandas as gpd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd
import rasterio
from dotenv import load_dotenv
from shapely.geometry import LineString, MultiPoint, Point
from shapely.ops import unary_union


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
OUTPUT_DIR = ROOT / "Week7_Output"
FIG_DIR = OUTPUT_DIR / "figures"
TABLE_DIR = OUTPUT_DIR / "tables"
DATA_DIR = OUTPUT_DIR / "data"


SPEED_DEFAULTS = {
    "motorway": 100,
    "motorway_link": 80,
    "trunk": 80,
    "trunk_link": 60,
    "primary": 60,
    "primary_link": 50,
    "secondary": 50,
    "secondary_link": 40,
    "tertiary": 40,
    "tertiary_link": 35,
    "residential": 30,
    "living_street": 15,
    "unclassified": 30,
    "service": 20,
}


def ensure_dirs() -> None:
    for path in (OUTPUT_DIR, FIG_DIR, TABLE_DIR, DATA_DIR):
        path.mkdir(parents=True, exist_ok=True)


def find_first_existing(candidates: Iterable[Path]) -> Path | None:
    for path in candidates:
        if path.exists():
            return path
    return None


def load_settings() -> Dict[str, object]:
    load_dotenv(ROOT / ".env", override=False)
    ensure_dirs()
    shelter_csv = find_first_existing(
        [
            PROJECT_ROOT / "0303" / "data" / "避難收容處所點位檔案v9_clean_updated.csv",
            ROOT / "避難收容處所點位檔案v9 (1).csv",
            PROJECT_ROOT / "AQI_analysis" / "data" / "shelters_cleaned.csv",
            PROJECT_ROOT / "0303" / "避難收容處所點位檔案v9.csv",
        ]
    )
    dislope_inventory = find_first_existing(
        [
            PROJECT_ROOT / "0331" / "outputs" / "dislope_shapefile" / "dislope_inventory.shp",
            PROJECT_ROOT / "0331" / "outputs" / "dislope_shapefile" / "archive" / "dislope_inventory_pre_enrich.shp",
        ]
    )
    raster_path = find_first_existing(
        [
            ROOT / "Week6_Lab" / "kriging_rainfall.tif",
            PROJECT_ROOT / "0331" / "Homework" / "kriging_rainfall_highres.tif",
            PROJECT_ROOT / "0324" / "Week6_Lab" / "kriging_rainfall.tif",
        ]
    )
    rainfall_json = find_first_existing(
        [
            ROOT / "Week6_Homework" / "fungwong_202511.json",
            PROJECT_ROOT / "0331" / "Homework" / "fungwong_202511.json",
            PROJECT_ROOT / "0324" / "Week6_Homework" / "fungwong_202511.json",
        ]
    )
    return {
        "place_name": os.getenv("WEEK7_PLACE_NAME", "Hualien City, Taiwan"),
        "network_type": os.getenv("WEEK7_NETWORK_TYPE", "drive"),
        "target_crs": os.getenv("WEEK7_TARGET_CRS", "EPSG:3826"),
        "graphml_path": ROOT / os.getenv("WEEK7_GRAPHML_PATH", "Week7_Output/data/hualien_network.graphml"),
        "raster_path": raster_path or ROOT / os.getenv("WEEK7_RASTER_PATH", "Week6_Lab/kriging_rainfall.tif"),
        "rainfall_json_path": rainfall_json or ROOT / os.getenv("WEEK7_RAINFALL_JSON", "Week6_Homework/fungwong_202511.json"),
        "shelter_csv_path": shelter_csv or ROOT / "避難收容處所點位檔案v9 (1).csv",
        "dislope_inventory_path": dislope_inventory,
        "road_break_cf": float(os.getenv("ROAD_BREAK_CF", "0.95")),
        "facility_count": int(os.getenv("WEEK7_FACILITY_COUNT", "5")),
    }


def load_shelter_data(shelter_csv_path: Path, target_county: str = "花蓮縣") -> gpd.GeoDataFrame:
    shelters_df = pd.read_csv(shelter_csv_path)
    county_shelters = shelters_df[
        shelters_df["縣市及鄉鎮市區"].fillna("").str.contains(target_county.replace("縣", ""))
    ].copy()
    gdf = gpd.GeoDataFrame(
        county_shelters,
        geometry=gpd.points_from_xy(county_shelters["經度"], county_shelters["緯度"]),
        crs="EPSG:4326",
    ).to_crs("EPSG:3826")
    return add_terrain_risk_assessment(gdf)


def add_terrain_risk_assessment(gdf_shelters: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf_shelters.copy()
    wgs = gdf.to_crs("EPSG:4326")
    lon = wgs.geometry.x
    lat = wgs.geometry.y

    west_factor = ((121.7 - lon).clip(lower=0)) / 0.8
    north_factor = ((lat - 23.3).clip(lower=0)) / 1.3
    local_variation = ((np.sin(lon * 15) + np.cos(lat * 12)) + 2) / 4

    gdf["mean_elevation"] = 25 + west_factor * 1500 + north_factor * 180 + local_variation * 80
    gdf["max_slope"] = 2 + west_factor * 28 + local_variation * 6

    def classify(row: pd.Series) -> str:
        if row["mean_elevation"] >= 700 or row["max_slope"] >= 22:
            return "HIGH"
        if row["mean_elevation"] >= 250 or row["max_slope"] >= 10:
            return "MEDIUM"
        return "LOW"

    gdf["terrain_risk"] = gdf.apply(classify, axis=1)
    gdf["shelter_id"] = [f"SH{i:03d}" for i in range(1, len(gdf) + 1)]
    gdf["capacity"] = pd.to_numeric(gdf["預計收容人數"], errors="coerce").fillna(0).astype(int)
    return gdf


def load_dislope_hualien(dislope_inventory_path: Path | None, target_crs: str) -> gpd.GeoDataFrame | None:
    if not dislope_inventory_path or not dislope_inventory_path.exists():
        return None
    gdf = gpd.read_file(dislope_inventory_path)
    mask = (
        gdf["SRC_CITY"].fillna("").astype(str).str.contains("花蓮", regex=False)
        | gdf["C_NAME"].fillna("").astype(str).str.contains("花蓮", regex=False)
    )
    subset = gdf.loc[mask].copy()
    if subset.empty:
        return None
    if subset.crs is None:
        subset = subset.set_crs("EPSG:3826")
    return subset.to_crs(target_crs)


def parse_speed_kph(maxspeed, highway) -> float:
    if isinstance(maxspeed, list) and maxspeed:
        values = [parse_speed_kph(item, highway) for item in maxspeed]
        values = [value for value in values if value > 0]
        if values:
            return float(np.mean(values))
    if isinstance(maxspeed, str):
        speed_text = maxspeed.lower().replace(";", "|").replace(",", "|")
        parts = [part.strip() for part in speed_text.split("|") if part.strip()]
        parsed = []
        for part in parts:
            digits = "".join(ch for ch in part if ch.isdigit() or ch == ".")
            if not digits:
                continue
            value = float(digits)
            if "mph" in part:
                value *= 1.60934
            parsed.append(value)
        if parsed:
            return float(np.mean(parsed))
    if isinstance(maxspeed, (int, float)) and maxspeed > 0:
        return float(maxspeed)

    highway_value = highway[0] if isinstance(highway, list) and highway else highway
    return float(SPEED_DEFAULTS.get(highway_value, 40))


def fetch_or_load_network(place_name: str, network_type: str, target_crs: str, graphml_path: Path):
    if graphml_path.exists():
        graph = ox.load_graphml(graphml_path)
        if str(graph.graph.get("crs")) != target_crs:
            graph = ox.project_graph(graph, to_crs=target_crs)
        return graph

    ox.settings.use_cache = True
    ox.settings.log_console = False
    graph = ox.graph_from_place(place_name, network_type=network_type, simplify=True)
    graph = ox.project_graph(graph, to_crs=target_crs)
    graphml_path.parent.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(graph, graphml_path)
    return graph


def annotate_travel_time(graph):
    for _, _, _, data in graph.edges(keys=True, data=True):
        length_m = float(data.get("length", 0.0))
        speed_kph = parse_speed_kph(data.get("maxspeed"), data.get("highway"))
        speed_mps = max(speed_kph / 3.6, 1.0)
        data["speed_kph"] = speed_kph
        data["travel_time"] = length_m / speed_mps if length_m > 0 else 0.0
    return graph


def multigraph_to_weighted_graph(graph, weight_attr: str) -> nx.Graph:
    simple = nx.Graph()
    for node, attrs in graph.nodes(data=True):
        simple.add_node(node, **attrs)
    for u, v, data in graph.edges(data=True):
        weight = float(data.get(weight_attr, data.get("length", 1.0)))
        if simple.has_edge(u, v):
            if weight < simple[u][v][weight_attr]:
                simple[u][v].update(data)
                simple[u][v][weight_attr] = weight
        else:
            simple.add_edge(u, v, **data)
            simple[u][v][weight_attr] = weight
    return simple


def get_edge_lines(graph) -> gpd.GeoDataFrame:
    nodes, edges = ox.graph_to_gdfs(graph, nodes=True, edges=True, fill_edge_geometry=True)
    if "geometry" not in edges.columns:
        edge_geoms = []
        for u, v, _ in edges.index:
            edge_geoms.append(
                LineString(
                    [
                        (graph.nodes[u]["x"], graph.nodes[u]["y"]),
                        (graph.nodes[v]["x"], graph.nodes[v]["y"]),
                    ]
                )
            )
        edges = edges.copy()
        edges["geometry"] = edge_geoms
    return edges


def sample_rainfall_to_edges(graph, raster_path: Path) -> gpd.GeoDataFrame:
    edges = get_edge_lines(graph).copy()
    with rasterio.open(raster_path) as src:
        if str(edges.crs) != str(src.crs):
            edges = edges.to_crs(src.crs)
        midpoints = edges.geometry.interpolate(0.5, normalized=True)
        coords = [(geom.x, geom.y) for geom in midpoints]
        samples = list(src.sample(coords))
        nodata = src.nodata
        rain_values = []
        for sample in samples:
            value = float(sample[0]) if len(sample) else np.nan
            if nodata is not None and np.isclose(value, nodata):
                value = np.nan
            if not np.isfinite(value):
                value = np.nan
            rain_values.append(value)
        fill_value = float(np.nanmedian(rain_values)) if np.isfinite(np.nanmedian(rain_values)) else 0.0
        edges["rain_mm"] = np.where(np.isfinite(rain_values), rain_values, fill_value)
        if str(edges.crs) != str(graph.graph["crs"]):
            edges = edges.to_crs(graph.graph["crs"])
    return edges[["rain_mm", "geometry"]]


def load_rainfall_stations_gdf(rainfall_json_path: Path) -> gpd.GeoDataFrame:
    raw = json.loads(rainfall_json_path.read_text(encoding="utf-8"))
    stations = raw.get("records", {}).get("Station", [])
    parsed = []
    for station in stations:
        coord = None
        for item in station.get("GeoInfo", {}).get("Coordinates", []):
            if item.get("CoordinateName") == "WGS84":
                coord = item
                break
            if coord is None and "StationLatitude" in item and "StationLongitude" in item:
                coord = item
        if coord is None:
            continue

        rainfall = station.get("RainfallElement", {})
        value = rainfall.get("Past1hr", {}).get("Precipitation", 0)
        value_24 = rainfall.get("Past24hr", {}).get("Precipitation", 0)
        try:
            rain_1hr = float(value)
        except (TypeError, ValueError):
            rain_1hr = 0.0
        try:
            rain_24hr = float(value_24)
        except (TypeError, ValueError):
            rain_24hr = 0.0
        if rain_1hr == -998:
            rain_1hr = 0.0
        if rain_24hr == -998:
            rain_24hr = 0.0
        rain_effective = max(rain_1hr, rain_24hr * 0.5)

        parsed.append(
            {
                "station_name": station.get("StationName", "unknown"),
                "station_id": station.get("StationID") or station.get("StationId"),
                "rain_1hr": rain_1hr,
                "rain_24hr": rain_24hr,
                "rain_effective": rain_effective,
                "lat": coord.get("StationLatitude"),
                "lon": coord.get("StationLongitude"),
            }
        )

    gdf = gpd.GeoDataFrame(
        parsed,
        geometry=gpd.points_from_xy(
            [row["lon"] for row in parsed],
            [row["lat"] for row in parsed],
        ),
        crs="EPSG:4326",
    )
    return gdf.to_crs("EPSG:3826")


def sample_station_rainfall_to_edges(graph, rainfall_json_path: Path) -> gpd.GeoDataFrame:
    edges = get_edge_lines(graph).copy()
    edges["geometry"] = edges.geometry.interpolate(0.5, normalized=True)
    edges = edges.set_geometry("geometry")

    stations = load_rainfall_stations_gdf(rainfall_json_path)
    if str(stations.crs) != str(edges.crs):
        stations = stations.to_crs(edges.crs)

    nodes, _ = ox.graph_to_gdfs(graph, nodes=True, edges=True)
    hull = nodes.geometry.unary_union.convex_hull.buffer(20_000)
    stations = stations[stations.geometry.within(hull)].copy()
    if stations.empty:
        stations = load_rainfall_stations_gdf(rainfall_json_path).to_crs(edges.crs)

    joined = gpd.sjoin_nearest(
        edges,
        stations[["station_name", "rain_1hr", "rain_24hr", "rain_effective", "geometry"]],
        how="left",
        distance_col="station_dist_m",
    )
    joined["rain_mm"] = joined["rain_effective"].fillna(0.0)
    return joined[["rain_mm", "geometry"]]


def rain_to_congestion(rain_mm: float) -> float:
    if rain_mm < 10:
        return 0.0
    if rain_mm < 40:
        return 0.15
    if rain_mm < 80:
        return 0.35
    if rain_mm < 120:
        return 0.65
    return 0.98


def apply_dynamic_weights(graph, edge_rain: gpd.GeoDataFrame, road_break_cf: float):
    dynamic_graph = graph.copy()
    break_graph = graph.copy()
    rain_lookup = edge_rain["rain_mm"].to_dict()

    for u, v, key, data in dynamic_graph.edges(keys=True, data=True):
        rain_mm = float(rain_lookup.get((u, v, key), 0.0))
        cf = rain_to_congestion(rain_mm)
        base_time = float(data.get("travel_time", 0.0))
        data["rain_mm"] = rain_mm
        data["congestion_factor"] = cf
        data["travel_time_adj"] = base_time / max(1.0 - cf, 0.05)

    to_remove: List[Tuple[int, int, int]] = []
    for u, v, key, data in break_graph.edges(keys=True, data=True):
        rain_mm = float(rain_lookup.get((u, v, key), 0.0))
        cf = rain_to_congestion(rain_mm)
        base_time = float(data.get("travel_time", 0.0))
        data["rain_mm"] = rain_mm
        data["congestion_factor"] = cf
        data["travel_time_adj"] = base_time / max(1.0 - cf, 0.05)
        if cf >= road_break_cf:
            to_remove.append((u, v, key))
    break_graph.remove_edges_from(to_remove)
    return dynamic_graph, break_graph


def _capacity_column(gdf: gpd.GeoDataFrame) -> pd.Series:
    return pd.to_numeric(gdf["預計收容人數"], errors="coerce").fillna(0)


def select_facilities(shelters: gpd.GeoDataFrame, graph, facility_count: int) -> gpd.GeoDataFrame:
    nodes, _ = ox.graph_to_gdfs(graph, nodes=True, edges=True)
    network_hull = nodes.geometry.unary_union.convex_hull.buffer(1500)
    candidates = shelters[shelters.geometry.within(network_hull)].copy()
    if len(candidates) < facility_count:
        candidates = shelters.copy()

    risk_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
    candidates["capacity"] = _capacity_column(candidates)
    candidates["terrain_rank"] = candidates["terrain_risk"].map(risk_order).fillna(0)
    candidates["nearest_node"] = ox.distance.nearest_nodes(
        graph,
        X=candidates.geometry.x.to_list(),
        Y=candidates.geometry.y.to_list(),
    )
    chosen = (
        candidates.sort_values(["capacity", "terrain_rank"], ascending=[False, False])
        .drop_duplicates(subset="nearest_node")
        .head(facility_count)
        .copy()
    )
    chosen["facility_name"] = chosen["避難收容處所名稱"]
    return chosen


def isochrone_polygon(graph, source_node: int, weight_attr: str, time_seconds: float):
    route_lengths = nx.single_source_dijkstra_path_length(graph, source_node, cutoff=time_seconds, weight=weight_attr)
    reachable_nodes = list(route_lengths.keys())
    node_points = [Point(graph.nodes[node]["x"], graph.nodes[node]["y"]) for node in reachable_nodes]
    if not node_points:
        return [], None, 0.0

    subgraph = graph.subgraph(reachable_nodes)
    line_buffers = []
    for u, v, data in subgraph.edges(data=True):
        geometry = data.get("geometry")
        if geometry is None:
            geometry = LineString(
                [(graph.nodes[u]["x"], graph.nodes[u]["y"]), (graph.nodes[v]["x"], graph.nodes[v]["y"])]
            )
        line_buffers.append(geometry.buffer(35))
    node_buffer = MultiPoint(node_points).buffer(120)
    merged = unary_union(line_buffers + [node_buffer]) if line_buffers else node_buffer
    area_km2 = merged.area / 1_000_000
    return reachable_nodes, merged, area_km2


def build_accessibility_table(
    graph_normal,
    graph_disaster,
    facilities: gpd.GeoDataFrame,
) -> pd.DataFrame:
    records = []
    largest_component = set(max(nx.connected_components(graph_disaster), key=len))

    for _, facility in facilities.iterrows():
        node_id = int(facility["nearest_node"])
        before_5 = isochrone_polygon(graph_normal, node_id, "travel_time", 300)
        after_5 = isochrone_polygon(graph_disaster, node_id, "travel_time_adj", 300)
        before_10 = isochrone_polygon(graph_normal, node_id, "travel_time", 600)
        after_10 = isochrone_polygon(graph_disaster, node_id, "travel_time_adj", 600)

        area_before_5 = before_5[2]
        area_after_5 = after_5[2]
        area_before_10 = before_10[2]
        area_after_10 = after_10[2]

        shrink_5 = 0 if area_before_5 == 0 else 1 - (area_after_5 / area_before_5)
        shrink_10 = 0 if area_before_10 == 0 else 1 - (area_after_10 / area_before_10)
        isolated = node_id not in largest_component or area_after_10 < 0.05

        records.append(
            {
                "facility_name": facility["facility_name"],
                "shelter_id": facility["shelter_id"],
                "nearest_node": node_id,
                "terrain_risk": facility["terrain_risk"],
                "capacity": int(facility["capacity"]),
                "pre_5min_km2": round(area_before_5, 3),
                "post_5min_km2": round(area_after_5, 3),
                "shrinkage_5_pct": round(shrink_5 * 100, 1),
                "pre_10min_km2": round(area_before_10, 3),
                "post_10min_km2": round(area_after_10, 3),
                "shrinkage_10_pct": round(shrink_10 * 100, 1),
                "isolated": isolated,
                "before_5_polygon": before_5[1],
                "after_5_polygon": after_5[1],
                "before_10_polygon": before_10[1],
                "after_10_polygon": after_10[1],
            }
        )

    return pd.DataFrame(records)


def bottleneck_table(graph, shelters: gpd.GeoDataFrame, hazard_gdf: gpd.GeoDataFrame | None = None, top_n: int = 5) -> gpd.GeoDataFrame:
    weighted = multigraph_to_weighted_graph(graph, "length")
    centrality = nx.betweenness_centrality(weighted, weight="length", normalized=True)
    top_nodes = sorted(centrality.items(), key=lambda item: item[1], reverse=True)[:top_n]
    gdf = gpd.GeoDataFrame(
        [
            {
                "node_id": node_id,
                "centrality": cent,
                "geometry": Point(graph.nodes[node_id]["x"], graph.nodes[node_id]["y"]),
            }
            for node_id, cent in top_nodes
        ],
        crs=graph.graph["crs"],
    )
    if hazard_gdf is not None and not hazard_gdf.empty:
        hazard = hazard_gdf[["CODE", "SLOPE_ANG", "TRAFFIC", "PROT_TARG", "geometry"]].copy()
        joined = gpd.sjoin_nearest(gdf, hazard, how="left", distance_col="nearest_hazard_m")
        joined["terrain_risk"] = np.where(
            joined["nearest_hazard_m"] <= 300, "HIGH",
            np.where(joined["nearest_hazard_m"] <= 800, "MEDIUM", "LOW")
        )
        joined["mean_elevation"] = np.nan
        joined["max_slope"] = pd.to_numeric(joined["SLOPE_ANG"], errors="coerce")
        return joined.sort_values("centrality", ascending=False).reset_index(drop=True)

    shelters_sample = shelters[["shelter_id", "terrain_risk", "mean_elevation", "max_slope", "geometry"]].copy()
    joined = gpd.sjoin_nearest(gdf, shelters_sample, how="left", distance_col="nearest_shelter_m")
    return joined.sort_values("centrality", ascending=False).reset_index(drop=True)


def plot_bottlenecks(graph, bottlenecks: gpd.GeoDataFrame, output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 12))
    ox.plot_graph(
        graph,
        ax=ax,
        node_size=0,
        edge_color="#a8b3c2",
        edge_linewidth=0.6,
        bgcolor="white",
        show=False,
        close=False,
    )

    color_map = {"LOW": "#2ca25f", "MEDIUM": "#fdae6b", "HIGH": "#de2d26"}
    for _, row in bottlenecks.iterrows():
        ax.scatter(
            row.geometry.x,
            row.geometry.y,
            s=220,
            color=color_map.get(row["terrain_risk"], "#3182bd"),
            edgecolors="black",
            marker="*",
            zorder=5,
        )
        ax.text(row.geometry.x + 60, row.geometry.y + 60, f"{int(row['node_id'])}", fontsize=9)

    ax.set_title("Top 5 Bottleneck Nodes with Terrain Risk Proxy", fontsize=14)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_isochrones(graph, table: pd.DataFrame, output_path: Path) -> None:
    row = table.iloc[0]
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    configs = [
        ("Before Disaster", row["before_10_polygon"], row["before_5_polygon"], "#2b8cbe", axes[0]),
        ("After Disaster", row["after_10_polygon"], row["after_5_polygon"], "#de2d26", axes[1]),
    ]

    for title, poly10, poly5, color, ax in configs:
        ox.plot_graph(
            graph,
            ax=ax,
            node_size=0,
            edge_color="#d0d7de",
            edge_linewidth=0.5,
            bgcolor="white",
            show=False,
            close=False,
        )
        if poly10 is not None:
            gpd.GeoSeries([poly10], crs=graph.graph["crs"]).plot(ax=ax, color=color, alpha=0.22, edgecolor=color)
        if poly5 is not None:
            gpd.GeoSeries([poly5], crs=graph.graph["crs"]).plot(ax=ax, color=color, alpha=0.45, edgecolor=color)
        ax.set_title(f"{row['facility_name']} - {title}", fontsize=13)

    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def save_supporting_outputs(
    bottlenecks: gpd.GeoDataFrame,
    accessibility: pd.DataFrame,
    prompt_text: str,
) -> None:
    bottlenecks.drop(columns="geometry").to_csv(TABLE_DIR / "top5_bottlenecks.csv", index=False)

    accessibility_out = accessibility.drop(
        columns=["before_5_polygon", "after_5_polygon", "before_10_polygon", "after_10_polygon"]
    )
    accessibility_out.to_csv(TABLE_DIR / "accessibility_impact_table.csv", index=False)
    (OUTPUT_DIR / "ai_strategy_prompt.txt").write_text(prompt_text, encoding="utf-8")


def load_rainfall_station_summary(rainfall_json_path: Path) -> pd.DataFrame:
    stations = load_rainfall_stations_gdf(rainfall_json_path).to_crs("EPSG:4326")
    stations["lon"] = stations.geometry.x
    stations["lat"] = stations.geometry.y
    return pd.DataFrame(stations.drop(columns="geometry"))


def build_ai_prompt(bottlenecks: gpd.GeoDataFrame, accessibility: pd.DataFrame) -> str:
    dist_col = "nearest_hazard_m" if "nearest_hazard_m" in bottlenecks.columns else "nearest_shelter_m"
    top5_cols = ["node_id", "centrality", "terrain_risk"]
    if dist_col in bottlenecks.columns:
        top5_cols.append(dist_col)
    top5_info = bottlenecks[top5_cols].to_dict("records")
    isolated = accessibility.loc[accessibility["isolated"], "facility_name"].tolist()
    table = accessibility[
        [
            "facility_name",
            "terrain_risk",
            "pre_5min_km2",
            "post_5min_km2",
            "shrinkage_5_pct",
            "pre_10min_km2",
            "post_10min_km2",
            "shrinkage_10_pct",
            "isolated",
        ]
    ].to_string(index=False)
    return f"""You are a transportation advisor at Hualien County Disaster Prevention Command Center.
Top 5 Bottleneck Nodes: {top5_info}
Accessibility Impact Table:
{table}
Isolated Facilities: {isolated}

Please provide:
1. Priority road segments to clear with reasons
2. Alternative rescue methods for isolated areas
3. Resource allocation recommendations
"""


def run_week7_analysis() -> Dict[str, object]:
    settings = load_settings()
    shelters = load_shelter_data(settings["shelter_csv_path"])
    dislope_hualien = load_dislope_hualien(settings["dislope_inventory_path"], settings["target_crs"])
    graph = fetch_or_load_network(
        place_name=settings["place_name"],
        network_type=settings["network_type"],
        target_crs=settings["target_crs"],
        graphml_path=settings["graphml_path"],
    )
    graph = annotate_travel_time(graph)

    bottlenecks = bottleneck_table(graph, shelters, hazard_gdf=dislope_hualien)
    edge_rain = sample_rainfall_to_edges(graph, settings["raster_path"])
    if edge_rain["rain_mm"].median() < 5:
        edge_rain = sample_station_rainfall_to_edges(graph, settings["rainfall_json_path"])
    graph_dyn, graph_break = apply_dynamic_weights(graph, edge_rain, settings["road_break_cf"])

    graph_normal_simple = multigraph_to_weighted_graph(graph_dyn, "travel_time")
    graph_disaster_simple = multigraph_to_weighted_graph(graph_break, "travel_time_adj")

    facilities = select_facilities(shelters, graph, settings["facility_count"])
    accessibility = build_accessibility_table(graph_normal_simple, graph_disaster_simple, facilities)

    plot_bottlenecks(graph, bottlenecks, FIG_DIR / "top5_bottlenecks.png")
    plot_isochrones(graph, accessibility, FIG_DIR / "isochrone_before_after.png")

    prompt_text = build_ai_prompt(bottlenecks, accessibility)
    save_supporting_outputs(bottlenecks, accessibility, prompt_text)

    return {
        "settings": settings,
        "shelters": shelters,
        "graph": graph,
        "bottlenecks": bottlenecks,
        "facilities": facilities,
        "accessibility": accessibility,
        "edge_rain": edge_rain,
        "ai_prompt": prompt_text,
        "rainfall_stations": load_rainfall_station_summary(settings["rainfall_json_path"]),
        "dislope_hualien": dislope_hualien,
    }
