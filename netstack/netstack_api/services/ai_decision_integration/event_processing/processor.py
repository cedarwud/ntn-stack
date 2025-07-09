# This file is intentionally left blank.

"""
Main Event Processor for the AI Decision Engine.
"""
from typing import Dict, Any, List, Optional

from ..interfaces.event_processor import (
    EventProcessorInterface,
    ProcessedEvent,
)
from .validator import EventValidator
from .exceptions import InvalidEventError, UnsupportedEventError
from .handlers.base_handler import EventHandler

# While the DI container will inject the handlers, we import them here
# for type hinting and potentially for default setup.
from .handlers.a4_handler import A4EventHandler
from .handlers.d1_handler import D1EventHandler
from .handlers.d2_handler import D2EventHandler
from .handlers.t1_handler import T1EventHandler


class EventProcessor(EventProcessorInterface):
    """
    Orchestrates the processing of 3GPP events by validating them
    and dispatching them to the appropriate handlers.
    """

    def __init__(self, handlers: Optional[Dict[str, EventHandler]] = None):
        """
        Initializes the EventProcessor.

        Args:
            handlers: A dictionary mapping event types to handler instances.
                      If None, a default set of handlers will be created.
        """
        self.validator = EventValidator()
        if handlers is None:
            self.handlers = {
                "A4": A4EventHandler(),
                "D1": D1EventHandler(),
                "D2": D2EventHandler(),
                "T1": T1EventHandler(),
            }
        else:
            self.handlers = handlers

    def process_event(self, event_type: str, event_data: Dict[str, Any]) -> ProcessedEvent:
        """
        Processes a 3GPP event by validating and dispatching it.
        """
        # The validator expects the event_type to be inside the event_data dict.
        # We ensure it's there for consistent validation.
        if "event_type" not in event_data:
            event_data["event_type"] = event_type

        if not self.validator.validate_event(event_data):
            raise InvalidEventError(f"Invalid event data for event type: {event_type}")

        handler = self.handlers.get(event_type)
        if not handler:
            raise UnsupportedEventError(f"No handler registered for event type: {event_type}")

        return handler.handle(event_data)

    def validate_event(self, event: Dict[str, Any]) -> bool:
        """Proxy method for the internal validator."""
        return self.validator.validate_event(event)

    def get_supported_events(self) -> List[str]:
        """Returns a list of supported event types."""
        return list(self.handlers.keys())

    # The following methods are part of the interface but might have
    # more complex logic or be configured elsewhere.
    # Providing basic placeholders for now.

    def get_trigger_conditions(self, event_type: str) -> Dict[str, Any]:
        """Gets trigger conditions for a given event type."""
        # This could be loaded from a configuration file.
        conditions = {
            "A4": {"description": "Neighbour cell becomes better than threshold"},
            "D1": {"description": "Serving worse than thresh1, neighbour better than thresh2"},
            "D2": {"description": "Serving cell becomes worse than threshold"},
            "T1": {"description": "RRC re-establishment"},
        }
        return conditions.get(event_type, {})

    def extract_measurement_values(self, event_data: Dict[str, Any]) -> Dict[str, float]:
        """Extracts measurement values from event data."""
        return event_data.get("measurement_values", {})
