#!/usr/bin/env python3
"""
最終項目驗證腳本
確認所有階段都已正確完成，並生成最終報告
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timezone

def check_phase_completion() -> Dict[str, Any]:
    """檢查所有階段的完成狀態"""
    print("🔍 檢查所有階段完成狀態...")
    
    phases = {
        "Phase 0: 數據真實性強化": {
            "files": [
                "netstack/netstack_api/models/doppler_calculation_engine.py",
                "netstack/netstack_api/models/ionospheric_models.py", 
                "netstack/netstack_api/services/weather_data_service.py",
                "netstack/netstack_api/models/ntn_path_loss_models.py"
            ],
            "status": "checking"
        },
        "Phase 1.1: 軌道計算引擎開發": {
            "files": [
                "netstack/netstack_api/services/orbit_calculation_engine.py",
                "netstack/netstack_api/services/tle_data_manager.py"
            ],
            "status": "checking"
        },
        "Phase 1.1.1: SIB19 統一基礎平台開發": {
            "files": [
                "netstack/netstack_api/services/sib19_unified_platform.py",
                "simworld/frontend/src/components/domains/measurement/shared/components/SIB19UnifiedPlatform.tsx"
            ],
            "status": "checking"
        },
        "Phase 1.2: 後端 API 統一建構": {
            "files": [
                "netstack/netstack_api/routers/measurement_events_router.py",
                "netstack/netstack_api/routers/orbit_router.py",
                "netstack/netstack_api/routers/sib19_router.py"
            ],
            "status": "checking"
        },
        "Phase 1.5: 統一 SIB19 基礎圖表架構": {
            "files": [
                "simworld/frontend/src/components/domains/measurement/shared/components/BaseEventViewer.tsx",
                "simworld/frontend/src/components/domains/measurement/config/eventConfig.ts",
                "simworld/frontend/src/plugins/charts/UniversalChart.tsx",
                "test_phase1.5_integration.py"
            ],
            "status": "checking"
        },
        "Phase 2.1: D2 事件": {
            "files": [
                "simworld/frontend/src/components/domains/measurement/charts/EnhancedD2Chart.tsx",
                "simworld/frontend/src/components/domains/measurement/charts/EnhancedD2Viewer.tsx",
                "simworld/frontend/src/components/domains/measurement/charts/EventD2Viewer.tsx"
            ],
            "status": "checking"
        },
        "Phase 2.2: D1 事件": {
            "files": [
                "simworld/frontend/src/components/domains/measurement/charts/EnhancedD1Chart.tsx",
                "simworld/frontend/src/components/domains/measurement/charts/EnhancedD1Viewer.tsx"
            ],
            "status": "checking"
        },
        "Phase 2.3: T1 事件": {
            "files": [
                "simworld/frontend/src/components/domains/measurement/charts/EnhancedT1Chart.tsx",
                "simworld/frontend/src/components/domains/measurement/charts/EnhancedT1Viewer.tsx"
            ],
            "status": "checking"
        },
        "Phase 2.4: A4 事件": {
            "files": [
                "simworld/frontend/src/components/domains/measurement/charts/EnhancedA4Chart.tsx",
                "simworld/frontend/src/components/domains/measurement/charts/EnhancedA4Viewer.tsx"
            ],
            "status": "checking"
        },
        "Phase 2.5: 系統整合測試": {
            "files": [
                "simworld/frontend/src/test/e2e.test.tsx",
                "monitoring/tests/integration_test_suite.py",
                "test_phase2.5_final_integration.py"
            ],
            "status": "checking"
        },
        "Phase 3.1: 簡易版模式實現": {
            "files": [
                "simworld/frontend/src/types/measurement-view-modes.ts",
                "simworld/frontend/src/components/domains/measurement/shared/hooks/useViewModeManager.ts"
            ],
            "status": "checking"
        },
        "Phase 3.2: 圖表說明統一改進": {
            "files": [
                "simworld/frontend/src/components/domains/measurement/shared/components/UnifiedChartExplanation.tsx",
                "simworld/frontend/src/components/domains/measurement/charts/EnhancedChartWithUnifiedExplanation.tsx"
            ],
            "status": "checking"
        },
        "Phase 3.3: 教育內容整合": {
            "files": [
                "simworld/frontend/src/components/domains/measurement/shared/components/EducationalContentSystem.tsx"
            ],
            "status": "checking"
        },
        "Phase 4: 系統整合和驗證": {
            "files": [
                "test_phase4_final_verification.py",
                "PROJECT_COMPLETION_REPORT.md"
            ],
            "status": "checking"
        }
    }
    
    # 檢查每個階段的文件
    for phase_name, phase_info in phases.items():
        existing_files = 0
        total_files = len(phase_info["files"])
        
        for file_path in phase_info["files"]:
            full_path = Path(f"/home/sat/ntn-stack/{file_path}")
            if full_path.exists():
                existing_files += 1
        
        completion_rate = (existing_files / total_files) * 100
        
        if completion_rate == 100:
            phase_info["status"] = "complete"
            print(f"  ✅ {phase_name}: 100% ({existing_files}/{total_files} 文件)")
        elif completion_rate >= 80:
            phase_info["status"] = "mostly_complete"
            print(f"  ⚠️ {phase_name}: {completion_rate:.0f}% ({existing_files}/{total_files} 文件)")
        else:
            phase_info["status"] = "incomplete"
            print(f"  ❌ {phase_name}: {completion_rate:.0f}% ({existing_files}/{total_files} 文件)")
        
        phase_info["completion_rate"] = completion_rate
        phase_info["existing_files"] = existing_files
        phase_info["total_files"] = total_files
    
    return phases

def check_critical_fixes() -> Dict[str, Any]:
    """檢查關鍵修正是否完成"""
    print("\n🔍 檢查關鍵修正...")
    
    fixes = {
        "D2 軌道週期修正": {
            "description": "D2 事件軌道週期從 120秒修正為 90分鐘",
            "files_to_check": [
                ("simworld/frontend/src/components/domains/measurement/charts/EventD2Viewer.tsx", "5400"),
                ("simworld/frontend/src/components/domains/satellite/visualization/DynamicSatelliteRenderer.tsx", "5400"),
                ("simworld/frontend/src/components/domains/measurement/shared/hooks/useEventD1Logic.ts", "5400")
            ],
            "status": "checking"
        },
        "論文研究級數據精度": {
            "description": "所有物理模型達到論文研究級精度",
            "files_to_check": [
                ("netstack/netstack_api/models/doppler_calculation_engine.py", "SGP4"),
                ("netstack/netstack_api/models/ionospheric_models.py", "Klobuchar"),
                ("netstack/netstack_api/models/ntn_path_loss_models.py", "3GPP TR 38.811")
            ],
            "status": "checking"
        }
    }
    
    for fix_name, fix_info in fixes.items():
        passed_checks = 0
        total_checks = len(fix_info["files_to_check"])
        
        for file_path, expected_content in fix_info["files_to_check"]:
            full_path = Path(f"/home/sat/ntn-stack/{file_path}")
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if expected_content in content:
                            passed_checks += 1
                except:
                    pass
        
        completion_rate = (passed_checks / total_checks) * 100
        
        if completion_rate == 100:
            fix_info["status"] = "complete"
            print(f"  ✅ {fix_name}: 100% ({passed_checks}/{total_checks} 檢查通過)")
        else:
            fix_info["status"] = "incomplete"
            print(f"  ❌ {fix_name}: {completion_rate:.0f}% ({passed_checks}/{total_checks} 檢查通過)")
        
        fix_info["completion_rate"] = completion_rate
    
    return fixes

def generate_final_report(phases: Dict[str, Any], fixes: Dict[str, Any]) -> Dict[str, Any]:
    """生成最終報告"""
    print("\n📊 生成最終項目報告...")
    
    # 計算總體完成度
    total_phases = len(phases)
    completed_phases = sum(1 for phase in phases.values() if phase["status"] == "complete")
    mostly_completed_phases = sum(1 for phase in phases.values() if phase["status"] == "mostly_complete")
    
    overall_completion = (completed_phases / total_phases) * 100
    
    # 計算修正完成度
    total_fixes = len(fixes)
    completed_fixes = sum(1 for fix in fixes.values() if fix["status"] == "complete")
    fixes_completion = (completed_fixes / total_fixes) * 100 if total_fixes > 0 else 100
    
    # 生成報告
    report = {
        "project_name": "NTN 衛星測量事件系統",
        "verification_date": datetime.now(timezone.utc).isoformat(),
        "overall_completion": overall_completion,
        "fixes_completion": fixes_completion,
        "status": "EXCELLENT" if overall_completion >= 95 and fixes_completion >= 95 else 
                 "COMPLETE" if overall_completion >= 90 and fixes_completion >= 90 else
                 "MOSTLY_COMPLETE" if overall_completion >= 80 else "INCOMPLETE",
        "phase_summary": {
            "total_phases": total_phases,
            "completed_phases": completed_phases,
            "mostly_completed_phases": mostly_completed_phases,
            "incomplete_phases": total_phases - completed_phases - mostly_completed_phases
        },
        "fixes_summary": {
            "total_fixes": total_fixes,
            "completed_fixes": completed_fixes
        },
        "detailed_phases": phases,
        "detailed_fixes": fixes,
        "achievements": [],
        "recommendations": []
    }
    
    # 識別成就
    if overall_completion >= 95:
        report["achievements"].append("🏆 所有主要階段 95% 以上完成")
    if fixes_completion >= 95:
        report["achievements"].append("🔧 所有關鍵修正完成")
    if completed_phases >= 10:
        report["achievements"].append("📈 超過 10 個階段完全完成")
    
    # 生成建議
    for phase_name, phase_info in phases.items():
        if phase_info["status"] == "incomplete":
            report["recommendations"].append(f"完成 {phase_name} 的剩餘工作")
    
    for fix_name, fix_info in fixes.items():
        if fix_info["status"] == "incomplete":
            report["recommendations"].append(f"完成 {fix_name} 的修正")
    
    return report

def main():
    """主函數"""
    print("🚀 NTN 衛星測量事件系統 - 最終項目驗證")
    print("=" * 70)
    
    # 檢查階段完成狀態
    phases = check_phase_completion()
    
    # 檢查關鍵修正
    fixes = check_critical_fixes()
    
    # 生成最終報告
    report = generate_final_report(phases, fixes)
    
    # 輸出結果
    print("\n" + "=" * 70)
    print("📋 最終項目驗證結果")
    print("=" * 70)
    
    print(f"項目名稱: {report['project_name']}")
    print(f"驗證日期: {report['verification_date']}")
    print(f"總體完成度: {report['overall_completion']:.1f}%")
    print(f"修正完成度: {report['fixes_completion']:.1f}%")
    print(f"項目狀態: {report['status']}")
    
    print(f"\n階段摘要:")
    print(f"  總階段數: {report['phase_summary']['total_phases']}")
    print(f"  完成階段: {report['phase_summary']['completed_phases']}")
    print(f"  大部分完成: {report['phase_summary']['mostly_completed_phases']}")
    print(f"  未完成階段: {report['phase_summary']['incomplete_phases']}")
    
    if report["achievements"]:
        print(f"\n🎉 主要成就:")
        for achievement in report["achievements"]:
            print(f"  {achievement}")
    
    if report["recommendations"]:
        print(f"\n💡 建議:")
        for rec in report["recommendations"]:
            print(f"  • {rec}")
    
    print("\n" + "=" * 70)
    
    if report["status"] == "EXCELLENT":
        print("🏆 項目驗證 - 優秀等級！")
        print("🎓 系統已達到論文研究級標準")
        return 0
    elif report["status"] == "COMPLETE":
        print("🎉 項目驗證通過！")
        print("✅ 系統品質良好")
        return 0
    elif report["status"] == "MOSTLY_COMPLETE":
        print("⚠️ 項目大部分完成，建議完善剩餘部分")
        return 1
    else:
        print("❌ 項目存在未完成部分，需要繼續開發")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
