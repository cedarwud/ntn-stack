"""
System Domain Interfaces

This module defines the interfaces for the system domain,
following the dependency inversion principle of clean architecture.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class SystemHealthInterface(ABC):
    """Interface for system health monitoring"""
    
    @abstractmethod
    async def check_system_health(self) -> Dict[str, Any]:
        """Check overall system health status"""
        pass
    
    @abstractmethod
    async def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get status of a specific service"""
        pass


class ConfigurationInterface(ABC):
    """Interface for system configuration management"""
    
    @abstractmethod
    async def get_configuration(self, config_key: str) -> Any:
        """Get configuration value"""
        pass
    
    @abstractmethod
    async def update_configuration(
        self, 
        config_key: str, 
        config_value: Any
    ) -> Dict[str, Any]:
        """Update configuration value"""
        pass


class MetricsCollectorInterface(ABC):
    """Interface for system metrics collection"""
    
    @abstractmethod
    async def collect_metrics(self) -> Dict[str, Any]:
        """Collect system metrics"""
        pass
    
    @abstractmethod
    async def export_metrics(self, format_type: str = "prometheus") -> str:
        """Export metrics in specified format"""
        pass