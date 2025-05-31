#!/usr/bin/env python3
"""
備份和恢復管理器
支援數據備份、增量備份和災難恢復

根據 TODO.md 第18項「部署流程優化與自動化」要求設計
"""

import os
import shutil
import tarfile
import gzip
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import subprocess
import docker

from deployment.config_manager import ServiceType, DeploymentEnvironment

logger = logging.getLogger(__name__)


class BackupType(str, Enum):
    """備份類型"""

    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class BackupStatus(str, Enum):
    """備份狀態"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class BackupRecord:
    """備份記錄"""

    backup_id: str
    service_type: ServiceType
    backup_type: BackupType
    status: BackupStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    file_path: Optional[str] = None
    file_size_bytes: int = 0
    checksum: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def duration_seconds(self) -> Optional[float]:
        """備份持續時間（秒）"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def file_size_mb(self) -> float:
        """文件大小（MB）"""
        return self.file_size_bytes / (1024 * 1024)


class BackupManager:
    """備份管理器"""

    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.backup_dir = self.workspace_root / "deployment" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.backup_history: List[BackupRecord] = []
        self.docker_client = docker.from_env()

        # 備份配置
        self.backup_config = {
            ServiceType.NETSTACK: {
                "containers": ["netstack-mongo"],
                "volumes": ["mongo_data", "mongo_config"],
                "config_files": ["netstack/config", "netstack/compose"],
            },
            ServiceType.SIMWORLD: {
                "containers": ["simworld_postgis"],
                "volumes": ["postgres_data"],
                "config_files": ["simworld/backend", "simworld/frontend"],
            },
        }

        # 保留政策（天數）
        self.retention_policy = {
            BackupType.FULL: 30,
            BackupType.INCREMENTAL: 7,
            BackupType.DIFFERENTIAL: 14,
        }

    def generate_backup_id(
        self, service_type: ServiceType, backup_type: BackupType
    ) -> str:
        """生成備份ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"backup_{service_type.value}_{backup_type.value}_{timestamp}"

    async def create_backup(
        self,
        service_type: ServiceType,
        backup_type: BackupType = BackupType.FULL,
        comment: str = "",
    ) -> BackupRecord:
        """創建備份"""
        backup_id = self.generate_backup_id(service_type, backup_type)

        record = BackupRecord(
            backup_id=backup_id,
            service_type=service_type,
            backup_type=backup_type,
            status=BackupStatus.PENDING,
            start_time=datetime.utcnow(),
            metadata={"comment": comment},
        )

        self.backup_history.append(record)

        try:
            logger.info(
                f"🗄️ 開始創建 {service_type.value} {backup_type.value} 備份: {backup_id}"
            )
            record.status = BackupStatus.IN_PROGRESS

            # 創建備份目錄
            backup_path = self.backup_dir / backup_id
            backup_path.mkdir(exist_ok=True)

            # 根據備份類型執行不同策略
            if backup_type == BackupType.FULL:
                success = await self._create_full_backup(
                    service_type, backup_path, record
                )
            elif backup_type == BackupType.INCREMENTAL:
                success = await self._create_incremental_backup(
                    service_type, backup_path, record
                )
            else:  # DIFFERENTIAL
                success = await self._create_differential_backup(
                    service_type, backup_path, record
                )

            if success:
                # 壓縮備份
                compressed_file = await self._compress_backup(backup_path, record)
                if compressed_file:
                    record.file_path = str(compressed_file)
                    record.file_size_bytes = compressed_file.stat().st_size
                    record.checksum = await self._calculate_checksum(compressed_file)
                    record.status = BackupStatus.SUCCESS

                    # 清理未壓縮的目錄
                    shutil.rmtree(backup_path)

                    logger.info(
                        f"✅ 備份創建成功: {backup_id} ({record.file_size_mb:.1f}MB)"
                    )
                else:
                    record.status = BackupStatus.FAILED
                    record.error_message = "壓縮失敗"
            else:
                record.status = BackupStatus.FAILED
                if not record.error_message:
                    record.error_message = "備份創建失敗"

        except Exception as e:
            record.status = BackupStatus.FAILED
            record.error_message = str(e)
            logger.error(f"❌ 備份創建異常: {e}")

        finally:
            record.end_time = datetime.utcnow()
            await self._save_backup_metadata(record)

        return record

    async def _create_full_backup(
        self, service_type: ServiceType, backup_path: Path, record: BackupRecord
    ) -> bool:
        """創建完整備份"""
        try:
            config = self.backup_config[service_type]

            # 1. 備份容器數據
            for container_name in config["containers"]:
                success = await self._backup_container_data(container_name, backup_path)
                if not success:
                    record.error_message = f"容器數據備份失敗: {container_name}"
                    return False

            # 2. 備份 Docker volumes
            for volume_name in config["volumes"]:
                success = await self._backup_docker_volume(volume_name, backup_path)
                if not success:
                    record.error_message = f"Volume 備份失敗: {volume_name}"
                    return False

            # 3. 備份配置文件
            for config_path in config["config_files"]:
                success = await self._backup_config_files(config_path, backup_path)
                if not success:
                    record.error_message = f"配置文件備份失敗: {config_path}"
                    return False

            # 4. 保存備份元數據
            metadata = {
                "backup_type": "full",
                "service_type": service_type.value,
                "timestamp": datetime.utcnow().isoformat(),
                "components": {
                    "containers": config["containers"],
                    "volumes": config["volumes"],
                    "config_files": config["config_files"],
                },
            }

            metadata_file = backup_path / "backup_metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            return True

        except Exception as e:
            logger.error(f"完整備份失敗: {e}")
            return False

    async def _create_incremental_backup(
        self, service_type: ServiceType, backup_path: Path, record: BackupRecord
    ) -> bool:
        """創建增量備份"""
        try:
            # 找到最近的備份作為基準
            last_backup = self._find_last_backup(service_type)
            if not last_backup:
                logger.info("未找到基準備份，創建完整備份")
                return await self._create_full_backup(service_type, backup_path, record)

            logger.info(f"基於備份創建增量備份: {last_backup.backup_id}")

            # 只備份變更的數據
            config = self.backup_config[service_type]
            base_time = last_backup.start_time

            # 備份變更的配置文件
            for config_path in config["config_files"]:
                success = await self._backup_changed_files(
                    config_path, backup_path, base_time
                )
                if not success:
                    record.error_message = f"增量備份失敗: {config_path}"
                    return False

            # 創建增量備份的元數據
            metadata = {
                "backup_type": "incremental",
                "service_type": service_type.value,
                "timestamp": datetime.utcnow().isoformat(),
                "base_backup": last_backup.backup_id,
                "base_time": base_time.isoformat(),
            }

            metadata_file = backup_path / "backup_metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            return True

        except Exception as e:
            logger.error(f"增量備份失敗: {e}")
            return False

    async def _create_differential_backup(
        self, service_type: ServiceType, backup_path: Path, record: BackupRecord
    ) -> bool:
        """創建差異備份"""
        try:
            # 找到最近的完整備份作為基準
            last_full_backup = self._find_last_full_backup(service_type)
            if not last_full_backup:
                logger.info("未找到完整備份，創建完整備份")
                return await self._create_full_backup(service_type, backup_path, record)

            logger.info(f"基於完整備份創建差異備份: {last_full_backup.backup_id}")

            # 備份自完整備份以來的所有變更
            config = self.backup_config[service_type]
            base_time = last_full_backup.start_time

            # 備份變更的數據
            for config_path in config["config_files"]:
                success = await self._backup_changed_files(
                    config_path, backup_path, base_time
                )
                if not success:
                    record.error_message = f"差異備份失敗: {config_path}"
                    return False

            # 創建差異備份的元數據
            metadata = {
                "backup_type": "differential",
                "service_type": service_type.value,
                "timestamp": datetime.utcnow().isoformat(),
                "base_backup": last_full_backup.backup_id,
                "base_time": base_time.isoformat(),
            }

            metadata_file = backup_path / "backup_metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            return True

        except Exception as e:
            logger.error(f"差異備份失敗: {e}")
            return False

    async def _backup_container_data(
        self, container_name: str, backup_path: Path
    ) -> bool:
        """備份容器數據"""
        try:
            container = self.docker_client.containers.get(container_name)

            # 創建容器數據導出
            if "mongo" in container_name:
                # MongoDB 數據導出
                dump_cmd = [
                    "docker",
                    "exec",
                    container_name,
                    "mongodump",
                    "--out",
                    "/tmp/backup",
                    "--gzip",
                ]

                process = await asyncio.create_subprocess_exec(
                    *dump_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    logger.error(f"MongoDB 導出失敗: {stderr.decode()}")
                    return False

                # 複製導出的數據
                copy_cmd = [
                    "docker",
                    "cp",
                    f"{container_name}:/tmp/backup",
                    str(backup_path / f"{container_name}_data"),
                ]

                process = await asyncio.create_subprocess_exec(
                    *copy_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                await process.communicate()
                return process.returncode == 0

            elif "postgis" in container_name:
                # PostgreSQL 數據導出
                dump_file = backup_path / f"{container_name}_dump.sql"

                dump_cmd = [
                    "docker",
                    "exec",
                    container_name,
                    "pg_dumpall",
                    "-U",
                    "postgres",
                ]

                with open(dump_file, "w") as f:
                    process = await asyncio.create_subprocess_exec(
                        *dump_cmd, stdout=f, stderr=asyncio.subprocess.PIPE
                    )

                    _, stderr = await process.communicate()

                if process.returncode != 0:
                    logger.error(f"PostgreSQL 導出失敗: {stderr.decode()}")
                    return False

                return True

            return True

        except Exception as e:
            logger.error(f"容器數據備份失敗: {e}")
            return False

    async def _backup_docker_volume(self, volume_name: str, backup_path: Path) -> bool:
        """備份 Docker volume"""
        try:
            volume_backup_path = backup_path / f"volume_{volume_name}"
            volume_backup_path.mkdir(exist_ok=True)

            # 使用臨時容器複製 volume 數據
            copy_cmd = [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{volume_name}:/source",
                "-v",
                f"{volume_backup_path}:/backup",
                "alpine",
                "cp",
                "-a",
                "/source/.",
                "/backup/",
            ]

            process = await asyncio.create_subprocess_exec(
                *copy_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                logger.error(f"Volume 備份失敗: {stderr.decode()}")
                return False

            return True

        except Exception as e:
            logger.error(f"Docker volume 備份失敗: {e}")
            return False

    async def _backup_config_files(self, config_path: str, backup_path: Path) -> bool:
        """備份配置文件"""
        try:
            source_path = self.workspace_root / config_path
            target_path = backup_path / "config" / config_path

            if source_path.exists():
                target_path.parent.mkdir(parents=True, exist_ok=True)

                if source_path.is_dir():
                    shutil.copytree(source_path, target_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(source_path, target_path)

                return True
            else:
                logger.warning(f"配置路徑不存在: {source_path}")
                return True  # 不存在的配置不算錯誤

        except Exception as e:
            logger.error(f"配置文件備份失敗: {e}")
            return False

    async def _backup_changed_files(
        self, config_path: str, backup_path: Path, since_time: datetime
    ) -> bool:
        """備份變更的文件"""
        try:
            source_path = self.workspace_root / config_path
            target_path = backup_path / "config" / config_path

            if not source_path.exists():
                return True

            changed_files = []

            if source_path.is_dir():
                for file_path in source_path.rglob("*"):
                    if file_path.is_file():
                        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_mtime > since_time:
                            changed_files.append(file_path)
            else:
                file_mtime = datetime.fromtimestamp(source_path.stat().st_mtime)
                if file_mtime > since_time:
                    changed_files.append(source_path)

            # 複製變更的文件
            for file_path in changed_files:
                relative_path = file_path.relative_to(self.workspace_root)
                target_file = backup_path / "config" / relative_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, target_file)

            logger.info(f"備份了 {len(changed_files)} 個變更文件")
            return True

        except Exception as e:
            logger.error(f"變更文件備份失敗: {e}")
            return False

    async def _compress_backup(
        self, backup_path: Path, record: BackupRecord
    ) -> Optional[Path]:
        """壓縮備份"""
        try:
            compressed_file = backup_path.with_suffix(".tar.gz")

            with tarfile.open(compressed_file, "w:gz") as tar:
                tar.add(backup_path, arcname=backup_path.name)

            logger.info(f"備份已壓縮: {compressed_file}")
            return compressed_file

        except Exception as e:
            logger.error(f"備份壓縮失敗: {e}")
            return None

    async def _calculate_checksum(self, file_path: Path) -> str:
        """計算文件校驗和"""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"校驗和計算失敗: {e}")
            return ""

    def _find_last_backup(self, service_type: ServiceType) -> Optional[BackupRecord]:
        """找到最近的備份"""
        service_backups = [
            b
            for b in self.backup_history
            if b.service_type == service_type and b.status == BackupStatus.SUCCESS
        ]

        if service_backups:
            return max(service_backups, key=lambda x: x.start_time)
        return None

    def _find_last_full_backup(
        self, service_type: ServiceType
    ) -> Optional[BackupRecord]:
        """找到最近的完整備份"""
        full_backups = [
            b
            for b in self.backup_history
            if (
                b.service_type == service_type
                and b.backup_type == BackupType.FULL
                and b.status == BackupStatus.SUCCESS
            )
        ]

        if full_backups:
            return max(full_backups, key=lambda x: x.start_time)
        return None

    async def restore_backup(
        self,
        backup_id: str,
        target_environment: DeploymentEnvironment = DeploymentEnvironment.DEVELOPMENT,
    ) -> bool:
        """恢復備份"""
        logger.info(f"🔄 開始恢復備份: {backup_id}")

        # 找到備份記錄
        backup_record = None
        for record in self.backup_history:
            if record.backup_id == backup_id:
                backup_record = record
                break

        if not backup_record:
            logger.error(f"❌ 找不到備份記錄: {backup_id}")
            return False

        if backup_record.status != BackupStatus.SUCCESS:
            logger.error(f"❌ 備份狀態無效: {backup_record.status}")
            return False

        try:
            # 解壓備份文件
            backup_file = Path(backup_record.file_path)
            if not backup_file.exists():
                logger.error(f"❌ 備份文件不存在: {backup_file}")
                return False

            # 驗證校驗和
            if backup_record.checksum:
                current_checksum = await self._calculate_checksum(backup_file)
                if current_checksum != backup_record.checksum:
                    logger.error("❌ 備份文件校驗和不匹配")
                    return False

            # 解壓到臨時目錄
            temp_dir = self.backup_dir / f"restore_{backup_id}"
            temp_dir.mkdir(exist_ok=True)

            with tarfile.open(backup_file, "r:gz") as tar:
                tar.extractall(temp_dir)

            # 讀取備份元數據
            metadata_file = temp_dir / backup_id / "backup_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
            else:
                logger.error("❌ 找不到備份元數據")
                return False

            # 根據備份類型執行恢復
            if metadata["backup_type"] == "full":
                success = await self._restore_full_backup(
                    temp_dir / backup_id, backup_record, metadata
                )
            else:
                # 增量和差異備份需要先恢復基準備份
                success = await self._restore_incremental_backup(
                    temp_dir / backup_id, backup_record, metadata
                )

            # 清理臨時目錄
            shutil.rmtree(temp_dir)

            if success:
                logger.info(f"✅ 備份恢復成功: {backup_id}")
            else:
                logger.error(f"❌ 備份恢復失敗: {backup_id}")

            return success

        except Exception as e:
            logger.error(f"❌ 備份恢復異常: {e}")
            return False

    async def _restore_full_backup(
        self, backup_path: Path, record: BackupRecord, metadata: Dict
    ) -> bool:
        """恢復完整備份"""
        try:
            service_type = record.service_type

            # 1. 停止相關服務
            logger.info("🛑 停止服務...")
            if service_type == ServiceType.NETSTACK:
                stop_cmd = ["make", "-C", str(self.workspace_root), "netstack-stop"]
            else:
                stop_cmd = ["make", "-C", str(self.workspace_root), "simworld-stop"]

            process = await asyncio.create_subprocess_exec(*stop_cmd)
            await process.communicate()

            # 2. 恢復配置文件
            config_path = backup_path / "config"
            if config_path.exists():
                for item in config_path.rglob("*"):
                    if item.is_file():
                        relative_path = item.relative_to(config_path)
                        target_path = self.workspace_root / relative_path
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, target_path)

            # 3. 恢復容器數據
            for container_data in backup_path.glob("*_data"):
                container_name = container_data.name.replace("_data", "")
                await self._restore_container_data(container_name, container_data)

            # 4. 恢復 Docker volumes
            for volume_dir in backup_path.glob("volume_*"):
                volume_name = volume_dir.name.replace("volume_", "")
                await self._restore_docker_volume(volume_name, volume_dir)

            return True

        except Exception as e:
            logger.error(f"完整備份恢復失敗: {e}")
            return False

    async def _restore_incremental_backup(
        self, backup_path: Path, record: BackupRecord, metadata: Dict
    ) -> bool:
        """恢復增量備份"""
        try:
            # 先恢復基準備份
            base_backup_id = metadata.get("base_backup")
            if base_backup_id:
                base_success = await self.restore_backup(base_backup_id)
                if not base_success:
                    logger.error("❌ 基準備份恢復失敗")
                    return False

            # 再應用增量變更
            config_path = backup_path / "config"
            if config_path.exists():
                for item in config_path.rglob("*"):
                    if item.is_file():
                        relative_path = item.relative_to(config_path)
                        target_path = self.workspace_root / relative_path
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, target_path)

            return True

        except Exception as e:
            logger.error(f"增量備份恢復失敗: {e}")
            return False

    async def _restore_container_data(
        self, container_name: str, data_path: Path
    ) -> bool:
        """恢復容器數據"""
        try:
            if "mongo" in container_name:
                # 恢復 MongoDB 數據
                restore_cmd = [
                    "docker",
                    "exec",
                    container_name,
                    "mongorestore",
                    "--gzip",
                    "/tmp/backup",
                ]

                # 先複製數據到容器
                copy_cmd = ["docker", "cp", str(data_path), f"{container_name}:/tmp/"]

                process = await asyncio.create_subprocess_exec(*copy_cmd)
                await process.communicate()

                if process.returncode == 0:
                    process = await asyncio.create_subprocess_exec(*restore_cmd)
                    await process.communicate()
                    return process.returncode == 0

            elif "postgis" in container_name:
                # 恢復 PostgreSQL 數據
                dump_file = data_path.parent / f"{container_name}_dump.sql"
                if dump_file.exists():
                    restore_cmd = [
                        "docker",
                        "exec",
                        "-i",
                        container_name,
                        "psql",
                        "-U",
                        "postgres",
                    ]

                    with open(dump_file, "r") as f:
                        process = await asyncio.create_subprocess_exec(
                            *restore_cmd,
                            stdin=f,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                        )

                        await process.communicate()
                        return process.returncode == 0

            return True

        except Exception as e:
            logger.error(f"容器數據恢復失敗: {e}")
            return False

    async def _restore_docker_volume(self, volume_name: str, volume_path: Path) -> bool:
        """恢復 Docker volume"""
        try:
            restore_cmd = [
                "docker",
                "run",
                "--rm",
                "-v",
                f"{volume_name}:/target",
                "-v",
                f"{volume_path}:/source",
                "alpine",
                "cp",
                "-a",
                "/source/.",
                "/target/",
            ]

            process = await asyncio.create_subprocess_exec(*restore_cmd)
            await process.communicate()

            return process.returncode == 0

        except Exception as e:
            logger.error(f"Docker volume 恢復失敗: {e}")
            return False

    async def _save_backup_metadata(self, record: BackupRecord):
        """保存備份元數據"""
        try:
            metadata_file = self.backup_dir / f"{record.backup_id}_metadata.json"

            metadata = {
                "backup_id": record.backup_id,
                "service_type": record.service_type.value,
                "backup_type": record.backup_type.value,
                "status": record.status.value,
                "start_time": record.start_time.isoformat(),
                "end_time": record.end_time.isoformat() if record.end_time else None,
                "duration_seconds": record.duration_seconds,
                "file_path": record.file_path,
                "file_size_bytes": record.file_size_bytes,
                "checksum": record.checksum,
                "error_message": record.error_message,
                "metadata": record.metadata,
            }

            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"保存備份元數據失敗: {e}")

    async def cleanup_old_backups(self):
        """清理過期備份"""
        logger.info("🧹 開始清理過期備份...")

        current_time = datetime.utcnow()
        cleaned_count = 0

        for record in self.backup_history[:]:  # 複製列表避免修改問題
            retention_days = self.retention_policy.get(record.backup_type, 30)
            expiry_time = record.start_time + timedelta(days=retention_days)

            if current_time > expiry_time:
                # 刪除備份文件
                if record.file_path and Path(record.file_path).exists():
                    Path(record.file_path).unlink()

                # 刪除元數據文件
                metadata_file = self.backup_dir / f"{record.backup_id}_metadata.json"
                if metadata_file.exists():
                    metadata_file.unlink()

                # 從歷史記錄中移除
                self.backup_history.remove(record)
                cleaned_count += 1

                logger.info(f"🗑️ 已清理過期備份: {record.backup_id}")

        logger.info(f"✅ 清理完成，共清理 {cleaned_count} 個過期備份")

    def list_backups(
        self, service_type: Optional[ServiceType] = None, limit: int = 20
    ) -> List[BackupRecord]:
        """列出備份記錄"""
        filtered_backups = self.backup_history

        if service_type:
            filtered_backups = [
                b for b in filtered_backups if b.service_type == service_type
            ]

        # 按時間倒序排列
        sorted_backups = sorted(
            filtered_backups, key=lambda x: x.start_time, reverse=True
        )

        return sorted_backups[:limit]

    def get_backup_info(self, backup_id: str) -> Optional[BackupRecord]:
        """獲取備份信息"""
        for record in self.backup_history:
            if record.backup_id == backup_id:
                return record
        return None


# 全局備份管理器實例
backup_manager = BackupManager()
