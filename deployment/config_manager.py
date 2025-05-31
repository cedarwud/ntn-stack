#!/usr/bin/env python3
"""
部署配置管理器
負責環境變數配置模板和驗證功能

根據 TODO.md 第18項「部署流程優化與自動化」要求設計
"""

import os
import yaml
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from jinja2 import Template, Environment, FileSystemLoader
import ipaddress
import socket

logger = logging.getLogger(__name__)


class DeploymentEnvironment(str, Enum):
    """部署環境類型"""

    DEVELOPMENT = "development"
    TESTING = "testing"
    LABORATORY = "laboratory"
    PRODUCTION = "production"
    FIELD = "field"  # 戶外實地測試


class ServiceType(str, Enum):
    """服務類型"""

    NETSTACK = "netstack"
    SIMWORLD = "simworld"
    MONITORING = "monitoring"


@dataclass
class NetworkConfig:
    """網路配置"""

    subnet: str = "172.20.0.0/16"
    gateway: str = "172.20.0.1"
    netstack_range: str = "172.20.0.10-172.20.0.50"
    simworld_range: str = "172.20.0.60-172.20.0.90"

    def validate(self) -> List[str]:
        """驗證網路配置"""
        errors = []
        try:
            network = ipaddress.IPv4Network(self.subnet, strict=False)
            gateway_ip = ipaddress.IPv4Address(self.gateway)
            if gateway_ip not in network:
                errors.append(f"Gateway {self.gateway} not in subnet {self.subnet}")
        except Exception as e:
            errors.append(f"Invalid network configuration: {e}")
        return errors


@dataclass
class ResourceLimits:
    """資源限制配置"""

    cpu_limit: str = "2"
    memory_limit: str = "2G"
    storage_limit: str = "10G"

    def validate(self) -> List[str]:
        """驗證資源限制"""
        errors = []
        # 驗證CPU限制格式
        if not re.match(r"^[0-9]+(\.[0-9]+)?$", self.cpu_limit):
            errors.append(f"Invalid CPU limit format: {self.cpu_limit}")

        # 驗證內存限制格式
        if not re.match(r"^[0-9]+[KMGT]?$", self.memory_limit):
            errors.append(f"Invalid memory limit format: {self.memory_limit}")

        return errors


@dataclass
class DeploymentConfig:
    """部署配置"""

    environment: DeploymentEnvironment
    service_type: ServiceType
    network: NetworkConfig
    resources: ResourceLimits
    gpu_enabled: bool = False
    backup_enabled: bool = True
    monitoring_enabled: bool = True
    health_check_enabled: bool = True
    custom_vars: Dict[str, Any] = None

    def __post_init__(self):
        if self.custom_vars is None:
            self.custom_vars = {}

    def to_dict(self) -> Dict:
        """轉換為字典"""
        return asdict(self)

    def validate(self) -> List[str]:
        """驗證配置"""
        errors = []

        # 驗證網路配置
        errors.extend(self.network.validate())

        # 驗證資源配置
        errors.extend(self.resources.validate())

        # 特定環境驗證
        if self.environment == DeploymentEnvironment.FIELD:
            if not self.backup_enabled:
                errors.append("Backup must be enabled for field deployment")
            if not self.monitoring_enabled:
                errors.append("Monitoring must be enabled for field deployment")

        return errors


class ConfigTemplateEngine:
    """配置模板引擎"""

    def __init__(self, template_dir: str = "deployment/templates"):
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # 註冊自定義過濾器
        self.env.filters["to_yaml"] = self._to_yaml
        self.env.filters["to_json"] = self._to_json

    def _to_yaml(self, value):
        """轉換為YAML格式"""
        return yaml.dump(value, default_flow_style=False)

    def _to_json(self, value):
        """轉換為JSON格式"""
        return json.dumps(value, indent=2)

    def render_template(self, template_name: str, config: DeploymentConfig) -> str:
        """渲染配置模板"""
        try:
            template = self.env.get_template(template_name)
            return template.render(config=config, **config.to_dict())
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            raise


