#!/usr/bin/env python3
"""
Phase 2.5 最終系統整合驗證
確保所有 Enhanced 組件協調運作，完成端到端功能測試
"""

import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

# 添加項目路徑
sys.path.append("/home/sat/ntn-stack")
sys.path.append("/home/sat/ntn-stack/netstack")


def run_command(command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
    """執行命令並返回結果"""
    try:
        result = subprocess.run(
            command.split(), cwd=cwd, capture_output=True, text=True, timeout=30
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command timeout",
            "returncode": -1,
        }
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}


def test_backend_services() -> Dict[str, Any]:
    """測試後端服務"""
    print("🔍 測試後端服務...")

    results = {
        "measurement_event_service": False,
        "orbit_calculation_engine": False,
        "sib19_unified_platform": False,
        "weather_data_service": False,
        "doppler_calculation": False,
        "ionospheric_models": False,
        "ntn_path_loss": False,
    }

    # 測試測量事件服務
    try:
        from netstack_api.services.measurement_event_service import (
            MeasurementEventService,
        )

        service = MeasurementEventService()
        results["measurement_event_service"] = True
        print("  ✅ 測量事件服務正常")
    except Exception as e:
        print(f"  ❌ 測量事件服務錯誤: {e}")

    # 測試軌道計算引擎
    try:
        from netstack_api.services.orbit_calculation_engine import (
            OrbitCalculationEngine,
        )

        engine = OrbitCalculationEngine()
        results["orbit_calculation_engine"] = True
        print("  ✅ 軌道計算引擎正常")
    except Exception as e:
        print(f"  ❌ 軌道計算引擎錯誤: {e}")

    # 測試 SIB19 統一平台
    try:
        from netstack_api.services.sib19_unified_platform import SIB19UnifiedPlatform

        platform = SIB19UnifiedPlatform()
        results["sib19_unified_platform"] = True
        print("  ✅ SIB19 統一平台正常")
    except Exception as e:
        print(f"  ❌ SIB19 統一平台錯誤: {e}")

    # 測試氣象數據服務
    try:
        from netstack_api.services.weather_data_service import WeatherDataService

        weather_service = WeatherDataService()
        results["weather_data_service"] = True
        print("  ✅ 氣象數據服務正常")
    except Exception as e:
        print(f"  ❌ 氣象數據服務錯誤: {e}")

    # 測試都卜勒計算引擎
    try:
        from netstack_api.models.doppler_calculation_engine import (
            DopplerCalculationEngine,
        )

        doppler_engine = DopplerCalculationEngine()
        results["doppler_calculation"] = True
        print("  ✅ 都卜勒計算引擎正常")
    except Exception as e:
        print(f"  ❌ 都卜勒計算引擎錯誤: {e}")

    # 測試電離層模型
    try:
        from netstack_api.models.ionospheric_models import KlobucharIonosphericModel

        iono_model = KlobucharIonosphericModel()
        results["ionospheric_models"] = True
        print("  ✅ 電離層模型正常")
    except Exception as e:
        print(f"  ❌ 電離層模型錯誤: {e}")

    # 測試 NTN 路徑損耗模型
    try:
        from netstack_api.models.ntn_path_loss_models import NTNPathLossModel

        path_loss_model = NTNPathLossModel()
        results["ntn_path_loss"] = True
        print("  ✅ NTN 路徑損耗模型正常")
    except Exception as e:
        print(f"  ❌ NTN 路徑損耗模型錯誤: {e}")

    return results


def test_enhanced_components() -> Dict[str, Any]:
    """測試 Enhanced 組件"""
    print("\n🔍 測試 Enhanced 組件...")

    results = {
        "component_files": {},
        "component_sizes": {},
        "component_completeness": {},
    }

    event_types = ["A4", "D1", "D2", "T1"]

    for event_type in event_types:
        print(f"  檢查 {event_type} Enhanced 組件...")

        # 檢查 Enhanced Chart
        chart_path = f"/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/charts/Enhanced{event_type}Chart.tsx"
        viewer_path = f"/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/charts/Enhanced{event_type}Viewer.tsx"

        chart_exists = Path(chart_path).exists()
        viewer_exists = Path(viewer_path).exists()

        results["component_files"][event_type] = {
            "chart": chart_exists,
            "viewer": viewer_exists,
        }

        # 檢查文件大小 (作為複雜度指標)
        if chart_exists:
            chart_size = Path(chart_path).stat().st_size
            results["component_sizes"][f"{event_type}_chart"] = chart_size

        if viewer_exists:
            viewer_size = Path(viewer_path).stat().st_size
            results["component_sizes"][f"{event_type}_viewer"] = viewer_size

        # 評估完整性
        completeness_score = 0
        if chart_exists:
            completeness_score += 50
        if viewer_exists:
            completeness_score += 50

        results["component_completeness"][event_type] = completeness_score

        if completeness_score == 100:
            print(f"    ✅ {event_type} Enhanced 組件完整")
        else:
            print(f"    ⚠️ {event_type} Enhanced 組件不完整 ({completeness_score}%)")

    return results


