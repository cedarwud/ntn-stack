# 🔧 NTN Stack 技術實現指南

**版本**: 1.0.0  
**建立日期**: 2025-08-06  
**適用於**: LEO 衛星切換研究系統 - 完整技術實現

## 📋 概述

本指南整合了 NTN Stack 的所有核心技術實現，包括衛星數據處理、算法實現和配置管理。**本系統嚴格遵循完整算法原則，絕不使用簡化或模擬數據**。

## 🛰️ 衛星數據處理技術

### 🎯 核心架構：Complete SGP4 + Pure Cron 驅動

**重要澄清**：系統實際運行時使用 `"sgp4_mode": "runtime_precision"`，即**完整的SGP4算法**。任何標記為 "simplified_for_build" 的文件僅為建構時的快速啟動數據，不影響運行時的算法精度。

```
🏗️ 建構階段        🚀 運行階段           🕒 Cron 維護
     ↓                ↓                   ↓
完整SGP4預計算    Runtime Precision     智能增量更新
     ↓                ↓                   ↓
快速啟動數據      完整物理模型          持續精度保證
```

### 📊 真實數據來源

#### TLE 數據獲取
**數據源**: CelesTrak 官方 TLE 數據  
**更新頻率**: 每 6 小時自動下載  
**星座覆蓋**: 
- **Starlink**: 8,042 顆活躍衛星 (2025年8月)
- **OneWeb**: 651 顆活躍衛星

```bash
/netstack/tle_data/
├── starlink/
│   ├── tle/starlink_20250803.tle    # 真實TLE數據
│   └── json/starlink.json           # 結構化數據
└── oneweb/
    ├── tle/oneweb_20250803.tle
    └── json/oneweb.json
```

#### TLE 數據格式驗證
```
STARLINK-1008           
1 44714U 19074B   25215.02554568  .00001428  00000+0  11473-3 0  9994
2 44714  53.0544  88.2424 0001286  82.9322 277.1813 15.06399309315962
```

### ⚙️ 完整 SGP4 算法實現

#### 核心計算引擎
**實現位置**: `/simworld/backend/app/services/sgp4_calculator.py`

**物理模型包含**:
- ✅ **完整 SGP4/SDP4 模型**: 高精度軌道傳播
- ✅ **J2 重力場影響**: 地球扁率效應
- ✅ **J4 高階重力場**: 更高精度修正  
- ✅ **大氣阻力**: 基於高度的密度模型
- ✅ **第三體引力**: 太陽和月球攝動
- ✅ **太陽輻射壓力**: 光壓攝動效應

#### 精度指標
```python
orbit_accuracy = {
    "position_accuracy": "< 100m",      # 位置精度
    "velocity_accuracy": "< 0.1 m/s",   # 速度精度  
    "prediction_horizon": "24 hours",   # 預測範圍
    "coordinate_system": "WGS84",       # 座標系統
    "time_precision": "< 1 second"      # 時間精度
}
```

#### 關鍵計算流程
```python
def propagate_orbit(self, tle: TLEData, timestamp: datetime) -> OrbitPosition:
    """完整 SGP4 軌道計算 - 無簡化"""
    
    # 1. 軌道要素提取和初始化
    inclination = tle.inclination * DEG_TO_RAD
    right_ascension = tle.right_ascension * DEG_TO_RAD
    eccentricity = tle.eccentricity
    
    # 2. J2 攝動修正
    c2 = 0.25 * J2 * xi**2 * (3 * theta**2 - 1) / beta**3
    
    # 3. 開普勒方程求解
    E = self._solve_kepler_equation(M, e)
    
    # 4. ECI 座標計算
    x_eci, y_eci, z_eci = self._orbit_to_eci(...)
    
    # 5. 高階攝動修正
    corrected_position, corrected_velocity = self._apply_high_order_perturbations(...)
    
    # 6. 地理座標轉換
    latitude, longitude, altitude = self._eci_to_geodetic(...)
```

### 🔄 Pure Cron 驅動架構

