"""
Tests for EventValidator.
"""

import pytest
from netstack.netstack_api.services.ai_decision_integration.event_processing.validator import (
    EventValidator,
)


@pytest.fixture
def validator():
    """Pytest fixture for EventValidator."""
    return EventValidator()


def test_validate_event_valid(validator):
    """Test a valid event."""
    event = {"event_type": "A4", "ue_id": "ue-123", "timestamp": 12345.67}
    assert validator.validate_event(event) is True


def test_validate_event_missing_key(validator):
    """Test an event with a missing key."""
    event = {"event_type": "A4", "ue_id": "ue-123"}  # missing timestamp
    assert validator.validate_event(event) is False


def test_validate_event_not_a_dict(validator):
    """Test when the event is not a dictionary."""
    event = "not_a_dict"
    assert validator.validate_event(event) is False


def test_validate_event_empty_dict(validator):
    """Test when the event is an empty dictionary."""
    event = {}
    assert validator.validate_event(event) is False
