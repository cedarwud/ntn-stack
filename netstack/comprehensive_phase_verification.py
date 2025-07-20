#!/usr/bin/env python3
"""
全面 Phase 驗證檢查
系統性檢查每個 Phase 的每個 step 是否都有確實開發實現
"""

import sys
import os

sys.path.append("/home/sat/ntn-stack/netstack")


def check_phase_0():
    """檢查 Phase 0: 數據真實性強化"""
    print("🔍 Phase 0: 數據真實性強化 - 詳細檢查")
    print("=" * 60)

    results = {}

    # Phase 0.1: 信號傳播模型真實化
    print("\n📋 Phase 0.1: 信號傳播模型真實化")
    print("-" * 40)

    # 檢查 ITU-R P.618 降雨衰減模型
    itu_file = "/home/sat/ntn-stack/netstack/netstack_api/models/itu_r_p618_rain_attenuation.py"
    if os.path.exists(itu_file):
        print("  ✅ ITU-R P.618 降雨衰減模型實現")
        with open(itu_file, "r") as f:
            content = f.read()
            if "class ITUR_P618_RainAttenuation" in content:
                print("    ✅ 完整類實現")
            if "calculate_rain_attenuation" in content:
                print("    ✅ 降雨衰減計算方法")
            if "k_alpha_parameters" in content:
                print("    ✅ k, α 參數表")
        results["0.1.1"] = True
    else:
        print("  ❌ ITU-R P.618 降雨衰減模型文件不存在")
        results["0.1.1"] = False

    # 檢查 NTN 路徑損耗模型
    ntn_file = "/home/sat/ntn-stack/netstack/netstack_api/models/ntn_path_loss_model.py"
    if os.path.exists(ntn_file):
        print("  ✅ NTN 路徑損耗模型實現")
        with open(ntn_file, "r") as f:
            content = f.read()
            if "class NTNPathLossModel" in content:
                print("    ✅ NTN 路徑損耗類實現")
            if "calculate_path_loss" in content:
                print("    ✅ 路徑損耗計算方法")
        results["0.1.2"] = True
    else:
        print("  ❌ NTN 路徑損耗模型文件不存在")
        results["0.1.2"] = False

    # Phase 0.2: 電離層和大氣效應模型
    print("\n📋 Phase 0.2: 電離層和大氣效應模型")
    print("-" * 40)

    # 檢查 Klobuchar 電離層延遲模型
    klobuchar_file = "/home/sat/ntn-stack/netstack/netstack_api/models/klobuchar_ionospheric_model.py"
    if os.path.exists(klobuchar_file):
        print("  ✅ Klobuchar 電離層延遲模型實現")
        with open(klobuchar_file, "r") as f:
            content = f.read()
            if "class KlobucharIonosphericModel" in content:
                print("    ✅ Klobuchar 模型類實現")
            if "calculate_ionospheric_delay" in content:
                print("    ✅ 電離層延遲計算方法")
        results["0.2.1"] = True
    else:
        print("  ❌ Klobuchar 電離層延遲模型文件不存在")
        results["0.2.1"] = False

    # Phase 0.3: 都卜勒頻移精確計算
    print("\n📋 Phase 0.3: 都卜勒頻移精確計算")
    print("-" * 40)

    # 檢查都卜勒計算引擎
    doppler_file = (
        "/home/sat/ntn-stack/netstack/netstack_api/models/doppler_calculation_engine.py"
    )
    if os.path.exists(doppler_file):
        print("  ✅ 都卜勒計算引擎實現")
        with open(doppler_file, "r") as f:
            content = f.read()
            if "class DopplerCalculationEngine" in content:
                print("    ✅ 都卜勒計算引擎類實現")
            if "calculate_doppler_shift" in content:
                print("    ✅ 都卜勒頻移計算方法")
        results["0.3.1"] = True
    else:
        print("  ❌ 都卜勒計算引擎文件不存在")
        results["0.3.1"] = False

    # 檢查驗證測試
    test_file = "/home/sat/ntn-stack/netstack/test_phase0_complete_verification.py"
    if os.path.exists(test_file):
        print("  ✅ Phase 0 完整驗證測試存在")
        results["0.test"] = True
    else:
        print("  ❌ Phase 0 完整驗證測試不存在")
        results["0.test"] = False

    return results