class ConfigValidator:
    """配置驗證器"""

    @staticmethod
    def validate_port(port: Union[str, int]) -> bool:
        """驗證端口號"""
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_hostname(hostname: str) -> bool:
        """驗證主機名"""
        if not hostname:
            return False

        # 檢查長度
        if len(hostname) > 253:
            return False

        # 檢查格式
        pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
        return bool(re.match(pattern, hostname))

    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """驗證IP地址"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_network_connectivity(host: str, port: int, timeout: int = 5) -> bool:
        """驗證網路連接性"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False

    @classmethod
    def validate_docker_compose_config(cls, config_file: str) -> List[str]:
        """驗證Docker Compose配置"""
        errors = []

        try:
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)

            # 檢查必要的頂級鍵
            required_keys = ["services"]
            for key in required_keys:
                if key not in config:
                    errors.append(f"Missing required key: {key}")

            # 檢查服務配置
            if "services" in config:
                for service_name, service_config in config["services"].items():
                    # 檢查端口配置
                    if "ports" in service_config:
                        for port_mapping in service_config["ports"]:
                            if ":" in str(port_mapping):
                                host_port, container_port = str(port_mapping).split(":")
                                if not cls.validate_port(
                                    host_port
                                ) or not cls.validate_port(container_port):
                                    errors.append(
                                        f"Invalid port mapping in service {service_name}: {port_mapping}"
                                    )

                    # 檢查環境變數
                    if "environment" in service_config:
                        env_vars = service_config["environment"]
                        if isinstance(env_vars, dict):
                            for key, value in env_vars.items():
                                if key.endswith("_HOST") and value:
                                    if not cls.validate_hostname(
                                        str(value)
                                    ) and not cls.validate_ip_address(str(value)):
                                        errors.append(
                                            f"Invalid hostname/IP in service {service_name}: {key}={value}"
                                        )

                    # 檢查網路配置
                    if "networks" in service_config:
                        networks = service_config["networks"]
                        if isinstance(networks, dict):
                            for network_name, network_config in networks.items():
                                if (
                                    isinstance(network_config, dict)
                                    and "ipv4_address" in network_config
                                ):
                                    if not cls.validate_ip_address(
                                        network_config["ipv4_address"]
                                    ):
                                        errors.append(
                                            f"Invalid IP address in service {service_name}: {network_config['ipv4_address']}"
                                        )

        except yaml.YAMLError as e:
            errors.append(f"Invalid YAML syntax: {e}")
        except FileNotFoundError:
            errors.append(f"Configuration file not found: {config_file}")
        except Exception as e:
            errors.append(f"Validation error: {e}")

        return errors


