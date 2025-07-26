# 04 - Phase 3: API 端點實現

> **上一階段**：[Phase 2 - 預計算引擎](./03-phase2-precompute-engine.md)  < /dev/null |  **下一階段**：[Phase 4 - 前端時間軸](./05-phase4-frontend-timeline.md)

## 🎯 Phase 3 目標
**目標**：實現時間軸查詢 API 和時間控制 API
**預估時間**: 1-2 天

## 📋 開發任務

### 3.1 時間軸查詢 API

#### **完整的時間點查詢 API**
```python
# satellite_history_api.py
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import asyncpg
import logging

router = APIRouter()

@router.get("/satellites/history/at_time")
async def get_satellites_at_time(
    target_time: datetime,
    observer_lat: float = 24.94417,
    observer_lon: float = 121.37139,
    min_elevation: float = 10.0,
    count: int = 10,
    constellation: Optional[str] = None
):
    """獲取指定時間點的衛星位置"""
    
    try:
        # 查詢預計算數據 (PostgreSQL)
        conn = await asyncpg.connect(RL_DATABASE_URL)
        try:
            # 構建查詢條件
            query_conditions = [
                "timestamp = $1",
                "observer_latitude = $2", 
                "observer_longitude = $3",
                "elevation_angle >= $4"
            ]
            params = [target_time, observer_lat, observer_lon, min_elevation]
            
            if constellation:
                query_conditions.append(f"constellation = ${len(params) + 1}")
                params.append(constellation)
            
            query = f"""
                SELECT satellite_id, norad_id, constellation, timestamp,
                       latitude, longitude, altitude, elevation_angle, azimuth_angle,
                       range_rate, signal_strength, path_loss_db,
                       calculation_method, data_quality
                FROM satellite_orbital_cache 
                WHERE {' AND '.join(query_conditions)}
                ORDER BY elevation_angle DESC 
                LIMIT ${len(params) + 1}
            """
            params.append(count)
            
            satellites = await conn.fetch(query, *params)
            
            # 轉換為字典格式並添加計算字段
            satellite_list = []
            for sat in satellites:
                satellite_data = {
                    "satellite_id": sat["satellite_id"],
                    "norad_id": sat["norad_id"],
                    "constellation": sat["constellation"],
                    "position": {
                        "latitude": float(sat["latitude"]),
                        "longitude": float(sat["longitude"]),
                        "altitude": float(sat["altitude"])
                    },
                    "observation": {
                        "elevation_angle": float(sat["elevation_angle"]),
                        "azimuth_angle": float(sat["azimuth_angle"]),
                        "range_km": float(sat["range_rate"]) if sat["range_rate"] else 0
                    },
                    "signal_quality": {
                        "signal_strength": float(sat["signal_strength"]) if sat["signal_strength"] else 0,
                        "path_loss_db": float(sat["path_loss_db"]) if sat["path_loss_db"] else 0
                    },
                    "data_quality": {
                        "calculation_method": sat["calculation_method"],
                        "quality_score": float(sat["data_quality"]) if sat["data_quality"] else 1.0
                    }
                }
                satellite_list.append(satellite_data)
                
        finally:
            await conn.close()
        
        return {
            "success": True,
            "timestamp": target_time.isoformat(),
            "observer_location": {
                "latitude": observer_lat,
                "longitude": observer_lon,
                "altitude": 100
            },
            "query_filters": {
                "min_elevation": min_elevation,
                "constellation": constellation,
                "max_count": count
            },
            "satellites": satellite_list,
            "count": len(satellite_list),
            "query_time_ms": 0  # 可添加實際查詢時間測量
        }
        
    except Exception as e:
        logging.error(f"時間點查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")

@router.get("/satellites/history/time_range") 
async def get_satellites_time_range(
    start_time: datetime,
    end_time: datetime,
    satellite_ids: Optional[List[str]] = Query(None),
    time_step_seconds: int = 30,
    observer_lat: float = 24.94417,
    observer_lon: float = 121.37139,
    min_elevation: float = 5.0
):
    """獲取時間範圍內的衛星軌跡數據（用於動畫）"""
    
    try:
        # 驗證時間範圍
        if end_time <= start_time:
            raise HTTPException(status_code=400, detail="結束時間必須晚於開始時間")
            
        duration_hours = (end_time - start_time).total_seconds() / 3600
        if duration_hours > 24:
            raise HTTPException(status_code=400, detail="時間範圍不能超過 24 小時")
        
        conn = await asyncpg.connect(RL_DATABASE_URL)
        try:
            # 構建查詢條件
            query_conditions = [
                "timestamp >= $1",
                "timestamp <= $2",
                "observer_latitude = $3",
                "observer_longitude = $4",
                "elevation_angle >= $5"
            ]
            params = [start_time, end_time, observer_lat, observer_lon, min_elevation]
            
            if satellite_ids:
                placeholders = ','.join([f'${i + len(params) + 1}' for i in range(len(satellite_ids))])
                query_conditions.append(f"satellite_id IN ({placeholders})")
                params.extend(satellite_ids)
            
            query = f"""
                SELECT satellite_id, constellation, timestamp,
                       latitude, longitude, altitude, elevation_angle, azimuth_angle,
                       signal_strength, path_loss_db
                FROM satellite_orbital_cache 
                WHERE {' AND '.join(query_conditions)}
                ORDER BY satellite_id, timestamp
            """
            
            trajectory_data = await conn.fetch(query, *params)
            
        finally:
            await conn.close()
        
        # 按衛星分組軌跡數據
        satellites_trajectories = {}
        for point in trajectory_data:
            sat_id = point["satellite_id"]
            if sat_id not in satellites_trajectories:
                satellites_trajectories[sat_id] = {
                    "satellite_id": sat_id,
                    "constellation": point["constellation"],
                    "trajectory_points": []
                }
            
            satellites_trajectories[sat_id]["trajectory_points"].append({
                "timestamp": point["timestamp"].isoformat(),
                "position": {
                    "latitude": float(point["latitude"]),
                    "longitude": float(point["longitude"]),
                    "altitude": float(point["altitude"])
                },
                "observation": {
                    "elevation_angle": float(point["elevation_angle"]),
                    "azimuth_angle": float(point["azimuth_angle"])
                },
                "signal_strength": float(point["signal_strength"]) if point["signal_strength"] else 0
            })
        
        return {
            "success": True,
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "duration_hours": duration_hours,
                "step_seconds": time_step_seconds
            },
            "observer_location": {
                "latitude": observer_lat,
                "longitude": observer_lon
            },
            "filters": {
                "satellite_ids": satellite_ids,
                "min_elevation": min_elevation
            },
            "satellites": list(satellites_trajectories.values()),
            "total_satellites": len(satellites_trajectories),
            "total_points": len(trajectory_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"時間範圍查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")
```

