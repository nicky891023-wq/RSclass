# 資料夾結構指南

## 📁 目錄概覽

```
0324/
├── Week5_Output/          # Week 5 相關檔案
├── Week6_Lab/            # Week 6 課程練習
├── Week6_Homework/       # Week 6 課後作業
├── Week6_Audit_Report.md # Week 6 檢核報告
├── [共用檔案...]        # 環境設定、資料檔案等
└── [其他資料夾...]      # Git、output 等
```

---

## 📂 資料夾說明

### 📘 Week5_Output/
**用途**: Week 5 所有相關檔案
**內容**:
- `Week5-Student.ipynb` - Week 5 課程練習
- `Homework-Week5.md` - Week 5 作業說明

### 🧪 Week6_Lab/
**用途**: Week 6 課程練習實作
**內容**:
- `Week6-Student.ipynb` - 課程練習模板
- `Week6-Executed.ipynb` - 課程練習執行結果 ⭐
- `Week6-Test-Run.ipynb` - 測試執行
- `*.png` - 課程練習圖表 (6個)
- `*.tif` - 課程練習 GeoTIFF (3個)

### 📝 Week6_Homework/
**用途**: Week 6 課後作業完整內容
**內容**:
- `Week6_Final_Submission.ipynb` - 最終作業繳交版本 ⭐
- `Week6_Shootout.ipynb` - 作業分析筆記本
- `week6_homework_execution.py` - 執行腳本
- `fungwong_202511.json` - 原始資料
- `event*.png` - 作業圖表 (6個)
- `cross_event_variogram_comparison.png` - 跨事件比較

### 📊 Week6_Audit_Report.md
**用途**: 完整的檢核報告
**內容**: 詳細的檢核結果、評分對應、改進建議

---

## 🎯 快速導航

### 🚀 如果要查看 Week 6 課程練習結果
```bash
cd Week6_Lab/
jupyter notebook Week6-Executed.ipynb
```

### 📋 如果要繳交 Week 6 作業
```bash
cd Week6_Homework/
# 主要繳交檔案: Week6_Final_Submission.ipynb
# 配合檔案: 所有 *.png 和 *.tif 檔案
```

### 📖 如果要檢視完整檢核報告
```bash
# 直接開啟: Week6_Audit_Report.md
```

---

## 📈 檔案統計

| 資料夾 | 檔案數 | 總大小 | 主要內容 |
|--------|--------|--------|----------|
| Week5_Output | 2 | 8.36 MB | Week 5 練習 |
| Week6_Lab | 10 | 2.13 MB | Week 6 課程練習 |
| Week6_Homework | 11 | 2.30 MB | Week 6 課後作業 |
| **總計** | **23** | **12.79 MB** | **Week 5+6 完整內容** |

---

## 🔄 檔案關聯圖

```
Week6_Lab/Week6-Executed.ipynb (課程練習)
    ↓ 基礎學習
Week6_Homework/Week6_Final_Submission.ipynb (作業繳交)
    ↓ 深度應用
Week6_Audit_Report.md (檢核報告)
```

---

## 💡 使用建議

### 🎓 學習路徑
1. 先看 `Week6_Lab/Week6-Executed.ipynb` 了解課程內容
2. 再看 `Week6_Homework/Week6_Final_Submission.ipynb` 了解作業完成度
3. 最後看 `Week6_Audit_Report.md` 了解整體評估

### 📤 繳交建議
- **主要**: `Week6_Homework/Week6_Final_Submission.ipynb`
- **圖表**: `Week6_Homework/*.png` (6個檔案)
- **資料**: `Week6_Homework/fungwong_202511.json`

### 🔍 檢查清單
- [x] Week 5 和 Week 6 檔案完全分離
- [x] 資料夾結構清晰明瞭
- [x] 檔案命名規範一致
- [x] 重要檔案都有備份

---

*最後更新: 2026年3月31日*
