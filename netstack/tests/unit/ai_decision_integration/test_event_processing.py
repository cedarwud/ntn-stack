"""
事件處理層測試
============

專門測試事件處理器、驗證器和處理器
"""

import pytest
import time
from unittest.mock import Mock

from ..event_processing.processor import EventProcessor
from ..event_processing.validator import EventValidator
from ..event_processing.exceptions import InvalidEventError, UnsupportedEventError
from ..event_processing.handlers.a4_handler import A4EventHandler
from ..event_processing.handlers.d1_handler import D1EventHandler
from ..event_processing.handlers.d2_handler import D2EventHandler
from ..event_processing.handlers.t1_handler import T1EventHandler


class TestEventValidator:
    """測試事件驗證器"""

    def test_valid_event(self):
        """測試有效事件"""
        validator = EventValidator()
        valid_event = {
            "event_type": "A4",
            "ue_id": "UE_001",
            "timestamp": time.time(),
        }
        assert validator.validate_event(valid_event) is True

    def test_invalid_event_missing_keys(self):
        """測試缺少必要欄位的無效事件"""
        validator = EventValidator()
        invalid_event = {"event_type": "A4"}  # 缺少 ue_id 和 timestamp
        assert validator.validate_event(invalid_event) is False

    def test_invalid_event_wrong_type(self):
        """測試錯誤類型的事件"""
        validator = EventValidator()
        assert validator.validate_event("not_a_dict") is False
        assert validator.validate_event(None) is False
        assert validator.validate_event([]) is False


class TestEventHandlers:
    """測試所有事件處理器"""

    def test_a4_handler(self):
        """測試 A4 事件處理器"""
        handler = A4EventHandler()
        event_data = {
            "event_type": "A4",
            "ue_id": "UE_001",
            "timestamp": time.time(),
            "source_cell": "CELL_001",
            "target_cells": ["CELL_002"],
            "measurement_values": {"rsrp": -80.0},
        }
        result = handler.handle(event_data)
        
        assert result.event_type == "A4"
        assert result.ue_id == "UE_001"
        assert result.confidence == 0.85
        assert "Neighbour cell becomes better than threshold" in result.trigger_conditions["description"]

    def test_d1_handler(self):
        """測試 D1 事件處理器"""
        handler = D1EventHandler()
        event_data = {
            "event_type": "D1",
            "ue_id": "UE_002",
            "timestamp": time.time(),
        }
        result = handler.handle(event_data)
        
        assert result.event_type == "D1"
        assert result.ue_id == "UE_002"
        assert result.confidence == 0.9

    def test_d2_handler(self):
        """測試 D2 事件處理器"""
        handler = D2EventHandler()
        event_data = {
            "event_type": "D2",
            "ue_id": "UE_003",
            "timestamp": time.time(),
        }
        result = handler.handle(event_data)
        
        assert result.event_type == "D2"
        assert result.ue_id == "UE_003"
        assert result.confidence == 0.8

    def test_t1_handler(self):
        """測試 T1 事件處理器"""
        handler = T1EventHandler()
        event_data = {
            "event_type": "T1",
            "ue_id": "UE_004",
            "timestamp": time.time(),
        }
        result = handler.handle(event_data)
        
        assert result.event_type == "T1"
        assert result.ue_id == "UE_004"
        assert result.confidence == 0.95


class TestEventProcessor:
    """測試事件處理器主類"""

    def test_processor_initialization_default(self):
        """測試處理器默認初始化"""
        processor = EventProcessor()
        assert len(processor.handlers) == 4
        assert "A4" in processor.handlers
        assert "D1" in processor.handlers
        assert "D2" in processor.handlers
        assert "T1" in processor.handlers

    def test_processor_initialization_custom(self):
        """測試處理器自定義初始化"""
        custom_handlers = {"TEST": Mock()}
        processor = EventProcessor(handlers=custom_handlers)
        assert len(processor.handlers) == 1
        assert "TEST" in processor.handlers

    def test_process_valid_a4_event(self):
        """測試處理有效的 A4 事件"""
        processor = EventProcessor()
        event_data = {
            "event_type": "A4",
            "ue_id": "UE_001",
            "timestamp": time.time(),
        }
        result = processor.process_event("A4", event_data)
        
        assert result.event_type == "A4"
        assert result.ue_id == "UE_001"

    def test_process_event_adds_event_type(self):
        """測試處理器自動添加事件類型"""
        processor = EventProcessor()
        event_data = {
            "ue_id": "UE_001",
            "timestamp": time.time(),
        }
        result = processor.process_event("A4", event_data)
        
        assert result.event_type == "A4"
        assert event_data["event_type"] == "A4"  # 驗證已添加到原始數據

    def test_process_invalid_event(self):
        """測試處理無效事件"""
        processor = EventProcessor()
        invalid_event = {"event_type": "A4"}  # 缺少必要欄位
        
        with pytest.raises(InvalidEventError):
            processor.process_event("A4", invalid_event)

    def test_process_unsupported_event(self):
        """測試處理不支援的事件類型"""
        processor = EventProcessor()
        event_data = {
            "event_type": "UNKNOWN",
            "ue_id": "UE_001",
            "timestamp": time.time(),
        }
        
        with pytest.raises(UnsupportedEventError):
            processor.process_event("UNKNOWN", event_data)

    def test_validate_event_proxy(self):
        """測試事件驗證代理方法"""
        processor = EventProcessor()
        valid_event = {
            "event_type": "A4",
            "ue_id": "UE_001",
            "timestamp": time.time(),
        }
        invalid_event = {"event_type": "A4"}
        
        assert processor.validate_event(valid_event) is True
        assert processor.validate_event(invalid_event) is False

    def test_get_supported_events(self):
        """測試獲取支援的事件類型"""
        processor = EventProcessor()
        supported = processor.get_supported_events()
        
        assert "A4" in supported
        assert "D1" in supported
        assert "D2" in supported
        assert "T1" in supported
        assert len(supported) == 4

    def test_get_trigger_conditions(self):
        """測試獲取觸發條件"""
        processor = EventProcessor()
        
        a4_conditions = processor.get_trigger_conditions("A4")
        assert "Neighbour cell becomes better than threshold" in a4_conditions["description"]
        
        d1_conditions = processor.get_trigger_conditions("D1")
        assert "Serving worse than thresh1" in d1_conditions["description"]
        
        unknown_conditions = processor.get_trigger_conditions("UNKNOWN")
        assert unknown_conditions == {}

    def test_extract_measurement_values(self):
        """測試提取測量值"""
        processor = EventProcessor()
        
        event_with_measurements = {
            "measurement_values": {"rsrp": -80.0, "rsrq": -10.0}
        }
        measurements = processor.extract_measurement_values(event_with_measurements)
        assert measurements["rsrp"] == -80.0
        assert measurements["rsrq"] == -10.0
        
        event_without_measurements = {}
        measurements = processor.extract_measurement_values(event_without_measurements)
        assert measurements == {}


if __name__ == "__main__":
    pytest.main([__file__])