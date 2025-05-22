# backend/app/api/v1/router.py
from fastapi import APIRouter, Response, status, Query
import os
from starlette.responses import FileResponse
from datetime import datetime, timedelta
import random
from typing import List, Optional
from pydantic import BaseModel

# Import new domain API routers
from app.domains.device.api.device_api import router as device_router

# 暫時註釋掉問題模組 - 將在解決SQLModel配置問題後恢復
# from app.domains.coordinates.api.coordinate_api import router as coordinates_router
# from app.domains.satellite.api.satellite_api import router as satellite_router
from app.domains.simulation.api.simulation_api import router as simulation_router
from app.domains.network.api.platform_api import router as platform_router

api_router = APIRouter()

# Register domain API routers
api_router.include_router(device_router, prefix="/devices", tags=["Devices"])
# 暫時註釋掉問題路由 - 將在解決SQLModel配置問題後恢復
# api_router.include_router(
#     coordinates_router, prefix="/coordinates", tags=["Coordinates"]
# )
# api_router.include_router(satellite_router, prefix="/satellites", tags=["Satellites"])
api_router.include_router(
    simulation_router, prefix="/simulations", tags=["Simulations"]
)
api_router.include_router(platform_router, prefix="/network", tags=["Network Platform"])


# 添加模型資源路由
@api_router.get("/sionna/models/{model_name}", tags=["Models"])
async def get_model(model_name: str):
    """提供3D模型文件"""
    # 定義模型文件存儲路徑
    static_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "static",
    )
    models_dir = os.path.join(static_dir, "models")

    # 獲取對應的模型文件
    model_file = os.path.join(models_dir, f"{model_name}.glb")

    # 檢查文件是否存在
    if not os.path.exists(model_file):
        return Response(
            content=f"模型 {model_name} 不存在", status_code=status.HTTP_404_NOT_FOUND
        )

    # 返回模型文件
    return FileResponse(
        path=model_file, media_type="model/gltf-binary", filename=f"{model_name}.glb"
    )


# 定義衛星可見性數據模型
class VisibleSatelliteInfo(BaseModel):
    norad_id: str
    name: str
    elevation_deg: float
    azimuth_deg: float
    distance_km: float
    velocity_km_s: float
    visible_for_sec: int
    orbit_altitude_km: float
    magnitude: Optional[float] = None


# 添加臨時的衛星可見性模擬端點
@api_router.get("/satellite-ops/visible_satellites", tags=["Satellites"])
async def get_visible_satellites(
    count: int = Query(10, gt=0, le=100),
    min_elevation_deg: float = Query(0, ge=0, le=90),
):
    """模擬返回可見衛星數據，用於前端開發"""

    # 模擬衛星數據生成
    satellites = []
    for i in range(count):
        # 生成隨機衛星數據
        elevation = random.uniform(min_elevation_deg, 90)
        satellite = VisibleSatelliteInfo(
            norad_id=f"NORAD-{40000 + i}",
            name=f"OneWeb-{1000 + i}",
            elevation_deg=elevation,
            azimuth_deg=random.uniform(0, 360),
            distance_km=random.uniform(500, 2000),
            velocity_km_s=random.uniform(5, 8),
            visible_for_sec=int(random.uniform(300, 1200)),
            orbit_altitude_km=random.uniform(500, 1200),
            magnitude=random.uniform(-1, 5),
        )
        satellites.append(satellite)

    # 按仰角從高到低排序
    satellites.sort(key=lambda x: x.elevation_deg, reverse=True)

    return {"satellites": satellites}
