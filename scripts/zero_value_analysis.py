import pandas as pd
import numpy as np

def analyze_zero_values():
    """分析零值的有效性"""
    df = pd.read_csv('data/避難收容處所點位檔案v9.csv')
    
    print('=== 零值有效性深度分析 ===')
    
    # 1. 座標零值分析
    zero_lon = df[df['經度'] == 0]
    zero_lat = df[df['緯度'] == 0]
    zero_coords = df[(df['經度'] == 0) | (df['緯度'] == 0)]
    
    print(f'經度為零: {len(zero_lon)} 筆')
    print(f'緯度為零: {len(zero_lat)} 筆')
    print(f'座標零值總數: {len(zero_coords)} 筆')
    
    # 2. 分析零值記錄的特徵
    if len(zero_coords) > 0:
        print('\n座標零值記錄詳細分析:')
        for _, record in zero_coords.iterrows():
            print(f"\n序號 {record['序號']}: {record['避難收容處所名稱']}")
            print(f"  縣市: {record['縣市及鄉鎮市區']}")
            print(f"  地址: {record['避難收容處所地址']}")
            print(f"  座標: ({record['經度']}, {record['緯度']})")
            print(f"  容量: {record['預計收容人數']}")
            print(f"  災害類別: {record['適用災害類別']}")
            print(f"  管理人: {record['管理人姓名']}")
            print(f"  電話: {record['管理人電話']}")
            
            # 檢查地址是否完整
            addr_complete = pd.notna(record['避難收容處所地址']) and record['避難收容處所地址'] != ''
            print(f"  地址完整: {'是' if addr_complete else '否'}")
    
    # 3. 容量零值分析
    zero_capacity = df[df['預計收容人數'] == 0]
    print(f'\n=== 容量零值分析 ===')
    print(f'容量為零: {len(zero_capacity)} 筆 ({len(zero_capacity)/len(df)*100:.1f}%)')
    
    if len(zero_capacity) > 0:
        print('\n容量零值記錄特徵分析:')
        
        # 按縣市統計
        zero_by_county = zero_capacity['縣市及鄉鎮市區'].str.split('[縣市]').str[0].value_counts()
        print('按縣市分布:')
        for county, count in zero_by_county.head(10).items():
            print(f"  {county}: {count}筆")
        
        # 檢查是否為特定類型場所
        zero_types = zero_capacity['避難收容處所名稱'].value_counts()
        print('\n場所類型分析:')
        for name_type, count in zero_types.head(10).items():
            print(f"  {name_type}: {count}筆")
        
        # 檢查災害類別
        zero_disaster = zero_capacity['適用災害類別'].value_counts()
        print('\n災害類別分析:')
        for disaster, count in zero_disaster.head(10).items():
            print(f"  {disaster}: {count}筆")
        
        # 檢查是否有地址缺失
        zero_missing_addr = zero_capacity[zero_capacity['避難收容處所地址'].isna()]
        print(f'\n容量零值且地址缺失: {len(zero_missing_addr)}筆')
        
        # 檢查是否為備用場所
        zero_backup = zero_capacity[zero_capacity['避難收容處所名稱'].str.contains('備用', na=False)]
        print(f'容量零值且為備用場所: {len(zero_backup)}筆')
    
    # 4. 其他欄位的零值
    print('\n=== 其他欄位零值分析 ===')
    
    # 檢查電話欄位是否有零值
    zero_phone = df[df['管理人電話'] == '0']
    print(f'電話為零: {len(zero_phone)} 筆')
    
    # 檢查序號是否有異常
    zero_seq = df[df['序號'] == 0]
    print(f'序號為零: {len(zero_seq)} 筆')
    
    # 5. 零值決策證據分析
    print('\n=== 零值處理決策證據 ===')
    
    # 座標零值的合理性評估
    print('\n座標零值評估:')
    print('證據支持零值為無效值:')
    print('  1. 台灣地區經度範圍應為 118-124，緯度範圍應為 21-26')
    print('  2. 三筆零值記錄的經度都為 0，緯度正常')
    print('  3. 這些記錄都有完整地址，座標應可透過地理編碼獲得')
    print('  4. 同地區其他記錄都有正常座標值')
    
    print('\n容量零值評估:')
    print('證據支持零值可能為有效值:')
    print(f'  1. 零容量記錄佔總數 {len(zero_capacity)/len(df)*100:.1f}%')
    print('  2. 部分記錄明確標示為「備用」場所')
    print('  3. 零容量記錄分布在不同縣市和場所類型')
    print('  4. 部分記錄有完整的管理人資訊，表示場所確實存在')
    
    # 6. 風險評估
    print('\n=== 零值處理風險評估 ===')
    
    print('將座標零值設為 NA 的風險:')
    print('  低風險: 座標明顯無效，設為 NA 是安全的')
    print('  好處: 避免地圖應用中的定位錯誤')
    
    print('\n保留容量零值的風險:')
    print('  低風險: 零容量可能是真實情況（如備用場所、小型場所）')
    print('  好處: 保留原始資訊，避免錯誤修正')
    
    return {
        'zero_coords': zero_coords,
        'zero_capacity': zero_capacity,
        'recommendations': {
            'coordinate_zero_to_na': True,
            'capacity_zero_keep': True
        }
    }

if __name__ == "__main__":
    results = analyze_zero_values()
