#!/usr/bin/env python3
"""
Phase 3 快速功能驗證腳本

快速驗證 Phase 3 決策透明化與視覺化功能的可用性：
- 檢查所有分析組件的導入和初始化
- 驗證核心功能的基本操作
- 測試 API 端點的可訪問性
- 生成功能可用性報告

使用方法:
    python phase_3_quick_verify.py
"""

import sys
import time
import logging
from datetime import datetime
from typing import Dict, List, Any

# 設置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_imports() -> Dict[str, bool]:
    """檢查 Phase 3 組件導入"""
    logger.info("🔍 檢查 Phase 3 組件導入...")
    
    imports = {}
    
    # 檢查核心分析組件
    try:
        from ..analytics import AdvancedExplainabilityEngine
        imports["explainability_engine"] = True
        logger.info("✅ AdvancedExplainabilityEngine 導入成功")
    except ImportError as e:
        imports["explainability_engine"] = False
        logger.warning(f"❌ AdvancedExplainabilityEngine 導入失敗: {e}")
    
    try:
        from ..analytics import ConvergenceAnalyzer
        imports["convergence_analyzer"] = True
        logger.info("✅ ConvergenceAnalyzer 導入成功")
    except ImportError as e:
        imports["convergence_analyzer"] = False
        logger.warning(f"❌ ConvergenceAnalyzer 導入失敗: {e}")
    
    try:
        from ..analytics import StatisticalTestingEngine
        imports["statistical_testing"] = True
        logger.info("✅ StatisticalTestingEngine 導入成功")
    except ImportError as e:
        imports["statistical_testing"] = False
        logger.warning(f"❌ StatisticalTestingEngine 導入失敗: {e}")
    
    try:
        from ..analytics import AcademicDataExporter
        imports["academic_exporter"] = True
        logger.info("✅ AcademicDataExporter 導入成功")
    except ImportError as e:
        imports["academic_exporter"] = False
        logger.warning(f"❌ AcademicDataExporter 導入失敗: {e}")
    
    try:
        from ..analytics import VisualizationEngine
        imports["visualization_engine"] = True
        logger.info("✅ VisualizationEngine 導入成功")
    except ImportError as e:
        imports["visualization_engine"] = False
        logger.warning(f"❌ VisualizationEngine 導入失敗: {e}")
    
    # 檢查 API
    try:
        from ..api.phase_3_api import router
        imports["phase3_api"] = True
        logger.info("✅ Phase 3 API 導入成功")
    except ImportError as e:
        imports["phase3_api"] = False
        logger.warning(f"❌ Phase 3 API 導入失敗: {e}")
    
    return imports

def check_dependencies() -> Dict[str, bool]:
    """檢查可選依賴項"""
    logger.info("🔍 檢查可選依賴項...")
    
    dependencies = {}
    
    # SciPy (統計測試)
    try:
        import scipy
        dependencies["scipy"] = True
        logger.info(f"✅ SciPy {scipy.__version__} 可用")
    except ImportError:
        dependencies["scipy"] = False
        logger.warning("⚠️  SciPy 不可用 - 統計測試功能受限")
    
    # Scikit-learn (機器學習分析)
    try:
        import sklearn
        dependencies["sklearn"] = True
        logger.info(f"✅ Scikit-learn {sklearn.__version__} 可用")
    except ImportError:
        dependencies["sklearn"] = False
        logger.warning("⚠️  Scikit-learn 不可用 - 特徵重要性分析受限")
    
    # Matplotlib (靜態圖表)
    try:
        import matplotlib
        dependencies["matplotlib"] = True
        logger.info(f"✅ Matplotlib {matplotlib.__version__} 可用")
    except ImportError:
        dependencies["matplotlib"] = False
        logger.warning("⚠️  Matplotlib 不可用 - 靜態視覺化受限")
    
    # Plotly (互動圖表)
    try:
        import plotly
        dependencies["plotly"] = True
        logger.info(f"✅ Plotly {plotly.__version__} 可用")
    except ImportError:
        dependencies["plotly"] = False
        logger.warning("⚠️  Plotly 不可用 - 互動視覺化受限")
    
    # Bokeh (實時儀表板)
    try:
        import bokeh
        dependencies["bokeh"] = True
        logger.info(f"✅ Bokeh {bokeh.__version__} 可用")
    except ImportError:
        dependencies["bokeh"] = False
        logger.warning("⚠️  Bokeh 不可用 - 實時儀表板受限")
    
    return dependencies

