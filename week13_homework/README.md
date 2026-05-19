# Week 13 Homework — ARIA v9.0：The Cloud Engine

**課程：** 遙測與空間資訊之分析與應用（NTU Remote Sensing & Spatial Information Analysis）
**指導教授：** 蘇文瑞 教授
**作業：** Week 13 課後作業 — 雲端尺度植被趨勢分析
**研究區：** 秀林 / 太魯閣（Xiulin / Taroko）山區　BBOX `[121.3453, 24.0460, 121.8515, 24.3577]`

## 內容 (Contents)

| 檔案 | 說明 |
|---|---|
| `Week13-Homework-Completed.ipynb` | 完成版作業筆記本 — Task 1–4 + Bonus 1–2,已執行、0 錯誤 |
| `Homework-Week13.md` | 作業題目說明 |
| `week13_hw_outputs/` | 產出圖檔:NDVI/SAR 時序圖、三期合成與 ΔNDVI 圖、ΔVV 圖、NDVI 時序動畫 GIF |

## 完成項目 (Tasks)

| 項目 | 配分 | 產出 |
|---|---|---|
| Task 1 — NDVI 時序分析 | 25% | 2020–2026 月均 NDVI 時序圖（291 張 Sentinel-2）+ 季節/地震/缺值分析 |
| Task 2 — 三期 Composite 比較 | 25% | 三期中值合成 + 三組 ΔNDVI 數值地圖、損害面積（公頃）、W9 比較 |
| Task 3 — SAR 時序 | 25% | Sentinel-1 VV 時序圖（147 張）+ ΔVV 圖 + 光學/SAR 交叉比對 |
| Task 4 — 匯出 + 整合摘要 | 25% | 2 個 GeoTIFF 匯出任務 + ARIA v9.0 整合摘要報告 |
| Bonus 1 — InSAR 干涉圖判讀 | +10% | 2016 熊本地震干涉圖 5 題 + 心得 |
| Bonus 2 — NDVI 時序動畫 | +10% | 13 幀半年度 NDVI 時序動畫 GIF |

## 主要結果 (Key Results)

- Sentinel-2 影像 **291 張**、Sentinel-1 影像 **147 張**,合計 438 張於 GEE 雲端處理（零下載）。
- 地震在 AOI 平均尺度訊號微弱（NDVI −0.0056）,但像元尺度 ΔNDVI < −0.15 的損害面積達 **7,368 ha**。
- 光學與 SAR 同時顯著變化的高信心區為 **164 ha**。

## 執行說明 (How to Run)

1. 安裝套件：`pip install earthengine-api geemap`
2. 首次使用先執行 `ee.Authenticate()`,並在 Setup cell 設定可用的 GEE project id。
3. 由上而下依序執行所有 cell；GEE 全部於雲端運算,一般筆電即可。