### 3.2 時間控制 API

#### **完整的時間軸資訊 API**
```python
@router.get("/satellites/history/timeline_info")
async def get_timeline_info(
    constellation: Optional[str] = None,
    observer_lat: float = 24.94417,
    observer_lon: float = 121.37139
):
    """獲取可用的歷史數據時間範圍"""
    
    try:
        conn = await asyncpg.connect(RL_DATABASE_URL)
        try:
            # 構建查詢條件
            query_conditions = [
                "observer_latitude = $1",
                "observer_longitude = $2"
            ]
            params = [observer_lat, observer_lon]
            
            if constellation:
                query_conditions.append(f"constellation = ${len(params) + 1}")
                params.append(constellation)
            
            # 獲取時間範圍統計
            timeline_query = f"""
                SELECT 
                    MIN(timestamp) as earliest_time,
                    MAX(timestamp) as latest_time,
                    COUNT(DISTINCT timestamp) as total_timepoints,
                    COUNT(DISTINCT satellite_id) as unique_satellites,
                    COUNT(DISTINCT constellation) as constellations,
                    COUNT(*) as total_records
                FROM satellite_orbital_cache 
                WHERE {' AND '.join(query_conditions)}
            """
            
            result = await conn.fetchrow(timeline_query, *params)
            
            if not result or not result['earliest_time']:
                return {
                    "success": False,
                    "message": "未找到歷史數據",
                    "available_time_range": None
                }
            
            # 計算統計資訊
            duration_hours = (
                result['latest_time'] - result['earliest_time']
            ).total_seconds() / 3600
            
            # 獲取星座詳細資訊
            constellation_query = f"""
                SELECT 
                    constellation,
                    COUNT(DISTINCT satellite_id) as satellite_count,
                    MIN(timestamp) as data_start,
                    MAX(timestamp) as data_end,
                    COUNT(*) as record_count
                FROM satellite_orbital_cache 
                WHERE observer_latitude = $1 AND observer_longitude = $2
                GROUP BY constellation
                ORDER BY constellation
            """
            
            constellations_data = await conn.fetch(
                constellation_query, observer_lat, observer_lon
            )
            
        finally:
            await conn.close()
        
        # 轉換星座資訊
        constellations_info = []
        for const_data in constellations_data:
            const_duration = (
                const_data['data_end'] - const_data['data_start']
            ).total_seconds() / 3600
            
            constellations_info.append({
                "constellation": const_data['constellation'],
                "satellite_count": const_data['satellite_count'],
                "data_start": const_data['data_start'].isoformat(),
                "data_end": const_data['data_end'].isoformat(),
                "duration_hours": round(const_duration, 2),
                "record_count": const_data['record_count']
            })
        
        return {
            "success": True,
            "available_time_range": {
                "start": result['earliest_time'].isoformat(),
                "end": result['latest_time'].isoformat(),
                "total_duration_hours": round(duration_hours, 2),
                "total_timepoints": result['total_timepoints'],
                "unique_satellites": result['unique_satellites'],
                "total_records": result['total_records']
            },
            "constellations": constellations_info,
            "observer_location": {
                "latitude": observer_lat,
                "longitude": observer_lon
            },
            "playback_settings": {
                "recommended_speeds": [0.5, 1, 2, 5, 10, 30, 60],
                "default_speed": 1,
                "time_step_seconds": 30,
                "max_playback_hours": 24
            },
            "data_quality": {
                "calculation_methods": ["SGP4", "emergency_simplified"],
                "quality_levels": ["high", "medium", "low"]
            }
        }
        
    except Exception as e:
        logging.error(f"時間軸資訊查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")

@router.get("/satellites/timeline/{constellation}")
async def get_constellation_timeline(
    constellation: str,
    observer_lat: float = 24.94417,
    observer_lon: float = 121.37139
):
    """獲取特定星座的時間軸資訊"""
    
    try:
        conn = await asyncpg.connect(RL_DATABASE_URL)
        try:
            # 檢查星座是否存在
            exists = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM satellite_orbital_cache 
                    WHERE constellation = $1 
                      AND observer_latitude = $2 
                      AND observer_longitude = $3
                )
            """, constellation, observer_lat, observer_lon)
            
            if not exists:
                raise HTTPException(
                    status_code=404, 
                    detail=f"未找到星座 '{constellation}' 的數據"
                )
            
            # 獲取詳細統計
            stats = await conn.fetchrow("""
                SELECT 
                    MIN(timestamp) as start_time,
                    MAX(timestamp) as end_time,
                    COUNT(DISTINCT timestamp) as total_points,
                    COUNT(DISTINCT satellite_id) as available_satellites,
                    AVG(signal_strength) as avg_signal_strength,
                    AVG(elevation_angle) as avg_elevation,
                    COUNT(*) FILTER (WHERE elevation_angle >= 15) as handover_candidates,
                    COUNT(*) FILTER (WHERE elevation_angle >= 10) as monitoring_satellites
                FROM satellite_orbital_cache 
                WHERE constellation = $1 
                  AND observer_latitude = $2 
                  AND observer_longitude = $3
            """, constellation, observer_lat, observer_lon)
            
            duration_hours = (
                stats['end_time'] - stats['start_time']
            ).total_seconds() / 3600
            
        finally:
            await conn.close()
        
        return {
            "success": True,
            "constellation": constellation,
            "start_time": stats['start_time'].isoformat(),
            "end_time": stats['end_time'].isoformat(),
            "duration_hours": round(duration_hours, 2),
            "total_points": stats['total_points'],
            "resolution": "30s",
            "available_satellites": stats['available_satellites'],
            "signal_quality": {
                "avg_signal_strength": round(float(stats['avg_signal_strength']), 2) if stats['avg_signal_strength'] else 0,
                "avg_elevation": round(float(stats['avg_elevation']), 2) if stats['avg_elevation'] else 0
            },
            "handover_statistics": {
                "handover_candidates": stats['handover_candidates'],  # 仰角 >= 15°
                "monitoring_satellites": stats['monitoring_satellites'],  # 仰角 >= 10°
                "total_observations": stats['handover_candidates'] + stats['monitoring_satellites']
            },
            "observer_location": {
                "latitude": observer_lat,
                "longitude": observer_lon
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"星座時間軸查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")

### 3.3 星座資訊 API

@router.get("/satellites/constellations/info")
async def get_constellations_info(
    observer_lat: float = 24.94417,
    observer_lon: float = 121.37139
):
    """獲取所有星座的基本資訊"""
    
    try:
        conn = await asyncpg.connect(RL_DATABASE_URL)
        try:
            constellations = await conn.fetch("""
                SELECT 
                    constellation,
                    COUNT(DISTINCT satellite_id) as satellite_count,
                    MIN(timestamp) as data_start,
                    MAX(timestamp) as data_end,
                    COUNT(DISTINCT timestamp) as timepoints,
                    AVG(signal_strength) as avg_signal_strength,
                    COUNT(*) FILTER (WHERE elevation_angle >= 10) as visible_observations,
                    MAX(elevation_angle) as max_elevation
                FROM satellite_orbital_cache 
                WHERE observer_latitude = $1 AND observer_longitude = $2
                GROUP BY constellation
                ORDER BY constellation
            """, observer_lat, observer_lon)
            
            constellations_list = []
            for const in constellations:
                duration_days = (
                    const['data_end'] - const['data_start']
                ).total_seconds() / (24 * 3600)
                
                constellations_list.append({
                    "constellation": const['constellation'],
                    "satellite_count": const['satellite_count'],
                    "data_start": const['data_start'].isoformat(),
                    "data_end": const['data_end'].isoformat(),
                    "total_days": round(duration_days, 2),
                    "timepoints": const['timepoints'],
                    "signal_quality": {
                        "avg_signal_strength": round(float(const['avg_signal_strength']), 2) if const['avg_signal_strength'] else 0,
                        "max_elevation": round(float(const['max_elevation']), 2) if const['max_elevation'] else 0
                    },
                    "visibility": {
                        "visible_observations": const['visible_observations'],
                        "visibility_ratio": round(const['visible_observations'] / const['timepoints'] * 100, 1) if const['timepoints'] > 0 else 0
                    }
                })
                
        finally:
            await conn.close()
        
        return {
            "success": True,
            "observer_location": {
                "latitude": observer_lat,
                "longitude": observer_lon
            },
            "constellations": constellations_list,
            "total_constellations": len(constellations_list),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logging.error(f"星座資訊查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")

### 3.4 D2 測量事件 API

@router.get("/satellites/d2/events")
async def get_d2_handover_events(
    timestamp: datetime,
    constellation: str = "starlink",
    observer_lat: float = 24.94417,
    observer_lon: float = 121.37139,
    d2_threshold_1: float = 15.0,  # 主要 handover 候選閾值
    d2_threshold_2: float = 10.0   # 監測範圍閾值
):
    """獲取 D2 測量事件（基於仰角的 handover 觸發）"""
    
    try:
        conn = await asyncpg.connect(RL_DATABASE_URL)
        try:
            # 獲取當前時間點的衛星數據
            current_satellites = await conn.fetch("""
                SELECT satellite_id, norad_id, constellation,
                       latitude, longitude, altitude, 
                       elevation_angle, azimuth_angle, 
                       signal_strength, path_loss_db,
                       range_rate
                FROM satellite_orbital_cache 
                WHERE timestamp = $1 
                  AND constellation = $2
                  AND observer_latitude = $3 
                  AND observer_longitude = $4
                  AND elevation_angle >= $5
                ORDER BY elevation_angle DESC
            """, timestamp, constellation, observer_lat, observer_lon, d2_threshold_2 - 5)
            
            # 計算 handover 事件
            handover_events = []
            serving_satellites = []
            handover_candidates = []
            monitoring_satellites = []
            
            for sat in current_satellites:
                elevation = float(sat['elevation_angle'])
                signal_strength = float(sat['signal_strength']) if sat['signal_strength'] else 0
                distance = float(sat['range_rate']) if sat['range_rate'] else 0
                
                # 計算地面距離（簡化）
                ground_distance = distance * 0.8 if distance > 0 else 0
                
                event_data = {
                    "satellite_id": sat['satellite_id'],
                    "norad_id": sat['norad_id'],
                    "constellation": sat['constellation'],
                    "position": {
                        "latitude": float(sat['latitude']),
                        "longitude": float(sat['longitude']),
                        "altitude": float(sat['altitude'])
                    },
                    "observation": {
                        "elevation_angle": elevation,
                        "azimuth_angle": float(sat['azimuth_angle']),
                        "distance_km": distance
                    },
                    "signal_quality": {
                        "signal_strength": signal_strength,
                        "path_loss_db": float(sat['path_loss_db']) if sat['path_loss_db'] else 0
                    },
                    "d2_metrics": {
                        "satellite_distance": distance,
                        "ground_distance": ground_distance,
                        "elevation_based_d2": elevation  # 使用仰角作為 D2 指標
                    }
                }
                
                # 分類衛星類型和事件
                if elevation >= d2_threshold_1:  # >= 15° 主要服務/候選
                    if elevation >= 30:  # 高仰角，可能是服務衛星
                        serving_satellites.append(event_data)
                        handover_events.append({
                            **event_data,
                            "event_type": "serving",
                            "trigger_condition": f"elevation >= 30° (serving satellite)",
                            "event_priority": "high",
                            "action": "maintain_connection"
                        })
                    else:  # 15-30°，handover 候選
                        handover_candidates.append(event_data)
                        handover_events.append({
                            **event_data,
                            "event_type": "handover_candidate",
                            "trigger_condition": f"elevation >= {d2_threshold_1}° (handover ready)",
                            "event_priority": "medium",
                            "action": "prepare_handover"
                        })
                        
                elif elevation >= d2_threshold_2:  # 10-15° 監測範圍
                    monitoring_satellites.append(event_data)
                    handover_events.append({
                        **event_data,
                        "event_type": "monitoring",
                        "trigger_condition": f"elevation >= {d2_threshold_2}° (monitoring range)",
                        "event_priority": "low",
                        "action": "monitor_signal"
                    })
                    
                elif elevation >= 5:  # 5-10° 即將可見
                    handover_events.append({
                        **event_data,
                        "event_type": "approaching",
                        "trigger_condition": "elevation >= 5° (approaching visibility)",
                        "event_priority": "info",
                        "action": "track_satellite"
                    })
            
        finally:
            await conn.close()
        
        return {
            "success": True,
            "timestamp": timestamp.isoformat(),
            "constellation": constellation,
            "observer_location": {
                "latitude": observer_lat,
                "longitude": observer_lon
            },
            "d2_thresholds": {
                "handover_threshold": d2_threshold_1,
                "monitoring_threshold": d2_threshold_2
            },
            "handover_events": handover_events,
            "satellite_categories": {
                "serving_satellites": serving_satellites,
                "handover_candidates": handover_candidates,
                "monitoring_satellites": monitoring_satellites
            },
            "statistics": {
                "total_events": len(handover_events),
                "serving_count": len(serving_satellites),
                "candidate_count": len(handover_candidates),
                "monitoring_count": len(monitoring_satellites)
            },
            "3gpp_compliance": {
                "max_measured_satellites": 8,  # 3GPP NTN 建議
                "current_measured": len([s for s in current_satellites if float(s['elevation_angle']) >= d2_threshold_2]),
                "handover_ready": len(handover_candidates),
                "compliant": len(handover_candidates) <= 5 and len(monitoring_satellites) <= 8
            }
        }
        
    except Exception as e:
        logging.error(f"D2 事件查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"查詢失敗: {str(e)}")
```

