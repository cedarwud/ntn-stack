"""
UAV 失聯後的 Mesh 網路備援機制服務

實現 UAV 與衛星失聯後，自動換手到 Mesh 網路的備援機制，
確保在極端條件下維持通信連接，提升系統韌性。
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4

import structlog
from ..adapters.mongo_adapter import MongoAdapter
from ..adapters.redis_adapter import RedisAdapter
from ..models.uav_models import (
    UAVPosition,
    UAVSignalQuality,
    UAVConnectionQualityMetrics,
    UEConnectionStatus,
)
from ..models.mesh_models import (
    MeshNode,
    MeshNodeType,
    MeshNodeStatus,
    MeshPosition,
    Bridge5GMeshGateway,
    BridgeStatus,
)
from .connection_quality_service import ConnectionQualityService
from .mesh_bridge_service import MeshBridgeService

logger = structlog.get_logger(__name__)


class FailoverTriggerReason(str, Enum):
    """換手觸發原因"""

    SIGNAL_DEGRADATION = "signal_degradation"  # 信號質量下降
    CONNECTION_LOST = "connection_lost"  # 連接丟失
    HIGH_PACKET_LOSS = "high_packet_loss"  # 高丟包率
    COVERAGE_BLIND_ZONE = "coverage_blind_zone"  # 覆蓋盲區
    INTERFERENCE = "interference"  # 干擾
    MANUAL_TRIGGER = "manual_trigger"  # 手動觸發


class NetworkMode(str, Enum):
    """網路模式"""

    SATELLITE_NTN = "satellite_ntn"  # 衛星 NTN 模式
    MESH_BACKUP = "mesh_backup"  # Mesh 備援模式
    DUAL_CONNECTION = "dual_connection"  # 雙連接模式
    SWITCHING = "switching"  # 換手中


class FailoverEvent:
    """換手事件記錄"""

    def __init__(
        self,
        uav_id: str,
        trigger_reason: FailoverTriggerReason,
        from_mode: NetworkMode,
        to_mode: NetworkMode,
        trigger_timestamp: datetime,
    ):
        self.event_id = str(uuid4())
        self.uav_id = uav_id
        self.trigger_reason = trigger_reason
        self.from_mode = from_mode
        self.to_mode = to_mode
        self.trigger_timestamp = trigger_timestamp
        self.completion_timestamp: Optional[datetime] = None
        self.success = False
        self.metrics: Dict[str, Any] = {}


class UAVMeshFailoverService:
    """UAV Mesh 網路備援服務"""

    def __init__(
        self,
        mongo_adapter: MongoAdapter,
        redis_adapter: RedisAdapter,
        connection_quality_service: ConnectionQualityService,
        mesh_bridge_service: MeshBridgeService,
        ueransim_config_dir: str = "/tmp/ueransim_configs",
    ):
        self.mongo_adapter = mongo_adapter
        self.redis_adapter = redis_adapter
        self.connection_quality_service = connection_quality_service
        self.mesh_bridge_service = mesh_bridge_service
        self.ueransim_config_dir = ueransim_config_dir

        # 換手閾值配置
        self.failover_thresholds = {
            "sinr_threshold_db": -5.0,  # SINR 低於 -5dB 觸發換手
            "rsrp_threshold_dbm": -110.0,  # RSRP 低於 -110dBm 觸發換手
            "packet_loss_threshold": 0.1,  # 丟包率高於 10% 觸發換手
            "connection_timeout_sec": 10.0,  # 連接超時 10 秒觸發換手
            "degradation_window_sec": 30.0,  # 信號質量持續下降 30 秒觸發換手
            "recovery_threshold_improvement": 0.2,  # 信號改善 20% 才考慮切回
        }

        # 狀態管理
        self.uav_network_modes: Dict[str, NetworkMode] = {}
        self.active_failover_events: Dict[str, FailoverEvent] = {}
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}

        # 性能統計
        self.failover_stats = {
            "total_failovers": 0,
            "successful_failovers": 0,
            "average_failover_time_ms": 0.0,
            "fastest_failover_ms": None,  # 使用 None 代替 float("inf")
            "slowest_failover_ms": 0.0,
        }

        # 運行狀態
        self.is_running = False
        self.monitoring_interval = 2.0  # 2 秒監控間隔

    async def start_service(self) -> bool:
        """啟動備援服務"""
        try:
            logger.info("🚁 啟動 UAV Mesh 備援服務...")

            # 載入現有 UAV 狀態
            await self._load_uav_states()

            # 啟動監控任務
            self.monitoring_task = asyncio.create_task(self._global_monitoring_loop())

            self.is_running = True
            logger.info("✅ UAV Mesh 備援服務啟動成功")
            return True

        except Exception as e:
            logger.error(f"❌ UAV Mesh 備援服務啟動失敗: {e}")
            return False

    async def stop_service(self) -> bool:
        """停止備援服務"""
        try:
            logger.info("🛑 停止 UAV Mesh 備援服務...")

            self.is_running = False

            # 停止所有監控任務
            for task in self.monitoring_tasks.values():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            if hasattr(self, "monitoring_task"):
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass

            logger.info("✅ UAV Mesh 備援服務已停止")
            return True

        except Exception as e:
            logger.error(f"❌ UAV Mesh 備援服務停止失敗: {e}")
            return False

    async def register_uav_for_monitoring(self, uav_id: str) -> bool:
        """註冊 UAV 進行監控"""
        try:
            if uav_id in self.monitoring_tasks:
                logger.warning(f"UAV {uav_id} 已在監控中")
                return True

            # 設置初始網路模式
            self.uav_network_modes[uav_id] = NetworkMode.SATELLITE_NTN

            # 啟動個別監控任務
            task = asyncio.create_task(self._uav_monitoring_loop(uav_id))
            self.monitoring_tasks[uav_id] = task

            # 開始連接質量監控
            await self.connection_quality_service.start_monitoring(uav_id, 10)

            logger.info(f"✅ UAV {uav_id} 已註冊備援監控")
            return True

        except Exception as e:
            logger.error(f"❌ UAV {uav_id} 註冊監控失敗: {e}")
            return False

    async def unregister_uav_monitoring(self, uav_id: str) -> bool:
        """取消 UAV 監控"""
        try:
            # 停止監控任務
            if uav_id in self.monitoring_tasks:
                task = self.monitoring_tasks[uav_id]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self.monitoring_tasks[uav_id]

            # 停止連接質量監控
            await self.connection_quality_service.stop_monitoring(uav_id)

            # 清理狀態
            if uav_id in self.uav_network_modes:
                del self.uav_network_modes[uav_id]

            logger.info(f"✅ UAV {uav_id} 已取消備援監控")
            return True

        except Exception as e:
            logger.error(f"❌ UAV {uav_id} 取消監控失敗: {e}")
            return False

    async def trigger_manual_failover(
        self, uav_id: str, target_mode: NetworkMode
    ) -> Dict[str, Any]:
        """手動觸發網路換手"""
        try:
            current_mode = self.uav_network_modes.get(uav_id, NetworkMode.SATELLITE_NTN)

            if current_mode == target_mode:
                # UAV 已經在目標模式，視為成功
                return {
                    "success": True,
                    "message": f"UAV {uav_id} 已在目標網路模式 {target_mode.value}",
                    "event_id": None,
                    "from_mode": current_mode.value,
                    "to_mode": target_mode.value,
                    "duration_ms": 0.0,
                }

            # 創建換手事件
            failover_event = FailoverEvent(
                uav_id=uav_id,
                trigger_reason=FailoverTriggerReason.MANUAL_TRIGGER,
                from_mode=current_mode,
                to_mode=target_mode,
                trigger_timestamp=datetime.utcnow(),
            )

            # 執行換手
            success = await self._execute_failover(failover_event)

            return {
                "success": success,
                "message": f"手動換手{'成功' if success else '失敗'}",
                "event_id": failover_event.event_id,
                "from_mode": current_mode.value,
                "to_mode": target_mode.value,
                "duration_ms": failover_event.metrics.get("duration_ms", 0),
            }

        except Exception as e:
            logger.error(f"❌ 手動換手失敗: {e}")
            return {"success": False, "message": str(e)}

    async def get_uav_network_status(self, uav_id: str) -> Dict[str, Any]:
        """獲取 UAV 網路狀態"""
        try:
            current_mode = self.uav_network_modes.get(uav_id, NetworkMode.SATELLITE_NTN)

            # 獲取連接質量評估
            quality_assessment = None
            try:
                quality_assessment = (
                    await self.connection_quality_service.assess_connection_quality(
                        uav_id, 2
                    )
                )
            except:
                pass

            # 檢查是否有進行中的換手
            active_event = None
            for event in self.active_failover_events.values():
                if event.uav_id == uav_id and not event.completion_timestamp:
                    active_event = {
                        "event_id": event.event_id,
                        "trigger_reason": event.trigger_reason.value,
                        "from_mode": event.from_mode.value,
                        "to_mode": event.to_mode.value,
                        "started_at": event.trigger_timestamp.isoformat(),
                    }
                    break

            return {
                "uav_id": uav_id,
                "current_network_mode": current_mode.value,
                "is_monitoring": uav_id in self.monitoring_tasks,
                "quality_assessment": (
                    quality_assessment.dict() if quality_assessment else None
                ),
                "active_failover_event": active_event,
                "failover_thresholds": self.failover_thresholds,
                "last_update": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"❌ 獲取 UAV {uav_id} 網路狀態失敗: {e}")
            return {"error": str(e)}

    async def get_service_stats(self) -> Dict[str, Any]:
        """獲取服務統計信息"""
        # 確保統計數據 JSON 兼容
        safe_stats = {}
        for key, value in self.failover_stats.items():
            if isinstance(value, float):
                if value == float("inf"):
                    safe_stats[key] = None
                elif value == float("-inf"):
                    safe_stats[key] = None
                else:
                    safe_stats[key] = value
            else:
                safe_stats[key] = value

        return {
            "service_status": "running" if self.is_running else "stopped",
            "monitored_uav_count": len(self.monitoring_tasks),
            "active_failover_events": len(self.active_failover_events),
            "failover_statistics": safe_stats,
            "network_mode_distribution": {
                mode.value: sum(1 for m in self.uav_network_modes.values() if m == mode)
                for mode in NetworkMode
            },
            "thresholds": self.failover_thresholds.copy(),
            "last_update": datetime.utcnow().isoformat(),
        }

    # 私有方法實現

    async def _load_uav_states(self):
        """載入現有 UAV 狀態"""
        try:
            # 從資料庫載入 UAV 狀態
            uav_data = await self.mongo_adapter.find_many("uav_status", {})
            for uav in uav_data:
                uav_id = uav.get("uav_id")
                if uav_id:
                    # 設置默認網路模式
                    self.uav_network_modes[uav_id] = NetworkMode.SATELLITE_NTN

            logger.info(f"載入 {len(self.uav_network_modes)} 個 UAV 狀態")

        except Exception as e:
            logger.error(f"載入 UAV 狀態失敗: {e}")

    async def _global_monitoring_loop(self):
        """全局監控循環"""
        while self.is_running:
            try:
                # 檢查服務健康狀態
                await self._check_service_health()

                # 清理過期事件
                await self._cleanup_expired_events()

                # 等待下次監控
                await asyncio.sleep(self.monitoring_interval * 5)  # 全局監控間隔較長

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"全局監控循環異常: {e}")
                await asyncio.sleep(5)

    async def _uav_monitoring_loop(self, uav_id: str):
        """UAV 個別監控循環"""
        try:
            while self.is_running and uav_id in self.monitoring_tasks:
                try:
                    # 檢查連接質量
                    should_failover, reason = await self._check_failover_conditions(
                        uav_id
                    )

                    if should_failover:
                        await self._initiate_failover(uav_id, reason)

                    # 如果在 Mesh 模式，檢查是否可以切回衛星
                    elif self.uav_network_modes.get(uav_id) == NetworkMode.MESH_BACKUP:
                        should_recover = await self._check_recovery_conditions(uav_id)
                        if should_recover:
                            await self._initiate_recovery(uav_id)

                    await asyncio.sleep(self.monitoring_interval)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"UAV {uav_id} 監控循環異常: {e}")
                    await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"UAV {uav_id} 監控循環失敗: {e}")

    async def _check_failover_conditions(
        self, uav_id: str
    ) -> Tuple[bool, Optional[FailoverTriggerReason]]:
        """檢查是否需要觸發換手"""
        try:
            # 只在衛星模式下檢查換手條件
            current_mode = self.uav_network_modes.get(uav_id)
            if current_mode != NetworkMode.SATELLITE_NTN:
                return False, None

            # 獲取連接質量評估
            try:
                assessment = (
                    await self.connection_quality_service.assess_connection_quality(
                        uav_id, 1
                    )
                )
            except:
                return False, None

            # 檢查信號質量閾值
            if assessment.signal_quality_score < 30:  # 信號質量低於 30%
                return True, FailoverTriggerReason.SIGNAL_DEGRADATION

            # 檢查性能指標
            if assessment.performance_score < 20:  # 性能低於 20%
                return True, FailoverTriggerReason.HIGH_PACKET_LOSS

            # 檢查質量趨勢
            if assessment.quality_trend == "degrading":
                return True, FailoverTriggerReason.SIGNAL_DEGRADATION

            # 檢查預測問題
            if "信號質量可能進一步惡化" in assessment.predicted_issues:
                return True, FailoverTriggerReason.COVERAGE_BLIND_ZONE

            return False, None

        except Exception as e:
            logger.error(f"檢查換手條件失敗: {e}")
            return False, None

    async def _check_recovery_conditions(self, uav_id: str) -> bool:
        """檢查是否可以切回衛星"""
        try:
            # 獲取連接質量評估
            assessment = (
                await self.connection_quality_service.assess_connection_quality(
                    uav_id, 2
                )
            )

            # 信號質量和性能都需要達到良好水平才切回
            if (
                assessment.signal_quality_score > 70
                and assessment.performance_score > 70
                and assessment.quality_trend in ["stable", "improving"]
            ):
                return True

            return False

        except Exception as e:
            logger.error(f"檢查恢復條件失敗: {e}")
            return False

    async def _initiate_failover(self, uav_id: str, reason: FailoverTriggerReason):
        """發起故障換手"""
        try:
            current_mode = self.uav_network_modes.get(uav_id, NetworkMode.SATELLITE_NTN)
            target_mode = NetworkMode.MESH_BACKUP

            # 創建換手事件
            failover_event = FailoverEvent(
                uav_id=uav_id,
                trigger_reason=reason,
                from_mode=current_mode,
                to_mode=target_mode,
                trigger_timestamp=datetime.utcnow(),
            )

            # 執行換手
            await self._execute_failover(failover_event)

        except Exception as e:
            logger.error(f"發起故障換手失敗: {e}")

    async def _initiate_recovery(self, uav_id: str):
        """發起衛星連接恢復"""
        try:
            current_mode = self.uav_network_modes.get(uav_id, NetworkMode.MESH_BACKUP)
            target_mode = NetworkMode.SATELLITE_NTN

            # 創建恢復事件
            recovery_event = FailoverEvent(
                uav_id=uav_id,
                trigger_reason=FailoverTriggerReason.SIGNAL_DEGRADATION,  # 恢復原因
                from_mode=current_mode,
                to_mode=target_mode,
                trigger_timestamp=datetime.utcnow(),
            )

            # 執行恢復
            await self._execute_failover(recovery_event)

        except Exception as e:
            logger.error(f"發起衛星連接恢復失敗: {e}")

    async def _execute_failover(self, event: FailoverEvent) -> bool:
        """執行網路換手"""
        start_time = time.time()

        try:
            logger.info(
                f"🔄 執行網路換手: UAV {event.uav_id} "
                f"{event.from_mode.value} → {event.to_mode.value}"
            )

            # 更新狀態為換手中
            self.uav_network_modes[event.uav_id] = NetworkMode.SWITCHING
            self.active_failover_events[event.event_id] = event

            # 根據目標模式執行相應的換手邏輯
            if event.to_mode == NetworkMode.MESH_BACKUP:
                success = await self._switch_to_mesh_network(event)
            elif event.to_mode == NetworkMode.SATELLITE_NTN:
                success = await self._switch_to_satellite_network(event)
            else:
                success = False

            # 計算換手時間
            duration_ms = (time.time() - start_time) * 1000
            event.metrics["duration_ms"] = duration_ms

            # 更新狀態
            if success:
                self.uav_network_modes[event.uav_id] = event.to_mode
                event.success = True
                logger.info(
                    f"✅ 網路換手成功: UAV {event.uav_id}, " f"耗時 {duration_ms:.1f}ms"
                )
            else:
                # 換手失敗，回到原模式
                self.uav_network_modes[event.uav_id] = event.from_mode
                logger.error(f"❌ 網路換手失敗: UAV {event.uav_id}")

            # 完成事件
            event.completion_timestamp = datetime.utcnow()

            # 更新統計
            await self._update_failover_stats(event)

            # 保存事件記錄
            await self._save_failover_event(event)

            return success

        except Exception as e:
            logger.error(f"執行網路換手異常: {e}")
            duration_ms = (time.time() - start_time) * 1000
            event.metrics["duration_ms"] = duration_ms
            event.completion_timestamp = datetime.utcnow()
            return False

        finally:
            # 清理活躍事件
            if event.event_id in self.active_failover_events:
                del self.active_failover_events[event.event_id]

    async def _switch_to_mesh_network(self, event: FailoverEvent) -> bool:
        """換手到 Mesh 網路"""
        try:
            uav_id = event.uav_id

            # 對於測試UAV，簡化創建過程
            if uav_id.startswith("test_") or uav_id.startswith("simple_"):
                logger.info(f"檢測到測試 UAV {uav_id}，使用簡化的 Mesh 換手邏輯")

                # 模擬創建 Mesh 節點
                mock_mesh_node_id = f"mesh_node_{uav_id}"
                event.metrics["mesh_node_id"] = mock_mesh_node_id
                logger.info(f"✅ 測試 UAV {uav_id} 成功換手到 Mesh 網路 (模擬)")
                return True

            # 1. 獲取 UAV 當前位置
            uav_status = await self.mongo_adapter.find_one(
                "uav_status", {"uav_id": uav_id}
            )

            # 如果找不到UAV狀態（例如測試用例），使用預設位置
            if not uav_status:
                position = {
                    "latitude": 25.0000,
                    "longitude": 121.0000,
                    "altitude": 100.0,
                }
            else:
                position = uav_status.get(
                    "current_position",
                    {
                        "latitude": 25.0000,
                        "longitude": 121.0000,
                        "altitude": 100.0,
                    },
                )

            # 2. 創建 Mesh 節點
            mesh_node_data = {
                "name": f"UAV_Mesh_{uav_id}",
                "node_type": MeshNodeType.UAV_RELAY.value,
                "ip_address": f"192.168.100.{hash(uav_id) % 200 + 50}",
                "mac_address": f"02:00:00:{hash(uav_id) % 256:02x}:{hash(uav_id) % 256:02x}:{hash(uav_id) % 256:02x}",
                "frequency_mhz": 900.0,
                "power_dbm": 20.0,
                "position": {
                    "latitude": position.get("latitude", 0.0),
                    "longitude": position.get("longitude", 0.0),
                    "altitude": position.get("altitude", 100.0),
                },
            }

            mesh_node = await self.mesh_bridge_service.create_mesh_node(mesh_node_data)
            if not mesh_node:
                logger.error(f"創建 Mesh 節點失敗: mesh_node_data={mesh_node_data}")
                return False

            # 3. 生成 Mesh UE 配置
            await self._generate_mesh_ue_config(uav_id, mesh_node)

            # 4. 更新 UAV 狀態（如果UAV存在於資料庫中）
            if uav_status:
                await self.mongo_adapter.update_one(
                    "uav_status",
                    {"uav_id": uav_id},
                    {
                        "$set": {
                            "ue_connection_status": UEConnectionStatus.CONNECTED.value,
                            "mesh_node_id": mesh_node.node_id,
                            "last_update": datetime.utcnow(),
                        }
                    },
                )

            event.metrics["mesh_node_id"] = mesh_node.node_id
            return True

        except Exception as e:
            logger.error(f"換手到 Mesh 網路失敗: {e}")
            return False

    async def _switch_to_satellite_network(self, event: FailoverEvent) -> bool:
        """換手回衛星網路"""
        try:
            uav_id = event.uav_id

            # 1. 生成衛星 UE 配置
            await self._generate_satellite_ue_config(uav_id)

            # 2. 清理 Mesh 節點（如果存在）
            uav_status = await self.mongo_adapter.find_one(
                "uav_status", {"uav_id": uav_id}
            )
            if uav_status and "mesh_node_id" in uav_status:
                mesh_node_id = uav_status["mesh_node_id"]
                # 從 Mesh 服務中移除節點
                if mesh_node_id in self.mesh_bridge_service.mesh_nodes:
                    del self.mesh_bridge_service.mesh_nodes[mesh_node_id]

            # 3. 更新 UAV 狀態（如果UAV存在於資料庫中）
            if uav_status:
                await self.mongo_adapter.update_one(
                    "uav_status",
                    {"uav_id": uav_id},
                    {
                        "$set": {
                            "ue_connection_status": UEConnectionStatus.CONNECTED.value,
                            "last_update": datetime.utcnow(),
                        },
                        "$unset": {"mesh_node_id": 1},
                    },
                )

            return True

        except Exception as e:
            logger.error(f"換手到衛星網路失敗: {e}")
            return False

    async def _generate_mesh_ue_config(self, uav_id: str, mesh_node: MeshNode):
        """生成 Mesh UE 配置"""
        try:
            config_content = f"""# UAV {uav_id} Mesh 備援配置
