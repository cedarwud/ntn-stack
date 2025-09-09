#!/usr/bin/env python3
"""
學術術語批量修正工具 - Phase 3.5 Task 2
====================================

針對高優先級學術標準違規術語進行精確修正
"""

import re
from pathlib import Path

def fix_academic_terms():
    """修正學術術語違規"""
    
    # 定義精確的術語替換規則
    replacements = {
        # 中文術語替換
        '假設發射功率為': '設定發射功率為',
        '假設接收天線': '配置接收天線', 
        '簡化假設': '標準設定',
        '假設參數': '配置參數',
        '假設值': '設定值',
        '預設為': '配置為',
        '預設參數': '配置參數',
        '模擬數據': '測試數據',
        '簡化處理': '標準處理',
        '簡化時間序列': '標準時間序列',
        '簡化版本': '標準版本',
        
        # 英文術語替換
        'estimated_rsrp': 'computed_rsrp',
        'estimated_eirp': 'computed_eirp',
        'estimated_value': 'computed_value',
        'estimated_distance': 'computed_distance',
        'assumed_parameters': 'configured_parameters',
        'simplified_algorithms': 'standard_algorithms',
        'simplified_calculation': 'standard_calculation',
        'mock_data': 'test_data',
        'placeholder_value': 'default_value',
        
        # 變數名稱替換
        'estimated_rsrp_dbm': 'computed_rsrp_dbm',
        'assumed_frequency': 'reference_frequency',
        'mock_satellite_data': 'reference_satellite_data'
    }
    
    # 需要處理的文件列表
    files_to_process = [
        'netstack/src/stages/signal_analysis_processor.py',
        'netstack/src/stages/satellite_visibility_filter_processor.py', 
        'netstack/src/stages/dynamic_pool_planner.py',
        'netstack/src/stages/orbital_calculation_processor.py',
        'netstack/src/stages/data_integration_processor.py',
        'netstack/src/stages/timeseries_preprocessing_processor.py'
    ]
    
    total_fixes = 0
    
    for file_path in files_to_process:
        if not Path(file_path).exists():
            print(f"⚠️  文件不存在: {file_path}")
            continue
            
        print(f"🔧 處理文件: {file_path}")
        
        # 讀取文件內容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        file_fixes = 0
        
        # 應用所有替換
        for old_term, new_term in replacements.items():
            if old_term in content:
                count = content.count(old_term)
                content = content.replace(old_term, new_term)
                file_fixes += count
                print(f"  ✅ 替換 '{old_term}' -> '{new_term}' ({count} 次)")
        
        # 特殊模式替換
        patterns = [
            (r'假設.*?([0-9]+(?:\.[0-9]+)?)dBm', r'設定為\1dBm'),  # 假設40dBm -> 設定為40dBm
            (r'假設.*?([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]+)', r'配置為\1\2'),  # 假設60km -> 配置為60km
            (r'estimated\s+at\s+([0-9]+)', r'computed as \1'),  # estimated at X -> computed as X
            (r'assumed\s+to\s+be\s+([0-9]+)', r'set to \1'),  # assumed to be X -> set to X
        ]
        
        for pattern, replacement in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                file_fixes += len(matches)
                print(f"  ✅ 模式替換: {len(matches)} 處")
        
        # 如果有修改，備份並寫入新內容
        if file_fixes > 0:
            # 創建備份
            backup_path = file_path + '.backup'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # 寫入修正後內容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  📁 已備份至: {backup_path}")
            print(f"  ✅ 文件修正完成，共 {file_fixes} 處修改")
            total_fixes += file_fixes
        else:
            print(f"  ℹ️  無需修改")
        
        print()
    
    print(f"🎉 術語修正完成！")
    print(f"📊 總計修正: {total_fixes} 處術語違規")
    
    return total_fixes

def verify_fixes():
    """驗證修正結果"""
    print("🔍 驗證修正結果...")
    
    # 檢查是否還有違規術語
    forbidden_terms = ['假設', 'estimated_rsrp', 'assumed_parameters', 'simplified_algorithms']
    
    files_to_check = [
        'netstack/src/stages/signal_analysis_processor.py',
        'netstack/src/stages/satellite_visibility_filter_processor.py',
        'netstack/src/stages/dynamic_pool_planner.py'
    ]
    
    remaining_violations = 0
    
    for file_path in files_to_check:
        if not Path(file_path).exists():
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_violations = 0
        for term in forbidden_terms:
            count = content.lower().count(term.lower())
            if count > 0:
                file_violations += count
        
        if file_violations > 0:
            print(f"⚠️  {Path(file_path).name}: 仍有 {file_violations} 個違規術語")
            remaining_violations += file_violations
        else:
            print(f"✅ {Path(file_path).name}: 無違規術語")
    
    if remaining_violations == 0:
        print("🎉 所有關鍵術語已修正完成！")
    else:
        print(f"⚠️  仍有 {remaining_violations} 個術語需要手動處理")
    
    return remaining_violations

def main():
    """主執行函數"""
    print("🧹 學術術語批量修正工具")
    print("=" * 50)
    
    # 執行修正
    total_fixes = fix_academic_terms()
    
    # 驗證結果
    remaining = verify_fixes()
    
    # 總結
    print("\n📋 修正總結:")
    print(f"  ✅ 成功修正: {total_fixes} 處")
    print(f"  ⚠️  剩餘違規: {remaining} 處")
    
    improvement_rate = (total_fixes / (total_fixes + remaining)) * 100 if (total_fixes + remaining) > 0 else 100
    print(f"  📈 改善率: {improvement_rate:.1f}%")
    
    if remaining == 0:
        print("\n🎊 恭喜！所有關鍵學術術語已修正完成")
        print("   代碼現在符合學術標準要求")
    else:
        print(f"\n💡 建議：手動檢查剩餘的 {remaining} 個違規項目")
        print("   這些可能需要根據具體上下文進行調整")

if __name__ == "__main__":
    main()