import pandas as pd
import folium
import numpy as np
import math
import re
from datetime import datetime
import os
import sys

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    使用 Haversine 公式計算兩點間的距離（公里）
    """
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371
    return c * r

def semantic_facility_analysis(facility_name):
    """
    語意分析設施名稱，判斷是否為室內設施
    """
    if pd.isna(facility_name):
        return False
    
    facility_name = str(facility_name).lower()
    
    # 室內設施關鍵詞
    indoor_keywords = [
        '學校', '國小', '國中', '高中', '大學', '校', '教室', '禮堂',
        '活動中心', '社區中心', '集會所', '會館', '中心',
        '體育館', '體育場', '健身房', '運動中心', '室內',
        '圖書館', '美術館', '博物館', '文化中心',
        '辦公處', '公所', '鄉公所', '區公所', '市公所',
        '醫院', '診所', '衛生所',
        '教室', '會議室', '大廳', '廳', '館', '樓', '室'
    ]
    
    # 室外設施關鍵詞
    outdoor_keywords = [
        '公園', '廣場', '廣場', '停車場', '停車',
        '運動場', '球場', '田徑場', '遊樂場', '遊戲場',
        '廣場', '廣場', '廣場', '廣場', '廣場',
        '河濱', '海濱', '海灘', '堤防', '綠地',
        '戶外', '露天', '室外'
    ]
    
    # 檢查是否包含室外關鍵詞
    for keyword in outdoor_keywords:
        if keyword in facility_name:
            return False
    
    # 檢查是否包含室內關鍵詞
    for keyword in indoor_keywords:
        if keyword in facility_name:
            return True
    
    # 預設為室內（避難所通常為室內設施）
    return True

def audit_shelter_data(csv_file):
    """
    審計避難所資料，檢查CRS和品質問題
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
    
    print(f"原始資料總筆數: {len(df)}")
    print(f"欄位: {list(df.columns)}")
    
    # 初始化問題統計
    issues = {
        'missing_coordinates': [],
        'invalid_coordinates': [],
        'crs_confusion': [],
        'outliers': [],
        'duplicate_coordinates': []
    }
    
    # 檢查 1: 缺失坐標
    print("\n=== 檢查缺失坐標 ===")
    missing_lat = df['緯度'].isna() | (df['緯度'] == '') | (df['緯度'] == 0)
    missing_lon = df['經度'].isna() | (df['經度'] == '') | (df['經度'] == 0)
    missing_coords = missing_lat | missing_lon
    
    issues['missing_coordinates'] = df[missing_coords].index.tolist()
    print(f"缺失坐標的記錄: {len(issues['missing_coordinates'])} 筆")
    
    # 檢查 2: CRS 混淆（判斷是否為 TWD97 vs WGS84）
    print("\n=== 檢查 CRS 混淆 ===")
    def check_crs_type(lat, lon):
        try:
            lat = float(lat)
            lon = float(lon)
            
            # TWD97 特徵：經度值通常在 200,000-400,000 範圍
            # WGS84 特徵：經度值在 119-123 範圍
            if 200000 <= lon <= 400000:
                return 'twd97'
            elif 119 <= lon <= 123:
                return 'wgs84'
            else:
                return 'unknown'
        except:
            return 'invalid'
    
    crs_types = df.apply(lambda row: check_crs_type(row['緯度'], row['經度']), axis=1)
    twd97_count = (crs_types == 'twd97').sum()
    wgs84_count = (crs_types == 'wgs84').sum()
    unknown_count = (crs_types == 'unknown').sum()
    
    print(f"TWD97 坐標: {twd97_count} 筆")
    print(f"WGS84 坐標: {wgs84_count} 筆")
    print(f"未知坐標系統: {unknown_count} 筆")
    
    # 檢查 3: 離群值（台灣邊界外）
    print("\n=== 檢查離群值 ===")
    def is_taiwan_coordinate(lat, lon):
        try:
            lat = float(lat)
            lon = float(lon)
            # 台灣主島及周邊離島精確範圍
            if (21.8 <= lat <= 25.3) and (120.0 <= lon <= 122.0):
                return True  # 台灣主島
            elif (24.3 <= lat <= 24.6) and (118.2 <= lon <= 118.5):
                return True  # 金門
            elif (26.1 <= lat <= 26.2) and (119.9 <= lon <= 120.1):
                return True  # 馬祖
            elif (23.5 <= lat <= 23.9) and (119.5 <= lon <= 119.7):
                return True  # 澎湖
            else:
                return False
        except:
            return False
    
    outlier_mask = df.apply(lambda row: not is_taiwan_coordinate(row['緯度'], row['經度']), axis=1)
    issues['outliers'] = df[outlier_mask].index.tolist()
    print(f"台灣邊界外的記錄: {len(issues['outliers'])} 筆")
    
    # 檢查 4: 重複坐標
    print("\n=== 檢查重複坐標 ===")
    coordinate_counts = df.groupby(['緯度', '經度']).size().reset_index(name='count')
    duplicate_coords = coordinate_counts[coordinate_counts['count'] > 1]
    
    for _, row in duplicate_coords.iterrows():
        lat, lon, count = row['緯度'], row['經度'], row['count']
        matching_indices = df[(df['緯度'] == lat) & (df['經度'] == lon)].index.tolist()
        issues['duplicate_coordinates'].extend(matching_indices)
    
    print(f"重複坐標的記錄: {len(issues['duplicate_coordinates'])} 筆")
    
    return issues, df

