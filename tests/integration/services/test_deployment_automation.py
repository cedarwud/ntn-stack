#!/usr/bin/env python3
"""
部署自動化測試程式
測試所有核心功能，確保100%通過

根據 TODO.md 第18項「部署流程優化與自動化」要求設計
"""

import pytest
import asyncio
import tempfile
import shutil
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import sys

# 添加項目根路徑到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from deployment.config_manager import (
    ConfigManager,
    DeploymentConfig,
    DeploymentEnvironment,
    ServiceType,
    NetworkConfig,
    ResourceLimits,
    ConfigValidator,
)

from deployment.automation.deploy_manager import (
    DeploymentAutomation,
    DeploymentStatus,
    DeploymentRecord,
    DockerHealthChecker,
    HealthCheckStatus,
)

from deployment.backup.backup_manager import (
    BackupManager,
    BackupType,
    BackupStatus,
    BackupRecord,
)


class TestConfigManager:
    """配置管理器測試"""

    @pytest.fixture
    def temp_workspace(self):
        """創建臨時工作空間"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def config_manager(self, temp_workspace):
        """創建配置管理器實例"""
        return ConfigManager(temp_workspace)

    def test_create_default_config_netstack_development(self, config_manager):
        """測試創建NetStack開發環境配置"""
        config = config_manager.create_default_config(
            DeploymentEnvironment.DEVELOPMENT, ServiceType.NETSTACK
        )

        assert config.environment == DeploymentEnvironment.DEVELOPMENT
        assert config.service_type == ServiceType.NETSTACK
        assert config.resources.cpu_limit == "1"
        assert config.resources.memory_limit == "1G"
        assert not config.gpu_enabled
        assert "MONGO_INITDB_DATABASE" in config.custom_vars
        assert "DB_URI" in config.custom_vars

    def test_create_default_config_simworld_production(self, config_manager):
        """測試創建SimWorld生產環境配置"""
        config = config_manager.create_default_config(
            DeploymentEnvironment.PRODUCTION, ServiceType.SIMWORLD
        )

        assert config.environment == DeploymentEnvironment.PRODUCTION
        assert config.service_type == ServiceType.SIMWORLD
        assert config.resources.cpu_limit == "4"
        assert config.resources.memory_limit == "4G"
        assert config.gpu_enabled
        assert "CUDA_VISIBLE_DEVICES" in config.custom_vars
        assert "POSTGRES_USER" in config.custom_vars

    def test_save_and_load_config(self, config_manager):
        """測試保存和載入配置"""
        original_config = config_manager.create_default_config(
            DeploymentEnvironment.TESTING, ServiceType.NETSTACK
        )

        # 保存配置
        config_path = config_manager.save_config(original_config, "test_config.yaml")
        assert Path(config_path).exists()

        # 載入配置
        loaded_config = config_manager.load_config("test_config.yaml")

        assert loaded_config.environment == original_config.environment
        assert loaded_config.service_type == original_config.service_type
        assert loaded_config.gpu_enabled == original_config.gpu_enabled

    def test_network_config_validation(self):
        """測試網路配置驗證"""
        # 有效配置
        valid_config = NetworkConfig(subnet="172.20.0.0/16", gateway="172.20.0.1")
        errors = valid_config.validate()
        assert len(errors) == 0

        # 無效配置 - 網關不在子網內
        invalid_config = NetworkConfig(subnet="172.20.0.0/16", gateway="192.168.1.1")
        errors = invalid_config.validate()
        assert len(errors) > 0
        assert "Gateway" in errors[0]

    def test_resource_limits_validation(self):
        """測試資源限制驗證"""
        # 有效配置
        valid_limits = ResourceLimits(cpu_limit="2.5", memory_limit="4G")
        errors = valid_limits.validate()
        assert len(errors) == 0

        # 無效配置
        invalid_limits = ResourceLimits(cpu_limit="invalid", memory_limit="invalid")
        errors = invalid_limits.validate()
        assert len(errors) == 2

    def test_generate_docker_compose(self, config_manager):
        """測試生成Docker Compose配置"""
        config = config_manager.create_default_config(
            DeploymentEnvironment.DEVELOPMENT, ServiceType.NETSTACK
        )

        with patch.object(
            config_manager.template_engine, "render_template"
        ) as mock_render:
            mock_render.return_value = "mock compose content"

            compose_path = config_manager.generate_docker_compose(config)

            mock_render.assert_called_once()
            assert Path(compose_path).exists()

    def test_generate_env_file(self, config_manager):
        """測試生成環境變數文件"""
        config = config_manager.create_default_config(
            DeploymentEnvironment.DEVELOPMENT, ServiceType.NETSTACK
        )

        env_path = config_manager.generate_env_file(config)

        assert Path(env_path).exists()

        # 檢查文件內容
        with open(env_path, "r") as f:
            content = f.read()

        assert "DEPLOYMENT_ENV=development" in content
        assert "SERVICE_TYPE=netstack" in content
        assert "GPU_ENABLED=false" in content


class TestConfigValidator:
    """配置驗證器測試"""

    def test_validate_port(self):
        """測試端口驗證"""
        assert ConfigValidator.validate_port(80)
        assert ConfigValidator.validate_port("8080")
        assert not ConfigValidator.validate_port(0)
        assert not ConfigValidator.validate_port(70000)
        assert not ConfigValidator.validate_port("invalid")

    def test_validate_hostname(self):
        """測試主機名驗證"""
        assert ConfigValidator.validate_hostname("localhost")
        assert ConfigValidator.validate_hostname("api.example.com")
        assert not ConfigValidator.validate_hostname("")
        assert not ConfigValidator.validate_hostname("a" * 300)

    def test_validate_ip_address(self):
        """測試IP地址驗證"""
        assert ConfigValidator.validate_ip_address("192.168.1.1")
        assert ConfigValidator.validate_ip_address("127.0.0.1")
        assert not ConfigValidator.validate_ip_address("invalid.ip")
        assert not ConfigValidator.validate_ip_address("999.999.999.999")

    def test_validate_docker_compose_config(self, tmp_path):
        """測試Docker Compose配置驗證"""
        # 有效配置
        valid_config = {
            "services": {
                "web": {"ports": ["8080:80"], "environment": {"DB_HOST": "localhost"}}
            }
        }

        config_file = tmp_path / "valid_compose.yaml"
        with open(config_file, "w") as f:
            yaml.dump(valid_config, f)

        errors = ConfigValidator.validate_docker_compose_config(str(config_file))
        assert len(errors) == 0

        # 無效配置
        invalid_config = {
            "services": {
                "web": {
                    "ports": ["invalid:port"],
                    "environment": {"DB_HOST": "invalid..hostname"},
                }
            }
        }

        invalid_config_file = tmp_path / "invalid_compose.yaml"
        with open(invalid_config_file, "w") as f:
            yaml.dump(invalid_config, f)

        errors = ConfigValidator.validate_docker_compose_config(
            str(invalid_config_file)
        )
        assert len(errors) > 0


class TestDeploymentAutomation:
    """部署自動化測試"""

    @pytest.fixture
    def temp_workspace(self):
        """創建臨時工作空間"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def deployment_manager(self, temp_workspace):
        """創建部署管理器實例"""
        return DeploymentAutomation(temp_workspace)

    @pytest.fixture
    def sample_config(self):
        """創建範例配置"""
        return DeploymentConfig(
            environment=DeploymentEnvironment.DEVELOPMENT,
            service_type=ServiceType.NETSTACK,
            network=NetworkConfig(),
            resources=ResourceLimits(),
        )

    def test_generate_deployment_id(self, deployment_manager):
        """測試生成部署ID"""
        deployment_id = deployment_manager.generate_deployment_id()

        assert deployment_id.startswith("deploy_")
        assert len(deployment_id) > 10

    @pytest.mark.asyncio
    async def test_pre_deployment_checks_success(
        self, deployment_manager, sample_config
    ):
        """測試部署前檢查成功"""
        with patch("docker.from_env") as mock_docker, patch(
            "shutil.disk_usage"
        ) as mock_disk_usage, patch.object(
            deployment_manager, "_check_port_availability"
        ) as mock_port_check:

            # Mock Docker 可用
            mock_client = Mock()
            mock_docker.return_value = mock_client
            mock_client.ping.return_value = True

            # Mock 充足的磁碟空間 (10GB)
            mock_disk_usage.return_value = Mock(free=10 * 1024**3)

            # Mock 端口檢查通過
            mock_port_check.return_value = None

            checks_passed, issues = await deployment_manager.pre_deployment_checks(
                sample_config
            )

            assert checks_passed
            assert len(issues) == 0

    @pytest.mark.asyncio
    async def test_pre_deployment_checks_failure(
        self, deployment_manager, sample_config
    ):
        """測試部署前檢查失敗"""
        with patch("docker.from_env") as mock_docker, patch(
            "shutil.disk_usage"
        ) as mock_disk_usage:

            # Mock Docker 不可用
            mock_docker.side_effect = Exception("Docker not available")

            # Mock 磁碟空間不足 (1GB)
            mock_disk_usage.return_value = Mock(free=1 * 1024**3)

            checks_passed, issues = await deployment_manager.pre_deployment_checks(
                sample_config
            )

            assert not checks_passed
            assert len(issues) >= 2  # Docker和磁碟空間問題

    @pytest.mark.asyncio
    async def test_deploy_service_success(self, deployment_manager, sample_config):
        """測試成功部署服務"""
        with patch.object(
            deployment_manager, "pre_deployment_checks"
        ) as mock_checks, patch.object(
            deployment_manager, "_stop_existing_services"
        ) as mock_stop, patch.object(
            deployment_manager, "_start_services"
        ) as mock_start, patch.object(
            deployment_manager, "_perform_health_checks"
        ) as mock_health, patch.object(
            deployment_manager, "_save_deployment_log"
        ) as mock_save:

            # Mock 檢查通過
            mock_checks.return_value = (True, [])

            # Mock 服務啟動成功
            mock_start.return_value = True

            # Mock 健康檢查通過
            mock_health.return_value = [
                Mock(status=HealthCheckStatus.HEALTHY),
                Mock(status=HealthCheckStatus.HEALTHY),
            ]

            record = await deployment_manager.deploy_service(sample_config)

            assert record.status == DeploymentStatus.SUCCESS
            assert record.rollback_available
            mock_checks.assert_called_once()
            mock_stop.assert_called_once()
            mock_start.assert_called_once()
            mock_health.assert_called_once()

    @pytest.mark.asyncio
    async def test_deploy_service_failure(self, deployment_manager, sample_config):
        """測試部署服務失敗"""
        with patch.object(
            deployment_manager, "pre_deployment_checks"
        ) as mock_checks, patch.object(
            deployment_manager, "_stop_existing_services"
        ) as mock_stop, patch.object(
            deployment_manager, "_start_services"
        ) as mock_start, patch.object(
            deployment_manager, "_save_deployment_log"
        ) as mock_save:

            # Mock 檢查通過
            mock_checks.return_value = (True, [])

            # Mock 服務啟動失敗
            mock_start.return_value = False

            record = await deployment_manager.deploy_service(sample_config)

            assert record.status == DeploymentStatus.FAILED
            assert not record.rollback_available
            assert "服務啟動失敗" in record.error_message

    @pytest.mark.asyncio
    async def test_rollback_deployment(self, deployment_manager, sample_config):
        """測試回滾部署"""
        # 創建一個成功的部署記錄
        successful_record = DeploymentRecord(
            deployment_id="deploy_20241201_120000",
            config=sample_config,
            status=DeploymentStatus.SUCCESS,
            start_time=datetime.utcnow(),
            rollback_available=True,
        )
        deployment_manager.deployment_history.append(successful_record)

        # 創建一個失敗的部署記錄
        failed_record = DeploymentRecord(
            deployment_id="deploy_20241201_130000",
            config=sample_config,
            status=DeploymentStatus.FAILED,
            start_time=datetime.utcnow(),
            rollback_available=True,
        )
        deployment_manager.deployment_history.append(failed_record)

        with patch.object(
            deployment_manager, "_stop_existing_services"
        ) as mock_stop, patch.object(
            deployment_manager, "deploy_service"
        ) as mock_deploy:

            # Mock 重新部署成功
            mock_deploy.return_value = Mock(status=DeploymentStatus.SUCCESS)

            success = await deployment_manager.rollback_deployment(
                "deploy_20241201_130000"
            )

            assert success
            mock_stop.assert_called_once()
            mock_deploy.assert_called_once()


