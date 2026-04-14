import pandas as pd
import numpy as np

def detailed_analysis():
    df = pd.read_csv('data/避難收容處所點位檔案v9.csv')
    
    print('=== 詳細座標異常分析 ===')
    # 經度異常
    invalid_lon = df[(df['經度'] < 100) | (df['經度'] > 130)]
    print(f'經度異常筆數: {len(invalid_lon)}')
    if len(invalid_lon) > 0:
        print(invalid_lon[['序號', '避難收容處所名稱', '經度', '緯度']].head())
    
    # 零值座標
    zero_coords = df[(df['經度'] == 0) | (df['緯度'] == 0)]
    print(f'\n零值座標筆數: {len(zero_coords)}')
    if len(zero_coords) > 0:
        print(zero_coords[['序號', '避難收容處所名稱', '經度', '緯度']].head())
    
    print('\n=== 重複座標詳細分析 ===')
    # 找出重複座標
    coord_groups = df.groupby(['經度', '緯度']).size().reset_index(name='count')
    duplicate_coords = coord_groups[coord_groups['count'] > 1]
    print(f'重複座標組數: {len(duplicate_coords)}')
    print(f'涉及總筆數: {duplicate_coords["count"].sum()}')
    
    # 顯示重複最多的座標
    if len(duplicate_coords) > 0:
        print('\n重複最多的座標:')
        top_duplicates = duplicate_coords.nlargest(5, 'count')
        for _, row in top_duplicates.iterrows():
            print(f'座標({row["經度"]:.6f}, {row["緯度"]:.6f}): {row["count"]}筆')
            locations = df[(df['經度'] == row['經度']) & (df['緯度'] == row['緯度'])]
            print(f'  地點: {locations["避難收容處所名稱"].tolist()[:3]}...')
    
    print('\n=== 電話格式異常分析 ===')
    phone_issues = []
    for idx, phone in enumerate(df['管理人電話']):
        if pd.notna(phone):
            phone_str = str(phone)
            # 檢查是否包含非數字字符（除了-、#、空格）
            if not all(c.isdigit() or c in '-# ' for c in phone_str):
                phone_issues.append((idx, phone_str))
    
    print(f'電話格式異常筆數: {len(phone_issues)}')
    if len(phone_issues) > 0:
        print('異常電話範例:')
        for i, (idx, phone) in enumerate(phone_issues[:5]):
            print(f'  {idx}: {phone}')
    
    print('\n=== 極大容量分析 ===')
    extreme_capacity = df[df['預計收容人數'] > 10000]
    print(f'極大容量筆數: {len(extreme_capacity)}')
    if len(extreme_capacity) > 0:
        print(extreme_capacity[['序號', '避難收容處所名稱', '預計收容人數']].head())
    
    print('\n=== 缺失值模式分析 ===')
    # 同時缺失村里和地址的記錄
    missing_both = df[df['村里'].isna() & df['避難收容處所地址'].isna()]
    print(f'村里和地址都缺失: {len(missing_both)}筆')
    
    # 缺失災害類別的記錄特徵
    missing_disaster = df[df['適用災害類別'].isna()]
    print(f'災害類別缺失記錄的容量統計:')
    print(f'  平均容量: {missing_disaster["預計收容人數"].mean():.1f}')
    print(f'  零容量比例: {(missing_disaster["預計收容人數"] == 0).sum() / len(missing_disaster) * 100:.1f}%')
    
    print('\n=== 縣市分布檢查 ===')
    county_dist = df['縣市及鄉鎮市區'].str.split('[縣市]').str[0].value_counts()
    print('縣市分布:')
    print(county_dist.head(10))
    
    return df

if __name__ == "__main__":
    df = detailed_analysis()