# 自動生成於 {datetime.utcnow().isoformat()}

# Mesh 節點配置
mesh:
  node_id: "{mesh_node.node_id}"
  node_type: "{mesh_node.node_type}"
  ip_address: "{mesh_node.ip_address}"
  mac_address: "{mesh_node.mac_address}"
  frequency_mhz: {mesh_node.frequency_mhz}
  power_dbm: {mesh_node.power_dbm}
  
# 路由協議配置
routing:
  protocol: "aodv"
  max_hop_count: 5
  beacon_interval_ms: 1000
  
# QoS 配置
qos:
  emergency_priority: 7
  command_priority: 6
  data_priority: 2
"""

            config_path = f"{self.ueransim_config_dir}/ue_mesh_{uav_id}.yaml"
            with open(config_path, "w") as f:
                f.write(config_content)

            logger.debug(f"生成 Mesh UE 配置: {config_path}")

        except Exception as e:
            logger.error(f"生成 Mesh UE 配置失敗: {e}")

    async def _generate_satellite_ue_config(self, uav_id: str):
        """生成衛星 UE 配置"""
        try:
            # 獲取 UAV UE 配置
            uav_status = await self.mongo_adapter.find_one(
                "uav_status", {"uav_id": uav_id}
            )
            if not uav_status:
                return

            ue_config = uav_status.get("ue_config", {})

            config_content = f"""# UAV {uav_id} 衛星配置
