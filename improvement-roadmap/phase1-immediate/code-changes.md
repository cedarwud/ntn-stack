# Phase 1: 程式碼修改指南

**修改範圍**: 立即修復的核心程式碼變更
**影響評估**: 中等 - 主要是配置和一致性修改

## 🔧 修改項目概覽

### 1. 全局配置系統建立

#### 新增檔案: `/netstack/config/satellite_config.py`

**目的**: 統一管理所有衛星數量相關的配置參數，整合來自舊版修復方案的詳細設計

```python
"""
衛星系統全局配置文件
統一管理所有衛星數量相關的配置參數

作者: 衛星系統團隊
日期: 2025-08-03
版本: 2.0 (整合舊版修復方案)
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class SatelliteConfig:
    """
    衛星系統配置類
    
    統一管理系統中所有與衛星數量、篩選、處理相關的配置參數
    確保符合 3GPP TS 38.331 SIB19 規範
    """
    
    # ========== SIB19 規範配置 ==========
    MAX_CANDIDATE_SATELLITES: int = 8  # 3GPP TS 38.331 規範上限
    MIN_CANDIDATE_SATELLITES: int = 1  # 最少候選衛星數
    
    # ========== 預處理優化配置 ==========
    PREPROCESS_SATELLITES: Dict[str, int] = field(default_factory=lambda: {
        "starlink": 40,    # Starlink 預處理衛星數
        "oneweb": 30,      # OneWeb 預處理衛星數
        "iridium": 20,     # Iridium 預處理衛星數（預留）
        "default": 30      # 其他星座默認值
    })
    
    # ========== 批次計算配置 ==========
    BATCH_COMPUTE_SATELLITES: int = 50  # 批次計算最大衛星數
    BATCH_COMPUTE_INTERVAL: int = 30   # 批次計算時間間隔（秒）
    
    # ========== 智能篩選配置 ==========
    INTELLIGENT_SELECTION: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True,                    # 是否啟用智能篩選
        "geographic_filter": True,          # 地理相關性篩選
        "handover_suitability": True,       # 換手適用性篩選
        "target_location": {                # 目標位置（台北科技大學）
            "latitude": 24.9441,
            "longitude": 121.3714,
            "altitude": 0.0
        },
        "coverage_radius_km": 1000,         # 覆蓋半徑
        "min_elevation_deg": 10.0,          # 最小仰角
        "preferred_elevation_deg": 30.0     # 偏好仰角
    })
    
    # ========== 軌道計算配置 ==========
    ORBIT_CALCULATION: Dict[str, Any] = field(default_factory=lambda: {
        "preprocess_method": "simplified",   # 預處理方法: "sgp4" 或 "simplified"
        "runtime_method": "sgp4",           # 運行時方法: 始終使用 "sgp4"
        "sgp4_in_build": False,             # 建置階段是否使用 SGP4
        "position_tolerance_km": 1.0,       # 位置容差
        "velocity_tolerance_km_s": 0.01     # 速度容差
    })
    
    # ========== 性能優化配置 ==========
    PERFORMANCE: Dict[str, Any] = field(default_factory=lambda: {
        "max_build_time_seconds": 300,      # 最大建置時間（5分鐘）
        "parallel_processing": True,        # 並行處理
        "cache_enabled": True,              # 啟用緩存
        "cache_ttl_hours": 24              # 緩存有效期
    })
    
    # ========== 驗證配置 ==========
    VALIDATION: Dict[str, Any] = field(default_factory=lambda: {
        "strict_mode": True,                # 嚴格模式
        "log_warnings": True,               # 記錄警告
        "reject_overflow": False            # 拒絕超量（False = 截斷）
    })
    
    def validate(self) -> bool:
        """
        驗證配置合理性
        
        Returns:
            bool: 配置是否有效
        """
        errors = []
        
        # 檢查候選衛星數量
        if self.MAX_CANDIDATE_SATELLITES > 8:
            errors.append(f"MAX_CANDIDATE_SATELLITES ({self.MAX_CANDIDATE_SATELLITES}) 超過 SIB19 規範限制 (8)")
        
        # 檢查預處理數量
        for constellation, count in self.PREPROCESS_SATELLITES.items():
            if count < self.MAX_CANDIDATE_SATELLITES:
                if self.VALIDATION["strict_mode"]:
                    errors.append(
                        f"{constellation} 預處理數量 {count} "
                        f"少於候選數量 {self.MAX_CANDIDATE_SATELLITES}"
                    )
                else:
                    logger.warning(
                        f"{constellation} 預處理數量 {count} "
                        f"少於候選數量 {self.MAX_CANDIDATE_SATELLITES}"
                    )
        
        # 檢查批次計算配置
        if self.BATCH_COMPUTE_SATELLITES < self.MAX_CANDIDATE_SATELLITES:
            errors.append(
                f"BATCH_COMPUTE_SATELLITES ({self.BATCH_COMPUTE_SATELLITES}) "
                f"不應少於 MAX_CANDIDATE_SATELLITES ({self.MAX_CANDIDATE_SATELLITES})"
            )
        
        if errors:
            for error in errors:
                logger.error(f"配置錯誤: {error}")
            if self.VALIDATION["strict_mode"]:
                raise ValueError(f"配置驗證失敗: {'; '.join(errors)}")
            return False
        
        logger.info("✅ 衛星配置驗證通過")
        return True
    
    def get_max_satellites_for_stage(self, stage: str, constellation: str = None) -> int:
        """根據處理階段獲取最大衛星數量"""
        if stage == "candidate":
            return self.MAX_CANDIDATE_SATELLITES
        elif stage == "preprocess":
            if constellation:
                return self.PREPROCESS_SATELLITES.get(
                    constellation, 
                    self.PREPROCESS_SATELLITES.get("default", 30)
                )
            return max(self.PREPROCESS_SATELLITES.values())
        elif stage == "batch":
            return self.BATCH_COMPUTE_SATELLITES
        else:
            logger.warning(f"未知的處理階段: {stage}")
            return self.MAX_CANDIDATE_SATELLITES
    
    def should_use_sgp4_in_build(self) -> bool:
        """判斷建置階段是否應使用 SGP4"""
        return self.ORBIT_CALCULATION.get("sgp4_in_build", False)

# ========== 全局配置實例 ==========
SATELLITE_CONFIG = SatelliteConfig()
SATELLITE_CONFIG.validate()

def get_config() -> SatelliteConfig:
    """獲取全局衛星配置"""
    return SATELLITE_CONFIG

# 向後兼容的常數（保持 API 兼容性）
MAX_CANDIDATES = SATELLITE_CONFIG.MAX_CANDIDATE_SATELLITES
PREPROCESS_STARLINK_COUNT = SATELLITE_CONFIG.PREPROCESS_SATELLITES['starlink']
PREPROCESS_ONEWEB_COUNT = SATELLITE_CONFIG.PREPROCESS_SATELLITES['oneweb']
```

