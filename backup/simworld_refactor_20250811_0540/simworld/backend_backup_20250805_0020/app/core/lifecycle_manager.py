"""
Unified Lifecycle Manager

Consolidates all lifecycle management logic into a single, coordinated system.
Part of Phase 3 service layer refactoring - replaces scattered lifecycle code.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from contextlib import asynccontextmanager
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class LifecyclePhase(Enum):
    """Application lifecycle phases"""
    STARTUP = "startup"
    RUNNING = "running" 
    SHUTDOWN = "shutdown"
    FAILED = "failed"


class ServicePriority(Enum):
    """Service startup/shutdown priority levels"""
    CRITICAL = 1    # Database, Redis, Config
    HIGH = 2        # Core services, Schedulers
    MEDIUM = 3      # Domain services, CQRS
    LOW = 4         # Background tasks, Monitoring


@dataclass
class ServiceDescriptor:
    """Service lifecycle descriptor"""
    name: str
    startup_func: Callable[[], Any]
    shutdown_func: Optional[Callable[[], Any]] = None
    priority: ServicePriority = ServicePriority.MEDIUM
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: int = 30
    retry_count: int = 3
    critical: bool = False  # If True, failure stops entire startup


class LifecycleManager:
    """
    Unified application lifecycle manager
    
    Coordinates startup and shutdown of all services with proper
    dependency management, error handling, and resource cleanup.
    """
    
    def __init__(self):
        self.services: Dict[str, ServiceDescriptor] = {}
        self.started_services: List[str] = []
        self.service_instances: Dict[str, Any] = {}
        self.current_phase = LifecyclePhase.STARTUP
        self.shutdown_hooks: List[Callable[[], Any]] = []
        
    def register_service(self, service: ServiceDescriptor):
        """Register a service for lifecycle management"""
        logger.info(f"Registering service: {service.name}")
        self.services[service.name] = service
        
    def register_shutdown_hook(self, hook: Callable[[], Any]):
        """Register a shutdown hook function"""
        self.shutdown_hooks.append(hook)
        
    async def startup(self):
        """Execute startup sequence for all registered services"""
        logger.info("Starting application lifecycle startup sequence")
        self.current_phase = LifecyclePhase.STARTUP
        
        try:
            # Sort services by priority and dependencies
            startup_order = self._calculate_startup_order()
            
            for service_name in startup_order:
                await self._start_service(service_name)
                
            self.current_phase = LifecyclePhase.RUNNING
            logger.info("Application startup completed successfully")
            
        except Exception as e:
            logger.error(f"Application startup failed: {e}")
            self.current_phase = LifecyclePhase.FAILED
            await self._emergency_shutdown()
            raise
            
    async def shutdown(self):
        """Execute shutdown sequence for all started services"""
        logger.info("Starting application lifecycle shutdown sequence")
        self.current_phase = LifecyclePhase.SHUTDOWN
        
        try:
            # Execute shutdown hooks first
            for hook in reversed(self.shutdown_hooks):
                try:
                    if asyncio.iscoroutinefunction(hook):
                        await hook()
                    else:
                        hook()
                except Exception as e:
                    logger.error(f"Shutdown hook failed: {e}")
            
            # Shutdown services in reverse order
            for service_name in reversed(self.started_services):
                await self._stop_service(service_name)
                
            logger.info("Application shutdown completed successfully")
            
        except Exception as e:
            logger.error(f"Application shutdown failed: {e}")
            raise
            
    async def _start_service(self, service_name: str):
        """Start a specific service with error handling and retries"""
        service = self.services[service_name]
        logger.info(f"Starting service: {service_name}")
        
        # Check dependencies
        for dep in service.dependencies:
            if dep not in self.started_services:
                raise RuntimeError(f"Service {service_name} depends on {dep} which is not started")
        
        # Start service with retries
        for attempt in range(service.retry_count):
            try:
                # Execute startup with timeout
                startup_coro = service.startup_func()
                if asyncio.iscoroutine(startup_coro):
                    result = await asyncio.wait_for(startup_coro, timeout=service.timeout_seconds)
                else:
                    result = startup_coro
                
                # Store service instance if returned
                if result is not None:
                    self.service_instances[service_name] = result
                
                self.started_services.append(service_name)
                logger.info(f"Service {service_name} started successfully")
                return
                
            except asyncio.TimeoutError:
                logger.error(f"Service {service_name} startup timeout (attempt {attempt + 1})")
                if attempt == service.retry_count - 1:
                    if service.critical:
                        raise RuntimeError(f"Critical service {service_name} failed to start")
                    else:
                        logger.warning(f"Non-critical service {service_name} failed to start")
                        return
                        
            except Exception as e:
                logger.error(f"Service {service_name} startup failed: {e} (attempt {attempt + 1})")
                if attempt == service.retry_count - 1:
                    if service.critical:
                        raise RuntimeError(f"Critical service {service_name} failed to start: {e}")
                    else:
                        logger.warning(f"Non-critical service {service_name} failed to start: {e}")
                        return
                
                await asyncio.sleep(1)  # Wait before retry
                
    async def _stop_service(self, service_name: str):
        """Stop a specific service"""
        service = self.services[service_name]
        logger.info(f"Stopping service: {service_name}")
        
        try:
            if service.shutdown_func:
                shutdown_coro = service.shutdown_func()
                if asyncio.iscoroutine(shutdown_coro):
                    await asyncio.wait_for(shutdown_coro, timeout=service.timeout_seconds)
                else:
                    shutdown_coro
                    
            # Remove from started services
            if service_name in self.started_services:
                self.started_services.remove(service_name)
                
            # Remove service instance
            if service_name in self.service_instances:
                del self.service_instances[service_name]
                
            logger.info(f"Service {service_name} stopped successfully")
            
        except asyncio.TimeoutError:
            logger.error(f"Service {service_name} shutdown timeout")
        except Exception as e:
            logger.error(f"Service {service_name} shutdown failed: {e}")
            
    def _calculate_startup_order(self) -> List[str]:
        """Calculate service startup order based on priority and dependencies"""
        # Group services by priority
        priority_groups = {}
        for name, service in self.services.items():
            priority = service.priority
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(name)
        
        # Sort each priority group by dependencies
        startup_order = []
        for priority in sorted(priority_groups.keys(), key=lambda x: x.value):
            group_services = priority_groups[priority]
            group_order = self._topological_sort(group_services)
            startup_order.extend(group_order)
            
        return startup_order
        
    def _topological_sort(self, service_names: List[str]) -> List[str]:
        """Sort services by dependencies using topological sort"""
        # Simple dependency resolution for services in the same priority group
        visited = set()
        result = []
        
        def visit(name):
            if name in visited:
                return
            visited.add(name)
            
            service = self.services[name]
            for dep in service.dependencies:
                if dep in service_names and dep not in visited:
                    visit(dep)
                    
            result.append(name)
            
        for name in service_names:
            visit(name)
            
        return result
        
    async def _emergency_shutdown(self):
        """Emergency shutdown in case of startup failure"""
        logger.error("Executing emergency shutdown")
        
        # Stop all started services
        for service_name in reversed(self.started_services):
            try:
                await self._stop_service(service_name)
            except Exception as e:
                logger.error(f"Emergency shutdown of {service_name} failed: {e}")
                
    def get_service_status(self) -> Dict[str, Any]:
        """Get current status of all services"""
        return {
            "phase": self.current_phase.value,
            "started_services": self.started_services.copy(),
            "total_services": len(self.services),
            "service_instances": list(self.service_instances.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    def get_service_instance(self, service_name: str) -> Optional[Any]:
        """Get a service instance by name"""
        return self.service_instances.get(service_name)


# Global lifecycle manager instance
lifecycle_manager = LifecycleManager()


@asynccontextmanager
async def lifespan_context(app):
    """
    Unified lifespan context manager for FastAPI
    
    Replaces the scattered lifespan management in main.py and db/lifespan.py
    """
    try:
        # Startup
        await lifecycle_manager.startup()
        
        # Application is ready
        yield
        
    finally:
        # Shutdown
        await lifecycle_manager.shutdown()


# Convenience functions for service registration
def register_service(
    name: str,
    startup_func: Callable[[], Any],
    shutdown_func: Optional[Callable[[], Any]] = None,
    priority: ServicePriority = ServicePriority.MEDIUM,
    dependencies: List[str] = None,
    timeout_seconds: int = 30,
    retry_count: int = 3,
    critical: bool = False
):
    """Register a service with the lifecycle manager"""
    service = ServiceDescriptor(
        name=name,
        startup_func=startup_func,
        shutdown_func=shutdown_func,
        priority=priority,
        dependencies=dependencies or [],
        timeout_seconds=timeout_seconds,
        retry_count=retry_count,
        critical=critical
    )
    lifecycle_manager.register_service(service)


def register_shutdown_hook(hook: Callable[[], Any]):
    """Register a shutdown hook"""
    lifecycle_manager.register_shutdown_hook(hook)


def get_service_instance(service_name: str) -> Optional[Any]:
    """Get a service instance"""
    return lifecycle_manager.get_service_instance(service_name)


def get_lifecycle_status() -> Dict[str, Any]:
    """Get current lifecycle status"""
    return lifecycle_manager.get_service_status()