import os
import requests
import folium
import math
from collections import defaultdict
import urllib3

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    使用 Haversine 公式計算兩點間的距離（公里）
    """
    # 將經緯度轉換為弧度
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine 公式
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # 地球半徑（公里）
    r = 6371
    return c * r

def twd67_to_wgs84(x, y):
    """
    將 TWD67 座標轉換為 WGS84 (近似轉換)
    這是一個簡化的轉換，實際應該使用更精確的轉換參數
    """
    # TWD67 到 WGS84 的近似轉換參數
    # 這裡使用簡化的轉換公式
    dx = -800  # X 方向偏移（米）
    dy = 300   # Y 方向偏移（米）
    
    # 將偏移量轉換為經緯度變化
    lat_offset = dy / 111320  # 1度緯度約111320米
    lon_offset = dx / (111320 * math.cos(25.0 * math.pi / 180))  # 台灣緯度約25度
    
    # 假設原始座標已經是經緯度格式，加上偏移
    lat = y + lat_offset
    lon = x + lon_offset
    
    return lat, lon

def get_weather_station_data():
    """
    獲取氣象站 API 數據
    假設 API 返回包含兩組座標的數據
    """
    # 模擬氣象站數據（實際應該從 API 獲取）
    # 這裡創建模擬數據來演示 CRS 比較
    mock_stations = [
        {
            'station_name': '台北',
            'twd67_lat': 25.0478,
            'twd67_lon': 121.5170,
            'wgs84_lat': 25.0340,
            'wgs84_lon': 121.5645
        },
        {
            'station_name': '台中',
            'twd67_lat': 24.1477,
            'twd67_lon': 120.6736,
            'wgs84_lat': 24.1340,
            'wgs84_lon': 120.7200
        },
        {
            'station_name': '高雄',
            'twd67_lat': 22.6273,
            'twd67_lon': 120.3014,
            'wgs84_lat': 22.6130,
            'wgs84_lon': 120.3480
        },
        {
            'station_name': '花蓮',
            'twd67_lat': 23.8224,
            'twd67_lon': 121.5474,
            'wgs84_lat': 23.8080,
            'wgs84_lon': 121.5940
        },
        {
            'station_name': '台東',
            'twd67_lat': 22.7598,
            'twd67_lon': 121.1607,
            'wgs84_lat': 22.7450,
            'wgs84_lon': 121.2070
        }
    ]
    
    return mock_stations

def create_crs_compare_map(stations):
    """
    創建 CRS 比較地圖
    """
    # 台灣中心點
    taiwan_center = [23.8, 120.9]
    
    # 創建地圖
    m = folium.Map(
        location=taiwan_center,
        zoom_start=7,
        tiles='OpenStreetMap'
    )
    
    # 統計數據
    distances = []
    
    for station in stations:
        station_name = station['station_name']
        
        # TWD67 座標（轉換為 WGS84）
        twd67_lat, twd67_lon = station['twd67_lat'], station['twd67_lon']
        
        # WGS84 座標
        wgs84_lat, wgs84_lon = station['wgs84_lat'], station['wgs84_lon']
        
        # 計算距離
        distance = calculate_distance(twd67_lat, twd67_lon, wgs84_lat, wgs84_lon)
        distances.append(distance)
        
        # 添加 TWD67 標記（紅色）
        folium.CircleMarker(
            location=[twd67_lat, twd67_lon],
            radius=8,
            popup=f"""
            <div style="font-family: Arial, sans-serif;">
                <h4>{station_name} (TWD67)</h4>
                <p><strong>座標:</strong> {twd67_lat:.6f}, {twd67_lon:.6f}</p>
                <p><strong>與WGS84距離:</strong> {distance:.3f} 公里 ({distance*1000:.1f} 公尺)</p>
            </div>
            """,
            color='darkred',
            weight=2,
            fillColor='red',
            fillOpacity=0.7,
            tooltip=f"{station_name} (TWD67)"
        ).add_to(m)
        
        # 添加 WGS84 標記（藍色）
        folium.CircleMarker(
            location=[wgs84_lat, wgs84_lon],
            radius=8,
            popup=f"""
            <div style="font-family: Arial, sans-serif;">
                <h4>{station_name} (WGS84)</h4>
                <p><strong>座標:</strong> {wgs84_lat:.6f}, {wgs84_lon:.6f}</p>
                <p><strong>與TWD67距離:</strong> {distance:.3f} 公里 ({distance*1000:.1f} 公尺)</p>
            </div>
            """,
            color='darkblue',
            weight=2,
            fillColor='blue',
            fillOpacity=0.7,
            tooltip=f"{station_name} (WGS84)"
        ).add_to(m)
        
        # 添加連接線
        folium.PolyLine(
            locations=[[twd67_lat, twd67_lon], [wgs84_lat, wgs84_lon]],
            color='green',
            weight=2,
            opacity=0.6,
            popup=f"距離: {distance:.3f} 公里"
        ).add_to(m)
    
    # 添加圖例
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 140px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <h4>座標系統比較</h4>
    <i class="fa fa-circle" style="color:red"></i> TWD67 座標<br>
    <i class="fa fa-circle" style="color:blue"></i> WGS84 座標<br>
    <i class="fa fa-minus" style="color:green"></i> 距離連線<br>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m, distances

def main():
    """
    主程式
    """
    print("正在獲取氣象站數據...")
    
    try:
        # 獲取氣象站數據
        stations = get_weather_station_data()
        print(f"成功獲取 {len(stations)} 個測站數據")
        
        # 創建比較地圖
        print("正在創建 CRS 比較地圖...")
        crs_map, distances = create_crs_compare_map(stations)
        
        # 保存地圖
        output_file = 'output/crs_compare_map.html'
        crs_map.save(output_file)
        print(f"地圖已保存至: {output_file}")
        
        # 統計分析
        print("\n=== CRS 比較統計分析 ===")
        print(f"測站數量: {len(stations)}")
        
        if distances:
            avg_distance = sum(distances) / len(distances)
            max_distance = max(distances)
            min_distance = min(distances)
            
            print(f"平均距離: {avg_distance:.3f} 公里 ({avg_distance*1000:.1f} 公尺)")
            print(f"最大距離: {max_distance:.3f} 公里 ({max_distance*1000:.1f} 公尺)")
            print(f"最小距離: {min_distance:.3f} 公里 ({min_distance*1000:.1f} 公尺)")
            
            print("\n各測站距離詳情:")
            for i, station in enumerate(stations):
                print(f"{station['station_name']}: {distances[i]:.3f} 公里 ({distances[i]*1000:.1f} 公尺)")
        
        print(f"\n請開啟 {output_file} 查看地圖")
        print("紅色標記為 TWD67 座標，藍色標記為 WGS84 座標")
        print("綠色連線顯示兩種座標系統的差距")
        
    except Exception as e:
        print(f"程式執行錯誤: {e}")

if __name__ == "__main__":
    main()