def clean_and_enhance_data(df):
    """
    清理並增強資料
    """
    print("\n正在清理並增強資料...")
    
    # 過濾掉缺失坐標的記錄
    df_clean = df.dropna(subset=['緯度', '經度'])
    df_clean = df_clean[(df_clean['緯度'] != 0) & (df_clean['經度'] != 0)]
    
    # 過濾掉台灣主島範圍外的記錄（保留離島）
    def is_valid_coordinate(lat, lon):
        try:
            lat = float(lat)
            lon = float(lon)
            # 台灣主島及周邊離島精確範圍
            # 主島：緯度 21.8-25.3, 經度 120.0-122.0
            # 離島：金門(24.3-24.6, 118.2-118.5)、馬祖(26.1-26.2, 119.9-120.1)、澎湖(23.5-23.9, 119.5-119.7)
            if (21.8 <= lat <= 25.3) and (120.0 <= lon <= 122.0):
                return True  # 台灣主島
            elif (24.3 <= lat <= 24.6) and (118.2 <= lon <= 118.5):
                return True  # 金門
            elif (26.1 <= lat <= 26.2) and (119.9 <= lon <= 120.1):
                return True  # 馬祖
            elif (23.5 <= lat <= 23.9) and (119.5 <= lon <= 119.7):
                return True  # 澎湖
            else:
                return False
        except:
            return False
    
    valid_mask = df_clean.apply(lambda row: is_valid_coordinate(row['緯度'], row['經度']), axis=1)
    df_clean = df_clean[valid_mask]
    
    # 語意分析設施類型
    print("正在進行設施名稱語意分析...")
    df_clean['is_indoor'] = df_clean['避難收容處所名稱'].apply(semantic_facility_analysis)
    
    indoor_count = df_clean['is_indoor'].sum()
    outdoor_count = len(df_clean) - indoor_count
    
    print(f"室內設施: {indoor_count} 個")
    print(f"室外設施: {outdoor_count} 個")
    
    print(f"清理後資料數量: {len(df_clean)} (原始: {len(df)})")
    
    return df_clean

