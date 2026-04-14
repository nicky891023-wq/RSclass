import pandas as pd
import numpy as np
import re
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_coordinate_system(df):
    """驗證座標系統，確認沒有 TWD97 TM2 被誤當作經緯度"""
    logger.info("驗證座標系統...")
    
    # 檢查 TWD97 TM2 範圍
    tm2_x_range = (180000, 320000)
    tm2_y_range = (2400000, 2800000)
    
    suspicious_tm2 = df[
        (df['經度'] >= tm2_x_range[0]) & (df['經度'] <= tm2_x_range[1]) &
        (df['緯度'] >= tm2_y_range[0]) & (df['緯度'] <= tm2_y_range[1])
    ]
    
    logger.info(f"疑似 TWD97 TM2 座標被當作經緯度: {len(suspicious_tm2)} 筆")
    
    if len(suspicious_tm2) > 0:
        logger.warning("發現疑似 TWD97 TM2 座標，需要專業處理")
        return False
    
    # 檢查經緯度範圍合理性 (台灣地區)
    tw_lon_range = (118, 124)
    tw_lat_range = (21, 26)
    
    valid_coords = df[
        (df['經度'] >= tw_lon_range[0]) & (df['經度'] <= tw_lon_range[1]) &
        (df['緯度'] >= tw_lat_range[0]) & (df['緯度'] <= tw_lat_range[1])
    ]
    
    logger.info(f"台灣地區合理座標: {len(valid_coords)} 筆")
    
    return len(suspicious_tm2) == 0

def clean_coordinate_data(df):
    """修正座標資料 - 僅處理明確無效的座標"""
    logger.info("開始修正座標資料...")
    
    # 統計修正前狀況
    zero_coords_before = df[(df['經度'] == 0) | (df['緯度'] == 0)].shape[0]
    invalid_lon_before = df[(df['經度'] < 100) | (df['經度'] > 130)].shape[0]
    invalid_lat_before = df[(df['緯度'] < 15) | (df['緯度'] > 30)].shape[0]
    
    df_clean = df.copy()
    
    # 僅處理明確無效的座標值
    # 經度為 0 是明確錯誤 (台灣經度範圍 118-124)
    zero_lon_mask = df_clean['經度'] == 0
    df_clean.loc[zero_lon_mask, '經度'] = np.nan
    
    # 統計修正後狀況
    zero_coords_after = df_clean[df_clean['經度'].isna()].shape[0]
    
    logger.info(f"座標修正: 經度零值 {zero_coords_before}筆 -> 設為NA")
    logger.info(f"座標修正後缺失經度: {zero_coords_after}筆")
    
    # 證明沒有處理緯度零值 (因為沒有發現)
    zero_lat_count = (df['緯度'] == 0).sum()
    logger.info(f"緯度零值記錄: {zero_lat_count}筆 (未處理，因為可能是有效值)")
    
    return df_clean

def analyze_duplicates_comprehensive(df):
    """全面分析重複記錄"""
    logger.info("開始全面重複分析...")
    
    # 1. 完全重複
    exact_duplicates = df.duplicated().sum()
    logger.info(f"完全重複記錄: {exact_duplicates} 筆")
    
    # 2. 同名同地址
    name_addr_duplicates = df.duplicated(subset=['避難收容處所名稱', '避難收容處所地址']).sum()
    logger.info(f"同名同地址重複: {name_addr_duplicates} 筆")
    
    # 3. 同座標
    coord_duplicates = df.duplicated(subset=['經度', '緯度']).sum()
    logger.info(f"同座標重複: {coord_duplicates} 筆")
    
    # 4. 近似座標 (小數點後3位)
    df_temp = df.copy()
    df_temp['經度_3位'] = df_temp['經度'].round(3)
    df_temp['緯度_3位'] = df_temp['緯度'].round(3)
    near_coord_duplicates = df_temp.duplicated(subset=['經度_3位', '緯度_3位']).sum()
    logger.info(f"近似座標重複 (小數點3位): {near_coord_duplicates} 筆")
    
    # 5. 相似地址
    def normalize_address(addr):
        if pd.isna(addr):
            return ''
        import re
        return re.sub(r'[^\w]', '', str(addr)).lower()
    
    df_temp['地址標準化'] = df_temp['避難收容處所地址'].apply(normalize_address)
    addr_duplicates = df_temp.duplicated(subset=['地址標準化']).sum()
    logger.info(f"相似地址重複: {addr_duplicates} 筆")
    
    return {
        'exact_duplicates': exact_duplicates,
        'name_addr_duplicates': name_addr_duplicates,
        'coord_duplicates': coord_duplicates,
        'near_coord_duplicates': near_coord_duplicates,
        'addr_duplicates': addr_duplicates
    }

