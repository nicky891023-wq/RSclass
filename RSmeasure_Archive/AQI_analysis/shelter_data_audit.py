import pandas as pd
import numpy as np
import re
from collections import defaultdict

def audit_shelter_data(csv_file):
    """
    審計避難所資料，找出坐標問題
    """
    print("開始審計避難所資料...")
    
    # 讀取 CSV 檔案
    try:
        df = pd.read_csv(csv_file, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(csv_file, encoding='big5')
        except:
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
    
    print(f"資料總筆數: {len(df)}")
    print(f"欄位: {list(df.columns)}")
    
    # 初始化問題統計
    issues = {
        'missing_coordinates': [],
        'invalid_coordinates': [],
        'extreme_coordinates': [],
        'duplicate_coordinates': [],
        'coordinate_format_issues': [],
        'missing_addresses': [],
        'inconsistent_data': []
    }
    
    # 檢查 1: 缺失坐標
    print("\n=== 檢查缺失坐標 ===")
    missing_lat = df['緯度'].isna() | (df['緯度'] == '') | (df['緯度'] == 0)
    missing_lon = df['經度'].isna() | (df['經度'] == '') | (df['經度'] == 0)
    missing_coords = missing_lat | missing_lon
    
    issues['missing_coordinates'] = df[missing_coords].index.tolist()
    print(f"缺失坐標的記錄: {len(issues['missing_coordinates'])} 筆")
    
    if len(issues['missing_coordinates']) > 0:
        print("缺失坐標的範例:")
        for idx in issues['missing_coordinates'][:5]:
            print(f"  序號 {df.loc[idx, '序號']}: {df.loc[idx, '避難收容處所名稱']} - 緯度: {df.loc[idx, '緯度']}, 經度: {df.loc[idx, '經度']}")
    
    # 檢查 2: 無效坐標值
    print("\n=== 檢查無效坐標值 ===")
    def is_valid_coordinate(lat, lon):
        try:
            lat = float(lat)
            lon = float(lon)
            # 台灣坐標範圍檢查
            return (21.5 <= lat <= 25.5) and (119.5 <= lon <= 122.5)
        except:
            return False
    
    invalid_mask = df.apply(lambda row: not is_valid_coordinate(row['緯度'], row['經度']), axis=1)
    issues['invalid_coordinates'] = df[invalid_mask].index.tolist()
    print(f"無效坐標的記錄: {len(issues['invalid_coordinates'])} 筆")
    
    if len(issues['invalid_coordinates']) > 0:
        print("無效坐標的範例:")
        for idx in issues['invalid_coordinates'][:5]:
            print(f"  序號 {df.loc[idx, '序號']}: {df.loc[idx, '避難收容處所名稱']} - 緯度: {df.loc[idx, '緯度']}, 經度: {df.loc[idx, '經度']}")
    
    # 檢查 3: 極端坐標值
    print("\n=== 檢查極端坐標值 ===")
    def is_extreme_coordinate(lat, lon):
        try:
            lat = float(lat)
            lon = float(lon)
            # 檢查是否在台灣邊界附近或超出合理範圍
            return (lat < 22.0 or lat > 25.0 or lon < 120.0 or lon > 122.0)
        except:
            return False
    
    extreme_mask = df.apply(lambda row: is_extreme_coordinate(row['緯度'], row['經度']), axis=1)
    issues['extreme_coordinates'] = df[extreme_mask].index.tolist()
    print(f"極端坐標的記錄: {len(issues['extreme_coordinates'])} 筆")
    
    if len(issues['extreme_coordinates']) > 0:
        print("極端坐標的範例:")
        for idx in issues['extreme_coordinates'][:5]:
            print(f"  序號 {df.loc[idx, '序號']}: {df.loc[idx, '避難收容處所名稱']} - 緯度: {df.loc[idx, '緯度']}, 經度: {df.loc[idx, '經度']}")
    
    # 檢查 4: 重複坐標
    print("\n=== 檢查重複坐標 ===")
    coordinate_counts = df.groupby(['緯度', '經度']).size().reset_index(name='count')
    duplicate_coords = coordinate_counts[coordinate_counts['count'] > 1]
    
    for _, row in duplicate_coords.iterrows():
        lat, lon, count = row['緯度'], row['經度'], row['count']
        matching_indices = df[(df['緯度'] == lat) & (df['經度'] == lon)].index.tolist()
        issues['duplicate_coordinates'].extend(matching_indices)
    
    print(f"重複坐標的記錄: {len(issues['duplicate_coordinates'])} 筆")
    
    if len(issues['duplicate_coordinates']) > 0:
        print("重複坐標的範例:")
        for _, row in duplicate_coords.head(3).iterrows():
            lat, lon, count = row['緯度'], row['經度'], row['count']
            matching_shelters = df[(df['緯度'] == lat) & (df['經度'] == lon)]['避難收容處所名稱'].tolist()
            print(f"  坐標 ({lat}, {lon}): {count} 個避難所 - {matching_shelters[:3]}")
    
    # 檢查 5: 坐標格式問題
    print("\n=== 檢查坐標格式問題 ===")
    def has_coordinate_format_issues(lat, lon):
        try:
            lat_str = str(lat)
            lon_str = str(lon)
            # 檢查是否有過多小數位（可能為轉換錯誤）
            if '.' in lat_str and len(lat_str.split('.')[1]) > 8:
                return True
            if '.' in lon_str and len(lon_str.split('.')[1]) > 8:
                return True
            # 檢查是否包含非數字字符
            if not re.match(r'^-?\d+\.?\d*$', lat_str) or not re.match(r'^-?\d+\.?\d*$', lon_str):
                return True
            return False
        except:
            return True
    
    format_issues_mask = df.apply(lambda row: has_coordinate_format_issues(row['緯度'], row['經度']), axis=1)
    issues['coordinate_format_issues'] = df[format_issues_mask].index.tolist()
    print(f"坐標格式問題的記錄: {len(issues['coordinate_format_issues'])} 筆")
    
    # 檢查 6: 缺失地址
    print("\n=== 檢查缺失地址 ===")
    missing_address = df['避難收容處所地址'].isna() | (df['避難收容處所地址'] == '') | (df['避難收容處所地址'] == '無門牌號碼')
    issues['missing_addresses'] = df[missing_address].index.tolist()
    print(f"缺失地址的記錄: {len(issues['missing_addresses'])} 筆")
    
    # 檢查 7: 資料不一致性
    print("\n=== 檢查資料不一致性 ===")
    # 檢查村里與地址是否一致
    inconsistent_data = []
    for idx, row in df.iterrows():
        village = str(row['村里']) if pd.notna(row['村里']) else ''
        address = str(row['避難收容處所地址']) if pd.notna(row['避難收容處所地址']) else ''
        
        # 簡單檢查：如果村里有值但地址為空，或地址不包含村里名稱
        if village and address and village not in address:
            inconsistent_data.append(idx)
    
    issues['inconsistent_data'] = inconsistent_data
    print(f"資料不一致的記錄: {len(issues['inconsistent_data'])} 筆")
    
    return issues, df

def generate_audit_report(issues, df, output_file='audit_report.md'):
    """
    生成審計報告
    """
    total_records = len(df)
    
    report_content = f"""# 避難所資料審計報告

## 資料概覽
- **總記錄數**: {total_records} 筆
- **審計時間**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## 發現的問題

### 1. 缺失坐標 ({len(issues['missing_coordinates'])} 筆)
**問題描述**: 緯度或經度欄位為空、零值或無效值

**影響程度**: 🔴 高 - 無法在地圖上定位這些避難所

**範例記錄**:
"""
    
    # 添加缺失坐標範例
    if len(issues['missing_coordinates']) > 0:
        for idx in issues['missing_coordinates'][:3]:
            report_content += f"- 序號 {df.loc[idx, '序號']}: {df.loc[idx, '避難收容處所名稱']} - 緯度: {df.loc[idx, '緯度']}, 經度: {df.loc[idx, '經度']}\n"
    
    report_content += f"""
### 2. 無效坐標 ({len(issues['invalid_coordinates'])} 筆)
**問題描述**: 坐標值不在台灣合理範圍內 (緯度 21.5-25.5, 經度 119.5-122.5)

**影響程度**: 🔴 高 - 坐標可能錯誤，導致定位不準

**範例記錄**:
"""
    
    # 添加無效坐標範例
    if len(issues['invalid_coordinates']) > 0:
        for idx in issues['invalid_coordinates'][:3]:
            report_content += f"- 序號 {df.loc[idx, '序號']}: {df.loc[idx, '避難收容處所名稱']} - 緯度: {df.loc[idx, '緯度']}, 經度: {df.loc[idx, '經度']}\n"
    
    report_content += f"""
### 3. 極端坐標 ({len(issues['extreme_coordinates'])} 筆)
**問題描述**: 坐標值在台灣邊界附近或超出常見範圍

**影響程度**: 🟡 中 - 可能為轉換錯誤或特殊位置

**範例記錄**:
"""
    
    # 添加極端坐標範例
    if len(issues['extreme_coordinates']) > 0:
        for idx in issues['extreme_coordinates'][:3]:
            report_content += f"- 序號 {df.loc[idx, '序號']}: {df.loc[idx, '避難收容處所名稱']} - 緯度: {df.loc[idx, '緯度']}, 經度: {df.loc[idx, '經度']}\n"
    
    report_content += f"""
### 4. 重複坐標 ({len(issues['duplicate_coordinates'])} 筆)
**問題描述**: 多個避難所使用相同的坐標

**影響程度**: 🟡 中 - 可能為資料輸入錯誤或同一地點多個名稱

**範例記錄**:
"""
    
    # 添加重複坐標範例
    coordinate_counts = df.groupby(['緯度', '經度']).size().reset_index(name='count')
    duplicate_coords = coordinate_counts[coordinate_counts['count'] > 1]
    
    for _, row in duplicate_coords.head(3).iterrows():
        lat, lon, count = row['緯度'], row['經度'], row['count']
        matching_shelters = df[(df['緯度'] == lat) & (df['經度'] == lon)]['避難收容處所名稱'].tolist()
        report_content += f"- 坐標 ({lat}, {lon}): {count} 個避難所 - {matching_shelters[:3]}\n"
    
    report_content += f"""
### 5. 坐標格式問題 ({len(issues['coordinate_format_issues'])} 筆)
**問題描述**: 坐標值包含非數字字符或過多小數位

**影響程度**: 🟡 中 - 可能影響資料處理和顯示

### 6. 缺失地址 ({len(issues['missing_addresses'])} 筆)
**問題描述**: 地址欄位為空或無效

**影響程度**: 🟡 中 - 影響避難所識別和導航

### 7. 資料不一致性 ({len(issues['inconsistent_data'])} 筆)
**問題描述**: 村里名稱與地址不一致

**影響程度**: 🟢 低 - 可能為行政區劃調整或輸入錯誤

## 統計摘要
"""
    
    # 計算問題統計
    total_issues = sum(len(issue_list) for issue_list in issues.values())
    report_content += f"""
- **總問題數**: {total_issues} 個
- **問題記錄數**: {len(set(idx for issue_list in issues.values() for idx in issue_list))} 筆 ({len(set(idx for issue_list in issues.values() for idx in issue_list))/total_records*100:.1f}%)
- **資料品質評分**: {max(0, 100 - (total_issues / total_records * 100)):.1f}/100

## 建議改善措施
1. **高優先級**: 修復缺失坐標和無效坐標問題
2. **中優先級**: 檢查重複坐標和極端坐標
3. **低優先級**: 統一資料格式和地址格式

## 技術說明
- **坐標範圍檢查**: 台灣主島緯度 21.5-25.5°N，經度 119.5-122.5°E
- **重複坐標檢測**: 基於完全相同的經緯度值
- **格式檢查**: 數字格式和小數位數合理性
"""
    
    # 保存報告
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"審計報告已保存至: {output_file}")
    return report_content

def main():
    """
    主程式
    """
    csv_file = 'data/shelters.csv'
    
    try:
        # 執行審計
        issues, df = audit_shelter_data(csv_file)
        
        # 生成報告
        report_content = generate_audit_report(issues, df)
        
        print("\n=== 審計完成 ===")
        print(f"發現 {sum(len(issue_list) for issue_list in issues.values())} 個問題")
        print("詳細報告請查看 audit_report.md")
        
    except Exception as e:
        print(f"審計過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
