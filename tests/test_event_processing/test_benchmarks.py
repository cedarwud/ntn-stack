"""
Performance benchmarks for the event processing layer.
"""

import pytest
from netstack.netstack_api.services.ai_decision_integration.event_processing.processor import (
    EventProcessor,
)

# Sample event for benchmarking
EVENT_DATA = {
    "event_type": "A4",
    "ue_id": "ue-benchmark-1",
    "timestamp": 12345.678,
    "source_cell": "cell-source-bench",
    "target_cells": ["cell-target-bench-1", "cell-target-bench-2"],
    "measurement_values": {"rsrp": -100, "rsrq": -12},
}


@pytest.fixture
def processor():
    """Fixture for a default EventProcessor."""
    return EventProcessor()


def test_processor_benchmark(processor, benchmark):
    """
    Benchmark the process_event method of the EventProcessor.
    """

    def run_process():
        processor.process_event("A4", EVENT_DATA)

    benchmark(run_process)
