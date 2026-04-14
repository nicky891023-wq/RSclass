# Week 3 - GeoPandas 完整學習包

## 📁 資料夾內容

### 📓 主要檔案
- **`Week3-GeoPandas-Student.ipynb`** - 完整的 Jupyter 筆記本，包含所有練習和實驗

### 🗺️ 輸出地圖 (outputs/)
- **`cell7_map.html`** - Cell 7 互動式地圖 (台北市 + NTU 緩衝區 + 避難所)
- **`lab1_river_buffer_map.html`** - Lab 1 河川緩衝區互動地圖
- **`lab2_shelter_risk_map.html`** - Lab 2 避難所洪風險分析地圖

### 📊 處理數據 (data/)
- **`river_buffer_500m.geojson`** - 河川 500m 緩衝區 GeoJSON 檔案

### 🌊 原始河川資料 (riverpoly/)
水利署河川面 (RIVERPOLY) 原始 Shapefile 檔案：
- `riverpoly.shp` - 主要圖形檔案
- `riverpoly.dbf` - 屬性資料
- `riverpoly.shx` - 索引檔案
- `riverpoly.prj` - 投影資訊
- `riverpoly.cpg` - 字元編碼
- `riverpoly.qpj` - QGIS 投影檔案

## 🎯 學習目標

### Phase 1 - 基礎操作 (Cell 1-4)
- ✅ GeoPandas 環境設置
- ✅ 台灣鄉鎮界線載入
- ✅ 座標系統轉換 (CRS Transformation)
- ✅ 幾何屬性計算

### Phase 2 - AI 協作練習 (Cell 5-8)
- ✅ 緩衝區分析 (Buffer Zone)
- ✅ 空間連接 (Spatial Join)
- ✅ 互動式地圖製作 (.explore())
- ✅ OpenStreetMap 數據下載

### Lab 1 - Buffer Unit Trap 實驗
- ✅ 河川數據載入與 CRS 檢查
- ✅ 正確 vs 錯誤緩衝區比較
- ✅ 視覺化對比分析
- ✅ CRS 單位陷阱深度理解

### Lab 2 - 空間連接實戰
- ✅ 避難所數據處理
- ✅ 洪風險空間分析
- ✅ 重複檢測與去重
- ✅ 風險評估地圖

## 🔧 技術重點

### 📍 CRS 重要概念
- **EPSG:4326** - WGS84 地理坐標系 (度數單位)
- **EPSG:3826** - TWD97/TM2 投影坐標系 (公尺單位)
- **單位陷阱** - 相同代碼在不同 CRS 下產生完全不同結果

### 🛠️ 核心技能
- `gpd.read_file()` - 載入空間數據
- `gdf.to_crs()` - 座標系轉換
- `gdf.buffer()` - 緩衝區分析
- `gpd.sjoin()` - 空間連接
- `gdf.explore()` - 互動式地圖
- `folium` - 網頁地圖製作

## 📖 使用說明

1. **開啟筆記本**：使用 Jupyter Notebook 或 VS Code 開啟 `Week3-GeoPandas-Student.ipynb`
2. **依序執行**：按 Cell 順序執行，觀察每個步驟的結果
3. **互動地圖**：開啟 `outputs/` 資料夾中的 HTML 檔案查看互動地圖
4. **數據探索**：使用 GIS 軟體 (QGIS/ArcGIS) 檢視 GeoJSON 和 Shapefile

## 🎓 學習成果

完成此學習包後，你將掌握：
- 🗺️ 空間數據處理基礎
- 🔄 座標系統轉換技巧
- 🛡️ CRS 單位陷阱防範
- 🔍 空間連接分析能力
- 📊 互動式地圖製作
- 🌐 真實世界數據處理

## 📝 備註

- 所有代碼已經過測試和錯誤修復
- 包含完整的中文註解和說明
- 提供多重錯誤處理機制
- 適合初學者和進階學習者

---
**課程**: 遙感與空間資訊分析應用 (114)  
**講師**: 蘇文瑞教授 · NCDR / 台大土木工程  
**完成日期**: 2026年3月10日
