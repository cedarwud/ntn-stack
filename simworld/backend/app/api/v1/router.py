"""
Simplified API Router

This module only handles route aggregation without business logic.
Replaces the monolithic router.py as part of Phase 2 refactoring.
"""

from fastapi import APIRouter

# Import domain API routers  
from app.api.routes.devices_postgresql import router as device_router  # PostgreSQL 版本 (替代 MongoDB)
from app.domains.coordinates.api.coordinate_api import router as coordinates_router

# from app.domains.satellite.api.satellite_api import router as satellite_router  # PostgreSQL 版本，已註釋
from app.domains.simulation.api.simulation_api import router as simulation_router

# Phase 2 重構：合併 wireless + interference → rf_simulation
from app.domains.rf_simulation.api.rf_simulation_api import router as rf_simulation_router

# from app.domains.handover.api.handover_api import router as handover_router  # 依賴 satellite 模組，暫時註釋
# from app.domains.handover.api.fine_grained_sync_api import (
#     router as fine_grained_sync_router,
# )  # 依賴 satellite 模組，暫時註釋
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

# from app.api.routes.satellite import router as satellite_ops_router  # PostgreSQL 版本，已註釋
from app.api.routes.satellite_redis import router as satellite_redis_router
from app.api.routes.uav import router as uav_router
from app.api.routes.integration import router as integration_router

# Import existing specialized routers
# from app.api.v1.satellite_admin_api import router as satellite_admin_router  # 依賴 satellite 模組，暫時註釋
from app.api.routes.health import router as health_router

# MongoDB routes removed - migrated to PostgreSQL

# Import TLE data routes for Phase 1 - Real satellite data integration

# Import measurement events routes for Phase 4 - Frontend integration
from app.api.routes.measurement_events import router as measurement_events_router

# Import historical orbits routes for real data fallback
from app.api.routes.historical_orbits import router as historical_orbits_router

# Import unified timeseries routes for 120-minute local data architecture
from app.api.routes.unified_timeseries import router as unified_timeseries_router

# Create main API router
api_router = APIRouter()

# Register core routes (health, models, scenes)
api_router.include_router(core_router, tags=["Core"])

# Register domain API routers with clean prefixes
api_router.include_router(
    device_router, prefix="/devices", tags=["Devices (PostgreSQL)"]
)
api_router.include_router(
    coordinates_router, prefix="/coordinates", tags=["Coordinates"]
)
# api_router.include_router(satellite_router, prefix="/satellites", tags=["Satellites"])  # 暫時註釋 PostgreSQL 版本
api_router.include_router(
    satellite_redis_router, prefix="/satellites", tags=["Satellites (Redis)"]
)
api_router.include_router(
    simulation_router, prefix="/simulations", tags=["Simulations"]
)

# Phase 2 重構：統一 RF 模擬 API (合併 wireless + interference)
api_router.include_router(
    rf_simulation_router, prefix="/rf", tags=["RF Simulation"]
)
# api_router.include_router(handover_router, prefix="/handover", tags=["Handover"])  # 依賴 satellite 模組，暫時註釋
api_router.include_router(system_router, prefix="/system", tags=["System"])

# Register handover sub-routers (暫時註釋，依賴 satellite 模組)
# api_router.include_router(
#     fine_grained_sync_router, prefix="/handover", tags=["Handover"]
# )
api_router.include_router(
    constrained_access_router, prefix="/handover", tags=["Handover"]
)
api_router.include_router(
    weather_prediction_router, prefix="/handover", tags=["Handover"]
)

# Register new performance domain API (replaces old performance routes)
api_router.include_router(performance_domain_router, tags=["Performance"])

# Register new consolidated routes
# api_router.include_router(satellite_ops_router, prefix="/satellite-ops", tags=["Satellite Operations"])  # 暫時註釋 PostgreSQL 版本
api_router.include_router(
    satellite_redis_router,
    prefix="/satellite-ops",
    tags=["Satellite Operations (Redis)"],
)
api_router.include_router(uav_router, prefix="/tracking", tags=["UAV Tracking"])
api_router.include_router(
    integration_router, prefix="/integration", tags=["Integration"]
)

# Register specialized routers (暫時註釋，依賴 satellite 模組)
# api_router.include_router(
#     satellite_admin_router, prefix="/admin", tags=["Administration"]
# )

# Register health routes
api_router.include_router(health_router, prefix="/health", tags=["Health"])

# Register TLE data routes for Phase 1 - Real satellite data integration

# Register measurement events routes for Phase 4 - Frontend integration
api_router.include_router(measurement_events_router, tags=["Measurement Events"])

# Register historical orbits routes for real data fallback
api_router.include_router(historical_orbits_router, tags=["Historical Orbits"])

# Register unified timeseries routes for 120-minute local data architecture
api_router.include_router(unified_timeseries_router, prefix="/satellites", tags=["Unified Timeseries"])

# Export the router
__all__ = ["api_router"]
