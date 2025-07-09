# This file is intentionally left blank.

"""
A4 Event Handler.
"""
import time
from typing import Dict, Any
from .base_handler import EventHandler
from ...interfaces.event_processor import (
    ProcessedEvent,
)


class A4EventHandler(EventHandler):
    """
    Handles 3GPP A4 measurement events.
    (Neighbour cell becomes better than threshold)
    """

    def handle(self, event_data: Dict[str, Any]) -> ProcessedEvent:
        """
        Processes an A4 event.

        Args:
            event_data: The raw A4 event data.

        Returns:
            A ProcessedEvent data object.
        """
        # 處理不同格式的事件數據
        if "event_data" in event_data:
            # 新格式：{event_type: "A4", event_data: {...}}
            inner_data = event_data["event_data"]
            event_type = event_data.get("event_type", "A4")
        else:
            # 舊格式：直接在頂層
            inner_data = event_data
            event_type = "A4"
        
        # 提取測量值
        measurement_values = {}
        if "rsrp" in inner_data:
            measurement_values["rsrp"] = inner_data["rsrp"]
        if "rsrq" in inner_data:
            measurement_values["rsrq"] = inner_data["rsrq"]
        if "sinr" in inner_data:
            measurement_values["sinr"] = inner_data["sinr"]
        
        # 如果沒有明確的測量值，從measurement_values字段提取
        if not measurement_values and "measurement_values" in inner_data:
            measurement_values = inner_data["measurement_values"]
        
        # 設置默認值
        if not measurement_values:
            measurement_values = {"rsrp": -80.0, "rsrq": -10.0}
        
        return ProcessedEvent(
            event_type=event_type,
            event_data=inner_data,
            timestamp=inner_data.get("timestamp", time.time()),
            confidence=0.85,
            trigger_conditions={"description": "Neighbour cell becomes better than threshold"},
            ue_id=inner_data.get("ue_id", "unknown_ue"),
            source_cell=inner_data.get("source_cell", "unknown_source"),
            target_cells=inner_data.get("target_cells", []),
            measurement_values=measurement_values,
        )
