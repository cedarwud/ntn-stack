"""
📊 性能分析引擎

統一的算法性能評估、比較和 A/B 測試框架。
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

from .interfaces import HandoverAlgorithm, HandoverContext, HandoverDecision
from .orchestrator import HandoverOrchestrator
from .registry import AlgorithmRegistry

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """指標類型"""
    LATENCY = "latency"
    SUCCESS_RATE = "success_rate"
    HANDOVER_FREQUENCY = "handover_frequency"
    NETWORK_EFFICIENCY = "network_efficiency"
    USER_SATISFACTION = "user_satisfaction"
    RESOURCE_UTILIZATION = "resource_utilization"
    DECISION_CONFIDENCE = "decision_confidence"
    ALGORITHM_RESPONSE_TIME = "algorithm_response_time"


@dataclass
class PerformanceMetric:
    """性能指標數據結構"""
    algorithm_name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    context_info: Dict[str, Any]
    scenario: str = "default"


@dataclass
class ComparisonResult:
    """算法比較結果"""
    algorithm_a: str
    algorithm_b: str
    metric_type: MetricType
    a_mean: float
    b_mean: float
    a_std: float
    b_std: float
    statistical_significance: float
    winner: Optional[str]
    improvement_percentage: float
    sample_size_a: int
    sample_size_b: int
    confidence_interval: Tuple[float, float]


@dataclass
class ABTestResult:
    """A/B 測試結果"""
    test_id: str
    algorithms: List[str]
    traffic_split: Dict[str, float]
    start_time: datetime
    end_time: Optional[datetime]
    total_requests: int
    results_by_algorithm: Dict[str, Dict[MetricType, float]]
    overall_winner: Optional[str]
    statistical_significance: Dict[str, float]
    recommendations: List[str]


class PerformanceAnalysisEngine:
    """性能分析引擎
    
    提供全面的算法性能分析功能：
    - 實時性能監控
    - 算法間比較分析
    - A/B 測試管理
    - 統計分析和報告生成
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化性能分析引擎
        
        Args:
            config: 分析引擎配置
        """
        self.config = config or {}
        
        # 性能數據存儲
        self.metrics_storage = []
        self.max_storage_size = self.config.get('max_storage_size', 10000)
        
        # A/B 測試管理
        self.active_ab_tests = {}
        self.completed_ab_tests = {}
        
        # 統計配置
        self.confidence_level = self.config.get('confidence_level', 0.95)
        self.min_sample_size = self.config.get('min_sample_size', 30)
        
        # 結果存儲路徑
        self.results_dir = Path(self.config.get('results_dir', 'analysis_results'))
        self.results_dir.mkdir(exist_ok=True)
        
        # 組件引用
        self.algorithm_registry = None
        self.orchestrator = None
        
        logger.info("性能分析引擎初始化完成")
    
    def set_components(self, algorithm_registry: AlgorithmRegistry, orchestrator: HandoverOrchestrator):
        """設置組件引用
        
        Args:
            algorithm_registry: 算法註冊中心
            orchestrator: 協調器
        """
        self.algorithm_registry = algorithm_registry
        self.orchestrator = orchestrator
    
    def record_metric(self, metric: PerformanceMetric) -> None:
        """記錄性能指標
        
        Args:
            metric: 性能指標
        """
        self.metrics_storage.append(metric)
        
        # 限制存儲大小
        if len(self.metrics_storage) > self.max_storage_size:
            self.metrics_storage = self.metrics_storage[-self.max_storage_size:]
        
        # 記錄到活躍的 A/B 測試
        for test_id, ab_test in self.active_ab_tests.items():
            if metric.algorithm_name in ab_test['algorithms']:
                self._update_ab_test_metrics(test_id, metric)
    
    def record_decision_metrics(self, algorithm_name: str, context: HandoverContext, 
                              decision: HandoverDecision) -> None:
        """記錄決策相關指標
        
        Args:
            algorithm_name: 算法名稱
            context: 換手上下文
            decision: 換手決策
        """
        timestamp = datetime.now()
        scenario = context.scenario_info.get('type', 'default') if context.scenario_info else 'default'
        
        # 記錄決策信心度
        confidence_metric = PerformanceMetric(
            algorithm_name=algorithm_name,
            metric_type=MetricType.DECISION_CONFIDENCE,
            value=decision.confidence,
            timestamp=timestamp,
            context_info={
                'ue_id': context.ue_id,
                'current_satellite': context.current_satellite,
                'candidate_count': len(context.candidate_satellites) if context.candidate_satellites else 0
            },
            scenario=scenario
        )
        self.record_metric(confidence_metric)
        
        # 記錄算法響應時間
        if decision.decision_time > 0:
            response_time_metric = PerformanceMetric(
                algorithm_name=algorithm_name,
                metric_type=MetricType.ALGORITHM_RESPONSE_TIME,
                value=decision.decision_time,
                timestamp=timestamp,
                context_info={'decision_type': decision.handover_decision.name},
                scenario=scenario
            )
            self.record_metric(response_time_metric)
    
    def get_algorithm_performance(self, algorithm_name: str, 
                                metric_type: MetricType,
                                time_window: Optional[timedelta] = None,
                                scenario: Optional[str] = None) -> Dict[str, float]:
        """獲取算法性能統計
        
        Args:
            algorithm_name: 算法名稱
            metric_type: 指標類型
            time_window: 時間窗口
            scenario: 場景過濾
            
        Returns:
            Dict[str, float]: 性能統計
        """
        # 過濾指標
        filtered_metrics = self._filter_metrics(
            algorithm_name=algorithm_name,
            metric_type=metric_type,
            time_window=time_window,
            scenario=scenario
        )
        
        if not filtered_metrics:
            return {'count': 0, 'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0}
        
        values = [m.value for m in filtered_metrics]
        
        return {
            'count': len(values),
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'median': np.median(values),
            'percentile_95': np.percentile(values, 95),
            'percentile_99': np.percentile(values, 99)
        }
    
    def compare_algorithms(self, algorithm_a: str, algorithm_b: str,
                         metric_type: MetricType,
                         time_window: Optional[timedelta] = None,
                         scenario: Optional[str] = None) -> ComparisonResult:
        """比較兩個算法的性能
        
        Args:
            algorithm_a: 算法A名稱
            algorithm_b: 算法B名稱
            metric_type: 比較指標
            time_window: 時間窗口
            scenario: 場景過濾
            
        Returns:
            ComparisonResult: 比較結果
        """
        # 獲取兩個算法的指標數據
        metrics_a = self._filter_metrics(algorithm_a, metric_type, time_window, scenario)
        metrics_b = self._filter_metrics(algorithm_b, metric_type, time_window, scenario)
        
        values_a = [m.value for m in metrics_a]
        values_b = [m.value for m in metrics_b]
        
        if len(values_a) < self.min_sample_size or len(values_b) < self.min_sample_size:
            logger.warning(f"樣本量不足，無法進行可靠的統計比較")
        
        # 計算統計數據
        mean_a = np.mean(values_a) if values_a else 0.0
        mean_b = np.mean(values_b) if values_b else 0.0
        std_a = np.std(values_a) if values_a else 0.0
        std_b = np.std(values_b) if values_b else 0.0
        
        # 統計顯著性檢驗 (t-test)
        statistical_significance = 0.0
        winner = None
        improvement_percentage = 0.0
        confidence_interval = (0.0, 0.0)
        
        if len(values_a) >= self.min_sample_size and len(values_b) >= self.min_sample_size:
            try:
                from scipy import stats
                t_stat, p_value = stats.ttest_ind(values_a, values_b)
                statistical_significance = p_value
                
                # 確定勝者 (根據指標類型決定高低優劣)
                if self._is_higher_better(metric_type):
                    if mean_a > mean_b and p_value < (1 - self.confidence_level):
                        winner = algorithm_a
                        improvement_percentage = ((mean_a - mean_b) / mean_b) * 100 if mean_b > 0 else 0
                    elif mean_b > mean_a and p_value < (1 - self.confidence_level):
                        winner = algorithm_b
                        improvement_percentage = ((mean_b - mean_a) / mean_a) * 100 if mean_a > 0 else 0
                else:
                    if mean_a < mean_b and p_value < (1 - self.confidence_level):
                        winner = algorithm_a
                        improvement_percentage = ((mean_b - mean_a) / mean_b) * 100 if mean_b > 0 else 0
                    elif mean_b < mean_a and p_value < (1 - self.confidence_level):
                        winner = algorithm_b
                        improvement_percentage = ((mean_a - mean_b) / mean_a) * 100 if mean_a > 0 else 0
                
                # 計算置信區間
                confidence_interval = stats.t.interval(
                    self.confidence_level,
                    len(values_a) + len(values_b) - 2,
                    loc=mean_a - mean_b,
                    scale=np.sqrt(std_a**2/len(values_a) + std_b**2/len(values_b))
                )
                
            except ImportError:
                logger.warning("scipy 不可用，跳過統計檢驗")
        
        return ComparisonResult(
            algorithm_a=algorithm_a,
            algorithm_b=algorithm_b,
            metric_type=metric_type,
            a_mean=mean_a,
            b_mean=mean_b,
            a_std=std_a,
            b_std=std_b,
            statistical_significance=statistical_significance,
            winner=winner,
            improvement_percentage=improvement_percentage,
            sample_size_a=len(values_a),
            sample_size_b=len(values_b),
            confidence_interval=confidence_interval
        )
    
    def start_ab_test(self, test_id: str, algorithms: List[str], 
                     traffic_split: Dict[str, float],
                     duration_hours: Optional[float] = None) -> bool:
        """啟動 A/B 測試
        
        Args:
            test_id: 測試ID
            algorithms: 參與測試的算法列表
            traffic_split: 流量分配比例
            duration_hours: 測試持續時間（小時）
            
        Returns:
            bool: 是否成功啟動
        """
        if test_id in self.active_ab_tests:
            logger.error(f"A/B 測試 '{test_id}' 已經在運行中")
            return False
        
        # 驗證流量分配
        total_split = sum(traffic_split.values())
        if abs(total_split - 1.0) > 0.01:
            logger.error(f"流量分配總和必須為 1.0，當前為 {total_split}")
            return False
        
        # 驗證算法存在
        for algorithm in algorithms:
            if not self.algorithm_registry or not self.algorithm_registry.is_registered(algorithm):
                logger.error(f"算法 '{algorithm}' 未註冊")
                return False
        
        # 創建 A/B 測試
        ab_test = {
            'test_id': test_id,
            'algorithms': algorithms,
            'traffic_split': traffic_split,
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(hours=duration_hours) if duration_hours else None,
            'total_requests': 0,
            'metrics_by_algorithm': {alg: {} for alg in algorithms}
        }
        
        self.active_ab_tests[test_id] = ab_test
        
        # 更新協調器的 A/B 測試配置
        if self.orchestrator:
            self.orchestrator.set_ab_test_config(test_id, traffic_split)
        
        logger.info(f"A/B 測試 '{test_id}' 已啟動，算法: {algorithms}，分配: {traffic_split}")
        return True
    
    def stop_ab_test(self, test_id: str) -> Optional[ABTestResult]:
        """停止 A/B 測試並生成結果
        
        Args:
            test_id: 測試ID
            
        Returns:
            Optional[ABTestResult]: 測試結果
        """
        if test_id not in self.active_ab_tests:
            logger.error(f"A/B 測試 '{test_id}' 不存在或未運行")
            return None
        
        ab_test = self.active_ab_tests.pop(test_id)
        ab_test['end_time'] = datetime.now()
        
        # 生成測試結果
        result = self._generate_ab_test_result(ab_test)
        
        # 保存結果
        self.completed_ab_tests[test_id] = result
        self._save_ab_test_result(result)
        
        # 清除協調器的 A/B 測試配置
        if self.orchestrator:
            self.orchestrator.clear_ab_test_config(test_id)
        
        logger.info(f"A/B 測試 '{test_id}' 已完成")
        return result
    
    def _filter_metrics(self, algorithm_name: Optional[str] = None,
                       metric_type: Optional[MetricType] = None,
                       time_window: Optional[timedelta] = None,
                       scenario: Optional[str] = None) -> List[PerformanceMetric]:
        """過濾性能指標"""
        filtered = self.metrics_storage.copy()
        
        if algorithm_name:
            filtered = [m for m in filtered if m.algorithm_name == algorithm_name]
        
        if metric_type:
            filtered = [m for m in filtered if m.metric_type == metric_type]
        
        if scenario:
            filtered = [m for m in filtered if m.scenario == scenario]
        
        if time_window:
            cutoff_time = datetime.now() - time_window
            filtered = [m for m in filtered if m.timestamp >= cutoff_time]
        
        return filtered
    
    def _is_higher_better(self, metric_type: MetricType) -> bool:
        """判斷指標是否越高越好"""
        better_when_higher = {
            MetricType.SUCCESS_RATE,
            MetricType.NETWORK_EFFICIENCY,
            MetricType.USER_SATISFACTION,
            MetricType.RESOURCE_UTILIZATION,
            MetricType.DECISION_CONFIDENCE
        }
        return metric_type in better_when_higher
    
    def _update_ab_test_metrics(self, test_id: str, metric: PerformanceMetric) -> None:
        """更新 A/B 測試指標"""
        if test_id not in self.active_ab_tests:
            return
        
        ab_test = self.active_ab_tests[test_id]
        
        if metric.algorithm_name not in ab_test['algorithms']:
            return
        
        # 更新總請求數
        ab_test['total_requests'] += 1
        
        # 更新算法指標
        alg_metrics = ab_test['metrics_by_algorithm'][metric.algorithm_name]
        
        if metric.metric_type not in alg_metrics:
            alg_metrics[metric.metric_type] = []
        
        alg_metrics[metric.metric_type].append(metric.value)
    
    def _generate_ab_test_result(self, ab_test: Dict[str, Any]) -> ABTestResult:
        """生成 A/B 測試結果"""
        algorithms = ab_test['algorithms']
        
        # 計算每個算法的平均指標
        results_by_algorithm = {}
        for algorithm in algorithms:
            alg_metrics = ab_test['metrics_by_algorithm'][algorithm]
            alg_results = {}
            
            for metric_type, values in alg_metrics.items():
                if values:
                    alg_results[metric_type] = np.mean(values)
            
            results_by_algorithm[algorithm] = alg_results
        
        # 確定整體勝者（基於多個指標的綜合評分）
        overall_winner = self._determine_overall_winner(results_by_algorithm)
        
        # 計算統計顯著性
        statistical_significance = {}
        if len(algorithms) == 2:
            for metric_type in MetricType:
                comp_result = self.compare_algorithms(
                    algorithms[0], algorithms[1], metric_type,
                    time_window=ab_test['end_time'] - ab_test['start_time']
                )
                statistical_significance[f"{algorithms[0]}_vs_{algorithms[1]}_{metric_type.value}"] = comp_result.statistical_significance
        
        # 生成建議
        recommendations = self._generate_recommendations(results_by_algorithm, overall_winner)
        
        return ABTestResult(
            test_id=ab_test['test_id'],
            algorithms=algorithms,
            traffic_split=ab_test['traffic_split'],
            start_time=ab_test['start_time'],
            end_time=ab_test['end_time'],
            total_requests=ab_test['total_requests'],
            results_by_algorithm=results_by_algorithm,
            overall_winner=overall_winner,
            statistical_significance=statistical_significance,
            recommendations=recommendations
        )
    
    def _determine_overall_winner(self, results_by_algorithm: Dict[str, Dict[MetricType, float]]) -> Optional[str]:
        """確定整體勝者"""
        if not results_by_algorithm:
            return None
        
        # 簡化的評分機制：對每個指標進行標準化並求平均
        algorithm_scores = {}
        
        for algorithm, metrics in results_by_algorithm.items():
            score = 0.0
            metric_count = 0
            
            for metric_type, value in metrics.items():
                # 根據指標類型調整分數
                if self._is_higher_better(metric_type):
                    score += value
                else:
                    score += (1.0 - value) if value <= 1.0 else 1.0 / (1.0 + value)
                metric_count += 1
            
            if metric_count > 0:
                algorithm_scores[algorithm] = score / metric_count
        
        if algorithm_scores:
            return max(algorithm_scores, key=algorithm_scores.get)
        
        return None
    
    def _generate_recommendations(self, results_by_algorithm: Dict[str, Dict[MetricType, float]], 
                                winner: Optional[str]) -> List[str]:
        """生成建議"""
        recommendations = []
        
        if winner:
            recommendations.append(f"建議使用算法 '{winner}' 作為主要算法")
        
        # 分析各算法的強弱項
        for algorithm, metrics in results_by_algorithm.items():
            strong_metrics = []
            weak_metrics = []
            
            for metric_type, value in metrics.items():
                if self._is_higher_better(metric_type) and value > 0.8:
                    strong_metrics.append(metric_type.value)
                elif not self._is_higher_better(metric_type) and value < 0.2:
                    strong_metrics.append(metric_type.value)
                else:
                    weak_metrics.append(metric_type.value)
            
            if strong_metrics:
                recommendations.append(f"算法 '{algorithm}' 在以下指標表現優秀: {', '.join(strong_metrics)}")
            
            if weak_metrics:
                recommendations.append(f"算法 '{algorithm}' 在以下指標需要改進: {', '.join(weak_metrics)}")
        
        return recommendations
    
    def _save_ab_test_result(self, result: ABTestResult) -> None:
        """保存 A/B 測試結果"""
        try:
            result_file = self.results_dir / f"ab_test_{result.test_id}_{result.start_time.strftime('%Y%m%d_%H%M%S')}.json"
            
            # 將結果轉換為可序列化的格式
            result_dict = {
                'test_id': result.test_id,
                'algorithms': result.algorithms,
                'traffic_split': result.traffic_split,
                'start_time': result.start_time.isoformat(),
                'end_time': result.end_time.isoformat() if result.end_time else None,
                'total_requests': result.total_requests,
                'results_by_algorithm': {
                    alg: {metric_type.value: value for metric_type, value in metrics.items()}
                    for alg, metrics in result.results_by_algorithm.items()
                },
                'overall_winner': result.overall_winner,
                'statistical_significance': result.statistical_significance,
                'recommendations': result.recommendations
            }
            
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"A/B 測試結果已保存: {result_file}")
            
        except Exception as e:
            logger.error(f"保存 A/B 測試結果失敗: {e}")
    
    def generate_performance_report(self, algorithms: Optional[List[str]] = None,
                                  time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """生成性能報告
        
        Args:
            algorithms: 算法列表（可選）
            time_window: 時間窗口（可選）
            
        Returns:
            Dict[str, Any]: 性能報告
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'time_window': str(time_window) if time_window else 'all_time',
            'algorithms': {},
            'comparisons': [],
            'summary': {}
        }
        
        # 獲取要分析的算法列表
        if not algorithms:
            algorithms = list(set(m.algorithm_name for m in self.metrics_storage))
        
        # 為每個算法生成報告
        for algorithm in algorithms:
            alg_report = {}
            
            for metric_type in MetricType:
                stats = self.get_algorithm_performance(algorithm, metric_type, time_window)
                if stats['count'] > 0:
                    alg_report[metric_type.value] = stats
            
            report['algorithms'][algorithm] = alg_report
        
        # 生成算法間比較
        for i, alg_a in enumerate(algorithms):
            for alg_b in algorithms[i+1:]:
                for metric_type in MetricType:
                    comparison = self.compare_algorithms(alg_a, alg_b, metric_type, time_window)
                    if comparison.sample_size_a > 0 and comparison.sample_size_b > 0:
                        report['comparisons'].append({
                            'algorithm_a': comparison.algorithm_a,
                            'algorithm_b': comparison.algorithm_b,
                            'metric': metric_type.value,
                            'winner': comparison.winner,
                            'improvement_percentage': comparison.improvement_percentage,
                            'statistical_significance': comparison.statistical_significance
                        })
        
        # 生成摘要
        if algorithms:
            best_by_metric = {}
            for metric_type in MetricType:
                best_alg = None
                best_value = None
                
                for algorithm in algorithms:
                    stats = self.get_algorithm_performance(algorithm, metric_type, time_window)
                    if stats['count'] > 0:
                        value = stats['mean']
                        if best_value is None:
                            best_alg = algorithm
                            best_value = value
                        elif self._is_higher_better(metric_type) and value > best_value:
                            best_alg = algorithm
                            best_value = value
                        elif not self._is_higher_better(metric_type) and value < best_value:
                            best_alg = algorithm
                            best_value = value
                
                if best_alg:
                    best_by_metric[metric_type.value] = {
                        'algorithm': best_alg,
                        'value': best_value
                    }
            
            report['summary']['best_by_metric'] = best_by_metric
        
        return report
    
    def get_active_ab_tests(self) -> Dict[str, Dict[str, Any]]:
        """獲取活躍的 A/B 測試狀態"""
        status = {}
        
        for test_id, ab_test in self.active_ab_tests.items():
            duration = datetime.now() - ab_test['start_time']
            
            status[test_id] = {
                'algorithms': ab_test['algorithms'],
                'traffic_split': ab_test['traffic_split'],
                'start_time': ab_test['start_time'].isoformat(),
                'duration_hours': duration.total_seconds() / 3600,
                'total_requests': ab_test['total_requests'],
                'end_time': ab_test['end_time'].isoformat() if ab_test['end_time'] else None,
                'is_expired': ab_test['end_time'] and datetime.now() > ab_test['end_time']
            }
        
        return status