def test_explainability_engine(imports: Dict[str, bool]) -> bool:
    """測試解釋性引擎"""
    if not imports.get("explainability_engine", False):
        logger.warning("⚠️  跳過解釋性引擎測試 - 組件不可用")
        return False
    
    try:
        logger.info("🧪 測試解釋性引擎...")
        
        from ..analytics import AdvancedExplainabilityEngine
        
        # 創建引擎
        engine = AdvancedExplainabilityEngine({
            "explainability_level": "basic",
            "enable_feature_importance": True,
        })
        
        # 測試決策解釋
        import numpy as np
        test_data = {
            "state": np.random.rand(10).tolist(),
            "action": 2,
            "q_values": np.random.rand(5).tolist(),
            "algorithm": "DQN",
            "episode": 100,
            "step": 50,
        }
        
        explanation = engine.explain_decision(test_data)
        
        if explanation is not None:
            logger.info("✅ 解釋性引擎測試通過")
            return True
        else:
            logger.warning("⚠️  解釋性引擎測試失敗 - 無法生成解釋")
            return False
            
    except Exception as e:
        logger.error(f"❌ 解釋性引擎測試失敗: {e}")
        return False

def test_convergence_analyzer(imports: Dict[str, bool]) -> bool:
    """測試收斂性分析器"""
    if not imports.get("convergence_analyzer", False):
        logger.warning("⚠️  跳過收斂性分析器測試 - 組件不可用")
        return False
    
    try:
        logger.info("🧪 測試收斂性分析器...")
        
        from ..analytics import ConvergenceAnalyzer
        
        # 創建分析器
        analyzer = ConvergenceAnalyzer({
            "smoothing_window": 5,
            "convergence_threshold": 0.01,
        })
        
        # 生成測試數據
        import numpy as np
        rewards = np.linspace(-50, 45, 100) + np.random.normal(0, 5, 100)
        
        # 測試學習曲線分析
        analysis = analyzer.analyze_learning_curve(rewards.tolist(), "total_reward")
        
        if analysis is not None:
            logger.info("✅ 收斂性分析器測試通過")
            return True
        else:
            logger.warning("⚠️  收斂性分析器測試失敗 - 無法生成分析")
            return False
            
    except Exception as e:
        logger.error(f"❌ 收斂性分析器測試失敗: {e}")
        return False

def test_statistical_engine(imports: Dict[str, bool], dependencies: Dict[str, bool]) -> bool:
    """測試統計測試引擎"""
    if not imports.get("statistical_testing", False):
        logger.warning("⚠️  跳過統計測試引擎測試 - 組件不可用")
        return False
    
    if not dependencies.get("scipy", False):
        logger.warning("⚠️  跳過統計測試引擎測試 - SciPy 不可用")
        return False
    
    try:
        logger.info("🧪 測試統計測試引擎...")
        
        from ..analytics import StatisticalTestingEngine
        
        # 創建引擎
        engine = StatisticalTestingEngine({
            "significance_level": 0.05,
            "enable_effect_size": True,
        })
        
        # 生成測試數據
        import numpy as np
        group_a = np.random.normal(45, 10, 50)
        group_b = np.random.normal(50, 10, 50)
        
        # 測試 t-test
        result = engine.perform_t_test(group_a, group_b, "test_comparison")
        
        if result is not None and "p_value" in result:
            logger.info("✅ 統計測試引擎測試通過")
            return True
        else:
            logger.warning("⚠️  統計測試引擎測試失敗 - 無法執行測試")
            return False
            
    except Exception as e:
        logger.error(f"❌ 統計測試引擎測試失敗: {e}")
        return False

