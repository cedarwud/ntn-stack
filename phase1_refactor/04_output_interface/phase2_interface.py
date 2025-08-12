#!/usr/bin/env python3
"""
Phase 1 → Phase 2 標準接口規範

功能:
1. 定義 Phase 1 到 Phase 2 的標準數據接口
2. 提供軌道數據查詢和傳輸規範
3. 確保數據格式標準化和版本兼容性

符合 CLAUDE.md 原則:
- 提供完整的軌道數據接口
- 確保數據格式的準確性和一致性
- 支援大規模數據傳輸
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Union, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import numpy as np
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class DataFormat(Enum):
    """數據格式類型"""
    JSON = "json"
    BINARY = "binary"
    COMPRESSED = "compressed"

class CoordinateSystem(Enum):
    """坐標系統類型"""
    ECI = "eci"  # Earth-Centered Inertial
    TEME = "teme"  # True Equator Mean Equinox
    GEODETIC = "geodetic"  # Latitude, Longitude, Altitude

@dataclass
class Phase1OrbitData:
    """Phase 1 軌道數據標準格式"""
    satellite_id: str
    constellation: str
    timestamp: datetime
    position_eci: List[float]  # [x, y, z] in km
    velocity_eci: List[float]  # [vx, vy, vz] in km/s
    position_teme: List[float]  # [x, y, z] in km
    velocity_teme: List[float]  # [vx, vy, vz] in km/s
    calculation_quality: float  # 計算品質指標 (0-1)
    error_code: int = 0
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Phase1DataBatch:
    """Phase 1 批量數據格式"""
    batch_id: str
    generation_time: datetime
    time_range_start: datetime
    time_range_end: datetime
    satellite_count: int
    total_records: int
    data_format: DataFormat
    coordinate_systems: List[CoordinateSystem]
    orbit_data: List[Phase1OrbitData]
    quality_metrics: Dict[str, float]
    version: str = "1.0"

@dataclass
class Phase1QueryRequest:
    """Phase 1 數據查詢請求"""
    request_id: str
    timestamp: datetime
    satellite_ids: Optional[List[str]] = None  # None = 全部
    constellations: Optional[List[str]] = None  # None = 全部
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    coordinate_system: CoordinateSystem = CoordinateSystem.ECI
    data_format: DataFormat = DataFormat.JSON
    max_records: int = 10000
    include_metadata: bool = False

@dataclass
class Phase1QueryResponse:
    """Phase 1 數據查詢響應"""
    request_id: str
    response_time: datetime
    success: bool
    total_matches: int
    returned_records: int
    has_more_data: bool
    data_batch: Optional[Phase1DataBatch] = None
    error_message: Optional[str] = None
    performance_metrics: Optional[Dict[str, float]] = None

class Phase1DataProvider(ABC):
    """Phase 1 數據提供者抽象基類"""
    
    @abstractmethod
    def query_orbit_data(self, request: Phase1QueryRequest) -> Phase1QueryResponse:
        """查詢軌道數據"""
        pass
    
    @abstractmethod
    def get_available_satellites(self) -> List[str]:
        """獲取可用衛星列表"""
        pass
    
    @abstractmethod
    def get_data_coverage(self) -> Dict[str, Any]:
        """獲取數據覆蓋範圍"""
        pass
    
    @abstractmethod
    def validate_data_integrity(self) -> bool:
        """驗證數據完整性"""
        pass

class Phase1StandardInterface:
    """Phase 1 標準接口實現"""
    
    def __init__(self, data_provider: Phase1DataProvider):
        """
        初始化標準接口
        
        Args:
            data_provider: Phase 1 數據提供者實例
        """
        self.data_provider = data_provider
        self.interface_version = "1.0"
        self.supported_formats = [DataFormat.JSON, DataFormat.BINARY, DataFormat.COMPRESSED]
        self.supported_coordinates = [CoordinateSystem.ECI, CoordinateSystem.TEME]
        
        logger.info("✅ Phase 1 標準接口初始化完成")
    
    def create_query_request(self, 
                           satellite_ids: Optional[List[str]] = None,
                           constellations: Optional[List[str]] = None,
                           time_range: Optional[Tuple[datetime, datetime]] = None,
                           coordinate_system: CoordinateSystem = CoordinateSystem.ECI,
                           data_format: DataFormat = DataFormat.JSON,
                           max_records: int = 10000) -> Phase1QueryRequest:
        """
        創建標準查詢請求
        
        Args:
            satellite_ids: 指定衛星 ID 列表
            constellations: 指定星座列表
            time_range: 時間範圍 (start, end)
            coordinate_system: 坐標系統
            data_format: 數據格式
            max_records: 最大記錄數
            
        Returns:
            Phase1QueryRequest: 標準查詢請求
        """
        import uuid
        
        request = Phase1QueryRequest(
            request_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            satellite_ids=satellite_ids,
            constellations=constellations,
            time_range_start=time_range[0] if time_range else None,
            time_range_end=time_range[1] if time_range else None,
            coordinate_system=coordinate_system,
            data_format=data_format,
            max_records=max_records,
            include_metadata=True
        )
        
        logger.debug(f"創建查詢請求: {request.request_id}")
        return request
    
    def execute_query(self, request: Phase1QueryRequest) -> Phase1QueryResponse:
        """
        執行查詢請求
        
        Args:
            request: 查詢請求
            
        Returns:
            Phase1QueryResponse: 查詢響應
        """
        try:
            logger.info(f"執行查詢請求: {request.request_id}")
            
            # 驗證請求
            validation_result = self._validate_request(request)
            if not validation_result['valid']:
                return Phase1QueryResponse(
                    request_id=request.request_id,
                    response_time=datetime.now(timezone.utc),
                    success=False,
                    total_matches=0,
                    returned_records=0,
                    has_more_data=False,
                    error_message=validation_result['error']
                )
            
            # 執行數據查詢
            start_time = datetime.now(timezone.utc)
            response = self.data_provider.query_orbit_data(request)
            end_time = datetime.now(timezone.utc)
            
            # 添加性能指標
            if response.success:
                query_time = (end_time - start_time).total_seconds()
                response.performance_metrics = {
                    'query_time_seconds': query_time,
                    'records_per_second': response.returned_records / max(query_time, 0.001),
                    'data_completeness': response.returned_records / max(response.total_matches, 1)
                }
            
            logger.info(f"查詢完成: {request.request_id}, 返回 {response.returned_records} 記錄")
            return response
            
        except Exception as e:
            logger.error(f"查詢執行失敗 {request.request_id}: {e}")
            return Phase1QueryResponse(
                request_id=request.request_id,
                response_time=datetime.now(timezone.utc),
                success=False,
                total_matches=0,
                returned_records=0,
                has_more_data=False,
                error_message=f"查詢執行異常: {e}"
            )
    
    def _validate_request(self, request: Phase1QueryRequest) -> Dict[str, Any]:
        """驗證查詢請求"""
        try:
            # 檢查數據格式支援
            if request.data_format not in self.supported_formats:
                return {
                    'valid': False,
                    'error': f"不支援的數據格式: {request.data_format.value}"
                }
            
            # 檢查坐標系統支援
            if request.coordinate_system not in self.supported_coordinates:
                return {
                    'valid': False,
                    'error': f"不支援的坐標系統: {request.coordinate_system.value}"
                }
            
            # 檢查記錄數限制
            if request.max_records <= 0 or request.max_records > 100000:
                return {
                    'valid': False,
                    'error': f"無效的記錄數限制: {request.max_records}"
                }
            
            # 檢查時間範圍
            if (request.time_range_start and request.time_range_end and 
                request.time_range_start >= request.time_range_end):
                return {
                    'valid': False,
                    'error': "無效的時間範圍"
                }
            
            return {'valid': True, 'error': None}
            
        except Exception as e:
            return {
                'valid': False,
                'error': f"請求驗證異常: {e}"
            }
    
    def get_interface_capabilities(self) -> Dict[str, Any]:
        """獲取接口能力信息"""
        try:
            data_coverage = self.data_provider.get_data_coverage()
            available_satellites = self.data_provider.get_available_satellites()
            
            capabilities = {
                "interface_version": self.interface_version,
                "supported_data_formats": [f.value for f in self.supported_formats],
                "supported_coordinate_systems": [c.value for c in self.supported_coordinates],
                "data_coverage": data_coverage,
                "available_satellites": {
                    "total_count": len(available_satellites),
                    "satellites": available_satellites[:100]  # 限制返回數量
                },
                "max_records_per_query": 100000,
                "data_integrity_validated": self.data_provider.validate_data_integrity()
            }
            
            return capabilities
            
        except Exception as e:
            logger.error(f"獲取接口能力失敗: {e}")
            return {
                "interface_version": self.interface_version,
                "error": f"獲取能力信息失敗: {e}"
            }
    
    def convert_data_format(self, 
                           data_batch: Phase1DataBatch, 
                           target_format: DataFormat) -> bytes:
        """
        轉換數據格式
        
        Args:
            data_batch: 原始數據批次
            target_format: 目標格式
            
        Returns:
            bytes: 轉換後的數據
        """
        try:
            if target_format == DataFormat.JSON:
                # 轉換為 JSON 格式
                data_dict = asdict(data_batch)
                
                # 處理 datetime 對象
                def datetime_converter(obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
                
                json_str = json.dumps(data_dict, default=datetime_converter, ensure_ascii=False, indent=2)
                return json_str.encode('utf-8')
                
            elif target_format == DataFormat.BINARY:
                # 轉換為二進制格式 (簡化實現)
                import pickle
                return pickle.dumps(data_batch)
                
            elif target_format == DataFormat.COMPRESSED:
                # 壓縮格式
                import gzip
                json_data = self.convert_data_format(data_batch, DataFormat.JSON)
                return gzip.compress(json_data)
                
            else:
                raise ValueError(f"不支援的目標格式: {target_format}")
                
        except Exception as e:
            logger.error(f"數據格式轉換失敗: {e}")
            raise
    
    def create_data_summary(self, data_batch: Phase1DataBatch) -> Dict[str, Any]:
        """創建數據摘要"""
        try:
            if not data_batch.orbit_data:
                return {"error": "無軌道數據"}
            
            # 統計信息
            constellations = set()
            satellites = set()
            position_magnitudes = []
            velocity_magnitudes = []
            quality_scores = []
            
            for orbit in data_batch.orbit_data:
                constellations.add(orbit.constellation)
                satellites.add(orbit.satellite_id)
                
                pos_mag = np.linalg.norm(orbit.position_eci)
                vel_mag = np.linalg.norm(orbit.velocity_eci)
                
                position_magnitudes.append(pos_mag)
                velocity_magnitudes.append(vel_mag)
                quality_scores.append(orbit.calculation_quality)
            
            summary = {
                "batch_info": {
                    "batch_id": data_batch.batch_id,
                    "generation_time": data_batch.generation_time.isoformat(),
                    "time_range": {
                        "start": data_batch.time_range_start.isoformat(),
                        "end": data_batch.time_range_end.isoformat()
                    },
                    "version": data_batch.version
                },
                "data_statistics": {
                    "total_records": len(data_batch.orbit_data),
                    "unique_satellites": len(satellites),
                    "constellations": list(constellations),
                    "constellation_count": len(constellations)
                },
                "orbit_statistics": {
                    "position_range_km": {
                        "min": float(np.min(position_magnitudes)),
                        "max": float(np.max(position_magnitudes)),
                        "mean": float(np.mean(position_magnitudes)),
                        "std": float(np.std(position_magnitudes))
                    },
                    "velocity_range_km_per_s": {
                        "min": float(np.min(velocity_magnitudes)),
                        "max": float(np.max(velocity_magnitudes)),
                        "mean": float(np.mean(velocity_magnitudes)),
                        "std": float(np.std(velocity_magnitudes))
                    }
                },
                "quality_metrics": {
                    "average_quality": float(np.mean(quality_scores)),
                    "min_quality": float(np.min(quality_scores)),
                    "records_high_quality": sum(1 for q in quality_scores if q >= 0.95),
                    "overall_batch_quality": data_batch.quality_metrics
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"創建數據摘要失敗: {e}")
            return {"error": f"摘要生成失敗: {e}"}

# 便利函數
def create_standard_interface(data_provider: Phase1DataProvider) -> Phase1StandardInterface:
    """創建標準接口實例"""
    return Phase1StandardInterface(data_provider)

def validate_orbit_data_format(orbit_data: Phase1OrbitData) -> Dict[str, bool]:
    """驗證軌道數據格式"""
    try:
        validation = {
            "has_satellite_id": bool(orbit_data.satellite_id),
            "has_constellation": bool(orbit_data.constellation),
            "has_valid_timestamp": isinstance(orbit_data.timestamp, datetime),
            "has_position_eci": (len(orbit_data.position_eci) == 3 and 
                               all(isinstance(x, (int, float)) for x in orbit_data.position_eci)),
            "has_velocity_eci": (len(orbit_data.velocity_eci) == 3 and 
                               all(isinstance(x, (int, float)) for x in orbit_data.velocity_eci)),
            "has_position_teme": (len(orbit_data.position_teme) == 3 and 
                                all(isinstance(x, (int, float)) for x in orbit_data.position_teme)),
            "has_velocity_teme": (len(orbit_data.velocity_teme) == 3 and 
                                all(isinstance(x, (int, float)) for x in orbit_data.velocity_teme)),
            "has_valid_quality": (0.0 <= orbit_data.calculation_quality <= 1.0),
        }
        
        # 檢查軌道高度合理性 (200-2000 km)
        earth_radius = 6371.0
        altitude = np.linalg.norm(orbit_data.position_eci) - earth_radius
        validation["reasonable_altitude"] = 200 <= altitude <= 2000
        
        # 檢查軌道速度合理性 (6-8 km/s)
        speed = np.linalg.norm(orbit_data.velocity_eci)
        validation["reasonable_velocity"] = 6.0 <= speed <= 8.0
        
        return validation
        
    except Exception as e:
        logger.error(f"軌道數據格式驗證失敗: {e}")
        return {"validation_error": False}

if __name__ == "__main__":
    # 測試用例
    print("Phase 1 → Phase 2 標準接口規範測試")
    print("=" * 50)
    
    # 測試數據結構
    test_orbit = Phase1OrbitData(
        satellite_id="TEST_001",
        constellation="test",
        timestamp=datetime.now(timezone.utc),
        position_eci=[7000.0, 0.0, 0.0],
        velocity_eci=[0.0, 7.5, 0.0],
        position_teme=[7000.0, 0.0, 0.0],
        velocity_teme=[0.0, 7.5, 0.0],
        calculation_quality=0.99
    )
    
    # 驗證格式
    validation = validate_orbit_data_format(test_orbit)
    print(f"軌道數據格式驗證: {all(validation.values())}")
    
    # 測試查詢請求
    test_request = Phase1QueryRequest(
        request_id="test_001",
        timestamp=datetime.now(timezone.utc),
        satellite_ids=["TEST_001"],
        coordinate_system=CoordinateSystem.ECI,
        data_format=DataFormat.JSON,
        max_records=1000
    )
    
    print(f"查詢請求創建: {test_request.request_id}")
    print("✅ 標準接口規範測試完成")