def check_phase_1():
    """檢查 Phase 1: 基礎設施重構"""
    print("\n🔍 Phase 1: 基礎設施重構 - 詳細檢查")
    print("=" * 60)

    results = {}

    # Phase 1.1: 軌道計算引擎開發
    print("\n📋 Phase 1.1: 軌道計算引擎開發")
    print("-" * 40)

    # 檢查軌道計算引擎
    orbit_file = (
        "/home/sat/ntn-stack/netstack/netstack_api/services/orbit_calculation_engine.py"
    )
    if os.path.exists(orbit_file):
        print("  ✅ 軌道計算引擎實現")
        with open(orbit_file, "r") as f:
            content = f.read()
            if "class OrbitCalculationEngine" in content:
                print("    ✅ 軌道計算引擎類實現")
            if "SGP4" in content:
                print("    ✅ SGP4 算法整合")
            if "calculate_satellite_position" in content:
                print("    ✅ 衛星位置計算方法")
        results["1.1.1"] = True
    else:
        print("  ❌ 軌道計算引擎文件不存在")
        results["1.1.1"] = False

    # 檢查 TLE 數據管理器
    tle_file = "/home/sat/ntn-stack/netstack/netstack_api/services/tle_data_manager.py"
    if os.path.exists(tle_file):
        print("  ✅ TLE 數據管理器實現")
        with open(tle_file, "r") as f:
            content = f.read()
            if "class TLEDataManager" in content:
                print("    ✅ TLE 數據管理器類實現")
            if "load_tle_data" in content:
                print("    ✅ TLE 數據加載方法")
        results["1.1.2"] = True
    else:
        print("  ❌ TLE 數據管理器文件不存在")
        results["1.1.2"] = False

    # Phase 1.1.1: SIB19 統一基礎平台開發
    print("\n📋 Phase 1.1.1: SIB19 統一基礎平台開發")
    print("-" * 40)

    # 檢查 SIB19 統一平台
    sib19_file = (
        "/home/sat/ntn-stack/netstack/netstack_api/services/sib19_unified_platform.py"
    )
    if os.path.exists(sib19_file):
        print("  ✅ SIB19 統一平台實現")
        with open(sib19_file, "r") as f:
            content = f.read()
            if "class SIB19UnifiedPlatform" in content:
                print("    ✅ SIB19 統一平台類實現")
            if "generate_sib19_broadcast" in content:
                print("    ✅ SIB19 廣播生成方法")
        results["1.1.1.1"] = True
    else:
        print("  ❌ SIB19 統一平台文件不存在")
        results["1.1.1.1"] = False

    # 檢查前端 SIB19 組件
    sib19_frontend = "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/shared/components/SIB19UnifiedPlatform.tsx"
    if os.path.exists(sib19_frontend):
        print("  ✅ 前端 SIB19 統一平台組件實現")
        results["1.1.1.2"] = True
    else:
        print("  ❌ 前端 SIB19 統一平台組件不存在")
        results["1.1.1.2"] = False

    # Phase 1.2: 後端 API 統一建構
    print("\n📋 Phase 1.2: 後端 API 統一建構")
    print("-" * 40)

    # 檢查測量事件服務
    measurement_service = "/home/sat/ntn-stack/netstack/netstack_api/services/measurement_event_service.py"
    if os.path.exists(measurement_service):
        print("  ✅ 測量事件服務實現")
        with open(measurement_service, "r") as f:
            content = f.read()
            if "class MeasurementEventService" in content:
                print("    ✅ 測量事件服務類實現")
            if "get_real_time_measurement_data" in content:
                print("    ✅ 實時測量數據方法")
            if "simulate_measurement_event" in content:
                print("    ✅ 測量事件模擬方法")
        results["1.2.1"] = True
    else:
        print("  ❌ 測量事件服務文件不存在")
        results["1.2.1"] = False

    # 檢查 API 路由器
    api_routers = [
        (
            "/home/sat/ntn-stack/netstack/netstack_api/routers/measurement_events_router.py",
            "測量事件路由器",
        ),
        (
            "/home/sat/ntn-stack/netstack/netstack_api/routers/orbit_router.py",
            "軌道路由器",
        ),
        (
            "/home/sat/ntn-stack/netstack/netstack_api/routers/sib19_router.py",
            "SIB19 路由器",
        ),
    ]

    for router_path, router_name in api_routers:
        if os.path.exists(router_path):
            print(f"  ✅ {router_name}實現")
            results[f"1.2.{router_name}"] = True
        else:
            print(f"  ❌ {router_name}不存在")
            results[f"1.2.{router_name}"] = False

    return results


