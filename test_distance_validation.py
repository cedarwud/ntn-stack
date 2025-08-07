#!/usr/bin/env python3
"""
距離驗證系統測試腳本

測試15顆衛星的距離計算精度
驗證理論公式vs SGP4系統計算的差異
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# 添加路徑
sys.path.append('/home/sat/ntn-stack/simworld/backend')

from app.services.distance_validator import create_distance_validator
from app.services.distance_calculator import Position

def load_satellite_data():
    """載入15顆衛星的測試數據"""
    return [
        {"name": "STARLINK-63389", "norad_id": "63389", "latitude": 25.1, "longitude": 121.5, "altitude": 550.0, "distance_km": 1005.39},
        {"name": "STARLINK-62508", "norad_id": "62508", "latitude": 24.8, "longitude": 120.9, "altitude": 550.0, "distance_km": 1752.60},
        {"name": "STARLINK-60332", "norad_id": "60332", "latitude": 24.5, "longitude": 120.8, "altitude": 550.0, "distance_km": 2261.54},
        {"name": "STARLINK-53422", "norad_id": "53422", "latitude": 24.4, "longitude": 120.7, "altitude": 550.0, "distance_km": 2542.20},
        {"name": "STARLINK-59424", "norad_id": "59424", "latitude": 24.7, "longitude": 122.2, "altitude": 550.0, "distance_km": 2307.87},
        {"name": "STARLINK-61673", "norad_id": "61673", "latitude": 24.3, "longitude": 120.6, "altitude": 550.0, "distance_km": 2871.59},
        {"name": "STARLINK-57346", "norad_id": "57346", "latitude": 26.2, "longitude": 122.8, "altitude": 550.0, "distance_km": 823.23},
        {"name": "STARLINK-56497", "norad_id": "56497", "latitude": 22.8, "longitude": 119.5, "altitude": 550.0, "distance_km": 5532.74},
        {"name": "STARLINK-55392", "norad_id": "55392", "latitude": 21.5, "longitude": 118.9, "altitude": 550.0, "distance_km": 8917.35},
        {"name": "STARLINK-51963", "norad_id": "51963", "latitude": 20.9, "longitude": 119.2, "altitude": 550.0, "distance_km": 8712.70},
        {"name": "STARLINK-46355", "norad_id": "46355", "latitude": 20.8, "longitude": 119.0, "altitude": 550.0, "distance_km": 9052.51},
        {"name": "STARLINK-60061", "norad_id": "60061", "latitude": 21.0, "longitude": 118.5, "altitude": 550.0, "distance_km": 9057.74},
        {"name": "STARLINK-51773", "norad_id": "51773", "latitude": 20.5, "longitude": 118.7, "altitude": 550.0, "distance_km": 10273.58},
        {"name": "STARLINK-45207", "norad_id": "45207", "latitude": 20.7, "longitude": 119.1, "altitude": 550.0, "distance_km": 9976.82},
        {"name": "STARLINK-61533", "norad_id": "61533", "latitude": 20.6, "longitude": 118.8, "altitude": 550.0, "distance_km": 10181.75}
    ]

async def test_distance_validation():
    """測試距離驗證系統"""
    print("🔧 啟動距離驗證系統測試")
    print("=" * 60)
    
    # 創建驗證器
    validator = create_distance_validator()
    
    # 載入衛星數據  
    satellites_data = load_satellite_data()
    
    # NTPU觀測點
    ue_position = Position(
        latitude=24.9441667,
        longitude=121.3713889,
        altitude=0.024  # 24m轉換為km
    )
    
    print(f"📍 觀測點: NTPU ({ue_position.latitude:.6f}°N, {ue_position.longitude:.6f}°E, {ue_position.altitude*1000:.0f}m)")
    print(f"📊 測試衛星數量: {len(satellites_data)}顆")
    print("")
    
    # 執行星座驗證
    validation_results, summary = validator.validate_satellite_constellation(
        satellites_data=satellites_data,
        ue_position=ue_position
    )
    
    # 顯示驗證結果
    print("📋 驗證結果摘要")
    print("-" * 40)
    print(f"總衛星數: {summary.total_satellites}顆")
    print(f"驗證通過: {summary.validation_passed}顆 ({summary.validation_passed/summary.total_satellites*100:.1f}%)")
    print(f"精度警告: {summary.validation_warnings}顆 ({summary.validation_warnings/summary.total_satellites*100:.1f}%)")
    print(f"精度失敗: {summary.validation_failed}顆 ({summary.validation_failed/summary.total_satellites*100:.1f}%)")
    print("")
    
    print("📈 誤差統計")
    print("-" * 40)
    print(f"平均誤差: {summary.mean_error_km:.2f} km")
    print(f"最大誤差: {summary.max_error_km:.2f} km")
    print(f"最小誤差: {summary.min_error_km:.2f} km")
    print(f"標準差: {summary.std_error_km:.2f} km")
    print("")
    
    print("🎯 仰角精度分析")
    print("-" * 40)
    print(f"高仰角(>60°)精度: {summary.high_elevation_accuracy:.1f}%")
    print(f"中仰角(30-60°)精度: {summary.medium_elevation_accuracy:.1f}%")
    print(f"低仰角(<30°)精度: {summary.low_elevation_accuracy:.1f}%")
    print("")
    
    print("📊 詳細驗證結果")
    print("-" * 80)
    print(f"{'衛星名稱':<15} {'仰角':<8} {'SGP4距離':<10} {'理論距離':<10} {'誤差':<8} {'相對誤差':<10} {'狀態':<8}")
    print("-" * 80)
    
    for result in validation_results:
        status_icon = {"PASS": "✅", "WARNING": "⚠️", "FAIL": "❌", "ERROR": "🚨"}.get(result.validation_status, "❓")
        print(
            f"{result.satellite_name:<15} "
            f"{result.elevation_deg:<8.1f} "
            f"{result.sgp4_distance_km:<10.1f} "
            f"{result.theoretical_distance_km:<10.1f} "
            f"{result.distance_difference_km:<8.1f} "
            f"{result.relative_error_percent:<10.1f} "
            f"{status_icon} {result.validation_status}"
        )
    
    # 識別問題衛星
    print("")
    print("🔍 問題分析")
    print("-" * 40)
    
    failed_sats = [r for r in validation_results if r.validation_status == "FAIL"]
    warning_sats = [r for r in validation_results if r.validation_status == "WARNING"]
    
    if failed_sats:
        print(f"❌ 精度失敗衛星 ({len(failed_sats)}顆):")
        for sat in failed_sats[:3]:  # 只顯示前3個
            print(f"   • {sat.satellite_name}: {sat.error_analysis}")
    
    if warning_sats:
        print(f"⚠️ 精度警告衛星 ({len(warning_sats)}顆):")
        for sat in warning_sats[:3]:  # 只顯示前3個
            print(f"   • {sat.satellite_name}: {sat.error_analysis}")
    
    # 生成完整報告
    report = validator.generate_validation_report(validation_results, summary)
    
    # 保存報告
    report_file = "/home/sat/ntn-stack/distance_validation_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("")
    print(f"📄 完整驗證報告已保存至: {report_file}")
    
    # 測試理論公式計算
    print("")
    print("🧮 理論公式測試")
    print("-" * 40)
    
    test_cases = [
        {"elevation": 84.27, "expected_sgp4": 1005.39},
        {"elevation": 49.65, "expected_sgp4": 823.23},
        {"elevation": 15.34, "expected_sgp4": 10181.75}
    ]
    
    for case in test_cases:
        theoretical = validator.calculate_theoretical_slant_range(case["elevation"])
        sgp4 = case["expected_sgp4"]
        diff = abs(theoretical - sgp4)
        error_pct = (diff / theoretical) * 100 if theoretical > 0 else 0
        
        print(f"仰角{case['elevation']:6.2f}°: 理論={theoretical:7.1f}km, SGP4={sgp4:7.1f}km, 誤差={diff:6.1f}km ({error_pct:5.1f}%)")
    
    print("")
    print("🎯 測試完成")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_distance_validation())