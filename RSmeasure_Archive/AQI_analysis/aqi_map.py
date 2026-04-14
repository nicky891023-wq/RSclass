import os
import requests
import folium
from dotenv import load_dotenv
from datetime import datetime
from collections import Counter
import csv
import math
import urllib3

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 載入環境變數
load_dotenv()

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

def export_to_csv(aqi_data, filename='output/aqi_data.csv'):
    """
    將 AQI 數據匯出為 CSV 檔案
    """
    # 台北車站座標
    taipei_station_lat, taipei_station_lon = 25.0478, 121.5170
    
    # 準備 CSV 資料
    csv_data = []
    for station in aqi_data:
        try:
            site_name = station.get('sitename', '未知測站')
            county = station.get('county', '未知縣市')
            aqi = station.get('aqi', 'N/A')
            status = station.get('status', '未知')
            pollutant = station.get('pollutant', 'N/A')
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
                '狀態': status,
                '主要污染物': pollutant,
                'PM2.5': station.get('pm2.5', 'N/A'),
                'PM10': station.get('pm10', 'N/A'),
                'SO2': station.get('so2', 'N/A'),
                'NO2': station.get('no2', 'N/A'),
                'CO': station.get('co', 'N/A'),
                'O3': station.get('o3', 'N/A'),
                '風速': station.get('wind_speed', 'N/A'),
                '風向': station.get('wind_direc', 'N/A'),
                '緯度': lat,
                '經度': lon,
                '距離台北車站(公里)': round(distance, 2) if distance != 'N/A' else 'N/A',
                '更新時間': station.get('publishtime', 'N/A')
            })
            
        except (ValueError, KeyError) as e:
            continue
    
    # 寫入 CSV 檔案
    if csv_data:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['測站名稱', '縣市', 'AQI', '狀態', '主要污染物', 'PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3', '風速', '風向', '緯度', '經度', '距離台北車站(公里)', '更新時間']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        
        print(f"數據已匯出至: {filename}")
        return len(csv_data)
    else:
        print("沒有資料可匯出")
        return 0

def get_epa_aqi_data():
    """
    從環境部 API 獲取全台即時 AQI 數據
    """
    api_key = os.getenv('EPA_API_KEY')
    if not api_key:
        raise ValueError("EPA_API_KEY 未在 .env 檔案中設定")
    
    # 環境部 API 端點 - AQX_P_432 (空氣品質測站即時監測數據)
    url = f"https://data.moenv.gov.tw/api/v2/AQX_P_432?api_key={api_key}"
    
    try:
        response = requests.get(url, verify=False)
        response.raise_for_status()
        data = response.json()
        
        # 檢查回應格式
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if data.get('success') != True:
                raise ValueError(f"API 呼叫失敗: {data.get('message', '未知錯誤')}")
            return data.get('records', data.get('data', []))
        else:
            raise ValueError("未知的 API 回應格式")
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"API 請求錯誤: {e}")
    except KeyError as e:
        raise Exception(f"API 回應格式錯誤: {e}")

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

