"""
模擬領域模組

包含Sionna相關的無線網路模擬功能。
"""

from app.domains.simulation.models.simulation_model import (
    SimulationParameters,
    SimulationResult,
    SimulationImageRequest,
)
from app.domains.simulation.interfaces.simulation_service_interface import (
    SimulationServiceInterface,
)
from app.domains.simulation.services.sionna_service import (
    SionnaSimulationService,
    sionna_service,
)
