#!/usr/bin/env python3
"""
衛星處理系統學術標準檢查工具
🎓 Grade A 學術標準合規性檢查

功能：
- 深度掃描所有六個階段的代碼
- 檢測Mock數據、簡化算法、時間基準違反
- 生成詳細的合規性報告
- 提供修復建議

使用方法：
python scripts/academic_standards_checker.py [--stage N] [--report-file output.json]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加src目錄到Python路徑
sys.path.append(str(Path(__file__).parent.parent / "src"))

from shared.academic_compliance_validator import AcademicComplianceValidator


def run_academic_standards_check(stage: int = None, report_file: str = None) -> Dict[str, Any]:
    """
    運行學術標準檢查

    Args:
        stage: 特定階段編號（1-6），None表示檢查所有階段
        report_file: 報告輸出文件路徑

    Returns:
        檢查結果字典
    """
    print("🎓 開始學術標準合規性檢查...")
    print("=" * 60)

    # 初始化檢查器
    validator = AcademicComplianceValidator()

    # 設定檢查範圍
    stages_dir = Path(__file__).parent.parent / "src" / "stages"

    if stage:
        print(f"🔍 檢查 Stage {stage}...")
        stage_dirs = list(stages_dir.glob(f"stage{stage}_*"))
        if not stage_dirs:
            print(f"❌ 未找到 Stage {stage} 目錄")
            return {}

        # 檢查特定階段
        stage_path = stage_dirs[0]
        result = validator._validate_stage(stage_path, stage)
        validator.validation_results["stage_results"][f"stage_{stage}"] = result
    else:
        print("🔍 檢查所有六個階段...")
        # 檢查所有階段
        validator.validate_all_stages(str(stages_dir))

    # 計算總體合規性
    validator._calculate_overall_compliance()

    # 生成詳細報告
    results = validator.validation_results

    print("\n📊 檢查結果摘要:")
    print("-" * 40)
    print(f"📁 掃描文件數: {results['total_files_scanned']}")
    print(f"⚠️  總違反數: {results['total_violations']}")
    print(f"🎯 整體等級: {results['overall_grade']}")
    print(f"📈 合規分數: {results['overall_compliance_score']:.1f}/100")

    # 顯示關鍵問題
    critical_issues = [v for v in results['violation_details'] if v.get('severity') == 'CRITICAL']
    if critical_issues:
        print(f"\n🚨 關鍵問題 ({len(critical_issues)} 個):")
        for issue in critical_issues[:5]:  # 只顯示前5個
            print(f"   ❌ {issue['file']}:{issue['line']} - {issue['context']}")
        if len(critical_issues) > 5:
            print(f"   ... 還有 {len(critical_issues) - 5} 個關鍵問題")

    # 保存報告
    if report_file:
        save_report(results, report_file)
        print(f"\n📄 詳細報告已保存至: {report_file}")

    # 給出建議
    provide_recommendations(results)

    return results


def save_report(results: Dict[str, Any], report_file: str) -> None:
    """保存詳細報告到文件"""
    report_path = Path(report_file)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # 添加時間戳和元數據
    report_data = {
        "metadata": {
            "check_timestamp": datetime.now().isoformat(),
            "tool_version": "1.0.0",
            "check_scope": "all_stages",
            "academic_standard": "Grade A"
        },
        "results": results
    }

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)


def provide_recommendations(results: Dict[str, Any]) -> None:
    """提供修復建議"""
    print("\n💡 修復建議:")
    print("-" * 40)

    # 統計違反類型
    violation_types = {}
    for violation in results['violation_details']:
        vtype = violation.get('type', 'unknown')
        violation_types[vtype] = violation_types.get(vtype, 0) + 1

    # 按嚴重程度排序建議
    if 'time_reference_violation' in violation_types:
        print("🕐 時間基準問題:")
        print("   1. 將所有 datetime.now() 改為使用 TLE epoch 時間")
        print("   2. 在軌道計算中嚴格使用 calculation_base_time = tle_epoch")
        print("   3. 數據品質評估基於內在特性，不依賴當前時間")

    if 'mock_data_violation' in violation_types:
        print("📊 Mock數據問題:")
        print("   1. 移除所有 MockPrediction、MockRepository 類")
        print("   2. 使用真實 SGP4 計算代替模擬數據")
        print("   3. 連接真實數據源（Space-Track、ITU-R）")

    if 'simplified_algorithm_violation' in violation_types:
        print("🔬 算法簡化問題:")
        print("   1. 實現完整的 SGP4/SDP4 軌道傳播")
        print("   2. 使用完整的 ITU-R P.618 大氣衰減模型")
        print("   3. 遵循 3GPP TS 38.821 NTN 標準")

    if 'hardcoded_parameter_violation' in violation_types:
        print("⚙️ 硬編碼參數問題:")
        print("   1. 將硬編碼值移至配置文件")
        print("   2. 從官方標準文檔載入參數")
        print("   3. 添加參數來源文檔引用")

    # 整體建議
    overall_grade = results.get('overall_grade', 'F')
    if overall_grade in ['F', 'C']:
        print("\n🚨 緊急行動要求:")
        print("   系統目前不符合學術標準，需要立即修復所有關鍵問題")
    elif overall_grade in ['B', 'B+']:
        print("\n⚠️ 改進建議:")
        print("   系統基本符合學術標準，建議修復剩餘問題以達到 Grade A")
    else:
        print("\n✅ 優秀!")
        print("   系統符合 Grade A 學術標準要求")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="衛星處理系統學術標準檢查工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/academic_standards_checker.py                    # 檢查所有階段
  python scripts/academic_standards_checker.py --stage 1          # 只檢查Stage 1
  python scripts/academic_standards_checker.py --report-file report.json  # 保存詳細報告
        """
    )

    parser.add_argument('--stage', type=int, choices=range(1, 7),
                        help='檢查特定階段 (1-6)')
    parser.add_argument('--report-file', type=str,
                        help='保存詳細報告的文件路徑')

    args = parser.parse_args()

    try:
        results = run_academic_standards_check(
            stage=args.stage,
            report_file=args.report_file
        )

        # 根據結果決定退出碼
        overall_grade = results.get('overall_grade', 'F')
        if overall_grade in ['F', 'C']:
            sys.exit(1)  # 不符合標準
        else:
            sys.exit(0)  # 符合標準

    except Exception as e:
        print(f"❌ 檢查過程發生錯誤: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()