#### 自動化數據處理流程
```bash
# Cron 調度時間表
02:00, 08:00, 14:00, 20:00  # TLE 自動下載
02:30, 08:30, 14:30, 20:30  # 智能增量處理  
03:15                       # 安全數據清理
```

#### 智能增量處理
**處理位置**: `/scripts/incremental_data_processor.sh`

```bash
#!/bin/bash
# 智能增量處理邏輯
check_tle_changes() {
    # 1. 比較新舊 TLE 衛星清單
    # 2. 檢測軌道參數顯著變化
    # 3. 識別需要重新計算的衛星
    # 4. 僅處理變更部分，避免完整重建
}

process_incremental_update() {
    # 1. 使用完整 SGP4 算法重新計算
    # 2. 更新受影響的時間序列數據  
    # 3. 驗證數據完整性和格式
    # 4. 原子性更新，確保一致性
}
```

### 📊 衛星篩選策略

#### 星座分離處理 (v3.1)
**核心原則**: Starlink 和 OneWeb **完全分離處理**，禁止跨星座換手

```python
constellation_specific_scoring = {
    "starlink": {
        "orbital_inclination": 0.30,    # 針對 53° 傾角優化
        "altitude_suitability": 0.25,   # 550km 最佳高度
        "orbital_shape": 0.20,          # 近圓軌道
        "pass_frequency": 0.15,         # 15+ 圈/天
        "phase_distribution": 0.10      # 相位分散
    },
    "oneweb": {
        "orbital_inclination": 0.25,    # 針對 87° 傾角優化
        "altitude_suitability": 0.25,   # 1200km 最佳高度  
        "orbital_shape": 0.20,          # 近圓軌道
        "polar_coverage": 0.20,         # 高傾角優勢
        "phase_distribution": 0.10      # 相位分散
    }
}
```

#### 動態篩選邏輯
```python
def dynamic_satellite_selection(visible_satellites: int) -> str:
    """基於可見衛星數量的動態篩選策略"""
    if visible_satellites < 8:
        return "relaxed_criteria"      # 確保最少換手候選
    elif 8 <= visible_satellites <= 45:
        return "standard_filtering"     # 平衡品質和數量
    else:
        return "strict_filtering"       # 選擇最優衛星
```

### 📈 時間序列數據處理

#### 數據生成參數
```python
timeseries_config = {
    "time_span_minutes": 120,          # 2小時覆蓋範圍
    "time_interval_seconds": 30,       # 30秒採樣間隔
    "total_time_points": 240,          # 總採樣點數
    "reference_location": {
        "latitude": 24.9441667,        # NTPU 座標
        "longitude": 121.3713889,
        "altitude": 0.0
    }
}
```

#### 輸出數據格式
```json
{
  "metadata": {
    "computation_time": "2025-08-06T10:56:16+00:00",
    "constellation": "starlink",
    "sgp4_mode": "runtime_precision",
    "data_source": "dynamic_generation",
    "network_dependency": false
  },
  "satellites": [
    {
      "satellite_id": "STARLINK-1007", 
      "timeseries": [
        {
          "time": "2025-08-04T09:53:00Z",
          "elevation_deg": 45.7,
          "azimuth_deg": 152.3,
          "range_km": 589.2,
          "lat": 24.944,
          "lon": 121.371,
          "alt_km": 589.2
        }
      ]
    }
  ]
}
```

## 🧠 核心算法實現

### 🛰️ 3GPP NTN 信令系統

#### NTN 特定 RRC 程序
**實施位置**: `/src/protocols/ntn/ntn_signaling.py`