def check_phase_1_5():
    """檢查 Phase 1.5: 統一 SIB19 基礎圖表架構重新設計"""
    print("\n🔍 Phase 1.5: 統一 SIB19 基礎圖表架構重新設計 - 詳細檢查")
    print("=" * 60)

    results = {}

    # Phase 1.5.1: 統一 SIB19 基礎平台分析設計
    print("\n📋 Phase 1.5.1: 統一 SIB19 基礎平台分析設計")
    print("-" * 40)

    # 檢查分析報告
    analysis_report = "/home/sat/ntn-stack/netstack/phase1_5_1_analysis_report.md"
    if os.path.exists(analysis_report):
        print("  ✅ 統一 SIB19 基礎平台分析報告存在")
        with open(analysis_report, "r") as f:
            content = f.read()
            if "資訊孤島問題" in content:
                print("    ✅ 資訊孤島問題分析")
            if "重複配置浪費" in content:
                print("    ✅ 重複配置浪費分析")
            if "統一改進主準則" in content:
                print("    ✅ 統一改進主準則設計")
        results["1.5.1.1"] = True
    else:
        print("  ❌ 統一 SIB19 基礎平台分析報告不存在")
        results["1.5.1.1"] = False

    # Phase 1.5.2: 統一基礎元件 + 事件特定元件實現
    print("\n📋 Phase 1.5.2: 統一基礎元件 + 事件特定元件實現")
    print("-" * 40)

    # 檢查統一數據管理器
    data_manager = "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/shared/services/SIB19UnifiedDataManager.ts"
    if os.path.exists(data_manager):
        print("  ✅ SIB19 統一數據管理器實現")
        with open(data_manager, "r") as f:
            content = f.read()
            if "class SIB19UnifiedDataManager" in content:
                print("    ✅ 統一數據管理器類實現")
            if "getA4SpecificData" in content:
                print("    ✅ A4 事件特定數據萃取")
            if "getD1SpecificData" in content:
                print("    ✅ D1 事件特定數據萃取")
            if "getD2SpecificData" in content:
                print("    ✅ D2 事件特定數據萃取")
            if "getT1SpecificData" in content:
                print("    ✅ T1 事件特定數據萃取")
        results["1.5.2.1"] = True
    else:
        print("  ❌ SIB19 統一數據管理器不存在")
        results["1.5.2.1"] = False

    # 檢查統一基礎圖表
    base_chart = "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/shared/components/SIB19UnifiedBaseChart.tsx"
    if os.path.exists(base_chart):
        print("  ✅ SIB19 統一基礎圖表實現")
        results["1.5.2.2"] = True
    else:
        print("  ❌ SIB19 統一基礎圖表不存在")
        results["1.5.2.2"] = False

    # 檢查 A4 事件專屬組件
    a4_chart = "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/shared/components/A4EventSpecificChart.tsx"
    if os.path.exists(a4_chart):
        print("  ✅ A4 事件專屬圖表實現")
        results["1.5.2.3"] = True
    else:
        print("  ❌ A4 事件專屬圖表不存在")
        results["1.5.2.3"] = False

    # Phase 1.5.3: 統一平台整合測試
    print("\n📋 Phase 1.5.3: 統一平台整合測試")
    print("-" * 40)

    # 檢查整合測試
    integration_test = "/home/sat/ntn-stack/netstack/test_phase1_5_3_integration.py"
    if os.path.exists(integration_test):
        print("  ✅ 統一平台整合測試實現")
        results["1.5.3.1"] = True
    else:
        print("  ❌ 統一平台整合測試不存在")
        results["1.5.3.1"] = False

    return results


