import os
import requests
import folium
import math
from collections import defaultdict
import urllib3
import json
from datetime import datetime

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

def get_cwb_weather_stations():
    """
    獲取中央氣象局測站資料
    """
    # CWB API 端點 - 測站基本資料
    url = "https://opendata.cwb.gov.tw/api/v1/rest/datastore/O-A0003-001"
    
    try:
        response = requests.get(url, verify=False, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        stations = []
        if data.get('success') == True:
            for record in data.get('records', {}).get('Station', []):
                station_info = {
                    'station_name': record.get('StationName', {}).get('StationName', '未知'),
                    'cwb_id': record.get('StationID', ''),
                    'lat': float(record.get('GeoInfo', {}).get('Coordinates', [{}])[0].get('StationLatitude', 0)),
                    'lon': float(record.get('GeoInfo', {}).get('Coordinates', [{}])[0].get('StationLongitude', 0)),
                    'county': record.get('GeoInfo', {}).get('County', '未知'),
                    'town': record.get('GeoInfo', {}).get('Town', '未知'),
                    'altitude': float(record.get('GeoInfo', {}).get('StationAltitude', 0))
                }
                if station_info['lat'] != 0 and station_info['lon'] != 0:
                    stations.append(station_info)
        
        print(f"成功獲取 {len(stations)} 個中央氣象局測站資料")
        return stations
        
    except Exception as e:
        print(f"獲取中央氣象局資料錯誤: {e}")
        return []

def get_epa_aqi_stations():
    """
    獲取環境部 AQI 測站資料
    """
    # 環境部 API 端點 - 空氣品質測站即時監測數據
    api_key = os.getenv('EPA_API_KEY', '')
    if not api_key:
        print("警告: EPA_API_KEY 未設定，使用模擬資料")
        return get_mock_epa_stations()
    
    url = f"https://data.moenv.gov.tw/api/v2/AQX_P_432?api_key={api_key}"
    
    try:
        response = requests.get(url, verify=False, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        stations = []
        for record in data:
            station_info = {
                'station_name': record.get('sitename', '未知'),
                'epa_id': record.get('siteid', ''),
                'lat': float(record.get('latitude', 0)),
                'lon': float(record.get('longitude', 0)),
                'county': record.get('county', '未知'),
                'aqi': record.get('aqi', 'N/A'),
                'status': record.get('status', '未知'),
                'pm25': record.get('pm2.5', 'N/A'),
                'pm10': record.get('pm10', 'N/A')
            }
            if station_info['lat'] != 0 and station_info['lon'] != 0:
                stations.append(station_info)
        
        print(f"成功獲取 {len(stations)} 個環境部 AQI 測站資料")
        return stations
        
    except Exception as e:
        print(f"獲取環境部資料錯誤: {e}")
        return get_mock_epa_stations()

def get_mock_epa_stations():
    """
    模擬環境部測站資料（當 API 失敗時使用）
    """
    mock_stations = [
        {'station_name': '中山', 'epa_id': '1', 'lat': 25.0623, 'lon': 121.5254, 'county': '台北市', 'aqi': '45', 'status': '良好'},
        {'station_name': '松山', 'epa_id': '2', 'lat': 25.0478, 'lon': 121.5770, 'county': '台北市', 'aqi': '52', 'status': '普通'},
        {'station_name': '大安', 'epa_id': '3', 'lat': 25.0263, 'lon': 121.5437, 'county': '台北市', 'aqi': '48', 'status': '良好'},
        {'station_name': '古亭', 'epa_id': '4', 'lat': 25.0167, 'lon': 121.5280, 'county': '台北市', 'aqi': '55', 'status': '普通'},
        {'station_name': '萬華', 'epa_id': '5', 'lat': 25.0308, 'lon': 121.4980, 'county': '台北市', 'aqi': '58', 'status': '普通'},
        {'station_name': '文山', 'epa_id': '6', 'lat': 24.9895, 'lon': 121.5715, 'county': '台北市', 'aqi': '42', 'status': '良好'},
        {'station_name': '士林', 'epa_id': '7', 'lat': 25.0877, 'lon': 121.5240, 'county': '台北市', 'aqi': '50', 'status': '良好'},
        {'station_name': '內湖', 'epa_id': '8', 'lat': 25.0699, 'lon': 121.5800, 'county': '台北市', 'aqi': '46', 'status': '良好'},
        {'station_name': '南港', 'epa_id': '9', 'lat': 25.0555, 'lon': 121.6030, 'county': '台北市', 'aqi': '44', 'status': '良好'},
        {'station_name': '板橋', 'epa_id': '10', 'lat': 25.0167, 'lon': 121.4620, 'county': '新北市', 'aqi': '60', 'status': '普通'}
    ]
    
    print(f"使用模擬環境部測站資料: {len(mock_stations)} 個測站")
    return mock_stations

def find_matching_stations(cwb_stations, epa_stations):
    """
    找出中央氣象局與環境部測站的匹配對應
    """
    matches = []
    
    for cwb_station in cwb_stations:
        cwb_name = cwb_station['station_name']
        cwb_county = cwb_station['county']
        
        # 尋找名稱相近的環境部測站
        for epa_station in epa_stations:
            epa_name = epa_station['station_name']
            epa_county = epa_station['county']
            
            # 檢查是否在同一縣市且名稱相似
            if cwb_county == epa_county or any(word in epa_name for word in cwb_name.split()):
                # 計算距離
                distance = calculate_distance(
                    cwb_station['lat'], cwb_station['lon'],
                    epa_station['lat'], epa_station['lon']
                )
                
                # 如果距離小於 5 公里，認為是同一個測站
                if distance < 5.0:
                    match_info = {
                        'cwb_station': cwb_station,
                        'epa_station': epa_station,
                        'distance': distance,
                        'match_type': 'auto'
                    }
                    matches.append(match_info)
                    break
    
    return matches

def create_comparison_map(cwb_stations, epa_stations, matches):
    """
    創建比較地圖
    """
    # 台灣中心點
    taiwan_center = [23.8, 120.9]
    
    # 創建地圖
    m = folium.Map(
        location=taiwan_center,
        zoom_start=8,
        tiles='OpenStreetMap'
    )
    
    # 添加中央氣象局測站（藍色）
    for station in cwb_stations:
        folium.CircleMarker(
            location=[station['lat'], station['lon']],
            radius=6,
            popup=f"""
            <div style="font-family: Arial, sans-serif;">
                <h4>{station['station_name']} (CWB)</h4>
                <p><strong>縣市:</strong> {station['county']}</p>
                <p><strong>座標:</strong> {station['lat']:.6f}, {station['lon']:.6f}</p>
                <p><strong>海拔:</strong> {station['altitude']} 公尺</p>
            </div>
            """,
            color='darkblue',
            weight=2,
            fillColor='blue',
            fillOpacity=0.7,
            tooltip=f"{station['station_name']} (CWB)"
        ).add_to(m)
    
    # 添加環境部測站（紅色）
    for station in epa_stations:
        folium.CircleMarker(
            location=[station['lat'], station['lon']],
            radius=6,
            popup=f"""
            <div style="font-family: Arial, sans-serif;">
                <h4>{station['station_name']} (EPA)</h4>
                <p><strong>縣市:</strong> {station['county']}</p>
                <p><strong>座標:</strong> {station['lat']:.6f}, {station['lon']:.6f}</p>
                <p><strong>AQI:</strong> {station['aqi']}</p>
                <p><strong>狀態:</strong> {station['status']}</p>
            </div>
            """,
            color='darkred',
            weight=2,
            fillColor='red',
            fillOpacity=0.7,
            tooltip=f"{station['station_name']} (EPA)"
        ).add_to(m)
    
    # 添加匹配測站的連接線
    for match in matches:
        cwb = match['cwb_station']
        epa = match['epa_station']
        distance = match['distance']
        
        folium.PolyLine(
            locations=[[cwb['lat'], cwb['lon']], [epa['lat'], epa['lon']]],
            color='green',
            weight=3,
            opacity=0.8,
            popup=f"匹配測站 - 距離: {distance:.3f} 公里"
        ).add_to(m)
    
    # 添加圖例
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 160px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <h4>測站比較圖例</h4>
    <i class="fa fa-circle" style="color:blue"></i> 中央氣象局測站<br>
    <i class="fa fa-circle" style="color:red"></i> 環境部 AQI 測站<br>
    <i class="fa fa-minus" style="color:green"></i> 匹配測站連線<br>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def generate_html_report(cwb_stations, epa_stations, matches):
    """
    生成 HTML 報告
    """
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>氣象局 vs 環境部測站比較分析</title>
    <style>
        body {{
            font-family: 'Microsoft JhengHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
        }}
        .stat-label {{
            margin-top: 10px;
            opacity: 0.9;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .distance-small {{
            color: #27ae60;
            font-weight: bold;
        }}
        .distance-medium {{
            color: #f39c12;
            font-weight: bold;
        }}
        .distance-large {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .update-time {{
            text-align: center;
            color: #7f8c8d;
            margin-top: 30px;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>氣象局 vs 環境部測站比較分析</h1>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{len(cwb_stations)}</div>
                <div class="stat-label">中央氣象局測站</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(epa_stations)}</div>
                <div class="stat-label">環境部 AQI 測站</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(matches)}</div>
                <div class="stat-label">匹配測站對</div>
            </div>
        </div>
        
        <h2>匹配測站分析</h2>
        <table>
            <thead>
                <tr>
                    <th>中央氣象局測站</th>
                    <th>環境部測站</th>
                    <th>縣市</th>
                    <th>距離 (公尺)</th>
                    <th>座標差異</th>
                </tr>
            </thead>
            <tbody>
"""
    
    # 添加匹配測站資料
    for match in matches:
        cwb = match['cwb_station']
        epa = match['epa_station']
        distance_m = match['distance'] * 1000
        
        # 距離分類
        if distance_m < 500:
            distance_class = 'distance-small'
        elif distance_m < 2000:
            distance_class = 'distance-medium'
        else:
            distance_class = 'distance-large'
        
        # 計算座標差異
        lat_diff = abs(cwb['lat'] - epa['lat']) * 111320  # 約111320公尺/度
        lon_diff = abs(cwb['lon'] - epa['lon']) * 111320 * math.cos(cwb['lat'] * math.pi / 180)
        
        html_content += f"""
                <tr>
                    <td>{cwb['station_name']}</td>
                    <td>{epa['station_name']}</td>
                    <td>{cwb['county']}</td>
                    <td class="{distance_class}">{distance_m:.1f}</td>
                    <td>緯度: {lat_diff:.1f}m, 經度: {lon_diff:.1f}m</td>
                </tr>
"""
    
    html_content += """
            </tbody>
        </table>
        
        <h2>統計摘要</h2>
        <div class="stats-grid">
"""
    
    # 計算統計數據
    if matches:
        distances = [match['distance'] * 1000 for match in matches]
        avg_distance = sum(distances) / len(distances)
        max_distance = max(distances)
        min_distance = min(distances)
        
        html_content += f"""
            <div class="stat-card">
                <div class="stat-number">{avg_distance:.1f}m</div>
                <div class="stat-label">平均距離</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{max_distance:.1f}m</div>
                <div class="stat-label">最大距離</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{min_distance:.1f}m</div>
                <div class="stat-label">最小距離</div>
            </div>
"""
    
    html_content += f"""
        </div>
        
        <div class="update-time">
            報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""
    
    return html_content

def main():
    """
    主程式
    """
    print("開始獲取真實氣象局與環境部資料...")
    
    try:
        # 獲取中央氣象局測站資料
        print("正在獲取中央氣象局測站資料...")
        cwb_stations = get_cwb_weather_stations()
        
        # 獲取環境部 AQI 測站資料
        print("正在獲取環境部 AQI 測站資料...")
        epa_stations = get_epa_aqi_stations()
        
        # 找出匹配測站
        print("正在分析測站匹配...")
        matches = find_matching_stations(cwb_stations, epa_stations)
        
        print(f"找到 {len(matches)} 對匹配測站")
        
        # 創建比較地圖
        print("正在創建比較地圖...")
        comparison_map = create_comparison_map(cwb_stations, epa_stations, matches)
        
        # 保存地圖
        map_file = 'output/real_stations_comparison_map.html'
        comparison_map.save(map_file)
        print(f"地圖已保存至: {map_file}")
        
        # 生成 HTML 報告
        print("正在生成 HTML 報告...")
        html_report = generate_html_report(cwb_stations, epa_stations, matches)
        
        # 保存 HTML 報告
        report_file = 'output/stations_comparison_report.html'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        print(f"HTML 報告已保存至: {report_file}")
        
        # 顯示統計結果
        print("\n=== 分析結果摘要 ===")
        print(f"中央氣象局測站: {len(cwb_stations)} 個")
        print(f"環境部 AQI 測站: {len(epa_stations)} 個")
        print(f"匹配測站對: {len(matches)} 對")
        
        if matches:
            distances = [match['distance'] * 1000 for match in matches]
            avg_distance = sum(distances) / len(distances)
            print(f"平均座標差距: {avg_distance:.1f} 公尺")
            
            # 距離分類統計
            small_count = sum(1 for d in distances if d < 500)
            medium_count = sum(1 for d in distances if 500 <= d < 2000)
            large_count = sum(1 for d in distances if d >= 2000)
            
            print(f"距離 < 500m: {small_count} 對")
            print(f"距離 500-2000m: {medium_count} 對")
            print(f"距離 >= 2000m: {large_count} 對")
        
        print(f"\n請查看以下檔案:")
        print(f"- 互動地圖: {map_file}")
        print(f"- 分析報告: {report_file}")
        
    except Exception as e:
        print(f"程式執行錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
