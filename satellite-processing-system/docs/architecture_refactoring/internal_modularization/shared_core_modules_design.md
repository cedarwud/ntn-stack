# 🔧 共享核心模組設計計劃

**目標**: 建立統一的核心功能模組，解決重複功能問題
**優先級**: 最高 (Phase 1首要任務)
**影響範圍**: 全部6個Stage

## 🎯 設計目標

### 解決重複功能問題
- **軌道計算重複**: 7個檔案 → 1個統一模組
- **信號計算重複**: 8個檔案 → 1個統一模組
- **可見性計算重複**: 6個檔案 → 1個統一模組

### 確保學術標準合規
- **Grade A標準**: 100%符合學術發表要求
- **TLE epoch時間**: 統一時間基準處理
- **標準算法**: 使用Skyfield等標準庫
- **無假設值**: 禁止任何預設值回退

### 建立清晰架構
- **單一職責**: 每個模組專注單一計算域
- **高內聚**: 相關功能聚集在同一模組
- **低耦合**: 模組間依賴關係清晰
- **易測試**: 每個模組可獨立測試

## 📁 模組架構設計

### 目錄結構
```
src/shared/core_modules/
├── __init__.py                          # 模組初始化和公開介面
├── orbital_calculations_core.py         # 軌道計算核心模組
├── visibility_calculations_core.py      # 可見性計算核心模組
├── signal_calculations_core.py          # 信號計算核心模組
├── physics_constants.py                 # 統一物理常數定義
├── time_standards.py                    # 統一時間基準處理
├── math_utilities.py                    # 統一數學工具函數
└── academic_validators.py               # 學術標準驗證工具
```

## 🛰️ orbital_calculations_core.py 設計

### 模組職責
統一處理所有軌道相關計算，確保計算精度和學術標準合規

### 核心類設計
```python
class OrbitalCalculationsCore:
    """
    軌道計算核心模組

    設計原則:
    - 使用Skyfield標準庫確保精度
    - 強制使用TLE epoch時間基準
    - 符合AIAA 2006-6753 SGP4標準
    - 禁止任何假設值或預設值
    """

    def __init__(self, time_standard_handler: TimeStandardsHandler):
        self.ts = time_standard_handler
        self.logger = logging.getLogger(__name__)

    # === 核心軌道計算方法 ===
    def calculate_satellite_positions(self, tle_data: List[Dict],
                                     time_points: List[float]) -> List[Dict]:
        """計算衛星在指定時間點的位置 (從Stage 1, 4, 5, 6提取整合)"""

    def extract_orbital_elements(self, satellites: List[Dict]) -> List[Dict]:
        """提取軌道元素 (從Stage 6提取)"""

    def calculate_mean_anomaly_from_position(self, position_data: Dict) -> float:
        """從位置數據計算平均近點角 (從Stage 6提取)"""

    def calculate_raan_from_position(self, position_data: Dict) -> float:
        """從位置數據計算升交點赤經 (從Stage 6提取)"""

    def perform_orbital_phase_analysis(self, satellites: List[Dict]) -> Dict:
        """執行軌道相位分析 (從Stage 6提取)"""

    # === 軌道傳播方法 ===
    def propagate_orbit(self, tle_line1: str, tle_line2: str,
                       target_time: float) -> Dict:
        """使用SGP4傳播軌道到目標時間"""

    def batch_propagate_orbits(self, tle_dataset: List[Dict],
                              time_span: Tuple[float, float]) -> List[Dict]:
        """批量軌道傳播處理"""

    # === 軌道分析方法 ===
    def analyze_constellation_phase_diversity(self, constellation_data: List[Dict]) -> Dict:
        """分析星座相位多樣性 (從Stage 6提取)"""

    def calculate_orbital_plane_distribution(self, satellites: List[Dict]) -> Dict:
        """計算軌道平面分布"""

    def optimize_raan_distribution(self, satellites: List[Dict],
                                  target_count: int) -> List[Dict]:
        """優化升交點赤經分布 (從Stage 6提取)"""
```

