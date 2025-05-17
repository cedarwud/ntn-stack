import httpx
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from redis.asyncio import Redis as AsyncRedis  # Import async Redis

# Corrected import paths based on typical project structure
# Assuming models are in app.db.models and schemas in app.schemas
from app.db.satellite_tle import SatelliteTLE
from app.schemas.satellite_tle import SatelliteTLECreate

logger = logging.getLogger(__name__)

CELESTRAK_ONEWEB_TLE_URL = (
    "https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle"
)
REDIS_LAST_TLE_SYNC_KEY = "tle_last_sync_timestamp"
TLE_SYNC_INTERVAL_HOURS = 24


def parse_tle_line_for_epoch(line1: str) -> Tuple[Optional[int], Optional[float]]:
    """Helper to parse epoch year and day from TLE line 1."""
    try:
        epoch_year_str = line1[18:20]
        year = int(epoch_year_str)
        # Standard TLE epoch year interpretation:
        # If YY is between 00 and 56, it's 20YY.
        # If YY is between 57 and 99, it's 19YY.
        if year >= 57:  # Years 1957-1999
            full_year = 1900 + year
        else:  # Years 2000-2056
            full_year = 2000 + year

        epoch_day_str = line1[20:32]
        day_fraction = float(epoch_day_str)
        return full_year, day_fraction
    except (ValueError, IndexError) as e:
        logger.warning(f"Could not parse epoch from TLE line 1: '{line1[:32]}...': {e}")
        return None, None


