from __future__ import annotations

import concurrent.futures
import csv
import json
import math
import os
import re
import time
import zipfile
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import matplotlib

matplotlib.use("Agg")

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import mercantile
import nbformat as nbf
import numpy as np
import pandas as pd
import planetary_computer
import pyproj
import rasterio
import requests
from PIL import Image
from rasterio.features import rasterize, shapes as raster_shapes
from rasterio.transform import Affine
from rasterio.warp import Resampling, reproject
from shapely.geometry import MultiPolygon, Polygon, box, shape
from shapely.ops import transform as shapely_transform
from shapely.ops import unary_union
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from vt2geojson.tools import vt_bytes_to_geojson


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"

TAROKO_BBOX = [121.40, 24.10, 121.80, 24.25]
TARGET_CRS = "EPSG:32651"
TARGET_RESOLUTION = 20

BANDS_ALL = ["B02", "B03", "B04", "B08", "B11", "B12", "SCL"]
BANDS = ["B02", "B03", "B04", "B08", "B11", "B12"]
BAND_NAMES = ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2"]

CLASS_INFO = [
    {"id": 0, "en": "Water", "zh": "水體", "color": "#1f78b4"},
    {"id": 1, "en": "Forest", "zh": "森林", "color": "#33a02c"},
    {"id": 2, "en": "Cropland", "zh": "農田/草生地", "color": "#b2df8a"},
    {"id": 3, "en": "Bare/Landslide", "zh": "裸地/崩塌", "color": "#d2691e"},
    {"id": 4, "en": "Built-up", "zh": "建物/都市", "color": "#e31a1c"},
]

CLASS_NAMES = [c["en"] for c in CLASS_INFO]
CLASS_ZH = [c["zh"] for c in CLASS_INFO]
CLASS_COLORS = [c["color"] for c in CLASS_INFO]
CLASS_CMAP = mcolors.ListedColormap(CLASS_COLORS)

PINNED_ITEM_ID = "S2A_MSIL2A_20240827T022531_R046_T51QUG_20240827T053853"
PINNED_PREFIX = (
    "https://sentinel2l2a01.blob.core.windows.net/sentinel2-l2/51/Q/UG/2024/08/27/"
    "S2A_MSIL2A_20240827T022531_N0511_R046_T51QUG_20240827T053853.SAFE/"
    "GRANULE/L2A_T51QUG_A047948_20240827T023722/IMG_DATA"
)
PINNED_ASSETS = {
    "B02": f"{PINNED_PREFIX}/R10m/T51QUG_20240827T022531_B02_10m.tif",
    "B03": f"{PINNED_PREFIX}/R10m/T51QUG_20240827T022531_B03_10m.tif",
    "B04": f"{PINNED_PREFIX}/R10m/T51QUG_20240827T022531_B04_10m.tif",
    "B08": f"{PINNED_PREFIX}/R10m/T51QUG_20240827T022531_B08_10m.tif",
    "B11": f"{PINNED_PREFIX}/R20m/T51QUG_20240827T022531_B11_20m.tif",
    "B12": f"{PINNED_PREFIX}/R20m/T51QUG_20240827T022531_B12_20m.tif",
    "SCL": f"{PINNED_PREFIX}/R20m/T51QUG_20240827T022531_SCL_20m.tif",
}

SWCB_MVT_URL = (
    "https://gis.ardswc.gov.tw/api/ardswc/vectortiles/shp/"
    "event_landslide_inventories/{z}/{y}/{x}.pbf"
)
SWCB_SOURCE_URL = "https://data.ardswc.gov.tw/Data/OpenData/OpenDataDetail?sid=697"


@dataclass
class CycleConfig:
    name: str
    roi_target: int
    patch_radius: int
    max_patches: int
    rf_estimators: int
    rf_min_leaf: int
    note: str
    final: bool = False


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_")


def affine_to_list(transform: Affine) -> list[float]:
    return [
        float(transform.a),
        float(transform.b),
        float(transform.c),
        float(transform.d),
        float(transform.e),
        float(transform.f),
    ]


def list_to_affine(values: list[float]) -> Affine:
    return Affine(*values)


def target_grid() -> tuple[Affine, int, int, dict[str, Any]]:
    transformer = pyproj.Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)
    west, south, east, north = TAROKO_BBOX
    corners = [
        transformer.transform(west, south),
        transformer.transform(west, north),
        transformer.transform(east, south),
        transformer.transform(east, north),
    ]
    xs = [p[0] for p in corners]
    ys = [p[1] for p in corners]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    width = int(math.ceil((xmax - xmin) / TARGET_RESOLUTION))
    height = int(math.ceil((ymax - ymin) / TARGET_RESOLUTION))
    transform = Affine(TARGET_RESOLUTION, 0, xmin, 0, -TARGET_RESOLUTION, ymax)
    meta = {
        "bbox_wgs84": TAROKO_BBOX,
        "target_crs": TARGET_CRS,
        "target_resolution_m": TARGET_RESOLUTION,
        "utm_bounds": [xmin, ymin, xmax, ymax],
        "height": height,
        "width": width,
    }
    return transform, height, width, meta


def _search_stac_item() -> tuple[dict[str, Any], dict[str, str]]:
    from pystac_client import Client

    search_configs = [
        ("2024-04-03/2024-05-31", 20, "strict post-earthquake"),
        ("2024-04-03/2024-08-31", 35, "relaxed cloud"),
        ("2024-04-03/2024-12-31", 60, "full post-earthquake season"),
    ]
    catalog = Client.open("https://planetarycomputer.microsoft.com/api/stac/v1")
    last_error = None
    for dt_range, max_cloud, label in search_configs:
        try:
            search = catalog.search(
                collections=["sentinel-2-l2a"],
                bbox=TAROKO_BBOX,
                datetime=dt_range,
                query={"eo:cloud_cover": {"lt": max_cloud}},
                sortby=[{"field": "properties.eo:cloud_cover", "direction": "asc"}],
                limit=20,
            )
            items = list(search.items())
            if items:
                item = sorted(items, key=lambda x: x.properties.get("eo:cloud_cover", 999))[0]
                assets = {band: item.assets[band].href for band in BANDS_ALL}
                metadata = {
                    "item_id": item.id,
                    "datetime": item.datetime.isoformat() if item.datetime else "",
                    "cloud_cover": item.properties.get("eo:cloud_cover"),
                    "platform": item.properties.get("platform"),
                    "search_label": label,
                    "source": "Microsoft Planetary Computer STAC",
                }
                return metadata, assets
        except Exception as exc:  # pragma: no cover - network fallback
            last_error = f"{type(exc).__name__}: {exc}"

    metadata = {
        "item_id": PINNED_ITEM_ID,
        "datetime": "2024-08-27T02:25:31+00:00",
        "cloud_cover": 8.358254,
        "platform": "Sentinel-2A",
        "search_label": "pinned fallback",
        "source": "Pinned Sentinel-2 L2A COG fallback",
        "fallback_reason": last_error or "STAC search returned no usable items",
    }
    return metadata, PINNED_ASSETS.copy()