### 學術標準實施
```python
class OrbitalCalculationsCore:
    def _ensure_tle_epoch_compliance(self, tle_data: Dict) -> float:
        """確保使用TLE epoch時間，符合Grade A標準"""
        if 'epoch' not in tle_data:
            raise ValueError("TLE數據必須包含epoch時間")

        epoch_time = tle_data['epoch']
        current_time = datetime.now(timezone.utc).timestamp()
        time_diff_days = abs(current_time - epoch_time) / 86400

        if time_diff_days > 7:
            self.logger.warning(f"TLE數據已過期 {time_diff_days:.1f} 天，可能影響計算精度")

        return epoch_time

    def _use_standard_sgp4_implementation(self, tle_line1: str, tle_line2: str) -> EarthSatellite:
        """使用標準SGP4實施，確保學術合規"""
        from skyfield.sgp4lib import EarthSatellite
        return EarthSatellite(tle_line1, tle_line2, ts=self.ts)
```

## 👁️ visibility_calculations_core.py 設計

### 模組職責
統一處理所有可見性和幾何計算，提供標準的觀測者-衛星幾何分析

### 核心類設計
```python
class VisibilityCalculationsCore:
    """
    可見性計算核心模組

    設計原則:
    - 使用標準球面三角學公式
    - 支援多種仰角門檻設定
    - 精確的大氣折射修正
    - 考慮地球扁率影響
    """

    def __init__(self, physics_constants: PhysicsConstants):
        self.constants = physics_constants
        self.logger = logging.getLogger(__name__)

    # === 基礎幾何計算 ===
    def calculate_elevation_azimuth(self, observer_coords: Tuple[float, float, float],
                                   satellite_position: Dict,
                                   timestamp: float) -> Tuple[float, float]:
        """計算仰角和方位角 (從Stage 2, 3, 4, 5, 6提取整合)"""

    def calculate_distance_to_satellite(self, observer_coords: Tuple[float, float, float],
                                       satellite_position: Dict) -> float:
        """計算觀測者到衛星的距離"""

    def determine_visibility_status(self, elevation_deg: float,
                                   min_elevation_deg: float) -> bool:
        """判定可見性狀態"""

    # === 覆蓋分析方法 ===
    def analyze_coverage_windows(self, satellites: List[Dict],
                                constellation_config: Dict) -> Dict:
        """分析覆蓋視窗 (從Stage 6提取)"""

    def calculate_coverage_duration(self, satellite_passes: List[Dict]) -> Dict:
        """計算覆蓋持續時間"""

    def identify_coverage_gaps(self, coverage_timeline: List[Dict]) -> List[Dict]:
        """識別覆蓋空隙"""

    # === 空間分析方法 ===
    def analyze_hemisphere_balance(self, satellite_positions: List[Dict]) -> Dict:
        """分析半球平衡性 (從Stage 6提取)"""

    def calculate_elevation_complementarity_score(self, satellites_a: List[Dict],
                                                 satellites_b: List[Dict]) -> float:
        """計算仰角互補性分數 (從Stage 6提取)"""

    def optimize_elevation_band_allocation(self, satellites: List[Dict],
                                          elevation_bands: List[Tuple[float, float]]) -> Dict:
        """優化仰角帶分配 (從Stage 6提取)"""
```

### 精度優化設計
```python
class VisibilityCalculationsCore:
    def _apply_atmospheric_refraction_correction(self, elevation_deg: float) -> float:
        """應用大氣折射修正"""
        if elevation_deg < 15.0:  # 低仰角需要折射修正
            # 使用標準大氣折射模型
            refraction_correction = self._calculate_refraction_correction(elevation_deg)
            return elevation_deg + refraction_correction
        return elevation_deg

    def _consider_earth_oblateness(self, observer_coords: Tuple[float, float, float]) -> Dict:
        """考慮地球扁率影響"""
        # 實施WGS84地球橢球模型
        pass
```

