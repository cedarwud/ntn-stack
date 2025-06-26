"""健康檢查路由模組"""
from fastapi import APIRouter
from datetime import datetime
from typing import Dict, Any

router = APIRouter(tags=["健康檢查"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康檢查端點"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "NetStack API is running"
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """就緒檢查端點"""
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat()
    }