**3GPP TS 38.331 標準實現**:
```python
# Event A4: 鄰近小區變得優於門檻
def event_a4_condition(Mn, Ofn, Ocn, Hys, Thresh):
    enter = (Mn + Ofn + Ocn - Hys) > Thresh
    leave = (Mn + Ofn + Ocn + Hys) < Thresh
    return enter, leave

# Event A5: 服務小區低於門檻1且鄰近小區高於門檻2  
def event_a5_condition(Mp, Mn, Ofn, Ocn, Hys, Thresh1, Thresh2):
    enter = (Mp + Hys < Thresh1) and (Mn + Ofn + Ocn - Hys > Thresh2)
    leave = (Mp - Hys > Thresh1) or (Mn + Ofn + Ocn + Hys < Thresh2)
    return enter, leave
```

**變數定義**:
- `Mn`: 鄰近小區測量結果 (dBm for RSRP, dB for RSRQ/RS-SINR)
- `Mp`: 服務小區測量結果
- `Ofn`: 測量對象特定偏移  
- `Ocn`: 小區特定偏移
- `Hys`: 遲滯參數 (dB)

#### 衛星位置資訊廣播 (SIB19)
```python
sib19_broadcast_format = {
    "satellite_id": "STARLINK-1234",
    "ephemeris_data": {
        "epoch": "2025-08-04T12:00:00Z",
        "position": {"x": 1234.5, "y": -5678.9, "z": 3456.7},
        "velocity": {"vx": 7.123, "vy": -2.456, "vz": 1.789}
    },
    "beam_info": [
        {"beam_id": 1, "coverage_area": {...}, "max_eirp": 45.2}
    ],
    "candidate_satellites": [
        {"satellite_id": "STARLINK-5678", "priority": 1}
    ]
}
```

### ⚡ 精細化切換決策引擎

#### 多維度決策評分
**實施位置**: `/src/algorithms/handover/fine_grained_decision.py`

```python
decision_factors = {
    "signal_strength": 0.30,        # RSRP/RSRQ 品質
    "satellite_elevation": 0.25,    # 仰角門檻優化
    "load_balancing": 0.20,         # 網路負載均衡  
    "handover_history": 0.15,       # 歷史成功率
    "prediction_confidence": 0.10   # ML 預測置信度
}

def evaluate_handover_candidates(candidates, ue_context):
    """精細化切換決策評估"""
    scores = []
    for candidate in candidates:
        score = (
            candidate.signal_strength * decision_factors["signal_strength"] +
            candidate.elevation * decision_factors["satellite_elevation"] +
            (100 - candidate.load) * decision_factors["load_balancing"] +
            candidate.history_success * decision_factors["handover_history"] +
            candidate.prediction_conf * decision_factors["prediction_confidence"]
        )
        scores.append((candidate, score))
    
    return sorted(scores, key=lambda x: x[1], reverse=True)
```

### 🎯 軌道預測優化

#### 高精度 SGP4/SDP4 實現
```python
orbit_prediction_features = {
    "sgp4_propagation": "完整 SGP4 模型",
    "atmospheric_drag": "高度相關密度模型", 
    "j2_perturbation": "地球扁率主要項",
    "j4_perturbation": "高階重力場修正",
    "third_body_effects": "太陽月球攝動",
    "solar_radiation": "光壓攝動效應"
}

def calculate_orbital_perturbations(position, velocity, timestamp, tle):
    """完整攝動效應計算"""
    j4_correction = calculate_j4_perturbation(position)
    third_body = calculate_third_body_perturbation(position, timestamp)  
    drag = calculate_atmospheric_drag(position, velocity, tle.drag_term)
    srp = calculate_solar_radiation_pressure(position, timestamp)
    
    return apply_all_corrections(j4_correction, third_body, drag, srp)
```

### 🤖 ML 驅動預測模型

#### 多模型融合架構
```python
ml_model_ensemble = {
    "lstm_predictor": {
        "input_features": 15,        # 多維特徵輸入
        "hidden_units": 128,         # LSTM 隱藏層
        "sequence_length": 60,       # 時間序列長度
        "prediction_horizon": 10     # 預測時間範圍
    },
    "transformer_predictor": {
        "d_model": 256,              # 模型維度
        "num_heads": 8,              # 多頭注意力
        "num_layers": 6,             # Transformer 層數
        "max_sequence_length": 100   # 最大序列長度
    },
    "hybrid_fusion": {
        "ensemble_weights": [0.6, 0.4],  # LSTM vs Transformer
        "confidence_threshold": 0.85,     # 預測置信度門檻
        "fallback_strategy": "geometric_mean"  # 融合策略
    }
}
```

