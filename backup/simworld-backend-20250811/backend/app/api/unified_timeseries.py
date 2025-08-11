"""
統一時間序列 API 端點
支援 120 分鐘預處理數據和動態生成
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
import logging

from ..services.local_volume_data_service import get_local_volume_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/satellites", tags=["unified_timeseries"])

@router.get("/unified/timeseries")
async def get_unified_timeseries_data(
    constellation: str = Query("starlink", description="星座名稱 (starlink, oneweb)"),
    reference_lat: float = Query(24.9441, description="參考位置緯度"),
    reference_lon: float = Query(121.3714, description="參考位置經度"),
    reference_alt: float = Query(0.0, description="參考位置高度 (米)")
) -> Dict[str, Any]:
    """
    獲取統一 120 分鐘時間序列數據
    
    優先使用預處理數據，不可用時動態生成
    基於 Docker Volume 本地數據，無網路依賴
    """
    try:
        # 驗證星座支援
        supported_constellations = ["starlink", "oneweb"]
        if constellation not in supported_constellations:
            raise HTTPException(
                status_code=400,
                detail=f"不支援的星座: {constellation}。僅支援 {', '.join(supported_constellations)}"
            )
        
        # 驗證參數範圍
        if not (-90 <= reference_lat <= 90):
            raise HTTPException(status_code=400, detail="緯度必須在 -90 到 90 之間")
        
        if not (-180 <= reference_lon <= 180):
            raise HTTPException(status_code=400, detail="經度必須在 -180 到 180 之間")
        
        if reference_alt < 0:
            raise HTTPException(status_code=400, detail="高度不能為負數")
        
        # 構建參考位置
        reference_location = {
            "latitude": reference_lat,
            "longitude": reference_lon,
            "altitude": reference_alt
        }
        
        logger.info(f"🌐 統一時間序列請求 - 星座: {constellation}, 位置: {reference_lat:.4f}°N, {reference_lon:.4f}°E")
        
        # 獲取本地數據服務
        volume_service = get_local_volume_service()
        
        # 生成統一時間序列數據
        unified_data = await volume_service.generate_120min_timeseries(
            constellation=constellation,
            reference_location=reference_location
        )
        
        if not unified_data:
            raise HTTPException(
                status_code=500,
                detail=f"無法生成 {constellation} 時間序列數據"
            )
        
        # 添加 API 響應元數據
        unified_data["metadata"]["api_version"] = "v1"
        unified_data["metadata"]["endpoint"] = "/api/v1/satellites/unified/timeseries"
        unified_data["metadata"]["request_params"] = {
            "constellation": constellation,
            "reference_location": reference_location
        }
        
        logger.info(f"✅ 成功返回統一時間序列數據: {len(unified_data.get('satellites', []))} 顆衛星")
        
        return unified_data
        
    except HTTPException:
        # 重新拋出 HTTP 異常
        raise
    except Exception as e:
        logger.error(f"❌ 統一時間序列 API 失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"內部服務錯誤: {str(e)}"
        )

@router.get("/unified/status")
async def get_unified_timeseries_status() -> Dict[str, Any]:
    """
    獲取統一時間序列服務狀態
    """
    try:
        volume_service = get_local_volume_service()
        
        # 檢查數據可用性
        data_available = volume_service.is_data_available()
        
        # 檢查數據新鮮度
        freshness_info = await volume_service.check_data_freshness()
        
        status = {
            "service_name": "unified_timeseries",
            "version": "1.0.0",
            "data_available": data_available,
            "supported_constellations": ["starlink", "oneweb"],
            "time_span_minutes": 120,
            "time_interval_seconds": 10,
            "total_time_points": 720,
            "data_sources": ["preprocess_timeseries", "dynamic_generation"],
            "freshness_info": freshness_info
        }
        
        return status
        
    except Exception as e:
        logger.error(f"❌ 統一時間序列狀態檢查失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"狀態檢查失敗: {str(e)}"
        )

@router.get("/unified/health")
async def get_unified_timeseries_health() -> Dict[str, Any]:
    """
    統一時間序列服務健康檢查
    """
    try:
        volume_service = get_local_volume_service()
        
        # 基本健康檢查
        health_status = {
            "status": "healthy",
            "timestamp": "2025-07-31T00:00:00Z",
            "checks": {}
        }
        
        # 檢查數據路徑
        try:
            data_available = volume_service.is_data_available()
            health_status["checks"]["data_availability"] = {
                "status": "pass" if data_available else "warn",
                "message": "數據可用" if data_available else "數據不可用，將使用動態生成"
            }
        except Exception as e:
            health_status["checks"]["data_availability"] = {
                "status": "fail",
                "message": f"數據檢查失敗: {str(e)}"
            }
        
        # 檢查 SGP4 計算器
        try:
            from ..services.sgp4_calculator import SGP4Calculator
            sgp4_calc = SGP4Calculator()
            health_status["checks"]["sgp4_calculator"] = {
                "status": "pass",
                "message": "SGP4 計算器可用"
            }
        except Exception as e:
            health_status["checks"]["sgp4_calculator"] = {
                "status": "fail",
                "message": f"SGP4 計算器失敗: {str(e)}"
            }
        
        # 總體健康狀態
        failed_checks = [check for check in health_status["checks"].values() if check["status"] == "fail"]
        if failed_checks:
            health_status["status"] = "unhealthy"
        elif any(check["status"] == "warn" for check in health_status["checks"].values()):
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ 健康檢查失敗: {e}")
        return {
            "status": "unhealthy",
            "timestamp": "2025-07-31T00:00:00Z",
            "error": str(e)
        }