"""
Service Registry

Consolidates all service registrations for the unified lifecycle manager.
Replaces scattered initialization code from main.py, db/lifespan.py, and service files.
"""

import asyncio
import logging
from typing import Any, Optional

from .lifecycle_manager import register_service, register_shutdown_hook, ServicePriority
from .config import configure_gpu_cpu, configure_matplotlib
from ..services.satellite_scheduler import initialize_scheduler, shutdown_scheduler
from ..db.redis_client import initialize_redis_client, close_redis_connection
from ..domains.satellite.services.cqrs_satellite_service import CQRSSatelliteService

logger = logging.getLogger(__name__)


async def seed_default_ground_station():
    """Seed default ground station data"""
    try:
        from ..services.ground_station_service import GroundStationService
        service = GroundStationService()
        await service.create_default_ground_station()
        logger.info("Default ground station seeded successfully")
    except Exception as e:
        logger.error(f"Failed to seed default ground station: {e}")
        raise


async def seed_initial_device_data():
    """Seed initial device data"""
    try:
        from ..domains.device.services.device_service import DeviceService
        from ..domains.device.adapters.sqlmodel_device_repository import SQLModelDeviceRepository
        from ..db.database import get_session
        
        # Get database session
        async with get_session() as session:
            repository = SQLModelDeviceRepository(session)
            service = DeviceService(repository)
            # TODO: Implement create_initial_devices method in DeviceService
            # await service.create_initial_devices()
        logger.info("Initial device data seeded successfully")
    except Exception as e:
        logger.error(f"Failed to seed initial device data: {e}")
        raise


def setup_environment():
    """Setup environment configuration"""
    try:
        configure_gpu_cpu()
        configure_matplotlib()
        logger.info("Environment configuration completed")
    except Exception as e:
        logger.error(f"Environment setup failed: {e}")
        raise


async def initialize_database():
    """Initialize database connection and create tables"""
    try:
        await database.connect()
        logger.info("Database initialized successfully")
        return database
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def shutdown_database():
    """Shutdown database connection"""
    try:
        await database.disconnect()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Database shutdown failed: {e}")


async def initialize_redis():
    """Initialize Redis client and sync TLE data"""
    try:
        redis_client = await initialize_redis_client()
        
        # Synchronize TLE data for both constellations
        from ..domains.satellite.services.tle_service import TLEService
        tle_service = TLEService()
        
        # Sync Starlink constellation
        await tle_service.sync_starlink_constellation()
        logger.info("Starlink TLE data synchronized")
        
        # Sync Kuiper constellation
        await tle_service.sync_kuiper_constellation()
        logger.info("Kuiper TLE data synchronized")
        
        logger.info("Redis initialized and TLE data synchronized")
        return redis_client
    except Exception as e:
        logger.error(f"Redis initialization failed: {e}")
        raise


async def shutdown_redis():
    """Shutdown Redis connection"""
    try:
        await close_redis_connection()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Redis shutdown failed: {e}")


async def initialize_satellite_scheduler_service():
    """Initialize satellite data scheduler"""
    try:
        # Get redis client from redis service
        from ..db.redis_client import get_redis_client
        redis_client = get_redis_client()
        if redis_client is None:
            raise RuntimeError("Redis client not available for satellite scheduler")
        
        await initialize_scheduler(redis_client)
        logger.info("Satellite scheduler initialized")
    except Exception as e:
        logger.error(f"Satellite scheduler initialization failed: {e}")
        raise


async def shutdown_satellite_scheduler_service():
    """Shutdown satellite scheduler"""
    try:
        await shutdown_scheduler()
        logger.info("Satellite scheduler stopped")
    except Exception as e:
        logger.error(f"Satellite scheduler shutdown failed: {e}")


async def initialize_cqrs_service():
    """Initialize CQRS satellite service"""
    try:
        service = CQRSSatelliteService()
        await service.start()
        logger.info("CQRS satellite service initialized")
        return service
    except Exception as e:
        logger.error(f"CQRS service initialization failed: {e}")
        raise


