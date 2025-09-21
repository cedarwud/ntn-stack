"""
數據接口定義

整合來源：
- shared/core_modules/data_flow_protocol.py (數據流協議)
- 各Stage的數據結構定義

定義統一的數據傳輸和存儲接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, Iterator, Protocol, runtime_checkable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging


class DataFormat(Enum):
    """數據格式枚舉"""
    JSON = "json"
    CSV = "csv"
    PICKLE = "pickle"
    NUMPY = "numpy"
    PANDAS = "pandas"
    BINARY = "binary"


class DataSourceType(Enum):
    """數據源類型枚舉"""
    FILE = "file"
    DATABASE = "database"
    API = "api"
    MEMORY = "memory"
    STREAM = "stream"


@dataclass
class DataMetadata:
    """數據元數據"""
    source_type: DataSourceType
    format: DataFormat
    size_bytes: int = 0
    record_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    schema_version: str = "1.0"
    encoding: str = "utf-8"
    compression: Optional[str] = None
    checksum: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'source_type': self.source_type.value,
            'format': self.format.value,
            'size_bytes': self.size_bytes,
            'record_count': self.record_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'schema_version': self.schema_version,
            'encoding': self.encoding,
            'compression': self.compression,
            'checksum': self.checksum,
            'tags': self.tags
        }


@dataclass
class DataPacket:
    """數據包"""
    data: Any
    metadata: DataMetadata
    packet_id: str
    stage_number: Optional[int] = None
    timestamp: datetime = field(default_factory=datetime.now)
    parent_packet_id: Optional[str] = None
    child_packet_ids: List[str] = field(default_factory=list)

    def get_size(self) -> int:
        """獲取數據包大小"""
        return self.metadata.size_bytes

    def get_record_count(self) -> int:
        """獲取記錄數量"""
        return self.metadata.record_count

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典（不包含實際數據）"""
        return {
            'packet_id': self.packet_id,
            'stage_number': self.stage_number,
            'timestamp': self.timestamp.isoformat(),
            'parent_packet_id': self.parent_packet_id,
            'child_packet_ids': self.child_packet_ids,
            'metadata': self.metadata.to_dict()
        }


class DataReader(ABC):
    """數據讀取器接口"""

    @abstractmethod
    def read(self, source: Any) -> DataPacket:
        """
        讀取數據

        Args:
            source: 數據源

        Returns:
            數據包
        """
        pass

    @abstractmethod
    def read_batch(self, source: Any, batch_size: int) -> Iterator[DataPacket]:
        """
        批量讀取數據

        Args:
            source: 數據源
            batch_size: 批量大小

        Returns:
            數據包迭代器
        """
        pass

    @abstractmethod
    def validate_source(self, source: Any) -> Dict[str, Any]:
        """
        驗證數據源

        Args:
            source: 數據源

        Returns:
            驗證結果
        """
        pass

    @abstractmethod
    def get_metadata(self, source: Any) -> DataMetadata:
        """
        獲取數據源元數據

        Args:
            source: 數據源

        Returns:
            元數據
        """
        pass


class DataWriter(ABC):
    """數據寫入器接口"""

    @abstractmethod
    def write(self, data_packet: DataPacket, destination: Any) -> bool:
        """
        寫入數據

        Args:
            data_packet: 數據包
            destination: 目標位置

        Returns:
            是否寫入成功
        """
        pass

    @abstractmethod
    def write_batch(self, data_packets: List[DataPacket], destination: Any) -> Dict[str, Any]:
        """
        批量寫入數據

        Args:
            data_packets: 數據包列表
            destination: 目標位置

        Returns:
            寫入結果 {'success_count': int, 'error_count': int, 'errors': List[str]}
        """
        pass

    @abstractmethod
    def validate_destination(self, destination: Any) -> Dict[str, Any]:
        """
        驗證目標位置

        Args:
            destination: 目標位置

        Returns:
            驗證結果
        """
        pass

    @abstractmethod
    def ensure_destination(self, destination: Any) -> bool:
        """
        確保目標位置存在

        Args:
            destination: 目標位置

        Returns:
            是否創建成功
        """
        pass


class DataTransformer(ABC):
    """數據轉換器接口"""

    @abstractmethod
    def transform(self, input_packet: DataPacket) -> DataPacket:
        """
        轉換數據

        Args:
            input_packet: 輸入數據包

        Returns:
            轉換後的數據包
        """
        pass

    @abstractmethod
    def transform_batch(self, input_packets: List[DataPacket]) -> List[DataPacket]:
        """
        批量轉換數據

        Args:
            input_packets: 輸入數據包列表

        Returns:
            轉換後的數據包列表
        """
        pass

    @abstractmethod
    def validate_transform(self, input_packet: DataPacket, output_packet: DataPacket) -> Dict[str, Any]:
        """
        驗證轉換結果

        Args:
            input_packet: 輸入數據包
            output_packet: 輸出數據包

        Returns:
            驗證結果
        """
        pass

    @abstractmethod
    def get_transform_rules(self) -> Dict[str, Any]:
        """
        獲取轉換規則

        Returns:
            轉換規則
        """
        pass


