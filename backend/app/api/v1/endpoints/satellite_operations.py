import logging
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
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

# Import default observer config
from app.core.config import (
    DEFAULT_OBSERVER_LAT,
    DEFAULT_OBSERVER_LON,
    DEFAULT_OBSERVER_ALT,
)

logger = logging.getLogger(__name__)
router = APIRouter()


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
    "/visible_satellites",  # New endpoint path
    response_model=SharedVisibleSatellitesResponse,
    summary="Get Visible Satellites for Default Observer",
    description="Calculates visible satellites for a pre-configured default observer location. Satellites are sorted by elevation.",
    tags=["Satellite Operations"],
)
async def get_visible_satellites_for_default_observer_api(
    request: Request,  # Added request for logging client IP
    count: int = Query(
        10,  # Default to 10, as requested
        alias="count",  # API parameter will be 'count'
        gt=0,
        description="Number of top satellites by elevation to return.",
    ),
    min_elevation_deg: float = Query(
        0.0,  # Default to 0.0 degrees (horizon)
        ge=0,
        le=90,
        description="Minimum elevation in degrees for a satellite to be considered visible.",
    ),
    calculation_time_utc: Optional[datetime] = Query(
        None,
        description="Time for visibility calculation (UTC ISO format). Defaults to now.",
    ),
    db: AsyncSession = Depends(get_db_session),
    redis: Optional[AsyncRedis] = Depends(get_redis_client),
):
    # Use the default observer location from config
    # We create a PydanticGroundStation object on the fly for the service function
    default_observer = PydanticGroundStation(
        id=-1,  # Dummy ID, as it's required by the schema but not used for DB ops here
        station_identifier="default_observer_config",  # Correct field name
        name="Default Observer (from config)",  # Correct field name
        latitude_deg=DEFAULT_OBSERVER_LAT,  # Correct field name
        longitude_deg=DEFAULT_OBSERVER_LON,  # Correct field name
        altitude_m=DEFAULT_OBSERVER_ALT,  # Correct field name
        description="Observer location loaded from backend configuration.",  # Optional, but good to have
        # created_at and updated_at are not part of GroundStationInDBBase schema directly
        # Pydantic model_validate (used by service) will handle ORM fields if needed
        # but we are creating a Pydantic object, not a DB object here.
        # For PydanticGroundStation which is GroundStationInDBBase, these are not explicit fields.
    )

    client_ip = request.client.host if request.client else "unknown"
    logger.info(
        f"Request for visible satellites for default observer received from {client_ip}. "
        f"Params: count={count}, min_elevation_deg={min_elevation_deg}, time_utc={calculation_time_utc}"
    )

    try:
        # Call the existing service function, passing the dynamically created observer
        # Note: The service `get_visible_satellites` expects `top_n`, so we map `count` to `top_n`.
        visible_sats_data = await get_visible_satellites(
            ground_station=default_observer,  # Pass the PydanticGroundStation object
            calculation_time_utc=calculation_time_utc,
            top_n=count,  # Map API's 'count' to service's 'top_n'
            min_elevation_deg=min_elevation_deg,
            redis_client=redis,
            db_session=db,
        )

        response_calc_time = (
            calculation_time_utc if calculation_time_utc else datetime.now(timezone.utc)
        )

        satellites_info_list: List[SharedVisibleSatelliteInfo] = []
        for sat_data in visible_sats_data:
            try:
                # Ensure all required fields for SharedVisibleSatelliteInfo are present in sat_data
                # If sat_data is a dict from a Pydantic model, it should be fine.
                # If it's raw data, ensure it matches the schema.
                satellites_info_list.append(SharedVisibleSatelliteInfo(**sat_data))
            except Exception as e:
                logger.error(
                    f"Error validating satellite data for response model: {sat_data.get('name')}, error: {e}"
                )
                continue

        logger.info(
            f"Returning {len(satellites_info_list)} visible satellites for default observer."
        )
        return SharedVisibleSatellitesResponse(
            ground_station_identifier=default_observer.station_identifier,  # Use dummy ID
            calculation_time_utc=response_calc_time,
            satellites=satellites_info_list,
            count=len(satellites_info_list),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error calculating visible satellites for default observer: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Error calculating satellite visibility: {str(e)}"
        )
