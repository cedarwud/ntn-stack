"""
Sionna Configuration Service

Provides standard configurations for Sionna simulations.
Centralizes common parameters and ensures consistency across different simulation types.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class SionnaConfigService:
    """
    Provides standard Sionna simulation configurations
    """
    
    # Standard antenna array configuration
    STANDARD_ARRAY_CONFIG = {
        "num_rows": 1,
        "num_cols": 1,
        "vertical_spacing": 0.5,
        "horizontal_spacing": 0.5,
        "pattern": "iso",
        "polarization": "V",
    }
    
    # Standard PathSolver configuration for CFR calculations
    CFR_PATHSOLVER_CONFIG = {
        "max_depth": 10,
        "los": True,
        "specular_reflection": True,
        "diffuse_reflection": False,
        "refraction": False,
        "synthetic_array": False,
        "seed": 41,
    }
    
    # Standard PathSolver configuration for Doppler calculations
    DOPPLER_PATHSOLVER_CONFIG = {
        "max_depth": 3,
        "los": True,
        "specular_reflection": True,
        "diffuse_reflection": False,
        "refraction": False,
        "synthetic_array": False,
        "seed": 41,
    }
    
    # Standard OFDM parameters
    OFDM_CONFIG = {
        "N_SUBCARRIERS": 1024,
        "SUBCARRIER_SPACING": 30e3,
        "num_ofdm_symbols": 1024,
    }
    
    # RadioMapSolver configuration
    RADIO_MAP_CONFIG = {
        "max_depth": 10,
        "samples_per_tx": 10**7,
    }
    
    @classmethod
    def get_array_config(cls, custom_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get antenna array configuration
        
        Args:
            custom_config: Optional custom configuration to override defaults
            
        Returns:
            Complete antenna array configuration
        """
        config = cls.STANDARD_ARRAY_CONFIG.copy()
        if custom_config:
            config.update(custom_config)
        return config
    
    @classmethod
    def get_pathsolver_config(cls, simulation_type: str = "cfr") -> Dict[str, Any]:
        """
        Get PathSolver configuration for specific simulation type
        
        Args:
            simulation_type: Type of simulation ("cfr", "doppler", "channel")
            
        Returns:
            PathSolver configuration
        """
        if simulation_type.lower() == "doppler":
            return cls.DOPPLER_PATHSOLVER_CONFIG.copy()
        else:
            return cls.CFR_PATHSOLVER_CONFIG.copy()
    
    @classmethod
    def get_ofdm_config(cls) -> Dict[str, Any]:
        """
        Get OFDM configuration
        
        Returns:
            OFDM parameters
        """
        return cls.OFDM_CONFIG.copy()
    
    @classmethod
    def get_radio_map_config(
        cls, 
        cell_size: float = 1.0, 
        samples_per_tx: int = 10**7
    ) -> Dict[str, Any]:
        """
        Get RadioMapSolver configuration
        
        Args:
            cell_size: Cell size in meters
            samples_per_tx: Number of samples per transmitter
            
        Returns:
            RadioMapSolver configuration
        """
        config = cls.RADIO_MAP_CONFIG.copy()
        config.update({
            "cell_size": (cell_size, cell_size),
            "samples_per_tx": samples_per_tx,
        })
        return config
    
    @classmethod
    def get_cfr_config(cls) -> Dict[str, Any]:
        """
        Get CFR calculation configuration
        
        Returns:
            CFR-specific configuration
        """
        ofdm = cls.get_ofdm_config()
        return {
            "N_SUBCARRIERS": ofdm["N_SUBCARRIERS"],
            "SUBCARRIER_SPACING": ofdm["SUBCARRIER_SPACING"],
            "N_SYMBOLS": 1,    # For CFR calculations (corrected from backup)
            "EBN0_dB": 20.0,   # Signal-to-noise ratio (corrected from backup)
        }
    
    @classmethod
    def log_configuration(cls, config_type: str, config: Dict[str, Any]) -> None:
        """
        Log configuration details for debugging
        
        Args:
            config_type: Type of configuration being logged
            config: Configuration dictionary
        """
        logger.info(f"{config_type} Configuration:")
        for key, value in config.items():
            logger.info(f"  {key}: {value}")