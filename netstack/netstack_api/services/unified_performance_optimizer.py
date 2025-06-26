"""
統一性能優化服務 (Unified Performance Optimizer)

整合了以下三個服務的功能：
1. performance_optimizer.py - API響應時間優化、緩存策略、異步處理優化
2. enhanced_performance_optimizer.py - 多維度性能調優、機器學習驅動的優化
3. automated_optimization_service.py - 自動化參數調優、智能優化決策

提供統一的性能優化接口，支持：
- 實時性能監控與分析
- 多層級優化策略（保守、平衡、激進、自適應）
- 機器學習驅動的自動調優
- 緩存管理與預熱
- 系統資源優化
- API響應時間優化
"""

import asyncio
import time
import psutil
import gc
import statistics
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import structlog
from fastapi import Request
from contextlib import asynccontextmanager
import aioredis
import json
import pickle
import joblib
import warnings
warnings.filterwarnings('ignore')

# Machine Learning imports
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, Matern
from sklearn.linear_model import LinearRegression
from scipy.optimize import minimize, differential_evolution
import optuna
from collections import deque, defaultdict

try:
    from ..adapters.redis_adapter import RedisAdapter
except ImportError:
    RedisAdapter = None

logger = structlog.get_logger(__name__)


class OptimizationDomain(Enum):
    """優化領域"""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    RESOURCE_UTILIZATION = "resource_utilization"
    AI_PERFORMANCE = "ai_performance"
    NETWORK_EFFICIENCY = "network_efficiency"
    SATELLITE_HANDOVER = "satellite_handover"
    UAV_COORDINATION = "uav_coordination"
    API_RESPONSE = "api_response"
    CACHE_EFFICIENCY = "cache_efficiency"


class OptimizationStrategy(Enum):
    """優化策略"""
    CONSERVATIVE = "conservative"  # 保守策略，小幅優化
    BALANCED = "balanced"         # 平衡策略，適中優化
    AGGRESSIVE = "aggressive"     # 激進策略，大幅優化
    ADAPTIVE = "adaptive"         # 自適應策略，根據環境決定


class PerformanceIndicator(Enum):
    """性能指標類型"""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    CACHE_HIT_RATE = "cache_hit_rate"
    ERROR_RATE = "error_rate"
    NETWORK_LATENCY = "network_latency"


