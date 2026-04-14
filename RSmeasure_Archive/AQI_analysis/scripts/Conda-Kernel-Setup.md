# 🌿 Conda GeoPandas Kernel 設置指南

## ✅ 已創建的 Conda Kernel

**Kernel 名稱**: `Conda (GeoPandas)`  
**Kernel ID**: `geopandas-conda`  
**Python 路徑**: `C:\Users\Wade\anaconda3\python.exe`

## 🎯 現在可用的 Kernels

```
Available kernels:
  geopandas-conda    C:\Users\Wade\AppData\Roaming\jupyter\kernels\geopandas-conda  ✅ 新建
  geopandas-env      C:\Users\Wade\AppData\Roaming\jupyter\kernels\geopandas-env
  python3            C:\Users\Wade\anaconda3\share\jupyter\kernels\python3
```

## 📋 如何使用 Conda Kernel

### Step 1: 重新啟動 Jupyter
1. **關閉所有 Jupyter Notebook 視窗**
2. **重新啟動 VS Code**（如果使用）
3. **重新開啟 notebook**

### Step 2: 選擇 Conda Kernel
1. 在 notebook 中點擊 **Kernel** → **Change kernel**
2. 選擇 **"Conda (GeoPandas)"**
3. 重新啟動 kernel

### Step 3: 驗證 Conda 環境
在 notebook 中執行：

```python
# 檢查是否使用 conda 環境
import sys
print(f'Python 路徑: {sys.executable}')
print(f'是否為 Conda: {"anaconda" in sys.executable.lower()}')

# 檢查套件
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import folium
import osmnx as ox
import numpy as np

print(f'✅ geopandas {gpd.__version__}')
print(f'✅ pandas {pd.__version__}')
print(f'✅ folium {folium.__version__}')
print(f'✅ osmnx {ox.__version__}')
print('🎉 Conda GeoPandas 環境就緒！')
```

## 🌿 Conda 環境的優勢

### ✅ 更好的套件管理
- **依賴關係**: conda 自動處理複雜依賴
- **編譯套件**: GDAL, GEOS, PROJ 等地理套件更穩定
- **版本控制**: 避免 pip 和 conda 套件衝突

### ✅ 系統整合
- **路徑管理**: 正確的系統路徑配置
- **環境變數**: 自動設定必要的環境變數
- **效能**: 更好的記憶體和 CPU 使用

## 🔧 如果仍然找不到 Kernel

### 檢查 Conda 狀態
```bash
# 檢查當前 conda 環境
conda info

# 檢查安裝的套件
conda list geopandas

# 檢查 kernel 配置
jupyter kernelspec list
```

### 重新安裝 Conda Kernel
```bash
# 移除舊的
jupyter kernelspec remove geopandas-conda

# 重新安裝
python -m ipykernel install --user --name geopandas-conda --display-name "Conda (GeoPandas)"
```

### 使用 Conda 直接安裝
```bash
# 在 conda 環境中安裝
conda install -c conda-forge geopandas folium mapclassify osmnx

# 然後安裝 kernel
python -m ipykernel install --user --name geopandas-conda --display-name "Conda (GeoPandas)"
```

## 🚀 立即開始

1. **重新啟動 Jupyter**
2. **選擇 "Conda (GeoPandas)" kernel**
3. **開啟 `Week3-GeoPandas-Student.ipynb`**
4. **開始 Week 3 課程**

---

**🌿 現在您有了一個專門的 Conda GeoPandas 環境！**