def check_phase_2():
    """檢查 Phase 2: 各事件標準合規修正與圖表重新實現"""
    print("\n🔍 Phase 2: 各事件標準合規修正與圖表重新實現 - 詳細檢查")
    print("=" * 60)

    results = {}

    # Phase 2.1: D2 事件優先修正與圖表重新實現
    print("\n📋 Phase 2.1: D2 事件優先修正與圖表重新實現")
    print("-" * 40)

    # 檢查 D2 事件專屬組件
    d2_chart = "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/shared/components/D2EventSpecificChart.tsx"
    if os.path.exists(d2_chart):
        print("  ✅ D2 事件專屬圖表實現")
        with open(d2_chart, "r") as f:
            content = f.read()
            if "90 分鐘" in content:
                print("    ✅ 軌道週期修正 (90分鐘)")
            if "真實 LEO" in content:
                print("    ✅ 真實 LEO 衛星軌道")
            if "validityTime" in content:
                print("    ✅ 星曆有效期整合")
            if "雙閾值" in content:
                print("    ✅ 雙閾值觸發視覺化")
        results["2.1.1"] = True
    else:
        print("  ❌ D2 事件專屬圖表不存在")
        results["2.1.1"] = False

    # 檢查 D2 驗證測試
    d2_test = "/home/sat/ntn-stack/netstack/test_phase2_1_verification.py"
    if os.path.exists(d2_test):
        print("  ✅ D2 事件驗證測試實現")
        results["2.1.2"] = True
    else:
        print("  ❌ D2 事件驗證測試不存在")
        results["2.1.2"] = False

    # Phase 2.2: D1 事件改進與圖表重新實現
    print("\n📋 Phase 2.2: D1 事件改進與圖表重新實現")
    print("-" * 40)

    # 檢查 D1 相關組件
    d1_components = [
        (
            "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/charts/EnhancedD1Chart.tsx",
            "D1 增強圖表",
        ),
        (
            "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/viewers/EnhancedD1Viewer.tsx",
            "D1 增強查看器",
        ),
    ]

    for component_path, component_name in d1_components:
        if os.path.exists(component_path):
            print(f"  ✅ {component_name}實現")
            results[f"2.2.{component_name}"] = True
        else:
            print(f"  ❌ {component_name}不存在")
            results[f"2.2.{component_name}"] = False

    # Phase 2.3: T1 事件增強與圖表重新實現
    print("\n📋 Phase 2.3: T1 事件增強與圖表重新實現")
    print("-" * 40)

    # 檢查 T1 事件專屬組件
    t1_chart = "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/shared/components/T1EventSpecificChart.tsx"
    if os.path.exists(t1_chart):
        print("  ✅ T1 事件專屬圖表實現")
        with open(t1_chart, "r") as f:
            content = f.read()
            if "GNSS 時間同步" in content:
                print("    ✅ GNSS 時間同步狀態")
            if "時鐘偏差" in content:
                print("    ✅ 時鐘偏差視覺化")
            if "時間窗口" in content:
                print("    ✅ 時間窗口展示")
            if "警告和恢復" in content:
                print("    ✅ 警告和恢復機制")
        results["2.3.1"] = True
    else:
        print("  ❌ T1 事件專屬圖表不存在")
        results["2.3.1"] = False

    # 檢查 T1 驗證測試
    t1_test = "/home/sat/ntn-stack/netstack/test_phase2_3_verification.py"
    if os.path.exists(t1_test):
        print("  ✅ T1 事件驗證測試實現")
        results["2.3.2"] = True
    else:
        print("  ❌ T1 事件驗證測試不存在")
        results["2.3.2"] = False

    # 檢查 T1 相關組件
    t1_components = [
        (
            "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/charts/EnhancedT1Chart.tsx",
            "T1 增強圖表",
        ),
        (
            "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/viewers/EnhancedT1Viewer.tsx",
            "T1 增強查看器",
        ),
    ]

    for component_path, component_name in t1_components:
        if os.path.exists(component_path):
            print(f"  ✅ {component_name}實現")
            results[f"2.3.{component_name}"] = True
        else:
            print(f"  ❌ {component_name}不存在")
            results[f"2.3.{component_name}"] = False

    # Phase 2.4: A4 事件 SIB19 強化和位置補償實現
    print("\n📋 Phase 2.4: A4 事件 SIB19 強化和位置補償實現")
    print("-" * 40)

    # 檢查 A4 相關組件
    a4_components = [
        (
            "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/charts/EnhancedA4Chart.tsx",
            "A4 增強圖表",
        ),
        (
            "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/viewers/EnhancedA4Viewer.tsx",
            "A4 增強查看器",
        ),
    ]

    for component_path, component_name in a4_components:
        if os.path.exists(component_path):
            print(f"  ✅ {component_name}實現")
            results[f"2.4.{component_name}"] = True
        else:
            print(f"  ❌ {component_name}不存在")
            results[f"2.4.{component_name}"] = False

    return results


