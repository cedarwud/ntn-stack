"""
Microservice Gateway for NetStack Service - Phase 2 Stage 4

提供統一的微服務接口，整合 NetStack 和 SimWorld 服務通信，
實現服務發現、負載均衡、安全認證和API路由功能。

Key Features:
- Service Discovery and Registration
- Load Balancing and Health Checks
- API Gateway and Routing
- Security and Authentication
- Circuit Breaker and Rate Limiting
- Monitoring and Logging
"""

import asyncio
import logging
import uuid
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import jwt

import structlog
import httpx
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
from prometheus_client import Counter, Histogram, Gauge

logger = structlog.get_logger(__name__)


class ServiceStatus(Enum):
    """服務狀態"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"


class LoadBalanceStrategy(Enum):
    """負載均衡策略"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_RANDOM = "weighted_random"
    GEOGRAPHIC_PROXIMITY = "geographic_proximity"


@dataclass
class ServiceEndpoint:
    """服務端點"""
    service_id: str
    service_name: str
    host: str
    port: int
    protocol: str = "http"
    weight: float = 1.0
    health_check_url: str = "/health"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 狀態追蹤
    status: ServiceStatus = ServiceStatus.HEALTHY
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    total_requests: int = 0
    active_connections: int = 0
    average_response_time_ms: float = 0.0
    
    def get_url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"


@dataclass
class APIRoute:
    """API路由配置"""
    route_id: str
    path_pattern: str
    target_service: str
    method: str
    authentication_required: bool = True
    rate_limit_per_minute: int = 100
    timeout_seconds: float = 30.0
    circuit_breaker_enabled: bool = True
    transform_request: Optional[Callable] = None
    transform_response: Optional[Callable] = None


@dataclass
class CircuitBreakerState:
    """熔斷器狀態"""
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    failure_threshold: int = 5
    timeout_seconds: int = 60


