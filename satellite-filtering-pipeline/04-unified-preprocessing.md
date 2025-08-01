# 統一預處理管道設計

**狀態**: 🔧 待擴展  
**計畫開始**: 2025-08-06  
**基礎檔案**: `/simworld/backend/enhance_d2_preprocessing.py`

## 📋 設計目標

建立單一統一的預處理管道，支援所有換手事件類型和用途需求：
- **完整事件支援** - D2, D1, A4, T1 換手事件檢測
- **分層標記整合** - Tier 1/2/3 用途標記
- **數據一致性** - 所有用途使用相同數據源
- **效能優化** - 單次處理，多重輸出

## 🏗️ 管道架構設計

### 統一處理流程
```
篩選後衛星數據 (500 顆)
    ↓
SGP4 軌道傳播 (120 分鐘)
    ↓
並行處理：
├── MRL 距離計算
├── 信號強度估算
├── 都卜勒頻移計算
└── 可見性判斷
    ↓
換手事件檢測：
├── D2 事件 (已實現)
├── D1 事件 (待實現)
├── A4 事件 (待實現)
└── T1 事件 (待實現)
    ↓
分層標記與輸出
```

## 📊 換手事件定義

### D2 事件 (已實現)
```python
# 3GPP D2: 基於 MRL 距離的換手
def detect_d2_event(current_sat, target_sat, ue_position):
    """
    觸發條件：
    1. 當前衛星 MRL 距離 > Thresh1 + Hysteresis
    2. 目標衛星 MRL 距離 < Thresh2 - Hysteresis
    """
    thresh1 = 1000  # km
    thresh2 = 800   # km
    hysteresis = 50 # km
```

### D1 事件 (待實現)
```python
# 3GPP D1: 基於信號品質的換手
def detect_d1_event(current_sat, target_sat, ue_position):
    """
    觸發條件：
    1. 當前衛星 RSRP < Thresh1
    2. 目標衛星 RSRP > Thresh2
    3. 考慮載波頻率和路徑損耗
    """
    rsrp_thresh1 = -110  # dBm
    rsrp_thresh2 = -105  # dBm
```

### A4 事件 (待實現)
```python
# 3GPP A4: 鄰近衛星信號超過門檻
def detect_a4_event(current_sat, neighbor_sats, ue_position):
    """
    觸發條件：
    1. 鄰近衛星 RSRP > Thresh
    2. 持續時間 > TimeToTrigger
    3. 用於準備潛在換手
    """
    rsrp_thresh = -100  # dBm
    time_to_trigger = 100  # ms
```

### T1 事件 (待實現)
```python
# NTN 特定 T1: 衛星即將離開覆蓋範圍
def detect_t1_event(satellite, ue_position, prediction_window):
    """
    觸發條件：
    1. 預測衛星仰角 < MinElevation
    2. 預測時間 < TimeThreshold
    3. 主動換手準備
    """
    min_elevation = 10  # degrees
    time_threshold = 30  # seconds
```

## 🔧 核心實現設計

### 統一預處理器類
```python
class UnifiedSatellitePreprocessor:
    def __init__(self, config: PreprocessConfig):
        self.config = config
        self.sgp4_calculator = SGP4Calculator()
        self.event_detectors = {
            'd2': D2EventDetector(),
            'd1': D1EventDetector(),
            'a4': A4EventDetector(),
            't1': T1EventDetector()
        }
        self.tier_classifier = TierClassifier()
        
    def preprocess(self, satellites: List[Dict]) -> Dict:
        """執行統一預處理"""
        # Step 1: SGP4 軌道計算
        orbital_data = self._compute_orbits(satellites)
        
        # Step 2: 信號參數計算
        signal_data = self._compute_signals(orbital_data)
        
        # Step 3: 換手事件檢測
        events = self._detect_all_events(signal_data)
        
        # Step 4: 分層標記
        tiered_data = self._apply_tier_labels(satellites)
        
        # Step 5: 整合輸出
        return self._create_unified_output(
            orbital_data, signal_data, events, tiered_data
        )
```

