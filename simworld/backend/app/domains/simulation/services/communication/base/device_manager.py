"""
Device Manager Service

Handles database operations for retrieving simulation devices.
Provides a unified interface for accessing transmitters, receivers, and jammers.
"""

import logging
from typing import List, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.device.models.device_model import Device, DeviceRole
from app.domains.device.services.device_service import DeviceService
from app.domains.device.adapters.sqlmodel_device_repository import SQLModelDeviceRepository

logger = logging.getLogger(__name__)


class DeviceManager:
    """
    Manages device data retrieval and configuration for Sionna simulations
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize device manager with database session"""
        self.session = session
        self.device_repository = SQLModelDeviceRepository(session)
        self.device_service = DeviceService(self.device_repository)
    
    async def load_simulation_devices(self) -> Tuple[List[Device], List[Device], List[Device]]:
        """
        Load all active devices for simulation
        
        Returns:
            Tuple of (desired_transmitters, jammers, receivers)
        """
        logger.info("Loading simulation devices from database...")
        
        # Get active desired transmitters
        active_desired = await self.device_service.get_devices(
            skip=0, limit=100, role=DeviceRole.DESIRED.value, active_only=True
        )
        
        # Get active jammers
        active_jammers = await self.device_service.get_devices(
            skip=0, limit=100, role=DeviceRole.JAMMER.value, active_only=True
        )
        
        # Get active receivers
        active_receivers = await self.device_service.get_devices(
            skip=0, limit=100, role=DeviceRole.RECEIVER.value, active_only=True
        )
        
        logger.info(f"Loaded devices - Desired: {len(active_desired)}, "
                   f"Jammers: {len(active_jammers)}, Receivers: {len(active_receivers)}")
        
        return active_desired, active_jammers, active_receivers
    
    def build_transmitter_list(self, desired: List[Device], jammers: List[Device]) -> List[Tuple[str, List[float], List[float], str, float]]:
        """
        Build transmitter list for Sionna simulation
        
        Returns:
            List of (name, position, orientation, role, power_dbm) tuples
        """
        tx_list = []
        
        # Add desired transmitters
        for tx in desired:
            tx_list.append((
                tx.name,
                [tx.position_x, tx.position_y, tx.position_z],
                [tx.orientation_x, tx.orientation_y, tx.orientation_z],
                "desired",
                tx.power_dbm
            ))
            
        # Add jammers
        for jammer in jammers:
            tx_list.append((
                jammer.name,
                [jammer.position_x, jammer.position_y, jammer.position_z],
                [jammer.orientation_x, jammer.orientation_y, jammer.orientation_z],
                "jammer",
                jammer.power_dbm
            ))
            
        return tx_list
    
    def get_receiver_config(self, receivers: List[Device]) -> Tuple[str, List[float]]:
        """
        Get receiver configuration for simulation
        
        Returns:
            Tuple of (receiver_name, receiver_position)
        """
        if not receivers:
            logger.warning("No active receivers found, using default position")
            return ("rx", [0, 0, 40])
        
        # Use first active receiver
        receiver = receivers[0]
        return (
            receiver.name,
            [receiver.position_x, receiver.position_y, receiver.position_z]
        )