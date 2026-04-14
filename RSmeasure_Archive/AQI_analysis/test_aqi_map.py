import os
import folium
from datetime import datetime
from collections import Counter
import csv
import math

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

def get_mock_aqi_data():
    """
    模擬 AQI 數據
    """
    return [
        {
            'sitename': '台北',
            'county': '台北市',
            'aqi': '45',
            'latitude': '25.0478',
            'longitude': '121.5170'
        },
        {
            'sitename': '松山',
            'county': '台北市', 
            'aqi': '52',
            'latitude': '25.0500',
            'longitude': '121.5800'
        },
        {
            'sitename': '中山',
            'county': '台北市',
            'aqi': '38',
            'latitude': '25.0670',
            'longitude': '121.5200'
        },
        {
            'sitename': '新店',
            'county': '新北市',
            'aqi': '125',
            'latitude': '24.9700',
            'longitude': '121.5400'
        },
        {
            'sitename': '板橋',
            'county': '新北市',
            'aqi': '78',
            'latitude': '25.0100',
            'longitude': '121.4600'
        },
        {
            'sitename': '桃園',
            'county': '桃園市',
            'aqi': '156',
            'latitude': '24.9900',
            'longitude': '121.3000'
        },
        {
            'sitename': '新竹',
            'county': '新竹市',
            'aqi': '42',
            'latitude': '24.8000',
            'longitude': '120.9700'
        },
        {
            'sitename': '台中',
            'county': '台中市',
            'aqi': '89',
            'latitude': '24.1500',
            'longitude': '120.6700'
        },
        {
            'sitename': '台南',
            'county': '台南市',
            'aqi': '67',
            'latitude': '22.9900',
            'longitude': '120.2000'
        },
        {
            'sitename': '高雄',
            'county': '高雄市',
            'aqi': '134',
            'latitude': '22.6200',
            'longitude': '120.3100'
        }
    ]

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
    else:
        return 'red'

def export_to_csv(aqi_data, filename='output/aqi_data.csv'):
    """
    將 AQI 數據匯出為 CSV 檔案
    """
    taipei_station_lat, taipei_station_lon = 25.0478, 121.5170
    
    csv_data = []
    for station in aqi_data:
        try:
            site_name = station.get('sitename', '未知測站')
            county = station.get('county', '未知縣市')
            aqi = station.get('aqi', 'N/A')
            lat = float(station.get('latitude', 0))
            lon = float(station.get('longitude', 0))
            
            if lat == 0 or lon == 0:
                distance = 'N/A'
            else:
                distance = calculate_distance(lat, lon, taipei_station_lat, taipei_station_lon)
            
            csv_data.append({
                '測站名稱': site_name,
                '縣市': county,
                'AQI': aqi,
                '緯度': lat,
                '經度': lon,
                '距離台北車站(公里)': round(distance, 2) if distance != 'N/A' else 'N/A'
            })
            
        except (ValueError, KeyError) as e:
            continue
    
    if csv_data:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['測站名稱', '縣市', 'AQI', '緯度', '經度', '距離台北車站(公里)']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        
        print(f"數據已匯出至: {filename}")
        return len(csv_data)
    else:
        print("沒有資料可匯出")
        return 0

def create_aqi_map(aqi_data):
    """
    創建 AQI 地圖
    """
    taiwan_center = [23.8, 120.9]
    
    m = folium.Map(
        location=taiwan_center,
        zoom_start=7,
        tiles='OpenStreetMap'
    )
    
    for station in aqi_data:
        try:
            site_name = station.get('sitename', '未知測站')
            county = station.get('county', '未知縣市')
            aqi = station.get('aqi', 'N/A')
            
            lat = float(station.get('latitude', 0))
            lon = float(station.get('longitude', 0))
            
            if lat == 0 or lon == 0:
                continue
            
            color = get_aqi_color(aqi)
            
            popup_content = f"""
            <b>{site_name}</b><br>
            縣市: {county}<br>
            AQI: {aqi}
            """
            
            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                popup=folium.Popup(popup_content, max_width=300),
                color='black',
                weight=1,
                fillColor=color,
                fillOpacity=0.7,
                tooltip=f"{site_name} - AQI: {aqi}"
            ).add_to(m)
            
        except (ValueError, KeyError) as e:
            print(f"處理測站資料時發生錯誤: {e}")
            continue
    
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 150px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <h4>AQI 指標</h4>
    <i class="fa fa-circle" style="color:green"></i> 0-50 良好<br>
    <i class="fa fa-circle" style="color:yellow"></i> 51-100 普通<br>
    <i class="fa fa-circle" style="color:red"></i> 101+ 不健康<br>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def main():
    """
    主程式
    """
    print("正在獲取模擬 AQI 數據...")
    
    try:
        aqi_data = get_mock_aqi_data()
        print(f"成功獲取 {len(aqi_data)} 個測站數據")
        
        print("正在創建 AQI 地圖...")
        aqi_map = create_aqi_map(aqi_data)
        
        output_file = 'output/aqi_map.html'
        aqi_map.save(output_file)
        print(f"地圖已保存至: {output_file}")
        
        print("正在匯出 CSV 資料...")
        csv_count = export_to_csv(aqi_data)
        print(f"已匯出 {csv_count} 筆測站資料")
        
        if aqi_data:
            print("\n=== AQI 統計資訊 ===")
            print(f"總測站數量: {len(aqi_data)}")
            
            counties = [station.get('county', '未知') for station in aqi_data]
            county_count = Counter(counties)
            print(f"縣市分布: {dict(county_count)}")
            
            valid_aqi_values = []
            for station in aqi_data:
                aqi = station.get('aqi')
                if aqi and aqi != '' and aqi != 'N/A':
                    try:
                        valid_aqi_values.append(float(aqi))
                    except ValueError:
                        continue
            
            if valid_aqi_values:
                avg_aqi = sum(valid_aqi_values) / len(valid_aqi_values)
                max_aqi = max(valid_aqi_values)
                min_aqi = min(valid_aqi_values)
                print(f"AQI 平均值: {avg_aqi:.1f}")
                print(f"AQI 最高值: {max_aqi:.1f}")
                print(f"AQI 最低值: {min_aqi:.1f}")
        
        print(f"\n請開啟 {output_file} 查看地圖")
        print("請開啟 output/aqi_data.csv 查看距離計算結果")
        
    except Exception as e:
        print(f"程式執行錯誤: {e}")

if __name__ == "__main__":
    main()
