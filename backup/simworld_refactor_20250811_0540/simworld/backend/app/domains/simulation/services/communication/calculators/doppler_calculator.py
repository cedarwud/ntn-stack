"""
Doppler Calculator

Handles Delay-Doppler analysis using Sionna PathSolver.
Includes 3D delay-doppler surface plotting with transmitter grouping.
"""

import logging
import numpy as np
import matplotlib.pyplot as plt
from typing import Any, List, Tuple
from sionna.rt import PathSolver, subcarrier_frequencies

from ..base import SceneSetupService, SionnaConfigService

logger = logging.getLogger(__name__)


class DopplerCalculator:
    """
    Specialized calculator for Delay-Doppler analysis
    """
    
    def __init__(self):
        self.config_service = SionnaConfigService()
        self.scene_service = SceneSetupService()
    
    def calculate_delay_doppler(
        self,
        scene: Any,
        tx_list: List[Tuple[str, List[float], List[float], str, float]],
        rx_config: Tuple[str, List[float]]
    ) -> Tuple[List[np.ndarray], List[int], List[int], np.ndarray, np.ndarray]:
        """
        Calculate delay-doppler response using Sionna
        
        Args:
            scene: Configured Sionna scene
            tx_list: List of transmitter configurations
            rx_config: Receiver configuration
            
        Returns:
            Tuple of (Hdd_list, idx_des, idx_jam, delay_bins, doppler_bins)
        """
        logger.info("Starting delay-doppler calculation")
        
        # Get configuration
        ofdm_config = self.config_service.get_ofdm_config()
        pathsolver_config = self.config_service.get_pathsolver_config("doppler")
        
        N_SUBCARRIERS = ofdm_config["N_SUBCARRIERS"]
        SUBCARRIER_SPACING = ofdm_config["SUBCARRIER_SPACING"]
        num_ofdm_symbols = ofdm_config["num_ofdm_symbols"]
        
        # Setup scene devices
        self.scene_service.clear_existing_devices(scene)
        self.scene_service.add_transmitters(scene, tx_list)
        self.scene_service.add_receiver(scene, rx_config[0], rx_config[1])
        
        # Set transmitter velocities for Doppler effect
        self.scene_service.set_transmitter_velocities(scene, [30, 0, 0])
        
        # Get transmitter indices by role
        idx_des, idx_jam = self.scene_service.get_transmitter_indices_by_role(scene)
        
        if not idx_des and not idx_jam:
            raise ValueError("No valid transmitters found in scene")
        
        # Calculate paths
        logger.info("Computing propagation paths for Doppler analysis")
        solver = PathSolver()
        paths = solver(scene, **pathsolver_config)
        
        # Generate frequency grid
        freqs = subcarrier_frequencies(N_SUBCARRIERS, SUBCARRIER_SPACING)
        
        # Calculate CFR with time dimension
        ofdm_symbol_duration = 1 / SUBCARRIER_SPACING
        H_unit = paths.cfr(
            frequencies=freqs,
            sampling_frequency=1 / ofdm_symbol_duration,
            num_time_steps=num_ofdm_symbols,
            normalize_delays=False,
            normalize=False,
            out_type="numpy",
        ).squeeze()
        
        # Apply power weighting
        all_txs = [scene.get(n) for n in scene.transmitters.keys()]
        tx_p_lin = 10 ** (np.array([tx.power_dbm for tx in all_txs]) / 10) / 1e3
        tx_p_lin = np.squeeze(tx_p_lin)
        sqrtP = np.sqrt(tx_p_lin)[:, None, None]
        H_unit = H_unit * sqrtP
        
        # Convert to delay-doppler domain
        Hdd_list = [np.abs(self._to_delay_doppler(H_unit[i])) for i in range(H_unit.shape[0])]
        
        # Generate bins for plotting
        delay_resolution = ofdm_symbol_duration / N_SUBCARRIERS
        doppler_resolution = SUBCARRIER_SPACING / num_ofdm_symbols
        
        doppler_bins = np.arange(
            -num_ofdm_symbols / 2 * doppler_resolution,
            num_ofdm_symbols / 2 * doppler_resolution,
            doppler_resolution,
        )
        delay_bins = (
            np.arange(0, N_SUBCARRIERS * delay_resolution, delay_resolution) / 1e-9
        )
        
        logger.info("Delay-doppler calculation completed")
        return Hdd_list, idx_des, idx_jam, delay_bins, doppler_bins
    
    def _to_delay_doppler(self, H_tf: np.ndarray) -> np.ndarray:
        """
        Convert time-frequency response to delay-doppler domain
        
        Args:
            H_tf: Time-frequency channel response
            
        Returns:
            Delay-doppler response
        """
        Hf = np.fft.fftshift(H_tf, axes=1)
        h_delay = np.fft.ifft(Hf, axis=1, norm="ortho")
        h_dd = np.fft.fft(h_delay, axis=0, norm="ortho")
        h_dd = np.fft.fftshift(h_dd, axes=0)
        return h_dd
    
    def create_doppler_plots(
        self,
        Hdd_list: List[np.ndarray],
        idx_des: List[int],
        idx_jam: List[int],
        delay_bins: np.ndarray,
        doppler_bins: np.ndarray,
        output_path: str
    ) -> bool:
        """
        Create delay-doppler plots with multiple surfaces
        
        Args:
            Hdd_list: List of delay-doppler responses for each transmitter
            idx_des: Indices of desired transmitters
            idx_jam: Indices of jammer transmitters
            delay_bins: Delay axis values (ns)
            doppler_bins: Doppler axis values (Hz)
            output_path: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Creating delay-doppler plots")
            
            # Create meshgrid
            x, y = np.meshgrid(delay_bins, doppler_bins)
            
            # Define plotting region (zoom into interesting area)
            offset = 20
            N_SUBCARRIERS = len(delay_bins)
            x_start = int(N_SUBCARRIERS / 2) - offset
            x_end = int(N_SUBCARRIERS / 2) + offset
            y_start = 0
            y_end = offset
            x_grid = x[x_start:x_end, y_start:y_end]
            y_grid = y[x_start:x_end, y_start:y_end]
            
            # Prepare grids and labels for plotting
            grids = []
            labels = []
            
            # Individual desired transmitters
            for k, i in enumerate(idx_des):
                Zi = Hdd_list[i][x_start:x_end, y_start:y_end]
                grids.append(Zi)
                labels.append(f"Des Tx{i}")
            
            # Individual jammers
            for k, i in enumerate(idx_jam):
                Zi = Hdd_list[i][x_start:x_end, y_start:y_end]
                grids.append(Zi)
                labels.append(f"Jam Tx{i}")
            
            # Desired all (if any)
            if idx_des:
                Z_des_all = np.sum([Hdd_list[i] for i in idx_des], axis=0)
                grids.append(Z_des_all[x_start:x_end, y_start:y_end])
                labels.append("Des ALL")
            
            # Jammer all (if any)
            if idx_jam:
                Z_jam_all = np.sum([Hdd_list[i] for i in idx_jam], axis=0)
                grids.append(Z_jam_all[x_start:x_end, y_start:y_end])
                labels.append("Jam ALL")
            
            # All transmitters combined
            Z_all = np.sum(Hdd_list, axis=0)
            grids.append(Z_all[x_start:x_end, y_start:y_end])
            labels.append("ALL Tx")
            
            # Unified Z axis
            z_min = 0
            z_max = max(g.max() for g in grids) * 1.05
            
            # Auto layout
            n_plots = len(grids)
            cols = 3
            rows = int(np.ceil(n_plots / cols))
            figsize = (cols * 4.5, rows * 4.5)
            
            # Create unified plot
            fig = plt.figure(figsize=figsize)
            fig.suptitle("Delay-Doppler Plots")
            
            for idx, (Z, label) in enumerate(zip(grids, labels), start=1):
                ax = fig.add_subplot(rows, cols, idx, projection="3d")
                ax.plot_surface(x_grid, y_grid, Z, cmap="viridis", edgecolor="none")
                ax.set_title(f"Delay–Doppler |{label}|", pad=8)
                ax.set_xlabel("Delay (ns)")
                ax.set_ylabel("Doppler (Hz)")
                ax.set_zlabel("|H|")
                ax.set_zlim(z_min, z_max)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close(fig)
            
            logger.info(f"Delay-doppler plots saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating delay-doppler plots: {e}")
            plt.close("all")
            return False