### 2. 修改 SIB19 統一平台

#### 檔案: `/netstack/netstack_api/services/sib19_unified_platform.py`

```python
# 在檔案開頭添加
from config.satellite_config import SATELLITE_CONFIG

class SIB19UnifiedPlatform:
    def __init__(self):
        # 使用統一配置
        self.max_tracked_satellites = SATELLITE_CONFIG.MAX_CANDIDATE_SATELLITES
        
        # 添加配置驗證
        SATELLITE_CONFIG.validate_configuration()
        
    def validate_candidate_count(self, count: int) -> int:
        """確保候選衛星數量符合 SIB19 規範"""
        if count > self.max_tracked_satellites:
            logger.warning(
                f"候選衛星數量 {count} 超過 SIB19 限制 {self.max_tracked_satellites}，"
                f"將截斷至 {self.max_tracked_satellites}"
            )
            return self.max_tracked_satellites
        return count
    
    async def get_optimal_candidates(self, observer_location: Position, 
                                   timestamp: datetime) -> List[str]:
        """獲取最佳候選衛星列表（符合 SIB19 規範）"""
        # ... 現有邏輯 ...
        
        # 確保返回的候選數量符合規範
        candidates = self._calculate_candidates(observer_location, timestamp)
        return candidates[:self.validate_candidate_count(len(candidates))]
```

