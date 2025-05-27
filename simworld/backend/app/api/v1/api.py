from fastapi import APIRouter

from app.api.v1.endpoints import satellite_operations

# Import other endpoint modules here if you have them, e.g.:
# from app.api.v1.endpoints import items, users

api_router_v1 = APIRouter()

api_router_v1.include_router(
    satellite_operations.router,
    prefix="/satellite_operations",
    tags=["Satellite Operations"],
)
# Include other routers:
# api_router_v1.include_router(items.router, prefix="/items", tags=["Items"])
# api_router_v1.include_router(users.router, prefix="/users", tags=["Users"])

# You might also have a top-level api_router if you version your API like /api/v1, /api/v2
# For example:
# top_level_api_router = APIRouter()
# top_level_api_router.include_router(api_router_v1, prefix="/v1")
