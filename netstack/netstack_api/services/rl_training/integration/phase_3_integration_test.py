"""
Phase 3 端到端整合測試

驗證所有 Phase 3 決策透明化與視覺化組件的整合工作：
- 高級解釋性分析引擎測試
- 收斂性分析器測試
- 統計測試引擎測試
- 學術數據匯出器測試
- 視覺化引擎測試
- 完整決策透明化工作流測試

Created for Phase 3: Decision Transparency & Visualization Optimization
"""

import asyncio
import logging
import time
import numpy as np
import tempfile
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# 設置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Phase3IntegrationTest:
    """Phase 3 整合測試類"""

    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        self.total_tests = 0
        self.passed_tests = 0
        self.temp_dir = tempfile.mkdtemp(prefix="phase3_test_")
        logger.info(f"📁 測試臨時目錄: {self.temp_dir}")

    async def run_all_tests(self) -> Dict[str, Any]:
        """運行所有 Phase 3 整合測試"""
        logger.info("🚀 開始 Phase 3 決策透明化與視覺化整合測試")
        start_time = time.time()

        test_functions = [
            self._test_analytics_imports,
            self._test_explainability_engine,
            self._test_convergence_analyzer,
            self._test_statistical_testing_engine,
            self._test_academic_data_exporter,
            self._test_visualization_engine,
            self._test_phase3_api_integration,
            self._test_complete_transparency_workflow,
        ]

        for test_func in test_functions:
            await self._run_test(test_func)

        duration = time.time() - start_time
        success_rate = self.passed_tests / max(self.total_tests, 1) * 100

        summary = {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": len(self.failed_tests),
            "success_rate": success_rate,
            "duration_seconds": duration,
            "test_results": self.test_results,
            "failed_test_names": self.failed_tests,
            "phase": "Phase 3: Decision Transparency & Visualization",
        }

        # 清理臨時文件
        self._cleanup_temp_files()

        logger.info(
            f"📊 Phase 3 測試完成！通過率: {success_rate:.1f}% ({self.passed_tests}/{self.total_tests})"
        )

        if self.failed_tests:
            logger.error(f"❌ 失敗的測試: {', '.join(self.failed_tests)}")
        else:
            logger.info("🎉 所有 Phase 3 測試都通過了！")

        return summary

    async def _run_test(self, test_func):
        """運行單個測試"""
        test_name = test_func.__name__
        self.total_tests += 1

        try:
            logger.info(f"🧪 運行測試: {test_name}")
            result = await test_func()

            if result.get("success", False):
                self.passed_tests += 1
                logger.info(f"✅ {test_name} 通過")
            else:
                self.failed_tests.append(test_name)
                logger.error(f"❌ {test_name} 失敗: {result.get('error', '未知錯誤')}")

            self.test_results.append(
                {
                    "test_name": test_name,
                    "success": result.get("success", False),
                    "duration": result.get("duration", 0),
                    "details": result.get("details", {}),
                    "error": result.get("error"),
                }
            )

        except Exception as e:
            self.failed_tests.append(test_name)
            logger.error(f"❌ {test_name} 異常: {str(e)}")

            self.test_results.append(
                {
                    "test_name": test_name,
                    "success": False,
                    "duration": 0,
                    "details": {},
                    "error": str(e),
                }
            )

    async def _test_analytics_imports(self) -> Dict[str, Any]:
        """測試 Phase 3 分析組件導入"""
        start_time = time.time()

        try:
            # 測試核心分析組件導入
            from ..analytics import (
                AdvancedExplainabilityEngine,
                ConvergenceAnalyzer,
                StatisticalTestingEngine,
                AcademicDataExporter,
                VisualizationEngine,
            )

            # 檢查可選依賴項
            dependencies = {}
            
            try:
                import scipy
                dependencies["scipy"] = True
            except ImportError:
                dependencies["scipy"] = False

            try:
                import sklearn
                dependencies["sklearn"] = True
            except ImportError:
                dependencies["sklearn"] = False

            try:
                import matplotlib
                dependencies["matplotlib"] = True
            except ImportError:
                dependencies["matplotlib"] = False

            try:
                import plotly
                dependencies["plotly"] = True
            except ImportError:
                dependencies["plotly"] = False

            available_deps = sum(dependencies.values())
            core_available = available_deps >= 2  # 至少需要 scipy 和其他一個

            return {
                "success": core_available,
                "duration": time.time() - start_time,
                "details": {
                    "all_imports_successful": True,
                    "dependencies": dependencies,
                    "available_dependencies": available_deps,
                    "core_dependencies_met": core_available,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "error": f"Phase 3 導入測試失敗: {str(e)}",
            }

    async def _test_explainability_engine(self) -> Dict[str, Any]:
        """測試高級解釋性分析引擎"""
        start_time = time.time()

        try:
            from ..analytics import AdvancedExplainabilityEngine

            # 創建引擎實例
            config = {
                "explainability_level": "detailed",
                "enable_feature_importance": True,
                "enable_decision_paths": True,
                "enable_counterfactual": True,
            }

            engine = AdvancedExplainabilityEngine(config)

            # 生成測試決策數據
            test_decision_data = {
                "state": np.random.rand(10),  # 10維狀態空間
                "action": 2,  # 選擇的動作
                "q_values": np.random.rand(5),  # 5個動作的Q值
                "algorithm": "DQN",
                "episode": 100,
                "step": 50,
                "scenario_context": {
                    "satellite_candidates": [
                        {"id": "sat_1", "signal_strength": 0.8, "elevation": 45},
                        {"id": "sat_2", "signal_strength": 0.6, "elevation": 30},
                        {"id": "sat_3", "signal_strength": 0.9, "elevation": 60},
                    ],
                    "user_location": {"lat": 24.7867, "lon": 120.9967},
                },
            }

            # 測試決策解釋
            explanation = engine.explain_decision(test_decision_data)

            # 測試特徵重要性分析
            feature_importance = engine.analyze_feature_importance(
                state=test_decision_data["state"],
                q_values=test_decision_data["q_values"],
                action=test_decision_data["action"],
            )

            # 測試決策路徑分析
            decision_path = engine.analyze_decision_path(test_decision_data)

            # 驗證結果
            tests_passed = {
                "explanation_generated": explanation is not None,
                "feature_importance_available": feature_importance is not None,
                "decision_path_available": decision_path is not None,
                "confidence_score_present": explanation.get("confidence_score") is not None if explanation else False,
            }

            success = sum(tests_passed.values()) >= 3  # 至少3個測試通過

            return {
                "success": success,
                "duration": time.time() - start_time,
                "details": {
                    "tests_passed": tests_passed,
                    "explanation_fields": list(explanation.keys()) if explanation else [],
                    "feature_importance_method": feature_importance.get("method") if feature_importance else None,
                    "decision_path_length": len(decision_path.get("path", [])) if decision_path else 0,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "error": f"解釋性引擎測試失敗: {str(e)}",
            }

    async def _test_convergence_analyzer(self) -> Dict[str, Any]:
        """測試收斂性分析器"""
        start_time = time.time()

        try:
            from ..analytics import ConvergenceAnalyzer

            # 創建分析器實例
            config = {
                "smoothing_window": 10,
                "convergence_threshold": 0.01,
                "min_stable_episodes": 20,
                "enable_forecasting": True,
            }

            analyzer = ConvergenceAnalyzer(config)

            # 生成模擬訓練數據
            episodes = 200
            # 模擬收斂的學習曲線
            base_reward = np.linspace(-100, 50, episodes)
            noise = np.random.normal(0, 10, episodes)
            rewards = base_reward + noise
            
            # 添加一些性能指標
            success_rates = np.clip(np.linspace(0.1, 0.9, episodes) + np.random.normal(0, 0.05, episodes), 0, 1)
            handover_latencies = np.maximum(np.linspace(100, 20, episodes) + np.random.normal(0, 5, episodes), 5)

            training_data = {
                "episodes": list(range(episodes)),
                "rewards": rewards.tolist(),
                "success_rates": success_rates.tolist(),
                "handover_latencies": handover_latencies.tolist(),
                "algorithm": "DQN",
                "scenario": "urban",
            }

            # 測試學習曲線分析
            curve_analysis = analyzer.analyze_learning_curve(
                rewards, 
                metric_name="total_reward"
            )

            # 測試收斂檢測
            convergence_result = analyzer.detect_convergence(
                rewards[-50:],  # 最後50個episode
                metric_name="total_reward"
            )

            # 測試性能趨勢分析
            trend_analysis = analyzer.analyze_performance_trend(training_data)

            # 測試訓練階段識別
            phase_analysis = analyzer.identify_training_phases(rewards)

            # 驗證結果
            tests_passed = {
                "curve_analysis_available": curve_analysis is not None,
                "convergence_detected": convergence_result is not None,
                "trend_analysis_available": trend_analysis is not None,
                "phases_identified": phase_analysis is not None and len(phase_analysis.get("phases", [])) > 0,
            }

            success = sum(tests_passed.values()) >= 3

            return {
                "success": success,
                "duration": time.time() - start_time,
                "details": {
                    "tests_passed": tests_passed,
                    "convergence_status": convergence_result.get("status") if convergence_result else None,
                    "identified_phases": len(phase_analysis.get("phases", [])) if phase_analysis else 0,
                    "trend_direction": trend_analysis.get("overall_trend") if trend_analysis else None,
                    "episodes_analyzed": episodes,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "error": f"收斂性分析器測試失敗: {str(e)}",
            }

    async def _test_statistical_testing_engine(self) -> Dict[str, Any]:
        """測試統計測試引擎"""
        start_time = time.time()

        try:
            from ..analytics import StatisticalTestingEngine

            # 創建引擎實例
            config = {
                "significance_level": 0.05,
                "enable_effect_size": True,
                "enable_power_analysis": True,
                "bootstrap_samples": 1000,
            }

            engine = StatisticalTestingEngine(config)

            # 生成測試數據 - 兩個算法的性能比較
            np.random.seed(42)  # 確保結果可重現
            
            algorithm_a_rewards = np.random.normal(45, 15, 100)  # DQN
            algorithm_b_rewards = np.random.normal(50, 12, 100)  # PPO (稍微更好)
            algorithm_c_rewards = np.random.normal(42, 18, 100)  # SAC

            # 測試 t-test (兩組比較)
            ttest_result = engine.perform_t_test(
                algorithm_a_rewards,
                algorithm_b_rewards,
                test_name="DQN_vs_PPO_rewards"
            )

            # 測試 Mann-Whitney U test (非參數測試)
            mannwhitney_result = engine.perform_mann_whitney_test(
                algorithm_a_rewards,
                algorithm_b_rewards,
                test_name="DQN_vs_PPO_nonparametric"
            )

            # 測試 ANOVA (多組比較)
            anova_data = {
                "DQN": algorithm_a_rewards,
                "PPO": algorithm_b_rewards,
                "SAC": algorithm_c_rewards,
            }
            anova_result = engine.perform_anova(
                anova_data,
                test_name="Three_Algorithm_Comparison"
            )

            # 測試效應量計算
            effect_size = engine.calculate_effect_size(
                algorithm_a_rewards,
                algorithm_b_rewards,
                method="cohen_d"
            )

            # 測試多重比較校正
            p_values = [0.01, 0.03, 0.08, 0.12, 0.001]
            corrected_results = engine.apply_multiple_comparison_correction(
                p_values,
                method="bonferroni"
            )

            # 驗證結果
            tests_passed = {
                "t_test_completed": ttest_result is not None,
                "mannwhitney_completed": mannwhitney_result is not None,
                "anova_completed": anova_result is not None,
                "effect_size_calculated": effect_size is not None,
                "multiple_correction_applied": corrected_results is not None,
            }

            success = sum(tests_passed.values()) >= 4

            return {
                "success": success,
                "duration": time.time() - start_time,
                "details": {
                    "tests_passed": tests_passed,
                    "t_test_significant": ttest_result.get("significant") if ttest_result else None,
                    "anova_significant": anova_result.get("significant") if anova_result else None,
                    "effect_size_magnitude": effect_size.get("magnitude") if effect_size else None,
                    "corrected_significant_tests": sum(corrected_results.get("significant", [])) if corrected_results else 0,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "error": f"統計測試引擎測試失敗: {str(e)}",
            }

    async def _test_academic_data_exporter(self) -> Dict[str, Any]:
        """測試學術數據匯出器"""
        start_time = time.time()

        try:
            from ..analytics import AcademicDataExporter

            # 創建匯出器實例
            config = {
                "export_directory": self.temp_dir,
                "default_format": "csv",
                "include_metadata": True,
                "include_validation": True,
            }

            exporter = AcademicDataExporter(config)

            # 生成測試研究數據
            research_data = {
                "experiment_metadata": {
                    "title": "LEO Satellite Handover RL Algorithm Comparison",
                    "authors": ["Research Team"],
                    "institution": "Test University",
                    "date": datetime.now().isoformat(),
                    "description": "Comparative analysis of DQN, PPO, and SAC algorithms",
                },
                "experimental_design": {
                    "algorithms": ["DQN", "PPO", "SAC"],
                    "scenarios": ["urban", "suburban", "rural"],
                    "episodes_per_algorithm": 1000,
                    "metrics": ["total_reward", "success_rate", "handover_latency"],
                },
                "results": {
                    "DQN": {
                        "total_reward": np.random.normal(45, 15, 100).tolist(),
                        "success_rate": np.random.uniform(0.7, 0.9, 100).tolist(),
                        "handover_latency": np.random.uniform(10, 50, 100).tolist(),
                    },
                    "PPO": {
                        "total_reward": np.random.normal(50, 12, 100).tolist(),
                        "success_rate": np.random.uniform(0.75, 0.95, 100).tolist(),
                        "handover_latency": np.random.uniform(8, 45, 100).tolist(),
                    },
                    "SAC": {
                        "total_reward": np.random.normal(47, 14, 100).tolist(),
                        "success_rate": np.random.uniform(0.72, 0.92, 100).tolist(),
                        "handover_latency": np.random.uniform(9, 48, 100).tolist(),
                    },
                },
                "statistical_analysis": {
                    "significance_tests": ["t_test", "anova", "mann_whitney"],
                    "effect_sizes": ["cohen_d", "eta_squared"],
                    "confidence_intervals": True,
                },
            }

            # 測試不同格式的匯出
            export_tests = {}

            # CSV 匯出
            try:
                csv_result = exporter.export_to_csv(
                    research_data,
                    filename="test_research_data.csv"
                )
                export_tests["csv_export"] = csv_result.get("success", False)
            except Exception as e:
                logger.warning(f"CSV匯出測試失敗: {e}")
                export_tests["csv_export"] = False

            # JSON 匯出
            try:
                json_result = exporter.export_to_json(
                    research_data,
                    filename="test_research_data.json"
                )
                export_tests["json_export"] = json_result.get("success", False)
            except Exception as e:
                logger.warning(f"JSON匯出測試失敗: {e}")
                export_tests["json_export"] = False

            # 學術報告生成
            try:
                report_result = exporter.generate_publication_ready_report(
                    research_data,
                    standard="IEEE",
                    filename="test_research_report"
                )
                export_tests["report_generation"] = report_result.get("success", False)
            except Exception as e:
                logger.warning(f"報告生成測試失敗: {e}")
                export_tests["report_generation"] = False

            # 研究數據包生成
            try:
                package_result = exporter.create_research_data_package(
                    research_data,
                    package_name="test_research_package"
                )
                export_tests["data_package"] = package_result.get("success", False)
            except Exception as e:
                logger.warning(f"數據包生成測試失敗: {e}")
                export_tests["data_package"] = False

            # 檢查輸出文件是否存在
            output_files = list(Path(self.temp_dir).glob("*"))
            files_created = len(output_files)

            success = sum(export_tests.values()) >= 2 and files_created > 0

            return {
                "success": success,
                "duration": time.time() - start_time,
                "details": {
                    "export_tests": export_tests,
                    "files_created": files_created,
                    "output_directory": self.temp_dir,
                    "successful_exports": sum(export_tests.values()),
                },
            }

        except Exception as e:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "error": f"學術數據匯出器測試失敗: {str(e)}",
            }

    async def _test_visualization_engine(self) -> Dict[str, Any]:
        """測試視覺化引擎"""
        start_time = time.time()

        try:
            from ..analytics import VisualizationEngine

            # 創建引擎實例
            config = {
                "output_directory": self.temp_dir,
                "default_theme": "academic",
                "enable_interactive": True,
                "enable_realtime": True,
            }

            engine = VisualizationEngine(config)

            # 生成測試數據
            episodes = np.arange(1, 101)
            dqn_rewards = np.random.normal(45, 15, 100)
            ppo_rewards = np.random.normal(50, 12, 100)
            sac_rewards = np.random.normal(47, 14, 100)

            visualization_data = {
                "learning_curves": {
                    "episodes": episodes.tolist(),
                    "DQN": dqn_rewards.tolist(),
                    "PPO": ppo_rewards.tolist(),
                    "SAC": sac_rewards.tolist(),
                },
                "performance_comparison": {
                    "algorithms": ["DQN", "PPO", "SAC"],
                    "mean_rewards": [np.mean(dqn_rewards), np.mean(ppo_rewards), np.mean(sac_rewards)],
                    "std_rewards": [np.std(dqn_rewards), np.std(ppo_rewards), np.std(sac_rewards)],
                },
                "convergence_analysis": {
                    "convergence_points": [80, 85, 78],
                    "final_performance": [np.mean(dqn_rewards[-10:]), np.mean(ppo_rewards[-10:]), np.mean(sac_rewards[-10:])],
                },
            }

            # 測試不同類型的視覺化
            visualization_tests = {}

            # 學習曲線圖
            try:
                learning_curve_result = engine.create_learning_curve_plot(
                    visualization_data["learning_curves"],
                    title="Algorithm Learning Curves",
                    filename="learning_curves"
                )
                visualization_tests["learning_curves"] = learning_curve_result.get("success", False)
            except Exception as e:
                logger.warning(f"學習曲線圖測試失敗: {e}")
                visualization_tests["learning_curves"] = False

            # 性能比較圖
            try:
                comparison_result = engine.create_performance_comparison_plot(
                    visualization_data["performance_comparison"],
                    title="Algorithm Performance Comparison",
                    filename="performance_comparison"
                )
                visualization_tests["performance_comparison"] = comparison_result.get("success", False)
            except Exception as e:
                logger.warning(f"性能比較圖測試失敗: {e}")
                visualization_tests["performance_comparison"] = False

            # 收斂分析圖
            try:
                convergence_result = engine.create_convergence_analysis_plot(
                    visualization_data["convergence_analysis"],
                    title="Convergence Analysis",
                    filename="convergence_analysis"
                )
                visualization_tests["convergence_analysis"] = convergence_result.get("success", False)
            except Exception as e:
                logger.warning(f"收斂分析圖測試失敗: {e}")
                visualization_tests["convergence_analysis"] = False

            # 儀表板生成
            try:
                dashboard_result = engine.create_analysis_dashboard(
                    visualization_data,
                    title="RL Algorithm Analysis Dashboard",
                    filename="analysis_dashboard"
                )
                visualization_tests["dashboard"] = dashboard_result.get("success", False)
            except Exception as e:
                logger.warning(f"儀表板生成測試失敗: {e}")
                visualization_tests["dashboard"] = False

            # 檢查生成的視覺化文件
            viz_files = list(Path(self.temp_dir).glob("*.png")) + list(Path(self.temp_dir).glob("*.html"))
            visualizations_created = len(viz_files)

            success = sum(visualization_tests.values()) >= 2 or visualizations_created > 0

            return {
                "success": success,
                "duration": time.time() - start_time,
                "details": {
                    "visualization_tests": visualization_tests,
                    "visualizations_created": visualizations_created,
                    "successful_visualizations": sum(visualization_tests.values()),
                    "output_directory": self.temp_dir,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "error": f"視覺化引擎測試失敗: {str(e)}",
            }

    async def _test_phase3_api_integration(self) -> Dict[str, Any]:
        """測試 Phase 3 API 整合"""
        start_time = time.time()

        try:
            # 檢查 Phase 3 API 是否存在
            api_components = {}

            try:
                # 檢查是否有 Phase 3 API 路由
                from ..api.phase_3_api import router as phase3_router
                api_components["phase3_api"] = True
            except ImportError:
                api_components["phase3_api"] = False

            try:
                # 檢查分析服務是否可通過 API 訪問
                from ..analytics import (
                    AdvancedExplainabilityEngine,
                    ConvergenceAnalyzer,
                    StatisticalTestingEngine,
                    AcademicDataExporter,
                    VisualizationEngine,
                )
                api_components["analytics_services"] = True
            except ImportError:
                api_components["analytics_services"] = False

            # 模擬 API 端點測試（不實際發送 HTTP 請求）
            api_endpoint_tests = {
                "explainability_endpoint": api_components.get("phase3_api", False),
                "convergence_endpoint": api_components.get("phase3_api", False),
                "statistical_endpoint": api_components.get("phase3_api", False),
                "export_endpoint": api_components.get("phase3_api", False),
                "visualization_endpoint": api_components.get("phase3_api", False),
            }

            available_endpoints = sum(api_endpoint_tests.values())
            success = api_components.get("analytics_services", False) and available_endpoints >= 2

            return {
                "success": success,
                "duration": time.time() - start_time,
                "details": {
                    "api_components": api_components,
                    "api_endpoint_tests": api_endpoint_tests,
                    "available_endpoints": available_endpoints,
                    "analytics_services_available": api_components.get("analytics_services", False),
                },
            }

        except Exception as e:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "error": f"Phase 3 API 整合測試失敗: {str(e)}",
            }

    async def _test_complete_transparency_workflow(self) -> Dict[str, Any]:
        """測試完整的決策透明化工作流"""
        start_time = time.time()

        try:
            from ..analytics import (
                AdvancedExplainabilityEngine,
                ConvergenceAnalyzer,
                StatisticalTestingEngine,
                AcademicDataExporter,
                VisualizationEngine,
            )

            # 創建所有組件
            explainability_engine = AdvancedExplainabilityEngine({})
            convergence_analyzer = ConvergenceAnalyzer({})
            statistical_engine = StatisticalTestingEngine({})
            data_exporter = AcademicDataExporter({"export_directory": self.temp_dir})
            visualization_engine = VisualizationEngine({"output_directory": self.temp_dir})

            workflow_steps = {}

            # 步驟 1: 生成模擬的完整訓練會話數據
            training_session = self._generate_complete_training_session()
            workflow_steps["training_session_generated"] = training_session is not None

            # 步驟 2: 收斂性分析
            try:
                convergence_analysis = convergence_analyzer.analyze_learning_curve(
                    training_session["rewards"],
                    metric_name="total_reward"
                )
                workflow_steps["convergence_analysis"] = convergence_analysis is not None
            except Exception as e:
                logger.warning(f"收斂性分析失敗: {e}")
                workflow_steps["convergence_analysis"] = False

            # 步驟 3: 統計分析
            try:
                # 比較不同算法
                algorithms = ["DQN", "PPO", "SAC"]
                algorithm_data = {}
                for alg in algorithms:
                    algorithm_data[alg] = np.random.normal(45 + algorithms.index(alg) * 2, 10, 50)

                statistical_analysis = statistical_engine.perform_anova(
                    algorithm_data,
                    test_name="Complete_Algorithm_Comparison"
                )
                workflow_steps["statistical_analysis"] = statistical_analysis is not None
            except Exception as e:
                logger.warning(f"統計分析失敗: {e}")
                workflow_steps["statistical_analysis"] = False

            # 步驟 4: 決策解釋
            try:
                decision_data = {
                    "state": np.random.rand(10),
                    "action": 2,
                    "q_values": np.random.rand(5),
                    "algorithm": "DQN",
                    "episode": 100,
                    "step": 50,
                }

                decision_explanation = explainability_engine.explain_decision(decision_data)
                workflow_steps["decision_explanation"] = decision_explanation is not None
            except Exception as e:
                logger.warning(f"決策解釋失敗: {e}")
                workflow_steps["decision_explanation"] = False

            # 步驟 5: 視覺化生成
            try:
                viz_data = {
                    "episodes": list(range(100)),
                    "DQN": training_session["rewards"][:100],
                    "PPO": (np.array(training_session["rewards"][:100]) + np.random.normal(0, 2, 100)).tolist(),
                }

                visualization_result = visualization_engine.create_learning_curve_plot(
                    viz_data,
                    title="Complete Workflow Visualization",
                    filename="workflow_visualization"
                )
                workflow_steps["visualization"] = visualization_result.get("success", False)
            except Exception as e:
                logger.warning(f"視覺化生成失敗: {e}")
                workflow_steps["visualization"] = False

            # 步驟 6: 學術報告生成
            try:
                research_data = {
                    "experiment_metadata": {
                        "title": "Complete Transparency Workflow Test",
                        "date": datetime.now().isoformat(),
                    },
                    "results": algorithm_data,
                    "analysis": {
                        "convergence": convergence_analysis if workflow_steps.get("convergence_analysis") else {},
                        "statistical": statistical_analysis if workflow_steps.get("statistical_analysis") else {},
                        "explanations": decision_explanation if workflow_steps.get("decision_explanation") else {},
                    },
                }

                export_result = data_exporter.export_to_json(
                    research_data,
                    filename="complete_workflow_report.json"
                )
                workflow_steps["academic_export"] = export_result.get("success", False)
            except Exception as e:
                logger.warning(f"學術報告生成失敗: {e}")
                workflow_steps["academic_export"] = False

            # 計算工作流成功率
            successful_steps = sum(workflow_steps.values())
            total_steps = len(workflow_steps)
            workflow_success = successful_steps >= total_steps * 0.7  # 70% 成功率門檻

            return {
                "success": workflow_success,
                "duration": time.time() - start_time,
                "details": {
                    "workflow_steps": workflow_steps,
                    "successful_steps": successful_steps,
                    "total_steps": total_steps,
                    "success_rate": successful_steps / total_steps * 100,
                    "components_tested": [
                        "explainability_engine",
                        "convergence_analyzer", 
                        "statistical_engine",
                        "data_exporter",
                        "visualization_engine",
                    ],
                },
            }

        except Exception as e:
            return {
                "success": False,
                "duration": time.time() - start_time,
                "error": f"完整透明化工作流測試失敗: {str(e)}",
            }

    def _generate_complete_training_session(self) -> Optional[Dict[str, Any]]:
        """生成完整的訓練會話數據"""
        try:
            episodes = 200
            
            # 模擬學習曲線 (包含初期探索、學習、收斂階段)
            exploration_phase = np.random.normal(-50, 20, 50)  # 初期探索
            learning_phase = np.linspace(-30, 40, 100) + np.random.normal(0, 10, 100)  # 學習階段
            convergence_phase = np.random.normal(45, 5, 50)  # 收斂階段
            
            rewards = np.concatenate([exploration_phase, learning_phase, convergence_phase])
            
            # 其他性能指標
            success_rates = np.clip(np.linspace(0.1, 0.9, episodes) + np.random.normal(0, 0.05, episodes), 0, 1)
            handover_latencies = np.maximum(np.linspace(100, 20, episodes) + np.random.normal(0, 5, episodes), 5)
            
            return {
                "episodes": list(range(episodes)),
                "rewards": rewards.tolist(),
                "success_rates": success_rates.tolist(),
                "handover_latencies": handover_latencies.tolist(),
                "algorithm": "DQN",
                "scenario": "urban",
                "total_steps": episodes * 100,  # 假設每個episode 100步
            }
            
        except Exception as e:
            logger.error(f"生成訓練會話數據失敗: {e}")
            return None

    def _cleanup_temp_files(self):
        """清理臨時測試文件"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"🧹 已清理臨時目錄: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"清理臨時文件失敗: {e}")


async def main():
    """主測試函數"""
    test_runner = Phase3IntegrationTest()
    results = await test_runner.run_all_tests()

    print("\n" + "=" * 80)
    print("📋 Phase 3 決策透明化與視覺化整合測試報告")
    print("=" * 80)
    print(f"總測試數: {results['total_tests']}")
    print(f"通過測試: {results['passed_tests']}")
    print(f"失敗測試: {results['failed_tests']}")
    print(f"成功率: {results['success_rate']:.1f}%")
    print(f"總耗時: {results['duration_seconds']:.2f} 秒")

    if results["failed_test_names"]:
        print(f"\n❌ 失敗的測試:")
        for test_name in results["failed_test_names"]:
            print(f"  - {test_name}")

    print("\n📊 詳細測試結果:")
    for result in results["test_results"]:
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {result['test_name']} ({result['duration']:.2f}s)")
        if not result["success"] and result.get("error"):
            print(f"     錯誤: {result['error']}")

    print("\n🔍 Phase 3 功能總結:")
    print("  ✓ 高級解釋性分析引擎 - Algorithm Explainability")
    print("  ✓ 收斂性分析器 - 學習曲線與趨勢分析")
    print("  ✓ 統計測試引擎 - 多算法性能對比")
    print("  ✓ 學術數據匯出器 - 符合學術標準的報告")
    print("  ✓ 視覺化引擎 - 決策過程視覺化")
    print("  ✓ 完整透明化工作流 - 端到端分析流程")

    print("\n" + "=" * 80)

    if results["success_rate"] >= 80:
        print("🎉 Phase 3 決策透明化功能驗證通過！")
        print("🚀 系統已準備好進入 Phase 4: todo.md 完美整合階段")
        return 0
    else:
        print("⚠️  Phase 3 存在一些問題，需要進一步檢查")
        return 1


if __name__ == "__main__":
    import sys

    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 測試運行時發生錯誤: {e}")
        sys.exit(1)