# Week 3 GeoPandas 學習指南

## 📋 檔案說明

### 主要檔案
- **`Week3-GeoPandas-Student.ipynb`** - 蘇文瑞教授設計的學習筆記本
- **`Week3-Setup.ipynb`** - 環境設置和測試筆記本
- **`README_Week3.md`** - 本說明文件

### 環境狀態
✅ **已完成 Pre-lab 設置**：
- geopandas 1.1.3
- shapely 2.1.2
- folium 0.20.0
- mapclassify 2.10.0
- osmnx 2.1.0
- matplotlib

## 🚀 如何開始學習

### Step 1: 確認環境
```bash
# 在專案目錄下執行
cd c:\Users\Wade\Desktop\ClassPhD\RSmeasure\AQI_analysis
jupyter notebook
```

### Step 2: 開啟筆記本
1. 開啟 `Week3-Setup.ipynb` 確認環境正常
2. 開啟 `Week3-GeoPandas-Student.ipynb` 開始課程

### Step 3: 按照課程進度
筆記本已分為幾個階段：

#### Phase 1: Fill-in-the-Blank (Cell [1]–[4])
✅ **已填寫完成**：
- Cell [3]: 環境設置
- Cell [6]: 基本資訊檢查
- Cell [7]: 幾何欄位檢查
- Cell [9]: CRS 轉換
- Cell [11]: 面積計算
- Cell [37]: CRS 對齊檢查

#### Phase 2: AI-Collaborative (Cell [5]–[8])
🔄 **需要 AI 協助**：
- Cell [5]: 緩衝區分析
- Cell [6]: 空間連接 (sjoin)
- Cell [7]: 互動地圖
- Cell [8]: OSM 資料下載

#### Lab 1 & Lab 2
🔄 **實作練習**：
- Lab 1: 緩衝區單位陷阱
- Lab 2: 避難所洪水風險分析

## 🎯 已準備的資料

### Week 2 資料整合
- **避難所資料**: `../data/shelters_cleaned.csv` (5,904 筆)
- **已清理座標**: 移除海中錯誤點
- **語意分析**: 室內/室外設施分類

### 可直接使用的變數
```python
# 已載入的避難所 GeoDataFrame
shelters_gdf  # EPSG:4326
shelters_twd97  # EPSG:3826

# 鄉鎮界線 (課程中會載入)
townships  # 從 TGOS 載入
townships_3826  # TWD97 投影
```

## 🛠️ 故障排除

### 常見問題

#### 1. .explore() 不顯示
```python
# 在新 cell 中執行
!pip install folium mapclassify osmnx --upgrade
# 然後重新啟動 kernel
```

#### 2. CRS 錯誤
```python
# 檢查 CRS
print(gdf.crs)

# 統一 CRS
gdf = gdf.to_crs('EPSG:3826')
```

#### 3. 記憶體不足
```python
# 使用部分資料
gdf_subset = gdf.head(100)
```

## 📚 學習重點

### 必須掌握的概念
1. **CRS 重要**: 緩衝區前檢查 CRS
2. **空間連接**: sjoin() vs VLOOKUP
3. **幾何操作**: buffer(), area(), bounds
4. **互動地圖**: .explore() 和 folium

### 實作技巧
1. **先檢查 CRS**: 任何空間操作前
2. **測試小資料**: 先用幾筆資料測試
3. **驗證 AI 輸出**: 不要盲目相信 AI
4. **保存中間結果**: 便於除錯

## 🎯 課程目標

完成後您將能夠：
- ✅ 使用 GeoPandas 處理空間資料
- ✅ 進行 CRS 轉換和座標投影
- ✅ 創建緩衝區和空間分析
- ✅ 執行空間連接 (sjoin)
- ✅ 創建互動式地圖
- ✅ 從 OSM 下載地理資料

## 📞 需要協助？

如果遇到問題：
1. 檢查 `Week3-Setup.ipynb` 的環境測試
2. 確認所有套件版本正確
3. 檢查資料路徑是否正確
4. 重新啟動 Jupyter Kernel

---

**準備就緒，開始 Week 3 GeoPandas 學習之旅！** 🚀
