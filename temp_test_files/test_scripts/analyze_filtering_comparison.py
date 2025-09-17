#!/usr/bin/env python3
"""
精確分析篩選對比
比較我的單一檔案計算器與階段二處理器的初步篩選結果
"""

import json
import sys
import os

# 確保可以載入我的計算器
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from satellite_visibility_calculator import SatelliteVisibilityCalculator

def analyze_at_least_once_visible():
    """
    重新運行計算器並統計在時間段內至少可見一次的衛星數量
    """
    print("🔍 重新分析：統計96分鐘內至少可見一次的衛星數量")

    # 使用與階段二相同的觀測位置
    observer_location = {
        'latitude': 24.9439,   # NTPU
        'longitude': 121.3711,
        'altitude': 50.0
    }

    # 創建計算器
    tle_data_path = "satellite-processing-system/data/tle_data"
    calculator = SatelliteVisibilityCalculator(tle_data_path, observer_location)

    # 運行分析（相同參數）
    success = calculator.run_complete_analysis(
        constellation='both',
        max_satellites=8837,
        duration_minutes=96,
        interval_seconds=30,
        min_elevation_deg=5.0
    )

    if not success:
        print("❌ 計算失敗")
        return None

    # 統計至少可見一次的衛星
    satellites_with_visibility = set()

    for time_entry in calculator.visibility_timeline:
        for visible_sat in time_entry['visible_satellites']:
            satellites_with_visibility.add(visible_sat['name'])

    print(f"\n📊 統計結果:")
    print(f"輸入衛星總數: 8,837 顆")
    print(f"至少可見一次的衛星: {len(satellites_with_visibility)} 顆")
    print(f"篩選率: {len(satellites_with_visibility)/8837*100:.1f}%")

    # 按星座分析
    starlink_visible = set()
    oneweb_visible = set()

    for time_entry in calculator.visibility_timeline:
        for visible_sat in time_entry['visible_satellites']:
            if visible_sat['constellation'] == 'starlink':
                starlink_visible.add(visible_sat['name'])
            elif visible_sat['constellation'] == 'oneweb':
                oneweb_visible.add(visible_sat['name'])

    print(f"\n🛰️ 按星座統計:")
    print(f"STARLINK: {len(starlink_visible)}/8186 顆 ({len(starlink_visible)/8186*100:.1f}%)")
    print(f"ONEWEB: {len(oneweb_visible)}/651 顆 ({len(oneweb_visible)/651*100:.1f}%)")

    return {
        'total_input': 8837,
        'total_visible': len(satellites_with_visibility),
        'starlink_visible': len(starlink_visible),
        'oneweb_visible': len(oneweb_visible),
        'filtering_rate': len(satellites_with_visibility)/8837*100
    }

def compare_with_stage2():
    """
    與階段二結果對比
    """
    print("\n" + "="*60)
    print("🔬 篩選結果對比分析")
    print("="*60)

    # 我的程式結果
    my_results = analyze_at_least_once_visible()

    if my_results is None:
        return

    # 階段二結果（已知）
    stage2_results = {
        'total_input': 8837,
        'total_output': 2272,
        'starlink_output': 2241,
        'oneweb_output': 31,
        'filtering_rate': 2272/8837*100
    }

    print(f"\n📊 對比結果:")
    print(f"{'指標':<25} {'我的程式':<15} {'階段二處理器':<15} {'差異'}")
    print("-" * 70)
    print(f"{'輸入衛星':<25} {my_results['total_input']:<15} {stage2_results['total_input']:<15} {my_results['total_input'] - stage2_results['total_input']}")
    print(f"{'篩選後衛星':<25} {my_results['total_visible']:<15} {stage2_results['total_output']:<15} {my_results['total_visible'] - stage2_results['total_output']}")
    print(f"{'Starlink篩選':<25} {my_results['starlink_visible']:<15} {stage2_results['starlink_output']:<15} {my_results['starlink_visible'] - stage2_results['starlink_output']}")
    print(f"{'OneWeb篩選':<25} {my_results['oneweb_visible']:<15} {stage2_results['oneweb_output']:<15} {my_results['oneweb_visible'] - stage2_results['oneweb_output']}")
    print(f"{'篩選率(%)':<25} {my_results['filtering_rate']:<15.1f} {stage2_results['filtering_rate']:<15.1f} {my_results['filtering_rate'] - stage2_results['filtering_rate']:.1f}")

    print(f"\n🎯 關鍵發現:")
    if my_results['total_visible'] > stage2_results['total_output']:
        print(f"• 我的程式篩選出較多衛星 (+{my_results['total_visible'] - stage2_results['total_output']} 顆)")
    elif my_results['total_visible'] < stage2_results['total_output']:
        print(f"• 階段二處理器篩選出較多衛星 (+{stage2_results['total_output'] - my_results['total_visible']} 顆)")
    else:
        print(f"• 兩個程式的篩選結果完全一致！")

    # 分析可能的差異原因
    print(f"\n🔍 可能的差異原因:")
    print(f"1. 時間基準不同 (TLE epoch vs 當前時間)")
    print(f"2. 座標系統精度差異")
    print(f"3. 篩選邏輯實現差異")
    print(f"4. 數據來源或版本差異")

    return my_results, stage2_results

if __name__ == "__main__":
    compare_with_stage2()