"""
NetStack API 健康檢查端點
"""

from fastapi import APIRouter
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/health",
    tags=["health"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=Dict[str, Any])
async def health_check():
    """
    系統健康檢查
    """
    try:
        # 導入健康服務
        from ...services.health_service import get_health_status
        
        health_status = await get_health_status()
        return health_status
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return {
            "overall_status": "unhealthy",
            "error": str(e)
        }