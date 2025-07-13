"""
API Route__all__ = [
    "core_router",
    # "satellite_router",  # PostgreSQL 版本，已註釋
    "uav_router",
    "performance_router",
    "integration_router",
]ge

This package contains modular route handlers organized by functionality.
Part of the Phase 2 API layer refactoring to replace the monolithic router.
"""

from .core import router as core_router
# from .satellite import router as satellite_router  # PostgreSQL 版本，已註釋
from .uav import router as uav_router
from .performance import router as performance_router
from .integration import router as integration_router

__all__ = [
    "core_router",
    "satellite_router", 
    "uav_router",
    "performance_router",
    "integration_router"
]