"""
Comprehensive Unit Tests for Stage 4 Optimization Decision Layer

This module provides complete test coverage for all Stage 4 optimization components:
- Stage4OptimizationProcessor
- PoolPlanner
- HandoverOptimizer
- MultiObjectiveOptimizer
- RLExtensionInterface
- ConfigurationManager
- PerformanceMonitor

Test Categories:
- Unit tests for individual components
- Integration tests for component interaction
- Performance and stress tests
- Error handling and recovery tests
- Configuration and validation tests
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import tempfile
import shutil
import time
import json
import yaml
from datetime import datetime, timezone
from typing import Dict, List, Any

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.join(project_root, 'src'))

# Import Stage 4 components
from stages.stage4_optimization.stage4_optimization_processor import Stage4OptimizationProcessor
from stages.stage4_optimization.pool_planner import PoolPlanner, PoolRequirements, SatelliteCandidate
from stages.stage4_optimization.handover_optimizer import HandoverOptimizer, HandoverThresholds
from stages.stage4_optimization.multi_obj_optimizer import MultiObjectiveOptimizer
from stages.stage4_optimization.rl_extension_interface import (
    RLExtensionCoordinator, RLAgentInterface, RLState, RLAction, RLReward,
    RLEnvironmentAdapter, DummyRLAgent
)
from stages.stage4_optimization.config_manager import ConfigurationManager
from stages.stage4_optimization.performance_monitor import PerformanceMonitor, PerformanceMetrics


class TestStage4OptimizationProcessor(unittest.TestCase):
    """測試Stage 4主處理器"""

    def setUp(self):
        """設置測試環境"""
        self.test_config = {
            'optimization_objectives': {
                'signal_quality_weight': 0.4,
                'coverage_weight': 0.3,
                'handover_cost_weight': 0.2,
                'energy_efficiency_weight': 0.1
            },
            'constraints': {
                'min_satellites_per_pool': 3,
                'max_handover_frequency': 5,
                'min_signal_quality': -110,
                'max_latency_ms': 100
            },
            'performance_monitoring': {
                'enable_detailed_metrics': True
            },
            'rl_extension': {
                'rl_enabled': False
            }
        }

        # 創建臨時配置目錄
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_config.yaml')

        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)

        # 使用模擬的配置管理器
        with patch('stages.stage4_optimization.stage4_optimization_processor.ConfigurationManager') as mock_config_manager:
            mock_config_manager.return_value.get_optimization_objectives.return_value = Mock(
                signal_quality_weight=0.4, coverage_weight=0.3,
                handover_cost_weight=0.2, energy_efficiency_weight=0.1
            )
            mock_config_manager.return_value.get_constraints.return_value = Mock(
                min_satellites_per_pool=3, max_handover_frequency=5,
                min_signal_quality=-110, max_latency_ms=100
            )
            mock_config_manager.return_value.get_config.return_value = {}
            mock_config_manager.return_value.get_rl_configuration.return_value = Mock(
                rl_enabled=False, hybrid_mode=True, rl_confidence_threshold=0.7
            )
            mock_config_manager.return_value.get_performance_targets.return_value = Mock()
            mock_config_manager.return_value.config_version = "1.0.0"
            mock_config_manager.return_value.get_configuration_info.return_value = {
                'config_path': self.config_path
            }

            self.processor = Stage4OptimizationProcessor(self.test_config)

    def tearDown(self):
        """清理測試環境"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_processor_initialization(self):
        """測試處理器初始化"""
        self.assertIsNotNone(self.processor)
        self.assertEqual(self.processor.stage_number, 4)
        self.assertIsNotNone(self.processor.pool_planner)
        self.assertIsNotNone(self.processor.handover_optimizer)
        self.assertIsNotNone(self.processor.multi_obj_optimizer)

    def test_process_valid_input(self):
        """測試有效輸入處理"""
        test_input = {
            'signal_quality_data': [
                {
                    'satellite_id': 'sat_001',
                    'constellation': 'starlink',
                    'average_signal_strength': -85.5,
                    'visibility_duration_minutes': 12.5,
                    'elevation_deg': 25.0
                },
                {
                    'satellite_id': 'sat_002',
                    'constellation': 'starlink',
                    'average_signal_strength': -78.2,
                    'visibility_duration_minutes': 15.3,
                    'elevation_deg': 32.0
                }
            ]
        }

        result = self.processor.process(test_input)

        # 驗證輸出結構
        self.assertIn('stage', result)
        self.assertEqual(result['stage'], 'stage4_optimization')
        self.assertIn('optimal_pool', result)
        self.assertIn('handover_strategy', result)
        self.assertIn('optimization_results', result)
        self.assertIn('metadata', result)

        # 驗證元數據
        metadata = result['metadata']
        self.assertIn('processing_time', metadata)
        self.assertIn('optimized_satellites', metadata)
        self.assertEqual(metadata['optimized_satellites'], 2)

    def test_process_empty_input(self):
        """測試空輸入處理"""
        test_input = {'signal_quality_data': []}

        result = self.processor.process(test_input)

        # 應該返回有效結果，即使沒有衛星數據
        self.assertIn('stage', result)
        self.assertEqual(result['metadata']['optimized_satellites'], 0)

    def test_process_invalid_input(self):
        """測試無效輸入處理"""
        test_input = {'invalid_field': 'invalid_data'}

        # 應該觸發錯誤處理
        result = self.processor.process(test_input)

        # 檢查是否有錯誤處理機制
        self.assertIn('stage', result)

    def test_error_handling_and_retry(self):
        """測試錯誤處理和重試機制"""
        # 模擬池規劃失敗
        with patch.object(self.processor.pool_planner, 'plan_dynamic_pool', side_effect=Exception("池規劃失敗")):
            test_input = {
                'signal_quality_data': [
                    {'satellite_id': 'sat_001', 'constellation': 'starlink'}
                ]
            }

            result = self.processor.process(test_input)

            # 應該返回故障恢復結果
            self.assertIn('stage', result)

    def test_performance_metrics_collection(self):
        """測試性能指標收集"""
        test_input = {
            'signal_quality_data': [
                {'satellite_id': 'sat_001', 'constellation': 'starlink', 'average_signal_strength': -85}
            ]
        }

        start_time = time.time()
        result = self.processor.process(test_input)
        end_time = time.time()

        # 驗證性能指標
        self.assertIn('performance_metrics', result['metadata'])
        processing_time = result['metadata']['performance_metrics']['processing_time_seconds']
        self.assertGreater(processing_time, 0)
        self.assertLess(processing_time, end_time - start_time + 1)  # 允許一些誤差


