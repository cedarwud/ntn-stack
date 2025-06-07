"""
自動化調優服務

階段八：機器學習驅動的系統參數自動調優機制
實現基於歷史性能數據的智能參數調優和系統優化
"""

import asyncio
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
import structlog
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, Matern
from scipy.optimize import minimize, differential_evolution
from dataclasses import dataclass, field
import optuna
from collections import deque, defaultdict
import pickle
import joblib
import warnings
warnings.filterwarnings('ignore')

from ..adapters.redis_adapter import RedisAdapter

logger = structlog.get_logger(__name__)

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

@dataclass
class PerformanceMetrics:
    """性能指標"""
    latency_ms: float
    throughput_mbps: float
    packet_loss_rate: float
    cpu_utilization: float
    memory_utilization: float
    power_consumption_w: float
    sinr_db: float
    coverage_percentage: float
    cost_per_hour: float
    user_satisfaction_score: float
    timestamp: datetime

@dataclass
class OptimizationResult:
    """優化結果"""
    parameter_changes: Dict[str, Dict]
    expected_improvements: Dict[str, float]
    confidence_score: float
    estimated_implementation_time: float
    rollback_plan: Dict
    validation_metrics: Dict

class BayesianOptimizer:
    """貝葉斯優化器"""
    
    def __init__(self, parameters: List[OptimizationParameter]):
        self.parameters = parameters
        self.parameter_bounds = {}
        self.observation_history = []
        self.gp_model = None
        self.acquisition_function = 'expected_improvement'
        
        # 設置參數邊界
        for param in parameters:
            self.parameter_bounds[param.name] = (param.min_value, param.max_value)
    
    def suggest_parameters(self, n_suggestions: int = 1) -> List[Dict]:
        """建議參數配置"""
        if len(self.observation_history) < 5:
            # 初期使用隨機採樣
            return self._random_sampling(n_suggestions)
        else:
            # 使用貝葉斯優化
            return self._bayesian_sampling(n_suggestions)
    
    def _random_sampling(self, n_suggestions: int) -> List[Dict]:
        """隨機採樣"""
        suggestions = []
        for _ in range(n_suggestions):
            suggestion = {}
            for param in self.parameters:
                if param.parameter_type == 'continuous':
                    value = np.random.uniform(param.min_value, param.max_value)
                elif param.parameter_type == 'discrete':
                    value = np.random.choice(
                        np.arange(param.min_value, param.max_value + 1, param.step_size)
                    )
                else:  # categorical
                    value = param.current_value  # 暫時使用當前值
                
                suggestion[param.name] = value
            suggestions.append(suggestion)
        
        return suggestions
    
    def _bayesian_sampling(self, n_suggestions: int) -> List[Dict]:
        """貝葉斯採樣"""
        if self.gp_model is None:
            self._train_gp_model()
        
        suggestions = []
        for _ in range(n_suggestions):
            # 使用期望改進作為獲取函數
            best_params = self._optimize_acquisition_function()
            suggestions.append(best_params)
        
        return suggestions
    
    def _train_gp_model(self):
        """訓練高斯過程模型"""
        if len(self.observation_history) < 3:
            return
        
        X = []
        y = []
        
        for obs in self.observation_history:
            param_vector = [obs['parameters'][param.name] for param in self.parameters]
            performance_score = obs['performance_score']
            X.append(param_vector)
            y.append(performance_score)
        
        X = np.array(X)
        y = np.array(y)
        
        # 使用RBF核的高斯過程
        kernel = RBF(length_scale=1.0)
        self.gp_model = GaussianProcessRegressor(
            kernel=kernel,
            alpha=1e-6,
            n_restarts_optimizer=10,
            random_state=42
        )
        
        self.gp_model.fit(X, y)
    
    def _optimize_acquisition_function(self) -> Dict:
        """優化獲取函數"""
        bounds = [self.parameter_bounds[param.name] for param in self.parameters]
        
        def acquisition(x):
            # 期望改進獲取函數
            x = x.reshape(1, -1)
            mu, sigma = self.gp_model.predict(x, return_std=True)
            
            if len(self.observation_history) > 0:
                f_best = max([obs['performance_score'] for obs in self.observation_history])
            else:
                f_best = 0
            
            with np.errstate(divide='warn'):
                improvement = mu - f_best
                Z = improvement / sigma
                ei = improvement * self._normal_cdf(Z) + sigma * self._normal_pdf(Z)
                return -ei[0]  # 最小化負期望改進
        
        # 使用差分進化優化
        result = differential_evolution(acquisition, bounds, seed=42, maxiter=100)
        
        # 將結果轉換為參數字典
        best_params = {}
        for i, param in enumerate(self.parameters):
            best_params[param.name] = result.x[i]
        
        return best_params
    
    def _normal_cdf(self, x):
        """標準正態分布累積密度函數"""
        return 0.5 * (1 + np.sign(x) * np.sqrt(1 - np.exp(-2 * x**2 / np.pi)))
    
    def _normal_pdf(self, x):
        """標準正態分布概率密度函數"""
        return np.exp(-0.5 * x**2) / np.sqrt(2 * np.pi)
    
    def add_observation(self, parameters: Dict, performance_score: float):
        """添加觀察結果"""
        observation = {
            'parameters': parameters,
            'performance_score': performance_score,
            'timestamp': datetime.utcnow()
        }
        self.observation_history.append(observation)
        
        # 保持歷史記錄在合理範圍內
        if len(self.observation_history) > 200:
            self.observation_history = self.observation_history[-200:]

