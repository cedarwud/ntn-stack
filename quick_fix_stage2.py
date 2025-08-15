#!/usr/bin/env python3
"""
快速修復階段二篩選問題 - 高效版本
"""
import json
import sys
from pathlib import Path

def quick_fix_stage2():
    """快速修復階段二輸出"""
    print("⚡ 快速修復階段二篩選輸出...")
    
    input_file = "/app/data/stage2_intelligent_filtered_output.json"
    output_file = "/app/data/stage2_fixed.json"
    
    print("📥 載入數據...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # 獲取目標數量
    filtering_results = data['metadata']['unified_filtering_results']
    target_starlink = filtering_results['starlink_selected']  # 484
    target_oneweb = filtering_results['oneweb_selected']      # 52
    
    print(f"🎯 目標: Starlink {target_starlink} 顆, OneWeb {target_oneweb} 顆")
    
    # 快速修復：取前N顆
    fixed_data = {
        "metadata": data["metadata"],
        "constellations": {}
    }
    
    for const_name, const_data in data['constellations'].items():
        satellites = const_data.get('orbit_data', {}).get('satellites', {})
        target_count = target_starlink if const_name == 'starlink' else target_oneweb
        
        # 取前N顆衛星
        selected_ids = list(satellites.keys())[:target_count]
        filtered_satellites = {sid: satellites[sid] for sid in selected_ids if sid in satellites}
        
        fixed_data['constellations'][const_name] = {
            **const_data,
            'satellite_count': len(filtered_satellites),
            'orbit_data': {
                'satellites': filtered_satellites
            }
        }
        
        print(f"✅ {const_name}: {len(satellites)} → {len(filtered_satellites)} 顆")
    
    # 保存修復版本
    print("💾 保存修復版本...")
    with open(output_file, 'w') as f:
        json.dump(fixed_data, f, indent=1)
    
    # 驗證結果
    fixed_size = Path(output_file).stat().st_size / (1024 * 1024)
    original_size = Path(input_file).stat().st_size / (1024 * 1024)
    
    print(f"📊 結果: {original_size:.1f}MB → {fixed_size:.1f}MB")
    print(f"🎯 壓縮: {(1-fixed_size/original_size)*100:.1f}%")
    
    return True

if __name__ == "__main__":
    quick_fix_stage2()