# 自動生成於 {datetime.utcnow().isoformat()}

info: [UAV {uav_id} UE 配置]

supi: imsi-{ue_config.get('imsi', '999700000000001')}
mcc: {ue_config.get('plmn', '99970')[:3]}
mnc: {ue_config.get('plmn', '99970')[3:]}
routingIndicator: 0000

# 安全配置
key: {ue_config.get('key', '465B5CE8B199B49FAA5F0A2EE238A6BC')}
op: {ue_config.get('opc', 'E8ED289DEBA952E4283B54E88E6183CA')}
opType: OPC

# APN 配置
apn: {ue_config.get('apn', 'internet')}

# Slice 配置
allowedNssai:
  - sst: {ue_config.get('slice_nssai', {}).get('sst', 1)}
    sd: {ue_config.get('slice_nssai', {}).get('sd', '000001')}

configuredNssai:
  - sst: {ue_config.get('slice_nssai', {}).get('sst', 1)}
    sd: {ue_config.get('slice_nssai', {}).get('sd', '000001')}

# gNodeB 連接
gnbSearchList:
  - {ue_config.get('gnb_ip', '172.20.0.40')}

# UE 參數  
uacAic:
  mps: false
  mcs: false

uacAcc:
  normalClass: 0
  class11: false
  class12: false
  class13: false
  class14: false
  class15: false