def create_aqi_map(aqi_data):
    """
    創建 AQI 地圖
    """
    # 台灣中心點
    taiwan_center = [23.8, 120.9]
    
    # 創建地圖
    m = folium.Map(
        location=taiwan_center,
        zoom_start=7,
        tiles='OpenStreetMap'
    )
    
    # 添加測站標記
    for station in aqi_data:
        try:
            # 獲取測站資訊
            site_name = station.get('sitename', '未知測站')
            county = station.get('county', '未知縣市')
            aqi = station.get('aqi', 'N/A')
            status = station.get('status', '未知')
            pollutant = station.get('pollutant', 'N/A')
            publishtime = station.get('publishtime', 'N/A')
            
            # 污染物數據
            pm2_5 = station.get('pm2.5', 'N/A')
            pm10 = station.get('pm10', 'N/A')
            so2 = station.get('so2', 'N/A')
            no2 = station.get('no2', 'N/A')
            co = station.get('co', 'N/A')
            o3 = station.get('o3', 'N/A')
            o3_8hr = station.get('o3_8hr', 'N/A')
            
            # 氣象數據
            wind_speed = station.get('wind_speed', 'N/A')
            wind_direc = station.get('wind_direc', 'N/A')
            co_8hr = station.get('co_8hr', 'N/A')
            pm2_5_avg = station.get('pm2.5_avg', 'N/A')
            pm10_avg = station.get('pm10_avg', 'N/A')
            so2_avg = station.get('so2_avg', 'N/A')
            
            # 經緯度
            lat = float(station.get('latitude', 0))
            lon = float(station.get('longitude', 0))
            
            if lat == 0 or lon == 0:
                continue
            
            # 獲取顏色
            color = get_aqi_color(aqi)
            
            # 創建彈出視窗內容 - 簡化版本確保點選功能正常
            popup_html = f"""
            <div style="width: 300px; font-family: Arial, sans-serif;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px; margin: -12px -12px 10px -12px; border-radius: 8px 8px 0 0;">
                    <h3 style="margin: 0; font-size: 18px;">{site_name}</h3>
                    <p style="margin: 4px 0 0 0; opacity: 0.9;">{county}</p>
                </div>
                
                <div style="padding: 10px;">
                    <div style="background: #f8f9fa; padding: 8px; border-radius: 5px; margin-bottom: 10px;">
                        <strong>AQI:</strong> <span style="font-size: 16px; font-weight: bold; color: {get_aqi_color(aqi)};">{aqi}</span>
                        <br><strong>狀態:</strong> {status}
                        <br><strong>主要污染物:</strong> {pollutant}
                    </div>
                    
                    <div style="margin-bottom: 10px;">
                        <strong>🔴 污染物濃度:</strong><br>
                        <small>PM2.5: {pm2_5} μg/m³ | PM10: {pm10} μg/m³</small><br>
                        <small>SO₂: {so2} ppb | NO₂: {no2} ppb</small><br>
                        <small>CO: {co} ppm | O₃: {o3} ppb</small>
                    </div>
                    
                    <div>
                        <strong>🌤️ 氣象資訊:</strong><br>
                        <small>風速: {wind_speed} m/s | 風向: {wind_direc}°</small><br>
                        <small>更新: {publishtime}</small>
                    </div>
                </div>
            </div>
            """
            
            # 添加圓形標記
            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                popup=folium.Popup(popup_html, max_width=350),
                color='black',
                weight=1,
                fillColor=color,
                fillOpacity=0.7,
                tooltip=f"{site_name} - AQI: {aqi}"
            ).add_to(m)
            
        except (ValueError, KeyError) as e:
            print(f"處理測站資料時發生錯誤: {e}")
            continue
    
    # 添加圖例
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
    print("正在獲取環境部 AQI 數據...")
    
    try:
        # 獲取 AQI 數據
        aqi_data = get_epa_aqi_data()
        print(f"成功獲取 {len(aqi_data)} 個測站數據")
        
        # 創建地圖
        print("正在創建 AQI 地圖...")
        aqi_map = create_aqi_map(aqi_data)
        
        # 保存地圖
        output_file = 'output/aqi_map.html'
        aqi_map.save(output_file)
        print(f"地圖已保存至: {output_file}")
        
        # 匯出 CSV 資料
        print("正在匯出 CSV 資料...")
        csv_count = export_to_csv(aqi_data)
        print(f"已匯出 {csv_count} 筆測站資料")
        
        # 顯示統計資訊
        if aqi_data:
            print("\n=== AQI 統計資訊 ===")
            print(f"總測站數量: {len(aqi_data)}")
            
            # 縣市分布
            counties = [station.get('county', '未知') for station in aqi_data]
            county_count = Counter(counties)
            print(f"縣市分布: {dict(county_count)}")
            
            # AQI 分布
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
        
    except Exception as e:
        print(f"程式執行錯誤: {e}")

if __name__ == "__main__":
    main()