class TestPoolPlanner(unittest.TestCase):
    """測試池規劃器"""

    def setUp(self):
        self.config = {'max_pools': 3, 'min_pool_size': 2}
        self.planner = PoolPlanner(self.config)

        self.test_satellites = [
            SatelliteCandidate(
                satellite_id=f"sat_{i:03d}",
                constellation="starlink",
                signal_strength=-80 - i,
                elevation_deg=20 + i * 2,
                azimuth_deg=i * 10,
                position={'lat': i, 'lon': i * 2, 'alt': 550}
            ) for i in range(10)
        ]

    def test_pool_planning_basic(self):
        """測試基本池規劃"""
        requirements = PoolRequirements(min_satellites_per_pool=2, min_signal_quality=-100)

        result = self.planner.plan_dynamic_pool(self.test_satellites, requirements)

        self.assertIn('planned_pools', result)
        self.assertIsInstance(result['planned_pools'], list)

    def test_coverage_analysis(self):
        """測試覆蓋分析"""
        result = self.planner.analyze_coverage(self.test_satellites[:5])

        self.assertIn('coverage_area', result)
        self.assertIn('satellite_count', result)
        self.assertEqual(result['satellite_count'], 5)

    def test_empty_satellite_list(self):
        """測試空衛星列表"""
        requirements = PoolRequirements(min_satellites_per_pool=1, min_signal_quality=-100)

        result = self.planner.plan_dynamic_pool([], requirements)

        self.assertIn('planned_pools', result)
        self.assertEqual(len(result['planned_pools']), 0)


