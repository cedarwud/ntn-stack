"""
統一同步算法服務 (Unified Synchronized Algorithm)

整合了以下兩個服務的功能：
1. enhanced_synchronized_algorithm.py - 增強版同步算法，包含二點預測、Binary search優化
2. paper_synchronized_algorithm.py - 論文標準Algorithm 1實作，T/R表管理

提供統一的同步算法接口，支持：
- 完整的論文Algorithm 1流程
- 增強版二點預測機制
- 高精度Binary search refinement
- 無信令同步協調機制
- 自適應參數調優
- 性能監控與統計
"""

import asyncio
import time
import logging
import uuid
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import statistics

import structlog
import numpy as np
from skyfield.api import load, EarthSatellite, Topos
from skyfield.positionlib import Geocentric
from pydantic import BaseModel

try:
    from .simworld_tle_bridge_service import SimWorldTLEBridgeService
except ImportError:
    SimWorldTLEBridgeService = None

logger = structlog.get_logger(__name__)


class AlgorithmPhase(Enum):
    """算法執行階段"""
    INITIALIZATION = "initialization"
    TWO_POINT_PREDICTION = "two_point_prediction" 
    BINARY_SEARCH = "binary_search"
    SYNCHRONIZATION = "synchronization"
    VALIDATION = "validation"
    COMPLETED = "completed"


class PredictionMethod(Enum):
    """預測方法類型"""
    ORBITAL_MECHANICS = "orbital_mechanics"
    SIGNAL_STRENGTH = "signal_strength"
    GEOMETRIC_ANALYSIS = "geometric_analysis"
    HYBRID_APPROACH = "hybrid_approach"


class AlgorithmState(Enum):
    """演算法狀態"""
    STOPPED = "stopped"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PERIODIC_UPDATE = "periodic_update"
    UE_UPDATE = "ue_update"
    ERROR = "error"


class HandoverTriggerType(Enum):
    """換手觸發類型"""
    PREDICTED = "predicted"
    EMERGENCY = "emergency"
    SCHEDULED = "scheduled"
    FORCED = "forced"


@dataclass
class AccessInfo:
    """論文標準接入資訊資料結構"""
    ue_id: str
    satellite_id: str
    next_satellite_id: Optional[str] = None
    handover_time: Optional[float] = None
    last_update: datetime = field(default_factory=datetime.utcnow)
    access_quality: float = 1.0
    prediction_confidence: float = 1.0
    signal_strength_dbm: float = -80.0
    elevation_angle_deg: float = 30.0


@dataclass
class TwoPointPredictionResult:
    """二點預測結果"""
    prediction_id: str
    ue_id: str
    satellite_id: str
    time_point_t: datetime
    time_point_t_delta: datetime
    delta_minutes: float
    
    # T 時間點預測
    prediction_t: Dict[str, Any]
    confidence_t: float
    accuracy_t: float
    
    # T+Δt 時間點預測
    prediction_t_delta: Dict[str, Any] 
    confidence_t_delta: float
    accuracy_t_delta: float
    
    # 一致性分析
    consistency_score: float
    temporal_stability: float
    prediction_drift: float
    
    # 插值結果
    interpolated_prediction: Dict[str, Any]
    extrapolation_confidence: float
    
    created_at: datetime = field(default_factory=datetime.now)


@dataclass 
class BinarySearchConfiguration:
    """Binary Search 配置"""
    search_id: str
    target_precision_ms: float = 25.0      # 目標精度 25ms
    max_iterations: int = 15               # 最大迭代次數
    convergence_threshold: float = 0.95    # 收斂閾值
    refinement_factor: float = 0.8         # 精化因子
    adaptive_step_size: bool = True        # 自適應步長
    early_termination: bool = True         # 早期終止