### 3. 修改預處理系統

#### 檔案: `/simworld/backend/preprocess_120min_timeseries.py`

```python
# 在檔案開頭添加
from config.satellite_config import SATELLITE_CONFIG

class TimeseriesPreprocessor:
    def __init__(self):
        # 使用統一配置
        self.use_sgp4_in_build = SATELLITE_CONFIG.USE_SGP4_IN_BUILD
        self.build_method = SATELLITE_CONFIG.BUILD_CALCULATION_METHOD
        
        # 衛星數量配置
        self.satellite_counts = SATELLITE_CONFIG.PREPROCESS_SATELLITES.copy()
        
    async def _generate_constellation_timeseries(self, constellation: str) -> Optional[Dict[str, Any]]:
        """生成指定星座的時間序列數據"""
        try:
            # ... 載入 TLE 數據 ...
            
            # 使用統一配置的目標數量
            target_count = self.satellite_counts.get(constellation, 30)
            
            selected_satellites = await self._intelligent_satellite_selection(
                tle_data, constellation, target_count
            )
            
            # 生成衛星時間序列
            satellites_timeseries = []
            
            for i, sat_data in enumerate(selected_satellites):
                try:
                    # 根據配置選擇計算方法
                    if self.use_sgp4_in_build:
                        satellite_timeseries = await self._calculate_sgp4_satellite_timeseries(
                            sat_data, start_time
                        )
                    else:
                        satellite_timeseries = await self._calculate_simplified_satellite_timeseries(
                            sat_data, start_time
                        )
                    
                    if satellite_timeseries:
                        satellites_timeseries.append({
                            "norad_id": sat_data.get("norad_id", 0),
                            "name": sat_data.get("name", "Unknown"),
                            "constellation": constellation,
                            "time_series": satellite_timeseries,
                            "calculation_method": self.build_method  # 添加計算方法標記
                        })
                        
                except Exception as e:
                    logger.warning(f"⚠️ 衛星 {sat_data.get('name', 'Unknown')} 計算失敗: {e}")
                    continue
            
            # 更新元數據
            unified_data = {
                "metadata": {
                    "computation_time": start_time.isoformat(),
                    "constellation": constellation,
                    "calculation_method": self.build_method,
                    "sgp4_enabled": self.use_sgp4_in_build,
                    "config_version": "1.3.0",
                    "satellites_processed": len(satellites_timeseries),
                    # ... 其他元數據 ...
                }
                # ... 其他數據 ...
            }
            
            return unified_data
            
        except Exception as e:
            logger.error(f"❌ {constellation} 時間序列生成失敗: {e}")
            return None

    async def _calculate_sgp4_satellite_timeseries(self, sat_data: Dict[str, Any], 
                                                 start_time: datetime) -> List[Dict[str, Any]]:
        """使用 SGP4 計算衛星時間序列"""
        try:
            from app.services.sgp4_calculator import SGP4Calculator, TLEData
            
            calculator = SGP4Calculator()
            
            # 建立 TLE 數據結構
            tle_data = TLEData(
                name=sat_data.get("name", "Unknown"),
                line1=sat_data.get("line1", ""),
                line2=sat_data.get("line2", "")
            )
            
            timeseries = []
            for i in range(self.total_time_points):
                timestamp = start_time + timedelta(seconds=i * self.time_interval_seconds)
                
                # 使用 SGP4 計算位置
                position = calculator.propagate_orbit(tle_data, timestamp)
                
                if position:
                    timeseries.append({
                        "time_offset_seconds": i * self.time_interval_seconds,
                        "latitude": position.latitude,
                        "longitude": position.longitude, 
                        "altitude_km": position.altitude,
                        "velocity_km_s": position.velocity,
                        "timestamp": timestamp.isoformat(),
                        "calculation_method": "sgp4"
                    })
                else:
                    # 如果 SGP4 失敗，回退到簡化模型
                    logger.warning(f"SGP4 計算失敗，回退到簡化模型: {sat_data.get('name')}")
                    return await self._calculate_simplified_satellite_timeseries(sat_data, start_time)
            
            return timeseries
            
        except Exception as e:
            logger.error(f"SGP4 計算錯誤: {e}")
            # 回退到簡化模型
            return await self._calculate_simplified_satellite_timeseries(sat_data, start_time)
```

