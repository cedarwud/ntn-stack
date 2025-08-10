#!/usr/bin/env python3
"""
驗證更新後的文檔內容準確性
確認所有數量和描述都與實際系統一致
"""

import re
import sys
from pathlib import Path

def validate_satellite_numbers():
    """驗證文檔中的衛星數量是否正確"""
    print("🔍 驗證文檔中的衛星數量")
    print("=" * 50)
    
    doc_path = Path("/home/sat/ntn-stack/docs/satellite_data_preprocessing.md")
    
    if not doc_path.exists():
        print(f"❌ 文檔不存在: {doc_path}")
        return False
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 預期的正確數量
    expected_values = {
        'starlink': 8064,
        'oneweb': 651, 
        'total': 8715
    }
    
    validation_results = {}
    
    # 檢查 Starlink 數量
    starlink_matches = re.findall(r'Starlink:?\s*(\d{1,3}(?:,\d{3})*)\s*顆', content)
    print(f"📡 Starlink 數量檢查:")
    for match in starlink_matches:
        number = int(match.replace(',', ''))
        status = "✅" if number == expected_values['starlink'] else "❌"
        print(f"   {status} 找到: {match} 顆 (期望: {expected_values['starlink']:,})")
        validation_results['starlink'] = number == expected_values['starlink']
    
    # 檢查 OneWeb 數量
    oneweb_matches = re.findall(r'OneWeb:?\s*(\d{1,3}(?:,\d{3})*)\s*顆', content)
    print(f"📡 OneWeb 數量檢查:")
    for match in oneweb_matches:
        number = int(match.replace(',', ''))
        status = "✅" if number == expected_values['oneweb'] else "❌"
        print(f"   {status} 找到: {match} 顆 (期望: {expected_values['oneweb']:,})")
        validation_results['oneweb'] = number == expected_values['oneweb']
    
    # 檢查總數
    total_patterns = [
        r'總計:?\s*(\d{1,5}(?:,\d{3})*)\s*顆',
        r'"satellites_processed":\s*(\d{1,5}(?:,\d{3})*)',
        r'基於(\d{1,5}(?:,\d{3})*)\s*顆衛星'
    ]
    
    print(f"📊 總數檢查:")
    total_valid = True
    for pattern in total_patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            number = int(match.replace(',', ''))
            status = "✅" if number == expected_values['total'] else "❌"
            print(f"   {status} 找到: {match} (期望: {expected_values['total']:,})")
            if number != expected_values['total']:
                total_valid = False
    
    validation_results['total'] = total_valid
    
    return all(validation_results.values())

def validate_stage1_description():
    """驗證第1階段的描述是否準確"""
    print("\n🎯 驗證第1階段描述準確性")
    print("=" * 50)
    
    doc_path = Path("/home/sat/ntn-stack/docs/satellite_data_preprocessing.md")
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查關鍵描述是否存在
    key_descriptions = [
        "解析全部 TLE 資訊",
        "判斷哪些衛星有可能通過 UE 上方", 
        "軌道不可預測性",
        "無篩選全量載入",
        "確保不遺漏任何潛在候選衛星",
        "沒有任何篩選邏輯"
    ]
    
    validation_results = {}
    
    for desc in key_descriptions:
        found = desc in content
        status = "✅" if found else "❌"
        print(f"   {status} {desc}")
        validation_results[desc] = found
    
    return all(validation_results.values())

def validate_consistency():
    """檢查文檔內部一致性"""
    print("\n🔄 檢查文檔內部一致性")
    print("=" * 50)
    
    doc_path = Path("/home/sat/ntn-stack/docs/satellite_data_preprocessing.md")
    
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否還有舊的數量
    old_numbers = ['8,042', '8042', '8,693', '8693', '8,695', '8695', '8,173', '8173']
    
    issues_found = []
    
    for old_num in old_numbers:
        if old_num in content:
            # 檢查上下文，看是否是在歷史或對比部分
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if old_num in line:
                    context = f"第{i+1}行: {line.strip()}"
                    # 如果不是在歷史部分，則是問題
                    if not any(keyword in line.lower() for keyword in ['歷程', '對比', '演進', '版本', 'v1.0', 'v2.0', 'fallback', '文檔', '預期']):
                        issues_found.append(f"❌ 發現舊數量 {old_num}: {context}")
    
    if issues_found:
        print("發現一致性問題:")
        for issue in issues_found:
            print(f"   {issue}")
        return False
    else:
        print("✅ 文檔內部一致性良好")
        return True

def main():
    """主驗證函數"""
    print("📋 文檔更新後驗證報告")
    print("=" * 80)
    print("目的: 確認所有數量和描述都與實際系統一致")
    print("=" * 80)
    
    # 執行所有驗證
    validation_results = {
        'numbers': validate_satellite_numbers(),
        'stage1_desc': validate_stage1_description(), 
        'consistency': validate_consistency()
    }
    
    print("\n" + "=" * 80)
    print("🎯 最終驗證結果")
    print("=" * 80)
    
    all_passed = True
    
    for category, passed in validation_results.items():
        status = "✅ 通過" if passed else "❌ 失敗"
        category_name = {
            'numbers': '衛星數量準確性',
            'stage1_desc': '第1階段描述完整性',
            'consistency': '文檔內部一致性'
        }[category]
        
        print(f"{status} {category_name}")
        
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 文檔驗證完全通過！")
        print("   所有數量和描述都與實際系統一致")
        print("   第1階段的真實目的已明確表達")
        return True
    else:
        print("⚠️ 文檔驗證發現問題")
        print("   請檢查上述失敗項目並進行修正")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)