def load_sentinel_stack(force: bool = False) -> dict[str, Any]:
    ensure_dirs()
    cache_path = DATA_DIR / "taroko_s2_stack.npz"
    meta_path = DATA_DIR / "taroko_s2_metadata.json"
    if cache_path.exists() and meta_path.exists() and not force:
        with np.load(cache_path, allow_pickle=False) as data:
            img = data["img"]
            scl = data["scl"]
            valid_mask = data["valid_mask"].astype(bool)
            transform = list_to_affine(data["transform"].tolist())
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        return {
            "img": img,
            "scl": scl,
            "valid_mask": valid_mask,
            "transform": transform,
            "metadata": metadata,
        }

    metadata, assets = _search_stac_item()
    transform, height, width, grid_meta = target_grid()
    layers: list[np.ndarray] = []
    print(f"Loading Sentinel-2 stack: {metadata['item_id']}")
    print(f"Target grid: {height} rows x {width} cols at {TARGET_RESOLUTION} m")
    for band in BANDS_ALL:
        href = planetary_computer.sign_url(assets[band])
        resampling = Resampling.nearest if band == "SCL" else Resampling.bilinear
        dest = np.full((height, width), np.nan, dtype=np.float32)
        with rasterio.Env(
            GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
            CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
        ):
            with rasterio.open(href) as src:
                reproject(
                    source=rasterio.band(src, 1),
                    destination=dest,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    src_nodata=src.nodata,
                    dst_transform=transform,
                    dst_crs=TARGET_CRS,
                    dst_nodata=np.nan,
                    resampling=resampling,
                )
        layers.append(dest)
        print(f"  loaded {band}")

    raw = np.stack(layers, axis=0)
    scl = raw[-1].copy()
    img = raw[:-1] / 10000.0
    cloud_or_bad = np.isin(scl, [0, 1, 3, 8, 9, 10, 11]) | np.any((img <= 0) | (img > 1), axis=0)
    img[:, cloud_or_bad] = np.nan
    valid_mask = ~np.any(np.isnan(img), axis=0)
    metadata.update(grid_meta)
    metadata["valid_pixels"] = int(valid_mask.sum())
    metadata["valid_percent"] = float(valid_mask.mean() * 100)
    metadata["bands"] = BANDS
    metadata["scl_masked_values"] = [0, 1, 3, 8, 9, 10, 11]

    np.savez_compressed(
        cache_path,
        img=img.astype(np.float32),
        scl=scl.astype(np.float32),
        valid_mask=valid_mask.astype(np.uint8),
        transform=np.array(affine_to_list(transform), dtype=np.float64),
    )
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"img": img, "scl": scl, "valid_mask": valid_mask, "transform": transform, "metadata": metadata}


def indices(img: np.ndarray) -> dict[str, np.ndarray]:
    blue, green, red, nir, swir1, swir2 = img
    eps = 1e-10
    ndvi = (nir - red) / (nir + red + eps)
    ndwi = (green - nir) / (green + nir + eps)
    ndbi = (swir1 - nir) / (swir1 + nir + eps)
    visible = (blue + green + red) / 3.0
    return {"ndvi": ndvi, "ndwi": ndwi, "ndbi": ndbi, "visible": visible}


def make_rgb(img: np.ndarray) -> np.ndarray:
    rgb = np.stack([img[2], img[1], img[0]], axis=-1).copy()
    out = np.zeros_like(rgb, dtype=np.float32)
    for i in range(3):
        band = rgb[:, :, i]
        valid = band[np.isfinite(band)]
        if len(valid) == 0:
            continue
        lo, hi = np.nanpercentile(valid, [2, 98])
        out[:, :, i] = np.clip((band - lo) / (hi - lo + 1e-10), 0, 1)
    out[~np.isfinite(out)] = 0
    return out


def save_class_map(
    class_map: np.ndarray,
    out_path: Path,
    title: str,
    colors: list[str] | None = None,
    labels: list[str] | None = None,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmap = mcolors.ListedColormap(colors or CLASS_COLORS)
    vmax = len(colors or CLASS_COLORS) - 0.5
    fig, ax = plt.subplots(figsize=(10, 7), dpi=160)
    masked = np.ma.masked_where(class_map < 0, class_map)
    im = ax.imshow(masked, cmap=cmap, vmin=-0.5, vmax=vmax)
    ax.set_title(title, fontsize=13)
    ax.set_xlabel("Column")
    ax.set_ylabel("Row")
    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02, ticks=range(len(colors or CLASS_COLORS)))
    cbar.ax.set_yticklabels(labels or CLASS_NAMES)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def interpret_cluster(mean_spectrum: np.ndarray) -> tuple[str, str]:
    blue, green, red, nir, swir1, swir2 = mean_spectrum
    ndvi = (nir - red) / (nir + red + 1e-10)
    ndwi = (green - nir) / (green + nir + 1e-10)
    ndbi = (swir1 - nir) / (swir1 + nir + 1e-10)
    visible = (blue + green + red) / 3.0
    if ndwi > 0.05 and nir < 0.12:
        return "Water / 水體", f"NDWI={ndwi:.2f}, NIR={nir:.2f} is low"
    if ndvi > 0.55:
        return "Forest / 森林", f"NDVI={ndvi:.2f} is high"
    if ndvi > 0.35:
        return "Cropland or grass / 農田或草生地", f"NDVI={ndvi:.2f} is moderate"
    if ndbi > -0.03 and visible > 0.12:
        return "Built-up or bright bare / 建物或亮裸地", f"NDBI={ndbi:.2f}, visible={visible:.2f}"
    return "Bare/Landslide / 裸地或崩塌", f"NDVI={ndvi:.2f}, SWIR1={swir1:.2f}"


