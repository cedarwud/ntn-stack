"""
Phase 3.2.2.3: ML 驅動預測模型整合實現

實現機器學習驅動的預測模型系統，包括：
1. 衛星軌道預測優化模型
2. 切換決策預測模型
3. 服務質量預測模型
4. 負載預測和資源優化模型
5. 異常檢測和故障預測模型

符合標準：
- TensorFlow/PyTorch 機器學習框架
- scikit-learn 傳統機器學習算法
- Time Series Forecasting 時間序列預測
- Online Learning 在線學習機制
- Model Versioning 模型版本管理
"""

import asyncio
import logging
import numpy as np
import pandas as pd
import pickle
import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Union, Callable
from enum import Enum
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
import threading
import uuid
import time
import math

# ML framework imports
try:
    import sklearn
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression, Ridge, Lasso
    from sklearn.neural_network import MLPRegressor
    from sklearn.svm import SVR
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.model_selection import train_test_split, cross_val_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """模型類型"""
    ORBIT_PREDICTION = "orbit_prediction"          # 軌道預測
    HANDOVER_DECISION = "handover_decision"        # 切換決策
    QOS_PREDICTION = "qos_prediction"              # 服務質量預測
    LOAD_PREDICTION = "load_prediction"            # 負載預測
    ANOMALY_DETECTION = "anomaly_detection"        # 異常檢測
    RESOURCE_OPTIMIZATION = "resource_optimization" # 資源優化


class PredictionTarget(Enum):
    """預測目標"""
    SIGNAL_STRENGTH = "signal_strength"            # 信號強度
    THROUGHPUT = "throughput"                      # 吞吐量
    LATENCY = "latency"                           # 延遲
    PACKET_LOSS = "packet_loss"                   # 丟包率
    HANDOVER_SUCCESS = "handover_success"         # 切換成功率
    SATELLITE_LOAD = "satellite_load"             # 衛星負載
    ORBITAL_POSITION = "orbital_position"         # 軌道位置
    DOPPLER_SHIFT = "doppler_shift"              # 都卜勒頻移


class TrainingStatus(Enum):
    """訓練狀態"""
    NOT_STARTED = "not_started"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"
    UPDATING = "updating"


