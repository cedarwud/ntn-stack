"""
Satellite API Routes

This module handles satellite-related routes including orbital calculations and satellite operations.
Extracted from the monolithic app/api/v1/router.py as part of Phase 2 refactoring.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio
import json

# Import satellite services
from app.domains.satellite.services.cqrs_satellite_service import (
    CQRSSatelliteService,
    SatellitePosition,
)
from app.domains.coordinates.models.coordinate_model import GeoCoordinate

# Import Skyfield
from skyfield.api import load, wgs84, EarthSatellite
import numpy as np

router = APIRouter()

# Global satellite data (will be refactored to proper service injection later)
ts = None
satellites = []
satellites_dict = {}
starlink_sats = []
kuiper_sats = []
oneweb_sats = []
globalstar_sats = []
iridium_sats = []
SKYFIELD_LOADED = False


async def initialize_satellites():
    """
    Initialize satellite data from database
    TODO: This should be moved to a proper satellite service
    """
    global ts, satellites, satellites_dict, starlink_sats, kuiper_sats, oneweb_sats, globalstar_sats, iridium_sats, SKYFIELD_LOADED

    if SKYFIELD_LOADED:
        return

    try:
        print("開始加載 Skyfield 時間尺度和衛星數據...")
        ts = load.timescale(builtin=True)
        print("時間尺度加載成功")

        # Load satellites from database
        from app.db.base import async_session_maker
        from app.domains.satellite.adapters.sqlmodel_satellite_repository import (
            SQLModelSatelliteRepository,
        )

        async def load_satellites_from_db():
            async with async_session_maker() as session:
                repo = SQLModelSatelliteRepository()
                repo._session = session
                db_satellites = await repo.get_satellites()

                skyfield_satellites = []
                for sat in db_satellites:
                    if sat.tle_data:
                        try:
                            tle_dict = (
                                json.loads(sat.tle_data)
                                if isinstance(sat.tle_data, str)
                                else sat.tle_data
                            )
                            line1 = tle_dict["line1"]
                            line2 = tle_dict["line2"]
                            skyfield_sat = EarthSatellite(line1, line2, sat.name, ts)
                            skyfield_satellites.append(skyfield_sat)
                        except Exception as e:
                            print(f"載入衛星 {sat.name} 失敗: {e}")

                return skyfield_satellites

        satellites = await load_satellites_from_db()
        print(f"從資料庫載入衛星成功，共 {len(satellites)} 顆衛星")

        # Build satellite dictionary
        satellites_dict = {sat.name: sat for sat in satellites}

        # Categorize satellites
        starlink_sats = [sat for sat in satellites if "STARLINK" in sat.name.upper()]
        kuiper_sats = [sat for sat in satellites if "KUIPER" in sat.name.upper()]
        oneweb_sats = [sat for sat in satellites if "ONEWEB" in sat.name.upper()]
        globalstar_sats = [
            sat for sat in satellites if "GLOBALSTAR" in sat.name.upper()
        ]
        iridium_sats = [sat for sat in satellites if "IRIDIUM" in sat.name.upper()]

        SKYFIELD_LOADED = True
        print(f"衛星分類完成: Starlink={len(starlink_sats)}, Kuiper={len(kuiper_sats)}")

    except Exception as e:
        print(f"衛星初始化失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"Satellite initialization failed: {e}"
        )


@router.get("/orbit/{satellite_id}", tags=["Satellites"])
async def get_satellite_orbit(satellite_id: str):
    """
    獲取衛星軌道資訊
    """
    await initialize_satellites()

    if satellite_id not in satellites_dict:
        available_satellites = list(satellites_dict.keys())[:10]  # Show first 10
        raise HTTPException(
            status_code=404,
            detail={
                "error": f"Satellite '{satellite_id}' not found",
                "available_satellites": available_satellites,
                "total_satellites": len(satellites_dict),
            },
        )

    try:
        satellite = satellites_dict[satellite_id]
        now = ts.now()

        # Calculate current position
        geocentric = satellite.at(now)
        subpoint = wgs84.subpoint(geocentric)

        # Calculate next pass information (simplified)
        orbit_info = {
            "satellite_id": satellite_id,
            "satellite_name": satellite.name,
            "current_position": {
                "latitude": subpoint.latitude.degrees,
                "longitude": subpoint.longitude.degrees,
                "altitude_km": subpoint.elevation.km,
                "timestamp": now.utc_iso(),
            },
            "orbital_period_minutes": 90,  # Approximate for LEO
            "inclination_degrees": 53.0,  # Approximate for Starlink
            "eccentricity": 0.0001,  # Nearly circular
        }

        return orbit_info

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating orbit: {e}")


@router.get("/visible_satellites", tags=["Satellites"])
async def get_visible_satellites(
    count: int = Query(default=50, description="回傳衛星數量限制"),
    min_elevation_deg: float = Query(default=-10.0, description="最小仰角 (度)"),
    observer_lat: float = Query(default=0.0, description="觀察者緯度"),
    observer_lon: float = Query(default=0.0, description="觀察者經度"),
    observer_alt: float = Query(default=0.0, description="觀察者高度 (公尺)"),
    global_view: bool = Query(default=True, description="全球視野模式"),
    constellation: Optional[str] = Query(default=None, description="星座過濾 (starlink, kuiper, oneweb, etc.)"),
):
    """
    獲取可見衛星列表
    """
    await initialize_satellites()

    try:
        now = ts.now()

        # Create observer location
        if global_view:
            # Global view: return satellites from multiple perspectives
            observer_locations = [
                wgs84.latlon(0.0, 0.0, 0.0),  # Equator, Prime Meridian
                wgs84.latlon(45.0, 0.0, 0.0),  # Mid-latitude
                wgs84.latlon(-45.0, 90.0, 0.0),  # Southern hemisphere
            ]
        else:
            observer_locations = [
                wgs84.latlon(observer_lat, observer_lon, observer_alt)
            ]

        # Filter satellites by constellation if specified
        filtered_satellites = satellites
        if constellation:
            constellation_lower = constellation.lower()
            if constellation_lower == "starlink":
                filtered_satellites = starlink_sats
            elif constellation_lower == "kuiper":
                filtered_satellites = kuiper_sats
            elif constellation_lower == "oneweb":
                filtered_satellites = oneweb_sats
            elif constellation_lower == "globalstar":
                filtered_satellites = globalstar_sats
            elif constellation_lower == "iridium":
                filtered_satellites = iridium_sats
            else:
                # If constellation not recognized, filter by name
                filtered_satellites = [sat for sat in satellites if constellation_lower in sat.name.lower()]

        visible_satellites = []

        for observer in observer_locations:
            # Use filtered satellites and limit processing
            satellites_to_process = filtered_satellites[:min(len(filtered_satellites), count * 3)]  # Process more to ensure we get enough visible ones
            for satellite in satellites_to_process:
                try:
                    # Calculate satellite position relative to observer
                    difference = satellite - observer
                    topocentric = difference.at(now)
                    alt, az, distance = topocentric.altaz()

                    if alt.degrees >= min_elevation_deg:
                        # Calculate additional orbital information
                        geocentric = satellite.at(now)
                        subpoint = wgs84.subpoint(geocentric)

                        satellite_info = {
                            "name": satellite.name,
                            "norad_id": (
                                str(satellite.model.satnum)
                                if hasattr(satellite.model, "satnum")
                                else "unknown"
                            ),
                            "elevation_deg": round(alt.degrees, 2),
                            "azimuth_deg": round(az.degrees, 2),
                            "distance_km": round(distance.km, 2),
                            "orbit_altitude_km": round(subpoint.elevation.km, 2),
                            "velocity_km_s": 7.5,  # Approximate orbital velocity for LEO
                            "latitude": round(subpoint.latitude.degrees, 4),
                            "longitude": round(subpoint.longitude.degrees, 4),
                        }

                        visible_satellites.append(satellite_info)

                except Exception as e:
                    print(f"Error processing satellite {satellite.name}: {e}")
                    continue

        # Remove duplicates and sort by elevation
        unique_satellites = {}
        for sat in visible_satellites:
            if (
                sat["name"] not in unique_satellites
                or sat["elevation_deg"]
                > unique_satellites[sat["name"]]["elevation_deg"]
            ):
                unique_satellites[sat["name"]] = sat

        result_satellites = list(unique_satellites.values())
        result_satellites.sort(key=lambda x: x["elevation_deg"], reverse=True)

        return {
            "satellites": result_satellites[:count],
            "processed": len(filtered_satellites),
            "visible": len(result_satellites),
            "constellation_filter": constellation,
            "observer": {
                "latitude": observer_lat,
                "longitude": observer_lon,
                "altitude_m": observer_alt,
            },
            "timestamp": now.utc_iso(),
            "global_view": global_view,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error calculating visible satellites: {e}"
        )


@router.get("/stats", tags=["Satellites"])
async def get_satellite_stats():
    """
    獲取衛星統計資訊
    """
    await initialize_satellites()

    return {
        "total_satellites": len(satellites),
        "constellations": {
            "starlink": len(starlink_sats),
            "kuiper": len(kuiper_sats),
            "oneweb": len(oneweb_sats),
            "globalstar": len(globalstar_sats),
            "iridium": len(iridium_sats),
        },
        "skyfield_loaded": SKYFIELD_LOADED,
        "timestamp": datetime.utcnow().isoformat(),
    }