class MLOptimizationEngine:
    """機器學習優化引擎"""
    
    def __init__(self):
        self.models = {
            'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'gradient_boosting': GradientBoostingRegressor(n_estimators=100, random_state=42),
            'gaussian_process': GaussianProcessRegressor(random_state=42)
        }
        self.best_model = None
        self.scaler = RobustScaler()
        self.feature_importance = None
        self.is_trained = False
        
    def train_models(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """訓練多個模型並選擇最佳模型"""
        if X.shape[0] < 10:
            return {'error': '訓練數據不足'}
        
        # 數據預處理
        X_scaled = self.scaler.fit_transform(X)
        
        # 分割數據
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        model_scores = {}
        
        # 訓練和評估每個模型
        for name, model in self.models.items():
            try:
                # 交叉驗證
                cv_scores = cross_val_score(model, X_train, y_train, cv=5)
                
                # 訓練模型
                model.fit(X_train, y_train)
                
                # 測試集評估
                y_pred = model.predict(X_test)
                test_score = r2_score(y_test, y_pred)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                mae = mean_absolute_error(y_test, y_pred)
                
                model_scores[name] = {
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std(),
                    'test_r2': test_score,
                    'rmse': rmse,
                    'mae': mae
                }
                
            except Exception as e:
                logger.warning(f"模型 {name} 訓練失敗", error=str(e))
                model_scores[name] = {'error': str(e)}
        
        # 選擇最佳模型
        best_model_name = max(
            [name for name, score in model_scores.items() if 'error' not in score],
            key=lambda x: model_scores[x]['test_r2'],
            default=None
        )
        
        if best_model_name:
            self.best_model = self.models[best_model_name]
            self.is_trained = True
            
            # 計算特徵重要性
            if hasattr(self.best_model, 'feature_importances_'):
                self.feature_importance = self.best_model.feature_importances_
        
        return {
            'best_model': best_model_name,
            'model_scores': model_scores,
            'is_trained': self.is_trained
        }
    
    def predict_performance(self, parameters: np.ndarray) -> Tuple[float, float]:
        """預測性能（返回均值和標準差）"""
        if not self.is_trained or self.best_model is None:
            return 0.5, 0.5
        
        parameters_scaled = self.scaler.transform(parameters.reshape(1, -1))
        
        if hasattr(self.best_model, 'predict') and hasattr(self.best_model, 'predict_std'):
            # 高斯過程回歸可以返回不確定性
            mean, std = self.best_model.predict(parameters_scaled, return_std=True)
            return float(mean[0]), float(std[0])
        else:
            # 其他模型只返回點估計
            prediction = self.best_model.predict(parameters_scaled)
            return float(prediction[0]), 0.1  # 假設標準差
    
    def get_feature_importance(self) -> Optional[np.ndarray]:
        """獲取特徵重要性"""
        return self.feature_importance

class AutomatedOptimizationService:
    """自動化調優服務"""
    
    def __init__(
        self,
        redis_adapter: RedisAdapter,
        optimization_interval_minutes: int = 30,
        model_save_path: str = "/tmp/optimization_models"
    ):
        self.logger = logger.bind(service="automated_optimization")
        self.redis_adapter = redis_adapter
        self.optimization_interval = timedelta(minutes=optimization_interval_minutes)
        self.model_save_path = Path(model_save_path)
        self.model_save_path.mkdir(parents=True, exist_ok=True)
        
        # 優化參數定義
        self.optimization_parameters = self._initialize_optimization_parameters()
        
        # 優化引擎
        self.bayesian_optimizer = BayesianOptimizer(self.optimization_parameters)
        self.ml_engine = MLOptimizationEngine()
        
        # 歷史數據
        self.performance_history = deque(maxlen=1000)
        self.optimization_history = deque(maxlen=200)
        
        # 優化狀態
        self.is_optimization_running = False
        self.last_optimization_time = None
        self.current_optimization_cycle = 0
        
        # 載入已保存的模型和數據
        self._load_saved_data()
    
    def _initialize_optimization_parameters(self) -> List[OptimizationParameter]:
        """初始化優化參數"""
        return [
            # 5G 核心網參數
            OptimizationParameter(
                name="amf_max_sessions",
                current_value=1000,
                min_value=100,
                max_value=5000,
                step_size=100,
                parameter_type="discrete",
                impact_weight=0.8
            ),
            OptimizationParameter(
                name="smf_session_timeout_seconds",
                current_value=300,
                min_value=60,
                max_value=1800,
                step_size=30,
                parameter_type="discrete",
                impact_weight=0.6
            ),
            OptimizationParameter(
                name="upf_buffer_size_mb",
                current_value=128,
                min_value=32,
                max_value=512,
                step_size=16,
                parameter_type="discrete",
                impact_weight=0.9
            ),
            
            # gNodeB 參數
            OptimizationParameter(
                name="gnb_tx_power_dbm",
                current_value=23,
                min_value=10,
                max_value=30,
                step_size=1,
                parameter_type="discrete",
                impact_weight=1.0
            ),
            OptimizationParameter(
                name="gnb_bandwidth_mhz",
                current_value=20,
                min_value=5,
                max_value=100,
                step_size=5,
                parameter_type="discrete",
                impact_weight=0.9
            ),
            OptimizationParameter(
                name="gnb_antenna_gain_db",
                current_value=15,
                min_value=0,
                max_value=25,
                step_size=1,
                parameter_type="discrete",
                impact_weight=0.7
            ),
            
            # UE 參數
            OptimizationParameter(
                name="ue_max_bitrate_mbps",
                current_value=100,
                min_value=10,
                max_value=1000,
                step_size=10,
                parameter_type="discrete",
                impact_weight=0.8
            ),
            OptimizationParameter(
                name="ue_handover_threshold_db",
                current_value=-100,
                min_value=-120,
                max_value=-80,
                step_size=2,
                parameter_type="discrete",
                impact_weight=0.6
            ),
            
            # 衛星特定參數
            OptimizationParameter(
                name="satellite_elevation_threshold_deg",
                current_value=10,
                min_value=5,
                max_value=30,
                step_size=1,
                parameter_type="discrete",
                impact_weight=0.9
            ),
            OptimizationParameter(
                name="satellite_handover_margin_db",
                current_value=3,
                min_value=1,
                max_value=10,
                step_size=0.5,
                parameter_type="continuous",
                impact_weight=0.7
            ),
            
            # AI-RAN 參數
            OptimizationParameter(
                name="airan_learning_rate",
                current_value=0.001,
                min_value=0.0001,
                max_value=0.01,
                step_size=0.0001,
                parameter_type="continuous",
                impact_weight=0.5
            ),
            OptimizationParameter(
                name="airan_epsilon",
                current_value=0.1,
                min_value=0.01,
                max_value=0.5,
                step_size=0.01,
                parameter_type="continuous",
                impact_weight=0.4
            )
        ]
    
    async def start_continuous_optimization(self):
        """啟動持續優化"""
        self.logger.info("啟動自動化持續優化")
        
        while True:
            try:
                # 檢查是否需要執行優化
                if self._should_run_optimization():
                    await self.run_optimization_cycle()
                
                # 等待下一個檢查週期
                await asyncio.sleep(60)  # 每分鐘檢查一次
                
            except Exception as e:
                self.logger.error("持續優化過程中發生錯誤", error=str(e))
                await asyncio.sleep(300)  # 發生錯誤時等待5分鐘
    
    def _should_run_optimization(self) -> bool:
        """檢查是否應該運行優化"""
        if self.is_optimization_running:
            return False
        
        if self.last_optimization_time is None:
            return True
        
        time_since_last = datetime.utcnow() - self.last_optimization_time
        return time_since_last >= self.optimization_interval
    
    async def run_optimization_cycle(self) -> Dict:
        """運行優化週期"""
        try:
            self.is_optimization_running = True
            self.current_optimization_cycle += 1
            cycle_start_time = datetime.utcnow()
            
            self.logger.info("開始優化週期", cycle=self.current_optimization_cycle)
            
            # 1. 收集當前性能數據
            current_metrics = await self._collect_current_metrics()
            
            # 2. 更新機器學習模型
            if len(self.performance_history) >= 20:
                model_update_result = await self._update_ml_models()
            else:
                model_update_result = {'status': 'insufficient_data'}
            
            # 3. 生成優化建議
            optimization_suggestions = await self._generate_optimization_suggestions(current_metrics)
            
            # 4. 評估和選擇最佳建議
            best_suggestion = await self._select_best_suggestion(optimization_suggestions, current_metrics)
            
            # 5. 實施優化（如果有可行的建議）
            implementation_result = None
            if best_suggestion and best_suggestion.get('confidence_score', 0) > 0.6:
                implementation_result = await self._implement_optimization(best_suggestion)
            
            # 6. 記錄優化結果
            optimization_record = {
                'cycle': self.current_optimization_cycle,
                'start_time': cycle_start_time.isoformat(),
                'end_time': datetime.utcnow().isoformat(),
                'current_metrics': current_metrics,
                'model_update': model_update_result,
                'suggestions_count': len(optimization_suggestions),
                'best_suggestion': best_suggestion,
                'implementation_result': implementation_result,
                'duration_seconds': (datetime.utcnow() - cycle_start_time).total_seconds()
            }
            
            self.optimization_history.append(optimization_record)
            self.last_optimization_time = datetime.utcnow()
            
            # 7. 保存數據和模型
            await self._save_optimization_data()
            
            return {
                'success': True,
                'optimization_cycle': self.current_optimization_cycle,
                'optimization_record': optimization_record
            }
        
        except Exception as e:
            self.logger.error("優化週期執行失敗", error=str(e))
            return {'success': False, 'error': str(e)}
        
        finally:
            self.is_optimization_running = False
    
    async def _collect_current_metrics(self) -> PerformanceMetrics:
        """收集當前性能指標"""
        try:
            # 從 Redis 獲取實時指標
            metrics_data = await self.redis_adapter.get("system_metrics:latest")
            
            if metrics_data:
                data = json.loads(metrics_data)
            else:
                # 使用預設值或模擬數據
                data = {
                    'latency_ms': 45.0,
                    'throughput_mbps': 75.0,
                    'packet_loss_rate': 0.02,
                    'cpu_utilization': 65.0,
                    'memory_utilization': 70.0,
                    'power_consumption_w': 120.0,
                    'sinr_db': 18.0,
                    'coverage_percentage': 82.0,
                    'cost_per_hour': 15.0,
                    'user_satisfaction_score': 8.2
                }
            
            metrics = PerformanceMetrics(
                latency_ms=data.get('latency_ms', 50.0),
                throughput_mbps=data.get('throughput_mbps', 50.0),
                packet_loss_rate=data.get('packet_loss_rate', 0.01),
                cpu_utilization=data.get('cpu_utilization', 60.0),
                memory_utilization=data.get('memory_utilization', 65.0),
                power_consumption_w=data.get('power_consumption_w', 100.0),
                sinr_db=data.get('sinr_db', 15.0),
                coverage_percentage=data.get('coverage_percentage', 80.0),
                cost_per_hour=data.get('cost_per_hour', 10.0),
                user_satisfaction_score=data.get('user_satisfaction_score', 8.0),
                timestamp=datetime.utcnow()
            )
            
            # 添加到歷史記錄
            self.performance_history.append(metrics)
            
            return metrics
        
        except Exception as e:
            self.logger.error("收集性能指標失敗", error=str(e))
            # 返回預設指標
            return PerformanceMetrics(
                latency_ms=50.0,
                throughput_mbps=50.0,
                packet_loss_rate=0.01,
                cpu_utilization=60.0,
                memory_utilization=65.0,
                power_consumption_w=100.0,
                sinr_db=15.0,
                coverage_percentage=80.0,
                cost_per_hour=10.0,
                user_satisfaction_score=8.0,
                timestamp=datetime.utcnow()
            )
    
    async def _update_ml_models(self) -> Dict:
        """更新機器學習模型"""
        try:
            if len(self.performance_history) < 20:
                return {'status': 'insufficient_data'}
            
            # 準備訓練數據
            X, y = self._prepare_training_data()
            
            if X.shape[0] < 10:
                return {'status': 'insufficient_training_samples'}
            
            # 訓練模型
            training_result = self.ml_engine.train_models(X, y)
            
            # 更新貝葉斯優化器
            for i, metrics in enumerate(list(self.performance_history)[-50:]):
                params = self._extract_current_parameters()
                performance_score = self._calculate_performance_score(metrics)
                self.bayesian_optimizer.add_observation(params, performance_score)
            
            return {
                'status': 'success',
                'training_result': training_result,
                'training_samples': X.shape[0]
            }
        
        except Exception as e:
            self.logger.error("更新機器學習模型失敗", error=str(e))
            return {'status': 'error', 'error': str(e)}
    
    def _prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """準備訓練數據"""
        features = []
        targets = []
        
        # 使用最近的性能歷史
        for metrics in list(self.performance_history)[-100:]:
            # 特徵向量（當前參數值）
            current_params = self._extract_current_parameters()
            feature_vector = [current_params[param.name] for param in self.optimization_parameters]
            
            # 目標值（性能分數）
            performance_score = self._calculate_performance_score(metrics)
            
            features.append(feature_vector)
            targets.append(performance_score)
        
        return np.array(features), np.array(targets)
    
    def _extract_current_parameters(self) -> Dict:
        """提取當前參數值"""
        # 這裡應該從實際的系統配置中提取參數值
        # 現在使用預設值
        current_params = {}
        for param in self.optimization_parameters:
            current_params[param.name] = param.current_value
        
        return current_params
    
    def _calculate_performance_score(self, metrics: PerformanceMetrics) -> float:
        """計算性能分數"""
        # 多維度性能評分（0-1）
        latency_score = max(0, 1 - metrics.latency_ms / 100.0)  # 延遲越低越好
        throughput_score = min(1, metrics.throughput_mbps / 100.0)  # 吞吐量越高越好
        reliability_score = 1 - metrics.packet_loss_rate  # 封包損失率越低越好
        efficiency_score = 1 - metrics.cpu_utilization / 100.0  # CPU使用率適中
        coverage_score = metrics.coverage_percentage / 100.0  # 覆蓋率越高越好
        quality_score = min(1, metrics.sinr_db / 30.0)  # SINR越高越好
        satisfaction_score = metrics.user_satisfaction_score / 10.0  # 用戶滿意度
        
        # 加權平均
        weights = [0.2, 0.2, 0.15, 0.1, 0.15, 0.1, 0.1]
        scores = [latency_score, throughput_score, reliability_score, 
                 efficiency_score, coverage_score, quality_score, satisfaction_score]
        
        return np.average(scores, weights=weights)
    
    async def _generate_optimization_suggestions(self, current_metrics: PerformanceMetrics) -> List[Dict]:
        """生成優化建議"""
        suggestions = []
        
        try:
            # 1. 貝葉斯優化建議
            bayesian_suggestions = self.bayesian_optimizer.suggest_parameters(3)
            
            for i, params in enumerate(bayesian_suggestions):
                suggestion = await self._evaluate_parameter_suggestion(params, current_metrics)
                suggestion['method'] = 'bayesian_optimization'
                suggestion['suggestion_id'] = f'bayesian_{i}'
                suggestions.append(suggestion)
            
            # 2. 基於ML模型的建議
            if self.ml_engine.is_trained:
                ml_suggestions = await self._generate_ml_based_suggestions(current_metrics)
                suggestions.extend(ml_suggestions)
            
            # 3. 基於規則的建議
            rule_based_suggestions = await self._generate_rule_based_suggestions(current_metrics)
            suggestions.extend(rule_based_suggestions)
            
            return suggestions
        
        except Exception as e:
            self.logger.error("生成優化建議失敗", error=str(e))
            return []
    
    async def _evaluate_parameter_suggestion(self, params: Dict, current_metrics: PerformanceMetrics) -> Dict:
        """評估參數建議"""
        try:
            # 計算參數變化
            current_params = self._extract_current_parameters()
            parameter_changes = {}
            
            for param_name, new_value in params.items():
                if param_name in current_params:
                    old_value = current_params[param_name]
                    if abs(new_value - old_value) > 0.001:  # 有顯著變化
                        parameter_changes[param_name] = {
                            'old_value': old_value,
                            'new_value': new_value,
                            'change_percentage': (new_value - old_value) / old_value * 100
                        }
            
            # 預測性能改善
            if self.ml_engine.is_trained:
                param_vector = np.array([params[param.name] for param in self.optimization_parameters])
                predicted_score, uncertainty = self.ml_engine.predict_performance(param_vector)
                current_score = self._calculate_performance_score(current_metrics)
                expected_improvement = predicted_score - current_score
                confidence = max(0, 1 - uncertainty)
            else:
                expected_improvement = 0.05  # 預設改善
                confidence = 0.5
            
            # 估算實施成本和風險
            implementation_cost = self._estimate_implementation_cost(parameter_changes)
            risk_score = self._assess_implementation_risk(parameter_changes)
            
            return {
                'parameter_changes': parameter_changes,
                'expected_improvement': expected_improvement,
                'confidence_score': confidence,
                'implementation_cost': implementation_cost,
                'risk_score': risk_score,
                'estimated_implementation_time': len(parameter_changes) * 30,  # 秒
                'rollback_plan': self._generate_rollback_plan(parameter_changes)
            }
        
        except Exception as e:
            self.logger.error("評估參數建議失敗", error=str(e))
            return {}
    
    async def _generate_ml_based_suggestions(self, current_metrics: PerformanceMetrics) -> List[Dict]:
        """生成基於ML的建議"""
        suggestions = []
        
        try:
            # 使用Optuna進行更智能的參數搜索
            def objective(trial):
                params = {}
                for param in self.optimization_parameters:
                    if param.parameter_type == 'continuous':
                        params[param.name] = trial.suggest_float(
                            param.name, param.min_value, param.max_value
                        )
                    elif param.parameter_type == 'discrete':
                        params[param.name] = trial.suggest_int(
                            param.name, int(param.min_value), int(param.max_value)
                        )
                
                # 預測性能
                param_vector = np.array([params[param.name] for param in self.optimization_parameters])
                predicted_score, _ = self.ml_engine.predict_performance(param_vector)
                return predicted_score
            
            # 運行Optuna優化
            study = optuna.create_study(direction='maximize')
            study.optimize(objective, n_trials=10, timeout=30)
            
            # 獲取最佳參數
            best_params = study.best_params
            suggestion = await self._evaluate_parameter_suggestion(best_params, current_metrics)
            suggestion['method'] = 'optuna_optimization'
            suggestion['suggestion_id'] = 'optuna_best'
            suggestions.append(suggestion)
        
        except Exception as e:
            self.logger.warning("Optuna優化失敗", error=str(e))
        
        return suggestions
    
    async def _generate_rule_based_suggestions(self, current_metrics: PerformanceMetrics) -> List[Dict]:
        """生成基於規則的建議"""
        suggestions = []
        current_params = self._extract_current_parameters()
        
        try:
            # 規則1: 如果延遲過高，調整相關參數
            if current_metrics.latency_ms > 60:
                params = current_params.copy()
                params['upf_buffer_size_mb'] = min(512, params['upf_buffer_size_mb'] * 1.2)
                params['smf_session_timeout_seconds'] = max(60, params['smf_session_timeout_seconds'] * 0.8)
                
                suggestion = await self._evaluate_parameter_suggestion(params, current_metrics)
                suggestion['method'] = 'rule_based_latency'
                suggestion['suggestion_id'] = 'rule_latency'
                suggestion['rule_description'] = '降低延遲優化'
                suggestions.append(suggestion)
            
            # 規則2: 如果吞吐量不足，調整功率和帶寬
            if current_metrics.throughput_mbps < 50:
                params = current_params.copy()
                params['gnb_tx_power_dbm'] = min(30, params['gnb_tx_power_dbm'] + 2)
                params['gnb_bandwidth_mhz'] = min(100, params['gnb_bandwidth_mhz'] * 1.5)
                
                suggestion = await self._evaluate_parameter_suggestion(params, current_metrics)
                suggestion['method'] = 'rule_based_throughput'
                suggestion['suggestion_id'] = 'rule_throughput'
                suggestion['rule_description'] = '提升吞吐量優化'
                suggestions.append(suggestion)
            
            # 規則3: 如果SINR較低，調整天線參數
            if current_metrics.sinr_db < 15:
                params = current_params.copy()
                params['gnb_antenna_gain_db'] = min(25, params['gnb_antenna_gain_db'] + 3)
                params['satellite_elevation_threshold_deg'] = min(30, params['satellite_elevation_threshold_deg'] + 5)
                
                suggestion = await self._evaluate_parameter_suggestion(params, current_metrics)
                suggestion['method'] = 'rule_based_sinr'
                suggestion['suggestion_id'] = 'rule_sinr'
                suggestion['rule_description'] = '改善信號品質優化'
                suggestions.append(suggestion)
        
        except Exception as e:
            self.logger.error("生成規則建議失敗", error=str(e))
        
        return suggestions
    
    async def _select_best_suggestion(self, suggestions: List[Dict], current_metrics: PerformanceMetrics) -> Optional[Dict]:
        """選擇最佳建議"""
        if not suggestions:
            return None
        
        # 根據多個因素評分
        for suggestion in suggestions:
            # 計算綜合評分
            improvement_score = suggestion.get('expected_improvement', 0) * 10
            confidence_score = suggestion.get('confidence_score', 0) * 5
            cost_penalty = suggestion.get('implementation_cost', 0) * -0.1
            risk_penalty = suggestion.get('risk_score', 0) * -2
            
            suggestion['total_score'] = improvement_score + confidence_score + cost_penalty + risk_penalty
        
        # 選擇評分最高的建議
        best_suggestion = max(suggestions, key=lambda x: x.get('total_score', 0))
        
        # 檢查是否值得實施
        if best_suggestion.get('total_score', 0) > 2.0 and best_suggestion.get('confidence_score', 0) > 0.5:
            return best_suggestion
        
        return None
    
    def _estimate_implementation_cost(self, parameter_changes: Dict) -> float:
        """估算實施成本"""
        cost = 0
        
        for param_name, change_info in parameter_changes.items():
            change_percentage = abs(change_info.get('change_percentage', 0))
            
            # 不同參數的變更成本不同
            if 'power' in param_name.lower():
                cost += change_percentage * 0.1  # 功率變更成本較低
            elif 'bandwidth' in param_name.lower():
                cost += change_percentage * 0.2  # 帶寬變更成本中等
            elif 'session' in param_name.lower() or 'timeout' in param_name.lower():
                cost += change_percentage * 0.05  # 軟體參數變更成本很低
            else:
                cost += change_percentage * 0.1
        
        return cost
    
    def _assess_implementation_risk(self, parameter_changes: Dict) -> float:
        """評估實施風險"""
        risk = 0
        
        for param_name, change_info in parameter_changes.items():
            change_percentage = abs(change_info.get('change_percentage', 0))
            
            # 大幅度變更風險較高
            if change_percentage > 50:
                risk += 0.8
            elif change_percentage > 20:
                risk += 0.4
            elif change_percentage > 10:
                risk += 0.2
            
            # 某些參數變更風險較高
            if 'power' in param_name.lower() and change_percentage > 20:
                risk += 0.3
            elif 'threshold' in param_name.lower() and change_percentage > 30:
                risk += 0.4
        
        return min(1.0, risk)
    
    def _generate_rollback_plan(self, parameter_changes: Dict) -> Dict:
        """生成回滾計劃"""
        rollback_plan = {
            'parameters': {},
            'estimated_rollback_time': len(parameter_changes) * 15,  # 秒
            'rollback_conditions': []
        }
        
        for param_name, change_info in parameter_changes.items():
            rollback_plan['parameters'][param_name] = change_info['old_value']
        
        # 定義自動回滾條件
        rollback_plan['rollback_conditions'] = [
            'latency_increase_over_20_percent',
            'throughput_decrease_over_30_percent',
            'packet_loss_rate_over_5_percent',
            'sinr_decrease_over_5_db'
        ]
        
        return rollback_plan
    
    async def _implement_optimization(self, suggestion: Dict) -> Dict:
        """實施優化"""
        try:
            implementation_start_time = datetime.utcnow()
            
            # 記錄實施前的性能
            pre_implementation_metrics = await self._collect_current_metrics()
            
            # 實施參數變更
            parameter_changes = suggestion.get('parameter_changes', {})
            implementation_results = []
            
            for param_name, change_info in parameter_changes.items():
                result = await self._apply_parameter_change(param_name, change_info['new_value'])
                implementation_results.append({
                    'parameter': param_name,
                    'old_value': change_info['old_value'],
                    'new_value': change_info['new_value'],
                    'result': result
                })
            
            # 等待系統穩定
            await asyncio.sleep(30)
            
            # 收集實施後的性能
            post_implementation_metrics = await self._collect_current_metrics()
            
            # 計算實際改善
            actual_improvement = self._calculate_performance_score(post_implementation_metrics) - \
                               self._calculate_performance_score(pre_implementation_metrics)
            
            # 檢查是否需要回滾
            should_rollback = self._should_rollback(
                pre_implementation_metrics, post_implementation_metrics, suggestion
            )
            
            if should_rollback:
                rollback_result = await self._execute_rollback(suggestion['rollback_plan'])
                return {
                    'success': False,
                    'rollback_executed': True,
                    'rollback_result': rollback_result,
                    'reason': 'performance_degradation_detected'
                }
            
            # 更新參數當前值
            await self._update_current_parameters(parameter_changes)
            
            implementation_time = (datetime.utcnow() - implementation_start_time).total_seconds()
            
            return {
                'success': True,
                'implementation_time_seconds': implementation_time,
                'parameter_changes_applied': len(implementation_results),
                'implementation_results': implementation_results,
                'pre_implementation_metrics': pre_implementation_metrics.__dict__,
                'post_implementation_metrics': post_implementation_metrics.__dict__,
                'actual_improvement': actual_improvement,
                'expected_improvement': suggestion.get('expected_improvement', 0)
            }
        
        except Exception as e:
            self.logger.error("實施優化失敗", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def _apply_parameter_change(self, param_name: str, new_value: float) -> Dict:
        """應用參數變更"""
        try:
            # 這裡應該實際修改系統配置
            # 現在只是模擬實施
            await asyncio.sleep(1)  # 模擬配置時間
            
            # 更新內部參數記錄
            for param in self.optimization_parameters:
                if param.name == param_name:
                    param.current_value = new_value
                    break
            
            return {
                'success': True,
                'parameter': param_name,
                'new_value': new_value,
                'applied_at': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                'success': False,
                'parameter': param_name,
                'error': str(e)
            }
    
    def _should_rollback(
        self, 
        pre_metrics: PerformanceMetrics, 
        post_metrics: PerformanceMetrics, 
        suggestion: Dict
    ) -> bool:
        """檢查是否應該回滾"""
        # 檢查關鍵性能指標是否嚴重下降
        latency_increase = (post_metrics.latency_ms - pre_metrics.latency_ms) / pre_metrics.latency_ms
        throughput_decrease = (pre_metrics.throughput_mbps - post_metrics.throughput_mbps) / pre_metrics.throughput_mbps
        packet_loss_increase = post_metrics.packet_loss_rate - pre_metrics.packet_loss_rate
        sinr_decrease = pre_metrics.sinr_db - post_metrics.sinr_db
        
        # 定義回滾條件
        if latency_increase > 0.2:  # 延遲增加超過20%
            return True
        if throughput_decrease > 0.3:  # 吞吐量降低超過30%
            return True
        if packet_loss_increase > 0.05:  # 封包損失率增加超過5%
            return True
        if sinr_decrease > 5:  # SINR降低超過5dB
            return True
        
        return False
    
    async def _execute_rollback(self, rollback_plan: Dict) -> Dict:
        """執行回滾"""
        try:
            rollback_start_time = datetime.utcnow()
            
            rollback_results = []
            for param_name, old_value in rollback_plan['parameters'].items():
                result = await self._apply_parameter_change(param_name, old_value)
                rollback_results.append(result)
            
            rollback_time = (datetime.utcnow() - rollback_start_time).total_seconds()
            
            return {
                'success': True,
                'rollback_time_seconds': rollback_time,
                'rollback_results': rollback_results
            }
        
        except Exception as e:
            self.logger.error("執行回滾失敗", error=str(e))
            return {'success': False, 'error': str(e)}
    
    async def _update_current_parameters(self, parameter_changes: Dict):
        """更新當前參數值"""
        for param_name, change_info in parameter_changes.items():
            for param in self.optimization_parameters:
                if param.name == param_name:
                    param.current_value = change_info['new_value']
                    break
    
    async def _save_optimization_data(self):
        """保存優化數據"""
        try:
            # 保存機器學習模型
            if self.ml_engine.is_trained:
                model_path = self.model_save_path / "ml_optimization_model.joblib"
                scaler_path = self.model_save_path / "ml_optimization_scaler.joblib"
                
                joblib.dump(self.ml_engine.best_model, model_path)
                joblib.dump(self.ml_engine.scaler, scaler_path)
            
            # 保存歷史數據
            history_path = self.model_save_path / "optimization_history.pkl"
            with open(history_path, 'wb') as f:
                pickle.dump({
                    'performance_history': list(self.performance_history),
                    'optimization_history': list(self.optimization_history),
                    'current_parameters': [param.__dict__ for param in self.optimization_parameters]
                }, f)
            
            self.logger.info("優化數據已保存")
        
        except Exception as e:
            self.logger.error("保存優化數據失敗", error=str(e))
    
    def _load_saved_data(self):
        """載入已保存的數據"""
        try:
            # 載入歷史數據
            history_path = self.model_save_path / "optimization_history.pkl"
            if history_path.exists():
                with open(history_path, 'rb') as f:
                    data = pickle.load(f)
                    
                    # 重建性能歷史
                    for metrics_dict in data.get('performance_history', []):
                        if isinstance(metrics_dict, dict):
                            metrics = PerformanceMetrics(**metrics_dict)
                            self.performance_history.append(metrics)
                    
                    # 重建優化歷史
                    self.optimization_history.extend(data.get('optimization_history', []))
                    
                    # 更新參數值
                    saved_params = data.get('current_parameters', [])
                    for saved_param in saved_params:
                        for param in self.optimization_parameters:
                            if param.name == saved_param['name']:
                                param.current_value = saved_param['current_value']
                                break
            
            # 載入機器學習模型
            model_path = self.model_save_path / "ml_optimization_model.joblib"
            scaler_path = self.model_save_path / "ml_optimization_scaler.joblib"
            
            if model_path.exists() and scaler_path.exists():
                self.ml_engine.best_model = joblib.load(model_path)
                self.ml_engine.scaler = joblib.load(scaler_path)
                self.ml_engine.is_trained = True
                self.logger.info("機器學習模型已載入")
        
        except Exception as e:
            self.logger.warning("載入保存數據失敗", error=str(e))
    
    async def get_service_status(self) -> Dict:
        """獲取服務狀態"""
        return {
            'service_name': '自動化調優服務',
            'is_optimization_running': self.is_optimization_running,
            'last_optimization_time': self.last_optimization_time.isoformat() if self.last_optimization_time else None,
            'current_optimization_cycle': self.current_optimization_cycle,
            'optimization_interval_minutes': self.optimization_interval.total_seconds() / 60,
            'performance_history_count': len(self.performance_history),
            'optimization_history_count': len(self.optimization_history),
            'ml_engine_trained': self.ml_engine.is_trained,
            'bayesian_optimizer_observations': len(self.bayesian_optimizer.observation_history),
            'optimization_parameters_count': len(self.optimization_parameters),
            'current_parameters': {param.name: param.current_value for param in self.optimization_parameters}
        }
    
    async def manual_optimization(self, target_objectives: Optional[Dict] = None) -> Dict:
        """手動觸發優化"""
        if self.is_optimization_running:
            return {'success': False, 'error': '優化正在進行中'}
        
        return await self.run_optimization_cycle()
    
    async def get_optimization_report(self, days: int = 7) -> Dict:
        """獲取優化報告"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        recent_optimizations = [
            opt for opt in self.optimization_history
            if datetime.fromisoformat(opt['start_time']) >= cutoff_date
        ]
        
        if not recent_optimizations:
            return {'report': 'no_recent_optimizations'}
        
        # 分析優化效果
        total_cycles = len(recent_optimizations)
        successful_optimizations = len([opt for opt in recent_optimizations 
                                      if opt.get('implementation_result', {}).get('success', False)])
        
        # 計算平均改善
        improvements = []
        for opt in recent_optimizations:
            impl_result = opt.get('implementation_result', {})
            if impl_result.get('success', False):
                improvements.append(impl_result.get('actual_improvement', 0))
        
        avg_improvement = np.mean(improvements) if improvements else 0
        
        return {
            'report_period_days': days,
            'total_optimization_cycles': total_cycles,
            'successful_optimizations': successful_optimizations,
            'success_rate': successful_optimizations / total_cycles if total_cycles > 0 else 0,
            'average_improvement': avg_improvement,
            'total_improvement': sum(improvements),
            'recent_optimizations': recent_optimizations[-10:]  # 最近10次
        }