### 3.5 API 錯誤處理和驗證

#### **統一錯誤處理機制**
```python
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import traceback
import logging

class APIErrorHandler:
    """統一 API 錯誤處理器"""
    
    @staticmethod
    def validation_error(message: str, details: dict = None):
        """參數驗證錯誤"""
        return HTTPException(
            status_code=400,
            detail={
                "error_type": "validation_error",
                "message": message,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def database_error(message: str = "數據庫查詢失敗"):
        """數據庫錯誤"""
        return HTTPException(
            status_code=503,
            detail={
                "error_type": "database_error", 
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "retry_after": 30
            }
        )
    
    @staticmethod
    def not_found_error(resource: str, identifier: str):
        """資源未找到錯誤"""
        return HTTPException(
            status_code=404,
            detail={
                "error_type": "resource_not_found",
                "message": f"{resource} '{identifier}' 未找到",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# 全局異常處理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局異常處理"""
    error_id = str(uuid.uuid4())[:8]
    
    logging.error(f"[{error_id}] 未處理的異常: {str(exc)}")
    logging.error(f"[{error_id}] 請求路徑: {request.url.path}")
    logging.error(f"[{error_id}] 堆疊追蹤: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error_type": "internal_server_error",
            "message": "服務器內部錯誤",
            "error_id": error_id,
            "timestamp": datetime.utcnow().isoformat(),
            "support_info": "請聯繫技術支援並提供錯誤 ID"
        }
    )

# 增強的端點實現（包含錯誤處理）
@router.get("/satellites/positions")
async def get_satellites_positions_enhanced(
    timestamp: datetime,
    constellation: Optional[str] = None,
    observer_lat: float = Query(24.94417, ge=-90, le=90),
    observer_lon: float = Query(121.37139, ge=-180, le=180),
    min_elevation: float = Query(10.0, ge=0, le=90),
    max_count: int = Query(10, ge=1, le=50)
):
    """增強版衛星位置查詢（包含完整錯誤處理）"""
    
    # 1. 參數驗證
    current_time = datetime.utcnow()
    if timestamp > current_time + timedelta(hours=24):
        raise APIErrorHandler.validation_error(
            "查詢時間不能超過當前時間 24 小時",
            {"timestamp": timestamp.isoformat(), "max_allowed": (current_time + timedelta(hours=24)).isoformat()}
        )
    
    if timestamp < current_time - timedelta(days=30):
        raise APIErrorHandler.validation_error(
            "查詢時間不能早於 30 天前",
            {"timestamp": timestamp.isoformat(), "min_allowed": (current_time - timedelta(days=30)).isoformat()}
        )
    
    # 2. 數據庫連接和查詢
    try:
        conn = await asyncpg.connect(RL_DATABASE_URL)
        
        try:
            # 檢查數據是否存在
            data_exists = await conn.fetchval("""
                SELECT EXISTS(
                    SELECT 1 FROM satellite_orbital_cache 
                    WHERE timestamp = $1 
                      AND observer_latitude = $2 
                      AND observer_longitude = $3
                )
            """, timestamp, observer_lat, observer_lon)
            
            if not data_exists:
                raise APIErrorHandler.not_found_error(
                    "衛星數據", 
                    f"時間點 {timestamp.isoformat()} 觀測點 ({observer_lat}, {observer_lon})"
                )
            
            # 構建查詢
            query_conditions = [
                "timestamp = $1",
                "observer_latitude = $2",
                "observer_longitude = $3", 
                "elevation_angle >= $4"
            ]
            params = [timestamp, observer_lat, observer_lon, min_elevation]
            
            if constellation:
                # 驗證星座名稱
                valid_constellations = await conn.fetch(
                    "SELECT DISTINCT constellation FROM satellite_orbital_cache"
                )
                valid_names = [row['constellation'] for row in valid_constellations]
                
                if constellation not in valid_names:
                    raise APIErrorHandler.validation_error(
                        f"不支援的星座名稱: {constellation}",
                        {"valid_constellations": valid_names}
                    )
                
                query_conditions.append(f"constellation = ${len(params) + 1}")
                params.append(constellation)
            
            query = f"""
                SELECT satellite_id, norad_id, constellation, timestamp,
                       latitude, longitude, altitude, elevation_angle, azimuth_angle,
                       range_rate, signal_strength, path_loss_db,
                       calculation_method, data_quality
                FROM satellite_orbital_cache 
                WHERE {' AND '.join(query_conditions)}
                ORDER BY elevation_angle DESC 
                LIMIT ${len(params) + 1}
            """
            params.append(max_count)
            
            # 記錄查詢開始時間
            query_start = time.time()
            satellites = await conn.fetch(query, *params)
            query_duration = (time.time() - query_start) * 1000  # 轉換為毫秒
            
            # 構建響應數據
            satellite_list = []
            for sat in satellites:
                satellite_data = {
                    "satellite_id": sat["satellite_id"],
                    "norad_id": sat["norad_id"],
                    "constellation": sat["constellation"],
                    "position": {
                        "latitude": float(sat["latitude"]),
                        "longitude": float(sat["longitude"]),
                        "altitude": float(sat["altitude"])
                    },
                    "observation": {
                        "elevation_angle": float(sat["elevation_angle"]),
                        "azimuth_angle": float(sat["azimuth_angle"]),
                        "range_km": float(sat["range_rate"]) if sat["range_rate"] else 0
                    },
                    "signal_quality": {
                        "signal_strength": float(sat["signal_strength"]) if sat["signal_strength"] else 0,
                        "path_loss_db": float(sat["path_loss_db"]) if sat["path_loss_db"] else 0
                    },
                    "data_quality": {
                        "calculation_method": sat["calculation_method"],
                        "quality_score": float(sat["data_quality"]) if sat["data_quality"] else 1.0
                    }
                }
                satellite_list.append(satellite_data)
            
        finally:
            await conn.close()
        
        # 3. 記錄性能指標
        logging.info(f"衛星位置查詢完成: {len(satellite_list)} 顆衛星, 查詢時間 {query_duration:.2f}ms")
        
        return {
            "success": True,
            "timestamp": timestamp.isoformat(),
            "observer_location": {
                "latitude": observer_lat,
                "longitude": observer_lon,
                "altitude": 100
            },
            "query_filters": {
                "min_elevation": min_elevation,
                "constellation": constellation,
                "max_count": max_count
            },
            "satellites": satellite_list,
            "count": len(satellite_list),
            "performance": {
                "query_time_ms": round(query_duration, 2),
                "cache_hit": False,  # 可實現緩存機制
                "data_freshness": "real_time"
            },
            "api_version": "v1.2"
        }
        
    except asyncpg.PostgresError as e:
        logging.error(f"PostgreSQL 錯誤: {e}")
        raise APIErrorHandler.database_error(f"數據庫查詢失敗: {str(e)}")
    
    except HTTPException:
        raise  # 重新拋出 HTTP 異常
    
    except Exception as e:
        logging.error(f"衛星位置查詢未知錯誤: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"查詢失敗: {str(e)}"
        )
```