def test_visualization_engine(imports: Dict[str, bool]) -> bool:
    """測試視覺化引擎"""
    if not imports.get("visualization_engine", False):
        logger.warning("⚠️  跳過視覺化引擎測試 - 組件不可用")
        return False
    
    try:
        logger.info("🧪 測試視覺化引擎...")
        
        from ..analytics import VisualizationEngine
        import tempfile
        
        # 創建引擎
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = VisualizationEngine({
                "output_directory": temp_dir,
                "default_theme": "academic",
            })
            
            # 生成測試數據
            import numpy as np
            episodes = list(range(50))
            rewards = np.linspace(-30, 40, 50) + np.random.normal(0, 5, 50)
            
            test_data = {
                "episodes": episodes,
                "DQN": rewards.tolist(),
            }
            
            # 測試學習曲線圖
            result = engine.create_learning_curve_plot(
                test_data,
                title="Test Learning Curve",
                filename="test_curve"
            )
            
            if result is not None and result.get("success", False):
                logger.info("✅ 視覺化引擎測試通過")
                return True
            else:
                logger.warning("⚠️  視覺化引擎測試失敗 - 無法生成圖表")
                return False
                
    except Exception as e:
        logger.error(f"❌ 視覺化引擎測試失敗: {e}")
        return False

def test_academic_exporter(imports: Dict[str, bool]) -> bool:
    """測試學術數據匯出器"""
    if not imports.get("academic_exporter", False):
        logger.warning("⚠️  跳過學術數據匯出器測試 - 組件不可用")
        return False
    
    try:
        logger.info("🧪 測試學術數據匯出器...")
        
        from ..analytics import AcademicDataExporter
        import tempfile
        
        # 創建匯出器
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = AcademicDataExporter({
                "export_directory": temp_dir,
                "default_format": "json",
            })
            
            # 測試數據
            test_data = {
                "experiment_metadata": {
                    "title": "Test Experiment",
                    "date": datetime.now().isoformat(),
                },
                "results": {
                    "algorithm_performance": [45, 50, 47],
                },
            }
            
            # 測試 JSON 匯出
            result = exporter.export_to_json(test_data, "test_export.json")
            
            if result is not None and result.get("success", False):
                logger.info("✅ 學術數據匯出器測試通過")
                return True
            else:
                logger.warning("⚠️  學術數據匯出器測試失敗 - 無法匯出數據")
                return False
                
    except Exception as e:
        logger.error(f"❌ 學術數據匯出器測試失敗: {e}")
        return False

def test_api_routes(imports: Dict[str, bool]) -> bool:
    """測試 API 路由"""
    if not imports.get("phase3_api", False):
        logger.warning("⚠️  跳過 API 路由測試 - API 不可用")
        return False
    
    try:
        logger.info("🧪 測試 API 路由...")
        
        from ..api.phase_3_api import router
        
        # 檢查路由數量
        route_count = len(router.routes)
        
        if route_count > 0:
            logger.info(f"✅ API 路由測試通過 - 發現 {route_count} 個端點")
            
            # 列出主要端點
            main_endpoints = [
                "/health",
                "/status", 
                "/explain/decision",
                "/analyze/convergence",
                "/test/statistical",
                "/visualize",
                "/export/academic",
            ]
            
            available_paths = [route.path for route in router.routes]
            matched_endpoints = [endpoint for endpoint in main_endpoints 
                               if any(endpoint in path for path in available_paths)]
            
            logger.info(f"📊 可用端點: {len(matched_endpoints)}/{len(main_endpoints)}")
            
            return True
        else:
            logger.warning("⚠️  API 路由測試失敗 - 沒有發現端點")
            return False
            
    except Exception as e:
        logger.error(f"❌ API 路由測試失敗: {e}")
        return False

