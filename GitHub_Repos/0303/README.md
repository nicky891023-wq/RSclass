# 避難收容處所點位檔案v9 資料稽核與修正

## 專案概述

本專案對台灣避難收容處所點位檔案進行全面的資料品質稽核與修正，確保空間資料的準確性和可用性。

## 檔案結構

```
├── data/                          # 資料檔案
│   ├── 避難收容處所點位檔案v9.csv          # 原始資料
│   └── 避難收容處所點位檔案v9_clean_updated.csv  # 清理後資料
├── scripts/                       # 分析腳本
│   ├── clean_csv_updated.py       # 主要清理腳本
│   ├── coordinate_system_check.py # 座標系統驗證
│   ├── duplicate_analysis.py      # 重複記錄分析
│   ├── zero_value_analysis.py     # 零值有效性分析
│   ├── data_audit.py              # 基本稽核
│   └── detailed_analysis.py      # 詳細分析
├── audit_report.md               # 完整稽核報告
├── ai_prompts.md                 # AI 提示記錄
├── reflection.md                 # 空間資料處理反思
├── requirements.txt              # Python 依賴
└── README.md                     # 本檔案
```

## 主要發現

### 資料概覽
- **總筆數**: 5,973 筆避難收容處所記錄
- **欄位數**: 15 個原始欄位 + 6 個品質標記欄位
- **地理範圍**: 台灣本島及離島地區

### 資料品質問題
1. **座標系統**: ✅ 確認使用 WGS84 經緯度，無 TWD97 TM2 誤判問題
2. **座標異常**: 3 筆經度零值，已設為 NA
3. **重複記錄**: 
   - 同名同地址: 30 筆 (15 組)
   - 同座標: 533 筆 (228 組)
   - 近似座標: 434 筆 (350 組)
4. **電話格式**: 375 筆格式異常，已修正
5. **容量零值**: 58 筆，經分析確認為有效值，保留原始資料
6. **缺失值**: 村里 209 筆、災害類別 184 筆、地址 3 筆

## 使用方法

### 環境設定
```bash
# 安裝依賴
pip install -r requirements.txt
```

### 執行資料清理
```bash
# 執行完整清理流程
python scripts/clean_csv_updated.py

# 執行各項分析
python scripts/coordinate_system_check.py
python scripts/duplicate_analysis.py
python scripts/zero_value_analysis.py
```

### 驗證結果
```python
import pandas as pd

# 讀取清理後資料
df = pd.read_csv('data/避難收容處所點位檔案v9_clean_updated.csv')

# 檢查品質標記
print("座標品質分布:", df['座標品質'].value_counts())
print("地址完整性分布:", df['地址完整性'].value_counts())
print("座標重複分布:", df['座標重複'].value_counts())
print("疑似重複分布:", df['疑似重複'].value_counts())
print("容量狀態分布:", df['容量狀態'].value_counts())
```

## 重要原則

### 保守處理原則
- 嚴格遵循「不要猜」原則
- 未進行地理編碼推測補值
- 所有不確定的值都標記為 NA 而非猜測

### 空間資料安全
- 確認無座標系統錯誤 (TWD97 TM2 vs WGS84)
- 確認無經緯度互換錯誤
- 僅處理明確無效的座標值

### 可追溯性
- 所有修正都有完整日誌記錄
- 新增 6 個品質標記欄位提供透明度
- 提供完整的再現步驟

## 報告文件

- [audit_report.md](audit_report.md) - 完整的資料品質稽核報告
- [ai_prompts.md](ai_prompts.md) - AI 處理過程記錄
- [reflection.md](reflection.md) - 空間資料處理反思與改進建議

## 技術規格

- **Python 版本**: 3.7+
- **主要套件**: pandas, numpy
- **編碼**: UTF-8
- **座標系統**: WGS84 經緯度

## 注意事項

1. 本專案嚴格遵循資料治理最佳實務
2. 所有清理過程都可重現
3. 建議在使用清理後資料前，人工確認高風險問題
4. 極大容量記錄 (8 筆 >10,000人) 需要專業評估

## 授權

本專案僅供學術研究和資料品質改善使用。

---

**更新日期**: 2026-03-03  
**版本**: v2.0 (更新版)  
**狀態**: 已完成深度空間資料錯誤檢查
