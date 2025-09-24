"""
文件處理工具

整合來源：
- 各Stage的文件輸入輸出處理
- JSON/CSV文件讀寫
- 數據持久化邏輯
"""

import json
import csv
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import gzip
import pickle


logger = logging.getLogger(__name__)


class FileUtils:
    """文件處理工具類"""

    @staticmethod
    def ensure_directory_exists(directory_path: Union[str, Path]) -> bool:
        """
        確保目錄存在，如不存在則創建

        Args:
            directory_path: 目錄路徑

        Returns:
            是否成功創建或已存在
        """
        try:
            Path(directory_path).mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"創建目錄失敗: {directory_path}, error: {e}")
            return False

    @staticmethod
    def read_json_file(file_path: Union[str, Path], default: Any = None) -> Any:
        """
        讀取JSON文件

        Args:
            file_path: 文件路徑
            default: 讀取失敗時的默認值

        Returns:
            JSON數據或默認值
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, IOError) as e:
            logger.error(f"讀取JSON文件失敗: {file_path}, error: {e}")
            return default

    @staticmethod
    def write_json_file(file_path: Union[str, Path], data: Any, create_dirs: bool = True, indent: int = 2) -> bool:
        """
        寫入JSON文件

        Args:
            file_path: 文件路徑
            data: 要寫入的數據
            create_dirs: 是否自動創建目錄
            indent: JSON格式化縮進

        Returns:
            是否寫入成功
        """
        try:
            file_path = Path(file_path)

            if create_dirs:
                FileUtils.ensure_directory_exists(file_path.parent)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False, default=FileUtils._json_serializer)

            return True

        except Exception as e:
            logger.error(f"寫入JSON文件失敗: {file_path}, error: {e}")
            return False

    @staticmethod
    def read_csv_file(file_path: Union[str, Path], delimiter: str = ',') -> List[Dict[str, Any]]:
        """
        讀取CSV文件

        Args:
            file_path: 文件路徑
            delimiter: 分隔符

        Returns:
            CSV數據列表
        """
        try:
            data = []
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                for row in reader:
                    data.append(dict(row))
            return data

        except Exception as e:
            logger.error(f"讀取CSV文件失敗: {file_path}, error: {e}")
            return []

    @staticmethod
    def write_csv_file(file_path: Union[str, Path], data: List[Dict[str, Any]],
                      fieldnames: Optional[List[str]] = None, create_dirs: bool = True) -> bool:
        """
        寫入CSV文件

        Args:
            file_path: 文件路徑
            data: 要寫入的數據
            fieldnames: 字段名列表，如為None則自動獲取
            create_dirs: 是否自動創建目錄

        Returns:
            是否寫入成功
        """
        try:
            if not data:
                return True

            file_path = Path(file_path)

            if create_dirs:
                FileUtils.ensure_directory_exists(file_path.parent)

            if fieldnames is None:
                fieldnames = list(data[0].keys())

            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)

            return True

        except Exception as e:
            logger.error(f"寫入CSV文件失敗: {file_path}, error: {e}")
            return False

    @staticmethod
    def read_text_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
        """
        讀取文本文件

        Args:
            file_path: 文件路徑
            encoding: 編碼格式

        Returns:
            文件內容或None
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except Exception as e:
            logger.error(f"讀取文本文件失敗: {file_path}, error: {e}")
            return None

    @staticmethod
    def write_text_file(file_path: Union[str, Path], content: str,
                       encoding: str = 'utf-8', create_dirs: bool = True) -> bool:
        """
        寫入文本文件

        Args:
            file_path: 文件路徑
            content: 文件內容
            encoding: 編碼格式
            create_dirs: 是否自動創建目錄

        Returns:
            是否寫入成功
        """
        try:
            file_path = Path(file_path)

            if create_dirs:
                FileUtils.ensure_directory_exists(file_path.parent)

            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)

            return True

        except Exception as e:
            logger.error(f"寫入文本文件失敗: {file_path}, error: {e}")
            return False

    @staticmethod
    def copy_file(source: Union[str, Path], destination: Union[str, Path], create_dirs: bool = True) -> bool:
        """
        複製文件

        Args:
            source: 源文件路徑
            destination: 目標文件路徑
            create_dirs: 是否自動創建目標目錄

        Returns:
            是否複製成功
        """
        try:
            destination = Path(destination)

            if create_dirs:
                FileUtils.ensure_directory_exists(destination.parent)

            shutil.copy2(source, destination)
            return True

        except Exception as e:
            logger.error(f"複製文件失敗: {source} -> {destination}, error: {e}")
            return False

    @staticmethod
    def move_file(source: Union[str, Path], destination: Union[str, Path], create_dirs: bool = True) -> bool:
        """
        移動文件

        Args:
            source: 源文件路徑
            destination: 目標文件路徑
            create_dirs: 是否自動創建目標目錄

        Returns:
            是否移動成功
        """
        try:
            destination = Path(destination)

            if create_dirs:
                FileUtils.ensure_directory_exists(destination.parent)

            shutil.move(source, destination)
            return True

        except Exception as e:
            logger.error(f"移動文件失敗: {source} -> {destination}, error: {e}")
            return False

    @staticmethod
    def delete_file(file_path: Union[str, Path]) -> bool:
        """
        刪除文件

        Args:
            file_path: 文件路徑

        Returns:
            是否刪除成功
        """
        try:
            Path(file_path).unlink(missing_ok=True)
            return True
        except Exception as e:
            logger.error(f"刪除文件失敗: {file_path}, error: {e}")
            return False

    @staticmethod
    def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        獲取文件信息

        Args:
            file_path: 文件路徑

        Returns:
            文件信息字典
        """
        try:
            path = Path(file_path)
            stat = path.stat()

            return {
                'exists': path.exists(),
                'is_file': path.is_file(),
                'is_directory': path.is_dir(),
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created_time': datetime.fromtimestamp(stat.st_ctime),
                'modified_time': datetime.fromtimestamp(stat.st_mtime),
                'accessed_time': datetime.fromtimestamp(stat.st_atime),
                'permissions': oct(stat.st_mode)[-3:],
                'name': path.name,
                'suffix': path.suffix,
                'parent': str(path.parent)
            }

        except Exception as e:
            logger.error(f"獲取文件信息失敗: {file_path}, error: {e}")
            return {'exists': False, 'error': str(e)}

    @staticmethod
    def list_files(directory: Union[str, Path], pattern: str = "*", recursive: bool = False) -> List[Path]:
        """
        列出目錄中的文件

        Args:
            directory: 目錄路徑
            pattern: 文件名模式
            recursive: 是否遞歸搜索

        Returns:
            文件路徑列表
        """
        try:
            directory = Path(directory)

            if not directory.exists():
                return []

            if recursive:
                files = list(directory.rglob(pattern))
            else:
                files = list(directory.glob(pattern))

            # 只返回文件，不包括目錄
            return [f for f in files if f.is_file()]

        except Exception as e:
            logger.error(f"列出文件失敗: {directory}, error: {e}")
            return []

    @staticmethod
    def cleanup_old_files(directory: Union[str, Path], max_age_days: int, pattern: str = "*") -> int:
        """
        清理舊文件

        Args:
            directory: 目錄路徑
            max_age_days: 最大保留天數
            pattern: 文件名模式

        Returns:
            刪除的文件數量
        """
        try:
            current_time = datetime.now().timestamp()
            max_age_seconds = max_age_days * 24 * 3600
            deleted_count = 0

            files = FileUtils.list_files(directory, pattern)

            for file_path in files:
                try:
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        deleted_count += 1
                        logger.debug(f"刪除舊文件: {file_path}")
                except Exception as e:
                    logger.warning(f"刪除文件失敗: {file_path}, error: {e}")

            logger.info(f"清理舊文件完成: {directory}, 刪除 {deleted_count} 個文件")
            return deleted_count

        except Exception as e:
            logger.error(f"清理舊文件失敗: {directory}, error: {e}")
            return 0

    @staticmethod
    def backup_file(file_path: Union[str, Path], backup_suffix: str = None) -> Optional[Path]:
        """
        備份文件

        Args:
            file_path: 原文件路徑
            backup_suffix: 備份後綴，如為None則使用時間戳

        Returns:
            備份文件路徑或None
        """
        try:
            file_path = Path(file_path)

            if not file_path.exists():
                logger.warning(f"要備份的文件不存在: {file_path}")
                return None

            if backup_suffix is None:
                backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")

            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup_{backup_suffix}")

            if FileUtils.copy_file(file_path, backup_path):
                logger.info(f"文件備份成功: {file_path} -> {backup_path}")
                return backup_path
            else:
                return None

        except Exception as e:
            logger.error(f"文件備份失敗: {file_path}, error: {e}")
            return None

    @staticmethod
    def compress_file(file_path: Union[str, Path], compression_level: int = 6) -> Optional[Path]:
        """
        壓縮文件（使用gzip）

        Args:
            file_path: 文件路徑
            compression_level: 壓縮級別 (1-9)

        Returns:
            壓縮文件路徑或None
        """
        try:
            file_path = Path(file_path)
            compressed_path = file_path.with_suffix(f"{file_path.suffix}.gz")

            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb', compresslevel=compression_level) as f_out:
                    shutil.copyfileobj(f_in, f_out)

            logger.info(f"文件壓縮成功: {file_path} -> {compressed_path}")
            return compressed_path

        except Exception as e:
            logger.error(f"文件壓縮失敗: {file_path}, error: {e}")
            return None

    @staticmethod
    def decompress_file(compressed_path: Union[str, Path]) -> Optional[Path]:
        """
        解壓縮文件（gzip格式）

        Args:
            compressed_path: 壓縮文件路徑

        Returns:
            解壓文件路徑或None
        """
        try:
            compressed_path = Path(compressed_path)

            if compressed_path.suffix == '.gz':
                output_path = compressed_path.with_suffix('')
            else:
                output_path = compressed_path.with_suffix('.decompressed')

            with gzip.open(compressed_path, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            logger.info(f"文件解壓成功: {compressed_path} -> {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"文件解壓失敗: {compressed_path}, error: {e}")
            return None

    @staticmethod
    def save_pickle(file_path: Union[str, Path], data: Any, create_dirs: bool = True) -> bool:
        """
        保存pickle文件

        Args:
            file_path: 文件路徑
            data: 要保存的數據
            create_dirs: 是否自動創建目錄

        Returns:
            是否保存成功
        """
        try:
            file_path = Path(file_path)

            if create_dirs:
                FileUtils.ensure_directory_exists(file_path.parent)

            with open(file_path, 'wb') as f:
                pickle.dump(data, f)

            return True

        except Exception as e:
            logger.error(f"保存pickle文件失敗: {file_path}, error: {e}")
            return False

    @staticmethod
    def load_pickle(file_path: Union[str, Path], default: Any = None) -> Any:
        """
        載入pickle文件

        Args:
            file_path: 文件路徑
            default: 載入失敗時的默認值

        Returns:
            載入的數據或默認值
        """
        try:
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"載入pickle文件失敗: {file_path}, error: {e}")
            return default

    @staticmethod
    def _json_serializer(obj):
        """JSON序列化器，處理datetime等特殊類型"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return str(obj)


# 便捷函數
def read_json(file_path: Union[str, Path], default: Any = None) -> Any:
    """便捷函數：讀取JSON文件"""
    return FileUtils.read_json_file(file_path, default)


def write_json(file_path: Union[str, Path], data: Any, indent: int = 2) -> bool:
    """便捷函數：寫入JSON文件"""
    return FileUtils.write_json_file(file_path, data, indent=indent)


def ensure_dir(directory_path: Union[str, Path]) -> bool:
    """便捷函數：確保目錄存在"""
    return FileUtils.ensure_directory_exists(directory_path)


def file_exists(file_path: Union[str, Path]) -> bool:
    """便捷函數：檢查文件是否存在"""
    return Path(file_path).exists()


def get_file_size(file_path: Union[str, Path]) -> int:
    """便捷函數：獲取文件大小"""
    try:
        return Path(file_path).stat().st_size
    except Exception:
        return 0


def create_timestamped_filename(base_name: str, extension: str = "") -> str:
    """便捷函數：創建帶時間戳的文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if extension and not extension.startswith('.'):
        extension = f".{extension}"
    return f"{base_name}_{timestamp}{extension}"