def get_aqi_station_data():
    """
    獲取 AQI 測站資料（模擬颱風後情境）
    """
    print("正在獲取 AQI 測站資料...")
    
    # 模擬颱風後 AQI 資料（大部分良好，但有些地區惡化）
    aqi_stations = [
        # 北部地區
        {'station_name': '中山', 'lat': 25.0623, 'lon': 121.5254, 'county': '台北市', 'aqi': 45, 'status': '良好'},
        {'station_name': '松山', 'lat': 25.0478, 'lon': 121.5770, 'county': '台北市', 'aqi': 48, 'status': '良好'},
        {'station_name': '大安', 'lat': 25.0263, 'lon': 121.5437, 'county': '台北市', 'aqi': 42, 'status': '良好'},
        {'station_name': '古亭', 'lat': 25.0167, 'lon': 121.5280, 'county': '台北市', 'aqi': 38, 'status': '良好'},
        {'station_name': '萬華', 'lat': 25.0308, 'lon': 121.4980, 'county': '台北市', 'aqi': 35, 'status': '良好'},
        {'station_name': '文山', 'lat': 24.9895, 'lon': 121.5715, 'county': '台北市', 'aqi': 40, 'status': '良好'},
        {'station_name': '士林', 'lat': 25.0877, 'lon': 121.5240, 'county': '台北市', 'aqi': 43, 'status': '良好'},
        {'station_name': '內湖', 'lat': 25.0699, 'lon': 121.5800, 'county': '台北市', 'aqi': 46, 'status': '良好'},
        {'station_name': '板橋', 'lat': 25.0167, 'lon': 121.4620, 'county': '新北市', 'aqi': 44, 'status': '良好'},
        {'station_name': '新店', 'lat': 24.9676, 'lon': 121.5394, 'county': '新北市', 'aqi': 41, 'status': '良好'},
        {'station_name': '桃園', 'lat': 24.9895, 'lon': 121.3011, 'county': '桃園市', 'aqi': 47, 'status': '良好'},
        {'station_name': '新竹', 'lat': 24.8197, 'lon': 120.9675, 'county': '新竹市', 'aqi': 39, 'status': '良好'},
        
        # 中部地區
        {'station_name': '台中', 'lat': 24.1477, 'lon': 120.6736, 'county': '台中市', 'aqi': 43, 'status': '良好'},
        {'station_name': '彰化', 'lat': 24.0767, 'lon': 120.5453, 'county': '彰化縣', 'aqi': 41, 'status': '良好'},
        {'station_name': '南投', 'lat': 23.9147, 'lon': 120.6819, 'county': '南投縣', 'aqi': 38, 'status': '良好'},
        {'station_name': '雲林', 'lat': 23.6995, 'lon': 120.4328, 'county': '雲林縣', 'aqi': 45, 'status': '良好'},
        {'station_name': '嘉義', 'lat': 23.4981, 'lon': 120.4458, 'county': '嘉義市', 'aqi': 42, 'status': '良好'},
        
        # 南部地區
        {'station_name': '台南', 'lat': 22.9999, 'lon': 120.2269, 'county': '台南市', 'aqi': 44, 'status': '良好'},
        {'station_name': '高雄', 'lat': 22.6273, 'lon': 120.3014, 'county': '高雄市', 'aqi': 46, 'status': '良好'},
        {'station_name': '左營', 'lat': 22.6900, 'lon': 120.2969, 'county': '高雄市', 'aqi': 43, 'status': '良好'},
        {'station_name': '屏東', 'lat': 22.4686, 'lon': 120.4897, 'county': '屏東縣', 'aqi': 40, 'status': '良好'},
        
        # 東部地區
        {'station_name': '花蓮', 'lat': 23.8224, 'lon': 121.5474, 'county': '花蓮縣', 'aqi': 35, 'status': '良好'},
        {'station_name': '台東', 'lat': 22.7598, 'lon': 121.1607, 'county': '台東縣', 'aqi': 33, 'status': '良好'},
    ]
    
    print(f"獲取 {len(aqi_stations)} 個 AQI 測站資料")
    return aqi_stations

def scenario_injection(aqi_stations):
    """
    情境模擬：注入高 AQI 值以驗證分析邏輯
    """
    print("\n正在進行情境模擬...")
    
    # 找到高雄測站並注入高 AQI 值
    for station in aqi_stations:
        if station['station_name'] == '高雄':
            original_aqi = station['aqi']
            station['aqi'] = 150  # 注入高 AQI 值
            station['status'] = '對所有族群不健康'
            print(f"情境注入: {station['station_name']} AQI 從 {original_aqi} 調整為 {station['aqi']}")
            break
    
    return aqi_stations

def find_nearest_aqi_station(shelter_lat, shelter_lon, aqi_stations):
    """
    找出距離避難所最近的 AQI 測站
    """
    min_distance = float('inf')
    nearest_station = None
    
    for station in aqi_stations:
        distance = calculate_distance(shelter_lat, shelter_lon, station['lat'], station['lon'])
        if distance < min_distance:
            min_distance = distance
            nearest_station = station
    
    return nearest_station, min_distance

def get_aqi_color(aqi_value):
    """
    根據 AQI 數值返回對應的顏色
    """
    try:
        aqi = int(aqi_value)
    except (ValueError, TypeError):
        return 'gray'
    
    if aqi <= 50:
        return 'green'
    elif aqi <= 100:
        return 'yellow'
    elif aqi <= 150:
        return 'orange'
    else:
        return 'red'

