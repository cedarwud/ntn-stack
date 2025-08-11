"""
Channel Calculator

Handles channel response analysis using Sionna PathSolver.
Generates 3D visualization of H_des, H_jam, and H_all channel responses.
"""

import logging
import numpy as np
import matplotlib.pyplot as plt
from typing import Any, List, Tuple
from sionna.rt import PathSolver, subcarrier_frequencies

from ..base import SceneSetupService, SionnaConfigService

logger = logging.getLogger(__name__)


class ChannelCalculator:
    """
    Specialized calculator for channel response analysis
    """
    
    def __init__(self):
        self.config_service = SionnaConfigService()
        self.scene_service = SceneSetupService()
    
    def calculate_channel_response(
        self,
        scene: Any,
        tx_list: List[Tuple[str, List[float], List[float], str, float]],
        rx_config: Tuple[str, List[float]]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate channel response using Sionna
        
        Args:
            scene: Configured Sionna scene
            tx_list: List of transmitter configurations
            rx_config: Receiver configuration
            
        Returns:
            Tuple of (H_des, H_jam, H_all) channel responses
        """
        logger.info("Starting channel response calculation")
        
        # Get configuration
        ofdm_config = self.config_service.get_ofdm_config()
        pathsolver_config = self.config_service.get_pathsolver_config("channel")
        
        n_subcarriers = ofdm_config["N_SUBCARRIERS"]
        subcarrier_spacing = ofdm_config["SUBCARRIER_SPACING"]
        num_ofdm_symbols = ofdm_config["num_ofdm_symbols"]
        
        # Setup scene devices
        self.scene_service.clear_existing_devices(scene)
        self.scene_service.add_transmitters(scene, tx_list)
        self.scene_service.add_receiver(scene, rx_config[0], rx_config[1])
        
        # Set transmitter velocities for channel analysis
        self.scene_service.set_transmitter_velocities(scene, [30, 0, 0])
        
        # Get transmitter indices by role
        idx_des, idx_jam = self.scene_service.get_transmitter_indices_by_role(scene)
        
        if not idx_des:
            raise ValueError("No desired transmitters found for channel response analysis")
        
        # Calculate paths
        logger.info("Computing propagation paths for channel analysis")
        solver = PathSolver()
        paths = solver(scene, **pathsolver_config)
        
        # Generate frequency grid
        freqs = subcarrier_frequencies(n_subcarriers, subcarrier_spacing)
        
        # Calculate CFR
        ofdm_symbol_duration = 1 / subcarrier_spacing
        H_unit = paths.cfr(
            frequencies=freqs,
            sampling_frequency=1 / ofdm_symbol_duration,
            num_time_steps=num_ofdm_symbols,
            normalize_delays=True,
            normalize=False,
            out_type="numpy",
        ).squeeze()  # shape: (num_tx, T, F)
        
        # Calculate H_all, H_des, H_jam
        logger.info("Computing H_all, H_des, H_jam")
        H_all = H_unit.sum(axis=0)
        
        # Safe computation with zero initialization
        H_des = np.zeros_like(H_all)
        if idx_des:
            H_des = H_unit[idx_des].sum(axis=0)
        
        H_jam = np.zeros_like(H_all)
        if idx_jam:
            H_jam = H_unit[idx_jam].sum(axis=0)
        
        logger.info("Channel response calculation completed")
        return H_des, H_jam, H_all
    
    def create_channel_response_plots(
        self,
        H_des: np.ndarray,
        H_jam: np.ndarray,
        H_all: np.ndarray,
        output_path: str
    ) -> bool:
        """
        Create 3D channel response plots
        
        Args:
            H_des: Desired signal channel response
            H_jam: Jammer signal channel response  
            H_all: Combined channel response
            output_path: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Creating channel response plots")
            
            # Prepare plotting grid
            T, F = H_des.shape
            t_axis = np.arange(T)
            f_axis = np.arange(F)
            T_mesh, F_mesh = np.meshgrid(t_axis, f_axis, indexing="ij")
            
            # Create figure with 3 subplots
            fig = plt.figure(figsize=(18, 5))
            
            # Subplot 1: H_des
            ax1 = fig.add_subplot(131, projection="3d")
            ax1.plot_surface(
                F_mesh, T_mesh, np.abs(H_des), cmap="viridis", edgecolor="none"
            )
            ax1.set_xlabel("子載波")
            ax1.set_ylabel("OFDM 符號")
            ax1.set_title("‖H_des‖")
            
            # Subplot 2: H_jam
            ax2 = fig.add_subplot(132, projection="3d")
            ax2.plot_surface(
                F_mesh, T_mesh, np.abs(H_jam), cmap="viridis", edgecolor="none"
            )
            ax2.set_xlabel("子載波")
            ax2.set_ylabel("OFDM 符號")
            ax2.set_title("‖H_jam‖")
            
            # Subplot 3: H_all
            ax3 = fig.add_subplot(133, projection="3d")
            ax3.plot_surface(
                F_mesh, T_mesh, np.abs(H_all), cmap="viridis", edgecolor="none"
            )
            ax3.set_xlabel("子載波")
            ax3.set_ylabel("OFDM 符號")
            ax3.set_title("‖H_all‖")
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close(fig)
            
            logger.info(f"Channel response plots saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating channel response plots: {e}")
            plt.close("all")
            return False