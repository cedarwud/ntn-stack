"""
Dependency Injection Container

Provides unified dependency injection for all SimWorld services.
Part of Phase 3 service layer refactoring - optimizes service dependencies.
"""

import asyncio
import logging
from typing import Dict, Type, Any, Optional, Callable, TypeVar, Generic
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifetime management"""
    SINGLETON = "singleton"      # Single instance for entire application
    SCOPED = "scoped"           # Single instance per request/operation
    TRANSIENT = "transient"     # New instance every time


@dataclass
class ServiceDescriptor:
    """Service registration descriptor"""
    service_type: Type
    implementation_type: Optional[Type] = None
    factory: Optional[Callable[..., Any]] = None
    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    dependencies: list = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class ServiceContainer:
    """
    Dependency injection container for SimWorld services
    
    Provides service registration, resolution, and lifetime management
    with proper dependency injection and circular dependency detection.
    """
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[str, Dict[Type, Any]] = {}
        self._resolution_stack: list = []
        
    def register_singleton(self, service_type: Type, implementation_type: Type = None, factory: Callable = None):
        """Register a service as singleton"""
        self._register_service(service_type, implementation_type, factory, ServiceLifetime.SINGLETON)
        
    def register_scoped(self, service_type: Type, implementation_type: Type = None, factory: Callable = None):
        """Register a service as scoped"""
        self._register_service(service_type, implementation_type, factory, ServiceLifetime.SCOPED)
        
    def register_transient(self, service_type: Type, implementation_type: Type = None, factory: Callable = None):
        """Register a service as transient"""
        self._register_service(service_type, implementation_type, factory, ServiceLifetime.TRANSIENT)
        
    def _register_service(self, service_type: Type, implementation_type: Type = None, factory: Callable = None, lifetime: ServiceLifetime = ServiceLifetime.SINGLETON):
        """Internal service registration"""
        if service_type in self._services:
            logger.warning(f"Service {service_type.__name__} is already registered, overriding")
            
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=implementation_type or service_type,
            factory=factory,
            lifetime=lifetime
        )
        
        self._services[service_type] = descriptor
        logger.debug(f"Registered {service_type.__name__} with lifetime {lifetime.value}")
        
    def resolve(self, service_type: Type[T], scope_id: str = "default") -> T:
        """Resolve a service instance"""
        if service_type not in self._services:
            raise ValueError(f"Service {service_type.__name__} is not registered")
            
        # Check for circular dependencies
        if service_type in self._resolution_stack:
            circular_path = " -> ".join([s.__name__ for s in self._resolution_stack] + [service_type.__name__])
            raise RuntimeError(f"Circular dependency detected: {circular_path}")
            
        try:
            self._resolution_stack.append(service_type)
            return self._create_instance(service_type, scope_id)
        finally:
            self._resolution_stack.remove(service_type)
            
    def _create_instance(self, service_type: Type[T], scope_id: str) -> T:
        """Create service instance based on lifetime"""
        descriptor = self._services[service_type]
        
        # Handle singleton lifetime
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if service_type not in self._singletons:
                self._singletons[service_type] = self._instantiate_service(descriptor, scope_id)
            return self._singletons[service_type]
            
        # Handle scoped lifetime
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            if scope_id not in self._scoped_instances:
                self._scoped_instances[scope_id] = {}
                
            scoped_services = self._scoped_instances[scope_id]
            if service_type not in scoped_services:
                scoped_services[service_type] = self._instantiate_service(descriptor, scope_id)
            return scoped_services[service_type]
            
        # Handle transient lifetime
        else:
            return self._instantiate_service(descriptor, scope_id)
            
    def _instantiate_service(self, descriptor: ServiceDescriptor, scope_id: str) -> Any:
        """Instantiate a service with dependency injection"""
        try:
            # Use factory if provided
            if descriptor.factory:
                if asyncio.iscoroutinefunction(descriptor.factory):
                    raise ValueError("Async factories are not supported in synchronous resolution")
                return descriptor.factory(self)
                
            # Get constructor dependencies
            dependencies = self._resolve_dependencies(descriptor.implementation_type, scope_id)
            
            # Create instance
            instance = descriptor.implementation_type(**dependencies)
            logger.debug(f"Created instance of {descriptor.service_type.__name__}")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to create instance of {descriptor.service_type.__name__}: {e}")
            raise
            
    def _resolve_dependencies(self, implementation_type: Type, scope_id: str) -> Dict[str, Any]:
        """Resolve constructor dependencies"""
        dependencies = {}
        
        # Get type hints for constructor
        import inspect
        signature = inspect.signature(implementation_type.__init__)
        
        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue
                
            # Skip parameters with default values
            if param.default != inspect.Parameter.empty:
                continue
                
            # Resolve dependency
            param_type = param.annotation
            if param_type != inspect.Parameter.empty and param_type in self._services:
                dependencies[param_name] = self.resolve(param_type, scope_id)
            else:
                logger.warning(f"Cannot resolve dependency {param_name}: {param_type} for {implementation_type.__name__}")
                
        return dependencies
        
    async def resolve_async(self, service_type: Type[T], scope_id: str = "default") -> T:
        """Resolve a service instance asynchronously"""
        # For now, delegate to synchronous resolution
        # In the future, this could handle async factories and initialization
        return self.resolve(service_type, scope_id)
        
    def clear_scope(self, scope_id: str):
        """Clear all scoped instances for a scope"""
        if scope_id in self._scoped_instances:
            del self._scoped_instances[scope_id]
            logger.debug(f"Cleared scope: {scope_id}")
            
    def dispose(self):
        """Dispose of all service instances"""
        for instance in self._singletons.values():
            if hasattr(instance, 'dispose'):
                try:
                    instance.dispose()
                except Exception as e:
                    logger.error(f"Error disposing service: {e}")
                    
        self._singletons.clear()
        self._scoped_instances.clear()
        logger.info("Service container disposed")
        
    def get_registered_services(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered services"""
        services_info = {}
        for service_type, descriptor in self._services.items():
            services_info[service_type.__name__] = {
                "service_type": service_type.__name__,
                "implementation_type": descriptor.implementation_type.__name__,
                "lifetime": descriptor.lifetime.value,
                "has_factory": descriptor.factory is not None,
                "is_instantiated": service_type in self._singletons
            }
        return services_info


