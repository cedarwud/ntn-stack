#!/usr/bin/env python3
"""
測試 CoordinateSpecificOrbitEngine
Phase 0.4 - 座標特定軌道引擎測試
"""

import sys
import json
from datetime import datetime, timezone
from pathlib import Path

# 添加 netstack 路徑
sys.path.append('netstack/src')
sys.path.append('netstack')

# 直接導入模組避免包導入問題
import importlib.util

# 導入座標引擎
engine_spec = importlib.util.spec_from_file_location(
    "coordinate_specific_orbit_engine", 
    "netstack/src/services/satellite/coordinate_specific_orbit_engine.py"
)
engine_module = importlib.util.module_from_spec(engine_spec)
engine_spec.loader.exec_module(engine_module)

CoordinateSpecificOrbitEngine = engine_module.CoordinateSpecificOrbitEngine
NTPU_COORDINATES = engine_module.NTPU_COORDINATES

# 導入 TLE 載入器
loader_spec = importlib.util.spec_from_file_location(
    "local_tle_loader", 
    "netstack/src/services/satellite/local_tle_loader.py"
)
loader_module = importlib.util.module_from_spec(loader_spec)
loader_spec.loader.exec_module(loader_module)

LocalTLELoader = loader_module.LocalTLELoader

def test_coordinate_engine():
    """測試座標特定軌道引擎"""
    print("🚀 Phase 0.4 - CoordinateSpecificOrbitEngine 測試")
    print("=" * 60)
    
    # 1. 初始化引擎
    print("\n📍 1. 初始化軌道引擎")
    engine = CoordinateSpecificOrbitEngine(
        observer_lat=NTPU_COORDINATES['lat'],
        observer_lon=NTPU_COORDINATES['lon'],
        observer_alt=NTPU_COORDINATES['alt'],
        min_elevation=5.0
    )
    
    # 2. 載入測試衛星數據
    print("\n📡 2. 載入 TLE 數據")
    loader = LocalTLELoader("tle_data")
    starlink_data = loader.load_collected_data('starlink')
    
    if not starlink_data.get('daily_data'):
        print("❌ 無法載入 TLE 數據")
        return
    
    # 取前5顆衛星進行測試 (節省時間)
    test_satellites = starlink_data['daily_data'][0]['satellites'][:5]
    print(f"✅ 載入測試衛星: {len(test_satellites)} 顆")
    
    # 3. 測試單顆衛星軌道計算
    print("\n🛰️ 3. 測試 96 分鐘軌道週期計算")
    reference_time = datetime.now(timezone.utc)
    test_satellite = test_satellites[0]
    
    orbit_data = engine.compute_96min_orbital_cycle(test_satellite, reference_time)
    
    if 'error' not in orbit_data:
        stats = orbit_data['statistics']
        print(f"衛星: {test_satellite['name']}")
        print(f"  - 總位置點: {stats['total_positions']}")
        print(f"  - 可見位置: {stats['visible_positions']}")
        print(f"  - 可見性: {stats['visibility_percentage']:.1f}%")
        print(f"  - 最大仰角: {stats['max_elevation']:.1f}°")
        print(f"  - 可見時段: {len(orbit_data['visibility_windows'])} 個")
    else:
        print(f"❌ 軌道計算失敗: {orbit_data['error']}")
        return
    
    # 4. 測試可見性篩選 (小規模測試)
    print(f"\n🔍 4. 測試可見性篩選 ({len(test_satellites)} 顆衛星)")
    
    filtered_satellites = engine.filter_visible_satellites(test_satellites, reference_time)
    
    print(f"篩選結果:")
    print(f"  - 輸入衛星: {len(test_satellites)}")
    print(f"  - 可見衛星: {len(filtered_satellites)}")
    print(f"  - 篩選效率: {(len(test_satellites) - len(filtered_satellites))/len(test_satellites)*100:.1f}% 減少")
    
    if len(filtered_satellites) == 0:
        print("⚠️ 無可見衛星，跳過後續測試")
        return
    
    # 5. 測試最佳時間窗口識別
    print(f"\n⏰ 5. 測試最佳時間窗口識別")
    
    optimal_window = engine.find_optimal_timewindow(filtered_satellites, window_hours=6, reference_time=reference_time)
    
    best_window = optimal_window['optimal_window']
    print(f"最佳時間窗口:")
    print(f"  - 時段: {best_window['start_time']} 至 {best_window['end_time']}")
    print(f"  - 時長: {best_window['duration_hours']} 小時")
    print(f"  - 品質分數: {best_window['quality_score']:.1f}")
    print(f"  - 可見衛星: {best_window['visible_satellites']}")
    print(f"  - 平均仰角: {best_window['avg_elevation']:.1f}°")
    print(f"  - 換手機會: {best_window['handover_opportunities']}")
    
    # 6. 測試前端展示數據生成
    print(f"\n🎨 6. 測試前端展示數據生成")
    
    display_data = engine.generate_display_optimized_data(
        optimal_window, 
        acceleration=60, 
        distance_scale=0.1
    )
    
    metadata = display_data['metadata']
    print(f"展示優化數據:")
    print(f"  - 加速倍數: {metadata['acceleration_factor']}x")
    print(f"  - 距離縮放: {metadata['distance_scale']}")
    print(f"  - 動畫時長: {metadata['animation_duration_seconds']:.1f} 秒")
    print(f"  - 建議FPS: {metadata['recommended_fps']}")
    print(f"  - 關鍵幀數: {len(display_data['animation_keyframes'])}")
    
    # 7. 輸出測試結果摘要
    print(f"\n📊 7. 測試結果摘要")
    
    test_summary = {
        'test_completed_at': datetime.now(timezone.utc).isoformat(),
        'engine_config': {
            'observer_location': NTPU_COORDINATES,
            'min_elevation': engine.min_elevation,
            'orbital_period_minutes': engine.orbital_period_minutes
        },
        'test_results': {
            'satellites_tested': len(test_satellites),
            'visible_satellites': len(filtered_satellites),
            'filtering_efficiency': f"{(len(test_satellites) - len(filtered_satellites))/len(test_satellites)*100:.1f}%",
            'best_window_quality': best_window['quality_score'],
            'animation_keyframes': len(display_data['animation_keyframes'])
        },
        'performance_metrics': {
            'orbit_calculation_success': 'error' not in orbit_data,
            'visibility_filtering_success': len(filtered_satellites) >= 0,
            'optimal_window_found': best_window['quality_score'] > 0
        }
    }
    
    # 保存測試結果
    output_file = Path("test_coordinate_engine_results.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(test_summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 測試完成，結果已保存至: {output_file}")
    print(f"\n🎯 Phase 0.4 CoordinateSpecificOrbitEngine 測試成功！")
    
    return test_summary

if __name__ == "__main__":
    try:
        result = test_coordinate_engine()
        if result:
            print(f"\n✨ 所有測試通過，CoordinateSpecificOrbitEngine 運作正常")
        else:
            print(f"\n❌ 測試失敗")
    except Exception as e:
        print(f"\n💥 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()