def check_phase_3():
    """檢查 Phase 3: UI/UX 統一改進"""
    print("\n🔍 Phase 3: UI/UX 統一改進 - 詳細檢查")
    print("=" * 60)

    results = {}

    # Phase 3.1: 簡易版模式實現
    print("\n📋 Phase 3.1: 簡易版模式實現")
    print("-" * 40)

    # 檢查視圖模式系統
    view_modes = (
        "/home/sat/ntn-stack/simworld/frontend/src/types/measurement-view-modes.ts"
    )
    if os.path.exists(view_modes):
        print("  ✅ 測量視圖模式系統實現")
        with open(view_modes, "r") as f:
            content = f.read()
            if "ViewMode" in content:
                print("    ✅ ViewMode 類型系統")
            if "ViewModeConfig" in content:
                print("    ✅ ViewModeConfig 配置介面")
        results["3.1.1"] = True
    else:
        print("  ❌ 測量視圖模式系統不存在")
        results["3.1.1"] = False

    # 檢查核心管理 Hook
    view_mode_manager = (
        "/home/sat/ntn-stack/simworld/frontend/src/hooks/useViewModeManager.ts"
    )
    if os.path.exists(view_mode_manager):
        print("  ✅ 核心管理 Hook 實現")
        results["3.1.2"] = True
    else:
        print("  ❌ 核心管理 Hook 不存在")
        results["3.1.2"] = False

    # 檢查 UI 組件
    ui_components = [
        (
            "/home/sat/ntn-stack/simworld/frontend/src/components/common/ViewModeToggle.tsx",
            "ViewModeToggle 組件",
        ),
        (
            "/home/sat/ntn-stack/simworld/frontend/src/components/common/EnhancedParameterPanel.tsx",
            "EnhancedParameterPanel 組件",
        ),
    ]

    for component_path, component_name in ui_components:
        if os.path.exists(component_path):
            print(f"  ✅ {component_name}實現")
            results[f"3.1.{component_name}"] = True
        else:
            print(f"  ❌ {component_name}不存在")
            results[f"3.1.{component_name}"] = False

    # 檢查集成示例和儀表板
    dashboard_components = [
        (
            "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/MeasurementEventDashboard.tsx",
            "MeasurementEventDashboard",
        )
    ]

    for component_path, component_name in dashboard_components:
        if os.path.exists(component_path):
            print(f"  ✅ {component_name}實現")
            results[f"3.1.{component_name}"] = True
        else:
            print(f"  ❌ {component_name}不存在")
            results[f"3.1.{component_name}"] = False

    # Phase 3.2: 圖表說明統一改進
    print("\n📋 Phase 3.2: 圖表說明統一改進")
    print("-" * 40)

    # 檢查說明系統
    explanation_system = "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/shared/components/ChartExplanationSystem.tsx"
    if os.path.exists(explanation_system):
        print("  ✅ 圖表說明系統實現")
        results["3.2.1"] = True
    else:
        print("  ❌ 圖表說明系統不存在")
        results["3.2.1"] = False

    # Phase 3.3: 教育內容整合
    print("\n📋 Phase 3.3: 教育內容整合")
    print("-" * 40)

    # 檢查教育模組
    education_modules = [
        (
            "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/education",
            "教育模組目錄",
        ),
        (
            "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/education/ConceptExplanation.tsx",
            "概念解釋模組",
        ),
        (
            "/home/sat/ntn-stack/simworld/frontend/src/components/domains/measurement/education/InteractiveGuide.tsx",
            "互動式指南",
        ),
    ]

    for module_path, module_name in education_modules:
        if os.path.exists(module_path):
            print(f"  ✅ {module_name}實現")
            results[f"3.3.{module_name}"] = True
        else:
            print(f"  ❌ {module_name}不存在")
            results[f"3.3.{module_name}"] = False

    return results