class TestHandoverOptimizer(unittest.TestCase):
    """測試換手優化器"""

    def setUp(self):
        self.config = {
            'prediction_horizon_minutes': 10,
            'trigger_sensitivity': 'medium'
        }
        self.optimizer = HandoverOptimizer(self.config)

    def test_handover_strategy_optimization(self):
        """測試換手策略優化"""
        current_status = {
            'satellites': [{'satellite_id': 'sat_001', 'signal_strength': -85}],
            'signal_metrics': {'sat_001': {'signal_strength': -85}}
        }

        candidates = [
            {'satellite_id': 'sat_002', 'signal_strength': -75},
            {'satellite_id': 'sat_003', 'signal_strength': -80}
        ]

        result = self.optimizer.optimize_handover_strategy(current_status, candidates)

        self.assertIn('optimized_decisions', result)
        self.assertIsInstance(result['optimized_decisions'], list)

    def test_handover_trigger_determination(self):
        """測試換手觸發確定"""
        gpp_events = [
            {'event_type': 'signal_degradation', 'severity': 'medium'},
            {'event_type': 'elevation_low', 'elevation': 8.0}
        ]

        result = self.optimizer.determine_handover_trigger(gpp_events)

        self.assertIsInstance(result, list)

    def test_timing_optimization(self):
        """測試時機優化"""
        trajectory = [
            {'time': 0, 'elevation': 15, 'signal': -80},
            {'time': 60, 'elevation': 25, 'signal': -75},
            {'time': 120, 'elevation': 20, 'signal': -82}
        ]

        windows = [{'start': 30, 'end': 90, 'priority': 'high'}]

        result = self.optimizer.select_handover_timing(trajectory, windows)

        self.assertIn('optimal_timing', result)


class TestMultiObjectiveOptimizer(unittest.TestCase):
    """測試多目標優化器"""

    def setUp(self):
        self.config = {
            'algorithm': 'nsga2',
            'population_size': 20,
            'max_generations': 10
        }
        self.optimizer = MultiObjectiveOptimizer(self.config)

    def test_multi_objective_optimization(self):
        """測試多目標優化"""
        objectives = {
            'signal_quality': -85.0,
            'coverage_range': 85.0,
            'handover_cost': 8.0,
            'energy_efficiency': 75.0
        }

        constraints = [
            {'name': 'min_satellites', 'type': 'inequality', 'function': 'satellites >= 3'}
        ]

        result = self.optimizer.optimize_multiple_objectives(objectives, constraints)

        self.assertIn('pareto_solutions', result)
        self.assertIn('recommended_solution', result)

    def test_pareto_optimal_finding(self):
        """測試帕累托最優解查找"""
        solution_set = [
            {'objectives': [0.8, 0.6], 'variables': [1, 2]},
            {'objectives': [0.6, 0.8], 'variables': [2, 1]},
            {'objectives': [0.5, 0.5], 'variables': [1.5, 1.5]}
        ]

        result = self.optimizer.find_pareto_optimal(solution_set)

        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_quality_cost_balance(self):
        """測試品質成本平衡"""
        solutions = [
            {'quality_score': 0.9, 'cost_score': 0.3},
            {'quality_score': 0.7, 'cost_score': 0.8},
            {'quality_score': 0.8, 'cost_score': 0.6}
        ]

        result = self.optimizer.balance_quality_cost(solutions)

        self.assertIn('optimal_balance', result)
        self.assertIn('recommendations', result)


