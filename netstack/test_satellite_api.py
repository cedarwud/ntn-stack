#!/usr/bin/env python3
"""
簡化的衛星映射 API 測試服務
用於測試衛星位置轉換為 gNodeB 參數功能
"""

from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import asyncio
import uuid

from netstack_api.services.satellite_gnb_mapping_service import SatelliteGnbMappingService
from netstack_api.models.ueransim_models import UAVPosition, NetworkParameters, UERANSIMConfigRequest

app = FastAPI(
    title="衛星映射測試 API",
    description="測試衛星位置轉換為 gNodeB 參數功能",
    version="1.0.0"
)

# 初始化衛星映射服務
satellite_service = SatelliteGnbMappingService(
    simworld_api_url="http://localhost:8000",  # simworld 服務地址
    redis_client=None  # 不使用 Redis 緩存
)

class SatelliteMappingRequest(BaseModel):
    satellite_id: int
    uav_latitude: Optional[float] = None
    uav_longitude: Optional[float] = None
    uav_altitude: Optional[float] = None
    frequency: Optional[int] = 2100
    bandwidth: Optional[int] = 20

class TrackingRequest(BaseModel):
    satellite_ids: str
    update_interval: int = 30

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {"status": "healthy", "service": "satellite_mapping_test"}

@app.post("/api/v1/satellite-gnb/mapping")
async def convert_satellite_to_gnb(request: SatelliteMappingRequest):
    """
    將衛星位置轉換為 gNodeB 參數
    """
    try:
        # 構建 UAV 位置（如果提供）
        uav_position = None
        if all([request.uav_latitude, request.uav_longitude, request.uav_altitude]):
            uav_position = UAVPosition(
                id="test_uav",
                latitude=request.uav_latitude,
                longitude=request.uav_longitude,
                altitude=request.uav_altitude
            )
        
        # 構建網絡參數
        network_params = NetworkParameters(
            frequency=request.frequency,
            bandwidth=request.bandwidth
        )
        
        # 調用衛星映射服務
        result = await satellite_service.convert_satellite_to_gnb_config(
            satellite_id=request.satellite_id,
            uav_position=uav_position,
            network_params=network_params
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"轉換失敗: {str(e)}")

@app.get("/api/v1/satellite-gnb/batch-mapping")
async def batch_convert_satellites_to_gnb(
    satellite_ids: str,
    uav_latitude: Optional[float] = None,
    uav_longitude: Optional[float] = None,
    uav_altitude: Optional[float] = None
):
    """
    批量轉換多個衛星位置為 gNodeB 參數
    """
    try:
        # 解析衛星 ID 列表
        sat_ids = [int(id.strip()) for id in satellite_ids.split(",")]
        
        # 構建 UAV 位置（如果提供）
        uav_position = None
        if all([uav_latitude, uav_longitude, uav_altitude]):
            uav_position = UAVPosition(
                id="test_uav",
                latitude=uav_latitude,
                longitude=uav_longitude,
                altitude=uav_altitude
            )
        
        # 批量轉換
        results = await satellite_service.get_multiple_satellite_configs(
            satellite_ids=sat_ids,
            uav_position=uav_position
        )
        
        # 統計結果
        total_satellites = len(sat_ids)
        successful_conversions = sum(1 for r in results.values() if r.get("success", False))
        success_rate = f"{(successful_conversions / total_satellites * 100):.1f}%"
        
        return {
            "success": True,
            "summary": {
                "total_satellites": total_satellites,
                "successful_conversions": successful_conversions,
                "success_rate": success_rate
            },
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量轉換失敗: {str(e)}")

@app.post("/api/v1/satellite-gnb/start-tracking")
async def start_continuous_tracking(request: TrackingRequest):
    """
    啟動衛星持續追蹤
    """
    try:
        # 解析衛星 ID 列表
        sat_ids = [int(id.strip()) for id in request.satellite_ids.split(",")]
        
        # 生成任務 ID
        task_id = str(uuid.uuid4())
        
        # 模擬啟動追蹤任務
        # 在實際實現中，這裡會啟動後台任務
        
        return {
            "success": True,
            "message": "衛星持續追蹤已啟動",
            "tracking_info": {
                "task_id": task_id,
                "satellite_ids": sat_ids,
                "update_interval_seconds": request.update_interval,
                "status": "active"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"啟動追蹤失敗: {str(e)}")

@app.post("/api/v1/ueransim/config/generate")
async def generate_ueransim_config(request: UERANSIMConfigRequest):
    """
    生成 UERANSIM 配置（整合衛星映射）
    """
    try:
        # 如果有衛星信息，先進行位置轉換
        gnb_config = None
        if request.satellite:
            # 構建 UAV 位置
            uav_position = None
            if request.uav:
                uav_position = UAVPosition(
                    id=request.uav.id,
                    latitude=request.uav.latitude,
                    longitude=request.uav.longitude,
                    altitude=request.uav.altitude
                )
            
            # 轉換衛星位置為 gNodeB 配置
            # 從衛星 ID 中提取數字部分
            satellite_id = 1  # 默認值
            if request.satellite.id.isdigit():
                satellite_id = int(request.satellite.id)
            elif "SAT-" in request.satellite.id:
                # 提取 SAT-001 中的 001
                try:
                    satellite_id = int(request.satellite.id.split("-")[-1])
                except:
                    satellite_id = 1
            
            satellite_result = await satellite_service.convert_satellite_to_gnb_config(
                satellite_id=satellite_id,
                uav_position=uav_position,
                network_params=request.network_params
            )
            
            if satellite_result.get("success"):
                gnb_config = satellite_result["gnb_config"]
        
        # 生成 UERANSIM 配置回應
        return {
            "success": True,
            "scenario_type": request.scenario.value,
            "gnb_config": gnb_config,
            "scenario_info": {
                "scenario_type": request.scenario.value,
                "generation_time": "2025-05-27T00:57:00.000000",
                "satellite_info": request.satellite.dict() if request.satellite else None,
                "uav_info": request.uav.dict() if request.uav else None,
                "network_info": {
                    "distance_km": 1500.0,
                    "path_loss_db": 342.4,
                    "adjusted_tx_power": 12.5
                } if gnb_config else None
            },
            "config_yaml": "# UERANSIM 配置 YAML\n# 基於衛星映射生成",
            "message": "UERANSIM 配置生成成功（整合衛星映射）"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配置生成失敗: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8083) 