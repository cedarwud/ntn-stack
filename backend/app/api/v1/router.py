# backend/app/api/v1/router.py
from fastapi import APIRouter

# Import existing endpoint modules from your project structure
from app.api.v1.endpoints import sionna
from app.api.v1.endpoints import devices
from app.api.v1.endpoints import coordinates

# Assuming these also exist or were intended based on previous attempts:
# from app.api.v1.endpoints import device
# from app.api.v1.endpoints import simulation
# from app.api.v1.endpoints import environment
# from app.api.v1.endpoints import beamforming

# New import for satellite operations
from app.api.v1.endpoints import satellite_operations

api_router = APIRouter()

# Include existing routers (based on your project, adjust if needed)
api_router.include_router(sionna.router, prefix="/sionna", tags=["Sionna Simulations"])
api_router.include_router(devices.router, prefix="/devices", tags=["Devices"])
api_router.include_router(
    coordinates.router, prefix="/coordinates", tags=["Coordinates"]
)

# Example structure for other routers if they exist with those names:
# if 'device' in locals() and hasattr(device, 'router'):
#     api_router.include_router(device.router, prefix="/device_specific", tags=["Device Specific"])
# if 'simulation' in locals() and hasattr(simulation, 'router'):
#     api_router.include_router(simulation.router, prefix="/simulations_alt", tags=["Simulations Alt"])
# if 'environment' in locals() and hasattr(environment, 'router'):
#     api_router.include_router(environment.router, prefix="/environment_setup", tags=["Environment Setup"])
# if 'beamforming' in locals() and hasattr(beamforming, 'router'):
#     api_router.include_router(beamforming.router, prefix="/beamforming_ops", tags=["Beamforming Ops"])


# Include the new satellite operations router
# The prefix used here will be appended to /api/v1 from main.py
# So the full path will be /api/v1/satellite-ops/...
api_router.include_router(
    satellite_operations.router, prefix="/satellite-ops", tags=["Satellite Operations"]
)
