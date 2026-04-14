# 🔧 Kernel 找不到的故障排除指南

## 🚨 常見問題及解決方案

### 問題 1: Jupyter 需要重新啟動
**症狀**: 新安裝的 kernel 不在選項中

**解決方案**:
1. **完全關閉所有 Jupyter 視窗**
2. **重新啟動 Jupyter Notebook**
3. **重新整理瀏覽器頁面**
4. **檢查 kernel 選單**

---

### 問題 2: VS Code/Jupyter 擴展問題
**症狀**: 在 VS Code 中找不到 kernel

**解決方案**:
1. **重新載入 VS Code 視窗**
   - 按 `Ctrl+Shift+P`
   - 輸入 "Developer: Reload Window"
   - 重新啟動

2. **重新啟動 Jupyter Kernel**
   - 在 notebook 中按 `Ctrl+Shift+P`
   - 輸入 "Jupyter: Restart Kernel"

---

### 問題 3: Kernel 配置錯誤
**症狀**: kernel 存在但無法啟動

**解決方案**:
```bash
# 檢查 kernel 配置
jupyter kernelspec list

# 重新安裝 kernel
python -m ipykernel install --user --name geopandas-env --display-name "Python (GeoPandas)"
```

---

### 問題 4: 權限問題
**症狀**: kernel 安裝但無法存取

**解決方案**:
```bash
# 以管理員身份執行
# 或重新安裝到用戶目錄
python -m ipykernel install --user --name geopandas-env --display-name "Python (GeoPandas)"
```

---

## 🛠️ 立即嘗試的步驟

### Step 1: 重新啟動所有東西
1. 關閉所有 Jupyter Notebook 視窗
2. 關閉 VS Code
3. 重新開啟 VS Code
4. 重新開啟 notebook

### Step 2: 檢查 kernel 是否真的存在
```bash
jupyter kernelspec list
```
**應該看到**:
```
Available kernels:
  geopandas-env    C:\Users\Wade\AppData\Roaming\jupyter\kernels\geopandas-env
  python3          C:\Users\Wade\anaconda3\share\jupyter\kernels\python3
```

### Step 3: 如果還是找不到，手動創建
```bash
# 刪除舊的（如果存在）
jupyter kernelspec remove geopandas-env

# 重新安裝
python -m ipykernel install --user --name geopandas-env --display-name "Python (GeoPandas)"

# 驗證安裝
jupyter kernelspec list
```

---

## 🎯 替代方案：直接使用現有的 Python3 Kernel

如果專用 kernel 持續有問題，可以直接使用 `python3` kernel：

### 在 notebook 開頭添加：
```python
# 檢查並安裝必要套件
import sys
import subprocess

required_packages = ['geopandas', 'shapely', 'folium', 'mapclassify', 'osmnx']
for package in required_packages:
    try:
        __import__(package)
        print(f'✅ {package} 已安裝')
    except ImportError:
        print(f'📦 安裝 {package}...')
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

# 現在可以正常使用
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import folium
import osmnx as ox
import numpy as np
from shapely.geometry import Point

print('🎉 環境設置完成！')
```

---

## 📞 如果仍然有問題

1. **確認 Python 路徑**:
   ```bash
   which python
   which jupyter
   ```

2. **檢查 ipykernel 版本**:
   ```bash
   pip show ipykernel
   ```

3. **更新 ipykernel**:
   ```bash
   pip install --upgrade ipykernel
   ```

---

## 🚀 快速測試

創建一個新的 notebook，並在第一個 cell 執行：

```python
# 測試環境
import geopandas as gpd
import pandas as pd
print(f'✅ geopandas {gpd.__version__}')
print(f'✅ pandas {pd.__version__}')
print('🎉 可以開始 Week 3 課程了！')
```

如果這個可以正常執行，表示環境沒問題，只是 kernel 顯示的問題。
