# 台灣 AQI 即時監測地圖

這個專案會從環境部 API 獲取全台空氣品質監測站的即時數據，並使用 Folium 在地圖上視覺化呈現。

## 功能特色

- 🌍 串接環境部 API (aqx_p_432) 獲取全台即時 AQI 數據
- 🔑 從 .env 檔案安全讀取 API 金鑰
- 📍 使用 Folium 在地圖上標示所有測站位置
- 🎨 根據 AQI 數值顯示不同顏色（綠色→黃色→橙色→紅色→紫色→褐色）
- 📊 顯示詳細的測站資訊（AQI、PM2.5、PM10 等）
- 📈 提供統計資訊和數據分析

## 安裝與執行

### 1. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 2. 設定環境變數

確保 `.env` 檔案包含以下內容：

```env
# Environment Protection Administration API
EPA_API_KEY=你的環境部API金鑰
```

### 3. 執行程式

```bash
python aqi_map.py
```

執行完成後，會在 `output/` 資料夾中生成 `aqi_map.html` 檔案，用瀏覽器開啟即可查看互動式地圖。

## 輸出檔案

- `output/aqi_map.html` - 互動式 AQI 地圖
- 終端機顯示統計資訊

## AQI 顏色對應

| AQI 範圍 | 狀態 | 顏色 |
|---------|------|------|
| 0-50 | 良好 | 綠色 |
| 51-100 | 普通 | 黃色 |
| 101+ | 不健康 | 紅色 |

## 專案結構

```
0224/
├── data/              # 資料存放目錄
├── output/            # 輸出檔案目錄
├── .env               # 環境變數設定
├── .gitignore         # Git 忽略檔案
├── requirements.txt   # Python 依賴套件
├── aqi_map.py        # 主程式
└── README.md          # 說明文件
```

## 注意事項

- 確保網路連線正常，能夠存取環境部 API
- API 金鑰請妥善保管，不要提交到版本控制系統
- 地圖檔案可能較大，建議使用現代瀏覽器開啟
