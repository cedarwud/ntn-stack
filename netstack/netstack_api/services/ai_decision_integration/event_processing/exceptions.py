"""
Custom exceptions for the event processing module.
"""


class EventProcessingError(Exception):
    """Base exception for event processing errors."""

    pass


class InvalidEventError(EventProcessingError):
    """Raised when an event is invalid or fails validation."""

    pass


class UnsupportedEventError(EventProcessingError):
    """Raised when there is no handler for a given event type."""

    pass
