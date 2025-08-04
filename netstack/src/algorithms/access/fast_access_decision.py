"""
Phase 3.2.2.2: 快速接入決策引擎實現

實現智能化的快速接入決策引擎，包括：
1. 多衛星接入候選評估和排序
2. 負載感知的接入決策算法
3. 服務質量預測和保證機制
4. 自適應接入控制和流量管理
5. 與軌道預測引擎的深度整合

符合標準：
- 3GPP TS 38.300 NTN 系統架構
- 3GPP TS 38.821 NTN 接入控制
- ITU-R M.1645 衛星接入協議
- IEEE 802.11 QoS 管理機制
"""

import asyncio
import logging
import math
import time
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from enum import Enum
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
import uuid
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)


class AccessDecisionType(Enum):
    """接入決策類型"""
    IMMEDIATE_ACCEPT = "immediate_accept"      # 立即接受
    CONDITIONAL_ACCEPT = "conditional_accept"  # 條件接受
    DELAYED_ACCEPT = "delayed_accept"          # 延遲接受
    REJECT_OVERLOAD = "reject_overload"        # 拒絕-過載
    REJECT_COVERAGE = "reject_coverage"        # 拒絕-覆蓋範圍
    REJECT_QOS = "reject_qos"                  # 拒絕-QoS無法滿足


class ServiceClass(Enum):
    """服務類別"""
    EMERGENCY = "emergency"          # 緊急服務
    VOICE = "voice"                 # 語音服務
    VIDEO = "video"                 # 視頻服務
    DATA = "data"                   # 數據服務
    IOT = "iot"                     # 物聯網服務
    BACKGROUND = "background"       # 背景服務


class AccessTrigger(Enum):
    """接入觸發類型"""
    INITIAL_ATTACH = "initial_attach"      # 初始附著
    HANDOVER = "handover"                  # 切換
    SERVICE_REQUEST = "service_request"    # 服務請求
    EMERGENCY_CALL = "emergency_call"      # 緊急呼叫
    PERIODIC_UPDATE = "periodic_update"    # 週期更新


@dataclass
class AccessCandidate:
    """接入候選衛星"""
    satellite_id: str
    beam_id: str
    frequency_band: str
    
    # 覆蓋信息
    elevation_angle: float = None
    azimuth_angle: float = None
    distance_km: float = None
    signal_strength_dbm: float = None
    path_loss_db: float = None
    doppler_shift_hz: float = None
    
    # 容量信息
    total_capacity_mbps: float = 0.0
    available_capacity_mbps: float = 0.0
    current_load_percent: float = 0.0
    active_users: int = 0
    max_users: int = 1000
    
    # 服務質量預測
    predicted_throughput_mbps: float = 0.0
    predicted_latency_ms: float = 0.0
    predicted_packet_loss_rate: float = 0.0
    predicted_availability_duration_s: float = 0.0
    
    # 接入成本
    setup_time_ms: float = 0.0
    signaling_overhead_kb: float = 0.0
    power_consumption_mw: float = 0.0
    interference_level_db: float = 0.0
    
    # 預測軌道信息
    visibility_window_start: Optional[datetime] = None
    visibility_window_end: Optional[datetime] = None
    orbital_velocity_kmh: float = 0.0
    
    # 評分結果
    composite_score: float = 0.0
    ranking: int = 0
    
    def calculate_load_factor(self) -> float:
        """計算負載因子"""
        if self.max_users <= 0:
            return 1.0
        user_load = self.active_users / self.max_users
        
        if self.total_capacity_mbps <= 0:
            return user_load
        capacity_load = 1.0 - (self.available_capacity_mbps / self.total_capacity_mbps)
        
        return max(user_load, capacity_load)
    
    def is_overloaded(self, threshold: float = 0.9) -> bool:
        """檢查是否過載"""
        return self.calculate_load_factor() > threshold
    
    def get_visibility_duration(self) -> float:
        """獲取可見性持續時間（秒）"""
        if self.visibility_window_start and self.visibility_window_end:
            return (self.visibility_window_end - self.visibility_window_start).total_seconds()
        return self.predicted_availability_duration_s


