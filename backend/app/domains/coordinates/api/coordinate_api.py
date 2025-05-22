import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from app.domains.coordinates.models.coordinate_model import (
    GeoCoordinate,
    CartesianCoordinate,
)
from app.domains.coordinates.services.coordinate_service import CoordinateService

logger = logging.getLogger(__name__)
router = APIRouter()

# 創建座標服務的單例
coordinate_service = CoordinateService()


@router.post("/geo-to-cartesian", response_model=CartesianCoordinate)
async def convert_geo_to_cartesian(geo: GeoCoordinate) -> CartesianCoordinate:
    """將地理座標轉換為笛卡爾座標"""
    try:
        result = await coordinate_service.geo_to_cartesian(geo)
        logger.info(f"Converted geo coords {geo} to cartesian {result}")
        return result
    except Exception as e:
        logger.error(f"Error converting geo to cartesian: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Coordinate conversion error: {str(e)}",
        )


@router.post("/cartesian-to-geo", response_model=GeoCoordinate)
async def convert_cartesian_to_geo(cartesian: CartesianCoordinate) -> GeoCoordinate:
    """將笛卡爾座標轉換為地理座標"""
    try:
        result = await coordinate_service.cartesian_to_geo(cartesian)
        logger.info(f"Converted cartesian coords {cartesian} to geo {result}")
        return result
    except Exception as e:
        logger.error(f"Error converting cartesian to geo: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Coordinate conversion error: {str(e)}",
        )


@router.post("/geo-to-ecef", response_model=CartesianCoordinate)
async def convert_geo_to_ecef(geo: GeoCoordinate) -> CartesianCoordinate:
    """將地理座標轉換為地球中心地固座標 (ECEF)"""
    try:
        result = await coordinate_service.geo_to_ecef(geo)
        logger.info(f"Converted geo coords {geo} to ECEF {result}")
        return result
    except Exception as e:
        logger.error(f"Error converting geo to ECEF: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Coordinate conversion error: {str(e)}",
        )


@router.post("/ecef-to-geo", response_model=GeoCoordinate)
async def convert_ecef_to_geo(ecef: CartesianCoordinate) -> GeoCoordinate:
    """將地球中心地固座標 (ECEF) 轉換為地理座標"""
    try:
        result = await coordinate_service.ecef_to_geo(ecef)
        logger.info(f"Converted ECEF coords {ecef} to geo {result}")
        return result
    except Exception as e:
        logger.error(f"Error converting ECEF to geo: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Coordinate conversion error: {str(e)}",
        )


@router.post("/bearing-distance", response_model=Dict[str, float])
async def calculate_bearing_distance(
    point1: GeoCoordinate, point2: GeoCoordinate
) -> Dict[str, float]:
    """計算兩點間的方位角和距離"""
    try:
        bearing, distance = await coordinate_service.bearing_distance(point1, point2)
        logger.info(
            f"Calculated bearing {bearing}° and distance {distance}m between {point1} and {point2}"
        )
        return {"bearing": bearing, "distance": distance}
    except Exception as e:
        logger.error(f"Error calculating bearing and distance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calculation error: {str(e)}",
        )


@router.post("/destination-point", response_model=GeoCoordinate)
async def calculate_destination_point(
    start: GeoCoordinate, bearing: float, distance: float
) -> GeoCoordinate:
    """根據起點、方位角和距離計算終點座標"""
    try:
        result = await coordinate_service.destination_point(start, bearing, distance)
        logger.info(
            f"Calculated destination point {result} from {start} with bearing {bearing}° and distance {distance}m"
        )
        return result
    except Exception as e:
        logger.error(f"Error calculating destination point: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calculation error: {str(e)}",
        )
