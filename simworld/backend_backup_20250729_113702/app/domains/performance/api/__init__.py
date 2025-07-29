"""
Performance Domain API Module

Exports the unified performance API router for integration
with the main FastAPI application.
"""

from .performance_api import router as performance_router

__all__ = ["performance_router"]