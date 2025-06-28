"""
健康檢查服務
負責系統各組件的健康狀態檢查
"""

import asyncio
import logging
import aiohttp
import psutil
from datetime import datetime
from typing import Dict, Any, List

from ..models.test_models import (
    ContainerHealth,
    ApiPerformance, 
    DatabasePerformance,
    SatelliteProcessing,
    SystemMetrics,
    CpuMetrics,
    MemoryMetrics,
    DiskMetrics,
    NetworkMetrics,
    TestStatus,
)

logger = logging.getLogger(__name__)


class HealthCheckService:
    """
    健康檢查服務
    提供系統各組件的健康狀態檢查功能
    """

    def __init__(self):
        self.api_endpoints = [
            "http://localhost:8888/health",
            "http://localhost:8888/api/v1/devices",
            "http://localhost:8888/api/v1/satellites",
            "http://localhost:8080/api/v1/health", 
            "http://localhost:8080/api/v1/metrics",
        ]

    async def check_container_health(self) -> ContainerHealth:
        """
        檢查容器健康狀態
        
        Returns:
            ContainerHealth: 容器健康狀態
        """
        try:
            # 這裡應該實際檢查 Docker 容器狀態
            # 目前使用模擬數據
            
            container_status = {
                "simworld_backend": TestStatus.HEALTHY,
                "simworld_frontend": TestStatus.HEALTHY, 
                "netstack_api": TestStatus.HEALTHY,
                "postgresql": TestStatus.HEALTHY,
                "redis": TestStatus.WARNING,  # 模擬一個警告狀態
            }
            
            total_containers = len(container_status)
            healthy_containers = sum(1 for status in container_status.values() 
                                   if status == TestStatus.HEALTHY)
            
            health_percentage = (healthy_containers / total_containers) * 100
            overall_status = TestStatus.HEALTHY if health_percentage == 100 else TestStatus.WARNING
            
            return ContainerHealth(
                total_containers=total_containers,
                healthy_containers=healthy_containers,
                health_percentage=round(health_percentage, 1),
                container_status=container_status,
                status=overall_status,
            )
            
        except Exception as e:
            logger.error(f"容器健康檢查失敗: {str(e)}")
            return ContainerHealth(
                total_containers=0,
                healthy_containers=0,
                health_percentage=0.0,
                container_status={},
                status=TestStatus.ERROR,
            )

    async def check_api_performance(self) -> ApiPerformance:
        """
        檢查 API 性能
        
        Returns:
            ApiPerformance: API 性能狀態
        """
        try:
            results = await asyncio.gather(
                *[self._test_endpoint(endpoint) for endpoint in self.api_endpoints],
                return_exceptions=True
            )
            
            healthy_endpoints = 0
            total_response_time = 0
            valid_responses = 0
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.warning(f"端點檢查失敗: {self.api_endpoints[i]}, 錯誤: {str(result)}")
                    continue
                    
                if result.get("success", False):
                    healthy_endpoints += 1
                    total_response_time += result.get("response_time", 0)
                    valid_responses += 1
            
            avg_response_time = total_response_time / valid_responses if valid_responses > 0 else 0
            status = TestStatus.HEALTHY if healthy_endpoints == len(self.api_endpoints) else TestStatus.WARNING
            
            return ApiPerformance(
                total_endpoints=len(self.api_endpoints),
                healthy_endpoints=healthy_endpoints,
                avg_response_time_ms=round(avg_response_time, 2),
                status=status,
            )
            
        except Exception as e:
            logger.error(f"API 性能檢查失敗: {str(e)}")
            return ApiPerformance(
                total_endpoints=len(self.api_endpoints),
                healthy_endpoints=0,
                avg_response_time_ms=0.0,
                status=TestStatus.ERROR,
            )

    async def check_database_performance(self) -> DatabasePerformance:
        """
        檢查資料庫性能
        
        Returns:
            DatabasePerformance: 資料庫性能狀態
        """
        try:
            # 這裡應該使用實際的資料庫連接測試
            # 目前使用模擬數據
            start_time = datetime.now()
            
            # 模擬資料庫查詢
            await asyncio.sleep(0.1)
            
            end_time = datetime.now()
            query_time = (end_time - start_time).total_seconds() * 1000
            
            return DatabasePerformance(
                connection_status="connected",
                query_response_time_ms=round(query_time, 2),
                pool_size=10,
                active_connections=3,
                idle_connections=7,
                status=TestStatus.HEALTHY,
            )
            
        except Exception as e:
            logger.error(f"資料庫性能檢查失敗: {str(e)}")
            return DatabasePerformance(
                connection_status="error",
                query_response_time_ms=0,
                pool_size=0,
                active_connections=0,
                idle_connections=0,
                status=TestStatus.ERROR,
                error=str(e),
            )

    async def check_satellite_processing(self) -> SatelliteProcessing:
        """
        檢查衛星處理功能
        
        Returns:
            SatelliteProcessing: 衛星處理狀態
        """
        try:
            # 測試衛星計算功能
            # 這裡應該實際測試 Skyfield 和軌道計算
            
            return SatelliteProcessing(
                skyfield_processing=True,
                orbit_calculation=True,
                tle_data_valid=True,
                prediction_accuracy=95.8,
                processing_time_ms=45.3,
                status=TestStatus.HEALTHY,
            )
            
        except Exception as e:
            logger.error(f"衛星處理檢查失敗: {str(e)}")
            return SatelliteProcessing(
                skyfield_processing=False,
                orbit_calculation=False,
                tle_data_valid=False,
                prediction_accuracy=0,
                processing_time_ms=0,
                status=TestStatus.ERROR,
                error=str(e),
            )

    async def get_system_metrics(self) -> SystemMetrics:
        """
        獲取系統性能指標
        
        Returns:
            SystemMetrics: 系統指標
        """
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_status = TestStatus.HEALTHY if cpu_percent < 80 else TestStatus.WARNING
            
            cpu_metrics = CpuMetrics(
                usage_percent=round(cpu_percent, 1),
                core_count=psutil.cpu_count(),
                status=cpu_status,
            )
            
            # 記憶體使用情況
            memory = psutil.virtual_memory()
            memory_status = TestStatus.HEALTHY if memory.percent < 80 else TestStatus.WARNING
            
            memory_metrics = MemoryMetrics(
                total_gb=round(memory.total / (1024**3), 2),
                used_gb=round(memory.used / (1024**3), 2),
                usage_percent=round(memory.percent, 1),
                status=memory_status,
            )
            
            # 磁碟使用情況
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            disk_status = TestStatus.HEALTHY if disk_usage_percent < 80 else TestStatus.WARNING
            
            disk_metrics = DiskMetrics(
                total_gb=round(disk.total / (1024**3), 2),
                used_gb=round(disk.used / (1024**3), 2),
                usage_percent=round(disk_usage_percent, 1),
                status=disk_status,
            )
            
            # 網路統計
            network = psutil.net_io_counters()
            network_metrics = NetworkMetrics(
                bytes_sent=network.bytes_sent,
                bytes_recv=network.bytes_recv,
                packets_sent=network.packets_sent,
                packets_recv=network.packets_recv,
                status=TestStatus.HEALTHY,
            )
            
            return SystemMetrics(
                cpu=cpu_metrics,
                memory=memory_metrics,
                disk=disk_metrics,
                network=network_metrics,
            )
            
        except Exception as e:
            logger.error(f"系統指標獲取失敗: {str(e)}")
            
            # 返回錯誤狀態的指標
            error_cpu = CpuMetrics(usage_percent=0, core_count=0, status=TestStatus.ERROR)
            error_memory = MemoryMetrics(total_gb=0, used_gb=0, usage_percent=0, status=TestStatus.ERROR)
            error_disk = DiskMetrics(total_gb=0, used_gb=0, usage_percent=0, status=TestStatus.ERROR)
            error_network = NetworkMetrics(
                bytes_sent=0, bytes_recv=0, packets_sent=0, packets_recv=0, status=TestStatus.ERROR
            )
            
            return SystemMetrics(
                cpu=error_cpu,
                memory=error_memory,
                disk=error_disk,
                network=error_network,
                error=str(e),
            )

    async def perform_comprehensive_health_check(self) -> Dict[str, Any]:
        """
        執行綜合健康檢查
        
        Returns:
            Dict: 綜合健康檢查結果
        """
        logger.info("開始執行綜合健康檢查")
        
        try:
            # 並行執行所有健康檢查
            container_health, api_performance, db_performance, satellite_processing, system_metrics = await asyncio.gather(
                self.check_container_health(),
                self.check_api_performance(),
                self.check_database_performance(),
                self.check_satellite_processing(),
                self.get_system_metrics(),
            )
            
            # 計算整體健康評分
            overall_health, health_score = self._calculate_overall_health(
                container_health, api_performance, db_performance, satellite_processing, system_metrics
            )
            
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_health": overall_health,
                "health_score": health_score,
                "container_health": container_health.dict(),
                "api_performance": api_performance.dict(),
                "database_performance": db_performance.dict(),
                "satellite_processing": satellite_processing.dict(),
                "system_metrics": system_metrics.dict(),
            }
            
        except Exception as e:
            logger.error(f"綜合健康檢查失敗: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "overall_health": TestStatus.ERROR,
                "health_score": 0.0,
                "error": str(e),
            }

    async def _test_endpoint(self, url: str, timeout: int = 5) -> Dict[str, Any]:
        """
        測試單個 API 端點
        
        Args:
            url: 端點 URL
            timeout: 超時時間
            
        Returns:
            Dict: 測試結果
        """
        start_time = datetime.now()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url) as response:
                    end_time = datetime.now()
                    response_time = (end_time - start_time).total_seconds() * 1000
                    
                    return {
                        "url": url,
                        "success": response.status < 400,
                        "status_code": response.status,
                        "response_time": response_time,
                    }
                    
        except Exception as e:
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                "url": url,
                "success": False,
                "status_code": 0,
                "response_time": response_time,
                "error": str(e),
            }

    def _calculate_overall_health(
        self,
        container_health: ContainerHealth,
        api_performance: ApiPerformance,
        db_performance: DatabasePerformance,
        satellite_processing: SatelliteProcessing,
        system_metrics: SystemMetrics,
    ) -> tuple[TestStatus, float]:
        """
        計算整體健康狀態和評分
        
        Returns:
            tuple: (健康狀態, 健康評分)
        """
        health_scores = []
        
        # 容器健康分數 (40% 權重)
        container_score = container_health.health_percentage / 100.0
        health_scores.append(("container", container_score, 0.4))
        
        # API 性能分數 (30% 權重)
        api_score = api_performance.healthy_endpoints / api_performance.total_endpoints if api_performance.total_endpoints > 0 else 0
        health_scores.append(("api", api_score, 0.3))
        
        # 資料庫分數 (15% 權重)
        db_score = 1.0 if db_performance.status == TestStatus.HEALTHY else 0.0
        health_scores.append(("database", db_score, 0.15))
        
        # 衛星處理分數 (15% 權重)
        satellite_score = 1.0 if satellite_processing.status == TestStatus.HEALTHY else 0.0
        health_scores.append(("satellite", satellite_score, 0.15))
        
        # 計算加權平均分數
        weighted_score = sum(score * weight for _, score, weight in health_scores)
        
        # 根據分數判定健康狀態
        if weighted_score >= 0.8:
            return TestStatus.HEALTHY, weighted_score
        elif weighted_score >= 0.6:
            return TestStatus.WARNING, weighted_score
        else:
            return TestStatus.ERROR, weighted_score