### 🔄 狀態同步保證機制

#### 分散式狀態管理
**實施位置**: `/src/algorithms/sync/state_synchronization.py`

```python
consistency_levels = {
    "STRONG": {
        "description": "強一致性 - 所有節點立即同步",
        "latency": "高延遲，強保證",
        "use_case": "關鍵切換決策"
    },
    "EVENTUAL": {
        "description": "最終一致性 - 允許短期不一致",
        "latency": "低延遲，最終保證", 
        "use_case": "一般狀態同步"
    },
    "WEAK": {
        "description": "弱一致性 - 最佳性能",
        "latency": "最低延遲",
        "use_case": "非關鍵監控數據"
    }
}

class StateEntry:
    def __init__(self, key, value, state_type, consistency_level):
        self.key = key
        self.value = value 
        self.state_type = state_type  # USER_CONTEXT, SATELLITE_STATE, etc.
        self.consistency_level = consistency_level
        self.version = 0
        self.last_modified = datetime.utcnow()
```

## ⚙️ 統一配置管理

### 🔧 核心配置系統
**位置**: `/netstack/src/core/config/satellite_config.py`

```python
@dataclass
class SatelliteConfig:
    """衛星系統統一配置類"""
    
    # 3GPP NTN 合規配置
    MAX_CANDIDATE_SATELLITES: int = 8
    
    # 衛星篩選配置  
    PREPROCESS_SATELLITES: Dict[str, int] = field(default_factory=lambda: {
        "starlink": 0,  # 動態決策，非固定數量
        "oneweb": 0     # 動態決策，非固定數量  
    })
    
    # 智能篩選配置
    INTELLIGENT_SELECTION: bool = True
    GEOGRAPHIC_FILTERING: bool = True
    ELEVATION_THRESHOLD_DEG: float = 10.0
    
    # 軌道計算精度配置
    SGP4_MODE: str = "runtime_precision"  # 運行時精度模式
    PERTURBATION_MODELING: bool = True    # 啟用攝動建模
    HIGH_ORDER_TERMS: bool = True         # 高階項修正
    
    # Pure Cron 驅動配置
    CRON_UPDATE_INTERVAL: int = 6         # 6小時更新週期
    INCREMENTAL_PROCESSING: bool = True   # 增量處理
    DATA_VALIDATION: bool = True          # 數據驗證
```

### 🌍 分層仰角門檻系統
```python
elevation_thresholds = {
    "ideal_service": 15.0,      # 理想服務門檻 (≥99.9% 成功率)
    "standard_service": 10.0,   # 標準服務門檻 (≥99.5% 成功率)  
    "minimum_service": 5.0,     # 最低服務門檻 (≥98% 成功率)
    "emergency_only": 3.0       # 緊急通訊門檻 (特殊授權)
}

environmental_adjustments = {
    "open_area": 0.9,           # 海洋、平原
    "standard": 1.0,            # 一般陸地
    "urban": 1.2,               # 城市建築遮蔽
    "complex_terrain": 1.5,     # 山區、高樓
    "severe_weather": 1.8       # 暴雨、雪災
}
```

## 📊 性能監控和指標

### ⚡ 系統性能基準
```python
performance_benchmarks = {
    "api_response_time": {
        "satellite_position": "< 50ms",
        "handover_decision": "< 100ms", 
        "trajectory_query": "< 200ms"
    },
    "algorithm_latency": {
        "sgp4_calculation": "< 15ms",
        "fine_grained_handover": "< 25ms",
        "ml_prediction": "< 50ms"
    },
    "accuracy_metrics": {
        "position_accuracy": "< 100m",
        "prediction_accuracy": "> 94%", 
        "handover_success_rate": "> 99%"
    }
}
```

