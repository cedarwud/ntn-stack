"""
Tests for Event Handlers.
"""

import pytest
from netstack.netstack_api.services.ai_decision_integration.event_processing.handlers.a4_handler import (
    A4EventHandler,
)
from netstack.netstack_api.services.ai_decision_integration.event_processing.handlers.d1_handler import (
    D1EventHandler,
)
from netstack.netstack_api.services.ai_decision_integration.event_processing.handlers.d2_handler import (
    D2EventHandler,
)
from netstack.netstack_api.services.ai_decision_integration.event_processing.handlers.t1_handler import (
    T1EventHandler,
)
from netstack.netstack_api.services.ai_decision_integration.interfaces.event_processor import (
    ProcessedEvent,
)

# Common test data
BASE_EVENT_DATA = {
    "ue_id": "ue-test-1",
    "source_cell": "cell-source-1",
    "target_cells": ["cell-target-1", "cell-target-2"],
    "measurement_values": {"rsrp": -95.5, "rsrq": -10.2},
}


@pytest.mark.parametrize(
    "handler_class, event_type",
    [
        (A4EventHandler, "A4"),
        (D1EventHandler, "D1"),
        (D2EventHandler, "D2"),
        (T1EventHandler, "T1"),
    ],
)
def test_event_handlers(handler_class, event_type):
    """
    Tests the handle method for all event handlers.
    """
    handler = handler_class()
    event_data = BASE_EVENT_DATA.copy()

    result = handler.handle(event_data)

    assert isinstance(result, ProcessedEvent)
    assert result.event_type == event_type
    assert result.ue_id == BASE_EVENT_DATA["ue_id"]
    assert result.event_data == event_data
    assert result.confidence > 0.0 and result.confidence <= 1.0


def test_a4_handler_specifics():
    """Test specific logic for A4EventHandler."""
    handler = A4EventHandler()
    result = handler.handle(BASE_EVENT_DATA)
    assert result.confidence == 0.85
    assert (
        result.trigger_conditions["description"]
        == "Neighbour cell becomes better than threshold"
    )


def test_d1_handler_specifics():
    """Test specific logic for D1EventHandler."""
    handler = D1EventHandler()
    result = handler.handle(BASE_EVENT_DATA)
    assert result.confidence == 0.90
    assert (
        result.trigger_conditions["description"]
        == "Serving worse than thresh1, neighbour better than thresh2"
    )