### 3.6 API 性能監控和日誌

#### **性能監控中間件**
```python
import time
from fastapi import Request
import logging

@app.middleware("http")
async def performance_monitoring_middleware(request: Request, call_next):
    """API 性能監控中間件"""
    
    start_time = time.time()
    request_id = str(uuid.uuid4())[:8]
    
    # 記錄請求開始
    logging.info(f"[{request_id}] 開始處理請求: {request.method} {request.url.path}")
    
    # 處理請求
    response = await call_next(request)
    
    # 計算處理時間
    process_time = time.time() - start_time
    response_time_ms = process_time * 1000
    
    # 記錄性能指標
    logging.info(
        f"[{request_id}] 請求完成: "
        f"狀態={response.status_code}, "
        f"響應時間={response_time_ms:.2f}ms"
    )
    
    # 性能告警（響應時間超過 200ms）
    if response_time_ms > 200:
        logging.warning(
            f"[{request_id}] 性能警告: 響應時間過長 ({response_time_ms:.2f}ms) "
            f"端點: {request.url.path}"
        )
    
    # 添加性能標頭
    response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"
    response.headers["X-Request-ID"] = request_id
    
    return response

# API 健康檢查端點
@router.get("/satellites/health")
async def api_health_check():
    """API 健康檢查端點"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.2.0",
        "uptime_seconds": time.time() - app_start_time,
        "checks": {}
    }
    
    # 1. 數據庫連接檢查
    try:
        conn = await asyncpg.connect(RL_DATABASE_URL)
        db_start = time.time()
        await conn.fetchval("SELECT 1")
        await conn.close()
        db_response_time = (time.time() - db_start) * 1000
        
        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": round(db_response_time, 2),
            "connection": "postgresql://rl_research"
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # 2. 數據完整性檢查
    try:
        conn = await asyncpg.connect(RL_DATABASE_URL)
        
        # 檢查表是否存在且有數據
        tables_check = await conn.fetch("""
            SELECT 
                table_name,
                (SELECT COUNT(*) FROM information_schema.tables 
                 WHERE table_name = t.table_name AND table_schema = 'public') as exists,
                CASE 
                    WHEN table_name = 'satellite_tle_data' THEN 
                        (SELECT COUNT(*) FROM satellite_tle_data WHERE is_active = true)
                    WHEN table_name = 'satellite_orbital_cache' THEN 
                        (SELECT COUNT(*) FROM satellite_orbital_cache)
                    ELSE 0
                END as record_count
            FROM (VALUES 
                ('satellite_tle_data'),
                ('satellite_orbital_cache'),
                ('d2_measurement_cache')
            ) as t(table_name)
        """)
        
        await conn.close()
        
        data_integrity = {}
        for table in tables_check:
            table_name = table['table_name']
            data_integrity[table_name] = {
                "exists": bool(table['exists']),
                "record_count": table['record_count'],
                "status": "healthy" if table['exists'] and table['record_count'] > 0 else "warning"
            }
        
        health_status["checks"]["data_integrity"] = {
            "status": "healthy",
            "tables": data_integrity
        }
        
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["data_integrity"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # 3. 系統資源檢查
    import psutil
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_status["checks"]["system_resources"] = {
            "status": "healthy" if cpu_percent < 80 and memory.percent < 85 else "warning",
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent,
            "memory_available_mb": round(memory.available / 1024 / 1024, 2)
        }
    except Exception as e:
        health_status["checks"]["system_resources"] = {
            "status": "unknown",
            "error": str(e)
        }
    
    # 根據各項檢查結果確定總體狀態
    check_statuses = [check.get("status", "unknown") for check in health_status["checks"].values()]
    
    if "unhealthy" in check_statuses:
        health_status["status"] = "unhealthy"
        status_code = 503
    elif "warning" in check_statuses or "degraded" in check_statuses:
        health_status["status"] = "degraded"  
        status_code = 200
    else:
        health_status["status"] = "healthy"
        status_code = 200
    
    return JSONResponse(content=health_status, status_code=status_code)
```