class TestDockerHealthChecker:
    """Docker健康檢查器測試"""

    @pytest.fixture
    def health_checker(self):
        """創建健康檢查器實例"""
        with patch("docker.from_env"):
            return DockerHealthChecker()

    @pytest.mark.asyncio
    async def test_check_container_health_running(self, health_checker):
        """測試檢查運行中容器健康狀態"""
        with patch.object(health_checker, "client") as mock_client:
            # Mock 運行中的容器
            mock_container = Mock()
            mock_container.status = "running"
            mock_container.attrs = {"State": {"Health": {"Status": "healthy"}}}
            mock_client.containers.get.return_value = mock_container

            health_info = await health_checker.check_container_health("test_container")

            assert health_info.service_name == "test_container"
            assert health_info.status == HealthCheckStatus.HEALTHY
            assert health_info.response_time_ms > 0

    @pytest.mark.asyncio
    async def test_check_container_health_not_running(self, health_checker):
        """測試檢查非運行狀態容器"""
        with patch.object(health_checker, "client") as mock_client:
            # Mock 停止的容器
            mock_container = Mock()
            mock_container.status = "exited"
            mock_client.containers.get.return_value = mock_container

            health_info = await health_checker.check_container_health("test_container")

            assert health_info.status == HealthCheckStatus.UNHEALTHY
            assert "Container not running" in health_info.error_message

    @pytest.mark.asyncio
    async def test_check_container_health_not_found(self, health_checker):
        """測試檢查不存在的容器"""
        with patch.object(health_checker, "client") as mock_client:
            import docker

            mock_client.containers.get.side_effect = docker.errors.NotFound(
                "Container not found"
            )

            health_info = await health_checker.check_container_health("test_container")

            assert health_info.status == HealthCheckStatus.UNHEALTHY
            assert "Container not found" in health_info.error_message

    @pytest.mark.asyncio
    async def test_check_service_endpoints_healthy(self, health_checker):
        """測試檢查健康的服務端點"""
        with patch("requests.get") as mock_get:
            # Mock 成功的HTTP響應
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            endpoints = ["http://localhost:8080/health", "http://localhost:8080/status"]
            health_info = await health_checker.check_service_endpoints(
                "test_service", endpoints
            )

            assert health_info.service_name == "test_service"
            assert health_info.status == HealthCheckStatus.HEALTHY
            assert len(health_info.endpoints_checked) == 2

    @pytest.mark.asyncio
    async def test_check_service_endpoints_unhealthy(self, health_checker):
        """測試檢查不健康的服務端點"""
        with patch("requests.get") as mock_get:
            # Mock 失敗的HTTP響應
            mock_get.side_effect = Exception("Connection failed")

            endpoints = ["http://localhost:8080/health"]
            health_info = await health_checker.check_service_endpoints(
                "test_service", endpoints
            )

            assert health_info.status == HealthCheckStatus.UNHEALTHY
            assert "Connection failed" in health_info.error_message