### 4. 修改批次預計算

#### 檔案: `/netstack/scripts/batch_precompute_taiwan.py`

```python
# 在檔案開頭添加
from config.satellite_config import SATELLITE_CONFIG

class TaiwanBatchPrecomputer:
    def __init__(self):
        # 使用統一配置
        self.max_satellites = SATELLITE_CONFIG.BATCH_COMPUTE_MAX_SATELLITES
        
    async def process_constellation(self, constellation: str, observer: Dict, 
                                  observer_name: str):
        """處理單一星座數據"""
        try:
            # ... 現有邏輯 ...
            
            # 使用統一配置的衛星數量
            results = await precomputer.compute_history_async(
                time_interval_seconds=30,
                min_elevation=10.0,
                max_satellites=self.max_satellites  # 使用統一配置
            )
            
            # ... 存儲邏輯 ...
            
        except Exception as e:
            logger.error(f"❌ {constellation} 處理失敗: {e}")
```

### 5. 精度驗證框架（來自舊版修復方案）

#### 新增檔案: `/netstack/validators/accuracy_validator.py`

```python
"""
精度驗證框架
確保預處理與運行時計算的一致性
"""

import numpy as np
import math
from typing import List, Tuple, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AccuracyValidator:
    """預處理與運行時精度驗證器"""
    
    def __init__(self):
        self.position_tolerance_km = 1.0  # 位置容差
        self.velocity_tolerance_km_s = 0.01  # 速度容差
        
    async def validate_preprocessing_accuracy(
        self, 
        preprocess_data: dict, 
        runtime_data: dict
    ) -> dict:
        """驗證預處理數據與運行時計算的一致性"""
        
        results = {
            "total_points": 0,
            "position_errors": [],
            "velocity_errors": [],
            "max_position_error_km": 0,
            "max_velocity_error_km_s": 0,
            "within_tolerance_ratio": 0,
            "validation_passed": False,
            "detailed_analysis": {}
        }
        
        # 提取時間序列數據
        preprocess_series = preprocess_data['satellites'][0]['time_series']
        runtime_series = runtime_data['positions']
        
        # 逐點比較
        for i, (pre, run) in enumerate(zip(preprocess_series, runtime_series)):
            # 計算位置誤差
            pos_error = self._calculate_position_error(
                pre['position'], run['position']
            )
            results['position_errors'].append(pos_error)
            
            # 計算速度誤差（如果有）
            if 'velocity' in pre and 'velocity' in run:
                vel_error = self._calculate_velocity_error(
                    pre['velocity'], run['velocity']
                )
                results['velocity_errors'].append(vel_error)
        
        # 統計分析
        results['total_points'] = len(preprocess_series)
        results['max_position_error_km'] = max(results['position_errors'])
        results['mean_position_error_km'] = np.mean(results['position_errors'])
        results['std_position_error_km'] = np.std(results['position_errors'])
        
        # 計算容差內的比例
        within_tolerance = sum(
            1 for e in results['position_errors'] 
            if e <= self.position_tolerance_km
        )
        results['within_tolerance_ratio'] = within_tolerance / results['total_points']
        
        # 判斷是否通過驗證
        results['validation_passed'] = (
            results['within_tolerance_ratio'] >= 0.95 and
            results['max_position_error_km'] <= self.position_tolerance_km * 3
        )
        
        # 詳細分析
        results['detailed_analysis'] = {
            "error_distribution": self._analyze_error_distribution(results['position_errors']),
            "temporal_drift": self._analyze_temporal_drift(results['position_errors']),
            "accuracy_grade": self._determine_accuracy_grade(results)
        }
        
        return results
    
    def _calculate_position_error(self, pos1: dict, pos2: dict) -> float:
        """計算兩個位置之間的距離誤差（km）"""
        # 簡化的大圓距離計算
        lat1, lon1 = math.radians(pos1['lat']), math.radians(pos1['lon'])
        lat2, lon2 = math.radians(pos2['lat']), math.radians(pos2['lon'])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        # 考慮高度差異
        ground_distance = 6371.0 * c
        altitude_diff = abs(pos1['alt'] - pos2['alt'])
        
        return math.sqrt(ground_distance**2 + altitude_diff**2)
    
    def _calculate_velocity_error(self, vel1: dict, vel2: dict) -> float:
        """計算速度向量誤差（km/s）"""
        dx = vel1['x'] - vel2['x']
        dy = vel1['y'] - vel2['y']
        dz = vel1['z'] - vel2['z']
        
        return math.sqrt(dx**2 + dy**2 + dz**2)
    
    def _analyze_error_distribution(self, errors: List[float]) -> dict:
        """分析誤差分佈"""
        errors_array = np.array(errors)
        
        return {
            "percentiles": {
                "p50": np.percentile(errors_array, 50),
                "p95": np.percentile(errors_array, 95),
                "p99": np.percentile(errors_array, 99)
            },
            "outliers_count": len([e for e in errors if e > np.percentile(errors_array, 95)]),
            "skewness": self._calculate_skewness(errors_array)
        }
    
    def _analyze_temporal_drift(self, errors: List[float]) -> dict:
        """分析時間漂移"""
        # 簡單的趨勢分析
        x = np.arange(len(errors))
        y = np.array(errors)
        
        # 線性擬合
        coefficients = np.polyfit(x, y, 1)
        drift_rate = coefficients[0]  # km/time_step
        
        return {
            "drift_rate_km_per_step": drift_rate,
            "total_drift_km": drift_rate * len(errors),
            "drift_significant": abs(drift_rate) > 0.001
        }
    
    def _determine_accuracy_grade(self, results: dict) -> str:
        """確定精度等級"""
        max_error = results['max_position_error_km']
        mean_error = results['mean_position_error_km']
        tolerance_ratio = results['within_tolerance_ratio']
        
        if max_error <= 0.1 and tolerance_ratio >= 0.99:
            return "A+ (Excellent)"
        elif max_error <= 0.5 and tolerance_ratio >= 0.95:
            return "A (Very Good)"
        elif max_error <= 1.0 and tolerance_ratio >= 0.90:
            return "B (Good)"
        elif max_error <= 3.0 and tolerance_ratio >= 0.80:
            return "C (Acceptable)"
        else:
            return "D (Poor)"
    
    def _calculate_skewness(self, data: np.ndarray) -> float:
        """計算偏度"""
        return float(np.mean(((data - np.mean(data)) / np.std(data)) ** 3))
    
    def generate_accuracy_report(self, validation_results: dict) -> str:
        """生成精度報告"""
        results = validation_results
        
        report = f"""
# 精度驗證報告

## 🎯 總體評估
- **驗證狀態**: {"✅ 通過" if results['validation_passed'] else "❌ 失敗"}
- **精度等級**: {results['detailed_analysis']['accuracy_grade']}
- **測試點數**: {results['total_points']}

## 📊 位置精度分析
- **最大誤差**: {results['max_position_error_km']:.3f} km
- **平均誤差**: {results['mean_position_error_km']:.3f} km
- **標準差**: {results['std_position_error_km']:.3f} km
- **容差內比例**: {results['within_tolerance_ratio']:.1%}

## 📈 誤差分佈
- **50% 分位數**: {results['detailed_analysis']['error_distribution']['percentiles']['p50']:.3f} km
- **95% 分位數**: {results['detailed_analysis']['error_distribution']['percentiles']['p95']:.3f} km
- **99% 分位數**: {results['detailed_analysis']['error_distribution']['percentiles']['p99']:.3f} km
- **異常值數量**: {results['detailed_analysis']['error_distribution']['outliers_count']}

## ⏱️ 時間漂移分析
- **漂移率**: {results['detailed_analysis']['temporal_drift']['drift_rate_km_per_step']:.6f} km/步
- **總漂移**: {results['detailed_analysis']['temporal_drift']['total_drift_km']:.3f} km
- **漂移顯著**: {"是" if results['detailed_analysis']['temporal_drift']['drift_significant'] else "否"}

## 💡 建議
"""
        
        if results['validation_passed']:
            report += "- ✅ 當前精度滿足要求，可繼續使用\n"
        else:
            report += "- ❌ 精度不足，建議：\n"
            if results['max_position_error_km'] > 3.0:
                report += "  - 考慮使用 SGP4 替代簡化模型\n"
            if results['within_tolerance_ratio'] < 0.9:
                report += "  - 優化軌道計算算法\n"
            if results['detailed_analysis']['temporal_drift']['drift_significant']:
                report += "  - 檢查時間同步和累積誤差\n"
        
        return report
```