def create_shelter_aqi_map(shelters_df, aqi_stations):
    """
    創建避難所與 AQI 測站疊圖
    """
    print("正在創建避難所與 AQI 疊圖...")
    
    # 台灣中心點
    taiwan_center = [23.8, 120.9]
    
    # 創建地圖
    m = folium.Map(
        location=taiwan_center,
        zoom_start=8,
        tiles='OpenStreetMap'
    )
    
    # 添加 AQI 測站
    for station in aqi_stations:
        color = get_aqi_color(station['aqi'])
        radius = 8 if station['aqi'] <= 100 else 12
        
        popup_content = f"""
        <div style="font-family: Arial, sans-serif;">
            <h4>{station['station_name']} AQI 測站</h4>
            <p><strong>縣市:</strong> {station['county']}</p>
            <p><strong>AQI:</strong> <span style="color: {color}; font-weight: bold;">{station['aqi']}</span></p>
            <p><strong>狀態:</strong> {station['status']}</p>
            <p><strong>座標:</strong> {station['lat']:.4f}, {station['lon']:.4f}</p>
        </div>
        """
        
        folium.CircleMarker(
            location=[station['lat'], station['lon']],
            radius=radius,
            popup=folium.Popup(popup_content, max_width=300),
            color='black',
            weight=2,
            fillColor=color,
            fillOpacity=0.8,
            tooltip=f"{station['station_name']} - AQI: {station['aqi']}"
        ).add_to(m)
    
    # 分析避難所風險
    analysis_results = []
    
    print("正在分析避難所風險...")
    
    for idx, shelter in shelters_df.iterrows():
        try:
            shelter_lat = float(shelter['緯度'])
            shelter_lon = float(shelter['經度'])
            shelter_name = shelter['避難收容處所名稱']
            shelter_address = shelter['避難收容處所地址']
            county = shelter['縣市及鄉鎮市區']
            is_indoor = shelter['is_indoor']
            
            # 驗證：檢查是否在海中
            if not (21.0 <= shelter_lat <= 26.0 and 118.0 <= shelter_lon <= 123.0):
                print(f"警告: 避難所 {shelter_name} 可能在海中 - 坐標: ({shelter_lat}, {shelter_lon})")
                continue
            
            # 找出最近的 AQI 測站
            nearest_station, distance = find_nearest_aqi_station(shelter_lat, shelter_lon, aqi_stations)
            
            # 判斷風險等級
            if nearest_station['aqi'] > 100:
                risk_level = 'High Risk'
                risk_color = 'red'
            elif nearest_station['aqi'] > 50 and not is_indoor:
                risk_level = 'Warning'
                risk_color = 'orange'
            else:
                risk_level = 'Low Risk'
                risk_color = 'green'
            
            # 創建避難所標記
            icon_type = 'home' if is_indoor else 'tree'
            popup_content = f"""
            <div style="font-family: Arial, sans-serif;">
                <h4>{shelter_name}</h4>
                <p><strong>地址:</strong> {shelter_address}</p>
                <p><strong>縣市:</strong> {county}</p>
                <p><strong>設施類型:</strong> {'室內' if is_indoor else '室外'}</p>
                <p><strong>最近 AQI 測站:</strong> {nearest_station['station_name']}</p>
                <p><strong>測站 AQI:</strong> <span style="color: {get_aqi_color(nearest_station['aqi'])}; font-weight: bold;">{nearest_station['aqi']}</span></p>
                <p><strong>距離:</strong> {distance:.2f} 公里</p>
                <p><strong>風險等級:</strong> <span style="color: {risk_color}; font-weight: bold;">{risk_level}</span></p>
                <p><strong>預計收容人數:</strong> {shelter.get('預計收容人數', 'N/A')}</p>
            </div>
            """
            
            folium.CircleMarker(
                location=[shelter_lat, shelter_lon],
                radius=5,
                popup=folium.Popup(popup_content, max_width=350),
                color='black',
                weight=1,
                fillColor=risk_color,
                fillOpacity=0.7,
                tooltip=f"{shelter_name} - {risk_level}"
            ).add_to(m)
            
            # 保存分析結果
            analysis_results.append({
                '避難所名稱': shelter_name,
                '地址': shelter_address,
                '縣市': county,
                '設施類型': '室內' if is_indoor else '室外',
                '緯度': shelter_lat,
                '經度': shelter_lon,
                '最近AQI測站': nearest_station['station_name'],
                '測站AQI': nearest_station['aqi'],
                '測站狀態': nearest_station['status'],
                '距離(公里)': round(distance, 2),
                '風險等級': risk_level,
                '預計收容人數': shelter.get('預計收容人數', 'N/A')
            })
            
        except Exception as e:
            print(f"處理避難所 {shelter.get('避難收容處所名稱', '未知')} 時發生錯誤: {e}")
            continue
    
    # 添加圖例
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 280px; height: 220px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px">
    <h4>圖例說明</h4>
    <p><strong>AQI 測站:</strong></p>
    <i class="fa fa-circle" style="color:green"></i> 良好 (0-50)<br>
    <i class="fa fa-circle" style="color:yellow"></i> 普通 (51-100)<br>
    <i class="fa fa-circle" style="color:orange"></i> 對敏感族群不健康 (101-150)<br>
    <i class="fa fa-circle" style="color:red"></i> 對所有族群不健康 (151+)<br>
    <p><strong>避難所風險:</strong></p>
    <i class="fa fa-circle" style="color:green"></i> 低風險 (AQI ≤ 50)<br>
    <i class="fa fa-circle" style="color:orange"></i> 警告 (AQI 51-100 + 室外)<br>
    <i class="fa fa-circle" style="color:red"></i> 高風險 (AQI > 100)<br>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m, analysis_results

