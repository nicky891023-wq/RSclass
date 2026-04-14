# GitHub Repository 建立指南 - Week 6

## 📋 建立步驟

### 1. 建立 GitHub Repository
1. 前往 [GitHub](https://github.com)
2. 點擊右上角的 "+" → "New repository"
3. Repository 名稱：`0331-Spatial-Prediction-Shootout`
4. 描述：`Week 6: Spatial Prediction Shootout + Project Proposal - Kriging vs Random Forest`
5. 設定為 **Public**（或 Private 如果你想要私人的）
6. **不要**勾選 "Add a README file"（我們已經有了）
7. **不要**勾選 "Add .gitignore"（我們已經有了）
8. 點擊 "Create repository"

### 2. 連接本地 Repository 到 GitHub
建立完成後，GitHub 會顯示以下命令。請複製並執行：

```bash
# 進入 0331 資料夾
cd 0331

# 初始化 Git Repository
git init

# 添加遠端 Repository (替換 YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/0331-Spatial-Prediction-Shootout.git

# 添加所有檔案
git add .

# 第一次提交
git commit -m "Week 6: Spatial Prediction Shootout + Project Proposal

✅ 課程練習完成:
  - Kriging vs Random Forest 實作比較
  - 四種內插方法視覺化
  - 不確定性分析 (Sigma Map)
  - GeoTIFF 輸出

✅ 課後作業完成:
  - 雙事件比較 (颱風型 vs 梅雨型)
  - Variogram 參數深度分析
  - 🔥 高解析度版本 (500m)
  - 期末專案提案

🔥 特色:
  - 高解析度輸出解決馬賽克問題
  - 專業展示品質
  - 完整技術文檔"

# 設定分支並推送
git branch -M main
git push -u origin main
```

### 3. 驗證上傳
上傳完成後，你可以在 GitHub 網頁上看到：

#### 📂 Lab/ 資料夾 (課程練習)
- 📓 `Week6-Executed.ipynb` - 課程練習執行結果 ⭐
- 📓 `Week6-Student.ipynb` - 課程練習模板
- 🖼️ `*.png` (6個) - 課程練習圖表
- 🗺️ `*.tif` (3個) - 課程練習 GeoTIFF

#### 📂 Homework/ 資料夾 (課後作業)
- 📓 `Week6_Final_Submission_HighRes.ipynb` - 最終作業繳交版本 ⭐🔥
- 📓 `week6_homework_highres.py` - 高解析度執行腳本 🔥
- 🖼️ `*.png` (11個) - 作業圖表 (含高解析度)
- 🗺️ `*.tif` (3個) - 高解析度 GeoTIFF 🔥
- 🌀 `fungwong_202511.json` - 原始資料

#### 📄 文件
- 📄 `README.md` - 完整專案說明
- 📄 `GITHUB_SETUP.md` - GitHub 設定指南

## 🎯 Repository 結構

```
0331-Spatial-Prediction-Shootout/
├── 📂 Lab/                           # 課程練習
│   ├── 📓 Week6-Executed.ipynb        # 課程練習執行結果 ⭐
│   ├── 📓 Week6-Student.ipynb         # 課程練習模板
│   ├── 🖼️ histogram_comparison.png    # 直方圖比較
│   ├── 🖼️ interpolation_shootout.png  # 四種內插方法比較
│   ├── 🖼️ kriging_vs_rf.png           # Kriging vs RF 比較
│   ├── 🖼️ sigma_map.png               # 不確定性圖
│   ├── 🗺️ kriging_rainfall.tif        # Kriging 降雨結果
│   ├── 🗺️ kriging_variance.tif        # Kriging 變異數
│   └── 🗺️ rf_rainfall.tif             # Random Forest 結果
│
├── 📂 Homework/                       # 課後作業
│   ├── 📓 Week6_Final_Submission_HighRes.ipynb  # 最終作業繳交版本 ⭐🔥
│   ├── 📓 week6_homework_highres.py            # 高解析度腳本 🔥
│   ├── 🖼️ event1_four_methods_comparison_highres.png   # 事件1高解析度比較 🔥
│   ├── 🖼️ event1_kriging_vs_rf_highres.png            # 事件1高解析度比較 🔥
│   ├── 🖼️ event1_sigma_map_highres.png                # 事件1高解析度不確定性 🔥
│   ├── 🖼️ cross_event_variogram_comparison.png        # 跨事件比較
│   ├── 🖼️ resolution_comparison.png                   # 解析度比較 🔥
│   ├── 🗺️ kriging_rainfall_highres.tif               # 高解析度 Kriging 降雨 🔥
│   ├── 🗺️ kriging_variance_highres.tif               # 高解析度 Kriging 變異數 🔥
│   ├── 🗺️ rf_rainfall_highres.tif                    # 高解析度 Random Forest 🔥
│   ├── 🌀 fungwong_202511.json                       # 原始雨量資料
│   └── [其他作業檔案...]                              # 完整作業內容
│
├── 📄 README.md                        # 專案說明
└── 📄 GITHUB_SETUP.md                  # GitHub 設定指南
```

## 🚀 快速指令

如果你想要快速完成，請執行：

```bash
# 1. 進入 0331 資料夾
cd 0331

# 2. 初始化並連接 GitHub
git init
git remote add origin https://github.com/YOUR_USERNAME/0331-Spatial-Prediction-Shootout.git

# 3. 添加並提交所有檔案
git add .
git commit -m "Week 6: Spatial Prediction Shootout + Project Proposal

✅ 課程練習完成 (Lab/)
✅ 課後作業完成 (Homework/)
✅ 🔥 高解析度版本 (500m)
✅ 專案提案整合"

# 4. 推送到 GitHub
git branch -M main
git push -u origin main
```

## ✅ 驗證清單

上傳完成後請確認：
- [ ] Lab/ 和 Homework/ 資料夾結構正確
- [ ] 所有 .ipynb 檔案都正確顯示
- [ ] 高解析度圖片檔案 (highres.png) 都存在
- [ ] GeoTIFF 檔案都正確上傳
- [ ] README.md 正確顯示格式
- [ ] .env 檔案被正確忽略（不應出現在 GitHub 上）

## 📊 檔案大小預估

| 類型 | 檔案數 | 總大小 | 備註 |
|------|--------|--------|------|
| 課程練習 | 10 | 2.15 MB | Lab/ |
| 課後作業 | 20 | 4.41 MB | Homework/ |
| 文件 | 2 | ~0.05 MB | README, SETUP |
| **總計** | **32** | **~6.6 MB** | **合理大小** |

## 🎉 完成！

一旦上傳完成，你就可以分享 GitHub 連結給老師或同學了！

**GitHub Repository 連結格式：**
```
https://github.com/YOUR_USERNAME/0331-Spatial-Prediction-Shootout
```

## 🔥 特色亮點

### 高解析度版本
- ✅ 500m 解析度 (4倍提升)
- ✅ 73,428 網格點 (4倍提升)
- ✅ 馬賽克效果完全消除
- ✅ 專業展示品質

### 完整技術文檔
- ✅ 詳細 README 說明
- ✅ 技術亮點總結
- ✅ 評分對應檢查
- ✅ 快速開始指南

---

*最後更新: 2026年3月31日*