## 📶 signal_calculations_core.py 設計

### 模組職責
統一處理所有信號品質和換手相關計算，確保3GPP NTN標準合規

### 核心類設計
```python
class SignalCalculationsCore:
    """
    信號計算核心模組

    設計原則:
    - 嚴格遵循3GPP NTN標準
    - 實施標準的路徑損耗模型
    - 支援A4/A5/D2事件計算
    - 考慮都卜勒效應影響
    """

    def __init__(self, physics_constants: PhysicsConstants):
        self.constants = physics_constants
        self.logger = logging.getLogger(__name__)

    # === 基礎信號計算 ===
    def calculate_path_loss(self, distance_km: float, frequency_hz: float) -> float:
        """計算路徑損耗 (從Stage 3, 4, 5, 6提取整合)"""

    def calculate_rsrp(self, satellite_eirp: float, path_loss: float,
                      antenna_gain: float) -> float:
        """計算RSRP信號功率"""

    def calculate_doppler_shift(self, satellite_velocity: Dict,
                               observer_coords: Tuple[float, float, float],
                               carrier_frequency: float) -> float:
        """計算都卜勒頻移"""

    # === 3GPP事件分析 ===
    def analyze_a4_event(self, neighbor_rsrp: float, threshold: float,
                        offset: float, hysteresis: float) -> Dict:
        """A4事件分析：鄰近衛星變得優於門檻值"""

    def analyze_a5_event(self, serving_rsrp: float, neighbor_rsrp: float,
                        threshold1: float, threshold2: float, hysteresis: float) -> Dict:
        """A5事件分析：服務衛星劣於門檻1且鄰近衛星優於門檻2"""

    def analyze_d2_event(self, serving_distance: float, neighbor_distance: float,
                        threshold1: float, threshold2: float, hysteresis: float) -> Dict:
        """D2事件分析：基於距離的換手事件"""

    # === 換手決策支援 ===
    def calculate_handover_margin(self, serving_signal: Dict,
                                 neighbor_signals: List[Dict]) -> Dict:
        """計算換手邊際"""

    def rank_handover_candidates(self, candidates: List[Dict],
                                ranking_criteria: Dict) -> List[Dict]:
        """排序換手候選"""

    def predict_signal_quality(self, satellite_trajectory: List[Dict],
                              prediction_horizon: float) -> List[Dict]:
        """預測信號品質變化 (從Stage 3, 6提取)"""
```

### 3GPP標準實施
```python
class SignalCalculationsCore:
    def _ensure_3gpp_compliance(self, measurement_config: Dict) -> Dict:
        """確保3GPP NTN標準合規"""
        required_params = ['frequency_band', 'measurement_bandwidth', 'threshold_values']
        for param in required_params:
            if param not in measurement_config:
                raise ValueError(f"缺少3GPP必要參數: {param}")

        return self._validate_3gpp_parameters(measurement_config)

    def _apply_ntn_specific_corrections(self, base_calculation: float,
                                       satellite_elevation: float) -> float:
        """應用NTN特定修正"""
        # 實施3GPP TS 38.821定義的NTN特定修正
        pass
```

## ⏰ time_standards.py 設計

### 模組職責
統一處理所有時間基準轉換，確保TLE epoch時間基準合規

### 核心類設計
```python
class TimeStandardsHandler:
    """
    時間標準處理模組

    設計原則:
    - 強制使用TLE epoch時間作為計算基準
    - 支援UTC/UT1/TT時間標準轉換
    - 集成Skyfield時間系統
    - 禁止使用當前系統時間進行軌道計算
    """

    def __init__(self):
        from skyfield.api import load
        self.ts = load.timescale()
        self.logger = logging.getLogger(__name__)

    def create_time_from_tle_epoch(self, tle_epoch: float) -> Any:
        """從TLE epoch創建時間對象"""

    def validate_time_basis_compliance(self, calculation_time: float,
                                     tle_epoch: float) -> bool:
        """驗證時間基準合規性"""

    def convert_time_formats(self, input_time: Any,
                           target_format: str) -> Any:
        """轉換時間格式"""

    def calculate_time_offset_from_epoch(self, tle_epoch: float,
                                       target_time: float) -> float:
        """計算相對於TLE epoch的時間偏移"""
```

