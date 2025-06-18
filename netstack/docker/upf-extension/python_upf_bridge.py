#!/usr/bin/env python3
"""
UPF 同步演算法 Python 橋接服務

實現 Python API 與 UPF C 模組的通信介面
支援論文中的同步演算法與 Open5GS UPF 整合
"""

import asyncio
import json
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import ctypes
from ctypes import (
    Structure,
    c_char,
    c_uint32,
    c_uint16,
    c_double,
    c_bool,
    c_uint64,
    c_uint8,
)
import structlog

logger = structlog.get_logger(__name__)


class SyncResult(Enum):
    """同步結果枚舉"""

    SUCCESS = 0
    ERROR_INVALID_PARAM = -1
    ERROR_UE_NOT_FOUND = -2
    ERROR_SATELLITE_NOT_FOUND = -3
    ERROR_HANDOVER_IN_PROGRESS = -4
    ERROR_ROUTING_UPDATE_FAILED = -5
    ERROR_MEMORY_ALLOCATION = -6
    ERROR_TIMEOUT = -7


class AccessStrategy(Enum):
    """UE 接入策略"""

    FLEXIBLE = 0
    CONSISTENT = 1


# C 結構體對應的 Python 類別
class UEContext(Structure):
    """UE 上下文結構"""

    _fields_ = [
        ("ue_id", c_char * 64),
        ("current_satellite_id", c_char * 64),
        ("target_satellite_id", c_char * 64),
        ("ipv4_addr", c_uint32),
        ("predicted_handover_time", c_double),
        ("handover_in_progress", c_bool),
        ("access_strategy", c_uint8),
    ]


class SatelliteInfo(Structure):
    """衛星資訊結構"""

    _fields_ = [
        ("satellite_id", c_char * 64),
        ("gnb_ip", c_uint32),
        ("gnb_port", c_uint16),
        ("latitude", c_double),
        ("longitude", c_double),
        ("altitude", c_double),
        ("is_active", c_bool),
        ("connected_ue_count", c_uint32),
    ]


class HandoverEvent(Structure):
    """換手事件結構"""

    _fields_ = [
        ("ue_id", c_char * 64),
        ("source_satellite", c_char * 64),
        ("target_satellite", c_char * 64),
        ("trigger_time", c_double),
        ("completion_time", c_double),
        ("result", ctypes.c_int),
        ("error_message", c_char * 256),
    ]


class SyncAlgorithmStatus(Structure):
    """同步演算法狀態結構"""

    _fields_ = [
        ("algorithm_running", c_bool),
        ("total_ue_count", c_uint32),
        ("active_handover_count", c_uint32),
        ("last_update_time", c_double),
        ("total_handover_count", c_uint64),
        ("successful_handover_count", c_uint64),
        ("average_handover_latency", c_double),
    ]


@dataclass
class UEInfo:
    """Python UE 資訊類別"""

    ue_id: str
    current_satellite_id: Optional[str] = None
    target_satellite_id: Optional[str] = None
    ipv4_addr: Optional[str] = None
    predicted_handover_time: Optional[float] = None
    handover_in_progress: bool = False
    access_strategy: AccessStrategy = AccessStrategy.FLEXIBLE
    position: Dict[str, float] = None

    def __post_init__(self):
        if self.position is None:
            self.position = {"lat": 0.0, "lon": 0.0, "alt": 0.0}


@dataclass
class HandoverRequest:
    """換手請求"""

    ue_id: str
    target_satellite_id: str
    predicted_time: float
    source_satellite_id: Optional[str] = None
    reason: str = "algorithm_prediction"


