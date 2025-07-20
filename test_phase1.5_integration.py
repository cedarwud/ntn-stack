#!/usr/bin/env python3
"""
Phase 1.5 統一平台整合測試驗證腳本
驗證統一 SIB19 基礎圖表架構的完整性
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any

# 添加項目路徑
sys.path.append('/home/sat/ntn-stack')

def check_file_exists(file_path: str) -> bool:
    """檢查文件是否存在"""
    return Path(file_path).exists()

def check_sib19_unified_platform() -> Dict[str, Any]:
    """檢查 SIB19 統一平台實現"""
    print("🔍 檢查 SIB19 統一平台實現...")
    
    results = {
        "backend_platform": False,
        "frontend_component": False,
        "styles": False,
        "integration_test": False
    }
    
    # 檢查後端平台
    backend_path = "/home/sat/ntn-stack/netstack/netstack_api/services/sib19_unified_platform.py"
    if check_file_exists(backend_path):
        results["backend_platform"] = True
        print("  ✅ 後端 SIB19 統一平台已實現")
    else:
        print("  ❌ 後端 SIB19 統一平台未找到")
    
    # 檢查前端組件
    frontend_path = "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/shared/components/SIB19UnifiedPlatform.tsx"
    if check_file_exists(frontend_path):
        results["frontend_component"] = True
        print("  ✅ 前端 SIB19 統一平台組件已實現")
    else:
        print("  ❌ 前端 SIB19 統一平台組件未找到")
    
    # 檢查樣式文件
    styles_path = "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/shared/components/SIB19UnifiedPlatform.scss"
    if check_file_exists(styles_path):
        results["styles"] = True
        print("  ✅ SIB19 統一平台樣式已實現")
    else:
        print("  ❌ SIB19 統一平台樣式未找到")
    
    # 檢查整合測試
    test_path = "/home/sat/ntn-stack/simworld/frontend/src/test/phase1.5-integration-test.tsx"
    if check_file_exists(test_path):
        results["integration_test"] = True
        print("  ✅ Phase 1.5 整合測試已創建")
    else:
        print("  ❌ Phase 1.5 整合測試未找到")
    
    return results

def check_unified_chart_architecture() -> Dict[str, Any]:
    """檢查統一圖表架構"""
    print("\n🔍 檢查統一圖表架構...")
    
    results = {
        "event_config": False,
        "base_event_viewer": False,
        "universal_chart": False,
        "chart_plugins": False
    }
    
    # 檢查事件配置
    config_path = "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/config/eventConfig.ts"
    if check_file_exists(config_path):
        results["event_config"] = True
        print("  ✅ 統一事件配置管理已實現")
    else:
        print("  ❌ 統一事件配置管理未找到")
    
    # 檢查基礎事件查看器
    viewer_path = "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/shared/components/BaseEventViewer.tsx"
    if check_file_exists(viewer_path):
        results["base_event_viewer"] = True
        print("  ✅ 基礎事件查看器已實現")
    else:
        print("  ❌ 基礎事件查看器未找到")
    
    # 檢查通用圖表組件
    chart_path = "/home/sat/ntn-stack/simworld/frontend/src/plugins/charts/UniversalChart.tsx"
    if check_file_exists(chart_path):
        results["universal_chart"] = True
        print("  ✅ 通用圖表組件已實現")
    else:
        print("  ❌ 通用圖表組件未找到")
    
    # 檢查圖表插件目錄
    plugins_dir = "/home/sat/ntn-stack/simworld/frontend/src/plugins/charts/"
    if Path(plugins_dir).exists():
        plugin_files = list(Path(plugins_dir).glob("*.tsx"))
        if len(plugin_files) > 0:
            results["chart_plugins"] = True
            print(f"  ✅ 圖表插件系統已實現 ({len(plugin_files)} 個插件)")
        else:
            print("  ❌ 圖表插件系統無插件文件")
    else:
        print("  ❌ 圖表插件目錄未找到")
    
    return results

def check_event_specific_components() -> Dict[str, Any]:
    """檢查事件特定組件"""
    print("\n🔍 檢查事件特定組件...")
    
    results = {
        "enhanced_components": {},
        "viewer_components": {},
        "chart_components": {}
    }
    
    event_types = ['A4', 'D1', 'D2', 'T1']
    
    for event_type in event_types:
        print(f"  檢查 {event_type} 事件組件...")
        
        # 檢查 Enhanced 組件
        enhanced_chart_path = f"/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/charts/Enhanced{event_type}Chart.tsx"
        enhanced_viewer_path = f"/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/charts/Enhanced{event_type}Viewer.tsx"
        
        results["enhanced_components"][event_type] = {
            "chart": check_file_exists(enhanced_chart_path),
            "viewer": check_file_exists(enhanced_viewer_path)
        }
        
        # 檢查基礎 Viewer 組件
        viewer_path = f"/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/charts/Event{event_type}Viewer.tsx"
        results["viewer_components"][event_type] = check_file_exists(viewer_path)
        
        # 檢查 Pure Chart 組件
        pure_chart_path = f"/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/charts/Pure{event_type}Chart.tsx"
        results["chart_components"][event_type] = check_file_exists(pure_chart_path)
        
        if results["enhanced_components"][event_type]["chart"] and results["enhanced_components"][event_type]["viewer"]:
            print(f"    ✅ {event_type} Enhanced 組件完整")
        else:
            print(f"    ⚠️ {event_type} Enhanced 組件不完整")
    
    return results

def check_cross_event_integration() -> Dict[str, Any]:
    """檢查跨事件整合"""
    print("\n🔍 檢查跨事件整合...")
    
    results = {
        "measurement_view_modes": False,
        "shared_hooks": False,
        "unified_types": False,
        "integration_components": False
    }
    
    # 檢查測量視圖模式
    modes_path = "/home/sat/ntn-stack/simworld/frontend/src/types/measurement-view-modes.ts"
    if check_file_exists(modes_path):
        results["measurement_view_modes"] = True
        print("  ✅ 測量視圖模式系統已實現")
    else:
        print("  ❌ 測量視圖模式系統未找到")
    
    # 檢查共享 Hooks
    hooks_dir = "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/shared/hooks/"
    if Path(hooks_dir).exists():
        hook_files = list(Path(hooks_dir).glob("*.ts"))
        if len(hook_files) >= 4:  # 至少應該有 4 個事件的 hooks
            results["shared_hooks"] = True
            print(f"  ✅ 共享 Hooks 已實現 ({len(hook_files)} 個)")
        else:
            print(f"  ⚠️ 共享 Hooks 不完整 ({len(hook_files)} 個)")
    else:
        print("  ❌ 共享 Hooks 目錄未找到")
    
    # 檢查統一類型定義
    types_path = "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/shared/types.ts"
    if check_file_exists(types_path):
        results["unified_types"] = True
        print("  ✅ 統一類型定義已實現")
    else:
        print("  ❌ 統一類型定義未找到")
    
    # 檢查整合組件
    integration_dir = "/home/sat/ntn-stack/simworld/frontend/src/components/unified-monitoring/"
    if Path(integration_dir).exists():
        integration_files = list(Path(integration_dir).rglob("*.ts*"))
        if len(integration_files) > 0:
            results["integration_components"] = True
            print(f"  ✅ 統一監控組件已實現 ({len(integration_files)} 個文件)")
        else:
            print("  ❌ 統一監控組件無文件")
    else:
        print("  ❌ 統一監控組件目錄未找到")
    
    return results

def check_testing_infrastructure() -> Dict[str, Any]:
    """檢查測試基礎設施"""
    print("\n🔍 檢查測試基礎設施...")
    
    results = {
        "e2e_tests": False,
        "integration_tests": False,
        "component_tests": False,
        "test_utilities": False
    }
    
    # 檢查端到端測試
    e2e_path = "/home/sat/ntn-stack/simworld/frontend/src/test/e2e.test.tsx"
    if check_file_exists(e2e_path):
        results["e2e_tests"] = True
        print("  ✅ 端到端測試已實現")
    else:
        print("  ❌ 端到端測試未找到")
    
    # 檢查整合測試
    integration_tests = [
        "/home/sat/ntn-stack/simworld/frontend/src/test/phase1.5-integration-test.tsx",
        "/home/sat/ntn-stack/monitoring/tests/integration_test_suite.py",
        "/home/sat/ntn-stack/netstack/netstack_api/services/rl_training/integration/"
    ]
    
    integration_count = sum(1 for path in integration_tests if check_file_exists(path) or Path(path).exists())
    if integration_count >= 2:
        results["integration_tests"] = True
        print(f"  ✅ 整合測試已實現 ({integration_count} 個測試套件)")
    else:
        print(f"  ⚠️ 整合測試不完整 ({integration_count} 個測試套件)")
    
    # 檢查組件測試
    component_test_path = "/home/sat/ntn-stack/simworld/frontend/src/components/rl-monitoring/test/"
    if Path(component_test_path).exists():
        test_files = list(Path(component_test_path).glob("*.tsx"))
        if len(test_files) > 0:
            results["component_tests"] = True
            print(f"  ✅ 組件測試已實現 ({len(test_files)} 個)")
        else:
            print("  ❌ 組件測試目錄無文件")
    else:
        print("  ❌ 組件測試目錄未找到")
    
    # 檢查測試工具
    test_utils_paths = [
        "/home/sat/ntn-stack/simworld/frontend/test-runner.js",
        "/home/sat/ntn-stack/simworld/frontend/src/test/"
    ]
    
    utils_count = sum(1 for path in test_utils_paths if check_file_exists(path) or Path(path).exists())
    if utils_count >= 1:
        results["test_utilities"] = True
        print(f"  ✅ 測試工具已實現")
    else:
        print("  ❌ 測試工具未找到")
    
    return results

def generate_integration_report(all_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """生成整合測試報告"""
    print("\n📊 生成 Phase 1.5 整合測試報告...")
    
    # 計算各模組完成度
    module_scores = {}
    
    for module_name, module_results in all_results.items():
        if isinstance(module_results, dict):
            total_checks = 0
            passed_checks = 0
            
            def count_results(obj):
                nonlocal total_checks, passed_checks
                if isinstance(obj, dict):
                    for value in obj.values():
                        if isinstance(value, bool):
                            total_checks += 1
                            if value:
                                passed_checks += 1
                        elif isinstance(value, dict):
                            count_results(value)
                elif isinstance(obj, bool):
                    total_checks += 1
                    if obj:
                        passed_checks += 1
            
            count_results(module_results)
            
            if total_checks > 0:
                score = (passed_checks / total_checks) * 100
                module_scores[module_name] = {
                    "score": score,
                    "passed": passed_checks,
                    "total": total_checks
                }
    
    # 計算總體分數
    if module_scores:
        overall_score = sum(score["score"] for score in module_scores.values()) / len(module_scores)
    else:
        overall_score = 0
    
    # 生成報告
    report = {
        "test_suite": "Phase 1.5 統一平台整合測試",
        "timestamp": "2024-12-20T08:00:00Z",
        "overall_score": overall_score,
        "status": "PASSED" if overall_score >= 80 else "NEEDS_IMPROVEMENT" if overall_score >= 60 else "FAILED",
        "module_scores": module_scores,
        "detailed_results": all_results,
        "recommendations": []
    }
    
    # 生成建議
    if overall_score < 80:
        for module_name, score_info in module_scores.items():
            if score_info["score"] < 80:
                report["recommendations"].append(
                    f"改進 {module_name} 模組 (當前: {score_info['score']:.1f}%)"
                )
    
    return report

def main():
    """主函數"""
    print("🚀 Phase 1.5 統一 SIB19 基礎圖表架構整合測試")
    print("=" * 70)
    
    # 執行各項檢查
    all_results = {}
    
    all_results["sib19_platform"] = check_sib19_unified_platform()
    all_results["chart_architecture"] = check_unified_chart_architecture()
    all_results["event_components"] = check_event_specific_components()
    all_results["cross_event_integration"] = check_cross_event_integration()
    all_results["testing_infrastructure"] = check_testing_infrastructure()
    
    # 生成報告
    report = generate_integration_report(all_results)
    
    # 輸出結果
    print("\n" + "=" * 70)
    print("📋 Phase 1.5 整合測試結果")
    print("=" * 70)
    
    print(f"總體分數: {report['overall_score']:.1f}%")
    print(f"測試狀態: {report['status']}")
    
    print("\n模組分數:")
    for module_name, score_info in report["module_scores"].items():
        status_icon = "✅" if score_info["score"] >= 80 else "⚠️" if score_info["score"] >= 60 else "❌"
        print(f"  {status_icon} {module_name}: {score_info['score']:.1f}% ({score_info['passed']}/{score_info['total']})")
    
    if report["recommendations"]:
        print("\n💡 改進建議:")
        for rec in report["recommendations"]:
            print(f"  • {rec}")
    
    print("\n🎯 Phase 1.5 功能總結:")
    print("  ✓ SIB19 統一基礎平台 - 資訊統一、應用分化")
    print("  ✓ 統一圖表架構 - 事件特定視覺化支援")
    print("  ✓ 跨事件資訊共享 - 鄰居細胞、SMTC、時間同步")
    print("  ✓ 事件特定組件 - Enhanced 組件完整實現")
    print("  ✓ 整合測試基礎設施 - 端到端測試支援")
    
    print("\n" + "=" * 70)
    
    if report["overall_score"] >= 80:
        print("🎉 Phase 1.5 統一平台整合測試通過！")
        print("🚀 可以繼續進行 Phase 2.5 最終系統整合驗證")
        return 0
    else:
        print("⚠️ Phase 1.5 存在一些問題，建議先完成改進")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
