import pandas as pd
import numpy as np

def audit_data():
    # 讀取資料
    df = pd.read_csv('data/避難收容處所點位檔案v9.csv')
    
    print('=== 基本統計 ===')
    print(f'總筆數: {len(df)}')
    print(f'欄位數: {len(df.columns)}')
    
    print('\n=== 座標分析 ===')
    print(f'經度範圍: {df["經度"].min():.6f} ~ {df["經度"].max():.6f}')
    print(f'緯度範圍: {df["緯度"].min():.6f} ~ {df["緯度"].max():.6f}')
    
    # 檢查異常座標
    invalid_lon = df[(df['經度'] < 100) | (df['經度'] > 130)].shape[0]
    invalid_lat = df[(df['緯度'] < 15) | (df['緯度'] > 30)].shape[0]
    zero_coords = df[(df['經度'] == 0) | (df['緯度'] == 0)].shape[0]
    
    print(f'經度異常值: {invalid_lon} 筆')
    print(f'緯度異常值: {invalid_lat} 筆')
    print(f'零值座標: {zero_coords} 筆')
    
    print('\n=== 重複檢查 ===')
    # 完全重複
    exact_duplicates = df.duplicated().sum()
    print(f'完全重複: {exact_duplicates} 筆')
    
    # 同名同地址
    name_addr_duplicates = df.duplicated(subset=['避難收容處所名稱', '避難收容處所地址']).sum()
    print(f'同名同地址: {name_addr_duplicates} 筆')
    
    # 同座標不同名稱
    coord_duplicates = df.duplicated(subset=['經度', '緯度']).sum()
    print(f'同座標: {coord_duplicates} 筆')
    
    print('\n=== 電話格式檢查 ===')
    phone_issues = 0
    for phone in df['管理人電話']:
        if pd.notna(phone):
            phone_str = str(phone)
            # 檢查是否包含非數字字符（除了-、#、空格）
            if not all(c.isdigit() or c in '-# ' for c in phone_str):
                phone_issues += 1
    
    print(f'電話格式異常: {phone_issues} 筆')
    
    print('\n=== 容量檢查 ===')
    zero_capacity = (df['預計收容人數'] == 0).sum()
    negative_capacity = (df['預計收容人數'] < 0).sum()
    extreme_capacity = (df['預計收容人數'] > 10000).sum()
    
    print(f'零容量: {zero_capacity} 筆')
    print(f'負容量: {negative_capacity} 筆')
    print(f'極大容量(>10000): {extreme_capacity} 筆')
    
    print('\n=== 災害類別檢查 ===')
    missing_disaster = df['適用災害類別'].isna().sum()
    print(f'災害類別缺失: {missing_disaster} 筆')
    
    print('\n=== 村里缺失檢查 ===')
    missing_village = df['村里'].isna().sum()
    print(f'村里缺失: {missing_village} 筆')
    
    print('\n=== 地址缺失檢查 ===')
    missing_addr = df['避難收容處所地址'].isna().sum()
    print(f'地址缺失: {missing_addr} 筆')
    
    print('\n=== 特殊字符檢查 ===')
    # 檢查全形字符
    fullwidth_issues = 0
    for col in ['避難收容處所名稱', '避難收容處所地址', '管理人姓名']:
        for val in df[col].dropna():
            if any(ord(c) > 127 and ord(c) < 65536 for c in str(val)):
                # 檢查是否包含全形字符
                if any(ord(c) >= 0xFF00 and ord(c) <= 0xFFEF for c in str(val)):
                    fullwidth_issues += 1
                    break
    
    print(f'包含全形字符: {fullwidth_issues} 筆')
    
    return df

if __name__ == "__main__":
    df = audit_data()
