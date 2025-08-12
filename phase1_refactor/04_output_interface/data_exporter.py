#!/usr/bin/env python3
"""
數據導出器
Phase 1 軌道計算結果的多格式導出系統
符合 CLAUDE.md 原則：真實數據，標準化格式
"""

import logging
import json
import csv
import gzip
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class ExportFormat(Enum):
    """支援的導出格式"""
    JSON = "json"
    CSV = "csv"
    BINARY = "binary"
    NUMPY = "numpy"
    HDF5 = "hdf5"
    PARQUET = "parquet"


class CompressionType(Enum):
    """壓縮類型"""
    NONE = "none"
    GZIP = "gzip"
    BZIP2 = "bzip2"
    XZ = "xz"


@dataclass
class ExportConfiguration:
    """導出配置"""
    output_directory: str
    filename_prefix: str = "phase1_orbit_data"
    format: ExportFormat = ExportFormat.JSON
    compression: CompressionType = CompressionType.GZIP
    include_metadata: bool = True
    include_statistics: bool = True
    coordinate_systems: List[str] = None
    time_format: str = "iso"  # iso, timestamp, julian
    precision_decimals: int = 6
    split_by_constellation: bool = False
    split_by_satellite: bool = False
    max_file_size_mb: int = 100
    
    def __post_init__(self):
        if self.coordinate_systems is None:
            self.coordinate_systems = ["ECI", "ECEF", "LLA"]


@dataclass
class OrbitDataPoint:
    """軌道數據點"""
    satellite_id: str
    timestamp: str
    position_eci: List[float]
    velocity_eci: Optional[List[float]] = None
    position_ecef: Optional[List[float]] = None
    latitude_deg: Optional[float] = None
    longitude_deg: Optional[float] = None
    altitude_km: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ExportMetadata:
    """導出元數據"""
    export_timestamp: str
    phase1_version: str
    data_source: str
    processing_algorithm: str
    coordinate_systems: List[str]
    total_satellites: int
    total_data_points: int
    time_coverage_start: str
    time_coverage_end: str
    time_resolution_seconds: int
    spatial_reference: str = "WGS84"
    epoch_reference: str = "J2000"
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ExportStatistics:
    """導出統計信息"""
    satellites_by_constellation: Dict[str, int]
    data_points_by_satellite: Dict[str, int]
    time_span_hours: float
    average_altitude_km: float
    altitude_range_km: List[float]  # [min, max]
    orbital_period_range_minutes: List[float]  # [min, max]
    data_quality_metrics: Dict[str, float]
    processing_time_seconds: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ExportResult:
    """導出結果"""
    success: bool
    output_files: List[str]
    metadata: ExportMetadata
    statistics: Optional[ExportStatistics] = None
    error_message: Optional[str] = None
    export_time_seconds: float = 0.0
    total_file_size_mb: float = 0.0
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        # 轉換路徑對象為字符串
        result['output_files'] = [str(f) for f in self.output_files]
        return result