## 🧮 math_utilities.py 設計

### 模組職責
提供統一的數學工具函數，避免重複實現

### 核心函數設計
```python
class MathUtilities:
    """數學工具函數集合"""

    @staticmethod
    def calculate_great_circle_distance(point1: Tuple[float, float],
                                      point2: Tuple[float, float]) -> float:
        """計算大圓距離"""

    @staticmethod
    def convert_cartesian_to_spherical(x: float, y: float, z: float) -> Tuple[float, float, float]:
        """笛卡兒座標轉球面座標"""

    @staticmethod
    def normalize_angle(angle_deg: float) -> float:
        """角度標準化到0-360度範圍"""

    @staticmethod
    def calculate_statistical_metrics(data_points: List[float]) -> Dict:
        """計算統計指標"""
```

## 📋 模組整合策略

### 統一初始化
```python
# src/shared/core_modules/__init__.py
from .orbital_calculations_core import OrbitalCalculationsCore
from .visibility_calculations_core import VisibilityCalculationsCore
from .signal_calculations_core import SignalCalculationsCore
from .time_standards import TimeStandardsHandler
from .physics_constants import PhysicsConstants

class SharedCoreModules:
    """共享核心模組統一管理器"""

    def __init__(self):
        self.physics_constants = PhysicsConstants()
        self.time_handler = TimeStandardsHandler()

        self.orbital_calc = OrbitalCalculationsCore(self.time_handler)
        self.visibility_calc = VisibilityCalculationsCore(self.physics_constants)
        self.signal_calc = SignalCalculationsCore(self.physics_constants)

    def get_orbital_calculator(self) -> OrbitalCalculationsCore:
        return self.orbital_calc

    def get_visibility_calculator(self) -> VisibilityCalculationsCore:
        return self.visibility_calc

    def get_signal_calculator(self) -> SignalCalculationsCore:
        return self.signal_calc
```

### Stage中的使用方式
```python
# 在各Stage中使用共享模組
from shared.core_modules import SharedCoreModules

class Stage6CoreProcessor:
    def __init__(self):
        self.core_modules = SharedCoreModules()
        self.orbital_calc = self.core_modules.get_orbital_calculator()
        self.visibility_calc = self.core_modules.get_visibility_calculator()

    def process_dynamic_pool_planning(self):
        # 使用統一的核心模組，不再重複實現
        orbital_data = self.orbital_calc.extract_orbital_elements(satellites)
        coverage_data = self.visibility_calc.analyze_coverage_windows(satellites)
        return self._create_dynamic_pool_strategy(orbital_data, coverage_data)
```

## 🎯 實施檢查清單

### 模組建立階段
- [ ] 創建目錄結構 `src/shared/core_modules/`
- [ ] 實施 `physics_constants.py` 和 `time_standards.py`
- [ ] 實施 `orbital_calculations_core.py` (整合7個重複功能)
- [ ] 實施 `visibility_calculations_core.py` (整合6個重複功能)
- [ ] 實施 `signal_calculations_core.py` (整合8個重複功能)
- [ ] 實施 `math_utilities.py` 和 `academic_validators.py`
- [ ] 創建統一管理器 `SharedCoreModules`

### 整合測試階段
- [ ] 單元測試每個核心模組
- [ ] 學術標準合規性測試
- [ ] 性能基準測試 (vs 原重複實現)
- [ ] 各Stage整合測試
- [ ] 文檔和API參考更新

---

**預估工期**: 2-3天
**影響範圍**: 所有Stage
**成功標準**: 0個重複功能，100%學術合規
**下一步**: 開始實施核心模組建立工作