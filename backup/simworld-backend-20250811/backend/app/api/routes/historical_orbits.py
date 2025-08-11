"""
歷史軌道數據 API 端點
提供基於真實歷史 TLE 數據的軌道計算服務
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from app.services.historical_orbit_generator import HistoricalOrbitGenerator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/satellites", tags=["historical-orbits"])


@router.get("/historical-orbits")
async def generate_historical_orbit_data(
    constellation: str = Query("starlink", description="星座名稱"),
    duration_hours: int = Query(6, ge=1, le=24, description="計算持續時間 (小時)"),
    time_step_minutes: int = Query(5, ge=1, le=60, description="時間步長 (分鐘)"),
    observer_lat: Optional[float] = Query(None, ge=-90, le=90, description="觀測者緯度"),
    observer_lon: Optional[float] = Query(None, ge=-180, le=180, description="觀測者經度"),
    observer_alt: Optional[float] = Query(None, ge=0, le=10000, description="觀測者高度 (公尺)"),
    observer_name: Optional[str] = Query(None, description="觀測位置名稱")
) -> Dict[str, Any]:
    """
    生成基於歷史真實 TLE 數據的軌道計算結果
    
    當 NetStack 預計算數據不可用時，此端點提供真實數據的 fallback
    """
    try:
        logger.info(f"🛰️ 生成 {constellation} 歷史軌道數據請求")
        
        # 創建歷史軌道生成器
        generator = HistoricalOrbitGenerator()
        
        # 設置觀測位置
        observer_location = None
        if observer_lat is not None and observer_lon is not None:
            observer_location = {
                "latitude": observer_lat,
                "longitude": observer_lon,
                "altitude": observer_alt or 50.0,
                "name": observer_name or f"Observer_{observer_lat:.2f}_{observer_lon:.2f}"
            }
        
        # 生成軌道數據
        orbit_data = await generator.generate_precomputed_orbit_data(
            constellation=constellation,
            duration_hours=duration_hours,
            time_step_minutes=time_step_minutes,
            observer_location=observer_location
        )
        
        # 添加 API 響應元數據
        orbit_data["api_metadata"] = {
            "endpoint": "/satellites/historical-orbits",
            "generation_time": datetime.utcnow().isoformat(),
            "request_parameters": {
                "constellation": constellation,
                "duration_hours": duration_hours,
                "time_step_minutes": time_step_minutes,
                "observer_location": observer_location
            },
            "data_source": "historical_tle_real_data",
            "is_simulation": False,
            "description": "基於真實歷史 TLE 數據的軌道計算"
        }
        
        logger.info(f"✅ 成功生成 {constellation} 歷史軌道數據")
        return orbit_data
        
    except Exception as e:
        logger.error(f"❌ 歷史軌道數據生成失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"歷史軌道數據生成失敗: {str(e)}"
        )


@router.get("/historical-orbits/health")
async def get_historical_orbits_health() -> Dict[str, Any]:
    """檢查歷史軌道服務健康狀態"""
    try:
        # 檢查歷史數據可用性
        from app.data.historical_tle_data import get_historical_tle_data, get_data_source_info
        
        # 測試各星座數據
        constellation_status = {}
        for constellation in ["starlink", "oneweb", "gps", "galileo"]:
            data = get_historical_tle_data(constellation)
            constellation_status[constellation] = {
                "available": len(data) > 0,
                "satellite_count": len(data),
                "status": "healthy" if len(data) > 0 else "no_data"
            }
        
        # 獲取數據源信息
        data_source_info = get_data_source_info()
        
        # 測試軌道生成器
        generator = HistoricalOrbitGenerator()
        generator_status = "healthy"
        
        return {
            "service_status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "constellation_data": constellation_status,
            "data_source": data_source_info,
            "orbit_generator": {
                "status": generator_status,
                "description": "歷史軌道生成器運行正常"
            },
            "capabilities": {
                "max_duration_hours": 24,
                "min_time_step_minutes": 1,
                "max_time_step_minutes": 60,
                "supported_constellations": list(constellation_status.keys())
            }
        }
        
    except Exception as e:
        logger.error(f"❌ 歷史軌道服務健康檢查失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"健康檢查失敗: {str(e)}"
        )


@router.get("/historical-orbits/constellations")
async def get_available_constellations() -> Dict[str, Any]:
    """獲取可用的星座列表及其數據統計"""
    try:
        from app.data.historical_tle_data import get_historical_tle_data
        
        constellations = {}
        for constellation in ["starlink", "oneweb", "gps", "galileo"]:
            data = get_historical_tle_data(constellation)
            
            if data:
                # 獲取第一顆衛星的示例信息
                sample_satellite = data[0]
                
                constellations[constellation] = {
                    "name": constellation.upper(),
                    "satellite_count": len(data),
                    "data_date": sample_satellite.get("launch_date", "2024-12"),
                    "sample_norad_ids": [sat["norad_id"] for sat in data[:3]],
                    "available": True
                }
            else:
                constellations[constellation] = {
                    "name": constellation.upper(),
                    "satellite_count": 0,
                    "available": False
                }
        
        return {
            "constellations": constellations,
            "total_satellites": sum(c["satellite_count"] for c in constellations.values()),
            "available_constellations": [k for k, v in constellations.items() if v["available"]],
            "data_source": "historical_tle_real_data"
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取星座列表失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取星座列表失敗: {str(e)}"
        )


@router.post("/historical-orbits/save")
async def save_historical_orbit_data(
    constellation: str = Query("starlink", description="星座名稱"),
    duration_hours: int = Query(6, ge=1, le=24, description="計算持續時間 (小時)"),
    output_filename: Optional[str] = Query(None, description="輸出文件名")
) -> Dict[str, Any]:
    """
    生成並保存歷史軌道數據到文件
    用於創建預計算數據文件
    """
    try:
        logger.info(f"🛰️ 生成並保存 {constellation} 歷史軌道數據")
        
        # 創建歷史軌道生成器
        generator = HistoricalOrbitGenerator()
        
        # 生成軌道數據
        orbit_data = await generator.generate_precomputed_orbit_data(
            constellation=constellation,
            duration_hours=duration_hours,
            time_step_minutes=1  # 高精度數據
        )
        
        # 確定保存路徑
        if not output_filename:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_filename = f"historical_{constellation}_orbits_{timestamp}.json"
        
        output_path = f"/tmp/{output_filename}"
        
        # 保存到文件
        success = await generator.save_precomputed_data_to_file(orbit_data, output_path)
        
        if success:
            return {
                "status": "success",
                "message": f"歷史軌道數據已保存",
                "output_file": output_path,
                "constellation": constellation,
                "duration_hours": duration_hours,
                "satellite_count": len(orbit_data["constellations"][constellation]["orbit_data"]["satellites"]),
                "generation_time": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="保存文件失敗"
            )
        
    except Exception as e:
        logger.error(f"❌ 保存歷史軌道數據失敗: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"保存失敗: {str(e)}"
        )