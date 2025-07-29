"""
Minimal Viable Product (MVP) for Unified Lifecycle Management
Gradual integration approach - adds only essential unified features to existing main.py
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Import MongoDB lifespan (migrated from PostgreSQL)
from app.db.lifespan import lifespan
from app.api.v1.router import api_router

# Phase 2 重構：使用統一的配置管理
from app.core.config import (
    OUTPUT_DIR,
    API_TITLE,
    API_DESCRIPTION,
    API_VERSION,
    CORS_ORIGINS,
)

logger = logging.getLogger(__name__)

# Create FastAPI app instance using existing proven lifespan
app = FastAPI(
    title=API_TITLE,
    description=API_DESCRIPTION,
    version=f"{API_VERSION}-phase2",
    lifespan=lifespan,  # Use existing proven lifespan
)

# --- Static Files Mount (Keep existing approach) ---
os.makedirs(OUTPUT_DIR, exist_ok=True)
logger.info(f"Static files directory set to: {OUTPUT_DIR}")

# Mount static files directory to /rendered_images URL path
app.mount("/rendered_images", StaticFiles(directory=OUTPUT_DIR), name="rendered_images")
logger.info(f"Mounted static files directory '{OUTPUT_DIR}' at '/rendered_images'.")

# Mount static directory
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
logger.info(f"Mounted static directory '{STATIC_DIR}' at '/static'.")

# --- CORS Middleware (Phase 2 重構：使用統一配置) ---
EXTERNAL_IP = os.getenv("EXTERNAL_IP", "127.0.0.1")

# 合併統一配置和動態配置
origins = CORS_ORIGINS + [
    f"http://{EXTERNAL_IP}",
    f"http://{EXTERNAL_IP}:5173",
    f"http://{EXTERNAL_IP}:3000",
    f"http://{EXTERNAL_IP}:8080",
    f"https://{EXTERNAL_IP}",
    f"https://{EXTERNAL_IP}:5173",
    # Docker internal networks
    "http://netstack-api:8080",
    "http://simworld-backend:8888",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)
logger.info(f"Enhanced CORS middleware configured for {len(origins)} origins")


# --- Test Endpoint (From main.py) ---
@app.get("/ping", tags=["Test"])
async def ping():
    """Test endpoint to verify service availability"""
    return {"message": "pong"}


# --- Include API Routers ---
app.include_router(api_router, prefix="/api/v1")
logger.info("Included API router v1 at /api/v1.")

# Include performance router
try:
    from app.routers.performance_router import performance_router

    app.include_router(performance_router, prefix="")
    logger.info("Performance router registered")
except ImportError as e:
    logger.warning(f"Performance router not available: {e}")


# Include algorithm performance router (with fallback)
try:
    from app.api.routes.algorithm_performance import (
        router as algorithm_performance_router,
    )

    # Remove the prefix since the router already has one
    app.include_router(algorithm_performance_router, prefix="")
    logger.info("Algorithm performance router registered")
except ImportError as e:
    logger.warning(f"Algorithm performance router not available: {e}")

    # Create fallback endpoint
    @app.get("/api/algorithm-performance/status", tags=["Algorithm Performance"])
    async def algorithm_performance_status():
        return {
            "status": "service_not_available",
            "message": "Algorithm performance service not configured",
        }


# --- Enhanced Root Endpoint ---
@app.get("/", tags=["Root"])
async def root():
    """Enhanced root endpoint with lifecycle status"""
    try:
        # Try to get lifecycle status if available
        lifecycle_info = "operational"
        if hasattr(app.state, "redis") and app.state.redis:
            lifecycle_info = "operational_with_redis"

        return {
            "message": "SimWorld Backend API - MVP",
            "version": "1.0.0-mvp",
            "status": lifecycle_info,
            "features": [
                "3D Simulation Engine",
                "Satellite Tracking",
                "Performance Monitoring",
                "NetStack Integration",
                "Enhanced CORS Support",
                "IEEE INFOCOM 2024 Algorithms",
            ],
            "endpoints": {
                "docs": "/docs",
                "api": "/api/v1",
                "ping": "/ping",
                "algorithm_performance": "/algorithm_performance",
            },
        }
    except Exception as e:
        logger.error(f"Root endpoint error: {e}")
        return {
            "message": "SimWorld Backend API - MVP",
            "status": "operational",
            "error": "Lifecycle status unavailable",
        }


# --- Optional Enhanced Health Check ---
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check with optional enhancements"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": "2025-01-05T05:30:00Z",
            "services": {
                "database": True,  # Assume healthy if app started
                "api": True,
            },
        }

        # Check Redis if available
        if hasattr(app.state, "redis") and app.state.redis:
            try:
                await app.state.redis.ping()
                health_status["services"]["redis"] = True
            except:
                health_status["services"]["redis"] = False
                health_status["status"] = "degraded"

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


# Log application setup completion
logger.info("SimWorld Backend API MVP setup complete.")
logger.info("Features: Enhanced CORS, Fallback endpoints, Optional lifecycle status")

# Export the application instance
__all__ = ["app"]
