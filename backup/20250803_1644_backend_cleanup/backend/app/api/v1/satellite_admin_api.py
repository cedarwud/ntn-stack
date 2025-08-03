"""
衛星管理 API
提供手動觸發更新和管理功能
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any

from app.services import satellite_scheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/satellite/admin", tags=["satellite-admin"])


class UpdateResponse(BaseModel):
    """更新響應模型"""
    success: bool
    message: str
    details: Dict[str, Any] = {}


@router.post("/force-update", response_model=UpdateResponse)
async def force_satellite_update():
    """
    強制執行一次衛星數據更新
    
    這會立即觸發：
    1. 從 Celestrak 獲取最新 OneWeb TLE 數據
    2. 更新 Redis 緩存
    3. 同步到資料庫
    4. 清理過期數據
    """
    try:
        if not satellite_scheduler.scheduler:
            raise HTTPException(
                status_code=503, 
                detail="衛星數據調度器未運行"
            )
        
        logger.info("收到手動更新請求")
        await satellite_scheduler.scheduler.force_update()
        
        return UpdateResponse(
            success=True,
            message="衛星數據更新完成",
            details={
                "update_type": "manual",
                "timestamp": "2025-06-13T11:20:00Z"
            }
        )
    
    except Exception as e:
        logger.error(f"手動更新失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"更新失敗: {str(e)}"
        )


@router.get("/status", response_model=Dict[str, Any])
async def get_scheduler_status():
    """
    獲取調度器狀態信息
    """
    try:
        if not satellite_scheduler.scheduler:
            return {
                "scheduler_running": False,
                "message": "調度器未運行"
            }
        
        return {
            "scheduler_running": satellite_scheduler.scheduler.is_running,
            "update_interval": "每週",
            "next_check": "每日檢查",
            "message": "調度器正常運行"
        }
    
    except Exception as e:
        logger.error(f"獲取調度器狀態失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"獲取狀態失敗: {str(e)}"
        )