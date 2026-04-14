# GitHub Repository 建立指南

## 📋 建立步驟

### 1. 建立 GitHub Repository
1. 前往 [GitHub](https://github.com)
2. 點擊右上角的 "+" → "New repository"
3. Repository 名稱：`0324-ARIA-v3-Dynamic-Risk-Monitoring`
4. 描述：`ARIA v3.0 動態風險監測系統 - Week 5 遙測與空間資訊分析`
5. 設定為 **Public**（或 Private 如果你想要私人的）
6. **不要**勾選 "Add a README file"（我們已經有了）
7. **不要**勾選 "Add .gitignore"（我們已經有了）
8. 點擊 "Create repository"

### 2. 連接本地 Repository 到 GitHub
建立完成後，GitHub 會顯示以下命令。請複製並執行：

```bash
git remote add origin https://github.com/YOUR_USERNAME/0324-ARIA-v3-Dynamic-Risk-Monitoring.git
git branch -M main
git push -u origin main
```

### 3. 驗證上傳
上傳完成後，你可以在 GitHub 網頁上看到：
- 📁 **課程練習資料夾**：`Week5-Student.ipynb`
- 📁 **作業資料夾**：`ARIA_v3.ipynb`
- 📁 **輸出檔案**：`output/` 目錄下的 HTML 和 JSON 檔案
- 📁 **文件**：`README.md`, `Homework-Week5.md`
- 📁 **環境設定**：`.env`, `requirements.txt`, `environment.yml`

## 🎯 Repository 結構

```
0324-ARIA-v3-Dynamic-Risk-Monitoring/
├── 📓 Week5-Student.ipynb          # 課程練習
├── 📓 ARIA_v3.ipynb               # 完整作業系統
├── 📄 README.md                   # 專案說明
├── 📄 Homework-Week5.md           # 作業要求
├── 📁 output/                     # 系統輸出
│   ├── ARIA_v3_Fungwong.html      # ARIA v3.0 互動地圖
│   ├── rainfall_map_week5.html    # Week 5 練習地圖
│   └── shelter_risk_audit_week5.json # 風險稽核報告
├── 📄 .env                        # 環境變數（已忽略）
├── 📄 requirements.txt            # Python 套件
├── 📄 environment.yml             # Conda 環境
├── 🌀 fungwong_202511.json        # 鳳凰颱風資料
├── 🏠 避難收容處所點位檔案v9 (1).csv # 避難所資料
├── 🗺️ TOWN_MOI_1120317.*         # 鄉鎮界線
└── 🌊 riverpoly/                  # 河川資料
```

## 🚀 快速指令

如果你想要快速完成，請執行：

```bash
# 1. 替換 YOUR_USERNAME 為你的 GitHub 使用者名稱
git remote add origin https://github.com/YOUR_USERNAME/0324-ARIA-v3-Dynamic-Risk-Monitoring.git

# 2. 推送到 GitHub
git branch -M main
git push -u origin main
```

## ✅ 驗證清單

上傳完成後請確認：
- [ ] 兩個 .ipynb 檔案都正確顯示
- [ ] output/ 目錄下的檔案都存在
- [ ] README.md 正確顯示格式
- [ ] .env 檔案被正確忽略（不應出現在 GitHub 上）

## 🎉 完成！

一旦上傳完成，你就可以分享 GitHub 連結給老師或同學了！

**GitHub Repository 連結格式：**
```
https://github.com/YOUR_USERNAME/0324-ARIA-v3-Dynamic-Risk-Monitoring
```
