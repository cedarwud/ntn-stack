"""
性能分析器 - 多算法性能對比和統計分析

提供完整的算法性能分析功能，包括：
- 多算法性能對比
- 統計顯著性測試
- A/B 測試分析
- 性能趨勢分析
- 收斂性分析
"""

import logging
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from scipy import stats
import math

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指標數據類"""
    algorithm: str
    session_id: int
    episode_rewards: List[float]
    success_rates: List[float]
    training_times: List[float]
    convergence_episode: Optional[int]
    final_performance: float
    stability_score: float

class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.analysis_cache: Dict[str, Any] = {}
        
    async def compare_algorithms(
        self,
        sessions_data: Dict[int, Any],
        metrics: List[str],
        statistical_tests: bool = True
    ) -> Dict[str, Any]:
        """
        多算法性能對比分析
        
        Args:
            sessions_data: 會話數據字典
            metrics: 要比較的指標列表
            statistical_tests: 是否執行統計檢驗
        """
        try:
            analysis_results = {
                "comparison_timestamp": datetime.now().isoformat(),
                "algorithms": [],
                "metrics_comparison": {},
                "rankings": {},
                "summary": {}
            }
            
            # 提取性能指標
            performance_data = {}
            for session_id, session_data in sessions_data.items():
                algorithm = session_data.get("algorithm_type", "unknown")
                metrics_data = await self._extract_performance_metrics(session_id, session_data)
                performance_data[algorithm] = metrics_data
                analysis_results["algorithms"].append(algorithm)
            
            # 對比分析
            for metric in metrics:
                metric_comparison = await self._compare_metric(performance_data, metric)
                analysis_results["metrics_comparison"][metric] = metric_comparison
            
            # 生成排名
            analysis_results["rankings"] = await self._generate_rankings(performance_data, metrics)
            
            # 統計檢驗
            if statistical_tests:
                analysis_results["statistical_tests"] = await self._perform_statistical_tests(performance_data)
            
            # 生成總結
            analysis_results["summary"] = await self._generate_summary(performance_data, metrics)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"算法性能對比分析失敗: {e}")
            raise
    
    async def _extract_performance_metrics(self, session_id: int, session_data: Any) -> PerformanceMetrics:
        """提取性能指標"""
        try:
            # 模擬性能數據提取（實際應從數據庫獲取）
            algorithm = session_data.get("algorithm_type", "unknown")
            total_episodes = session_data.get("total_episodes", 100)
            
            # 生成模擬的性能數據
            episode_rewards = self._generate_mock_rewards(algorithm, total_episodes)
            success_rates = self._generate_mock_success_rates(algorithm, total_episodes)
            training_times = [0.1] * total_episodes  # 每回合100ms
            
            # 計算收斂回合
            convergence_episode = self._detect_convergence(episode_rewards)
            
            # 計算最終性能
            final_performance = np.mean(episode_rewards[-10:]) if len(episode_rewards) >= 10 else np.mean(episode_rewards)
            
            # 計算穩定性分數
            stability_score = self._calculate_stability_score(episode_rewards)
            
            return PerformanceMetrics(
                algorithm=algorithm,
                session_id=session_id,
                episode_rewards=episode_rewards,
                success_rates=success_rates,
                training_times=training_times,
                convergence_episode=convergence_episode,
                final_performance=final_performance,
                stability_score=stability_score
            )
            
        except Exception as e:
            logger.error(f"提取性能指標失敗: {e}")
            # 返回默認指標
            return PerformanceMetrics(
                algorithm="unknown",
                session_id=session_id,
                episode_rewards=[0.0],
                success_rates=[0.0],
                training_times=[0.1],
                convergence_episode=None,
                final_performance=0.0,
                stability_score=0.0
            )
    
    def _generate_mock_rewards(self, algorithm: str, episodes: int) -> List[float]:
        """生成模擬獎勵數據（基於算法特性）"""
        rewards = []
        base_performance = {"dqn": 0.6, "ppo": 0.8, "sac": 0.75}.get(algorithm, 0.5)
        
        for i in range(episodes):
            # 模擬學習曲線
            progress = i / episodes
            learning_factor = 1 - math.exp(-3 * progress)  # 學習曲線
            noise = np.random.normal(0, 0.1)  # 添加噪音
            
            reward = base_performance * learning_factor + noise
            rewards.append(max(0, reward))  # 確保非負
        
        return rewards
    
    def _generate_mock_success_rates(self, algorithm: str, episodes: int) -> List[float]:
        """生成模擬成功率數據"""
        success_rates = []
        base_success = {"dqn": 0.7, "ppo": 0.85, "sac": 0.8}.get(algorithm, 0.6)
        
        for i in range(episodes):
            progress = i / episodes
            success_factor = 1 - math.exp(-2 * progress)
            noise = np.random.normal(0, 0.05)
            
            success_rate = base_success * success_factor + noise
            success_rates.append(max(0, min(1, success_rate)))  # 限制在[0,1]
        
        return success_rates
    
    def _detect_convergence(self, rewards: List[float], window_size: int = 20) -> Optional[int]:
        """檢測收斂回合"""
        if len(rewards) < window_size * 2:
            return None
        
        for i in range(window_size, len(rewards) - window_size):
            current_mean = np.mean(rewards[i:i+window_size])
            future_mean = np.mean(rewards[i+window_size:i+2*window_size])
            
            # 如果變化小於5%，認為已收斂
            if abs(future_mean - current_mean) / max(abs(current_mean), 0.01) < 0.05:
                return i
        
        return None
    
    def _calculate_stability_score(self, rewards: List[float]) -> float:
        """計算穩定性分數"""
        if len(rewards) < 2:
            return 0.0
        
        # 使用變異係數的倒數作為穩定性分數
        mean_reward = np.mean(rewards)
        std_reward = np.std(rewards)
        
        if mean_reward == 0:
            return 0.0
        
        cv = std_reward / abs(mean_reward)  # 變異係數
        stability = 1 / (1 + cv)  # 轉換為穩定性分數
        
        return stability
    
    async def _compare_metric(self, performance_data: Dict[str, PerformanceMetrics], metric: str) -> Dict[str, Any]:
        """對比單個指標"""
        try:
            comparison = {
                "metric": metric,
                "values": {},
                "ranking": [],
                "best_algorithm": None,
                "performance_gap": 0.0
            }
            
            # 提取指標值
            metric_values = {}
            for algorithm, metrics in performance_data.items():
                if metric == "final_performance":
                    value = metrics.final_performance
                elif metric == "stability_score":
                    value = metrics.stability_score
                elif metric == "convergence_speed":
                    value = metrics.convergence_episode if metrics.convergence_episode else float('inf')
                elif metric == "average_reward":
                    value = np.mean(metrics.episode_rewards)
                elif metric == "success_rate":
                    value = np.mean(metrics.success_rates)
                else:
                    value = 0.0
                
                metric_values[algorithm] = value
                comparison["values"][algorithm] = value
            
            # 排序（除了收斂速度，其他都是越大越好）
            if metric == "convergence_speed":
                sorted_algorithms = sorted(metric_values.items(), key=lambda x: x[1])
            else:
                sorted_algorithms = sorted(metric_values.items(), key=lambda x: x[1], reverse=True)
            
            comparison["ranking"] = [alg for alg, _ in sorted_algorithms]
            comparison["best_algorithm"] = sorted_algorithms[0][0]
            
            # 計算性能差距
            if len(sorted_algorithms) >= 2:
                best_value = sorted_algorithms[0][1]
                second_value = sorted_algorithms[1][1]
                if best_value != 0:
                    comparison["performance_gap"] = abs(best_value - second_value) / abs(best_value) * 100
            
            return comparison
            
        except Exception as e:
            logger.error(f"指標對比失敗: {e}")
            return {"metric": metric, "error": str(e)}
    
    async def _generate_rankings(self, performance_data: Dict[str, PerformanceMetrics], metrics: List[str]) -> Dict[str, Any]:
        """生成綜合排名"""
        try:
            # 計算每個算法在各指標上的得分
            algorithm_scores = {}
            
            for algorithm in performance_data.keys():
                total_score = 0
                valid_metrics = 0
                
                for metric in metrics:
                    metric_comparison = await self._compare_metric(performance_data, metric)
                    ranking = metric_comparison["ranking"]
                    
                    if algorithm in ranking:
                        # 排名越靠前得分越高
                        score = len(ranking) - ranking.index(algorithm)
                        total_score += score
                        valid_metrics += 1
                
                if valid_metrics > 0:
                    algorithm_scores[algorithm] = total_score / valid_metrics
                else:
                    algorithm_scores[algorithm] = 0
            
            # 排序
            ranked_algorithms = sorted(algorithm_scores.items(), key=lambda x: x[1], reverse=True)
            
            return {
                "overall_ranking": [alg for alg, _ in ranked_algorithms],
                "scores": dict(ranked_algorithms),
                "ranking_method": "average_rank_score"
            }
            
        except Exception as e:
            logger.error(f"生成排名失敗: {e}")
            return {"error": str(e)}
    
    async def _perform_statistical_tests(self, performance_data: Dict[str, PerformanceMetrics]) -> Dict[str, Any]:
        """執行統計檢驗"""
        try:
            statistical_results = {
                "tests_performed": [],
                "pairwise_comparisons": {},
                "overall_significance": False
            }
            
            algorithms = list(performance_data.keys())
            
            # 如果有多於兩個算法，執行 ANOVA
            if len(algorithms) > 2:
                rewards_groups = [metrics.episode_rewards for metrics in performance_data.values()]
                
                # 執行 One-way ANOVA
                try:
                    f_stat, p_value = stats.f_oneway(*rewards_groups)
                    statistical_results["anova"] = {
                        "f_statistic": float(f_stat),
                        "p_value": float(p_value),
                        "significant": p_value < 0.05
                    }
                    statistical_results["tests_performed"].append("anova")
                    statistical_results["overall_significance"] = p_value < 0.05
                except Exception as e:
                    logger.warning(f"ANOVA 測試失敗: {e}")
            
            # 成對 t 檢驗
            for i, alg1 in enumerate(algorithms):
                for j, alg2 in enumerate(algorithms[i+1:], i+1):
                    try:
                        rewards1 = performance_data[alg1].episode_rewards
                        rewards2 = performance_data[alg2].episode_rewards
                        
                        # 執行獨立樣本 t 檢驗
                        t_stat, p_value = stats.ttest_ind(rewards1, rewards2)
                        
                        comparison_key = f"{alg1}_vs_{alg2}"
                        statistical_results["pairwise_comparisons"][comparison_key] = {
                            "t_statistic": float(t_stat),
                            "p_value": float(p_value),
                            "significant": p_value < 0.05,
                            "effect_size": self._calculate_cohens_d(rewards1, rewards2)
                        }
                        
                    except Exception as e:
                        logger.warning(f"t檢驗失敗 ({alg1} vs {alg2}): {e}")
            
            statistical_results["tests_performed"].append("t_test")
            
            return statistical_results
            
        except Exception as e:
            logger.error(f"統計檢驗失敗: {e}")
            return {"error": str(e)}
    
    def _calculate_cohens_d(self, group1: List[float], group2: List[float]) -> float:
        """計算 Cohen's d 效應量"""
        try:
            n1, n2 = len(group1), len(group2)
            mean1, mean2 = np.mean(group1), np.mean(group2)
            var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
            
            # 合併標準差
            pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
            
            if pooled_std == 0:
                return 0.0
            
            cohens_d = (mean1 - mean2) / pooled_std
            return float(cohens_d)
            
        except Exception as e:
            logger.error(f"計算 Cohen's d 失敗: {e}")
            return 0.0
    
    async def _generate_summary(self, performance_data: Dict[str, PerformanceMetrics], metrics: List[str]) -> Dict[str, Any]:
        """生成分析總結"""
        try:
            summary = {
                "total_algorithms": len(performance_data),
                "metrics_analyzed": len(metrics),
                "key_findings": [],
                "recommendations": []
            }
            
            # 找出最佳算法
            best_overall = None
            best_score = -1
            
            for algorithm, metrics_data in performance_data.items():
                # 簡單的綜合評分
                score = (metrics_data.final_performance * 0.4 + 
                        metrics_data.stability_score * 0.3 + 
                        np.mean(metrics_data.success_rates) * 0.3)
                
                if score > best_score:
                    best_score = score
                    best_overall = algorithm
            
            summary["best_overall_algorithm"] = best_overall
            summary["best_overall_score"] = float(best_score)
            
            # 添加關鍵發現
            summary["key_findings"].append(f"最佳整體算法: {best_overall}")
            
            # 分析收斂性
            converged_algorithms = [alg for alg, metrics in performance_data.items() 
                                  if metrics.convergence_episode is not None]
            if converged_algorithms:
                summary["key_findings"].append(f"收斂算法: {', '.join(converged_algorithms)}")
            
            # 添加建議
            if best_overall:
                summary["recommendations"].append(f"建議優先使用 {best_overall} 算法")
            
            # 穩定性分析
            most_stable = max(performance_data.items(), key=lambda x: x[1].stability_score)
            summary["recommendations"].append(f"最穩定算法: {most_stable[0]}")
            
            return summary
            
        except Exception as e:
            logger.error(f"生成總結失敗: {e}")
            return {"error": str(e)}
    
    async def perform_ab_test_analysis(
        self,
        results_a: Dict[str, Any],
        results_b: Dict[str, Any],
        significance_level: float = 0.05
    ) -> Dict[str, Any]:
        """執行 A/B 測試分析"""
        try:
            # 模擬 A/B 測試結果提取
            rewards_a = results_a.get("episode_rewards", [0.6] * 50)  # 模擬數據
            rewards_b = results_b.get("episode_rewards", [0.8] * 50)  # 模擬數據
            
            # 執行 t 檢驗
            t_stat, p_value = stats.ttest_ind(rewards_a, rewards_b)
            
            # 計算效應量
            cohens_d = self._calculate_cohens_d(rewards_a, rewards_b)
            
            # 計算置信區間
            mean_diff = np.mean(rewards_a) - np.mean(rewards_b)
            se_diff = math.sqrt(np.var(rewards_a, ddof=1)/len(rewards_a) + 
                               np.var(rewards_b, ddof=1)/len(rewards_b))
            
            # 95% 置信區間
            t_critical = stats.t.ppf(1 - significance_level/2, len(rewards_a) + len(rewards_b) - 2)
            ci_lower = mean_diff - t_critical * se_diff
            ci_upper = mean_diff + t_critical * se_diff
            
            analysis_result = {
                "test_type": "independent_t_test",
                "sample_size_a": len(rewards_a),
                "sample_size_b": len(rewards_b),
                "mean_a": float(np.mean(rewards_a)),
                "mean_b": float(np.mean(rewards_b)),
                "mean_difference": float(mean_diff),
                "t_statistic": float(t_stat),
                "p_value": float(p_value),
                "significant": p_value < significance_level,
                "effect_size": float(cohens_d),
                "confidence_interval": {
                    "lower": float(ci_lower),
                    "upper": float(ci_upper),
                    "level": 1 - significance_level
                },
                "interpretation": self._interpret_ab_test_results(p_value, cohens_d, significance_level)
            }
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"A/B 測試分析失敗: {e}")
            return {"error": str(e)}
    
    def _interpret_ab_test_results(self, p_value: float, cohens_d: float, alpha: float) -> str:
        """解釋 A/B 測試結果"""
        if p_value < alpha:
            if abs(cohens_d) < 0.2:
                return "統計顯著但效應量很小"
            elif abs(cohens_d) < 0.5:
                return "統計顯著且有中等效應量"
            else:
                return "統計顯著且有大效應量"
        else:
            return "無統計顯著差異"
    
    async def generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """基於分析結果生成建議"""
        try:
            recommendations = []
            
            # 基於總體排名的建議
            if "rankings" in analysis_results and "overall_ranking" in analysis_results["rankings"]:
                best_algorithm = analysis_results["rankings"]["overall_ranking"][0]
                recommendations.append(f"推薦使用 {best_algorithm} 算法，綜合性能最佳")
            
            # 基於統計檢驗的建議
            if "statistical_tests" in analysis_results:
                if analysis_results["statistical_tests"].get("overall_significance", False):
                    recommendations.append("算法間存在統計顯著差異，建議選擇性能最佳的算法")
                else:
                    recommendations.append("算法間無顯著差異，可根據其他因素（如計算效率）選擇")
            
            # 基於穩定性的建議
            if "metrics_comparison" in analysis_results and "stability_score" in analysis_results["metrics_comparison"]:
                stability_ranking = analysis_results["metrics_comparison"]["stability_score"]["ranking"]
                if stability_ranking:
                    most_stable = stability_ranking[0]
                    recommendations.append(f"對穩定性要求較高的場景建議使用 {most_stable} 算法")
            
            # 基於收斂性的建議
            if "metrics_comparison" in analysis_results and "convergence_speed" in analysis_results["metrics_comparison"]:
                convergence_ranking = analysis_results["metrics_comparison"]["convergence_speed"]["ranking"]
                if convergence_ranking:
                    fastest_convergence = convergence_ranking[0]
                    recommendations.append(f"需要快速收斂的場景建議使用 {fastest_convergence} 算法")
            
            # 默認建議
            if not recommendations:
                recommendations.append("建議進行更多輪測試以獲得更可靠的結論")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"生成建議失敗: {e}")
            return ["分析過程中出現錯誤，建議檢查數據和重新分析"]