class UPFSyncBridge:
    """
    UPF 同步演算法橋接服務

    負責：
    1. Python API 與 UPF C 模組通信
    2. 同步演算法狀態管理
    3. 換手事件處理
    4. 路由表更新協調
    """

    def __init__(self, library_path: str = "./libsync_algorithm.so"):
        """
        初始化橋接服務

        Args:
            library_path: C 函式庫路徑
        """
        self.logger = structlog.get_logger(__name__)
        self.library_path = library_path
        self.lib = None

        # 狀態管理
        self.is_running = False
        self.periodic_update_task = None
        self.update_interval = 5.0  # 預設 5 秒更新週期

        # UE 和衛星快取
        self.ue_cache: Dict[str, UEInfo] = {}
        self.satellite_cache: Dict[str, Dict[str, Any]] = {}
        self.handover_queue: List[HandoverRequest] = []

        # 統計資訊
        self.stats = {
            "total_handovers": 0,
            "successful_handovers": 0,
            "failed_handovers": 0,
            "average_latency_ms": 0.0,
            "uptime_seconds": 0.0,
        }

        self.start_time = time.time()

        self.logger.info("UPF 同步演算法橋接服務初始化", library_path=library_path)

    def load_c_library(self) -> bool:
        """載入 C 函式庫"""
        import os

        # 多重路徑搜尋策略
        search_paths = [
            self.library_path,  # 原始路徑
            "./libsync_algorithm.so",  # 當前目錄
            "/home/sat/ntn-stack/netstack/docker/upf-extension/libsync_algorithm.so",  # 源碼目錄
            os.path.join(
                os.path.dirname(__file__), "libsync_algorithm.so"
            ),  # 相對於此檔案
        ]

        for path in search_paths:
            try:
                if os.path.exists(path):
                    self.lib = ctypes.CDLL(path)

                    # 定義函數簽名
                    self._define_function_signatures()

                    # 初始化 C 模組
                    result = self.lib.sync_algorithm_init()
                    if result != SyncResult.SUCCESS.value:
                        raise RuntimeError(f"C 模組初始化失敗: {result}")

                    self.logger.info("C 函式庫載入成功", library_path=path)
                    self.library_path = path  # 更新為實際載入路徑
                    return True

            except Exception as e:
                self.logger.debug(f"嘗試載入 {path} 失敗: {e}")
                continue

        # 所有路徑都失敗
        self.logger.warning(
            "C 函式庫載入失敗，使用模擬模式", searched_paths=search_paths
        )
        self.lib = None
        return False

    def _define_function_signatures(self):
        """定義 C 函數簽名"""
        if not self.lib:
            return

        # sync_algorithm_init
        self.lib.sync_algorithm_init.restype = ctypes.c_int

        # sync_algorithm_cleanup
        self.lib.sync_algorithm_cleanup.restype = None

        # sync_algorithm_register_ue
        self.lib.sync_algorithm_register_ue.argtypes = [ctypes.POINTER(UEContext)]
        self.lib.sync_algorithm_register_ue.restype = ctypes.c_int

        # sync_algorithm_trigger_handover
        self.lib.sync_algorithm_trigger_handover.argtypes = [
            ctypes.c_char_p,
            ctypes.c_char_p,
            c_double,
        ]
        self.lib.sync_algorithm_trigger_handover.restype = ctypes.c_int

        # sync_algorithm_get_status
        self.lib.sync_algorithm_get_status.argtypes = [
            ctypes.POINTER(SyncAlgorithmStatus)
        ]
        self.lib.sync_algorithm_get_status.restype = ctypes.c_int

    async def start(self) -> bool:
        """啟動橋接服務"""
        if self.is_running:
            self.logger.warning("橋接服務已在運行中")
            return True

        try:
            # 嘗試載入 C 函式庫
            library_loaded = self.load_c_library()

            # 啟動週期性更新任務
            self.is_running = True
            self.periodic_update_task = asyncio.create_task(
                self._periodic_update_loop()
            )

            self.logger.info(
                "UPF 同步演算法橋接服務已啟動",
                library_loaded=library_loaded,
                simulation_mode=not library_loaded,
            )

            return True

        except Exception as e:
            self.logger.error("啟動橋接服務失敗", error=str(e))
            self.is_running = False
            return False

    async def stop(self):
        """停止橋接服務"""
        if not self.is_running:
            return

        self.is_running = False

        # 停止週期性更新
        if self.periodic_update_task:
            self.periodic_update_task.cancel()
            try:
                await self.periodic_update_task
            except asyncio.CancelledError:
                pass

        # 清理 C 模組
        if self.lib:
            self.lib.sync_algorithm_cleanup()

        self.logger.info("UPF 同步演算法橋接服務已停止")

    async def register_ue(self, ue_info: UEInfo) -> bool:
        """註冊 UE"""
        try:
            # 更新快取
            self.ue_cache[ue_info.ue_id] = ue_info

            # 呼叫 C 函數（如果可用）
            if self.lib:
                ue_context = UEContext()
                ue_context.ue_id = ue_info.ue_id.encode("utf-8")
                ue_context.current_satellite_id = (
                    ue_info.current_satellite_id or ""
                ).encode("utf-8")
                ue_context.access_strategy = ue_info.access_strategy.value
                ue_context.handover_in_progress = ue_info.handover_in_progress

                result = self.lib.sync_algorithm_register_ue(ctypes.byref(ue_context))
                if result != SyncResult.SUCCESS.value:
                    self.logger.error(
                        "C 模組 UE 註冊失敗", ue_id=ue_info.ue_id, result=result
                    )
                    return False

            self.logger.info(
                "UE 註冊成功",
                ue_id=ue_info.ue_id,
                access_strategy=ue_info.access_strategy.name,
                current_satellite=ue_info.current_satellite_id,
            )

            return True

        except Exception as e:
            self.logger.error("UE 註冊失敗", ue_id=ue_info.ue_id, error=str(e))
            return False

    async def trigger_handover(self, handover_request: HandoverRequest) -> bool:
        """觸發 UE 換手"""
        try:
            start_time = time.time()

            # 檢查 UE 是否存在
            if handover_request.ue_id not in self.ue_cache:
                self.logger.error(
                    "觸發換手失敗：UE 不存在", ue_id=handover_request.ue_id
                )
                return False

            ue_info = self.ue_cache[handover_request.ue_id]

            # 檢查是否已在換手中
            if ue_info.handover_in_progress:
                self.logger.warning("UE 換手已在進行中", ue_id=handover_request.ue_id)
                return False

            # 更新 UE 狀態
            ue_info.handover_in_progress = True
            ue_info.target_satellite_id = handover_request.target_satellite_id
            ue_info.predicted_handover_time = handover_request.predicted_time

            # 呼叫 C 函數（如果可用）
            success = True
            if self.lib:
                result = self.lib.sync_algorithm_trigger_handover(
                    handover_request.ue_id.encode("utf-8"),
                    handover_request.target_satellite_id.encode("utf-8"),
                    handover_request.predicted_time,
                )
                success = result == SyncResult.SUCCESS.value

            if success:
                # 模擬換手完成（實際應該等待 UPF 確認）
                await asyncio.sleep(0.02)  # 20ms 模擬延遲

                # 更新 UE 狀態
                ue_info.current_satellite_id = handover_request.target_satellite_id
                ue_info.target_satellite_id = None
                ue_info.handover_in_progress = False

                # 更新統計
                latency_ms = (time.time() - start_time) * 1000
                self.stats["total_handovers"] += 1
                self.stats["successful_handovers"] += 1
                self._update_average_latency(latency_ms)

                self.logger.info(
                    "UE 換手成功完成",
                    ue_id=handover_request.ue_id,
                    target_satellite=handover_request.target_satellite_id,
                    latency_ms=latency_ms,
                    reason=handover_request.reason,
                )

                return True
            else:
                # 換手失敗，恢復狀態
                ue_info.handover_in_progress = False
                ue_info.target_satellite_id = None
                self.stats["failed_handovers"] += 1

                self.logger.error(
                    "UE 換手失敗",
                    ue_id=handover_request.ue_id,
                    target_satellite=handover_request.target_satellite_id,
                )

                return False

        except Exception as e:
            self.logger.error(
                "觸發換手異常", ue_id=handover_request.ue_id, error=str(e)
            )

            # 恢復 UE 狀態
            if handover_request.ue_id in self.ue_cache:
                self.ue_cache[handover_request.ue_id].handover_in_progress = False

            return False

    async def get_ue_status(self, ue_id: str) -> Optional[Dict[str, Any]]:
        """獲取 UE 狀態"""
        if ue_id not in self.ue_cache:
            return None

        ue_info = self.ue_cache[ue_id]
        return {
            "ue_id": ue_info.ue_id,
            "current_satellite_id": ue_info.current_satellite_id,
            "target_satellite_id": ue_info.target_satellite_id,
            "handover_in_progress": ue_info.handover_in_progress,
            "access_strategy": ue_info.access_strategy.name,
            "position": ue_info.position,
            "predicted_handover_time": ue_info.predicted_handover_time,
        }

    async def get_algorithm_status(self) -> Dict[str, Any]:
        """獲取演算法狀態"""
        uptime = time.time() - self.start_time
        self.stats["uptime_seconds"] = uptime

        status = {
            "service_status": {
                "running": self.is_running,
                "library_loaded": self.lib is not None,
                "uptime_seconds": uptime,
                "last_update": datetime.now(timezone.utc).isoformat(),
            },
            "ue_management": {
                "registered_ue_count": len(self.ue_cache),
                "active_handover_count": sum(
                    1 for ue in self.ue_cache.values() if ue.handover_in_progress
                ),
            },
            "handover_statistics": self.stats,
            "configuration": {
                "update_interval_seconds": self.update_interval,
                "library_path": self.library_path,
            },
        }

        # 如果 C 函式庫可用，獲取更詳細的狀態
        if self.lib:
            try:
                c_status = SyncAlgorithmStatus()
                result = self.lib.sync_algorithm_get_status(ctypes.byref(c_status))

                if result == SyncResult.SUCCESS.value:
                    status["c_module_status"] = {
                        "algorithm_running": c_status.algorithm_running,
                        "total_ue_count": c_status.total_ue_count,
                        "active_handover_count": c_status.active_handover_count,
                        "last_update_time": c_status.last_update_time,
                        "total_handover_count": c_status.total_handover_count,
                        "successful_handover_count": c_status.successful_handover_count,
                        "average_handover_latency": c_status.average_handover_latency,
                    }
            except Exception as e:
                self.logger.warning("獲取 C 模組狀態失敗", error=str(e))

        return status

    async def update_ue_position(
        self, ue_id: str, latitude: float, longitude: float, altitude: float = 0.0
    ) -> bool:
        """更新 UE 位置"""
        if ue_id not in self.ue_cache:
            return False

        try:
            ue_info = self.ue_cache[ue_id]
            ue_info.position = {"lat": latitude, "lon": longitude, "alt": altitude}

            # 呼叫 C 函數更新位置（如果可用）
            if self.lib:
                result = self.lib.sync_algorithm_update_ue_position(
                    ue_id.encode("utf-8"), latitude, longitude, altitude
                )
                if result != SyncResult.SUCCESS.value:
                    self.logger.warning(
                        "C 模組位置更新失敗", ue_id=ue_id, result=result
                    )

            self.logger.debug(
                "UE 位置已更新",
                ue_id=ue_id,
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
            )

            return True

        except Exception as e:
            self.logger.error("更新 UE 位置失敗", ue_id=ue_id, error=str(e))
            return False

    async def _periodic_update_loop(self):
        """週期性更新迴圈"""
        self.logger.info("週期性更新迴圈已啟動", update_interval=self.update_interval)

        try:
            while self.is_running:
                await self._perform_periodic_update()
                await asyncio.sleep(self.update_interval)

        except asyncio.CancelledError:
            self.logger.info("週期性更新迴圈已取消")
            raise
        except Exception as e:
            self.logger.error("週期性更新迴圈異常", error=str(e))

    async def _perform_periodic_update(self):
        """執行週期性更新"""
        try:
            # 處理待處理的換手請求
            await self._process_handover_queue()

            # 檢查超時的換手
            await self._check_handover_timeouts()

            # 更新統計資訊
            await self._update_statistics()

        except Exception as e:
            self.logger.error("週期性更新執行失敗", error=str(e))

    async def _process_handover_queue(self):
        """處理換手佇列"""
        if not self.handover_queue:
            return

        current_time = time.time()
        processed_requests = []

        for request in self.handover_queue:
            if current_time >= request.predicted_time:
                success = await self.trigger_handover(request)
                processed_requests.append(request)

                if success:
                    self.logger.info(
                        "佇列換手執行成功",
                        ue_id=request.ue_id,
                        target_satellite=request.target_satellite_id,
                    )

        # 移除已處理的請求
        for request in processed_requests:
            self.handover_queue.remove(request)

    async def _check_handover_timeouts(self):
        """檢查換手超時"""
        current_time = time.time()
        timeout_threshold = 30.0  # 30 秒超時

        for ue_info in self.ue_cache.values():
            if (
                ue_info.handover_in_progress
                and ue_info.predicted_handover_time
                and current_time - ue_info.predicted_handover_time > timeout_threshold
            ):

                self.logger.warning(
                    "換手超時，重置 UE 狀態",
                    ue_id=ue_info.ue_id,
                    timeout_seconds=timeout_threshold,
                )

                ue_info.handover_in_progress = False
                ue_info.target_satellite_id = None
                self.stats["failed_handovers"] += 1

    async def _update_statistics(self):
        """更新統計資訊"""
        total_handovers = self.stats["total_handovers"]
        if total_handovers > 0:
            success_rate = (self.stats["successful_handovers"] / total_handovers) * 100
            self.stats["success_rate_percent"] = success_rate

    def _update_average_latency(self, new_latency_ms: float):
        """更新平均延遲"""
        current_avg = self.stats["average_latency_ms"]
        total_handovers = self.stats["total_handovers"]

        if total_handovers == 1:
            self.stats["average_latency_ms"] = new_latency_ms
        else:
            # 移動平均計算
            self.stats["average_latency_ms"] = (
                current_avg * (total_handovers - 1) + new_latency_ms
            ) / total_handovers

    async def schedule_handover(self, handover_request: HandoverRequest):
        """排程換手請求"""
        self.handover_queue.append(handover_request)
        self.logger.info(
            "換手請求已排程",
            ue_id=handover_request.ue_id,
            target_satellite=handover_request.target_satellite_id,
            predicted_time=handover_request.predicted_time,
            queue_size=len(self.handover_queue),
        )

    def get_registered_ues(self) -> List[str]:
        """獲取已註冊的 UE 列表"""
        return list(self.ue_cache.keys())

    def get_handover_queue_status(self) -> Dict[str, Any]:
        """獲取換手佇列狀態"""
        return {
            "queue_size": len(self.handover_queue),
            "pending_handovers": [
                {
                    "ue_id": req.ue_id,
                    "target_satellite": req.target_satellite_id,
                    "predicted_time": req.predicted_time,
                    "reason": req.reason,
                }
                for req in self.handover_queue
            ],
        }