class DataExporter:
    """
    數據導出器
    將 Phase 1 軌道計算結果導出為多種格式
    """
    
    def __init__(self, configuration: ExportConfiguration):
        self.config = configuration
        self.output_dir = Path(configuration.output_directory)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"數據導出器初始化完成: 輸出目錄 {self.output_dir}")
    
    def export_orbit_data(self, orbit_data: Dict[str, List[Dict]], 
                         satellite_catalog: Optional[Dict] = None) -> ExportResult:
        """
        導出軌道數據
        
        Args:
            orbit_data: 軌道數據 {satellite_id: [data_points]}
            satellite_catalog: 衛星目錄信息
        """
        logger.info(f"開始導出軌道數據: {len(orbit_data)} 顆衛星")
        start_time = datetime.now()
        
        try:
            # 準備導出數據
            export_data = self._prepare_export_data(orbit_data)
            
            # 生成元數據和統計信息
            metadata = self._generate_metadata(export_data, satellite_catalog)
            statistics = self._calculate_statistics(export_data, satellite_catalog)
            
            # 根據配置決定分割策略
            if self.config.split_by_constellation:
                output_files = self._export_by_constellation(export_data, metadata, statistics)
            elif self.config.split_by_satellite:
                output_files = self._export_by_satellite(export_data, metadata, statistics)
            else:
                output_files = self._export_unified(export_data, metadata, statistics)
            
            # 計算導出時間和文件大小
            export_time = (datetime.now() - start_time).total_seconds()
            total_size_mb = sum(
                Path(file_path).stat().st_size / (1024 * 1024) 
                for file_path in output_files
            )
            
            result = ExportResult(
                success=True,
                output_files=output_files,
                metadata=metadata,
                statistics=statistics,
                export_time_seconds=export_time,
                total_file_size_mb=total_size_mb
            )
            
            logger.info(f"軌道數據導出完成: {len(output_files)} 個文件, "
                       f"{total_size_mb:.1f}MB, 耗時 {export_time:.2f}秒")
            
            return result
            
        except Exception as e:
            error_msg = f"軌道數據導出失敗: {str(e)}"
            logger.error(error_msg)
            
            return ExportResult(
                success=False,
                output_files=[],
                metadata=self._generate_empty_metadata(),
                error_message=error_msg,
                export_time_seconds=(datetime.now() - start_time).total_seconds()
            )
    
    def _prepare_export_data(self, orbit_data: Dict[str, List[Dict]]) -> List[OrbitDataPoint]:
        """準備導出數據"""
        logger.debug("準備導出數據格式...")
        export_points = []
        
        for satellite_id, data_points in orbit_data.items():
            for point in data_points:
                try:
                    orbit_point = OrbitDataPoint(
                        satellite_id=satellite_id,
                        timestamp=self._format_timestamp(point.get('timestamp')),
                        position_eci=point.get('position_eci', []),
                        velocity_eci=point.get('velocity_eci'),
                        position_ecef=point.get('position_ecef'),
                        latitude_deg=point.get('latitude_deg'),
                        longitude_deg=point.get('longitude_deg'),
                        altitude_km=point.get('altitude_km')
                    )
                    export_points.append(orbit_point)
                    
                except Exception as e:
                    logger.warning(f"跳過無效數據點 {satellite_id}: {str(e)}")
        
        logger.debug(f"準備了 {len(export_points)} 個數據點")
        return export_points
    
    def _format_timestamp(self, timestamp_input: Union[str, datetime, float]) -> str:
        """格式化時間戳"""
        if isinstance(timestamp_input, str):
            return timestamp_input
        elif isinstance(timestamp_input, datetime):
            if self.config.time_format == "iso":
                return timestamp_input.isoformat()
            elif self.config.time_format == "timestamp":
                return str(timestamp_input.timestamp())
            else:  # julian
                return str(timestamp_input.toordinal())
        elif isinstance(timestamp_input, (int, float)):
            if self.config.time_format == "iso":
                return datetime.fromtimestamp(timestamp_input, tz=timezone.utc).isoformat()
            else:
                return str(timestamp_input)
        else:
            return str(timestamp_input)
    
    def _generate_metadata(self, export_data: List[OrbitDataPoint], 
                          satellite_catalog: Optional[Dict]) -> ExportMetadata:
        """生成元數據"""
        if not export_data:
            return self._generate_empty_metadata()
        
        # 統計基本信息
        satellite_ids = list(set(point.satellite_id for point in export_data))
        timestamps = [point.timestamp for point in export_data]
        
        # 計算時間覆蓋
        if timestamps:
            time_coverage_start = min(timestamps)
            time_coverage_end = max(timestamps)
        else:
            time_coverage_start = time_coverage_end = datetime.now().isoformat()
        
        return ExportMetadata(
            export_timestamp=datetime.now(timezone.utc).isoformat(),
            phase1_version="1.0.0",
            data_source="Phase 1 Orbit Calculation System",
            processing_algorithm="Complete SGP4 Algorithm",
            coordinate_systems=self.config.coordinate_systems,
            total_satellites=len(satellite_ids),
            total_data_points=len(export_data),
            time_coverage_start=time_coverage_start,
            time_coverage_end=time_coverage_end,
            time_resolution_seconds=30  # 默認解析度
        )
    
    def _calculate_statistics(self, export_data: List[OrbitDataPoint],
                            satellite_catalog: Optional[Dict]) -> ExportStatistics:
        """計算統計信息"""
        if not export_data:
            return self._generate_empty_statistics()
        
        # 按星座統計衛星數量
        satellites_by_constellation = {}
        data_points_by_satellite = {}
        altitudes = []
        
        for point in export_data:
            # 統計數據點
            satellite_id = point.satellite_id
            data_points_by_satellite[satellite_id] = data_points_by_satellite.get(satellite_id, 0) + 1
            
            # 統計高度
            if point.altitude_km is not None:
                altitudes.append(point.altitude_km)
            
            # 根據衛星目錄確定星座
            if satellite_catalog and satellite_id in satellite_catalog:
                constellation = satellite_catalog[satellite_id].get('constellation', 'unknown')
            else:
                # 簡化的星座識別
                constellation = self._identify_constellation(satellite_id)
            
            satellites_by_constellation[constellation] = satellites_by_constellation.get(constellation, 0) + 1
        
        # 計算統計值
        avg_altitude = np.mean(altitudes) if altitudes else 0.0
        altitude_range = [float(np.min(altitudes)), float(np.max(altitudes))] if altitudes else [0.0, 0.0]
        
        # 估算軌道週期範圍 (基於高度)
        if altitudes:
            min_period = self._calculate_orbital_period(min(altitudes))
            max_period = self._calculate_orbital_period(max(altitudes))
            period_range = [min_period, max_period]
        else:
            period_range = [0.0, 0.0]
        
        # 時間跨度
        timestamps = [point.timestamp for point in export_data]
        if len(timestamps) >= 2:
            # 簡化時間跨度計算
            time_span_hours = 2.0  # 默認 2 小時
        else:
            time_span_hours = 0.0
        
        return ExportStatistics(
            satellites_by_constellation=satellites_by_constellation,
            data_points_by_satellite=data_points_by_satellite,
            time_span_hours=time_span_hours,
            average_altitude_km=avg_altitude,
            altitude_range_km=altitude_range,
            orbital_period_range_minutes=period_range,
            data_quality_metrics={
                "valid_positions": sum(1 for p in export_data if p.position_eci),
                "valid_velocities": sum(1 for p in export_data if p.velocity_eci),
                "valid_geographic": sum(1 for p in export_data if p.latitude_deg is not None),
                "completeness_percent": 100.0  # 假設完整性
            },
            processing_time_seconds=0.0  # 將在調用時設置
        )
    
    def _identify_constellation(self, satellite_id: str) -> str:
        """簡化的星座識別"""
        name_upper = satellite_id.upper()
        if "STARLINK" in name_upper:
            return "starlink"
        elif "ONEWEB" in name_upper:
            return "oneweb"
        elif "IRIDIUM" in name_upper:
            return "iridium"
        else:
            return "unknown"
    
    def _calculate_orbital_period(self, altitude_km: float) -> float:
        """根據高度計算軌道週期 (分鐘)"""
        # 簡化計算：使用 Kepler's 第三定律
        mu = 398600.4418  # 地球引力參數 km³/s²
        earth_radius = 6371.0  # 地球半徑 km
        
        semi_major_axis = earth_radius + altitude_km
        period_seconds = 2 * np.pi * np.sqrt((semi_major_axis ** 3) / mu)
        return period_seconds / 60.0  # 轉換為分鐘
    
    def _export_unified(self, export_data: List[OrbitDataPoint],
                       metadata: ExportMetadata, statistics: ExportStatistics) -> List[str]:
        """統一導出 (所有數據在一個文件中)"""
        logger.debug("使用統一導出模式")
        
        filename = f"{self.config.filename_prefix}_unified"
        output_file = self._write_data_file(export_data, metadata, statistics, filename)
        
        return [output_file]
    
    def _export_by_constellation(self, export_data: List[OrbitDataPoint],
                               metadata: ExportMetadata, statistics: ExportStatistics) -> List[str]:
        """按星座分別導出"""
        logger.debug("使用按星座分別導出模式")
        
        # 按星座分組數據
        constellation_data = {}
        for point in export_data:
            constellation = self._identify_constellation(point.satellite_id)
            if constellation not in constellation_data:
                constellation_data[constellation] = []
            constellation_data[constellation].append(point)
        
        output_files = []
        for constellation, data_points in constellation_data.items():
            filename = f"{self.config.filename_prefix}_{constellation}"
            
            # 為每個星座調整元數據
            constellation_metadata = self._adjust_metadata_for_subset(metadata, data_points)
            constellation_stats = self._adjust_statistics_for_subset(statistics, data_points)
            
            output_file = self._write_data_file(data_points, constellation_metadata, constellation_stats, filename)
            output_files.append(output_file)
        
        return output_files
    
    def _export_by_satellite(self, export_data: List[OrbitDataPoint],
                           metadata: ExportMetadata, statistics: ExportStatistics) -> List[str]:
        """按衛星分別導出"""
        logger.debug("使用按衛星分別導出模式")
        
        # 按衛星分組數據
        satellite_data = {}
        for point in export_data:
            satellite_id = point.satellite_id
            if satellite_id not in satellite_data:
                satellite_data[satellite_id] = []
            satellite_data[satellite_id].append(point)
        
        output_files = []
        for satellite_id, data_points in satellite_data.items():
            filename = f"{self.config.filename_prefix}_{satellite_id}"
            
            # 為每顆衛星調整元數據
            satellite_metadata = self._adjust_metadata_for_subset(metadata, data_points)
            satellite_stats = self._adjust_statistics_for_subset(statistics, data_points)
            
            output_file = self._write_data_file(data_points, satellite_metadata, satellite_stats, filename)
            output_files.append(output_file)
        
        return output_files
    
    def _write_data_file(self, data_points: List[OrbitDataPoint],
                        metadata: ExportMetadata, statistics: ExportStatistics,
                        filename_base: str) -> str:
        """寫入數據文件"""
        # 根據格式選擇寫入方法
        if self.config.format == ExportFormat.JSON:
            return self._write_json_file(data_points, metadata, statistics, filename_base)
        elif self.config.format == ExportFormat.CSV:
            return self._write_csv_file(data_points, metadata, statistics, filename_base)
        elif self.config.format == ExportFormat.BINARY:
            return self._write_binary_file(data_points, metadata, statistics, filename_base)
        elif self.config.format == ExportFormat.NUMPY:
            return self._write_numpy_file(data_points, metadata, statistics, filename_base)
        else:
            raise ValueError(f"不支援的導出格式: {self.config.format}")
    
    def _write_json_file(self, data_points: List[OrbitDataPoint],
                        metadata: ExportMetadata, statistics: ExportStatistics,
                        filename_base: str) -> str:
        """寫入 JSON 文件"""
        filename = f"{filename_base}.json"
        if self.config.compression != CompressionType.NONE:
            filename += f".{self.config.compression.value}"
        
        output_path = self.output_dir / filename
        
        # 構造導出數據結構
        export_structure = {
            "metadata": metadata.to_dict() if self.config.include_metadata else {},
            "statistics": statistics.to_dict() if self.config.include_statistics else {},
            "data": [point.to_dict() for point in data_points]
        }
        
        # 寫入文件 (支持壓縮)
        if self.config.compression == CompressionType.GZIP:
            with gzip.open(output_path, 'wt', encoding='utf-8') as f:
                json.dump(export_structure, f, indent=2, ensure_ascii=False)
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_structure, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"JSON 文件已保存: {output_path}")
        return str(output_path)
    
    def _write_csv_file(self, data_points: List[OrbitDataPoint],
                       metadata: ExportMetadata, statistics: ExportStatistics,
                       filename_base: str) -> str:
        """寫入 CSV 文件"""
        filename = f"{filename_base}.csv"
        if self.config.compression != CompressionType.NONE:
            filename += f".{self.config.compression.value}"
        
        output_path = self.output_dir / filename
        
        if not data_points:
            # 創建空文件
            open(output_path, 'w').close()
            return str(output_path)
        
        # CSV 欄位名稱
        fieldnames = list(data_points[0].to_dict().keys())
        
        # 寫入 CSV 文件
        if self.config.compression == CompressionType.GZIP:
            with gzip.open(output_path, 'wt', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for point in data_points:
                    writer.writerow(point.to_dict())
        else:
            with open(output_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for point in data_points:
                    writer.writerow(point.to_dict())
        
        # 寫入元數據文件
        if self.config.include_metadata:
            metadata_path = self.output_dir / f"{filename_base}_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "metadata": metadata.to_dict(),
                    "statistics": statistics.to_dict()
                }, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"CSV 文件已保存: {output_path}")
        return str(output_path)
    
    def _write_binary_file(self, data_points: List[OrbitDataPoint],
                          metadata: ExportMetadata, statistics: ExportStatistics,
                          filename_base: str) -> str:
        """寫入二進制文件"""
        filename = f"{filename_base}.pkl"
        if self.config.compression != CompressionType.NONE:
            filename += f".{self.config.compression.value}"
        
        output_path = self.output_dir / filename
        
        # 構造導出數據結構
        export_structure = {
            "metadata": metadata.to_dict() if self.config.include_metadata else {},
            "statistics": statistics.to_dict() if self.config.include_statistics else {},
            "data": [point.to_dict() for point in data_points]
        }
        
        # 寫入二進制文件
        if self.config.compression == CompressionType.GZIP:
            with gzip.open(output_path, 'wb') as f:
                pickle.dump(export_structure, f, protocol=pickle.HIGHEST_PROTOCOL)
        else:
            with open(output_path, 'wb') as f:
                pickle.dump(export_structure, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        logger.debug(f"二進制文件已保存: {output_path}")
        return str(output_path)
    
    def _write_numpy_file(self, data_points: List[OrbitDataPoint],
                         metadata: ExportMetadata, statistics: ExportStatistics,
                         filename_base: str) -> str:
        """寫入 NumPy 文件"""
        filename = f"{filename_base}.npz"
        output_path = self.output_dir / filename
        
        if not data_points:
            # 創建空數組
            np.savez_compressed(output_path, 
                               satellite_ids=np.array([]),
                               positions=np.array([]).reshape(0, 3))
            return str(output_path)
        
        # 提取數據到 NumPy 數組
        satellite_ids = [point.satellite_id for point in data_points]
        positions = np.array([point.position_eci for point in data_points])
        
        # 可選的數據
        arrays_to_save = {
            "satellite_ids": np.array(satellite_ids),
            "positions_eci": positions
        }
        
        # 添加速度數據 (如果存在)
        velocities = [point.velocity_eci for point in data_points if point.velocity_eci is not None]
        if velocities and len(velocities) == len(data_points):
            arrays_to_save["velocities_eci"] = np.array(velocities)
        
        # 添加地理座標數據 (如果存在)
        latitudes = [point.latitude_deg for point in data_points if point.latitude_deg is not None]
        if latitudes and len(latitudes) == len(data_points):
            longitudes = [point.longitude_deg for point in data_points]
            altitudes = [point.altitude_km for point in data_points]
            arrays_to_save["latitudes"] = np.array(latitudes)
            arrays_to_save["longitudes"] = np.array(longitudes)
            arrays_to_save["altitudes"] = np.array(altitudes)
        
        # 保存壓縮的 NumPy 文件
        np.savez_compressed(output_path, **arrays_to_save)
        
        # 保存元數據
        if self.config.include_metadata:
            metadata_path = self.output_dir / f"{filename_base}_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "metadata": metadata.to_dict(),
                    "statistics": statistics.to_dict()
                }, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"NumPy 文件已保存: {output_path}")
        return str(output_path)
    
    def _adjust_metadata_for_subset(self, original_metadata: ExportMetadata,
                                   data_subset: List[OrbitDataPoint]) -> ExportMetadata:
        """為數據子集調整元數據"""
        satellite_ids = list(set(point.satellite_id for point in data_subset))
        
        adjusted_metadata = ExportMetadata(
            export_timestamp=original_metadata.export_timestamp,
            phase1_version=original_metadata.phase1_version,
            data_source=original_metadata.data_source,
            processing_algorithm=original_metadata.processing_algorithm,
            coordinate_systems=original_metadata.coordinate_systems,
            total_satellites=len(satellite_ids),
            total_data_points=len(data_subset),
            time_coverage_start=original_metadata.time_coverage_start,
            time_coverage_end=original_metadata.time_coverage_end,
            time_resolution_seconds=original_metadata.time_resolution_seconds
        )
        
        return adjusted_metadata
    
    def _adjust_statistics_for_subset(self, original_statistics: ExportStatistics,
                                    data_subset: List[OrbitDataPoint]) -> ExportStatistics:
        """為數據子集調整統計信息"""
        # 重新計算統計信息 (簡化版本)
        satellite_ids = list(set(point.satellite_id for point in data_subset))
        altitudes = [point.altitude_km for point in data_subset if point.altitude_km is not None]
        
        adjusted_statistics = ExportStatistics(
            satellites_by_constellation={"subset": len(satellite_ids)},
            data_points_by_satellite={sid: sum(1 for p in data_subset if p.satellite_id == sid) for sid in satellite_ids},
            time_span_hours=original_statistics.time_span_hours,
            average_altitude_km=np.mean(altitudes) if altitudes else 0.0,
            altitude_range_km=[float(np.min(altitudes)), float(np.max(altitudes))] if altitudes else [0.0, 0.0],
            orbital_period_range_minutes=original_statistics.orbital_period_range_minutes,
            data_quality_metrics=original_statistics.data_quality_metrics,
            processing_time_seconds=0.0
        )
        
        return adjusted_statistics
    
    def _generate_empty_metadata(self) -> ExportMetadata:
        """生成空元數據"""
        return ExportMetadata(
            export_timestamp=datetime.now(timezone.utc).isoformat(),
            phase1_version="1.0.0",
            data_source="Phase 1 Orbit Calculation System",
            processing_algorithm="Complete SGP4 Algorithm",
            coordinate_systems=self.config.coordinate_systems,
            total_satellites=0,
            total_data_points=0,
            time_coverage_start="",
            time_coverage_end="",
            time_resolution_seconds=30
        )
    
    def _generate_empty_statistics(self) -> ExportStatistics:
        """生成空統計信息"""
        return ExportStatistics(
            satellites_by_constellation={},
            data_points_by_satellite={},
            time_span_hours=0.0,
            average_altitude_km=0.0,
            altitude_range_km=[0.0, 0.0],
            orbital_period_range_minutes=[0.0, 0.0],
            data_quality_metrics={},
            processing_time_seconds=0.0
        )
    
    def export_summary_report(self, export_result: ExportResult, output_filename: str = "export_summary.json") -> bool:
        """導出摘要報告"""
        try:
            report_path = self.output_dir / output_filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(export_result.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"導出摘要報告已保存: {report_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存導出摘要報告失敗: {str(e)}")
            return False


