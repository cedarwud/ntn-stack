#!/usr/bin/env python3
"""
Phase 1 重構 - 增強標準化 API 接口

功能:
1. 提供 Phase 1 軌道數據的 REST API
2. 使用標準化的 Phase 1 → Phase 2 接口
3. 支援批量查詢和高性能數據傳輸
4. 向下兼容原有 API 格式

符合 CLAUDE.md 原則:
- 提供真實的軌道計算結果
- 支援全量衛星數據查詢
- 確保 API 響應性能和數據準確性
"""

from fastapi import FastAPI, HTTPException, Query, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any, Union
import json
from pydantic import BaseModel

# 添加 Phase 1 模組路徑
PHASE1_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHASE1_ROOT / "04_output_interface"))

logger = logging.getLogger(__name__)

# 創建 FastAPI 應用
app = FastAPI(
    title="Phase 1 增強軌道計算 API",
    description="基於標準化接口的全量衛星軌道計算和數據查詢服務，兼容原有 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加 CORS 支援
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局組件
standard_interface = None
data_provider = None

# Pydantic 模型
class OrbitQueryModel(BaseModel):
    """軌道查詢模型"""
    satellite_ids: Optional[List[str]] = None
    constellations: Optional[List[str]] = None
    time_range_start: Optional[str] = None
    time_range_end: Optional[str] = None
    coordinate_system: str = "eci"
    data_format: str = "json"
    max_records: int = 1000
    include_metadata: bool = True

class BatchQueryModel(BaseModel):
    """批量查詢模型"""
    queries: List[OrbitQueryModel]
    batch_id: Optional[str] = None
    priority: str = "normal"

async def get_standard_interface():
    """獲取標準接口"""
    global standard_interface, data_provider
    
    if standard_interface is None:
        try:
            # 導入標準接口組件
            from phase1_data_provider import create_sgp4_data_provider
            from phase2_interface import create_standard_interface
            
            # 創建數據提供者
            data_provider = create_sgp4_data_provider()
            
            # 創建標準接口
            standard_interface = create_standard_interface(data_provider)
            
            logger.info("✅ 標準接口初始化完成")
            
        except Exception as e:
            logger.error(f"標準接口初始化失敗: {e}")
            raise HTTPException(status_code=500, detail=f"系統初始化失敗: {e}")
    
    return standard_interface

@app.get("/")
async def root():
    """根端點 - API 信息"""
    return {
        "service": "Phase 1 增強軌道計算 API",
        "version": "1.0.0",
        "interface_version": "1.0",
        "status": "running",
        "description": "基於標準化 Phase 1 → Phase 2 接口的軌道數據服務，向下兼容原有 API",
        "endpoints": {
            # 標準接口
            "health": "/health",
            "capabilities": "/capabilities", 
            "satellites": "/satellites",
            "orbit_query": "/orbit/query",
            "orbit_batch": "/orbit/batch",
            "statistics": "/statistics",
            "data_coverage": "/data/coverage",
            "data_integrity": "/data/integrity",
            
            # 兼容接口 (原有 API 格式)
            "legacy_satellite_orbits": "/api/v1/phase1/satellite_orbits",
            "legacy_constellations": "/api/v1/phase1/constellations/info",
            "legacy_health": "/api/v1/phase1/health"
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health")
async def health_check():
    """健康檢查"""
    try:
        interface = await get_standard_interface()
        
        # 使用標準接口檢查能力
        capabilities = interface.get_interface_capabilities()
        
        health_status = {
            "service": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "interface_version": interface.interface_version,
            "data_integrity": capabilities.get("data_integrity_validated", False),
            "components": {
                "standard_interface": "healthy",
                "data_provider": "healthy" if data_provider else "error",
                "available_satellites": capabilities.get("available_satellites", {}).get("total_count", 0)
            }
        }
        
        if not capabilities.get("data_integrity_validated", False):
            health_status["service"] = "degraded"
            health_status["warnings"] = ["數據完整性驗證失敗"]
        
        return health_status
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        raise HTTPException(status_code=500, detail=f"健康檢查失敗: {e}")

# =============================================================================
# 兼容性 API (維持原有接口格式)
# =============================================================================

@app.get("/api/v1/phase1/satellite_orbits")
async def get_satellite_orbits_legacy(
    constellation: str = Query(..., description="星座名稱"),
    count: int = Query(200, ge=1, le=10000, description="返回數量")
):
    """獲取衛星軌道數據 (兼容原有 API 格式)"""
    try:
        interface = await get_standard_interface()
        
        # 導入必要的枚舉類型
        from phase2_interface import CoordinateSystem, DataFormat
        
        # 創建標準查詢請求
        request = interface.create_query_request(
            constellations=[constellation],
            coordinate_system=CoordinateSystem.ECI,
            data_format=DataFormat.JSON,
            max_records=count
        )
        
        # 執行查詢
        response = interface.execute_query(request)
        
        if not response.success:
            raise HTTPException(status_code=500, detail=response.error_message)
        
        # 轉換為兼容格式
        legacy_results = []
        
        if response.data_batch and response.data_batch.orbit_data:
            for orbit in response.data_batch.orbit_data:
                result = {
                    "satellite_id": orbit.satellite_id,
                    "satellite_name": orbit.metadata.get("satellite_name", "") if orbit.metadata else "",
                    "constellation": orbit.constellation,
                    "timestamp": orbit.timestamp.isoformat(),
                    "position": {
                        "x": orbit.position_eci[0],
                        "y": orbit.position_eci[1], 
                        "z": orbit.position_eci[2]
                    },
                    "velocity": {
                        "vx": orbit.velocity_eci[0],
                        "vy": orbit.velocity_eci[1],
                        "vz": orbit.velocity_eci[2]
                    },
                    "data_source": "phase1_sgp4_full_calculation",
                    "algorithm": "complete_sgp4_algorithm"
                }
                legacy_results.append(result)
        
        logger.info(f"返回 {len(legacy_results)} 條 {constellation} 軌道數據 (兼容格式)")
        return legacy_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"兼容 API 查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"軌道數據查詢失敗: {e}")

@app.get("/api/v1/phase1/constellations/info")
async def get_constellations_info_legacy():
    """獲取星座統計信息 (兼容原有 API 格式)"""
    try:
        capabilities = (await get_standard_interface()).get_interface_capabilities()
        data_coverage = data_provider.get_data_coverage()
        
        # 構建兼容格式的響應
        constellations_info = {}
        constellation_dist = data_coverage.get("constellation_distribution", {})
        
        for constellation_name, count in constellation_dist.items():
            constellations_info[constellation_name] = {
                "total_satellites": count,
                "available_satellites": count,
                "data_source": "phase1_sgp4_full_calculation"
            }
        
        result = {
            "generation_timestamp": data_coverage.get("data_load_time", datetime.now(timezone.utc)).isoformat(),
            "algorithm": "complete_sgp4_algorithm",
            "constellations": constellations_info,
            "total_satellites": data_coverage.get("total_satellites", 0)
        }
        
        return result
        
    except Exception as e:
        logger.error(f"兼容 API 星座信息查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"星座信息查詢失敗: {e}")

@app.get("/api/v1/phase1/satellite/{satellite_id}/trajectory")
async def get_satellite_trajectory_legacy(
    satellite_id: str,
    constellation: str = Query(..., description="星座名稱")
):
    """獲取單顆衛星軌跡 (兼容原有 API 格式)"""
    try:
        interface = await get_standard_interface()
        
        # 導入必要的枚舉類型
        from phase2_interface import CoordinateSystem, DataFormat
        
        # 創建時間範圍查詢 (過去1小時到未來1小時)
        now = datetime.now(timezone.utc)
        time_range = (now - timedelta(hours=1), now + timedelta(hours=1))
        
        # 創建標準查詢請求
        request = interface.create_query_request(
            satellite_ids=[satellite_id],
            time_range=time_range,
            coordinate_system=CoordinateSystem.ECI,
            data_format=DataFormat.JSON,
            max_records=1000
        )
        
        # 執行查詢
        response = interface.execute_query(request)
        
        if not response.success:
            if "不存在" in (response.error_message or ""):
                raise HTTPException(status_code=404, detail=f"衛星 '{satellite_id}' 不存在")
            else:
                raise HTTPException(status_code=500, detail=response.error_message)
        
        if not response.data_batch or not response.data_batch.orbit_data:
            raise HTTPException(status_code=404, detail=f"衛星 '{satellite_id}' 軌跡數據不存在")
        
        # 轉換為兼容格式
        positions = []
        satellite_name = ""
        tle_epoch = ""
        
        for orbit in response.data_batch.orbit_data:
            if orbit.satellite_id == satellite_id:
                if not satellite_name and orbit.metadata:
                    satellite_name = orbit.metadata.get("satellite_name", "")
                    tle_epoch = orbit.metadata.get("tle_epoch", "")
                
                positions.append({
                    "timestamp": orbit.timestamp.isoformat(),
                    "position_eci": orbit.position_eci,
                    "velocity_eci": orbit.velocity_eci
                })
        
        result = {
            "satellite_id": satellite_id,
            "satellite_name": satellite_name,
            "constellation": constellation,
            "tle_epoch": tle_epoch,
            "positions": positions,
            "total_positions": len(positions),
            "data_source": "phase1_sgp4_full_calculation",
            "computation_parameters": {
                "algorithm": "complete_sgp4_algorithm",
                "coordinate_system": "eci"
            }
        }
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"兼容 API 衛星軌跡查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"衛星軌跡查詢失敗: {e}")

@app.get("/api/v1/phase1/health")
async def phase1_health_check_legacy():
    """Phase 1 健康檢查 (兼容原有 API 格式)"""
    try:
        # 檢查數據可用性
        data_available = False
        satellite_count = 0
        
        try:
            coverage = data_provider.get_data_coverage()
            data_available = coverage.get("total_satellites", 0) > 0
            satellite_count = coverage.get("total_satellites", 0)
        except:
            pass
        
        status = "healthy" if data_available else "no_data"
        
        return {
            "status": status,
            "service": "Phase 1 Satellite Orbit Data",
            "algorithm": "complete_sgp4_algorithm",
            "data_available": data_available,
            "total_satellites": satellite_count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"兼容 API 健康檢查失敗: {e}")
        return {
            "status": "error",
            "service": "Phase 1 Satellite Orbit Data",
            "algorithm": "complete_sgp4_algorithm",
            "data_available": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

@app.get("/api/v1/phase1/execution/summary")
async def get_execution_summary_legacy():
    """獲取執行摘要 (兼容原有 API 格式)"""
    try:
        coverage = data_provider.get_data_coverage()
        
        # 構建執行摘要 
        summary = {
            "execution_timestamp": coverage.get("data_load_time", datetime.now(timezone.utc)).isoformat(),
            "algorithm": "complete_sgp4_algorithm",
            "data_source": coverage.get("data_source_path", "/netstack/tle_data"),
            "processing_stats": {
                "total_tle_records": coverage.get("total_tle_records", 0),
                "successful_satellites": coverage.get("total_satellites", 0),
                "constellation_distribution": coverage.get("constellation_distribution", {})
            },
            "sgp4_engine_stats": coverage.get("sgp4_engine_stats", {}),
            "status": "completed"
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"兼容 API 執行摘要查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"執行摘要查詢失敗: {e}")

# =============================================================================
# 新標準 API 接口
# =============================================================================

@app.get("/capabilities")
async def get_capabilities():
    """獲取接口能力"""
    try:
        interface = await get_standard_interface()
        capabilities = interface.get_interface_capabilities()
        
        return {
            "interface_capabilities": capabilities,
            "query_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"獲取接口能力失敗: {e}")
        raise HTTPException(status_code=500, detail=f"接口能力查詢失敗: {e}")

@app.get("/satellites")
async def get_satellites(
    constellation: Optional[str] = Query(None, description="星座名稱篩選"),
    limit: int = Query(100, ge=1, le=10000, description="返回數量限制"),
    include_details: bool = Query(False, description="包含詳細信息")
):
    """獲取衛星列表"""
    try:
        interface = await get_standard_interface()
        
        # 獲取可用衛星
        available_satellites = data_provider.get_available_satellites()
        
        # 如果指定星座，進行篩選
        if constellation:
            satellite_catalog = data_provider.satellite_catalog
            filtered_satellites = [
                sat_id for sat_id in available_satellites
                if satellite_catalog.get(sat_id, {}).get('constellation') == constellation
            ]
        else:
            filtered_satellites = available_satellites
        
        # 應用限制
        limited_satellites = filtered_satellites[:limit]
        
        response = {
            "total_satellites": len(available_satellites),
            "filtered_satellites": len(filtered_satellites),
            "returned_satellites": len(limited_satellites),
            "constellation_filter": constellation,
            "satellites": limited_satellites,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # 如果需要詳細信息
        if include_details and limited_satellites:
            satellite_catalog = data_provider.satellite_catalog
            detailed_satellites = []
            
            for sat_id in limited_satellites:
                sat_info = satellite_catalog.get(sat_id, {})
                detailed_satellites.append({
                    "satellite_id": sat_id,
                    "satellite_name": sat_info.get('satellite_name', ''),
                    "constellation": sat_info.get('constellation', ''),
                    "tle_epoch": sat_info.get('epoch', '').isoformat() if sat_info.get('epoch') else None,
                    "loaded_time": sat_info.get('loaded_time', '').isoformat() if sat_info.get('loaded_time') else None
                })
            
            response["satellite_details"] = detailed_satellites
        
        return response
        
    except Exception as e:
        logger.error(f"獲取衛星列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"衛星列表查詢失敗: {e}")

@app.post("/orbit/query")
async def query_orbit_data(query: OrbitQueryModel):
    """標準軌道數據查詢"""
    try:
        interface = await get_standard_interface()
        
        # 導入必要的枚舉類型
        from phase2_interface import CoordinateSystem, DataFormat
        
        # 解析坐標系統
        coord_system = CoordinateSystem.ECI if query.coordinate_system.lower() == "eci" else CoordinateSystem.TEME
        
        # 解析數據格式
        data_format = DataFormat.JSON  # 目前只支援 JSON
        
        # 解析時間範圍
        time_range = None
        if query.time_range_start and query.time_range_end:
            try:
                start_time = datetime.fromisoformat(query.time_range_start.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(query.time_range_end.replace('Z', '+00:00'))
                time_range = (start_time, end_time)
            except ValueError as ve:
                raise HTTPException(status_code=400, detail=f"時間格式錯誤: {ve}")
        
        # 創建標準查詢請求
        request = interface.create_query_request(
            satellite_ids=query.satellite_ids,
            constellations=query.constellations,
            time_range=time_range,
            coordinate_system=coord_system,
            data_format=data_format,
            max_records=query.max_records
        )
        
        # 執行查詢
        response = interface.execute_query(request)
        
        # 轉換為 API 響應格式
        api_response = {
            "request_id": response.request_id,
            "success": response.success,
            "total_matches": response.total_matches,
            "returned_records": response.returned_records,
            "has_more_data": response.has_more_data,
            "response_time": response.response_time.isoformat(),
            "performance_metrics": response.performance_metrics,
            "error_message": response.error_message
        }
        
        # 添加數據批次信息
        if response.data_batch:
            batch = response.data_batch
            api_response["data_batch"] = {
                "batch_id": batch.batch_id,
                "generation_time": batch.generation_time.isoformat(),
                "time_range": {
                    "start": batch.time_range_start.isoformat(),
                    "end": batch.time_range_end.isoformat()
                },
                "satellite_count": batch.satellite_count,
                "total_records": batch.total_records,
                "quality_metrics": batch.quality_metrics,
                "orbit_data": [
                    {
                        "satellite_id": orbit.satellite_id,
                        "constellation": orbit.constellation,
                        "timestamp": orbit.timestamp.isoformat(),
                        "position_eci": orbit.position_eci,
                        "velocity_eci": orbit.velocity_eci,
                        "position_teme": orbit.position_teme,
                        "velocity_teme": orbit.velocity_teme,
                        "calculation_quality": orbit.calculation_quality,
                        "error_code": orbit.error_code,
                        "metadata": orbit.metadata
                    }
                    for orbit in batch.orbit_data
                ]
            }
            
            # 如果需要，創建數據摘要
            summary = interface.create_data_summary(batch)
            api_response["data_summary"] = summary
        
        return api_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"軌道數據查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"軌道數據查詢失敗: {e}")

@app.get("/statistics")
async def get_statistics():
    """獲取統計信息"""
    try:
        interface = await get_standard_interface()
        capabilities = interface.get_interface_capabilities()
        
        stats = {
            "service_info": {
                "name": "Phase 1 增強軌道計算 API",
                "version": "1.0.0",
                "interface_version": interface.interface_version,
                "uptime": "運行中"
            },
            "data_statistics": capabilities.get("data_coverage", {}),
            "satellite_statistics": capabilities.get("available_satellites", {}),
            "interface_capabilities": {
                "supported_formats": capabilities.get("supported_data_formats", []),
                "supported_coordinates": capabilities.get("supported_coordinate_systems", []),
                "max_records_per_query": capabilities.get("max_records_per_query", 0)
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"獲取統計信息失敗: {e}")
        raise HTTPException(status_code=500, detail=f"統計信息查詢失敗: {e}")

if __name__ == "__main__":
    import uvicorn
    
    logging.basicConfig(level=logging.INFO)
    logger.info("啟動 Phase 1 增強軌道計算 API")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)