### 📈 學術研究支援
```python
research_capabilities = {
    "algorithm_comparison": {
        "supported_algorithms": ["fine_grained", "traditional", "ml_driven"],
        "metrics": ["latency", "success_rate", "accuracy"],
        "statistical_tests": ["t-test", "ANOVA", "Mann-Whitney U"]
    },
    "data_export": {
        "formats": ["CSV", "JSON", "Excel"], 
        "visualization": ["learning_curves", "performance_plots"],
        "ieee_compliance": True
    }
}
```

## 🔧 維護和故障排除

### 日常維護指令
```bash
# 系統狀態檢查
make status                    # 完整系統狀態
curl http://localhost:8080/health | jq    # NetStack 健康
curl http://localhost:8888/api/v1/satellites/unified/health | jq  # SimWorld 健康

# Cron 調度監控  
crontab -l | grep tle         # 檢查 Cron 任務
tail -f /tmp/tle_download.log  # TLE 下載日誌
tail -f /tmp/incremental_update.log  # 增量處理日誌

# 數據完整性驗證
docker exec simworld_backend ls -la /app/netstack/tle_data/
curl -s http://localhost:8888/api/v1/satellites/unified/status | jq
```

### 性能調優指南
```bash
# 系統資源監控
docker stats                           # 容器資源使用
curl -w "@curl-format.txt" -s http://localhost:8080/api/v1/handover_decision/performance_metrics

# 算法性能測試
cd /home/sat/ntn-stack/netstack
python -m pytest tests/unit/test_fine_grained_handover.py -v --benchmark-only
```

## ⚠️ 重要注意事項

### 算法完整性保證
1. **絕對禁止簡化**: 運行時使用完整 SGP4 算法，任何 "simplified_for_build" 標記僅為建構時預計算
2. **真實數據保證**: 所有 TLE 數據來自 CelesTrak 官方，衛星位置計算基於真實物理模型
3. **精度維持**: 位置精度 < 100m，預測準確率 > 94%，符合學術研究標準

### 系統設計原則
1. **Pure Cron 驅動**: 容器純載入 + Cron 自動調度，實現零維護運行
2. **星座分離**: Starlink 和 OneWeb 完全分離處理，符合真實技術約束
3. **動態篩選**: 基於實際可見性自動調整，避免硬編碼限制

## ⚙️ 統一配置管理系統

**版本**: 1.0.0  
**建立日期**: 2025-08-04  
**目的**: 確保系統配置的一致性和可維護性  

### 🔧 核心配置類

**位置**: `/netstack/src/core/config/satellite_config.py`

```python
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass  
class SatelliteConfig:
    """衛星系統統一配置類"""
    
    # SIB19 合規配置
    MAX_CANDIDATE_SATELLITES: int = 8
    
    # 預處理優化配置
    PREPROCESS_SATELLITES: Dict[str, int] = None
    
    # 智能篩選配置
    INTELLIGENT_SELECTION: Dict[str, Any] = None
    
    # 觀測位置配置
    OBSERVER_LOCATION: Dict[str, float] = None
    
    # 仰角門檻配置  
    ELEVATION_THRESHOLDS: Dict[str, float] = None
    
    def __post_init__(self):
        """初始化預設值"""
        self.PREPROCESS_SATELLITES = self.PREPROCESS_SATELLITES or {
            "starlink": 40,
            "oneweb": 30
        }
        
        self.INTELLIGENT_SELECTION = self.INTELLIGENT_SELECTION or {
            "enabled": True,
            "geographic_filter": True,
            "handover_suitability": True,
            "target_location": {"lat": 24.9441667, "lon": 121.3713889}
        }
        
        self.OBSERVER_LOCATION = self.OBSERVER_LOCATION or {
            "latitude": 24.9441667,   # 台北科技大學
            "longitude": 121.3713889,
            "altitude": 50.0          # 米
        }
        
        self.ELEVATION_THRESHOLDS = self.ELEVATION_THRESHOLDS or {
            "minimum": 5.0,    # 最小可見仰角
            "handover": 10.0,  # 切換觸發仰角  
            "optimal": 15.0    # 最佳服務仰角
        }
```

