"""
完整的3GPP換手事件觸發服務

整合A4、A5、D2事件的實時觸發和決策系統
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

try:
    # 嘗試容器內的路徑
    from netstack.src.services.threegpp_event_generator import ThreeGPPEventGenerator, MeasurementEventType
except ImportError:
    # 嘗試本地開發路徑
    from .threegpp_event_generator import ThreeGPPEventGenerator, MeasurementEventType
try:
    # 嘗試容器內的路徑
    from netstack_api.services.distance_correction_service import DistanceCorrectionService
except ImportError:
    # 嘗試本地開發路徑  
    from netstack_api.services.distance_correction_service import DistanceCorrectionService

logger = logging.getLogger(__name__)

class HandoverPriority(Enum):
    """換手優先級"""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class HandoverDecision:
    """換手決策結果"""
    should_handover: bool
    target_satellite_id: Optional[str]
    handover_reason: str
    priority: HandoverPriority
    expected_improvement: Dict[str, float]  # RSRP改善、距離改善等
    confidence_score: float
    triggered_events: List[str]  # 觸發的事件類型列表

@dataclass
class SatelliteMeasurement:
    """衛星測量數據"""
    satellite_id: str
    timestamp: float
    rsrp_dbm: float
    rsrq_db: float
    distance_km: float
    elevation_deg: float
    azimuth_deg: float
    is_visible: bool
    signal_quality_score: float

class HandoverEventTriggerService:
    """完整的換手事件觸發服務"""
    
    def __init__(self):
        # 初始化3GPP事件生成器和距離修正服務
        self.event_generator = ThreeGPPEventGenerator()
        self.distance_corrector = DistanceCorrectionService()
        
        # 事件歷史記錄
        self.event_history: List[Dict] = []
        self.handover_history: List[Dict] = []
        
        # 事件回調函數
        self.event_callbacks: Dict[str, List[Callable]] = {}
        
        # 系統狀態
        self.is_active = False
        self.monitoring_interval_seconds = 5.0  # 5秒監控間隔
        self.handover_cooldown_seconds = 30.0   # 30秒換手冷卻時間
        
        logger.info("🎯 換手事件觸發服務初始化完成")
    
    async def start_monitoring(self):
        """開始事件監控"""
        self.is_active = True
        logger.info("🚀 開始換手事件監控")
        
        # 開始監控任務
        asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """停止事件監控"""
        self.is_active = False
        logger.info("⏹️ 停止換手事件監控")
    
    async def _monitoring_loop(self):
        """監控循環"""
        while self.is_active:
            try:
                await self._perform_event_check()
                await asyncio.sleep(self.monitoring_interval_seconds)
            except Exception as e:
                logger.error(f"監控循環錯誤: {e}")
                await asyncio.sleep(1.0)
    
    async def process_satellite_measurements(
        self, 
        serving_satellite: SatelliteMeasurement,
        neighbor_satellites: List[SatelliteMeasurement],
        observer_location: Dict[str, float] = None
    ) -> HandoverDecision:
        """
        處理衛星測量數據並做出換手決策
        
        這是主要的入口點，整合所有A4/A5/D2事件判斷
        """
        timestamp = datetime.now().timestamp()
        
        logger.info(
            f"🔍 處理衛星測量: 服務衛星={serving_satellite.satellite_id}, "
            f"鄰居衛星數={len(neighbor_satellites)}"
        )
        
        # 1. 準備數據結構供3GPP事件生成器使用
        handover_data = self._prepare_handover_data(
            serving_satellite, neighbor_satellites, timestamp
        )
        
        # 2. 生成3GPP事件 (包含A4/A5/D2)
        events = self.event_generator.generate_measurement_events(handover_data)
        
        # 3. 分析觸發的事件
        triggered_events = [e for e in events if e['timestamp'] >= timestamp - 60]
        
        # 4. 基於事件做出換手決策
        handover_decision = await self._make_handover_decision(
            serving_satellite, neighbor_satellites, triggered_events
        )
        
        # 5. 記錄事件和決策
        self._record_events(triggered_events)
        self._record_handover_decision(handover_decision, timestamp)
        
        # 6. 觸發回調
        await self._trigger_event_callbacks(triggered_events, handover_decision)
        
        logger.info(
            f"💡 換手決策: {handover_decision.should_handover}, "
            f"目標: {handover_decision.target_satellite_id}, "
            f"原因: {handover_decision.handover_reason}"
        )
        
        return handover_decision
    
    def _prepare_handover_data(
        self, 
        serving_satellite: SatelliteMeasurement, 
        neighbor_satellites: List[SatelliteMeasurement],
        timestamp: float
    ) -> Dict[str, Any]:
        """準備3GPP事件生成器需要的數據結構"""
        trajectories = {}
        
        # 服務衛星軌跡點
        serving_point = {
            'timestamp': timestamp,
            'elevation': serving_satellite.elevation_deg,
            'azimuth': serving_satellite.azimuth_deg,
            'distance_km': serving_satellite.distance_km,
            'range_km': serving_satellite.distance_km,
            'signal_strength': serving_satellite.signal_quality_score,
            'is_visible': serving_satellite.is_visible,
            'rsrp_dbm': serving_satellite.rsrp_dbm
        }
        trajectories[serving_satellite.satellite_id] = [serving_point]
        
        # 鄰居衛星軌跡點
        for neighbor in neighbor_satellites:
            neighbor_point = {
                'timestamp': timestamp,
                'elevation': neighbor.elevation_deg,
                'azimuth': neighbor.azimuth_deg,
                'distance_km': neighbor.distance_km,
                'range_km': neighbor.distance_km,
                'signal_strength': neighbor.signal_quality_score,
                'is_visible': neighbor.is_visible,
                'rsrp_dbm': neighbor.rsrp_dbm
            }
            trajectories[neighbor.satellite_id] = [neighbor_point]
        
        return {
            'trajectories': trajectories,
            'observer_location': {
                'lat': 24.9441667,  # NTPU預設位置
                'lon': 121.3713889,
                'alt': 0.024
            },
            'timestamp': timestamp
        }
    
    async def _make_handover_decision(
        self,
        serving_satellite: SatelliteMeasurement,
        neighbor_satellites: List[SatelliteMeasurement],
        triggered_events: List[Dict]
    ) -> HandoverDecision:
        """基於觸發的事件做出換手決策"""
        
        # 檢查是否在冷卻期
        if self._is_in_handover_cooldown():
            return HandoverDecision(
                should_handover=False,
                target_satellite_id=None,
                handover_reason="在換手冷卻期內",
                priority=HandoverPriority.LOW,
                expected_improvement={},
                confidence_score=0.0,
                triggered_events=[]
            )
        
        # 分析觸發的事件
        event_types = [e['event_type'] for e in triggered_events]
        handover_candidates = []
        
        # 🎯 A4事件分析 - 鄰居衛星信號優於閾值
        a4_events = [e for e in triggered_events if e['event_type'] == 'A4']
        for event in a4_events:
            candidate_id = event['measurements'].get('handover_candidate')
            if candidate_id:
                handover_candidates.append({
                    'satellite_id': candidate_id,
                    'reason': 'A4_strong_neighbor_signal',
                    'priority': HandoverPriority.MEDIUM,
                    'rsrp_improvement': event['measurements'].get('margin', 0),
                    'confidence': 0.7
                })
        
        # 🎯 A5事件分析 - 服務衛星劣化且鄰居衛星良好
        a5_events = [e for e in triggered_events if e['event_type'] == 'A5']  
        for event in a5_events:
            candidate_id = event['measurements'].get('handover_candidate')
            if candidate_id:
                handover_candidates.append({
                    'satellite_id': candidate_id,
                    'reason': 'A5_serving_degraded_neighbor_good',
                    'priority': HandoverPriority.HIGH,
                    'rsrp_improvement': event['measurements'].get('neighbor_margin', 0),
                    'confidence': 0.9
                })
        
        # 🎯 D2事件分析 - 距離優化換手
        d2_events = [e for e in triggered_events if e['event_type'] == 'D2']
        for event in d2_events:
            candidate_id = event['measurements'].get('handover_candidate')
            if candidate_id:
                handover_candidates.append({
                    'satellite_id': candidate_id,
                    'reason': 'D2_distance_optimization',
                    'priority': HandoverPriority.MEDIUM,
                    'distance_improvement': event['measurements'].get('distance_advantage_km', 0),
                    'confidence': 0.6
                })
        
        # 選擇最佳換手候選
        if not handover_candidates:
            return HandoverDecision(
                should_handover=False,
                target_satellite_id=None,
                handover_reason="無合適的換手候選",
                priority=HandoverPriority.LOW,
                expected_improvement={},
                confidence_score=0.0,
                triggered_events=event_types
            )
        
        # 按優先級和信心分數排序
        handover_candidates.sort(
            key=lambda x: (x['priority'].value, x['confidence']), 
            reverse=True
        )
        
        best_candidate = handover_candidates[0]
        
        return HandoverDecision(
            should_handover=True,
            target_satellite_id=best_candidate['satellite_id'],
            handover_reason=best_candidate['reason'],
            priority=best_candidate['priority'],
            expected_improvement={
                'rsrp_improvement_dbm': best_candidate.get('rsrp_improvement', 0),
                'distance_improvement_km': best_candidate.get('distance_improvement', 0)
            },
            confidence_score=best_candidate['confidence'],
            triggered_events=event_types
        )
    
    def _is_in_handover_cooldown(self) -> bool:
        """檢查是否在換手冷卻期內"""
        if not self.handover_history:
            return False
        
        last_handover = self.handover_history[-1]
        time_since_last = datetime.now().timestamp() - last_handover['timestamp']
        
        return time_since_last < self.handover_cooldown_seconds
    
    def _record_events(self, events: List[Dict]):
        """記錄事件到歷史"""
        self.event_history.extend(events)
        
        # 保留最近1小時的事件
        cutoff_time = datetime.now().timestamp() - 3600
        self.event_history = [
            e for e in self.event_history 
            if e.get('timestamp', 0) >= cutoff_time
        ]
    
    def _record_handover_decision(self, decision: HandoverDecision, timestamp: float):
        """記錄換手決策"""
        if decision.should_handover:
            self.handover_history.append({
                'timestamp': timestamp,
                'target_satellite': decision.target_satellite_id,
                'reason': decision.handover_reason,
                'priority': decision.priority.value,
                'confidence': decision.confidence_score
            })
    
    async def _trigger_event_callbacks(
        self, 
        events: List[Dict], 
        decision: HandoverDecision
    ):
        """觸發註冊的事件回調"""
        for event in events:
            event_type = event['event_type']
            if event_type in self.event_callbacks:
                for callback in self.event_callbacks[event_type]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event, decision)
                        else:
                            callback(event, decision)
                    except Exception as e:
                        logger.error(f"事件回調執行錯誤: {e}")
    
    def register_event_callback(self, event_type: str, callback: Callable):
        """註冊事件回調函數"""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)
        logger.info(f"已註冊 {event_type} 事件回調")
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """獲取事件統計"""
        event_counts = {}
        for event in self.event_history:
            event_type = event.get('event_type', 'unknown')
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            'total_events': len(self.event_history),
            'event_breakdown': event_counts,
            'total_handovers': len(self.handover_history),
            'last_handover': self.handover_history[-1] if self.handover_history else None,
            'monitoring_active': self.is_active
        }
    
    def update_configuration(self, config: Dict[str, Any]):
        """更新配置參數"""
        if 'monitoring_interval_seconds' in config:
            self.monitoring_interval_seconds = config['monitoring_interval_seconds']
        
        if 'handover_cooldown_seconds' in config:
            self.handover_cooldown_seconds = config['handover_cooldown_seconds']
        
        # 更新3GPP事件生成器配置
        if 'rsrp_thresholds' in config:
            self.event_generator.measurement_config['rsrp_thresholds'].update(
                config['rsrp_thresholds']
            )
        
        if 'distance_thresholds' in config:
            self.event_generator.distance_config.update(config['distance_thresholds'])
        
        logger.info("📝 換手事件觸發服務配置已更新")
    
    async def _perform_event_check(self):
        """執行定期事件檢查 (可擴展為自動監控)"""
        # 這裡可以實現自動的系統狀態檢查
        # 例如定期查詢衛星位置，自動觸發事件檢查
        pass

# 全局服務實例
_global_handover_trigger_service: Optional[HandoverEventTriggerService] = None

def get_handover_trigger_service() -> HandoverEventTriggerService:
    """獲取全局換手觸發服務實例"""
    global _global_handover_trigger_service
    if _global_handover_trigger_service is None:
        _global_handover_trigger_service = HandoverEventTriggerService()
    return _global_handover_trigger_service

async def create_test_measurement_scenario() -> Tuple[SatelliteMeasurement, List[SatelliteMeasurement]]:
    """創建測試用的測量場景"""
    serving = SatelliteMeasurement(
        satellite_id="STARLINK-12345",
        timestamp=datetime.now().timestamp(),
        rsrp_dbm=-105.0,  # 較弱信號，可能觸發A5事件
        rsrq_db=-12.0,
        distance_km=5500.0,  # 較遠距離，可能觸發D2事件
        elevation_deg=25.0,
        azimuth_deg=180.0,
        is_visible=True,
        signal_quality_score=0.6
    )
    
    neighbors = [
        SatelliteMeasurement(
            satellite_id="STARLINK-67890",
            timestamp=datetime.now().timestamp(),
            rsrp_dbm=-95.0,  # 強信號，可能觸發A4事件
            rsrq_db=-8.0,
            distance_km=2500.0,  # 近距離，有利於D2事件
            elevation_deg=45.0,
            azimuth_deg=90.0,
            is_visible=True,
            signal_quality_score=0.8
        ),
        SatelliteMeasurement(
            satellite_id="STARLINK-11111",
            timestamp=datetime.now().timestamp(),
            rsrp_dbm=-98.0,
            rsrq_db=-10.0,
            distance_km=3200.0,
            elevation_deg=35.0,
            azimuth_deg=270.0,
            is_visible=True,
            signal_quality_score=0.7
        )
    ]
    
    return serving, neighbors