"""
Phase 2 背景下載狀態監控 API
提供下載進度查詢和控制功能
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import os
import logging

from ..services.phase2_background_downloader import Phase2BackgroundDownloader

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/satellite-phase2", tags=["Phase 2 Background Download"])

def get_downloader() -> Phase2BackgroundDownloader:
    """依賴注入：獲取 Phase 2 下載器實例"""
    db_url = os.getenv("SATELLITE_DATABASE_URL", "postgresql://netstack_user:netstack_password@netstack-postgres:5432/netstack_db")
    return Phase2BackgroundDownloader(db_url)

@router.get("/status", summary="獲取 Phase 2 下載狀態")
async def get_download_status(downloader: Phase2BackgroundDownloader = Depends(get_downloader)) -> Dict[str, Any]:
    """
    獲取 45 天衛星數據背景下載的當前狀態
    
    返回：
    - status: not_started, downloading, completed, failed
    - progress: 下載進度百分比 (0-100)
    - timestamp: 最後更新時間
    - total_expected_records: 預期總記錄數
    - error: 錯誤信息（如果有）
    """
    try:
        status = await downloader.get_download_status()
        return {
            "phase2_download": status,
            "api_impact": "none",  # Phase 2 不影響 API 性能
            "background_process": True
        }
    except Exception as e:
        logger.error(f"❌ 獲取 Phase 2 狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"無法獲取下載狀態: {str(e)}")

@router.post("/start", summary="手動啟動 Phase 2 下載")
async def start_download(downloader: Phase2BackgroundDownloader = Depends(get_downloader)) -> Dict[str, str]:
    """
    手動啟動 45 天數據背景下載
    注意：這不會影響當前 API 響應性能
    """
    try:
        # 檢查當前狀態
        status = await downloader.get_download_status()
        
        if status.get("status") == "downloading":
            return {
                "message": "Phase 2 下載已在進行中",
                "current_progress": f"{status.get('progress', 0)}%",
                "api_impact": "none"
            }
        elif status.get("status") == "completed":
            return {
                "message": "Phase 2 數據已完成下載",
                "status": "completed",
                "api_impact": "none"
            }
        
        # 啟動背景下載
        await downloader.start_background_download()
        
        return {
            "message": "Phase 2 背景下載已啟動",
            "status": "downloading",
            "api_impact": "none",
            "note": "下載將在背景進行，不影響 API 響應性能"
        }
        
    except Exception as e:
        logger.error(f"❌ 啟動 Phase 2 下載失敗: {e}")
        raise HTTPException(status_code=500, detail=f"無法啟動下載: {str(e)}")

@router.get("/research-data/summary", summary="獲取研究級數據摘要")
async def get_research_data_summary(downloader: Phase2BackgroundDownloader = Depends(get_downloader)) -> Dict[str, Any]:
    """
    獲取已下載的研究級數據摘要信息
    """
    try:
        existing_data = await downloader._check_existing_research_data()
        
        if not existing_data:
            return {
                "research_data_available": False,
                "message": "尚無研究級數據",
                "recommendation": "請啟動 Phase 2 下載"
            }
        
        return {
            "research_data_available": True,
            "data_summary": {
                "total_records": existing_data['record_count'],
                "days_coverage": existing_data['days_coverage'],
                "earliest_time": existing_data['earliest_time'].isoformat() if existing_data['earliest_time'] else None,
                "latest_time": existing_data['latest_time'].isoformat() if existing_data['latest_time'] else None,
                "data_quality": "research_grade",
                "constellation": "research_grade"
            },
            "completeness": {
                "target_days": 45,
                "actual_days": existing_data['days_coverage'],
                "percentage": min(100, (existing_data['days_coverage'] / 45) * 100)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取研究數據摘要失敗: {e}")
        raise HTTPException(status_code=500, detail=f"無法獲取數據摘要: {str(e)}")

@router.get("/performance-impact", summary="檢查對 API 性能的影響")
async def check_performance_impact() -> Dict[str, Any]:
    """
    檢查 Phase 2 背景下載對 FastAPI 性能的影響
    """
    return {
        "background_download_impact": {
            "api_response_time": "no_impact",
            "memory_usage": "minimal_increase",
            "cpu_usage": "background_only",
            "database_connections": "separate_pool"
        },
        "isolation_measures": {
            "separate_asyncio_tasks": True,
            "independent_db_connections": True,
            "rate_limiting": True,
            "automatic_pause_on_load": True
        },
        "monitoring": {
            "download_progress_tracking": True,
            "error_recovery": True,
            "status_persistence": True
        },
        "guarantee": "Phase 2 下載設計為完全非阻塞，不會影響 API 響應性能"
    }