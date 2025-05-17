import logging
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from redis.asyncio import Redis as AsyncRedis

# Use actual dependencies
from app.api.dependencies import get_db_session, get_redis_client

from app.services.tle_service import synchronize_oneweb_tles
from app.services.orbit_service import get_visible_satellites
from app.schemas.ground_station import GroundStation as PydanticGroundStation
from app.db.ground_station import GroundStation as DBGroundStation

logger = logging.getLogger(__name__)
router = APIRouter()


# --- Pydantic Models for API ---
class TLESyncTriggerPayload(BaseModel):
    force_update: bool = Field(
        False, description="Set to true to force TLE synchronization even if not stale."
    )


class TLESyncResponse(BaseModel):
    message: str
    details: Optional[str] = None


class VisibleSatelliteInfo(BaseModel):
    norad_id: Optional[int]
    name: Optional[str]
    elevation_deg: float
    azimuth_deg: float
    distance_km: float
    line1: Optional[str] = None
    line2: Optional[str] = None


class VisibleSatellitesResponse(BaseModel):
    ground_station_identifier: str
    calculation_time_utc: datetime
    satellites: List[VisibleSatelliteInfo]
    count: int


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
    response_model=TLESyncResponse,
    summary="Trigger OneWeb TLE Synchronization",
    description="Manually triggers the synchronization of OneWeb TLE data. Stores data in DB and Redis.",
    tags=["Satellite Operations"],
)
async def trigger_tle_synchronization_api(
    # request: Request, # Not needed if get_redis_client handles it
    payload: TLESyncTriggerPayload = Body(default_factory=TLESyncTriggerPayload),
    db: AsyncSession = Depends(get_db_session),
    redis: Optional[AsyncRedis] = Depends(
        get_redis_client
    ),  # Redis can be None if not available
):
    if not redis:
        # This check aligns with get_redis_client possibly returning None
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
        return TLESyncResponse(
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
    response_model=VisibleSatellitesResponse,
    summary="Get Visible Satellites for a Ground Station",
    description="Calculates visible satellites for a ground station.",
    tags=["Satellite Operations"],
)
async def get_visible_satellites_for_station_api(
    # request: Request, # Not needed if get_redis_client handles it
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
    redis: Optional[AsyncRedis] = Depends(get_redis_client),  # Redis can be None
):
    # The orbit_service.get_visible_satellites is designed to accept Optional redis_client and db_session
    # It will try Redis first, then DB. If both are None or unavailable, it should handle it gracefully (e.g., log and return empty list).
    # However, for this API, we might decide that at least one must be available.
    if (
        not redis and not db
    ):  # db is always available via get_db_session unless an error occurs in the dependency itself.
        # The get_redis_client might return None if not configured/available.
        # If orbit_service strictly needs at least one, this check is good.
        # Based on orbit_service logic, it can handle None for redis_client and db_session (logs and returns empty)
        # So this specific check might be too strict if partial functionality is okay.
        # However, if TLE data is essential, then:
        logger.warning(
            "Visible satellites endpoint called but no data source (Redis or DB) seems fully available through dependencies."
        )
        # Depending on strictness, could raise 503 or let orbit_service handle it.
        # For now, let orbit_service handle it, as it has internal logging.

    ground_station_pydantic = PydanticGroundStation.model_validate(
        ground_station_db_obj
    )

    try:
        visible_sats_data = await get_visible_satellites(
            ground_station=ground_station_pydantic,
            calculation_time_utc=calculation_time_utc,
            top_n=top_n,
            min_elevation_deg=min_elevation_deg,
            redis_client=redis,  # Pass redis (can be None)
            db_session=db,  # Pass db session
        )

        response_calc_time = (
            calculation_time_utc if calculation_time_utc else datetime.now(timezone.utc)
        )

        return VisibleSatellitesResponse(
            ground_station_identifier=ground_station_db_obj.station_identifier,
            calculation_time_utc=response_calc_time,
            satellites=[VisibleSatelliteInfo(**sat) for sat in visible_sats_data],
            count=len(visible_sats_data),
        )
    except HTTPException:  # Re-raise HTTPExceptions from dependencies
        raise
    except Exception as e:
        logger.error(
            f"Error calculating visible satellites for {ground_station_db_obj.station_identifier}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Error calculating satellite visibility: {str(e)}"
        )