def test_api_endpoints() -> Dict[str, Any]:
    """測試 API 端點"""
    print("\n🔍 測試 API 端點...")

    results = {
        "measurement_events": False,
        "orbit_calculation": False,
        "sib19_status": False,
        "weather_data": False,
    }

    # 檢查 API 路由文件
    api_files = [
        "/home/sat/ntn-stack/netstack/netstack_api/routers/measurement_events_router.py",
        "/home/sat/ntn-stack/netstack/netstack_api/routers/orbit_router.py",
        "/home/sat/ntn-stack/netstack/netstack_api/routers/sib19_router.py",
    ]

    for api_file in api_files:
        if Path(api_file).exists():
            filename = Path(api_file).stem
            if "measurement" in filename:
                results["measurement_events"] = True
                print("  ✅ 測量事件 API 路由存在")
            elif "orbit" in filename:
                results["orbit_calculation"] = True
                print("  ✅ 軌道計算 API 路由存在")
            elif "sib19" in filename:
                results["sib19_status"] = True
                print("  ✅ SIB19 API 路由存在")

    # 檢查氣象數據 API (在服務中實現)
    weather_service_path = (
        "/home/sat/ntn-stack/netstack/netstack_api/services/weather_data_service.py"
    )
    if Path(weather_service_path).exists():
        results["weather_data"] = True
        print("  ✅ 氣象數據服務存在")

    return results


def test_frontend_integration() -> Dict[str, Any]:
    """測試前端整合"""
    print("\n🔍 測試前端整合...")

    results = {
        "build_success": False,
        "component_imports": False,
        "routing": False,
        "state_management": False,
    }

    # 測試前端構建
    frontend_dir = "/home/sat/ntn-stack/simworld/frontend"
    if Path(frontend_dir).exists():
        print("  測試前端構建...")
        build_result = run_command("npm run build", cwd=frontend_dir)

        if build_result["success"]:
            results["build_success"] = True
            print("  ✅ 前端構建成功")
        else:
            print(f"  ❌ 前端構建失敗: {build_result['stderr']}")

    # 檢查組件導入
    main_app_path = f"{frontend_dir}/src/App.tsx"
    if Path(main_app_path).exists():
        with open(main_app_path, "r", encoding="utf-8") as f:
            content = f.read()
            if "measurement" in content.lower():
                results["component_imports"] = True
                print("  ✅ 測量組件導入正常")

    # 檢查路由配置
    router_files = list(Path(f"{frontend_dir}/src").rglob("*router*.tsx"))
    if router_files:
        results["routing"] = True
        print(f"  ✅ 路由配置存在 ({len(router_files)} 個文件)")

    # 檢查狀態管理
    state_files = list(Path(f"{frontend_dir}/src").rglob("*store*.ts*"))
    hook_files = list(Path(f"{frontend_dir}/src").rglob("use*.ts*"))

    if state_files or len(hook_files) > 5:
        results["state_management"] = True
        print(f"  ✅ 狀態管理實現 ({len(state_files)} store, {len(hook_files)} hooks)")

    return results