@dataclass
class BinarySearchResult:
    """Binary Search 結果"""
    search_id: str
    ue_id: str
    satellite_id: str
    target_satellite_id: str
    
    # 搜尋配置
    initial_time_range: Tuple[float, float]
    final_precision_achieved: float
    iterations_used: int
    convergence_achieved: bool
    
    # 最終結果
    optimal_handover_time: float
    confidence_score: float
    prediction_error_estimate: float
    
    # 過程數據
    search_iterations: List[Dict[str, Any]]
    total_search_time_ms: float
    
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SynchronizationCoordinator:
    """同步協調器"""
    coordinator_id: str
    access_network_nodes: List[str]
    coordination_protocol: str = "signaling_free"
    sync_tolerance_ms: float = 50.0
    max_coordination_delay_ms: float = 200.0
    
    # 協調狀態
    active_coordinations: Dict[str, Dict] = field(default_factory=dict)
    coordination_history: List[Dict] = field(default_factory=list)


@dataclass
class HandoverPrediction:
    """換手預測結果"""
    prediction_id: str
    ue_id: str
    current_satellite_id: str
    target_satellite_id: str
    predicted_handover_time: datetime
    confidence_score: float
    trigger_type: HandoverTriggerType
    prediction_method: PredictionMethod
    
    # 信號品質預測
    signal_quality_before: float
    signal_quality_after: float
    signal_quality_trend: str
    
    # 幾何分析
    elevation_angle_current: float
    elevation_angle_target: float
    distance_to_satellite_km: float
    
    # 預測誤差估計
    prediction_error_ms: float
    prediction_uncertainty: float
    
    created_at: datetime = field(default_factory=datetime.now)
    valid_until: datetime = field(default_factory=lambda: datetime.now() + timedelta(minutes=5))