class MicroserviceGateway:
    """微服務網關"""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.logger = structlog.get_logger(__name__)
        
        # 服務註冊中心
        self.service_registry: Dict[str, List[ServiceEndpoint]] = {}
        self.service_discovery_cache: Dict[str, ServiceEndpoint] = {}
        
        # API路由
        self.api_routes: Dict[str, APIRoute] = {}
        
        # 負載均衡
        self.load_balance_strategy = LoadBalanceStrategy.ROUND_ROBIN
        self.round_robin_counters: Dict[str, int] = {}
        
        # 熔斷器
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {}
        
        # 安全認證
        self.jwt_secret = "ntn-stack-microservice-secret-key"
        self.security = HTTPBearer()
        
        # Redis連接
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # HTTP客戶端
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # 監控指標
        self.setup_metrics()
        
        # FastAPI應用
        self.app = FastAPI(
            title="NTN Stack Microservice Gateway",
            description="微服務API網關",
            version="2.0.0"
        )
        self.setup_fastapi()
        
        # 服務狀態
        self.is_running = False
        self.health_check_task: Optional[asyncio.Task] = None

    def setup_metrics(self):
        """設置監控指標"""
        self.metrics = {
            "requests_total": Counter(
                "gateway_requests_total",
                "Total number of requests",
                ["service", "method", "status"]
            ),
            "request_duration": Histogram(
                "gateway_request_duration_seconds",
                "Request duration in seconds",
                ["service", "method"]
            ),
            "active_connections": Gauge(
                "gateway_active_connections",
                "Number of active connections",
                ["service"]
            ),
            "circuit_breaker_state": Gauge(
                "gateway_circuit_breaker_state",
                "Circuit breaker state (0=closed, 1=open, 2=half_open)",
                ["service"]
            )
        }

    def setup_fastapi(self):
        """設置FastAPI應用"""
        # CORS中間件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 註冊路由
        self.setup_gateway_routes()

    def setup_gateway_routes(self):
        """設置網關路由"""
        
        @self.app.get("/health")
        async def health_check():
            """健康檢查"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "services": len(self.service_registry),
                "routes": len(self.api_routes)
            }
        
        @self.app.post("/api/v1/services/register")
        async def register_service(endpoint: dict):
            """註冊服務"""
            try:
                service_endpoint = ServiceEndpoint(**endpoint)
                await self.register_service_endpoint(service_endpoint)
                return {"status": "registered", "service_id": service_endpoint.service_id}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
        
        @self.app.delete("/api/v1/services/{service_id}")
        async def unregister_service(service_id: str):
            """註銷服務"""
            await self.unregister_service_endpoint(service_id)
            return {"status": "unregistered", "service_id": service_id}
        
        @self.app.get("/api/v1/services")
        async def list_services():
            """列出所有服務"""
            return {
                "services": {
                    name: [
                        {
                            "service_id": endpoint.service_id,
                            "host": endpoint.host,
                            "port": endpoint.port,
                            "status": endpoint.status.value,
                            "weight": endpoint.weight
                        }
                        for endpoint in endpoints
                    ]
                    for name, endpoints in self.service_registry.items()
                }
            }
        
        @self.app.post("/api/v1/routes")
        async def create_route(route_config: dict):
            """創建API路由"""
            try:
                route = APIRoute(**route_config)
                await self.add_api_route(route)
                return {"status": "created", "route_id": route.route_id}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

    async def start_gateway(self):
        """啟動網關"""
        if not self.is_running:
            self.is_running = True
            
            # 初始化預設服務和路由
            await self.initialize_default_services()
            await self.initialize_default_routes()
            
            # 啟動健康檢查
            self.health_check_task = asyncio.create_task(self.health_check_loop())
            
            self.logger.info("微服務網關已啟動")

    async def stop_gateway(self):
        """停止網關"""
        if self.is_running:
            self.is_running = False
            
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass
            
            await self.http_client.aclose()
            self.logger.info("微服務網關已停止")

    async def initialize_default_services(self):
        """初始化預設服務"""
        # NetStack服務
        netstack_endpoint = ServiceEndpoint(
            service_id="netstack_primary",
            service_name="netstack",
            host="localhost",
            port=8000,
            metadata={
                "version": "2.0.0",
                "capabilities": ["prediction", "synchronization", "verification"]
            }
        )
        
        # SimWorld服務
        simworld_endpoint = ServiceEndpoint(
            service_id="simworld_primary",
            service_name="simworld",
            host="localhost", 
            port=8001,
            metadata={
                "version": "2.0.0",
                "capabilities": ["simulation", "modeling", "visualization"]
            }
        )
        
        await self.register_service_endpoint(netstack_endpoint)
        await self.register_service_endpoint(simworld_endpoint)

    async def initialize_default_routes(self):
        """初始化預設路由"""
        # NetStack API路由
        netstack_routes = [
            APIRoute(
                route_id="netstack_prediction",
                path_pattern="/api/v1/netstack/prediction/*",
                target_service="netstack",
                method="POST",
                rate_limit_per_minute=200
            ),
            APIRoute(
                route_id="netstack_synchronization",
                path_pattern="/api/v1/netstack/sync/*",
                target_service="netstack",
                method="POST",
                rate_limit_per_minute=100
            ),
            APIRoute(
                route_id="netstack_verification",
                path_pattern="/api/v1/netstack/verification/*",
                target_service="netstack",
                method="GET",
                rate_limit_per_minute=50
            )
        ]
        
        # SimWorld API路由
        simworld_routes = [
            APIRoute(
                route_id="simworld_simulation",
                path_pattern="/api/v1/simworld/simulation/*",
                target_service="simworld",
                method="POST",
                rate_limit_per_minute=100
            ),
            APIRoute(
                route_id="simworld_modeling",
                path_pattern="/api/v1/simworld/modeling/*",
                target_service="simworld",
                method="GET",
                rate_limit_per_minute=150
            )
        ]
        
        for route in netstack_routes + simworld_routes:
            await self.add_api_route(route)

    async def register_service_endpoint(self, endpoint: ServiceEndpoint):
        """註冊服務端點"""
        service_name = endpoint.service_name
        
        if service_name not in self.service_registry:
            self.service_registry[service_name] = []
        
        # 檢查是否已存在
        existing = next(
            (ep for ep in self.service_registry[service_name] 
             if ep.service_id == endpoint.service_id), None
        )
        
        if existing:
            # 更新現有端點
            existing.host = endpoint.host
            existing.port = endpoint.port
            existing.weight = endpoint.weight
            existing.metadata = endpoint.metadata
        else:
            # 添加新端點
            self.service_registry[service_name].append(endpoint)
        
        # 立即健康檢查
        await self.check_service_health(endpoint)
        
        # 更新Redis
        await self.update_service_registry_cache()
        
        self.logger.info(f"服務已註冊: {endpoint.service_name}({endpoint.service_id})")

    async def unregister_service_endpoint(self, service_id: str):
        """註銷服務端點"""
        for service_name, endpoints in self.service_registry.items():
            self.service_registry[service_name] = [
                ep for ep in endpoints if ep.service_id != service_id
            ]
        
        # 清理空的服務
        self.service_registry = {
            name: endpoints for name, endpoints in self.service_registry.items()
            if endpoints
        }
        
        await self.update_service_registry_cache()
        self.logger.info(f"服務已註銷: {service_id}")

    async def add_api_route(self, route: APIRoute):
        """添加API路由"""
        self.api_routes[route.route_id] = route
        self.logger.info(f"API路由已添加: {route.path_pattern} -> {route.target_service}")

    async def discover_service(self, service_name: str) -> Optional[ServiceEndpoint]:
        """服務發現"""
        if service_name not in self.service_registry:
            return None
        
        endpoints = [
            ep for ep in self.service_registry[service_name]
            if ep.status == ServiceStatus.HEALTHY
        ]
        
        if not endpoints:
            return None
        
        # 應用負載均衡策略
        return await self.apply_load_balancing(service_name, endpoints)

    async def apply_load_balancing(self, service_name: str, 
                                 endpoints: List[ServiceEndpoint]) -> ServiceEndpoint:
        """應用負載均衡策略"""
        if self.load_balance_strategy == LoadBalanceStrategy.ROUND_ROBIN:
            if service_name not in self.round_robin_counters:
                self.round_robin_counters[service_name] = 0
            
            index = self.round_robin_counters[service_name] % len(endpoints)
            self.round_robin_counters[service_name] += 1
            return endpoints[index]
        
        elif self.load_balance_strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            return min(endpoints, key=lambda ep: ep.active_connections)
        
        elif self.load_balance_strategy == LoadBalanceStrategy.WEIGHTED_RANDOM:
            import random
            weights = [ep.weight for ep in endpoints]
            return random.choices(endpoints, weights=weights)[0]
        
        else:
            # 預設隨機選擇
            import random
            return random.choice(endpoints)

    async def proxy_request(self, service_name: str, path: str, method: str,
                          headers: dict = None, body: bytes = None) -> dict:
        """代理請求到目標服務"""
        # 服務發現
        endpoint = await self.discover_service(service_name)
        if not endpoint:
            raise HTTPException(
                status_code=503, 
                detail=f"Service {service_name} not available"
            )
        
        # 檢查熔斷器
        if await self.is_circuit_breaker_open(endpoint.service_id):
            raise HTTPException(
                status_code=503,
                detail=f"Circuit breaker open for {endpoint.service_id}"
            )
        
        # 構建目標URL
        target_url = f"{endpoint.get_url()}{path}"
        
        # 發送請求
        start_time = time.time()
        try:
            endpoint.active_connections += 1
            
            response = await self.http_client.request(
                method=method,
                url=target_url,
                headers=headers,
                content=body,
                timeout=30.0
            )
            
            # 記錄成功
            await self.record_request_success(endpoint, time.time() - start_time)
            
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.content
            }
            
        except Exception as e:
            # 記錄失敗
            await self.record_request_failure(endpoint, str(e))
            raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")
        
        finally:
            endpoint.active_connections = max(0, endpoint.active_connections - 1)

    async def check_service_health(self, endpoint: ServiceEndpoint):
        """檢查服務健康狀態"""
        try:
            health_url = f"{endpoint.get_url()}{endpoint.health_check_url}"
            response = await self.http_client.get(health_url, timeout=5.0)
            
            if response.status_code == 200:
                endpoint.status = ServiceStatus.HEALTHY
                endpoint.consecutive_failures = 0
            else:
                endpoint.status = ServiceStatus.UNHEALTHY
                endpoint.consecutive_failures += 1
            
            endpoint.last_health_check = datetime.now()
            
        except Exception as e:
            endpoint.status = ServiceStatus.UNHEALTHY
            endpoint.consecutive_failures += 1
            endpoint.last_health_check = datetime.now()
            self.logger.warning(f"健康檢查失敗: {endpoint.service_id}: {e}")

    async def health_check_loop(self):
        """健康檢查循環"""
        while self.is_running:
            try:
                for endpoints in self.service_registry.values():
                    for endpoint in endpoints:
                        await self.check_service_health(endpoint)
                
                await asyncio.sleep(30.0)  # 30秒檢查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"健康檢查循環異常: {e}")
                await asyncio.sleep(10.0)

    async def is_circuit_breaker_open(self, service_id: str) -> bool:
        """檢查熔斷器是否開啟"""
        if service_id not in self.circuit_breakers:
            self.circuit_breakers[service_id] = CircuitBreakerState()
        
        breaker = self.circuit_breakers[service_id]
        
        if breaker.state == "OPEN":
            # 檢查是否超過超時時間
            if (breaker.last_failure_time and 
                datetime.now() - breaker.last_failure_time > 
                timedelta(seconds=breaker.timeout_seconds)):
                breaker.state = "HALF_OPEN"
                return False
            return True
        
        return False

    async def record_request_success(self, endpoint: ServiceEndpoint, response_time: float):
        """記錄請求成功"""
        endpoint.total_requests += 1
        
        # 更新平均響應時間
        if endpoint.total_requests == 1:
            endpoint.average_response_time_ms = response_time * 1000
        else:
            alpha = 0.1  # 平滑因子
            endpoint.average_response_time_ms = (
                alpha * response_time * 1000 +
                (1 - alpha) * endpoint.average_response_time_ms
            )
        
        # 重置熔斷器
        if endpoint.service_id in self.circuit_breakers:
            breaker = self.circuit_breakers[endpoint.service_id]
            if breaker.state == "HALF_OPEN":
                breaker.state = "CLOSED"
                breaker.failure_count = 0

    async def record_request_failure(self, endpoint: ServiceEndpoint, error: str):
        """記錄請求失敗"""
        endpoint.total_requests += 1
        
        # 更新熔斷器
        if endpoint.service_id not in self.circuit_breakers:
            self.circuit_breakers[endpoint.service_id] = CircuitBreakerState()
        
        breaker = self.circuit_breakers[endpoint.service_id]
        breaker.failure_count += 1
        breaker.last_failure_time = datetime.now()
        
        # 檢查是否需要開啟熔斷器
        if breaker.failure_count >= breaker.failure_threshold:
            breaker.state = "OPEN"

    async def update_service_registry_cache(self):
        """更新服務註冊緩存到Redis"""
        try:
            registry_data = {}
            for service_name, endpoints in self.service_registry.items():
                registry_data[service_name] = [
                    {
                        "service_id": ep.service_id,
                        "host": ep.host,
                        "port": ep.port,
                        "status": ep.status.value,
                        "weight": ep.weight,
                        "metadata": ep.metadata
                    }
                    for ep in endpoints
                ]
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.redis_client.set,
                "service_registry",
                json.dumps(registry_data),
                300  # 5分鐘過期
            )
            
        except Exception as e:
            self.logger.warning(f"更新Redis緩存失敗: {e}")

    async def get_gateway_status(self) -> Dict[str, Any]:
        """獲取網關狀態"""
        return {
            "gateway_status": {
                "is_running": self.is_running,
                "registered_services": len(self.service_registry),
                "api_routes": len(self.api_routes),
                "load_balance_strategy": self.load_balance_strategy.value
            },
            "service_registry": {
                name: [
                    {
                        "service_id": ep.service_id,
                        "status": ep.status.value,
                        "consecutive_failures": ep.consecutive_failures,
                        "total_requests": ep.total_requests,
                        "active_connections": ep.active_connections,
                        "avg_response_time_ms": ep.average_response_time_ms
                    }
                    for ep in endpoints
                ]
                for name, endpoints in self.service_registry.items()
            },
            "circuit_breakers": {
                service_id: {
                    "state": breaker.state,
                    "failure_count": breaker.failure_count,
                    "last_failure": breaker.last_failure_time.isoformat() if breaker.last_failure_time else None
                }
                for service_id, breaker in self.circuit_breakers.items()
            }
        }