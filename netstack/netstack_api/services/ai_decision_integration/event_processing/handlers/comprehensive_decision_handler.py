"""
Comprehensive Decision Event Handler
====================================

Handles comprehensive decision events for complex multi-factor scenarios.
"""

import time
from typing import Dict, Any
from .base_handler import EventHandler
from ...interfaces.event_processor import (
    ProcessedEvent,
)


class ComprehensiveDecisionHandler(EventHandler):
    """
    Handles comprehensive decision events for complex scenarios.
    """

    def handle(self, event_data: Dict[str, Any]) -> ProcessedEvent:
        """
        Processes a comprehensive decision event.

        Args:
            event_data: The raw comprehensive decision event data.

        Returns:
            A ProcessedEvent data object.
        """
        # 處理不同格式的事件數據
        if "event_data" in event_data:
            # 新格式：{event_type: "comprehensive_decision", event_data: {...}}
            inner_data = event_data["event_data"]
            event_type = event_data.get("event_type", "comprehensive_decision")
        else:
            # 舊格式：直接在頂層
            inner_data = event_data
            event_type = "comprehensive_decision"
        
        # 提取測量值 - 支持多種格式
        measurement_values = {}
        
        # 標準測量值
        for key in ["rsrp", "rsrq", "sinr", "throughput", "latency", "load_factor"]:
            if key in inner_data:
                measurement_values[key] = inner_data[key]
        
        # 從 measurement_values 字段提取
        if "measurement_values" in inner_data:
            measurement_values.update(inner_data["measurement_values"])
        
        # 複雜決策的默認值
        if not measurement_values:
            measurement_values = {
                "rsrp": -85.0,
                "rsrq": -12.0,
                "sinr": 15.0,
                "throughput": 50.0,
                "latency": 25.0,
                "load_factor": 0.6
            }
        
        # 提取目標單元列表
        target_cells = inner_data.get("target_cells", [])
        if not target_cells and "candidates" in inner_data:
            target_cells = inner_data["candidates"]
        
        return ProcessedEvent(
            event_type=event_type,
            event_data=inner_data,
            timestamp=inner_data.get("timestamp", time.time()),
            confidence=0.95,  # 綜合決策的高置信度
            trigger_conditions={
                "description": "Comprehensive multi-factor decision required",
                "complexity": "high",
                "factors": list(measurement_values.keys())
            },
            ue_id=inner_data.get("ue_id", "unknown_ue"),
            source_cell=inner_data.get("source_cell", "unknown_source"),
            target_cells=target_cells,
            measurement_values=measurement_values,
        )