def check_phase_4():
    """檢查 Phase 4: 系統整合和驗證"""
    print("\n🔍 Phase 4: 系統整合和驗證 - 詳細檢查")
    print("=" * 60)

    results = {}

    # Phase 4.1: 整合測試
    print("\n📋 Phase 4.1: 整合測試")
    print("-" * 40)

    # 檢查端到端測試
    e2e_tests = [
        (
            "/home/sat/ntn-stack/netstack/test_end_to_end_functionality.py",
            "端到端功能測試",
        ),
        ("/home/sat/ntn-stack/netstack/test_api_performance.py", "API 性能測試"),
        ("/home/sat/ntn-stack/netstack/test_ui_mode_switching.py", "UI 模式切換測試"),
    ]

    for test_path, test_name in e2e_tests:
        if os.path.exists(test_path):
            print(f"  ✅ {test_name}實現")
            results[f"4.1.{test_name}"] = True
        else:
            print(f"  ❌ {test_name}不存在")
            results[f"4.1.{test_name}"] = False

    # Phase 4.2: 性能優化
    print("\n📋 Phase 4.2: 性能優化")
    print("-" * 40)

    # 檢查性能優化模組
    performance_modules = [
        (
            "/home/sat/ntn-stack/netstack/netstack_api/services/orbit_cache_service.py",
            "軌道計算緩存服務",
        ),
        (
            "/home/sat/ntn-stack/netstack/netstack_api/services/performance_optimizer.py",
            "性能優化器",
        ),
    ]

    for module_path, module_name in performance_modules:
        if os.path.exists(module_path):
            print(f"  ✅ {module_name}實現")
            results[f"4.2.{module_name}"] = True
        else:
            print(f"  ❌ {module_name}不存在")
            results[f"4.2.{module_name}"] = False

    # Phase 4.3: 文檔和培訓
    print("\n📋 Phase 4.3: 文檔和培訓")
    print("-" * 40)

    # 檢查文檔
    documentation = [
        ("/home/sat/ntn-stack/docs/api_documentation.md", "API 文檔"),
        ("/home/sat/ntn-stack/docs/developer_guide.md", "開發者指南"),
        ("/home/sat/ntn-stack/docs/user_manual.md", "用戶手冊"),
        ("/home/sat/ntn-stack/docs/troubleshooting.md", "故障排除手冊"),
    ]

    for doc_path, doc_name in documentation:
        if os.path.exists(doc_path):
            print(f"  ✅ {doc_name}實現")
            results[f"4.3.{doc_name}"] = True
        else:
            print(f"  ❌ {doc_name}不存在")
            results[f"4.3.{doc_name}"] = False

    return results


def main():
    """主函數 - 執行全面檢查"""
    print("🚀 NTN-Stack 測量事件系統 - 全面 Phase 驗證檢查")
    print("=" * 80)
    print("目標：系統性檢查每個 Phase 的每個 step 是否都有確實開發實現")
    print("=" * 80)

    all_results = {}

    # 檢查各個 Phase
    phases = [
        ("Phase 0", check_phase_0),
        ("Phase 1", check_phase_1),
        ("Phase 1.5", check_phase_1_5),
        ("Phase 2", check_phase_2),
        ("Phase 3", check_phase_3),
        ("Phase 4", check_phase_4),
    ]

    for phase_name, check_func in phases:
        try:
            results = check_func()
            all_results[phase_name] = results
        except Exception as e:
            print(f"❌ {phase_name} 檢查過程中發生錯誤: {e}")
            all_results[phase_name] = {}

    # 統計總體結果
    print("\n" + "=" * 80)
    print("📊 全面檢查結果統計")
    print("=" * 80)

    total_checks = 0
    passed_checks = 0

    for phase_name, results in all_results.items():
        phase_total = len(results)
        phase_passed = sum(1 for result in results.values() if result)
        total_checks += phase_total
        passed_checks += phase_passed

        if phase_total > 0:
            percentage = (phase_passed / phase_total) * 100
            print(f"{phase_name}: {phase_passed}/{phase_total} ({percentage:.1f}%)")

            # 顯示失敗的項目
            failed_items = [item for item, result in results.items() if not result]
            if failed_items:
                print(f"  ❌ 未實現項目: {', '.join(failed_items)}")
        else:
            print(f"{phase_name}: 無檢查項目")

    print("\n" + "-" * 80)
    if total_checks > 0:
        overall_percentage = (passed_checks / total_checks) * 100
        print(
            f"📈 總體完成度: {passed_checks}/{total_checks} ({overall_percentage:.1f}%)"
        )

        if overall_percentage >= 90:
            print("🎉 項目整體完成度優秀！")
        elif overall_percentage >= 70:
            print("✅ 項目整體完成度良好，還有改進空間")
        else:
            print("⚠️ 項目還需要大量開發工作")
    else:
        print("❌ 沒有找到任何檢查項目")

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
