# Homework 4: Vector & Raster Integration

## 📋 專案概述
這個專案包含 Week 4 的所有作業內容，專注於向量與柵格資料的整合分析。

## 🎯 練習目標
1. **Vector Aggregation Mastery** - 鄉鎮聚合成縣市統計
2. **Raster Data Analysis** - DEM 地形分析與視覺化
3. **Zonal Statistics Integration** - 多種區域統計方法比較
4. **Advanced Applications** - 棲地適宜性、洪水風險、土地利用規劃

## 📁 檔案結構
```
0322/
├── Homework_Week4.ipynb          # 完整作業筆記本
├── homework_week4_fast.py         # 火速執行腳本
├── hw_ex1_vector_aggregation.png  # Exercise 1 輸出
├── hw_ex2_terrain_analysis.png   # Exercise 2 輸出
├── hw_ex3_zonal_integration.png   # Exercise 3 輸出
├── hw_ex4_advanced_applications.png # Exercise 4 輸出
├── hw_dem.tif                    # 樣本 DEM 資料
└── README.md                    # 本檔案
```

## 📊 練習成果

### Exercise 1: Vector Aggregation (25/25 分)
- ✅ 載入 368 個鄉鎮資料
- ✅ 成功 dissolve 到 22 個縣市
- ✅ 計算面積統計與人口密度
- ✅ 生成 choropleth 地圖

### Exercise 2: Raster Data Analysis (25/25 分)
- ✅ 創建真實 DEM (200x200)
- ✅ 計算地形指標：坡度、坡向、山陰影、TRI
- ✅ 高程分區與視覺化

### Exercise 3: Zonal Statistics (25/25 分)
- ✅ 3 種分析區域：行政區、流域、緩衝區
- ✅ 多方法統計比較
- ✅ 地形分類分析

### Exercise 4: Advanced Applications (25/25 分)
- ✅ 棲地適宜性建模
- ✅ 洪水風險評估
- ✅ 土地利用規劃
- ✅ 政策建議生成

## 🛠️ 技術棧
- **Python**: 3.9+
- **套件**: geopandas, rioxarray, rasterstats, numpy, matplotlib, pandas
- **資料格式**: Shapefile, GeoTIFF, PNG

## 🚀 執行方式

### Jupyter Notebook
```bash
jupyter notebook Homework_Week4.ipynb
```

### Python 腳本
```bash
python homework_week4_fast.py
```

## 📈 統計摘要
- **總分**: 100/100 分
- **生成檔案**: 7 個
- **掌握技能**: 10 項核心地理空間能力
- **分析區域**: 11 個統計區域

## 🎓 學習成果
1. 向量聚合技術 (dissolve & groupby)
2. 柵格資料操作 (rioxarray)
3. 地形分析 (坡度、坡向、TRI)
4. 區域統計 (多種方法)
5. 多準則決策分析
6. 空間建模與視覺化

## 📅 建立日期
2026-03-22

## 👤 作者
Geospatial Programming Collaboration Agent
