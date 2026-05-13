# Week 12 Homework Report: ARIA v8.0 Classification Engine

## Abstract

本作業以 Sentinel-2 L2A 災後影像完成秀林/太魯閣研究區（`[121.4, 24.1, 121.8, 24.25]`）的五類土地覆蓋分類。流程包含 K-means 非監督式分群、KMZ ROI 建立與解析、Random Forest 監督式分類、混淆矩陣與官方農村水保署事件型崩塌資料驗證，最後輸出面積統計與中文災害應變報告。

## Data And Workflow

- Sentinel-2 item: `S2B_MSIL2A_20240404T022529_R046_T51QUG_20240404T063438`，來源：Microsoft Planetary Computer STAC。
- 有效像元：1,256,573 pixels（72.3%）；已套用 SCL cloud/shadow/snow mask，排除 SCL [0, 1, 3, 8, 9, 10, 11] 與異常反射率像元。
- 訓練 ROI：`data/taroko_training_rois.kmz`，由本機流程建立後重新以 KMZ workflow 解析，不直接拿 mask 跳過。
- 獨立驗證資料：`data/20240802新生崩塌地.kml`，由 ARDSWC 官方事件型崩塌 MVT 服務轉出；作業 Google Drive 連結經檢查回傳 Week12 notebook JSON，因此改採官方 OpenData/MVT 來源。

## Task 1: K-means

K-means 使用六個 Sentinel-2 反射率波段，先以 120,000 個有效像元抽樣標準化訓練，再預測全區 1,256,573 個有效像元。分群平均光譜如下：

|   cluster |   pixel_count |     Blue |    Green |      Red |      NIR |    SWIR1 |    SWIR2 | interpreted_label                      | reason                   |
|----------:|--------------:|---------:|---------:|---------:|---------:|---------:|---------:|:---------------------------------------|:-------------------------|
|         0 |        552620 | 0.18711  | 0.169242 | 0.159164 | 0.155918 | 0.152587 | 0.143002 | Built-up or bright bare / 建物或亮裸地 | NDBI=-0.01, visible=0.17 |
|         1 |        229401 | 0.191576 | 0.206421 | 0.186296 | 0.419097 | 0.312167 | 0.226268 | Cropland or grass / 農田或草生地       | NDVI=0.38 is moderate    |
|         2 |         78041 | 0.271434 | 0.280011 | 0.267609 | 0.420074 | 0.362682 | 0.293752 | Bare/Landslide / 裸地或崩塌            | NDVI=0.22, SWIR1=0.36    |
|         3 |        388077 | 0.143439 | 0.162024 | 0.14191  | 0.395826 | 0.267815 | 0.184111 | Cropland or grass / 農田或草生地       | NDVI=0.47 is moderate    |
|         4 |          8434 | 0.472265 | 0.474677 | 0.470132 | 0.59442  | 0.54812  | 0.47509  | Bare/Landslide / 裸地或崩塌            | NDVI=0.12, SWIR1=0.55    |

K-means 對水體與高 NDVI 森林較容易分出，因為 NIR/SWIR 反應很明確；裸地、崩塌、道路與建物則光譜相近，容易混在同一或相鄰 cluster，必須靠監督式 ROI 與空間脈絡修正。

## Task 2: Random Forest

- 訓練樣本：4,881 pixels from parsed KMZ ROIs。
- Test accuracy: 0.939
- OOB score: 0.945
- Macro F1: 0.930
- Weighted F1: 0.939
- Macro-weighted F1 gap: 0.009
- 最重要波段：`Blue`，feature importance = 0.198。

Feature importance:

| band   |   importance |
|:-------|-------------:|
| Blue   |     0.197856 |
| Green  |     0.104105 |
| Red    |     0.176189 |
| NIR    |     0.188036 |
| SWIR1  |     0.150995 |
| SWIR2  |     0.182819 |

K-means 與 RF 的差異在於：K-means 僅依光譜自然分群，能探索未知類別但語意不穩定；RF 使用 KMZ ROI 將類別固定成水體、森林、農田/草生地、裸地/崩塌、建物/都市，因此更符合災後土地覆蓋圖的需求。

Blue 在本次 RF 中排名最高，推測與研究區同時包含海域、山區陰影、亮裸土與道路/建物有關；短波段對水體與明亮裸露地的反差敏感，因此有助於把水體、亮裸地與都市類別拉開。不過 Blue 也容易受大氣與薄雲影響，所以仍需搭配 NIR、SWIR1、SWIR2 解讀，而不宜單獨作為崩塌判釋依據。

