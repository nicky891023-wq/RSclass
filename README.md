# ARIA v3.0 - 動態風險監測系統

## 🎯 系統概述

ARIA v3.0 是一個全自動區域受災衝擊評估系統，整合了即時雨量監測與避難所風險評估，能夠回答「現在哪裡最危險？」的關鍵問題。

## 📋 系統需求

### Python 環境
- Python 3.9+
- Conda 環境推薦

### 必要套件
```bash
conda create -n aria_v3 python=3.9
conda activate aria_v3
pip install -r requirements.txt
```

或使用 conda 環境檔案：
```bash
conda env create -f environment.yml
conda activate aria_v3
```

## 🚀 快速開始

### 1. 環境設定
```bash
# 建立並啟動 conda 環境
conda create -n aria_v3 python=3.9
conda activate aria_v3

# 安裝必要套件
pip install -r requirements.txt
```

### 2. 設定環境變數
複製並編輯 `.env` 檔案：
```bash
# .env 檔案範例
APP_MODE=SIMULATION
CWA_API_KEY=your-cwa-api-key-here
TARGET_COUNTY=花蓮縣
BUFFER_HIGH_RAIN=5000
RAINFALL_CRITICAL=80
RAINFALL_URGENT=40
```

### 3. 執行系統
```bash
# 啟動 Jupyter Notebook
jupyter notebook

# 開啟並執行 ARIA_v3.ipynb
```

## 📁 檔案結構

```
0324/
├── ARIA_v3.ipynb              # 完整系統主程式
├── Week5-Student.ipynb        # 學生練習版本
├── Homework-Week5.md          # 作業說明文件
├── .env                       # 環境變數設定
├── requirements.txt           # Python 套件清單
├── environment.yml            # Conda 環境檔案
├── fungwong_202511.json      # 鳳凰颱風模擬資料
├── 避難收容處所點位檔案v9 (1).csv  # 避難所資料
├── TOWN_MOI_1120317.*        # 鄉鎮界線圖
├── riverpoly/                 # 河川資料
└── output/                    # 系統輸出檔案
    ├── ARIA_v3_Fungwong.html  # 互動式監測地圖
    └── shelter_risk_audit_week5.json  # 風險稽核資料
```

## 🎯 核心功能

### 1. 即時雨量監測
- **LIVE 模式**：連接 CWA 即時雨量 API
- **SIMULATION 模式**：載入鳳凰颱風歷史資料
- **Fallback 機制**：API 失敗自動切換

### 2. 動態風險評估
- **CRITICAL**：時雨量 > 80mm 影響範圍內
- **URGENT**：時雨量 > 40mm 且地形風險 HIGH
- **WARNING**：時雨量 > 40mm 或地形風險 HIGH
- **SAFE**：其餘情況

### 3. 空間疊合分析
- 5km 雨量影響範圍 Buffer
- 避難所與雨量站空間疊合
- CRS 坐標系統自動轉換

### 4. 互動式視覺化
- Folium 動態地圖
- 多圖層控制
- 豐富 Popup 資訊
- 雨量熱力圖

## 🔧 技術規格

### 坐標系統
- **分析用**：EPSG:3826 (TWD97/TM2)
- **視覺化用**：EPSG:4326 (WGS84)

### 資料來源
- **避難所**：內政部避難收容處所點位檔案
- **雨量資料**：中央氣象署 O-A0002-001 API
- **地理資料**：國土測繪中心鄉鎮市區界

### API 整合
- **CWA 雨量 API**：https://opendata.cwa.gov.tw/
- **環境部 API**：已整合金鑰設定

## 📊 系統輸出

### 1. 互動式地圖
- 檔案：`output/ARIA_v3_Fungwong.html`
- 功能：即時風險監測儀表板
- 圖層：雨量站、避難所、影響範圍、熱力圖

### 2. 風險稽核報告
- 檔案：`output/shelter_risk_audit_week5.json`
- 內容：詳細風險分析統計
- 格式：JSON 結構化資料

### 3. 分析統計
- 動態風險分佈
- 受影響避難所統計
- 雨量站分析報告

## 🚨 AI 診斷日誌

### 已解決的技術挑戰

#### 1. CRS 坐標系統對齊問題
**問題**：空間疊合分析時，雨量站與避難所的 CRS 不一致導致 sjoin 結果為空
**解決**：在分析前將所有資料統一轉換為 EPSG:3826，確保空間計算準確性

#### 2. CWA API 與 CoLife 資料格式差異
**問題**：兩種資料來源的 JSON 結構略有不同，特別是坐標資料的格式
**解決**：建立 `normalize_cwa_json()` 函數，自動偵測並統一處理不同格式

#### 3. Folium 坐標順序問題
**問題**：Folium 使用 [latitude, longitude] 順序，與 GIS 常見的 [longitude, latitude] 不同
**解決**：在建立地圖標記時特別注意坐標順序轉換

#### 4. 動態風險分級邏輯實作
**問題**：需要同時考慮雨量強度與地形風險的複合評估
**解決**：按照作業要求實作四級風險分類系統 (CRITICAL/URGENT/WARNING/SAFE)

## 🎯 使用場景

### 1. 災害監測
- 即時監控颱風、暴雨等極端天氣
- 動態評估避難所風險狀況
- 提供決策支援資訊

### 2. 應變指揮
- 識別高風險避難所
- 優先資源分配
- 疏散路線規劃

### 3. 歷史分析
- 過去災害事件重現
- 風險模式分析
- 系統效能驗證

## 📞 技術支援

### 常見問題

#### Q: Jupyter Kernel 找不到 aria_v3 環境？
A: 確認已正確啟動 conda 環境：
```bash
conda activate aria_v3
python -m ipykernel install --user --name aria_v3 --display-name "Python (aria_v3)"
```

#### Q: API 呼叫失敗？
A: 檢查 `.env` 檔案中的 API 金鑰設定，或切換至 SIMULATION 模式。

#### Q: 地圖顯示異常？
A: 確認所有必要套件已正確安裝，特別是 `folium` 和 `branca`。

## 📈 效能指標

- **資料處理速度**：< 30 秒
- **地圖載入時間**：< 10 秒
- **API 回應時間**：< 5 秒
- **記憶體使用量**：< 2GB

## 🎯 系統限制

1. **資料範圍**：目前僅支援台灣地區
2. **更新頻率**：LIVE 模式依 API 限制
3. **瀏覽器相容性**：建議使用 Chrome、Firefox

## 📝 授權資訊

- **開發單位**：ARIA 開發團隊
- **資料來源**：中央氣象署、內政部、環境部
- **授權條款**：教育研究使用

---

**ARIA v3.0 - 讓災害監測更智能、更即時、更準確** 🎯
