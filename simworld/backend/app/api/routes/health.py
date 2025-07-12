"""
System monitoring endpoints for the API
"""

from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()

@router.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {"status": "healthy", "service": "simworld-backend"}

@router.get("/monitoring-config")
async def get_monitoring_config():
    """Get current monitoring configuration"""
    import os
    return {
        "prometheus_url": os.getenv("PROMETHEUS_URL", "http://localhost:9090"),
        "alertmanager_url": os.getenv("ALERTMANAGER_URL", "http://localhost:9093"),
        "monitoring_enabled": True
    }
