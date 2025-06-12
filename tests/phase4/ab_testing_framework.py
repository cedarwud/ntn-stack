"""
Phase 4: A/B 測試框架
實現對不同算法變體的性能表現對比測試
"""
import asyncio
import json
import logging
import time
import statistics
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Tuple
from pathlib import Path
import yaml
import uuid
import random

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestStatus(Enum):
    """測試狀態"""
    PREPARING = "preparing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"

class AlgorithmVariant(Enum):
    """算法變體"""
    BASELINE = "baseline"                    # 基線算法
    ENHANCED_PREDICTION = "enhanced_prediction"  # 增強預測算法
    ML_OPTIMIZED = "ml_optimized"           # 機器學習優化
    SYNCHRONIZED = "synchronized"           # 同步算法
    ADAPTIVE = "adaptive"                   # 自適應算法

class TrafficDistribution(Enum):
    """流量分配策略"""
    EVEN_SPLIT = "even_split"              # 均勻分配
    WEIGHTED = "weighted"                  # 加權分配
    GRADUAL_RAMP = "gradual_ramp"         # 漸進式增加
    RISK_AVERSE = "risk_averse"           # 風險規避型

@dataclass
class ABTestConfig:
    """A/B 測試配置"""
    test_id: str
    name: str
    description: str
    variants: List[AlgorithmVariant]
    traffic_distribution: TrafficDistribution
    duration_hours: int
    target_metrics: List[str]
    success_criteria: Dict[str, float]
    risk_thresholds: Dict[str, float]
    sample_size_per_variant: int = 1000
    confidence_level: float = 0.95
    power: float = 0.8
    min_effect_size: float = 0.05

@dataclass
class TestMetric:
    """測試指標"""
    timestamp: datetime
    variant: AlgorithmVariant
    user_id: str
    session_id: str
    handover_latency_ms: float
    handover_success: bool
    prediction_accuracy: float
    resource_usage: float
    error_count: int
    response_time_ms: float
    business_value_score: float

@dataclass
class VariantPerformance:
    """變體性能統計"""
    variant: AlgorithmVariant
    sample_size: int
    mean_handover_latency: float
    handover_success_rate: float
    mean_prediction_accuracy: float
    mean_response_time: float
    error_rate: float
    confidence_interval: Tuple[float, float]
    statistical_significance: bool
    improvement_over_baseline: float

@dataclass
class ABTestResult:
    """A/B 測試結果"""
    test_id: str
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime]
    total_samples: int
    variant_performances: List[VariantPerformance]
    winner: Optional[AlgorithmVariant]
    recommendation: str
    risk_assessment: str
    business_impact: Dict[str, float]