class TestRLExtensionInterface(unittest.TestCase):
    """測試RL擴展接口"""

    def setUp(self):
        self.config = {
            'rl_enabled': True,
            'hybrid_mode': True,
            'rl_confidence_threshold': 0.7
        }
        self.coordinator = RLExtensionCoordinator(self.config)
        self.dummy_agent = DummyRLAgent()

    def test_rl_coordinator_initialization(self):
        """測試RL協調器初始化"""
        self.assertTrue(self.coordinator.rl_enabled)
        self.assertTrue(self.coordinator.hybrid_mode)
        self.assertEqual(self.coordinator.rl_confidence_threshold, 0.7)

    def test_agent_registration(self):
        """測試代理註冊"""
        self.coordinator.register_rl_agent(self.dummy_agent)
        self.assertIsNotNone(self.coordinator.rl_agent)

    def test_environment_adapter(self):
        """測試環境適配器"""
        adapter = RLEnvironmentAdapter()

        optimization_data = {
            'candidates': [
                {
                    'satellite_id': 'sat_001',
                    'signal_analysis': {
                        'latitude': 10.0,
                        'longitude': 20.0,
                        'average_signal_strength': -85.0
                    }
                }
            ]
        }

        rl_state = adapter.convert_to_rl_state(optimization_data)

        self.assertIsInstance(rl_state, RLState)
        self.assertEqual(len(rl_state.satellite_positions), 1)
        self.assertEqual(len(rl_state.signal_strengths), 1)

    def test_dummy_agent_action_selection(self):
        """測試示例代理動作選擇"""
        rl_state = RLState(
            satellite_positions=[{'lat': 10, 'lon': 20, 'alt': 550}],
            signal_strengths=[-85.0],
            coverage_metrics={'total_satellites': 1},
            handover_history=[],
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={}
        )

        action = self.dummy_agent.select_action(rl_state)

        self.assertIsInstance(action, RLAction)
        self.assertGreater(action.confidence, 0)
        self.assertLessEqual(action.confidence, 1)

    def test_reward_calculation(self):
        """測試獎勵計算"""
        adapter = RLEnvironmentAdapter()

        previous_state = RLState(
            satellite_positions=[],
            signal_strengths=[-90.0],
            coverage_metrics={'coverage_area': 1000},
            handover_history=[],
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={}
        )

        current_state = RLState(
            satellite_positions=[],
            signal_strengths=[-85.0],
            coverage_metrics={'coverage_area': 1200},
            handover_history=[],
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={}
        )

        action = RLAction(
            action_type="satellite_selection",
            target_satellites=["sat_001"],
            parameters={},
            confidence=0.8
        )

        optimization_results = {'energy_efficiency_score': 0.75}

        reward = adapter.calculate_reward(previous_state, action, current_state, optimization_results)

        self.assertIsInstance(reward, RLReward)
        self.assertIn('signal_quality', reward.component_rewards)


