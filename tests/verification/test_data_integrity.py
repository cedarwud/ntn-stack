#!/usr/bin/env python3
"""
測試數據完整性檢查和驗證系統
"""

import sys
sys.path.append('src/services/satellite')

# 直接導入和執行測試
from data_integrity_validator import DataIntegrityValidator

def main():
    print("🔍 Phase 0 數據完整性檢查測試")
    print("=" * 50)
    
    # 使用正確的路徑初始化驗證器
    validator = DataIntegrityValidator('/home/sat/ntn-stack/tle_data')
    
    # 1. 測試單個文件驗證
    print("\n📄 測試單個文件驗證")
    print("-" * 30)
    
    starlink_file = '/home/sat/ntn-stack/tle_data/starlink/tle/starlink_20250727.tle'
    result = validator.validate_file_integrity(starlink_file)
    
    print(f"✅ 文件: starlink_20250727.tle")
    print(f"✅ 有效: {result['valid']}")
    print(f"✅ 總衛星數: {result['total_satellites']}")
    print(f"✅ 有效衛星數: {result['valid_satellites']}")
    print(f"✅ 成功率: {result['file_stats'].get('success_rate_percent', 0):.1f}%")
    print(f"✅ 文件大小: {result['file_stats'].get('size_mb', 0):.2f} MB")
    
    if result['errors']:
        print(f"❌ 錯誤數: {len(result['errors'])}")
        for error in result['errors'][:3]:
            print(f"   - {error}")
    
    if result['warnings']:
        print(f"⚠️ 警告數: {len(result['warnings'])}")
        for warning in result['warnings'][:3]:
            print(f"   - {warning}")
    
    # 2. 測試數據連續性
    print("\n📊 測試數據連續性")
    print("-" * 30)
    
    for constellation in ['starlink', 'oneweb']:
        continuity = validator.validate_data_continuity(constellation)
        print(f"\n🛰️ {constellation.upper()}:")
        print(f"  - 連續性: {'✅' if continuity['continuous'] else '❌'}")
        print(f"  - 總天數: {continuity['coverage_stats'].get('total_days', 0)}")
        print(f"  - 日期範圍: {continuity['coverage_stats'].get('start_date', 'N/A')} - {continuity['coverage_stats'].get('end_date', 'N/A')}")
        print(f"  - 覆蓋率: {continuity['coverage_stats'].get('coverage_rate_percent', 0):.1f}%")
        
        if continuity['date_gaps']:
            print(f"  - 缺失日期: {len(continuity['date_gaps'])} 天")
            
        if continuity['recommendations']:
            print(f"  - 建議: {len(continuity['recommendations'])} 項")
    
    # 3. 生成綜合報告
    print("\n📋 生成綜合報告")
    print("-" * 30)
    
    report = validator.generate_comprehensive_report()
    
    print(f"✅ 總體摘要:")
    print(f"  - 檢查星座數: {report['overall_summary']['total_constellations']}")
    print(f"  - 有效星座數: {report['overall_summary']['valid_constellations']}")
    print(f"  - 總文件數: {report['overall_summary']['total_files']}")
    print(f"  - 有效文件數: {report['overall_summary']['valid_files']}")
    print(f"  - 總衛星數: {report['overall_summary']['total_satellites']}")
    print(f"  - 有效衛星數: {report['overall_summary']['valid_satellites']}")
    
    # 導出報告
    report_file = validator.export_report_to_file(report)
    print(f"\n📄 詳細報告已保存至: {report_file}")
    
    print("\n🎉 數據完整性檢查測試完成")

if __name__ == "__main__":
    main()