def generate_report(
    imports: Dict[str, bool],
    dependencies: Dict[str, bool],
    component_tests: Dict[str, bool]
) -> Dict[str, Any]:
    """生成詳細報告"""
    
    total_imports = len(imports)
    successful_imports = sum(imports.values())
    import_rate = successful_imports / total_imports * 100 if total_imports > 0 else 0
    
    total_deps = len(dependencies)
    successful_deps = sum(dependencies.values())
    dependency_rate = successful_deps / total_deps * 100 if total_deps > 0 else 0
    
    total_tests = len(component_tests)
    successful_tests = sum(component_tests.values())
    test_rate = successful_tests / total_tests * 100 if total_tests > 0 else 0
    
    # 計算總體可用性
    overall_score = (import_rate * 0.5 + dependency_rate * 0.2 + test_rate * 0.3)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "phase": "Phase 3: Decision Transparency & Visualization",
        "summary": {
            "overall_score": overall_score,
            "status": "excellent" if overall_score >= 90 else 
                     "good" if overall_score >= 70 else
                     "fair" if overall_score >= 50 else
                     "poor",
        },
        "imports": {
            "total": total_imports,
            "successful": successful_imports,
            "rate": import_rate,
            "details": imports,
        },
        "dependencies": {
            "total": total_deps,
            "successful": successful_deps,
            "rate": dependency_rate,
            "details": dependencies,
        },
        "component_tests": {
            "total": total_tests,
            "successful": successful_tests,
            "rate": test_rate,
            "details": component_tests,
        },
        "capabilities": {
            "decision_explanation": component_tests.get("explainability_engine", False),
            "convergence_analysis": component_tests.get("convergence_analyzer", False),
            "statistical_testing": component_tests.get("statistical_engine", False),
            "visualization": component_tests.get("visualization_engine", False),
            "academic_export": component_tests.get("academic_exporter", False),
            "api_access": component_tests.get("api_routes", False),
        },
        "recommendations": [],
    }
    
    # 生成建議
    if not dependencies.get("scipy", False):
        report["recommendations"].append("安裝 SciPy 以啟用完整的統計測試功能")
    
    if not dependencies.get("matplotlib", False):
        report["recommendations"].append("安裝 Matplotlib 以啟用靜態視覺化功能")
    
    if not dependencies.get("plotly", False):
        report["recommendations"].append("安裝 Plotly 以啟用互動視覺化功能")
    
    if overall_score < 70:
        report["recommendations"].append("建議檢查 Phase 3 組件的安裝和配置")
    
    return report

def main():
    """主函數"""
    start_time = time.time()
    
    print("🚀 Phase 3 決策透明化與視覺化功能快速驗證")
    print("=" * 60)
    
    # 1. 檢查導入
    imports = check_imports()
    
    # 2. 檢查依賴項
    dependencies = check_dependencies()
    
    # 3. 測試核心組件
    component_tests = {}
    component_tests["explainability_engine"] = test_explainability_engine(imports)
    component_tests["convergence_analyzer"] = test_convergence_analyzer(imports)
    component_tests["statistical_engine"] = test_statistical_engine(imports, dependencies)
    component_tests["visualization_engine"] = test_visualization_engine(imports)
    component_tests["academic_exporter"] = test_academic_exporter(imports)
    component_tests["api_routes"] = test_api_routes(imports)
    
    # 4. 生成報告
    report = generate_report(imports, dependencies, component_tests)
    
    duration = time.time() - start_time
    
    # 5. 顯示結果
    print("\n" + "=" * 60)
    print("📊 Phase 3 功能驗證報告")
    print("=" * 60)
    
    print(f"⏱️  驗證時間: {duration:.2f} 秒")
    print(f"🎯 總體評分: {report['summary']['overall_score']:.1f}/100")
    print(f"📊 狀態: {report['summary']['status'].upper()}")
    
    print(f"\n📦 組件導入: {report['imports']['successful']}/{report['imports']['total']} ({report['imports']['rate']:.1f}%)")
    for component, available in imports.items():
        status = "✅" if available else "❌"
        print(f"  {status} {component}")
    
    print(f"\n🔧 依賴項: {report['dependencies']['successful']}/{report['dependencies']['total']} ({report['dependencies']['rate']:.1f}%)")
    for dep, available in dependencies.items():
        status = "✅" if available else "⚠️ "
        print(f"  {status} {dep}")
    
    print(f"\n🧪 功能測試: {report['component_tests']['successful']}/{report['component_tests']['total']} ({report['component_tests']['rate']:.1f}%)")
    for test, passed in component_tests.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {test}")
    
    print(f"\n🎯 可用功能:")
    for capability, available in report['capabilities'].items():
        status = "✅" if available else "❌"
        print(f"  {status} {capability}")
    
    if report['recommendations']:
        print(f"\n💡 建議:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
    
    print("\n" + "=" * 60)
    
    if report['summary']['overall_score'] >= 70:
        print("🎉 Phase 3 功能驗證通過！系統可以開始決策透明化與視覺化工作。")
        return 0
    else:
        print("⚠️  Phase 3 功能驗證未完全通過，建議檢查上述問題。")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  驗證被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 驗證過程中發生錯誤: {e}")
        sys.exit(1)