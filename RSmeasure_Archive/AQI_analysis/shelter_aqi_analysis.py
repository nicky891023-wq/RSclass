import pandas as pd
import folium
import numpy as np
import math
from datetime import datetime
import os

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

def get_clean_shelter_data(csv_file):
    """
    清理並過濾避難所資料
    """
    print("正在讀取避難所資料...")
    
    try:
        df = pd.read_csv(csv_file, encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(csv_file, encoding='big5')
        except:
            df = pd.read_csv(csv_file, encoding='utf-8-sig')
    
    # 清理資料
    print("正在清理避難所資料...")
    
    # 過濾掉缺失坐標的記錄
    df_clean = df.dropna(subset=['緯度', '經度'])
    df_clean = df_clean[(df_clean['緯度'] != 0) & (df_clean['經度'] != 0)]
    
    # 過濾掉無效坐標（不在台灣主島範圍內）
    def is_valid_taiwan_coordinate(lat, lon):
        try:
            lat = float(lat)
            lon = float(lon)
            return (21.5 <= lat <= 25.5) and (119.5 <= lon <= 122.5)
        except:
            return False
    
    valid_mask = df_clean.apply(lambda row: is_valid_taiwan_coordinate(row['緯度'], row['經度']), axis=1)
    df_clean = df_clean[valid_mask]
    
    print(f"清理後避難所數量: {len(df_clean)} (原始: {len(df)})")
    
    return df_clean

def get_aqi_station_data():
    """
    獲取 AQI 測站資料（使用模擬資料）
    """
    print("正在獲取 AQI 測站資料...")
    
    # 模擬 AQI 測站資料（颱風後空氣品質）
    aqi_stations = [
        # 北部地區
        {'station_name': '中山', 'lat': 25.0623, 'lon': 121.5254, 'county': '台北市', 'aqi': 85, 'status': '普通'},
        {'station_name': '松山', 'lat': 25.0478, 'lon': 121.5770, 'county': '台北市', 'aqi': 92, 'status': '普通'},
        {'station_name': '大安', 'lat': 25.0263, 'lon': 121.5437, 'county': '台北市', 'aqi': 78, 'status': '普通'},
        {'station_name': '古亭', 'lat': 25.0167, 'lon': 121.5280, 'county': '台北市', 'aqi': 105, 'status': '對敏感族群不健康'},
        {'station_name': '萬華', 'lat': 25.0308, 'lon': 121.4980, 'county': '台北市', 'aqi': 112, 'status': '對敏感族群不健康'},
        {'station_name': '文山', 'lat': 24.9895, 'lon': 121.5715, 'county': '台北市', 'aqi': 125, 'status': '對所有族群不健康'},
        {'station_name': '士林', 'lat': 25.0877, 'lon': 121.5240, 'county': '台北市', 'aqi': 88, 'status': '普通'},
        {'station_name': '內湖', 'lat': 25.0699, 'lon': 121.5800, 'county': '台北市', 'aqi': 95, 'status': '普通'},
        {'station_name': '板橋', 'lat': 25.0167, 'lon': 121.4620, 'county': '新北市', 'aqi': 118, 'status': '對所有族群不健康'},
        {'station_name': '新店', 'lat': 24.9676, 'lon': 121.5394, 'county': '新北市', 'aqi': 82, 'status': '普通'},
        {'station_name': '桃園', 'lat': 24.9895, 'lon': 121.3011, 'county': '桃園市', 'aqi': 135, 'status': '對所有族群不健康'},
        {'station_name': '新竹', 'lat': 24.8197, 'lon': 120.9675, 'county': '新竹市', 'aqi': 98, 'status': '普通'},
        
        # 中部地區
        {'station_name': '台中', 'lat': 24.1477, 'lon': 120.6736, 'county': '台中市', 'aqi': 142, 'status': '對所有族群不健康'},
        {'station_name': '彰化', 'lat': 24.0767, 'lon': 120.5453, 'county': '彰化縣', 'aqi': 128, 'status': '對所有族群不健康'},
        {'station_name': '南投', 'lat': 23.9147, 'lon': 120.6819, 'county': '南投縣', 'aqi': 76, 'status': '普通'},
        {'station_name': '雲林', 'lat': 23.6995, 'lon': 120.4328, 'county': '雲林縣', 'aqi': 155, 'status': '非常不健康'},
        {'station_name': '嘉義', 'lat': 23.4981, 'lon': 120.4458, 'county': '嘉義市', 'aqi': 132, 'status': '對所有族群不健康'},
        
        # 南部地區
        {'station_name': '台南', 'lat': 22.9999, 'lon': 120.2269, 'county': '台南市', 'aqi': 145, 'status': '對所有族群不健康'},
        {'station_name': '高雄', 'lat': 22.6273, 'lon': 120.3014, 'county': '高雄市', 'aqi': 168, 'status': '非常不健康'},
        {'station_name': '左營', 'lat': 22.6900, 'lon': 120.2969, 'county': '高雄市', 'aqi': 162, 'status': '非常不健康'},
        {'station_name': '屏東', 'lat': 22.4686, 'lon': 120.4897, 'county': '屏東縣', 'aqi': 138, 'status': '對所有族群不健康'},
        
        # 東部地區
        {'station_name': '花蓮', 'lat': 23.8224, 'lon': 121.5474, 'county': '花蓮縣', 'aqi': 65, 'status': '普通'},
        {'station_name': '台東', 'lat': 22.7598, 'lon': 121.1607, 'county': '台東縣', 'aqi': 58, 'status': '良好'},
    ]
    
    print(f"獲取 {len(aqi_stations)} 個 AQI 測站資料")
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
    elif aqi <= 200:
        return 'red'
    else:
        return 'purple'

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
    high_risk_stations = [s for s in aqi_stations if s['aqi'] > 100]
    
    for station in aqi_stations:
        color = get_aqi_color(station['aqi'])
        radius = 8 if station['aqi'] <= 100 else 12
        
        # 特別標記高風險測站
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
        
        # 為高風險測站添加警示圈
        if station['aqi'] > 100:
            folium.Circle(
                location=[station['lat'], station['lon']],
                radius=10000,  # 10公里影響範圍
                popup=f"{station['station_name']} 高風險區域 (AQI: {station['aqi']})",
                color='red',
                weight=2,
                fill=True,
                fillOpacity=0.1
            ).add_to(m)
    
    # 分析避難所風險
    high_risk_shelters = []
    medium_risk_shelters = []
    low_risk_shelters = []
    
    print("正在分析避難所風險...")
    
    for idx, shelter in shelters_df.iterrows():
        try:
            shelter_lat = float(shelter['緯度'])
            shelter_lon = float(shelter['經度'])
            shelter_name = shelter['避難收容處所名稱']
            shelter_address = shelter['避難收容處所地址']
            county = shelter['縣市及鄉鎮市區']
            
            # 找出最近的 AQI 測站
            nearest_station, distance = find_nearest_aqi_station(shelter_lat, shelter_lon, aqi_stations)
            
            # 判斷風險等級
            if nearest_station['aqi'] > 150:
                risk_level = 'high'
                risk_color = 'red'
                high_risk_shelters.append(shelter)
            elif nearest_station['aqi'] > 100:
                risk_level = 'medium'
                risk_color = 'orange'
                medium_risk_shelters.append(shelter)
            else:
                risk_level = 'low'
                risk_color = 'green'
                low_risk_shelters.append(shelter)
            
            # 創建避難所標記
            popup_content = f"""
            <div style="font-family: Arial, sans-serif;">
                <h4>{shelter_name}</h4>
                <p><strong>地址:</strong> {shelter_address}</p>
                <p><strong>縣市:</strong> {county}</p>
                <p><strong>最近 AQI 測站:</strong> {nearest_station['station_name']}</p>
                <p><strong>測站 AQI:</strong> <span style="color: {get_aqi_color(nearest_station['aqi'])}; font-weight: bold;">{nearest_station['aqi']}</span></p>
                <p><strong>距離:</strong> {distance:.2f} 公里</p>
                <p><strong>風險等級:</strong> <span style="color: {risk_color}; font-weight: bold;">{risk_level.upper()}</span></p>
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
                tooltip=f"{shelter_name} - 風險: {risk_level}"
            ).add_to(m)
            
        except Exception as e:
            print(f"處理避難所 {shelter.get('避難收容處所名稱', '未知')} 時發生錯誤: {e}")
            continue
    
    # 添加圖例
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 250px; height: 200px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px">
    <h4>圖例說明</h4>
    <p><strong>AQI 測站:</strong></p>
    <i class="fa fa-circle" style="color:green"></i> 良好 (0-50)<br>
    <i class="fa fa-circle" style="color:yellow"></i> 普通 (51-100)<br>
    <i class="fa fa-circle" style="color:orange"></i> 對敏感族群不健康 (101-150)<br>
    <i class="fa fa-circle" style="color:red"></i> 對所有族群不健康 (151-200)<br>
    <i class="fa fa-circle" style="color:purple"></i> 非常不健康 (201+)<br>
    <p><strong>避難所風險:</strong></p>
    <i class="fa fa-circle" style="color:green"></i> 低風險 (AQI ≤ 100)<br>
    <i class="fa fa-circle" style="color:orange"></i> 中風險 (AQI 101-150)<br>
    <i class="fa fa-circle" style="color:red"></i> 高風險 (AQI > 150)<br>
    <p><strong>紅色圓圈:</strong> 高風險 AQI 測站影響範圍</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m, {
        'high_risk': high_risk_shelters,
        'medium_risk': medium_risk_shelters,
        'low_risk': low_risk_shelters,
        'high_risk_stations': high_risk_stations
    }

def generate_analysis_report(shelters_df, risk_analysis, aqi_stations, output_file='shelter_analysis_report.md'):
    """
    生成分析報告
    """
    total_shelters = len(shelters_df)
    high_risk_count = len(risk_analysis['high_risk'])
    medium_risk_count = len(risk_analysis['medium_risk'])
    low_risk_count = len(risk_analysis['low_risk'])
    high_risk_stations = len(risk_analysis['high_risk_stations'])
    
    report_content = f"""# 颱風後避難所空氣品質風險分析報告

## 分析概覽
- **分析時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **避難所總數**: {total_shelters} 個
- **AQI 測站數**: {len(aqi_stations)} 個

## 風險分析結果

### 避難所風險分布
- **🔴 高風險避難所**: {high_risk_count} 個 ({high_risk_count/total_shelters*100:.1f}%)
  - 定義: 附近 AQI 測站 > 150
  - 影響: 對所有族群健康有害
  
- **🟡 中風險避難所**: {medium_risk_count} 個 ({medium_risk_count/total_shelters*100:.1f}%)
  - 定義: 附近 AQI 測站 101-150
  - 影響: 對敏感族群有害
  
- **🟢 低風險避難所**: {low_risk_count} 個 ({low_risk_count/total_shelters*100:.1f}%)
  - 定義: 附近 AQI 測站 ≤ 100
  - 影響: 空氣品質可接受

### 高風險 AQI 測站
- **高風險測站數**: {high_risk_stations} 個
- **影響範圍**: 每個測站周圍 10 公里

"""
    
    # 添加高風險避難所詳細資訊
    if high_risk_count > 0:
        report_content += "## 🔴 高風險避難所詳細資訊\n\n"
        report_content += "| 避難所名稱 | 地址 | 縣市 | 最近測站 | AQI | 距離(公里) | 預計收容人數 |\n"
        report_content += "|-----------|------|------|----------|-----|-----------|--------------|\n"
        
        for shelter in risk_analysis['high_risk'][:20]:  # 顯示前20個
            try:
                shelter_lat = float(shelter['緯度'])
                shelter_lon = float(shelter['經度'])
                nearest_station, distance = find_nearest_aqi_station(shelter_lat, shelter_lon, aqi_stations)
                
                report_content += f"| {shelter['避難收容處所名稱']} | {shelter['避難收容處所地址']} | {shelter['縣市及鄉鎮市區']} | {nearest_station['station_name']} | {nearest_station['aqi']} | {distance:.2f} | {shelter.get('預計收容人數', 'N/A')} |\n"
            except:
                continue
        
        if high_risk_count > 20:
            report_content += f"| ... 還有 {high_risk_count - 20} 個高風險避難所 | | | | | | |\n"
    
    # 添加高風險測站詳細資訊
    if high_risk_stations > 0:
        report_content += "\n## 🔴 高風險 AQI 測站\n\n"
        report_content += "| 測站名稱 | 縣市 | AQI | 狀態 | 座標 |\n"
        report_content += "|----------|------|-----|------|------|\n"
        
        for station in risk_analysis['high_risk_stations']:
            report_content += f"| {station['station_name']} | {station['county']} | {station['aqi']} | {station['status']} | {station['lat']:.4f}, {station['lon']:.4f} |\n"
    
    report_content += f"""
## 建議措施

### 立即行動 (高風險)
1. **通報相關單位**: 通知 {high_risk_count} 個高風險避難所管理單位
2. **提供防護設備**: 為避難民眾提供 N95 口罩或空氣清淨機
3. **通訊系統**: 建立空氣品質監測通報機制
4. **醫療準備**: 準備呼吸道疾病醫療資源

### 預防措施 (中風險)
1. **監測加強**: 加強 {medium_risk_count} 個中風險避難所的空氣品質監測
2. **敏感族群保護**: 特別關注兒童、老人、慢性病患者
3. **通報機制**: 建立 AQI 超標通報程序

### 長期改善
1. **避難所選址**: 未來避難所選址應考慮空氣品質因素
2. **綠化改善**: 在避難所周圍增加綠化以改善空氣品質
3. **通風系統**: 改善避難所通風系統

## 技術說明
- **分析方法**: 以最近 AQI 測站數值評估避難所風險
- **距離計算**: 使用 Haversine 公式計算球面距離
- **風險分級**: 依據環保署 AQI 標準分級
- **影響範圍**: 高風險測站周圍 10 公里視為影響區域

## 限制與建議
1. **資料限制**: 實際 AQI 數值可能因時間和地點而異
2. **空間解析度**: 建議增加更多 AQI 測站以提高精確度
3. **即時監測**: 建議建立即時監測和預警系統
"""
    
    # 保存報告
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"分析報告已保存至: {output_file}")
    return report_content

def main():
    """
    主程式
    """
    print("開始颱風後避難所空氣品質風險分析...")
    
    try:
        # 讀取避難所資料
        shelters_df = get_clean_shelter_data('data/shelters.csv')
        
        # 獲取 AQI 測站資料
        aqi_stations = get_aqi_station_data()
        
        # 創建疊圖
        shelter_map, risk_analysis = create_shelter_aqi_map(shelters_df, aqi_stations)
        
        # 保存地圖
        map_file = 'output/shelter_aqi_risk_map.html'
        shelter_map.save(map_file)
        print(f"風險地圖已保存至: {map_file}")
        
        # 生成分析報告
        report_content = generate_analysis_report(shelters_df, risk_analysis, aqi_stations)
        
        # 顯示統計結果
        print("\n=== 分析結果摘要 ===")
        total_shelters = len(shelters_df)
        print(f"避難所總數: {total_shelters}")
        print(f"🔴 高風險避難所: {len(risk_analysis['high_risk'])} 個 ({len(risk_analysis['high_risk'])/total_shelters*100:.1f}%)")
        print(f"🟡 中風險避難所: {len(risk_analysis['medium_risk'])} 個 ({len(risk_analysis['medium_risk'])/total_shelters*100:.1f}%)")
        print(f"🟢 低風險避難所: {len(risk_analysis['low_risk'])} 個 ({len(risk_analysis['low_risk'])/total_shelters*100:.1f}%)")
        print(f"🔴 高風險 AQI 測站: {len(risk_analysis['high_risk_stations'])} 個")
        
        print(f"\n請查看以下檔案:")
        print(f"- 風險地圖: {map_file}")
        print(f"- 分析報告: shelter_analysis_report.md")
        
    except Exception as e:
        print(f"程式執行錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
