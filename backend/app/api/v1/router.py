# backend/app/api/v1/router.py
from fastapi import APIRouter

# Import new domain API routers
from app.domains.device.api.device_api import router as device_router
from app.domains.coordinates.api.coordinate_api import router as coordinates_router
from app.domains.satellite.api.satellite_api import router as satellite_router
from app.domains.simulation.api.simulation_api import router as simulation_router
from app.domains.network.api.platform_api import router as platform_router

api_router = APIRouter()

# Register domain API routers
api_router.include_router(device_router, prefix="/devices", tags=["Devices"])
api_router.include_router(
    coordinates_router, prefix="/coordinates", tags=["Coordinates"]
)
api_router.include_router(satellite_router, prefix="/satellites", tags=["Satellites"])
api_router.include_router(
    simulation_router, prefix="/simulations", tags=["Simulations"]
)
api_router.include_router(platform_router, prefix="/network", tags=["Network Platform"])
