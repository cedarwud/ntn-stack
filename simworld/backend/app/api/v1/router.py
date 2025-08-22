"""
Simplified API Router

This module only handles route aggregation without business logic.
Replaces the monolithic router.py as part of Phase 2 refactoring.
"""

from fastapi import APIRouter

# Import domain API routers
# from app.api.routes.devices_postgresql import router as device_router  # PostgreSQL 版本 (已移除，改用 MongoDB)
from app.api.routes.devices_mongodb import router as devices_mongodb_router
from app.domains.coordinates.api.coordinate_api import router as coordinates_router


from app.domains.simulation.api.simulation_api import router as simulation_router


# Import new consolidated route modules
from app.api.routes.core import router as core_router


from app.api.routes.satellite_redis import router as satellite_redis_router

# from app.api.routes.integration import router as integration_router  # 已刪除的 RL 相關功能

# Import existing specialized routers

from app.api.routes.health import router as health_router

# MongoDB routes removed - migrated to PostgreSQL

# Import TLE data routes for Phase 1 - Real satellite data integration

# Import measurement events routes for Phase 4 - Frontend integration


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
    devices_mongodb_router, prefix="/devices", tags=["Devices (MongoDB)"]
)
api_router.include_router(
    coordinates_router, prefix="/coordinates", tags=["Coordinates"]
)

api_router.include_router(
    satellite_redis_router, prefix="/satellites", tags=["Satellites (Redis)"]
)
api_router.include_router(
    simulation_router, prefix="/simulations", tags=["Simulations"]
)



# Register new consolidated routes

api_router.include_router(
    satellite_redis_router,
    prefix="/satellite-ops",
    tags=["Satellite Operations (Redis)"],
)


# Register health routes
api_router.include_router(health_router, prefix="/health", tags=["Health"])

# Register TLE data routes for Phase 1 - Real satellite data integration

# Register measurement events routes for Phase 4 - Frontend integration


# Register historical orbits routes for real data fallback
api_router.include_router(historical_orbits_router, tags=["Historical Orbits"])

# Register unified timeseries routes for 120-minute local data architecture
api_router.include_router(
    unified_timeseries_router, prefix="/satellites", tags=["Unified Timeseries"]
)

# Export the router
__all__ = ["api_router"]