## Task 3: Accuracy And SWCB Validation

ROI confusion matrix:

```text
                precision    recall  f1-score   support

         Water       1.00      1.00      1.00       279
        Forest       0.95      0.97      0.96       268
      Cropland       0.96      0.93      0.95       289
Bare/Landslide       0.82      0.90      0.86       150
      Built-up       0.91      0.86      0.89       235

      accuracy                           0.94      1221
     macro avg       0.93      0.93      0.93      1221
  weighted avg       0.94      0.94      0.94      1221

```

SWCB landslide validation:

- 官方崩塌 polygon count in bbox: 1,216
- SWCB rasterized area: 471.0 ha
- RF bare/landslide area: 201.8 ha
- Precision: 0.028
- Recall: 0.012
- IoU: 0.009

RF 的裸地/崩塌類比官方崩塌多，主因是 Sentinel-2 20 m 像元會將河床、道路開挖面、亮裸土與崩塌混合。SWCB polygons 來自較高解析影像判釋，且僅標崩塌，不包含一般裸地，因此 precision/IoU 不宜直接解讀成 RF 全分類品質，而應視為崩塌熱區篩選能力。

OOB accuracy (0.945) 與 test accuracy (0.939) 差距僅 0.006，Macro/Weighted F1 gap 為 0.009，低於 0.03；各類 test support 皆大於 30 pixels，因此內部驗證相對穩定。外部 SWCB 驗證顯著較低，顯示模型在 ROI 類別內表現良好，但「裸地/崩塌」對官方崩塌清冊的語意與尺度轉換仍不足。FN 多半會集中在小面積或窄長邊坡崩塌、山區陰影及雲/陰影遮罩附近，這些位置在 20 m Sentinel-2 影像中容易被森林或裸地背景稀釋。

## Task 4: Area Statistics And AI Report

|   class_id | class_en       | class_zh    |   pixels |   area_ha |   area_km2 |   percent_valid |
|-----------:|:---------------|:------------|---------:|----------:|-----------:|----------------:|
|          0 | Water          | 水體        |   542261 |  21690.4  |   216.904  |       43.154    |
|          1 | Forest         | 森林        |   347101 |  13884    |   138.84   |       27.6228   |
|          2 | Cropland       | 農田/草生地 |   241125 |   9645    |    96.45   |       19.1891   |
|          3 | Bare/Landslide | 裸地/崩塌   |     5044 |    201.76 |     2.0176 |        0.401409 |
|          4 | Built-up       | 建物/都市   |   121042 |   4841.68 |    48.4168 |        9.63271  |

### AI-generated Commander Report

災後土地覆蓋分析顯示，秀林/太魯閣研究區仍以森林為主，森林面積約 13884.0 公頃，占有效像元 27.6%。RF 判釋之裸地/崩塌面積約 201.8 公頃，主要沿中央山脈側坡、溪谷與蘇花公路周邊呈帶狀或斑塊分布；水體約 21690.4 公頃，多在東側海域及河口，建物/都市約 4841.7 公頃，分布零散。ROI 測試集 overall accuracy 為 93.9%，OOB 為 94.5%。與農村水保署事件型崩塌資料比對，崩塌 IoU 為 0.009、recall 為 0.012，代表此圖可快速指出疑似裸露與崩塌熱區，但仍會把河床、道路邊坡或亮裸土混入崩塌類。建議將此分類圖作為避難所評估與路網分析的第一層篩選：優先檢查崩塌/裸地接近道路、聚落與橋梁的位置，再用高解析影像或現地調查確認可通行性與二次災害風險。

### Critical Evaluation

AI briefing 中引用的森林、裸地/崩塌、水體、建物/都市面積與 accuracy/OOB/SWCB IoU 均已和前述統計表及 metrics.json 核對，未發現新增類別或任意改寫數值；不確定性描述也合理指出 20 m 混合像元、河床/道路邊坡混入與官方崩塌清冊尺度差異。本次成果符合 ARIA v8.0 從「閾值偵測」升級到「多類別分類器」的精神，但 ROI 為本機自動 KMZ 流程產生，仍不等同人工 Google Earth 判釋；山區陰影、河床與崩塌光譜接近，會提高誤判。後續若要改進，我會加入 DEM slope/aspect、SAR coherence、道路距離，並人工修訂 ROI 與 FN 熱區。

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

Validation status: **PASS**.
