"""
UAV Tracking API Routes

This module handles UAV-related routes including position tracking and trajectory management.
Extracted from the monolithic app/api/v1/router.py as part of Phase 2 refactoring.
"""

from fastapi import APIRouter, HTTPException, Response, status
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime
import json

router = APIRouter()


class UAVPosition(BaseModel):
    """UAV 位置資料模型"""
    uav_id: str
    latitude: float
    longitude: float
    altitude: float
    heading: Optional[float] = 0.0
    speed: Optional[float] = 0.0
    timestamp: Optional[str] = None


class UAVPositionResponse(BaseModel):
    """UAV 位置回應模型"""
    success: bool
    uav_id: str
    position: UAVPosition
    message: Optional[str] = None


# In-memory storage for UAV positions (should be replaced with proper database)
uav_positions: Dict[str, UAVPosition] = {}


@router.post("/uav/position", tags=["UAV Tracking"])
async def update_uav_position(position: UAVPosition):
    """
    更新 UAV 位置
    """
    try:
        # Set timestamp if not provided
        if not position.timestamp:
            position.timestamp = datetime.utcnow().isoformat()
        
        # Store position in memory (TODO: persist to database)
        uav_positions[position.uav_id] = position
        
        return UAVPositionResponse(
            success=True,
            uav_id=position.uav_id,
            position=position,
            message=f"Position updated for UAV {position.uav_id}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update UAV position: {str(e)}"
        )


@router.get("/uav/{uav_id}/position", tags=["UAV Tracking"])
async def get_uav_position(uav_id: str):
    """
    獲取特定 UAV 的位置
    """
    if uav_id not in uav_positions:
        raise HTTPException(
            status_code=404,
            detail={
                "error": f"UAV '{uav_id}' not found",
                "available_uavs": list(uav_positions.keys())
            }
        )
    
    position = uav_positions[uav_id]
    
    return UAVPositionResponse(
        success=True,
        uav_id=uav_id,
        position=position,
        message=f"Current position for UAV {uav_id}"
    )


@router.get("/uav/positions", tags=["UAV Tracking"])
async def get_all_uav_positions():
    """
    獲取所有 UAV 的位置
    """
    if not uav_positions:
        return {
            "success": True,
            "count": 0,
            "positions": [],
            "message": "No UAV positions available"
        }
    
    positions_list = [
        UAVPositionResponse(
            success=True,
            uav_id=uav_id,
            position=position
        )
        for uav_id, position in uav_positions.items()
    ]
    
    return {
        "success": True,
        "count": len(positions_list),
        "positions": positions_list,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.delete("/uav/{uav_id}/position", tags=["UAV Tracking"])
async def delete_uav_position(uav_id: str):
    """
    刪除 UAV 位置記錄
    """
    if uav_id not in uav_positions:
        raise HTTPException(
            status_code=404,
            detail=f"UAV '{uav_id}' not found"
        )
    
    deleted_position = uav_positions.pop(uav_id)
    
    return {
        "success": True,
        "message": f"Position record for UAV {uav_id} deleted",
        "deleted_position": deleted_position,
        "remaining_uavs": list(uav_positions.keys())
    }


class UAVTrajectory(BaseModel):
    """UAV 軌跡資料模型"""
    uav_id: str
    trajectory_points: List[UAVPosition]
    total_distance_km: Optional[float] = None
    duration_minutes: Optional[float] = None


@router.post("/uav/{uav_id}/trajectory", tags=["UAV Tracking"])
async def update_uav_trajectory(uav_id: str, trajectory: UAVTrajectory):
    """
    更新 UAV 軌跡
    """
    try:
        if trajectory.uav_id != uav_id:
            raise HTTPException(
                status_code=400,
                detail="UAV ID in path does not match UAV ID in trajectory data"
            )
        
        # Update current position to latest trajectory point
        if trajectory.trajectory_points:
            latest_position = trajectory.trajectory_points[-1]
            uav_positions[uav_id] = latest_position
        
        return {
            "success": True,
            "uav_id": uav_id,
            "trajectory_points": len(trajectory.trajectory_points),
            "message": f"Trajectory updated for UAV {uav_id}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update UAV trajectory: {str(e)}"
        )


@router.get("/uav/{uav_id}/stats", tags=["UAV Tracking"])
async def get_uav_stats(uav_id: str):
    """
    獲取 UAV 統計資訊
    """
    if uav_id not in uav_positions:
        raise HTTPException(
            status_code=404,
            detail=f"UAV '{uav_id}' not found"
        )
    
    position = uav_positions[uav_id]
    
    # Calculate basic stats
    stats = {
        "uav_id": uav_id,
        "current_position": position,
        "altitude_category": "low" if position.altitude < 100 else "medium" if position.altitude < 500 else "high",
        "speed_category": "stationary" if position.speed < 1 else "slow" if position.speed < 10 else "fast",
        "last_update": position.timestamp,
        "tracking_duration_minutes": 0,  # TODO: calculate from first position
    }
    
    return stats


@router.get("/uav/stats/summary", tags=["UAV Tracking"])
async def get_uav_summary_stats():
    """
    獲取所有 UAV 的統計摘要
    """
    if not uav_positions:
        return {
            "total_uavs": 0,
            "active_uavs": 0,
            "avg_altitude": 0,
            "avg_speed": 0,
            "altitude_distribution": {},
            "speed_distribution": {}
        }
    
    altitudes = [pos.altitude for pos in uav_positions.values()]
    speeds = [pos.speed or 0 for pos in uav_positions.values()]
    
    # Calculate distributions
    altitude_dist = {
        "low": len([a for a in altitudes if a < 100]),
        "medium": len([a for a in altitudes if 100 <= a < 500]),
        "high": len([a for a in altitudes if a >= 500])
    }
    
    speed_dist = {
        "stationary": len([s for s in speeds if s < 1]),
        "slow": len([s for s in speeds if 1 <= s < 10]),
        "fast": len([s for s in speeds if s >= 10])
    }
    
    return {
        "total_uavs": len(uav_positions),
        "active_uavs": len(uav_positions),  # All stored positions are considered active
        "avg_altitude": round(sum(altitudes) / len(altitudes), 2) if altitudes else 0,
        "avg_speed": round(sum(speeds) / len(speeds), 2) if speeds else 0,
        "altitude_distribution": altitude_dist,
        "speed_distribution": speed_dist,
        "timestamp": datetime.utcnow().isoformat()
    }