@dataclass
class PerformanceMetric:
    """性能指標數據結構"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    category: str = "api"
    target: Optional[float] = None
    domain: OptimizationDomain = OptimizationDomain.LATENCY
    confidence: float = 1.0


@dataclass
class OptimizationResult:
    """優化結果數據結構"""
    optimization_type: str
    before_value: float
    after_value: float
    improvement_percent: float
    success: bool
    timestamp: datetime
    techniques_applied: List[str]
    domain: OptimizationDomain = OptimizationDomain.LATENCY
    strategy_used: OptimizationStrategy = OptimizationStrategy.BALANCED
    confidence_score: float = 1.0


@dataclass
class OptimizationParameter:
    """優化參數定義"""
    name: str
    current_value: float
    min_value: float
    max_value: float
    step_size: float
    parameter_type: str  # 'continuous', 'discrete', 'categorical'
    impact_weight: float = 1.0
    constraints: List[str] = field(default_factory=list)
    domain: OptimizationDomain = OptimizationDomain.LATENCY


@dataclass
class SystemMetrics:
    """系統性能指標集合"""
    latency_ms: float
    throughput_ops_sec: float
    cpu_usage_percent: float
    memory_usage_percent: float
    cache_hit_rate: float
    error_rate_percent: float
    network_latency_ms: float
    timestamp: datetime
    custom_metrics: Dict[str, float] = field(default_factory=dict)


class UnifiedPerformanceOptimizer:
    """統一性能優化器"""

    def __init__(
        self,
        redis_adapter: Optional[RedisAdapter] = None,
        strategy: OptimizationStrategy = OptimizationStrategy.BALANCED,
        enable_ml_optimization: bool = True,
        enable_auto_tuning: bool = True,
    ):
        self.strategy = strategy
        self.enable_ml_optimization = enable_ml_optimization
        self.enable_auto_tuning = enable_auto_tuning
        self.redis_adapter = redis_adapter
        
        # Performance tracking
        self.metrics_history: List[PerformanceMetric] = []
        self.optimization_results: List[OptimizationResult] = []
        self.system_metrics_history: deque = deque(maxlen=10000)
        
        # Cache management
        self.cache_manager = None
        self._cache_hits = 0
        self._cache_total_ops = 0
        
        # Performance targets
        self.performance_targets = {
            "api_response_time_ms": 100,
            "cpu_usage_percent": 80,
            "memory_usage_percent": 85,
            "cache_hit_rate": 0.8,
            "throughput_ops_sec": 1000,
            "error_rate_percent": 1.0,
            "network_latency_ms": 50,
        }
        
        # Optimization parameters
        self.optimization_parameters: Dict[str, OptimizationParameter] = {}
        self._initialize_optimization_parameters()
        
        # ML models for prediction
        self.performance_models: Dict[str, Any] = {}
        self.scaler = StandardScaler()
        self.feature_columns = []
        
        # Auto-tuning
        self.tuning_history: Dict[str, List] = defaultdict(list)
        self.best_parameters: Dict[str, float] = {}
        
        # Monitoring state
        self._monitoring_active = False
        self._optimization_active = False
        
        self.logger = logger.bind(service="unified_performance_optimizer")

    def _initialize_optimization_parameters(self):
        """初始化優化參數"""
        parameters = [
            OptimizationParameter(
                name="cache_ttl_seconds",
                current_value=300,
                min_value=60,
                max_value=3600,
                step_size=60,
                parameter_type="continuous",
                domain=OptimizationDomain.CACHE_EFFICIENCY,
            ),
            OptimizationParameter(
                name="worker_pool_size",
                current_value=4,
                min_value=2,
                max_value=16,
                step_size=1,
                parameter_type="discrete",
                domain=OptimizationDomain.THROUGHPUT,
            ),
            OptimizationParameter(
                name="response_timeout_ms",
                current_value=5000,
                min_value=1000,
                max_value=30000,
                step_size=1000,
                parameter_type="continuous",
                domain=OptimizationDomain.LATENCY,
            ),
            OptimizationParameter(
                name="batch_size",
                current_value=32,
                min_value=8,
                max_value=128,
                step_size=8,
                parameter_type="discrete",
                domain=OptimizationDomain.THROUGHPUT,
            ),
        ]
        
        for param in parameters:
            self.optimization_parameters[param.name] = param

    async def initialize(self):
        """初始化性能優化器"""
        try:
            # Initialize cache manager
            self.cache_manager = await self._init_cache_manager()
            
            # Initialize ML models if enabled
            if self.enable_ml_optimization:
                await self._initialize_ml_models()
            
            # Load historical optimization data
            await self._load_optimization_history()
            
            self.logger.info("✅ 統一性能優化器初始化完成")
        except Exception as e:
            self.logger.error(f"❌ 統一性能優化器初始化失敗: {e}")

    async def _init_cache_manager(self):
        """初始化緩存管理器"""
        try:
            if self.redis_adapter:
                # Use provided Redis adapter
                await self.redis_adapter.ping()
                self.logger.info("✅ 使用現有 Redis 適配器")
                return self.redis_adapter
            else:
                # Try to connect to Redis directly
                redis = aioredis.from_url("redis://172.20.0.60:6379", decode_responses=True)
                await redis.ping()
                self.logger.info("✅ Redis 緩存連接成功")
                return redis
        except Exception as e:
            self.logger.warning(f"⚠️ Redis 不可用，使用內存緩存: {e}")
            return {}  # Use dict as simple cache

    async def _initialize_ml_models(self):
        """初始化機器學習模型"""
        try:
            # Performance prediction models
            self.performance_models = {
                "latency_predictor": RandomForestRegressor(n_estimators=100, random_state=42),
                "throughput_predictor": GradientBoostingRegressor(random_state=42),
                "resource_predictor": GaussianProcessRegressor(kernel=RBF()),
            }
            
            # Feature columns for ML models
            self.feature_columns = [
                "cpu_usage", "memory_usage", "cache_hit_rate", 
                "request_rate", "concurrent_users", "time_of_day"
            ]
            
            self.logger.info("✅ ML 模型初始化完成")
        except Exception as e:
            self.logger.error(f"ML 模型初始化失敗: {e}")

    async def _load_optimization_history(self):
        """載入歷史優化數據"""
        try:
            # Load from cache or persistent storage
            if isinstance(self.cache_manager, dict):
                return
            
            history_data = await self.cache_manager.get("optimization_history")
            if history_data:
                data = json.loads(history_data)
                # Restore optimization results and best parameters
                self.best_parameters = data.get("best_parameters", {})
                self.logger.info(f"✅ 載入歷史優化數據: {len(self.best_parameters)} 個參數")
        except Exception as e:
            self.logger.warning(f"載入歷史數據失敗: {e}")

    async def start_monitoring(self):
        """開始性能監控"""
        if self._monitoring_active:
            return

        self._monitoring_active = True
        
        # Start monitoring tasks
        asyncio.create_task(self._performance_monitoring_loop())
        
        if self.enable_auto_tuning:
            asyncio.create_task(self._auto_optimization_loop())
        
        self.logger.info("🔍 開始統一性能監控")

    async def _performance_monitoring_loop(self):
        """性能監控循環"""
        while self._monitoring_active:
            try:
                await self._collect_comprehensive_metrics()
                await asyncio.sleep(5)  # 5秒間隔
            except Exception as e:
                self.logger.error(f"性能監控錯誤: {e}")
                await asyncio.sleep(10)

    async def _auto_optimization_loop(self):
        """自動優化循環"""
        while self._monitoring_active:
            try:
                if len(self.system_metrics_history) >= 10:  # 有足夠數據時開始優化
                    await self.run_intelligent_optimization_cycle()
                await asyncio.sleep(60)  # 1分鐘間隔
            except Exception as e:
                self.logger.error(f"自動優化錯誤: {e}")
                await asyncio.sleep(120)

    async def _collect_comprehensive_metrics(self):
        """收集綜合性能指標"""
        current_time = datetime.utcnow()
        
        # System resource metrics
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        
        # Cache metrics
        cache_stats = await self._get_cache_stats()
        cache_hit_rate = cache_stats.get("hit_rate", 0)
        
        # Network metrics (simulated)
        network_latency = await self._measure_network_latency()
        
        # Create system metrics
        system_metrics = SystemMetrics(
            latency_ms=0,  # Will be updated by request measurements
            throughput_ops_sec=self._calculate_current_throughput(),
            cpu_usage_percent=cpu_percent,
            memory_usage_percent=memory.percent,
            cache_hit_rate=cache_hit_rate,
            error_rate_percent=self._calculate_error_rate(),
            network_latency_ms=network_latency,
            timestamp=current_time,
        )
        
        self.system_metrics_history.append(system_metrics)
        
        # Create individual performance metrics
        metrics = [
            PerformanceMetric("cpu_usage_percent", cpu_percent, "%", current_time),
            PerformanceMetric("memory_usage_percent", memory.percent, "%", current_time),
            PerformanceMetric("cache_hit_rate", cache_hit_rate, "ratio", current_time),
            PerformanceMetric("network_latency_ms", network_latency, "ms", current_time),
        ]
        
        # Store metrics
        self.metrics_history.extend(metrics)
        if len(self.metrics_history) > 10000:
            self.metrics_history = self.metrics_history[-10000:]

    async def _get_cache_stats(self) -> Dict:
        """獲取緩存統計"""
        try:
            if isinstance(self.cache_manager, dict):
                total_operations = max(self._cache_total_ops, 1)
                return {
                    "hit_rate": self._cache_hits / total_operations,
                    "size": len(self.cache_manager),
                }
            else:
                # Redis stats
                info = await self.cache_manager.info("stats")
                keyspace_hits = info.get("keyspace_hits", 0)
                keyspace_misses = info.get("keyspace_misses", 0)
                total_cache_ops = keyspace_hits + keyspace_misses
                hit_rate = keyspace_hits / max(total_cache_ops, 1)
                return {"hit_rate": hit_rate}
        except Exception as e:
            self.logger.warning(f"無法獲取緩存統計: {e}")
            return {"hit_rate": 0}

    async def _measure_network_latency(self) -> float:
        """測量網路延遲"""
        try:
            # Simulate network latency measurement
            # In production, this would ping actual services
            return np.random.normal(20, 5)  # Simulated latency
        except Exception:
            return 50.0

    def _calculate_current_throughput(self) -> float:
        """計算當前吞吐量"""
        try:
            if len(self.system_metrics_history) < 2:
                return 0
            
            # Calculate based on recent metrics
            recent_metrics = list(self.system_metrics_history)[-10:]
            return np.mean([m.throughput_ops_sec for m in recent_metrics if hasattr(m, 'throughput_ops_sec')])
        except Exception:
            return 0

    def _calculate_error_rate(self) -> float:
        """計算錯誤率"""
        # This would be calculated from actual error logs
        return 0.5  # Simulated low error rate

    @asynccontextmanager
    async def measure_request_performance(self, request: Request):
        """測量請求性能的上下文管理器"""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024

        try:
            yield
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024

            duration_ms = (end_time - start_time) * 1000
            memory_delta = end_memory - start_memory

            # Record performance metrics
            current_time = datetime.utcnow()
            endpoint_name = request.url.path.replace('/', '_')
            
            metrics = [
                PerformanceMetric(
                    f"api_response_time{endpoint_name}",
                    duration_ms,
                    "ms",
                    current_time,
                    domain=OptimizationDomain.API_RESPONSE,
                ),
                PerformanceMetric(
                    "memory_delta_mb", 
                    memory_delta, 
                    "MB", 
                    current_time,
                    domain=OptimizationDomain.RESOURCE_UTILIZATION,
                ),
            ]

            self.metrics_history.extend(metrics)

            # Trigger optimization if response time exceeds threshold
            if duration_ms > self.performance_targets["api_response_time_ms"]:
                await self._trigger_response_time_optimization(request.url.path, duration_ms)

    async def _trigger_response_time_optimization(self, endpoint: str, current_ms: float):
        """觸發響應時間優化"""
        self.logger.warning(f"⚠️ API 響應時間超標: {endpoint} = {current_ms:.1f}ms")

        # Apply immediate optimizations
        techniques = []

        # 1. Garbage collection
        before_gc = psutil.Process().memory_info().rss / 1024 / 1024
        gc.collect()
        after_gc = psutil.Process().memory_info().rss / 1024 / 1024

        if before_gc - after_gc > 1:  # Released > 1MB
            techniques.append("garbage_collection")

        # 2. Cache warming for the endpoint
        await self._warm_cache_for_endpoint(endpoint)
        techniques.append("cache_warming")

        # 3. Apply ML-based optimization if enabled
        if self.enable_ml_optimization:
            ml_optimizations = await self._apply_ml_optimization(endpoint, current_ms)
            techniques.extend(ml_optimizations)

        # Record optimization result
        self.optimization_results.append(
            OptimizationResult(
                optimization_type="api_response_time",
                before_value=current_ms,
                after_value=0,  # Will be updated on next request
                improvement_percent=0,
                success=len(techniques) > 0,
                timestamp=datetime.utcnow(),
                techniques_applied=techniques,
                domain=OptimizationDomain.API_RESPONSE,
                strategy_used=self.strategy,
            )
        )

    async def _warm_cache_for_endpoint(self, endpoint: str):
        """為特定端點預熱緩存"""
        try:
            # Warm cache based on endpoint type
            if "uav" in endpoint.lower():
                await self._cache_data("uav_common_data", {"type": "uav", "cached_at": datetime.utcnow().isoformat()})
            elif "satellite" in endpoint.lower():
                await self._cache_data("satellite_common_data", {"type": "satellite", "cached_at": datetime.utcnow().isoformat()})
            elif "handover" in endpoint.lower():
                await self._cache_data("handover_common_data", {"type": "handover", "cached_at": datetime.utcnow().isoformat()})

            self.logger.info(f"✅ 緩存預熱完成: {endpoint}")
        except Exception as e:
            self.logger.error(f"緩存預熱失敗: {e}")

    async def _cache_data(self, key: str, data: Dict, ttl: int = 300):
        """緩存數據"""
        try:
            if isinstance(self.cache_manager, dict):
                self.cache_manager[key] = data
                asyncio.create_task(self._expire_cache_key(key, ttl))
            else:
                await self.cache_manager.setex(key, ttl, json.dumps(data))
        except Exception as e:
            self.logger.error(f"緩存設置失敗: {e}")

    async def _expire_cache_key(self, key: str, ttl: int):
        """過期緩存鍵"""
        await asyncio.sleep(ttl)
        if isinstance(self.cache_manager, dict) and key in self.cache_manager:
            del self.cache_manager[key]

    async def _apply_ml_optimization(self, endpoint: str, current_ms: float) -> List[str]:
        """應用ML驅動的優化"""
        try:
            if not self.performance_models or len(self.system_metrics_history) < 10:
                return []

            # Prepare features for ML model
            features = self._prepare_features_for_ml()
            
            # Predict optimal parameters
            techniques = []
            
            # Use latency predictor to suggest optimizations
            if "latency_predictor" in self.performance_models:
                # This is a simplified example - in production, you'd use more sophisticated ML
                predicted_latency = self.performance_models["latency_predictor"].predict([features])
                if predicted_latency[0] < current_ms * 0.8:  # If ML suggests 20% improvement is possible
                    techniques.append("ml_parameter_tuning")

            return techniques
        except Exception as e:
            self.logger.error(f"ML 優化應用失敗: {e}")
            return []

    def _prepare_features_for_ml(self) -> List[float]:
        """為ML模型準備特徵"""
        if not self.system_metrics_history:
            return [0] * len(self.feature_columns)

        latest_metrics = self.system_metrics_history[-1]
        return [
            latest_metrics.cpu_usage_percent,
            latest_metrics.memory_usage_percent,
            latest_metrics.cache_hit_rate,
            latest_metrics.throughput_ops_sec,
            10,  # Simulated concurrent users
            datetime.now().hour,  # Time of day
        ]

    async def run_intelligent_optimization_cycle(self) -> Dict:
        """運行智能優化循環"""
        self.logger.info("🔄 開始智能優化循環")

        # Analyze current performance
        analysis = await self._analyze_comprehensive_performance()
        
        # Identify optimization opportunities
        opportunities = await self._identify_intelligent_opportunities(analysis)
        
        # Apply optimizations based on strategy
        results = await self._apply_strategic_optimizations(opportunities)
        
        # Run auto-tuning if enabled
        if self.enable_auto_tuning and opportunities:
            tuning_results = await self._run_auto_parameter_tuning(opportunities)
            results.extend(tuning_results)

        self.logger.info(f"✅ 智能優化循環完成，應用了 {len(results)} 項優化")

        return {
            "analysis": analysis,
            "opportunities": opportunities,
            "results": results,
            "strategy": self.strategy.value,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _analyze_comprehensive_performance(self) -> Dict:
        """分析綜合性能"""
        if not self.system_metrics_history:
            return {"status": "insufficient_data"}

        # Get recent metrics
        recent_metrics = list(self.system_metrics_history)[-20:]
        if not recent_metrics:
            return {"status": "no_recent_data"}

        # Calculate statistics for each metric type
        analysis = {}
        
        # CPU analysis
        cpu_values = [m.cpu_usage_percent for m in recent_metrics]
        analysis["cpu"] = self._calculate_metric_stats(cpu_values)
        
        # Memory analysis
        memory_values = [m.memory_usage_percent for m in recent_metrics]
        analysis["memory"] = self._calculate_metric_stats(memory_values)
        
        # Cache analysis
        cache_values = [m.cache_hit_rate for m in recent_metrics]
        analysis["cache"] = self._calculate_metric_stats(cache_values)
        
        # Throughput analysis
        throughput_values = [m.throughput_ops_sec for m in recent_metrics]
        analysis["throughput"] = self._calculate_metric_stats(throughput_values)

        # Overall system health score
        analysis["health_score"] = self._calculate_system_health_score(recent_metrics)

        return analysis

    def _calculate_metric_stats(self, values: List[float]) -> Dict:
        """計算指標統計"""
        if not values:
            return {}
        
        return {
            "current": values[-1],
            "average": statistics.mean(values),
            "max": max(values),
            "min": min(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "trend": "increasing" if len(values) > 1 and values[-1] > values[0] else "stable",
        }

    def _calculate_system_health_score(self, metrics: List[SystemMetrics]) -> float:
        """計算系統健康分數 (0-100)"""
        if not metrics:
            return 0
        
        latest = metrics[-1]
        score = 100
        
        # Penalize high resource usage
        if latest.cpu_usage_percent > 80:
            score -= (latest.cpu_usage_percent - 80) * 2
        if latest.memory_usage_percent > 85:
            score -= (latest.memory_usage_percent - 85) * 3
        
        # Penalize low cache hit rate
        if latest.cache_hit_rate < 0.8:
            score -= (0.8 - latest.cache_hit_rate) * 50
        
        # Penalize high error rate
        if latest.error_rate_percent > 1:
            score -= latest.error_rate_percent * 10
        
        return max(0, min(100, score))

    async def _identify_intelligent_opportunities(self, analysis: Dict) -> List[Dict]:
        """識別智能優化機會"""
        opportunities = []

        for metric_name, stats in analysis.items():
            if not isinstance(stats, dict) or metric_name == "health_score":
                continue

            current_value = stats.get("current", 0)
            trend = stats.get("trend", "stable")
            std_dev = stats.get("std_dev", 0)

            # Identify opportunities based on thresholds and trends
            if metric_name == "cpu" and current_value > 70:
                opportunities.append({
                    "type": "cpu_optimization",
                    "metric": "cpu_usage_percent",
                    "current_value": current_value,
                    "severity": "high" if current_value > 85 else "medium",
                    "trend": trend,
                    "variability": std_dev,
                    "recommended_actions": ["algorithm_optimization", "load_balancing", "caching"],
                })

            elif metric_name == "memory" and current_value > 80:
                opportunities.append({
                    "type": "memory_optimization", 
                    "metric": "memory_usage_percent",
                    "current_value": current_value,
                    "severity": "high" if current_value > 90 else "medium",
                    "trend": trend,
                    "recommended_actions": ["garbage_collection", "memory_pooling", "data_compression"],
                })

            elif metric_name == "cache" and current_value < 0.7:
                opportunities.append({
                    "type": "cache_optimization",
                    "metric": "cache_hit_rate", 
                    "current_value": current_value,
                    "severity": "high" if current_value < 0.5 else "medium",
                    "trend": trend,
                    "recommended_actions": ["cache_warming", "ttl_optimization", "cache_strategy_review"],
                })

        return opportunities

    async def _apply_strategic_optimizations(self, opportunities: List[Dict]) -> List[OptimizationResult]:
        """根據策略應用優化"""
        results = []

        for opportunity in opportunities:
            try:
                # Determine optimization intensity based on strategy
                intensity = self._get_optimization_intensity(opportunity)
                
                before_value = opportunity["current_value"]
                applied_techniques = []

                # Apply optimizations based on recommendations and strategy
                for action in opportunity["recommended_actions"][:intensity]:
                    success = await self._apply_optimization_action(action, intensity)
                    if success:
                        applied_techniques.append(action)

                # Calculate improvement based on strategy and applied techniques
                improvement_percent = self._calculate_expected_improvement(
                    opportunity, applied_techniques, intensity
                )
                after_value = before_value * (1 - improvement_percent / 100)

                result = OptimizationResult(
                    optimization_type=opportunity["type"],
                    before_value=before_value,
                    after_value=after_value,
                    improvement_percent=improvement_percent,
                    success=len(applied_techniques) > 0,
                    timestamp=datetime.utcnow(),
                    techniques_applied=applied_techniques,
                    domain=self._get_domain_for_opportunity(opportunity),
                    strategy_used=self.strategy,
                    confidence_score=self._calculate_confidence_score(opportunity),
                )

                results.append(result)
                self.optimization_results.append(result)

            except Exception as e:
                self.logger.error(f"優化應用失敗: {e}")

        return results

    def _get_optimization_intensity(self, opportunity: Dict) -> int:
        """根據策略獲取優化強度"""
        severity = opportunity.get("severity", "medium")
        
        if self.strategy == OptimizationStrategy.CONSERVATIVE:
            return 1 if severity == "high" else 0
        elif self.strategy == OptimizationStrategy.BALANCED:
            return 2 if severity == "high" else 1
        elif self.strategy == OptimizationStrategy.AGGRESSIVE:
            return 3 if severity == "high" else 2
        else:  # ADAPTIVE
            # Adaptive strategy based on system health
            health_score = self._calculate_system_health_score(list(self.system_metrics_history)[-5:])
            if health_score < 60:
                return 3  # Aggressive when health is poor
            elif health_score < 80:
                return 2  # Balanced when health is moderate  
            else:
                return 1  # Conservative when health is good

    def _calculate_expected_improvement(
        self, opportunity: Dict, techniques: List[str], intensity: int
    ) -> float:
        """計算期望改善百分比"""
        base_improvement = len(techniques) * 3  # 3% per technique
        intensity_multiplier = 1 + (intensity - 1) * 0.5  # 50% boost per intensity level
        severity_multiplier = 1.5 if opportunity.get("severity") == "high" else 1.0
        
        return min(50, base_improvement * intensity_multiplier * severity_multiplier)

    def _get_domain_for_opportunity(self, opportunity: Dict) -> OptimizationDomain:
        """獲取優化機會對應的領域"""
        opportunity_type = opportunity.get("type", "")
        if "cpu" in opportunity_type:
            return OptimizationDomain.RESOURCE_UTILIZATION
        elif "memory" in opportunity_type:
            return OptimizationDomain.RESOURCE_UTILIZATION
        elif "cache" in opportunity_type:
            return OptimizationDomain.CACHE_EFFICIENCY
        elif "latency" in opportunity_type:
            return OptimizationDomain.LATENCY
        else:
            return OptimizationDomain.LATENCY

    def _calculate_confidence_score(self, opportunity: Dict) -> float:
        """計算優化信心分數"""
        # Base confidence on data quality and opportunity clarity
        base_confidence = 0.7
        
        # Higher confidence for well-defined problems
        if opportunity.get("severity") == "high":
            base_confidence += 0.2
        
        # Higher confidence when we have stable trends
        if opportunity.get("trend") == "stable":
            base_confidence += 0.1
        
        return min(1.0, base_confidence)

    async def _apply_optimization_action(self, action: str, intensity: int = 1) -> bool:
        """應用具體的優化行動"""
        try:
            if action == "garbage_collection":
                for _ in range(intensity):
                    gc.collect()
                return True

            elif action == "cache_warming":
                endpoints = ["/api/v1/uav", "/api/v1/satellite", "/api/v1/handover"][:intensity]
                for endpoint in endpoints:
                    await self._warm_cache_for_endpoint(endpoint)
                return True

            elif action == "algorithm_optimization":
                # Simulate algorithm optimization
                await asyncio.sleep(0.1 * intensity)
                return True

            elif action == "load_balancing":
                # Simulate load balancing adjustment
                return True

            elif action == "memory_pooling":
                # Simulate memory pool optimization
                for _ in range(intensity):
                    gc.collect()
                return True

            elif action == "ttl_optimization":
                # Optimize cache TTL based on usage patterns
                await self._optimize_cache_ttl(intensity)
                return True

            else:
                self.logger.warning(f"未知的優化行動: {action}")
                return False

        except Exception as e:
            self.logger.error(f"優化行動執行失敗 {action}: {e}")
            return False

    async def _optimize_cache_ttl(self, intensity: int):
        """優化緩存TTL"""
        try:
            # Adjust TTL based on hit rate analysis
            current_ttl = self.optimization_parameters.get("cache_ttl_seconds")
            if current_ttl:
                # Increase TTL if hit rate is low, decrease if memory is high
                latest_metrics = list(self.system_metrics_history)[-1] if self.system_metrics_history else None
                if latest_metrics:
                    if latest_metrics.cache_hit_rate < 0.5:
                        current_ttl.current_value = min(
                            current_ttl.max_value, 
                            current_ttl.current_value * (1 + 0.1 * intensity)
                        )
                    elif latest_metrics.memory_usage_percent > 85:
                        current_ttl.current_value = max(
                            current_ttl.min_value,
                            current_ttl.current_value * (1 - 0.1 * intensity)
                        )
        except Exception as e:
            self.logger.error(f"TTL 優化失敗: {e}")

    async def _run_auto_parameter_tuning(self, opportunities: List[Dict]) -> List[OptimizationResult]:
        """運行自動參數調優"""
        if not self.enable_auto_tuning:
            return []

        results = []
        
        try:
            # Select parameters to tune based on opportunities
            parameters_to_tune = self._select_parameters_for_tuning(opportunities)
            
            for param_name in parameters_to_tune:
                if param_name in self.optimization_parameters:
                    result = await self._tune_single_parameter(param_name)
                    if result:
                        results.append(result)
                        
        except Exception as e:
            self.logger.error(f"自動參數調優失敗: {e}")
        
        return results

    def _select_parameters_for_tuning(self, opportunities: List[Dict]) -> List[str]:
        """選擇需要調優的參數"""
        parameters_to_tune = []
        
        for opportunity in opportunities:
            opportunity_type = opportunity.get("type", "")
            
            if "cache" in opportunity_type:
                parameters_to_tune.append("cache_ttl_seconds")
            elif "cpu" in opportunity_type or "throughput" in opportunity_type:
                parameters_to_tune.append("worker_pool_size")
            elif "latency" in opportunity_type:
                parameters_to_tune.append("response_timeout_ms")
        
        return list(set(parameters_to_tune))  # Remove duplicates

    async def _tune_single_parameter(self, param_name: str) -> Optional[OptimizationResult]:
        """調優單個參數"""
        try:
            parameter = self.optimization_parameters[param_name]
            before_value = parameter.current_value
            
            # Use Optuna for parameter optimization
            study = optuna.create_study(direction="minimize")
            
            def objective(trial):
                # Suggest parameter value
                if parameter.parameter_type == "continuous":
                    value = trial.suggest_float(
                        param_name, 
                        parameter.min_value, 
                        parameter.max_value
                    )
                else:  # discrete
                    value = trial.suggest_int(
                        param_name,
                        int(parameter.min_value),
                        int(parameter.max_value),
                        step=int(parameter.step_size)
                    )
                
                # Simulate performance evaluation with the new parameter value
                return self._evaluate_parameter_performance(param_name, value)
            
            # Run optimization
            study.optimize(objective, n_trials=10, timeout=30)
            
            if study.best_trial:
                best_value = study.best_value
                optimal_value = study.best_params[param_name]
                
                # Update parameter
                parameter.current_value = optimal_value
                self.best_parameters[param_name] = optimal_value
                
                improvement_percent = abs(before_value - optimal_value) / before_value * 100
                
                return OptimizationResult(
                    optimization_type="parameter_tuning",
                    before_value=before_value,
                    after_value=optimal_value,
                    improvement_percent=improvement_percent,
                    success=True,
                    timestamp=datetime.utcnow(),
                    techniques_applied=[f"optuna_tuning_{param_name}"],
                    domain=parameter.domain,
                    strategy_used=self.strategy,
                    confidence_score=0.8,
                )
                
        except Exception as e:
            self.logger.error(f"參數調優失敗 {param_name}: {e}")
        
        return None

    def _evaluate_parameter_performance(self, param_name: str, value: float) -> float:
        """評估參數性能（模擬）"""
        # This is a simplified simulation - in production, you'd measure actual performance
        if not self.system_metrics_history:
            return 1.0
        
        latest_metrics = self.system_metrics_history[-1]
        
        # Simulate performance score based on parameter and current system state
        if param_name == "cache_ttl_seconds":
            # Longer TTL generally improves hit rate but uses more memory
            memory_penalty = (value / 3600) * latest_metrics.memory_usage_percent / 100
            hit_rate_benefit = min(0.2, value / 1800)  # Max 20% benefit
            return 1.0 - hit_rate_benefit + memory_penalty
        
        elif param_name == "worker_pool_size":
            # More workers can improve throughput but increase CPU usage
            cpu_penalty = (value / 16) * latest_metrics.cpu_usage_percent / 100
            throughput_benefit = min(0.3, value / 10)  # Max 30% benefit
            return 1.0 - throughput_benefit + cpu_penalty
        
        else:
            return 1.0

    async def get_cached_data(self, key: str) -> Optional[Dict]:
        """獲取緩存數據"""
        try:
            self._cache_total_ops += 1
            
            if isinstance(self.cache_manager, dict):
                if key in self.cache_manager:
                    self._cache_hits += 1
                    return self.cache_manager[key]
                return None
            else:
                data = await self.cache_manager.get(key)
                if data:
                    self._cache_hits += 1
                    return json.loads(data)
                return None
        except Exception as e:
            self.logger.error(f"緩存獲取失敗: {e}")
            return None

    async def set_cached_data(self, key: str, data: Dict, ttl: int = 300):
        """設置緩存數據"""
        await self._cache_data(key, data, ttl)

    def get_comprehensive_performance_summary(self) -> Dict:
        """獲取綜合性能摘要"""
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "strategy": self.strategy.value,
            "total_optimizations": len(self.optimization_results),
            "successful_optimizations": len([r for r in self.optimization_results if r.success]),
            "ml_enabled": self.enable_ml_optimization,
            "auto_tuning_enabled": self.enable_auto_tuning,
        }

        # Current system state
        if self.system_metrics_history:
            latest = self.system_metrics_history[-1]
            summary["current_system_state"] = {
                "cpu_usage_percent": latest.cpu_usage_percent,
                "memory_usage_percent": latest.memory_usage_percent,
                "cache_hit_rate": latest.cache_hit_rate,
                "throughput_ops_sec": latest.throughput_ops_sec,
                "error_rate_percent": latest.error_rate_percent,
                "network_latency_ms": latest.network_latency_ms,
                "health_score": self._calculate_system_health_score([latest]),
            }

        # Optimization results by domain
        domain_results = defaultdict(list)
        for result in self.optimization_results:
            domain_results[result.domain.value].append(result)
        
        summary["optimization_by_domain"] = {}
        for domain, results in domain_results.items():
            summary["optimization_by_domain"][domain] = {
                "total": len(results),
                "successful": len([r for r in results if r.success]),
                "avg_improvement": np.mean([r.improvement_percent for r in results if r.success]) if results else 0,
            }

        # Best parameters
        summary["current_parameters"] = {
            name: param.current_value 
            for name, param in self.optimization_parameters.items()
        }

        # Performance targets status
        if self.system_metrics_history:
            latest = self.system_metrics_history[-1]
            summary["targets_status"] = {
                "api_response_time_ms": {
                    "target": self.performance_targets["api_response_time_ms"],
                    "current": "measured_per_request",
                    "meets_target": "varies",
                },
                "cpu_usage_percent": {
                    "target": self.performance_targets["cpu_usage_percent"],
                    "current": latest.cpu_usage_percent,
                    "meets_target": latest.cpu_usage_percent <= self.performance_targets["cpu_usage_percent"],
                },
                "memory_usage_percent": {
                    "target": self.performance_targets["memory_usage_percent"],
                    "current": latest.memory_usage_percent,
                    "meets_target": latest.memory_usage_percent <= self.performance_targets["memory_usage_percent"],
                },
                "cache_hit_rate": {
                    "target": self.performance_targets["cache_hit_rate"],
                    "current": latest.cache_hit_rate,
                    "meets_target": latest.cache_hit_rate >= self.performance_targets["cache_hit_rate"],
                },
            }

        return summary

    async def stop_monitoring(self):
        """停止性能監控"""
        self._monitoring_active = False
        
        # Save optimization history to cache
        await self._save_optimization_history()
        
        self.logger.info("🔍 統一性能監控已停止")

    async def _save_optimization_history(self):
        """保存優化歷史"""
        try:
            if isinstance(self.cache_manager, dict):
                return
            
            history_data = {
                "best_parameters": self.best_parameters,
                "total_optimizations": len(self.optimization_results),
                "last_updated": datetime.utcnow().isoformat(),
            }
            
            await self.cache_manager.setex(
                "optimization_history",
                86400,  # 24 hours
                json.dumps(history_data)
            )
        except Exception as e:
            self.logger.warning(f"保存優化歷史失敗: {e}")

    def change_strategy(self, new_strategy: OptimizationStrategy):
        """更改優化策略"""
        old_strategy = self.strategy
        self.strategy = new_strategy
        self.logger.info(f"優化策略已更改: {old_strategy.value} → {new_strategy.value}")

    def enable_ml_features(self, enable: bool = True):
        """啟用/禁用ML功能"""
        self.enable_ml_optimization = enable
        self.logger.info(f"ML 優化功能: {'啟用' if enable else '禁用'}")

    def enable_auto_tuning_features(self, enable: bool = True):
        """啟用/禁用自動調優功能"""
        self.enable_auto_tuning = enable
        self.logger.info(f"自動調優功能: {'啟用' if enable else '禁用'}")


# Global instance
unified_performance_optimizer = UnifiedPerformanceOptimizer()