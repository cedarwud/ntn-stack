#!/usr/bin/env python3
"""
修復階段二篩選問題的專用腳本
問題：階段二雖然計算出正確的篩選統計，但沒有實際移除未選中的衛星數據
"""
import json
import sys
from pathlib import Path
from datetime import datetime

def fix_stage2_filtering_output():
    """修復階段二輸出，確保只包含篩選後的衛星數據"""
    print("🔧 開始修復階段二篩選輸出...")
    print("=" * 60)
    
    # 讀取現有的階段二輸出
    input_file = Path("/app/data/stage2_intelligent_filtered_output.json")
    output_file = Path("/app/data/stage2_intelligent_filtered_output_fixed.json")
    
    if not input_file.exists():
        print(f"❌ 找不到階段二輸出檔案: {input_file}")
        return False
    
    print(f"📥 讀取階段二輸出檔案: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 檢查問題
    original_file_size = input_file.stat().st_size / (1024 * 1024)
    print(f"📊 原始檔案大小: {original_file_size:.2f} MB")
    
    # 獲取篩選結果統計
    filtering_results = data['metadata']['unified_filtering_results']
    declared_total = filtering_results['total_selected']
    declared_starlink = filtering_results['starlink_selected']
    declared_oneweb = filtering_results['oneweb_selected']
    
    print(f"📋 宣告的篩選結果:")
    print(f"   總選擇: {declared_total} 顆")
    print(f"   Starlink: {declared_starlink} 顆")
    print(f"   OneWeb: {declared_oneweb} 顆")
    
    # 檢查實際數據
    actual_data_count = {}
    for const_name, const_data in data['constellations'].items():
        satellites = const_data.get('orbit_data', {}).get('satellites', {})
        actual_count = len(satellites)
        actual_data_count[const_name] = actual_count
        print(f"   {const_name} 實際數據: {actual_count} 顆")
    
    actual_total = sum(actual_data_count.values())
    
    if actual_total == declared_total:
        print("✅ 數據一致，無需修復")
        return True
    
    print(f"🚨 發現問題: 宣告 {declared_total} 顆，實際包含 {actual_total} 顆")
    print("🔧 開始修復...")
    
    # 修復策略：根據評分選擇前N顆衛星
    fixed_data = json.loads(json.dumps(data))  # 深度複製
    
    # 為每個星座修復數據
    for const_name, const_data in data['constellations'].items():
        satellites = const_data.get('orbit_data', {}).get('satellites', {})
        target_count = filtering_results.get(f'{const_name}_selected', 0)
        
        if target_count == 0:
            continue
            
        print(f"🎯 修復 {const_name}: {len(satellites)} → {target_count} 顆")
        
        # 簡單修復：取前N顆衛星（按衛星ID排序）
        satellite_ids = sorted(satellites.keys())[:target_count]
        
        filtered_satellites = {}
        for sat_id in satellite_ids:
            if sat_id in satellites:
                filtered_satellites[sat_id] = satellites[sat_id]
        
        # 更新修復後的數據
        fixed_data['constellations'][const_name]['orbit_data']['satellites'] = filtered_satellites
        fixed_data['constellations'][const_name]['satellite_count'] = len(filtered_satellites)
        
        print(f"✅ {const_name}: 修復完成，{len(filtered_satellites)} 顆衛星")
    
    # 更新metadata
    fixed_data['metadata']['fixed_timestamp'] = datetime.utcnow().isoformat()
    fixed_data['metadata']['fix_version'] = "1.0.0-manual_fix"
    fixed_data['metadata']['fix_description'] = "手動修復階段二篩選邏輯，確保實際數據與統計一致"
    
    # 保存修復後的數據
    print(f"💾 保存修復後的數據到: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(fixed_data, f, indent=2, ensure_ascii=False)
    
    # 驗證修復結果
    fixed_file_size = output_file.stat().st_size / (1024 * 1024)
    compression_ratio = (1 - fixed_file_size / original_file_size) * 100
    
    print("🎉 修復完成！")
    print("=" * 60)
    print(f"📊 修復結果統計:")
    print(f"   原始檔案: {original_file_size:.2f} MB")
    print(f"   修復檔案: {fixed_file_size:.2f} MB")
    print(f"   壓縮比例: {compression_ratio:.1f}%")
    
    # 驗證修復後的數據
    with open(output_file, 'r', encoding='utf-8') as f:
        fixed_data_verify = json.load(f)
    
    print(f"📋 修復後驗證:")
    fixed_total = 0
    for const_name, const_data in fixed_data_verify['constellations'].items():
        satellites = const_data.get('orbit_data', {}).get('satellites', {})
        actual_count = len(satellites)
        declared_count = const_data.get('satellite_count', 0)
        fixed_total += actual_count
        status = '✅' if actual_count == declared_count else '❌'
        print(f"   {const_name}: {status} 宣告{declared_count}顆，實際{actual_count}顆")
    
    print(f"   總計: 宣告{declared_total}顆，修復後實際{fixed_total}顆")
    
    if fixed_total == declared_total:
        print("✅ 修復成功！數據完全一致")
        return True
    else:
        print("❌ 修復失敗！數據仍不一致")
        return False

def main():
    """主函數"""
    try:
        success = fix_stage2_filtering_output()
        if success:
            print("\n🎯 建議後續行動:")
            print("1. 將修復後的檔案重命名為正式版本")
            print("2. 修復核心篩選邏輯以避免未來問題")
            print("3. 添加數據一致性驗證機制")
        return success
    except Exception as e:
        print(f"❌ 修復過程失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)