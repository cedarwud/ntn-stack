"""
統一時間序列數據 API 端點
基於本地 Docker Volume 數據，提供 120 分鐘統一時間序列
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
import logging

from ...services.local_volume_data_service import get_local_volume_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/unified/timeseries")
async def get_unified_timeseries_data(
    constellation: str = Query("starlink", description="星座名稱 (starlink/oneweb)"),
    reference_lat: float = Query(24.9441, description="參考緯度"),
    reference_lon: float = Query(121.3714, description="參考經度"),
    reference_alt: float = Query(0.0, description="參考高度(米)")
) -> Dict[str, Any]:
    """
    獲取統一 120 分鐘時間序列數據
    基於本地 Docker Volume 數據，零網路依賴
    """
    try:
        # 驗證星座支援
        if constellation not in ["starlink", "oneweb"]:
            raise HTTPException(
                status_code=400,
                detail=f"不支援的星座: {constellation}。僅支援 starlink, oneweb"
            )
        
        reference_location = {
            "latitude": reference_lat,
            "longitude": reference_lon,
            "altitude": reference_alt
        }
        
        logger.info(f"🛰️ 請求統一時間序列數據: {constellation}")
        logger.info(f"📍 參考位置: {reference_lat:.4f}°N, {reference_lon:.4f}°E")
        
        # 使用本地 Volume 數據服務
        volume_service = get_local_volume_service()
        
        # 檢查數據可用性
        if not volume_service.is_data_available():
            raise HTTPException(
                status_code=503,
                detail="本地衛星數據不可用，請檢查 Docker Volume 掛載"
            )
        
        # 生成統一時間序列數據
        unified_data = await volume_service.generate_120min_timeseries(
            constellation=constellation,
            reference_location=reference_location
        )
        
        if not unified_data:
            raise HTTPException(
                status_code=500,
                detail=f"生成 {constellation} 時間序列數據失敗"
            )
        
        logger.info(f"✅ 成功提供統一時間序列數據: {unified_data['metadata']['satellites_processed']} 顆衛星")
        
        return {
            "success": True,
            "data": unified_data,
            "message": f"成功生成 {constellation} 120分鐘統一時間序列數據"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 統一時間序列數據 API 錯誤: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"內部服務錯誤: {str(e)}"
        )


@router.get("/unified/timeseries/health")
async def check_unified_timeseries_health() -> Dict[str, Any]:
    """檢查統一時間序列數據服務健康狀態"""
    try:
        volume_service = get_local_volume_service()
        
        # 檢查數據新鮮度
        freshness_info = await volume_service.check_data_freshness()
        
        # 檢查數據可用性
        data_available = volume_service.is_data_available()
        
        health_status = {
            "service": "unified_timeseries",
            "status": "healthy" if data_available else "unhealthy",
            "data_available": data_available,
            "data_freshness": freshness_info,
            "supported_constellations": ["starlink", "oneweb"],
            "time_span_minutes": 120,
            "time_interval_seconds": 10,
            "total_time_points": 720
        }
        
        status_code = 200 if data_available else 503
        
        return {
            "success": data_available,
            "health": health_status,
            "message": "統一時間序列服務健康檢查完成"
        }
        
    except Exception as e:
        logger.error(f"❌ 健康檢查失敗: {e}")
        return {
            "success": False,
            "health": {
                "service": "unified_timeseries",
                "status": "error",
                "error": str(e)
            },
            "message": "健康檢查失敗"
        }


@router.get("/unified/timeseries/metadata")
async def get_timeseries_metadata(
    constellation: str = Query("starlink", description="星座名稱")
) -> Dict[str, Any]:
    """獲取時間序列數據的元數據資訊"""
    try:
        if constellation not in ["starlink", "oneweb"]:
            raise HTTPException(
                status_code=400,
                detail=f"不支援的星座: {constellation}"
            )
        
        volume_service = get_local_volume_service()
        
        # 檢查本地 TLE 数据
        tle_data = await volume_service.get_local_tle_data(constellation)
        
        metadata = {
            "constellation": constellation,
            "satellites_available": len(tle_data) if tle_data else 0,
            "time_configuration": {
                "time_span_minutes": 120,
                "time_interval_seconds": 10,
                "total_time_points": 720
            },
            "data_source": "local_docker_volume_direct",
            "network_dependency": False,
            "supported_events": ["D1", "D2", "A4", "T1"],
            "position_calculation": "simplified_orbital_model",
            "reference_location_default": {
                "latitude": 24.9441,
                "longitude": 121.3714,
                "name": "國立台北科技大學"
            }
        }
        
        return {
            "success": True,
            "metadata": metadata,
            "message": f"{constellation} 時間序列元數據"
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取元數據失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取元數據失敗: {str(e)}"
        )