class ConfigManager:
    """配置管理器主類"""

    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.deployment_dir = self.workspace_root / "deployment"
        self.templates_dir = self.deployment_dir / "templates"
        self.configs_dir = self.deployment_dir / "configs"
        self.template_engine = ConfigTemplateEngine(str(self.templates_dir))
        self.validator = ConfigValidator()

        # 確保目錄存在
        self.deployment_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        self.configs_dir.mkdir(exist_ok=True)

    def create_default_config(
        self, environment: DeploymentEnvironment, service_type: ServiceType
    ) -> DeploymentConfig:
        """創建預設配置"""
        # 根據環境和服務類型調整配置
        config = DeploymentConfig(
            environment=environment,
            service_type=service_type,
            network=NetworkConfig(),
            resources=ResourceLimits(),
        )

        # 環境特定調整
        if environment == DeploymentEnvironment.PRODUCTION:
            config.resources.cpu_limit = "4"
            config.resources.memory_limit = "4G"
            config.gpu_enabled = True
        elif environment == DeploymentEnvironment.FIELD:
            config.resources.cpu_limit = "3"
            config.resources.memory_limit = "3G"
            config.backup_enabled = True
            config.monitoring_enabled = True
        elif environment == DeploymentEnvironment.DEVELOPMENT:
            config.resources.cpu_limit = "1"
            config.resources.memory_limit = "1G"
            config.gpu_enabled = False

        # 服務特定調整
        if service_type == ServiceType.SIMWORLD:
            config.gpu_enabled = True  # SimWorld通常需要GPU
            config.custom_vars.update(
                {
                    "CUDA_VISIBLE_DEVICES": "0" if config.gpu_enabled else "-1",
                    "PYOPENGL_PLATFORM": "egl",
                    "POSTGRES_USER": "simworld_user",
                    "POSTGRES_PASSWORD": "simworld_pass",
                    "POSTGRES_DB": "simworld_db",
                }
            )
        elif service_type == ServiceType.NETSTACK:
            config.custom_vars.update(
                {
                    "MONGO_INITDB_DATABASE": "open5gs",
                    "DB_URI": "mongodb://mongo/open5gs",
                }
            )

        return config

    def save_config(self, config: DeploymentConfig, filename: str) -> str:
        """保存配置到文件"""
        config_path = self.configs_dir / filename

        with open(config_path, "w") as f:
            yaml.dump(config.to_dict(), f, default_flow_style=False)

        logger.info(f"Configuration saved to {config_path}")
        return str(config_path)

    def load_config(self, filename: str) -> DeploymentConfig:
        """從文件載入配置"""
        config_path = self.configs_dir / filename

        with open(config_path, "r") as f:
            data = yaml.safe_load(f)

        # 重建對象
        network = NetworkConfig(**data.get("network", {}))
        resources = ResourceLimits(**data.get("resources", {}))

        config = DeploymentConfig(
            environment=DeploymentEnvironment(data["environment"]),
            service_type=ServiceType(data["service_type"]),
            network=network,
            resources=resources,
            gpu_enabled=data.get("gpu_enabled", False),
            backup_enabled=data.get("backup_enabled", True),
            monitoring_enabled=data.get("monitoring_enabled", True),
            health_check_enabled=data.get("health_check_enabled", True),
            custom_vars=data.get("custom_vars", {}),
        )

        return config

    def generate_docker_compose(self, config: DeploymentConfig) -> str:
        """生成Docker Compose配置"""
        template_name = f"{config.service_type.value}-compose.yaml.j2"

        try:
            compose_content = self.template_engine.render_template(
                template_name, config
            )

            # 保存生成的配置
            output_path = (
                self.configs_dir
                / f"{config.service_type.value}-{config.environment.value}-compose.yaml"
            )
            with open(output_path, "w") as f:
                f.write(compose_content)

            logger.info(f"Docker Compose configuration generated: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to generate Docker Compose configuration: {e}")
            raise

    def generate_env_file(self, config: DeploymentConfig) -> str:
        """生成環境變數文件"""
        env_content = []

        # 基本環境變數
        env_content.append(f"# Generated for {config.environment.value} environment")
        env_content.append(f"DEPLOYMENT_ENV={config.environment.value}")
        env_content.append(f"SERVICE_TYPE={config.service_type.value}")
        env_content.append(f"GPU_ENABLED={str(config.gpu_enabled).lower()}")

        # 網路配置
        env_content.append(f"NETWORK_SUBNET={config.network.subnet}")
        env_content.append(f"NETWORK_GATEWAY={config.network.gateway}")

        # 資源限制
        env_content.append(f"CPU_LIMIT={config.resources.cpu_limit}")
        env_content.append(f"MEMORY_LIMIT={config.resources.memory_limit}")
        env_content.append(f"STORAGE_LIMIT={config.resources.storage_limit}")

        # 自定義變數
        for key, value in config.custom_vars.items():
            env_content.append(f"{key}={value}")

        # 保存環境變數文件
        env_path = (
            self.configs_dir
            / f"{config.service_type.value}-{config.environment.value}.env"
        )
        with open(env_path, "w") as f:
            f.write("\n".join(env_content))

        logger.info(f"Environment file generated: {env_path}")
        return str(env_path)

    def validate_configuration(self, config: DeploymentConfig) -> Dict[str, List[str]]:
        """驗證部署配置"""
        validation_results = {"config_errors": config.validate(), "file_errors": []}

        # 如果配置已生成文件，驗證文件
        compose_file = (
            self.configs_dir
            / f"{config.service_type.value}-{config.environment.value}-compose.yaml"
        )
        if compose_file.exists():
            validation_results["file_errors"] = (
                self.validator.validate_docker_compose_config(str(compose_file))
            )

        return validation_results

    def list_configurations(self) -> List[Dict[str, str]]:
        """列出所有配置文件"""
        configs = []

        for config_file in self.configs_dir.glob("*.yaml"):
            if not config_file.name.endswith("-compose.yaml"):
                try:
                    config = self.load_config(config_file.name)
                    configs.append(
                        {
                            "filename": config_file.name,
                            "environment": config.environment.value,
                            "service_type": config.service_type.value,
                            "created": config_file.stat().st_mtime,
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to load config {config_file.name}: {e}")

        return sorted(configs, key=lambda x: x["created"], reverse=True)


# 全局配置管理器實例
config_manager = ConfigManager()