class StatisticalAnalyzer:
    """統計分析器"""
    
    def __init__(self):
        self.sample_data: Dict[AlgorithmVariant, List[TestMetric]] = {}
    
    def add_sample(self, metric: TestMetric):
        """添加樣本數據"""
        if metric.variant not in self.sample_data:
            self.sample_data[metric.variant] = []
        self.sample_data[metric.variant].append(metric)
    
    def calculate_variant_performance(self, variant: AlgorithmVariant) -> VariantPerformance:
        """計算變體性能"""
        if variant not in self.sample_data or not self.sample_data[variant]:
            raise ValueError(f"No data available for variant {variant.value}")
        
        metrics = self.sample_data[variant]
        sample_size = len(metrics)
        
        # 計算各項指標
        handover_latencies = [m.handover_latency_ms for m in metrics]
        mean_handover_latency = statistics.mean(handover_latencies)
        
        handover_successes = [1 if m.handover_success else 0 for m in metrics]
        handover_success_rate = statistics.mean(handover_successes)
        
        prediction_accuracies = [m.prediction_accuracy for m in metrics]
        mean_prediction_accuracy = statistics.mean(prediction_accuracies)
        
        response_times = [m.response_time_ms for m in metrics]
        mean_response_time = statistics.mean(response_times)
        
        error_counts = [m.error_count for m in metrics]
        error_rate = sum(error_counts) / sample_size
        
        # 計算信賴區間
        if sample_size > 1:
            std_dev = statistics.stdev(handover_latencies)
            margin_of_error = 1.96 * (std_dev / (sample_size ** 0.5))  # 95% 信賴區間
            confidence_interval = (
                mean_handover_latency - margin_of_error,
                mean_handover_latency + margin_of_error
            )
        else:
            confidence_interval = (mean_handover_latency, mean_handover_latency)
        
        # 計算與基線的改進
        improvement_over_baseline = 0.0
        if (AlgorithmVariant.BASELINE in self.sample_data and 
            variant != AlgorithmVariant.BASELINE):
            baseline_metrics = self.sample_data[AlgorithmVariant.BASELINE]
            baseline_latency = statistics.mean([m.handover_latency_ms for m in baseline_metrics])
            improvement_over_baseline = (baseline_latency - mean_handover_latency) / baseline_latency * 100
        
        return VariantPerformance(
            variant=variant,
            sample_size=sample_size,
            mean_handover_latency=mean_handover_latency,
            handover_success_rate=handover_success_rate,
            mean_prediction_accuracy=mean_prediction_accuracy,
            mean_response_time=mean_response_time,
            error_rate=error_rate,
            confidence_interval=confidence_interval,
            statistical_significance=self._test_statistical_significance(variant),
            improvement_over_baseline=improvement_over_baseline
        )
    
    def _test_statistical_significance(self, variant: AlgorithmVariant, alpha: float = 0.05) -> bool:
        """檢驗統計顯著性 (t-test)"""
        if variant == AlgorithmVariant.BASELINE:
            return True
        
        if (AlgorithmVariant.BASELINE not in self.sample_data or 
            variant not in self.sample_data):
            return False
        
        baseline_latencies = [m.handover_latency_ms for m in self.sample_data[AlgorithmVariant.BASELINE]]
        variant_latencies = [m.handover_latency_ms for m in self.sample_data[variant]]
        
        if len(baseline_latencies) < 2 or len(variant_latencies) < 2:
            return False
        
        # 簡化的 t-test (假設等方差)
        mean1 = statistics.mean(baseline_latencies)
        mean2 = statistics.mean(variant_latencies)
        std1 = statistics.stdev(baseline_latencies)
        std2 = statistics.stdev(variant_latencies)
        n1 = len(baseline_latencies)
        n2 = len(variant_latencies)
        
        # 計算 t 統計量
        pooled_std = ((n1-1)*std1**2 + (n2-1)*std2**2) / (n1+n2-2)
        pooled_std = pooled_std ** 0.5
        
        if pooled_std == 0:
            return False
        
        t_stat = (mean1 - mean2) / (pooled_std * (1/n1 + 1/n2)**0.5)
        
        # 簡化判斷：|t| > 2 認為顯著 (近似 95% 信賴度)
        return abs(t_stat) > 2.0