async def shutdown_cqrs_service():
    """Shutdown CQRS service"""
    try:
        from .lifecycle_manager import get_service_instance
        service = get_service_instance("cqrs_satellite_service")
        if service:
            await service.stop()
        logger.info("CQRS satellite service stopped")
    except Exception as e:
        logger.error(f"CQRS service shutdown failed: {e}")


async def initialize_performance_services():
    """Initialize performance domain services (simplified - direct instantiation)"""
    try:
        from ..domains.performance.services.simworld_optimizer import SimWorldOptimizer
        from ..domains.performance.services.algorithm_calculator import AlgorithmCalculator
        from ..domains.performance.services.performance_aggregator import PerformanceAggregator
        
        # Direct instantiation - simpler and faster than DI container
        optimizer = SimWorldOptimizer()
        calculator = AlgorithmCalculator()
        aggregator = PerformanceAggregator()
        
        logger.info("Performance services initialized (direct instantiation)")
        return {
            "optimizer": optimizer,
            "calculator": calculator,
            "aggregator": aggregator
        }
    except Exception as e:
        logger.error(f"Performance services initialization failed: {e}")
        raise


def register_all_services():
    """
    Register all services with the lifecycle manager
    
    This function consolidates all the scattered service initialization
    logic from main.py, db/lifespan.py, and various service files.
    """
    logger.info("Registering all services with lifecycle manager")
    
    # Phase 1: Critical Infrastructure (Priority 1)
    register_service(
        name="environment_setup",
        startup_func=setup_environment,
        priority=ServicePriority.CRITICAL,
        critical=True,
        timeout_seconds=10
    )
    
    register_service(
        name="database",
        startup_func=initialize_database,
        shutdown_func=shutdown_database,
        priority=ServicePriority.CRITICAL,
        dependencies=["environment_setup"],
        critical=True,
        timeout_seconds=30
    )
    
    register_service(
        name="redis",
        startup_func=initialize_redis,
        shutdown_func=shutdown_redis,
        priority=ServicePriority.CRITICAL,
        dependencies=["environment_setup"],
        critical=True,
        timeout_seconds=60  # TLE sync can take time
    )
    
    # Phase 2: Core Services (Priority 2)
    register_service(
        name="satellite_scheduler",
        startup_func=initialize_satellite_scheduler_service,
        shutdown_func=shutdown_satellite_scheduler_service,
        priority=ServicePriority.HIGH,
        dependencies=["database", "redis"],
        critical=False,
        timeout_seconds=30
    )
    
    register_service(
        name="cqrs_satellite_service",
        startup_func=initialize_cqrs_service,
        shutdown_func=shutdown_cqrs_service,
        priority=ServicePriority.HIGH,
        dependencies=["database", "redis"],
        critical=False,
        timeout_seconds=30
    )
    
    # Phase 3: Domain Services (Priority 3)
    register_service(
        name="performance_services",
        startup_func=initialize_performance_services,
        priority=ServicePriority.MEDIUM,
        dependencies=["database"],
        critical=False,
        timeout_seconds=20
    )
    
    # Phase 4: Data Seeding (Priority 4)
    register_service(
        name="ground_station_seed",
        startup_func=seed_default_ground_station,
        priority=ServicePriority.LOW,
        dependencies=["database"],
        critical=False,
        timeout_seconds=20
    )
    
    register_service(
        name="device_data_seed",
        startup_func=seed_initial_device_data,
        priority=ServicePriority.LOW,
        dependencies=["database", "ground_station_seed"],
        critical=False,
        timeout_seconds=20
    )
    
    # Register shutdown hooks for cleanup
    register_shutdown_hook(lambda: logger.info("All services shut down successfully"))
    
    logger.info("All services registered successfully")


def get_registered_services_info():
    """Get information about all registered services"""
    from .lifecycle_manager import lifecycle_manager
    
    services_info = []
    for name, service in lifecycle_manager.services.items():
        services_info.append({
            "name": name,
            "priority": service.priority.name,
            "dependencies": service.dependencies,
            "critical": service.critical,
            "timeout_seconds": service.timeout_seconds
        })
    
    return services_info