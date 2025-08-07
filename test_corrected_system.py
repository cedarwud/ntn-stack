#!/usr/bin/env python3
"""
測試修復後的距離計算系統

驗證理論公式修正是否有效改善距離計算精度
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# 添加路徑
sys.path.append('/home/sat/ntn-stack/netstack')

from netstack_api.services.distance_correction_service import create_distance_correction_service

def load_test_satellites():
    """載入測試衛星數據"""
    return [
        {"name": "STARLINK-63389", "norad_id": "63389", "elevation_deg": 84.27, "distance_km": 1005.39, "orbit_altitude_km": 550.0},
        {"name": "STARLINK-62508", "norad_id": "62508", "elevation_deg": 73.40, "distance_km": 1752.60, "orbit_altitude_km": 550.0},
        {"name": "STARLINK-60332", "norad_id": "60332", "elevation_deg": 66.36, "distance_km": 2261.54, "orbit_altitude_km": 550.0},
        {"name": "STARLINK-53422", "norad_id": "53422", "elevation_deg": 65.54, "distance_km": 2542.20, "orbit_altitude_km": 550.0},
        {"name": "STARLINK-59424", "norad_id": "59424", "elevation_deg": 63.12, "distance_km": 2307.87, "orbit_altitude_km": 550.0},
        {"name": "STARLINK-61673", "norad_id": "61673", "elevation_deg": 61.40, "distance_km": 2871.59, "orbit_altitude_km": 550.0},
        {"name": "STARLINK-57346", "norad_id": "57346", "elevation_deg": 49.65, "distance_km": 823.23, "orbit_altitude_km": 550.0},
        {"name": "STARLINK-56497", "norad_id": "56497", "elevation_deg": 34.94, "distance_km": 5532.74, "orbit_altitude_km": 550.0},
        {"name": "STARLINK-55392", "norad_id": "55392", "elevation_deg": 25.40, "distance_km": 8917.35, "orbit_altitude_km": 550.0},
        {"name": "STARLINK-51963", "norad_id": "51963", "elevation_deg": 18.25, "distance_km": 8712.70, "orbit_altitude_km": 550.0},
        {"name": "STARLINK-46355", "norad_id": "46355", "elevation_deg": 17.77, "distance_km": 9052.51, "orbit_altitude_km": 550.0},
        {"name": "STARLINK-60061", "norad_id": "60061", "elevation_deg": 16.85, "distance_km": 9057.74, "orbit_altitude_km": 550.0},
        {"name": "STARLINK-51773", "norad_id": "51773", "elevation_deg": 16.06, "distance_km": 10273.58, "orbit_altitude_km": 550.0},
        {"name": "STARLINK-45207", "norad_id": "45207", "elevation_deg": 15.92, "distance_km": 9976.82, "orbit_altitude_km": 550.0},
        {"name": "STARLINK-61533", "norad_id": "61533", "elevation_deg": 15.34, "distance_km": 10181.75, "orbit_altitude_km": 550.0}
    ]

async def test_distance_correction():
    """測試距離修正系統"""
    print("🔧 測試距離修正系統")
    print("=" * 60)
    
    # 創建距離修正服務
    correction_service = create_distance_correction_service()
    
    # 載入測試數據
    test_satellites = load_test_satellites()
    
    print(f"📊 測試衛星數量: {len(test_satellites)}顆")
    print(f"📍 觀測點: NTPU (24.9441667°N, 121.3713889°E)")
    print("")
    
    # 處理星座修正
    corrected_satellites, correction_stats = correction_service.process_satellite_constellation(
        test_satellites,
        observer_lat=24.9441667,
        observer_lon=121.3713889
    )
    
    # 顯示修正統計
    print("📈 修正統計摘要")
    print("-" * 40)
    total = correction_stats["total_satellites"]
    corrected = correction_stats["corrections_applied"]
    validated = correction_stats["validation_passed"]
    
    print(f"總衛星數: {total}顆")
    print(f"應用修正: {corrected}顆 ({corrected/total*100:.1f}%)")
    print(f"高信心修正: {correction_stats['high_confidence_corrections']}顆")
    print(f"驗證通過: {validated}顆 ({validated/total*100:.1f}%)")
    print(f"平均誤差改善: {correction_stats['average_original_error']:.1f}km → {correction_stats['average_corrected_error']:.1f}km")
    
    improvement = 0
    if correction_stats['average_original_error'] > 0:
        improvement = (1 - correction_stats['average_corrected_error']/correction_stats['average_original_error']) * 100
        print(f"精度改善: {improvement:.1f}%")
    
    print("")
    
    # 修正方法分佈
    if correction_stats['correction_methods']:
        print("🛠️ 修正方法分佈")
        print("-" * 40)
        for method, count in correction_stats['correction_methods'].items():
            print(f"{method}: {count}次 ({count/corrected*100:.1f}%)")
        print("")
    
    # 詳細對比
    print("📊 修正前後對比")
    print("-" * 80)
    print(f"{'衛星名稱':<15} {'仰角':<8} {'原始距離':<10} {'理論距離':<10} {'修正距離':<10} {'原始誤差':<10} {'修正誤差':<10}")
    print("-" * 80)
    
    for i, sat in enumerate(corrected_satellites):
        original = sat["distance_km"] if "original_distance_km" not in sat else sat["original_distance_km"]
        theoretical = sat.get("theoretical_distance_km", 0)
        corrected_dist = sat["distance_km"]
        
        original_error = abs(original - theoretical) if theoretical > 0 else 0
        corrected_error = abs(corrected_dist - theoretical) if theoretical > 0 else 0
        
        print(
            f"{sat['name']:<15} "
            f"{sat['elevation_deg']:<8.1f} "
            f"{original:<10.1f} "
            f"{theoretical:<10.1f} "
            f"{corrected_dist:<10.1f} "
            f"{original_error:<10.1f} "
            f"{corrected_error:<10.1f}"
        )
    
    # 按仰角分析
    print("")
    print("🎯 仰角分組分析")
    print("-" * 40)
    
    high_elev = [s for s in corrected_satellites if s.get('elevation_deg', 0) > 60]
    medium_elev = [s for s in corrected_satellites if 20 <= s.get('elevation_deg', 0) <= 60]
    low_elev = [s for s in corrected_satellites if s.get('elevation_deg', 0) < 20]
    
    def analyze_group(group, name):
        if not group:
            return
        
        original_errors = []
        corrected_errors = []
        
        for sat in group:
            original = sat["distance_km"] if "original_distance_km" not in sat else sat["original_distance_km"]
            theoretical = sat.get("theoretical_distance_km", 0)
            corrected_dist = sat["distance_km"]
            
            if theoretical > 0:
                original_errors.append(abs(original - theoretical))
                corrected_errors.append(abs(corrected_dist - theoretical))
        
        if original_errors:
            avg_original = sum(original_errors) / len(original_errors)
            avg_corrected = sum(corrected_errors) / len(corrected_errors)
            improvement = (1 - avg_corrected / avg_original) * 100 if avg_original > 0 else 0
            
            print(f"{name} ({len(group)}顆):")
            print(f"  平均原始誤差: {avg_original:.1f}km")
            print(f"  平均修正誤差: {avg_corrected:.1f}km")
            print(f"  精度改善: {improvement:.1f}%")
    
    analyze_group(high_elev, "高仰角(>60°)")
    analyze_group(medium_elev, "中仰角(20-60°)")
    analyze_group(low_elev, "低仰角(<20°)")
    
    # 生成修正報告
    report = correction_service.generate_correction_report(correction_stats)
    
    # 保存報告
    report_file = "/home/sat/ntn-stack/distance_correction_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("")
    print(f"📄 修正報告已保存至: {report_file}")
    
    # 測試特定仰角的理論計算
    print("")
    print("🧮 理論公式驗證")
    print("-" * 40)
    
    test_elevations = [84.27, 60.0, 45.0, 30.0, 15.34]
    for elev in test_elevations:
        theoretical = correction_service.calculate_theoretical_slant_range(elev, 550.0)
        print(f"仰角{elev:6.2f}°: 理論斜距 = {theoretical:7.1f}km")
    
    print("")
    print("🎯 測試完成")
    
    # 返回關鍵統計
    return {
        "total_satellites": total,
        "corrections_applied": corrected,
        "accuracy_improvement": improvement,
        "original_error": correction_stats['average_original_error'],
        "corrected_error": correction_stats['average_corrected_error']
    }

if __name__ == "__main__":
    result = asyncio.run(test_distance_correction())
    
    print("")
    print("📈 最終評估")
    print("=" * 60)
    print(f"✅ 系統修復成功: {result['corrections_applied']}/{result['total_satellites']}顆衛星應用修正")
    print(f"📊 精度改善: {result['accuracy_improvement']:.1f}%")
    print(f"🎯 平均誤差: {result['original_error']:.1f}km → {result['corrected_error']:.1f}km")
    
    if result['accuracy_improvement'] > 50:
        print("🌟 修復效果優秀！")
    elif result['accuracy_improvement'] > 25:
        print("✅ 修復效果良好！") 
    else:
        print("⚠️ 修復效果有限，需要進一步優化")