### 3.7 API 文檔和使用範例

#### **完整的 API 規格文檔**
```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="LEO 衛星軌道分析 API",
        version="1.2.0",
        description="""
        ## LEO 衛星軌道分析系統 API
        
        本 API 提供基於真實 TLE 數據和 SGP4 軌道計算的 LEO 衛星位置查詢服務。
        
        ### 主要功能
        - 🛰️ **衛星位置查詢**: 基於時間點和觀測位置查詢可見衛星
        - ⏰ **時間軸資訊**: 獲取歷史數據的時間範圍和統計資訊
        - 📊 **軌跡查詢**: 查詢衛星在時間範圍內的運動軌跡
        - 📡 **D2 測量事件**: 基於 3GPP NTN 標準的 handover 事件分析
        
        ### 數據來源
        - **TLE 數據**: CelesTrak + Space-Track 真實軌道數據
        - **軌道計算**: SGP4 標準算法，30 秒解析度
        - **觀測位置**: 預設台灣（24.94°N, 121.37°E）
        - **支援星座**: Starlink、OneWeb
        
        ### 性能特性
        - **響應時間**: < 100ms (95% 請求)
        - **數據準確性**: 基於真實 TLE + SGP4 計算
        - **3GPP NTN 合規**: 完全符合國際標準
        """,
        routes=app.routes,
    )
    
    # 添加自定義標籤
    openapi_schema["tags"] = [
        {
            "name": "衛星位置查詢",
            "description": "基於時間點查詢衛星位置和可見性"
        },
        {
            "name": "時間軸控制",
            "description": "歷史數據時間範圍和時間軸資訊"
        },
        {
            "name": "軌跡分析",
            "description": "衛星運動軌跡和時間序列數據"
        },
        {
            "name": "D2 測量事件",
            "description": "3GPP NTN 標準的 handover 事件分析"
        },
        {
            "name": "系統監控",
            "description": "API 健康檢查和系統狀態監控"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# 為每個端點添加詳細的文檔
@router.get(
    "/satellites/positions",
    tags=["衛星位置查詢"],
    summary="查詢指定時間點的衛星位置",
    description="""
    基於指定的時間點和觀測位置，查詢當時可見的衛星位置資訊。
    
    **使用案例**:
    - 分析特定時刻的衛星覆蓋情況
    - 研究 handover 候選衛星
    - 驗證軌道預測準確性
    
    **返回數據包含**:
    - 衛星基本資訊（ID、NORAD 編號、星座）
    - 精確位置（緯度、經度、高度）
    - 觀測角度（仰角、方位角、距離）
    - 信號品質（信號強度、路徑損耗）
    - 數據品質（計算方法、準確度評分）
    """,
    response_description="衛星位置資訊列表，按仰角降序排列",
    responses={
        200: {
            "description": "查詢成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "timestamp": "2025-01-23T12:00:00Z",
                        "observer_location": {
                            "latitude": 24.94417,
                            "longitude": 121.37139,
                            "altitude": 100
                        },
                        "satellites": [
                            {
                                "satellite_id": "starlink-1",
                                "norad_id": 50001,
                                "constellation": "starlink",
                                "position": {
                                    "latitude": 25.1,
                                    "longitude": 121.5,
                                    "altitude": 550.2
                                },
                                "observation": {
                                    "elevation_angle": 35.4,
                                    "azimuth_angle": 180.0,
                                    "range_km": 1200.5
                                },
                                "signal_quality": {
                                    "signal_strength": -85.4,
                                    "path_loss_db": 162.8
                                }
                            }
                        ],
                        "count": 1,
                        "performance": {
                            "query_time_ms": 45.2
                        }
                    }
                }
            }
        },
        400: {"description": "參數驗證錯誤"},
        404: {"description": "指定時間點無可用數據"},
        503: {"description": "數據庫連接失敗"}
    }
)
async def get_satellites_positions_documented():
    """文檔化的衛星位置查詢端點"""
    pass  # 實際實現在上面的函數中
```

