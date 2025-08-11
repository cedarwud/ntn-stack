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
    # Phase 2 重構：使用統一的配置管理
    from app.core.config import PROMETHEUS_URL, ALERTMANAGER_URL, MONITORING_ENABLED
    
    return {
        "prometheus_url": PROMETHEUS_URL,
        "alertmanager_url": ALERTMANAGER_URL,
        "monitoring_enabled": MONITORING_ENABLED
    }