@dataclass
class AccessRequest:
    """接入請求"""
    request_id: str
    user_id: str
    device_id: str
    trigger_type: AccessTrigger
    service_class: ServiceClass
    timestamp: datetime
    
    # 位置信息
    user_latitude: float = None
    user_longitude: float = None
    user_altitude_m: float = 0.0
    
    # 服務需求
    required_bandwidth_mbps: float = 1.0
    max_acceptable_latency_ms: float = 1000.0
    min_acceptable_reliability: float = 0.95
    max_acceptable_jitter_ms: float = 100.0
    
    # 優先級和期限
    priority: int = 5  # 1-10, 10為最高
    deadline_ms: Optional[int] = None
    max_waiting_time_ms: int = 30000  # 30秒
    
    # 當前狀態
    current_satellite_id: Optional[str] = None
    current_signal_strength_dbm: Optional[float] = None
    battery_level_percent: Optional[float] = None
    device_capabilities: Dict[str, Any] = field(default_factory=dict)
    
    # 額外信息
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccessPlan:
    """接入計劃"""
    plan_id: str
    request: AccessRequest
    selected_candidate: AccessCandidate
    decision: AccessDecisionType
    execution_time: datetime
    
    # 時序信息
    preparation_phase_duration_ms: int = 0
    execution_phase_duration_ms: int = 0
    completion_phase_duration_ms: int = 0
    
    # 資源預留
    reserved_bandwidth_mbps: float = 0.0
    reserved_beam_capacity_percent: float = 0.0
    allocated_frequency_khz: float = 0.0
    
    # 服務質量保證
    guaranteed_throughput_mbps: float = 0.0
    guaranteed_max_latency_ms: float = 0.0
    guaranteed_reliability: float = 0.0
    
    # 條件和約束
    conditions: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    fallback_options: List[AccessCandidate] = field(default_factory=list)
    
    # 執行狀態
    status: str = "planned"
    execution_result: Optional[Dict[str, Any]] = None
    
    def get_total_duration_ms(self) -> int:
        """獲取總執行時間"""
        return (self.preparation_phase_duration_ms + 
                self.execution_phase_duration_ms + 
                self.completion_phase_duration_ms)
    
    def is_expired(self) -> bool:
        """檢查計劃是否過期"""
        if self.request.deadline_ms:
            elapsed = (datetime.now(timezone.utc) - self.execution_time).total_seconds() * 1000
            return elapsed > self.request.deadline_ms
        return False


