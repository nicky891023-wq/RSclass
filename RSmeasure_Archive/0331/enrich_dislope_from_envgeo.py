from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd


TARGET_PATH = Path("outputs/dislope_shapefile/dislope_inventory.shp")
SOURCE_DIR = Path("outputs/dislope_shapefile/05_環境地質基本圖")
ARCHIVE_DIR = Path("outputs/dislope_shapefile/archive")
METADATA_PATH = Path("outputs/dislope_shapefile/enrich_metadata.json")

CITY_FOLDER_MAP = {
    "臺北市": "臺北市",
    "新北市": "新北市",
    "桃園市": "桃園市",
    "臺中市": "台中市",
    "臺南市": "台南市",
    "高雄市": "高雄市",
    "基隆市": "基隆市",
    "新竹縣市": "新竹縣市",
    "苗栗縣": "苗栗縣",
    "南投縣": "南投縣",
    "雲林縣": "雲林縣",
    "嘉義縣市": "嘉義縣市",
    "屏東縣": "屏東縣",
    "宜蘭縣": "宜蘭縣",
    "花蓮縣": "花蓮縣",
    "臺東縣": "台東縣",
}

SIDECAR_SUFFIXES = [".shp", ".shx", ".dbf", ".prj", ".cpg", ".geojson"]


def collect_source_paths() -> dict[str, Path]:
    source_paths: dict[str, Path] = {}
    for shp in SOURCE_DIR.rglob("*.shp"):
        if "順向坡" in shp.name:
            source_paths[shp.name] = shp
    return source_paths


def get_source_path(source_paths: dict[str, Path], folder_name: str) -> Path:
    for name, path in source_paths.items():
        if folder_name in name:
            return path
    raise FileNotFoundError(f"Cannot find source shapefile for {folder_name}")


def choose_best_within_match(
    target_city: gpd.GeoDataFrame, source_city: gpd.GeoDataFrame
) -> pd.DataFrame:
    rep = target_city[["TID", "geometry"]].copy()
    rep["geometry"] = rep.representative_point()
    joined = gpd.sjoin(
        rep,
        source_city[["SID", "geometry"]],
        how="left",
        predicate="within",
    ).dropna(subset=["SID"])
    if joined.empty:
        return pd.DataFrame(columns=["TID", "SID", "MATCH_MTH", "MATCH_DST"])

    joined["SID"] = joined["SID"].astype(int)
    target_geom = target_city.set_index("TID").geometry
    source_geom = source_city.set_index("SID").geometry
    joined["OVERLAP"] = [
        target_geom.loc[tid].intersection(source_geom.loc[sid]).area
        for tid, sid in zip(joined["TID"], joined["SID"])
    ]
    best = (
        joined.sort_values(["TID", "OVERLAP"], ascending=[True, False])
        .drop_duplicates("TID")
        .loc[:, ["TID", "SID"]]
    )
    best["MATCH_MTH"] = "within"
    best["MATCH_DST"] = 0.0
    return best


def choose_best_intersects_match(
    target_city: gpd.GeoDataFrame,
    source_city: gpd.GeoDataFrame,
    matched_tids: set[int],
) -> pd.DataFrame:
    remaining = target_city[~target_city["TID"].isin(matched_tids)][["TID", "geometry"]].copy()
    if remaining.empty:
        return pd.DataFrame(columns=["TID", "SID", "MATCH_MTH", "MATCH_DST"])

    joined = gpd.sjoin(
        remaining,
        source_city[["SID", "geometry"]],
        how="left",
        predicate="intersects",
    ).dropna(subset=["SID"])
    if joined.empty:
        return pd.DataFrame(columns=["TID", "SID", "MATCH_MTH", "MATCH_DST"])

    joined["SID"] = joined["SID"].astype(int)
    target_geom = target_city.set_index("TID").geometry
    source_geom = source_city.set_index("SID").geometry
    joined["OVERLAP"] = [
        target_geom.loc[tid].intersection(source_geom.loc[sid]).area
        for tid, sid in zip(joined["TID"], joined["SID"])
    ]
    joined = joined[joined["OVERLAP"] > 0].copy()
    if joined.empty:
        return pd.DataFrame(columns=["TID", "SID", "MATCH_MTH", "MATCH_DST"])

    best = (
        joined.sort_values(["TID", "OVERLAP"], ascending=[True, False])
        .drop_duplicates("TID")
        .loc[:, ["TID", "SID"]]
    )
    best["MATCH_MTH"] = "intersect"
    best["MATCH_DST"] = 0.0
    return best