## 📋 完整實施檢查清單

### 🎯 **Phase 3.1: 核心 API 端點開發**
- [ ] **時間點查詢 API** (`/satellites/positions`)
  - [ ] 基本查詢功能實現
  - [ ] 參數驗證（時間範圍、地理座標、仰角閾值）
  - [ ] 星座篩選支援
  - [ ] 結果排序和分頁
  - [ ] 錯誤處理機制

- [ ] **時間軸資訊 API** (`/satellites/timeline/info`, `/satellites/timeline/{constellation}`)
  - [ ] 可用數據範圍查詢
  - [ ] 星座統計資訊
  - [ ] 播放控制參數
  - [ ] 數據品質指標

- [ ] **軌跡查詢 API** (`/satellites/history/time_range`)
  - [ ] 時間範圍驗證（最大 24 小時）
  - [ ] 衛星 ID 篩選
  - [ ] 軌跡點插值
  - [ ] 大數據量優化

- [ ] **星座資訊 API** (`/satellites/constellations/info`)
  - [ ] 多星座統計
  - [ ] 可見性分析
  - [ ] 信號品質統計
  - [ ] 更新時間資訊

### 🎯 **Phase 3.2: D2 測量事件系統**
- [ ] **D2 事件分析 API** (`/satellites/d2/events`)
  - [ ] 3GPP NTN 標準合規性
  - [ ] Handover 觸發條件判斷
  - [ ] 衛星分類（服務/候選/監測）
  - [ ] 事件優先級排序
  - [ ] 統計資訊計算

- [ ] **Handover 候選分析**
  - [ ] 多重閾值支援（15°/10°/5°）
  - [ ] 信號強度評估
  - [ ] 距離計算優化
  - [ ] 切換建議生成

### 🎯 **Phase 3.3: 錯誤處理和驗證**
- [ ] **統一錯誤處理**
  - [ ] 自定義異常類別
  - [ ] 錯誤類型分類
  - [ ] 詳細錯誤訊息
  - [ ] 錯誤 ID 追蹤

- [ ] **參數驗證增強**
  - [ ] 時間格式驗證
  - [ ] 地理座標邊界檢查
  - [ ] 數值範圍限制
  - [ ] 星座名稱驗證

- [ ] **數據完整性檢查**
  - [ ] 數據存在性驗證
  - [ ] 時間連續性檢查
  - [ ] 數據品質評估
  - [ ] 缺失數據處理

### 🎯 **Phase 3.4: 性能監控和優化**
- [ ] **性能監控中間件**
  - [ ] 請求響應時間記錄
  - [ ] 請求 ID 追蹤
  - [ ] 性能警告機制
  - [ ] 標頭資訊添加

- [ ] **健康檢查系統**
  - [ ] 數據庫連接檢查
  - [ ] 數據完整性驗證
  - [ ] 系統資源監控
  - [ ] 多層次狀態報告

- [ ] **查詢優化**
  - [ ] 數據庫索引優化
  - [ ] 查詢計劃分析
  - [ ] 連接池配置
  - [ ] 結果緩存機制

### 🎯 **Phase 3.5: API 文檔和測試**
- [ ] **OpenAPI 文檔**
  - [ ] 完整的端點文檔
  - [ ] 參數說明和範例
  - [ ] 響應格式定義
  - [ ] 錯誤碼說明

- [ ] **使用範例**
  - [ ] cURL 命令範例
  - [ ] Python 客戶端範例
  - [ ] JavaScript 前端整合
  - [ ] 錯誤處理範例

## 🧪 詳細驗證步驟

### 🔍 **基本功能驗證**