# Global service container instance
service_container = ServiceContainer()


# Interface definitions for common services
class IPerformanceOptimizer(ABC):
    """Interface for performance optimization services"""
    
    @abstractmethod
    async def optimize_component(self, component: str, optimization_type: str) -> Any:
        pass


class IAlgorithmCalculator(ABC):
    """Interface for algorithm calculation services"""
    
    @abstractmethod
    async def measure_algorithm_performance(self, algorithm_name: str, test_scenarios: list) -> Any:
        pass


class IPerformanceAggregator(ABC):
    """Interface for performance aggregation services"""
    
    @abstractmethod
    async def aggregate_performance_data(self, time_window: Any, components: list = None) -> Any:
        pass


def register_performance_services():
    """Register performance domain services with dependency injection"""
    try:
        from ..domains.performance.services.simworld_optimizer import SimWorldOptimizer
        from ..domains.performance.services.algorithm_calculator import AlgorithmCalculator
        from ..domains.performance.services.performance_aggregator import PerformanceAggregator
        
        # Register concrete implementations
        service_container.register_singleton(SimWorldOptimizer)
        service_container.register_singleton(AlgorithmCalculator)
        service_container.register_singleton(PerformanceAggregator)
        
        # Register interfaces to implementations
        service_container.register_singleton(IPerformanceOptimizer, SimWorldOptimizer)
        service_container.register_singleton(IAlgorithmCalculator, AlgorithmCalculator)
        service_container.register_singleton(IPerformanceAggregator, PerformanceAggregator)
        
        logger.info("Performance services registered with dependency injection")
        
    except ImportError as e:
        logger.error(f"Failed to register performance services: {e}")


def register_core_services():
    """Register core application services"""
    try:
        from ..services.satellite_scheduler import SatelliteScheduler
        
        # Register core services as singletons
        service_container.register_singleton(SatelliteScheduler)
        
        logger.info("Core services registered with dependency injection")
        
    except ImportError as e:
        logger.error(f"Failed to register core services: {e}")


def register_domain_services():
    """Register domain services"""
    try:
        from ..domains.satellite.services.cqrs_satellite_service import CQRSSatelliteService
        from ..domains.satellite.services.tle_service import TLEService
        from ..domains.satellite.services.orbit_service import OrbitService
        
        # Register domain services
        service_container.register_singleton(TLEService)
        service_container.register_singleton(OrbitService)
        service_container.register_scoped(CQRSSatelliteService)  # Scoped for request isolation
        
        logger.info("Domain services registered with dependency injection")
        
    except ImportError as e:
        logger.error(f"Failed to register domain services: {e}")


def configure_dependency_injection():
    """Configure all dependency injection registrations"""
    logger.info("Configuring dependency injection container")
    
    register_core_services()
    register_domain_services()
    register_performance_services()
    
    logger.info("Dependency injection configuration completed")


# Convenience functions for FastAPI dependency injection
def get_performance_optimizer() -> IPerformanceOptimizer:
    """FastAPI dependency for performance optimizer"""
    return service_container.resolve(IPerformanceOptimizer)


def get_algorithm_calculator() -> IAlgorithmCalculator:
    """FastAPI dependency for algorithm calculator"""
    return service_container.resolve(IAlgorithmCalculator)


def get_performance_aggregator() -> IPerformanceAggregator:
    """FastAPI dependency for performance aggregator"""
    return service_container.resolve(IPerformanceAggregator)


# Export container and main functions
__all__ = [
    "service_container",
    "configure_dependency_injection",
    "get_performance_optimizer",
    "get_algorithm_calculator", 
    "get_performance_aggregator",
    "IPerformanceOptimizer",
    "IAlgorithmCalculator",
    "IPerformanceAggregator"
]