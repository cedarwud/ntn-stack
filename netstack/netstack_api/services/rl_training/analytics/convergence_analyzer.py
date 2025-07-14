"""
Convergence Analyzer for RL Training Analysis

提供強化學習訓練收斂性分析功能，包括：
- 學習曲線分析和趨勢檢測
- 收斂性評估和預測
- 性能趨勢識別
- 訓練穩定性分析
- 早停建議

此模組為 Phase 3 決策透明化的重要組成部分。
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from collections import deque

# 嘗試導入科學計算庫，如不可用則優雅降級
try:
    from scipy import stats
    from scipy.signal import savgol_filter
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("scipy not available, using simplified trend analysis")

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import PolynomialFeatures
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("sklearn not available, using basic regression analysis")

logger = logging.getLogger(__name__)

class ConvergenceStatus(Enum):
    """收斂狀態"""
    CONVERGING = "converging"
    CONVERGED = "converged"
    DIVERGING = "diverging"
    STAGNANT = "stagnant"
    OSCILLATING = "oscillating"
    INSUFFICIENT_DATA = "insufficient_data"

class TrendDirection(Enum):
    """趨勢方向"""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"

class PerformancePhase(Enum):
    """訓練階段"""
    INITIAL_EXPLORATION = "initial_exploration"
    RAPID_LEARNING = "rapid_learning"
    FINE_TUNING = "fine_tuning"
    CONVERGED = "converged"
    OVERFITTING = "overfitting"

@dataclass
class ConvergenceMetrics:
    """收斂性指標"""
    convergence_score: float  # 0-1, 1表示完全收斂
    stability_score: float    # 0-1, 1表示非常穩定
    improvement_rate: float   # 改進速率
    episodes_to_convergence: Optional[int]  # 預估收斂所需episode數
    confidence_interval: Tuple[float, float]  # 性能置信區間
    trend_direction: TrendDirection
    convergence_status: ConvergenceStatus

@dataclass
class LearningCurveSegment:
    """學習曲線段"""
    start_episode: int
    end_episode: int
    segment_type: PerformancePhase
    slope: float
    r_squared: float
    mean_performance: float
    variance: float
    description: str

@dataclass
class PerformanceTrend:
    """性能趨勢分析"""
    metric_name: str
    current_value: float
    trend_direction: TrendDirection
    trend_strength: float  # 0-1, 趨勢強度
    recent_change: float   # 最近變化
    volatility: float      # 波動性
    prediction_horizon: int  # 預測展望期
    predicted_values: List[float]
    confidence_bounds: List[Tuple[float, float]]

@dataclass
class LearningCurveAnalysis:
    """完整的學習曲線分析"""
    algorithm_name: str
    session_id: str
    analysis_timestamp: datetime
    
    # 基本統計
    total_episodes: int
    current_performance: float
    best_performance: float
    worst_performance: float
    
    # 收斂性分析
    convergence_metrics: ConvergenceMetrics
    
    # 曲線分割
    curve_segments: List[LearningCurveSegment]
    
    # 性能趨勢
    performance_trends: Dict[str, PerformanceTrend]
    
    # 訓練階段
    current_phase: PerformancePhase
    phase_transitions: List[Tuple[int, PerformancePhase]]
    
    # 預測和建議
    early_stopping_recommendation: Optional[int]
    training_recommendations: List[str]
    performance_forecast: Dict[str, Any]
    
    # 視覺化數據
    visualization_data: Dict[str, Any]

class ConvergenceAnalyzer:
    """
    收斂性分析器
    
    提供全面的強化學習訓練收斂性分析，包括學習曲線分析、
    趨勢檢測、收斂性評估和訓練建議。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化收斂性分析器
        
        Args:
            config: 配置參數
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # 分析參數
        self.min_episodes_for_analysis = self.config.get('min_episodes', 10)
        self.convergence_window_size = self.config.get('convergence_window', 50)
        self.stability_threshold = self.config.get('stability_threshold', 0.05)
        self.trend_window_size = self.config.get('trend_window', 20)
        self.smoothing_window = self.config.get('smoothing_window', 5)
        
        # 收斂性檢測參數
        self.convergence_threshold = self.config.get('convergence_threshold', 0.02)
        self.stagnation_threshold = self.config.get('stagnation_threshold', 0.001)
        self.oscillation_threshold = self.config.get('oscillation_threshold', 0.1)
        
        # 內部狀態
        self.performance_history = {}
        self.analysis_cache = {}
        
        self.logger.info("Convergence Analyzer initialized")
    
    async def analyze_convergence(
        self,
        training_data: Dict[str, Any],
        metrics: Optional[List[str]] = None
    ) -> LearningCurveAnalysis:
        """
        執行完整的收斂性分析
        
        Args:
            training_data: 訓練數據，包含episode性能記錄
            metrics: 要分析的指標列表，默認分析所有可用指標
            
        Returns:
            完整的學習曲線分析結果
        """
        session_id = training_data.get('session_id', f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        algorithm_name = training_data.get('algorithm_name', 'Unknown')
        
        self.logger.info(f"Starting convergence analysis for {algorithm_name} session {session_id}")
        
        try:
            # 提取性能數據
            performance_data = self._extract_performance_data(training_data)
            
            if len(performance_data['episodes']) < self.min_episodes_for_analysis:
                return self._create_insufficient_data_analysis(session_id, algorithm_name, performance_data)
            
            # 1. 基本統計分析
            basic_stats = self._calculate_basic_statistics(performance_data)
            
            # 2. 收斂性分析
            convergence_metrics = await self._analyze_convergence_metrics(performance_data)
            
            # 3. 學習曲線分割
            curve_segments = await self._segment_learning_curve(performance_data)
            
            # 4. 性能趨勢分析
            performance_trends = await self._analyze_performance_trends(
                performance_data, metrics or ['total_reward', 'success_rate']
            )
            
            # 5. 訓練階段識別
            current_phase, phase_transitions = await self._identify_training_phase(
                performance_data, curve_segments
            )
            
            # 6. 早停建議
            early_stopping = await self._generate_early_stopping_recommendation(
                performance_data, convergence_metrics
            )
            
            # 7. 訓練建議
            recommendations = await self._generate_training_recommendations(
                convergence_metrics, curve_segments, current_phase
            )
            
            # 8. 性能預測
            forecast = await self._generate_performance_forecast(performance_data, performance_trends)
            
            # 9. 視覺化數據
            viz_data = await self._generate_convergence_visualization_data(
                performance_data, curve_segments, performance_trends
            )
            
            # 構建完整分析結果
            analysis = LearningCurveAnalysis(
                algorithm_name=algorithm_name,
                session_id=session_id,
                analysis_timestamp=datetime.now(),
                total_episodes=len(performance_data['episodes']),
                current_performance=basic_stats['current_performance'],
                best_performance=basic_stats['best_performance'],
                worst_performance=basic_stats['worst_performance'],
                convergence_metrics=convergence_metrics,
                curve_segments=curve_segments,
                performance_trends=performance_trends,
                current_phase=current_phase,
                phase_transitions=phase_transitions,
                early_stopping_recommendation=early_stopping,
                training_recommendations=recommendations,
                performance_forecast=forecast,
                visualization_data=viz_data
            )
            
            # 緩存結果
            self.analysis_cache[session_id] = analysis
            
            self.logger.info(f"Convergence analysis completed for session {session_id}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in convergence analysis: {e}")
            return self._create_error_analysis(session_id, algorithm_name, e)
    
    def _extract_performance_data(self, training_data: Dict[str, Any]) -> Dict[str, List]:
        """提取性能數據"""
        episodes = training_data.get('episodes', [])
        
        if not episodes:
            # 嘗試從其他格式提取
            episode_rewards = training_data.get('episode_rewards', [])
            if episode_rewards:
                episodes = [{'episode': i, 'total_reward': reward} for i, reward in enumerate(episode_rewards)]
        
        # 標準化數據格式
        performance_data = {
            'episodes': [],
            'total_rewards': [],
            'success_rates': [],
            'episode_lengths': [],
            'timestamps': []
        }
        
        for i, episode in enumerate(episodes):
            if isinstance(episode, dict):
                performance_data['episodes'].append(episode.get('episode', i))
                performance_data['total_rewards'].append(episode.get('total_reward', 0))
                performance_data['success_rates'].append(episode.get('success_rate', 0))
                performance_data['episode_lengths'].append(episode.get('episode_length', 0))
                performance_data['timestamps'].append(episode.get('timestamp', datetime.now()))
            else:
                # 假設是簡單的獎勵列表
                performance_data['episodes'].append(i)
                performance_data['total_rewards'].append(float(episode))
                performance_data['success_rates'].append(0)
                performance_data['episode_lengths'].append(0)
                performance_data['timestamps'].append(datetime.now())
        
        return performance_data
    
    def _calculate_basic_statistics(self, performance_data: Dict[str, List]) -> Dict[str, float]:
        """計算基本統計指標"""
        rewards = performance_data['total_rewards']
        
        if not rewards:
            return {
                'current_performance': 0.0,
                'best_performance': 0.0,
                'worst_performance': 0.0,
                'mean_performance': 0.0,
                'std_performance': 0.0
            }
        
        return {
            'current_performance': float(rewards[-1]),
            'best_performance': float(max(rewards)),
            'worst_performance': float(min(rewards)),
            'mean_performance': float(np.mean(rewards)),
            'std_performance': float(np.std(rewards))
        }
    
    async def _analyze_convergence_metrics(self, performance_data: Dict[str, List]) -> ConvergenceMetrics:
        """分析收斂性指標"""
        rewards = np.array(performance_data['total_rewards'])
        
        if len(rewards) < self.min_episodes_for_analysis:
            return ConvergenceMetrics(
                convergence_score=0.0,
                stability_score=0.0,
                improvement_rate=0.0,
                episodes_to_convergence=None,
                confidence_interval=(0.0, 0.0),
                trend_direction=TrendDirection.STABLE,
                convergence_status=ConvergenceStatus.INSUFFICIENT_DATA
            )
        
        # 計算收斂分數
        convergence_score = await self._calculate_convergence_score(rewards)
        
        # 計算穩定性分數
        stability_score = await self._calculate_stability_score(rewards)
        
        # 計算改進速率
        improvement_rate = await self._calculate_improvement_rate(rewards)
        
        # 預估收斂所需episode數
        episodes_to_convergence = await self._estimate_convergence_episodes(rewards, improvement_rate)
        
        # 計算置信區間
        confidence_interval = await self._calculate_confidence_interval(rewards)
        
        # 趨勢方向
        trend_direction = await self._determine_trend_direction(rewards)
        
        # 收斂狀態
        convergence_status = await self._determine_convergence_status(
            rewards, convergence_score, stability_score, improvement_rate
        )
        
        return ConvergenceMetrics(
            convergence_score=convergence_score,
            stability_score=stability_score,
            improvement_rate=improvement_rate,
            episodes_to_convergence=episodes_to_convergence,
            confidence_interval=confidence_interval,
            trend_direction=trend_direction,
            convergence_status=convergence_status
        )
    
    async def _calculate_convergence_score(self, rewards: np.ndarray) -> float:
        """計算收斂分數"""
        if len(rewards) < self.convergence_window_size:
            window_size = len(rewards) // 2
        else:
            window_size = self.convergence_window_size
        
        if window_size < 5:
            return 0.0
        
        # 計算最近窗口的穩定性
        recent_rewards = rewards[-window_size:]
        recent_mean = np.mean(recent_rewards)
        recent_std = np.std(recent_rewards)
        
        # 相對標準差作為穩定性指標
        coefficient_of_variation = recent_std / abs(recent_mean) if recent_mean != 0 else float('inf')
        
        # 轉換為收斂分數 (0-1)
        convergence_score = max(0.0, 1.0 - min(1.0, coefficient_of_variation))
        
        return float(convergence_score)
    
    async def _calculate_stability_score(self, rewards: np.ndarray) -> float:
        """計算穩定性分數"""
        if len(rewards) < 10:
            return 0.0
        
        # 使用滾動標準差評估穩定性
        window_size = min(20, len(rewards) // 2)
        rolling_stds = []
        
        for i in range(window_size, len(rewards)):
            window_std = np.std(rewards[i-window_size:i])
            rolling_stds.append(window_std)
        
        if not rolling_stds:
            return 0.0
        
        # 計算穩定性趨勢
        recent_stability = np.mean(rolling_stds[-5:]) if len(rolling_stds) >= 5 else np.mean(rolling_stds)
        overall_range = np.max(rewards) - np.min(rewards)
        
        # 標準化穩定性分數
        if overall_range > 0:
            stability_score = max(0.0, 1.0 - (recent_stability / overall_range))
        else:
            stability_score = 1.0
        
        return float(stability_score)
    
    async def _calculate_improvement_rate(self, rewards: np.ndarray) -> float:
        """計算改進速率"""
        if len(rewards) < 2:
            return 0.0
        
        # 使用線性回歸計算趨勢
        episodes = np.arange(len(rewards))
        
        if SKLEARN_AVAILABLE:
            # 使用sklearn進行線性回歸
            model = LinearRegression()
            model.fit(episodes.reshape(-1, 1), rewards)
            improvement_rate = float(model.coef_[0])
        else:
            # 簡單的線性趨勢計算
            improvement_rate = float((rewards[-1] - rewards[0]) / len(rewards))
        
        return improvement_rate
    
    async def _estimate_convergence_episodes(
        self, 
        rewards: np.ndarray, 
        improvement_rate: float
    ) -> Optional[int]:
        """預估收斂所需episode數"""
        if improvement_rate <= 0:
            return None
        
        current_performance = rewards[-1]
        best_performance = np.max(rewards)
        
        # 如果已經達到最佳性能，認為已收斂
        if abs(current_performance - best_performance) < self.convergence_threshold:
            return 0
        
        # 基於改進速率估算
        performance_gap = best_performance - current_performance
        estimated_episodes = int(performance_gap / improvement_rate)
        
        # 添加安全邊際
        estimated_episodes = int(estimated_episodes * 1.5)
        
        # 限制最大預估值
        return min(estimated_episodes, 1000) if estimated_episodes > 0 else None
    
    async def _calculate_confidence_interval(
        self, 
        rewards: np.ndarray, 
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """計算性能置信區間"""
        if len(rewards) < 2:
            return (0.0, 0.0)
        
        window_size = min(self.convergence_window_size, len(rewards))
        recent_rewards = rewards[-window_size:]
        
        mean_reward = np.mean(recent_rewards)
        std_reward = np.std(recent_rewards)
        
        if SCIPY_AVAILABLE:
            # 使用t分布計算置信區間
            alpha = 1 - confidence_level
            t_value = stats.t.ppf(1 - alpha/2, len(recent_rewards) - 1)
            margin_error = t_value * std_reward / np.sqrt(len(recent_rewards))
        else:
            # 簡化計算
            margin_error = 1.96 * std_reward / np.sqrt(len(recent_rewards))
        
        lower_bound = mean_reward - margin_error
        upper_bound = mean_reward + margin_error
        
        return (float(lower_bound), float(upper_bound))
    
    async def _determine_trend_direction(self, rewards: np.ndarray) -> TrendDirection:
        """確定趨勢方向"""
        if len(rewards) < self.trend_window_size:
            window_size = len(rewards)
        else:
            window_size = self.trend_window_size
        
        if window_size < 3:
            return TrendDirection.STABLE
        
        recent_rewards = rewards[-window_size:]
        
        # 計算趨勢斜率
        episodes = np.arange(len(recent_rewards))
        if SKLEARN_AVAILABLE:
            model = LinearRegression()
            model.fit(episodes.reshape(-1, 1), recent_rewards)
            slope = model.coef_[0]
        else:
            slope = (recent_rewards[-1] - recent_rewards[0]) / len(recent_rewards)
        
        # 計算變異性
        volatility = np.std(recent_rewards) / np.mean(np.abs(recent_rewards)) if np.mean(np.abs(recent_rewards)) > 0 else 0
        
        # 判斷趨勢
        if volatility > 0.2:
            return TrendDirection.VOLATILE
        elif slope > self.stagnation_threshold:
            return TrendDirection.IMPROVING
        elif slope < -self.stagnation_threshold:
            return TrendDirection.DECLINING
        else:
            return TrendDirection.STABLE
    
    async def _determine_convergence_status(
        self,
        rewards: np.ndarray,
        convergence_score: float,
        stability_score: float,
        improvement_rate: float
    ) -> ConvergenceStatus:
        """確定收斂狀態"""
        if len(rewards) < self.min_episodes_for_analysis:
            return ConvergenceStatus.INSUFFICIENT_DATA
        
        # 檢查收斂
        if convergence_score > 0.8 and stability_score > 0.8:
            return ConvergenceStatus.CONVERGED
        
        # 檢查發散
        if improvement_rate < -self.stagnation_threshold and stability_score < 0.3:
            return ConvergenceStatus.DIVERGING
        
        # 檢查震盪
        recent_rewards = rewards[-self.trend_window_size:]
        if len(recent_rewards) > 5:
            peaks = 0
            for i in range(1, len(recent_rewards) - 1):
                if recent_rewards[i] > recent_rewards[i-1] and recent_rewards[i] > recent_rewards[i+1]:
                    peaks += 1
            oscillation_ratio = peaks / (len(recent_rewards) / 2)
            
            if oscillation_ratio > self.oscillation_threshold:
                return ConvergenceStatus.OSCILLATING
        
        # 檢查停滯
        if abs(improvement_rate) < self.stagnation_threshold and convergence_score < 0.5:
            return ConvergenceStatus.STAGNANT
        
        # 默認為收斂中
        return ConvergenceStatus.CONVERGING
    
    async def _segment_learning_curve(self, performance_data: Dict[str, List]) -> List[LearningCurveSegment]:
        """分割學習曲線"""
        rewards = np.array(performance_data['total_rewards'])
        episodes = np.array(performance_data['episodes'])
        
        if len(rewards) < 10:
            # 數據太少，返回單一段
            return [LearningCurveSegment(
                start_episode=0,
                end_episode=len(rewards) - 1,
                segment_type=PerformancePhase.INITIAL_EXPLORATION,
                slope=0.0,
                r_squared=0.0,
                mean_performance=float(np.mean(rewards)),
                variance=float(np.var(rewards)),
                description="數據不足，無法分割"
            )]
        
        segments = []
        segment_size = max(5, len(rewards) // 4)  # 每段至少5個episode
        
        for i in range(0, len(rewards), segment_size):
            end_idx = min(i + segment_size, len(rewards))
            segment_rewards = rewards[i:end_idx]
            segment_episodes = episodes[i:end_idx]
            
            if len(segment_rewards) < 3:
                continue
            
            # 計算段統計
            slope = await self._calculate_segment_slope(segment_episodes, segment_rewards)
            r_squared = await self._calculate_segment_r_squared(segment_episodes, segment_rewards)
            mean_perf = float(np.mean(segment_rewards))
            variance = float(np.var(segment_rewards))
            
            # 確定段類型
            segment_type = await self._classify_segment_type(slope, r_squared, variance, i, len(rewards))
            
            # 生成描述
            description = await self._generate_segment_description(
                segment_type, slope, r_squared, mean_perf
            )
            
            segment = LearningCurveSegment(
                start_episode=int(segment_episodes[0]),
                end_episode=int(segment_episodes[-1]),
                segment_type=segment_type,
                slope=slope,
                r_squared=r_squared,
                mean_performance=mean_perf,
                variance=variance,
                description=description
            )
            
            segments.append(segment)
        
        return segments
    
    async def _calculate_segment_slope(self, episodes: np.ndarray, rewards: np.ndarray) -> float:
        """計算段斜率"""
        if SKLEARN_AVAILABLE and len(episodes) > 2:
            model = LinearRegression()
            model.fit(episodes.reshape(-1, 1), rewards)
            return float(model.coef_[0])
        else:
            return float((rewards[-1] - rewards[0]) / (episodes[-1] - episodes[0])) if len(rewards) > 1 else 0.0
    
    async def _calculate_segment_r_squared(self, episodes: np.ndarray, rewards: np.ndarray) -> float:
        """計算段R²值"""
        if len(episodes) < 3:
            return 0.0
        
        if SKLEARN_AVAILABLE:
            model = LinearRegression()
            model.fit(episodes.reshape(-1, 1), rewards)
            return float(model.score(episodes.reshape(-1, 1), rewards))
        else:
            # 簡化的R²計算
            mean_reward = np.mean(rewards)
            ss_res = np.sum((rewards - np.mean(rewards)) ** 2)
            ss_tot = np.sum((rewards - mean_reward) ** 2)
            return float(1 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0
    
    async def _classify_segment_type(
        self, 
        slope: float, 
        r_squared: float, 
        variance: float,
        segment_start: int,
        total_episodes: int
    ) -> PerformancePhase:
        """分類段類型"""
        # 基於在訓練中的位置
        position_ratio = segment_start / total_episodes
        
        # 基於斜率和擬合度
        if position_ratio < 0.2:
            return PerformancePhase.INITIAL_EXPLORATION
        elif slope > 0.1 and r_squared > 0.5:
            return PerformancePhase.RAPID_LEARNING
        elif abs(slope) < 0.05 and variance < 0.1:
            if position_ratio > 0.8:
                return PerformancePhase.CONVERGED
            else:
                return PerformancePhase.FINE_TUNING
        elif slope < -0.05:
            return PerformancePhase.OVERFITTING
        else:
            return PerformancePhase.FINE_TUNING
    
    async def _generate_segment_description(
        self,
        segment_type: PerformancePhase,
        slope: float,
        r_squared: float,
        mean_performance: float
    ) -> str:
        """生成段描述"""
        type_descriptions = {
            PerformancePhase.INITIAL_EXPLORATION: "初始探索階段，性能波動較大",
            PerformancePhase.RAPID_LEARNING: f"快速學習階段，性能提升率 {slope:.3f}",
            PerformancePhase.FINE_TUNING: f"微調階段，平均性能 {mean_performance:.3f}",
            PerformancePhase.CONVERGED: f"收斂階段，性能穩定在 {mean_performance:.3f}",
            PerformancePhase.OVERFITTING: f"可能過擬合，性能下降 {slope:.3f}"
        }
        
        base_description = type_descriptions.get(segment_type, "未知階段")
        return f"{base_description}，擬合度 R² = {r_squared:.3f}"
    
    async def _analyze_performance_trends(
        self,
        performance_data: Dict[str, List],
        metrics: List[str]
    ) -> Dict[str, PerformanceTrend]:
        """分析性能趨勢"""
        trends = {}
        
        for metric in metrics:
            if metric in performance_data:
                values = np.array(performance_data[metric])
                if len(values) > 0:
                    trend = await self._analyze_single_metric_trend(metric, values)
                    trends[metric] = trend
        
        return trends
    
    async def _analyze_single_metric_trend(self, metric_name: str, values: np.ndarray) -> PerformanceTrend:
        """分析單一指標趨勢"""
        if len(values) < 2:
            return PerformanceTrend(
                metric_name=metric_name,
                current_value=float(values[0]) if len(values) > 0 else 0.0,
                trend_direction=TrendDirection.STABLE,
                trend_strength=0.0,
                recent_change=0.0,
                volatility=0.0,
                prediction_horizon=0,
                predicted_values=[],
                confidence_bounds=[]
            )
        
        current_value = float(values[-1])
        
        # 趨勢方向和強度
        trend_direction = await self._determine_trend_direction(values)
        trend_strength = await self._calculate_trend_strength(values)
        
        # 最近變化
        recent_window = min(10, len(values))
        recent_change = float(values[-1] - values[-recent_window])
        
        # 波動性
        volatility = float(np.std(values) / np.mean(np.abs(values))) if np.mean(np.abs(values)) > 0 else 0.0
        
        # 預測
        prediction_horizon = min(10, len(values) // 2)
        predicted_values, confidence_bounds = await self._predict_performance_trend(
            values, prediction_horizon
        )
        
        return PerformanceTrend(
            metric_name=metric_name,
            current_value=current_value,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            recent_change=recent_change,
            volatility=volatility,
            prediction_horizon=prediction_horizon,
            predicted_values=predicted_values,
            confidence_bounds=confidence_bounds
        )
    
    async def _calculate_trend_strength(self, values: np.ndarray) -> float:
        """計算趨勢強度"""
        if len(values) < 3:
            return 0.0
        
        # 使用線性回歸的R²值作為趨勢強度
        episodes = np.arange(len(values))
        
        if SKLEARN_AVAILABLE:
            model = LinearRegression()
            model.fit(episodes.reshape(-1, 1), values)
            trend_strength = float(model.score(episodes.reshape(-1, 1), values))
        else:
            # 簡化計算
            correlation = np.corrcoef(episodes, values)[0, 1]
            trend_strength = float(correlation ** 2) if not np.isnan(correlation) else 0.0
        
        return max(0.0, min(1.0, trend_strength))
    
    async def _predict_performance_trend(
        self,
        values: np.ndarray,
        horizon: int
    ) -> Tuple[List[float], List[Tuple[float, float]]]:
        """預測性能趨勢"""
        if len(values) < 3 or horizon <= 0:
            return [], []
        
        episodes = np.arange(len(values))
        future_episodes = np.arange(len(values), len(values) + horizon)
        
        try:
            if SKLEARN_AVAILABLE:
                # 使用多項式回歸進行預測
                poly_features = PolynomialFeatures(degree=2)
                X_poly = poly_features.fit_transform(episodes.reshape(-1, 1))
                
                model = LinearRegression()
                model.fit(X_poly, values)
                
                X_future_poly = poly_features.transform(future_episodes.reshape(-1, 1))
                predictions = model.predict(X_future_poly)
                
                # 簡化的置信區間
                prediction_std = np.std(values - model.predict(X_poly))
                confidence_bounds = [
                    (float(pred - 1.96 * prediction_std), float(pred + 1.96 * prediction_std))
                    for pred in predictions
                ]
                
                return [float(p) for p in predictions], confidence_bounds
            else:
                # 簡化的線性預測
                slope = (values[-1] - values[0]) / len(values)
                predictions = [float(values[-1] + slope * (i + 1)) for i in range(horizon)]
                
                std_dev = float(np.std(values))
                confidence_bounds = [
                    (pred - 1.96 * std_dev, pred + 1.96 * std_dev)
                    for pred in predictions
                ]
                
                return predictions, confidence_bounds
                
        except Exception as e:
            self.logger.warning(f"Prediction failed: {e}")
            return [], []
    
    async def _identify_training_phase(
        self,
        performance_data: Dict[str, List],
        curve_segments: List[LearningCurveSegment]
    ) -> Tuple[PerformancePhase, List[Tuple[int, PerformancePhase]]]:
        """識別當前訓練階段和階段轉換"""
        if not curve_segments:
            return PerformancePhase.INITIAL_EXPLORATION, []
        
        # 當前階段是最後一個段的類型
        current_phase = curve_segments[-1].segment_type
        
        # 階段轉換記錄
        phase_transitions = []
        prev_phase = None
        
        for segment in curve_segments:
            if prev_phase is not None and segment.segment_type != prev_phase:
                phase_transitions.append((segment.start_episode, segment.segment_type))
            prev_phase = segment.segment_type
        
        return current_phase, phase_transitions
    
    async def _generate_early_stopping_recommendation(
        self,
        performance_data: Dict[str, List],
        convergence_metrics: ConvergenceMetrics
    ) -> Optional[int]:
        """生成早停建議"""
        if convergence_metrics.convergence_status == ConvergenceStatus.CONVERGED:
            return len(performance_data['episodes'])
        
        if convergence_metrics.convergence_status == ConvergenceStatus.STAGNANT:
            # 建議在停滯開始後繼續一定episode數
            stagnant_threshold = 20
            return len(performance_data['episodes']) + stagnant_threshold
        
        if convergence_metrics.convergence_status == ConvergenceStatus.DIVERGING:
            # 建議立即停止
            return len(performance_data['episodes'])
        
        if convergence_metrics.episodes_to_convergence:
            # 基於預估收斂時間給建議
            current_episodes = len(performance_data['episodes'])
            recommended_stop = current_episodes + convergence_metrics.episodes_to_convergence
            return min(recommended_stop, current_episodes + 200)  # 最多再訓練200個episode
        
        return None
    
    async def _generate_training_recommendations(
        self,
        convergence_metrics: ConvergenceMetrics,
        curve_segments: List[LearningCurveSegment],
        current_phase: PerformancePhase
    ) -> List[str]:
        """生成訓練建議"""
        recommendations = []
        
        # 基於收斂狀態的建議
        if convergence_metrics.convergence_status == ConvergenceStatus.CONVERGED:
            recommendations.append("訓練已收斂，建議保存模型並進行評估")
        elif convergence_metrics.convergence_status == ConvergenceStatus.DIVERGING:
            recommendations.append("性能發散，建議降低學習率或檢查獎勵函數")
        elif convergence_metrics.convergence_status == ConvergenceStatus.STAGNANT:
            recommendations.append("訓練停滯，建議調整探索策略或增加網絡複雜度")
        elif convergence_metrics.convergence_status == ConvergenceStatus.OSCILLATING:
            recommendations.append("性能震盪，建議降低學習率或增加批大小")
        
        # 基於穩定性的建議
        if convergence_metrics.stability_score < 0.5:
            recommendations.append("訓練不穩定，建議使用學習率調度或梯度裁剪")
        
        # 基於改進速率的建議
        if convergence_metrics.improvement_rate < 0.01:
            recommendations.append("改進緩慢，建議檢查網絡架構或調整超參數")
        
        # 基於訓練階段的建議
        if current_phase == PerformancePhase.INITIAL_EXPLORATION:
            recommendations.append("初始探索階段，可以適當增加探索率")
        elif current_phase == PerformancePhase.OVERFITTING:
            recommendations.append("可能過擬合，建議使用正則化或早停")
        
        return recommendations
    
    async def _generate_performance_forecast(
        self,
        performance_data: Dict[str, List],
        performance_trends: Dict[str, PerformanceTrend]
    ) -> Dict[str, Any]:
        """生成性能預測"""
        forecast = {
            'forecast_horizon': 10,
            'predictions': {},
            'confidence_level': 0.95,
            'forecast_quality': 'medium'
        }
        
        for metric_name, trend in performance_trends.items():
            if trend.predicted_values:
                forecast['predictions'][metric_name] = {
                    'values': trend.predicted_values,
                    'confidence_bounds': trend.confidence_bounds,
                    'trend_direction': trend.trend_direction.value,
                    'trend_strength': trend.trend_strength
                }
        
        return forecast
    
    async def _generate_convergence_visualization_data(
        self,
        performance_data: Dict[str, List],
        curve_segments: List[LearningCurveSegment],
        performance_trends: Dict[str, PerformanceTrend]
    ) -> Dict[str, Any]:
        """生成收斂性視覺化數據"""
        viz_data = {
            # 基本性能曲線
            'performance_curve': {
                'episodes': performance_data['episodes'],
                'rewards': performance_data['total_rewards'],
                'success_rates': performance_data.get('success_rates', [])
            },
            
            # 曲線分段
            'curve_segments': [
                {
                    'start': seg.start_episode,
                    'end': seg.end_episode,
                    'type': seg.segment_type.value,
                    'slope': seg.slope,
                    'mean_performance': seg.mean_performance
                }
                for seg in curve_segments
            ],
            
            # 趨勢預測
            'trend_predictions': {},
            
            # 收斂性指標
            'convergence_indicators': {
                'convergence_window': self.convergence_window_size,
                'stability_window': self.trend_window_size
            }
        }
        
        # 添加趨勢預測數據
        for metric_name, trend in performance_trends.items():
            if trend.predicted_values:
                current_episodes = len(performance_data['episodes'])
                future_episodes = list(range(
                    current_episodes, 
                    current_episodes + len(trend.predicted_values)
                ))
                
                viz_data['trend_predictions'][metric_name] = {
                    'episodes': future_episodes,
                    'predictions': trend.predicted_values,
                    'confidence_bounds': trend.confidence_bounds
                }
        
        return viz_data
    
    def _create_insufficient_data_analysis(
        self,
        session_id: str,
        algorithm_name: str,
        performance_data: Dict[str, List]
    ) -> LearningCurveAnalysis:
        """創建數據不足的分析結果"""
        return LearningCurveAnalysis(
            algorithm_name=algorithm_name,
            session_id=session_id,
            analysis_timestamp=datetime.now(),
            total_episodes=len(performance_data.get('episodes', [])),
            current_performance=0.0,
            best_performance=0.0,
            worst_performance=0.0,
            convergence_metrics=ConvergenceMetrics(
                convergence_score=0.0,
                stability_score=0.0,
                improvement_rate=0.0,
                episodes_to_convergence=None,
                confidence_interval=(0.0, 0.0),
                trend_direction=TrendDirection.STABLE,
                convergence_status=ConvergenceStatus.INSUFFICIENT_DATA
            ),
            curve_segments=[],
            performance_trends={},
            current_phase=PerformancePhase.INITIAL_EXPLORATION,
            phase_transitions=[],
            early_stopping_recommendation=None,
            training_recommendations=["需要更多訓練數據進行分析"],
            performance_forecast={},
            visualization_data={}
        )
    
    def _create_error_analysis(
        self,
        session_id: str,
        algorithm_name: str,
        error: Exception
    ) -> LearningCurveAnalysis:
        """創建錯誤情況的分析結果"""
        return LearningCurveAnalysis(
            algorithm_name=algorithm_name,
            session_id=session_id,
            analysis_timestamp=datetime.now(),
            total_episodes=0,
            current_performance=0.0,
            best_performance=0.0,
            worst_performance=0.0,
            convergence_metrics=ConvergenceMetrics(
                convergence_score=0.0,
                stability_score=0.0,
                improvement_rate=0.0,
                episodes_to_convergence=None,
                confidence_interval=(0.0, 0.0),
                trend_direction=TrendDirection.STABLE,
                convergence_status=ConvergenceStatus.INSUFFICIENT_DATA
            ),
            curve_segments=[],
            performance_trends={},
            current_phase=PerformancePhase.INITIAL_EXPLORATION,
            phase_transitions=[],
            early_stopping_recommendation=None,
            training_recommendations=[f"分析失敗: {str(error)}"],
            performance_forecast={},
            visualization_data={}
        )
    
    async def compare_convergence_across_algorithms(
        self,
        algorithm_analyses: Dict[str, LearningCurveAnalysis]
    ) -> Dict[str, Any]:
        """比較不同算法的收斂性"""
        comparison = {
            'algorithms': list(algorithm_analyses.keys()),
            'convergence_comparison': {},
            'performance_comparison': {},
            'recommendations': []
        }
        
        # 收斂性比較
        for alg_name, analysis in algorithm_analyses.items():
            comparison['convergence_comparison'][alg_name] = {
                'convergence_score': analysis.convergence_metrics.convergence_score,
                'stability_score': analysis.convergence_metrics.stability_score,
                'convergence_status': analysis.convergence_metrics.convergence_status.value,
                'episodes_to_convergence': analysis.convergence_metrics.episodes_to_convergence
            }
            
            comparison['performance_comparison'][alg_name] = {
                'best_performance': analysis.best_performance,
                'current_performance': analysis.current_performance,
                'improvement_rate': analysis.convergence_metrics.improvement_rate
            }
        
        # 生成比較建議
        if len(algorithm_analyses) > 1:
            # 找出最佳收斂算法
            best_convergence = max(
                algorithm_analyses.items(),
                key=lambda x: x[1].convergence_metrics.convergence_score
            )
            comparison['recommendations'].append(
                f"{best_convergence[0]} 具有最佳收斂性能 "
                f"(收斂分數: {best_convergence[1].convergence_metrics.convergence_score:.3f})"
            )
            
            # 找出最佳性能算法
            best_performance = max(
                algorithm_analyses.items(),
                key=lambda x: x[1].best_performance
            )
            comparison['recommendations'].append(
                f"{best_performance[0]} 達到最佳性能 "
                f"(最佳獎勵: {best_performance[1].best_performance:.3f})"
            )
        
        return comparison
    
    async def export_convergence_analysis(
        self,
        analysis: LearningCurveAnalysis,
        export_format: str = 'json'
    ) -> Dict[str, Any]:
        """匯出收斂性分析結果"""
        export_data = {
            'metadata': {
                'algorithm_name': analysis.algorithm_name,
                'session_id': analysis.session_id,
                'analysis_timestamp': analysis.analysis_timestamp.isoformat(),
                'total_episodes': analysis.total_episodes,
                'export_format': export_format
            },
            'convergence_metrics': {
                'convergence_score': analysis.convergence_metrics.convergence_score,
                'stability_score': analysis.convergence_metrics.stability_score,
                'improvement_rate': analysis.convergence_metrics.improvement_rate,
                'convergence_status': analysis.convergence_metrics.convergence_status.value,
                'trend_direction': analysis.convergence_metrics.trend_direction.value
            },
            'performance_summary': {
                'current_performance': analysis.current_performance,
                'best_performance': analysis.best_performance,
                'worst_performance': analysis.worst_performance
            },
            'training_insights': {
                'current_phase': analysis.current_phase.value,
                'early_stopping_recommendation': analysis.early_stopping_recommendation,
                'training_recommendations': analysis.training_recommendations
            },
            'visualization_data': analysis.visualization_data
        }
        
        return export_data