class TestBackupManager:
    """備份管理器測試"""

    @pytest.fixture
    def temp_workspace(self):
        """創建臨時工作空間"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def backup_manager(self, temp_workspace):
        """創建備份管理器實例"""
        with patch("docker.from_env"):
            return BackupManager(temp_workspace)

    def test_generate_backup_id(self, backup_manager):
        """測試生成備份ID"""
        backup_id = backup_manager.generate_backup_id(
            ServiceType.NETSTACK, BackupType.FULL
        )

        assert backup_id.startswith("backup_netstack_full_")
        assert len(backup_id) > 20

    @pytest.mark.asyncio
    async def test_create_full_backup_success(self, backup_manager):
        """測試成功創建完整備份"""
        with patch.object(
            backup_manager, "_create_full_backup"
        ) as mock_full_backup, patch.object(
            backup_manager, "_compress_backup"
        ) as mock_compress, patch.object(
            backup_manager, "_calculate_checksum"
        ) as mock_checksum, patch.object(
            backup_manager, "_save_backup_metadata"
        ) as mock_save:

            # Mock 備份成功
            mock_full_backup.return_value = True

            # Mock 壓縮成功
            compressed_file = Path(backup_manager.backup_dir) / "test_backup.tar.gz"
            compressed_file.touch()
            mock_compress.return_value = compressed_file

            # Mock 校驗和計算
            mock_checksum.return_value = "test_checksum"

            record = await backup_manager.create_backup(
                ServiceType.NETSTACK, BackupType.FULL
            )

            assert record.status == BackupStatus.SUCCESS
            assert record.file_path == str(compressed_file)
            assert record.checksum == "test_checksum"
            mock_full_backup.assert_called_once()
            mock_compress.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_backup_failure(self, backup_manager):
        """測試備份創建失敗"""
        with patch.object(
            backup_manager, "_create_full_backup"
        ) as mock_full_backup, patch.object(
            backup_manager, "_save_backup_metadata"
        ) as mock_save:

            # Mock 備份失敗
            mock_full_backup.return_value = False

            record = await backup_manager.create_backup(
                ServiceType.NETSTACK, BackupType.FULL
            )

            assert record.status == BackupStatus.FAILED
            assert "備份創建失敗" in record.error_message

    @pytest.mark.asyncio
    async def test_create_incremental_backup(self, backup_manager):
        """測試創建增量備份"""
        # 創建一個基準備份記錄
        base_backup = BackupRecord(
            backup_id="backup_netstack_full_20241201_120000",
            service_type=ServiceType.NETSTACK,
            backup_type=BackupType.FULL,
            status=BackupStatus.SUCCESS,
            start_time=datetime.utcnow() - timedelta(days=1),
        )
        backup_manager.backup_history.append(base_backup)

        with patch.object(
            backup_manager, "_create_incremental_backup"
        ) as mock_incremental, patch.object(
            backup_manager, "_compress_backup"
        ) as mock_compress, patch.object(
            backup_manager, "_save_backup_metadata"
        ) as mock_save:

            # Mock 增量備份成功
            mock_incremental.return_value = True

            # Mock 壓縮成功
            compressed_file = (
                Path(backup_manager.backup_dir) / "test_incremental.tar.gz"
            )
            compressed_file.touch()
            mock_compress.return_value = compressed_file

            record = await backup_manager.create_backup(
                ServiceType.NETSTACK, BackupType.INCREMENTAL
            )

            assert record.status == BackupStatus.SUCCESS
            mock_incremental.assert_called_once()

    @pytest.mark.asyncio
    async def test_restore_backup_success(self, backup_manager):
        """測試成功恢復備份"""
        # 創建一個備份記錄
        backup_record = BackupRecord(
            backup_id="backup_netstack_full_20241201_120000",
            service_type=ServiceType.NETSTACK,
            backup_type=BackupType.FULL,
            status=BackupStatus.SUCCESS,
            start_time=datetime.utcnow(),
            file_path=str(backup_manager.backup_dir / "test_backup.tar.gz"),
            checksum="test_checksum",
        )
        backup_manager.backup_history.append(backup_record)

        # 創建模擬的備份文件
        backup_file = Path(backup_record.file_path)
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        backup_file.touch()

        with patch.object(
            backup_manager, "_calculate_checksum"
        ) as mock_checksum, patch("tarfile.open") as mock_tarfile, patch.object(
            backup_manager, "_restore_full_backup"
        ) as mock_restore:

            # Mock 校驗和匹配
            mock_checksum.return_value = "test_checksum"

            # Mock tarfile 解壓
            mock_tar = Mock()
            mock_tarfile.return_value.__enter__.return_value = mock_tar

            # Mock 恢復成功
            mock_restore.return_value = True

            # 創建模擬的元數據文件
            metadata_content = {"backup_type": "full", "service_type": "netstack"}

            with patch("builtins.open", mock_open_with_json(metadata_content)):
                success = await backup_manager.restore_backup(
                    "backup_netstack_full_20241201_120000"
                )

            assert success
            mock_restore.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_old_backups(self, backup_manager):
        """測試清理過期備份"""
        # 創建過期備份記錄
        old_backup = BackupRecord(
            backup_id="old_backup",
            service_type=ServiceType.NETSTACK,
            backup_type=BackupType.FULL,
            status=BackupStatus.SUCCESS,
            start_time=datetime.utcnow() - timedelta(days=35),  # 超過30天保留期
            file_path=str(backup_manager.backup_dir / "old_backup.tar.gz"),
        )

        # 創建新備份記錄
        new_backup = BackupRecord(
            backup_id="new_backup",
            service_type=ServiceType.NETSTACK,
            backup_type=BackupType.FULL,
            status=BackupStatus.SUCCESS,
            start_time=datetime.utcnow() - timedelta(days=1),
            file_path=str(backup_manager.backup_dir / "new_backup.tar.gz"),
        )

        backup_manager.backup_history = [old_backup, new_backup]

        # 創建模擬文件
        Path(old_backup.file_path).touch()
        Path(new_backup.file_path).touch()

        await backup_manager.cleanup_old_backups()

        # 檢查過期備份被清理
        assert len(backup_manager.backup_history) == 1
        assert backup_manager.backup_history[0].backup_id == "new_backup"
        assert not Path(old_backup.file_path).exists()

    def test_list_backups(self, backup_manager):
        """測試列出備份記錄"""
        # 創建多個備份記錄
        backup1 = BackupRecord(
            backup_id="backup1",
            service_type=ServiceType.NETSTACK,
            backup_type=BackupType.FULL,
            status=BackupStatus.SUCCESS,
            start_time=datetime.utcnow() - timedelta(days=2),
        )

        backup2 = BackupRecord(
            backup_id="backup2",
            service_type=ServiceType.SIMWORLD,
            backup_type=BackupType.INCREMENTAL,
            status=BackupStatus.SUCCESS,
            start_time=datetime.utcnow() - timedelta(days=1),
        )

        backup_manager.backup_history = [backup1, backup2]

        # 測試列出所有備份
        all_backups = backup_manager.list_backups()
        assert len(all_backups) == 2
        assert all_backups[0].backup_id == "backup2"  # 按時間倒序

        # 測試按服務類型篩選
        netstack_backups = backup_manager.list_backups(ServiceType.NETSTACK)
        assert len(netstack_backups) == 1
        assert netstack_backups[0].backup_id == "backup1"


def mock_open_with_json(data):
    """創建模擬文件打開函數，返回JSON數據"""
    from unittest.mock import mock_open

    return mock_open(read_data=json.dumps(data))


@pytest.mark.asyncio
async def test_integration_deployment_flow():
    """集成測試：完整的部署流程"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 初始化管理器
        from deployment.config_manager import ConfigManager
        from deployment.automation.deploy_manager import DeploymentAutomation

        config_manager = ConfigManager(temp_dir)
        deploy_manager = DeploymentAutomation(temp_dir)

        # 創建配置
        config = config_manager.create_default_config(
            DeploymentEnvironment.DEVELOPMENT, ServiceType.NETSTACK
        )

        # Mock所有外部依賴
        with patch.object(
            deploy_manager, "pre_deployment_checks"
        ) as mock_checks, patch.object(
            deploy_manager, "_stop_existing_services"
        ), patch.object(
            deploy_manager, "_start_services"
        ) as mock_start, patch.object(
            deploy_manager, "_perform_health_checks"
        ) as mock_health, patch.object(
            deploy_manager, "_save_deployment_log"
        ):

            # Mock 成功流程
            mock_checks.return_value = (True, [])
            mock_start.return_value = True
            mock_health.return_value = [
                Mock(status=HealthCheckStatus.HEALTHY),
                Mock(status=HealthCheckStatus.HEALTHY),
            ]

            # 執行部署
            record = await deploy_manager.deploy_service(config)

            # 驗證結果
            assert record.status == DeploymentStatus.SUCCESS
            assert record.config.service_type == ServiceType.NETSTACK
            assert record.config.environment == DeploymentEnvironment.DEVELOPMENT


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "--tb=short"])