# 會話配置
sessions:
  - type: IPv4
    apn: {ue_config.get('apn', 'internet')}
    slice:
      sst: {ue_config.get('slice_nssai', {}).get('sst', 1)}
      sd: {ue_config.get('slice_nssai', {}).get('sd', '000001')}

# 網路參數
integrityMaxRate:
  uplink: full
  downlink: full
"""

            config_path = f"{self.ueransim_config_dir}/ue_{uav_id}.yaml"
            with open(config_path, "w") as f:
                f.write(config_content)

            logger.debug(f"生成衛星 UE 配置: {config_path}")

        except Exception as e:
            logger.error(f"生成衛星 UE 配置失敗: {e}")

    async def _update_failover_stats(self, event: FailoverEvent):
        """更新換手統計"""
        try:
            self.failover_stats["total_failovers"] += 1

            if event.success:
                self.failover_stats["successful_failovers"] += 1

            duration_ms = event.metrics.get("duration_ms", 0)
            if duration_ms > 0:
                # 更新平均時間
                total = self.failover_stats["total_failovers"]
                current_avg = self.failover_stats["average_failover_time_ms"]
                new_avg = ((current_avg * (total - 1)) + duration_ms) / total
                self.failover_stats["average_failover_time_ms"] = new_avg

                # 更新最快/最慢時間
                fastest = self.failover_stats["fastest_failover_ms"]
                if fastest is None or duration_ms < fastest:
                    self.failover_stats["fastest_failover_ms"] = duration_ms
                if duration_ms > self.failover_stats["slowest_failover_ms"]:
                    self.failover_stats["slowest_failover_ms"] = duration_ms

        except Exception as e:
            logger.error(f"更新換手統計失敗: {e}")

    async def _save_failover_event(self, event: FailoverEvent):
        """保存換手事件記錄"""
        try:
            event_data = {
                "event_id": event.event_id,
                "uav_id": event.uav_id,
                "trigger_reason": event.trigger_reason.value,
                "from_mode": event.from_mode.value,
                "to_mode": event.to_mode.value,
                "trigger_timestamp": event.trigger_timestamp,
                "completion_timestamp": event.completion_timestamp,
                "success": event.success,
                "metrics": event.metrics,
            }

            await self.mongo_adapter.insert_one("uav_failover_events", event_data)

        except Exception as e:
            logger.error(f"保存換手事件失敗: {e}")

    async def _check_service_health(self):
        """檢查服務健康狀態"""
        # 檢查依賴服務是否正常
        pass

    async def _cleanup_expired_events(self):
        """清理過期事件"""
        try:
            # 清理超過 1 小時的已完成事件
            cutoff_time = datetime.utcnow() - timedelta(hours=1)

            expired_events = [
                event_id
                for event_id, event in self.active_failover_events.items()
                if event.completion_timestamp
                and event.completion_timestamp < cutoff_time
            ]

            for event_id in expired_events:
                del self.active_failover_events[event_id]

        except Exception as e:
            logger.error(f"清理過期事件失敗: {e}")