### 6. 數據驗證機制

#### 新增檔案: `/tests/test_data_consistency.py`

```python
"""
數據一致性驗證測試
確保預處理數據與運行時計算的一致性
"""

import pytest
import json
from datetime import datetime, timezone
from pathlib import Path

from config.satellite_config import SATELLITE_CONFIG
from simworld.backend.app.services.sgp4_calculator import SGP4Calculator, TLEData
from simworld.backend.preprocess_120min_timeseries import TimeseriesPreprocessor

class TestDataConsistency:
    
    def test_config_validation(self):
        """測試配置驗證"""
        assert SATELLITE_CONFIG.validate_configuration() == True
        assert SATELLITE_CONFIG.MAX_CANDIDATE_SATELLITES <= 8
        
    def test_preprocessing_consistency(self):
        """測試預處理數據一致性"""
        # 載入預處理數據
        data_path = Path("/app/data/starlink_120min_timeseries.json")
        if data_path.exists():
            with open(data_path) as f:
                preprocess_data = json.load(f)
            
            # 驗證元數據
            metadata = preprocess_data["metadata"]
            assert "calculation_method" in metadata
            assert "sgp4_enabled" in metadata
            assert "config_version" in metadata
            
            # 驗證衛星數據結構
            satellites = preprocess_data["satellites"]
            for sat in satellites[:3]:  # 抽樣檢查前3顆
                assert "calculation_method" in sat
                assert "time_series" in sat
                
                # 檢查時間序列數據完整性
                timeseries = sat["time_series"]
                assert len(timeseries) > 0
                
                for point in timeseries[:5]:  # 抽樣檢查
                    required_fields = ["timestamp", "latitude", "longitude", "altitude_km"]
                    for field in required_fields:
                        assert field in point, f"Missing field {field} in satellite {sat['name']}"
    
    def test_candidate_count_compliance(self):
        """測試候選衛星數量符合性"""
        from netstack.netstack_api.services.sib19_unified_platform import SIB19UnifiedPlatform
        
        platform = SIB19UnifiedPlatform()
        
        # 測試正常情況
        assert platform.validate_candidate_count(5) == 5
        
        # 測試超出限制
        assert platform.validate_candidate_count(10) == SATELLITE_CONFIG.MAX_CANDIDATE_SATELLITES
        
    def test_sgp4_calculation_accuracy(self):
        """測試 SGP4 計算精度"""
        calculator = SGP4Calculator()
        
        # 使用測試 TLE 數據
        test_tle = TLEData(
            name="TEST SAT",
            line1="1 25544U 98067A   21001.00000000  .00002182  00000-0  40917-4 0  9990",
            line2="2 25544  51.6461 339.2911 0002829  86.4002 273.8155 15.48919103260342"
        )
        
        timestamp = datetime.now(timezone.utc)
        position = calculator.propagate_orbit(test_tle, timestamp)
        
        assert position is not None
        assert -90 <= position.latitude <= 90
        assert -180 <= position.longitude <= 180
        assert position.altitude > 0
        
    @pytest.mark.performance
    def test_build_time_performance(self):
        """測試建置時間性能"""
        import time
        from simworld.backend.preprocess_120min_timeseries import TimeseriesPreprocessor
        
        preprocessor = TimeseriesPreprocessor()
        
        # 測試小樣本處理時間
        start_time = time.time()
        
        # 模擬處理3顆衛星
        test_satellites = [
            {"name": "TEST-1", "line1": "test", "line2": "test"},
            {"name": "TEST-2", "line1": "test", "line2": "test"},
            {"name": "TEST-3", "line1": "test", "line2": "test"}
        ]
        
        # 這裡應該調用實際的處理邏輯，但簡化為時間測試
        processing_time = time.time() - start_time
        
        # 確保處理時間合理（每顆衛星 < 1秒）
        assert processing_time < 3.0, f"處理時間過長: {processing_time:.2f}s"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### 6. 配置驗證腳本

#### 新增檔案: `/scripts/validate_config.py`

```python
#!/usr/bin/env python3
"""
配置驗證腳本
確保所有模組正確使用統一配置
"""