@runtime_checkable
class DataSchema(Protocol):
    """數據結構協議"""

    def validate(self, data: Any) -> Dict[str, Any]:
        """驗證數據結構"""
        ...

    def get_fields(self) -> List[str]:
        """獲取字段列表"""
        ...

    def get_field_type(self, field_name: str) -> type:
        """獲取字段類型"""
        ...

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        ...


class DataValidator(ABC):
    """數據驗證器接口"""

    @abstractmethod
    def validate_data(self, data_packet: DataPacket) -> Dict[str, Any]:
        """
        驗證數據

        Args:
            data_packet: 數據包

        Returns:
            驗證結果
        """
        pass

    @abstractmethod
    def validate_schema(self, data: Any, schema: DataSchema) -> Dict[str, Any]:
        """
        驗證數據結構

        Args:
            data: 數據
            schema: 數據結構

        Returns:
            驗證結果
        """
        pass

    @abstractmethod
    def validate_integrity(self, data_packet: DataPacket) -> Dict[str, Any]:
        """
        驗證數據完整性

        Args:
            data_packet: 數據包

        Returns:
            驗證結果
        """
        pass

    @abstractmethod
    def get_validation_rules(self) -> Dict[str, Any]:
        """
        獲取驗證規則

        Returns:
            驗證規則
        """
        pass


class DataRepository(ABC):
    """數據存儲庫接口"""

    @abstractmethod
    def store(self, data_packet: DataPacket) -> str:
        """
        存儲數據

        Args:
            data_packet: 數據包

        Returns:
            存儲ID
        """
        pass

    @abstractmethod
    def retrieve(self, packet_id: str) -> Optional[DataPacket]:
        """
        檢索數據

        Args:
            packet_id: 數據包ID

        Returns:
            數據包或None
        """
        pass

    @abstractmethod
    def update(self, packet_id: str, data_packet: DataPacket) -> bool:
        """
        更新數據

        Args:
            packet_id: 數據包ID
            data_packet: 新的數據包

        Returns:
            是否更新成功
        """
        pass

    @abstractmethod
    def delete(self, packet_id: str) -> bool:
        """
        刪除數據

        Args:
            packet_id: 數據包ID

        Returns:
            是否刪除成功
        """
        pass

    @abstractmethod
    def list_packets(self, stage_number: Optional[int] = None,
                    start_time: Optional[datetime] = None,
                    end_time: Optional[datetime] = None) -> List[str]:
        """
        列出數據包

        Args:
            stage_number: 階段編號
            start_time: 開始時間
            end_time: 結束時間

        Returns:
            數據包ID列表
        """
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        獲取存儲統計

        Returns:
            統計信息
        """
        pass


class DataFlowManager(ABC):
    """數據流管理器接口"""

    @abstractmethod
    def create_flow(self, source_stage: int, target_stage: int, flow_config: Dict[str, Any]) -> str:
        """
        創建數據流

        Args:
            source_stage: 源階段
            target_stage: 目標階段
            flow_config: 流配置

        Returns:
            流ID
        """
        pass

    @abstractmethod
    def transfer_data(self, flow_id: str, data_packet: DataPacket) -> bool:
        """
        傳輸數據

        Args:
            flow_id: 流ID
            data_packet: 數據包

        Returns:
            是否傳輸成功
        """
        pass

    @abstractmethod
    def monitor_flow(self, flow_id: str) -> Dict[str, Any]:
        """
        監控數據流

        Args:
            flow_id: 流ID

        Returns:
            監控信息
        """
        pass

    @abstractmethod
    def close_flow(self, flow_id: str) -> bool:
        """
        關閉數據流

        Args:
            flow_id: 流ID

        Returns:
            是否關閉成功
        """
        pass


# 便捷函數
def create_data_packet(data: Any, source_type: DataSourceType, format: DataFormat,
                      packet_id: str, stage_number: Optional[int] = None) -> DataPacket:
    """便捷函數：創建數據包"""
    metadata = DataMetadata(
        source_type=source_type,
        format=format,
        created_at=datetime.now()
    )

    return DataPacket(
        data=data,
        metadata=metadata,
        packet_id=packet_id,
        stage_number=stage_number
    )


def create_validation_result(valid: bool, errors: Optional[List[str]] = None,
                           warnings: Optional[List[str]] = None,
                           details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """便捷函數：創建驗證結果"""
    return {
        'valid': valid,
        'errors': errors or [],
        'warnings': warnings or [],
        'details': details or {}
    }


def estimate_data_size(data: Any) -> int:
    """便捷函數：估算數據大小"""
    try:
        import sys
        return sys.getsizeof(data)
    except Exception:
        return 0