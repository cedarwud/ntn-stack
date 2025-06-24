"""
基準算法抽象基類

定義標準化的算法接口，確保所有基準算法都有一致的行為：
- 統一的決策接口
- 標準化的性能指標
- 可配置的參數
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class AlgorithmResult:
    """算法決策結果"""
    
    # 核心決策
    handover_decision: int  # 0: no_handover, 1: trigger, 2: prepare
    target_satellite: Optional[int] = None
    timing: float = 2.0  # 切換時機 (秒)
    confidence: float = 1.0  # 決策置信度
    
    # 性能指標
    decision_time: float = 0.0  # 決策耗時 (ms)
    expected_latency: float = 25.0  # 預期延遲 (ms)
    expected_success_rate: float = 0.9  # 預期成功率
    
    # 額外資訊
    algorithm_name: str = "Unknown"
    decision_reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'handover_decision': self.handover_decision,
            'target_satellite': self.target_satellite,
            'timing': self.timing,
            'confidence': self.confidence,
            'decision_time': self.decision_time,
            'expected_latency': self.expected_latency,
            'expected_success_rate': self.expected_success_rate,
            'algorithm_name': self.algorithm_name,
            'decision_reason': self.decision_reason,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }


class BaseAlgorithm(ABC):
    """
    基準算法抽象基類
    
    所有基準算法必須繼承此類並實現其抽象方法
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化算法
        
        Args:
            name: 算法名稱
            config: 算法配置參數
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # 性能統計
        self.statistics = {
            'total_decisions': 0,
            'total_decision_time': 0.0,
            'average_decision_time': 0.0,
            'handover_decisions': 0,
            'no_handover_decisions': 0,
            'preparation_decisions': 0
        }
        
        # 初始化算法特定參數
        self._initialize_algorithm()
    
    @abstractmethod
    def _initialize_algorithm(self):
        """初始化算法特定參數 - 子類必須實現"""
        pass
    
    @abstractmethod
    def make_decision(self, observation: np.ndarray, info: Dict[str, Any]) -> AlgorithmResult:
        """
        根據觀測做出切換決策 - 子類必須實現
        
        Args:
            observation: 環境觀測向量
            info: 環境額外資訊
            
        Returns:
            AlgorithmResult: 決策結果
        """
        pass
    
    def decide(self, observation: np.ndarray, info: Dict[str, Any]) -> AlgorithmResult:
        """
        統一的決策入口點（包含性能統計）
        
        Args:
            observation: 環境觀測向量
            info: 環境額外資訊
            
        Returns:
            AlgorithmResult: 決策結果
        """
        start_time = time.time()
        
        try:
            # 調用子類實現的決策邏輯
            result = self.make_decision(observation, info)
            
            # 設置算法名稱
            result.algorithm_name = self.name
            
            # 計算決策時間
            decision_time = (time.time() - start_time) * 1000  # 轉換為毫秒
            result.decision_time = decision_time
            
            # 更新統計
            self._update_statistics(result, decision_time)
            
            return result
            
        except Exception as e:
            self.logger.error(f"決策過程出錯: {e}")
            # 返回默認的安全決策
            return AlgorithmResult(
                handover_decision=0,  # 不切換
                algorithm_name=self.name,
                decision_reason=f"Error: {str(e)}",
                decision_time=(time.time() - start_time) * 1000
            )
    
    def _update_statistics(self, result: AlgorithmResult, decision_time: float):
        """更新算法統計資訊"""
        self.statistics['total_decisions'] += 1
        self.statistics['total_decision_time'] += decision_time
        self.statistics['average_decision_time'] = (
            self.statistics['total_decision_time'] / self.statistics['total_decisions']
        )
        
        # 統計決策類型
        if result.handover_decision == 0:
            self.statistics['no_handover_decisions'] += 1
        elif result.handover_decision == 1:
            self.statistics['handover_decisions'] += 1
        elif result.handover_decision == 2:
            self.statistics['preparation_decisions'] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取算法統計資訊"""
        return self.statistics.copy()
    
    def reset_statistics(self):
        """重置統計資訊"""
        for key in self.statistics:
            self.statistics[key] = 0 if isinstance(self.statistics[key], (int, float)) else 0.0
    
    def get_config(self) -> Dict[str, Any]:
        """獲取算法配置"""
        return self.config.copy()
    
    def update_config(self, new_config: Dict[str, Any]):
        """更新算法配置"""
        self.config.update(new_config)
        # 重新初始化以應用新配置
        self._initialize_algorithm()
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.name}(decisions={self.statistics['total_decisions']}, " \
               f"avg_time={self.statistics['average_decision_time']:.2f}ms)"
    
    def __repr__(self) -> str:
        """詳細字符串表示"""
        return f"{self.__class__.__name__}(name='{self.name}', config={self.config})"


class AlgorithmEvaluator:
    """
    算法評估器
    
    用於評估和比較不同算法的性能
    """
    
    def __init__(self):
        self.algorithms: Dict[str, BaseAlgorithm] = {}
        self.evaluation_results: Dict[str, List[AlgorithmResult]] = {}
    
    def register_algorithm(self, algorithm: BaseAlgorithm):
        """註冊算法進行評估"""
        self.algorithms[algorithm.name] = algorithm
        self.evaluation_results[algorithm.name] = []
        logger.info(f"已註冊算法: {algorithm.name}")
    
    def evaluate_algorithm(
        self,
        algorithm_name: str,
        observations: List[np.ndarray],
        infos: List[Dict[str, Any]]
    ) -> List[AlgorithmResult]:
        """
        評估指定算法
        
        Args:
            algorithm_name: 算法名稱
            observations: 觀測序列
            infos: 資訊序列
            
        Returns:
            List[AlgorithmResult]: 決策結果序列
        """
        if algorithm_name not in self.algorithms:
            raise ValueError(f"未找到算法: {algorithm_name}")
        
        algorithm = self.algorithms[algorithm_name]
        results = []
        
        logger.info(f"開始評估算法: {algorithm_name}, 場景數: {len(observations)}")
        
        for i, (obs, info) in enumerate(zip(observations, infos)):
            try:
                result = algorithm.decide(obs, info)
                results.append(result)
            except Exception as e:
                logger.error(f"算法 {algorithm_name} 在場景 {i} 中出錯: {e}")
                # 添加錯誤結果
                error_result = AlgorithmResult(
                    handover_decision=0,
                    algorithm_name=algorithm_name,
                    decision_reason=f"Error in scenario {i}: {str(e)}"
                )
                results.append(error_result)
        
        # 保存評估結果
        self.evaluation_results[algorithm_name].extend(results)
        
        logger.info(f"算法 {algorithm_name} 評估完成，處理了 {len(results)} 個場景")
        return results
    
    def compare_algorithms(
        self,
        observations: List[np.ndarray],
        infos: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        比較所有註冊的算法
        
        Args:
            observations: 觀測序列
            infos: 資訊序列
            
        Returns:
            Dict: 比較結果
        """
        comparison_results = {}
        
        # 評估每個算法
        for algorithm_name in self.algorithms:
            results = self.evaluate_algorithm(algorithm_name, observations, infos)
            
            # 計算性能指標
            metrics = self._calculate_metrics(results)
            comparison_results[algorithm_name] = {
                'results': results,
                'metrics': metrics,
                'statistics': self.algorithms[algorithm_name].get_statistics()
            }
        
        # 生成比較摘要
        summary = self._generate_comparison_summary(comparison_results)
        
        return {
            'individual_results': comparison_results,
            'summary': summary,
            'evaluation_info': {
                'total_scenarios': len(observations),
                'algorithms_count': len(self.algorithms),
                'timestamp': datetime.now().isoformat()
            }
        }
    
    def _calculate_metrics(self, results: List[AlgorithmResult]) -> Dict[str, float]:
        """計算算法性能指標"""
        if not results:
            return {}
        
        metrics = {
            'average_decision_time': np.mean([r.decision_time for r in results]),
            'average_expected_latency': np.mean([r.expected_latency for r in results]),
            'average_expected_success_rate': np.mean([r.expected_success_rate for r in results]),
            'average_confidence': np.mean([r.confidence for r in results]),
            'handover_rate': len([r for r in results if r.handover_decision == 1]) / len(results),
            'preparation_rate': len([r for r in results if r.handover_decision == 2]) / len(results),
            'no_handover_rate': len([r for r in results if r.handover_decision == 0]) / len(results)
        }
        
        return metrics
    
    def _generate_comparison_summary(self, comparison_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成算法比較摘要"""
        if not comparison_results:
            return {}
        
        # 找出各項指標的最佳算法
        best_algorithms = {}
        metrics_keys = ['average_decision_time', 'average_expected_latency', 'average_expected_success_rate']
        
        for metric in metrics_keys:
            if metric == 'average_decision_time' or metric == 'average_expected_latency':
                # 越小越好
                best_algo = min(
                    comparison_results.keys(),
                    key=lambda x: comparison_results[x]['metrics'].get(metric, float('inf'))
                )
            else:
                # 越大越好
                best_algo = max(
                    comparison_results.keys(),
                    key=lambda x: comparison_results[x]['metrics'].get(metric, 0)
                )
            
            best_algorithms[metric] = best_algo
        
        summary = {
            'best_algorithms': best_algorithms,
            'algorithm_ranking': self._rank_algorithms(comparison_results),
            'performance_gaps': self._calculate_performance_gaps(comparison_results)
        }
        
        return summary
    
    def _rank_algorithms(self, comparison_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """根據綜合性能對算法進行排名"""
        rankings = []
        
        for algo_name, data in comparison_results.items():
            metrics = data['metrics']
            
            # 簡單的綜合評分（可以調整權重）
            score = (
                (1 / (metrics.get('average_decision_time', 1) + 0.1)) * 0.2 +  # 決策速度
                (1 / (metrics.get('average_expected_latency', 1) + 0.1)) * 0.4 +  # 延遲性能
                metrics.get('average_expected_success_rate', 0) * 0.4  # 成功率
            )
            
            rankings.append({
                'algorithm': algo_name,
                'score': score,
                'metrics': metrics
            })
        
        # 按分數排序
        rankings.sort(key=lambda x: x['score'], reverse=True)
        
        return rankings
    
    def _calculate_performance_gaps(self, comparison_results: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """計算算法間的性能差距"""
        gaps = {}
        algos = list(comparison_results.keys())
        
        for i, algo1 in enumerate(algos):
            gaps[algo1] = {}
            metrics1 = comparison_results[algo1]['metrics']
            
            for j, algo2 in enumerate(algos):
                if i != j:
                    metrics2 = comparison_results[algo2]['metrics']
                    
                    # 計算關鍵指標的相對差距
                    latency_gap = (
                        (metrics1.get('average_expected_latency', 0) - metrics2.get('average_expected_latency', 0))
                        / max(metrics2.get('average_expected_latency', 1), 0.1) * 100
                    )
                    
                    success_gap = (
                        (metrics1.get('average_expected_success_rate', 0) - metrics2.get('average_expected_success_rate', 0))
                        / max(metrics2.get('average_expected_success_rate', 1), 0.1) * 100
                    )
                    
                    gaps[algo1][algo2] = {
                        'latency_gap_percent': latency_gap,
                        'success_rate_gap_percent': success_gap
                    }
        
        return gaps