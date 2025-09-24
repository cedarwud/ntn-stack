"""
Storage Manager for Stage 6 Persistence API
統一存儲管理模組 - 替代原本8個backup_*檔案

Author: Claude Code
Created: 2025-09-21
Purpose: 提供統一的數據存儲、備份和恢復管理
"""

import json
import os
import logging
import shutil
import gzip
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class StorageMetadata:
    """存儲元數據"""
    data_id: str
    data_type: str
    timestamp: str
    version: str
    size_bytes: int
    checksum: str
    backup_policy: str
    retention_days: int


class StorageManager:
    """
    統一存儲管理器

    功能職責：
    - 統一存儲管理（替代8個分散的備份模組）
    - 多種存儲後端支援
    - 數據版本控制
    - 自動備份和恢復
    """

    def __init__(self, config: Optional[Dict] = None):
        """初始化存儲管理器"""
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 存儲配置
        self.storage_config = self.config.get('storage', {
            'primary_backend': 'filesystem',
            'backup_backend': 'filesystem',
            'compression_enabled': True,
            'retention_days': 30,
            'backup_frequency': 'daily'
        })

        # 存儲路徑配置
        self.primary_storage_path = Path(self.config.get('primary_storage_path', '/orbit-engine/data/storage'))
        self.backup_storage_path = Path(self.config.get('backup_storage_path', '/orbit-engine/data/backups'))

        # 創建存儲目錄
        self._ensure_storage_directories()

        # 存儲統計
        self.storage_stats = {
            'data_stored': 0,
            'backups_created': 0,
            'storage_size_mb': 0,
            'last_cleanup': None
        }

        self.logger.info("✅ Storage Manager 初始化完成")

    def _ensure_storage_directories(self) -> None:
        """確保存儲目錄存在"""
        self.primary_storage_path.mkdir(parents=True, exist_ok=True)
        self.backup_storage_path.mkdir(parents=True, exist_ok=True)

        # 創建子目錄
        for subdir in ['satellite_pools', 'animation_data', 'handover_events', 'metadata']:
            (self.primary_storage_path / subdir).mkdir(exist_ok=True)
            (self.backup_storage_path / subdir).mkdir(exist_ok=True)

    def store_data(self, data_type: str, data: Dict[str, Any], metadata: Optional[Dict] = None) -> str:
        """
        存儲數據到主要存儲

        Args:
            data_type: 數據類型 (satellite_pools, animation_data, handover_events)
            data: 要存儲的數據
            metadata: 額外的元數據

        Returns:
            數據ID
        """
        try:
            # 生成數據ID
            timestamp = datetime.now(timezone.utc)
            data_id = f"{data_type}_{timestamp.strftime('%Y%m%d_%H%M%S')}_{id(data) % 10000:04d}"

            # 準備存儲數據
            storage_data = {
                'data_id': data_id,
                'data_type': data_type,
                'timestamp': timestamp.isoformat(),
                'data': data,
                'metadata': metadata or {}
            }

            # 計算校驗和
            data_json = json.dumps(storage_data, sort_keys=True, default=str)
            checksum = hashlib.sha256(data_json.encode()).hexdigest()

            # 創建存儲元數據
            storage_metadata = StorageMetadata(
                data_id=data_id,
                data_type=data_type,
                timestamp=timestamp.isoformat(),
                version="1.0",
                size_bytes=len(data_json.encode()),
                checksum=checksum,
                backup_policy=self.storage_config['backup_frequency'],
                retention_days=self.storage_config['retention_days']
            )

            # 存儲到文件系統
            storage_path = self.primary_storage_path / data_type / f"{data_id}.json"
            metadata_path = self.primary_storage_path / 'metadata' / f"{data_id}_metadata.json"

            # 壓縮選項
            if self.storage_config['compression_enabled']:
                storage_path = storage_path.with_suffix('.json.gz')
                with gzip.open(storage_path, 'wt', encoding='utf-8') as f:
                    json.dump(storage_data, f, indent=2, ensure_ascii=False, default=str)
            else:
                with open(storage_path, 'w', encoding='utf-8') as f:
                    json.dump(storage_data, f, indent=2, ensure_ascii=False, default=str)

            # 存儲元數據
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(storage_metadata), f, indent=2, ensure_ascii=False)

            # 更新統計
            self.storage_stats['data_stored'] += 1
            self.storage_stats['storage_size_mb'] += storage_metadata.size_bytes / (1024 * 1024)

            self.logger.info(f"✅ 數據已存儲: {data_id}")
            return data_id

        except Exception as e:
            self.logger.error(f"❌ 存儲數據失敗: {e}")
            raise

    def backup_data(self, data_id: str, backup_policy: Optional[str] = None) -> bool:
        """
        根據策略備份數據

        Args:
            data_id: 數據ID
            backup_policy: 備份策略 (daily, weekly, manual)

        Returns:
            備份是否成功
        """
        try:
            # 查找原始數據
            data_info = self._find_data_by_id(data_id)
            if not data_info:
                self.logger.error(f"❌ 找不到數據: {data_id}")
                return False

            # 讀取原始數據
            original_data = self.retrieve_data(data_id)
            if not original_data:
                return False

            # 創建備份
            backup_timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            backup_id = f"{data_id}_backup_{backup_timestamp}"

            backup_path = self.backup_storage_path / data_info['data_type'] / f"{backup_id}.json"

            # 備份數據包含原始數據 + 備份信息
            backup_data = {
                'original_data_id': data_id,
                'backup_id': backup_id,
                'backup_timestamp': datetime.now(timezone.utc).isoformat(),
                'backup_policy': backup_policy or self.storage_config['backup_frequency'],
                'original_data': original_data
            }

            # 壓縮備份
            if self.storage_config['compression_enabled']:
                backup_path = backup_path.with_suffix('.json.gz')
                with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)
            else:
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)

            # 更新統計
            self.storage_stats['backups_created'] += 1

            self.logger.info(f"✅ 數據已備份: {data_id} -> {backup_id}")
            return True

        except Exception as e:
            self.logger.error(f"❌ 備份數據失敗: {e}")
            return False

    def retrieve_data(self, data_id: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        檢索數據

        Args:
            data_id: 數據ID
            version: 版本號（可選）

        Returns:
            檢索到的數據
        """
        try:
            data_info = self._find_data_by_id(data_id)
            if not data_info:
                self.logger.warning(f"⚠️ 找不到數據: {data_id}")
                return None

            # 構建文件路徑
            data_path = data_info['file_path']

            # 讀取數據
            if data_path.suffix == '.gz':
                with gzip.open(data_path, 'rt', encoding='utf-8') as f:
                    stored_data = json.load(f)
            else:
                with open(data_path, 'r', encoding='utf-8') as f:
                    stored_data = json.load(f)

            self.logger.info(f"✅ 數據已檢索: {data_id}")
            return stored_data

        except Exception as e:
            self.logger.error(f"❌ 檢索數據失敗: {e}")
            return None

    def cleanup_old_data(self, retention_policy: Optional[Dict] = None) -> Dict[str, int]:
        """
        清理舊數據

        Args:
            retention_policy: 保留策略

        Returns:
            清理統計
        """
        try:
            policy = retention_policy or {
                'retention_days': self.storage_config['retention_days'],
                'keep_backups': True
            }

            cleanup_stats = {
                'files_deleted': 0,
                'space_freed_mb': 0,
                'backups_cleaned': 0
            }

            cutoff_date = datetime.now(timezone.utc).timestamp() - (policy['retention_days'] * 24 * 3600)

            # 清理主存儲
            cleanup_stats.update(self._cleanup_directory(self.primary_storage_path, cutoff_date))

            # 清理備份（如果允許）
            if not policy['keep_backups']:
                backup_cleanup = self._cleanup_directory(self.backup_storage_path, cutoff_date)
                cleanup_stats['backups_cleaned'] = backup_cleanup['files_deleted']
                cleanup_stats['space_freed_mb'] += backup_cleanup['space_freed_mb']

            # 更新統計
            self.storage_stats['last_cleanup'] = datetime.now(timezone.utc).isoformat()

            self.logger.info(f"✅ 清理完成: 刪除 {cleanup_stats['files_deleted']} 個文件，釋放 {cleanup_stats['space_freed_mb']:.2f} MB")
            return cleanup_stats

        except Exception as e:
            self.logger.error(f"❌ 清理舊數據失敗: {e}")
            return {'files_deleted': 0, 'space_freed_mb': 0, 'backups_cleaned': 0}

    def _find_data_by_id(self, data_id: str) -> Optional[Dict[str, Any]]:
        """通過ID查找數據文件"""
        try:
            # 搜索主存儲
            for data_type_dir in self.primary_storage_path.iterdir():
                if data_type_dir.is_dir() and data_type_dir.name != 'metadata':
                    for file_path in data_type_dir.glob(f"{data_id}.*"):
                        if file_path.is_file():
                            return {
                                'data_id': data_id,
                                'data_type': data_type_dir.name,
                                'file_path': file_path
                            }
            return None
        except Exception as e:
            self.logger.error(f"❌ 查找數據失敗: {e}")
            return None

    def _cleanup_directory(self, directory: Path, cutoff_timestamp: float) -> Dict[str, int]:
        """清理目錄中的舊文件"""
        stats = {'files_deleted': 0, 'space_freed_mb': 0}

        try:
            for file_path in directory.rglob("*.json*"):
                if file_path.is_file():
                    file_mtime = file_path.stat().st_mtime
                    if file_mtime < cutoff_timestamp:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        stats['files_deleted'] += 1
                        stats['space_freed_mb'] += file_size / (1024 * 1024)
        except Exception as e:
            self.logger.error(f"❌ 清理目錄失敗: {e}")

        return stats

    def get_storage_statistics(self) -> Dict[str, Any]:
        """獲取存儲統計信息"""
        try:
            # 計算當前存儲使用量
            total_size = 0
            total_files = 0

            for storage_path in [self.primary_storage_path, self.backup_storage_path]:
                for file_path in storage_path.rglob("*.json*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
                        total_files += 1

            current_stats = {
                'total_files': total_files,
                'total_size_mb': total_size / (1024 * 1024),
                'primary_storage_path': str(self.primary_storage_path),
                'backup_storage_path': str(self.backup_storage_path),
                'compression_enabled': self.storage_config['compression_enabled'],
                'retention_days': self.storage_config['retention_days']
            }

            # 合併歷史統計
            current_stats.update(self.storage_stats)

            return current_stats

        except Exception as e:
            self.logger.error(f"❌ 獲取存儲統計失敗: {e}")
            return {}

    def list_stored_data(self, data_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出存儲的數據"""
        try:
            data_list = []

            search_dirs = [self.primary_storage_path / data_type] if data_type else self.primary_storage_path.iterdir()

            for dir_path in search_dirs:
                if dir_path.is_dir() and dir_path.name != 'metadata':
                    for file_path in dir_path.glob("*.json*"):
                        if file_path.is_file():
                            # 讀取元數據
                            data_id = file_path.stem.replace('.json', '')
                            metadata_path = self.primary_storage_path / 'metadata' / f"{data_id}_metadata.json"

                            metadata = {}
                            if metadata_path.exists():
                                with open(metadata_path, 'r', encoding='utf-8') as f:
                                    metadata = json.load(f)

                            data_list.append({
                                'data_id': data_id,
                                'data_type': dir_path.name,
                                'file_path': str(file_path),
                                'file_size_mb': file_path.stat().st_size / (1024 * 1024),
                                'modified_time': datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc).isoformat(),
                                'metadata': metadata
                            })

            return sorted(data_list, key=lambda x: x['modified_time'], reverse=True)

        except Exception as e:
            self.logger.error(f"❌ 列出存儲數據失敗: {e}")
            return []