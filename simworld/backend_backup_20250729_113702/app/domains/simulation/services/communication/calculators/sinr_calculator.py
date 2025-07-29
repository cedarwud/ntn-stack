"""
SINR Calculator

Handles Signal-to-Interference-plus-Noise Ratio mapping using Sionna RadioMapSolver.
"""

import logging
import numpy as np
import matplotlib.pyplot as plt
from typing import Any, List, Tuple
from sionna.rt import RadioMapSolver

from ..base import SceneSetupService, SionnaConfigService

logger = logging.getLogger(__name__)


class SINRCalculator:
    """
    Specialized calculator for SINR mapping analysis
    """
    
    def __init__(self):
        self.config_service = SionnaConfigService()
        self.scene_service = SceneSetupService()
    
    def calculate_sinr_map(
        self,
        scene: Any,
        tx_list: List[Tuple[str, List[float], List[float], str, float]],
        rx_config: Tuple[str, List[float]],
        cell_size: float = 1.0,
        samples_per_tx: int = 10**7
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate SINR map using RadioMapSolver
        
        Returns:
            Tuple of (x_unique, y_unique, sinr_db)
        """
        logger.info("Starting SINR map calculation")
        
        # Setup scene
        self.scene_service.clear_existing_devices(scene)
        self.scene_service.add_transmitters(scene, tx_list)
        self.scene_service.add_receiver(scene, rx_config[0], rx_config[1])
        
        # Get transmitter indices
        idx_des, idx_jam = self.scene_service.get_transmitter_indices_by_role(scene)
        
        # Calculate radio map
        rm_config = self.config_service.get_radio_map_config(cell_size, samples_per_tx)
        rm_solver = RadioMapSolver()
        rm = rm_solver(scene, **rm_config)
        
        # Extract coordinates and RSS
        cc = rm.cell_centers.numpy()
        x_unique = cc[0, :, 0]
        y_unique = cc[:, 0, 1]
        
        all_txs = [scene.get(n) for n in scene.transmitters.keys()]
        rss_list = [rm.rss[i].numpy() for i in range(len(all_txs))]
        
        # Calculate SINR
        N0_map = 1e-12  # Noise power
        
        if idx_des:
            rss_des = sum(rss_list[i] for i in idx_des)
        else:
            rss_des = np.zeros((len(y_unique), len(x_unique)))
            
        if idx_jam:
            rss_jam = sum(rss_list[i] for i in idx_jam)
        else:
            rss_jam = np.zeros((len(y_unique), len(x_unique)))
        
        # SINR in dB
        sinr_db = 10 * np.log10(
            np.clip(rss_des / (rss_des + rss_jam + N0_map), 1e-12, None)
        )
        
        logger.info("SINR map calculation completed")
        return x_unique, y_unique, sinr_db