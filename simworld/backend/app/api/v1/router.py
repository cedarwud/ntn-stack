"""
Simplified API Router

This module only handles route aggregation without business logic.
Replaces the monolithic router.py as part of Phase 2 refactoring.
"""

from fastapi import APIRouter

# Import domain API routers
from app.domains.device.api.device_api import router as device_router
from app.domains.coordinates.api.coordinate_api import router as coordinates_router
from app.domains.satellite.api.satellite_api import router as satellite_router
from app.domains.simulation.api.simulation_api import router as simulation_router
from app.domains.wireless.api.wireless_api import router as wireless_router
from app.domains.interference.api.interference_api import router as interference_router
from app.domains.handover.api.handover_api import router as handover_router
from app.domains.handover.api.fine_grained_sync_api import (
    router as fine_grained_sync_router,
)
from app.domains.handover.api.constrained_access_api import (
    router as constrained_access_router,
)
from app.domains.handover.api.weather_prediction_api import (
    router as weather_prediction_router,
)
from app.domains.system.api.system_api import router as system_router

# Import new performance domain API
from app.domains.performance.api.performance_api import (
    router as performance_domain_router,
)

# Import new consolidated route modules
from app.api.routes.core import router as core_router
from app.api.routes.satellite import router as satellite_ops_router
from app.api.routes.uav import router as uav_router
from app.api.routes.integration import router as integration_router

# Import existing specialized routers
from app.api.v1.testing import router as testing_router
from app.api.v1.satellite_admin_api import router as satellite_admin_router

# Create main API router
api_router = APIRouter()

# Register core routes (health, models, scenes)
api_router.include_router(core_router, tags=["Core"])

# Register domain API routers with clean prefixes
api_router.include_router(device_router, prefix="/devices", tags=["Devices"])
api_router.include_router(
    coordinates_router, prefix="/coordinates", tags=["Coordinates"]
)
api_router.include_router(satellite_router, prefix="/satellites", tags=["Satellites"])
api_router.include_router(
    simulation_router, prefix="/simulations", tags=["Simulations"]
)
api_router.include_router(wireless_router, prefix="/wireless", tags=["Wireless"])
api_router.include_router(
    interference_router, prefix="/interference", tags=["Interference"]
)
api_router.include_router(handover_router, prefix="/handover", tags=["Handover"])
api_router.include_router(system_router, prefix="/system", tags=["System"])

# Register handover sub-routers
api_router.include_router(
    fine_grained_sync_router, prefix="/handover", tags=["Handover"]
)
api_router.include_router(
    constrained_access_router, prefix="/handover", tags=["Handover"]
)
api_router.include_router(
    weather_prediction_router, prefix="/handover", tags=["Handover"]
)

# Register new performance domain API (replaces old performance routes)
api_router.include_router(performance_domain_router, tags=["Performance"])

# Register new consolidated routes
api_router.include_router(
    satellite_ops_router, prefix="/satellite-ops", tags=["Satellite Operations"]
)
api_router.include_router(uav_router, prefix="/tracking", tags=["UAV Tracking"])
api_router.include_router(
    integration_router, prefix="/integration", tags=["Integration"]
)

# Register specialized routers
api_router.include_router(testing_router, prefix="/testing", tags=["Testing"])
api_router.include_router(
    satellite_admin_router, prefix="/admin", tags=["Administration"]
)

# Export the router
__all__ = ["api_router"]
