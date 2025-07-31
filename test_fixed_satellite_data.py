#!/usr/bin/env python3
"""
測試修復後的衛星數據 - 生成軌跡圖並對比
"""

import sys
import json
import requests
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

def test_api_response():
    """測試統一時間序列API響應"""
    try:
        url = "http://localhost:8888/api/v1/satellites/unified/timeseries"
        params = {
            "constellation": "starlink",
            "limit": 3  # 只測試3顆衛星
        }
        
        print("🔄 正在請求統一時間序列數據...")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ API 請求失敗: {response.status_code}")
            print(f"錯誤內容: {response.text}")
            return None
            
        data = response.json()
        print(f"✅ API 請求成功")
        
        # 檢查數據結構
        if 'satellites' not in data:
            print("❌ 響應中沒有 satellites 字段")
            return None
            
        satellites = data['satellites']
        print(f"📊 獲得 {len(satellites)} 顆衛星數據")
        
        return data
        
    except Exception as e:
        print(f"❌ API 測試失敗: {e}")
        return None

def extract_position_data(data):
    """從API響應中提取位置數據"""
    satellites_data = []
    
    for satellite in data['satellites']:
        sat_name = satellite.get('name', 'Unknown')
        time_series = satellite.get('time_series', [])
        
        if not time_series:
            print(f"⚠️ 衛星 {sat_name} 沒有時間序列數據")
            continue
            
        # 提取觀測數據
        elevations = []
        ranges = []
        timestamps = []
        
        for point in time_series:
            observation = point.get('observation', {})
            elevations.append(observation.get('elevation_deg', 0))
            ranges.append(observation.get('range_km', 0))
            timestamps.append(point.get('time_offset_seconds', 0))
        
        satellites_data.append({
            'name': sat_name,
            'elevations': elevations,
            'ranges': ranges,
            'timestamps': timestamps
        })
        
        print(f"✅ 衛星 {sat_name}:")
        print(f"   - 仰角範圍: {min(elevations):.1f}° ~ {max(elevations):.1f}°")
        print(f"   - 距離範圍: {min(ranges):.1f} ~ {max(ranges):.1f} km")
        print(f"   - 數據點數: {len(timestamps)}")
    
    return satellites_data

def create_trajectory_plot(satellites_data, output_filename="real_v3_fixed.png"):
    """創建衛星軌跡圖"""
    try:
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        colors = ['green', 'orange', 'red', 'blue', 'purple']
        
        for i, sat_data in enumerate(satellites_data):
            if i >= len(colors):
                break
                
            color = colors[i]
            name = sat_data['name']
            timestamps = np.array(sat_data['timestamps']) / 60  # 轉換為分鐘
            elevations = sat_data['elevations']
            ranges = sat_data['ranges']
            
            # 仰角圖
            ax1.plot(timestamps, elevations, color=color, linewidth=2, 
                    label=f"{name}", marker='o', markersize=1)
            
            # 距離圖
            ax2.plot(timestamps, ranges, color=color, linewidth=2, 
                    label=f"{name}", marker='o', markersize=1)
        
        # 設置仰角圖
        ax1.set_ylabel('衛星仰角 (度)', fontsize=12, color='green')
        ax1.set_title('修復後的衛星軌跡 - 仰角變化', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper right')
        ax1.set_ylim(-5, 95)
        
        # 設置距離圖
        ax2.set_xlabel('時間 (分鐘)', fontsize=12)
        ax2.set_ylabel('衛星距離 (km)', fontsize=12, color='orange')
        ax2.set_title('修復後的衛星軌跡 - 距離變化', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='upper right')
        ax2.set_ylim(300, 3200)
        
        plt.tight_layout()
        plt.savefig(output_filename, dpi=150, bbox_inches='tight')
        print(f"✅ 軌跡圖已保存: {output_filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ 創建軌跡圖失敗: {e}")
        return False

def analyze_data_quality(satellites_data):
    """分析數據品質"""
    print("\n📈 數據品質分析:")
    
    for sat_data in satellites_data:
        name = sat_data['name']
        elevations = sat_data['elevations']
        ranges = sat_data['ranges']
        
        # 檢查數據變化
        elev_variation = max(elevations) - min(elevations)
        range_variation = max(ranges) - min(ranges)
        
        # 檢查是否有重複值（水平線問題）
        unique_elevations = len(set(elevations))
        unique_ranges = len(set(ranges))
        
        print(f"\n  衛星 {name}:")
        print(f"    仰角變化: {elev_variation:.1f}° (獨特值: {unique_elevations}/{len(elevations)})")
        print(f"    距離變化: {range_variation:.1f} km (獨特值: {unique_ranges}/{len(ranges)})")
        
        # 判斷是否修復
        if elev_variation < 1.0 and unique_elevations < 10:
            print(f"    ⚠️ 可能仍有水平線問題 (仰角變化太小)")
        elif elev_variation > 10.0 and unique_elevations > 50:
            print(f"    ✅ 仰角變化正常 (軌道動力學)")
        
        if range_variation < 10.0 and unique_ranges < 10:
            print(f"    ⚠️ 可能仍有水平線問題 (距離變化太小)")  
        elif range_variation > 100.0 and unique_ranges > 50:
            print(f"    ✅ 距離變化正常 (軌道動力學)")

def main():
    """主函數"""
    print("🛰️ 測試修復後的衛星數據系統")
    print("=" * 60)
    
    # 1. 測試API響應
    data = test_api_response()
    if not data:
        print("❌ API 測試失敗，無法繼續")
        return False
    
    # 2. 提取位置數據
    print("\n📊 提取衛星位置數據...")
    satellites_data = extract_position_data(data)
    
    if not satellites_data:
        print("❌ 沒有有效的衛星數據")
        return False
    
    # 3. 分析數據品質
    analyze_data_quality(satellites_data)
    
    # 4. 生成軌跡圖
    print(f"\n🎨 生成修復後的衛星軌跡圖...")
    success = create_trajectory_plot(satellites_data)
    
    if success:
        print(f"\n✅ 測試完成! 修復後的軌跡圖已生成")
        print(f"📄 請檢查 real_v3_fixed.png 並與之前的 real_v2.png 對比")
        return True
    else:
        print(f"\n❌ 測試失敗")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)