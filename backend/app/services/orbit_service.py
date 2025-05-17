# backend/app/services/orbit_service.py
import logging
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

from skyfield.api import load, Topos, EarthSatellite, wgs84
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from redis.asyncio import Redis as AsyncRedis  # Import async Redis
from skyfield.framelib import itrs  # Import ITRS frame

# Corrected import paths
from app.db.ground_station import GroundStation as DBGroundStation
from app.db.satellite_tle import SatelliteTLE as DBSatelliteTLE
from app.schemas.ground_station import GroundStation as PydanticGroundStation
from app.services.tle_service import TLE_DATA_CACHE_PREFIX, parse_tle_line_for_epoch

logger = logging.getLogger(__name__)

try:
    ts = load.timescale()
    # eph = load('de421.bsp') # Optional, not strictly needed for this specific calculation
except Exception as e:
    logger.error(f"Failed to load Skyfield timescale: {e}")
    ts = None


def _create_skyfield_satellite(tle_data: Dict[str, Any]) -> Optional[EarthSatellite]:
    """Helper to create an EarthSatellite object from TLE data dictionary."""
    if not ts:
        logger.error("Skyfield timescale not loaded. Cannot create satellite object.")
        return None
    try:
        if not all(k in tle_data for k in ["name", "line1", "line2"]):
            logger.warning(
                f"TLE data for NORAD {tle_data.get('norad_id')} missing fields. Skipping."
            )
            return None
        return EarthSatellite(
            tle_data["line1"], tle_data["line2"], tle_data["name"], ts
        )
    except ValueError as e:
        logger.warning(
            f"Skyfield ValueError for NORAD {tle_data.get('norad_id')}, Name: {tle_data.get('name')}: {e}"
        )
        return None
    except Exception as e:
        logger.error(
            f"Unexpected error creating Skyfield satellite for NORAD {tle_data.get('norad_id')}: {e}"
        )
        return None


async def get_all_tles_from_redis(redis: AsyncRedis) -> List[Dict[str, Any]]:
    """Fetches all TLEs stored in Redis (keys matching 'tle:*')."""
    tles = []
    try:
        # Ensure redis client is not None before proceeding
        if redis is None:
            logger.warning("Redis client is None in get_all_tles_from_redis.")
            return []

        keys = await redis.keys("tle:*")  # Gets all keys matching the pattern
        if not keys:
            logger.info("No TLE keys found in Redis with pattern 'tle:*'.")
            return []

        # Fetch all values in a single MGET command if possible, or iterate
        # For simplicity, iterating here. For very large numbers, MGET is better.
        for key_bytes in keys:
            key = key_bytes.decode()  # Convert bytes to string
            tle_json = await redis.get(key)
            if tle_json:
                try:
                    tle_data = json.loads(tle_json.decode())
                    tles.append(tle_data)
                except json.JSONDecodeError:
                    logger.warning(
                        f"Could not decode JSON for TLE data from Redis key: {key}"
                    )
        logger.info(f"Fetched {len(tles)} TLEs from Redis.")
    except Exception as e:
        logger.error(f"Error fetching TLEs from Redis: {e}")
    return tles


async def get_all_tles_from_db(db: AsyncSession) -> List[Dict[str, Any]]:
    """Fetches all TLEs from the database."""
    tles = []
    try:
        if db is None:
            logger.warning("DB session is None in get_all_tles_from_db.")
            return []

        result = await db.execute(select(DBSatelliteTLE))
        db_tles = result.scalars().all()
        for tle_db_obj in db_tles:
            tles.append(
                {
                    "norad_id": tle_db_obj.norad_id,
                    "name": tle_db_obj.name,
                    "line1": tle_db_obj.line1,
                    "line2": tle_db_obj.line2,
                    "epoch_year": tle_db_obj.epoch_year,
                    "epoch_day": tle_db_obj.epoch_day,
                    "source_updated_at": (
                        tle_db_obj.source_updated_at.isoformat()
                        if tle_db_obj.source_updated_at
                        else None
                    ),
                    "last_fetched_at": (
                        tle_db_obj.last_fetched_at.isoformat()
                        if tle_db_obj.last_fetched_at
                        else None
                    ),
                }
            )
        logger.info(f"Fetched {len(tles)} TLEs from Database.")
    except Exception as e:
        logger.error(f"Error fetching TLEs from Database: {e}")
    return tles