class TestConfigurationManager(unittest.TestCase):
    """測試配置管理器"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'test_config.yaml')

        self.test_config = {
            'optimization_objectives': {
                'signal_quality_weight': 0.4,
                'coverage_weight': 0.3
            },
            'constraints': {
                'min_satellites_per_pool': 5
            }
        }

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_config_loading(self):
        """測試配置載入"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)

        config_manager = ConfigurationManager(self.config_path)

        self.assertIsNotNone(config_manager.current_config)
        self.assertIn('optimization_objectives', config_manager.current_config)

    def test_config_validation(self):
        """測試配置驗證"""
        # 測試有效配置
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)

        config_manager = ConfigurationManager(self.config_path)

        # 應該不拋出異常
        self.assertIsNotNone(config_manager)

    def test_config_update(self):
        """測試配置更新"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)

        config_manager = ConfigurationManager(self.config_path)

        updates = {'signal_quality_weight': 0.5}
        config_manager.update_config('optimization_objectives', updates)

        updated_objectives = config_manager.get_config('optimization_objectives')
        self.assertEqual(updated_objectives['signal_quality_weight'], 0.5)

    def test_config_export_import(self):
        """測試配置導出導入"""
        with open(self.config_path, 'w') as f:
            yaml.dump(self.test_config, f)

        config_manager = ConfigurationManager(self.config_path)

        export_path = os.path.join(self.temp_dir, 'exported_config.yaml')
        config_manager.export_configuration(export_path)

        self.assertTrue(os.path.exists(export_path))

        # 測試導入
        new_config_manager = ConfigurationManager()
        new_config_manager.import_configuration(export_path)


class TestPerformanceMonitor(unittest.TestCase):
    """測試性能監控器"""

    def setUp(self):
        self.config = {
            'enable_detailed_metrics': True,
            'benchmark_targets': {
                'processing_time_max_seconds': 5.0,
                'memory_usage_max_mb': 200,
                'decision_quality_min_score': 0.8
            }
        }
        self.monitor = PerformanceMonitor(self.config)

    def test_process_monitoring(self):
        """測試處理過程監控"""
        # 開始監控
        self.monitor.start_process_monitoring({'test': 'data'})

        # 模擬處理
        time.sleep(0.1)

        # 結束監控
        results = {'test': 'results'}
        metrics = self.monitor.end_process_monitoring(results)

        self.assertIsInstance(metrics, PerformanceMetrics)
        self.assertGreater(metrics.processing_time_seconds, 0)

    def test_error_recording(self):
        """測試錯誤記錄"""
        test_error = ValueError("測試錯誤")
        context = {'operation': 'test_operation'}

        self.monitor.record_error(test_error, context)

        self.assertEqual(self.monitor.total_errors, 1)

    def test_algorithm_benchmarking(self):
        """測試算法基準測試"""
        def test_algorithm(input_data):
            time.sleep(0.01)  # 模擬處理時間
            return {'result': len(input_data)}

        test_inputs = [
            [1, 2, 3],
            [1, 2, 3, 4, 5],
            [1, 2]
        ]

        benchmark = self.monitor.benchmark_algorithm(
            'test_algorithm',
            test_algorithm,
            test_inputs,
            '測試算法基準'
        )

        self.assertEqual(benchmark.algorithm_name, 'test_algorithm')
        self.assertGreater(benchmark.processing_time, 0)
        self.assertEqual(benchmark.success_rate, 1.0)

    def test_performance_summary(self):
        """測試性能摘要"""
        # 模擬一些處理
        self.monitor.start_process_monitoring()
        time.sleep(0.05)
        self.monitor.end_process_monitoring({'test': 'data'})

        summary = self.monitor.get_performance_summary()

        self.assertIn('total_processes', summary)
        self.assertEqual(summary['total_processes'], 1)

    def test_performance_alerts(self):
        """測試性能警報"""
        # 創建一個會觸發警報的指標
        slow_metrics = PerformanceMetrics(
            timestamp=datetime.now(timezone.utc).isoformat(),
            processing_time_seconds=10.0,  # 超過5秒限制
            memory_usage_mb=100.0,
            cpu_usage_percent=50.0,
            satellites_processed=10,
            decision_quality_score=0.9,
            constraint_satisfaction_rate=0.95,
            optimization_effectiveness=0.8,
            algorithm_convergence='excellent',
            error_count=0
        )

        self.monitor._check_performance_alerts(slow_metrics)
        alerts = self.monitor.get_performance_alerts()

        # 應該有處理時間警報
        self.assertGreater(len(alerts), 0)
        self.assertTrue(any(alert['type'] == 'processing_time_exceeded' for alert in alerts))


class TestIntegration(unittest.TestCase):
    """整合測試"""

    def setUp(self):
        """設置整合測試環境"""
        self.temp_dir = tempfile.mkdtemp()

        # 創建測試配置
        self.test_config = {
            'optimization_objectives': {
                'signal_quality_weight': 0.4,
                'coverage_weight': 0.3,
                'handover_cost_weight': 0.2,
                'energy_efficiency_weight': 0.1
            },
            'constraints': {
                'min_satellites_per_pool': 2,
                'max_handover_frequency': 8,
                'min_signal_quality': -110,
                'max_latency_ms': 100
            },
            'performance_monitoring': {
                'enable_detailed_metrics': True,
                'benchmark_targets': {
                    'processing_time_max_seconds': 10.0,
                    'memory_usage_max_mb': 300,
                    'decision_quality_min_score': 0.6
                }
            },
            'rl_extension': {
                'rl_enabled': False  # 禁用RL以簡化測試
            }
        }

    def tearDown(self):
        """清理測試環境"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_end_to_end_processing(self):
        """測試端到端處理"""
        # 創建真實的測試輸入
        test_input = {
            'signal_quality_data': [
                {
                    'satellite_id': 'STARLINK-001',
                    'constellation': 'starlink',
                    'average_signal_strength': -82.5,
                    'visibility_duration_minutes': 18.7,
                    'elevation_deg': 45.0,
                    'azimuth_deg': 120.0,
                    'latitude': 37.7749,
                    'longitude': -122.4194,
                    'altitude_km': 550.0
                },
                {
                    'satellite_id': 'STARLINK-002',
                    'constellation': 'starlink',
                    'average_signal_strength': -79.1,
                    'visibility_duration_minutes': 22.3,
                    'elevation_deg': 52.0,
                    'azimuth_deg': 180.0,
                    'latitude': 37.7849,
                    'longitude': -122.4094,
                    'altitude_km': 550.0
                },
                {
                    'satellite_id': 'ONEWEB-001',
                    'constellation': 'oneweb',
                    'average_signal_strength': -88.3,
                    'visibility_duration_minutes': 15.1,
                    'elevation_deg': 28.0,
                    'azimuth_deg': 60.0,
                    'latitude': 37.7649,
                    'longitude': -122.4294,
                    'altitude_km': 1200.0
                }
            ],
            'gpp_events': [
                {
                    'event_type': 'signal_degradation',
                    'severity': 'medium',
                    'satellite_id': 'STARLINK-001',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            ]
        }

        # 使用模擬配置管理器
        with patch('stages.stage4_optimization.stage4_optimization_processor.ConfigurationManager') as mock_config_manager:
            # 配置模擬
            mock_instance = mock_config_manager.return_value
            mock_instance.get_optimization_objectives.return_value = Mock(
                signal_quality_weight=0.4, coverage_weight=0.3,
                handover_cost_weight=0.2, energy_efficiency_weight=0.1
            )
            mock_instance.get_constraints.return_value = Mock(
                min_satellites_per_pool=2, max_handover_frequency=8,
                min_signal_quality=-110, max_latency_ms=100
            )
            mock_instance.get_config.return_value = {}
            mock_instance.get_rl_configuration.return_value = Mock(
                rl_enabled=False, hybrid_mode=True, rl_confidence_threshold=0.7
            )
            mock_instance.get_performance_targets.return_value = Mock()
            mock_instance.config_version = "1.0.0"
            mock_instance.get_configuration_info.return_value = {'config_path': '/test/path'}

            # 創建處理器並執行
            processor = Stage4OptimizationProcessor(self.test_config)

            start_time = time.time()
            result = processor.process(test_input)
            end_time = time.time()

            # 驗證結果結構
            self.assertIsInstance(result, dict)
            self.assertEqual(result['stage'], 'stage4_optimization')

            # 驗證主要部分存在
            required_sections = ['optimal_pool', 'handover_strategy', 'optimization_results', 'metadata']
            for section in required_sections:
                self.assertIn(section, result, f"缺少部分: {section}")

            # 驗證optimal_pool結構
            optimal_pool = result['optimal_pool']
            self.assertIn('selected_satellites', optimal_pool)
            self.assertIn('pool_metrics', optimal_pool)
            self.assertIn('coverage_analysis', optimal_pool)

            # 驗證handover_strategy結構
            handover_strategy = result['handover_strategy']
            self.assertIn('triggers', handover_strategy)
            self.assertIn('timing', handover_strategy)
            self.assertIn('fallback_plans', handover_strategy)

            # 驗證optimization_results結構
            optimization_results = result['optimization_results']
            self.assertIn('objectives', optimization_results)
            self.assertIn('constraints', optimization_results)
            self.assertIn('pareto_solutions', optimization_results)

            # 驗證metadata
            metadata = result['metadata']
            self.assertIn('processing_time', metadata)
            self.assertIn('optimized_satellites', metadata)
            self.assertIn('generated_strategies', metadata)
            self.assertEqual(metadata['optimized_satellites'], 3)

            # 驗證處理時間合理
            processing_time = end_time - start_time
            self.assertLess(processing_time, 10.0, "處理時間過長")

            # 驗證性能指標
            if 'performance_metrics' in metadata:
                perf_metrics = metadata['performance_metrics']
                self.assertIn('processing_time_seconds', perf_metrics)
                self.assertGreater(perf_metrics['processing_time_seconds'], 0)

    def test_stress_testing(self):
        """壓力測試"""
        # 創建大量衛星數據
        large_input = {
            'signal_quality_data': [
                {
                    'satellite_id': f'SAT_{i:04d}',
                    'constellation': 'starlink' if i % 2 == 0 else 'oneweb',
                    'average_signal_strength': -80 - (i % 40),
                    'visibility_duration_minutes': 10 + (i % 20),
                    'elevation_deg': 15 + (i % 70),
                    'azimuth_deg': i % 360,
                    'latitude': -90 + (i % 180),
                    'longitude': -180 + (i % 360),
                    'altitude_km': 550 + (i % 1000)
                }
                for i in range(100)  # 100顆衛星
            ]
        }

        # 使用模擬配置管理器
        with patch('stages.stage4_optimization.stage4_optimization_processor.ConfigurationManager') as mock_config_manager:
            mock_instance = mock_config_manager.return_value
            mock_instance.get_optimization_objectives.return_value = Mock(
                signal_quality_weight=0.4, coverage_weight=0.3,
                handover_cost_weight=0.2, energy_efficiency_weight=0.1
            )
            mock_instance.get_constraints.return_value = Mock(
                min_satellites_per_pool=5, max_handover_frequency=10,
                min_signal_quality=-120, max_latency_ms=50
            )
            mock_instance.get_config.return_value = {}
            mock_instance.get_rl_configuration.return_value = Mock(
                rl_enabled=False, hybrid_mode=True, rl_confidence_threshold=0.7
            )
            mock_instance.get_performance_targets.return_value = Mock()
            mock_instance.config_version = "1.0.0"
            mock_instance.get_configuration_info.return_value = {'config_path': '/test/path'}

            processor = Stage4OptimizationProcessor(self.test_config)

            start_time = time.time()
            result = processor.process(large_input)
            end_time = time.time()

            # 驗證能夠處理大量數據
            self.assertIsInstance(result, dict)
            self.assertEqual(result['metadata']['optimized_satellites'], 100)

            # 驗證處理時間在合理範圍內（考慮到100顆衛星）
            processing_time = end_time - start_time
            self.assertLess(processing_time, 30.0, "大量數據處理時間過長")

    def test_error_recovery_scenarios(self):
        """測試錯誤恢復場景"""
        test_input = {
            'signal_quality_data': [
                {'satellite_id': 'SAT_001', 'constellation': 'starlink'}
            ]
        }

        # 使用模擬配置管理器
        with patch('stages.stage4_optimization.stage4_optimization_processor.ConfigurationManager') as mock_config_manager:
            mock_instance = mock_config_manager.return_value
            mock_instance.get_optimization_objectives.return_value = Mock(
                signal_quality_weight=0.4, coverage_weight=0.3,
                handover_cost_weight=0.2, energy_efficiency_weight=0.1
            )
            mock_instance.get_constraints.return_value = Mock(
                min_satellites_per_pool=2, max_handover_frequency=8,
                min_signal_quality=-110, max_latency_ms=100
            )
            mock_instance.get_config.return_value = {'fallback_strategy': 'simplified_optimization'}
            mock_instance.get_rl_configuration.return_value = Mock(
                rl_enabled=False, hybrid_mode=True, rl_confidence_threshold=0.7
            )
            mock_instance.get_performance_targets.return_value = Mock()
            mock_instance.config_version = "1.0.0"
            mock_instance.get_configuration_info.return_value = {'config_path': '/test/path'}

            processor = Stage4OptimizationProcessor(self.test_config)

            # 模擬池規劃失敗
            with patch.object(processor.pool_planner, 'plan_dynamic_pool', side_effect=Exception("模擬失敗")):
                result = processor.process(test_input)

                # 應該有錯誤處理結果
                self.assertIsInstance(result, dict)
                self.assertEqual(result['stage'], 'stage4_optimization')

                # 檢查是否觸發了故障恢復
                metadata = result['metadata']
                if 'fallback_strategy' in metadata:
                    self.assertIn(metadata['fallback_strategy'], ['simplified_optimization', 'minimal_output'])


if __name__ == '__main__':
    # 設置測試環境
    unittest.TestLoader.sortTestMethodsUsing = None

    # 創建測試套件
    test_classes = [
        TestStage4OptimizationProcessor,
        TestPoolPlanner,
        TestHandoverOptimizer,
        TestMultiObjectiveOptimizer,
        TestRLExtensionInterface,
        TestConfigurationManager,
        TestPerformanceMonitor,
        TestIntegration
    ]

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 輸出測試摘要
    print(f"\n{'='*60}")
    print(f"測試摘要:")
    print(f"總測試數: {result.testsRun}")
    print(f"失敗: {len(result.failures)}")
    print(f"錯誤: {len(result.errors)}")
    print(f"跳過: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"成功率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*60}")

    # 如果有失敗或錯誤，退出碼為1
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code)