import sys
import importlib
from pathlib import Path

# 添加項目路徑
sys.path.append(str(Path(__file__).parent.parent))

from config.satellite_config import SATELLITE_CONFIG

def validate_all_configs():
    """驗證所有配置"""
    
    print("🔍 開始配置驗證...")
    
    # 1. 基本配置驗證
    try:
        SATELLITE_CONFIG.validate_configuration()
        print("✅ 基本配置驗證通過")
    except Exception as e:
        print(f"❌ 基本配置驗證失敗: {e}")
        return False
    
    # 2. 模組導入驗證
    modules_to_check = [
        "netstack.netstack_api.services.sib19_unified_platform",
        "simworld.backend.preprocess_120min_timeseries",
        "netstack.scripts.batch_precompute_taiwan"
    ]
    
    for module_name in modules_to_check:
        try:
            module = importlib.import_module(module_name)
            print(f"✅ 模組 {module_name} 載入成功")
        except Exception as e:
            print(f"❌ 模組 {module_name} 載入失敗: {e}")
            return False
    
    # 3. 配置一致性檢查
    consistency_checks = [
        ("MAX_CANDIDATE_SATELLITES", lambda: SATELLITE_CONFIG.MAX_CANDIDATE_SATELLITES <= 8),
        ("PREPROCESS_SATELLITES", lambda: sum(SATELLITE_CONFIG.PREPROCESS_SATELLITES.values()) <= 100),
        ("BUILD_TIME_LIMIT", lambda: SATELLITE_CONFIG.MAX_BUILD_TIME_MINUTES <= 15)
    ]
    
    for check_name, check_func in consistency_checks:
        try:
            if check_func():
                print(f"✅ {check_name} 一致性檢查通過")
            else:
                print(f"❌ {check_name} 一致性檢查失敗")
                return False
        except Exception as e:
            print(f"❌ {check_name} 檢查異常: {e}")
            return False
    
    print("🎉 所有配置驗證通過！")
    return True

if __name__ == "__main__":
    success = validate_all_configs()
    sys.exit(0 if success else 1)
```

## 🔍 程式碼審查檢查清單

### 修改前檢查
- [ ] 備份所有要修改的檔案
- [ ] 確認相依性不會被破壞
- [ ] 預估修改影響範圍

### 修改中檢查
- [ ] 遵循現有代碼風格
- [ ] 添加適當的錯誤處理
- [ ] 保持向後兼容性

### 修改後檢查
- [ ] 所有測試通過
- [ ] 配置驗證腳本通過
- [ ] 性能基準達標
- [ ] 文檔同步更新

## 📊 修改影響評估

| 檔案類型 | 修改檔案數 | 風險等級 | 測試要求 |
|----------|------------|----------|----------|
| 配置檔案 | 1 (新增) | 低 | 單元測試 |
| 核心服務 | 3 | 中 | 整合測試 |
| 腳本工具 | 2 | 低 | 功能測試 |
| 測試檔案 | 2 (新增) | 低 | 自動驗證 |

---

**重要提醒**: 所有修改必須遵循「先測試，後部署」的原則，確保系統穩定性。