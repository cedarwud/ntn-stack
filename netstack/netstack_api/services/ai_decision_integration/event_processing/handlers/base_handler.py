# This file is intentionally left blank.

"""
Base Handler for event processing.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from ...interfaces.event_processor import (
    ProcessedEvent,
)


class EventHandler(ABC):
    """
    Abstract base class for event handlers.
    """

    @abstractmethod
    def handle(self, event_data: Dict[str, Any]) -> ProcessedEvent:
        """
        Handles an event and returns structured data.

        Args:
            event_data: The raw event data dictionary.

        Returns:
            A ProcessedEvent data object.
        """
        pass
