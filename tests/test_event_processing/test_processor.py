"""
Tests for the main EventProcessor.
"""

import pytest
from unittest.mock import MagicMock, patch

from netstack.netstack_api.services.ai_decision_integration.event_processing.processor import (
    EventProcessor,
)
from netstack.netstack_api.services.ai_decision_integration.event_processing.exceptions import (
    InvalidEventError,
    UnsupportedEventError,
)


@pytest.fixture
def mock_handlers():
    """Pytest fixture for mock handlers."""
    handlers = {"A4": MagicMock(), "D1": MagicMock()}
    # Configure the mock to have a 'handle' method
    handlers["A4"].handle.return_value = "Processed A4"
    handlers["D1"].handle.return_value = "Processed D1"
    return handlers


@pytest.fixture
def mock_validator():
    """Pytest fixture for a mock validator."""
    with patch(
        "netstack.netstack_api.services.ai_decision_integration.event_processing.processor.EventValidator"
    ) as mock:
        yield mock()


def test_processor_dispatch(mock_handlers, mock_validator):
    """Test that the processor dispatches to the correct handler."""
    mock_validator.validate_event.return_value = True
    processor = EventProcessor(handlers=mock_handlers)

    # Test dispatch to A4 handler
    result_a4 = processor.process_event("A4", {"ue_id": "1", "timestamp": 1})
    mock_handlers["A4"].handle.assert_called_once()
    mock_handlers["D1"].handle.assert_not_called()
    assert result_a4 == "Processed A4"

    # Test dispatch to D1 handler
    result_d1 = processor.process_event("D1", {"ue_id": "2", "timestamp": 2})
    mock_handlers["D1"].handle.assert_called_once()
    assert result_d1 == "Processed D1"


def test_processor_invalid_event(mock_handlers, mock_validator):
    """Test that the processor raises InvalidEventError for invalid data."""
    mock_validator.validate_event.return_value = False
    processor = EventProcessor(handlers=mock_handlers)

    with pytest.raises(InvalidEventError):
        processor.process_event("A4", {"bad_data": True})


def test_processor_unsupported_event(mock_handlers, mock_validator):
    """Test that the processor raises UnsupportedEventError for an unknown event type."""
    mock_validator.validate_event.return_value = True
    processor = EventProcessor(handlers=mock_handlers)

    with pytest.raises(UnsupportedEventError):
        processor.process_event("UNKNOWN_EVENT", {"ue_id": "3", "timestamp": 3})


def test_processor_default_handlers():
    """Test that the processor initializes with default handlers if none are provided."""
    processor = EventProcessor()
    assert "A4" in processor.handlers
    assert "D1" in processor.handlers
    assert "D2" in processor.handlers
    assert "T1" in processor.handlers
    assert len(processor.handlers) == 4
