# 🚀 GeoPandas Kernel 設置指南

## ✅ 已為您創建的專用 Kernel

**Kernel 名稱**: `Python (GeoPandas)`  
**Kernel ID**: `geopandas-env`

## 📋 如何使用專用 Kernel

### Step 1: 開啟 Jupyter Notebook
```bash
cd c:\Users\Wade\Desktop\ClassPhD\RSmeasure\AQI_analysis\scripts
jupyter notebook
```

### Step 2: 選擇正確的 Kernel
1. 在任何 Jupyter Notebook 中
2. 點擊 **Kernel** → **Change kernel**
3. 選擇 **"Python (GeoPandas)"**
4. 點擊 **Restart** 重新啟動

### Step 3: 驗證環境
開啟 `Test-Kernel.ipynb` 並執行所有 cells 來驗證環境

## 🎯 Kernel 包含的套件

### ✅ 已安裝並測試
- **geopandas** 1.1.3 - 空間資料處理
- **shapely** 2.1.2 - 幾何運算
- **folium** 0.20.0 - 互動地圖
- **mapclassify** 2.10.0 - 地圖分類
- **osmnx** 2.1.0 - OpenStreetMap 資料
- **matplotlib** - 繪圖
- **pandas** - 資料處理
- **numpy** - 數值計算

## 🔧 故障排除

### 如果無法找到 "Python (GeoPandas)" kernel
```bash
# 重新安裝 kernel
python -m ipykernel install --user --name geopandas-env --display-name "Python (GeoPandas)"

# 檢查可用 kernels
jupyter kernelspec list
```

### 如果套件載入失敗
```bash
# 在 kernel 中重新安裝
!pip install geopandas shapely folium mapclassify osmnx --upgrade
```

### 如果 kernel 無法啟動
1. 關閉所有 Jupyter sessions
2. 重新啟動 Jupyter
3. 選擇 "Python (GeoPandas)" kernel

## 📚 使用建議

### 🎯 適用於
- **Week 3 GeoPandas 課程**
- **所有空間分析專案**
- **避難所風險分析**
- **地理資料視覺化**

### 🔄 每次使用前
1. 確認選擇了正確的 kernel
2. 執行 `Test-Kernel.ipynb` 驗證
3. 檢查所有套件版本

### 📝 最佳實踐
- 每個新筆記本都檢查 kernel
- 保存重要的中間結果
- 定期更新套件版本

## 🚀 立即開始

1. **開啟** `Test-Kernel.ipynb`
2. **選擇** "Python (GeoPandas)" kernel
3. **執行** 所有測試 cells
4. **確認** 所有功能正常
5. **開啟** `Week3-GeoPandas-Student.ipynb` 開始課程

---

**🎉 準備就緒！您的專用 GeoPandas 環境已經設置完成。**
