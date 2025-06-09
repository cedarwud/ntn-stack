"""
3GPP NTN N2 Interface Implementation - Phase 2 Stage 5

實現3GPP TS 38.413定義的N2接口，支援衛星網路特有的功能：
- NTN-specific mobility management
- Satellite beam management
- Timing advance adjustment
- NTN-specific handover procedures
- Conditional handover for satellite networks

Key Features:
- NG Application Protocol (NGAP) messages
- NTN-specific information elements
- Satellite beam switching coordination
- Enhanced mobility procedures
- Real-time timing adjustment
"""

import asyncio
import logging
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json

import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)


class NgapMessageType(Enum):
    """NGAP消息類型"""
    # Initial procedures
    NG_SETUP_REQUEST = "ng_setup_request"
    NG_SETUP_RESPONSE = "ng_setup_response"
    NG_SETUP_FAILURE = "ng_setup_failure"
    
    # UE Context procedures
    INITIAL_CONTEXT_SETUP_REQUEST = "initial_context_setup_request"
    INITIAL_CONTEXT_SETUP_RESPONSE = "initial_context_setup_response"
    UE_CONTEXT_RELEASE_REQUEST = "ue_context_release_request"
    UE_CONTEXT_RELEASE_COMPLETE = "ue_context_release_complete"
    
    # Handover procedures
    HANDOVER_REQUEST = "handover_request"
    HANDOVER_REQUEST_ACKNOWLEDGE = "handover_request_acknowledge"
    HANDOVER_COMMAND = "handover_command"
    HANDOVER_PREPARATION_FAILURE = "handover_preparation_failure"
    
    # NTN-specific procedures
    NTN_BEAM_SWITCH_REQUEST = "ntn_beam_switch_request"
    NTN_BEAM_SWITCH_RESPONSE = "ntn_beam_switch_response"
    NTN_TIMING_ADVANCE_UPDATE = "ntn_timing_advance_update"
    NTN_CONDITIONAL_HANDOVER_SETUP = "ntn_conditional_handover_setup"


class NtnCellType(Enum):
    """NTN小區類型"""
    SATELLITE_EARTH_FIXED = "satellite_earth_fixed"
    SATELLITE_EARTH_MOVING = "satellite_earth_moving"
    AIRBORNE_VEHICLE = "airborne_vehicle"


class NtnHandoverCause(Enum):
    """NTN切換原因"""
    SATELLITE_BEAM_SWITCH = "satellite_beam_switch"
    SATELLITE_VISIBILITY_LOSS = "satellite_visibility_loss"
    SIGNAL_QUALITY_DEGRADATION = "signal_quality_degradation"
    TIMING_ADVANCE_LIMIT = "timing_advance_limit"
    LOAD_BALANCING = "load_balancing"


@dataclass
class NtnCellInfo:
    """NTN小區信息"""
    cell_id: str
    satellite_id: str
    beam_id: str
    cell_type: NtnCellType
    
    # Geographic coverage
    coverage_area: Dict[str, float]  # lat_min, lat_max, lon_min, lon_max
    ephemeris_data: Dict[str, Any]
    
    # Timing parameters
    timing_advance_offset: float  # microseconds
    maximum_timing_advance: float  # microseconds
    
    # Quality metrics
    signal_strength_dbm: float
    signal_quality_db: float
    interference_level_db: float
    
    # Service parameters
    supported_services: List[str]
    maximum_ue_count: int
    current_ue_count: int


@dataclass
class NtnUeContext:
    """NTN UE上下文"""
    ue_id: str
    amf_ue_ngap_id: int
    ran_ue_ngap_id: int
    
    # Current serving cell
    serving_cell: NtnCellInfo
    neighbor_cells: List[NtnCellInfo]
    
    # NTN-specific parameters
    current_timing_advance: float
    last_timing_update: datetime
    predicted_trajectory: List[Dict[str, Any]]
    
    # Mobility state
    mobility_state: str  # stationary, low_mobility, high_mobility
    location_estimate: Dict[str, float]  # lat, lon, alt
    velocity_estimate: Dict[str, float]  # vx, vy, vz
    
    # Service context
    pdu_sessions: List[Dict[str, Any]]
    security_context: Dict[str, Any]
    
    # NTN conditional handover
    conditional_handover_candidates: List[Dict[str, Any]]
    handover_restrictions: Dict[str, Any]