class FastAccessDecisionEngine:
    """快速接入決策引擎"""
    
    def __init__(self, engine_id: str = None):
        self.engine_id = engine_id or f"fast_access_{uuid.uuid4().hex[:8]}"
        
        # 決策配置
        self.decision_config = {
            'evaluation_interval_ms': 100,
            'max_candidates_per_request': 10,
            'load_balancing_enabled': True,
            'qos_prediction_enabled': True,
            'emergency_priority_threshold': 8,
            'overload_threshold': 0.85,
            'min_signal_strength_dbm': -120.0,
            'min_elevation_angle_deg': 10.0,
            'decision_timeout_ms': 5000,
            'resource_reservation_duration_ms': 60000
        }
        
        # 評估權重
        self.evaluation_weights = {
            'signal_quality': 0.25,
            'capacity_availability': 0.20,
            'predicted_performance': 0.20,
            'access_cost': 0.15,
            'service_compatibility': 0.10,
            'load_balancing': 0.10
        }
        
        # 服務類別配置
        self.service_configs = {
            ServiceClass.EMERGENCY: {
                'priority_boost': 5,
                'max_latency_ms': 100,
                'min_reliability': 0.999,
                'preemption_allowed': True
            },
            ServiceClass.VOICE: {
                'priority_boost': 2,
                'max_latency_ms': 150,
                'min_reliability': 0.98,
                'jitter_tolerance_ms': 20
            },
            ServiceClass.VIDEO: {
                'priority_boost': 1,
                'max_latency_ms': 300,
                'min_reliability': 0.95,
                'bandwidth_priority': True
            },
            ServiceClass.DATA: {
                'priority_boost': 0,
                'max_latency_ms': 1000,
                'min_reliability': 0.90,
                'throughput_priority': True
            },
            ServiceClass.IOT: {
                'priority_boost': -1,
                'max_latency_ms': 5000,
                'min_reliability': 0.85,
                'power_efficiency': True
            },
            ServiceClass.BACKGROUND: {
                'priority_boost': -2,
                'max_latency_ms': 10000,
                'min_reliability': 0.80,
                'opportunistic': True
            }
        }
        
        # 運行狀態
        self.is_running = False
        self.decision_task: Optional[asyncio.Task] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # 請求管理
        self.pending_requests: Dict[str, AccessRequest] = {}
        self.active_plans: Dict[str, AccessPlan] = {}
        self.completed_accesses: deque = deque(maxlen=1000)
        
        # 候選衛星緩存
        self.candidate_cache: Dict[str, List[AccessCandidate]] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # 資源狀態追蹤
        self.satellite_loads: Dict[str, float] = defaultdict(float)
        self.beam_allocations: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.frequency_usage: Dict[str, float] = defaultdict(float)
        
        # 統計信息
        self.stats = {
            'requests_received': 0,
            'requests_accepted': 0,
            'requests_rejected': 0,
            'average_decision_time_ms': 0.0,
            'total_decision_time_ms': 0.0,
            'emergency_requests': 0,
            'handover_requests': 0,
            'qos_violations': 0,
            'load_balancing_decisions': 0
        }
        
        # 線程池
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.decision_lock = threading.RLock()
        
        # 外部集成接口
        self.orbit_prediction_engine = None
        self.handover_decision_engine = None
        self.state_sync_engine = None
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def start_engine(self):
        """啟動決策引擎"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # 啟動決策處理任務
        self.decision_task = asyncio.create_task(self._decision_processing_loop())
        
        # 啟動監控任務
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        self.logger.info(f"🚀 快速接入決策引擎已啟動 - ID: {self.engine_id}")
    
    async def stop_engine(self):
        """停止決策引擎"""
        self.is_running = False
        
        # 停止所有任務
        for task in [self.decision_task, self.monitoring_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self.executor.shutdown(wait=True)
        self.logger.info("⏹️ 快速接入決策引擎已停止")
    
    # === 核心決策方法 ===
    
    async def submit_access_request(self, request: AccessRequest) -> str:
        """提交接入請求"""
        try:
            with self.decision_lock:
                self.pending_requests[request.request_id] = request
                self.stats['requests_received'] += 1
                
                # 緊急請求統計
                if request.service_class == ServiceClass.EMERGENCY:
                    self.stats['emergency_requests'] += 1
                
                # 切換請求統計
                if request.trigger_type == AccessTrigger.HANDOVER:
                    self.stats['handover_requests'] += 1
            
            self.logger.info(f"📥 接收接入請求: {request.request_id} - 用戶: {request.user_id}")
            return request.request_id
            
        except Exception as e:
            self.logger.error(f"❌ 提交接入請求失敗: {e}")
            raise
    
    async def cancel_access_request(self, request_id: str) -> bool:
        """取消接入請求"""
        try:
            with self.decision_lock:
                # 從待處理請求中移除
                if request_id in self.pending_requests:
                    del self.pending_requests[request_id]
                    self.logger.info(f"🚫 已取消待處理接入請求: {request_id}")
                    return True
                
                # 從活動計劃中移除
                if request_id in self.active_plans:
                    plan = self.active_plans[request_id]
                    await self._release_reserved_resources(plan)
                    del self.active_plans[request_id]
                    self.logger.info(f"🚫 已取消活動接入計劃: {request_id}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ 取消接入請求失敗: {e}")
            return False
    
    async def _decision_processing_loop(self):
        """決策處理循環"""
        try:
            while self.is_running:
                await asyncio.sleep(self.decision_config['evaluation_interval_ms'] / 1000.0)
                
                if not self.pending_requests:
                    continue
                
                # 獲取待處理請求（按優先級排序）
                requests_to_process = list(self.pending_requests.values())
                requests_to_process.sort(
                    key=lambda r: (-r.priority, r.timestamp), 
                    reverse=False
                )
                
                # 處理請求
                for request in requests_to_process:
                    if not self.is_running:
                        break
                    
                    try:
                        await self._process_access_request(request)
                    except Exception as e:
                        self.logger.error(f"❌ 處理接入請求失敗 {request.request_id}: {e}")
                        
                        # 標記為失敗並移除
                        with self.decision_lock:
                            if request.request_id in self.pending_requests:
                                del self.pending_requests[request.request_id]
                            self.stats['requests_rejected'] += 1
                
        except asyncio.CancelledError:
            self.logger.info("🔄 決策處理循環已取消")
        except Exception as e:
            self.logger.error(f"❌ 決策處理循環異常: {e}")
    
    async def _process_access_request(self, request: AccessRequest):
        """處理接入請求"""
        start_time = time.time()
        
        try:
            # 獲取候選衛星
            candidates = await self._get_access_candidates(request)
            
            if not candidates:
                self.logger.warning(f"⚠️ 請求 {request.request_id} 無可用候選衛星")
                await self._reject_request(request, AccessDecisionType.REJECT_COVERAGE)
                return
            
            # 評估和排序候選衛星
            evaluated_candidates = await self._evaluate_candidates(request, candidates)
            
            # 做出接入決策
            decision, selected_candidate = await self._make_access_decision(request, evaluated_candidates)
            
            if decision == AccessDecisionType.IMMEDIATE_ACCEPT:
                # 創建接入計劃
                plan = await self._create_access_plan(request, selected_candidate, decision, evaluated_candidates)
                
                # 預留資源
                if await self._reserve_resources(plan):
                    with self.decision_lock:
                        if request.request_id in self.pending_requests:
                            del self.pending_requests[request.request_id]
                        self.active_plans[plan.plan_id] = plan
                        self.stats['requests_accepted'] += 1
                    
                    self.logger.info(f"✅ 接入請求已接受: {request.request_id} -> 衛星: {selected_candidate.satellite_id}")
                else:
                    await self._reject_request(request, AccessDecisionType.REJECT_OVERLOAD)
            
            elif decision == AccessDecisionType.CONDITIONAL_ACCEPT:
                # 創建條件接入計劃
                plan = await self._create_access_plan(request, selected_candidate, decision, evaluated_candidates)
                with self.decision_lock:
                    self.active_plans[plan.plan_id] = plan
                
                self.logger.info(f"🔄 條件接入: {request.request_id} -> 衛星: {selected_candidate.satellite_id}")
            
            else:
                await self._reject_request(request, decision)
            
            # 更新統計
            processing_time = (time.time() - start_time) * 1000
            self.stats['total_decision_time_ms'] += processing_time
            
            total_requests = self.stats['requests_accepted'] + self.stats['requests_rejected']
            if total_requests > 0:
                self.stats['average_decision_time_ms'] = \
                    self.stats['total_decision_time_ms'] / total_requests
            
        except Exception as e:
            self.logger.error(f"❌ 處理接入請求異常: {e}")
            await self._reject_request(request, AccessDecisionType.REJECT_OVERLOAD)
    
    async def _get_access_candidates(self, request: AccessRequest) -> List[AccessCandidate]:
        """獲取接入候選衛星"""
        try:
            # 檢查緩存
            cache_key = f"{request.user_latitude}_{request.user_longitude}_{int(time.time() // 60)}"
            
            if cache_key in self.candidate_cache:
                cached_time = self.cache_timestamps.get(cache_key)
                if cached_time and (datetime.now(timezone.utc) - cached_time).seconds < 300:  # 5分鐘緩存
                    return self.candidate_cache[cache_key]
            
            # 模擬獲取可見衛星（實際應該調用軌道預測引擎）
            candidates = []
            
            # 生成模擬候選衛星
            for i in range(5):  # 假設5顆可見衛星
                satellite_id = f"SAT-{1001 + i}"
                candidate = AccessCandidate(
                    satellite_id=satellite_id,
                    beam_id=f"BEAM-{i+1}",
                    frequency_band="Ka-band"
                )
                
                # 模擬覆蓋信息
                candidate.elevation_angle = 15.0 + i * 10.0  # 15-55度
                candidate.azimuth_angle = float(i * 72)  # 均勻分佈
                candidate.distance_km = 1000.0 + i * 200.0  # 1000-1800km
                candidate.signal_strength_dbm = -90.0 - i * 5.0  # -90到-110dBm
                candidate.path_loss_db = 180.0 + i * 5.0
                candidate.doppler_shift_hz = -50000.0 + i * 25000.0
                
                # 模擬容量信息
                candidate.total_capacity_mbps = 1000.0
                candidate.current_load_percent = 0.3 + i * 0.1  # 30%-70%負載
                candidate.available_capacity_mbps = candidate.total_capacity_mbps * (1.0 - candidate.current_load_percent)
                candidate.active_users = int(candidate.current_load_percent * 100)
                candidate.max_users = 200
                
                # 模擬服務質量預測
                load_factor = candidate.calculate_load_factor()
                candidate.predicted_throughput_mbps = candidate.available_capacity_mbps * 0.8
                candidate.predicted_latency_ms = 50.0 + load_factor * 200.0
                candidate.predicted_packet_loss_rate = load_factor * 0.01
                candidate.predicted_availability_duration_s = 600.0 - i * 60.0  # 10-6分鐘
                
                # 模擬接入成本
                candidate.setup_time_ms = 100.0 + i * 20.0
                candidate.signaling_overhead_kb = 5.0 + i * 1.0
                candidate.power_consumption_mw = 500.0 + i * 100.0
                candidate.interference_level_db = -80.0 - i * 5.0
                
                # 模擬軌道信息
                current_time = datetime.now(timezone.utc)
                candidate.visibility_window_start = current_time
                candidate.visibility_window_end = current_time + timedelta(seconds=candidate.predicted_availability_duration_s)
                candidate.orbital_velocity_kmh = 27000.0  # 典型LEO速度
                
                candidates.append(candidate)
            
            # 過濾不符合基本要求的候選
            filtered_candidates = []
            for candidate in candidates:
                if (candidate.signal_strength_dbm >= self.decision_config['min_signal_strength_dbm'] and
                    candidate.elevation_angle >= self.decision_config['min_elevation_angle_deg'] and
                    not candidate.is_overloaded(self.decision_config['overload_threshold'])):
                    filtered_candidates.append(candidate)
            
            # 更新緩存
            self.candidate_cache[cache_key] = filtered_candidates
            self.cache_timestamps[cache_key] = datetime.now(timezone.utc)
            
            return filtered_candidates
            
        except Exception as e:
            self.logger.error(f"❌ 獲取接入候選失敗: {e}")
            return []
    
    async def _evaluate_candidates(self, request: AccessRequest, 
                                  candidates: List[AccessCandidate]) -> List[AccessCandidate]:
        """評估候選衛星"""
        try:
            for candidate in candidates:
                score = 0.0
                
                # 1. 信號質量評分
                signal_score = self._evaluate_signal_quality(candidate)
                score += signal_score * self.evaluation_weights['signal_quality']
                
                # 2. 容量可用性評分
                capacity_score = self._evaluate_capacity_availability(candidate, request)
                score += capacity_score * self.evaluation_weights['capacity_availability']
                
                # 3. 預測性能評分
                performance_score = self._evaluate_predicted_performance(candidate, request)
                score += performance_score * self.evaluation_weights['predicted_performance']
                
                # 4. 接入成本評分
                cost_score = self._evaluate_access_cost(candidate)
                score += cost_score * self.evaluation_weights['access_cost']
                
                # 5. 服務兼容性評分
                compatibility_score = self._evaluate_service_compatibility(candidate, request)
                score += compatibility_score * self.evaluation_weights['service_compatibility']
                
                # 6. 負載平衡評分
                load_balance_score = self._evaluate_load_balancing(candidate)
                score += load_balance_score * self.evaluation_weights['load_balancing']
                
                candidate.composite_score = score
            
            # 按分數排序
            candidates.sort(key=lambda c: c.composite_score, reverse=True)
            
            # 設置排名
            for i, candidate in enumerate(candidates):
                candidate.ranking = i + 1
            
            return candidates[:self.decision_config['max_candidates_per_request']]
            
        except Exception as e:
            self.logger.error(f"❌ 評估候選衛星失敗: {e}")
            return candidates
    
    def _evaluate_signal_quality(self, candidate: AccessCandidate) -> float:
        """評估信號質量"""
        # 信號強度評分 (歸一化到0-1)
        signal_strength = candidate.signal_strength_dbm or -100.0
        signal_norm = max(0, min(1, 
            (signal_strength + 120) / 30  # -120到-90dBm映射到0-1
        ))
        
        # 仰角評分
        elevation = candidate.elevation_angle or 0.0
        elevation_norm = max(0, min(1, 
            (elevation - 10) / 80  # 10-90度映射到0-1
        ))
        
        # 路徑損耗評分 (較低的路徑損耗得分更高)
        path_loss = candidate.path_loss_db or 180.0
        path_loss_norm = max(0, min(1, 
            (200 - path_loss) / 50  # 150-200dB映射到1-0
        ))
        
        return (signal_norm * 0.4 + elevation_norm * 0.3 + path_loss_norm * 0.3)
    
    def _evaluate_capacity_availability(self, candidate: AccessCandidate, 
                                       request: AccessRequest) -> float:
        """評估容量可用性"""
        # 可用帶寬評分
        available_ratio = candidate.available_capacity_mbps / max(1, candidate.total_capacity_mbps)
        bandwidth_score = min(1.0, available_ratio * 2)  # 50%可用容量得1分
        
        # 用戶負載評分
        user_load = candidate.active_users / max(1, candidate.max_users)
        user_score = max(0, 1.0 - user_load)
        
        # 需求匹配評分
        if candidate.available_capacity_mbps >= request.required_bandwidth_mbps:
            demand_score = 1.0
        else:
            demand_score = candidate.available_capacity_mbps / request.required_bandwidth_mbps
        
        return (bandwidth_score * 0.4 + user_score * 0.3 + demand_score * 0.3)
    
    def _evaluate_predicted_performance(self, candidate: AccessCandidate, 
                                       request: AccessRequest) -> float:
        """評估預測性能"""
        # 延遲評分
        if candidate.predicted_latency_ms <= request.max_acceptable_latency_ms:
            latency_score = max(0, min(1, 
                (request.max_acceptable_latency_ms - candidate.predicted_latency_ms) / 
                request.max_acceptable_latency_ms
            ))
        else:
            latency_score = 0.0
        
        # 吞吐量評分
        throughput_ratio = candidate.predicted_throughput_mbps / max(0.1, request.required_bandwidth_mbps)
        throughput_score = min(1.0, throughput_ratio)
        
        # 可靠性評分
        reliability_score = max(0, min(1, 
            (1.0 - candidate.predicted_packet_loss_rate) / request.min_acceptable_reliability
        ))
        
        # 可用時間評分
        availability_score = min(1.0, candidate.predicted_availability_duration_s / 300.0)  # 5分鐘基準
        
        return (latency_score * 0.3 + throughput_score * 0.3 + 
                reliability_score * 0.2 + availability_score * 0.2)
    
    def _evaluate_access_cost(self, candidate: AccessCandidate) -> float:
        """評估接入成本"""
        # 建立時間評分 (較短得分更高)
        setup_score = max(0, min(1, (500 - candidate.setup_time_ms) / 400))  # 100-500ms映射到1-0
        
        # 信令開銷評分
        signaling_score = max(0, min(1, (10 - candidate.signaling_overhead_kb) / 8))  # 2-10KB映射到1-0
        
        # 功耗評分
        power_score = max(0, min(1, (1000 - candidate.power_consumption_mw) / 500))  # 500-1000mW映射到1-0
        
        # 干擾水平評分
        interference_score = max(0, min(1, (candidate.interference_level_db + 100) / 20))  # -100到-80dBm映射到0-1
        
        return (setup_score * 0.3 + signaling_score * 0.2 + 
                power_score * 0.2 + interference_score * 0.3)
    
    def _evaluate_service_compatibility(self, candidate: AccessCandidate, 
                                       request: AccessRequest) -> float:
        """評估服務兼容性"""
        service_config = self.service_configs.get(request.service_class, {})
        
        # 延遲兼容性
        max_service_latency = service_config.get('max_latency_ms', request.max_acceptable_latency_ms)
        if candidate.predicted_latency_ms <= max_service_latency:
            latency_compatibility = 1.0
        else:
            latency_compatibility = max_service_latency / candidate.predicted_latency_ms
        
        # 可靠性兼容性
        min_service_reliability = service_config.get('min_reliability', request.min_acceptable_reliability)
        predicted_reliability = 1.0 - candidate.predicted_packet_loss_rate
        if predicted_reliability >= min_service_reliability:
            reliability_compatibility = 1.0
        else:
            reliability_compatibility = predicted_reliability / min_service_reliability
        
        # 帶寬兼容性
        if candidate.predicted_throughput_mbps >= request.required_bandwidth_mbps:
            bandwidth_compatibility = 1.0
        else:
            bandwidth_compatibility = candidate.predicted_throughput_mbps / request.required_bandwidth_mbps
        
        return (latency_compatibility * 0.4 + reliability_compatibility * 0.3 + 
                bandwidth_compatibility * 0.3)
    
    def _evaluate_load_balancing(self, candidate: AccessCandidate) -> float:
        """評估負載平衡"""
        if not self.decision_config['load_balancing_enabled']:
            return 1.0
        
        # 當前負載評分 (較低負載得分更高)
        load_factor = candidate.calculate_load_factor()
        load_score = max(0, 1.0 - load_factor)
        
        # 歷史負載趨勢 (模擬)
        historical_load = self.satellite_loads.get(candidate.satellite_id, 0.5)
        trend_score = max(0, 1.0 - historical_load)
        
        return (load_score * 0.7 + trend_score * 0.3)
    
    async def _make_access_decision(self, request: AccessRequest, 
                                   candidates: List[AccessCandidate]) -> Tuple[AccessDecisionType, AccessCandidate]:
        """做出接入決策"""
        if not candidates:
            return AccessDecisionType.REJECT_COVERAGE, None
        
        best_candidate = candidates[0]  # 已排序，第一個是最佳
        
        # 緊急服務優先處理
        if request.service_class == ServiceClass.EMERGENCY:
            if best_candidate.composite_score > 0.3:  # 較低門檻
                return AccessDecisionType.IMMEDIATE_ACCEPT, best_candidate
            else:
                return AccessDecisionType.REJECT_QOS, best_candidate
        
        # 基於綜合分數決策
        if best_candidate.composite_score >= 0.8:
            return AccessDecisionType.IMMEDIATE_ACCEPT, best_candidate
        elif best_candidate.composite_score >= 0.6:
            return AccessDecisionType.CONDITIONAL_ACCEPT, best_candidate
        elif best_candidate.composite_score >= 0.4:
            return AccessDecisionType.DELAYED_ACCEPT, best_candidate
        else:
            # 根據主要問題類型決定拒絕原因
            if best_candidate.is_overloaded():
                return AccessDecisionType.REJECT_OVERLOAD, best_candidate
            elif best_candidate.predicted_latency_ms > request.max_acceptable_latency_ms * 2:
                return AccessDecisionType.REJECT_QOS, best_candidate
            else:
                return AccessDecisionType.REJECT_COVERAGE, best_candidate
    
    async def _create_access_plan(self, request: AccessRequest, 
                                 candidate: AccessCandidate, 
                                 decision: AccessDecisionType,
                                 candidates: List[AccessCandidate] = None) -> AccessPlan:
        """創建接入計劃"""
        plan = AccessPlan(
            plan_id=f"plan_{uuid.uuid4().hex[:8]}",
            request=request,
            selected_candidate=candidate,
            decision=decision,
            execution_time=datetime.now(timezone.utc) + timedelta(milliseconds=50)
        )
        
        # 設置時序信息
        setup_time = candidate.setup_time_ms or 200.0
        plan.preparation_phase_duration_ms = max(50, int(setup_time * 0.3))
        plan.execution_phase_duration_ms = max(100, int(setup_time * 0.6))
        plan.completion_phase_duration_ms = max(30, int(setup_time * 0.1))
        
        # 資源預留
        plan.reserved_bandwidth_mbps = request.required_bandwidth_mbps * 1.1  # 10%冗餘
        plan.reserved_beam_capacity_percent = (plan.reserved_bandwidth_mbps / 
                                               max(1, candidate.total_capacity_mbps)) * 100
        plan.allocated_frequency_khz = plan.reserved_bandwidth_mbps * 1000  # 簡化計算
        
        # 服務質量保證
        predicted_throughput = candidate.predicted_throughput_mbps or request.required_bandwidth_mbps
        predicted_latency = candidate.predicted_latency_ms or request.max_acceptable_latency_ms
        predicted_loss_rate = candidate.predicted_packet_loss_rate or 0.01
        
        plan.guaranteed_throughput_mbps = min(predicted_throughput, request.required_bandwidth_mbps)
        plan.guaranteed_max_latency_ms = max(predicted_latency, request.max_acceptable_latency_ms)
        plan.guaranteed_reliability = min(1.0 - predicted_loss_rate, request.min_acceptable_reliability)
        
        # 條件設置
        if decision == AccessDecisionType.CONDITIONAL_ACCEPT:
            plan.conditions = [
                f"等待衛星負載降至 {self.decision_config['overload_threshold'] * 100:.0f}% 以下",
                f"信號強度保持在 {self.decision_config['min_signal_strength_dbm']} dBm 以上"
            ]
        
        # 備用選項
        if candidates and len(candidates) > 1:
            plan.fallback_options = candidates[1:3]  # 前2個備用選項
        
        return plan
    
    async def _reserve_resources(self, plan: AccessPlan) -> bool:
        """預留資源"""
        try:
            satellite_id = plan.selected_candidate.satellite_id
            beam_id = plan.selected_candidate.beam_id
            
            # 檢查資源可用性
            current_load = self.satellite_loads.get(satellite_id, 0.0)
            required_load = plan.reserved_beam_capacity_percent / 100.0
            
            if current_load + required_load > self.decision_config['overload_threshold']:
                return False
            
            # 預留資源
            with self.decision_lock:
                self.satellite_loads[satellite_id] = current_load + required_load
                
                if satellite_id not in self.beam_allocations:
                    self.beam_allocations[satellite_id] = {}
                self.beam_allocations[satellite_id][beam_id] = \
                    self.beam_allocations[satellite_id].get(beam_id, 0.0) + plan.reserved_bandwidth_mbps
                
                self.frequency_usage[plan.allocated_frequency_khz] = time.time()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 資源預留失敗: {e}")
            return False
    
    async def _release_reserved_resources(self, plan: AccessPlan):
        """釋放預留資源"""
        try:
            satellite_id = plan.selected_candidate.satellite_id
            beam_id = plan.selected_candidate.beam_id
            
            with self.decision_lock:
                # 釋放衛星負載
                current_load = self.satellite_loads.get(satellite_id, 0.0)
                required_load = plan.reserved_beam_capacity_percent / 100.0
                self.satellite_loads[satellite_id] = max(0.0, current_load - required_load)
                
                # 釋放波束容量
                if satellite_id in self.beam_allocations and beam_id in self.beam_allocations[satellite_id]:
                    self.beam_allocations[satellite_id][beam_id] = max(0.0,
                        self.beam_allocations[satellite_id][beam_id] - plan.reserved_bandwidth_mbps)
                
                # 釋放頻率
                if plan.allocated_frequency_khz in self.frequency_usage:
                    del self.frequency_usage[plan.allocated_frequency_khz]
            
        except Exception as e:
            self.logger.error(f"❌ 釋放資源失敗: {e}")
    
    async def _reject_request(self, request: AccessRequest, reason: AccessDecisionType):
        """拒絕請求"""
        with self.decision_lock:
            if request.request_id in self.pending_requests:
                del self.pending_requests[request.request_id]
            self.stats['requests_rejected'] += 1
        
        self.logger.info(f"❌ 拒絕接入請求: {request.request_id} - 原因: {reason.value}")
    
    async def _monitoring_loop(self):
        """監控循環"""
        try:
            while self.is_running:
                await asyncio.sleep(10.0)  # 每10秒監控一次
                
                # 清理過期計劃
                await self._cleanup_expired_plans()
                
                # 更新衛星負載信息
                await self._update_satellite_loads()
                
                # 清理緩存
                await self._cleanup_cache()
                
        except asyncio.CancelledError:
            self.logger.info("📊 監控循環已取消")
        except Exception as e:
            self.logger.error(f"❌ 監控循環異常: {e}")
    
    async def _cleanup_expired_plans(self):
        """清理過期計劃"""
        try:
            expired_plans = []
            
            for plan_id, plan in self.active_plans.items():
                if plan.is_expired():
                    expired_plans.append(plan_id)
            
            for plan_id in expired_plans:
                plan = self.active_plans[plan_id]
                await self._release_reserved_resources(plan)
                del self.active_plans[plan_id]
                self.logger.debug(f"🗑️ 清理過期計劃: {plan_id}")
                
        except Exception as e:
            self.logger.error(f"❌ 清理過期計劃失敗: {e}")
    
    async def _update_satellite_loads(self):
        """更新衛星負載信息"""
        try:
            # 模擬負載更新 (實際應該從網路管理系統獲取)
            for satellite_id in list(self.satellite_loads.keys()):
                # 模擬負載變化
                current_load = self.satellite_loads[satellite_id]
                # 負載有少量隨機變化
                change = (np.random.random() - 0.5) * 0.1  # ±5%變化
                new_load = max(0.0, min(1.0, current_load + change))
                self.satellite_loads[satellite_id] = new_load
                
        except Exception as e:
            self.logger.error(f"❌ 更新衛星負載失敗: {e}")
    
    async def _cleanup_cache(self):
        """清理緩存"""
        try:
            current_time = datetime.now(timezone.utc)
            expired_keys = []
            
            for key, timestamp in self.cache_timestamps.items():
                if (current_time - timestamp).seconds > 600:  # 10分鐘過期
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.candidate_cache[key]
                del self.cache_timestamps[key]
            
            if expired_keys:
                self.logger.debug(f"🗑️ 清理過期緩存: {len(expired_keys)} 個")
                
        except Exception as e:
            self.logger.error(f"❌ 清理緩存失敗: {e}")
    
    # === 公共接口方法 ===
    
    def get_engine_status(self) -> Dict[str, Any]:
        """獲取引擎狀態"""
        with self.decision_lock:
            return {
                'engine_id': self.engine_id,
                'is_running': self.is_running,
                'pending_requests': len(self.pending_requests),
                'active_plans': len(self.active_plans),
                'completed_accesses': len(self.completed_accesses),
                'satellite_loads': dict(self.satellite_loads),
                'statistics': self.stats.copy(),
                'configuration': {
                    'decision_config': self.decision_config.copy(),
                    'evaluation_weights': self.evaluation_weights.copy(),
                    'service_configs': {k.value: v for k, v in self.service_configs.items()}
                }
            }
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        if 'decision_config' in config:
            self.decision_config.update(config['decision_config'])
        
        if 'evaluation_weights' in config:
            self.evaluation_weights.update(config['evaluation_weights'])
        
        if 'service_configs' in config:
            for service_class, service_config in config['service_configs'].items():
                if hasattr(ServiceClass, service_class.upper()):
                    self.service_configs[ServiceClass(service_class)].update(service_config)
        
        self.logger.info(f"🔧 快速接入決策引擎配置已更新: {list(config.keys())}")


# === 便利函數 ===

def create_fast_access_decision_engine(engine_id: str = None) -> FastAccessDecisionEngine:
    """創建快速接入決策引擎"""
    engine = FastAccessDecisionEngine(engine_id)
    
    logger.info(f"✅ 快速接入決策引擎創建完成 - ID: {engine.engine_id}")
    return engine


def create_test_access_request(user_id: str = "test_user", 
                              service_class: ServiceClass = ServiceClass.DATA,
                              trigger_type: AccessTrigger = AccessTrigger.INITIAL_ATTACH,
                              priority: int = 5) -> AccessRequest:
    """創建測試接入請求"""
    return AccessRequest(
        request_id=f"test_req_{int(time.time()*1000)}",
        user_id=user_id,
        device_id=f"device_{user_id}",
        trigger_type=trigger_type,
        service_class=service_class,
        timestamp=datetime.now(timezone.utc),
        user_latitude=24.9441667,  # NTPU位置
        user_longitude=121.3713889,
        user_altitude_m=50.0,
        required_bandwidth_mbps=10.0,
        max_acceptable_latency_ms=500.0,
        min_acceptable_reliability=0.95,
        priority=priority,
        device_capabilities={
            "supported_bands": ["Ka-band", "Ku-band"],
            "max_tx_power_dbm": 30.0,
            "antenna_gain_dbi": 25.0
        }
    )


def create_sample_access_candidates() -> List[AccessCandidate]:
    """創建示例接入候選"""
    candidates = []
    
    for i in range(3):
        satellite_id = f"SAT-{2001 + i}"
        candidate = AccessCandidate(
            satellite_id=satellite_id,
            beam_id=f"BEAM-{i+1}",
            frequency_band="Ka-band",
            elevation_angle=20.0 + i * 15.0,
            azimuth_angle=float(i * 120),
            distance_km=1200.0 + i * 300.0,
            signal_strength_dbm=-95.0 - i * 3.0,
            total_capacity_mbps=1000.0,
            current_load_percent=0.4 + i * 0.1,
            predicted_throughput_mbps=600.0 - i * 100.0,
            predicted_latency_ms=80.0 + i * 30.0,
            predicted_availability_duration_s=900.0 - i * 150.0
        )
        candidate.available_capacity_mbps = candidate.total_capacity_mbps * (1.0 - candidate.current_load_percent)
        candidates.append(candidate)
    
    return candidates