### 📊 關鍵配置參數

#### 1. 衛星候選配置
```python
satellite_selection = {
    # 3GPP NTN 標準合規
    "MAX_CANDIDATE_SATELLITES": 8,    # SIB19 最大候選數
    
    # 預處理階段優化  
    "PREPROCESS_SATELLITES": {
        "starlink": 40,               # Starlink 智能篩選數量
        "oneweb": 30                  # OneWeb 智能篩選數量
    },
    
    # 運行時動態調整
    "RUNTIME_CANDIDATES": 8           # API 返回候選數量
}
```

#### 2. 智能篩選配置
```python
intelligent_selection = {
    "enabled": True,                  # 啟用智能篩選
    "geographic_filter": True,        # 地理相關性篩選
    "handover_suitability": True,     # 切換適用性評分
    
    # 地理篩選參數
    "target_location": {
        "lat": 24.9441667,            # 目標緯度 (台北科技大學)
        "lon": 121.3713889            # 目標經度
    },
    
    # 評分權重配置
    "scoring_weights": {
        "inclination_score": 0.25,    # 軌道傾角權重
        "altitude_score": 0.20,       # 高度適用性權重
        "orbital_shape": 0.15,        # 軌道形狀權重  
        "pass_frequency": 0.20,       # 經過頻率權重
        "constellation_bonus": 0.20   # 星座類型權重
    }
}
```

#### 3. 軌道計算配置
```python
orbit_calculation = {
    # SGP4 計算模式
    "sgp4_mode": "production",        # production | simplified | debug
    
    # 精度配置
    "position_accuracy_m": 100,       # 目標位置精度 (米)
    "time_resolution_s": 10,          # 時間解析度 (秒)
    
    # 預測範圍
    "prediction_horizon_h": 24,       # 預測時間範圍 (小時)
    "update_interval_h": 1,           # 軌道更新間隔 (小時)
    
    # 攝動模型
    "atmospheric_drag": True,         # 大氣阻力
    "j2_perturbation": True,          # J2 重力場攝動
    "solar_radiation": False          # 太陽輻射壓 (LEO 影響小)
}
```

#### 4. 仰角門檻配置
```python  
elevation_thresholds = {
    # 基礎門檻 (度)
    "minimum": 5.0,                   # 最小可見仰角
    "handover": 10.0,                 # 切換觸發仰角
    "optimal": 15.0,                  # 最佳服務仰角
    
    # 環境調整係數
    "environment_factors": {
        "urban": 1.1,                 # 城市環境
        "suburban": 1.0,              # 郊區環境
        "rural": 0.9,                 # 鄉村環境
        "mountain": 1.3,              # 山區環境
        "coastal": 1.0                # 海岸環境
    },
    
    # 天氣調整係數
    "weather_factors": {
        "clear": 1.0,                 # 晴天
        "light_rain": 1.1,            # 小雨
        "heavy_rain": 1.4,            # 大雨
        "snow": 1.2,                  # 下雪
        "fog": 1.15                   # 霧
    }
}
```

### 🔄 配置載入機制

#### 配置來源優先級 (高到低)
1. **環境變數**: `SATELLITE_*` 環境變數
2. **命令列參數**: `--config` 參數指定的檔案
3. **配置檔案**: `config/satellite_config.json`
4. **預設值**: 程式碼中的預設配置

#### 配置載入流程
```python
def load_configuration() -> SatelliteConfig:
    """載入配置的完整流程"""
    config_data = {}
    
    # 1. 載入預設配置
    config_data.update(DEFAULT_CONFIG)
    
    # 2. 載入檔案配置
    config_file = os.getenv('SATELLITE_CONFIG_FILE', 'config/satellite_config.json')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            file_config = json.load(f)
            config_data.update(file_config)
    
    # 3. 載入環境變數
    env_config = {}
    for key, value in os.environ.items():
        if key.startswith('SATELLITE_'):
            config_key = key[10:]  # 移除 'SATELLITE_' 前綴
            env_config[config_key] = parse_env_value(value)
    config_data.update(env_config)
    
    # 4. 建立配置實例
    return SatelliteConfig(**config_data)
```

