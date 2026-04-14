import pandas as pd
import numpy as np
import re
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_coordinate_data(df):
    """修正座標資料"""
    logger.info("開始修正座標資料...")
    
    # 統計修正前狀況
    zero_coords_before = df[(df['經度'] == 0) | (df['緯度'] == 0)].shape[0]
    invalid_lon_before = df[(df['經度'] < 100) | (df['經度'] > 130)].shape[0]
    invalid_lat_before = df[(df['緯度'] < 15) | (df['緯度'] > 30)].shape[0]
    
    # 將零值和異常值設為NA
    df_clean = df.copy()
    
    # 經度異常值設為NA
    invalid_lon_mask = (df_clean['經度'] < 100) | (df_clean['經度'] > 130)
    df_clean.loc[invalid_lon_mask, '經度'] = np.nan
    
    # 緯度異常值設為NA  
    invalid_lat_mask = (df_clean['緯度'] < 15) | (df_clean['緯度'] > 30)
    df_clean.loc[invalid_lat_mask, '緯度'] = np.nan
    
    # 零值設為NA
    zero_mask = (df_clean['經度'] == 0) | (df_clean['緯度'] == 0)
    df_clean.loc[zero_mask, ['經度', '緯度']] = np.nan
    
    # 統計修正後狀況
    zero_coords_after = df_clean[(df_clean['經度'].isna()) | (df_clean['緯度'].isna())].shape[0]
    
    logger.info(f"座標修正: 異常經度 {invalid_lon_before}筆 -> 設為NA")
    logger.info(f"座標修正: 異常緯度 {invalid_lat_before}筆 -> 設為NA") 
    logger.info(f"座標修正: 零值座標 {zero_coords_before}筆 -> 設為NA")
    logger.info(f"座標修正後缺失座標總數: {zero_coords_after}筆")
    
    return df_clean

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
            
            # 科學記號格式 (如 4.72E+11)
            if 'E+' in phone_str or 'e+' in phone_str:
                has_issue = True
                # 嘗試轉換
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
                # 移除非標準字符，保留數字、-、#、空格
                cleaned = re.sub(r'[^\d\-\#\s]', '', phone_str)
                if cleaned != phone_str:
                    phone_str = cleaned if cleaned else np.nan
                    phone_issues_fixed += 1
            
            # 全形字符轉半形
            if pd.notna(phone_str):
                fullwidth_to_halfwidth = str.maketrans(
                    '０１２３４５６７８９－＃', 
                    '0123456789-#'
                )
                converted = phone_str.translate(fullwidth_to_halfwidth)
                if converted != phone_str:
                    phone_str = converted
                    phone_issues_fixed += 1
            
            if has_issue:
                phone_issues_before += 1
                
            df_clean.loc[idx, '管理人電話'] = phone_str
    
    logger.info(f"電話格式修正: 發現問題 {phone_issues_before}筆，修正 {phone_issues_fixed}筆")
    
    return df_clean

def clean_capacity_data(df):
    """修正容量資料"""
    logger.info("開始檢查容量資料...")
    
    zero_capacity = (df['預計收容人數'] == 0).sum()
    extreme_capacity = (df['預計收容人數'] > 10000).sum()
    
    # 極大容量記錄 - 標記但不修改
    extreme_records = df[df['預計收容人數'] > 10000]
    
    logger.info(f"容量檢查: 零容量 {zero_capacity}筆")
    logger.info(f"容量檢查: 極大容量(>10000) {extreme_capacity}筆")
    
    if len(extreme_records) > 0:
        logger.info("極大容量記錄:")
        for _, record in extreme_records.iterrows():
            logger.info(f"  {record['避難收容處所名稱']}: {record['預計收容人數']}人")
    
    return df