async def get_visible_satellites(
    ground_station: PydanticGroundStation,
    calculation_time_utc: Optional[datetime] = None,
    top_n: int = 10,
    min_elevation_deg: float = 5.0,
    redis_client: Optional[AsyncRedis] = None,
    db_session: Optional[AsyncSession] = None,
) -> List[Dict[str, Any]]:
    """
    Calculates and returns the top N visible satellites from a given ground station.
    Tries to fetch TLEs from Redis first, then falls back to DB.
    """
    if not ts:
        logger.error("Skyfield timescale not loaded. Visibility calculation aborted.")
        return []

    all_tle_data = []
    if redis_client:
        all_tle_data = await get_all_tles_from_redis(redis_client)

    if not all_tle_data and db_session:
        logger.info(
            "No TLEs from Redis or Redis client not provided. Falling back to DB."
        )
        all_tle_data = await get_all_tles_from_db(db_session)

    if not all_tle_data:
        logger.warning("No TLE data available. Cannot calculate visibility.")
        return []

    gs_topos = wgs84.latlon(
        ground_station.latitude_deg,
        ground_station.longitude_deg,
        elevation_m=ground_station.altitude_m,
    )

    if calculation_time_utc:
        if calculation_time_utc.tzinfo is None:
            calculation_time_utc = calculation_time_utc.replace(tzinfo=timezone.utc)
        sky_time = ts.from_datetime(calculation_time_utc)
    else:
        sky_time = ts.now()

    visible_satellites = []
    for tle_data in all_tle_data:
        satellite = _create_skyfield_satellite(tle_data)
        if not satellite:
            continue

        difference = satellite - gs_topos
        topocentric = difference.at(sky_time)
        alt, az, distance = topocentric.altaz()

        if alt.degrees > min_elevation_deg:
            ecef_x_km, ecef_y_km, ecef_z_km = None, None, None
            try:
                # Calculate ECEF (ITRS) coordinates
                geocentric_position = satellite.at(sky_time)
                # The .frame_xyz(itrs) converts to ITRS frame, which is ECEF.
                # Result is a tuple of Distance objects (x, y, z)
                itrf_vector = geocentric_position.frame_xyz(itrs).km
                ecef_x_km = itrf_vector[0]
                ecef_y_km = itrf_vector[1]
                ecef_z_km = itrf_vector[2]
            except Exception as e:
                logger.error(
                    f"Error calculating ECEF for {tle_data.get('name', 'UnknownSatellite')}: {e}"
                )

            sat_info = {
                "norad_id": tle_data.get("norad_id"),
                "name": tle_data.get("name"),
                "elevation_deg": round(alt.degrees, 2),
                "azimuth_deg": round(az.degrees, 2),
                "distance_km": round(distance.km, 2),
                "line1": tle_data.get("line1"),
                "line2": tle_data.get("line2"),
                "ecef_x_km": ecef_x_km,
                "ecef_y_km": ecef_y_km,
                "ecef_z_km": ecef_z_km,
            }
            # Use json.dumps for logging to see None as null if that's the case
            logger.info(
                f"Calculated satellite_info for {sat_info.get('name', 'UnknownSatellite')}: {json.dumps(sat_info)}"
            )
            visible_satellites.append(sat_info)

    visible_satellites.sort(key=lambda s: s["elevation_deg"], reverse=True)
    logger.info(
        f"Found {len(visible_satellites)} sats above {min_elevation_deg} deg. Returning top {top_n}."
    )
    return visible_satellites[:top_n]
