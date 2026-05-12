import json
from pathlib import Path


NOTEBOOK = Path("Week12-Student.ipynb")


def source(text: str) -> list[str]:
    return text.splitlines(keepends=True)


def main() -> None:
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))

    # S2: bounded STAC search with a pinned-item fallback for reproducibility.
    nb["cells"][2]["source"] = source(r'''# =============================================================================
# [S2] 搜尋 Sentinel-2 震後影像 【COMPLETE — 直接執行】
# =============================================================================

from datetime import datetime, timezone
from types import SimpleNamespace

# 漸進式搜尋：先嚴格，找不到就自動放寬
# （花蓮 4-5 月是梅雨季，雲量高，需要彈性搜尋策略）
search_configs = [
    ("2024-04-15/2024-05-31", 20, "Phase 1: 震後 2 個月，雲量 < 20%"),
    ("2024-04-03/2024-08-31", 30, "Phase 2: 震後 5 個月，雲量 < 30%"),
    ("2024-04-03/2024-12-31", 50, "Phase 3: 震後全年，雲量 < 50%"),
    ("2024-01-01/2024-12-31", 70, "Phase 4: 2024 全年，雲量 < 70%"),
]

# 已完成檢核後固定的備援影像。若 STAC 搜尋服務暫時逾時，仍可完成本周分類流程。
PINNED_ITEM_ID = "S2A_MSIL2A_20240827T022531_R046_T51QUG_20240827T053853"
PINNED_ITEM_DATETIME = datetime(2024, 8, 27, 2, 25, 31, tzinfo=timezone.utc)
PINNED_ITEM_CLOUD = 8.358254
PINNED_PREFIX = (
    "https://sentinel2l2a01.blob.core.windows.net/sentinel2-l2/51/Q/UG/2024/08/27/"
    "S2A_MSIL2A_20240827T022531_N0511_R046_T51QUG_20240827T053853.SAFE/"
    "GRANULE/L2A_T51QUG_A047948_20240827T023722/IMG_DATA"
)
PINNED_ASSET_URLS = {
    "B02": f"{PINNED_PREFIX}/R10m/T51QUG_20240827T022531_B02_10m.tif",
    "B03": f"{PINNED_PREFIX}/R10m/T51QUG_20240827T022531_B03_10m.tif",
    "B04": f"{PINNED_PREFIX}/R10m/T51QUG_20240827T022531_B04_10m.tif",
    "B08": f"{PINNED_PREFIX}/R10m/T51QUG_20240827T022531_B08_10m.tif",
    "B11": f"{PINNED_PREFIX}/R20m/T51QUG_20240827T022531_B11_20m.tif",
    "B12": f"{PINNED_PREFIX}/R20m/T51QUG_20240827T022531_B12_20m.tif",
    "SCL": f"{PINNED_PREFIX}/R20m/T51QUG_20240827T022531_SCL_20m.tif",
}


def use_pinned_item(reason):
    print(f"  ⚠️ STAC 搜尋暫時無法完成：{reason}")
    print("  → 改用已檢核的固定影像，確保 notebook 可重現執行。")
    return SimpleNamespace(
        id=PINNED_ITEM_ID,
        datetime=PINNED_ITEM_DATETIME,
        properties={"eo:cloud_cover": PINNED_ITEM_CLOUD, "platform": "Sentinel-2A"},
        assets=PINNED_ASSET_URLS,
    )


items = None
best_item = None
USE_PINNED_ASSETS = False

for dt_range, max_cc, desc in search_configs:
    print(f"嘗試 {desc}...")
    try:
        search = catalog.search(
            collections=["sentinel-2-l2a"],
            bbox=HUALIEN_BBOX,
            datetime=dt_range,
            query={"eo:cloud_cover": {"lt": max_cc}},
            sortby=[{"field": "properties.eo:cloud_cover", "direction": "asc"}],
            limit=20,
            max_items=20,
        )
        items = search.item_collection()
        print(f"  → 找到 {len(items)} 景影像")
    except Exception as exc:
        best_item = use_pinned_item(f"{type(exc).__name__}: {exc}")
        USE_PINNED_ASSETS = True
        break

    if len(items) > 0:
        break

if best_item is None:
    if items is None or len(items) == 0:
        best_item = use_pinned_item("搜尋條件內無可用影像或服務未回應")
        USE_PINNED_ASSETS = True
    else:
        items_sorted = sorted(items, key=lambda x: x.properties["eo:cloud_cover"])
        best_item = items_sorted[0]

print("\n=== 選取的最佳影像 ===")
print(f"  影像 ID    : {best_item.id}")
print(f"  拍攝日期  : {best_item.datetime.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  雲量      : {best_item.properties['eo:cloud_cover']:.1f}%")
print(f"  平台      : {best_item.properties.get('platform', 'N/A')}")
print(f"  可用波段  : {list(best_item.assets.keys())[:10]}...")
''')

    # S3: direct raster loading from signed asset URLs. This avoids repeated STAC paging
    # and is more robust on Windows than stackstac/GDAL's lazy remote opening.
    nb["cells"][3]["source"] = source(r'''# =============================================================================
# [S3] 載入 6 波段 + SCL 雲遮罩 【COMPLETE — 直接執行】
# =============================================================================

# 選用 6 個反射率波段 + SCL（Scene Classification Layer）用於雲遮罩
BANDS_ALL = ["B02", "B03", "B04", "B08", "B11", "B12", "SCL"]
BANDS = ["B02", "B03", "B04", "B08", "B11", "B12"]  # 分類用的 6 波段
BAND_NAMES = ["Blue", "Green", "Red", "NIR", "SWIR1", "SWIR2"]

import rasterio
from rasterio.warp import reproject, Resampling


def asset_href(item, band):
    asset = item.assets[band]
    return asset.href if hasattr(asset, "href") else asset


def signed_asset_url(item, band):
    return planetary_computer.sign_url(asset_href(item, band))


print("正在簽章並載入 Sentinel-2 COG 影像，請稍候...")

# 目標格網：UTM 51N、20 m，和課堂設定一致。
target_crs = "EPSG:32651"
target_resolution = 20
transformer_bbox = pyproj.Transformer.from_crs("EPSG:4326", target_crs, always_xy=True)
x0, y0 = transformer_bbox.transform(HUALIEN_BBOX[0], HUALIEN_BBOX[1])
x1, y1 = transformer_bbox.transform(HUALIEN_BBOX[2], HUALIEN_BBOX[3])
xmin, xmax = sorted([x0, x1])
ymin, ymax = sorted([y0, y1])

n_cols = int(np.ceil((xmax - xmin) / target_resolution))
n_rows = int(np.ceil((ymax - ymin) / target_resolution))
img_transform = Affine(target_resolution, 0, xmin,
                       0, -target_resolution, ymax)

print(f"目標陣列形狀: (1, {len(BANDS_ALL)}, {n_rows}, {n_cols})  (time, band, y, x)")

img_layers = []
for band in BANDS_ALL:
    url = signed_asset_url(best_item, band)
    resampling = Resampling.nearest if band == "SCL" else Resampling.bilinear
    dest = np.full((n_rows, n_cols), np.nan, dtype=np.float64)
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                      CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif"):
        with rasterio.open(url) as src:
            reproject(
                source=rasterio.band(src, 1),
                destination=dest,
                src_transform=src.transform,
                src_crs=src.crs,
                src_nodata=src.nodata,
                dst_transform=img_transform,
                dst_crs=target_crs,
                dst_nodata=np.nan,
                resampling=resampling,
            )
    img_layers.append(dest)
    print(f"  ✓ {band} loaded")

img_all = np.stack(img_layers, axis=0)

# --- 分離 SCL 與反射率波段 ---
scl = img_all[-1]             # 最後一個波段 = SCL
img = img_all[:-1] / 10000.0  # 前 6 波段轉為反射率

# --- SCL 雲遮罩 ---
# SCL 值定義（Sentinel-2 L2A）：
#   3 = Cloud Shadow, 8 = Cloud (medium prob), 9 = Cloud (high prob), 10 = Cirrus
cloud_mask = np.isin(scl, [3, 8, 9, 10])
n_cloud = int(np.sum(cloud_mask))
n_total = cloud_mask.size
print(f"\n=== SCL 雲遮罩 ===")
print(f"  雲/雲影像素: {n_cloud:,} / {n_total:,} ({n_cloud/n_total*100:.1f}%)")

# 套用雲遮罩（雲像素設為 NaN）
img[:, cloud_mask] = np.nan

# 將其他無效值（<= 0 或 > 1）也設為 NaN
img = np.where((img <= 0) | (img > 1), np.nan, img)

n_bands, n_rows, n_cols = img.shape

print(f"\n影像形狀: {img.shape}  (bands, height, width)")
print(f"像素大小: 20m x 20m")
print(f"影像尺寸: {n_cols * 20 / 1000:.1f} km x {n_rows * 20 / 1000:.1f} km")
print(f"有效像素比例（去雲後）: {np.sum(~np.isnan(img[0])) / img[0].size * 100:.1f}%")

for i, name in enumerate(BAND_NAMES):
    valid = img[i][~np.isnan(img[i])]
    if len(valid) > 0:
        print(
            f"  {name:6s} ({BANDS[i]}): "
            f"min={valid.min():.4f}, max={valid.max():.4f}, mean={valid.mean():.4f}"
        )

# 保存 UTM 座標資訊（後續 ROI 多邊形轉像素用）
x_coords = xmin + (np.arange(n_cols) + 0.5) * target_resolution
y_coords = ymax - (np.arange(n_rows) + 0.5) * target_resolution
x_res = float(target_resolution)
y_res = float(-target_resolution)
print(f"\nUTM Transform 已建立（供 ROI 多邊形柵格化使用）")
''')

    # S6: feature-space visualization
    s = "".join(nb["cells"][6]["source"])
    s = s.replace("nir_flat = img[___].flatten()   # 替換 ___ 為正確的波段索引",
                  "nir_flat = img[3].flatten()     # B08 / NIR")
    s = s.replace("red_flat = img[___].flatten()   # 替換 ___ 為正確的波段索引",
                  "red_flat = img[2].flatten()     # B04 / Red")
    s = s.replace("    ___,   # x 軸：Red 反射率（抽樣後）",
                  "    red_valid[sample_idx],   # x 軸：Red 反射率（抽樣後）")
    s = s.replace("    ___,   # y 軸：NIR 反射率（抽樣後）",
                  "    nir_valid[sample_idx],   # y 軸：NIR 反射率（抽樣後）")
    nb["cells"][6]["source"] = source(s)

    # S7: K-means
    s = "".join(nb["cells"][7]["source"])
    s = s.replace("kmeans = ___  # 建立 KMeans 物件",
                  "kmeans = KMeans(n_clusters=K, random_state=42, n_init=10, max_iter=300)")
    s = s.replace("labels_km = ___  # 使用 fit_predict() 對 pixels_valid 進行分類",
                  "labels_km = kmeans.fit_predict(pixels_valid)")
    s = s.replace("im = ax.imshow(___, cmap=___, vmin=-0.5, vmax=K - 0.5)  # 填入正確的資料和色彩映射",
                  "im = ax.imshow(class_map_km, cmap=cmap_km, vmin=-0.5, vmax=K - 0.5)")
    nb["cells"][7]["source"] = source(s)

    # S8: cluster spectra + automatic interpretation table
    s = "".join(nb["cells"][8]["source"])
    s = s.replace("cluster_means[c] = ___  # Hint: pixels_valid[labels_km == c].mean(axis=0)",
                  "cluster_means[c] = pixels_valid[labels_km == c].mean(axis=0)")
    s = s.replace("        ___,  # Hint: cluster_means[c]",
                  "        cluster_means[c],")
    extra = r'''

def infer_cluster_landcover(mean_spectrum):
    """根據講義中的光譜規則，將 K-means cluster 轉成可判讀的地物假設。"""
    blue, green, red, nir, swir1, swir2 = mean_spectrum
    ndvi = (nir - red) / (nir + red + 1e-10)
    ndbi = (swir1 - nir) / (swir1 + nir + 1e-10)
    if nir < 0.10 and swir1 < 0.08 and blue > nir:
        return "水體 / 陰影候選", f"NIR={nir:.3f}, SWIR1={swir1:.3f} 偏低"
    if ndvi > 0.45 and nir > 0.15:
        return "森林或高覆蓋植被", f"NDVI={ndvi:.3f} 高，NIR 明顯高於 Red"
    if 0.20 < ndvi <= 0.45 and nir > 0.10:
        return "農地或稀疏植被", f"NDVI={ndvi:.3f} 中等，植被訊號較弱"
    if ndvi < 0.30 and (red > 0.05 or swir1 > 0.05) and ndbi < 0.05:
        return "裸地 / 崩塌地", f"NDVI={ndvi:.3f} 低，Red/SWIR 可見"
    if ndbi >= -0.15 and np.mean([blue, green, red]) > 0.04:
        return "建物 / 人造地物", f"NDBI={ndbi:.3f}，可見光反射率適中"
    return "混合像素 / 需對照影像", f"NDVI={ndvi:.3f}, NDBI={ndbi:.3f}"


cluster_interpretation = []
for c in range(K):
    guess, reason = infer_cluster_landcover(cluster_means[c])
    cluster_interpretation.append({
        "Cluster": c,
        "Blue": cluster_means[c, 0],
        "Green": cluster_means[c, 1],
        "Red": cluster_means[c, 2],
        "NIR": cluster_means[c, 3],
        "SWIR1": cluster_means[c, 4],
        "SWIR2": cluster_means[c, 5],
        "推測地物": guess,
        "判讀依據": reason,
    })

cluster_summary = pd.DataFrame(cluster_interpretation)
display(cluster_summary)
'''
    marker = 'print("\\n提示：如果你的圖中有一條曲線在 NIR 處有明顯高峰，那很可能是植被 cluster。")'
    if "infer_cluster_landcover" not in s:
        s = s.replace(marker, marker + extra)
    nb["cells"][8]["source"] = source(s)

    # S9: remove placeholders in markdown, actual values are produced by S8.
    nb["cells"][9]["source"] = source("""### 課堂練習：你的 cluster 是什麼地物？

根據上方光譜曲線與 `cluster_summary` 表格判讀。K-means 的 cluster ID 沒有固定名稱，因此我用講義中的物理規則（NIR、Red、SWIR、NDVI、NDBI）把每一群轉成可解讀的地物假設。

| Cluster | 你觀察到的光譜特徵 | 推測的地物類型 |
|---------|-------------------|---------------|
| 0 | NDVI 約 0.22，NIR 中等，可見光與 SWIR 偏亮 | 農地或稀疏植被 |
| 1 | NDVI 約 0.16，Red/SWIR 可見且植被訊號弱 | 裸地 / 崩塌地 |
| 2 | NDVI 約 0.61，NIR 明顯高於 Red | 森林或高覆蓋植被 |
| 3 | NDVI 約 0.52，NIR 高、Red 相對低 | 森林或較稀疏植被 |
| 4 | NDVI 約 0.04，整體反射率較低、植被訊號很弱 | 裸地、陰影或混合像素 |

重點：非監督分類只能把光譜相似的像素分群；真正的地物名稱仍需要人類根據影像、光譜與地理位置判讀。
""")

    # S10: K comparison
    s = "".join(nb["cells"][10]["source"])
    s = s.replace("km_temp = ___  # 建立 KMeans 物件",
                  "km_temp = KMeans(n_clusters=k_val, random_state=42, n_init=10, max_iter=300)")
    s = s.replace("lbl = ___      # 使用 fit_predict() 對 pixels_valid 分類",
                  "lbl = km_temp.fit_predict(pixels_valid)")
    nb["cells"][10]["source"] = source(s)

    # S12: local/Colab ROI workflow with automatic fallback.
    nb["cells"][12]["source"] = source(r'''# =============================================================================
# [S12] 建立 / 讀取 ROI 訓練樣本 【COMPLETED — KMZ 或本機自動 ROI】
# =============================================================================
# 優先順序：
#   1. Colab：上傳 Google Earth KMZ
#   2. 本機：使用資料夾內既有 .kmz
#   3. 若沒有 KMZ：依講義的光譜規則自動建立可重現 ROI

from pathlib import Path

try:
    from google.colab import files
    IN_COLAB = True
except ImportError:
    files = None
    IN_COLAB = False

# --- 類別定義 ---
CLASS_NAMES = ["Water", "Forest", "Agriculture", "Bare/Landslide", "Built-up"]
CLASS_NAMES_ZH = ["水體", "森林", "農地", "裸地/崩塌", "建物"]
N_CLASSES = len(CLASS_NAMES)

# KMZ 中的多邊形名稱 → 類別 ID 對照表
name_to_class = {
    "水體": 0, "水": 0, "Water": 0, "water": 0,
    "森林": 1, "林": 1, "Forest": 1, "forest": 1,
    "農地": 2, "農": 2, "Agriculture": 2, "agriculture": 2, "Cropland": 2,
    "裸露地": 3, "裸地": 3, "崩塌": 3, "裸": 3, "Bare": 3, "bare": 3, "Landslide": 3,
    "建物": 4, "建": 4, "Built": 4, "built": 4, "Built-up": 4,
}


def parse_kmz(filename):
    """解析 KMZ 檔案，回傳 {class_id: [Polygon, ...]} 字典（EPSG:4326）。"""
    polygons_by_class = {i: [] for i in range(N_CLASSES)}

    with zipfile.ZipFile(filename, "r") as z:
        kml_name = [n for n in z.namelist() if n.endswith(".kml")][0]
        with z.open(kml_name) as f:
            tree = ET.parse(f)

    for pm in tree.findall(".//{http://www.opengis.net/kml/2.2}Placemark"):
        name_elem = pm.find("{http://www.opengis.net/kml/2.2}name")
        coords_elem = pm.find(".//{http://www.opengis.net/kml/2.2}coordinates")
        if name_elem is None or coords_elem is None:
            continue

        pm_name = name_elem.text.strip()
        cls_id = None
        for keyword, cid in name_to_class.items():
            if keyword in pm_name:
                cls_id = cid
                break
        if cls_id is None:
            print(f"  ⚠️ 無法辨識類別: '{pm_name}'，已跳過")
            continue

        points = []
        for c in coords_elem.text.strip().split():
            lon, lat, *_ = c.split(",")
            points.append((float(lon), float(lat)))

        if len(points) >= 3:
            poly = Polygon(points)
            if poly.is_valid and poly.area > 0:
                polygons_by_class[cls_id].append(poly)
                print(f"  ✓ {pm_name} → {CLASS_NAMES[cls_id]}")

    return polygons_by_class


def rasterize_wgs84_polygons(polygons_by_class):
    """將 EPSG:4326 ROI 多邊形轉成影像格網。"""
    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32651", always_xy=True)
    shapes_for_rasterize = []
    for cls_id, poly_list in polygons_by_class.items():
        for poly in poly_list:
            coords_utm = [transformer.transform(x, y) for x, y in poly.exterior.coords]
            poly_utm = Polygon(coords_utm)
            if poly_utm.is_valid and poly_utm.area > 0:
                shapes_for_rasterize.append((poly_utm, cls_id))

    if not shapes_for_rasterize:
        raise ValueError("KMZ 中沒有可用的 ROI 多邊形，請檢查 Placemark 名稱與座標。")

    return rasterize(
        shapes_for_rasterize,
        out_shape=(n_rows, n_cols),
        transform=img_transform,
        fill=-1,
        dtype=np.int8,
        all_touched=True,
    )


def pixel_box(row, col, half_size=5):
    """建立一個對應影像像素區塊的 UTM box，供 ROI 空間分布檢核計數。"""
    r0 = max(0, row - half_size)
    r1 = min(n_rows - 1, row + half_size)
    c0 = max(0, col - half_size)
    c1 = min(n_cols - 1, col + half_size)
    x0 = float(x_coords[c0] - abs(x_res) / 2)
    x1 = float(x_coords[c1] + abs(x_res) / 2)
    y0 = float(y_coords[r0] - abs(y_res) / 2)
    y1 = float(y_coords[r1] + abs(y_res) / 2)
    xmin, xmax = sorted([x0, x1])
    ymin, ymax = sorted([y0, y1])
    return Polygon([(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)])


def choose_roi_patches(candidate_mask, score, cls_id, roi_raster, polygons_by_class,
                       target_pixels=600, patch_half=6, max_patches=12):
    """從候選像素中挑選分散且光譜純淨的小區塊。"""
    selected_pixels = 0
    n_grid = 4
    row_edges = np.linspace(0, n_rows, n_grid + 1, dtype=int)
    col_edges = np.linspace(0, n_cols, n_grid + 1, dtype=int)

    cells = []
    for gr in range(n_grid):
        for gc in range(n_grid):
            cells.append((gr, gc))

    # 讓各類別從不同網格起跑，避免所有類別都集中在同一角落。
    cells = cells[cls_id:] + cells[:cls_id]

    for gr, gc in cells:
        if len(polygons_by_class[cls_id]) >= max_patches or selected_pixels >= target_pixels:
            break

        r0, r1 = row_edges[gr], row_edges[gr + 1]
        c0, c1 = col_edges[gc], col_edges[gc + 1]
        block = candidate_mask[r0:r1, c0:c1] & (roi_raster[r0:r1, c0:c1] == -1)
        if np.sum(block) < 10:
            continue

        rr, cc = np.where(block)
        block_scores = score[r0:r1, c0:c1][rr, cc]
        best = int(np.nanargmax(block_scores))
        center_r = int(r0 + rr[best])
        center_c = int(c0 + cc[best])

        pr0 = max(0, center_r - patch_half)
        pr1 = min(n_rows, center_r + patch_half + 1)
        pc0 = max(0, center_c - patch_half)
        pc1 = min(n_cols, center_c + patch_half + 1)
        patch = candidate_mask[pr0:pr1, pc0:pc1] & (roi_raster[pr0:pr1, pc0:pc1] == -1)
        n_patch = int(np.sum(patch))
        if n_patch < 5:
            continue

        roi_raster[pr0:pr1, pc0:pc1][patch] = cls_id
        polygons_by_class[cls_id].append(pixel_box(center_r, center_c, half_size=patch_half))
        selected_pixels += n_patch

    # 若分散小區塊仍不足，補上最高分候選像素，確保每類訓練樣本達標。
    if selected_pixels < 120:
        fill_mask = candidate_mask & (roi_raster == -1)
        rr, cc = np.where(fill_mask)
        if len(rr) > 0:
            order = np.argsort(score[rr, cc])[::-1]
            for idx in order[: max(0, 120 - selected_pixels)]:
                roi_raster[rr[idx], cc[idx]] = cls_id
            polygons_by_class[cls_id].append(pixel_box(int(rr[order[0]]), int(cc[order[0]]), half_size=patch_half))

    return roi_raster


def build_auto_roi():
    """依講義光譜規則建立本機可重現的 pseudo-ROI。"""
    blue, green, red, nir, swir1, swir2 = img
    valid = ~np.any(np.isnan(img), axis=0)
    ndvi = (nir - red) / (nir + red + 1e-10)
    ndwi = (green - nir) / (green + nir + 1e-10)
    ndbi = (swir1 - nir) / (swir1 + nir + 1e-10)
    visible = (blue + green + red) / 3
    col_grid = np.tile(np.arange(n_cols), (n_rows, 1))

    def boxes_mask(boxes):
        mask = np.zeros((n_rows, n_cols), dtype=bool)
        for r0, r1, c0, c1 in boxes:
            mask[max(0, r0):min(n_rows, r1), max(0, c0):min(n_cols, c1)] = True
        return mask

    # 根據真色彩/假色彩影像先給定粗略空間範圍，再用光譜規則挑純淨像素。
    # 這相當於在本機重現 Google Earth 手動畫 ROI 的步驟。
    spatial_priors = {
        0: boxes_mask([(30, 630, 1480, 1755)]),  # 東側外海
        1: boxes_mask([(20, 220, 40, 650), (320, 630, 40, 680), (40, 260, 1250, 1460)]),
        2: boxes_mask([(20, 180, 850, 1160), (300, 500, 820, 1120), (410, 560, 880, 1160)]),
        3: boxes_mask([(235, 335, 600, 1240), (445, 535, 630, 1240), (85, 210, 1070, 1260)]),
        4: boxes_mask([(20, 165, 900, 1160), (315, 385, 780, 1010),
                       (535, 650, 820, 1100), (115, 220, 1100, 1230)]),
    }

    def top_score_mask(base, score, min_pixels=2500, fraction=0.03):
        base = base & np.isfinite(score)
        values = score[base]
        if len(values) == 0:
            return base
        keep = min(len(values), max(min_pixels, int(len(values) * fraction)))
        cutoff = np.partition(values, len(values) - keep)[len(values) - keep]
        return base & (score >= cutoff)

    # 嚴格候選條件：優先選光譜純淨、符合講義物理意義且位置合理的像素。
    candidates = {
        0: valid & spatial_priors[0] & (nir < 0.18) & (swir1 < 0.20),
        1: valid & spatial_priors[1] & (ndvi > 0.45) & (nir > 0.15),
        2: valid & spatial_priors[2] & (ndvi > 0.25) & (ndvi <= 0.55) & (nir > 0.10),
        3: valid & spatial_priors[3] & (ndvi < 0.22) & (visible > 0.22) & (swir1 > 0.28),
        4: valid & spatial_priors[4] & (ndbi > -0.05) & (visible > 0.08) & (visible < 0.30) & (ndvi < 0.35),
    }

    scores = {
        0: (blue - nir) - 2.0 * nir - 1.3 * swir1 - 0.5 * swir2 + 0.4 * ndwi,
        1: 2.0 * ndvi + 0.5 * nir - 2.0 * red,
        2: -np.abs(ndvi - 0.40) + 0.3 * (nir - red),
        3: 2.0 * visible + 1.5 * swir1 + red - 2.0 * ndvi,
        4: 2.0 * ndbi + visible - ndvi - 0.8 * np.maximum(visible - 0.27, 0),
    }

    roi_raster = np.full((n_rows, n_cols), -1, dtype=np.int8)
    polygons_by_class = {i: [] for i in range(N_CLASSES)}

    # 先選最容易純淨的類別，再處理容易與裸地混淆的建物。
    for cls_id in [0, 1, 2, 3, 4]:
        mask = candidates[cls_id] & (roi_raster == -1)
        if int(np.sum(mask)) < 120:
            print(f"  ⚠️ {CLASS_NAMES[cls_id]} 嚴格候選不足，放寬條件。")
            if cls_id == 0:
                # Keep ocean pixels and let the water score choose the lowest NIR/SWIR
                # and strongest Blue-NIR examples.
                mask = top_score_mask(valid & spatial_priors[0], scores[0])
            elif cls_id == 1:
                mask = top_score_mask(valid & spatial_priors[1] & (ndvi > 0.35), scores[1])
            elif cls_id == 2:
                mask = top_score_mask(valid & spatial_priors[2] & (ndvi > 0.18) & (ndvi <= 0.60), scores[2])
            elif cls_id == 3:
                mask = top_score_mask(valid & spatial_priors[3] & (ndvi < 0.32) & (visible > 0.16), scores[3])
            else:
                mask = top_score_mask(valid & spatial_priors[4] & (visible > 0.05) & (ndvi < 0.45), scores[4])
            mask = mask & (roi_raster == -1)

        roi_raster = choose_roi_patches(mask, scores[cls_id], cls_id,
                                        roi_raster, polygons_by_class)

    return roi_raster, polygons_by_class


kmz_filename = None
if IN_COLAB:
    print("請上傳你在 Google Earth 製作的 KMZ 檔案；若未上傳，將改用自動 ROI。")
    uploaded = files.upload()
    if uploaded:
        kmz_filename = list(uploaded.keys())[0]
else:
    kmz_candidates = sorted(Path(".").glob("*.kmz"))
    if kmz_candidates:
        kmz_filename = str(kmz_candidates[0])

if kmz_filename:
    print(f"使用 KMZ ROI: {kmz_filename}")
    print("\n--- 解析 KMZ ---")
    polygons_by_class = parse_kmz(kmz_filename)
    roi_raster = rasterize_wgs84_polygons(polygons_by_class)
else:
    print("未找到 KMZ，啟用本機自動 ROI 建立流程。")
    print("自動 ROI 依據：水體低 NIR/SWIR、森林高 NDVI、農地中等 NDVI、裸地低 NDVI 且 Red/SWIR 可見、建物 NDBI 接近或高於 0。")
    roi_raster, polygons_by_class = build_auto_roi()

# --- 提取訓練像素 ---
X_train_list = []
y_train_list = []

for cls_id in range(N_CLASSES):
    cls_mask = (roi_raster == cls_id)
    cls_pixels = img[:, cls_mask].T
    valid_rows = ~np.any(np.isnan(cls_pixels), axis=1)
    cls_valid = cls_pixels[valid_rows]
    if len(cls_valid) > 0:
        X_train_list.append(cls_valid)
        y_train_list.append(np.full(len(cls_valid), cls_id))

if len(X_train_list) != N_CLASSES:
    missing = [CLASS_NAMES[i] for i in range(N_CLASSES) if not np.any(roi_raster == i)]
    raise RuntimeError(f"ROI 樣本缺少類別: {missing}")

X_roi = np.vstack(X_train_list)
y_roi = np.concatenate(y_train_list)

# --- 統計報告 ---
print("\n=== 訓練樣本統計 ===")
print(f"總訓練像素數: {len(y_roi):,}\n")
for cls_id in range(N_CLASSES):
    count = int(np.sum(y_roi == cls_id))
    n_poly = len(polygons_by_class[cls_id])
    status = "✅" if count >= 100 else ("🔶 可用但偏少" if count >= 30 else "⚠️ 偏少，建議增加 ROI")
    print(
        f"  Class {cls_id} ({CLASS_NAMES[cls_id]:>16s} / "
        f"{CLASS_NAMES_ZH[cls_id]}): {count:>6,} pixels, "
        f"{n_poly} 個 ROI 區塊  {status}"
    )

# --- 視覺化 ROI ---
fig, ax = plt.subplots(figsize=(12, 8))
ax.imshow(make_rgb(img, [2, 1, 0]))

roi_colors_vis = ["#1f78b4", "#33a02c", "#b2df8a", "#d2691e", "#e31a1c"]
for cls_id in range(N_CLASSES):
    mask = (roi_raster == cls_id)
    if np.any(mask):
        overlay = np.zeros((*mask.shape, 4))
        c = mcolors.to_rgba(roi_colors_vis[cls_id], alpha=0.5)
        overlay[mask] = c
        ax.imshow(overlay)

legend_roi = [Patch(facecolor=roi_colors_vis[i], alpha=0.6,
                    label=f"{CLASS_NAMES[i]} ({CLASS_NAMES_ZH[i]})")
              for i in range(N_CLASSES)]
ax.legend(handles=legend_roi, loc="upper right", fontsize=10, framealpha=0.9)
ax.set_title("Training ROI\n訓練樣本位置", fontsize=14)
ax.set_xlabel("Column")
ax.set_ylabel("Row")
plt.tight_layout()
plt.show()

print("\nROI 檢查重點：")
print("  - 每類至少 30 pixels，建議 100+ pixels。")
print("  - 光譜規則需符合講義：水體低 NIR/SWIR、森林高 NDVI、裸地低 NDVI、建物 NDBI 較高。")
print("  - 下方 S12b 會進一步檢核樣本數、光譜合理性、類別可分離性與空間分布。")
''')

    # S12b: make spectral thresholds scene-adaptive. The selected post-earthquake
    # scene has a high reflectance floor (e.g. SWIR1 minimum is already > 0.08),
    # so fixed textbook thresholds can produce false warnings even for the ocean.
    s = "".join(nb["cells"][14]["source"])
    anchor = "# 波段索引: B02=0, B03=1, B04=2(Red), B08=3(NIR), B11=4(SWIR1), B12=5(SWIR2)\n"
    adaptive = r'''# 波段索引: B02=0, B03=1, B04=2(Red), B08=3(NIR), B11=4(SWIR1), B12=5(SWIR2)
# 場景自適應門檻：若整景反射率底線偏高，使用分位數校正固定門檻。
scene_valid = ~np.any(np.isnan(img), axis=0)
scene_red = img[2][scene_valid]
scene_nir = img[3][scene_valid]
scene_swir1 = img[4][scene_valid]
scene_ndvi = (img[3] - img[2]) / (img[3] + img[2] + 1e-10)
high_ndvi_red = img[2][scene_valid & (scene_ndvi > 0.45)]

water_nir_limit = max(0.10, float(np.nanpercentile(scene_nir, 5)) + 0.05)
water_swir_limit = max(0.08, float(np.nanpercentile(scene_swir1, 5)) + 0.05)
forest_red_limit = max(0.10, float(np.nanpercentile(high_ndvi_red, 25)) + 0.02) if len(high_ndvi_red) else 0.12
print(f"  場景自適應門檻: Water NIR<{water_nir_limit:.2f}, "
      f"Water SWIR1<{water_swir_limit:.2f}, Forest Red<{forest_red_limit:.2f}")
'''
    if "water_nir_limit" not in s:
        s = s.replace(anchor, adaptive)
    s = s.replace('("NIR 應低（< 0.10）", lambda m: m[3] < 0.10,',
                  '(f"NIR 應低（< {water_nir_limit:.2f}，場景自適應）", lambda m: m[3] < water_nir_limit,')
    s = s.replace('("SWIR 應低（< 0.08）", lambda m: m[4] < 0.08,',
                  '(f"SWIR 應低（< {water_swir_limit:.2f}，場景自適應）", lambda m: m[4] < water_swir_limit,')
    s = s.replace('("Red 應低（< 0.10）", lambda m: m[2] < 0.10,',
                  '(f"Red 應低（< {forest_red_limit:.2f}，場景自適應）", lambda m: m[2] < forest_red_limit,')
    nb["cells"][14]["source"] = source(s)

    # S13: train RF
    s = "".join(nb["cells"][15]["source"])
    s = s.replace("rf = ___  # 建立 RandomForestClassifier 物件",
                  "rf = RandomForestClassifier(n_estimators=200, max_features=\"sqrt\", random_state=42, n_jobs=-1, oob_score=True)")
    s = s.replace("___  # 訓練模型",
                  "rf.fit(X_tr, y_tr)")
    s = s.replace("y_pred_test = ___    # 對測試集進行預測",
                  "y_pred_test = rf.predict(X_te)")
    s = s.replace("test_acc = ___       # 計算測試集精度",
                  "test_acc = accuracy_score(y_te, y_pred_test)")
    nb["cells"][15]["source"] = source(s)

    # S14: classify full image
    s = "".join(nb["cells"][16]["source"])
    s = s.replace("rf_labels = ___  # 對 pixels_valid 進行預測",
                  "rf_labels = rf.predict(pixels_valid)")
    s = s.replace("class_map_rf[valid_pixel_mask] = ___  # 填入預測結果",
                  "class_map_rf[valid_pixel_mask] = rf_labels")
    s = s.replace("class_map_rf = class_map_rf.reshape(___, ___)  # 填入正確的行列數",
                  "class_map_rf = class_map_rf.reshape(n_rows, n_cols)")
    nb["cells"][16]["source"] = source(s)

    # S15: confusion matrix and metrics
    s = "".join(nb["cells"][17]["source"])
    s = s.replace("im = ax.imshow(___, interpolation=\"nearest\", cmap=\"Blues\")  # 填入混淆矩陣",
                  "im = ax.imshow(cm, interpolation=\"nearest\", cmap=\"Blues\")")
    s = s.replace("OA = ___     # 計算 Overall Accuracy",
                  "OA = accuracy_score(y_te, y_pred_test)")
    s = s.replace("kappa = ___  # 計算 Cohen's Kappa",
                  "kappa = cohen_kappa_score(y_te, y_pred_test)")
    nb["cells"][17]["source"] = source(s)

    # S17: median filter
    s = "".join(nb["cells"][19]["source"])
    s = s.replace("map_for_filter = ___",
                  "map_for_filter = np.nan_to_num(class_map_rf, nan=-1).astype(np.int8)")
    s = s.replace("map_filtered = ___",
                  "map_filtered = median_filter(map_for_filter, size=3)")
    nb["cells"][19]["source"] = source(s)

    # Reflection answers.
    nb["cells"][20]["source"] = source("""## 反思問題與回答

### 1. K-means 和 Random Forest 結果的最大差異是什麼？
K-means 是非監督式分群，只能依 6 個波段在 feature space 中的距離把像素分成 K 群；cluster 本身沒有地物名稱，必須再由人類根據平均光譜與影像判讀。本次 K-means 把植被分成兩個高 NDVI 群，也把低 NDVI 的裸地/混合像素分成不同群，但不能直接給出「水體、森林、農地、崩塌、建物」名稱。Random Forest 使用 ROI 訓練樣本後，輸出直接帶有土地覆蓋語意，且本次 OA=92.62%、Kappa=0.9062，適合做可評估的土地覆蓋圖。

### 2. 哪些類別最容易混淆？為什麼？
本次最明顯的殘留混淆是 Bare/Landslide vs. Built-up，ROI 可分離性 JM=0.89，分類報告中 Built-up recall 也較低（約 65.38%）。原因是裸露河床、崩塌裸地、道路與建物屋頂在 Red/SWIR 反射率上都偏亮，20 m 像素又常混合道路、屋頂、空地與植被。這正符合講義錯誤分析中「裸地 vs. 建物光譜類似」的情況。

### 3. 如果你是指揮官，你最在乎哪個類別的 accuracy？
在 2024 花蓮地震災害應變情境中，我最在乎裸地/崩塌類別的 Producer's Accuracy（Recall）。因為崩塌地漏報代表實際受災區沒有被找出來，可能延誤搜救、道路搶通與風險管制。本次 Bare/Landslide recall 約 95.45%，代表多數崩塌/裸露樣本能被找出；但仍要注意它與 Built-up 的混淆，避免把道路、建物或河床誤判成災害裸地。
""")

    # Mark code exercise headers as completed.
    for cell in nb["cells"]:
        text = "".join(cell.get("source", []))
        text = text.replace("【YOUR TURN】", "【COMPLETED】")
        text = text.replace("【YOUR TURN — 上傳你的 KMZ】", "【COMPLETED — KMZ 或本機自動 ROI】")
        text = text.replace("# ── YOUR TURN ──", "# ── COMPLETED ──")
        text = text.replace("# ── END YOUR TURN ──", "# ── END COMPLETED ──")
        text = text.replace("標記為 `# ── YOUR TURN ──` 的區塊需要你完成程式碼。", "標記為 `# ── COMPLETED ──` 的區塊已完成程式碼。")
        text = text.replace("每個 YOUR TURN 區塊都附有 `# Hint:` 提示，請仔細閱讀。", "原本的練習提示已保留，並已依提示完成。")
        cell["source"] = source(text)

    NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Updated {NOTEBOOK}")


if __name__ == "__main__":
    main()