def clean_phone_data(df):
    """修正電話格式"""
    logger.info("開始修正電話格式...")
    
    phone_issues_before = 0
    phone_issues_fixed = 0
    
    df_clean = df.copy()
    
    for idx, phone in enumerate(df_clean['管理人電話']):
        if pd.notna(phone):
            phone_str = str(phone)
            
            # 檢查是否有問題
            has_issue = False
            
            # 科學記號格式
            if 'E+' in phone_str or 'e+' in phone_str:
                has_issue = True
                try:
                    phone_num = int(float(phone_str))
                    phone_str = str(phone_num)
                    phone_issues_fixed += 1
                except:
                    phone_str = np.nan
                    phone_issues_fixed += 1
                    
            # 包含特殊字符
            elif not all(c.isdigit() or c in '-# ' for c in phone_str):
                has_issue = True
                cleaned = re.sub(r'[^\d\-\#\s]', '', phone_str)
                if cleaned != phone_str:
                    phone_str = cleaned if cleaned else np.nan
                    phone_issues_fixed += 1
            
            # 全形字符轉半形
            if pd.notna(phone_str):
                fullwidth_to_halfwidth = str.maketrans('０１２３４５６７８９－＃', '0123456789-#')
                converted = phone_str.translate(fullwidth_to_halfwidth)
                if converted != phone_str:
                    phone_str = converted
                    phone_issues_fixed += 1
            
            if has_issue:
                phone_issues_before += 1
                
            df_clean.loc[idx, '管理人電話'] = phone_str
    
    logger.info(f"電話格式修正: 發現問題 {phone_issues_before}筆，修正 {phone_issues_fixed}筆")
    
    return df_clean

def validate_capacity_zeros(df):
    """驗證容量零值的合理性"""
    logger.info("驗證容量零值...")
    
    zero_capacity = df[df['預計收容人數'] == 0]
    logger.info(f"容量零值記錄: {len(zero_capacity)} 筆 ({len(zero_capacity)/len(df)*100:.1f}%)")
    
    # 分析零值記錄特徵
    backup_places = zero_capacity[zero_capacity['避難收容處所名稱'].str.contains('備用', na=False)]
    logger.info(f"零容量且為備用場所: {len(backup_places)} 筆")
    
    # 檢查是否有完整管理資訊
    has_manager = zero_capacity[zero_capacity['管理人姓名'].notna() & (zero_capacity['管理人姓名'] != '')]
    logger.info(f"零容量且有管理人資訊: {len(has_manager)} 筆")
    
    # 結論: 零值可能是有效的，不應修改
    logger.info("結論: 容量零值可能是有效值（如備用場所、小型場所），保留原始值")
    
    return True

