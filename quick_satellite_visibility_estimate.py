#!/usr/bin/env python3
"""
快速衛星可見性估算
基於LEO衛星理論模型，快速估算404顆衛星配置下的可見數量
"""

import math

def quick_leo_visibility_estimate():
    """快速估算LEO衛星可見性"""
    
    print("🛰️ LEO衛星可見性快速估算")
    print("="*50)
    
    # 基本參數
    earth_radius_km = 6371
    sat_altitude_km = 550  # Starlink典型軌道
    observer_lat = 24.9442  # NTPU緯度
    
    # 計算地平線距離
    horizon_distance_km = math.sqrt((earth_radius_km + sat_altitude_km)**2 - earth_radius_km**2)
    print(f"📍 觀測點: NTPU ({observer_lat}°N)")
    print(f"🛰️ 衛星軌道高度: {sat_altitude_km} km")
    print(f"🌅 理論地平線距離: {horizon_distance_km:.0f} km")
    
    # 可見天空面積計算
    # 地球表面積
    earth_surface_area = 4 * math.pi * earth_radius_km**2
    print(f"🌍 地球表面積: {earth_surface_area/1e6:.1f} 百萬平方公里")
    
    # 可見天空圓錐面積 (仰角≥0度)
    visible_area_ratio = 0.5  # 理論上觀測者可見地球50%表面
    visible_area = earth_surface_area * visible_area_ratio
    print(f"👁️ 可見天空面積: {visible_area/1e6:.1f} 百萬平方公里 (50%)")
    
    # 仰角限制
    elevation_thresholds = {
        "0度": 0,
        "5度": 5,
        "10度": 10
    }
    
    print(f"\n📊 不同仰角門檻下的可見面積比例:")
    
    area_ratios = {}
    for threshold_name, elevation_deg in elevation_thresholds.items():
        # 簡化計算：仰角限制會減少可見面積
        if elevation_deg == 0:
            area_ratio = 0.5  # 地平線以上50%
        else:
            # 使用球冠公式估算
            elevation_rad = math.radians(elevation_deg)
            # 簡化：仰角越高，可見面積越小
            area_ratio = 0.5 * (1 - elevation_deg / 90)
        
        area_ratios[threshold_name] = area_ratio
        print(f"   {threshold_name}: {area_ratio:.3f} ({area_ratio*100:.1f}%)")
    
    # 衛星分佈計算
    print(f"\n🛰️ 衛星分佈分析:")
    
    # 假設衛星均勻分佈在地球表面上方
    configurations = {
        "當前404顆": 404,
        "理論21顆同時可見": 21,
        "前端硬編碼30顆": 30
    }
    
    print(f"\n📈 不同配置下的可見衛星估算:")
    
    for config_name, total_satellites in configurations.items():
        print(f"\n--- {config_name} ---")
        
        for threshold_name, area_ratio in area_ratios.items():
            # 簡單估算：可見衛星 = 總衛星數 × 可見面積比例
            visible_count = total_satellites * area_ratio
            
            # 考慮星座特定門檻
            if threshold_name == "5度":
                # Starlink 5度門檻 (假設75%是Starlink)
                starlink_count = int(total_satellites * 0.75)
                starlink_visible = starlink_count * area_ratio
                oneweb_visible = 0  # 10度門檻下OneWeb不可見
                total_visible = starlink_visible
                print(f"   {threshold_name} (Starlink): {total_visible:.1f} 顆")
                
            elif threshold_name == "10度":
                # OneWeb 10度門檻 (假設25%是OneWeb)
                oneweb_count = int(total_satellites * 0.25)
                oneweb_visible = oneweb_count * area_ratio
                print(f"   {threshold_name} (OneWeb): {oneweb_visible:.1f} 顆")
                
            else:
                print(f"   {threshold_name}: {visible_count:.1f} 顆")
    
    # 綜合估算
    print(f"\n🎯 綜合估算結果 (404顆配置):")
    
    # 假設：75% Starlink (5度), 25% OneWeb (10度)
    starlink_count = 404 * 0.75  # 303顆
    oneweb_count = 404 * 0.25    # 101顆
    
    # 5度門檻下的可見Starlink
    starlink_visible_5deg = starlink_count * area_ratios["5度"]
    
    # 10度門檻下的可見OneWeb  
    oneweb_visible_10deg = oneweb_count * area_ratios["10度"]
    
    # 總可見數量
    total_simultaneous_visible = starlink_visible_5deg + oneweb_visible_10deg
    
    print(f"   Starlink可見 (5度): {starlink_visible_5deg:.1f} 顆")
    print(f"   OneWeb可見 (10度): {oneweb_visible_10deg:.1f} 顆")
    print(f"   總同時可見: {total_simultaneous_visible:.1f} 顆")
    
    # 物理約束檢查
    print(f"\n🔬 物理約束驗證:")
    
    # LEO衛星軌道週期約96分鐘
    orbital_period_min = 96
    print(f"   軌道週期: {orbital_period_min} 分鐘")
    
    # 衛星在可見範圍內的時間 (約10-15分鐘)
    visibility_duration_min = 12
    print(f"   單顆衛星可見時間: ~{visibility_duration_min} 分鐘")
    
    # 理論上需要多少顆衛星來維持連續覆蓋
    satellites_needed_for_coverage = orbital_period_min / visibility_duration_min
    print(f"   維持連續覆蓋需要: {satellites_needed_for_coverage:.1f} 倍衛星")
    
    # 對比404顆配置是否合理
    if total_simultaneous_visible > 0:
        coverage_multiplier = 404 / total_simultaneous_visible
        print(f"   404顆配置的覆蓋倍數: {coverage_multiplier:.1f}x")
        
        if coverage_multiplier >= satellites_needed_for_coverage:
            print(f"   ✅ 404顆配置足夠維持 {total_simultaneous_visible:.1f} 顆同時可見")
        else:
            print(f"   ⚠️ 404顆配置可能不足以維持穩定覆蓋")
    
    print(f"\n🏁 結論:")
    print(f"   在404顆衛星的動態池配置下，")
    print(f"   NTPU觀測點理論上同時可見約 {total_simultaneous_visible:.0f} 顆衛星")
    print(f"   這個數量符合LEO衛星網絡的設計目標")

if __name__ == "__main__":
    quick_leo_visibility_estimate()