async def fetch_raw_tles_from_source(
    url: str = CELESTRAK_ONEWEB_TLE_URL,
) -> Optional[str]:
    """Fetches raw TLE data from the given URL."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
            return response.text
    except httpx.RequestError as e:
        logger.error(f"Error fetching TLE data from {url}: {e}")
        return None


def parse_raw_tle_data(raw_data: str) -> List[Dict[str, any]]:
    """Parses raw TLE text into a list of TLE objects."""
    tles = []
    lines = raw_data.strip().splitlines()
    i = 0
    while i + 2 < len(lines):
        name = lines[i].strip()
        line1 = lines[i + 1].strip()
        line2 = lines[i + 2].strip()

        if not (line1.startswith("1 ") and line2.startswith("2 ")):
            logger.warning(f"Skipping invalid TLE entry starting with name: {name}")
            i += 1
            continue

        try:
            norad_id_str = line1[2:7].strip()
            if not norad_id_str.isdigit():
                logger.warning(
                    f"Invalid NORAD ID '{norad_id_str}' for TLE: {name}. Skipping."
                )
                i += 3
                continue
            norad_id = int(norad_id_str)

            norad_id_l2_str = line2[2:7].strip()
            if not norad_id_l2_str.isdigit() or int(norad_id_l2_str) != norad_id:
                logger.warning(
                    f"NORAD ID mismatch or invalid in Line 2 for TLE: {name}. Skipping."
                )
                i += 3
                continue

            epoch_year, epoch_day = parse_tle_line_for_epoch(line1)

            tles.append(
                {
                    "norad_id": norad_id,
                    "name": name,
                    "line1": line1,
                    "line2": line2,
                    "epoch_year": epoch_year,
                    "epoch_day": epoch_day,
                    "source_updated_at": None,
                }
            )
        except ValueError as e:
            logger.error(
                f"Error parsing NORAD ID for TLE entry (name: {name}): {e}. Lines: {line1}, {line2}"
            )
        except Exception as e:
            logger.error(
                f"Unexpected error parsing TLE entry (name: {name}): {e}. Lines: {line1}, {line2}"
            )
        i += 3
    return tles


async def store_tles_in_db(db: AsyncSession, tles: List[Dict[str, any]]):
    """Stores or updates TLEs in the database."""
    if not tles:
        return

    tle_objects_to_upsert = []
    for tle_data in tles:
        try:
            tle_create_obj = SatelliteTLECreate(**tle_data)
            tle_objects_to_upsert.append(tle_create_obj.model_dump())
        except Exception as e:
            logger.error(
                f"Validation error for TLE NORAD {tle_data.get('norad_id')}: {e}"
            )
            continue

    if not tle_objects_to_upsert:
        logger.info("No valid TLE objects to upsert after validation.")
        return

    stmt = pg_insert(SatelliteTLE).values(tle_objects_to_upsert)

    update_values = {
        "name": stmt.excluded.name,
        "line1": stmt.excluded.line1,
        "line2": stmt.excluded.line2,
        "epoch_year": stmt.excluded.epoch_year,
        "epoch_day": stmt.excluded.epoch_day,
        "source_updated_at": stmt.excluded.source_updated_at,
        # last_fetched_at is handled by onupdate=func.now() in the model
    }

    final_stmt = stmt.on_conflict_do_update(
        index_elements=["norad_id"], set_=update_values
    )

    try:
        await db.execute(final_stmt)
        await db.commit()
        logger.info(
            f"Successfully upserted {len(tle_objects_to_upsert)} TLEs into the database."
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Database error during TLE upsert: {e}")


async def store_tles_in_redis(redis: AsyncRedis, tles: List[Dict[str, any]]):
    """Stores TLEs in Redis, keyed by NORAD ID."""
    if not tles:
        return
    try:
        import json

        async with redis.pipeline(transaction=True) as pipe:
            for tle in tles:
                if "norad_id" in tle:
                    key = f"tle:{tle['norad_id']}"
                    tle_data_for_redis = tle.copy()
                    if isinstance(
                        tle_data_for_redis.get("source_updated_at"), datetime
                    ):
                        tle_data_for_redis["source_updated_at"] = tle_data_for_redis[
                            "source_updated_at"
                        ].isoformat()

                    await pipe.set(key, json.dumps(tle_data_for_redis))
            await pipe.execute()
        logger.info(f"Successfully stored/updated {len(tles)} TLEs in Redis.")
    except Exception as e:
        logger.error(f"Redis error during TLE storage: {e}")


async def get_last_tle_sync_time(redis: AsyncRedis) -> Optional[datetime]:
    """Gets the timestamp of the last successful TLE sync from Redis."""
    try:
        timestamp_str = await redis.get(REDIS_LAST_TLE_SYNC_KEY)
        if timestamp_str:
            return datetime.fromisoformat(timestamp_str.decode())
        return None
    except Exception as e:
        logger.error(f"Redis error getting last TLE sync time: {e}")
        return None


async def set_last_tle_sync_time(redis: AsyncRedis, sync_time: datetime):
    """Sets the timestamp of the TLE sync in Redis."""
    try:
        await redis.set(REDIS_LAST_TLE_SYNC_KEY, sync_time.isoformat())
        logger.info(f"Last TLE sync time set to: {sync_time.isoformat()}")
    except Exception as e:
        logger.error(f"Redis error setting last TLE sync time: {e}")


async def synchronize_oneweb_tles(
    db: AsyncSession, redis: AsyncRedis, force_update: bool = False
):
    """
    Main function to synchronize OneWeb TLEs.
    Fetches TLEs, stores them in DB and Redis if they are stale or force_update is True.
    """
    logger.info("Attempting to synchronize OneWeb TLEs...")
    last_sync = await get_last_tle_sync_time(redis)

    needs_update = False
    if force_update:
        logger.info("Force update is True. Proceeding with TLE synchronization.")
        needs_update = True
    elif last_sync is None:
        logger.info(
            "No previous TLE sync time found. Proceeding with TLE synchronization."
        )
        needs_update = True
    else:
        if last_sync.tzinfo is None:
            last_sync = last_sync.replace(tzinfo=timezone.utc)

        current_time_utc = datetime.now(timezone.utc)
        if current_time_utc - last_sync > timedelta(hours=TLE_SYNC_INTERVAL_HOURS):
            logger.info(
                f"Last TLE sync was at {last_sync}, older than {TLE_SYNC_INTERVAL_HOURS} hours. Proceeding."
            )
            needs_update = True
        else:
            logger.info(
                f"Last TLE sync at {last_sync} is still fresh. No update needed."
            )

    if needs_update:
        raw_tles = await fetch_raw_tles_from_source()
        if raw_tles:
            parsed_tles = parse_raw_tle_data(raw_tles)
            if parsed_tles:
                logger.info(f"Fetched and parsed {len(parsed_tles)} TLEs.")
                await store_tles_in_db(db, parsed_tles)
                await store_tles_in_redis(redis, parsed_tles)
                await set_last_tle_sync_time(redis, datetime.now(timezone.utc))
                logger.info("OneWeb TLE synchronization completed successfully.")
            else:
                logger.warning("Failed to parse any TLEs from the fetched data.")
        else:
            logger.error(
                "Failed to fetch TLE data from source. Synchronization aborted."
            )
    else:
        logger.info("TLE data is up-to-date. No synchronization performed.")