def save_analysis_results(analysis_results, output_file='outputs/shelter_aqi_analysis.csv'):
    """
    保存分析結果到 CSV
    """
    print(f"正在保存分析結果到 {output_file}...")
    
    df_results = pd.DataFrame(analysis_results)
    df_results.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    # 統計結果
    total_shelters = len(analysis_results)
    high_risk_count = sum(1 for r in analysis_results if r['風險等級'] == 'High Risk')
    warning_count = sum(1 for r in analysis_results if r['風險等級'] == 'Warning')
    low_risk_count = sum(1 for r in analysis_results if r['風險等級'] == 'Low Risk')
    
    print(f"分析結果統計:")
    print(f"總避難所: {total_shelters}")
    print(f"高風險: {high_risk_count} ({high_risk_count/total_shelters*100:.1f}%)")
    print(f"警告: {warning_count} ({warning_count/total_shelters*100:.1f}%)")
    print(f"低風險: {low_risk_count} ({low_risk_count/total_shelters*100:.1f}%)")
    
    return df_results

def generate_audit_report(issues, df, output_file='outputs/audit_report.md'):
    """
    生成審計報告
    """
    total_records = len(df)
    
    report_content = f"""# 避難所資料審計報告

## 資料概覽
- **總記錄數**: {total_records} 筆
- **審計時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 發現的問題

### 1. 缺失坐標 ({len(issues['missing_coordinates'])} 筆)
**問題描述**: 緯度或經度欄位為空、零值或無效值

**影響程度**: 🔴 高 - 無法在地圖上定位這些避難所

### 2. CRS 混淆
**問題描述**: 坐標系統不一致，可能混合 TWD97 和 WGS84

**影響程度**: 🟡 中 - 需要坐標轉換才能正確定位

### 3. 離群值 ({len(issues['outliers'])} 筆)
**問題描述**: 坐標位在台灣邊界外

**影響程度**: 🟡 中 - 可能為轉換錯誤或離島資料

### 4. 重複坐標 ({len(issues['duplicate_coordinates'])} 筆)
**問題描述**: 多個避難所使用相同的坐標

**影響程度**: 🟡 中 - 可能為資料輸入錯誤

## 資料增強
- **語意分析**: 根據設施名稱推斷室內/室外類型
- **坐標清理**: 過濾無效坐標，保留有效資料
- **風險分級**: 建立基於 AQI 的風險評估系統

## 技術說明
- **CRS 檢查**: 經度值 > 200,000 判斷為 TWD97，119-123 判斷為 WGS84
- **語意分析**: 使用關鍵詞匹配判斷設施類型
- **距離計算**: 使用 Haversine 公式計算球面距離
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"審計報告已保存至: {output_file}")
    return report_content

def main():
    """
    主程式
    """
    print("開始颱風後避難所空氣品質風險分析...")
    
    try:
        # 讀取避難所資料
        csv_file = 'data/shelters.csv'
        issues, df = audit_shelter_data(csv_file)
        
        # 清理並增強資料
        shelters_df = clean_and_enhance_data(df)
        
        # 保存清理後的資料
        shelters_df.to_csv('data/shelters_cleaned.csv', index=False, encoding='utf-8-sig')
        print("清理後資料已保存至 data/shelters_cleaned.csv")
        
        # 獲取 AQI 測站資料
        aqi_stations = get_aqi_station_data()
        
        # 情境模擬（注入高 AQI 值）
        aqi_stations = scenario_injection(aqi_stations)
        
        # 創建疊圖
        shelter_map, analysis_results = create_shelter_aqi_map(shelters_df, aqi_stations)
        
        # 保存地圖
        map_file = 'outputs/shelter_aqi_map.html'
        shelter_map.save(map_file)
        print(f"風險地圖已保存至: {map_file}")
        
        # 保存分析結果
        results_df = save_analysis_results(analysis_results)
        
        # 生成審計報告
        generate_audit_report(issues, df)
        
        print(f"\n=== 分析完成 ===")
        print(f"請查看以下檔案:")
        print(f"- 清理後資料: data/shelters_cleaned.csv")
        print(f"- 風險地圖: {map_file}")
        print(f"- 分析結果: outputs/shelter_aqi_analysis.csv")
        print(f"- 審計報告: outputs/audit_report.md")
        
    except Exception as e:
        print(f"程式執行錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
