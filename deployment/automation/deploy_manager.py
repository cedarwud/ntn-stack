#!/usr/bin/env python3
"""
部署自動化管理器
提供一鍵部署、回滾和監控功能

根據 TODO.md 第18項「部署流程優化與自動化」要求設計
"""

import asyncio
import subprocess
import time
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import docker
import requests

from deployment.config_manager import (
    config_manager,
    DeploymentConfig,
    DeploymentEnvironment,
    ServiceType,
)

logger = logging.getLogger(__name__)


class DeploymentStatus(str, Enum):
    """部署狀態"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class HealthCheckStatus(str, Enum):
    """健康檢查狀態"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ServiceHealthInfo:
    """服務健康資訊"""

    service_name: str
    status: HealthCheckStatus
    response_time_ms: float
    last_check: datetime
    error_message: Optional[str] = None
    endpoints_checked: List[str] = None

    def __post_init__(self):
        if self.endpoints_checked is None:
            self.endpoints_checked = []


@dataclass
class DeploymentRecord:
    """部署記錄"""

    deployment_id: str
    config: DeploymentConfig
    status: DeploymentStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    services_deployed: List[str] = None
    error_message: Optional[str] = None
    rollback_available: bool = False
    health_check_results: List[ServiceHealthInfo] = None

    def __post_init__(self):
        if self.services_deployed is None:
            self.services_deployed = []
        if self.health_check_results is None:
            self.health_check_results = []

    @property
    def duration_seconds(self) -> Optional[float]:
        """部署持續時間（秒）"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class DockerHealthChecker:
    """Docker 健康檢查器"""

    def __init__(self):
        self.client = docker.from_env()

    async def check_container_health(self, container_name: str) -> ServiceHealthInfo:
        """檢查容器健康狀態"""
        start_time = time.time()

        try:
            container = self.client.containers.get(container_name)

            # 檢查容器狀態
            if container.status != "running":
                return ServiceHealthInfo(
                    service_name=container_name,
                    status=HealthCheckStatus.UNHEALTHY,
                    response_time_ms=(time.time() - start_time) * 1000,
                    last_check=datetime.utcnow(),
                    error_message=f"Container not running: {container.status}",
                )

            # 檢查健康檢查狀態
            health = container.attrs.get("State", {}).get("Health", {})
            if health:
                health_status = health.get("Status", "unknown")
                if health_status == "healthy":
                    status = HealthCheckStatus.HEALTHY
                elif health_status == "unhealthy":
                    status = HealthCheckStatus.UNHEALTHY
                else:
                    status = HealthCheckStatus.UNKNOWN
            else:
                # 沒有健康檢查配置，假設容器運行即健康
                status = HealthCheckStatus.HEALTHY

            return ServiceHealthInfo(
                service_name=container_name,
                status=status,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.utcnow(),
            )

        except docker.errors.NotFound:
            return ServiceHealthInfo(
                service_name=container_name,
                status=HealthCheckStatus.UNHEALTHY,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.utcnow(),
                error_message="Container not found",
            )
        except Exception as e:
            return ServiceHealthInfo(
                service_name=container_name,
                status=HealthCheckStatus.UNHEALTHY,
                response_time_ms=(time.time() - start_time) * 1000,
                last_check=datetime.utcnow(),
                error_message=str(e),
            )

    async def check_service_endpoints(
        self, service_name: str, endpoints: List[str]
    ) -> ServiceHealthInfo:
        """檢查服務端點健康狀態"""
        start_time = time.time()
        checked_endpoints = []
        errors = []

        for endpoint in endpoints:
            try:
                response = requests.get(endpoint, timeout=10)
                checked_endpoints.append(f"{endpoint} -> {response.status_code}")

                if response.status_code >= 400:
                    errors.append(f"{endpoint}: HTTP {response.status_code}")

            except Exception as e:
                checked_endpoints.append(f"{endpoint} -> ERROR")
                errors.append(f"{endpoint}: {str(e)}")

        # 判斷整體健康狀態
        if not errors:
            status = HealthCheckStatus.HEALTHY
        elif len(errors) < len(endpoints):
            status = HealthCheckStatus.UNKNOWN  # 部分端點有問題
        else:
            status = HealthCheckStatus.UNHEALTHY  # 所有端點都有問題

        return ServiceHealthInfo(
            service_name=service_name,
            status=status,
            response_time_ms=(time.time() - start_time) * 1000,
            last_check=datetime.utcnow(),
            endpoints_checked=checked_endpoints,
            error_message="; ".join(errors) if errors else None,
        )


class DeploymentAutomation:
    """部署自動化管理器"""

    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.deployment_history: List[DeploymentRecord] = []
        self.health_checker = DockerHealthChecker()
        self.deployment_dir = self.workspace_root / "deployment"
        self.logs_dir = self.deployment_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # 服務端點配置
        self.service_endpoints = {
            ServiceType.NETSTACK: [
                "http://localhost:8080/health",
                "http://localhost:8080/api/v1/status",
            ],
            ServiceType.SIMWORLD: ["http://localhost:8888/", "http://localhost:5173/"],
        }

    def generate_deployment_id(self) -> str:
        """生成部署ID"""
        return f"deploy_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    async def pre_deployment_checks(
        self, config: DeploymentConfig
    ) -> Tuple[bool, List[str]]:
        """部署前檢查"""
        logger.info("🔍 執行部署前檢查...")

        checks_passed = True
        issues = []

        # 1. 配置驗證
        validation_results = config_manager.validate_configuration(config)
        if validation_results["config_errors"]:
            checks_passed = False
            issues.extend(
                [f"配置錯誤: {error}" for error in validation_results["config_errors"]]
            )

        if validation_results["file_errors"]:
            checks_passed = False
            issues.extend(
                [f"文件錯誤: {error}" for error in validation_results["file_errors"]]
            )

        # 2. Docker 可用性檢查
        try:
            client = docker.from_env()
            client.ping()
        except Exception as e:
            checks_passed = False
            issues.append(f"Docker 不可用: {e}")

        # 3. 磁碟空間檢查
        import shutil

        disk_usage = shutil.disk_usage(self.workspace_root)
        free_gb = disk_usage.free / (1024**3)
        if free_gb < 5:  # 至少需要5GB可用空間
            checks_passed = False
            issues.append(f"磁碟空間不足: 僅剩 {free_gb:.1f}GB")

        # 4. 端口可用性檢查
        await self._check_port_availability(config, issues)

        if not checks_passed:
            logger.error(f"❌ 部署前檢查失敗: {len(issues)} 個問題")
            for issue in issues:
                logger.error(f"  - {issue}")
        else:
            logger.info("✅ 部署前檢查通過")

        return checks_passed, issues

    async def _check_port_availability(
        self, config: DeploymentConfig, issues: List[str]
    ):
        """檢查端口可用性"""
        import socket

        # 根據服務類型檢查相應端口
        ports_to_check = []

        if config.service_type == ServiceType.NETSTACK:
            ports_to_check = [8080, 27017]  # API端口和MongoDB端口
        elif config.service_type == ServiceType.SIMWORLD:
            ports_to_check = [8888, 5173, 5432]  # Backend, Frontend, PostgreSQL端口

        for port in ports_to_check:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(("localhost", port))
                sock.close()

                if result == 0:
                    issues.append(f"端口 {port} 已被佔用")
            except Exception:
                pass  # 端口檢查失敗不算嚴重問題

    async def deploy_service(
        self, config: DeploymentConfig, force: bool = False
    ) -> DeploymentRecord:
        """部署服務"""
        deployment_id = self.generate_deployment_id()

        record = DeploymentRecord(
            deployment_id=deployment_id,
            config=config,
            status=DeploymentStatus.PENDING,
            start_time=datetime.utcnow(),
        )

        self.deployment_history.append(record)

        try:
            logger.info(
                f"🚀 開始部署 {config.service_type.value} ({config.environment.value})"
            )

            # 1. 部署前檢查
            if not force:
                checks_passed, issues = await self.pre_deployment_checks(config)
                if not checks_passed:
                    record.status = DeploymentStatus.FAILED
                    record.error_message = f"部署前檢查失敗: {'; '.join(issues)}"
                    record.end_time = datetime.utcnow()
                    return record

            record.status = DeploymentStatus.IN_PROGRESS

            # 2. 生成配置文件
            compose_file = config_manager.generate_docker_compose(config)
            env_file = config_manager.generate_env_file(config)

            logger.info(f"📝 配置文件已生成: {compose_file}")

            # 3. 停止現有服務（如果存在）
            await self._stop_existing_services(config)

            # 4. 啟動服務
            success = await self._start_services(config, compose_file)

            if success:
                # 5. 健康檢查
                await asyncio.sleep(10)  # 等待服務啟動
                health_results = await self._perform_health_checks(config)
                record.health_check_results = health_results

                # 判斷部署是否成功
                healthy_services = [
                    h for h in health_results if h.status == HealthCheckStatus.HEALTHY
                ]
                if (
                    len(healthy_services) >= len(health_results) * 0.8
                ):  # 80%服務健康即視為成功
                    record.status = DeploymentStatus.SUCCESS
                    record.rollback_available = True
                    logger.info(f"✅ 部署成功: {deployment_id}")
                else:
                    record.status = DeploymentStatus.FAILED
                    record.error_message = "健康檢查失敗"
                    logger.error(f"❌ 部署失敗: 健康檢查不通過")
            else:
                record.status = DeploymentStatus.FAILED
                record.error_message = "服務啟動失敗"
                logger.error(f"❌ 部署失敗: 服務啟動失敗")

        except Exception as e:
            record.status = DeploymentStatus.FAILED
            record.error_message = str(e)
            logger.error(f"❌ 部署異常: {e}")

        finally:
            record.end_time = datetime.utcnow()
            await self._save_deployment_log(record)

        return record

    async def _stop_existing_services(self, config: DeploymentConfig):
        """停止現有服務"""
        try:
            if config.service_type == ServiceType.NETSTACK:
                cmd = ["make", "-C", str(self.workspace_root), "netstack-stop"]
            else:
                cmd = ["make", "-C", str(self.workspace_root), "simworld-stop"]

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.warning(f"停止現有服務時出現警告: {stderr.decode()}")
            else:
                logger.info("🛑 現有服務已停止")

        except Exception as e:
            logger.warning(f"停止現有服務失敗: {e}")

    async def _start_services(
        self, config: DeploymentConfig, compose_file: str
    ) -> bool:
        """啟動服務"""
        try:
            # 切換到對應的服務目錄
            if config.service_type == ServiceType.NETSTACK:
                service_dir = self.workspace_root / "netstack"
                cmd = ["docker", "compose", "-f", compose_file, "up", "-d"]
            else:
                service_dir = self.workspace_root / "simworld"
                cmd = ["docker", "compose", "-f", compose_file, "up", "-d"]

            logger.info(f"🔄 執行啟動命令: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=service_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logger.info("✅ 服務啟動成功")
                return True
            else:
                logger.error(f"❌ 服務啟動失敗: {stderr.decode()}")
                return False

        except Exception as e:
            logger.error(f"❌ 啟動服務異常: {e}")
            return False

    async def _perform_health_checks(
        self, config: DeploymentConfig
    ) -> List[ServiceHealthInfo]:
        """執行健康檢查"""
        logger.info("🏥 執行健康檢查...")

        health_results = []

        # 容器健康檢查
        if config.service_type == ServiceType.NETSTACK:
            containers = ["netstack-mongo", "netstack-nrf", "netstack-api"]
        else:
            containers = ["simworld_postgis", "simworld_backend", "simworld_frontend"]

        for container in containers:
            health_info = await self.health_checker.check_container_health(container)
            health_results.append(health_info)

        # 端點健康檢查
        endpoints = self.service_endpoints.get(config.service_type, [])
        if endpoints:
            endpoint_health = await self.health_checker.check_service_endpoints(
                f"{config.service_type.value}_endpoints", endpoints
            )
            health_results.append(endpoint_health)

        # 記錄健康檢查結果
        healthy_count = len(
            [h for h in health_results if h.status == HealthCheckStatus.HEALTHY]
        )
        logger.info(f"🏥 健康檢查完成: {healthy_count}/{len(health_results)} 服務健康")

        for result in health_results:
            status_emoji = "✅" if result.status == HealthCheckStatus.HEALTHY else "❌"
            logger.info(
                f"  {status_emoji} {result.service_name}: {result.status.value}"
            )
            if result.error_message:
                logger.warning(f"    錯誤: {result.error_message}")

        return health_results

    async def rollback_deployment(self, deployment_id: str) -> bool:
        """回滾部署"""
        logger.info(f"🔄 開始回滾部署: {deployment_id}")

        # 找到要回滾的部署記錄
        target_record = None
        for record in self.deployment_history:
            if record.deployment_id == deployment_id:
                target_record = record
                break

        if not target_record:
            logger.error(f"❌ 找不到部署記錄: {deployment_id}")
            return False

        if not target_record.rollback_available:
            logger.error(f"❌ 部署 {deployment_id} 不支援回滾")
            return False

        try:
            # 停止當前服務
            await self._stop_existing_services(target_record.config)

            # 找到上一個成功的部署
            previous_success = None
            for record in reversed(self.deployment_history):
                if (
                    record.config.service_type == target_record.config.service_type
                    and record.status == DeploymentStatus.SUCCESS
                    and record.deployment_id != deployment_id
                ):
                    previous_success = record
                    break

            if previous_success:
                # 重新部署上一個成功的配置
                logger.info(f"🔄 回滾到部署: {previous_success.deployment_id}")
                rollback_record = await self.deploy_service(
                    previous_success.config, force=True
                )

                if rollback_record.status == DeploymentStatus.SUCCESS:
                    target_record.status = DeploymentStatus.ROLLED_BACK
                    logger.info(f"✅ 回滾成功")
                    return True
                else:
                    logger.error(f"❌ 回滾失敗")
                    return False
            else:
                logger.error(f"❌ 找不到可回滾的版本")
                return False

        except Exception as e:
            logger.error(f"❌ 回滾異常: {e}")
            return False

    async def _save_deployment_log(self, record: DeploymentRecord):
        """保存部署日誌"""
        try:
            log_file = self.logs_dir / f"{record.deployment_id}.json"

            # 將記錄轉換為可序列化的格式
            log_data = {
                "deployment_id": record.deployment_id,
                "config": record.config.to_dict(),
                "status": record.status.value,
                "start_time": record.start_time.isoformat(),
                "end_time": record.end_time.isoformat() if record.end_time else None,
                "duration_seconds": record.duration_seconds,
                "services_deployed": record.services_deployed,
                "error_message": record.error_message,
                "rollback_available": record.rollback_available,
                "health_check_results": [
                    {
                        "service_name": h.service_name,
                        "status": h.status.value,
                        "response_time_ms": h.response_time_ms,
                        "last_check": h.last_check.isoformat(),
                        "error_message": h.error_message,
                        "endpoints_checked": h.endpoints_checked,
                    }
                    for h in record.health_check_results
                ],
            }

            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)

            logger.info(f"📝 部署日誌已保存: {log_file}")

        except Exception as e:
            logger.error(f"保存部署日誌失敗: {e}")

    def get_deployment_status(self, deployment_id: str) -> Optional[DeploymentRecord]:
        """獲取部署狀態"""
        for record in self.deployment_history:
            if record.deployment_id == deployment_id:
                return record
        return None

    def list_deployments(
        self, service_type: Optional[ServiceType] = None, limit: int = 10
    ) -> List[DeploymentRecord]:
        """列出部署記錄"""
        filtered_records = self.deployment_history

        if service_type:
            filtered_records = [
                r for r in filtered_records if r.config.service_type == service_type
            ]

        # 按時間倒序排列
        sorted_records = sorted(
            filtered_records, key=lambda x: x.start_time, reverse=True
        )

        return sorted_records[:limit]

    async def monitor_services(
        self, config: DeploymentConfig, duration_minutes: int = 10
    ) -> List[ServiceHealthInfo]:
        """監控服務健康狀態"""
        logger.info(
            f"📊 開始監控 {config.service_type.value} 服務 {duration_minutes} 分鐘"
        )

        end_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
        health_history = []

        while datetime.utcnow() < end_time:
            health_results = await self._perform_health_checks(config)
            health_history.extend(health_results)

            # 檢查是否有服務不健康
            unhealthy_services = [
                h for h in health_results if h.status == HealthCheckStatus.UNHEALTHY
            ]
            if unhealthy_services:
                logger.warning(
                    f"⚠️ 發現不健康的服務: {[s.service_name for s in unhealthy_services]}"
                )

            await asyncio.sleep(30)  # 每30秒檢查一次

        logger.info(f"📊 監控完成")
        return health_history


# 全局部署管理器實例
deployment_manager = DeploymentAutomation()