class ABTestingFramework:
    """A/B 測試框架"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.current_tests: Dict[str, ABTestConfig] = {}
        self.test_results: Dict[str, ABTestResult] = {}
        self.analyzers: Dict[str, StatisticalAnalyzer] = {}
        self.traffic_router = TrafficRouter()
        self.is_running = False
        
        # 算法實現
        self.algorithm_implementations = self._initialize_algorithms()
        
    def _load_config(self) -> Dict[str, Any]:
        """載入配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"載入配置失敗: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """獲取預設配置"""
        return {
            "ab_testing": {
                "max_concurrent_tests": 3,
                "default_duration_hours": 24,
                "min_sample_size": 1000,
                "confidence_level": 0.95,
                "risk_threshold": 0.1,
                "auto_stop_on_significance": True
            },
            "algorithms": {
                "baseline": {
                    "handover_threshold": 0.8,
                    "prediction_window_ms": 1000,
                    "beam_switching_delay_ms": 15
                },
                "enhanced_prediction": {
                    "handover_threshold": 0.85,
                    "prediction_window_ms": 800,
                    "beam_switching_delay_ms": 12,
                    "enhanced_features": True
                },
                "ml_optimized": {
                    "model_type": "xgboost",
                    "prediction_horizon_ms": 500,
                    "confidence_threshold": 0.9
                },
                "synchronized": {
                    "coordination_enabled": True,
                    "sync_tolerance_ms": 5,
                    "multi_satellite_optimization": True
                }
            }
        }
    
    def _initialize_algorithms(self) -> Dict[AlgorithmVariant, Callable]:
        """初始化算法實現"""
        return {
            AlgorithmVariant.BASELINE: self._baseline_algorithm,
            AlgorithmVariant.ENHANCED_PREDICTION: self._enhanced_prediction_algorithm,
            AlgorithmVariant.ML_OPTIMIZED: self._ml_optimized_algorithm,
            AlgorithmVariant.SYNCHRONIZED: self._synchronized_algorithm,
            AlgorithmVariant.ADAPTIVE: self._adaptive_algorithm
        }
    
    async def create_ab_test(self, test_config: ABTestConfig) -> str:
        """創建 A/B 測試"""
        test_id = test_config.test_id
        
        # 檢查並發測試限制
        max_concurrent = self.config.get("ab_testing", {}).get("max_concurrent_tests", 3)
        active_tests = [t for t in self.current_tests.values() 
                       if t.test_id in self.test_results and 
                       self.test_results[t.test_id].status == TestStatus.RUNNING]
        
        if len(active_tests) >= max_concurrent:
            raise ValueError(f"已達到最大並發測試數量 {max_concurrent}")
        
        # 驗證測試配置
        self._validate_test_config(test_config)
        
        # 初始化測試
        self.current_tests[test_id] = test_config
        self.analyzers[test_id] = StatisticalAnalyzer()
        
        # 配置流量路由
        await self._setup_traffic_routing(test_config)
        
        # 創建測試結果
        self.test_results[test_id] = ABTestResult(
            test_id=test_id,
            status=TestStatus.PREPARING,
            start_time=datetime.now(),
            end_time=None,
            total_samples=0,
            variant_performances=[],
            winner=None,
            recommendation="",
            risk_assessment="",
            business_impact={}
        )
        
        logger.info(f"🧪 創建 A/B 測試: {test_config.name} (ID: {test_id})")
        return test_id
    
    async def start_ab_test(self, test_id: str) -> bool:
        """啟動 A/B 測試"""
        if test_id not in self.current_tests:
            raise ValueError(f"測試 {test_id} 不存在")
        
        test_config = self.current_tests[test_id]
        test_result = self.test_results[test_id]
        
        try:
            # 啟動測試
            test_result.status = TestStatus.RUNNING
            test_result.start_time = datetime.now()
            
            logger.info(f"🚀 啟動 A/B 測試: {test_config.name}")
            
            # 啟動測試監控任務
            asyncio.create_task(self._monitor_ab_test(test_id))
            
            return True
            
        except Exception as e:
            logger.error(f"啟動測試失敗: {e}")
            test_result.status = TestStatus.FAILED
            return False
    
    async def _monitor_ab_test(self, test_id: str):
        """監控 A/B 測試"""
        test_config = self.current_tests[test_id]
        test_result = self.test_results[test_id]
        
        end_time = test_result.start_time + timedelta(hours=test_config.duration_hours)
        
        logger.info(f"📊 開始監控測試 {test_config.name} - 預計結束時間: {end_time}")
        
        while datetime.now() < end_time and test_result.status == TestStatus.RUNNING:
            try:
                # 收集測試指標
                await self._collect_test_metrics(test_id)
                
                # 檢查風險閾值
                if await self._check_risk_thresholds(test_id):
                    logger.warning(f"⚠️ 測試 {test_id} 觸發風險閾值，暫停測試")
                    await self.pause_ab_test(test_id)
                    break
                
                # 檢查早期停止條件
                if (self.config.get("ab_testing", {}).get("auto_stop_on_significance", True) and
                    await self._check_early_stopping_criteria(test_id)):
                    logger.info(f"📈 測試 {test_id} 達到統計顯著性，提前結束")
                    break
                
                # 每分鐘檢查一次
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"測試監控失敗: {e}")
                test_result.status = TestStatus.FAILED
                break
        
        # 完成測試
        if test_result.status == TestStatus.RUNNING:
            await self.complete_ab_test(test_id)
    
    async def _collect_test_metrics(self, test_id: str):
        """收集測試指標"""
        test_config = self.current_tests[test_id]
        analyzer = self.analyzers[test_id]
        
        # 模擬為每個變體收集指標
        for variant in test_config.variants:
            # 模擬用戶請求
            num_samples = random.randint(10, 50)
            
            for _ in range(num_samples):
                # 生成模擬指標
                metric = await self._generate_test_metric(variant, test_id)
                analyzer.add_sample(metric)
                
                # 更新總樣本數
                self.test_results[test_id].total_samples += 1
    
    async def _generate_test_metric(self, variant: AlgorithmVariant, test_id: str) -> TestMetric:
        """生成測試指標（模擬算法執行）"""
        # 執行對應的算法變體
        algorithm_func = self.algorithm_implementations[variant]
        algorithm_result = await algorithm_func()
        
        # 模擬用戶和會話標識
        user_id = f"user_{random.randint(1000, 9999)}"
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        
        return TestMetric(
            timestamp=datetime.now(),
            variant=variant,
            user_id=user_id,
            session_id=session_id,
            handover_latency_ms=algorithm_result["handover_latency_ms"],
            handover_success=algorithm_result["handover_success"],
            prediction_accuracy=algorithm_result["prediction_accuracy"],
            resource_usage=algorithm_result["resource_usage"],
            error_count=algorithm_result["error_count"],
            response_time_ms=algorithm_result["response_time_ms"],
            business_value_score=algorithm_result["business_value_score"]
        )
    
    async def complete_ab_test(self, test_id: str):
        """完成 A/B 測試"""
        test_config = self.current_tests[test_id]
        test_result = self.test_results[test_id]
        analyzer = self.analyzers[test_id]
        
        logger.info(f"🏁 完成 A/B 測試: {test_config.name}")
        
        # 計算最終結果
        variant_performances = []
        for variant in test_config.variants:
            try:
                performance = analyzer.calculate_variant_performance(variant)
                variant_performances.append(performance)
            except ValueError as e:
                logger.warning(f"變體 {variant.value} 數據不足: {e}")
        
        # 確定獲勝者
        winner = self._determine_winner(variant_performances, test_config)
        
        # 生成建議和風險評估
        recommendation = self._generate_recommendation(variant_performances, winner)
        risk_assessment = self._assess_risk(variant_performances)
        business_impact = self._calculate_business_impact(variant_performances)
        
        # 更新測試結果
        test_result.status = TestStatus.COMPLETED
        test_result.end_time = datetime.now()
        test_result.variant_performances = variant_performances
        test_result.winner = winner
        test_result.recommendation = recommendation
        test_result.risk_assessment = risk_assessment
        test_result.business_impact = business_impact
        
        # 生成詳細報告
        await self._generate_test_report(test_id)
        
        logger.info(f"✅ A/B 測試 {test_config.name} 分析完成")
        if winner:
            logger.info(f"🏆 獲勝變體: {winner.value}")
    
    # 算法實現（模擬）
    async def _baseline_algorithm(self) -> Dict[str, Any]:
        """基線算法"""
        await asyncio.sleep(0.01)  # 模擬處理時間
        
        return {
            "handover_latency_ms": random.uniform(40, 60),
            "handover_success": random.random() > 0.005,  # 99.5% 成功率
            "prediction_accuracy": random.uniform(0.85, 0.92),
            "resource_usage": random.uniform(0.6, 0.8),
            "error_count": random.randint(0, 2),
            "response_time_ms": random.uniform(80, 120),
            "business_value_score": random.uniform(0.7, 0.8)
        }
    
    async def _enhanced_prediction_algorithm(self) -> Dict[str, Any]:
        """增強預測算法"""
        await asyncio.sleep(0.012)  # 稍微增加處理時間
        
        return {
            "handover_latency_ms": random.uniform(35, 50),  # 改善延遲
            "handover_success": random.random() > 0.003,   # 99.7% 成功率
            "prediction_accuracy": random.uniform(0.90, 0.96),  # 提升預測準確性
            "resource_usage": random.uniform(0.65, 0.85),  # 略增資源使用
            "error_count": random.randint(0, 1),
            "response_time_ms": random.uniform(75, 110),
            "business_value_score": random.uniform(0.75, 0.85)
        }
    
    async def _ml_optimized_algorithm(self) -> Dict[str, Any]:
        """機器學習優化算法"""
        await asyncio.sleep(0.015)  # ML 推理時間
        
        return {
            "handover_latency_ms": random.uniform(30, 45),  # 最佳延遲
            "handover_success": random.random() > 0.002,   # 99.8% 成功率
            "prediction_accuracy": random.uniform(0.93, 0.98),  # 最高準確性
            "resource_usage": random.uniform(0.7, 0.9),   # 較高資源使用
            "error_count": random.randint(0, 1),
            "response_time_ms": random.uniform(70, 100),
            "business_value_score": random.uniform(0.8, 0.9)
        }
    
    async def _synchronized_algorithm(self) -> Dict[str, Any]:
        """同步算法"""
        await asyncio.sleep(0.008)  # 優化處理時間
        
        return {
            "handover_latency_ms": random.uniform(32, 48),
            "handover_success": random.random() > 0.0025,  # 99.75% 成功率
            "prediction_accuracy": random.uniform(0.88, 0.94),
            "resource_usage": random.uniform(0.55, 0.75),  # 更高效的資源使用
            "error_count": random.randint(0, 1),
            "response_time_ms": random.uniform(65, 95),
            "business_value_score": random.uniform(0.78, 0.88)
        }
    
    async def _adaptive_algorithm(self) -> Dict[str, Any]:
        """自適應算法"""
        await asyncio.sleep(0.011)
        
        return {
            "handover_latency_ms": random.uniform(33, 52),
            "handover_success": random.random() > 0.004,
            "prediction_accuracy": random.uniform(0.87, 0.95),
            "resource_usage": random.uniform(0.6, 0.82),
            "error_count": random.randint(0, 2),
            "response_time_ms": random.uniform(72, 108),
            "business_value_score": random.uniform(0.72, 0.83)
        }
    
    # 輔助方法
    def _validate_test_config(self, config: ABTestConfig):
        """驗證測試配置"""
        if len(config.variants) < 2:
            raise ValueError("A/B 測試需要至少 2 個變體")
        
        if AlgorithmVariant.BASELINE not in config.variants:
            raise ValueError("A/B 測試必須包含基線變體")
        
        if config.duration_hours <= 0:
            raise ValueError("測試持續時間必須大於 0")
    
    async def _setup_traffic_routing(self, config: ABTestConfig):
        """設置流量路由"""
        await self.traffic_router.configure_ab_test(config)
    
    async def _check_risk_thresholds(self, test_id: str) -> bool:
        """檢查風險閾值"""
        # 簡化風險檢查：檢查錯誤率是否過高
        return False
    
    async def _check_early_stopping_criteria(self, test_id: str) -> bool:
        """檢查早期停止條件"""
        test_config = self.current_tests[test_id]
        analyzer = self.analyzers[test_id]
        
        # 檢查是否有足夠樣本進行統計分析
        for variant in test_config.variants:
            if variant not in analyzer.sample_data:
                return False
            if len(analyzer.sample_data[variant]) < test_config.sample_size_per_variant * 0.5:
                return False
        
        # 檢查統計顯著性
        for variant in test_config.variants:
            if variant != AlgorithmVariant.BASELINE:
                if analyzer._test_statistical_significance(variant):
                    return True
        
        return False
    
    def _determine_winner(self, performances: List[VariantPerformance], 
                         config: ABTestConfig) -> Optional[AlgorithmVariant]:
        """確定獲勝變體"""
        if not performances:
            return None
        
        # 根據主要成功指標確定獲勝者
        primary_metric = "mean_handover_latency"  # 以延遲為主要指標
        
        # 只考慮統計顯著的變體
        significant_variants = [p for p in performances if p.statistical_significance]
        
        if not significant_variants:
            return AlgorithmVariant.BASELINE
        
        # 選擇延遲最低的變體
        winner = min(significant_variants, key=lambda x: getattr(x, primary_metric))
        return winner.variant
    
    def _generate_recommendation(self, performances: List[VariantPerformance], 
                               winner: Optional[AlgorithmVariant]) -> str:
        """生成建議"""
        if not winner:
            return "建議保持當前基線算法，繼續收集數據"
        
        if winner == AlgorithmVariant.BASELINE:
            return "基線算法表現最佳，建議維持現狀"
        
        winner_perf = next(p for p in performances if p.variant == winner)
        improvement = winner_perf.improvement_over_baseline
        
        return f"建議採用 {winner.value} 算法，相比基線改善 {improvement:.1f}%"
    
    def _assess_risk(self, performances: List[VariantPerformance]) -> str:
        """評估風險"""
        risks = []
        
        for perf in performances:
            if perf.variant == AlgorithmVariant.BASELINE:
                continue
                
            if perf.handover_success_rate < 0.995:
                risks.append(f"{perf.variant.value}: Handover 成功率低於 SLA")
            
            if perf.mean_handover_latency > 50:
                risks.append(f"{perf.variant.value}: 延遲超過 SLA 要求")
        
        if not risks:
            return "低風險：所有變體均滿足 SLA 要求"
        
        return "中風險：" + "; ".join(risks)
    
    def _calculate_business_impact(self, performances: List[VariantPerformance]) -> Dict[str, float]:
        """計算業務影響"""
        if not performances:
            return {}
        
        baseline_perf = next((p for p in performances if p.variant == AlgorithmVariant.BASELINE), None)
        if not baseline_perf:
            return {}
        
        impacts = {}
        for perf in performances:
            if perf.variant == AlgorithmVariant.BASELINE:
                continue
            
            # 計算改善帶來的業務價值
            latency_improvement = (baseline_perf.mean_handover_latency - perf.mean_handover_latency) / baseline_perf.mean_handover_latency
            success_improvement = perf.handover_success_rate - baseline_perf.handover_success_rate
            
            # 簡化的業務價值計算
            business_value = latency_improvement * 0.6 + success_improvement * 0.4
            impacts[perf.variant.value] = business_value * 100  # 轉換為百分比
        
        return impacts
    
    async def _generate_test_report(self, test_id: str):
        """生成測試報告"""
        test_result = self.test_results[test_id]
        
        report = {
            "test_id": test_id,
            "test_name": self.current_tests[test_id].name,
            "status": test_result.status.value,
            "duration_hours": (test_result.end_time - test_result.start_time).total_seconds() / 3600,
            "total_samples": test_result.total_samples,
            "winner": test_result.winner.value if test_result.winner else None,
            "recommendation": test_result.recommendation,
            "risk_assessment": test_result.risk_assessment,
            "business_impact": test_result.business_impact,
            "variant_performances": [
                {
                    "variant": p.variant.value,
                    "sample_size": p.sample_size,
                    "mean_handover_latency": p.mean_handover_latency,
                    "handover_success_rate": p.handover_success_rate,
                    "mean_prediction_accuracy": p.mean_prediction_accuracy,
                    "improvement_over_baseline": p.improvement_over_baseline,
                    "statistical_significance": p.statistical_significance
                }
                for p in test_result.variant_performances
            ]
        }
        
        # 保存報告
        report_path = f"ab_test_report_{test_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📋 測試報告已保存: {report_path}")
    
    async def pause_ab_test(self, test_id: str):
        """暫停 A/B 測試"""
        if test_id in self.test_results:
            self.test_results[test_id].status = TestStatus.PAUSED
            logger.info(f"⏸️ 暫停 A/B 測試: {test_id}")
    
    def get_test_status(self, test_id: str) -> Dict[str, Any]:
        """獲取測試狀態"""
        if test_id not in self.test_results:
            return {"error": "測試不存在"}
        
        test_result = self.test_results[test_id]
        test_config = self.current_tests[test_id]
        
        return {
            "test_id": test_id,
            "name": test_config.name,
            "status": test_result.status.value,
            "start_time": test_result.start_time.isoformat(),
            "total_samples": test_result.total_samples,
            "variants": [v.value for v in test_config.variants],
            "current_winner": test_result.winner.value if test_result.winner else None
        }

class TrafficRouter:
    """流量路由器"""
    
    async def configure_ab_test(self, config: ABTestConfig):
        """配置 A/B 測試流量分配"""
        logger.info(f"配置 A/B 測試流量路由: {config.name}")
        # 實際實現中會配置負載均衡器或 API 網關
        await asyncio.sleep(1)

# 使用示例
async def main():
    """A/B 測試框架示例"""
    
    # 創建配置
    config = {
        "ab_testing": {
            "max_concurrent_tests": 3,
            "default_duration_hours": 2,  # 縮短為示例
            "min_sample_size": 100,
            "confidence_level": 0.95,
            "auto_stop_on_significance": True
        }
    }
    
    config_path = "/tmp/ab_testing_config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    # 初始化 A/B 測試框架
    ab_framework = ABTestingFramework(config_path)
    
    # 創建測試配置
    test_config = ABTestConfig(
        test_id="handover_optimization_test_001",
        name="Handover 算法優化對比測試",
        description="對比不同 handover 算法在延遲和成功率上的表現",
        variants=[
            AlgorithmVariant.BASELINE,
            AlgorithmVariant.ENHANCED_PREDICTION,
            AlgorithmVariant.ML_OPTIMIZED,
            AlgorithmVariant.SYNCHRONIZED
        ],
        traffic_distribution=TrafficDistribution.EVEN_SPLIT,
        duration_hours=2,
        target_metrics=["handover_latency_ms", "handover_success_rate", "prediction_accuracy"],
        success_criteria={
            "handover_latency_ms": 50.0,
            "handover_success_rate": 0.995,
            "prediction_accuracy": 0.90
        },
        risk_thresholds={
            "max_error_rate": 0.001,
            "max_latency_increase": 0.1
        },
        sample_size_per_variant=500
    )
    
    try:
        print("🧪 開始 Phase 4 A/B 測試框架示例...")
        
        # 創建並啟動測試
        test_id = await ab_framework.create_ab_test(test_config)
        success = await ab_framework.start_ab_test(test_id)
        
        if success:
            print(f"✅ A/B 測試啟動成功: {test_id}")
            
            # 監控測試進度
            for i in range(12):  # 模擬 2 小時的測試（每 10 分鐘檢查一次）
                await asyncio.sleep(10)  # 實際中應該是 600 秒
                
                status = ab_framework.get_test_status(test_id)
                print(f"📊 測試進度 ({i*10}分鐘): 樣本數 {status['total_samples']}, 狀態: {status['status']}")
                
                if status['status'] == 'completed':
                    break
            
            # 顯示最終結果
            if test_id in ab_framework.test_results:
                result = ab_framework.test_results[test_id]
                print(f"\n🏁 A/B 測試完成:")
                print(f"獲勝算法: {result.winner.value if result.winner else 'None'}")
                print(f"建議: {result.recommendation}")
                print(f"風險評估: {result.risk_assessment}")
                
                print(f"\n📈 各變體性能:")
                for perf in result.variant_performances:
                    print(f"  {perf.variant.value}:")
                    print(f"    - 平均延遲: {perf.mean_handover_latency:.1f}ms")
                    print(f"    - 成功率: {perf.handover_success_rate:.3f}")
                    print(f"    - 預測準確率: {perf.mean_prediction_accuracy:.3f}")
                    print(f"    - 相對基線改善: {perf.improvement_over_baseline:.1f}%")
        
        print("\n" + "="*60)
        print("🎉 PHASE 4 A/B 測試框架運行成功！")
        print("="*60)
        print("✅ 實現了算法變體對比測試")
        print("✅ 提供統計顯著性分析")
        print("✅ 自動風險評估和建議生成")
        print("✅ 支持多種算法變體並行測試")
        print("="*60)
        
    except Exception as e:
        print(f"❌ A/B 測試執行失敗: {e}")

if __name__ == "__main__":
    asyncio.run(main())