#### **1. 衛星位置查詢驗證**
```bash
echo "=== 衛星位置查詢測試 ==="

# 1.1 基本查詢測試
echo "1.1 基本查詢測試:"
curl -X GET "http://localhost:8080/api/v1/satellites/positions" \
  -G \
  -d "timestamp=2025-01-23T12:00:00Z" \
  -d "constellation=starlink" \
  -d "min_elevation=10" \
  -H "Accept: application/json" | jq '
    {
      success: .success,
      satellite_count: .count,
      query_time_ms: .performance.query_time_ms,
      satellites: .satellites[0:3] | map({
        satellite_id: .satellite_id,
        elevation: .observation.elevation_angle,
        signal_strength: .signal_quality.signal_strength
      })
    }'

# 1.2 參數邊界測試
echo "1.2 參數邊界測試:"

# 測試最小仰角邊界
curl -s -X GET "http://localhost:8080/api/v1/satellites/positions" \
  -G \
  -d "timestamp=2025-01-23T12:00:00Z" \
  -d "min_elevation=0" | jq '.count' | xargs echo "仰角 0°: 衛星數量 ="

curl -s -X GET "http://localhost:8080/api/v1/satellites/positions" \
  -G \
  -d "timestamp=2025-01-23T12:00:00Z" \
  -d "min_elevation=30" | jq '.count' | xargs echo "仰角 30°: 衛星數量 ="

# 測試觀測位置邊界
curl -s -X GET "http://localhost:8080/api/v1/satellites/positions" \
  -G \
  -d "timestamp=2025-01-23T12:00:00Z" \
  -d "observer_lat=90" \
  -d "observer_lon=180" \
  -w "HTTP狀態: %{http_code}\n" \
  -o /dev/null

# 1.3 錯誤處理測試
echo "1.3 錯誤處理測試:"

# 無效時間格式
curl -s -X GET "http://localhost:8080/api/v1/satellites/positions" \
  -G \
  -d "timestamp=invalid-time" \
  -w "HTTP狀態: %{http_code}\n" | head -1

# 未來時間（超過 24 小時）
future_time=$(date -d "+2 days" -u +"%Y-%m-%dT%H:%M:%SZ")
curl -s -X GET "http://localhost:8080/api/v1/satellites/positions" \
  -G \
  -d "timestamp=$future_time" | jq '.detail.error_type'

# 無效星座名稱
curl -s -X GET "http://localhost:8080/api/v1/satellites/positions" \
  -G \
  -d "timestamp=2025-01-23T12:00:00Z" \
  -d "constellation=invalid_constellation" | jq '.detail.error_type'
```

#### **2. 時間軸資訊驗證**
```bash
echo "=== 時間軸資訊測試 ==="

# 2.1 全域時間軸資訊
echo "2.1 全域時間軸資訊:"
curl -X GET "http://localhost:8080/api/v1/satellites/history/timeline_info" | jq '
{
  available_range: .available_time_range | {
    duration_hours: .total_duration_hours,
    satellites: .unique_satellites,
    timepoints: .total_timepoints
  },
  constellations: .constellations | map({
    name: .constellation,
    satellites: .satellite_count,
    duration: .duration_hours
  })
}'

# 2.2 特定星座時間軸
echo "2.2 Starlink 星座時間軸:"
curl -X GET "http://localhost:8080/api/v1/satellites/timeline/starlink" | jq '
{
  constellation: .constellation,
  duration_hours: .duration_hours,
  satellites: .available_satellites,
  signal_quality: .signal_quality,
  handover_stats: .handover_statistics
}'

# 2.3 不存在星座測試
echo "2.3 不存在星座測試:"
curl -s -X GET "http://localhost:8080/api/v1/satellites/timeline/nonexistent" \
  -w "HTTP狀態: %{http_code}\n" | tail -1
```

#### **3. D2 測量事件驗證**
```bash
echo "=== D2 測量事件測試 ==="

# 3.1 基本 D2 事件查詢
echo "3.1 基本 D2 事件查詢:"
curl -X GET "http://localhost:8080/api/v1/satellites/d2/events" \
  -G \
  -d "timestamp=2025-01-23T12:00:00Z" \
  -d "constellation=starlink" \
  -d "d2_threshold_1=15" \
  -d "d2_threshold_2=10" | jq '
{
  total_events: .statistics.total_events,
  serving_satellites: .statistics.serving_count,
  handover_candidates: .statistics.candidate_count,
  monitoring_satellites: .statistics.monitoring_count,
  gpp_compliance: ."3gpp_compliance".compliant,
  sample_events: .handover_events[0:2] | map({
    satellite: .satellite_id,
    event_type: .event_type,
    elevation: .observation.elevation_angle,
    action: .action
  })
}'

# 3.2 閾值對比測試
echo "3.2 不同閾值對比:"
for threshold in 5 10 15 20; do
  count=$(curl -s -X GET "http://localhost:8080/api/v1/satellites/d2/events" \
    -G \
    -d "timestamp=2025-01-23T12:00:00Z" \
    -d "constellation=starlink" \
    -d "d2_threshold_2=$threshold" | jq '.statistics.total_events')
  echo "  閾值 ${threshold}°: $count 個事件"  
done

# 3.3 3GPP NTN 合規性檢查
echo "3.3 3GPP NTN 合規性:"
curl -s -X GET "http://localhost:8080/api/v1/satellites/d2/events" \
  -G \
  -d "timestamp=2025-01-23T12:00:00Z" \
  -d "constellation=starlink" | jq '
{
  max_allowed: ."3gpp_compliance".max_measured_satellites,
  current_measured: ."3gpp_compliance".current_measured,
  handover_ready: ."3gpp_compliance".handover_ready,
  compliant: ."3gpp_compliance".compliant,
  verdict: (if ."3gpp_compliance".compliant then "✅ 符合 3GPP NTN 標準" else "❌ 超出 3GPP NTN 建議" end)
}'
```

### ⚡ **性能驗證測試**

#### **4. API 響應時間測試**
```bash
echo "=== API 響應時間測試 ==="

# 4.1 單一請求響應時間
echo "4.1 單一請求響應時間測試:"
API_ENDPOINTS=(
  "satellites/health"
  "satellites/constellations/info"
  "satellites/timeline/starlink"
  "satellites/positions?timestamp=2025-01-23T12:00:00Z&constellation=starlink"
)

for endpoint in "${API_ENDPOINTS[@]}"; do
  echo "測試端點: $endpoint"
  
  # 執行 5 次測試
  total_time=0
  for i in {1..5}; do
    response_time=$(curl -w "%{time_total}" -o /dev/null -s "http://localhost:8080/api/v1/$endpoint")
    total_time=$(echo "$total_time + $response_time" | bc -l)
  done
  
  avg_time=$(echo "scale=3; $total_time / 5" | bc -l)
  avg_ms=$(echo "$avg_time * 1000" | bc -l)
  
  echo "  平均響應時間: ${avg_ms} ms"
  
  # 檢查是否符合性能目標
  if (( $(echo "$avg_ms < 100" | bc -l) )); then
    echo "  ✅ 符合性能目標 (<100ms)"
  else
    echo "  ❌ 超出性能目標 (>=100ms)"
  fi
  echo ""
done

# 4.2 併發請求測試
echo "4.2 併發請求測試:"
if command -v parallel &> /dev/null; then
  echo "執行 10 個併發請求..."
  start_time=$(date +%s.%N)
  
  seq 1 10 | parallel -j 10 \
    "curl -w 'Request {}: %{time_total}s\n' -o /dev/null -s 'http://localhost:8080/api/v1/satellites/constellations/info'" \
    > /tmp/concurrent_results.txt
  
  end_time=$(date +%s.%N)
  total_duration=$(echo "$end_time - $start_time" | bc -l)
  
  echo "併發測試結果:"
  echo "  總持續時間: ${total_duration}s"
  echo "  平均每請求時間: $(grep "Request" /tmp/concurrent_results.txt | awk '{sum+=$3} END {print sum/NR "s"}')"
  echo "  所有請求完成: $(wc -l < /tmp/concurrent_results.txt)/10"
else
  echo "需要安裝 GNU parallel 進行併發測試"
fi
```

