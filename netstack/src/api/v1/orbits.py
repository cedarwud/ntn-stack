"""
軌道計算與衛星軌跡 API 端點

提供衛星軌道計算與軌跡預測的 RESTful API 接口，包括：
- 衛星軌跡查詢
- 軌道參數獲取
- 位置預測
- 可視化數據生成
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import logging

# 導入軌道計算引擎
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "../../../netstack_api"))

from services.orbit_calculation_engine import OrbitCalculationEngine

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/orbits", tags=["Orbital Calculations"])

# 全局軌道計算引擎實例
orbit_engine: Optional[OrbitCalculationEngine] = None


# Pydantic 模型定義
class TrajectoryPoint(BaseModel):
    """軌跡點模型"""

    timestamp: float = Field(..., description="時間戳 (Unix timestamp)")
    latitude: float = Field(..., description="緯度 (度)")
    longitude: float = Field(..., description="經度 (度)")
    altitude: float = Field(..., description="高度 (km)")
    velocity: float = Field(0.0, description="速度 (km/s)")


class TrajectoryResponse(BaseModel):
    """軌跡響應模型"""

    satellite_id: str = Field(..., description="衛星ID")
    start_time: float = Field(..., description="開始時間 (Unix timestamp)")
    end_time: float = Field(..., description="結束時間 (Unix timestamp)")
    step_seconds: int = Field(..., description="時間步長 (秒)")
    trajectory: List[TrajectoryPoint] = Field(..., description="軌跡點列表")
    total_points: int = Field(..., description="總點數")


class ErrorResponse(BaseModel):
    """錯誤響應模型"""

    error: str = Field(..., description="錯誤類型")
    message: str = Field(..., description="錯誤消息")
    status_code: int = Field(..., description="HTTP狀態碼")
    timestamp: str = Field(..., description="時間戳")
    path: str = Field(..., description="請求路徑")
    method: str = Field(..., description="HTTP方法")


# 啟動事件
@router.on_event("startup")
async def startup_orbit_service():
    """啟動軌道服務"""
    global orbit_engine
    try:
        orbit_engine = OrbitCalculationEngine()
        logger.info("軌道計算引擎初始化成功")
    except Exception as e:
        logger.error(f"軌道計算引擎初始化失敗: {e}")
        raise


# 關閉事件
@router.on_event("shutdown")
async def shutdown_orbit_service():
    """關閉軌道服務"""
    global orbit_engine
    if orbit_engine:
        logger.info("軌道服務關閉")
        orbit_engine = None


@router.get(
    "/satellite/{satellite_id}/trajectory",
    summary="獲取衛星軌跡",
    description="根據衛星ID和時間範圍計算衛星軌跡",
    response_model=TrajectoryResponse,
    responses={
        400: {"model": ErrorResponse, "description": "請求參數錯誤"},
        404: {"model": ErrorResponse, "description": "衛星未找到"},
        500: {"model": ErrorResponse, "description": "服務器內部錯誤"},
    },
)
async def get_satellite_trajectory(
    satellite_id: str,
    start_time: float = Query(..., description="開始時間 (Unix timestamp)"),
    duration_hours: float = Query(2.0, description="持續時間 (小時)", ge=0.1, le=24.0),
    step_minutes: float = Query(0.5, description="時間步長 (分鐘)", ge=0.1, le=60.0),
):
    """
    獲取指定衛星的軌跡數據

    Args:
        satellite_id: 衛星ID (NORAD ID)
        start_time: 開始時間的 Unix 時間戳
        duration_hours: 軌跡持續時間 (小時)
        step_minutes: 時間步長 (分鐘)

    Returns:
        包含軌跡點的響應對象
    """
    global orbit_engine

    if not orbit_engine:
        raise HTTPException(status_code=500, detail="軌道計算引擎未初始化")

    try:
        # 計算結束時間和步長秒數
        end_time = start_time + (duration_hours * 3600)
        step_seconds = int(step_minutes * 60)

        # 調用軌道計算引擎
        trajectory_data = orbit_engine.calculate_satellite_trajectory(
            satellite_id=satellite_id,
            start_time=start_time,
            end_time=end_time,
            step_seconds=step_seconds,
        )

        # 將軌跡數據轉換為響應格式
        trajectory_points = []
        for point in trajectory_data:
            trajectory_points.append(
                TrajectoryPoint(
                    timestamp=point.get("timestamp", start_time),
                    latitude=point.get("latitude", 0.0),
                    longitude=point.get("longitude", 0.0),
                    altitude=point.get("altitude", 550.0),
                    velocity=point.get("velocity", 7.5),
                )
            )

        return TrajectoryResponse(
            satellite_id=satellite_id,
            start_time=start_time,
            end_time=end_time,
            step_seconds=step_seconds,
            trajectory=trajectory_points,
            total_points=len(trajectory_points),
        )

    except ValueError as ve:
        logger.error(f"軌跡計算參數錯誤 - 衛星ID: {satellite_id}, 錯誤: {ve}")
        raise HTTPException(status_code=400, detail=f"參數錯誤: {str(ve)}")
    except FileNotFoundError as fe:
        logger.error(f"衛星數據未找到 - 衛星ID: {satellite_id}, 錯誤: {fe}")
        raise HTTPException(status_code=404, detail=f"衛星 {satellite_id} 的數據未找到")
    except Exception as e:
        logger.error(f"軌跡計算失敗 - 衛星ID: {satellite_id}, 錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"軌跡計算失敗: {str(e)}")


@router.get(
    "/satellite/{satellite_id}/position",
    summary="獲取衛星當前位置",
    description="獲取指定衛星在指定時間的位置信息",
)
async def get_satellite_position(
    satellite_id: str,
    timestamp: Optional[float] = Query(
        None, description="時間戳 (Unix timestamp)，默認為當前時間"
    ),
):
    """獲取衛星在指定時間的位置"""
    global orbit_engine

    if not orbit_engine:
        raise HTTPException(status_code=500, detail="軌道計算引擎未初始化")

    try:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).timestamp()

        # 獲取單個時間點的軌跡
        trajectory_data = orbit_engine.calculate_satellite_trajectory(
            satellite_id=satellite_id,
            start_time=timestamp,
            end_time=timestamp + 1,  # 1秒後
            step_seconds=1,
        )

        if not trajectory_data:
            raise HTTPException(
                status_code=404,
                detail=f"無法獲取衛星 {satellite_id} 在時間 {timestamp} 的位置",
            )

        position = trajectory_data[0]
        return {
            "satellite_id": satellite_id,
            "timestamp": timestamp,
            "position": {
                "latitude": position.get("latitude", 0.0),
                "longitude": position.get("longitude", 0.0),
                "altitude": position.get("altitude", 550.0),
            },
            "velocity": position.get("velocity", 7.5),
        }

    except Exception as e:
        logger.error(f"位置計算失敗 - 衛星ID: {satellite_id}, 錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"位置計算失敗: {str(e)}")


@router.get(
    "/health", summary="軌道服務健康檢查", description="檢查軌道計算服務的運行狀態"
)
async def orbit_service_health():
    """軌道服務健康檢查"""
    global orbit_engine

    return {
        "service": "orbits",
        "status": "healthy" if orbit_engine else "unhealthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engine_status": "initialized" if orbit_engine else "not_initialized",
    }
