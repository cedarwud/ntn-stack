"""
干擾控制服務

使用事件驅動架構實現高性能異步干擾檢測和響應：
- 實時干擾檢測 (<100ms)
- 異步事件處理
- AI-RAN 決策自動化
- 動態頻率管理
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

import aiohttp
import structlog
import numpy as np

from .event_bus_service import (
    EventBusService,
    Event,
    EventPriority,
    event_handler,
    get_event_bus,
    publish_event,
)

logger = structlog.get_logger(__name__)


# 事件類型定義
class InterferenceEventTypes:
    """干擾相關事件類型"""

    INTERFERENCE_DETECTED = "interference.detected"
    INTERFERENCE_RESOLVED = "interference.resolved"
    JAMMER_CREATED = "jammer.created"
    JAMMER_STOPPED = "jammer.stopped"
    AI_DECISION_REQUESTED = "ai_ran.decision_requested"
    AI_DECISION_COMPLETED = "ai_ran.decision_completed"
    FREQUENCY_SWITCHED = "frequency.switched"
    MITIGATION_APPLIED = "mitigation.applied"
    MONITORING_STARTED = "monitoring.started"
    MONITORING_STOPPED = "monitoring.stopped"


class InterferenceControlService:
    """事件驅動的干擾控制服務"""

    def __init__(
        self,
        simworld_api_url: str = "http://simworld-backend:8000",
        ueransim_config_dir: str = "/tmp/ueransim_configs",
        update_interval_sec: float = 0.1,  # 100ms 檢測間隔
        detection_threshold_db: float = -10.0,
        auto_mitigation: bool = True,
        event_bus: Optional[EventBusService] = None,
    ):
        self.simworld_api_url = simworld_api_url
        self.ueransim_config_dir = Path(ueransim_config_dir)
        self.update_interval_sec = update_interval_sec
        self.detection_threshold_db = detection_threshold_db
        self.auto_mitigation = auto_mitigation

        # 事件總線
        self.event_bus = event_bus

        # 狀態管理
        self.active_scenarios: Dict[str, Dict] = {}
        self.ai_ran_decisions: Dict[str, Dict] = {}
        self.interference_detections: Dict[str, Dict] = {}
        self.monitoring_targets: Dict[str, Dict] = {}

        # 服務狀態
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        self.detector_tasks: Dict[str, asyncio.Task] = {}

        # 性能指標
        self.metrics = {
            "detections_count": 0,
            "detection_time_avg_ms": 0.0,
            "ai_decisions_count": 0,
            "mitigations_applied": 0,
            "scenarios_active": 0,
            "events_published": 0,
            "events_processed": 0,
        }

        # HTTP 客戶端
        self.http_session: Optional[aiohttp.ClientSession] = None

        self.logger = logger.bind(service="interference_control")

    async def start(self):
        """啟動干擾控制服務"""
        try:
            self.logger.info("�� 啟動事件驅動干擾控制服務...")

            # 初始化事件總線
            if not self.event_bus:
                self.event_bus = await get_event_bus()

            # 註冊事件處理器
            await self._register_event_handlers()

            # 創建 HTTP 客戶端
            self.http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )

            # 啟動全局監控
            await self.start_global_monitoring()

            self.logger.info("✅ 事件驅動干擾控制服務啟動完成")

        except Exception as e:
            self.logger.error("❌ 干擾控制服務啟動失敗", error=str(e))
            raise

    async def stop(self):
        """停止干擾控制服務"""
        try:
            self.logger.info("🛑 停止干擾控制服務...")

            # 停止監控
            await self.stop_interference_monitoring()

            # 停止所有檢測器任務
            for task in self.detector_tasks.values():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # 關閉 HTTP 客戶端
            if self.http_session:
                await self.http_session.close()

            self.logger.info("✅ 干擾控制服務已停止")

        except Exception as e:
            self.logger.error("❌ 停止干擾控制服務失敗", error=str(e))

    async def _register_event_handlers(self):
        """註冊事件處理器"""
        if not self.event_bus:
            return

        # 註冊干擾檢測事件處理器
        self.event_bus.register_handler(
            InterferenceEventTypes.INTERFERENCE_DETECTED,
            self._handle_interference_detected,
            priority=10,  # 高優先級
            timeout_seconds=5,
        )

        # 註冊 AI 決策請求處理器
        self.event_bus.register_handler(
            InterferenceEventTypes.AI_DECISION_REQUESTED,
            self._handle_ai_decision_request,
            priority=20,
            timeout_seconds=10,
        )

        # 註冊干擾場景創建處理器
        self.event_bus.register_handler(
            InterferenceEventTypes.JAMMER_CREATED,
            self._handle_jammer_created,
            priority=30,
            timeout_seconds=5,
        )

        # 註冊頻率切換處理器
        self.event_bus.register_handler(
            InterferenceEventTypes.FREQUENCY_SWITCHED,
            self._handle_frequency_switched,
            priority=15,
            timeout_seconds=5,
        )

        self.logger.info("事件處理器註冊完成")

    async def start_global_monitoring(self):
        """啟動全局干擾監控"""
        if self.is_monitoring:
            self.logger.warning("干擾監控已在運行中")
            return

        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._global_monitoring_loop())

        # 發布監控啟動事件
        await self._publish_event(
            InterferenceEventTypes.MONITORING_STARTED,
            {
                "update_interval_sec": self.update_interval_sec,
                "detection_threshold_db": self.detection_threshold_db,
                "auto_mitigation": self.auto_mitigation,
            },
            priority=EventPriority.HIGH,
        )

        self.logger.info("✅ 全局干擾監控已啟動")

    async def stop_interference_monitoring(self):
        """停止干擾監控"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        # 發布監控停止事件
        await self._publish_event(
            InterferenceEventTypes.MONITORING_STOPPED,
            {"timestamp": datetime.utcnow().isoformat()},
            priority=EventPriority.NORMAL,
        )

        self.logger.info("干擾監控已停止")

    async def _global_monitoring_loop(self):
        """全局監控循環"""
        while self.is_monitoring:
            try:
                start_time = time.time()

                # 並行檢測所有活躍場景
                detection_tasks = []
                for scenario_id in list(self.active_scenarios.keys()):
                    task = asyncio.create_task(
                        self._detect_interference_for_scenario(scenario_id)
                    )
                    detection_tasks.append(task)

                if detection_tasks:
                    await asyncio.gather(*detection_tasks, return_exceptions=True)

                # 計算檢測時間
                detection_time = (time.time() - start_time) * 1000
                self._update_detection_time_metric(detection_time)

                # 等待下次檢測
                await asyncio.sleep(self.update_interval_sec)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("監控循環錯誤", error=str(e))
                await asyncio.sleep(1.0)

    async def _detect_interference_for_scenario(self, scenario_id: str):
        """檢測特定場景的干擾"""
        try:
            scenario = self.active_scenarios.get(scenario_id)
            if not scenario:
                return

            # 快速干擾檢測
            interference_data = await self._fast_interference_detection(scenario)

            if interference_data and interference_data.get("interference_detected"):
                # 發布干擾檢測事件
                await self._publish_event(
                    InterferenceEventTypes.INTERFERENCE_DETECTED,
                    {
                        "scenario_id": scenario_id,
                        "detection_time": datetime.utcnow().isoformat(),
                        "interference_level_db": interference_data.get(
                            "interference_level_db"
                        ),
                        "affected_frequency_mhz": interference_data.get(
                            "frequency_mhz"
                        ),
                        "jammer_type": interference_data.get("suspected_jammer_type"),
                        "confidence": interference_data.get("confidence_score", 0.0),
                        "victim_positions": scenario.get("victim_positions", []),
                    },
                    priority=EventPriority.CRITICAL,
                    correlation_id=scenario_id,
                )

                self.metrics["detections_count"] += 1

        except Exception as e:
            self.logger.error("場景干擾檢測失敗", scenario_id=scenario_id, error=str(e))

    async def _fast_interference_detection(self, scenario: Dict) -> Optional[Dict]:
        """快速干擾檢測（<50ms）"""
        try:
            if not self.http_session:
                return None

            # 簡化的快速檢測請求
            detection_request = {
                "victim_positions": scenario.get("victim_positions", []),
                "frequency_mhz": scenario.get("victim_frequency_mhz", 2150.0),
                "bandwidth_mhz": scenario.get("victim_bandwidth_mhz", 20.0),
                "fast_mode": True,  # 啟用快速模式
                "threshold_db": self.detection_threshold_db,
            }

            async with self.http_session.post(
                f"{self.simworld_api_url}/api/v1/interference/fast-detect",
                json=detection_request,
                timeout=aiohttp.ClientTimeout(total=0.05),  # 50ms 超時
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.debug("快速檢測API響應異常", status=response.status)

        except asyncio.TimeoutError:
            self.logger.debug("快速檢測超時")
        except Exception as e:
            self.logger.debug("快速檢測異常", error=str(e))

        return None

    async def _handle_interference_detected(self, event: Event):
        """處理干擾檢測事件"""
        try:
            data = event.data
            scenario_id = data.get("scenario_id")

            self.logger.info(
                "🚨 干擾檢測事件",
                scenario_id=scenario_id,
                interference_level=data.get("interference_level_db"),
                frequency=data.get("affected_frequency_mhz"),
            )

            # 記錄檢測結果
            detection_id = f"det_{uuid.uuid4().hex[:8]}"
            self.interference_detections[detection_id] = {
                "id": detection_id,
                "scenario_id": scenario_id,
                "detection_time": data.get("detection_time"),
                "data": data,
                "status": "detected",
            }

            # 如果啟用自動緩解，觸發 AI 決策
            if self.auto_mitigation:
                await self._publish_event(
                    InterferenceEventTypes.AI_DECISION_REQUESTED,
                    {
                        "detection_id": detection_id,
                        "scenario_id": scenario_id,
                        "interference_data": data,
                        "request_time": datetime.utcnow().isoformat(),
                    },
                    priority=EventPriority.HIGH,
                    correlation_id=scenario_id,
                    causation_id=event.id,
                )

            self.metrics["events_processed"] += 1

        except Exception as e:
            self.logger.error("處理干擾檢測事件失敗", error=str(e))

    async def _handle_ai_decision_request(self, event: Event):
        """處理 AI 決策請求事件"""
        try:
            data = event.data
            detection_id = data.get("detection_id")
            scenario_id = data.get("scenario_id")
            interference_data = data.get("interference_data", {})

            self.logger.info(
                "🤖 處理 AI 決策請求",
                detection_id=detection_id,
                scenario_id=scenario_id,
            )

            # 調用 AI-RAN 決策 API
            ai_decision = await self._request_ai_ran_decision(interference_data)

            if ai_decision:
                # 記錄 AI 決策
                decision_id = f"ai_{uuid.uuid4().hex[:8]}"
                self.ai_ran_decisions[decision_id] = {
                    "id": decision_id,
                    "detection_id": detection_id,
                    "scenario_id": scenario_id,
                    "decision": ai_decision,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                # 發布 AI 決策完成事件
                await self._publish_event(
                    InterferenceEventTypes.AI_DECISION_COMPLETED,
                    {
                        "decision_id": decision_id,
                        "detection_id": detection_id,
                        "scenario_id": scenario_id,
                        "recommended_action": ai_decision.get("recommended_action"),
                        "new_frequency_mhz": ai_decision.get("new_frequency_mhz"),
                        "confidence": ai_decision.get("confidence", 0.0),
                        "decision_time_ms": ai_decision.get("decision_time_ms", 0),
                    },
                    priority=EventPriority.HIGH,
                    correlation_id=scenario_id,
                    causation_id=event.id,
                )

                # 如果建議頻率切換，直接執行
                if ai_decision.get(
                    "recommended_action"
                ) == "frequency_hopping" and ai_decision.get("new_frequency_mhz"):

                    await self._publish_event(
                        InterferenceEventTypes.FREQUENCY_SWITCHED,
                        {
                            "scenario_id": scenario_id,
                            "old_frequency_mhz": interference_data.get(
                                "affected_frequency_mhz"
                            ),
                            "new_frequency_mhz": ai_decision.get("new_frequency_mhz"),
                            "switch_reason": "ai_recommendation",
                            "decision_id": decision_id,
                        },
                        priority=EventPriority.HIGH,
                        correlation_id=scenario_id,
                    )

                self.metrics["ai_decisions_count"] += 1

            self.metrics["events_processed"] += 1

        except Exception as e:
            self.logger.error("處理 AI 決策請求失敗", error=str(e))

    async def _request_ai_ran_decision(self, interference_data: Dict) -> Optional[Dict]:
        """請求 AI-RAN 抗干擾決策"""
        try:
            if not self.http_session:
                return None

            decision_request = {
                "interference_detections": [interference_data],
                "available_frequencies": [2100.0, 2150.0, 2200.0, 2300.0],  # 可用頻率
                "scenario_description": "Real-time interference mitigation",
                "fast_decision": True,  # 要求快速決策
            }

            async with self.http_session.post(
                f"{self.simworld_api_url}/api/v1/interference/ai-ran-decision",
                json=decision_request,
                timeout=aiohttp.ClientTimeout(total=2.0),  # 2秒超時
            ) as response:
                if response.status == 200:
                    return await response.json()

        except Exception as e:
            self.logger.error("AI-RAN 決策請求失敗", error=str(e))

        return None

    async def _handle_frequency_switched(self, event: Event):
        """處理頻率切換事件"""
        try:
            data = event.data
            scenario_id = data.get("scenario_id")

            self.logger.info(
                "📻 頻率切換事件",
                scenario_id=scenario_id,
                old_freq=data.get("old_frequency_mhz"),
                new_freq=data.get("new_frequency_mhz"),
            )

            # 更新場景配置
            if scenario_id in self.active_scenarios:
                self.active_scenarios[scenario_id]["victim_frequency_mhz"] = data.get(
                    "new_frequency_mhz"
                )

            # 應用頻率切換到 UERANSIM 配置
            success = await self._apply_frequency_switch(
                scenario_id, data.get("new_frequency_mhz")
            )

            if success:
                await self._publish_event(
                    InterferenceEventTypes.MITIGATION_APPLIED,
                    {
                        "scenario_id": scenario_id,
                        "mitigation_type": "frequency_hopping",
                        "new_frequency_mhz": data.get("new_frequency_mhz"),
                        "success": True,
                        "applied_time": datetime.utcnow().isoformat(),
                    },
                    priority=EventPriority.NORMAL,
                    correlation_id=scenario_id,
                )

                self.metrics["mitigations_applied"] += 1

            self.metrics["events_processed"] += 1

        except Exception as e:
            self.logger.error("處理頻率切換事件失敗", error=str(e))

    async def _apply_frequency_switch(
        self, scenario_id: str, new_frequency_mhz: float
    ) -> bool:
        """應用頻率切換到 UERANSIM"""
        try:
            # 這裡應該實現實際的 UERANSIM 配置更新
            # 暫時返回模擬結果
            self.logger.info(
                "應用頻率切換", scenario_id=scenario_id, new_frequency=new_frequency_mhz
            )

            # 模擬配置更新延遲
            await asyncio.sleep(0.01)  # 10ms

            return True

        except Exception as e:
            self.logger.error("應用頻率切換失敗", error=str(e))
            return False

    async def _handle_jammer_created(self, event: Event):
        """處理干擾源創建事件"""
        try:
            data = event.data
            scenario_id = data.get("scenario_id")

            self.logger.info("📡 干擾源創建事件", scenario_id=scenario_id)

            # 為新場景啟動專用檢測器
            if scenario_id not in self.detector_tasks:
                task = asyncio.create_task(
                    self._dedicated_scenario_detector(scenario_id)
                )
                self.detector_tasks[scenario_id] = task

            self.metrics["scenarios_active"] = len(self.active_scenarios)
            self.metrics["events_processed"] += 1

        except Exception as e:
            self.logger.error("處理干擾源創建事件失敗", error=str(e))

    async def _dedicated_scenario_detector(self, scenario_id: str):
        """專用場景檢測器（更高精度檢測）"""
        try:
            while scenario_id in self.active_scenarios:
                # 執行高精度檢測
                await self._high_precision_detection(scenario_id)

                # 較短的檢測間隔
                await asyncio.sleep(self.update_interval_sec / 2)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error("專用檢測器異常", scenario_id=scenario_id, error=str(e))

    async def _high_precision_detection(self, scenario_id: str):
        """高精度干擾檢測"""
        # 實現更詳細的干擾檢測邏輯
        pass

    async def _publish_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        priority: EventPriority = EventPriority.NORMAL,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
    ):
        """發布事件的便利方法"""
        try:
            if self.event_bus:
                await self.event_bus.publish(
                    event_type=event_type,
                    data=data,
                    source="interference_control_service",
                    priority=priority,
                    correlation_id=correlation_id,
                    causation_id=causation_id,
                    ttl_seconds=300,  # 5分鐘 TTL
                )
                self.metrics["events_published"] += 1

        except Exception as e:
            self.logger.error("事件發布失敗", event_type=event_type, error=str(e))

    def _update_detection_time_metric(self, detection_time_ms: float):
        """更新檢測時間指標"""
        current_avg = self.metrics["detection_time_avg_ms"]
        count = self.metrics["detections_count"]

        if count == 0:
            self.metrics["detection_time_avg_ms"] = detection_time_ms
        else:
            # 移動平均
            self.metrics["detection_time_avg_ms"] = (
                current_avg * count + detection_time_ms
            ) / (count + 1)

    # ===== 公共 API 方法 =====

    async def create_jammer_scenario(
        self,
        scenario_name: str,
        jammer_configs: List[Dict[str, Any]],
        victim_positions: List[List[float]],
        victim_frequency_mhz: float = 2150.0,
        victim_bandwidth_mhz: float = 20.0,
    ) -> Dict[str, Any]:
        """創建干擾場景"""
        try:
            scenario_id = f"scenario_{uuid.uuid4().hex[:8]}"

            # 調用 SimWorld API 創建干擾場景
            scenario_data = {
                "scenario_name": scenario_name,
                "jammer_configs": jammer_configs,
                "victim_positions": victim_positions,
                "victim_frequency_mhz": victim_frequency_mhz,
                "victim_bandwidth_mhz": victim_bandwidth_mhz,
            }

            if self.http_session:
                async with self.http_session.post(
                    f"{self.simworld_api_url}/api/v1/interference/scenarios",
                    json=scenario_data,
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        scenario_id = result.get("scenario_id", scenario_id)

            # 記錄活躍場景
            self.active_scenarios[scenario_id] = {
                "scenario_id": scenario_id,
                "scenario_name": scenario_name,
                "jammer_configs": jammer_configs,
                "victim_positions": victim_positions,
                "victim_frequency_mhz": victim_frequency_mhz,
                "victim_bandwidth_mhz": victim_bandwidth_mhz,
                "created_time": datetime.utcnow().isoformat(),
                "status": "active",
            }

            # 發布干擾源創建事件
            await self._publish_event(
                InterferenceEventTypes.JAMMER_CREATED,
                {
                    "scenario_id": scenario_id,
                    "scenario_name": scenario_name,
                    "jammer_count": len(jammer_configs),
                    "victim_count": len(victim_positions),
                    "frequency_mhz": victim_frequency_mhz,
                },
                priority=EventPriority.HIGH,
                correlation_id=scenario_id,
            )

            self.logger.info(
                "干擾場景已創建",
                scenario_id=scenario_id,
                jammer_count=len(jammer_configs),
            )

            return {
                "success": True,
                "scenario_id": scenario_id,
                "message": f"干擾場景 {scenario_name} 已創建",
                "active_scenarios": len(self.active_scenarios),
            }

        except Exception as e:
            self.logger.error("創建干擾場景失敗", error=str(e))
            return {
                "success": False,
                "error": str(e),
            }

    async def stop_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """停止干擾場景"""
        try:
            if scenario_id not in self.active_scenarios:
                return {
                    "success": False,
                    "error": f"場景不存在: {scenario_id}",
                }

            # 停止專用檢測器
            if scenario_id in self.detector_tasks:
                self.detector_tasks[scenario_id].cancel()
                del self.detector_tasks[scenario_id]

            # 移除活躍場景
            del self.active_scenarios[scenario_id]

            # 發布場景停止事件
            await self._publish_event(
                InterferenceEventTypes.JAMMER_STOPPED,
                {
                    "scenario_id": scenario_id,
                    "stop_time": datetime.utcnow().isoformat(),
                },
                priority=EventPriority.NORMAL,
                correlation_id=scenario_id,
            )

            self.logger.info("干擾場景已停止", scenario_id=scenario_id)

            return {
                "success": True,
                "message": f"場景 {scenario_id} 已停止",
                "active_scenarios": len(self.active_scenarios),
            }

        except Exception as e:
            self.logger.error("停止干擾場景失敗", error=str(e))
            return {
                "success": False,
                "error": str(e),
            }

    def get_service_status(self) -> Dict[str, Any]:
        """獲取服務狀態"""
        return {
            "service_name": "EventDrivenInterferenceControlService",
            "is_monitoring": self.is_monitoring,
            "active_scenarios_count": len(self.active_scenarios),
            "ai_ran_decisions_count": len(self.ai_ran_decisions),
            "interference_detections_count": len(self.interference_detections),
            "simworld_api_url": self.simworld_api_url,
            "ueransim_config_dir": str(self.ueransim_config_dir),
            "update_interval_sec": self.update_interval_sec,
            "detection_threshold_db": self.detection_threshold_db,
            "auto_mitigation": self.auto_mitigation,
            "metrics": self.metrics,
            "event_bus_connected": self.event_bus is not None,
        }

    async def get_metrics(self) -> Dict[str, Any]:
        """獲取詳細指標"""
        event_bus_metrics = {}
        if self.event_bus:
            event_bus_metrics = await self.event_bus.get_metrics()

        return {
            "interference_control": self.metrics,
            "event_bus": event_bus_metrics,
            "active_scenarios": list(self.active_scenarios.keys()),
            "detector_tasks": list(self.detector_tasks.keys()),
        }
