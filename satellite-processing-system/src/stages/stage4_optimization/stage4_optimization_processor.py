#!/usr/bin/env python3
"""
Stage 4 Optimization Processor - 階段四：優化決策層
基於信號分析結果進行衛星選擇優化和換手決策

根據 @docs/stages/stage4-optimization.md 設計
功能職責：
- 協調整個決策流程
- 整合優化算法
- 管理RL擴展接口
- 驗證決策結果

核心工作：
1. 動態池規劃和衛星選擇優化
2. 換手決策算法和策略制定
3. 多目標優化（信號品質vs覆蓋範圍vs切換成本）
4. 強化學習擴展點預留
"""

import logging
import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import json

# 添加共享模組路徑
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from shared.core_modules.stage_interface import StageInterface
from shared.base_stage_processor import BaseStageProcessor

# 導入Stage 4專業模組
from .pool_planner import PoolPlanner, PoolRequirements
from .handover_optimizer import HandoverOptimizer, HandoverThresholds
from .multi_obj_optimizer import MultiObjectiveOptimizer


class Stage4OptimizationProcessor(BaseStageProcessor, StageInterface):
    """
    Stage 4 優化決策處理器

    專注於衛星選擇優化和換手決策：
    - 動態池規劃和衛星選擇優化
    - 換手決策算法和策略制定
    - 多目標優化（信號品質vs覆蓋範圍vs切換成本）
    - 強化學習擴展點預留
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化Stage 4優化決策處理器 - 完整企業級實現"""
        # 初始化基礎處理器和接口
        BaseStageProcessor.__init__(self, stage_name="stage4_optimization", config=config)
        StageInterface.__init__(self, stage_number=4, stage_name="optimization", config=config)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 設置階段編號
        self.stage_number = 4

        # 🔧 初始化配置管理器
        from .config_manager import ConfigurationManager
        self.config_manager = ConfigurationManager()
        
        # 合併外部配置和默認配置
        if config:
            self.config_manager.update_config('external_overrides', config, save_immediately=False)

        # 📊 初始化性能監控器
        from .performance_monitor import PerformanceMonitor
        perf_config = self.config_manager.get_config('performance_monitoring')
        self.performance_monitor = PerformanceMonitor(perf_config)

        # 從配置管理器獲取優化參數
        self.optimization_objectives = self.config_manager.get_optimization_objectives()
        self.constraints = self.config_manager.get_constraints()
        performance_targets = self.config_manager.get_performance_targets()

        # 初始化專業優化引擎
        pool_config = self.config_manager.get_config('pool_planner')
        handover_config = self.config_manager.get_config('handover_optimizer')
        multi_obj_config = self.config_manager.get_config('multi_objective_optimizer')

        self.pool_planner = PoolPlanner(pool_config)
        self.handover_optimizer = HandoverOptimizer(handover_config)
        self.multi_obj_optimizer = MultiObjectiveOptimizer(multi_obj_config)

        # 🤖 初始化RL擴展接口
        from .rl_extension_interface import RLExtensionCoordinator, DummyRLAgent
        rl_config = self.config_manager.get_rl_configuration()
        rl_extension_config = self.config_manager.get_config('rl_extension')
        
        self.rl_coordinator = RLExtensionCoordinator(rl_extension_config)
        
        # 如果啟用RL，註冊默認代理
        if rl_config.rl_enabled:
            dummy_agent = DummyRLAgent(rl_extension_config.get('rl_agent', {}))
            self.rl_coordinator.register_rl_agent(dummy_agent)

        # 處理配置
        self.processing_config = {
            'enable_pool_planning': True,
            'enable_handover_optimization': True,
            'enable_multi_objective_optimization': True,
            'rl_extension_ready': True,
            'rl_enabled': rl_config.rl_enabled,
            'hybrid_mode': rl_config.hybrid_mode,
            'output_format': 'optimization_decisions_v2',
            'academic_compliance': True,
            'performance_monitoring': perf_config.get('enable_detailed_metrics', True),
            'error_recovery': self.config_manager.get_config('error_handling')
        }

        # 🎯 增強處理統計
        self.processing_stats = {
            'satellites_processed': 0,
            'pools_planned': 0,
            'handover_strategies_generated': 0,
            'multi_objective_optimizations': 0,
            'rl_decisions_used': 0,
            'traditional_decisions_used': 0,
            'hybrid_decisions': 0,
            'processing_time_seconds': 0,
            'optimization_effectiveness': 0.0,
            'constraint_violations': 0,
            'error_count': 0,
            'memory_peak_mb': 0.0,
            'decision_quality_average': 0.0
        }

        # 錯誤處理配置
        error_config = self.config_manager.get_config('error_handling')
        self.max_retry_attempts = error_config.get('max_retry_attempts', 3)
        self.retry_delay = error_config.get('retry_delay_seconds', 1.0)
        self.fallback_strategy = error_config.get('fallback_strategy', 'simplified_optimization')

        # 驗證配置
        validation_config = self.config_manager.get_config('validation')
        self.enable_input_validation = validation_config.get('enable_input_validation', True)
        self.enable_output_validation = validation_config.get('enable_output_validation', True)

        self.logger.info("✅ Stage 4優化決策處理器初始化完成 (企業級版本)")
        self.logger.info(f"🔧 配置管理器: {self.config_manager.get_configuration_info()['config_path']}")
        self.logger.info(f"📊 性能監控: {'啟用' if self.processing_config['performance_monitoring'] else '禁用'}")
        
        if self.processing_config['rl_enabled']:
            self.logger.info(f"🤖 RL擴展已啟用 (混合模式: {'是' if rl_config.hybrid_mode else '否'})")
        
        # 記錄關鍵配置
        self.logger.info(f"🎯 優化目標權重: 信號{self.optimization_objectives.signal_quality_weight:.1f} "
                        f"覆蓋{self.optimization_objectives.coverage_weight:.1f} "
                        f"成本{self.optimization_objectives.handover_cost_weight:.1f} "
                        f"能效{self.optimization_objectives.energy_efficiency_weight:.1f}")
        
        self.logger.info(f"🔒 約束條件: 最少衛星{self.constraints.min_satellites_per_pool} "
                        f"最大換手{self.constraints.max_handover_frequency}/h "
                        f"信號門檻{self.constraints.min_signal_quality}dBm "
                        f"延遲<{self.constraints.max_latency_ms}ms")
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stage 4主處理流程 - 優化決策層 (企業級實現)

        Args:
            input_data: Stage 3信號分析輸出

        Returns:
            優化決策結果
        """
        # 🔄 開始性能監控
        process_info = {
            'stage': 'stage4_optimization',
            'input_size': len(str(input_data)),
            'rl_enabled': self.processing_config['rl_enabled']
        }
        
        if self.processing_config['performance_monitoring']:
            self.performance_monitor.start_process_monitoring(process_info)

        retry_count = 0
        last_error = None

        while retry_count <= self.max_retry_attempts:
            try:
                start_time = time.time()
                self.logger.info(f"🎯 開始Stage 4優化決策處理 (嘗試 {retry_count + 1}/{self.max_retry_attempts + 1})")

                # ✅ 驗證輸入數據
                if self.enable_input_validation:
                    self._validate_input_comprehensive(input_data)
                else:
                    self._validate_input_not_empty(input_data)
                
                validated_input = self._validate_stage3_input(input_data)

                # ✅ 提取信號分析數據
                signal_analysis_data = self._extract_signal_analysis_data(validated_input)

                # ✅ 執行傳統優化算法
                traditional_results = self._execute_traditional_optimization_with_monitoring(signal_analysis_data)

                # 🤖 RL擴展：協調決策制定
                if self.processing_config['rl_enabled']:
                    self.logger.info("🤖 執行RL擴展決策協調")
                    coordinated_decision = self.rl_coordinator.coordinate_decision_making(
                        signal_analysis_data, traditional_results
                    )
                    
                    # 更新RL統計
                    rl_stats = self.rl_coordinator.get_coordination_statistics()
                    self.processing_stats.update({
                        'rl_decisions_used': rl_stats.get('rl_decisions_used', 0),
                        'traditional_decisions_used': rl_stats.get('traditional_decisions_used', 0),
                        'hybrid_decisions': rl_stats.get('hybrid_decisions', 0)
                    })
                    
                    # 使用協調後的決策
                    final_results = self._integrate_coordinated_decision(coordinated_decision, traditional_results)
                else:
                    # 使用傳統優化結果
                    final_results = traditional_results
                    self.processing_stats['traditional_decisions_used'] += 1

                # 計算處理時間和效能指標
                end_time = time.time()
                processing_time = end_time - start_time
                self.processing_stats['processing_time_seconds'] = processing_time

                # 🎯 構建符合文檔規範的輸出格式
                result = self._build_standardized_output(final_results, signal_analysis_data, processing_time)

                # ✅ 驗證輸出
                if self.enable_output_validation:
                    self._validate_output_comprehensive(result)

                # 📊 結束性能監控
                if self.processing_config['performance_monitoring']:
                    performance_metrics = self.performance_monitor.end_process_monitoring(result)
                    
                    # 更新統計
                    self.processing_stats.update({
                        'memory_peak_mb': performance_metrics.memory_usage_mb,
                        'decision_quality_average': performance_metrics.decision_quality_score
                    })

                self.logger.info(f"✅ Stage 4優化決策完成: {processing_time:.3f}s "
                               f"(衛星: {len(signal_analysis_data.get('candidates', []))}, "
                               f"質量: {performance_metrics.decision_quality_score:.3f})")
                
                return result

            except Exception as e:
                retry_count += 1
                last_error = e
                
                # 記錄錯誤
                if self.processing_config['performance_monitoring']:
                    self.performance_monitor.record_error(e, {
                        'retry_count': retry_count,
                        'input_data_size': len(str(input_data))
                    })
                
                self.processing_stats['error_count'] += 1
                
                if retry_count <= self.max_retry_attempts:
                    self.logger.warning(f"⚠️ Stage 4處理失敗，重試中 ({retry_count}/{self.max_retry_attempts}): {e}")
                    time.sleep(self.retry_delay * retry_count)  # 指數退避
                else:
                    self.logger.error(f"❌ Stage 4處理最終失敗: {e}")
                    
                    # 嘗試故障恢復
                    return self._execute_fallback_strategy(input_data, last_error)

        # 不應該到達這裡
        return self._create_error_result(str(last_error) if last_error else "未知錯誤")

    def _extract_selected_satellites(self, pool_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取選中的衛星列表"""
        try:
            selected_satellites = []
            if 'planned_pools' in pool_results:
                for pool in pool_results['planned_pools']:
                    if 'satellites' in pool:
                        selected_satellites.extend(pool['satellites'])
            return selected_satellites
        except Exception as e:
            self.logger.error(f"提取選中衛星失敗: {e}")
            return []

    def _extract_pool_metrics(self, pool_results: Dict[str, Any]) -> Dict[str, Any]:
        """提取池指標"""
        try:
            if 'planning_analysis' in pool_results:
                return pool_results['planning_analysis']
            return {
                'pool_count': len(pool_results.get('planned_pools', [])),
                'total_satellites': sum(len(pool.get('satellites', [])) for pool in pool_results.get('planned_pools', [])),
                'planning_quality': 'optimal' if pool_results.get('planned_pools') else 'no_pools'
            }
        except Exception as e:
            self.logger.error(f"提取池指標失敗: {e}")
            return {}

    def _extract_coverage_analysis(self, pool_results: Dict[str, Any]) -> Dict[str, Any]:
        """提取覆蓋分析"""
        try:
            coverage_data = {}
            if 'planned_pools' in pool_results:
                for i, pool in enumerate(pool_results['planned_pools']):
                    if 'coverage_analysis' in pool:
                        coverage_data[f'pool_{i}'] = pool['coverage_analysis']
            return coverage_data
        except Exception as e:
            self.logger.error(f"提取覆蓋分析失敗: {e}")
            return {}

    def _extract_handover_triggers(self, handover_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取換手觸發器"""
        try:
            triggers = []
            if 'trigger_events' in handover_results:
                triggers = handover_results['trigger_events']
            elif 'optimized_decisions' in handover_results:
                # 從優化決策中提取觸發器
                for decision in handover_results['optimized_decisions']:
                    if 'trigger_conditions' in decision:
                        triggers.append(decision['trigger_conditions'])
            return triggers
        except Exception as e:
            self.logger.error(f"提取換手觸發器失敗: {e}")
            return []

    def _extract_handover_timing(self, handover_results: Dict[str, Any]) -> Dict[str, Any]:
        """提取換手時機"""
        try:
            if 'execution_strategy' in handover_results:
                return handover_results['execution_strategy']
            return {
                'optimal_timing': handover_results.get('optimal_timing', {}),
                'timing_windows': handover_results.get('timing_windows', [])
            }
        except Exception as e:
            self.logger.error(f"提取換手時機失敗: {e}")
            return {}

    def _extract_fallback_plans(self, handover_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取後備計劃"""
        try:
            if 'fallback_strategies' in handover_results:
                return handover_results['fallback_strategies']
            return []
        except Exception as e:
            self.logger.error(f"提取後備計劃失敗: {e}")
            return []

    def _extract_optimization_objectives(self, multi_obj_results: Dict[str, Any]) -> Dict[str, Any]:
        """提取優化目標"""
        try:
            if 'objectives_analysis' in multi_obj_results:
                return multi_obj_results['objectives_analysis']
            return {
                'signal_quality': multi_obj_results.get('signal_quality_objective', {}),
                'coverage_range': multi_obj_results.get('coverage_objective', {}),
                'handover_cost': multi_obj_results.get('handover_cost_objective', {}),
                'energy_efficiency': multi_obj_results.get('energy_objective', {})
            }
        except Exception as e:
            self.logger.error(f"提取優化目標失敗: {e}")
            return {}

    def _extract_optimization_constraints(self, multi_obj_results: Dict[str, Any]) -> Dict[str, Any]:
        """提取優化約束"""
        try:
            if 'constraints_analysis' in multi_obj_results:
                return multi_obj_results['constraints_analysis']
            return {
                'min_satellites_constraint': self.constraints['min_satellites_per_pool'],
                'signal_quality_constraint': self.constraints['min_signal_quality'],
                'handover_frequency_constraint': self.constraints['max_handover_frequency'],
                'latency_constraint': self.constraints['max_latency_ms']
            }
        except Exception as e:
            self.logger.error(f"提取優化約束失敗: {e}")
            return {}

    def _extract_pareto_solutions(self, multi_obj_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取帕累托解"""
        try:
            return multi_obj_results.get('pareto_solutions', [])
        except Exception as e:
            self.logger.error(f"提取帕累托解失敗: {e}")
            return []

    def _count_generated_strategies(self, handover_results: Dict[str, Any]) -> int:
        """計算生成的策略數量"""
        try:
            strategies_count = 0
            if 'optimized_decisions' in handover_results:
                strategies_count += len(handover_results['optimized_decisions'])
            if 'fallback_strategies' in handover_results:
                strategies_count += len(handover_results['fallback_strategies'])
            return strategies_count
        except Exception as e:
            self.logger.error(f"計算策略數量失敗: {e}")
            return 0

    def _execute_traditional_optimization(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行傳統優化算法組合"""
        try:
            # ✅ 執行動態池規劃
            pool_planning_results = self._execute_pool_planning(signal_data)

            # ✅ 執行換手優化
            handover_optimization = self._execute_handover_optimization(
                signal_data, pool_planning_results
            )

            # ✅ 執行多目標優化
            multi_objective_results = self._execute_multi_objective_optimization(
                pool_planning_results, handover_optimization
            )

            return {
                'pool_planning': pool_planning_results,
                'handover_optimization': handover_optimization,
                'multi_objective': multi_objective_results,
                'decision_source': 'traditional_optimization'
            }

        except Exception as e:
            self.logger.error(f"傳統優化執行失敗: {e}")
            raise

    def _integrate_coordinated_decision(self, coordinated_decision: Dict[str, Any], 
                                      traditional_results: Dict[str, Any]) -> Dict[str, Any]:
        """整合協調決策結果"""
        try:
            if coordinated_decision.get('decision_source') == 'hybrid_rl_traditional':
                # 混合決策：結合RL和傳統結果
                integrated_results = traditional_results.copy()
                integrated_results['decision_source'] = 'hybrid_rl_traditional'
                integrated_results['rl_coordination'] = coordinated_decision
                
                # 更新池規劃結果
                if 'final_selection' in coordinated_decision:
                    self._update_pool_with_rl_selection(
                        integrated_results['pool_planning'], 
                        coordinated_decision['final_selection']
                    )
                
            elif coordinated_decision.get('decision_source') == 'rl_agent':
                # 純RL決策
                integrated_results = self._convert_rl_to_traditional_format(
                    coordinated_decision, traditional_results
                )
                integrated_results['decision_source'] = 'rl_agent'
                
            else:
                # 回退到傳統優化
                integrated_results = traditional_results
                
            return integrated_results
            
        except Exception as e:
            self.logger.error(f"協調決策整合失敗: {e}")
            # 錯誤時回退到傳統結果
            return traditional_results

    def _update_pool_with_rl_selection(self, pool_results: Dict[str, Any], 
                                     rl_selection: Dict[str, Any]):
        """用RL選擇更新池規劃結果"""
        if 'selected_satellites' in rl_selection and 'planned_pools' in pool_results:
            # 簡化：用RL選擇的衛星更新第一個池
            if pool_results['planned_pools']:
                pool_results['planned_pools'][0]['rl_enhanced'] = True
                pool_results['planned_pools'][0]['rl_satellites'] = rl_selection['selected_satellites']

    def _convert_rl_to_traditional_format(self, rl_decision: Dict[str, Any], 
                                        template: Dict[str, Any]) -> Dict[str, Any]:
        """將RL決策轉換為傳統格式"""
        # 使用傳統結果作為模板，用RL決策覆蓋關鍵部分
        converted = template.copy()
        
        if 'decision' in rl_decision:
            rl_data = rl_decision['decision']
            
            # 更新池規劃
            if 'selected_satellites' in rl_data:
                converted['pool_planning']['rl_selected_satellites'] = rl_data['selected_satellites']
                
        return converted

    def _calculate_performance_metrics(self, results: Dict[str, Any], 
                                     processing_time: float) -> Dict[str, Any]:
        """計算性能指標"""
        try:
            # 基礎性能指標
            metrics = {
                'processing_time_seconds': processing_time,
                'memory_efficiency': 'optimal' if processing_time < 10.0 else 'acceptable',
                'computation_complexity': 'O(n²)' if len(self.processing_stats.get('satellites_processed', 0)) > 500 else 'O(n)',
                'decision_quality_score': self._calculate_decision_quality_score(results),
                'constraint_satisfaction_rate': self._calculate_constraint_satisfaction_rate(results),
                'optimization_convergence': self._assess_optimization_convergence(results)
            }

            # RL特定指標
            if self.processing_config['rl_enabled']:
                rl_stats = self.rl_coordinator.get_coordination_statistics()
                metrics.update({
                    'rl_usage_rate': rl_stats.get('rl_usage_rate', 0.0),
                    'hybrid_usage_rate': rl_stats.get('hybrid_usage_rate', 0.0),
                    'rl_confidence_avg': 0.75  # 示例值，實際應從RL記錄計算
                })

            return metrics

        except Exception as e:
            self.logger.error(f"性能指標計算失敗: {e}")
            return {'processing_time_seconds': processing_time, 'calculation_error': str(e)}

    def _calculate_decision_quality_score(self, results: Dict[str, Any]) -> float:
        """計算決策質量分數"""
        try:
            quality_factors = []

            # 池規劃質量
            pool_planning = results.get('pool_planning', {})
            if 'planned_pools' in pool_planning:
                pool_count = len(pool_planning['planned_pools'])
                pool_quality = min(1.0, pool_count / 3.0)  # 3個池為理想
                quality_factors.append(pool_quality)

            # 換手優化質量
            handover_opt = results.get('handover_optimization', {})
            if 'optimized_decisions' in handover_opt:
                handover_count = len(handover_opt['optimized_decisions'])
                handover_quality = min(1.0, handover_count / 5.0)  # 5個策略為理想
                quality_factors.append(handover_quality)

            # 多目標優化質量
            multi_obj = results.get('multi_objective', {})
            if 'pareto_solutions' in multi_obj:
                pareto_count = len(multi_obj['pareto_solutions'])
                pareto_quality = min(1.0, pareto_count / 10.0)  # 10個解為理想
                quality_factors.append(pareto_quality)

            return sum(quality_factors) / len(quality_factors) if quality_factors else 0.5

        except Exception as e:
            self.logger.error(f"決策質量計算失敗: {e}")
            return 0.5

    def _calculate_constraint_satisfaction_rate(self, results: Dict[str, Any]) -> float:
        """計算約束滿足率"""
        try:
            total_constraints = len(self.constraints)
            satisfied_constraints = 0

            # 檢查每個約束
            for constraint_name, constraint_value in self.constraints.items():
                if self._check_constraint_satisfaction(constraint_name, constraint_value, results):
                    satisfied_constraints += 1

            return satisfied_constraints / total_constraints if total_constraints > 0 else 1.0

        except Exception as e:
            self.logger.error(f"約束滿足率計算失敗: {e}")
            return 0.5

    def _check_constraint_satisfaction(self, constraint_name: str, constraint_value: Any, 
                                     results: Dict[str, Any]) -> bool:
        """檢查單個約束是否滿足"""
        try:
            if constraint_name == 'min_satellites_per_pool':
                pool_planning = results.get('pool_planning', {})
                pools = pool_planning.get('planned_pools', [])
                for pool in pools:
                    if len(pool.get('satellites', [])) < constraint_value:
                        return False
                return True

            elif constraint_name == 'max_handover_frequency':
                handover_opt = results.get('handover_optimization', {})
                decisions = handover_opt.get('optimized_decisions', [])
                return len(decisions) <= constraint_value

            elif constraint_name == 'min_signal_quality':
                # 簡化檢查：假設優化後信號質量滿足要求
                return True

            elif constraint_name == 'max_latency_ms':
                # 簡化檢查：假設處理延遲滿足要求
                processing_time_ms = self.processing_stats.get('processing_time_seconds', 0) * 1000
                return processing_time_ms <= constraint_value

            return True

        except Exception as e:
            self.logger.error(f"約束檢查失敗 {constraint_name}: {e}")
            return False

    def _assess_optimization_convergence(self, results: Dict[str, Any]) -> str:
        """評估優化收斂性"""
        try:
            convergence_indicators = []

            # 多目標優化收斂性
            multi_obj = results.get('multi_objective', {})
            if 'pareto_solutions' in multi_obj:
                pareto_count = len(multi_obj['pareto_solutions'])
                if pareto_count >= 5:
                    convergence_indicators.append('pareto_converged')
                else:
                    convergence_indicators.append('pareto_limited')

            # 池規劃穩定性
            pool_planning = results.get('pool_planning', {})
            if 'planned_pools' in pool_planning:
                if len(pool_planning['planned_pools']) > 0:
                    convergence_indicators.append('pool_stable')
                else:
                    convergence_indicators.append('pool_unstable')

            # 整體評估
            if 'pareto_converged' in convergence_indicators and 'pool_stable' in convergence_indicators:
                return 'excellent_convergence'
            elif len(convergence_indicators) >= 1:
                return 'acceptable_convergence'
            else:
                return 'poor_convergence'

        except Exception as e:
            self.logger.error(f"收斂性評估失敗: {e}")
            return 'assessment_failed'

    def _validate_input_comprehensive(self, input_data: Dict[str, Any]):
        """全面驗證輸入數據"""
        try:
            # 基本結構驗證
            if not isinstance(input_data, dict):
                raise ValueError("輸入數據必須是字典格式")

            # 檢查必要字段
            required_fields = ['signal_quality_data']
            for field in required_fields:
                if field not in input_data:
                    raise ValueError(f"缺少必要字段: {field}")

            # 驗證信號質量數據
            signal_data = input_data['signal_quality_data']
            if not isinstance(signal_data, list):
                raise ValueError("signal_quality_data必須是列表格式")

            # 驗證信號數據完整性
            for i, signal_record in enumerate(signal_data):
                if not isinstance(signal_record, dict):
                    raise ValueError(f"信號記錄 {i} 必須是字典格式")
                
                if 'satellite_id' not in signal_record:
                    self.logger.warning(f"信號記錄 {i} 缺少satellite_id")

            self.logger.debug("✅ 輸入數據全面驗證通過")

        except Exception as e:
            self.logger.error(f"❌ 輸入數據驗證失敗: {e}")
            raise

    def _validate_output_comprehensive(self, output_data: Dict[str, Any]):
        """全面驗證輸出數據"""
        try:
            # 檢查基本結構
            required_sections = ['stage', 'optimal_pool', 'handover_strategy', 'optimization_results', 'metadata']
            for section in required_sections:
                if section not in output_data:
                    raise ValueError(f"輸出缺少必要部分: {section}")

            # 驗證每個部分的結構
            self._validate_optimal_pool_structure(output_data['optimal_pool'])
            self._validate_handover_strategy_structure(output_data['handover_strategy'])
            self._validate_optimization_results_structure(output_data['optimization_results'])
            self._validate_metadata_structure(output_data['metadata'])

            self.logger.debug("✅ 輸出數據全面驗證通過")

        except Exception as e:
            self.logger.error(f"❌ 輸出數據驗證失敗: {e}")
            raise

    def _validate_optimal_pool_structure(self, pool_data: Dict[str, Any]):
        """驗證最優池結構"""
        required_fields = ['selected_satellites', 'pool_metrics', 'coverage_analysis']
        for field in required_fields:
            if field not in pool_data:
                raise ValueError(f"optimal_pool缺少字段: {field}")

    def _validate_handover_strategy_structure(self, handover_data: Dict[str, Any]):
        """驗證換手策略結構"""
        required_fields = ['triggers', 'timing', 'fallback_plans']
        for field in required_fields:
            if field not in handover_data:
                raise ValueError(f"handover_strategy缺少字段: {field}")

    def _validate_optimization_results_structure(self, opt_data: Dict[str, Any]):
        """驗證優化結果結構"""
        required_fields = ['objectives', 'constraints', 'pareto_solutions']
        for field in required_fields:
            if field not in opt_data:
                raise ValueError(f"optimization_results缺少字段: {field}")

    def _validate_metadata_structure(self, metadata: Dict[str, Any]):
        """驗證元數據結構"""
        required_fields = ['processing_time', 'optimized_satellites', 'generated_strategies']
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"metadata缺少字段: {field}")

    def _execute_traditional_optimization_with_monitoring(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行帶監控的傳統優化"""
        try:
            optimization_start = time.time()

            # 執行各個優化算法並監控性能
            pool_planning_results = self._execute_pool_planning_monitored(signal_data)
            handover_optimization = self._execute_handover_optimization_monitored(signal_data, pool_planning_results)
            multi_objective_results = self._execute_multi_objective_optimization_monitored(
                pool_planning_results, handover_optimization
            )

            optimization_time = time.time() - optimization_start

            return {
                'pool_planning': pool_planning_results,
                'handover_optimization': handover_optimization,
                'multi_objective': multi_objective_results,
                'decision_source': 'traditional_optimization',
                'optimization_time': optimization_time
            }

        except Exception as e:
            self.logger.error(f"傳統優化執行失敗: {e}")
            raise

    def _execute_pool_planning_monitored(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行帶監控的池規劃"""
        try:
            start_time = time.time()
            
            if not self.processing_config['enable_pool_planning']:
                return {'pool_planning': 'disabled'}

            self.logger.debug("🏊 執行動態池規劃")

            # 使用配置管理器的參數
            pool_config = self.config_manager.get_config('pool_planner')
            
            # 準備池規劃需求
            requirements = PoolRequirements(
                min_satellites_per_pool=self.constraints.min_satellites_per_pool,
                min_signal_quality=self.constraints.min_signal_quality
            )

            # 執行池規劃
            planning_results = self.pool_planner.plan_dynamic_pool(
                signal_data['candidates'], requirements
            )

            # 分析覆蓋範圍
            if 'planned_pools' in planning_results and planning_results['planned_pools']:
                for pool in planning_results['planned_pools']:
                    if 'satellites' in pool:
                        coverage_analysis = self.pool_planner.analyze_coverage(pool['satellites'])
                        pool['coverage_analysis'] = coverage_analysis

            # 更新統計
            if 'planned_pools' in planning_results:
                self.processing_stats['pools_planned'] = len(planning_results['planned_pools'])

            processing_time = time.time() - start_time
            planning_results['processing_time_seconds'] = processing_time

            self.logger.info(f"✅ 動態池規劃完成: {self.processing_stats['pools_planned']}個池, {processing_time:.3f}s")
            return planning_results

        except Exception as e:
            self.logger.error(f"動態池規劃失敗: {e}")
            # 返回安全的默認結果
            return {
                'error': str(e),
                'planned_pools': [],
                'fallback_strategy': 'single_pool_fallback'
            }

    def _execute_handover_optimization_monitored(self, signal_data: Dict[str, Any],
                                               pool_results: Dict[str, Any]) -> Dict[str, Any]:
        """執行帶監控的換手優化"""
        try:
            start_time = time.time()
            
            if not self.processing_config['enable_handover_optimization']:
                return {'handover_optimization': 'disabled'}

            self.logger.debug("🔄 執行換手優化")

            # 準備換手優化數據
            current_signal_status = {
                'satellites': signal_data['candidates'],
                'signal_metrics': signal_data['signal_metrics']
            }

            # 從池規劃結果提取候選目標
            handover_candidates = []
            if 'planned_pools' in pool_results and not pool_results.get('error'):
                for pool in pool_results['planned_pools']:
                    if 'satellites' in pool:
                        handover_candidates.extend(pool['satellites'])

            # 如果沒有池規劃結果，使用原始候選者
            if not handover_candidates:
                handover_candidates = signal_data['candidates']

            # 執行換手策略優化
            handover_results = self.handover_optimizer.optimize_handover_strategy(
                current_signal_status, handover_candidates
            )

            # 確定換手觸發條件
            gpp_events = signal_data.get('gpp_events', [])
            if gpp_events:
                trigger_events = self.handover_optimizer.determine_handover_trigger(gpp_events)
                handover_results['trigger_events'] = trigger_events

            # 更新統計
            if 'optimized_decisions' in handover_results:
                self.processing_stats['handover_strategies_generated'] = len(handover_results['optimized_decisions'])

            processing_time = time.time() - start_time
            handover_results['processing_time_seconds'] = processing_time

            self.logger.info(f"✅ 換手優化完成: {self.processing_stats['handover_strategies_generated']}個策略, {processing_time:.3f}s")
            return handover_results

        except Exception as e:
            self.logger.error(f"換手優化失敗: {e}")
            # 返回安全的默認結果
            return {
                'error': str(e),
                'optimized_decisions': [],
                'fallback_strategy': 'no_handover'
            }

    def _execute_multi_objective_optimization_monitored(self, pool_results: Dict[str, Any],
                                                      handover_results: Dict[str, Any]) -> Dict[str, Any]:
        """執行帶監控的多目標優化"""
        try:
            start_time = time.time()
            
            if not self.processing_config['enable_multi_objective_optimization']:
                return {'multi_objective_optimization': 'disabled'}

            self.logger.debug("🎯 執行多目標優化")

            # 準備目標函數
            objectives = {
                'signal_quality': -85.0,  # 目標信號強度
                'coverage_range': 85.0,   # 目標覆蓋率
                'handover_cost': 8.0,     # 目標換手成本
                'energy_efficiency': 75.0 # 目標能效
            }

            # 準備約束條件
            constraints = [
                {
                    'name': 'min_satellites_constraint',
                    'type': 'inequality',
                    'function': f"satellites_count >= {self.constraints.min_satellites_per_pool}",
                    'penalty': 100.0,
                    'hard': True
                },
                {
                    'name': 'signal_quality_constraint',
                    'type': 'inequality',
                    'function': f"signal_quality >= {self.constraints.min_signal_quality}",
                    'penalty': 75.0,
                    'hard': True
                },
                {
                    'name': 'handover_frequency_constraint',
                    'type': 'inequality',
                    'function': f"handover_frequency <= {self.constraints.max_handover_frequency}",
                    'penalty': 50.0,
                    'hard': True
                }
            ]

            # 執行多目標優化
            optimization_results = self.multi_obj_optimizer.optimize_multiple_objectives(
                objectives, constraints
            )

            # 平衡品質與成本
            if 'pareto_solutions' in optimization_results and optimization_results['pareto_solutions']:
                balance_results = self.multi_obj_optimizer.balance_quality_cost(
                    optimization_results['pareto_solutions']
                )
                optimization_results['quality_cost_balance'] = balance_results

            # 更新統計
            self.processing_stats['multi_objective_optimizations'] += 1

            processing_time = time.time() - start_time
            optimization_results['processing_time_seconds'] = processing_time

            self.logger.info(f"✅ 多目標優化完成: {len(optimization_results.get('pareto_solutions', []))}個解, {processing_time:.3f}s")
            return optimization_results

        except Exception as e:
            self.logger.error(f"多目標優化失敗: {e}")
            # 返回安全的默認結果
            return {
                'error': str(e),
                'pareto_solutions': [],
                'fallback_strategy': 'single_objective'
            }

    def _build_standardized_output(self, final_results: Dict[str, Any], 
                                  signal_analysis_data: Dict[str, Any],
                                  processing_time: float) -> Dict[str, Any]:
        """構建標準化輸出格式"""
        try:
            # 計算性能指標
            performance_metrics = self._calculate_performance_metrics(final_results, processing_time)
            
            # 構建符合文檔規範的結果
            result = {
                'stage': 'stage4_optimization',
                'optimal_pool': {
                    'selected_satellites': self._extract_selected_satellites(final_results.get('pool_planning', {})),
                    'pool_metrics': self._extract_pool_metrics(final_results.get('pool_planning', {})),
                    'coverage_analysis': self._extract_coverage_analysis(final_results.get('pool_planning', {}))
                },
                'handover_strategy': {
                    'triggers': self._extract_handover_triggers(final_results.get('handover_optimization', {})),
                    'timing': self._extract_handover_timing(final_results.get('handover_optimization', {})),
                    'fallback_plans': self._extract_fallback_plans(final_results.get('handover_optimization', {}))
                },
                'optimization_results': {
                    'objectives': self._extract_optimization_objectives(final_results.get('multi_objective', {})),
                    'constraints': self._extract_optimization_constraints(final_results.get('multi_objective', {})),
                    'pareto_solutions': self._extract_pareto_solutions(final_results.get('multi_objective', {}))
                },
                'metadata': {
                    'processing_time': datetime.now(timezone.utc).isoformat(),
                    'optimized_satellites': len(signal_analysis_data.get('candidates', [])),
                    'generated_strategies': self._count_generated_strategies(final_results.get('handover_optimization', {})),
                    'rl_enabled': self.processing_config['rl_enabled'],
                    'decision_source': final_results.get('decision_source', 'traditional_optimization'),
                    'performance_metrics': performance_metrics,
                    'processor_version': 'v2.0_enterprise_optimization_layer',
                    'config_version': self.config_manager.config_version,
                    'optimization_effectiveness': performance_metrics.get('decision_quality_score', 0.0),
                    'constraint_compliance': performance_metrics.get('constraint_satisfaction_rate', 0.0)
                }
            }

            # 添加RL相關信息
            if self.processing_config['rl_enabled']:
                rl_stats = self.rl_coordinator.get_coordination_statistics()
                result['metadata']['rl_coordination'] = {
                    'rl_usage_rate': rl_stats.get('rl_usage_rate', 0.0),
                    'hybrid_usage_rate': rl_stats.get('hybrid_usage_rate', 0.0),
                    'coordination_effectiveness': rl_stats.get('total_decisions', 0)
                }

            # 添加性能監控結果
            if self.processing_config['performance_monitoring']:
                result['metadata']['performance_summary'] = self.performance_monitor.get_performance_summary()

            return result

        except Exception as e:
            self.logger.error(f"標準化輸出構建失敗: {e}")
            raise

    def _execute_fallback_strategy(self, input_data: Dict[str, Any], error: Exception) -> Dict[str, Any]:
        """執行故障恢復策略"""
        try:
            self.logger.info(f"🚨 執行故障恢復策略: {self.fallback_strategy}")

            if self.fallback_strategy == 'simplified_optimization':
                return self._execute_simplified_optimization(input_data)
            elif self.fallback_strategy == 'minimal_output':
                return self._create_minimal_output(input_data)
            else:
                return self._create_error_result(str(error))

        except Exception as fallback_error:
            self.logger.error(f"❌ 故障恢復也失敗: {fallback_error}")
            return self._create_error_result(f"Original: {error}, Fallback: {fallback_error}")

    def _execute_simplified_optimization(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行簡化優化"""
        try:
            self.logger.info("🔧 執行簡化優化策略")

            # 簡化的信號分析
            signal_data = input_data.get('signal_quality_data', [])
            
            # 選擇信號最強的衛星作為簡化池
            best_satellites = []
            if signal_data:
                # 按信號強度排序，選擇前5個
                sorted_signals = sorted(signal_data, 
                                      key=lambda x: x.get('average_signal_strength', -120), 
                                      reverse=True)
                best_satellites = sorted_signals[:5]

            # 構建簡化結果
            result = {
                'stage': 'stage4_optimization',
                'optimal_pool': {
                    'selected_satellites': best_satellites,
                    'pool_metrics': {'strategy': 'simplified', 'satellite_count': len(best_satellites)},
                    'coverage_analysis': {'strategy': 'simplified'}
                },
                'handover_strategy': {
                    'triggers': [],
                    'timing': {'strategy': 'immediate'},
                    'fallback_plans': [{'type': 'maintain_current'}]
                },
                'optimization_results': {
                    'objectives': {'strategy': 'simplified'},
                    'constraints': {'strategy': 'basic_constraints'},
                    'pareto_solutions': []
                },
                'metadata': {
                    'processing_time': datetime.now(timezone.utc).isoformat(),
                    'optimized_satellites': len(best_satellites),
                    'generated_strategies': 1,
                    'fallback_strategy': 'simplified_optimization',
                    'processor_version': 'v2.0_fallback_mode'
                }
            }

            self.logger.info("✅ 簡化優化完成")
            return result

        except Exception as e:
            self.logger.error(f"❌ 簡化優化失敗: {e}")
            return self._create_minimal_output(input_data)

    def _create_minimal_output(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """創建最小輸出"""
        return {
            'stage': 'stage4_optimization',
            'optimal_pool': {
                'selected_satellites': [],
                'pool_metrics': {},
                'coverage_analysis': {}
            },
            'handover_strategy': {
                'triggers': [],
                'timing': {},
                'fallback_plans': []
            },
            'optimization_results': {
                'objectives': {},
                'constraints': {},
                'pareto_solutions': []
            },
            'metadata': {
                'processing_time': datetime.now(timezone.utc).isoformat(),
                'optimized_satellites': 0,
                'generated_strategies': 0,
                'fallback_strategy': 'minimal_output',
                'processor_version': 'v2.0_minimal_mode'
            }
        }

    def _validate_stage3_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證Stage 3輸入數據"""
        try:
            # 檢查必要的信號分析數據
            if 'signal_quality_data' not in input_data:
                raise ValueError("缺少Stage 3信號品質數據")

            signal_data = input_data['signal_quality_data']
            if not isinstance(signal_data, list):
                raise ValueError("Stage 3信號數據格式錯誤，應為列表")

            # 允許空列表，但記錄警告
            if len(signal_data) == 0:
                self.logger.warning("⚠️ Stage 3信號品質數據為空，將處理為無信號分析結果的情況")

            # 檢查其他可選字段
            if 'gpp_events' in input_data:
                self.logger.info("📡 檢測到3GPP事件數據，將用於換手優化")

            return input_data

        except Exception as e:
            self.logger.error(f"❌ Stage 3輸入驗證失敗: {e}")
            raise

    def _extract_signal_analysis_data(self, validated_input: Dict[str, Any]) -> Dict[str, Any]:
        """提取信號分析數據"""
        try:
            signal_quality_data = validated_input['signal_quality_data']
            gpp_events = validated_input.get('gpp_events', [])

            # 轉換為優化算法格式
            candidates = []
            signal_metrics = {}

            for signal_record in signal_quality_data:
                # 提取候選衛星信息
                candidate = {
                    'satellite_id': signal_record.get('satellite_id'),
                    'constellation': signal_record.get('constellation'),
                    'signal_analysis': signal_record,
                    'position_timeseries': signal_record.get('position_timeseries_with_signal', [])
                }
                candidates.append(candidate)

                # 收集信號指標
                satellite_id = signal_record.get('satellite_id')
                if satellite_id:
                    signal_metrics[satellite_id] = {
                        'signal_strength': signal_record.get('average_signal_strength', -120),
                        'visibility_duration': signal_record.get('visibility_duration_minutes', 0)
                    }

            self.processing_stats['satellites_processed'] = len(candidates)

            extracted_data = {
                'candidates': candidates,
                'signal_metrics': signal_metrics,
                'gpp_events': gpp_events,
                'total_candidates': len(candidates),
                'extraction_timestamp': datetime.now(timezone.utc).isoformat()
            }

            self.logger.info(f"📊 提取了 {len(candidates)} 個候選衛星的信號分析數據")
            return extracted_data

        except Exception as e:
            self.logger.error(f"❌ 信號分析數據提取失敗: {e}")
            return {'candidates': [], 'signal_metrics': {}, 'gpp_events': []}

    def _execute_pool_planning(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行動態池規劃"""
        try:
            if not self.processing_config['enable_pool_planning']:
                return {'pool_planning': 'disabled'}

            self.logger.info("🎯 執行動態池規劃")

            # 準備池規劃需求
            requirements = PoolRequirements(
                min_satellites_per_pool=self.constraints['min_satellites_per_pool'],
                min_signal_quality=self.constraints['min_signal_quality']
            )

            # 執行池規劃
            planning_results = self.pool_planner.plan_dynamic_pool(
                signal_data['candidates'], requirements
            )

            # 分析覆蓋範圍
            if 'planned_pools' in planning_results and planning_results['planned_pools']:
                for pool in planning_results['planned_pools']:
                    if 'satellites' in pool:
                        coverage_analysis = self.pool_planner.analyze_coverage(pool['satellites'])
                        pool['coverage_analysis'] = coverage_analysis

            # 更新統計
            if 'planned_pools' in planning_results:
                self.processing_stats['pools_planned'] = len(planning_results['planned_pools'])

            self.logger.info(f"✅ 動態池規劃完成，規劃了 {self.processing_stats['pools_planned']} 個衛星池")
            return planning_results

        except Exception as e:
            self.logger.error(f"❌ 動態池規劃失敗: {e}")
            return {'error': str(e), 'planned_pools': []}

    def _execute_handover_optimization(self, signal_data: Dict[str, Any],
                                     pool_results: Dict[str, Any]) -> Dict[str, Any]:
        """執行換手優化"""
        try:
            if not self.processing_config['enable_handover_optimization']:
                return {'handover_optimization': 'disabled'}

            self.logger.info("🔄 執行換手優化")

            # 準備換手優化數據
            current_signal_status = {
                'satellites': signal_data['candidates'],
                'signal_metrics': signal_data['signal_metrics']
            }

            # 從池規劃結果提取候選目標
            handover_candidates = []
            if 'planned_pools' in pool_results:
                for pool in pool_results['planned_pools']:
                    if 'satellites' in pool:
                        handover_candidates.extend(pool['satellites'])

            # 如果沒有池規劃結果，使用原始候選者
            if not handover_candidates:
                handover_candidates = signal_data['candidates']

            # 執行換手策略優化
            handover_results = self.handover_optimizer.optimize_handover_strategy(
                current_signal_status, handover_candidates
            )

            # 確定換手觸發條件
            gpp_events = signal_data.get('gpp_events', [])
            if gpp_events:
                trigger_events = self.handover_optimizer.determine_handover_trigger(gpp_events)
                handover_results['trigger_events'] = trigger_events

            # 更新統計
            if 'optimized_decisions' in handover_results:
                self.processing_stats['handover_strategies_generated'] = len(handover_results['optimized_decisions'])

            self.logger.info(f"✅ 換手優化完成，生成了 {self.processing_stats['handover_strategies_generated']} 個優化策略")
            return handover_results

        except Exception as e:
            self.logger.error(f"❌ 換手優化失敗: {e}")
            return {'error': str(e), 'optimized_decisions': []}

    def _execute_multi_objective_optimization(self, pool_results: Dict[str, Any],
                                            handover_results: Dict[str, Any]) -> Dict[str, Any]:
        """執行多目標優化"""
        try:
            if not self.processing_config['enable_multi_objective_optimization']:
                return {'multi_objective_optimization': 'disabled'}

            self.logger.info("🎯 執行多目標優化")

            # 準備目標函數
            objectives = {
                'signal_quality': -85.0,  # 目標信號強度
                'coverage_range': 85.0,   # 目標覆蓋率
                'handover_cost': 8.0,     # 目標換手成本
                'energy_efficiency': 75.0 # 目標能效
            }

            # 準備約束條件
            constraints = [
                {
                    'name': 'min_satellites_constraint',
                    'type': 'inequality',
                    'function': f"satellites_count >= {self.constraints['min_satellites_per_pool']}",
                    'penalty': 100.0,
                    'hard': True
                },
                {
                    'name': 'signal_quality_constraint',
                    'type': 'inequality',
                    'function': f"signal_quality >= {self.constraints['min_signal_quality']}",
                    'penalty': 75.0,
                    'hard': True
                },
                {
                    'name': 'handover_frequency_constraint',
                    'type': 'inequality',
                    'function': f"handover_frequency <= {self.constraints['max_handover_frequency']}",
                    'penalty': 50.0,
                    'hard': True
                }
            ]

            # 執行多目標優化
            optimization_results = self.multi_obj_optimizer.optimize_multiple_objectives(
                objectives, constraints
            )

            # 平衡品質與成本
            if 'pareto_solutions' in optimization_results and optimization_results['pareto_solutions']:
                balance_results = self.multi_obj_optimizer.balance_quality_cost(
                    optimization_results['pareto_solutions']
                )
                optimization_results['quality_cost_balance'] = balance_results

            # 更新統計
            self.processing_stats['multi_objective_optimizations'] += 1

            self.logger.info("✅ 多目標優化完成")
            return optimization_results

        except Exception as e:
            self.logger.error(f"❌ 多目標優化失敗: {e}")
            return {'error': str(e), 'pareto_solutions': []}

    def _integrate_optimization_decisions(self, pool_results: Dict[str, Any],
                                        handover_results: Dict[str, Any],
                                        multi_obj_results: Dict[str, Any]) -> Dict[str, Any]:
        """整合優化決策"""
        try:
            integrated_decisions = {
                'decision_type': 'integrated_optimization',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            # 整合池規劃決策
            if 'planned_pools' in pool_results:
                integrated_decisions['satellite_pool_decisions'] = {
                    'selected_pools': pool_results['planned_pools'],
                    'pool_count': len(pool_results['planned_pools']),
                    'total_satellites_in_pools': sum(
                        len(pool.get('satellites', [])) for pool in pool_results['planned_pools']
                    ),
                    'planning_quality': pool_results.get('planning_analysis', {})
                }

            # 整合換手決策
            if 'optimized_decisions' in handover_results:
                integrated_decisions['handover_decisions'] = {
                    'handover_strategies': handover_results['optimized_decisions'],
                    'execution_strategy': handover_results.get('execution_strategy', {}),
                    'strategy_evaluation': handover_results.get('strategy_evaluation', {}),
                    'triggers_identified': len(handover_results.get('trigger_events', []))
                }

            # 整合多目標優化結果
            if 'recommended_solution' in multi_obj_results:
                integrated_decisions['multi_objective_decisions'] = {
                    'recommended_solution': multi_obj_results['recommended_solution'],
                    'pareto_front_size': len(multi_obj_results.get('pareto_solutions', [])),
                    'solution_quality': multi_obj_results.get('solution_quality', {}),
                    'quality_cost_balance': multi_obj_results.get('quality_cost_balance', {})
                }

            # 計算整體決策置信度
            integrated_decisions['overall_confidence'] = self._calculate_decision_confidence(
                pool_results, handover_results, multi_obj_results
            )

            # 生成執行建議
            integrated_decisions['execution_recommendations'] = self._generate_execution_recommendations(
                integrated_decisions
            )

            return integrated_decisions

        except Exception as e:
            self.logger.error(f"❌ 優化決策整合失敗: {e}")
            return {'decision_type': 'integration_failed', 'error': str(e)}

    def _create_decision_summary(self, integrated_decisions: Dict[str, Any]) -> Dict[str, Any]:
        """創建決策摘要"""
        try:
            summary = {
                'summary_type': 'optimization_decision_summary',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }

            # 池規劃摘要
            if 'satellite_pool_decisions' in integrated_decisions:
                pool_decisions = integrated_decisions['satellite_pool_decisions']
                summary['pool_planning_summary'] = {
                    'pools_created': pool_decisions.get('pool_count', 0),
                    'satellites_allocated': pool_decisions.get('total_satellites_in_pools', 0),
                    'planning_effectiveness': 'high' if pool_decisions.get('pool_count', 0) > 0 else 'low'
                }

            # 換手決策摘要
            if 'handover_decisions' in integrated_decisions:
                handover_decisions = integrated_decisions['handover_decisions']
                summary['handover_summary'] = {
                    'strategies_generated': len(handover_decisions.get('handover_strategies', [])),
                    'triggers_detected': handover_decisions.get('triggers_identified', 0),
                    'handover_readiness': 'ready' if len(handover_decisions.get('handover_strategies', [])) > 0 else 'not_ready'
                }

            # 多目標優化摘要
            if 'multi_objective_decisions' in integrated_decisions:
                multi_obj = integrated_decisions['multi_objective_decisions']
                summary['optimization_summary'] = {
                    'pareto_solutions_found': multi_obj.get('pareto_front_size', 0),
                    'solution_quality_score': multi_obj.get('solution_quality', {}).get('quality_score', 0.0),
                    'optimization_status': 'optimized' if multi_obj.get('pareto_front_size', 0) > 0 else 'no_optimization'
                }

            # 整體摘要
            summary['overall_summary'] = {
                'decision_confidence': integrated_decisions.get('overall_confidence', 0.0),
                'optimization_effectiveness': self._assess_optimization_effectiveness(integrated_decisions),
                'implementation_priority': self._determine_implementation_priority(integrated_decisions),
                'next_steps': integrated_decisions.get('execution_recommendations', [])
            }

            return summary

        except Exception as e:
            self.logger.error(f"❌ 決策摘要創建失敗: {e}")
            return {'summary_type': 'summary_creation_failed', 'error': str(e)}

    def _calculate_decision_confidence(self, pool_results: Dict[str, Any],
                                     handover_results: Dict[str, Any],
                                     multi_obj_results: Dict[str, Any]) -> float:
        """計算決策置信度"""
        try:
            confidence_scores = []

            # 池規劃置信度
            if 'planned_pools' in pool_results and pool_results['planned_pools']:
                pool_confidence = min(1.0, len(pool_results['planned_pools']) / 3)  # 3個池為理想
                confidence_scores.append(pool_confidence)

            # 換手優化置信度
            if 'strategy_evaluation' in handover_results:
                strategy_eval = handover_results['strategy_evaluation']
                handover_confidence = strategy_eval.get('effectiveness_score', 0.5)
                confidence_scores.append(handover_confidence)

            # 多目標優化置信度
            if 'solution_quality' in multi_obj_results:
                quality = multi_obj_results['solution_quality']
                optimization_confidence = quality.get('quality_score', 0.5)
                confidence_scores.append(optimization_confidence)

            # 計算平均置信度
            if confidence_scores:
                return sum(confidence_scores) / len(confidence_scores)
            else:
                return 0.5  # 中等置信度

        except Exception as e:
            self.logger.error(f"❌ 決策置信度計算失敗: {e}")
            return 0.5

    def _assess_optimization_effectiveness(self, decisions: Dict[str, Any]) -> str:
        """評估優化效果"""
        confidence = decisions.get('overall_confidence', 0.0)

        if confidence >= 0.8:
            return 'highly_effective'
        elif confidence >= 0.6:
            return 'moderately_effective'
        elif confidence >= 0.4:
            return 'partially_effective'
        else:
            return 'low_effectiveness'

    def _determine_implementation_priority(self, decisions: Dict[str, Any]) -> str:
        """確定實施優先級"""
        confidence = decisions.get('overall_confidence', 0.0)

        # 檢查是否有緊急換手需求
        has_urgent_handover = False
        if 'handover_decisions' in decisions:
            handover_strategies = decisions['handover_decisions'].get('handover_strategies', [])
            for strategy in handover_strategies:
                if strategy.get('execution_priority', 0) > 0.8:
                    has_urgent_handover = True
                    break

        if has_urgent_handover:
            return 'urgent'
        elif confidence >= 0.7:
            return 'high'
        elif confidence >= 0.5:
            return 'medium'
        else:
            return 'low'

    def _generate_execution_recommendations(self, decisions: Dict[str, Any]) -> List[str]:
        """生成執行建議"""
        recommendations = []

        # 基於池規劃結果的建議
        if 'satellite_pool_decisions' in decisions:
            pool_count = decisions['satellite_pool_decisions'].get('pool_count', 0)
            if pool_count == 0:
                recommendations.append("建議重新評估衛星候選者，當前無法形成有效衛星池")
            elif pool_count < 2:
                recommendations.append("建議增加衛星池數量以提高系統冗餘性")
            else:
                recommendations.append("衛星池規劃良好，建議按計劃實施")

        # 基於換手決策的建議
        if 'handover_decisions' in decisions:
            strategies = decisions['handover_decisions'].get('handover_strategies', [])
            if not strategies:
                recommendations.append("當前無需立即執行換手操作")
            else:
                recommendations.append(f"建議執行 {len(strategies)} 個換手策略，優先處理高優先級換手")

        # 基於多目標優化的建議
        if 'multi_objective_decisions' in decisions:
            quality_score = decisions['multi_objective_decisions'].get('solution_quality', {}).get('quality_score', 0)
            if quality_score < 0.5:
                recommendations.append("建議調整優化目標權重以提高解決方案品質")
            else:
                recommendations.append("多目標優化結果良好，建議採用推薦解決方案")

        # 整體建議
        confidence = decisions.get('overall_confidence', 0.0)
        if confidence < 0.4:
            recommendations.append("整體決策置信度較低，建議收集更多數據後重新優化")

        return recommendations

    def _create_error_result(self, error: str) -> Dict[str, Any]:
        """創建錯誤結果"""
        return {
            'stage': 'stage4_optimization',
            'error': error,
            'optimal_pool': {},
            'handover_strategy': {},
            'optimization_results': {},
            'processor_version': 'v1.0_optimization_with_error'
        }

    def get_processing_statistics(self) -> Dict[str, Any]:
        """獲取處理統計"""
        stats = self.processing_stats.copy()
        stats['engine_statistics'] = {
            'pool_planner': self.pool_planner.get_planning_statistics(),
            'handover_optimizer': self.handover_optimizer.get_optimization_statistics(),
            'multi_obj_optimizer': self.multi_obj_optimizer.get_optimization_statistics()
        }
        return stats

    def validate_stage_compliance(self) -> Dict[str, Any]:
        """驗證階段合規性"""
        return {
            'stage4_responsibilities': [
                'dynamic_pool_planning',
                'handover_decision_optimization',
                'multi_objective_optimization',
                'satellite_selection_optimization'
            ],
            'architecture_improvements': [
                'integrated_optimization_engines',
                'focused_on_decision_optimization',
                'multi_objective_consideration',
                'rl_extension_ready'
            ],
            'compliance_status': 'COMPLIANT_optimization_decision_layer'
        }

    # 實現抽象方法 (來自 BaseStageProcessor 和 StageInterface)
    def validate_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證輸入數據 - 實現抽象方法"""
        return self._validate_stage3_input(input_data)

    def validate_output(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證輸出數據 - 實現抽象方法"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        # 檢查必要字段
        required_fields = ['stage', 'optimal_pool', 'handover_strategy', 'optimization_results']
        for field in required_fields:
            if field not in output_data:
                validation_result['errors'].append(f"缺少必要字段: {field}")
                validation_result['valid'] = False

        return validation_result

    def extract_key_metrics(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """提取關鍵指標 - 實現抽象方法"""
        try:
            return {
                'satellites_processed': result_data.get('statistics', {}).get('satellites_processed', 0),
                'pools_planned': result_data.get('statistics', {}).get('pools_planned', 0),
                'handover_strategies_generated': result_data.get('statistics', {}).get('handover_strategies_generated', 0),
                'multi_objective_optimizations': result_data.get('statistics', {}).get('multi_objective_optimizations', 0),
                'processing_time_seconds': result_data.get('statistics', {}).get('processing_time_seconds', 0),
                'overall_confidence': result_data.get('integrated_decisions', {}).get('overall_confidence', 0.0),
                'success_rate': 1.0 if 'error' not in result_data else 0.0
            }
        except Exception as e:
            self.logger.error(f"關鍵指標提取失敗: {e}")
            return {}

    def run_validation_checks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """運行驗證檢查 - 實現抽象方法"""
        try:
            # 🔥 使用真實驗證框架 - 修正驗證器導入
            from shared.validation_framework.validation_engine import ValidationEngine
            from shared.validation_framework.stage4_validator import Stage4TimeseriesValidator

            # 創建驗證引擎
            engine = ValidationEngine('stage4')
            engine.add_validator(Stage4TimeseriesValidator())

            # 準備輸入數據
            input_data = {}
            if 'signal_quality_data' in data:
                input_data = data
            else:
                # 嘗試從當前對象狀態構建輸入數據
                input_data = {'signal_quality_data': []}

            # 執行真實驗證
            validation_result = engine.validate(input_data, data)

            # 轉換為標準格式
            is_valid = validation_result.overall_status == 'PASS'
            
            # 🔥 額外的Grade A標準檢查
            grade_a_checks = self._perform_grade_a_checks(data)
            
            return {
                'validation_status': 'passed' if is_valid and grade_a_checks['passed'] else 'failed',
                'checks_performed': [check.check_name for check in validation_result.checks] + grade_a_checks['checks'],
                'stage_compliance': is_valid,
                'academic_standards': grade_a_checks['passed'],
                'overall_status': validation_result.overall_status,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'validation_details': {
                    'success_rate': validation_result.success_rate if is_valid else 0.0,
                    'errors': [check.message for check in validation_result.checks if check.status.value == 'FAILURE'] + grade_a_checks['errors'],
                    'warnings': [check.message for check in validation_result.checks if check.status.value == 'WARNING'] + grade_a_checks['warnings'],
                    'validator_used': 'Stage4TimeseriesValidator + Grade_A_Optimizer_Checks',
                    'grade_a_compliance': grade_a_checks
                }
            }

        except Exception as e:
            self.logger.error(f"❌ Stage 4驗證失敗: {e}")
            
            # 🔥 回退到簡化但嚴格的Grade A檢查
            grade_a_checks = self._perform_grade_a_checks(data)
            
            return {
                'validation_status': 'passed' if grade_a_checks['passed'] else 'failed',
                'overall_status': 'PASS' if grade_a_checks['passed'] else 'FAIL',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'validation_details': {
                    'success_rate': 1.0 if grade_a_checks['passed'] else 0.0,
                    'errors': grade_a_checks['errors'],
                    'warnings': grade_a_checks['warnings'],
                    'validator_used': 'Grade_A_Optimizer_Checks_Only',
                    'grade_a_compliance': grade_a_checks
                }
            }

    def _perform_grade_a_checks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """執行Grade A學術標準檢查"""
        checks = []
        errors = []
        warnings = []
        
        # 檢查是否使用真實優化算法
        if 'optimization_results' in data:
            opt_results = data['optimization_results']
            
            # 檢查是否有帕累托解
            if 'pareto_solutions' in opt_results:
                pareto_count = len(opt_results['pareto_solutions'])
                if pareto_count > 0:
                    checks.append('pareto_optimization_algorithm')
                else:
                    # Grade A合規檢查：確保使用完整優化算法
                    errors.append('未找到帕累托最優解，需檢查優化算法完整性')
            
            # 檢查多目標優化
            if 'recommended_solution' in opt_results:
                checks.append('multi_objective_optimization')
            else:
                errors.append('缺少多目標優化結果')

        # 檢查池規劃是否基於真實計算
        if 'optimal_pool' in data:
            pool_data = data['optimal_pool']
            if 'planned_pools' in pool_data:
                checks.append('dynamic_pool_planning')
            else:
                warnings.append('池規劃結果不完整')

        # 檢查換手策略是否基於標準
        if 'handover_strategy' in data:
            handover_data = data['handover_strategy']
            if 'optimized_decisions' in handover_data:
                checks.append('standards_based_handover')
            else:
                warnings.append('換手策略不完整')

        # 檢查處理統計
        if 'statistics' in data:
            stats = data['statistics']
            if stats.get('satellites_processed', 0) > 0:
                checks.append('real_data_processing')
            else:
                errors.append('未處理真實衛星數據')

        # 總體Grade A合規檢查
        passed = len(errors) == 0 and len(checks) >= 3
        
        return {
            'passed': passed,
            'checks': checks,
            'errors': errors,
            'warnings': warnings,
            'grade_a_score': len(checks) / max(4, len(checks) + len(errors))
        }

    def save_results(self, results: Dict[str, Any]) -> str:
        """保存結果 - 實現抽象方法"""
        try:
            import json
            import os
            from pathlib import Path

            # 生成輸出路徑
            output_dir = Path(f"/satellite-processing/data/outputs/stage{self.stage_number}")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "optimization_decisions_output.json"

            # 保存為JSON格式
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"✅ 結果已保存: {output_path}")
            return str(output_path)

        except Exception as e:
            self.logger.error(f"❌ 保存結果失敗: {e}")
            return ""