def add_comprehensive_quality_flags(df):
    """新增全面的資料品質標記"""
    logger.info("新增全面的資料品質標記...")
    
    df_clean = df.copy()
    
    # 1. 座標品質標記
    df_clean['座標品質'] = '正常'
    df_clean.loc[df_clean['經度'].isna(), '座標品質'] = '經度缺失'
    
    # 2. 地址完整性標記
    df_clean['地址完整性'] = '完整'
    df_clean.loc[df_clean['避難收容處所地址'].isna(), '地址完整性'] = '缺失地址'
    df_clean.loc[df_clean['村里'].isna(), '地址完整性'] = '缺失村里'
    df_clean.loc[df_clean['避難收容處所地址'].isna() & df_clean['村里'].isna(), '地址完整性'] = '完全缺失'
    
    # 3. 資料完整性標記
    df_clean['資料完整性'] = '完整'
    df_clean.loc[df_clean['適用災害類別'].isna(), '資料完整性'] = '缺失災害類別'
    
    # 4. 重複標記
    coord_counts = df_clean.groupby(['經度', '緯度']).size()
    duplicate_coords = coord_counts[coord_counts > 1].index
    df_clean['座標重複'] = '否'
    for coord in duplicate_coords:
        mask = (df_clean['經度'] == coord[0]) & (df_clean['緯度'] == coord[1])
        df_clean.loc[mask, '座標重複'] = '是'
    
    # 5. 新增疑似重複標記
    df_clean['疑似重複'] = '否'
    
    # 同名同地址標記
    name_addr_groups = df_clean.groupby(['避難收容處所名稱', '避難收容處所地址']).size()
    duplicate_name_addr = name_addr_groups[name_addr_groups > 1].index
    for name_addr in duplicate_name_addr:
        mask = (df_clean['避難收容處所名稱'] == name_addr[0]) & (df_clean['避難收容處所地址'] == name_addr[1])
        df_clean.loc[mask, '疑似重複'] = '同名同地址'
    
    # 6. 容量異常標記
    df_clean['容量狀態'] = '正常'
    df_clean.loc[df_clean['預計收容人數'] == 0, '容量狀態'] = '零容量'
    df_clean.loc[df_clean['預計收容人數'] > 10000, '容量狀態'] = '極大容量'
    
    # 統計品質標記
    logger.info("資料品質標記統計:")
    for col in ['座標品質', '地址完整性', '資料完整性', '座標重複', '疑似重複', '容量狀態']:
        if col in df_clean.columns:
            logger.info(f"{col}: {df_clean[col].value_counts().to_dict()}")
    
    return df_clean

def main():
    """主清理流程 - 更新版"""
    logger.info("開始執行更新版資料清理流程...")
    
    # 讀取原始資料
    df = pd.read_csv('data/避難收容處所點位檔案v9.csv')
    logger.info(f"讀取原始資料: {df.shape[0]}筆, {df.shape[1]}欄")
    
    # 1. 驗證座標系統
    coord_system_valid = validate_coordinate_system(df)
    if not coord_system_valid:
        logger.warning("座標系統可能存在問題，但繼續處理")
    
    # 2. 全面重複分析
    duplicate_stats = analyze_duplicates_comprehensive(df)
    
    # 3. 驗證容量零值
    capacity_zeros_valid = validate_capacity_zeros(df)
    
    # 4. 執行清理步驟
    df_clean = clean_coordinate_data(df)
    df_clean = clean_phone_data(df_clean)
    df_clean = add_comprehensive_quality_flags(df_clean)
    
    # 5. 保存清理後資料
    output_path = 'data/避難收容處所點位檔案v9_clean_updated.csv'
    df_clean.to_csv(output_path, index=False, encoding='utf-8-sig')
    logger.info(f"清理後資料已保存至: {output_path}")
    
    # 6. 最終統計
    logger.info("=== 更新版清理完成統計 ===")
    logger.info(f"原始資料: {df.shape[0]}筆")
    logger.info(f"清理後資料: {df_clean.shape[0]}筆")
    logger.info(f"新增欄位: {df_clean.shape[1] - df.shape[1]}個")
    
    # 7. 重複統計總結
    logger.info("=== 重複分析總結 ===")
    for key, value in duplicate_stats.items():
        logger.info(f"{key}: {value}筆")
    
    return df_clean

if __name__ == "__main__":
    cleaned_df = main()