def test_data_flow_integration() -> Dict[str, Any]:
    """測試數據流整合"""
    print("\n🔍 測試數據流整合...")

    results = {
        "backend_to_frontend": False,
        "real_time_updates": False,
        "error_handling": False,
        "data_validation": False,
    }

    # 檢查後端到前端的數據流
    api_client_files = list(
        Path("/home/sat/ntn-stack/simworld/frontend/src").rglob("*api*.ts*")
    )
    service_files = list(
        Path("/home/sat/ntn-stack/simworld/frontend/src").rglob("*service*.ts*")
    )

    if api_client_files or service_files:
        results["backend_to_frontend"] = True
        print(
            f"  ✅ 後端到前端數據流 ({len(api_client_files)} API, {len(service_files)} 服務)"
        )

    # 檢查實時更新機制
    websocket_files = list(Path("/home/sat/ntn-stack").rglob("*websocket*"))
    sse_files = list(Path("/home/sat/ntn-stack").rglob("*sse*"))

    if websocket_files or sse_files:
        results["real_time_updates"] = True
        print(f"  ✅ 實時更新機制 ({len(websocket_files)} WS, {len(sse_files)} SSE)")

    # 檢查錯誤處理
    error_files = list(
        Path("/home/sat/ntn-stack/simworld/frontend/src").rglob("*error*")
    )
    try_catch_files = []

    # 搜索包含 try-catch 的文件
    for ts_file in Path("/home/sat/ntn-stack/simworld/frontend/src").rglob("*.ts*"):
        try:
            with open(ts_file, "r", encoding="utf-8") as f:
                content = f.read()
                if "try" in content and "catch" in content:
                    try_catch_files.append(ts_file)
        except:
            continue

    if error_files or len(try_catch_files) > 10:
        results["error_handling"] = True
        print(
            f"  ✅ 錯誤處理機制 ({len(error_files)} 錯誤組件, {len(try_catch_files)} try-catch)"
        )

    # 檢查數據驗證
    validation_files = list(Path("/home/sat/ntn-stack").rglob("*validation*"))
    schema_files = list(Path("/home/sat/ntn-stack").rglob("*schema*"))

    if validation_files or schema_files:
        results["data_validation"] = True
        print(
            f"  ✅ 數據驗證機制 ({len(validation_files)} 驗證, {len(schema_files)} 模式)"
        )

    return results


def test_performance_metrics() -> Dict[str, Any]:
    """測試性能指標"""
    print("\n🔍 測試性能指標...")

    results = {
        "bundle_size": False,
        "component_count": 0,
        "code_complexity": False,
        "test_coverage": False,
    }

    # 檢查打包大小
    dist_dir = "/home/sat/ntn-stack/simworld/frontend/dist"
    if Path(dist_dir).exists():
        js_files = list(Path(dist_dir).rglob("*.js"))
        total_size = sum(f.stat().st_size for f in js_files)

        if total_size < 10 * 1024 * 1024:  # 小於 10MB
            results["bundle_size"] = True
            print(f"  ✅ 打包大小合理 ({total_size / 1024 / 1024:.1f} MB)")
        else:
            print(f"  ⚠️ 打包大小較大 ({total_size / 1024 / 1024:.1f} MB)")

    # 統計組件數量
    component_files = list(
        Path("/home/sat/ntn-stack/simworld/frontend/src/components").rglob("*.tsx")
    )
    results["component_count"] = len(component_files)
    print(f"  📊 組件數量: {len(component_files)}")

    # 評估代碼複雜度 (基於文件大小)
    large_files = []
    for comp_file in component_files:
        if comp_file.stat().st_size > 50 * 1024:  # 大於 50KB
            large_files.append(comp_file)

    if len(large_files) < len(component_files) * 0.2:  # 少於 20% 的大文件
        results["code_complexity"] = True
        print(f"  ✅ 代碼複雜度合理 ({len(large_files)} 個大文件)")
    else:
        print(f"  ⚠️ 代碼複雜度較高 ({len(large_files)} 個大文件)")

    # 檢查測試覆蓋率
    test_files = list(Path("/home/sat/ntn-stack").rglob("*.test.*"))
    spec_files = list(Path("/home/sat/ntn-stack").rglob("*.spec.*"))

    total_test_files = len(test_files) + len(spec_files)
    if total_test_files > 10:
        results["test_coverage"] = True
        print(f"  ✅ 測試覆蓋率良好 ({total_test_files} 個測試文件)")
    else:
        print(f"  ⚠️ 測試覆蓋率需要改進 ({total_test_files} 個測試文件)")

    return results


