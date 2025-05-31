#!/usr/bin/env python3
"""
部署命令行工具
提供統一的部署、備份、監控和管理界面

使用方式:
python deployment/cli/deploy_cli.py --help

根據 TODO.md 第18項「部署流程優化與自動化」要求設計
"""

import asyncio
import logging
import sys
import argparse
import json
from pathlib import Path
from typing import Optional
import time
from datetime import datetime

# 添加項目根路徑到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from deployment.config_manager import (
    config_manager,
    DeploymentEnvironment,
    ServiceType,
    DeploymentConfig,
)
from deployment.automation.deploy_manager import deployment_manager
from deployment.backup.backup_manager import backup_manager, BackupType

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("deployment/logs/deploy_cli.log"),
    ],
)

logger = logging.getLogger(__name__)


class DeploymentCLI:
    """部署命令行介面"""

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description="NTN Stack 部署工具",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
示例:
  # 部署 NetStack 開發環境
  python deploy_cli.py deploy --service netstack --env development
  
  # 部署 SimWorld 生產環境
  python deploy_cli.py deploy --service simworld --env production --gpu
  
  # 創建完整備份
  python deploy_cli.py backup --service netstack --type full
  
  # 恢復備份
  python deploy_cli.py restore --backup-id backup_netstack_full_20241201_120000
  
  # 監控服務健康狀態
  python deploy_cli.py monitor --service netstack --duration 30
  
  # 列出部署記錄
  python deploy_cli.py list-deployments --service simworld --limit 5
            """,
        )

        self._setup_subcommands()

    def _setup_subcommands(self):
        """設置子命令"""
        subparsers = self.parser.add_subparsers(dest="command", help="可用命令")

        # 部署命令
        deploy_parser = subparsers.add_parser("deploy", help="部署服務")
        deploy_parser.add_argument(
            "--service",
            choices=["netstack", "simworld"],
            required=True,
            help="要部署的服務",
        )
        deploy_parser.add_argument(
            "--env",
            choices=["development", "testing", "laboratory", "production", "field"],
            default="development",
            help="部署環境",
        )
        deploy_parser.add_argument("--gpu", action="store_true", help="啟用GPU支援")
        deploy_parser.add_argument(
            "--force", action="store_true", help="強制部署（跳過檢查）"
        )
        deploy_parser.add_argument("--cpu-limit", type=str, help="CPU限制")
        deploy_parser.add_argument("--memory-limit", type=str, help="內存限制")

        # 停止命令
        stop_parser = subparsers.add_parser("stop", help="停止服務")
        stop_parser.add_argument(
            "--service",
            choices=["netstack", "simworld"],
            required=True,
            help="要停止的服務",
        )

        # 重啟命令
        restart_parser = subparsers.add_parser("restart", help="重啟服務")
        restart_parser.add_argument(
            "--service",
            choices=["netstack", "simworld"],
            required=True,
            help="要重啟的服務",
        )

        # 回滾命令
        rollback_parser = subparsers.add_parser("rollback", help="回滾部署")
        rollback_parser.add_argument(
            "--deployment-id", required=True, help="要回滾的部署ID"
        )

        # 備份命令
        backup_parser = subparsers.add_parser("backup", help="創建備份")
        backup_parser.add_argument(
            "--service",
            choices=["netstack", "simworld"],
            required=True,
            help="要備份的服務",
        )
        backup_parser.add_argument(
            "--type",
            choices=["full", "incremental", "differential"],
            default="full",
            help="備份類型",
        )
        backup_parser.add_argument("--comment", type=str, help="備份註釋")

        # 恢復命令
        restore_parser = subparsers.add_parser("restore", help="恢復備份")
        restore_parser.add_argument("--backup-id", required=True, help="要恢復的備份ID")
        restore_parser.add_argument(
            "--target-env",
            choices=["development", "testing", "laboratory", "production", "field"],
            default="development",
            help="目標環境",
        )

        # 監控命令
        monitor_parser = subparsers.add_parser("monitor", help="監控服務")
        monitor_parser.add_argument(
            "--service",
            choices=["netstack", "simworld"],
            required=True,
            help="要監控的服務",
        )
        monitor_parser.add_argument(
            "--duration", type=int, default=10, help="監控持續時間（分鐘）"
        )

        # 健康檢查命令
        health_parser = subparsers.add_parser("health", help="執行健康檢查")
        health_parser.add_argument(
            "--service",
            choices=["netstack", "simworld"],
            required=True,
            help="要檢查的服務",
        )

        # 列出部署記錄
        list_deploy_parser = subparsers.add_parser(
            "list-deployments", help="列出部署記錄"
        )
        list_deploy_parser.add_argument(
            "--service", choices=["netstack", "simworld"], help="篩選服務"
        )
        list_deploy_parser.add_argument(
            "--limit", type=int, default=10, help="顯示數量限制"
        )

        # 列出備份記錄
        list_backup_parser = subparsers.add_parser("list-backups", help="列出備份記錄")
        list_backup_parser.add_argument(
            "--service", choices=["netstack", "simworld"], help="篩選服務"
        )
        list_backup_parser.add_argument(
            "--limit", type=int, default=20, help="顯示數量限制"
        )

        # 清理命令
        cleanup_parser = subparsers.add_parser("cleanup", help="清理過期備份")

        # 配置命令
        config_parser = subparsers.add_parser("config", help="配置管理")
        config_subparsers = config_parser.add_subparsers(dest="config_action")

        # 生成配置
        generate_config_parser = config_subparsers.add_parser(
            "generate", help="生成配置"
        )
        generate_config_parser.add_argument(
            "--service",
            choices=["netstack", "simworld"],
            required=True,
            help="服務類型",
        )
        generate_config_parser.add_argument(
            "--env",
            choices=["development", "testing", "laboratory", "production", "field"],
            required=True,
            help="環境類型",
        )
        generate_config_parser.add_argument("--output", type=str, help="輸出文件名")

        # 驗證配置
        validate_config_parser = config_subparsers.add_parser(
            "validate", help="驗證配置"
        )
        validate_config_parser.add_argument(
            "--config-file", required=True, help="配置文件路徑"
        )

        # 狀態命令
        status_parser = subparsers.add_parser("status", help="查看系統狀態")
        status_parser.add_argument(
            "--detailed", action="store_true", help="顯示詳細信息"
        )

    async def run(self):
        """運行命令行工具"""
        args = self.parser.parse_args()

        if not args.command:
            self.parser.print_help()
            return

        try:
            if args.command == "deploy":
                await self._handle_deploy(args)
            elif args.command == "stop":
                await self._handle_stop(args)
            elif args.command == "restart":
                await self._handle_restart(args)
            elif args.command == "rollback":
                await self._handle_rollback(args)
            elif args.command == "backup":
                await self._handle_backup(args)
            elif args.command == "restore":
                await self._handle_restore(args)
            elif args.command == "monitor":
                await self._handle_monitor(args)
            elif args.command == "health":
                await self._handle_health(args)
            elif args.command == "list-deployments":
                await self._handle_list_deployments(args)
            elif args.command == "list-backups":
                await self._handle_list_backups(args)
            elif args.command == "cleanup":
                await self._handle_cleanup(args)
            elif args.command == "config":
                await self._handle_config(args)
            elif args.command == "status":
                await self._handle_status(args)
            else:
                print(f"❌ 未知命令: {args.command}")
                self.parser.print_help()

        except KeyboardInterrupt:
            print("\n⚠️ 操作被用戶中斷")
        except Exception as e:
            logger.error(f"命令執行失敗: {e}")
            print(f"❌ 執行失敗: {e}")
            sys.exit(1)

    async def _handle_deploy(self, args):
        """處理部署命令"""
        print(f"🚀 開始部署 {args.service} ({args.env})")

        # 創建部署配置
        service_type = ServiceType(args.service)
        environment = DeploymentEnvironment(args.env)

        config = config_manager.create_default_config(environment, service_type)

        # 應用命令行參數
        if args.gpu:
            config.gpu_enabled = True
        if args.cpu_limit:
            config.resources.cpu_limit = args.cpu_limit
        if args.memory_limit:
            config.resources.memory_limit = args.memory_limit

        # 執行部署
        record = await deployment_manager.deploy_service(config, force=args.force)

        # 顯示結果
        self._print_deployment_result(record)

    async def _handle_stop(self, args):
        """處理停止命令"""
        print(f"🛑 停止 {args.service} 服務")

        # 根據服務類型創建配置
        service_type = ServiceType(args.service)
        config = config_manager.create_default_config(
            DeploymentEnvironment.DEVELOPMENT, service_type
        )

        await deployment_manager._stop_existing_services(config)
        print(f"✅ {args.service} 服務已停止")

    async def _handle_restart(self, args):
        """處理重啟命令"""
        print(f"🔄 重啟 {args.service} 服務")

        # 找到最近的成功部署
        service_type = ServiceType(args.service)
        deployments = deployment_manager.list_deployments(service_type, limit=1)

        if deployments:
            latest_deployment = deployments[0]
            record = await deployment_manager.deploy_service(
                latest_deployment.config, force=True
            )
            self._print_deployment_result(record)
        else:
            print(f"❌ 找不到 {args.service} 的部署記錄")

    async def _handle_rollback(self, args):
        """處理回滾命令"""
        print(f"🔄 回滾部署: {args.deployment_id}")

        success = await deployment_manager.rollback_deployment(args.deployment_id)

        if success:
            print(f"✅ 回滾成功: {args.deployment_id}")
        else:
            print(f"❌ 回滾失敗: {args.deployment_id}")

    async def _handle_backup(self, args):
        """處理備份命令"""
        print(f"🗄️ 創建 {args.service} {args.type} 備份")

        service_type = ServiceType(args.service)
        backup_type = BackupType(args.type)
        comment = args.comment or f"CLI backup at {datetime.now().isoformat()}"

        record = await backup_manager.create_backup(service_type, backup_type, comment)

        self._print_backup_result(record)

    async def _handle_restore(self, args):
        """處理恢復命令"""
        print(f"🔄 恢復備份: {args.backup_id}")

        target_env = DeploymentEnvironment(args.target_env)
        success = await backup_manager.restore_backup(args.backup_id, target_env)

        if success:
            print(f"✅ 備份恢復成功: {args.backup_id}")
        else:
            print(f"❌ 備份恢復失敗: {args.backup_id}")

    async def _handle_monitor(self, args):
        """處理監控命令"""
        print(f"📊 開始監控 {args.service} 服務 {args.duration} 分鐘")

        service_type = ServiceType(args.service)
        config = config_manager.create_default_config(
            DeploymentEnvironment.DEVELOPMENT, service_type
        )

        health_history = await deployment_manager.monitor_services(
            config, args.duration
        )

        print(f"📊 監控完成，共收集 {len(health_history)} 條健康記錄")

    async def _handle_health(self, args):
        """處理健康檢查命令"""
        print(f"🏥 檢查 {args.service} 服務健康狀態")

        service_type = ServiceType(args.service)
        config = config_manager.create_default_config(
            DeploymentEnvironment.DEVELOPMENT, service_type
        )

        health_results = await deployment_manager._perform_health_checks(config)
        self._print_health_results(health_results)

    async def _handle_list_deployments(self, args):
        """處理列出部署記錄命令"""
        service_type = ServiceType(args.service) if args.service else None
        deployments = deployment_manager.list_deployments(service_type, args.limit)

        self._print_deployments_table(deployments)

    async def _handle_list_backups(self, args):
        """處理列出備份記錄命令"""
        service_type = ServiceType(args.service) if args.service else None
        backups = backup_manager.list_backups(service_type, args.limit)

        self._print_backups_table(backups)

    async def _handle_cleanup(self, args):
        """處理清理命令"""
        print("🧹 開始清理過期備份...")
        await backup_manager.cleanup_old_backups()
        print("✅ 清理完成")

    async def _handle_config(self, args):
        """處理配置命令"""
        if args.config_action == "generate":
            await self._generate_config(args)
        elif args.config_action == "validate":
            await self._validate_config(args)
        else:
            print("❌ 未知的配置操作")

    async def _generate_config(self, args):
        """生成配置"""
        print(f"📝 生成 {args.service} {args.env} 配置")

        service_type = ServiceType(args.service)
        environment = DeploymentEnvironment(args.env)

        config = config_manager.create_default_config(environment, service_type)

        if args.output:
            filename = args.output
        else:
            filename = f"{args.service}-{args.env}-config.yaml"

        config_path = config_manager.save_config(config, filename)
        compose_path = config_manager.generate_docker_compose(config)
        env_path = config_manager.generate_env_file(config)

        print(f"✅ 配置已生成:")
        print(f"  - 配置文件: {config_path}")
        print(f"  - Compose 文件: {compose_path}")
        print(f"  - 環境變數文件: {env_path}")

    async def _validate_config(self, args):
        """驗證配置"""
        print(f"🔍 驗證配置文件: {args.config_file}")

        try:
            config = config_manager.load_config(args.config_file)
            validation_results = config_manager.validate_configuration(config)

            if (
                not validation_results["config_errors"]
                and not validation_results["file_errors"]
            ):
                print("✅ 配置驗證通過")
            else:
                print("❌ 配置驗證失敗:")
                for error in validation_results["config_errors"]:
                    print(f"  - 配置錯誤: {error}")
                for error in validation_results["file_errors"]:
                    print(f"  - 文件錯誤: {error}")

        except Exception as e:
            print(f"❌ 配置文件載入失敗: {e}")

    async def _handle_status(self, args):
        """處理狀態命令"""
        print("📊 系統狀態")
        print("=" * 50)

        # 顯示部署狀態
        print("\n🚀 部署狀態:")
        recent_deployments = deployment_manager.list_deployments(limit=5)
        if recent_deployments:
            for deployment in recent_deployments:
                status_emoji = "✅" if deployment.status.value == "success" else "❌"
                print(
                    f"  {status_emoji} {deployment.deployment_id} - {deployment.config.service_type.value} ({deployment.status.value})"
                )
        else:
            print("  📝 無部署記錄")

        # 顯示備份狀態
        print("\n🗄️ 備份狀態:")
        recent_backups = backup_manager.list_backups(limit=5)
        if recent_backups:
            for backup in recent_backups:
                status_emoji = "✅" if backup.status.value == "success" else "❌"
                print(
                    f"  {status_emoji} {backup.backup_id} - {backup.service_type.value} ({backup.file_size_mb:.1f}MB)"
                )
        else:
            print("  📝 無備份記錄")

        # 詳細信息
        if args.detailed:
            print("\n🔍 詳細信息:")

            # Docker 容器狀態
            try:
                import docker

                client = docker.from_env()
                containers = client.containers.list(all=True)

                print("  🐳 Docker 容器:")
                for container in containers:
                    if any(name in container.name for name in ["netstack", "simworld"]):
                        status_emoji = "✅" if container.status == "running" else "❌"
                        print(
                            f"    {status_emoji} {container.name}: {container.status}"
                        )

            except Exception as e:
                print(f"    ❌ Docker 狀態檢查失敗: {e}")

    def _print_deployment_result(self, record):
        """打印部署結果"""
        print("\n" + "=" * 50)
        print("📋 部署結果")
        print("=" * 50)

        status_emoji = "✅" if record.status.value == "success" else "❌"
        print(f"狀態: {status_emoji} {record.status.value}")
        print(f"部署ID: {record.deployment_id}")
        print(f"服務: {record.config.service_type.value}")
        print(f"環境: {record.config.environment.value}")
        print(f"開始時間: {record.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if record.end_time:
            print(f"結束時間: {record.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"持續時間: {record.duration_seconds:.1f} 秒")

        if record.error_message:
            print(f"錯誤信息: {record.error_message}")

        if record.health_check_results:
            print("\n🏥 健康檢查結果:")
            self._print_health_results(record.health_check_results)

    def _print_backup_result(self, record):
        """打印備份結果"""
        print("\n" + "=" * 50)
        print("📋 備份結果")
        print("=" * 50)

        status_emoji = "✅" if record.status.value == "success" else "❌"
        print(f"狀態: {status_emoji} {record.status.value}")
        print(f"備份ID: {record.backup_id}")
        print(f"服務: {record.service_type.value}")
        print(f"類型: {record.backup_type.value}")
        print(f"開始時間: {record.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        if record.end_time:
            print(f"結束時間: {record.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"持續時間: {record.duration_seconds:.1f} 秒")

        if record.file_path:
            print(f"文件路徑: {record.file_path}")
            print(f"文件大小: {record.file_size_mb:.1f} MB")

        if record.error_message:
            print(f"錯誤信息: {record.error_message}")

    def _print_health_results(self, health_results):
        """打印健康檢查結果"""
        for result in health_results:
            status_emoji = "✅" if result.status.value == "healthy" else "❌"
            print(
                f"  {status_emoji} {result.service_name}: {result.status.value} ({result.response_time_ms:.1f}ms)"
            )

            if result.error_message:
                print(f"    ⚠️  錯誤: {result.error_message}")

            if result.endpoints_checked:
                print(f"    🔗 端點: {', '.join(result.endpoints_checked)}")

    def _print_deployments_table(self, deployments):
        """打印部署記錄表格"""
        if not deployments:
            print("📝 無部署記錄")
            return

        print("\n📋 部署記錄")
        print("-" * 80)
        print(f"{'部署ID':<30} {'服務':<10} {'環境':<12} {'狀態':<10} {'時間':<20}")
        print("-" * 80)

        for deployment in deployments:
            status_emoji = "✅" if deployment.status.value == "success" else "❌"
            print(
                f"{deployment.deployment_id:<30} {deployment.config.service_type.value:<10} "
                f"{deployment.config.environment.value:<12} {status_emoji} {deployment.status.value:<8} "
                f"{deployment.start_time.strftime('%Y-%m-%d %H:%M'):<20}"
            )

    def _print_backups_table(self, backups):
        """打印備份記錄表格"""
        if not backups:
            print("📝 無備份記錄")
            return

        print("\n📋 備份記錄")
        print("-" * 90)
        print(
            f"{'備份ID':<30} {'服務':<10} {'類型':<12} {'狀態':<8} {'大小(MB)':<10} {'時間':<20}"
        )
        print("-" * 90)

        for backup in backups:
            status_emoji = "✅" if backup.status.value == "success" else "❌"
            print(
                f"{backup.backup_id:<30} {backup.service_type.value:<10} "
                f"{backup.backup_type.value:<12} {status_emoji} {backup.status.value:<6} "
                f"{backup.file_size_mb:<8.1f} {backup.start_time.strftime('%Y-%m-%d %H:%M'):<20}"
            )


def main():
    """主函數"""
    cli = DeploymentCLI()
    asyncio.run(cli.run())


if __name__ == "__main__":
    main()