@dataclass
class NgapMessage:
    """NGAP消息"""
    message_id: str
    message_type: NgapMessageType
    initiating_message: bool
    source_id: str
    destination_id: str
    
    # Message content
    procedure_code: int
    criticality: str  # reject, ignore, notify
    value: Dict[str, Any]
    
    # NTN extensions
    ntn_specific_ies: Dict[str, Any] = field(default_factory=dict)
    
    # Tracking
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None


class NtnN2Interface:
    """3GPP NTN N2接口實現"""
    
    def __init__(self, amf_endpoint: str, gnb_endpoint: str):
        self.logger = structlog.get_logger(__name__)
        self.amf_endpoint = amf_endpoint
        self.gnb_endpoint = gnb_endpoint
        
        # Interface state
        self.ng_connection_established = False
        self.interface_state = "inactive"  # inactive, active, error
        
        # UE contexts
        self.ue_contexts: Dict[str, NtnUeContext] = {}
        self.amf_ue_id_mapping: Dict[int, str] = {}
        self.ran_ue_id_mapping: Dict[int, str] = {}
        
        # Cell management
        self.served_cells: Dict[str, NtnCellInfo] = {}
        self.neighbor_relations: Dict[str, List[str]] = {}
        
        # Message handling
        self.message_handlers: Dict[NgapMessageType, callable] = {}
        self.setup_message_handlers()
        
        # Conditional handover
        self.conditional_handover_configs: Dict[str, Dict[str, Any]] = {}
        
        # Statistics
        self.interface_stats = {
            "total_messages": 0,
            "successful_procedures": 0,
            "failed_procedures": 0,
            "handovers_initiated": 0,
            "handovers_completed": 0,
            "beam_switches": 0,
            "timing_updates": 0
        }
        
        # Service state
        self.is_running = False
        self.interface_task: Optional[asyncio.Task] = None

    def setup_message_handlers(self):
        """設置消息處理器"""
        self.message_handlers = {
            NgapMessageType.NG_SETUP_REQUEST: self.handle_ng_setup_request,
            NgapMessageType.NG_SETUP_RESPONSE: self.handle_ng_setup_response,
            NgapMessageType.INITIAL_CONTEXT_SETUP_REQUEST: self.handle_initial_context_setup_request,
            NgapMessageType.HANDOVER_REQUEST: self.handle_handover_request,
            NgapMessageType.NTN_BEAM_SWITCH_REQUEST: self.handle_ntn_beam_switch_request,
            NgapMessageType.NTN_TIMING_ADVANCE_UPDATE: self.handle_ntn_timing_advance_update,
            NgapMessageType.NTN_CONDITIONAL_HANDOVER_SETUP: self.handle_ntn_conditional_handover_setup
        }

    async def start_n2_interface(self):
        """啟動N2接口"""
        if not self.is_running:
            self.is_running = True
            
            # 初始化小區信息
            await self.initialize_ntn_cells()
            
            # 建立NG連接
            await self.establish_ng_connection()
            
            # 啟動接口維護任務
            self.interface_task = asyncio.create_task(self.interface_maintenance_loop())
            
            self.logger.info("NTN N2接口已啟動")

    async def stop_n2_interface(self):
        """停止N2接口"""
        if self.is_running:
            self.is_running = False
            
            if self.interface_task:
                self.interface_task.cancel()
                try:
                    await self.interface_task
                except asyncio.CancelledError:
                    pass
            
            # 釋放所有UE上下文
            await self.release_all_ue_contexts()
            
            self.interface_state = "inactive"
            self.logger.info("NTN N2接口已停止")

    async def initialize_ntn_cells(self):
        """初始化NTN小區"""
        # 配置衛星小區
        oneweb_cell_1 = NtnCellInfo(
            cell_id="ntn_cell_oneweb_001",
            satellite_id="oneweb_001",
            beam_id="beam_001",
            cell_type=NtnCellType.SATELLITE_EARTH_MOVING,
            coverage_area={
                "lat_min": 20.0, "lat_max": 30.0,
                "lon_min": 115.0, "lon_max": 125.0
            },
            ephemeris_data={
                "orbital_elements": {},
                "prediction_accuracy": 0.95
            },
            timing_advance_offset=1000.0,  # 1ms
            maximum_timing_advance=20000.0,  # 20ms
            signal_strength_dbm=-75.0,
            signal_quality_db=15.0,
            interference_level_db=-100.0,
            supported_services=["eMBB", "URLLC"],
            maximum_ue_count=1000,
            current_ue_count=0
        )
        
        self.served_cells["ntn_cell_oneweb_001"] = oneweb_cell_1
        
        # 配置鄰居關係
        self.neighbor_relations["ntn_cell_oneweb_001"] = ["ntn_cell_oneweb_002", "ntn_cell_oneweb_003"]

    async def establish_ng_connection(self):
        """建立NG連接"""
        try:
            # 發送NG Setup Request
            ng_setup_request = await self.create_ng_setup_request()
            response = await self.send_ngap_message(ng_setup_request)
            
            if response and response.message_type == NgapMessageType.NG_SETUP_RESPONSE:
                self.ng_connection_established = True
                self.interface_state = "active"
                self.logger.info("NG連接已建立")
            else:
                self.interface_state = "error"
                self.logger.error("NG連接建立失敗")
                
        except Exception as e:
            self.interface_state = "error"
            self.logger.error(f"NG連接建立異常: {e}")

    async def create_ng_setup_request(self) -> NgapMessage:
        """創建NG Setup Request"""
        message = NgapMessage(
            message_id=f"ng_setup_{uuid.uuid4().hex[:8]}",
            message_type=NgapMessageType.NG_SETUP_REQUEST,
            initiating_message=True,
            source_id=self.gnb_endpoint,
            destination_id=self.amf_endpoint,
            procedure_code=21,  # NGSetup
            criticality="reject",
            value={
                "global_ran_node_id": {
                    "global_gnb_id": {
                        "plmn_identity": "00101",
                        "gnb_id": {"gnb_id": "0x000001"}
                    }
                },
                "ran_node_name": "NTN-gNB-001",
                "supported_ta_list": [
                    {
                        "tac": "000001",
                        "broadcast_plmns": [{"plmn_identity": "00101"}]
                    }
                ],
                "default_paging_drx": "v256"
            },
            ntn_specific_ies={
                "ntn_capability": {
                    "supported_ntn_cell_types": ["satellite_earth_moving"],
                    "timing_advance_capability": {
                        "maximum_timing_advance": 20000,
                        "timing_resolution": 1.0
                    },
                    "beam_management_capability": {
                        "beam_switching_time_ms": 50,
                        "simultaneous_beams": 8
                    },
                    "conditional_handover_support": True
                }
            }
        )
        
        return message

    async def handle_ng_setup_request(self, message: NgapMessage) -> NgapMessage:
        """處理NG Setup Request"""
        # 驗證請求
        if self.validate_ng_setup_request(message):
            # 創建成功回應
            response = NgapMessage(
                message_id=f"ng_setup_resp_{uuid.uuid4().hex[:8]}",
                message_type=NgapMessageType.NG_SETUP_RESPONSE,
                initiating_message=False,
                source_id=self.amf_endpoint,
                destination_id=message.source_id,
                procedure_code=21,
                criticality="reject",
                value={
                    "amf_name": "NTN-AMF-001",
                    "served_guami_list": [
                        {
                            "guami": {
                                "plmn_identity": "00101",
                                "amf_region_id": "01",
                                "amf_set_id": "001",
                                "amf_pointer": "01"
                            }
                        }
                    ],
                    "relative_amf_capacity": 128
                },
                correlation_id=message.message_id
            )
        else:
            # 創建失敗回應
            response = NgapMessage(
                message_id=f"ng_setup_fail_{uuid.uuid4().hex[:8]}",
                message_type=NgapMessageType.NG_SETUP_FAILURE,
                initiating_message=False,
                source_id=self.amf_endpoint,
                destination_id=message.source_id,
                procedure_code=21,
                criticality="reject",
                value={
                    "cause": {"protocol": "semantic_error"},
                    "time_to_wait": "v60s"
                },
                correlation_id=message.message_id
            )
        
        return response

    async def handle_ng_setup_response(self, message: NgapMessage) -> None:
        """處理NG Setup Response"""
        self.ng_connection_established = True
        self.interface_state = "active"
        self.interface_stats["successful_procedures"] += 1
        self.logger.info("NG Setup成功")

    async def handle_initial_context_setup_request(self, message: NgapMessage) -> NgapMessage:
        """處理Initial Context Setup Request"""
        try:
            # 提取UE信息
            amf_ue_ngap_id = message.value.get("amf_ue_ngap_id")
            ran_ue_ngap_id = message.value.get("ran_ue_ngap_id")
            
            # 創建NTN UE上下文
            ue_context = await self.create_ntn_ue_context(
                amf_ue_ngap_id, ran_ue_ngap_id, message.value
            )
            
            # 存儲上下文
            ue_id = f"ue_{amf_ue_ngap_id}_{ran_ue_ngap_id}"
            self.ue_contexts[ue_id] = ue_context
            self.amf_ue_id_mapping[amf_ue_ngap_id] = ue_id
            self.ran_ue_id_mapping[ran_ue_ngap_id] = ue_id
            
            # 執行NTN特定的設置
            await self.setup_ntn_specific_context(ue_context)
            
            # 創建成功回應
            response = NgapMessage(
                message_id=f"initial_ctx_resp_{uuid.uuid4().hex[:8]}",
                message_type=NgapMessageType.INITIAL_CONTEXT_SETUP_RESPONSE,
                initiating_message=False,
                source_id=self.gnb_endpoint,
                destination_id=message.source_id,
                procedure_code=14,
                criticality="reject",
                value={
                    "amf_ue_ngap_id": amf_ue_ngap_id,
                    "ran_ue_ngap_id": ran_ue_ngap_id,
                    "pdu_session_resource_setup_response_list": []
                },
                ntn_specific_ies={
                    "ntn_ue_context": {
                        "timing_advance": ue_context.current_timing_advance,
                        "serving_beam": ue_context.serving_cell.beam_id,
                        "conditional_handover_configured": bool(ue_context.conditional_handover_candidates)
                    }
                },
                correlation_id=message.message_id
            )
            
            self.interface_stats["successful_procedures"] += 1
            return response
            
        except Exception as e:
            self.logger.error(f"Initial Context Setup失敗: {e}")
            self.interface_stats["failed_procedures"] += 1
            raise

    async def create_ntn_ue_context(self, amf_ue_ngap_id: int, ran_ue_ngap_id: int, 
                                  message_value: Dict[str, Any]) -> NtnUeContext:
        """創建NTN UE上下文"""
        # 選擇服務小區（簡化實現）
        serving_cell = list(self.served_cells.values())[0]
        
        # 計算初始timing advance
        initial_timing_advance = await self.calculate_initial_timing_advance(serving_cell)
        
        # 預測UE軌跡
        predicted_trajectory = await self.predict_ue_trajectory(amf_ue_ngap_id)
        
        ue_context = NtnUeContext(
            ue_id=f"ue_{amf_ue_ngap_id}_{ran_ue_ngap_id}",
            amf_ue_ngap_id=amf_ue_ngap_id,
            ran_ue_ngap_id=ran_ue_ngap_id,
            serving_cell=serving_cell,
            neighbor_cells=await self.get_neighbor_cells(serving_cell.cell_id),
            current_timing_advance=initial_timing_advance,
            last_timing_update=datetime.now(),
            predicted_trajectory=predicted_trajectory,
            mobility_state="stationary",
            location_estimate={"lat": 25.0, "lon": 121.0, "alt": 100.0},
            velocity_estimate={"vx": 0.0, "vy": 0.0, "vz": 0.0},
            pdu_sessions=[],
            security_context={},
            conditional_handover_candidates=[],
            handover_restrictions={}
        )
        
        return ue_context

    async def setup_ntn_specific_context(self, ue_context: NtnUeContext):
        """設置NTN特定上下文"""
        # 配置條件切換
        await self.configure_conditional_handover(ue_context)
        
        # 啟動timing advance監控
        await self.start_timing_advance_monitoring(ue_context)
        
        # 更新服務小區統計
        ue_context.serving_cell.current_ue_count += 1

    async def handle_ntn_beam_switch_request(self, message: NgapMessage) -> NgapMessage:
        """處理NTN波束切換請求"""
        try:
            # 提取切換參數
            ue_id = message.ntn_specific_ies.get("ue_id")
            target_beam_id = message.ntn_specific_ies.get("target_beam_id")
            switch_time = message.ntn_specific_ies.get("switch_time")
            
            ue_context = self.ue_contexts.get(ue_id)
            if not ue_context:
                raise Exception(f"UE context not found: {ue_id}")
            
            # 執行波束切換
            switch_result = await self.execute_beam_switch(ue_context, target_beam_id, switch_time)
            
            # 創建回應
            response = NgapMessage(
                message_id=f"beam_switch_resp_{uuid.uuid4().hex[:8]}",
                message_type=NgapMessageType.NTN_BEAM_SWITCH_RESPONSE,
                initiating_message=False,
                source_id=self.gnb_endpoint,
                destination_id=message.source_id,
                procedure_code=100,  # NTN-specific
                criticality="reject",
                value={
                    "result": "success" if switch_result["success"] else "failure"
                },
                ntn_specific_ies={
                    "beam_switch_result": switch_result
                },
                correlation_id=message.message_id
            )
            
            self.interface_stats["beam_switches"] += 1
            return response
            
        except Exception as e:
            self.logger.error(f"波束切換失敗: {e}")
            raise

    async def handle_ntn_timing_advance_update(self, message: NgapMessage) -> None:
        """處理NTN Timing Advance更新"""
        try:
            ue_id = message.ntn_specific_ies.get("ue_id")
            new_timing_advance = message.ntn_specific_ies.get("timing_advance")
            
            ue_context = self.ue_contexts.get(ue_id)
            if ue_context:
                ue_context.current_timing_advance = new_timing_advance
                ue_context.last_timing_update = datetime.now()
                
                self.interface_stats["timing_updates"] += 1
                self.logger.info(f"Timing Advance已更新: {ue_id} -> {new_timing_advance}μs")
                
        except Exception as e:
            self.logger.error(f"Timing Advance更新失敗: {e}")

    async def handle_ntn_conditional_handover_setup(self, message: NgapMessage) -> NgapMessage:
        """處理NTN條件切換設置"""
        try:
            ue_id = message.ntn_specific_ies.get("ue_id")
            handover_conditions = message.ntn_specific_ies.get("handover_conditions")
            candidate_cells = message.ntn_specific_ies.get("candidate_cells")
            
            ue_context = self.ue_contexts.get(ue_id)
            if not ue_context:
                raise Exception(f"UE context not found: {ue_id}")
            
            # 配置條件切換
            conditional_config = await self.setup_conditional_handover_config(
                ue_context, handover_conditions, candidate_cells
            )
            
            # 存儲配置
            self.conditional_handover_configs[ue_id] = conditional_config
            ue_context.conditional_handover_candidates = candidate_cells
            
            # 創建回應
            response = NgapMessage(
                message_id=f"cond_ho_setup_resp_{uuid.uuid4().hex[:8]}",
                message_type=NgapMessageType.NTN_CONDITIONAL_HANDOVER_SETUP,
                initiating_message=False,
                source_id=self.gnb_endpoint,
                destination_id=message.source_id,
                procedure_code=101,  # NTN-specific
                criticality="reject",
                value={
                    "result": "success",
                    "configured_candidates": len(candidate_cells)
                },
                ntn_specific_ies={
                    "conditional_handover_config": conditional_config
                },
                correlation_id=message.message_id
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"條件切換設置失敗: {e}")
            raise

    async def send_ngap_message(self, message: NgapMessage) -> Optional[NgapMessage]:
        """發送NGAP消息"""
        try:
            self.interface_stats["total_messages"] += 1
            
            # 序列化消息（簡化實現）
            message_data = {
                "message_id": message.message_id,
                "message_type": message.message_type.value,
                "procedure_code": message.procedure_code,
                "value": message.value,
                "ntn_specific_ies": message.ntn_specific_ies
            }
            
            # 模擬發送和接收
            await asyncio.sleep(0.01)  # 模擬網路延遲
            
            # 如果有對應的處理器，處理消息
            if message.message_type in self.message_handlers:
                handler = self.message_handlers[message.message_type]
                if asyncio.iscoroutinefunction(handler):
                    response = await handler(message)
                    return response
            
            return None
            
        except Exception as e:
            self.logger.error(f"NGAP消息發送失敗: {e}")
            return None

    # 輔助方法實現
    async def calculate_initial_timing_advance(self, serving_cell: NtnCellInfo) -> float:
        """計算初始timing advance"""
        # 基於衛星距離計算
        satellite_distance_km = 1200.0  # LEO典型距離
        light_speed_km_per_us = 0.3  # 光速 km/μs
        round_trip_delay_us = (satellite_distance_km * 2) / light_speed_km_per_us
        
        return round_trip_delay_us + serving_cell.timing_advance_offset

    async def predict_ue_trajectory(self, ue_id: int) -> List[Dict[str, Any]]:
        """預測UE軌跡"""
        # 簡化實現
        return [
            {
                "timestamp": (datetime.now() + timedelta(minutes=i)).isoformat(),
                "lat": 25.0 + i * 0.01,
                "lon": 121.0 + i * 0.01,
                "alt": 100.0
            }
            for i in range(10)  # 10個預測點
        ]

    async def get_neighbor_cells(self, cell_id: str) -> List[NtnCellInfo]:
        """獲取鄰居小區"""
        neighbor_ids = self.neighbor_relations.get(cell_id, [])
        return [self.served_cells[nid] for nid in neighbor_ids if nid in self.served_cells]

    async def interface_maintenance_loop(self):
        """接口維護循環"""
        while self.is_running:
            try:
                # 檢查連接狀態
                await self.check_ng_connection_health()
                
                # 更新UE timing advance
                await self.update_all_timing_advances()
                
                # 檢查條件切換觸發
                await self.check_conditional_handover_triggers()
                
                await asyncio.sleep(1.0)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"接口維護循環異常: {e}")
                await asyncio.sleep(5.0)

    def validate_ng_setup_request(self, message: NgapMessage) -> bool:
        """驗證NG Setup Request"""
        required_fields = ["global_ran_node_id", "supported_ta_list"]
        return all(field in message.value for field in required_fields)

    async def get_n2_interface_status(self) -> Dict[str, Any]:
        """獲取N2接口狀態"""
        return {
            "interface_status": {
                "is_running": self.is_running,
                "interface_state": self.interface_state,
                "ng_connection_established": self.ng_connection_established
            },
            "ue_contexts": {
                "total_ues": len(self.ue_contexts),
                "active_sessions": sum(1 for ue in self.ue_contexts.values() if ue.pdu_sessions)
            },
            "cell_information": {
                "served_cells": len(self.served_cells),
                "total_ue_capacity": sum(cell.maximum_ue_count for cell in self.served_cells.values()),
                "current_ue_load": sum(cell.current_ue_count for cell in self.served_cells.values())
            },
            "interface_statistics": self.interface_stats.copy(),
            "ntn_features": {
                "conditional_handover_configs": len(self.conditional_handover_configs),
                "beam_management_active": True,
                "timing_advance_monitoring": True
            }
        }

    # 其他輔助方法的簡化實現
    async def execute_beam_switch(self, ue_context: NtnUeContext, target_beam_id: str, switch_time: float) -> Dict[str, Any]:
        """執行波束切換"""
        return {"success": True, "switch_time_ms": switch_time, "new_beam_id": target_beam_id}

    async def configure_conditional_handover(self, ue_context: NtnUeContext):
        """配置條件切換"""
        pass

    async def start_timing_advance_monitoring(self, ue_context: NtnUeContext):
        """啟動timing advance監控"""
        pass

    async def setup_conditional_handover_config(self, ue_context: NtnUeContext, conditions: Dict, candidates: List) -> Dict[str, Any]:
        """設置條件切換配置"""
        return {"configured": True, "conditions": conditions, "candidates": len(candidates)}

    async def check_ng_connection_health(self):
        """檢查NG連接健康"""
        pass

    async def update_all_timing_advances(self):
        """更新所有UE的timing advance"""
        pass

    async def check_conditional_handover_triggers(self):
        """檢查條件切換觸發"""
        pass

    async def release_all_ue_contexts(self):
        """釋放所有UE上下文"""
        for ue_context in self.ue_contexts.values():
            ue_context.serving_cell.current_ue_count = max(0, ue_context.serving_cell.current_ue_count - 1)
        
        self.ue_contexts.clear()
        self.amf_ue_id_mapping.clear()
        self.ran_ue_id_mapping.clear()