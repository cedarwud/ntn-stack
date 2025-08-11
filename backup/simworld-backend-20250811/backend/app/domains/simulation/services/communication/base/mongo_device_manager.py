"""
MongoDB Device Manager Service

Handles MongoDB operations for retrieving simulation devices.
Provides a unified interface for accessing transmitters, receivers, and jammers from MongoDB.
"""

import logging
from typing import List, Tuple, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongodb_config import get_mongodb_database

logger = logging.getLogger(__name__)


class MongoDeviceManager:
    """
    Manages device data retrieval from MongoDB for Sionna simulations
    """
    
    def __init__(self):
        """Initialize MongoDB device manager"""
        self.db = None
    
    async def _get_database(self) -> AsyncIOMotorDatabase:
        """Get MongoDB database connection"""
        if self.db is None:
            self.db = await get_mongodb_database()
        return self.db
    
    async def load_simulation_devices(self) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Load all active devices for simulation from MongoDB
        
        Returns:
            Tuple of (desired_transmitters, jammers, receivers)
        """
        logger.info("Loading simulation devices from MongoDB...")
        
        try:
            db = await self._get_database()
            
            # Get active desired transmitters
            active_desired = []
            async for device in db.devices.find({"role": "desired", "active": True}):
                active_desired.append(device)
            
            # Get active jammers
            active_jammers = []
            async for device in db.devices.find({"role": "jammer", "active": True}):
                active_jammers.append(device)
            
            # Get active receivers
            active_receivers = []
            async for device in db.devices.find({"role": "receiver", "active": True}):
                active_receivers.append(device)
            
            logger.info(f"Loaded devices from MongoDB - Desired: {len(active_desired)}, "
                       f"Jammers: {len(active_jammers)}, Receivers: {len(active_receivers)}")
            
            return active_desired, active_jammers, active_receivers
            
        except Exception as e:
            logger.error(f"Failed to load devices from MongoDB: {e}")
            raise
    
    def build_transmitter_list(self, desired: List[Dict], jammers: List[Dict]) -> List[Tuple[str, List[float], List[float], str, float]]:
        """
        Build transmitter list for Sionna simulation from MongoDB devices
        
        Returns:
            List of (name, position, orientation, role, power_dbm) tuples
        """
        tx_list = []
        
        # Add desired transmitters
        for tx in desired:
            tx_list.append((
                tx["name"],
                [float(tx["position_x"]), float(tx["position_y"]), float(tx["position_z"])],
                [float(tx["orientation_x"]), float(tx["orientation_y"]), float(tx["orientation_z"])],
                "desired",
                float(tx["power_dbm"])
            ))
            
        # Add jammers
        for jammer in jammers:
            tx_list.append((
                jammer["name"],
                [float(jammer["position_x"]), float(jammer["position_y"]), float(jammer["position_z"])],
                [float(jammer["orientation_x"]), float(jammer["orientation_y"]), float(jammer["orientation_z"])],
                "jammer",
                float(jammer["power_dbm"])
            ))
            
        logger.info(f"Built transmitter list with {len(tx_list)} devices: "
                   f"{len(desired)} desired + {len(jammers)} jammers")
        return tx_list
    
    def get_receiver_config(self, receivers: List[Dict]) -> Tuple[str, List[float]]:
        """
        Get receiver configuration for simulation from MongoDB devices
        
        Returns:
            Tuple of (receiver_name, receiver_position)
        """
        if not receivers:
            logger.warning("No active receivers found, using default position")
            return ("rx", [0.0, 0.0, 40.0])
        
        # Use first active receiver
        receiver = receivers[0]
        position = [float(receiver["position_x"]), float(receiver["position_y"]), float(receiver["position_z"])]
        
        logger.info(f"Using receiver '{receiver['name']}' at position {position}")
        return (receiver["name"], position)