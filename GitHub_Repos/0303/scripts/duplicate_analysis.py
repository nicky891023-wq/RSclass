import pandas as pd
import numpy as np

def analyze_duplicates():
    """分析各種類型的重複記錄"""
    df = pd.read_csv('data/避難收容處所點位檔案v9.csv')
    
    print('=== 重複記錄深度分析 ===')
    
    # 1. 完全重複記錄
    exact_duplicates = df[df.duplicated(keep=False)]
    print(f'完全重複記錄: {len(exact_duplicates)} 筆')
    
    # 2. 同名同地址
    name_addr_duplicates = df[df.duplicated(subset=['避難收容處所名稱', '避難收容處所地址'], keep=False)]
    name_addr_groups = name_addr_duplicates.groupby(['避難收容處所名稱', '避難收容處所地址']).size().reset_index(name='count')
    name_addr_groups = name_addr_groups[name_addr_groups['count'] > 1]
    
    print(f'同名同地址重複: {len(name_addr_duplicates)} 筆，涉及 {len(name_addr_groups)} 組')
    
    if len(name_addr_groups) > 0:
        print('\n同名同地址重複詳情:')
        for _, group in name_addr_groups.head(10).iterrows():
            print(f"  名稱: {group['避難收容處所名稱']}")
            print(f"  地址: {group['避難收容處所地址']}")
            print(f"  重複次數: {group['count']}")
            print()
    
    # 3. 同座標不同名稱
    coord_duplicates = df[df.duplicated(subset=['經度', '緯度'], keep=False)]
    coord_groups = coord_duplicates.groupby(['經度', '緯度']).size().reset_index(name='count')
    coord_groups = coord_groups[coord_groups['count'] > 1]
    
    print(f'同座標記錄: {len(coord_duplicates)} 筆，涉及 {len(coord_groups)} 組')
    
    # 4. 近似座標 (小數點後3位相同)
    df['經度_3位'] = df['經度'].round(3)
    df['緯度_3位'] = df['緯度'].round(3)
    near_coord_duplicates = df[df.duplicated(subset=['經度_3位', '緯度_3位'], keep=False)]
    near_coord_groups = near_coord_duplicates.groupby(['經度_3位', '緯度_3位']).size().reset_index(name='count')
    near_coord_groups = near_coord_groups[near_coord_groups['count'] > 1]
    
    print(f'近似座標記錄 (小數點3位): {len(near_coord_duplicates)} 筆，涉及 {len(near_coord_groups)} 組')
    
    # 5. 相似地址 (去除空格和標點符號後比較)
    def normalize_address(addr):
        if pd.isna(addr):
            return ''
        # 移除空格、標點符號，轉為小寫
        import re
        return re.sub(r'[^\w]', '', str(addr)).lower()
    
    df['地址標準化'] = df['避難收容處所地址'].apply(normalize_address)
    addr_duplicates = df[df.duplicated(subset=['地址標準化'], keep=False)]
    addr_groups = addr_duplicates.groupby('地址標準化').size().reset_index(name='count')
    addr_groups = addr_groups[addr_groups['count'] > 1]
    
    print(f'相似地址記錄: {len(addr_duplicates)} 筆，涉及 {len(addr_groups)} 組')
    
    # 6. 相似名稱
    def normalize_name(name):
        if pd.isna(name):
            return ''
        import re
        # 移除常見後綴，標準化
        name = re.sub(r'[（）()]\w*[）)]$', '', str(name))  # 移除括號內容
        name = re.sub(r'（備用）', '', name)
        name = re.sub(r'\s+', '', name)  # 移除空格
        return name.lower()
    
    df['名稱標準化'] = df['避難收容處所名稱'].apply(normalize_name)
    name_duplicates = df[df.duplicated(subset=['名稱標準化'], keep=False)]
    name_groups = name_duplicates.groupby('名稱標準化').size().reset_index(name='count')
    name_groups = name_groups[name_groups['count'] > 1]
    
    print(f'相似名稱記錄: {len(name_duplicates)} 筆，涉及 {len(name_groups)} 組')
    
    # 7. 疑似重複綜合分析
    print('\n=== 疑似重複綜合統計 ===')
    
    # 找出有多種重複類型的記錄
    suspicious_records = pd.DataFrame()
    
    # 同座標且地址相似
    coord_addr_similar = df[
        df.duplicated(subset=['經度', '緯度'], keep=False) & 
        df.duplicated(subset=['地址標準化'], keep=False)
    ]
    
    # 同座標且名稱相似  
    coord_name_similar = df[
        df.duplicated(subset=['經度', '緯度'], keep=False) & 
        df.duplicated(subset=['名稱標準化'], keep=False)
    ]
    
    print(f'同座標且地址相似: {len(coord_addr_similar)} 筆')
    print(f'同座標且名稱相似: {len(coord_name_similar)} 筆')
    
    # 8. 生成疑似重複清單
    suspicious_list = []
    
    # 高重複座標 (>5筆)
    high_coord_dups = coord_groups[coord_groups['count'] > 5]
    for _, group in high_coord_dups.iterrows():
        records = df[(df['經度'] == group['經度']) & (df['緯度'] == group['緯度'])]
        suspicious_list.append({
            '類型': '高重複座標',
            '座標': f"({group['經度']:.6f}, {group['緯度']:.6f})",
            '數量': group['count'],
            '記錄': records['避難收容處所名稱'].tolist()[:5]
        })
    
    # 同名同地址
    for _, group in name_addr_groups.iterrows():
        records = df[(df['避難收容處所名稱'] == group['避難收容處所名稱']) & 
                   (df['避難收容處所地址'] == group['避難收容處所地址'])]
        suspicious_list.append({
            '類型': '同名同地址',
            '名稱': group['避難收容處所名稱'],
            '地址': group['避難收容處所地址'],
            '數量': group['count'],
            '記錄': records['序號'].tolist()
        })
    
    return {
        'exact_duplicates': exact_duplicates,
        'name_addr_duplicates': name_addr_duplicates,
        'coord_duplicates': coord_duplicates,
        'near_coord_duplicates': near_coord_duplicates,
        'addr_duplicates': addr_duplicates,
        'name_duplicates': name_duplicates,
        'suspicious_list': suspicious_list
    }

if __name__ == "__main__":
    results = analyze_duplicates()