@dataclass
class TrainingData:
    """訓練數據"""
    feature_data: np.ndarray
    target_data: np.ndarray
    feature_names: List[str]
    target_name: str
    timestamp: datetime
    data_source: str
    quality_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelMetrics:
    """模型指標"""
    mse: float = 0.0                    # 均方誤差
    mae: float = 0.0                    # 平均絕對誤差
    rmse: float = 0.0                   # 均方根誤差
    r2_score: float = 0.0               # 決定係數
    accuracy: float = 0.0               # 準確率（分類模型）
    precision: float = 0.0              # 精確率
    recall: float = 0.0                 # 召回率
    f1_score: float = 0.0               # F1分數
    training_time_ms: float = 0.0       # 訓練時間
    inference_time_ms: float = 0.0      # 推理時間
    model_size_bytes: int = 0           # 模型大小
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PredictionResult:
    """預測結果"""
    prediction_id: str
    model_id: str
    input_features: Dict[str, Any]
    predicted_value: Union[float, np.ndarray]
    confidence_score: float
    prediction_timestamp: datetime
    model_version: str
    feature_importance: Optional[Dict[str, float]] = None
    uncertainty_bounds: Optional[Tuple[float, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MLPredictionModel:
    """機器學習預測模型基類"""
    
    def __init__(self, model_id: str, model_type: ModelType, 
                 prediction_target: PredictionTarget):
        self.model_id = model_id
        self.model_type = model_type
        self.prediction_target = prediction_target
        self.version = "1.0.0"
        
        # 模型狀態
        self.is_trained = False
        self.training_status = TrainingStatus.NOT_STARTED
        self.last_training_time: Optional[datetime] = None
        
        # 模型對象
        self.model = None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        
        # 訓練歷史
        self.training_history: List[TrainingData] = []
        self.metrics_history: List[ModelMetrics] = []
        
        # 配置
        self.config = {
            'retrain_threshold_samples': 1000,
            'retrain_threshold_accuracy_drop': 0.05,
            'feature_importance_threshold': 0.01,
            'prediction_confidence_threshold': 0.7,
            'max_training_data_size': 10000,
            'auto_retrain_enabled': True,
            'online_learning_enabled': False
        }
        
        # 統計信息
        self.stats = {
            'predictions_made': 0,
            'successful_predictions': 0,
            'training_sessions': 0,
            'total_training_time_ms': 0.0,
            'average_prediction_time_ms': 0.0,
            'data_points_processed': 0,
            'model_accuracy_trend': []
        }
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def initialize_model(self, **model_params):
        """初始化機器學習模型"""
        if not SKLEARN_AVAILABLE:
            raise RuntimeError("scikit-learn not available for ML models")
        
        try:
            # 根據預測目標選擇合適的模型
            if self.prediction_target in [PredictionTarget.SIGNAL_STRENGTH, 
                                        PredictionTarget.THROUGHPUT,
                                        PredictionTarget.LATENCY]:
                # 回歸模型
                self.model = RandomForestRegressor(
                    n_estimators=model_params.get('n_estimators', 100),
                    max_depth=model_params.get('max_depth', 10),
                    random_state=42,
                    n_jobs=-1
                )
            
            elif self.prediction_target == PredictionTarget.HANDOVER_SUCCESS:
                # 分類模型（使用回歸器的閾值方式）
                self.model = GradientBoostingRegressor(
                    n_estimators=model_params.get('n_estimators', 100),
                    learning_rate=model_params.get('learning_rate', 0.1),
                    max_depth=model_params.get('max_depth', 6),
                    random_state=42
                )
            
            else:
                # 默認使用隨機森林
                self.model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42,
                    n_jobs=-1
                )
            
            self.logger.info(f"✅ 模型 {self.model_id} 初始化完成 - 類型: {type(self.model).__name__}")
            
        except Exception as e:
            self.logger.error(f"❌ 模型初始化失敗: {e}")
            raise
    
    async def train(self, training_data: TrainingData, 
                   validation_split: float = 0.2) -> ModelMetrics:
        """訓練模型"""
        if not SKLEARN_AVAILABLE:
            raise RuntimeError("scikit-learn not available for model training")
        
        start_time = time.time()
        self.training_status = TrainingStatus.TRAINING
        
        try:
            # 數據預處理
            X = training_data.feature_data
            y = training_data.target_data
            
            if X.shape[0] == 0 or y.shape[0] == 0:
                raise ValueError("訓練數據為空")
            
            # 數據標準化
            X_scaled = self.scaler.fit_transform(X)
            
            # 分割訓練和驗證數據
            if validation_split > 0:
                X_train, X_val, y_train, y_val = train_test_split(
                    X_scaled, y, test_size=validation_split, random_state=42
                )
            else:
                X_train, y_train = X_scaled, y
                X_val, y_val = None, None
            
            # 訓練模型
            self.model.fit(X_train, y_train)
            
            # 計算指標
            metrics = ModelMetrics()
            
            if X_val is not None and y_val is not None:
                y_pred = self.model.predict(X_val)
                metrics.mse = mean_squared_error(y_val, y_pred)
                metrics.mae = mean_absolute_error(y_val, y_pred)
                metrics.rmse = np.sqrt(metrics.mse)
                metrics.r2_score = r2_score(y_val, y_pred)
            else:
                # 使用訓練數據計算指標（不理想但可用）
                y_pred = self.model.predict(X_train)
                metrics.mse = mean_squared_error(y_train, y_pred)
                metrics.mae = mean_absolute_error(y_train, y_pred)
                metrics.rmse = np.sqrt(metrics.mse)
                metrics.r2_score = r2_score(y_train, y_pred)
            
            # 訓練時間
            training_time = (time.time() - start_time) * 1000
            metrics.training_time_ms = training_time
            
            # 模型大小估算
            try:
                import sys
                metrics.model_size_bytes = sys.getsizeof(pickle.dumps(self.model))
            except:
                metrics.model_size_bytes = 0
            
            # 更新狀態
            self.is_trained = True
            self.training_status = TrainingStatus.COMPLETED
            self.last_training_time = datetime.now(timezone.utc)
            
            # 記錄訓練歷史
            self.training_history.append(training_data)
            if len(self.training_history) > self.config['max_training_data_size']:
                self.training_history = self.training_history[-self.config['max_training_data_size']:]
            
            self.metrics_history.append(metrics)
            
            # 更新統計
            self.stats['training_sessions'] += 1
            self.stats['total_training_time_ms'] += training_time
            self.stats['data_points_processed'] += X.shape[0]
            self.stats['model_accuracy_trend'].append(metrics.r2_score)
            
            self.logger.info(f"✅ 模型 {self.model_id} 訓練完成 - "
                           f"R²: {metrics.r2_score:.4f}, "
                           f"RMSE: {metrics.rmse:.4f}, "
                           f"訓練時間: {training_time:.1f}ms")
            
            return metrics
            
        except Exception as e:
            self.training_status = TrainingStatus.FAILED
            self.logger.error(f"❌ 模型訓練失敗: {e}")
            raise
    
    async def predict(self, features: Dict[str, Any]) -> PredictionResult:
        """進行預測"""
        if not self.is_trained:
            raise RuntimeError(f"模型 {self.model_id} 尚未訓練")
        
        start_time = time.time()
        
        try:
            # 特徵向量化
            feature_vector = self._vectorize_features(features)
            
            # 數據標準化
            if self.scaler:
                feature_vector_scaled = self.scaler.transform(feature_vector.reshape(1, -1))
            else:
                feature_vector_scaled = feature_vector.reshape(1, -1)
            
            # 預測
            prediction = self.model.predict(feature_vector_scaled)[0]
            
            # 計算置信度（基於特徵重要性和歷史準確性）
            confidence = self._calculate_confidence(features, prediction)
            
            # 計算不確定性邊界（如果模型支持）
            uncertainty_bounds = self._calculate_uncertainty_bounds(
                feature_vector_scaled, prediction
            )
            
            # 特徵重要性
            feature_importance = self._get_feature_importance(features.keys())
            
            # 創建預測結果
            result = PredictionResult(
                prediction_id=f"pred_{uuid.uuid4().hex[:8]}",
                model_id=self.model_id,
                input_features=features,
                predicted_value=float(prediction),
                confidence_score=confidence,
                prediction_timestamp=datetime.now(timezone.utc),
                model_version=self.version,
                feature_importance=feature_importance,
                uncertainty_bounds=uncertainty_bounds
            )
            
            # 推理時間
            inference_time = (time.time() - start_time) * 1000
            result.metadata['inference_time_ms'] = inference_time
            
            # 更新統計
            self.stats['predictions_made'] += 1
            if confidence >= self.config['prediction_confidence_threshold']:
                self.stats['successful_predictions'] += 1
            
            # 更新平均推理時間
            total_predictions = self.stats['predictions_made']
            current_avg = self.stats['average_prediction_time_ms']
            self.stats['average_prediction_time_ms'] = \
                (current_avg * (total_predictions - 1) + inference_time) / total_predictions
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 預測失敗: {e}")
            raise
    
    def _vectorize_features(self, features: Dict[str, Any]) -> np.ndarray:
        """將特徵字典轉換為數值向量"""
        try:
            # 基本特徵列表（可根據具體模型擴展）
            feature_order = [
                'signal_strength_dbm', 'elevation_angle', 'distance_km',
                'satellite_load', 'user_count', 'available_bandwidth_mbps',
                'current_throughput_mbps', 'current_latency_ms',
                'doppler_shift_hz', 'interference_level_db'
            ]
            
            vector = []
            for feature_name in feature_order:
                value = features.get(feature_name, 0.0)
                if isinstance(value, (int, float)):
                    vector.append(float(value))
                else:
                    vector.append(0.0)
            
            # 如果向量為空，添加默認特徵
            if not vector:
                vector = [0.0] * 10  # 10個默認特徵
            
            return np.array(vector)
            
        except Exception as e:
            self.logger.error(f"❌ 特徵向量化失敗: {e}")
            # 返回默認向量
            return np.zeros(10)
    
    def _calculate_confidence(self, features: Dict[str, Any], prediction: float) -> float:
        """計算預測置信度"""
        try:
            # 基於歷史準確性的基礎置信度
            if self.metrics_history:
                latest_metrics = self.metrics_history[-1]
                base_confidence = max(0.1, min(0.9, latest_metrics.r2_score))
            else:
                base_confidence = 0.5
            
            # 基於特徵質量的調整
            feature_quality = self._assess_feature_quality(features)
            
            # 基於預測值合理性的調整
            prediction_reasonableness = self._assess_prediction_reasonableness(prediction)
            
            # 綜合置信度
            confidence = base_confidence * feature_quality * prediction_reasonableness
            
            return max(0.0, min(1.0, confidence))
            
        except Exception:
            return 0.5  # 默認中等置信度
    
    def _assess_feature_quality(self, features: Dict[str, Any]) -> float:
        """評估特徵質量"""
        try:
            quality_score = 1.0
            
            # 檢查關鍵特徵是否存在
            key_features = ['signal_strength_dbm', 'elevation_angle', 'distance_km']
            missing_key_features = sum(1 for f in key_features if f not in features)
            quality_score *= (1.0 - missing_key_features / len(key_features) * 0.3)
            
            # 檢查特徵值的合理性
            for feature_name, value in features.items():
                if not isinstance(value, (int, float)):
                    quality_score *= 0.9
                elif math.isnan(value) or math.isinf(value):
                    quality_score *= 0.8
                else:
                    # 檢查特徵值範圍
                    if feature_name == 'signal_strength_dbm' and not (-150 <= value <= -30):
                        quality_score *= 0.9
                    elif feature_name == 'elevation_angle' and not (0 <= value <= 90):
                        quality_score *= 0.9
            
            return max(0.1, quality_score)
            
        except Exception:
            return 0.8  # 默認較高質量
    
    def _assess_prediction_reasonableness(self, prediction: float) -> float:
        """評估預測值合理性"""
        try:
            if math.isnan(prediction) or math.isinf(prediction):
                return 0.1
            
            # 根據預測目標檢查合理性
            if self.prediction_target == PredictionTarget.SIGNAL_STRENGTH:
                if -150 <= prediction <= -30:
                    return 1.0
                else:
                    return 0.6
            elif self.prediction_target == PredictionTarget.THROUGHPUT:
                if 0 <= prediction <= 1000:  # 0-1000 Mbps
                    return 1.0
                else:
                    return 0.7
            elif self.prediction_target == PredictionTarget.LATENCY:
                if 0 <= prediction <= 5000:  # 0-5000 ms
                    return 1.0
                else:
                    return 0.7
            
            return 0.9  # 默認高合理性
            
        except Exception:
            return 0.8
    
    def _calculate_uncertainty_bounds(self, feature_vector: np.ndarray, 
                                    prediction: float) -> Optional[Tuple[float, float]]:
        """計算不確定性邊界"""
        try:
            if hasattr(self.model, 'predict') and hasattr(self.model, 'estimators_'):
                # 對於隨機森林等集成模型，使用樹的預測方差
                if hasattr(self.model, 'estimators_'):
                    tree_predictions = [tree.predict(feature_vector)[0] 
                                      for tree in self.model.estimators_]
                    std_dev = np.std(tree_predictions)
                    
                    # 95%置信區間
                    lower_bound = prediction - 1.96 * std_dev
                    upper_bound = prediction + 1.96 * std_dev
                    
                    return (float(lower_bound), float(upper_bound))
            
            # 基於歷史誤差的簡單估算
            if self.metrics_history:
                latest_metrics = self.metrics_history[-1]
                error_margin = latest_metrics.rmse * 1.96  # 95%置信區間
                
                return (prediction - error_margin, prediction + error_margin)
            
            return None
            
        except Exception:
            return None
    
    def _get_feature_importance(self, feature_names: List[str]) -> Dict[str, float]:
        """獲取特徵重要性"""
        try:
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
                
                # 創建特徵重要性字典
                importance_dict = {}
                for i, importance in enumerate(importances):
                    if i < len(feature_names):
                        feature_name = list(feature_names)[i]
                        if importance >= self.config['feature_importance_threshold']:
                            importance_dict[feature_name] = float(importance)
                
                return importance_dict
            
            return {}
            
        except Exception:
            return {}
    
    async def update_model(self, new_data: TrainingData) -> bool:
        """增量更新模型"""
        try:
            if not self.config['online_learning_enabled']:
                return False
            
            # 對於支持增量學習的模型，進行在線更新
            # 這裡簡化為重新訓練（生產環境中可以使用增量學習算法）
            
            # 合併新數據和歷史數據
            if self.training_history:
                # 合併最近的訓練數據
                recent_data = self.training_history[-5:]  # 最近5次的數據
                combined_features = []
                combined_targets = []
                
                for data in recent_data:
                    combined_features.append(data.feature_data)
                    combined_targets.append(data.target_data)
                
                combined_features.append(new_data.feature_data)
                combined_targets.append(new_data.target_data)
                
                # 創建合併的訓練數據
                combined_training_data = TrainingData(
                    feature_data=np.vstack(combined_features),
                    target_data=np.hstack(combined_targets),
                    feature_names=new_data.feature_names,
                    target_name=new_data.target_name,
                    timestamp=datetime.now(timezone.utc),
                    data_source="incremental_update"
                )
                
                # 重新訓練
                await self.train(combined_training_data, validation_split=0.1)
                
                self.logger.info(f"✅ 模型 {self.model_id} 增量更新完成")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 模型增量更新失敗: {e}")
            return False
    
    def save_model(self, file_path: str) -> bool:
        """保存模型"""
        try:
            model_data = {
                'model_id': self.model_id,
                'model_type': self.model_type.value,
                'prediction_target': self.prediction_target.value,
                'version': self.version,
                'model': self.model,
                'scaler': self.scaler,
                'is_trained': self.is_trained,
                'last_training_time': self.last_training_time,
                'config': self.config,
                'stats': self.stats,
                'metrics_history': self.metrics_history[-10:]  # 最近10次指標
            }
            
            with open(file_path, 'wb') as f:
                pickle.dump(model_data, f)
            
            self.logger.info(f"✅ 模型 {self.model_id} 已保存到 {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 模型保存失敗: {e}")
            return False
    
    def load_model(self, file_path: str) -> bool:
        """加載模型"""
        try:
            with open(file_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model_id = model_data['model_id']
            self.model_type = ModelType(model_data['model_type'])
            self.prediction_target = PredictionTarget(model_data['prediction_target'])
            self.version = model_data['version']
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.is_trained = model_data['is_trained']
            self.last_training_time = model_data['last_training_time']
            self.config.update(model_data.get('config', {}))
            self.stats.update(model_data.get('stats', {}))
            self.metrics_history = model_data.get('metrics_history', [])
            
            self.logger.info(f"✅ 模型 {self.model_id} 已從 {file_path} 加載")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 模型加載失敗: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """獲取模型信息"""
        return {
            'model_id': self.model_id,
            'model_type': self.model_type.value,
            'prediction_target': self.prediction_target.value,
            'version': self.version,
            'is_trained': self.is_trained,
            'training_status': self.training_status.value,
            'last_training_time': self.last_training_time.isoformat() if self.last_training_time else None,
            'model_class': type(self.model).__name__ if self.model else None,
            'config': self.config,
            'stats': self.stats,
            'latest_metrics': self.metrics_history[-1].__dict__ if self.metrics_history else None
        }


class MLPredictionEngine:
    """機器學習預測引擎管理器"""
    
    def __init__(self, engine_id: str = None):
        self.engine_id = engine_id or f"ml_engine_{uuid.uuid4().hex[:8]}"
        
        # 模型管理
        self.models: Dict[str, MLPredictionModel] = {}
        self.model_registry: Dict[ModelType, List[str]] = defaultdict(list)
        
        # 配置
        self.config = {
            'auto_model_selection': True,
            'ensemble_predictions': False,
            'model_performance_threshold': 0.7,
            'retrain_schedule_hours': 24,
            'prediction_cache_enabled': True,
            'prediction_cache_ttl_seconds': 300
        }
        
        # 預測緩存
        self.prediction_cache: Dict[str, Tuple[PredictionResult, datetime]] = {}
        
        # 統計信息
        self.stats = {
            'total_models': 0,
            'active_models': 0,
            'total_predictions': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'model_training_sessions': 0,
            'average_prediction_accuracy': 0.0
        }
        
        # 線程鎖
        self.lock = threading.RLock()
        
        # 運行狀態
        self.is_running = False
        self.maintenance_task: Optional[asyncio.Task] = None
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def start_engine(self):
        """啟動預測引擎"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # 啟動維護任務
        self.maintenance_task = asyncio.create_task(self._maintenance_loop())
        
        self.logger.info(f"🚀 ML預測引擎已啟動 - ID: {self.engine_id}")
    
    async def stop_engine(self):
        """停止預測引擎"""
        self.is_running = False
        
        if self.maintenance_task:
            self.maintenance_task.cancel()
            try:
                await self.maintenance_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("⏹️ ML預測引擎已停止")
    
    def register_model(self, model: MLPredictionModel) -> bool:
        """註冊模型"""
        try:
            with self.lock:
                self.models[model.model_id] = model
                self.model_registry[model.model_type].append(model.model_id)
                self.stats['total_models'] += 1
                
                if model.is_trained:
                    self.stats['active_models'] += 1
            
            self.logger.info(f"✅ 模型註冊成功: {model.model_id} ({model.model_type.value})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 模型註冊失敗: {e}")
            return False
    
    def unregister_model(self, model_id: str) -> bool:
        """註銷模型"""
        try:
            with self.lock:
                if model_id in self.models:
                    model = self.models[model_id]
                    del self.models[model_id]
                    
                    # 從註冊表中移除
                    if model_id in self.model_registry[model.model_type]:
                        self.model_registry[model.model_type].remove(model_id)
                    
                    self.stats['total_models'] -= 1
                    if model.is_trained:
                        self.stats['active_models'] -= 1
                    
                    self.logger.info(f"✅ 模型註銷成功: {model_id}")
                    return True
                else:
                    self.logger.warning(f"⚠️ 模型未找到: {model_id}")
                    return False
            
        except Exception as e:
            self.logger.error(f"❌ 模型註銷失敗: {e}")
            return False
    
    async def predict(self, model_id: str, features: Dict[str, Any], 
                     use_cache: bool = True) -> PredictionResult:
        """進行預測"""
        try:
            # 檢查緩存
            if use_cache and self.config['prediction_cache_enabled']:
                cache_key = f"{model_id}_{hash(str(sorted(features.items())))}"
                
                if cache_key in self.prediction_cache:
                    cached_result, cache_time = self.prediction_cache[cache_key]
                    cache_age = (datetime.now(timezone.utc) - cache_time).total_seconds()
                    
                    if cache_age < self.config['prediction_cache_ttl_seconds']:
                        self.stats['cache_hits'] += 1
                        return cached_result
                
                self.stats['cache_misses'] += 1
            
            # 獲取模型
            if model_id not in self.models:
                raise ValueError(f"模型未找到: {model_id}")
            
            model = self.models[model_id]
            
            # 進行預測
            result = await model.predict(features)
            
            # 更新緩存
            if use_cache and self.config['prediction_cache_enabled']:
                cache_key = f"{model_id}_{hash(str(sorted(features.items())))}"
                self.prediction_cache[cache_key] = (result, datetime.now(timezone.utc))
            
            # 更新統計
            self.stats['total_predictions'] += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 預測失敗: {e}")
            raise
    
    async def predict_with_ensemble(self, model_type: ModelType, 
                                   prediction_target: PredictionTarget,
                                   features: Dict[str, Any]) -> PredictionResult:
        """使用集成方法進行預測"""
        try:
            # 獲取相關模型
            relevant_models = []
            for model_id in self.model_registry[model_type]:
                model = self.models.get(model_id)
                if model and model.is_trained and model.prediction_target == prediction_target:
                    relevant_models.append(model)
            
            if not relevant_models:
                raise ValueError(f"沒有可用的模型進行預測: {model_type.value}, {prediction_target.value}")
            
            if len(relevant_models) == 1:
                # 只有一個模型，直接預測
                return await relevant_models[0].predict(features)
            
            # 集成預測
            predictions = []
            confidences = []
            
            for model in relevant_models:
                try:
                    result = await model.predict(features)
                    predictions.append(result.predicted_value)
                    confidences.append(result.confidence_score)
                except Exception as e:
                    self.logger.warning(f"⚠️ 模型 {model.model_id} 預測失敗: {e}")
                    continue
            
            if not predictions:
                raise RuntimeError("所有模型預測都失敗")
            
            # 加權平均預測
            weights = np.array(confidences)
            weights = weights / weights.sum()  # 歸一化
            
            ensemble_prediction = np.average(predictions, weights=weights)
            ensemble_confidence = np.mean(confidences)
            
            # 創建集成預測結果
            result = PredictionResult(
                prediction_id=f"ensemble_{uuid.uuid4().hex[:8]}",
                model_id=f"ensemble_{model_type.value}",
                input_features=features,
                predicted_value=float(ensemble_prediction),
                confidence_score=ensemble_confidence,
                prediction_timestamp=datetime.now(timezone.utc),
                model_version="ensemble_1.0",
                metadata={
                    'ensemble_size': len(predictions),
                    'individual_predictions': predictions,
                    'individual_confidences': confidences,
                    'model_ids': [m.model_id for m in relevant_models]
                }
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 集成預測失敗: {e}")
            raise
    
    async def train_model(self, model_id: str, training_data: TrainingData) -> ModelMetrics:
        """訓練指定模型"""
        try:
            if model_id not in self.models:
                raise ValueError(f"模型未找到: {model_id}")
            
            model = self.models[model_id]
            
            # 訓練模型
            metrics = await model.train(training_data)
            
            # 更新統計
            self.stats['model_training_sessions'] += 1
            
            # 更新活躍模型計數
            if model.is_trained:
                with self.lock:
                    self.stats['active_models'] = sum(
                        1 for m in self.models.values() if m.is_trained
                    )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"❌ 模型訓練失敗: {e}")
            raise
    
    def get_best_model(self, model_type: ModelType, 
                      prediction_target: PredictionTarget) -> Optional[MLPredictionModel]:
        """獲取最佳模型"""
        try:
            candidates = []
            
            for model_id in self.model_registry[model_type]:
                model = self.models.get(model_id)
                if (model and model.is_trained and 
                    model.prediction_target == prediction_target):
                    candidates.append(model)
            
            if not candidates:
                return None
            
            # 根據最新指標選擇最佳模型
            best_model = max(candidates, key=lambda m: (
                m.metrics_history[-1].r2_score if m.metrics_history else 0.0
            ))
            
            return best_model
            
        except Exception as e:
            self.logger.error(f"❌ 獲取最佳模型失敗: {e}")
            return None
    
    async def _maintenance_loop(self):
        """維護循環"""
        try:
            while self.is_running:
                await asyncio.sleep(3600)  # 每小時檢查一次
                
                # 清理過期緩存
                await self._cleanup_cache()
                
                # 檢查模型性能
                await self._check_model_performance()
                
        except asyncio.CancelledError:
            self.logger.info("🔄 維護循環已取消")
        except Exception as e:
            self.logger.error(f"❌ 維護循環異常: {e}")
    
    async def _cleanup_cache(self):
        """清理過期緩存"""
        try:
            current_time = datetime.now(timezone.utc)
            expired_keys = []
            
            for cache_key, (result, cache_time) in self.prediction_cache.items():
                cache_age = (current_time - cache_time).total_seconds()
                if cache_age > self.config['prediction_cache_ttl_seconds']:
                    expired_keys.append(cache_key)
            
            for key in expired_keys:
                del self.prediction_cache[key]
            
            if expired_keys:
                self.logger.debug(f"🗑️ 清理過期緩存: {len(expired_keys)} 個")
                
        except Exception as e:
            self.logger.error(f"❌ 清理緩存失敗: {e}")
    
    async def _check_model_performance(self):
        """檢查模型性能"""
        try:
            for model in self.models.values():
                if model.is_trained and model.metrics_history:
                    latest_metrics = model.metrics_history[-1]
                    
                    # 檢查性能是否低於閾值
                    if latest_metrics.r2_score < self.config['model_performance_threshold']:
                        self.logger.warning(
                            f"⚠️ 模型 {model.model_id} 性能較低: "
                            f"R² = {latest_metrics.r2_score:.4f}"
                        )
                        
                        # 可以在這裡觸發重新訓練或其他維護操作
                
        except Exception as e:
            self.logger.error(f"❌ 檢查模型性能失敗: {e}")
    
    def get_engine_status(self) -> Dict[str, Any]:
        """獲取引擎狀態"""
        with self.lock:
            return {
                'engine_id': self.engine_id,
                'is_running': self.is_running,
                'total_models': self.stats['total_models'],
                'active_models': self.stats['active_models'],
                'total_predictions': self.stats['total_predictions'],
                'cache_hit_rate': (
                    self.stats['cache_hits'] / 
                    max(1, self.stats['cache_hits'] + self.stats['cache_misses'])
                ),
                'prediction_cache_size': len(self.prediction_cache),
                'registered_model_types': {
                    model_type.value: len(model_ids) 
                    for model_type, model_ids in self.model_registry.items()
                },
                'config': self.config,
                'stats': self.stats
            }


# === 便利函數 ===

def create_ml_prediction_engine(engine_id: str = None) -> MLPredictionEngine:
    """創建ML預測引擎"""
    engine = MLPredictionEngine(engine_id)
    logger.info(f"✅ ML預測引擎創建完成 - ID: {engine.engine_id}")
    return engine


def create_orbit_prediction_model(model_id: str = None) -> MLPredictionModel:
    """創建軌道預測模型"""
    model_id = model_id or f"orbit_pred_{uuid.uuid4().hex[:8]}"
    model = MLPredictionModel(
        model_id=model_id,
        model_type=ModelType.ORBIT_PREDICTION,
        prediction_target=PredictionTarget.ORBITAL_POSITION
    )
    
    if SKLEARN_AVAILABLE:
        model.initialize_model(n_estimators=150, max_depth=12)
    
    logger.info(f"✅ 軌道預測模型創建完成 - ID: {model_id}")
    return model


def create_handover_prediction_model(model_id: str = None) -> MLPredictionModel:
    """創建切換預測模型"""
    model_id = model_id or f"handover_pred_{uuid.uuid4().hex[:8]}"
    model = MLPredictionModel(
        model_id=model_id,
        model_type=ModelType.HANDOVER_DECISION,
        prediction_target=PredictionTarget.HANDOVER_SUCCESS
    )
    
    if SKLEARN_AVAILABLE:
        model.initialize_model(n_estimators=100, learning_rate=0.1, max_depth=8)
    
    logger.info(f"✅ 切換預測模型創建完成 - ID: {model_id}")
    return model


def create_qos_prediction_model(model_id: str = None, 
                               target: PredictionTarget = PredictionTarget.THROUGHPUT) -> MLPredictionModel:
    """創建QoS預測模型"""
    model_id = model_id or f"qos_pred_{uuid.uuid4().hex[:8]}"
    model = MLPredictionModel(
        model_id=model_id,
        model_type=ModelType.QOS_PREDICTION,
        prediction_target=target
    )
    
    if SKLEARN_AVAILABLE:
        model.initialize_model(n_estimators=120, max_depth=10)
    
    logger.info(f"✅ QoS預測模型創建完成 - ID: {model_id} (目標: {target.value})")
    return model


def create_sample_training_data(data_type: str = "orbit") -> TrainingData:
    """創建示例訓練數據"""
    np.random.seed(42)  # 確保可重現性
    
    if data_type == "orbit":
        # 軌道預測訓練數據
        n_samples = 1000
        
        # 特徵：時間、初始位置、速度等
        features = np.random.rand(n_samples, 6)  # 6個特徵
        features[:, 0] = features[:, 0] * 6000  # 時間（秒）
        features[:, 1:3] = (features[:, 1:3] - 0.5) * 180  # 緯度、經度
        features[:, 3] = features[:, 3] * 1000 + 500  # 高度（500-1500km）
        features[:, 4:6] = features[:, 4:6] * 8  # 速度分量
        
        # 目標：未來位置（簡化的軌道模型）
        targets = features[:, 1] + 0.1 * features[:, 0] + np.random.normal(0, 0.1, n_samples)
        
        return TrainingData(
            feature_data=features,
            target_data=targets,
            feature_names=['time', 'lat', 'lon', 'alt', 'vel_x', 'vel_y'],
            target_name='future_lat',
            timestamp=datetime.now(timezone.utc),
            data_source='simulation'
        )
    
    elif data_type == "qos":
        # QoS預測訓練數據
        n_samples = 800
        
        # 特徵：信號強度、距離、負載等
        features = np.random.rand(n_samples, 8)
        features[:, 0] = -120 + features[:, 0] * 40  # 信號強度 (-120 to -80 dBm)
        features[:, 1] = features[:, 1] * 50 + 10    # 仰角 (10-60度)
        features[:, 2] = features[:, 2] * 1000 + 500 # 距離 (500-1500km)
        features[:, 3] = features[:, 3] * 0.8        # 負載 (0-0.8)
        features[:, 4] = features[:, 4] * 200        # 用戶數 (0-200)
        features[:, 5] = features[:, 5] * 1000       # 可用帶寬 (0-1000Mbps)
        features[:, 6] = features[:, 6] * 100        # 當前吞吐量 (0-100Mbps)
        features[:, 7] = features[:, 7] * 500 + 50   # 當前延遲 (50-550ms)
        
        # 目標：預測吞吐量（基於特徵的複雜關係）
        targets = (
            50 + (features[:, 0] + 120) * 2 +  # 信號強度影響
            features[:, 1] * 0.5 +              # 仰角影響
            (1 - features[:, 3]) * 30 +         # 負載影響（反向）
            features[:, 5] * 0.1 +              # 可用帶寬影響
            np.random.normal(0, 5, n_samples)   # 噪聲
        )
        targets = np.clip(targets, 0, 100)      # 限制在合理範圍
        
        return TrainingData(
            feature_data=features,
            target_data=targets,
            feature_names=['signal_strength', 'elevation', 'distance', 'load', 
                         'users', 'available_bw', 'current_throughput', 'current_latency'],
            target_name='predicted_throughput',
            timestamp=datetime.now(timezone.utc),
            data_source='simulation'
        )
    
    else:
        raise ValueError(f"未知的數據類型: {data_type}")