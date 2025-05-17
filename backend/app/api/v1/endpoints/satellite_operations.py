import logging
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from redis.asyncio import Redis as AsyncRedis

# Use actual dependencies
from app.api.dependencies import get_db_session, get_redis_client

# Import the shared Pydantic models from app.schemas
from app.schemas.satellite_operations import (
    TLESyncTriggerPayload as SharedTLESyncTriggerPayload,  # Use alias to avoid name clash if needed
    TLESyncResponse as SharedTLESyncResponse,
    VisibleSatelliteInfo as SharedVisibleSatelliteInfo,
    VisibleSatellitesResponse as SharedVisibleSatellitesResponse,
)

from app.services.tle_service import synchronize_oneweb_tles
from app.services.orbit_service import get_visible_satellites
from app.schemas.ground_station import GroundStation as PydanticGroundStation
from app.db.ground_station import GroundStation as DBGroundStation

logger = logging.getLogger(__name__)
router = APIRouter()


# --- Helper function to get ground station (now a dependency) ---
async def get_ground_station_dependency(
    station_identifier: str = Path(
        ..., description="The unique identifier of the ground station."
    ),
    db: AsyncSession = Depends(get_db_session),  # Using actual dependency
) -> DBGroundStation:
    result = await db.execute(
        select(DBGroundStation).where(
            DBGroundStation.station_identifier == station_identifier
        )
    )
    db_gs = result.scalar_one_or_none()
    if not db_gs:
        raise HTTPException(
            status_code=404,
            detail=f"Ground station with identifier '{station_identifier}' not found.",
        )
    return db_gs


# --- API Endpoints ---


@router.post(
    "/tle/synchronize",
    response_model=SharedTLESyncResponse,  # Use shared model
    summary="Trigger OneWeb TLE Synchronization",
    description="Manually triggers the synchronization of OneWeb TLE data. Stores data in DB and Redis.",
    tags=["Satellite Operations"],
)
async def trigger_tle_synchronization_api(
    payload: SharedTLESyncTriggerPayload = Body(
        default_factory=SharedTLESyncTriggerPayload
    ),  # Use shared model
    db: AsyncSession = Depends(get_db_session),
    redis: Optional[AsyncRedis] = Depends(get_redis_client),
):
    if not redis:
        raise HTTPException(
            status_code=503,
            detail="Redis client not available. TLE synchronization cannot be performed.",
        )
    try:
        logger.info(
            f"Manual TLE synchronization triggered with force_update={payload.force_update}."
        )
        await synchronize_oneweb_tles(
            db=db, redis=redis, force_update=payload.force_update
        )
        return SharedTLESyncResponse(  # Use shared model
            message="TLE synchronization process initiated successfully."
        )
    except Exception as e:
        logger.error(
            f"Error during manual TLE synchronization trigger: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get(
    "/ground_stations/{station_identifier}/visible_satellites",
    response_model=SharedVisibleSatellitesResponse,  # Use shared model
    summary="Get Visible Satellites for a Ground Station",
    description="Calculates visible satellites for a ground station.",
    tags=["Satellite Operations"],
)
async def get_visible_satellites_for_station_api(
    ground_station_db_obj: DBGroundStation = Depends(get_ground_station_dependency),
    top_n: int = Query(
        10,
        gt=0,
        description="Number of top satellites by elevation. Set a large number to get more results.",
    ),
    min_elevation_deg: float = Query(
        5.0, ge=0, le=90, description="Minimum elevation in degrees."
    ),
    calculation_time_utc: Optional[datetime] = Query(
        None,
        description="Time for visibility calculation (UTC ISO format). Defaults to now.",
    ),
    db: AsyncSession = Depends(get_db_session),
    redis: Optional[AsyncRedis] = Depends(get_redis_client),
):
    ground_station_pydantic = PydanticGroundStation.model_validate(
        ground_station_db_obj
    )

    try:
        visible_sats_data = await get_visible_satellites(
            ground_station=ground_station_pydantic,
            calculation_time_utc=calculation_time_utc,
            top_n=top_n,
            min_elevation_deg=min_elevation_deg,
            redis_client=redis,
            db_session=db,
        )

        response_calc_time = (
            calculation_time_utc if calculation_time_utc else datetime.now(timezone.utc)
        )

        # Construct the list of satellite info objects using the SHARED Pydantic model
        satellites_info_list: List[SharedVisibleSatelliteInfo] = []
        for sat_data in visible_sats_data:
            try:
                satellites_info_list.append(SharedVisibleSatelliteInfo(**sat_data))
            except Exception as e:
                logger.error(
                    f"Error validating satellite data for SHARED response model: {sat_data.get('name')}, error: {e}"
                )
                continue

        return SharedVisibleSatellitesResponse(  # Use shared model
            ground_station_identifier=ground_station_db_obj.station_identifier,
            calculation_time_utc=response_calc_time,
            satellites=satellites_info_list,  # This now uses the shared model with ECEF fields
            count=len(satellites_info_list),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error calculating visible satellites for {ground_station_db_obj.station_identifier}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Error calculating satellite visibility: {str(e)}"
        )
