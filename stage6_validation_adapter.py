#!/usr/bin/env python3
"""
Stage 6 Validation Adapter - 動態池規劃處理器驗證轉接器
Phase 3 驗證框架整合：動態資源池規劃算法與優化策略驗證
"""

from typing import List, Dict, Any, Optional
import logging
import json
import asyncio
from datetime import datetime, timezone
import math

# 設置日誌
logger = logging.getLogger(__name__)

class Stage6ValidationAdapter:
    """Stage 6 動態池規劃處理驗證轉接器 - Zero Intrusion Integration"""
    
    def __init__(self):
        """初始化 Stage 6 驗證轉接器"""
        self.stage_name = "stage6_dynamic_pool_planning"
        self.validation_engines = {}
        
        # 動態池規劃驗證標準
        self.POOL_PLANNING_STANDARDS = {
            'min_pool_size': 3,  # 最小池大小
            'max_pool_size': 50,  # 最大池大小
            'resource_utilization_threshold': 0.85,  # 資源利用率門檻
            'load_balancing_quality_threshold': 0.9,  # 負載平衡品質門檻
            'optimization_convergence_required': True,  # 需要優化收斂
        }
        
        # 學術級演算法標準 
        self.ACADEMIC_STANDARDS = {
            'grade_a_requirements': {
                'proven_optimization_algorithms': True,
                'mathematical_convergence_proof': True,
                'complexity_analysis_documented': True,
                'benchmarking_against_standards': True
            },
            'grade_b_requirements': {
                'established_heuristics_used': True,
                'performance_metrics_documented': True,
                'algorithm_rationale_explained': True
            },
            'grade_c_violations': {
                'random_allocation_strategy': True,
                'unproven_heuristics': True,
                'no_optimization_objective': True,
                'arbitrary_resource_assignment': True
            }
        }
        
        try:
            # 初始化驗證引擎
            self._initialize_validation_engines()
            logger.info("✅ Stage 6 驗證轉接器初始化成功")
            
        except Exception as e:
            logger.error(f"❌ Stage 6 驗證引擎初始化失敗: {e}")
            self.validation_engines = {}

    def _initialize_validation_engines(self):
        """初始化驗證引擎"""
        self.validation_engines = {
            'pool_configuration': self._validate_pool_configuration,
            'optimization_algorithm': self._validate_optimization_algorithm,
            'resource_allocation': self._validate_resource_allocation,
            'load_balancing': self._validate_load_balancing,
            'academic_standards': self._validate_academic_standards
        }
        
    async def pre_process_validation(self, input_data: Dict[str, Any], 
                                   context: Dict[str, Any] = None) -> Dict[str, Any]:
        """預處理驗證 - 動態池規劃前檢查"""
        validation_start = datetime.now(timezone.utc)
        
        try:
            # 準備驗證上下文
            validation_context = {
                'stage_id': 'stage6_dynamic_pool_planning',
                'phase': 'pre_process',
                'input_satellites_count': self._count_input_satellites(input_data),
                'validation_timestamp': validation_start.isoformat(),
                'context': context or {}
            }
            
            logger.info(f"🔍 Stage 6 預處理驗證開始: {validation_context['input_satellites_count']} 顆衛星")
            
            # 驗證結果收集
            validation_results = {
                'success': True,
                'warnings': [],
                'blocking_errors': [],
                'validation_summary': {}
            }
            
            # 1. 池配置預檢查
            pool_config_result = await self._validate_pool_configuration(input_data)
            validation_results['validation_summary']['pool_configuration'] = pool_config_result
            if not pool_config_result['success']:
                validation_results['blocking_errors'].extend(pool_config_result.get('errors', []))
            
            # 2. 優化算法預檢查
            algorithm_result = await self._validate_optimization_algorithm(input_data, 'pre_process')
            validation_results['validation_summary']['optimization_algorithm'] = algorithm_result
            if not algorithm_result['success']:
                validation_results['warnings'].extend(algorithm_result.get('warnings', []))
            
            # 3. 學術標準檢查
            academic_result = await self._validate_academic_standards(input_data, 'pre_process')
            validation_results['validation_summary']['academic_compliance'] = academic_result
            if not academic_result['success']:
                validation_results['blocking_errors'].extend(academic_result.get('violations', []))
            
            # 決定整體驗證結果
            if validation_results['blocking_errors']:
                validation_results['success'] = False
                logger.error(f"🚨 Stage 6 預處理驗證失敗: {len(validation_results['blocking_errors'])} 個阻斷性錯誤")
            else:
                logger.info("✅ Stage 6 預處理驗證通過")
            
            # 記錄驗證時間
            validation_end = datetime.now(timezone.utc)
            validation_results['validation_duration'] = (validation_end - validation_start).total_seconds()
            
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Stage 6 預處理驗證異常: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'validation_timestamp': validation_start.isoformat()
            }
    
    async def post_process_validation(self, output_data: Dict[str, Any], 
                                    processing_metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """後處理驗證 - 動態池規劃結果檢查"""
        validation_start = datetime.now(timezone.utc)
        
        try:
            logger.info("🔍 Stage 6 後處理驗證開始")
            
            # 驗證結果收集
            validation_results = {
                'success': True,
                'warnings': [],
                'academic_compliance': {},
                'quality_metrics': {}
            }
            
            # 1. 資源分配檢查
            allocation_result = await self._validate_resource_allocation(output_data)
            validation_results['quality_metrics']['resource_allocation'] = allocation_result
            
            if not allocation_result['success']:
                validation_results['success'] = False
                validation_results['error'] = f"資源分配檢查失敗: {allocation_result.get('errors', [])}"
            
            # 2. 負載平衡檢查
            load_balancing_result = await self._validate_load_balancing(output_data)
            validation_results['quality_metrics']['load_balancing'] = load_balancing_result
            
            # 3. 優化算法後處理檢查
            algorithm_result = await self._validate_optimization_algorithm(output_data, 'post_process')
            validation_results['quality_metrics']['optimization_algorithm'] = algorithm_result
            
            # 4. 學術標準後處理檢查
            academic_result = await self._validate_academic_standards(output_data, 'post_process')
            validation_results['academic_compliance'] = academic_result
            
            # 品質門禁檢查
            if academic_result.get('grade_level') == 'C' or not academic_result.get('compliant', True):
                validation_results['success'] = False
                validation_results['error'] = "Quality gate blocked: 學術標準不符，發現Grade C違規項目"
                logger.error("🚨 品質門禁阻斷: Stage 6動態池規劃不符合學術標準")
            
            # 5. 處理指標驗證
            if processing_metrics:
                metrics_validation = self._validate_processing_metrics(processing_metrics)
                validation_results['quality_metrics']['processing_metrics'] = metrics_validation
            
            # 記錄驗證時間
            validation_end = datetime.now(timezone.utc)
            validation_results['validation_duration'] = (validation_end - validation_start).total_seconds()
            
            if validation_results['success']:
                logger.info("✅ Stage 6 後處理驗證通過")
            else:
                logger.error(f"🚨 Stage 6 後處理驗證失敗: {validation_results.get('error', '未知錯誤')}")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Stage 6 後處理驗證異常: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'validation_timestamp': validation_start.isoformat()
            }
    
    async def _validate_pool_configuration(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證動態池配置"""
        try:
            errors = []
            warnings = []
            config_analysis = {
                'total_pools': 0,
                'average_pool_size': 0,
                'pool_size_distribution': {},
                'configuration_valid': True
            }
            
            # 檢查動態池配置
            if 'dynamic_pools' in data:
                pools_data = data['dynamic_pools']
                
                if isinstance(pools_data, dict):
                    pool_sizes = []
                    
                    for pool_id, pool_data in pools_data.items():
                        config_analysis['total_pools'] += 1
                        
                        # 檢查池大小
                        if 'satellites' in pool_data:
                            pool_size = len(pool_data['satellites'])
                            pool_sizes.append(pool_size)
                            
                            # 驗證池大小範圍
                            if pool_size < self.POOL_PLANNING_STANDARDS['min_pool_size']:
                                errors.append(f"池 {pool_id} 大小不足: {pool_size} < {self.POOL_PLANNING_STANDARDS['min_pool_size']}")
                                config_analysis['configuration_valid'] = False
                            
                            if pool_size > self.POOL_PLANNING_STANDARDS['max_pool_size']:
                                warnings.append(f"池 {pool_id} 大小過大: {pool_size} > {self.POOL_PLANNING_STANDARDS['max_pool_size']}")
                    
                    # 計算統計數據
                    if pool_sizes:
                        config_analysis['average_pool_size'] = sum(pool_sizes) / len(pool_sizes)
                        config_analysis['pool_size_distribution'] = {
                            'min': min(pool_sizes),
                            'max': max(pool_sizes),
                            'std_dev': self._calculate_std_dev(pool_sizes)
                        }
                else:
                    errors.append("動態池數據格式無效")
            else:
                errors.append("缺少動態池配置數據")
            
            # 判斷結果
            success = len(errors) == 0 and config_analysis['configuration_valid']
            
            return {
                'success': success,
                'errors': errors,
                'warnings': warnings,
                'config_analysis': config_analysis
            }
            
        except Exception as e:
            logger.error(f"池配置驗證失敗: {e}")
            return {'success': False, 'errors': [str(e)]}
    
    async def _validate_optimization_algorithm(self, data: Dict[str, Any], phase: str) -> Dict[str, Any]:
        """驗證優化算法"""
        try:
            warnings = []
            algorithm_analysis = {
                'algorithm_type': 'unknown',
                'convergence_detected': False,
                'optimization_objective_clear': False,
                'performance_metrics_available': False
            }
            
            # 檢查優化相關數據
            data_str = json.dumps(data, default=str).lower()
            
            # 識別算法類型
            if any(term in data_str for term in ['genetic', 'evolutionary']):
                algorithm_analysis['algorithm_type'] = 'evolutionary'
            elif any(term in data_str for term in ['gradient', 'descent']):
                algorithm_analysis['algorithm_type'] = 'gradient_based'
            elif any(term in data_str for term in ['greedy', 'heuristic']):
                algorithm_analysis['algorithm_type'] = 'heuristic'
            elif any(term in data_str for term in ['random', 'stochastic']):
                algorithm_analysis['algorithm_type'] = 'stochastic'
                warnings.append("檢測到隨機策略，可能不符合學術要求")
            
            # 檢查收斂性
            if any(term in data_str for term in ['converged', 'convergence', 'optimal']):
                algorithm_analysis['convergence_detected'] = True
            
            # 檢查優化目標
            if any(term in data_str for term in ['objective', 'minimize', 'maximize', 'optimize']):
                algorithm_analysis['optimization_objective_clear'] = True
            else:
                warnings.append("未明確定義優化目標")
            
            # 檢查性能指標
            if any(term in data_str for term in ['performance', 'efficiency', 'utilization', 'throughput']):
                algorithm_analysis['performance_metrics_available'] = True
            
            # 判斷算法品質
            algorithm_quality_score = sum([
                algorithm_analysis['convergence_detected'],
                algorithm_analysis['optimization_objective_clear'],
                algorithm_analysis['performance_metrics_available'],
                algorithm_analysis['algorithm_type'] not in ['unknown', 'stochastic']
            ])
            
            success = algorithm_quality_score >= 3  # 至少滿足3個條件
            
            return {
                'success': success,
                'warnings': warnings,
                'algorithm_analysis': algorithm_analysis,
                'quality_score': algorithm_quality_score
            }
            
        except Exception as e:
            logger.error(f"優化算法驗證失敗: {e}")
            return {'success': False, 'errors': [str(e)]}
    
    async def _validate_resource_allocation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證資源分配"""
        try:
            errors = []
            allocation_metrics = {
                'total_resources': 0,
                'allocated_resources': 0,
                'utilization_rate': 0.0,
                'allocation_efficiency': 0.0,
                'resource_distribution_balance': 0.0
            }
            
            # 檢查資源分配結果
            if 'dynamic_pools' in data:
                pools_data = data['dynamic_pools']
                pool_sizes = []
                total_satellites = 0
                
                for pool_id, pool_data in pools_data.items():
                    if 'satellites' in pool_data:
                        pool_size = len(pool_data['satellites'])
                        pool_sizes.append(pool_size)
                        total_satellites += pool_size
                
                allocation_metrics['total_resources'] = total_satellites
                allocation_metrics['allocated_resources'] = total_satellites
                allocation_metrics['utilization_rate'] = 1.0  # 假設全部分配
                
                # 計算分配效率（基於池大小的均勻性）
                if pool_sizes and len(pool_sizes) > 1:
                    mean_size = sum(pool_sizes) / len(pool_sizes)
                    variance = sum((x - mean_size) ** 2 for x in pool_sizes) / len(pool_sizes)
                    std_dev = math.sqrt(variance)
                    
                    # 效率分數基於變異係數的倒數
                    cv = std_dev / mean_size if mean_size > 0 else 1
                    allocation_metrics['allocation_efficiency'] = max(0, 1 - cv)
                    allocation_metrics['resource_distribution_balance'] = allocation_metrics['allocation_efficiency']
                
                # 檢查分配品質
                if allocation_metrics['allocation_efficiency'] < 0.7:
                    errors.append(f"資源分配效率過低: {allocation_metrics['allocation_efficiency']:.2f} < 0.7")
                
                # 檢查利用率
                if allocation_metrics['utilization_rate'] < self.POOL_PLANNING_STANDARDS['resource_utilization_threshold']:
                    errors.append(f"資源利用率不足: {allocation_metrics['utilization_rate']:.2f}")
            else:
                errors.append("缺少動態池資源分配數據")
            
            success = len(errors) == 0
            
            return {
                'success': success,
                'errors': errors,
                'allocation_metrics': allocation_metrics
            }
            
        except Exception as e:
            logger.error(f"資源分配驗證失敗: {e}")
            return {'success': False, 'errors': [str(e)]}
    
    async def _validate_load_balancing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證負載平衡"""
        try:
            warnings = []
            load_balance_metrics = {
                'load_variance': 0.0,
                'balance_quality': 0.0,
                'hotspot_detected': False,
                'balanced_distribution': True
            }
            
            # 檢查負載平衡
            if 'dynamic_pools' in data:
                pools_data = data['dynamic_pools']
                pool_loads = []
                
                for pool_id, pool_data in pools_data.items():
                    # 計算池負載（基於衛星數量）
                    load = len(pool_data.get('satellites', []))
                    pool_loads.append(load)
                
                if len(pool_loads) > 1:
                    # 計算負載平衡指標
                    mean_load = sum(pool_loads) / len(pool_loads)
                    variance = sum((load - mean_load) ** 2 for load in pool_loads) / len(pool_loads)
                    load_balance_metrics['load_variance'] = variance
                    
                    # 平衡品質分數
                    if mean_load > 0:
                        cv = math.sqrt(variance) / mean_load
                        load_balance_metrics['balance_quality'] = max(0, 1 - cv)
                    
                    # 檢測熱點
                    max_load = max(pool_loads)
                    if max_load > mean_load * 1.5:
                        load_balance_metrics['hotspot_detected'] = True
                        warnings.append(f"檢測到熱點池，負載: {max_load} > 平均值 * 1.5")
                    
                    # 判斷分布是否平衡
                    if load_balance_metrics['balance_quality'] < self.POOL_PLANNING_STANDARDS['load_balancing_quality_threshold']:
                        load_balance_metrics['balanced_distribution'] = False
                        warnings.append(f"負載平衡品質不足: {load_balance_metrics['balance_quality']:.2f}")
            
            success = load_balance_metrics['balanced_distribution'] and not load_balance_metrics['hotspot_detected']
            
            return {
                'success': success,
                'warnings': warnings,
                'load_balance_metrics': load_balance_metrics
            }
            
        except Exception as e:
            logger.error(f"負載平衡驗證失敗: {e}")
            return {'success': False, 'errors': [str(e)]}
    
    async def _validate_academic_standards(self, data: Dict[str, Any], phase: str) -> Dict[str, Any]:
        """驗證學術標準合規性"""
        try:
            violations = []
            compliance_score = 0
            total_checks = 0
            
            # Grade A 檢查：證明的優化算法
            total_checks += 1
            if self._check_proven_optimization_algorithms(data):
                compliance_score += 1
            else:
                violations.append("未使用經過證明的優化算法 (Grade A 要求)")
            
            # Grade A 檢查：複雜度分析文檔
            total_checks += 1
            if self._check_complexity_analysis_documentation(data):
                compliance_score += 1
            else:
                violations.append("缺少算法複雜度分析文檔 (Grade A 要求)")
            
            # Grade A 檢查：與標準比較
            total_checks += 1
            if self._check_benchmarking_against_standards(data):
                compliance_score += 1
            else:
                violations.append("缺少與標準算法的比較基準 (Grade A 要求)")
            
            # Grade C 檢查：禁止項目
            forbidden_patterns = self._check_forbidden_planning_patterns(data)
            if forbidden_patterns:
                violations.extend([f"發現禁止模式: {pattern} (Grade C 違規)" for pattern in forbidden_patterns])
            
            # 計算合規等級
            compliance_rate = compliance_score / max(total_checks, 1) if total_checks > 0 else 0
            
            if compliance_rate >= 0.9 and not violations:
                grade_level = 'A'
                compliant = True
            elif compliance_rate >= 0.7 and len(violations) <= 2:
                grade_level = 'B'
                compliant = True
            else:
                grade_level = 'C'
                compliant = False
            
            return {
                'success': compliant,
                'compliant': compliant,
                'grade_level': grade_level,
                'compliance_rate': compliance_rate,
                'violations': violations,
                'checks_performed': total_checks
            }
            
        except Exception as e:
            logger.error(f"學術標準驗證失敗: {e}")
            return {
                'success': False,
                'compliant': False,
                'grade_level': 'C',
                'violations': [str(e)]
            }
    
    def _count_input_satellites(self, data: Dict[str, Any]) -> int:
        """統計輸入衛星數量"""
        try:
            total = 0
            if 'satellites' in data:
                satellites = data['satellites']
                for constellation, const_data in satellites.items():
                    if isinstance(const_data, dict) and 'satellites' in const_data:
                        total += len(const_data['satellites'])
            return total
        except:
            return 0
    
    def _calculate_std_dev(self, values: List[float]) -> float:
        """計算標準偏差"""
        if len(values) <= 1:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)
    
    def _check_proven_optimization_algorithms(self, data: Dict[str, Any]) -> bool:
        """檢查是否使用經過證明的優化算法"""
        try:
            data_str = json.dumps(data, default=str).lower()
            proven_algorithms = [
                'dijkstra', 'bellman', 'floyd', 'a*', 'genetic_algorithm',
                'simulated_annealing', 'particle_swarm', 'linear_programming',
                'integer_programming', 'dynamic_programming'
            ]
            
            return any(algorithm in data_str for algorithm in proven_algorithms)
        except:
            return False
    
    def _check_complexity_analysis_documentation(self, data: Dict[str, Any]) -> bool:
        """檢查算法複雜度分析文檔"""
        try:
            data_str = json.dumps(data, default=str).lower()
            complexity_indicators = [
                'complexity', 'big_o', 'time_complexity', 'space_complexity',
                'computational_complexity', 'algorithm_analysis'
            ]
            
            return any(indicator in data_str for indicator in complexity_indicators)
        except:
            return False
    
    def _check_benchmarking_against_standards(self, data: Dict[str, Any]) -> bool:
        """檢查與標準算法的比較基準"""
        try:
            data_str = json.dumps(data, default=str).lower()
            benchmark_indicators = [
                'benchmark', 'comparison', 'baseline', 'standard_algorithm',
                'performance_comparison', 'competitive_analysis'
            ]
            
            return any(indicator in data_str for indicator in benchmark_indicators)
        except:
            return False
    
    def _check_forbidden_planning_patterns(self, data: Dict[str, Any]) -> List[str]:
        """檢查禁止的規劃模式"""
        forbidden = []
        
        try:
            data_str = json.dumps(data, default=str).lower()
            
            if 'random' in data_str and 'allocation' in data_str:
                forbidden.append("隨機資源分配策略")
            
            if 'arbitrary' in data_str and ('assignment' in data_str or 'planning' in data_str):
                forbidden.append("任意分配策略")
            
            if 'no_optimization' in data_str or 'without_optimization' in data_str:
                forbidden.append("無優化目標策略")
            
            if 'greedy_only' in data_str or 'simple_greedy' in data_str:
                forbidden.append("純貪婪算法（無證明支持）")
        
        except:
            pass
        
        return forbidden
    
    def _validate_processing_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """驗證處理指標"""
        try:
            validation_result = {
                'success': True,
                'issues': []
            }
            
            # 檢查基本指標
            required_metrics = ['input_satellites', 'allocated_pools', 'optimization_time']
            for metric in required_metrics:
                if metric not in metrics:
                    validation_result['issues'].append(f"缺少必要指標: {metric}")
                    validation_result['success'] = False
            
            # 檢查優化效率
            if 'optimization_time' in metrics and metrics['optimization_time'] > 1800:  # 30分鐘
                validation_result['issues'].append("優化時間過長，可能存在算法效率問題")
            
            # 檢查分配品質
            if 'allocation_quality' in metrics and metrics['allocation_quality'] < 0.8:
                validation_result['issues'].append("分配品質不足80%")
            
            return validation_result
            
        except Exception as e:
            return {
                'success': False,
                'issues': [str(e)]
            }