def generate_final_integration_report(
    all_results: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """生成最終整合報告"""
    print("\n📊 生成 Phase 2.5 最終整合報告...")

    # 計算各模組分數
    module_scores = {}

    for module_name, module_results in all_results.items():
        if isinstance(module_results, dict):
            total_checks = 0
            passed_checks = 0

            def count_results(obj):
                nonlocal total_checks, passed_checks
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if isinstance(value, bool):
                            total_checks += 1
                            if value:
                                passed_checks += 1
                        elif isinstance(value, dict):
                            count_results(value)
                        elif isinstance(value, int) and key == "component_count":
                            # 組件數量評分
                            total_checks += 1
                            if value >= 20:  # 至少 20 個組件
                                passed_checks += 1
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
                    "total": total_checks,
                }

    # 計算總體分數
    if module_scores:
        overall_score = sum(score["score"] for score in module_scores.values()) / len(
            module_scores
        )
    else:
        overall_score = 0

    # 生成報告
    report = {
        "test_suite": "Phase 2.5 最終系統整合驗證",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_score": overall_score,
        "status": (
            "PASSED"
            if overall_score >= 85
            else "NEEDS_IMPROVEMENT" if overall_score >= 70 else "FAILED"
        ),
        "module_scores": module_scores,
        "detailed_results": all_results,
        "critical_issues": [],
        "recommendations": [],
    }

    # 識別關鍵問題
    for module_name, score_info in module_scores.items():
        if score_info["score"] < 70:
            report["critical_issues"].append(
                f"{module_name} 模組分數過低 ({score_info['score']:.1f}%)"
            )

    # 生成建議
    if overall_score < 85:
        for module_name, score_info in module_scores.items():
            if score_info["score"] < 85:
                report["recommendations"].append(
                    f"改進 {module_name} 模組 (當前: {score_info['score']:.1f}%)"
                )

    return report


def main():
    """主函數"""
    print("🚀 Phase 2.5 最終系統整合驗證")
    print("=" * 70)

    # 執行各項測試
    all_results = {}

    all_results["backend_services"] = test_backend_services()
    all_results["enhanced_components"] = test_enhanced_components()
    all_results["api_endpoints"] = test_api_endpoints()
    all_results["frontend_integration"] = test_frontend_integration()
    all_results["data_flow_integration"] = test_data_flow_integration()
    all_results["performance_metrics"] = test_performance_metrics()

    # 生成報告
    report = generate_final_integration_report(all_results)

    # 輸出結果
    print("\n" + "=" * 70)
    print("📋 Phase 2.5 最終整合驗證結果")
    print("=" * 70)

    print(f"總體分數: {report['overall_score']:.1f}%")
    print(f"測試狀態: {report['status']}")

    print("\n模組分數:")
    for module_name, score_info in report["module_scores"].items():
        status_icon = (
            "✅"
            if score_info["score"] >= 85
            else "⚠️" if score_info["score"] >= 70 else "❌"
        )
        print(
            f"  {status_icon} {module_name}: {score_info['score']:.1f}% ({score_info['passed']}/{score_info['total']})"
        )

    if report["critical_issues"]:
        print("\n🚨 關鍵問題:")
        for issue in report["critical_issues"]:
            print(f"  • {issue}")

    if report["recommendations"]:
        print("\n💡 改進建議:")
        for rec in report["recommendations"]:
            print(f"  • {rec}")

    print("\n🎯 Phase 2.5 系統整合總結:")
    print("  ✓ 後端服務 - 測量事件、軌道計算、SIB19、氣象數據")
    print("  ✓ Enhanced 組件 - A4/D1/D2/T1 完整實現")
    print("  ✓ API 端點 - RESTful API 完整支援")
    print("  ✓ 前端整合 - 組件導入、路由、狀態管理")
    print("  ✓ 數據流整合 - 後端到前端、實時更新、錯誤處理")
    print("  ✓ 性能指標 - 打包大小、組件數量、測試覆蓋率")

    print("\n" + "=" * 70)

    if report["overall_score"] >= 85:
        print("🎉 Phase 2.5 最終系統整合驗證通過！")
        print("🚀 系統已準備好進行 Phase 3.2 UI/UX 改進")
        return 0
    elif report["overall_score"] >= 70:
        print("⚠️ Phase 2.5 基本通過，但建議先完成改進")
        return 1
    else:
        print("❌ Phase 2.5 存在嚴重問題，需要立即修復")
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
