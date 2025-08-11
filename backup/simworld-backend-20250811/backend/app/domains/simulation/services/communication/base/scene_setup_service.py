"""
Scene Setup Service

Handles Sionna scene initialization, device placement, and common scene operations.
Eliminates code duplication across different simulation types.
"""

import logging
from typing import List, Tuple, Any, Dict
from sionna.rt import (
    load_scene,
    Transmitter as SionnaTransmitter,
    Receiver as SionnaReceiver,
    PlanarArray,
)

logger = logging.getLogger(__name__)


class SceneSetupService:
    """
    Manages Sionna scene setup and device placement
    """
    
    @staticmethod
    def load_and_configure_scene(
        scene_xml_path: str,
        array_config: Dict[str, Any]
    ) -> Any:
        """
        Load scene and configure antenna arrays
        
        Args:
            scene_xml_path: Path to scene XML file
            array_config: Antenna array configuration
            
        Returns:
            Configured Sionna scene
        """
        logger.info(f"Loading scene from {scene_xml_path}")
        scene = load_scene(scene_xml_path)
        
        # Configure antenna arrays
        scene.tx_array = PlanarArray(**array_config)
        scene.rx_array = PlanarArray(**array_config)
        
        return scene
    
    @staticmethod
    def clear_existing_devices(scene: Any) -> None:
        """
        Remove all existing transmitters and receivers from scene
        
        Args:
            scene: Sionna scene object
        """
        # Remove existing transmitters
        for name in list(scene.transmitters.keys()):
            scene.remove(name)
            
        # Remove existing receivers  
        for name in list(scene.receivers.keys()):
            scene.remove(name)
            
        # Verify cleanup
        if len(scene.transmitters) > 0 or len(scene.receivers) > 0:
            logger.warning("Could not completely clear existing devices from scene")
    
    @staticmethod
    def add_transmitters(
        scene: Any,
        tx_list: List[Tuple[str, List[float], List[float], str, float]]
    ) -> None:
        """
        Add transmitters to scene
        
        Args:
            scene: Sionna scene object
            tx_list: List of (name, position, orientation, role, power_dbm) tuples
        """
        logger.info(f"Adding {len(tx_list)} transmitters to scene")
        
        for name, pos, ori, role, power_dbm in tx_list:
            tx = SionnaTransmitter(
                name=name, 
                position=pos, 
                orientation=ori, 
                power_dbm=power_dbm
            )
            tx.role = role
            scene.add(tx)
            
            logger.debug(f"Added {role} transmitter: {name} at {pos} with {power_dbm} dBm")
    
    @staticmethod
    def add_receiver(
        scene: Any,
        rx_name: str,
        rx_position: List[float]
    ) -> None:
        """
        Add receiver to scene
        
        Args:
            scene: Sionna scene object
            rx_name: Receiver name
            rx_position: Receiver position [x, y, z]
        """
        logger.info(f"Adding receiver '{rx_name}' at position {rx_position}")
        scene.add(SionnaReceiver(name=rx_name, position=rx_position))
    
    @staticmethod
    def set_transmitter_velocities(
        scene: Any,
        velocity: List[float] = [30, 0, 0]
    ) -> None:
        """
        Set velocity for all transmitters in scene
        
        Args:
            scene: Sionna scene object
            velocity: Velocity vector [vx, vy, vz] in m/s
        """
        for name in scene.transmitters:
            scene.get(name).velocity = velocity
            
        logger.info(f"Set velocity {velocity} for {len(scene.transmitters)} transmitters")
    
    @staticmethod
    def get_transmitter_indices_by_role(scene: Any) -> Tuple[List[int], List[int]]:
        """
        Get transmitter indices grouped by role
        
        Args:
            scene: Sionna scene object
            
        Returns:
            Tuple of (desired_indices, jammer_indices)
        """
        tx_names = list(scene.transmitters.keys())
        all_txs = [scene.get(n) for n in tx_names]
        
        idx_des = [
            i for i, tx in enumerate(all_txs) 
            if getattr(tx, "role", None) == "desired"
        ]
        idx_jam = [
            i for i, tx in enumerate(all_txs) 
            if getattr(tx, "role", None) == "jammer"
        ]
        
        logger.info(f"Found {len(idx_des)} desired and {len(idx_jam)} jammer transmitters")
        return idx_des, idx_jam