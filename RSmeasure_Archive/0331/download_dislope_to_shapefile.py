from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import requests


API_URL = "https://landslide.geologycloud.tw/map/api/opendata/lsdata/dislope"
OUTPUT_DIR = Path("outputs") / "dislope_shapefile"
SHAPEFILE_PATH = OUTPUT_DIR / "dislope_inventory_3826_area_m2.shp"
GEOJSON_PATH = OUTPUT_DIR / "dislope_inventory_3826_area_m2.geojson"
METADATA_PATH = OUTPUT_DIR / "download_metadata_3826_area_m2.json"
TARGET_CRS = "EPSG:3826"

CITY_COUNTS = {
    "\u81fa\u5317\u5e02": 437,
    "\u65b0\u5317\u5e02": 3166,
    "\u6843\u5712\u5e02": 466,
    "\u81fa\u4e2d\u5e02": 1694,
    "\u81fa\u5357\u5e02": 2279,
    "\u9ad8\u96c4\u5e02": 1102,
    "\u57fa\u9686\u5e02": 525,
    "\u65b0\u7af9\u7e23\u5e02": 1202,
    "\u82d7\u6817\u7e23": 1475,
    "\u5357\u6295\u7e23": 2450,
    "\u96f2\u6797\u7e23": 124,
    "\u5609\u7fa9\u7e23\u5e02": 1273,
    "\u5c4f\u6771\u7e23": 471,
    "\u5b9c\u862d\u7e23": 622,
    "\u82b1\u84ee\u7e23": 881,
    "\u81fa\u6771\u7e23": 840,
}


def fetch_city_geojson(city: str, expected_count: int) -> dict:
    params = {
        "filename": city,
        "coordinate": "WGS84",
        "filetype": "json",
        "limit": expected_count,
    }
    response = requests.get(API_URL, params=params, timeout=120)
    response.raise_for_status()

    data = response.json()
    features = data.get("features", [])
    if len(features) != expected_count:
        raise ValueError(
            f"{city} expected {expected_count} features, got {len(features)} from API."
        )

    for feature in features:
        feature.setdefault("properties", {})
        feature["properties"]["SRC_CITY"] = city

    return data


def normalize_columns(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if "C_Name" in gdf.columns:
        if "C_NAME" not in gdf.columns:
            gdf = gdf.rename(columns={"C_Name": "C_NAME"})
        else:
            gdf["C_NAME"] = gdf["C_NAME"].fillna(gdf["C_Name"])
            gdf = gdf.drop(columns=["C_Name"])
    return gdf


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_features: list[dict] = []
    downloaded_counts: dict[str, int] = {}

    for city, expected_count in CITY_COUNTS.items():
        city_data = fetch_city_geojson(city, expected_count)
        city_features = city_data["features"]
        all_features.extend(city_features)
        downloaded_counts[city] = len(city_features)
        print(f"{city}: {len(city_features)} features")

    gdf = gpd.GeoDataFrame.from_features(all_features, crs="EPSG:4326")
    gdf = normalize_columns(gdf)
    gdf = gdf.to_crs(TARGET_CRS)

    # Recalculate area after unifying CRS to EPSG:3826. Unit is square meters.
    gdf["AREA"] = gdf.geometry.area

    gdf.to_file(SHAPEFILE_PATH, driver="ESRI Shapefile", encoding="UTF-8")
    gdf.to_file(GEOJSON_PATH, driver="GeoJSON")

    metadata = {
        "source_api": API_URL,
        "coordinate": "TWD97 / EPSG:3826",
        "total_features": len(gdf),
        "cities": downloaded_counts,
        "fields": list(gdf.columns),
        "area_unit": "m^2",
        "outputs": {
            "shapefile": str(SHAPEFILE_PATH),
            "geojson": str(GEOJSON_PATH),
        },
    }
    METADATA_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Total features: {len(gdf)}")
    print(f"CRS: {gdf.crs}")
    print(f"Shapefile: {SHAPEFILE_PATH}")
    print(f"GeoJSON: {GEOJSON_PATH}")


if __name__ == "__main__":
    main()