#### **5. 系統健康檢查驗證**
```bash
echo "=== 系統健康檢查 ==="

# 5.1 健康檢查端點測試
echo "5.1 健康檢查端點:"
health_response=$(curl -s "http://localhost:8080/api/v1/satellites/health")
echo "$health_response" | jq '
{
  overall_status: .status,
  uptime_hours: (.uptime_seconds / 3600 | floor),
  database: .checks.database.status,
  db_response_time: .checks.database.response_time_ms,
  data_integrity: .checks.data_integrity.status,
  system_resources: .checks.system_resources.status,
  cpu_percent: .checks.system_resources.cpu_percent,
  memory_percent: .checks.system_resources.memory_percent
}'

# 5.2 數據完整性驗證
echo "5.2 數據完整性檢查:"
echo "$health_response" | jq '.checks.data_integrity.tables' | jq -r '
to_entries[] | 
"  \(.key): 存在=\(.value.exists), 記錄數=\(.value.record_count), 狀態=\(.value.status)"'

# 5.3 系統資源警告檢查
echo "5.3 系統資源狀態:"
cpu_usage=$(echo "$health_response" | jq -r '.checks.system_resources.cpu_percent // 0')
memory_usage=$(echo "$health_response" | jq -r '.checks.system_resources.memory_percent // 0')

if (( $(echo "$cpu_usage > 70" | bc -l) )); then
  echo "  ⚠️  CPU 使用率過高: ${cpu_usage}%"
else
  echo "  ✅ CPU 使用率正常: ${cpu_usage}%"
fi

if (( $(echo "$memory_usage > 80" | bc -l) )); then
  echo "  ⚠️  記憶體使用率過高: ${memory_usage}%"
else
  echo "  ✅ 記憶體使用率正常: ${memory_usage}%"
fi
```

### 📊 **數據準確性驗證**

#### **6. 軌道計算準確性測試**
```bash
echo "=== 軌道計算準確性測試 ==="

# 6.1 位置連續性檢查
echo "6.1 衛星位置連續性檢查:"
satellite_id="starlink-1"
base_time="2025-01-23T12:00:00Z"

echo "檢查衛星 $satellite_id 在 5 分鐘內的位置變化:"
for offset in 0 60 120 180 240 300; do
  timestamp=$(date -d "$base_time + $offset seconds" -u +"%Y-%m-%dT%H:%M:%SZ")
  
  position=$(curl -s -X GET "http://localhost:8080/api/v1/satellites/positions" \
    -G \
    -d "timestamp=$timestamp" \
    -d "constellation=starlink" | \
    jq -r --arg sat_id "$satellite_id" '
      .satellites[] | 
      select(.satellite_id == $sat_id) | 
      "\(.position.latitude),\(.position.longitude),\(.position.altitude)"')
  
  if [ -n "$position" ]; then
    echo "  T+${offset}s: $position"
  else
    echo "  T+${offset}s: 衛星不可見"
  fi
done

# 6.2 仰角計算驗證
echo "6.2 仰角計算合理性檢查:"
curl -s -X GET "http://localhost:8080/api/v1/satellites/positions" \
  -G \
  -d "timestamp=2025-01-23T12:00:00Z" \
  -d "constellation=starlink" \
  -d "min_elevation=0" | jq -r '
.satellites[] | 
select(.observation.elevation_angle > 0) |
"衛星 \(.satellite_id): 仰角=\(.observation.elevation_angle)°, 方位角=\(.observation.azimuth_angle)°, 距離=\(.observation.range_km)km"
' | head -5

# 6.3 信號強度合理性檢查
echo "6.3 信號強度合理性檢查:"
curl -s -X GET "http://localhost:8080/api/v1/satellites/positions" \
  -G \
  -d "timestamp=2025-01-23T12:00:00Z" \
  -d "constellation=starlink" | jq -r '
.satellites[] |
select(.signal_quality.signal_strength != 0) |
"衛星 \(.satellite_id): 信號強度=\(.signal_quality.signal_strength)dBm, 路徑損耗=\(.signal_quality.path_loss_db)dB"
' | head -3
```

## 🎯 **完成標準與驗收條件**

### ✅ **功能完整性標準**
1. **API 端點完成度**: 所有 4 個主要端點正常工作
   - 衛星位置查詢 (`/positions`) ✓
   - 時間軸資訊 (`/timeline/*`) ✓
   - 軌跡查詢 (`/time_range`) ✓
   - D2 測量事件 (`/d2/events`) ✓

2. **錯誤處理完善性**: 所有異常情況都有適當處理
   - 參數驗證錯誤 ✓
   - 數據未找到錯誤 ✓
   - 數據庫連接錯誤 ✓
   - 系統內部錯誤 ✓

3. **數據準確性**: 計算結果符合物理規律
   - SGP4 軌道計算正確 ✓
   - 仰角/方位角計算合理 ✓
   - 信號強度模型正確 ✓
   - 3GPP NTN 標準合規 ✓

### ⚡ **性能要求標準**
1. **響應時間**: API 響應時間 < 100ms (95% 請求)
2. **併發處理**: 支援 20 個併發用戶無錯誤
3. **數據庫查詢**: 主要查詢 < 50ms
4. **系統穩定性**: 連續運行 24 小時無崩潰

### 📋 **文檔完整性標準**
1. **API 文檔**: OpenAPI 規格完整，包含所有端點
2. **使用範例**: 每個端點都有 cURL 和程式碼範例
3. **錯誤說明**: 所有錯誤碼都有詳細說明
4. **驗證腳本**: 提供完整的測試驗證腳本

### 🔧 **維護性標準**
1. **日誌記錄**: 所有關鍵操作都有適當日誌
2. **監控指標**: 性能和健康狀態可監控
3. **錯誤追蹤**: 所有錯誤都可追蹤和除錯
4. **版本管理**: API 版本控制和向後兼容

**🎉 當所有上述標準都達成時，Phase 3 即完成並可進入 Phase 4 前端開發階段！**

