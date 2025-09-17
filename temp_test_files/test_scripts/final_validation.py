#!/usr/bin/env python3
"""
最終驗證腳本
"""
import sys
import os
sys.path.append("/home/sat/ntn-stack/satellite-processing-system/src")

from shared.academic_compliance_validator import AcademicComplianceValidator

def main():
    """執行最終驗證"""
    print("🎯 執行最終學術合規驗證...")

    # 在容器內執行驗證
    validator = AcademicComplianceValidator()
    results = validator.validate_all_stages("/home/sat/ntn-stack/satellite-processing-system/src/stages")

    critical_count = results["compliance_summary"].get("total_critical_issues", 0)
    high_count = results["compliance_summary"].get("total_high_issues", 0)
    overall_grade = results["compliance_summary"]["overall_compliance"]

    print(f"📊 最終驗證結果:")
    print(f"   Critical問題數: {critical_count}")
    print(f"   High問題數: {high_count}")
    print(f"   整體合規等級: {overall_grade}")
    print()

    if critical_count == 0:
        print("🎉 SUCCESS: 所有Critical hardcoded問題已歸零!")
        if high_count == 0:
            print("🎉 PERFECT: 所有High問題也已解決!")
            if overall_grade == "A" or overall_grade == "B":
                print(f"🏆 EXCELLENT: 達到 Grade {overall_grade} 學術合規標準!")
            else:
                print(f"⚠️  整體等級仍為 {overall_grade}，但無Critical問題")
        else:
            print(f"⚠️  仍有 {high_count} 個High問題需要優化")
    else:
        print(f"❌ 仍有 {critical_count} 個Critical問題需要處理")

        # 顯示前5個Critical問題
        print("\n🔍 前5個Critical問題:")
        critical_violations = [
            v for stage_result in results["stage_results"].values()
            for v in stage_result["violations"]
            if v["severity"] == "Critical"
        ][:5]

        for i, violation in enumerate(critical_violations, 1):
            print(f"   {i}. {violation['file']}:{violation['line']} - {violation['context']}")

if __name__ == "__main__":
    main()