### 信號強度計算
```python
def _compute_signal_strength(self, sat_position, ue_position):
    """計算接收信號強度 (RSRP)"""
    # 自由空間路徑損耗
    distance = calculate_distance(sat_position, ue_position)
    frequency = 2.0e9  # 2 GHz (S-band)
    
    # Friis 傳輸方程
    path_loss = 20 * log10(distance) + 20 * log10(frequency) + 32.44
    
    # 考慮大氣衰減
    elevation = calculate_elevation(sat_position, ue_position)
    atmospheric_loss = self._atmospheric_attenuation(elevation)
    
    # 計算 RSRP
    tx_power = 30  # dBm
    antenna_gain = 15  # dBi
    rsrp = tx_power + antenna_gain - path_loss - atmospheric_loss
    
    return rsrp
```

### 都卜勒頻移計算
```python
def _compute_doppler_shift(self, sat_velocity, sat_position, ue_position):
    """計算都卜勒頻移"""
    # 相對速度向量
    relative_velocity = calculate_relative_velocity(
        sat_velocity, sat_position, ue_position
    )
    
    # 都卜勒公式
    frequency = 2.0e9  # Hz
    c = 299792458  # m/s
    doppler_shift = frequency * (relative_velocity / c)
    
    return doppler_shift
```

## 📦 統一輸出格式

### JSON 結構設計
```json
{
  "metadata": {
    "version": "2.0.0",
    "processing_time": "2025-08-01T12:00:00Z",
    "total_satellites": 500,
    "time_span_minutes": 120,
    "tier_distribution": {
      "tier_1": 20,
      "tier_2": 80,
      "tier_3": 500
    }
  },
  "satellites": [
    {
      "id": "STARLINK-1234",
      "constellation": "starlink",
      "tier_labels": ["tier_1", "tier_2", "tier_3"],
      "orbital_data": {
        "positions": [...],
        "velocities": [...],
        "timestamps": [...]
      },
      "signal_data": {
        "rsrp": [...],
        "doppler": [...],
        "elevation": [...],
        "azimuth": [...]
      },
      "mrl_distances": [...],
      "handover_events": {
        "d2": [{
          "timestamp": "2025-08-01T12:15:30Z",
          "target_satellite": "STARLINK-5678",
          "trigger_reason": "mrl_distance_exceeded"
        }],
        "d1": [...],
        "a4": [...],
        "t1": [...]
      }
    }
  ],
  "ue_trajectory": {
    "positions": [...],
    "timestamps": [...]
  },
  "summary_statistics": {
    "total_d2_events": 45,
    "total_d1_events": 38,
    "total_a4_events": 156,
    "total_t1_events": 52,
    "average_handover_interval": 158.3
  }
}
```

## 💡 關鍵設計決策

### 1. 並行處理策略
```python
# 使用多線程加速計算
from concurrent.futures import ThreadPoolExecutor

def _parallel_compute(self, satellites, compute_func):
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for sat in satellites:
            future = executor.submit(compute_func, sat)
            futures.append(future)
        
        results = [f.result() for f in futures]
    return results
```

### 2. 記憶體優化
- 使用生成器處理大型時間序列
- 分批處理衛星數據
- 定期清理中間結果

### 3. 增量更新支援
```python
def preprocess_incremental(self, new_time_window):
    """支援增量時間窗口更新"""
    # 載入先前狀態
    previous_state = self._load_state()
    
    # 只計算新時間段
    new_data = self._compute_new_window(
        previous_state, new_time_window
    )
    
    # 合併結果
    return self._merge_results(previous_state, new_data)
```

## 🚀 實施計畫

### Phase 1: 事件檢測擴展 (2天)
- [ ] 實現 D1 事件檢測器
- [ ] 實現 A4 事件檢測器
- [ ] 實現 T1 事件檢測器

### Phase 2: 信號計算模組 (2天)
- [ ] RSRP 計算實現
- [ ] 都卜勒頻移計算
- [ ] 大氣衰減模型

### Phase 3: 整合與優化 (2天)
- [ ] 整合所有模組
- [ ] 性能優化
- [ ] 測試驗證

## ✅ 完成標準

- [ ] 四種事件類型完整支援
- [ ] 處理 500 顆衛星 < 60 秒
- [ ] 記憶體使用 < 4GB
- [ ] 輸出格式向後兼容
- [ ] 單元測試覆蓋率 > 90%

## 📚 相關文件

- D2 事件實現：`/simworld/backend/enhance_d2_preprocessing.py`
- 分層設計：`03-tier-classification.md`
- 3GPP 標準：`/docs/ts.md`, `/docs/sib19.md`
