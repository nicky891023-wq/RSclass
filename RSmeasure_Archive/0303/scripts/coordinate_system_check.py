import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def analyze_coordinate_systems():
    """深入分析座標系統問題"""
    df = pd.read_csv('data/避難收容處所點位檔案v9.csv')
    
    print('=== 座標系統深度分析 ===')
    
    # 基本統計
    print(f'經度統計:')
    print(f'  最小值: {df["經度"].min():.6f}')
    print(f'  最大值: {df["經度"].max():.6f}')
    print(f'  平均值: {df["經度"].mean():.6f}')
    print(f'  標準差: {df["經度"].std():.6f}')
    
    print(f'\n緯度統計:')
    print(f'  最小值: {df["緯度"].min():.6f}')
    print(f'  最大值: {df["緯度"].max():.6f}')
    print(f'  平均值: {df["緯度"].mean():.6f}')
    print(f'  標準差: {df["緯度"].std():.6f}')
    
    # 檢查可能的 TWD97 TM2 座標
    print('\n=== TWD97 TM2 座標檢查 ===')
    
    # TWD97 TM2 的典型範圍 (台灣)
    tm2_x_range = (180000, 320000)  # 東西範圍
    tm2_y_range = (2400000, 2800000)  # 南北範圍
    
    # 檢查是否有座標落在 TM2 範圍
    possible_tm2_x = df[(df['經度'] >= tm2_x_range[0]) & (df['經度'] <= tm2_x_range[1])]
    possible_tm2_y = df[(df['緯度'] >= tm2_y_range[0]) & (df['緯度'] <= tm2_y_range[1])]
    
    print(f'可能的 TM2 X 座標 (經度欄位): {len(possible_tm2_x)} 筆')
    print(f'可能的 TM2 Y 座標 (緯度欄位): {len(possible_tm2_y)} 筆')
    
    # 檢查是否有座標明顯是 TM2 但被當作經緯度
    suspicious_tm2 = df[
        (df['經度'] >= 100000) & (df['經度'] <= 500000) &
        (df['緯度'] >= 2000000) & (df['緯度'] <= 3000000)
    ]
    
    print(f'疑似 TM2 座標被當作經緯度: {len(suspicious_tm2)} 筆')
    
    if len(suspicious_tm2) > 0:
        print('\n疑似 TM2 座標範例:')
        print(suspicious_tm2[['序號', '避難收容處所名稱', '經度', '緯度']].head(10))
    
    # 檢查經緯度互換的可能性
    print('\n=== 經緯度互換檢查 ===')
    
    # 正常台灣經緯度範圍
    normal_lon_range = (118, 124)
    normal_lat_range = (21, 26)
    
    # 檢查是否有經緯度可能互換
    swapped_possible = df[
        (df['經度'] >= normal_lat_range[0]) & (df['經度'] <= normal_lat_range[1]) &
        (df['緯度'] >= normal_lon_range[0]) & (df['緯度'] <= normal_lon_range[1]) &
        (df['經度'] < df['緯度'])  # 經度小於緯度是異常情況
    ]
    
    print(f'可能經緯度互換: {len(swapped_possible)} 筆')
    
    if len(swapped_possible) > 0:
        print('\n可能經緯度互換範例:')
        print(swapped_possible[['序號', '避難收容處所名稱', '經度', '緯度']].head(10))
    
    # 檢查零值的合理性
    print('\n=== 零值分析 ===')
    
    zero_coords = df[(df['經度'] == 0) | (df['緯度'] == 0)]
    print(f'零值座標記錄: {len(zero_coords)} 筆')
    
    if len(zero_coords) > 0:
        print('\n零值座標詳細資訊:')
        for _, record in zero_coords.iterrows():
            print(f"  序號{record['序號']}: {record['避難收容處所名稱']}")
            print(f"    縣市: {record['縣市及鄉鎮市區']}")
            print(f"    地址: {record['避難收容處所地址']}")
            print(f"    座標: ({record['經度']}, {record['緯度']})")
            print(f"    容量: {record['預計收容人數']}")
            print()
    
    # 檢查座標分布的合理性
    print('=== 座標分布分析 ===')
    
    # 移除零值和異常值後的分布
    valid_coords = df[
        (df['經度'] > 0) & (df['經度'] < 180) &
        (df['緯度'] > 0) & (df['緯度'] < 90)
    ]
    
    print(f'有效座標記錄: {len(valid_coords)} 筆')
    
    # 檢查是否有異常聚集
    coord_counts = valid_coords.groupby(['經度', '緯度']).size().reset_index(name='count')
    high_duplicates = coord_counts[coord_counts['count'] > 5]
    
    print(f'高度重複座標 (>5筆): {len(high_duplicates)} 組')
    
    if len(high_duplicates) > 0:
        print('\n高度重複座標詳情:')
        for _, record in high_duplicates.head(10).iterrows():
            print(f"  座標({record['經度']:.6f}, {record['緯度']:.6f}): {record['count']}筆")
    
    return {
        'suspicious_tm2': suspicious_tm2,
        'swapped_possible': swapped_possible,
        'zero_coords': zero_coords,
        'high_duplicates': high_duplicates
    }

if __name__ == "__main__":
    results = analyze_coordinate_systems()
