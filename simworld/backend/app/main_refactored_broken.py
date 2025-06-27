"""
Refactored Main Application

Updated to use the unified lifecycle manager instead of scattered lifecycle code.
Part of Phase 3 service layer refactoring.
"""

import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import unified lifecycle management
from app.core.lifecycle_manager import lifespan_context
from app.core.service_registry import register_all_services, get_registered_services_info
from app.api.v1.router import api_router
from app.core.config import OUTPUT_DIR

logger = logging.getLogger(__name__)

# Register all services before creating the app
register_all_services()

# Log registered services for debugging
services_info = get_registered_services_info()
logger.info(f"Registered {len(services_info)} services for lifecycle management")
for service_info in services_info:
    logger.debug(f"Service: {service_info['name']} (Priority: {service_info['priority']}, Critical: {service_info['critical']})")

# Create FastAPI app instance with unified lifecycle management
app = FastAPI(
    title="SimWorld Backend API",
    description="Unified API for SimWorld 3D simulation engine with NetStack integration",
    version="1.0.0",
    lifespan=lifespan_context,  # Use unified lifecycle context manager
)

# --- Static Files Mount ---
# Ensure static files directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)
logger.info(f"Static files directory set to: {OUTPUT_DIR}")

# Mount static files directory to /rendered_images URL path (maintain compatibility with frontend)
app.mount("/rendered_images", StaticFiles(directory=OUTPUT_DIR), name="rendered_images")
logger.info(f"Mounted static files directory '{OUTPUT_DIR}' at '/rendered_images'.")

# Mount static directory
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
logger.info(f"Mounted static directory '{STATIC_DIR}' at '/static'.")

# --- CORS Middleware ---
# Get external IP from environment variable, default to localhost for safety
EXTERNAL_IP = os.getenv("EXTERNAL_IP", "127.0.0.1")

# Allow cross-origin requests from specific domains, including production environment IP addresses
origins = [
    "http://localhost",
    "http://localhost:5173",  # Local development environment
    "http://127.0.0.1:5173",
    f"http://{EXTERNAL_IP}",
    f"http://{EXTERNAL_IP}:5173",  # External environment IP address
    f"http://{EXTERNAL_IP}:3000",
    f"http://{EXTERNAL_IP}:8080",
    f"https://{EXTERNAL_IP}",
    f"https://{EXTERNAL_IP}:5173",
    # NetStack integration endpoints
    "http://172.20.0.40",     # NetStack API container
    "http://172.20.0.40:8080",
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

logger.info(f"CORS middleware configured for origins: {origins}")

# --- API Router Registration ---
# Include the main API router with all endpoints
app.include_router(api_router, prefix="/api/v1")
logger.info("Main API router registered at /api/v1")

# --- Health Check Endpoint ---
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with basic application information"""
    from app.core.lifecycle_manager import get_lifecycle_status
    
    lifecycle_status = get_lifecycle_status()
    
    return {
        "message": "SimWorld Backend API",
        "version": "1.0.0",
        "status": "operational",
        "lifecycle": {
            "phase": lifecycle_status["phase"],
            "services_started": len(lifecycle_status["started_services"]),
            "total_services": lifecycle_status["total_services"]
        },
        "features": [
            "3D Simulation Engine",
            "Satellite Tracking",
            "Performance Monitoring", 
            "NetStack Integration",
            "Real-time WebSocket",
            "IEEE INFOCOM 2024 Algorithms"
        ],
        "endpoints": {
            "docs": "/docs",
            "api": "/api/v1",
            "health": "/health"
        }
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Comprehensive health check endpoint"""
    from app.core.lifecycle_manager import get_lifecycle_status
    
    try:
        lifecycle_status = get_lifecycle_status()
        
        # Check if all critical services are running
        all_services_healthy = lifecycle_status["phase"] == "running"
        
        return {
            "status": "healthy" if all_services_healthy else "degraded",
            "timestamp": lifecycle_status["timestamp"],
            "lifecycle": lifecycle_status,
            "services": {
                "database": "database" in lifecycle_status["started_services"],
                "redis": "redis" in lifecycle_status["started_services"], 
                "scheduler": "satellite_scheduler" in lifecycle_status["started_services"],
                "cqrs": "cqrs_satellite_service" in lifecycle_status["started_services"],
                "performance": "performance_services" in lifecycle_status["started_services"]
            },
            "integration": {
                "netstack_available": True,  # TODO: Add actual NetStack connectivity check
                "containers_running": True   # TODO: Add actual container health check
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": lifecycle_status.get("timestamp") if 'lifecycle_status' in locals() else None
        }

@app.get("/debug/lifecycle", tags=["Debug"])
async def debug_lifecycle():
    """Debug endpoint for lifecycle management status"""
    from app.core.lifecycle_manager import get_lifecycle_status
    
    lifecycle_status = get_lifecycle_status()
    services_info = get_registered_services_info()
    
    return {
        "lifecycle_status": lifecycle_status,
        "registered_services": services_info,
        "service_registration_order": [s["name"] for s in sorted(services_info, key=lambda x: x["priority"])]
    }

# Log application setup completion
logger.info("FastAPI application setup complete with unified lifecycle management.")
logger.info("Application ready for deployment with proper service coordination.")

# Export the application instance
__all__ = ["app"]