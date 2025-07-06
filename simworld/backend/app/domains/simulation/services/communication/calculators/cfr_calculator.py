"""
CFR Calculator

Handles Channel Frequency Response calculations using Sionna.
Includes QPSK+OFDM signal generation and constellation plotting.
"""

import logging
import numpy as np
import matplotlib.pyplot as plt
from typing import Any, List, Tuple, Dict
from sionna.rt import PathSolver, subcarrier_frequencies

from ..base import SceneSetupService, SionnaConfigService

logger = logging.getLogger(__name__)


class CFRCalculator:
    """
    Specialized calculator for Channel Frequency Response analysis
    """
    
    def __init__(self):
        self.config_service = SionnaConfigService()
        self.scene_service = SceneSetupService()
    
    def _dbm_to_watts(self, dbm: float) -> float:
        """Convert dBm to watts"""
        return 10 ** (dbm / 10) / 1000
    
    def calculate_cfr(
        self,
        scene: Any,
        tx_list: List[Tuple[str, List[float], List[float], str, float]],
        rx_config: Tuple[str, List[float]]
    ) -> Tuple[np.ndarray, np.ndarray, List[int], List[int]]:
        """
        Calculate Channel Frequency Response using Sionna
        
        Args:
            scene: Configured Sionna scene
            tx_list: List of transmitter configurations
            rx_config: Receiver configuration
            
        Returns:
            Tuple of (main_channel, interference_channel, desired_indices, jammer_indices)
        """
        logger.info("Starting CFR calculation")
        
        # Get configuration
        cfr_config = self.config_service.get_cfr_config()
        pathsolver_config = self.config_service.get_pathsolver_config("cfr")
        
        # Setup scene devices
        self.scene_service.clear_existing_devices(scene)
        self.scene_service.add_transmitters(scene, tx_list)
        self.scene_service.add_receiver(scene, rx_config[0], rx_config[1])
        
        # Configure transmitter velocities for CFR
        self.scene_service.set_transmitter_velocities(scene, [30, 0, 0])
        
        # Get transmitter indices by role
        idx_des, idx_jam = self.scene_service.get_transmitter_indices_by_role(scene)
        
        if not idx_des and not idx_jam:
            raise ValueError("No valid transmitters found in scene")
        
        # Calculate paths
        logger.info("Computing propagation paths")
        solver = PathSolver()
        paths = solver(scene, **pathsolver_config)
        
        # Generate frequency grid
        freqs = subcarrier_frequencies(
            cfr_config["N_SUBCARRIERS"], 
            cfr_config["SUBCARRIER_SPACING"]
        )
        
        # Calculate CFR
        ofdm_symbol_duration = 1 / cfr_config["SUBCARRIER_SPACING"]
        H_unit = paths.cfr(
            frequencies=freqs,
            sampling_frequency=1 / ofdm_symbol_duration,
            num_time_steps=cfr_config["N_SUBCARRIERS"],
            normalize_delays=True,
            normalize=False,
            out_type="numpy",
        ).squeeze()
        
        # Apply power weighting (convert dBm to watts)
        all_txs = [scene.get(n) for n in scene.transmitters.keys()]
        tx_powers_dbm = [tx.power_dbm for tx in all_txs]
        tx_powers = [self._dbm_to_watts(p) for p in tx_powers_dbm]
        H = H_unit[:, 0, :]  # Take first time step
        
        # Calculate main and interference channels with proper power weighting
        h_main = np.zeros(cfr_config["N_SUBCARRIERS"], dtype=complex)
        if idx_des:
            h_main = sum(np.sqrt(tx_powers[i]) * H[i] for i in idx_des)
        
        h_intf = np.zeros(cfr_config["N_SUBCARRIERS"], dtype=complex)
        if idx_jam:
            h_intf = sum(np.sqrt(tx_powers[i]) * H[i] for i in idx_jam)
        
        logger.info("CFR calculation completed")
        return h_main, h_intf, idx_des, idx_jam
    
    def generate_qpsk_ofdm_signals(
        self, 
        h_main: np.ndarray, 
        h_intf: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate QPSK+OFDM signals for constellation analysis
        
        Args:
            h_main: Main channel frequency response
            h_intf: Interference channel frequency response
            
        Returns:
            Tuple of (equalized_no_interference, equalized_with_interference)
        """
        logger.info("Generating QPSK+OFDM symbols")
        
        cfr_config = self.config_service.get_cfr_config()
        N_SYMBOLS = cfr_config["N_SYMBOLS"]
        N_SUBCARRIERS = len(h_main)
        EBN0_dB = cfr_config["EBN0_dB"]
        
        # Generate random QPSK symbols
        bits = np.random.randint(0, 2, (N_SYMBOLS, N_SUBCARRIERS, 2))
        bits_jam = np.random.randint(0, 2, (N_SYMBOLS, N_SUBCARRIERS, 2))
        
        X_sig = (1 - 2 * bits[..., 0] + 1j * (1 - 2 * bits[..., 1])) / np.sqrt(2)
        X_jam = (1 - 2 * bits_jam[..., 0] + 1j * (1 - 2 * bits_jam[..., 1])) / np.sqrt(2)
        
        # Apply channel
        Y_sig = X_sig * h_main[None, :]
        Y_int = X_jam * h_intf[None, :]
        
        # Add noise
        p_sig = np.mean(np.abs(Y_sig) ** 2)
        N0 = p_sig / (10 ** (EBN0_dB / 10) * 2) if p_sig > 0 else 1e-10
        noise = np.sqrt(N0 / 2) * (
            np.random.randn(*Y_sig.shape) + 1j * np.random.randn(*Y_sig.shape)
        )
        
        Y_tot = Y_sig + Y_int + noise
        
        # Equalization (with safety check for zero division)
        non_zero_mask = np.abs(h_main) > 1e-10
        y_eq_no_i = np.zeros_like(Y_sig)
        y_eq_with_i = np.zeros_like(Y_tot)
        
        if np.any(non_zero_mask):
            y_eq_no_i[:, non_zero_mask] = (Y_sig + noise)[:, non_zero_mask] / h_main[None, non_zero_mask]
            y_eq_with_i[:, non_zero_mask] = Y_tot[:, non_zero_mask] / h_main[None, non_zero_mask]
        
        return y_eq_no_i, y_eq_with_i
    
    def create_cfr_plot(
        self, 
        h_main: np.ndarray, 
        h_intf: np.ndarray,
        y_eq_no_i: np.ndarray,
        y_eq_with_i: np.ndarray,
        output_path: str
    ) -> bool:
        """
        Create CFR and constellation plot
        
        Args:
            h_main: Main channel frequency response
            h_intf: Interference channel frequency response
            y_eq_no_i: Equalized symbols without interference
            y_eq_with_i: Equalized symbols with interference
            output_path: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Creating CFR plot")
            
            fig, ax = plt.subplots(1, 3, figsize=(15, 4))
            
            # Constellation without interference
            ax[0].scatter(y_eq_no_i.real, y_eq_no_i.imag, s=4, alpha=0.25)
            ax[0].set(title="No interference", xlabel="Real", ylabel="Imag")
            ax[0].grid(True)
            
            # Constellation with interference
            ax[1].scatter(y_eq_with_i.real, y_eq_with_i.imag, s=4, alpha=0.25)
            ax[1].set(title="With interferer", xlabel="Real", ylabel="Imag")
            ax[1].grid(True)
            
            # CFR magnitude
            ax[2].plot(np.abs(h_main), label="|H_main|")
            ax[2].plot(np.abs(h_intf), label="|H_intf|")
            ax[2].set(title="CFR Magnitude", xlabel="Subcarrier Index")
            ax[2].legend()
            ax[2].grid(True)
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches="tight")
            plt.close(fig)
            
            logger.info(f"CFR plot saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating CFR plot: {e}")
            plt.close("all")
            return False