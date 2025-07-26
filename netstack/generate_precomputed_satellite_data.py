#!/usr/bin/env python3
"""
生成預計算衛星數據的腳本
在 Docker 建置時執行，產生內建的衛星歷史數據
"""

import argparse
import math
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any

def generate_simplified_satellite_data(
    observer_lat: float,
    observer_lon: float, 
    duration_hours: int,
    time_step_seconds: int
) -> List[Dict[str, Any]]:
    """生成簡化的衛星數據用於預載"""
    
    data = []
    start_time = datetime.utcnow()
    
    # 模擬 8 顆 LEO 衛星（符合 3GPP NTN 標準）
    satellites = [
        {"id": f"PRECOMP-{i+1}", "norad_id": 60000 + i, "orbit_offset": i * 45}
        for i in range(8)
    ]
    
    time_points = int(duration_hours * 3600 / time_step_seconds)
    
    for t in range(time_points):
        current_time = start_time + timedelta(seconds=t * time_step_seconds)
        
        for sat in satellites:
            # LEO 衛星軌道參數
            orbit_period = 95 * 60  # 95 分鐘軌道週期
            angular_velocity = 2 * math.pi / orbit_period
            
            # 軌道角度（考慮時間和衛星偏移）
            angle = (angular_velocity * t * time_step_seconds + 
                    math.radians(sat["orbit_offset"])) % (2 * math.pi)
            
            # 軌道傾斜角 53 度（類似 Starlink）
            inclination = math.radians(53.0)
            
            # 計算衛星位置
            sat_lat = math.degrees(math.asin(math.sin(inclination) * math.sin(angle)))
            
            # 經度考慮地球自轉
            earth_rotation_rate = 2 * math.pi / (24 * 3600)  # 地球自轉角速度
            lon_drift = math.degrees(earth_rotation_rate * t * time_step_seconds)
            sat_lon = (observer_lon + 120 * math.cos(angle) - lon_drift) % 360
            if sat_lon > 180:
                sat_lon -= 360
                
            # 衛星高度（550km 類似 Starlink）
            altitude = 550
                
            # 計算相對觀測者的距離和角度
            lat_diff_rad = math.radians(sat_lat - observer_lat)
            lon_diff_rad = math.radians(sat_lon - observer_lon)
            
            # 地心距離計算
            a = math.sin(lat_diff_rad/2)**2 + math.cos(math.radians(observer_lat)) * \
                math.cos(math.radians(sat_lat)) * math.sin(lon_diff_rad/2)**2
            ground_distance = 2 * 6371 * math.asin(math.sqrt(a))  # km
            
            # 空間距離（考慮高度）
            space_distance = math.sqrt(ground_distance**2 + altitude**2)
            
            # 仰角計算
            if ground_distance > 0:
                elevation = math.degrees(math.atan(altitude / ground_distance))
            else:
                elevation = 90.0
                
            # 方位角計算
            y = math.sin(lon_diff_rad) * math.cos(math.radians(sat_lat))
            x = (math.cos(math.radians(observer_lat)) * math.sin(math.radians(sat_lat)) - 
                 math.sin(math.radians(observer_lat)) * math.cos(math.radians(sat_lat)) * 
                 math.cos(lon_diff_rad))
            azimuth = (math.degrees(math.atan2(y, x)) + 360) % 360
            
            # 只保留仰角 > 10 度的可見衛星
            if elevation >= 10:
                # 信號強度基於距離的簡化模型
                signal_strength = max(25, 90 - 20 * math.log10(space_distance / 100))
                path_loss = 92.4 + 20 * math.log10(space_distance) + 20 * math.log10(28)  # 28 GHz
                
                record = {
                    "satellite_id": sat["id"],
                    "norad_id": sat["norad_id"],
                    "constellation": "precomputed",
                    "timestamp": current_time.isoformat(),
                    "latitude": round(sat_lat, 6),
                    "longitude": round(sat_lon, 6),
                    "altitude": altitude,
                    "elevation_angle": round(elevation, 2),
                    "azimuth_angle": round(azimuth, 2),
                    "observer_latitude": observer_lat,
                    "observer_longitude": observer_lon,
                    "observer_altitude": 100,
                    "signal_strength": round(signal_strength, 2),
                    "path_loss_db": round(path_loss, 2),
                    "calculation_method": "precomputed",
                    "data_quality": 0.8  # 中等品質預載數據
                }
                data.append(record)
                
    return data