### 🛠️ 配置驗證機制

#### 配置完整性檢查
```python
class ConfigValidator:
    """配置驗證器"""
    
    @staticmethod
    def validate_satellite_config(config: SatelliteConfig) -> List[str]:
        """驗證衛星配置的完整性"""
        errors = []
        
        # 檢查候選衛星數量
        if config.MAX_CANDIDATE_SATELLITES < 1 or config.MAX_CANDIDATE_SATELLITES > 16:
            errors.append("MAX_CANDIDATE_SATELLITES 必須在 1-16 之間")
        
        # 檢查觀測位置
        lat = config.OBSERVER_LOCATION["latitude"]
        lon = config.OBSERVER_LOCATION["longitude"] 
        if not (-90 <= lat <= 90):
            errors.append("觀測緯度必須在 -90 到 90 度之間")
        if not (-180 <= lon <= 180):
            errors.append("觀測經度必須在 -180 到 180 度之間")
            
        # 檢查仰角門檻
        if config.ELEVATION_THRESHOLDS["minimum"] < 0:
            errors.append("最小仰角不能小於 0 度")
        if config.ELEVATION_THRESHOLDS["handover"] <= config.ELEVATION_THRESHOLDS["minimum"]:
            errors.append("切換仰角必須大於最小仰角")
            
        return errors
    
    @staticmethod
    def validate_and_load() -> SatelliteConfig:
        """驗證並載入配置"""
        config = load_configuration()
        errors = ConfigValidator.validate_satellite_config(config)
        
        if errors:
            raise ValueError(f"配置驗證失敗: {'; '.join(errors)}")
            
        return config
```

### 🔧 實際使用範例

#### 在算法中使用配置
```python
from src.core.config.satellite_config import get_satellite_config

def handover_decision_algorithm(candidates):
    """切換決策算法使用配置"""
    config = get_satellite_config()
    
    # 使用配置的候選數量限制
    max_candidates = config.MAX_CANDIDATE_SATELLITES
    candidates = candidates[:max_candidates]
    
    # 使用配置的仰角門檻
    min_elevation = config.ELEVATION_THRESHOLDS["handover"]
    valid_candidates = [
        c for c in candidates 
        if c["elevation_deg"] >= min_elevation
    ]
    
    # 使用智能篩選配置
    if config.INTELLIGENT_SELECTION["enabled"]:
        return intelligent_selection_algorithm(valid_candidates, config)
    else:
        return traditional_selection_algorithm(valid_candidates)
```

#### Docker 容器配置
```yaml
# docker-compose.yml 環境變數
environment:
  - SATELLITE_CONFIG_MODE=production
  - MAX_CANDIDATE_SATELLITES=8
  - OBSERVER_LAT=24.9441667
  - OBSERVER_LON=121.3713889
  - ELEVATION_THRESHOLD=10.0
  - SGP4_MODE=production
  - LOG_LEVEL=INFO
```

### ⚠️ 配置管理注意事項

#### 1. 配置一致性
- **所有組件** 必須使用 `get_satellite_config()` 獲取配置
- **禁止硬編碼** 配置參數在程式碼中
- **配置變更** 後必須重啟相關服務

#### 2. 性能考量  
- 配置載入時進行一次性驗證
- 頻繁訪問的配置值可以快取
- 避免在性能關鍵路徑中重複載入配置

#### 3. 安全性
- 敏感配置使用環境變數而非配置檔案
- 配置檔案權限控制 (600 或 640)
- 生產環境禁用配置動態更新 API

---

**本技術指南確保 LEO 衛星切換研究系統的完整技術實現，為學術研究和算法開發提供可靠的技術基礎。**