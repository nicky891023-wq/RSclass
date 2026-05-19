# Week 13 — Google Earth Engine & Cloud-Scale Time Series

**課程 (Course):** 遙測與空間資訊之分析與應用 (Remote Sensing and Spatial Information Analysis and Applications)
**主題 (Theme):** Cloud-based satellite time-series analysis with Google Earth Engine — ARIA v9.0
**研究區 (Study Area):** Hualien, Taiwan (花蓮) — 2024/04/03 地震與堰塞湖分析

## 內容 (Contents)

| 檔案 | 說明 |
|---|---|
| `Week13-Student.ipynb` | 完成版練習筆記本 — S1–S10 + S5b，已執行、0 錯誤 |
| `Week13-Slides.pptx` | 課程投影片 |
| `Week13_outputs/` | 輸出圖檔：時間序列折線圖、S5b NDVI/ΔNDVI 數值地圖與 GIF 動畫、`gif_frames/` |

## 工作流程 (Workflow)

```
S1 環境設定 → S2 篩選 Sentinel-2 → S3 雲遮罩 + NDVI → S4 時間序列
   → S5 三期合成 → S5b 數值地圖 + GIF → S6 SAR 時間序列
   → S7 跨感測器交叉比對 → S8 匯出 GeoTIFF → S10 自由探索 → S9 反思
```

- 透過 GEE Python API 存取並篩選大量衛星影像，於雲端計算 NDVI / SAR 時間序列。
- 結合光學 (Sentinel-2) 與雷達 (Sentinel-1) 進行震後植被變化偵測。
- S5b 以可重現的程式產生三期 NDVI / ΔNDVI 數值地圖與 GIF 動畫。
- 所有課程問答以繁體中文作答，並以筆記本實際輸出的數值佐證。