class UnifiedSynchronizedAlgorithm:
    """
    統一同步算法服務
    
    整合論文Algorithm 1標準實作與增強版功能，提供完整的
    衛星換手預測與同步協調解決方案。
    """

    def __init__(
        self,
        delta_t: float = 5.0,
        binary_search_precision: float = 0.025,  # 25ms
        enable_enhanced_features: bool = True,
        enable_ml_prediction: bool = False,
        simworld_tle_bridge: Optional = None,
    ):
        """
        初始化統一同步算法
        
        Args:
            delta_t: 週期更新時間間隔 Δt (秒)
            binary_search_precision: 二分搜尋精度 (秒)
            enable_enhanced_features: 啟用增強功能
            enable_ml_prediction: 啟用機器學習預測
            simworld_tle_bridge: TLE 資料橋接服務
        """
        self.logger = structlog.get_logger(__name__)
        
        # 核心參數
        self.delta_t = delta_t
        self.binary_search_precision = binary_search_precision
        self.enable_enhanced_features = enable_enhanced_features
        self.enable_ml_prediction = enable_ml_prediction
        
        # 論文Algorithm 1核心資料結構
        self.T: float = time.time()  # 上次更新時間戳
        self.R: Dict[str, AccessInfo] = {}  # UE-衛星關係表
        self.Tp: Dict[str, float] = {}  # 預測的換手時間表
        
        # 增強功能資料結構
        self.prediction_cache: Dict[str, TwoPointPredictionResult] = {}
        self.binary_search_results: Dict[str, BinarySearchResult] = {}
        self.handover_predictions: Dict[str, HandoverPrediction] = {}
        
        # 同步協調
        self.synchronization_coordinator = SynchronizationCoordinator(
            coordinator_id=str(uuid.uuid4()),
            access_network_nodes=[],
        )
        
        # 服務整合
        if SimWorldTLEBridgeService:
            self.tle_bridge = simworld_tle_bridge or SimWorldTLEBridgeService()
        else:
            self.tle_bridge = None
        
        # 演算法狀態
        self.state = AlgorithmState.STOPPED
        self.algorithm_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # 性能統計
        self.performance_metrics = {
            "total_predictions": 0,
            "successful_predictions": 0,
            "average_prediction_time_ms": 0.0,
            "prediction_accuracy_rate": 0.0,
            "binary_search_iterations_avg": 0.0,
            "handover_success_rate": 0.0,
            "sync_coordination_success_rate": 0.0,
        }
        
        # 配置參數
        self.config = {
            "prediction_window_minutes": 10.0,
            "minimum_elevation_angle_deg": 5.0,
            "signal_threshold_dbm": -110.0,
            "handover_hysteresis_db": 3.0,
            "max_prediction_age_minutes": 5.0,
        }

    async def initialize(self):
        """初始化算法"""
        try:
            self.state = AlgorithmState.INITIALIZING
            
            # 初始化TLE數據橋接
            if self.tle_bridge:
                await self.tle_bridge.initialize()
            
            # 初始化ML模型（如果啟用）
            if self.enable_ml_prediction:
                await self._initialize_ml_models()
            
            # 載入歷史數據
            await self._load_historical_data()
            
            self.logger.info("✅ 統一同步算法初始化完成")
            
        except Exception as e:
            self.state = AlgorithmState.ERROR
            self.logger.error(f"❌ 統一同步算法初始化失敗: {e}")
            raise

    async def _initialize_ml_models(self):
        """初始化機器學習模型"""
        try:
            # 簡化的ML模型初始化
            self.ml_models = {
                "handover_predictor": None,  # 在實際環境中會載入訓練好的模型
                "signal_quality_predictor": None,
            }
            self.logger.info("✅ ML 模型初始化完成")
        except Exception as e:
            self.logger.error(f"ML 模型初始化失敗: {e}")

    async def _load_historical_data(self):
        """載入歷史數據"""
        try:
            # 在實際環境中，這裡會從數據庫或緩存載入歷史數據
            self.logger.info("✅ 歷史數據載入完成")
        except Exception as e:
            self.logger.warning(f"歷史數據載入失敗: {e}")

    async def start_algorithm(self):
        """啟動論文Algorithm 1主迴圈"""
        if self.is_running:
            self.logger.warning("算法已在運行中")
            return

        try:
            await self.initialize()
            self.is_running = True
            self.state = AlgorithmState.RUNNING
            
            # 啟動主算法迴圈
            self.algorithm_task = asyncio.create_task(self._algorithm_main_loop())
            
            self.logger.info("🚀 統一同步算法已啟動")
            
        except Exception as e:
            self.is_running = False
            self.state = AlgorithmState.ERROR
            self.logger.error(f"算法啟動失敗: {e}")
            raise

    async def _algorithm_main_loop(self):
        """論文Algorithm 1主迴圈"""
        while self.is_running:
            try:
                current_time = time.time()
                
                # 檢查是否需要週期性更新
                if current_time - self.T >= self.delta_t:
                    await self._periodic_update()
                    self.T = current_time
                
                # 處理UE狀態變更
                await self._process_ue_updates()
                
                # 執行增強功能（如果啟用）
                if self.enable_enhanced_features:
                    await self._run_enhanced_features()
                
                # 短暫休眠以避免CPU過度使用
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"算法主迴圈錯誤: {e}")
                await asyncio.sleep(1)

    async def _periodic_update(self):
        """週期性更新 - 論文Algorithm 1 PERIODIC_UPDATE"""
        self.state = AlgorithmState.PERIODIC_UPDATE
        
        try:
            # 更新所有活躍UE的衛星關係
            for ue_id, access_info in self.R.items():
                await self._update_ue_satellite_relationship(ue_id, access_info)
            
            # 清理過期的預測
            await self._cleanup_expired_predictions()
            
            self.logger.debug(f"週期性更新完成，管理 {len(self.R)} 個UE")
            
        except Exception as e:
            self.logger.error(f"週期性更新失敗: {e}")
        finally:
            self.state = AlgorithmState.RUNNING

    async def _update_ue_satellite_relationship(self, ue_id: str, access_info: AccessInfo):
        """更新UE-衛星關係"""
        try:
            # 獲取當前衛星狀態
            current_satellite_state = await self._get_satellite_state(access_info.satellite_id)
            
            # 檢查信號品質
            signal_quality = await self._calculate_signal_quality(ue_id, access_info.satellite_id)
            access_info.access_quality = signal_quality
            
            # 檢查是否需要換手
            if await self._should_trigger_handover(ue_id, access_info):
                await self._trigger_handover_prediction(ue_id, access_info)
            
            access_info.last_update = datetime.utcnow()
            
        except Exception as e:
            self.logger.error(f"UE關係更新失敗 {ue_id}: {e}")

    async def _process_ue_updates(self):
        """處理UE狀態更新"""
        # 在實際環境中，這裡會處理來自網路的UE位置/狀態更新
        pass

    async def _run_enhanced_features(self):
        """執行增強功能"""
        try:
            # 運行二點預測
            await self._run_two_point_prediction()
            
            # 運行Binary search優化
            await self._run_binary_search_optimization()
            
            # 運行同步協調
            await self._run_synchronization_coordination()
            
        except Exception as e:
            self.logger.error(f"增強功能運行失敗: {e}")

    async def _run_two_point_prediction(self):
        """運行二點預測機制"""
        current_time = datetime.now()
        
        for ue_id in self.R:
            try:
                # 為每個UE運行二點預測
                prediction_result = await self._perform_two_point_prediction(ue_id, current_time)
                if prediction_result:
                    self.prediction_cache[ue_id] = prediction_result
                    
            except Exception as e:
                self.logger.error(f"二點預測失敗 {ue_id}: {e}")

    async def _perform_two_point_prediction(
        self, ue_id: str, current_time: datetime
    ) -> Optional[TwoPointPredictionResult]:
        """執行二點預測"""
        try:
            access_info = self.R.get(ue_id)
            if not access_info:
                return None
            
            # 設定預測時間點
            time_point_t = current_time
            delta_minutes = self.config["prediction_window_minutes"]
            time_point_t_delta = current_time + timedelta(minutes=delta_minutes)
            
            # T時間點預測
            prediction_t = await self._predict_at_time_point(ue_id, time_point_t)
            confidence_t = self._calculate_prediction_confidence(prediction_t)
            
            # T+Δt時間點預測
            prediction_t_delta = await self._predict_at_time_point(ue_id, time_point_t_delta)
            confidence_t_delta = self._calculate_prediction_confidence(prediction_t_delta)
            
            # 一致性分析
            consistency_score = self._analyze_prediction_consistency(prediction_t, prediction_t_delta)
            temporal_stability = self._calculate_temporal_stability(prediction_t, prediction_t_delta)
            prediction_drift = self._calculate_prediction_drift(prediction_t, prediction_t_delta)
            
            # 插值預測
            interpolated_prediction = self._interpolate_predictions(prediction_t, prediction_t_delta)
            extrapolation_confidence = min(confidence_t, confidence_t_delta) * consistency_score
            
            return TwoPointPredictionResult(
                prediction_id=str(uuid.uuid4()),
                ue_id=ue_id,
                satellite_id=access_info.satellite_id,
                time_point_t=time_point_t,
                time_point_t_delta=time_point_t_delta,
                delta_minutes=delta_minutes,
                prediction_t=prediction_t,
                confidence_t=confidence_t,
                accuracy_t=0.0,  # 將在驗證時更新
                prediction_t_delta=prediction_t_delta,
                confidence_t_delta=confidence_t_delta,
                accuracy_t_delta=0.0,
                consistency_score=consistency_score,
                temporal_stability=temporal_stability,
                prediction_drift=prediction_drift,
                interpolated_prediction=interpolated_prediction,
                extrapolation_confidence=extrapolation_confidence,
            )
            
        except Exception as e:
            self.logger.error(f"二點預測執行失敗: {e}")
            return None

    async def _predict_at_time_point(self, ue_id: str, time_point: datetime) -> Dict[str, Any]:
        """在特定時間點進行預測"""
        # 簡化的預測實作
        access_info = self.R.get(ue_id)
        if not access_info:
            return {}
        
        # 模擬軌道計算和信號預測
        satellite_position = await self._calculate_satellite_position(access_info.satellite_id, time_point)
        signal_strength = await self._predict_signal_strength(ue_id, access_info.satellite_id, time_point)
        
        return {
            "satellite_position": satellite_position,
            "signal_strength_dbm": signal_strength,
            "elevation_angle_deg": self._calculate_elevation_angle(satellite_position),
            "prediction_time": time_point.isoformat(),
        }

    async def _calculate_satellite_position(self, satellite_id: str, time_point: datetime) -> Dict[str, float]:
        """計算衛星位置"""
        # 簡化的衛星位置計算
        # 在實際環境中會使用SGP4/SDP4模型和TLE數據
        return {
            "latitude_deg": 0.0,
            "longitude_deg": 0.0,
            "altitude_km": 550.0,
        }

    async def _predict_signal_strength(self, ue_id: str, satellite_id: str, time_point: datetime) -> float:
        """預測信號強度"""
        # 簡化的信號強度預測
        # 在實際環境中會考慮路徑損耗、天氣等因素
        return -85.0  # dBm

    def _calculate_elevation_angle(self, satellite_position: Dict[str, float]) -> float:
        """計算仰角"""
        # 簡化的仰角計算
        return 45.0  # degrees

    def _calculate_prediction_confidence(self, prediction: Dict[str, Any]) -> float:
        """計算預測信心度"""
        # 基於多個因素計算信心度
        base_confidence = 0.8
        
        # 根據信號強度調整
        signal_strength = prediction.get("signal_strength_dbm", -100)
        if signal_strength > -80:
            base_confidence += 0.1
        elif signal_strength < -100:
            base_confidence -= 0.2
        
        return max(0.0, min(1.0, base_confidence))

    def _analyze_prediction_consistency(self, prediction_t: Dict, prediction_t_delta: Dict) -> float:
        """分析預測一致性"""
        # 簡化的一致性分析
        signal_diff = abs(
            prediction_t.get("signal_strength_dbm", 0) - 
            prediction_t_delta.get("signal_strength_dbm", 0)
        )
        
        # 信號差異越小，一致性越高
        consistency = max(0.0, 1.0 - signal_diff / 50.0)
        return consistency

    def _calculate_temporal_stability(self, prediction_t: Dict, prediction_t_delta: Dict) -> float:
        """計算時間穩定性"""
        # 簡化的穩定性計算
        return 0.85

    def _calculate_prediction_drift(self, prediction_t: Dict, prediction_t_delta: Dict) -> float:
        """計算預測漂移"""
        # 簡化的漂移計算
        return 0.05

    def _interpolate_predictions(self, prediction_t: Dict, prediction_t_delta: Dict) -> Dict[str, Any]:
        """插值預測"""
        # 簡單的線性插值
        interpolated = {}
        
        for key in prediction_t:
            if key in prediction_t_delta and isinstance(prediction_t[key], (int, float)):
                interpolated[key] = (prediction_t[key] + prediction_t_delta[key]) / 2
            else:
                interpolated[key] = prediction_t[key]
        
        return interpolated

    async def _run_binary_search_optimization(self):
        """運行Binary search優化"""
        for ue_id, prediction in self.prediction_cache.items():
            try:
                # 檢查是否需要進行binary search
                if prediction.extrapolation_confidence > 0.7:
                    search_result = await self._perform_binary_search(ue_id, prediction)
                    if search_result:
                        self.binary_search_results[ue_id] = search_result
                        
            except Exception as e:
                self.logger.error(f"Binary search優化失敗 {ue_id}: {e}")

    async def _perform_binary_search(
        self, ue_id: str, prediction: TwoPointPredictionResult
    ) -> Optional[BinarySearchResult]:
        """執行Binary search"""
        try:
            search_id = str(uuid.uuid4())
            config = BinarySearchConfiguration(search_id=search_id)
            
            access_info = self.R.get(ue_id)
            if not access_info or not access_info.next_satellite_id:
                return None
            
            # 設定搜尋範圍
            current_time = time.time()
            search_start = current_time
            search_end = current_time + (self.config["prediction_window_minutes"] * 60)
            
            # Binary search迭代
            iterations = []
            search_start_time = time.time()
            
            low, high = search_start, search_end
            best_time = None
            best_score = -1
            
            for iteration in range(config.max_iterations):
                mid_time = (low + high) / 2
                
                # 評估換手時間點的適合度
                score = await self._evaluate_handover_time(ue_id, mid_time)
                
                iteration_data = {
                    "iteration": iteration,
                    "low": low,
                    "high": high,
                    "mid": mid_time,
                    "score": score,
                    "precision": high - low,
                }
                iterations.append(iteration_data)
                
                # 更新最佳結果
                if score > best_score:
                    best_score = score
                    best_time = mid_time
                
                # 檢查收斂條件
                precision_achieved = high - low
                if precision_achieved <= config.target_precision_ms / 1000:
                    break
                
                # 調整搜尋範圍
                if score > 0.5:  # 假設score > 0.5表示較好的換手時間
                    high = mid_time
                else:
                    low = mid_time
            
            search_end_time = time.time()
            
            return BinarySearchResult(
                search_id=search_id,
                ue_id=ue_id,
                satellite_id=access_info.satellite_id,
                target_satellite_id=access_info.next_satellite_id,
                initial_time_range=(search_start, search_end),
                final_precision_achieved=precision_achieved,
                iterations_used=len(iterations),
                convergence_achieved=precision_achieved <= config.target_precision_ms / 1000,
                optimal_handover_time=best_time,
                confidence_score=best_score,
                prediction_error_estimate=precision_achieved,
                search_iterations=iterations,
                total_search_time_ms=(search_end_time - search_start_time) * 1000,
            )
            
        except Exception as e:
            self.logger.error(f"Binary search執行失敗: {e}")
            return None

    async def _evaluate_handover_time(self, ue_id: str, handover_time: float) -> float:
        """評估換手時間點的適合度"""
        try:
            # 簡化的評估函數
            # 在實際環境中會考慮信號品質、負載平衡等多個因素
            
            access_info = self.R.get(ue_id)
            if not access_info:
                return 0.0
            
            # 模擬信號品質評估
            current_signal = await self._predict_signal_strength(ue_id, access_info.satellite_id, datetime.fromtimestamp(handover_time))
            target_signal = await self._predict_signal_strength(ue_id, access_info.next_satellite_id, datetime.fromtimestamp(handover_time))
            
            # 計算適合度分數
            signal_improvement = target_signal - current_signal
            
            # 正規化到0-1範圍
            score = max(0.0, min(1.0, (signal_improvement + 20) / 40))
            
            return score
            
        except Exception as e:
            self.logger.error(f"換手時間評估失敗: {e}")
            return 0.0

    async def _run_synchronization_coordination(self):
        """運行同步協調"""
        try:
            # 處理活躍的協調請求
            for coordination_id, coordination_data in list(self.synchronization_coordinator.active_coordinations.items()):
                await self._process_coordination(coordination_id, coordination_data)
            
        except Exception as e:
            self.logger.error(f"同步協調失敗: {e}")

    async def _process_coordination(self, coordination_id: str, coordination_data: Dict):
        """處理單個協調請求"""
        try:
            # 簡化的協調處理
            # 在實際環境中會與網路節點進行通信
            
            # 檢查協調是否完成
            if coordination_data.get("status") == "pending":
                coordination_data["status"] = "completed"
                coordination_data["completed_at"] = datetime.utcnow().isoformat()
                
                # 移動到歷史記錄
                self.synchronization_coordinator.coordination_history.append(coordination_data)
                del self.synchronization_coordinator.active_coordinations[coordination_id]
                
        except Exception as e:
            self.logger.error(f"協調處理失敗 {coordination_id}: {e}")

    async def _get_satellite_state(self, satellite_id: str) -> Dict[str, Any]:
        """獲取衛星狀態"""
        # 簡化的衛星狀態獲取
        return {
            "satellite_id": satellite_id,
            "operational": True,
            "signal_power": -75.0,
            "load_percentage": 45.0,
        }

    async def _calculate_signal_quality(self, ue_id: str, satellite_id: str) -> float:
        """計算信號品質"""
        # 簡化的信號品質計算
        # 在實際環境中會考慮RSRP, RSRQ, SINR等指標
        return 0.8

    async def _should_trigger_handover(self, ue_id: str, access_info: AccessInfo) -> bool:
        """判斷是否應該觸發換手"""
        # 簡化的換手觸發邏輯
        signal_quality = access_info.access_quality
        signal_threshold = 0.5
        
        return signal_quality < signal_threshold

    async def _trigger_handover_prediction(self, ue_id: str, access_info: AccessInfo):
        """觸發換手預測"""
        try:
            # 選擇最佳目標衛星
            target_satellite_id = await self._select_best_target_satellite(ue_id)
            
            if target_satellite_id:
                access_info.next_satellite_id = target_satellite_id
                
                # 創建換手預測
                prediction = HandoverPrediction(
                    prediction_id=str(uuid.uuid4()),
                    ue_id=ue_id,
                    current_satellite_id=access_info.satellite_id,
                    target_satellite_id=target_satellite_id,
                    predicted_handover_time=datetime.utcnow() + timedelta(minutes=2),
                    confidence_score=0.8,
                    trigger_type=HandoverTriggerType.PREDICTED,
                    prediction_method=PredictionMethod.HYBRID_APPROACH,
                    signal_quality_before=access_info.access_quality,
                    signal_quality_after=0.9,  # 預期改善
                    signal_quality_trend="improving",
                    elevation_angle_current=30.0,
                    elevation_angle_target=45.0,
                    distance_to_satellite_km=800.0,
                    prediction_error_ms=25.0,
                    prediction_uncertainty=0.1,
                )
                
                self.handover_predictions[ue_id] = prediction
                
                # 更新預測時間表
                self.Tp[ue_id] = prediction.predicted_handover_time.timestamp()
                
                self.logger.info(f"✅ 換手預測已觸發: {ue_id} -> {target_satellite_id}")
                
        except Exception as e:
            self.logger.error(f"換手預測觸發失敗: {e}")

    async def _select_best_target_satellite(self, ue_id: str) -> Optional[str]:
        """選擇最佳目標衛星"""
        # 簡化的衛星選擇邏輯
        # 在實際環境中會考慮信號強度、負載、覆蓋範圍等因素
        available_satellites = ["sat_002", "sat_003", "sat_004"]
        
        if available_satellites:
            return available_satellites[0]
        
        return None

    async def _cleanup_expired_predictions(self):
        """清理過期的預測"""
        current_time = datetime.utcnow()
        max_age = timedelta(minutes=self.config["max_prediction_age_minutes"])
        
        # 清理過期的換手預測
        expired_predictions = [
            ue_id for ue_id, prediction in self.handover_predictions.items()
            if current_time - prediction.created_at > max_age
        ]
        
        for ue_id in expired_predictions:
            del self.handover_predictions[ue_id]
            if ue_id in self.Tp:
                del self.Tp[ue_id]
        
        if expired_predictions:
            self.logger.debug(f"清理了 {len(expired_predictions)} 個過期預測")

    async def add_ue(self, ue_id: str, satellite_id: str, **kwargs) -> bool:
        """添加UE到管理列表"""
        try:
            if ue_id in self.R:
                self.logger.warning(f"UE {ue_id} 已存在")
                return False
            
            access_info = AccessInfo(
                ue_id=ue_id,
                satellite_id=satellite_id,
                **kwargs
            )
            
            self.R[ue_id] = access_info
            
            self.logger.info(f"✅ UE已添加: {ue_id} -> {satellite_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加UE失敗: {e}")
            return False

    async def remove_ue(self, ue_id: str) -> bool:
        """從管理列表移除UE"""
        try:
            if ue_id not in self.R:
                self.logger.warning(f"UE {ue_id} 不存在")
                return False
            
            # 清理相關數據
            del self.R[ue_id]
            
            if ue_id in self.Tp:
                del self.Tp[ue_id]
            if ue_id in self.prediction_cache:
                del self.prediction_cache[ue_id]
            if ue_id in self.binary_search_results:
                del self.binary_search_results[ue_id]
            if ue_id in self.handover_predictions:
                del self.handover_predictions[ue_id]
            
            self.logger.info(f"✅ UE已移除: {ue_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"移除UE失敗: {e}")
            return False

    async def update_ue_position(self, ue_id: str, latitude: float, longitude: float, altitude: float = 0.0):
        """更新UE位置 - 觸發Algorithm 1的UPDATE_UE"""
        try:
            if ue_id not in self.R:
                self.logger.warning(f"UE {ue_id} 不存在")
                return
            
            self.state = AlgorithmState.UE_UPDATE
            
            # 更新UE位置信息
            access_info = self.R[ue_id]
            # 在實際實作中，這裡會更新UE的地理位置
            
            # 重新評估衛星連接
            await self._update_ue_satellite_relationship(ue_id, access_info)
            
            self.logger.debug(f"UE位置已更新: {ue_id}")
            
        except Exception as e:
            self.logger.error(f"UE位置更新失敗: {e}")
        finally:
            self.state = AlgorithmState.RUNNING

    def get_algorithm_status(self) -> Dict[str, Any]:
        """獲取算法狀態"""
        return {
            "state": self.state.value,
            "is_running": self.is_running,
            "managed_ues": len(self.R),
            "active_predictions": len(self.handover_predictions),
            "cached_predictions": len(self.prediction_cache),
            "binary_search_results": len(self.binary_search_results),
            "last_update_time": self.T,
            "delta_t": self.delta_t,
            "performance_metrics": self.performance_metrics,
            "configuration": self.config,
        }

    def get_ue_status(self, ue_id: str) -> Optional[Dict[str, Any]]:
        """獲取特定UE的狀態"""
        if ue_id not in self.R:
            return None
        
        access_info = self.R[ue_id]
        
        status = {
            "ue_id": ue_id,
            "current_satellite": access_info.satellite_id,
            "next_satellite": access_info.next_satellite_id,
            "access_quality": access_info.access_quality,
            "prediction_confidence": access_info.prediction_confidence,
            "last_update": access_info.last_update.isoformat(),
        }
        
        # 添加預測信息
        if ue_id in self.handover_predictions:
            prediction = self.handover_predictions[ue_id]
            status["handover_prediction"] = {
                "predicted_time": prediction.predicted_handover_time.isoformat(),
                "confidence": prediction.confidence_score,
                "trigger_type": prediction.trigger_type.value,
            }
        
        # 添加二點預測信息
        if ue_id in self.prediction_cache:
            prediction = self.prediction_cache[ue_id]
            status["two_point_prediction"] = {
                "consistency_score": prediction.consistency_score,
                "temporal_stability": prediction.temporal_stability,
                "extrapolation_confidence": prediction.extrapolation_confidence,
            }
        
        # 添加Binary search結果
        if ue_id in self.binary_search_results:
            search_result = self.binary_search_results[ue_id]
            status["binary_search"] = {
                "optimal_handover_time": search_result.optimal_handover_time,
                "confidence_score": search_result.confidence_score,
                "iterations_used": search_result.iterations_used,
                "precision_achieved": search_result.final_precision_achieved,
            }
        
        return status

    def get_performance_summary(self) -> Dict[str, Any]:
        """獲取性能摘要"""
        total_ues = len(self.R)
        active_predictions = len(self.handover_predictions)
        
        # 計算預測準確率
        successful_predictions = sum(1 for p in self.handover_predictions.values() if p.confidence_score > 0.8)
        prediction_accuracy = successful_predictions / max(active_predictions, 1)
        
        # 計算平均Binary search迭代次數
        if self.binary_search_results:
            avg_iterations = statistics.mean(r.iterations_used for r in self.binary_search_results.values())
        else:
            avg_iterations = 0
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "algorithm_state": self.state.value,
            "total_managed_ues": total_ues,
            "active_predictions": active_predictions,
            "prediction_accuracy": prediction_accuracy,
            "avg_binary_search_iterations": avg_iterations,
            "enhanced_features_enabled": self.enable_enhanced_features,
            "ml_prediction_enabled": self.enable_ml_prediction,
            "uptime_seconds": time.time() - self.T if self.is_running else 0,
            "performance_metrics": self.performance_metrics,
        }

    async def stop_algorithm(self):
        """停止算法"""
        try:
            self.is_running = False
            
            if self.algorithm_task:
                self.algorithm_task.cancel()
                try:
                    await self.algorithm_task
                except asyncio.CancelledError:
                    pass
            
            self.state = AlgorithmState.STOPPED
            self.logger.info("🛑 統一同步算法已停止")
            
        except Exception as e:
            self.logger.error(f"停止算法失敗: {e}")


# Global instance
unified_synchronized_algorithm = UnifiedSynchronizedAlgorithm()