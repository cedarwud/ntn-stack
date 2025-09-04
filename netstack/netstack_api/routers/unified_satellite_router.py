"""
統一衛星數據路由器
為前端提供統一的衛星數據API，基於真實TLE和SGP4軌道計算
"""

from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Query, HTTPException
import structlog

from .simple_satellite_router import get_visible_satellites

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/satellite", tags=["Unified Satellite Data"])

@router.get("/unified")
async def get_unified_satellite_data(
    time: str = Query("", description="ISO時間戳，空字符串使用當前時間"),
    constellation: str = Query("both", description="星座選擇: starlink, oneweb, both"),
    count: int = Query(100, description="最大衛星數量"),
    min_elevation_deg: float = Query(10.0, description="最小仰角度數")
):
    """
    統一衛星數據API端點 - 基於真實TLE和SGP4軌道計算
    
    使用netstack/tle_data/中的真實TLE數據和Stage 6預計算結果
    確保符合CLAUDE.md的"REAL ALGORITHMS ONLY"原則
    """
    try:
        logger.info(f"🛰️ 統一衛星數據請求: constellation={constellation}, time={time}")
        
        # 處理時間參數
        current_time = datetime.now(timezone.utc).isoformat() + 'Z' if not time else time
        
        all_satellites = []
        
        # 根據星座選擇獲取數據
        if constellation in ["starlink", "both"]:
            starlink_satellites = await get_visible_satellites(
                count=max(15, count//2) if constellation == "both" else count,
                constellation="starlink",
                min_elevation_deg=min_elevation_deg,
                utc_timestamp=current_time
            )
            # 轉換格式以匹配前端需求
            for sat in starlink_satellites.get("satellites", []):
                unified_sat = {
                    "id": str(sat.get("norad_id", sat.get("satellite_id", "unknown"))),
                    "norad_id": str(sat.get("norad_id", sat.get("satellite_id", "unknown"))),
                    "name": sat.get("name", f"starlink_{sat.get('norad_id', 'unknown')}"),
                    "elevation_deg": sat.get("elevation_deg", 0),
                    "azimuth_deg": sat.get("azimuth_deg", 0),  
                    "distance_km": sat.get("range_km", 0),
                    "is_visible": sat.get("is_visible", sat.get("elevation_deg", 0) >= min_elevation_deg),
                    "constellation": "starlink",
                    "last_updated": current_time
                }
                all_satellites.append(unified_sat)
        
        if constellation in ["oneweb", "both"]:
            oneweb_satellites = await get_visible_satellites(
                count=max(8, count//3) if constellation == "both" else count,
                constellation="oneweb",
                min_elevation_deg=min_elevation_deg,
                utc_timestamp=current_time
            )
            # 轉換格式以匹配前端需求
            for sat in oneweb_satellites.get("satellites", []):
                unified_sat = {
                    "id": str(sat.get("norad_id", sat.get("satellite_id", "unknown"))),
                    "norad_id": str(sat.get("norad_id", sat.get("satellite_id", "unknown"))),
                    "name": sat.get("name", f"oneweb_{sat.get('norad_id', 'unknown')}"),
                    "elevation_deg": sat.get("elevation_deg", 0),
                    "azimuth_deg": sat.get("azimuth_deg", 0),
                    "distance_km": sat.get("range_km", 0), 
                    "is_visible": sat.get("is_visible", sat.get("elevation_deg", 0) >= min_elevation_deg),
                    "constellation": "oneweb",
                    "last_updated": current_time
                }
                all_satellites.append(unified_sat)
        
        # 按仰角排序
        all_satellites.sort(key=lambda x: x["elevation_deg"], reverse=True)
        
        response = {
            "satellites": all_satellites[:count],
            "total_count": len(all_satellites),
            "metadata": {
                "timestamp": current_time,
                "constellation": constellation,
                "min_elevation_deg": min_elevation_deg,
                "data_source": "real_tle_sgp4",
                "stage6_optimized": True
            }
        }
        
        logger.info(f"✅ 返回 {len(all_satellites)} 顆真實軌道計算的衛星數據")
        return response
        
    except Exception as e:
        logger.error(f"❌ 統一衛星數據API錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"衛星數據獲取失敗: {str(e)}")

@router.get("/time-base")
async def get_tle_time_base():
    """獲取TLE數據的基準時間信息，供前端使用"""
    try:
        import os
        from pathlib import Path
        
        tle_data_dir = Path("/app/tle_data")
        time_base_info = {}
        
        for constellation in ['starlink', 'oneweb']:
            tle_dir = tle_data_dir / constellation / "tle"
            if tle_dir.exists():
                tle_files = list(tle_dir.glob(f"{constellation}_*.tle"))
                if tle_files:
                    # 找出最新日期的檔案
                    latest_date = None
                    latest_file = None
                    
                    for tle_file in tle_files:
                        date_str = tle_file.stem.split('_')[-1]
                        if latest_date is None or date_str > latest_date:
                            latest_date = date_str
                            latest_file = tle_file
                    
                    # 解析日期並創建基準時間
                    if latest_date:
                        try:
                            year = int(latest_date[:4])
                            month = int(latest_date[4:6])
                            day = int(latest_date[6:8])
                            base_time = datetime(year, month, day, 12, 0, 0, timezone.utc)
                            
                            time_base_info[constellation] = {
                                "tle_file_date": latest_date,
                                "base_time_iso": base_time.isoformat(),
                                "base_time_unix": int(base_time.timestamp())
                            }
                        except (ValueError, IndexError):
                            time_base_info[constellation] = {
                                "error": f"無法解析日期 {latest_date}"
                            }
        
        # 統一基準時間（使用所有星座中最新的日期）
        if time_base_info:
            all_dates = [info.get("tle_file_date", "00000000") for info in time_base_info.values() if "tle_file_date" in info]
            if all_dates:
                unified_date = max(all_dates)
                year = int(unified_date[:4])
                month = int(unified_date[4:6])
                day = int(unified_date[6:8])
                unified_base_time = datetime(year, month, day, 12, 0, 0, timezone.utc)
                
                return {
                    "status": "success",
                    "unified_base_time": {
                        "tle_date": unified_date,
                        "iso_time": unified_base_time.isoformat(),
                        "unix_timestamp": int(unified_base_time.timestamp()),
                        "description": "統一TLE基準時間，適用於軌道計算和前端時間控制"
                    },
                    "constellation_details": time_base_info
                }
        
        return {
            "status": "error",
            "message": "無法找到有效的TLE數據文件"
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取TLE基準時間失敗: {e}")
        return {
            "status": "error",
            "message": f"TLE時間基準獲取失敗: {str(e)}"
        }

@router.get("/stage6-dynamic-pool")
async def get_stage6_dynamic_pool_data(
    constellation: str = Query("both", description="星座選擇: starlink, oneweb, both"),
    count: int = Query(20, description="最大衛星數量"),
    time_offset_seconds: int = Query(0, description="時間偏移秒數，用於動畫控制")
):
    """
    獲取階段六動態池數據，包含完整的position_timeseries
    專為前端3D可視化和動畫控制設計
    """
    try:
        import json
        import os
        from pathlib import Path
        
        logger.info(f"🎯 階段六動態池數據請求: constellation={constellation}, time_offset={time_offset_seconds}")
        
        # 查找階段六輸出文件
        stage6_file_paths = [
            "/app/data/leo_outputs/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json",
            "/app/data/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json"
        ]
        
        stage6_data = None
        used_file = None
        
        for file_path in stage6_file_paths:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    stage6_data = json.load(f)
                used_file = file_path
                break
        
        if not stage6_data:
            raise HTTPException(
                status_code=404, 
                detail="階段六動態池數據未找到。請先執行六階段數據處理流程。"
            )
        
        # 提取動態池數據
        dynamic_pool = stage6_data.get('dynamic_satellite_pool', {})
        selection_details = dynamic_pool.get('selection_details', [])
        
        if not selection_details:
            raise HTTPException(
                status_code=404,
                detail="階段六動態池中無衛星數據。"
            )
        
        # 根據星座過濾和平衡衛星
        def process_satellite_data(satellite):
            """處理單顆衛星數據"""
            sat_constellation = satellite.get('constellation', '').lower()
            position_timeseries = satellite.get('position_timeseries', [])
            
            if not position_timeseries:
                return None
                
            # 根據時間偏移找到對應的數據點
            time_index = (time_offset_seconds // 30) % len(position_timeseries)  # 30秒間隔
            current_position = position_timeseries[time_index]
            
            return {
                "id": str(satellite.get("norad_id", satellite.get("satellite_id", "unknown"))),
                "norad_id": satellite.get("norad_id"),
                "name": satellite.get("satellite_name", f"{sat_constellation}_{satellite.get('norad_id', 'unknown')}"),
                "constellation": sat_constellation,
                "elevation_deg": current_position.get("elevation_deg", 0),
                "azimuth_deg": current_position.get("azimuth_deg", 0),
                "distance_km": current_position.get("range_km", 0),
                "is_visible": current_position.get("is_visible", False),
                "signal_strength": satellite.get("signal_metrics", {}).get("rsrp_dbm", -100),
                "position_eci": current_position.get("position_eci", {}),
                "velocity_eci": current_position.get("velocity_eci", {}),
                # 完整的時間序列數據供前端使用
                "position_timeseries": position_timeseries,
                "total_visible_time": satellite.get("total_visible_time", 0),
                "coverage_ratio": satellite.get("coverage_ratio", 0),
                "selection_rationale": satellite.get("selection_rationale", {}),
                "last_updated": stage6_data.get('metadata', {}).get('timestamp', '')
            }
        
        # 處理所有衛星，根據真實可見性過濾
        all_processed_satellites = []
        for satellite in selection_details:
            sat_constellation = satellite.get('constellation', '').lower()
            
            # 根據constellation參數過濾
            if constellation == "both" or constellation == sat_constellation:
                processed_sat = process_satellite_data(satellite)
                if processed_sat:
                    all_processed_satellites.append(processed_sat)
        
        # 🎯 修復：優先顯示真正可見的衛星
        # 分離可見和不可見衛星
        visible_satellites = [sat for sat in all_processed_satellites if sat.get("is_visible", False)]
        invisible_satellites = [sat for sat in all_processed_satellites if not sat.get("is_visible", False)]
        
        # 分別按仰角排序
        visible_satellites.sort(key=lambda x: x.get("elevation_deg", -999), reverse=True)
        invisible_satellites.sort(key=lambda x: x.get("elevation_deg", -999), reverse=True)
        
        # 優先使用可見衛星，不足時用高仰角的不可見衛星補充
        result_satellites = visible_satellites[:count]
        if len(result_satellites) < count:
            remaining = count - len(result_satellites)
            result_satellites.extend(invisible_satellites[:remaining])
        
        response = {
            "satellites": result_satellites,
            "total_count": len(result_satellites),
            "metadata": {
                "data_source": "stage6_dynamic_pool",
                "stage6_file": used_file,
                "constellation": constellation,
                "time_offset_seconds": time_offset_seconds,
                "total_available_satellites": len(selection_details),
                "timeseries_points": len(result_satellites[0].get("position_timeseries", [])) if result_satellites else 0,
                "timeseries_interval_seconds": 30
            }
        }
        
        logger.info(f"✅ 返回階段六動態池數據: {len(result_satellites)} 顆衛星")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 階段六動態池數據API錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"階段六數據獲取失敗: {str(e)}")

@router.get("/health")
async def unified_satellite_health():
    """衛星數據服務健康檢查"""
    return {
        "status": "healthy",
        "service": "unified_satellite_data",
        "data_source": "real_tle_sgp4",
        "endpoints": [
            "/api/v1/satellite/unified",
            "/api/v1/satellite/stage6-dynamic-pool",
            "/api/v1/satellite/time-base",
            "/api/v1/satellite/health"
        ]
    }