def generate_sql_file(data: List[Dict[str, Any]], output_file: str):
    """將數據轉換為 SQL 插入語句"""
    
    with open(output_file, 'w') as f:
        f.write("-- 預計算衛星歷史數據\n")
        f.write("-- 生成時間: " + datetime.now().isoformat() + "\n\n")
        
        # 清空舊的預載數據
        f.write("DELETE FROM satellite_orbital_cache WHERE constellation = 'precomputed';\n")
        f.write("DELETE FROM satellite_tle_data WHERE constellation = 'precomputed';\n\n")
        
        # 插入對應的 TLE 數據
        f.write("-- 插入預載衛星的 TLE 數據\n")
        satellites = [
            {"id": f"PRECOMP-{i+1}", "norad_id": 60000 + i, "orbit_offset": i * 45}
            for i in range(8)
        ]
        
        for sat in satellites:
            f.write(f"INSERT INTO satellite_tle_data (satellite_id, norad_id, satellite_name, constellation, line1, line2, epoch, orbital_period) VALUES ")
            f.write(f"('{sat['id']}', {sat['norad_id']}, '{sat['id']}', 'precomputed', ")
            f.write(f"'1 {sat['norad_id']}U 24001A   24001.00000000  .00000000  00000-0  00000-0 0  9990', ")
            f.write(f"'2 {sat['norad_id']}  53.0000   0.0000 0000000   0.0000   0.0000 15.50000000000000', ")
            f.write(f"'2024-01-01 00:00:00+00', 95.0);\n")
        
        f.write("\n")
        
        # 批次插入新數據
        if data:
            f.write("INSERT INTO satellite_orbital_cache (\n")
            f.write("    satellite_id, norad_id, constellation, timestamp,\n")
            f.write("    position_x, position_y, position_z,\n") 
            f.write("    latitude, longitude, altitude,\n")
            f.write("    velocity_x, velocity_y, velocity_z, orbital_period,\n")
            f.write("    elevation_angle, azimuth_angle, range_rate,\n")
            f.write("    calculation_method, data_quality\n")
            f.write(") VALUES\n")
            
            for i, record in enumerate(data):
                comma = "," if i < len(data) - 1 else ";"
                f.write(f"    ('{record['satellite_id']}', {record['norad_id']}, '{record['constellation']}', '{record['timestamp']}',\n")
                f.write(f"     0, 0, 0,\n")  # position_x, y, z
                f.write(f"     {record['latitude']}, {record['longitude']}, {record['altitude']},\n")
                f.write(f"     0, 0, 0, NULL,\n")  # velocity_x, y, z, orbital_period
                f.write(f"     {record['elevation_angle']}, {record['azimuth_angle']}, 0,\n")
                f.write(f"     '{record['calculation_method']}', {record['data_quality']}){comma}\n")

def main():
    parser = argparse.ArgumentParser(description='生成預計算衛星數據')
    parser.add_argument('--observer_lat', type=float, default=24.94417,
                       help='觀測者緯度 (預設: 台灣台北)')
    parser.add_argument('--observer_lon', type=float, default=121.37139,
                       help='觀測者經度 (預設: 台灣台北)')
    parser.add_argument('--duration_hours', type=int, default=6,
                       help='數據持續時間（小時）')
    parser.add_argument('--time_step_seconds', type=int, default=30,
                       help='時間步長（秒）')
    parser.add_argument('--output', type=str, required=True,
                       help='輸出 SQL 文件路徑')
    
    args = parser.parse_args()
    
    print(f"🛰️  開始生成預計算衛星數據...")
    print(f"   觀測位置: ({args.observer_lat:.5f}, {args.observer_lon:.5f})")
    print(f"   持續時間: {args.duration_hours} 小時")
    print(f"   時間步長: {args.time_step_seconds} 秒")
    
    # 生成數據
    data = generate_simplified_satellite_data(
        args.observer_lat,
        args.observer_lon,
        args.duration_hours,
        args.time_step_seconds
    )
    
    print(f"✅ 生成 {len(data)} 條衛星數據記錄")
    
    # 寫入 SQL 文件
    generate_sql_file(data, args.output)
    print(f"💾 SQL 文件已保存至: {args.output}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())