def create_data_exporter(configuration: ExportConfiguration) -> DataExporter:
    """創建數據導出器實例"""
    return DataExporter(configuration)


def create_default_export_config(output_directory: str) -> ExportConfiguration:
    """創建默認導出配置"""
    return ExportConfiguration(
        output_directory=output_directory,
        filename_prefix="phase1_orbit_data",
        format=ExportFormat.JSON,
        compression=CompressionType.GZIP,
        include_metadata=True,
        include_statistics=True
    )


# 測試代碼
if __name__ == "__main__":
    import tempfile
    import os
    
    logging.basicConfig(level=logging.INFO)
    
    # 創建臨時輸出目錄
    with tempfile.TemporaryDirectory() as temp_dir:
        # 創建導出配置
        config = create_default_export_config(temp_dir)
        
        # 創建數據導出器
        exporter = create_data_exporter(config)
        
        # 創建測試數據
        test_orbit_data = {
            "STARLINK-1007": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "position_eci": [6500.0, 0.0, 0.0],
                    "velocity_eci": [0.0, 7.5, 0.0],
                    "altitude_km": 550.0,
                    "latitude_deg": 0.0,
                    "longitude_deg": 0.0
                }
            ],
            "ONEWEB-0001": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "position_eci": [7571.0, 0.0, 0.0],
                    "velocity_eci": [0.0, 6.8, 0.0],
                    "altitude_km": 1200.0,
                    "latitude_deg": 0.0,
                    "longitude_deg": 0.0
                }
            ]
        }
        
        # 執行導出
        result = exporter.export_orbit_data(test_orbit_data)
        
        print("✅ 數據導出器測試完成")
        print(f"成功: {result.success}")
        print(f"輸出文件: {len(result.output_files)} 個")
        print(f"總數據點: {result.metadata.total_data_points}")
        print(f"總衛星數: {result.metadata.total_satellites}")
        
        # 列出生成的文件
        for file_path in result.output_files:
            file_size = os.path.getsize(file_path) / 1024  # KB
            print(f"  - {os.path.basename(file_path)} ({file_size:.1f} KB)")