def choose_best_nearest_match(
    target_city: gpd.GeoDataFrame,
    source_city: gpd.GeoDataFrame,
    matched_tids: set[int],
    max_distance: float = 100.0,
) -> pd.DataFrame:
    remaining = target_city[~target_city["TID"].isin(matched_tids)][["TID", "geometry"]].copy()
    if remaining.empty:
        return pd.DataFrame(columns=["TID", "SID", "MATCH_MTH", "MATCH_DST"])

    rep = remaining.copy()
    rep["geometry"] = rep.representative_point()
    joined = gpd.sjoin_nearest(
        rep,
        source_city[["SID", "geometry"]],
        how="left",
        distance_col="MATCH_DST",
    ).dropna(subset=["SID"])
    if joined.empty:
        return pd.DataFrame(columns=["TID", "SID", "MATCH_MTH", "MATCH_DST"])

    joined["SID"] = joined["SID"].astype(int)
    joined = joined[joined["MATCH_DST"] <= max_distance].copy()
    if joined.empty:
        return pd.DataFrame(columns=["TID", "SID", "MATCH_MTH", "MATCH_DST"])

    best = (
        joined.sort_values(["TID", "MATCH_DST"], ascending=[True, True])
        .drop_duplicates("TID")
        .loc[:, ["TID", "SID", "MATCH_DST"]]
    )
    best["MATCH_MTH"] = "near100m"
    return best


def archive_current_outputs() -> None:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    for suffix in SIDECAR_SUFFIXES:
        src = TARGET_PATH.with_suffix(suffix)
        if src.exists():
            dst = ARCHIVE_DIR / f"dislope_inventory_pre_enrich{suffix}"
            if dst.exists():
                dst.unlink()
            src.replace(dst)


def main() -> None:
    target = gpd.read_file(TARGET_PATH)
    target["TID"] = range(len(target))
    target["MATCH_MTH"] = None
    target["MATCH_DST"] = None

    source_paths = collect_source_paths()
    if not source_paths:
        raise FileNotFoundError("No source dislope shapefiles found in 05_環境地質基本圖")

    sample_source = gpd.read_file(next(iter(source_paths.values()))).to_crs(target.crs)
    source_fields = [col for col in sample_source.columns if col != "geometry"]
    new_source_fields = [col for col in source_fields if col not in target.columns]
    for col in new_source_fields:
        target[col] = None

    city_stats: list[dict[str, int | str]] = []

    for city, folder in CITY_FOLDER_MAP.items():
        source_path = get_source_path(source_paths, folder)
        source_city = gpd.read_file(source_path).to_crs(target.crs).reset_index(drop=True)
        source_city["SID"] = range(len(source_city))

        target_mask = target["SRC_CITY"] == city
        target_city = target[target_mask].copy().reset_index(drop=True)

        match_within = choose_best_within_match(target_city, source_city)
        matched_tids = set(match_within["TID"].tolist())

        match_intersects = choose_best_intersects_match(target_city, source_city, matched_tids)
        matched_tids |= set(match_intersects["TID"].tolist())

        match_nearest = choose_best_nearest_match(target_city, source_city, matched_tids)

        city_matches = pd.concat(
            [match_within, match_intersects, match_nearest],
            ignore_index=True,
        )

        if not city_matches.empty:
            source_attrs = source_city.drop(columns="geometry").copy()
            merged = city_matches.merge(source_attrs, on="SID", how="left")
            merged = merged.set_index("TID")
            for tid, row in merged.iterrows():
                for col in new_source_fields:
                    target.loc[target["TID"] == tid, col] = row[col]
                if pd.isna(target.loc[target["TID"] == tid, "AP_DATE"]).all():
                    target.loc[target["TID"] == tid, "AP_DATE"] = row["AP_DATE"]
                target.loc[target["TID"] == tid, "MATCH_MTH"] = row["MATCH_MTH"]
                target.loc[target["TID"] == tid, "MATCH_DST"] = row["MATCH_DST"]

        city_stats.append(
            {
                "city": city,
                "target_features": int(len(target_city)),
                "source_features": int(len(source_city)),
                "matched_within": int(len(match_within)),
                "matched_intersects": int(len(match_intersects)),
                "matched_near100m": int(len(match_nearest)),
                "unmatched": int(len(target_city) - len(city_matches)),
            }
        )
        print(
            city,
            "within",
            len(match_within),
            "intersects",
            len(match_intersects),
            "near100m",
            len(match_nearest),
            "unmatched",
            len(target_city) - len(city_matches),
        )

    archive_current_outputs()

    target = target.drop(columns="TID")
    target.to_file(TARGET_PATH, driver="ESRI Shapefile", encoding="UTF-8")
    target.to_file(TARGET_PATH.with_suffix(".geojson"), driver="GeoJSON")

    metadata = {
        "target_path": str(TARGET_PATH),
        "source_dir": str(SOURCE_DIR),
        "total_features": int(len(target)),
        "matched_total": int(target["MATCH_MTH"].notna().sum()),
        "unmatched_total": int(target["MATCH_MTH"].isna().sum()),
        "match_methods": target["MATCH_MTH"].fillna("unmatched").value_counts().to_dict(),
        "city_stats": city_stats,
        "new_fields_added": new_source_fields + ["MATCH_MTH", "MATCH_DST"],
    }
    METADATA_PATH.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Matched total:", metadata["matched_total"])
    print("Unmatched total:", metadata["unmatched_total"])
    print("Output:", TARGET_PATH)


if __name__ == "__main__":
    main()