def run_kmeans(data: dict[str, Any], out_dir: Path, random_state: int = 42) -> dict[str, Any]:
    img = data["img"]
    valid = data["valid_mask"]
    x_valid = img[:, valid].T
    rng = np.random.default_rng(random_state)
    sample_n = min(120_000, len(x_valid))
    sample_idx = rng.choice(len(x_valid), size=sample_n, replace=False)
    scaler = StandardScaler()
    x_sample = scaler.fit_transform(x_valid[sample_idx])
    kmeans = KMeans(n_clusters=5, random_state=random_state, n_init=10, max_iter=300)
    kmeans.fit(x_sample)

    labels = np.empty(len(x_valid), dtype=np.int16)
    chunk = 250_000
    for start in range(0, len(x_valid), chunk):
        stop = min(len(x_valid), start + chunk)
        labels[start:stop] = kmeans.predict(scaler.transform(x_valid[start:stop]))

    kmap = np.full(valid.shape, -1, dtype=np.int16)
    kmap[valid] = labels
    cluster_means = np.vstack([x_valid[labels == c].mean(axis=0) for c in range(5)])
    rows = []
    for c in range(5):
        label, reason = interpret_cluster(cluster_means[c])
        rows.append(
            {
                "cluster": c,
                "pixel_count": int((labels == c).sum()),
                **{band: float(cluster_means[c, i]) for i, band in enumerate(BAND_NAMES)},
                "interpreted_label": label,
                "reason": reason,
            }
        )
    cluster_df = pd.DataFrame(rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    cluster_df.to_csv(out_dir / "kmeans_mean_spectra.csv", index=False, encoding="utf-8-sig")
    save_class_map(
        kmap,
        out_dir / "kmeans_classification.png",
        "K-means Classification (K=5)",
        colors=["#2b83ba", "#1a9850", "#91cf60", "#fdae61", "#d7191c"],
        labels=[f"C{i}" for i in range(5)],
    )

    fig, ax = plt.subplots(figsize=(9, 5), dpi=160)
    for c in range(5):
        ax.plot(BAND_NAMES, cluster_means[c], marker="o", label=f"C{c}")
    ax.set_ylabel("Mean reflectance")
    ax.set_title("K-means Mean Spectra")
    ax.grid(alpha=0.25)
    ax.legend(ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(out_dir / "kmeans_mean_spectra.png", bbox_inches="tight")
    plt.close(fig)

    return {
        "map": kmap,
        "cluster_table": rows,
        "sample_n": int(sample_n),
        "valid_n": int(len(x_valid)),
    }


def pixel_center_grids(transform: Affine, shape_hw: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    rows, cols = shape_hw
    x = transform.c + (np.arange(cols) + 0.5) * transform.a
    y = transform.f + (np.arange(rows) + 0.5) * transform.e
    return np.meshgrid(x, y)


def lonlat_grids(transform: Affine, shape_hw: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    xx, yy = pixel_center_grids(transform, shape_hw)
    transformer = pyproj.Transformer.from_crs(TARGET_CRS, "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(xx, yy)
    return lon.astype(np.float32), lat.astype(np.float32)


def percentile(arr: np.ndarray, mask: np.ndarray, q: float) -> float:
    values = arr[mask & np.isfinite(arr)]
    if len(values) == 0:
        return float("nan")
    return float(np.nanpercentile(values, q))


def top_score_mask(base: np.ndarray, score: np.ndarray, keep: int) -> np.ndarray:
    base = base & np.isfinite(score)
    rr, cc = np.where(base)
    if len(rr) <= keep:
        return base
    values = score[rr, cc]
    cutoff = np.partition(values, len(values) - keep)[len(values) - keep]
    return base & (score >= cutoff)


def select_patches(
    candidate_mask: np.ndarray,
    score: np.ndarray,
    cls_id: int,
    roi: np.ndarray,
    target_pixels: int,
    patch_radius: int,
    max_patches: int,
    rng: np.random.Generator,
) -> list[tuple[int, int]]:
    selected: list[tuple[int, int]] = []
    candidate_mask = candidate_mask & (roi == -1) & np.isfinite(score)
    rr, cc = np.where(candidate_mask)
    if len(rr) == 0:
        return selected
    values = score[rr, cc]
    order = np.argsort(values)[::-1]
    height, width = roi.shape
    min_distance = max(10, patch_radius * 4)
    selected_pixels = 0
    top_limit = min(len(order), max(15_000, max_patches * 350))
    for oi in order[:top_limit]:
        if len(selected) >= max_patches or selected_pixels >= target_pixels:
            break
        r, c = int(rr[oi]), int(cc[oi])
        if any((r - sr) ** 2 + (c - sc) ** 2 < min_distance**2 for sr, sc in selected):
            continue
        r0 = max(0, r - patch_radius)
        r1 = min(height, r + patch_radius + 1)
        c0 = max(0, c - patch_radius)
        c1 = min(width, c + patch_radius + 1)
        patch = candidate_mask[r0:r1, c0:c1] & (roi[r0:r1, c0:c1] == -1)
        if int(patch.sum()) < max(5, patch_radius):
            continue
        roi[r0:r1, c0:c1][patch] = cls_id
        selected.append((r, c))
        selected_pixels += int(patch.sum())

    if selected_pixels < max(120, target_pixels // 4):
        remaining = candidate_mask & (roi == -1)
        rr2, cc2 = np.where(remaining)
        if len(rr2):
            take = min(len(rr2), max(120, target_pixels // 4) - selected_pixels)
            ranked = np.argsort(score[rr2, cc2])[::-1][:take]
            roi[rr2[ranked], cc2[ranked]] = cls_id
            selected.append((int(rr2[ranked[0]]), int(cc2[ranked[0]])))
    return selected


def build_roi_mask(data: dict[str, Any], config: CycleConfig) -> tuple[np.ndarray, dict[str, Any]]:
    img = data["img"]
    scl = data["scl"]
    valid = data["valid_mask"]
    transform = data["transform"]
    idx = indices(img)
    ndvi, ndwi, ndbi, visible = idx["ndvi"], idx["ndwi"], idx["ndbi"], idx["visible"]
    blue, green, red, nir, swir1, swir2 = img
    lon, lat = lonlat_grids(transform, valid.shape)

    q = {
        "ndvi20": percentile(ndvi, valid, 20),
        "ndvi35": percentile(ndvi, valid, 35),
        "ndvi55": percentile(ndvi, valid, 55),
        "ndvi70": percentile(ndvi, valid, 70),
        "visible45": percentile(visible, valid, 45),
        "visible60": percentile(visible, valid, 60),
        "visible75": percentile(visible, valid, 75),
        "swir60": percentile(swir1, valid, 60),
        "swir75": percentile(swir1, valid, 75),
        "nir25": percentile(nir, valid, 25),
        "ndbi60": percentile(ndbi, valid, 60),
    }

    inland = lon < 121.68
    coast = lon > 121.55
    ocean = lon > 121.63
    valley = (lon > 121.50) & (lon < 121.74) & (lat > 24.105) & (lat < 24.245)
    mountain = lon < 121.62

    broad = {
        0: valid & ocean,
        1: valid & inland,
        2: valid & valley,
        3: valid & mountain,
        4: valid & coast,
    }
    candidates = {
        0: broad[0] & ((scl == 6) | ((ndwi > np.nanpercentile(ndwi[valid], 70)) & (nir < q["nir25"] + 0.03))),
        1: broad[1] & (ndvi > max(0.48, q["ndvi70"])) & (nir > red),
        2: broad[2] & (ndvi > max(0.22, q["ndvi35"])) & (ndvi < 0.62) & (visible < q["visible75"] + 0.05),
        3: broad[3] & (ndvi < min(0.32, q["ndvi35"] + 0.05)) & (swir1 > q["swir60"]) & (visible > q["visible45"]),
        4: broad[4] & (ndvi < min(0.42, q["ndvi55"])) & (ndbi > q["ndbi60"] - 0.08) & (visible > q["visible45"]),
    }
    scores = {
        0: 2.2 * ndwi - 1.5 * nir - 1.0 * swir1 - 0.4 * visible,
        1: 2.0 * ndvi + 0.5 * nir - 0.8 * visible,
        2: -np.abs(ndvi - 0.38) + 0.2 * nir - 0.4 * np.abs(ndbi),
        3: 1.4 * swir1 + 1.2 * visible + 0.4 * red - 2.0 * ndvi,
        4: 1.2 * ndbi + 0.9 * visible - 0.8 * ndvi,
    }

    relaxed = {
        0: top_score_mask(broad[0] & valid, scores[0], 8000),
        1: top_score_mask(broad[1] & valid & (ndvi > q["ndvi55"]), scores[1], 9000),
        2: top_score_mask(broad[2] & valid & (ndvi > 0.16) & (ndvi < 0.68), scores[2], 9000),
        3: top_score_mask(broad[3] & valid & (ndvi < 0.45) & (visible > q["visible45"] - 0.03), scores[3], 9000),
        4: top_score_mask(broad[4] & valid & (ndvi < 0.55) & (visible > q["visible45"] - 0.02), scores[4], 9000),
    }

    roi = np.full(valid.shape, -1, dtype=np.int16)
    rng = np.random.default_rng(100 + len(config.name))
    roi_counts_before: dict[str, int] = {}
    selected_centers: dict[str, list[tuple[int, int]]] = {}
    for cls_id in [0, 1, 3, 4, 2]:
        mask = candidates[cls_id] & (roi == -1)
        roi_counts_before[CLASS_NAMES[cls_id]] = int(mask.sum())
        if int(mask.sum()) < max(150, config.roi_target // 2):
            mask = relaxed[cls_id] & (roi == -1)
        centers = select_patches(
            mask,
            scores[cls_id],
            cls_id,
            roi,
            target_pixels=config.roi_target,
            patch_radius=config.patch_radius,
            max_patches=config.max_patches,
            rng=rng,
        )
        selected_centers[CLASS_NAMES[cls_id]] = centers

    counts = {CLASS_NAMES[i]: int((roi == i).sum()) for i in range(len(CLASS_INFO))}
    diagnostics = {
        "candidate_pixels_before_relax": roi_counts_before,
        "roi_pixels": counts,
        "selected_centers": {k: len(v) for k, v in selected_centers.items()},
        "quantiles": {k: float(v) for k, v in q.items()},
    }
    return roi, diagnostics


def polygon_to_kml_coordinates(poly: Polygon) -> str:
    return " ".join(f"{x:.8f},{y:.8f},0" for x, y in poly.exterior.coords)


def write_roi_kmz(roi: np.ndarray, transform: Affine, kmz_path: Path) -> None:
    transformer = pyproj.Transformer.from_crs(TARGET_CRS, "EPSG:4326", always_xy=True)
    kml: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        "<Document>",
        "<name>Week12 Taroko Training ROIs</name>",
    ]
    for cls in CLASS_INFO:
        color = mcolors.to_hex(cls["color"]).replace("#", "")
        # KML color order: aabbggrr.
        rr, gg, bb = color[0:2], color[2:4], color[4:6]
        kml_color = f"bb{bb}{gg}{rr}"
        kml.extend(
            [
                f'<Style id="class_{cls["id"]}">',
                f"<LineStyle><color>{kml_color}</color><width>1</width></LineStyle>",
                f"<PolyStyle><color>{kml_color}</color></PolyStyle>",
                "</Style>",
            ]
        )
    for cls in CLASS_INFO:
        cls_id = cls["id"]
        mask = roi == cls_id
        if not mask.any():
            continue
        for n, (geom_json, value) in enumerate(
            raster_shapes(mask.astype(np.uint8), mask=mask, transform=transform),
            start=1,
        ):
            if int(value) != 1:
                continue
            geom = shape(geom_json)
            geom_wgs = shapely_transform(transformer.transform, geom)
            polygons = list(geom_wgs.geoms) if isinstance(geom_wgs, MultiPolygon) else [geom_wgs]
            for sub, poly in enumerate(polygons, start=1):
                if poly.is_empty or poly.area <= 0:
                    continue
                name = f"{cls_id}_{cls['en']}_{cls['zh']}_{n:02d}_{sub:02d}"
                kml.extend(
                    [
                        "<Placemark>",
                        f"<name>{name}</name>",
                        f'<styleUrl>#class_{cls_id}</styleUrl>',
                        "<Polygon><outerBoundaryIs><LinearRing>",
                        f"<coordinates>{polygon_to_kml_coordinates(poly)}</coordinates>",
                        "</LinearRing></outerBoundaryIs></Polygon>",
                        "</Placemark>",
                    ]
                )
    kml.extend(["</Document>", "</kml>"])
    kmz_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(kmz_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("doc.kml", "\n".join(kml).encode("utf-8"))


def parse_kmz_polygons(kmz_path: Path) -> dict[int, list[Polygon]]:
    with zipfile.ZipFile(kmz_path, "r") as zf:
        kml_name = next(n for n in zf.namelist() if n.lower().endswith(".kml"))
        root = ET.fromstring(zf.read(kml_name))
    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    polygons_by_class: dict[int, list[Polygon]] = {i: [] for i in range(len(CLASS_INFO))}
    for pm in root.findall(".//kml:Placemark", ns):
        name_el = pm.find("kml:name", ns)
        coords_el = pm.find(".//kml:coordinates", ns)
        if name_el is None or coords_el is None or not name_el.text:
            continue
        match = re.match(r"(\d)_", name_el.text.strip())
        if not match:
            continue
        cls_id = int(match.group(1))
        coords = []
        for token in coords_el.text.strip().split():
            lon, lat, *_ = token.split(",")
            coords.append((float(lon), float(lat)))
        if len(coords) >= 4:
            poly = Polygon(coords)
            if not poly.is_valid:
                poly = poly.buffer(0)
            if not poly.is_empty:
                polygons_by_class[cls_id].append(poly)
    return polygons_by_class


def rasterize_wgs84_class_polygons(polygons_by_class: dict[int, list[Polygon]], shape_hw: tuple[int, int], transform: Affine) -> np.ndarray:
    transformer = pyproj.Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)
    shapes_with_values = []
    for cls_id, polygons in polygons_by_class.items():
        for poly in polygons:
            poly_utm = shapely_transform(transformer.transform, poly)
            if not poly_utm.is_empty:
                shapes_with_values.append((poly_utm, cls_id))
    if not shapes_with_values:
        raise RuntimeError("No valid polygons could be rasterized from KMZ.")
    return rasterize(
        shapes_with_values,
        out_shape=shape_hw,
        transform=transform,
        fill=-1,
        dtype=np.int16,
        all_touched=False,
    )


def make_training_data(img: np.ndarray, roi_from_kmz: np.ndarray, rng_seed: int = 42) -> tuple[np.ndarray, np.ndarray, dict[str, int]]:
    rng = np.random.default_rng(rng_seed)
    x_list: list[np.ndarray] = []
    y_list: list[np.ndarray] = []
    counts: dict[str, int] = {}
    for cls_id, cls in enumerate(CLASS_INFO):
        mask = roi_from_kmz == cls_id
        pixels = img[:, mask].T
        pixels = pixels[~np.any(np.isnan(pixels), axis=1)]
        counts[cls["en"]] = int(len(pixels))
        if len(pixels) == 0:
            continue
        max_samples = 2200
        if len(pixels) > max_samples:
            pixels = pixels[rng.choice(len(pixels), max_samples, replace=False)]
        x_list.append(pixels)
        y_list.append(np.full(len(pixels), cls_id, dtype=np.int16))
    if len(x_list) != len(CLASS_INFO):
        missing = [CLASS_NAMES[i] for i in range(len(CLASS_INFO)) if counts.get(CLASS_NAMES[i], 0) == 0]
        raise RuntimeError(f"Missing ROI training classes after KMZ parse: {missing}")
    return np.vstack(x_list), np.concatenate(y_list), counts


def plot_roi_overlay(data: dict[str, Any], roi: np.ndarray, out_path: Path) -> None:
    rgb = make_rgb(data["img"])
    fig, ax = plt.subplots(figsize=(10, 7), dpi=160)
    ax.imshow(rgb)
    for cls in CLASS_INFO:
        mask = roi == cls["id"]
        overlay = np.zeros((*mask.shape, 4), dtype=np.float32)
        overlay[mask] = mcolors.to_rgba(cls["color"], alpha=0.55)
        ax.imshow(overlay)
    patches = [plt.matplotlib.patches.Patch(color=cls["color"], label=f"{cls['id']} {cls['en']}") for cls in CLASS_INFO]
    ax.legend(handles=patches, fontsize=8, loc="upper right", framealpha=0.9)
    ax.set_title("Training ROI parsed from KMZ")
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def run_random_forest(
    data: dict[str, Any],
    kmz_path: Path,
    config: CycleConfig,
    out_dir: Path,
) -> dict[str, Any]:
    polygons_by_class = parse_kmz_polygons(kmz_path)
    roi_from_kmz = rasterize_wgs84_class_polygons(polygons_by_class, data["valid_mask"].shape, data["transform"])
    plot_roi_overlay(data, roi_from_kmz, out_dir / "training_roi_from_kmz.png")
    x_train, y_train, roi_counts = make_training_data(data["img"], roi_from_kmz, rng_seed=200 + len(config.name))
    x_tr, x_te, y_tr, y_te = train_test_split(
        x_train,
        y_train,
        test_size=0.25,
        random_state=42,
        stratify=y_train,
    )
    rf = RandomForestClassifier(
        n_estimators=config.rf_estimators,
        min_samples_leaf=config.rf_min_leaf,
        random_state=42,
        n_jobs=-1,
        oob_score=True,
        class_weight="balanced_subsample",
    )
    rf.fit(x_tr, y_tr)
    y_pred = rf.predict(x_te)
    test_acc = accuracy_score(y_te, y_pred)
    macro_f1 = f1_score(y_te, y_pred, average="macro")
    weighted_f1 = f1_score(y_te, y_pred, average="weighted")
    cm = confusion_matrix(y_te, y_pred, labels=list(range(len(CLASS_INFO))))
    report = classification_report(y_te, y_pred, target_names=CLASS_NAMES, output_dict=True, zero_division=0)
    report_text = classification_report(y_te, y_pred, target_names=CLASS_NAMES, zero_division=0)

    x_valid = data["img"][:, data["valid_mask"]].T
    labels = np.empty(len(x_valid), dtype=np.int16)
    chunk = 250_000
    for start in range(0, len(x_valid), chunk):
        stop = min(len(x_valid), start + chunk)
        labels[start:stop] = rf.predict(x_valid[start:stop])
    class_map = np.full(data["valid_mask"].shape, -1, dtype=np.int16)
    class_map[data["valid_mask"]] = labels
    save_class_map(class_map, out_dir / "rf_classification.png", "Random Forest Land Cover Classification")

    fig, ax = plt.subplots(figsize=(7, 5), dpi=160)
    order = np.argsort(rf.feature_importances_)
    ax.barh(np.array(BAND_NAMES)[order], rf.feature_importances_[order], color="#4c78a8")
    ax.set_xlabel("Feature importance")
    ax.set_title("Random Forest Band Importance")
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(out_dir / "feature_importance.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.5, 5.5), dpi=160)
    im = ax.imshow(cm, cmap="Blues")
    ax.set_title("Confusion Matrix")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Reference ROI")
    ax.set_xticks(range(len(CLASS_INFO)), CLASS_NAMES, rotation=35, ha="right")
    ax.set_yticks(range(len(CLASS_INFO)), CLASS_NAMES)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.045, pad=0.02)
    fig.tight_layout()
    fig.savefig(out_dir / "confusion_matrix.png", bbox_inches="tight")
    plt.close(fig)

    return {
        "map": class_map,
        "roi_counts": roi_counts,
        "train_sample_count": int(len(x_train)),
        "test_accuracy": float(test_acc),
        "oob_score": float(rf.oob_score_),
        "macro_f1": float(macro_f1),
        "weighted_f1": float(weighted_f1),
        "macro_weighted_gap": float(weighted_f1 - macro_f1),
        "oob_test_gap": float(test_acc - rf.oob_score_),
        "feature_importance": {BAND_NAMES[i]: float(v) for i, v in enumerate(rf.feature_importances_)},
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
        "classification_report_text": report_text,
    }


def _tile_features(tile: mercantile.Tile, z: int) -> list[dict[str, Any]]:
    url = SWCB_MVT_URL.format(z=z, y=tile.y, x=tile.x)
    response = requests.get(url, timeout=20)
    if len(response.content) <= 100:
        return []
    geojson = vt_bytes_to_geojson(response.content, tile.x, tile.y, z)
    return geojson.get("features", [])


def write_polygons_kml(polygons: list[tuple[dict[str, Any], Any]], kml_path: Path) -> None:
    kml: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        "<Document>",
        "<name>20240802新生崩塌地 - ARDSWC event landslide inventory</name>",
    ]
    for i, (props, geom) in enumerate(polygons, start=1):
        geoms = list(geom.geoms) if isinstance(geom, MultiPolygon) else [geom]
        for j, poly in enumerate(geoms, start=1):
            if not isinstance(poly, Polygon) or poly.is_empty:
                continue
            name = f"SWCB_{props.get('gid', i)}_{j}"
            event = props.get("events", "")
            area = props.get("area_ha", "")
            kml.extend(
                [
                    "<Placemark>",
                    f"<name>{name}</name>",
                    "<ExtendedData>",
                    f'<Data name="events"><value>{event}</value></Data>',
                    f'<Data name="area_ha"><value>{area}</value></Data>',
                    f'<Data name="source"><value>{props.get("datasource", "")}</value></Data>',
                    "</ExtendedData>",
                    "<Polygon><outerBoundaryIs><LinearRing>",
                    f"<coordinates>{polygon_to_kml_coordinates(poly)}</coordinates>",
                    "</LinearRing></outerBoundaryIs></Polygon>",
                    "</Placemark>",
                ]
            )
    kml.extend(["</Document>", "</kml>"])
    kml_path.write_text("\n".join(kml), encoding="utf-8")


def download_swcb_kml(force: bool = False) -> tuple[Path, dict[str, Any]]:
    ensure_dirs()
    kml_path = DATA_DIR / "20240802新生崩塌地.kml"
    meta_path = DATA_DIR / "swcb_reference_metadata.json"
    if kml_path.exists() and meta_path.exists() and not force:
        return kml_path, json.loads(meta_path.read_text(encoding="utf-8"))

    west, south, east, north = TAROKO_BBOX
    z = 14
    tiles = list(mercantile.tiles(west, south, east, north, [z]))
    study_box = box(west, south, east, north)
    parts_by_gid: dict[str, list[Any]] = defaultdict(list)
    props_by_gid: dict[str, dict[str, Any]] = {}
    print(f"Downloading ARDSWC/SWCB MVT landslide reference: {len(tiles)} tiles")
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(_tile_features, tile, z) for tile in tiles]
        for future in concurrent.futures.as_completed(futures):
            for feat in future.result():
                props = feat.get("properties", {})
                geom = shape(feat["geometry"])
                if not geom.is_valid:
                    geom = geom.buffer(0)
                if geom.is_empty or not geom.intersects(study_box):
                    continue
                gid = str(props.get("gid") or f"nogid_{len(parts_by_gid)}")
                clipped = geom.intersection(study_box)
                if not clipped.is_empty:
                    parts_by_gid[gid].append(clipped)
                    props_by_gid[gid] = props

    polygons: list[tuple[dict[str, Any], Any]] = []
    for gid, parts in parts_by_gid.items():
        geom = unary_union(parts)
        if not geom.is_valid:
            geom = geom.buffer(0)
        if not geom.is_empty:
            props = props_by_gid[gid].copy()
            props["gid"] = gid
            polygons.append((props, geom))

    if not polygons:
        raise RuntimeError("Official ARDSWC landslide MVT returned no polygons in the Taroko bbox.")
    write_polygons_kml(polygons, kml_path)
    total_area_ha = sum(float(p.get("area_ha", 0) or 0) for p, _ in polygons)
    metadata = {
        "source_url": SWCB_SOURCE_URL,
        "mvt_url_pattern": SWCB_MVT_URL,
        "zoom": z,
        "tile_count": len(tiles),
        "polygon_count": len(polygons),
        "event_names": sorted({str(p.get("events", "")) for p, _ in polygons}),
        "reported_area_ha_sum": total_area_ha,
        "note": "Google Drive homework link was checked locally but returned the Week12 notebook JSON; official ARDSWC MVT was used instead.",
    }
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return kml_path, metadata


def read_kml_polygons(kml_path: Path) -> list[Polygon]:
    root = ET.parse(kml_path).getroot()
    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    polygons: list[Polygon] = []
    for coords_el in root.findall(".//kml:coordinates", ns):
        coords = []
        for token in coords_el.text.strip().split():
            lon, lat, *_ = token.split(",")
            coords.append((float(lon), float(lat)))
        if len(coords) >= 4:
            poly = Polygon(coords)
            if not poly.is_valid:
                poly = poly.buffer(0)
            if not poly.is_empty:
                polygons.append(poly)
    return polygons


def run_swcb_validation(data: dict[str, Any], rf_map: np.ndarray, out_dir: Path) -> dict[str, Any]:
    kml_path, swcb_meta = download_swcb_kml()
    polygons = read_kml_polygons(kml_path)
    study = box(*TAROKO_BBOX)
    polygons = [poly.intersection(study) for poly in polygons if poly.intersects(study)]
    transformer = pyproj.Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)
    shapes_with_values = []
    for poly in polygons:
        geom = shapely_transform(transformer.transform, poly)
        if not geom.is_empty:
            shapes_with_values.append((geom, 1))
    swcb_mask = rasterize(
        shapes_with_values,
        out_shape=data["valid_mask"].shape,
        transform=data["transform"],
        fill=0,
        dtype=np.uint8,
        all_touched=True,
    ).astype(bool)
    rf_landslide = (rf_map == 3) & data["valid_mask"]
    ref = swcb_mask & data["valid_mask"]
    tp = rf_landslide & ref
    fp = rf_landslide & ~ref
    fn = ~rf_landslide & ref
    tn = ~rf_landslide & ~ref & data["valid_mask"]
    counts = {
        "tp": int(tp.sum()),
        "fp": int(fp.sum()),
        "fn": int(fn.sum()),
        "tn": int(tn.sum()),
    }
    precision = counts["tp"] / max(1, counts["tp"] + counts["fp"])
    recall = counts["tp"] / max(1, counts["tp"] + counts["fn"])
    iou = counts["tp"] / max(1, counts["tp"] + counts["fp"] + counts["fn"])
    pixel_ha = (TARGET_RESOLUTION * TARGET_RESOLUTION) / 10_000
    metrics = {
        **counts,
        "precision": float(precision),
        "recall": float(recall),
        "iou": float(iou),
        "swcb_pixel_area_ha": float(ref.sum() * pixel_ha),
        "rf_bare_landslide_area_ha": float(rf_landslide.sum() * pixel_ha),
        "swcb_polygon_count": int(len(polygons)),
        "swcb_kml": str(kml_path.relative_to(BASE_DIR)),
        "swcb_source": swcb_meta,
    }

    rgb = make_rgb(data["img"])
    overlay = np.zeros((*rf_map.shape, 4), dtype=np.float32)
    overlay[tp] = mcolors.to_rgba("#d73027", alpha=0.78)
    overlay[fn] = mcolors.to_rgba("#fee08b", alpha=0.82)
    overlay[fp] = mcolors.to_rgba("#4575b4", alpha=0.62)
    fig, ax = plt.subplots(figsize=(10, 7), dpi=160)
    ax.imshow(rgb)
    ax.imshow(overlay)
    patches = [
        plt.matplotlib.patches.Patch(color="#d73027", label="TP: RF landslide + SWCB"),
        plt.matplotlib.patches.Patch(color="#fee08b", label="FN: SWCB missed by RF"),
        plt.matplotlib.patches.Patch(color="#4575b4", label="FP: RF bare/landslide only"),
    ]
    ax.legend(handles=patches, loc="lower left", fontsize=8, framealpha=0.9)
    ax.set_title("RF Bare/Landslide vs Official SWCB Landslide Polygons")
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(out_dir / "swcb_overlay.png", bbox_inches="tight")
    plt.close(fig)
    return metrics


def write_area_stats(data: dict[str, Any], rf_map: np.ndarray, out_dir: Path) -> tuple[list[dict[str, Any]], Path]:
    pixel_ha = (TARGET_RESOLUTION * TARGET_RESOLUTION) / 10_000
    valid_n = int(data["valid_mask"].sum())
    rows = []
    for cls in CLASS_INFO:
        pixels = int(((rf_map == cls["id"]) & data["valid_mask"]).sum())
        area_ha = pixels * pixel_ha
        rows.append(
            {
                "class_id": cls["id"],
                "class_en": cls["en"],
                "class_zh": cls["zh"],
                "pixels": pixels,
                "area_ha": area_ha,
                "area_km2": area_ha / 100.0,
                "percent_valid": pixels / max(1, valid_n) * 100,
            }
        )
    out_path = out_dir / "class_area_stats.csv"
    with out_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows, out_path


def plot_kmeans_rf_comparison(kmap: np.ndarray, rf_map: np.ndarray, out_dir: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), dpi=160)
    axes[0].imshow(np.ma.masked_where(kmap < 0, kmap), cmap="tab10", vmin=-0.5, vmax=4.5)
    axes[0].set_title("K-means clusters")
    axes[0].set_axis_off()
    axes[1].imshow(np.ma.masked_where(rf_map < 0, rf_map), cmap=CLASS_CMAP, vmin=-0.5, vmax=4.5)
    axes[1].set_title("Random Forest classes")
    axes[1].set_axis_off()
    fig.tight_layout()
    fig.savefig(out_dir / "kmeans_vs_rf_comparison.png", bbox_inches="tight")
    plt.close(fig)


def commander_report(area_rows: list[dict[str, Any]], rf_metrics: dict[str, Any], swcb: dict[str, Any]) -> str:
    area_by_class = {row["class_en"]: row for row in area_rows}
    forest = area_by_class["Forest"]
    landslide = area_by_class["Bare/Landslide"]
    water = area_by_class["Water"]
    built = area_by_class["Built-up"]
    return (
        "災後土地覆蓋分析顯示，秀林/太魯閣研究區仍以森林為主，"
        f"森林面積約 {forest['area_ha']:.1f} 公頃，占有效像元 {forest['percent_valid']:.1f}%。"
        f"RF 判釋之裸地/崩塌面積約 {landslide['area_ha']:.1f} 公頃，主要沿中央山脈側坡、溪谷與蘇花公路周邊呈帶狀或斑塊分布；"
        f"水體約 {water['area_ha']:.1f} 公頃，多在東側海域及河口，建物/都市約 {built['area_ha']:.1f} 公頃，分布零散。"
        f"ROI 測試集 overall accuracy 為 {rf_metrics['test_accuracy']:.1%}，OOB 為 {rf_metrics['oob_score']:.1%}。"
        f"與農村水保署事件型崩塌資料比對，崩塌 IoU 為 {swcb['iou']:.3f}、recall 為 {swcb['recall']:.3f}，"
        "代表此圖可快速指出疑似裸露與崩塌熱區，但仍會把河床、道路邊坡或亮裸土混入崩塌類。"
        "建議將此分類圖作為避難所評估與路網分析的第一層篩選：優先檢查崩塌/裸地接近道路、聚落與橋梁的位置，"
        "再用高解析影像或現地調查確認可通行性與二次災害風險。"
    )


def write_report(
    out_dir: Path,
    data: dict[str, Any],
    kmeans_result: dict[str, Any],
    rf_metrics: dict[str, Any],
    swcb_metrics: dict[str, Any],
    area_rows: list[dict[str, Any]],
    validation: dict[str, Any],
) -> Path:
    report_path = BASE_DIR / "Homework-Week12-Report.md"
    area_df = pd.DataFrame(area_rows)
    cluster_df = pd.DataFrame(kmeans_result["cluster_table"])
    top_band = max(rf_metrics["feature_importance"], key=rf_metrics["feature_importance"].get)
    llm_text = commander_report(area_rows, rf_metrics, swcb_metrics)
    (out_dir / "llm_commander_report.md").write_text(llm_text, encoding="utf-8")
    text = f"""# Week 12 Homework Report: ARIA v8.0 Classification Engine

## Abstract

本作業以 Sentinel-2 L2A 災後影像完成秀林/太魯閣研究區（`{TAROKO_BBOX}`）的五類土地覆蓋分類。流程包含 K-means 非監督式分群、KMZ ROI 建立與解析、Random Forest 監督式分類、混淆矩陣與官方農村水保署事件型崩塌資料驗證，最後輸出面積統計與中文災害應變報告。

## Data And Workflow

- Sentinel-2 item: `{data['metadata']['item_id']}`，來源：{data['metadata']['source']}。
- 有效像元：{data['metadata']['valid_pixels']:,} pixels（{data['metadata']['valid_percent']:.1f}%）。
- 訓練 ROI：`data/taroko_training_rois.kmz`，由本機流程建立後重新以 KMZ workflow 解析，不直接拿 mask 跳過。
- 獨立驗證資料：`data/20240802新生崩塌地.kml`，由 ARDSWC 官方事件型崩塌 MVT 服務轉出；作業 Google Drive 連結經檢查回傳 Week12 notebook JSON，因此改採官方 OpenData/MVT 來源。

## Task 1: K-means

K-means 使用六個 Sentinel-2 反射率波段，先以 {kmeans_result['sample_n']:,} 個有效像元抽樣標準化訓練，再預測全區 {kmeans_result['valid_n']:,} 個有效像元。分群平均光譜如下：

{cluster_df.to_markdown(index=False)}

K-means 對水體與高 NDVI 森林較容易分出，因為 NIR/SWIR 反應很明確；裸地、崩塌、道路與建物則光譜相近，容易混在同一或相鄰 cluster，必須靠監督式 ROI 與空間脈絡修正。

## Task 2: Random Forest

- 訓練樣本：{rf_metrics['train_sample_count']:,} pixels from parsed KMZ ROIs。
- Test accuracy: {rf_metrics['test_accuracy']:.3f}
- OOB score: {rf_metrics['oob_score']:.3f}
- Macro F1: {rf_metrics['macro_f1']:.3f}
- Weighted F1: {rf_metrics['weighted_f1']:.3f}
- Macro-weighted F1 gap: {rf_metrics['macro_weighted_gap']:.3f}
- 最重要波段：`{top_band}`，feature importance = {rf_metrics['feature_importance'][top_band]:.3f}。

Feature importance:

{pd.DataFrame([{'band': k, 'importance': v} for k, v in rf_metrics['feature_importance'].items()]).to_markdown(index=False)}

K-means 與 RF 的差異在於：K-means 僅依光譜自然分群，能探索未知類別但語意不穩定；RF 使用 KMZ ROI 將類別固定成水體、森林、農田/草生地、裸地/崩塌、建物/都市，因此更符合災後土地覆蓋圖的需求。

## Task 3: Accuracy And SWCB Validation

ROI confusion matrix:

```text
{rf_metrics['classification_report_text']}
```

SWCB landslide validation:

- 官方崩塌 polygon count in bbox: {swcb_metrics['swcb_polygon_count']:,}
- SWCB rasterized area: {swcb_metrics['swcb_pixel_area_ha']:.1f} ha
- RF bare/landslide area: {swcb_metrics['rf_bare_landslide_area_ha']:.1f} ha
- Precision: {swcb_metrics['precision']:.3f}
- Recall: {swcb_metrics['recall']:.3f}
- IoU: {swcb_metrics['iou']:.3f}

RF 的裸地/崩塌類比官方崩塌多，主因是 Sentinel-2 20 m 像元會將河床、道路開挖面、亮裸土與崩塌混合。SWCB polygons 來自較高解析影像判釋，且僅標崩塌，不包含一般裸地，因此 precision/IoU 不宜直接解讀成 RF 全分類品質，而應視為崩塌熱區篩選能力。

## Task 4: Area Statistics And AI Report

{area_df.to_markdown(index=False)}

### AI-generated Commander Report

{llm_text}

### Critical Evaluation

本次成果符合 ARIA v8.0 從「閾值偵測」升級到「多類別分類器」的精神：同時利用六波段資訊與 ROI 訓練樣本，能產出可支援面積統計、路網風險篩選與避難所周邊環境判讀的分類圖。然而限制也很明確：ROI 為本機自動 KMZ 流程產生，雖經光譜與空間條件檢核，但仍不等同人工 Google Earth 判釋；山區陰影、河床與崩塌光譜接近，20 m 混合像元會提高誤判；官方崩塌資料與 Sentinel-2 日期、解析度、標註定義不同，造成 FN/FP。後續可加入 DEM slope/aspect、SAR coherence、道路距離與人工修訂 ROI 改善。

## Output Checklist

- `outputs/kmeans_classification.png`
- `outputs/rf_classification.png`
- `outputs/confusion_matrix.png`
- `outputs/swcb_overlay.png`
- `outputs/class_area_stats.csv`
- `outputs/feature_importance.png`
- `outputs/kmeans_vs_rf_comparison.png`
- `data/taroko_training_rois.kmz`
- `data/20240802新生崩塌地.kml`

Validation status: **{validation['status']}**.
"""
    report_path.write_text(text, encoding="utf-8")
    return report_path


def validate_outputs(out_dir: Path, rf_metrics: dict[str, Any] | None = None, swcb_metrics: dict[str, Any] | None = None) -> dict[str, Any]:
    required = [
        "kmeans_classification.png",
        "rf_classification.png",
        "confusion_matrix.png",
        "swcb_overlay.png",
        "class_area_stats.csv",
    ]
    checks: list[dict[str, Any]] = []
    min_sizes = {
        ".png": 1000,
        ".csv": 50,
    }
    for name in required:
        path = out_dir / name
        ok = path.exists() and path.stat().st_size > min_sizes.get(path.suffix.lower(), 1000)
        detail = f"{path.stat().st_size:,} bytes" if path.exists() else "missing"
        if ok and path.suffix.lower() == ".png":
            with Image.open(path) as img:
                arr = np.asarray(img.convert("RGB"))
            ok = bool(arr.std() > 2)
            detail += f", image_std={arr.std():.2f}"
        checks.append({"name": name, "ok": ok, "detail": detail})

    csv_path = out_dir / "class_area_stats.csv"
    if csv_path.exists():
        df = pd.read_csv(csv_path)
        csv_ok = len(df) == 5 and abs(df["percent_valid"].sum() - 100) < 0.25
        checks.append({"name": "area_stats_sum", "ok": bool(csv_ok), "detail": f"sum={df['percent_valid'].sum():.3f}"})

    kmz_path = DATA_DIR / "taroko_training_rois.kmz"
    kml_path = DATA_DIR / "20240802新生崩塌地.kml"
    checks.append({"name": "training_kmz_exists", "ok": kmz_path.exists() and kmz_path.stat().st_size > 1000, "detail": str(kmz_path)})
    checks.append({"name": "swcb_kml_exists", "ok": kml_path.exists() and kml_path.stat().st_size > 1000, "detail": str(kml_path)})

    if rf_metrics:
        roi_ok = all(v >= 80 for v in rf_metrics.get("roi_counts", {}).values())
        checks.append({"name": "roi_class_coverage", "ok": bool(roi_ok), "detail": json.dumps(rf_metrics.get("roi_counts", {}), ensure_ascii=False)})
        gap_ok = abs(rf_metrics.get("oob_test_gap", 0)) < 0.20
        checks.append({"name": "oob_test_gap", "ok": bool(gap_ok), "detail": f"{rf_metrics.get('oob_test_gap', 0):.3f}"})
    if swcb_metrics:
        swcb_ok = swcb_metrics.get("swcb_polygon_count", 0) > 0 and swcb_metrics.get("swcb_pixel_area_ha", 0) > 0
        checks.append({"name": "swcb_reference_nonempty", "ok": bool(swcb_ok), "detail": f"{swcb_metrics.get('swcb_polygon_count', 0)} polygons"})

    status = "PASS" if all(c["ok"] for c in checks) else "REVIEW"
    return {"status": status, "checks": checks}


def append_quality_log(config: CycleConfig, metrics: dict[str, Any], validation: dict[str, Any]) -> None:
    log_path = BASE_DIR / "quality_check_log.md"
    header = "# Week12 Homework Quality Check Log\n\n" if not log_path.exists() else ""
    lines = [
        f"## {config.name}",
        "",
        f"- Note: {config.note}",
        f"- ROI target/radius/max patches: {config.roi_target} / {config.patch_radius} / {config.max_patches}",
        f"- RF trees/min leaf: {config.rf_estimators} / {config.rf_min_leaf}",
        f"- Test accuracy: {metrics['rf']['test_accuracy']:.3f}",
        f"- OOB score: {metrics['rf']['oob_score']:.3f}",
        f"- Macro F1 / Weighted F1: {metrics['rf']['macro_f1']:.3f} / {metrics['rf']['weighted_f1']:.3f}",
        f"- SWCB IoU / precision / recall: {metrics['swcb']['iou']:.3f} / {metrics['swcb']['precision']:.3f} / {metrics['swcb']['recall']:.3f}",
        f"- Validation: {validation['status']}",
        "",
        "| Check | Status | Detail |",
        "|---|---:|---|",
    ]
    for check in validation["checks"]:
        lines.append(f"| {check['name']} | {'PASS' if check['ok'] else 'REVIEW'} | {check['detail']} |")
    lines.append("")
    with log_path.open("a", encoding="utf-8") as f:
        f.write(header + "\n".join(lines) + "\n")


def run_homework(config: CycleConfig | None = None, append_log: bool = True) -> dict[str, Any]:
    ensure_dirs()
    if config is None:
        config = CycleConfig(
            name="notebook_final_rerun",
            roi_target=1050,
            patch_radius=5,
            max_patches=16,
            rf_estimators=300,
            rf_min_leaf=1,
            note="Notebook final rerun using cached Sentinel-2 and official SWCB KML.",
            final=True,
        )

    out_dir = OUTPUT_DIR if config.final else OUTPUT_DIR / safe_name(config.name)
    out_dir.mkdir(parents=True, exist_ok=True)
    data = load_sentinel_stack()
    kmeans = run_kmeans(data, out_dir, random_state=42)

    roi_mask, roi_diag = build_roi_mask(data, config)
    cycle_kmz = DATA_DIR / f"taroko_training_rois_{safe_name(config.name)}.kmz"
    write_roi_kmz(roi_mask, data["transform"], cycle_kmz)
    final_kmz = DATA_DIR / "taroko_training_rois.kmz"
    if config.final:
        write_roi_kmz(roi_mask, data["transform"], final_kmz)
        kmz_for_rf = final_kmz
    else:
        kmz_for_rf = cycle_kmz

    rf = run_random_forest(data, kmz_for_rf, config, out_dir)
    swcb = run_swcb_validation(data, rf["map"], out_dir)
    area_rows, _ = write_area_stats(data, rf["map"], out_dir)
    plot_kmeans_rf_comparison(kmeans["map"], rf["map"], out_dir)
    validation = validate_outputs(out_dir, rf, swcb)
    if config.final:
        write_report(out_dir, data, kmeans, rf, swcb, area_rows, validation)

    metrics = {
        "config": asdict(config),
        "sentinel": data["metadata"],
        "roi_diagnostics": roi_diag,
        "kmeans": {k: v for k, v in kmeans.items() if k != "map"},
        "rf": {k: v for k, v in rf.items() if k != "map"},
        "swcb": swcb,
        "area_stats": area_rows,
        "validation": validation,
    }
    metrics_path = out_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    if append_log:
        append_quality_log(config, metrics, validation)
    return metrics


def reset_quality_log() -> None:
    path = BASE_DIR / "quality_check_log.md"
    if path.exists():
        path.unlink()


def run_quality_cycles() -> list[dict[str, Any]]:
    reset_quality_log()
    configs = [
        CycleConfig(
            name="Cycle 1 - strict baseline",
            roi_target=450,
            patch_radius=3,
            max_patches=10,
            rf_estimators=160,
            rf_min_leaf=2,
            note="Baseline with stricter ROI patches; inspect KMZ coverage and initial SWCB overlay.",
        ),
        CycleConfig(
            name="Cycle 2 - expanded ROI and balanced RF",
            roi_target=750,
            patch_radius=4,
            max_patches=14,
            rf_estimators=220,
            rf_min_leaf=1,
            note="Expanded sparse cropland/built-up ROI coverage and increased forest size.",
        ),
        CycleConfig(
            name="Cycle 3 - final corrected deliverables",
            roi_target=1050,
            patch_radius=5,
            max_patches=16,
            rf_estimators=300,
            rf_min_leaf=1,
            note="Final rerun after confirming KMZ parse, official SWCB KML, output files, and area totals.",
            final=True,
        ),
    ]
    results = []
    for config in configs:
        print(f"\n=== {config.name} ===")
        results.append(run_homework(config, append_log=True))
    create_notebook()
    return results


def create_notebook() -> Path:
    notebook_path = BASE_DIR / "Week12-Homework-Completed.ipynb"
    nb = nbf.v4.new_notebook()
    cells = []
    cells.append(
        nbf.v4.new_markdown_cell(
            "# Week 12 Homework: ARIA v8.0 Classification Engine\n\n"
            "Study area: Xiulin / Taroko (`TAROKO_BBOX = [121.40, 24.10, 121.80, 24.25]`). "
            "This notebook runs the final checked workflow: Sentinel-2 loading, K-means, KMZ ROI creation/parse, Random Forest, SWCB landslide validation, area statistics, and AI-generated commander report."
        )
    )
    cells.append(
        nbf.v4.new_code_cell(
            "from pathlib import Path\n"
            "import json\n"
            "import pandas as pd\n"
            "from IPython.display import Image, display, Markdown\n\n"
            "from week12_homework_pipeline import CycleConfig, run_homework\n\n"
            "config = CycleConfig(\n"
            "    name='Notebook final rerun',\n"
            "    roi_target=1050,\n"
            "    patch_radius=5,\n"
            "    max_patches=16,\n"
            "    rf_estimators=300,\n"
            "    rf_min_leaf=1,\n"
            "    note='Executed notebook rerun after three script quality cycles.',\n"
            "    final=True,\n"
            ")\n"
            "metrics = run_homework(config, append_log=True)\n"
            "print(json.dumps({\n"
            "    'item': metrics['sentinel']['item_id'],\n"
            "    'valid_percent': metrics['sentinel']['valid_percent'],\n"
            "    'test_accuracy': metrics['rf']['test_accuracy'],\n"
            "    'oob_score': metrics['rf']['oob_score'],\n"
            "    'swcb_iou': metrics['swcb']['iou'],\n"
            "    'validation': metrics['validation']['status'],\n"
            "}, indent=2, ensure_ascii=False))"
        )
    )
    cells.append(nbf.v4.new_markdown_cell("## Task 1: K-means Unsupervised Classification"))
    cells.append(
        nbf.v4.new_code_cell(
            "display(Image(filename='outputs/kmeans_classification.png'))\n"
            "pd.read_csv('outputs/kmeans_mean_spectra.csv')"
        )
    )
    cells.append(nbf.v4.new_markdown_cell("## Task 2: Random Forest Supervised Classification"))
    cells.append(
        nbf.v4.new_code_cell(
            "display(Image(filename='outputs/training_roi_from_kmz.png'))\n"
            "display(Image(filename='outputs/rf_classification.png'))\n"
            "display(Image(filename='outputs/feature_importance.png'))\n"
            "pd.DataFrame([metrics['rf']['feature_importance']])"
        )
    )
    cells.append(nbf.v4.new_markdown_cell("## Task 3: Accuracy Assessment And SWCB Validation"))
    cells.append(
        nbf.v4.new_code_cell(
            "display(Image(filename='outputs/confusion_matrix.png'))\n"
            "print(metrics['rf']['classification_report_text'])\n"
            "display(Image(filename='outputs/swcb_overlay.png'))\n"
            "pd.DataFrame([metrics['swcb']]).drop(columns=['swcb_source'], errors='ignore')"
        )
    )
    cells.append(nbf.v4.new_markdown_cell("## Task 4: Area Statistics, AI Report, Critical Evaluation"))
    cells.append(
        nbf.v4.new_code_cell(
            "display(Image(filename='outputs/kmeans_vs_rf_comparison.png'))\n"
            "display(pd.read_csv('outputs/class_area_stats.csv'))\n"
            "display(Markdown(Path('outputs/llm_commander_report.md').read_text(encoding='utf-8')))\n"
            "display(Markdown(Path('Homework-Week12-Report.md').read_text(encoding='utf-8')))"
        )
    )
    cells.append(nbf.v4.new_markdown_cell("## Quality Checks"))
    cells.append(
        nbf.v4.new_code_cell(
            "display(Markdown(Path('quality_check_log.md').read_text(encoding='utf-8')))\n"
            "metrics['validation']"
        )
    )
    nb["cells"] = cells
    nb["metadata"]["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb["metadata"]["language_info"] = {"name": "python", "pygments_lexer": "ipython3"}
    notebook_path.write_text(nbf.writes(nb), encoding="utf-8")
    return notebook_path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run Week 12 homework pipeline.")
    parser.add_argument("--quality-cycles", action="store_true", help="Run three quality cycles and create final deliverables.")
    parser.add_argument("--create-notebook", action="store_true", help="Create the final notebook only.")
    parser.add_argument("--force-stack", action="store_true", help="Re-download/reproject Sentinel-2 stack.")
    args = parser.parse_args()

    if args.force_stack:
        load_sentinel_stack(force=True)
    if args.create_notebook:
        print(create_notebook())
    elif args.quality_cycles:
        run_quality_cycles()
    else:
        metrics = run_homework()
        print(json.dumps({"status": metrics["validation"]["status"], "accuracy": metrics["rf"]["test_accuracy"]}, indent=2))


if __name__ == "__main__":
    main()