def standardize_boolean_fields(df):
    """標準化布林欄位"""
    logger.info("開始標準化布林欄位...")
    
    boolean_cols = ['室內', '室外', '適合避難弱者安置']
    
    for col in boolean_cols:
        if col in df.columns:
            # 統計原始值
            value_counts = df[col].value_counts()
            logger.info(f"{col}欄位原始分布: {dict(value_counts)}")
            
            # 標準化為是/否
            df_clean = df.copy()
            
            # 將所有非'是'的值標準化為'否'
            df_clean[col] = df_clean[col].apply(lambda x: '是' if str(x) == '是' else '否')
            
            # 統計修正後
            new_counts = df_clean[col].value_counts()
            logger.info(f"{col}欄位修正後分布: {dict(new_counts)}")
    
    return df_clean

def add_data_quality_flags(df):
    """新增資料品質標記欄位"""
    logger.info("新增資料品質標記...")
    
    df_clean = df.copy()
    
    # 座標品質標記
    df_clean['座標品質'] = '正常'
    df_clean.loc[df_clean['經度'].isna() | df_clean['緯度'].isna(), '座標品質'] = '缺失'
    
    # 地址完整性標記
    df_clean['地址完整性'] = '完整'
    df_clean.loc[df_clean['避難收容處所地址'].isna(), '地址完整性'] = '缺失地址'
    df_clean.loc[df_clean['村里'].isna(), '地址完整性'] = '缺失村里'
    df_clean.loc[df_clean['避難收容處所地址'].isna() & df_clean['村里'].isna(), '地址完整性'] = '完全缺失'
    
    # 資料完整性標記
    df_clean['資料完整性'] = '完整'
    df_clean.loc[df_clean['適用災害類別'].isna(), '資料完整性'] = '缺失災害類別'
    
    # 重複座標標記
    coord_counts = df_clean.groupby(['經度', '緯度']).size()
    duplicate_coords = coord_counts[coord_counts > 1].index
    df_clean['座標重複'] = '否'
    for coord in duplicate_coords:
        mask = (df_clean['經度'] == coord[0]) & (df_clean['緯度'] == coord[1])
        df_clean.loc[mask, '座標重複'] = '是'
    
    # 統計品質標記
    logger.info("資料品質標記統計:")
    logger.info(f"座標品質: {df_clean['座標品質'].value_counts().to_dict()}")
    logger.info(f"地址完整性: {df_clean['地址完整性'].value_counts().to_dict()}")
    logger.info(f"資料完整性: {df_clean['資料完整性'].value_counts().to_dict()}")
    logger.info(f"座標重複: {df_clean['座標重複'].value_counts().to_dict()}")
    
    return df_clean

def main():
    """主清理流程"""
    logger.info("開始執行資料清理流程...")
    
    # 讀取原始資料
    df = pd.read_csv('data/避難收容處所點位檔案v9.csv')
    logger.info(f"讀取原始資料: {df.shape[0]}筆, {df.shape[1]}欄")
    
    # 執行清理步驟
    df_clean = clean_coordinate_data(df)
    df_clean = clean_phone_data(df_clean)
    df_clean = clean_capacity_data(df_clean)
    df_clean = standardize_boolean_fields(df_clean)
    df_clean = add_data_quality_flags(df_clean)
    
    # 保存清理後資料
    output_path = 'data/避難收容處所點位檔案v9_clean.csv'
    df_clean.to_csv(output_path, index=False, encoding='utf-8-sig')
    logger.info(f"清理後資料已保存至: {output_path}")
    
    # 最終統計
    logger.info("=== 清理完成統計 ===")
    logger.info(f"原始資料: {df.shape[0]}筆")
    logger.info(f"清理後資料: {df_clean.shape[0]}筆")
    logger.info(f"新增欄位: {df_clean.shape[1] - df.shape[1]}個")
    
    # 缺失值統計
    missing_stats = df_clean.isnull().sum()
    logger.info("清理後缺失值統計:")
    for col, count in missing_stats.items():
        if count > 0:
            logger.info(f"  {col}: {count}筆")
    
    return df_clean

if __name__ == "__main__":
    cleaned_df = main()
