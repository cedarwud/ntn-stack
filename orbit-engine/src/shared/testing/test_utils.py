"""
測試工具

整合來源：
- tests/conftest.py (測試工具函數)
- 各Stage的測試輔助函數

提供統一的測試工具集
"""

import json
import csv
import random
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable, Generator
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
import math
import time
from contextlib import contextmanager


logger = logging.getLogger(__name__)


@dataclass
class TestDataSpec:
    """測試數據規格"""
    data_type: str
    size: int
    constraints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TestDataGenerator:
    """測試數據生成器"""

    @staticmethod
    def generate_tle_data(satellite_count: int = 10, epoch_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        生成測試用TLE數據

        Args:
            satellite_count: 衛星數量
            epoch_date: 歷元時間

        Returns:
            TLE數據列表
        """
        if epoch_date is None:
            epoch_date = datetime.now(timezone.utc)

        tle_data = []
        for i in range(satellite_count):
            satellite_id = 40000 + i
            inclination = 53.0 + random.uniform(-5, 5)
            raan = random.uniform(0, 360)
            eccentricity = random.uniform(0.0001, 0.01)
            arg_perigee = random.uniform(0, 360)
            mean_anomaly = random.uniform(0, 360)
            mean_motion = 15.5 + random.uniform(-0.5, 0.5)

            # 計算TLE時間格式
            year = epoch_date.year % 100
            day_of_year = epoch_date.timetuple().tm_yday
            day_fraction = (epoch_date.hour * 3600 + epoch_date.minute * 60 + epoch_date.second) / 86400
            epoch_day = day_of_year + day_fraction

            line1 = f"1 {satellite_id}U 24001{chr(65+i)}   {year:02d}{epoch_day:012.8f}  .00001000  00000-0  67960-4 0  999{i}"
            line2 = f"2 {satellite_id}  {inclination:8.4f} {raan:8.4f} {eccentricity:7.7f} {arg_perigee:8.4f} {mean_anomaly:8.4f} {mean_motion:11.8f}{i*100:5d}"

            # 計算校驗和
            line1 = TestDataGenerator._add_checksum(line1)
            line2 = TestDataGenerator._add_checksum(line2)

            tle_data.append({
                'satellite_id': satellite_id,
                'line0': f"TEST-SAT-{satellite_id}",
                'line1': line1,
                'line2': line2,
                'epoch_year': epoch_date.year,
                'epoch_day': epoch_day,
                'inclination': inclination,
                'raan': raan,
                'eccentricity': eccentricity,
                'arg_perigee': arg_perigee,
                'mean_anomaly': mean_anomaly,
                'mean_motion': mean_motion
            })

        return tle_data

    @staticmethod
    def _add_checksum(line: str) -> str:
        """為TLE行添加校驗和"""
        checksum = 0
        for char in line[:-1]:  # 除了最後一位
            if char.isdigit():
                checksum += int(char)
            elif char == '-':
                checksum += 1

        return line[:-1] + str(checksum % 10)

    @staticmethod
    def generate_observer_location(region: str = "taiwan") -> Dict[str, float]:
        """
        生成觀測者位置

        Args:
            region: 地區 ("taiwan", "global", "custom")

        Returns:
            觀測者位置
        """
        if region == "taiwan":
            # 台灣地區隨機位置
            return {
                'latitude': random.uniform(22.0, 25.5),
                'longitude': random.uniform(120.0, 122.0),
                'altitude_km': random.uniform(0, 3.5)
            }
        elif region == "global":
            # 全球隨機位置
            return {
                'latitude': random.uniform(-90, 90),
                'longitude': random.uniform(-180, 180),
                'altitude_km': random.uniform(0, 5.0)
            }
        else:
            # NTPU預設位置
            return {
                'latitude': 24.9441667,
                'longitude': 121.3713889,
                'altitude_km': 0.035
            }

    @staticmethod
    def generate_signal_quality_data(satellite_count: int = 10) -> List[Dict[str, Any]]:
        """
        生成信號品質測試數據

        Args:
            satellite_count: 衛星數量

        Returns:
            信號品質數據
        """
        signal_data = []
        for i in range(satellite_count):
            # 基於真實的信號特性生成數據
            elevation = random.uniform(5, 90)  # 仰角範圍
            distance_km = random.uniform(500, 2000)  # 距離範圍

            # 基於仰角和距離計算合理的信號強度
            # 高仰角 = 更好的信號
            base_rsrp = -80 - (90 - elevation) * 0.5 - (distance_km - 500) * 0.02
            rsrp_dbm = base_rsrp + random.uniform(-5, 5)

            rsrq_db = -10 - random.uniform(0, 10)
            sinr_db = 10 + elevation / 10 + random.uniform(-5, 5)

            signal_data.append({
                'satellite_id': 40000 + i,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'elevation_deg': elevation,
                'azimuth_deg': random.uniform(0, 360),
                'distance_km': distance_km,
                'rsrp_dbm': rsrp_dbm,
                'rsrq_db': rsrq_db,
                'sinr_db': sinr_db,
                'quality_score': TestDataGenerator._calculate_quality_score(rsrp_dbm, rsrq_db, sinr_db)
            })

        return signal_data

    @staticmethod
    def _calculate_quality_score(rsrp: float, rsrq: float, sinr: float) -> float:
        """計算信號品質分數"""
        # 正規化各項指標
        rsrp_norm = max(0, min(1, (rsrp + 140) / 100))  # -140 to -40 dBm
        rsrq_norm = max(0, min(1, (rsrq + 25) / 15))    # -25 to -10 dB
        sinr_norm = max(0, min(1, (sinr + 5) / 30))     # -5 to 25 dB

        # 加權平均
        return 0.4 * rsrp_norm + 0.3 * rsrq_norm + 0.3 * sinr_norm

    @staticmethod
    def generate_time_series(start_time: datetime, end_time: datetime,
                           step_minutes: int = 5) -> List[datetime]:
        """
        生成時間序列

        Args:
            start_time: 開始時間
            end_time: 結束時間
            step_minutes: 時間步長

        Returns:
            時間序列
        """
        time_series = []
        current_time = start_time
        step_delta = timedelta(minutes=step_minutes)

        while current_time <= end_time:
            time_series.append(current_time)
            current_time += step_delta

        return time_series


class TestFileManager:
    """測試文件管理器"""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(tempfile.gettempdir()) / "satellite_tests"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.created_files: List[Path] = []

    def create_test_file(self, filename: str, content: Any, file_format: str = "json") -> Path:
        """
        創建測試文件

        Args:
            filename: 文件名
            content: 文件內容
            file_format: 文件格式

        Returns:
            文件路徑
        """
        file_path = self.base_dir / filename

        if file_format == "json":
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=2, ensure_ascii=False, default=str)
        elif file_format == "csv":
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                if isinstance(content, list) and content:
                    writer = csv.DictWriter(f, fieldnames=content[0].keys())
                    writer.writeheader()
                    writer.writerows(content)
        elif file_format == "text":
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(str(content))

        self.created_files.append(file_path)
        return file_path

    def cleanup(self):
        """清理創建的測試文件"""
        for file_path in self.created_files:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                logger.warning(f"清理測試文件失敗: {file_path}, error: {e}")

        self.created_files.clear()


class PerformanceMeasurer:
    """性能測量器"""

    def __init__(self):
        self.measurements: Dict[str, List[float]] = {}

    @contextmanager
    def measure(self, operation_name: str) -> Generator[None, None, None]:
        """
        性能測量上下文管理器

        Args:
            operation_name: 操作名稱
        """
        start_time = time.perf_counter()
        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time

            if operation_name not in self.measurements:
                self.measurements[operation_name] = []

            self.measurements[operation_name].append(duration)
            logger.debug(f"操作 {operation_name} 耗時: {duration:.3f}秒")

    def get_statistics(self, operation_name: str) -> Dict[str, float]:
        """
        獲取操作統計信息

        Args:
            operation_name: 操作名稱

        Returns:
            統計信息
        """
        if operation_name not in self.measurements:
            return {}

        measurements = self.measurements[operation_name]
        return {
            'count': len(measurements),
            'total_time': sum(measurements),
            'average_time': sum(measurements) / len(measurements),
            'min_time': min(measurements),
            'max_time': max(measurements),
            'std_deviation': self._calculate_std_dev(measurements)
        }

    def _calculate_std_dev(self, values: List[float]) -> float:
        """計算標準差"""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)

    def get_all_statistics(self) -> Dict[str, Dict[str, float]]:
        """獲取所有操作的統計信息"""
        return {op: self.get_statistics(op) for op in self.measurements.keys()}


class MockDataService:
    """模擬數據服務（僅用於單元測試隔離）"""

    def __init__(self):
        self.data_store: Dict[str, Any] = {}

    def store_data(self, key: str, data: Any):
        """存儲數據"""
        self.data_store[key] = data

    def get_data(self, key: str) -> Any:
        """獲取數據"""
        return self.data_store.get(key)

    def clear(self):
        """清空數據"""
        self.data_store.clear()


class TestAssertion:
    """增強的測試斷言工具"""

    @staticmethod
    def assert_coordinates_valid(lat: float, lon: float, alt: float = None):
        """驗證座標有效性"""
        assert -90 <= lat <= 90, f"無效緯度: {lat}"
        assert -180 <= lon <= 180, f"無效經度: {lon}"
        if alt is not None:
            assert -1000 <= alt <= 100000, f"無效高度: {alt} km"

    @staticmethod
    def assert_signal_quality_valid(rsrp: float, rsrq: float, sinr: float):
        """驗證信號品質參數有效性"""
        assert -140 <= rsrp <= -30, f"無效RSRP: {rsrp} dBm"
        assert -25 <= rsrq <= -3, f"無效RSRQ: {rsrq} dB"
        assert -10 <= sinr <= 30, f"無效SINR: {sinr} dB"

    @staticmethod
    def assert_time_range_valid(start_time: datetime, end_time: datetime):
        """驗證時間範圍有效性"""
        assert start_time < end_time, "開始時間必須早於結束時間"
        duration = end_time - start_time
        assert duration.total_seconds() > 0, "時間範圍必須為正值"
        assert duration.total_seconds() < 86400 * 365, "時間範圍不能超過一年"

    @staticmethod
    def assert_processing_result_valid(result: Dict[str, Any], required_fields: List[str]):
        """驗證處理結果有效性"""
        assert isinstance(result, dict), "處理結果必須是字典格式"

        for field in required_fields:
            assert field in result, f"處理結果缺少必要字段: {field}"

        if 'timestamp' in result:
            timestamp = result['timestamp']
            if isinstance(timestamp, str):
                try:
                    datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    assert False, f"無效的時間戳格式: {timestamp}"

    @staticmethod
    def assert_data_consistency(data1: Any, data2: Any, tolerance: float = 1e-6):
        """驗證數據一致性"""
        if isinstance(data1, (int, float)) and isinstance(data2, (int, float)):
            assert abs(data1 - data2) <= tolerance, f"數據不一致: {data1} vs {data2}"
        elif isinstance(data1, dict) and isinstance(data2, dict):
            assert set(data1.keys()) == set(data2.keys()), "字典鍵不一致"
            for key in data1.keys():
                TestAssertion.assert_data_consistency(data1[key], data2[key], tolerance)
        elif isinstance(data1, list) and isinstance(data2, list):
            assert len(data1) == len(data2), f"列表長度不一致: {len(data1)} vs {len(data2)}"
            for i, (item1, item2) in enumerate(zip(data1, data2)):
                TestAssertion.assert_data_consistency(item1, item2, tolerance)
        else:
            assert data1 == data2, f"數據值不一致: {data1} vs {data2}"


# 便捷函數
def create_test_environment(test_name: str, cleanup_on_exit: bool = True) -> Dict[str, Any]:
    """便捷函數：創建測試環境"""
    file_manager = TestFileManager()
    performance_measurer = PerformanceMeasurer()
    mock_service = MockDataService()

    env = {
        'test_name': test_name,
        'file_manager': file_manager,
        'performance_measurer': performance_measurer,
        'mock_service': mock_service,
        'cleanup_on_exit': cleanup_on_exit
    }

    if cleanup_on_exit:
        import atexit
        atexit.register(lambda: file_manager.cleanup())

    return env


def generate_test_satellite_data(count: int = 10, region: str = "taiwan") -> Dict[str, Any]:
    """便捷函數：生成完整的測試衛星數據"""
    observer_location = TestDataGenerator.generate_observer_location(region)
    tle_data = TestDataGenerator.generate_tle_data(count)
    signal_data = TestDataGenerator.generate_signal_quality_data(count)

    return {
        'observer_location': observer_location,
        'tle_data': tle_data,
        'signal_data': signal_data,
        'generated_at': datetime.now(timezone.utc).isoformat()
    }


def validate_test_data_academic_compliance(data_description: str, algorithm_description: str) -> bool:
    """便捷函數：驗證測試數據學術合規性"""
    forbidden_patterns = [
        "mock", "fake", "random", "simulated",
        "simplified", "estimated", "假設", "模擬"
    ]

    for pattern in forbidden_patterns:
        if pattern.lower() in data_description.lower():
            logger.warning(f"數據描述包含禁用模式: {pattern}")
            return False
        if pattern.lower() in algorithm_description.lower():
            logger.warning(f"算法描述包含禁用模式: {pattern}")
            return False

    return True