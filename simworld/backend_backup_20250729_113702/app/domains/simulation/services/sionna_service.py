"""
Sionna Simulation Service V2 - Refactored Modular Version

This is the new modular version of the Sionna simulation service that replaces
the monolithic sionna_service.py. It orchestrates the following specialized services:
- SceneManagementService: Scene health checking, XML path resolution, file management
- RenderingService: 3D rendering and image generation
- CommunicationSimulationService: RF communication simulation using Sionna

This refactored version maintains 100% API compatibility with the original service
while providing better modularity, testability, and maintainability.
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

# Interface and models
from app.domains.simulation.interfaces.simulation_service_interface import SimulationServiceInterface
from app.domains.simulation.models.simulation_model import SimulationParameters

# Modular services
from .scene.scene_management_service import SceneManagementService
from .rendering.rendering_service import RenderingService
from .communication.communication_simulation_service import CommunicationSimulationService

# Config imports
from app.core.config import (
    CFR_PLOT_IMAGE_PATH,
    DOPPLER_IMAGE_PATH,
    CHANNEL_RESPONSE_IMAGE_PATH,
    SINR_MAP_IMAGE_PATH,
)

logger = logging.getLogger(__name__)


class SionnaSimulationService(SimulationServiceInterface):
    """
    Refactored Sionna Simulation Service (Modular Architecture)
    
    This is the new modular version that replaced the monolithic implementation:
    - Maintains 100% API compatibility with the original service
    - Uses specialized services for different responsibilities
    - Provides better error handling and logging
    - Easier to test and maintain
    """
    
    def __init__(self):
        """Initialize the refactored simulation service with modular components"""
        # Initialize specialized services
        self.scene_service = SceneManagementService()
        self.rendering_service = RenderingService()
        self.communication_service = CommunicationSimulationService(self.scene_service)
        
        logger.info("SionnaSimulationService initialized with modular architecture")
    
    # =============================================================================
    # Scene Rendering - Delegated to RenderingService
    # =============================================================================
    
    async def generate_empty_scene_image(self, output_path: str) -> bool:
        """
        Generate empty scene image by rendering the GLB file
        
        This method delegates to the RenderingService for 3D visualization
        
        Args:
            output_path: Path where the image should be saved
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Generating empty scene image at {output_path}")
        
        try:
            # Prepare output file using scene service
            self.scene_service.prepare_output_file(output_path, "空場景圖檔")
            
            # Delegate to rendering service
            success = self.rendering_service.generate_empty_scene_image(output_path)
            
            if success:
                # Verify output using scene service
                return self.scene_service.verify_output_file(output_path)
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error generating empty scene image: {e}", exc_info=True)
            return False
    
    # =============================================================================
    # Communication Simulations - Delegated to CommunicationSimulationService
    # =============================================================================
    
    async def generate_cfr_plot(
        self,
        session: AsyncSession,
        output_path: str = str(CFR_PLOT_IMAGE_PATH),
        scene_name: str = "nycu",
    ) -> bool:
        """
        Generate Channel Frequency Response (CFR) plot
        
        This method delegates to the CommunicationSimulationService for RF simulation
        
        Args:
            session: Database session for fetching device data
            output_path: Path where the plot should be saved
            scene_name: Name of the scene to use
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Generating CFR plot for scene '{scene_name}' at {output_path}")
        
        try:
            # Prepare output file
            self.scene_service.prepare_output_file(output_path, "CFR 圖檔")
            
            # Get scene XML path with health checking
            scene_xml_path = self.scene_service.get_scene_xml_file_path(scene_name)
            logger.info(f"Using scene: {scene_xml_path}")
            
            # For now, delegate to the communication service
            # TODO: Implement full CFR generation with extracted logic
            success = await self.communication_service.generate_cfr_plot(
                session, output_path, scene_name
            )
            
            if success:
                return self.scene_service.verify_output_file(output_path)
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error generating CFR plot: {e}", exc_info=True)
            return False
    
    async def generate_sinr_map(
        self,
        session: AsyncSession,
        output_path: str = str(SINR_MAP_IMAGE_PATH),
        scene_name: str = "nycu",
        sinr_vmin: float = -40,
        sinr_vmax: float = 0,
        cell_size: float = 1.0,
        samples_per_tx: int = 10**7,
    ) -> bool:
        """
        Generate SINR (Signal-to-Interference-plus-Noise Ratio) map
        
        This method delegates to the CommunicationSimulationService for radio map generation
        
        Args:
            session: Database session for fetching device data
            output_path: Path where the map should be saved
            scene_name: Name of the scene to use
            sinr_vmin: Minimum SINR value for colormap (dB)
            sinr_vmax: Maximum SINR value for colormap (dB)
            cell_size: Size of each cell in the map (meters)
            samples_per_tx: Number of samples per transmitter
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Generating SINR map for scene '{scene_name}' at {output_path}")
        
        try:
            # Prepare output file
            self.scene_service.prepare_output_file(output_path, "SINR 地圖圖檔")
            
            # Get scene XML path with health checking
            scene_xml_path = self.scene_service.get_scene_xml_file_path(scene_name)
            logger.info(f"Using scene: {scene_xml_path}")
            
            # Delegate to communication service
            success = await self.communication_service.generate_sinr_map(
                session, output_path, scene_name, sinr_vmin, sinr_vmax, cell_size, samples_per_tx
            )
            
            if success:
                return self.scene_service.verify_output_file(output_path)
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error generating SINR map: {e}", exc_info=True)
            return False
    
    async def generate_doppler_plots(
        self,
        session: AsyncSession,
        output_path: str = str(DOPPLER_IMAGE_PATH),
        scene_name: str = "nycu",
    ) -> bool:
        """
        Generate delay-Doppler plots
        
        This method delegates to the CommunicationSimulationService for Doppler analysis
        
        Args:
            session: Database session for fetching device data
            output_path: Path where the plots should be saved
            scene_name: Name of the scene to use
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Generating Doppler plots for scene '{scene_name}' at {output_path}")
        
        try:
            # Prepare output file
            self.scene_service.prepare_output_file(output_path, "延遲多普勒圖檔")
            
            # Get scene XML path with health checking
            scene_xml_path = self.scene_service.get_scene_xml_file_path(scene_name)
            logger.info(f"Using scene: {scene_xml_path}")
            
            # Delegate to communication service
            success = await self.communication_service.generate_doppler_plots(
                session, output_path, scene_name
            )
            
            if success:
                return self.scene_service.verify_output_file(output_path)
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error generating Doppler plots: {e}", exc_info=True)
            return False
    
    async def generate_channel_response_plots(
        self,
        session: AsyncSession,
        output_path: str = str(CHANNEL_RESPONSE_IMAGE_PATH),
        scene_name: str = "nycu",
    ) -> bool:
        """
        Generate channel response plots (H_des, H_jam, H_all)
        
        This method delegates to the CommunicationSimulationService for channel analysis
        
        Args:
            session: Database session for fetching device data
            output_path: Path where the plots should be saved
            scene_name: Name of the scene to use
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Generating channel response plots for scene '{scene_name}' at {output_path}")
        
        try:
            # Prepare output file
            self.scene_service.prepare_output_file(output_path, "通道響應圖檔")
            
            # Get scene XML path with health checking
            scene_xml_path = self.scene_service.get_scene_xml_file_path(scene_name)
            logger.info(f"Using scene: {scene_xml_path}")
            
            # Delegate to communication service
            success = await self.communication_service.generate_channel_response_plots(
                session, output_path, scene_name
            )
            
            if success:
                return self.scene_service.verify_output_file(output_path)
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error generating channel response plots: {e}", exc_info=True)
            return False
    
    # =============================================================================
    # Generic Simulation Interface
    # =============================================================================
    
    async def run_simulation(
        self, 
        session: AsyncSession, 
        params: SimulationParameters
    ) -> Dict[str, Any]:
        """
        Run a generic simulation based on parameters
        
        This method provides a unified interface for different simulation types
        
        Args:
            session: Database session
            params: Simulation parameters
            
        Returns:
            Dictionary containing simulation results
        """
        logger.info(f"Running simulation with params: {params}")
        
        try:
            simulation_type = params.simulation_type.lower()
            
            if simulation_type == "cfr":
                success = await self.generate_cfr_plot(
                    session, params.output_path, params.scene_name
                )
                return {"success": success, "type": "cfr", "output_path": params.output_path}
                
            elif simulation_type == "sinr":
                success = await self.generate_sinr_map(
                    session, params.output_path, params.scene_name
                )
                return {"success": success, "type": "sinr", "output_path": params.output_path}
                
            elif simulation_type == "doppler":
                success = await self.generate_doppler_plots(
                    session, params.output_path, params.scene_name
                )
                return {"success": success, "type": "doppler", "output_path": params.output_path}
                
            elif simulation_type == "channel":
                success = await self.generate_channel_response_plots(
                    session, params.output_path, params.scene_name
                )
                return {"success": success, "type": "channel", "output_path": params.output_path}
                
            elif simulation_type == "scene":
                success = await self.generate_empty_scene_image(params.output_path)
                return {"success": success, "type": "scene", "output_path": params.output_path}
                
            else:
                logger.error(f"Unknown simulation type: {simulation_type}")
                return {"success": False, "error": f"Unknown simulation type: {simulation_type}"}
                
        except Exception as e:
            logger.error(f"Error running simulation: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    # =============================================================================
    # Service Health and Status
    # =============================================================================
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get the status of all modular services
        
        Returns:
            Dictionary containing service status information
        """
        return {
            "service_version": "v2.0",
            "architecture": "modular",
            "components": {
                "scene_service": "active",
                "rendering_service": "active", 
                "communication_service": "active"
            },
            "gpu_available": self.communication_service._setup_gpu(),
            "status": "healthy"
        }


# Create a default instance for backwards compatibility
sionna_service = SionnaSimulationService()