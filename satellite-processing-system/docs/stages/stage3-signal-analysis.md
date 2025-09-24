# 📡 階段三：信號分析層

[🔄 返回文檔總覽](../README.md) > 階段三

## 📖 階段概述

**目標**：對可連線衛星進行精細信號品質分析及3GPP NTN事件檢測
**輸入**：Stage 2鏈路可行性評估層記憶體傳遞的可連線衛星軌道數據
**輸出**：信號品質數據 + 3GPP事件數據 → 記憶體傳遞至階段四
**核心工作**：
1. RSRP/RSRQ/SINR信號品質計算
2. 3GPP NTN標準事件檢測（A4/A5/D2事件）
3. 物理層參數計算（路徑損耗、都卜勒偏移）
4. 信號品質評估和分類

**實際處理**：約500-1000顆可連線衛星的信號分析
**處理時間**：約6-7秒（v2.0優化版本）

### 🏗️ v2.0 模組化架構

Stage 3 專注於純粹的信號分析，移除換手決策功能：

```
┌─────────────────────────────────────────────────────────────┐
│                   Stage 3: 信號分析層                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │Signal Quality│  │3GPP Event   │  │Physics      │       │
│  │Calculator   │  │Detector     │  │Calculator   │       │
│  │             │  │             │  │             │       │
│  │ • RSRP計算   │  │ • A4事件檢測 │  │ • 路徑損耗   │       │
│  │ • RSRQ計算   │  │ • A5事件檢測 │  │ • 都卜勒偏移 │       │
│  │ • SINR計算   │  │ • D2事件檢測 │  │ • 大氣衰減   │       │
│  │ • 品質評估   │  │ • 門檻管理   │  │ • 自由空間   │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│           │              │               │                │
│           └──────────────┼───────────────┘                │
│                          ▼                                │
│           ┌─────────────────────────────────┐            │
│           │   Stage3 Signal Processor      │            │
│           │                                 │            │
│           │ • 信號分析協調                   │            │
│           │ • 3GPP事件管理                  │            │
│           │ • 品質監控報告                   │            │
│           │ • 結果數據整合                   │            │
│           └─────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### 核心原則
- **信號精度**: 使用標準物理公式確保信號計算精度
- **3GPP合規**: 完全符合3GPP NTN標準的事件檢測
- **純粹分析**: 只進行信號分析，不做優化決策
- **實時監控**: 支援信號品質的實時監控和報告

## 📦 模組設計

### 1. Signal Quality Calculator (`signal_quality_calculator.py`)

#### 功能職責
- RSRP (Reference Signal Received Power) 計算
- RSRQ (Reference Signal Received Quality) 計算
- SINR (Signal to Interference plus Noise Ratio) 計算
- 信號品質評估和分類

#### 核心方法
```python
class SignalQualityCalculator:
    def calculate_rsrp(self, satellite_data):
        """計算參考信號接收功率"""

    def calculate_rsrq(self, rsrp, rssi):
        """計算參考信號接收品質"""

    def calculate_sinr(self, signal_power, interference_power):
        """計算信號干擾噪聲比"""
```

### 2. 3GPP Event Detector (`gpp_event_detector.py`)

#### 功能職責
- A4事件檢測：鄰近衛星信號優於門檻
- A5事件檢測：服務衛星劣化且鄰近衛星良好
- D2事件檢測：基於距離的換手觸發
- 門檻管理和事件報告

#### 核心方法
```python
class GPPEventDetector:
    def detect_a4_events(self, satellites, threshold):
        """檢測A4事件"""

    def detect_a5_events(self, serving_sat, neighbor_sats):
        """檢測A5事件"""

    def detect_d2_events(self, satellites, distance_threshold):
        """檢測D2事件"""
```

### 3. Physics Calculator (`physics_calculator.py`)

#### 功能職責
- 自由空間路徑損耗計算
- 都卜勒頻移計算
- 大氣衰減模型
- 傳播延遲計算

#### 核心方法
```python
class PhysicsCalculator:
    def calculate_free_space_loss(self, distance, frequency):
        """計算自由空間路徑損耗"""

    def calculate_doppler_shift(self, velocity, frequency):
        """計算都卜勒頻移"""

    def calculate_atmospheric_loss(self, elevation, frequency):
        """計算大氣衰減"""
```

### 4. Stage3 Signal Processor (`stage3_signal_analysis_processor.py`)

#### 功能職責
- 協調整個信號分析流程
- 管理3GPP事件檢測
- 整合各種信號品質指標
- 生成信號分析報告

## 🔄 數據流程

### 輸入處理
```python
# 從Stage 2接收數據
stage2_output = {
    'satellites': {...},  # 可連線衛星軌道數據
    'metadata': {...}     # 軌道計算元數據
}
```

### 處理流程
1. **軌道數據驗證**: 確認從Stage 2接收的數據完整性
2. **信號品質計算**: 計算RSRP、RSRQ、SINR等指標
3. **物理參數計算**: 路徑損耗、都卜勒偏移等
4. **3GPP事件檢測**: A4、A5、D2事件檢測
5. **結果整合**: 組織信號分析輸出數據

### 輸出格式
```python
stage3_output = {
    'stage': 'stage3_signal_analysis',
    'satellites': {
        'satellite_id': {
            'signal_quality': {
                'rsrp_dbm': -85.2,
                'rsrq_db': -12.5,
                'sinr_db': 15.3
            },
            'gpp_events': [
                {'type': 'A4', 'timestamp': '...', 'threshold': -100}
            ],
            'physics_parameters': {
                'path_loss_db': 165.2,
                'doppler_shift_hz': 1250.5,
                'atmospheric_loss_db': 2.1
            }
        }
    },
    'metadata': {
        'processing_time': '2025-09-21T04:07:00Z',
        'analyzed_satellites': 756,
        'detected_events': 1250
    }
}
```

## ⚙️ 配置參數

### 信號計算配置
```yaml
signal_calculation:
  frequency_ghz: 12.0         # Ku頻段12GHz
  tx_power_dbm: 43.0          # 發射功率43dBm
  antenna_gain_db: 35.0       # 天線增益35dB
  noise_floor_dbm: -114.0     # 噪聲底限
```

### 3GPP事件門檻
```yaml
gpp_thresholds:
  a4_threshold_dbm: -100      # A4事件門檻
  a5_threshold1_dbm: -110     # A5事件門檻1
  a5_threshold2_dbm: -95      # A5事件門檻2
  d2_distance_km: 1500        # D2事件距離門檻
```

## 🎯 性能指標

### 處理效能
- **輸入數據**: 約500-1000顆可連線衛星
- **計算時間**: 6-7秒
- **記憶體使用**: <500MB
- **輸出數據**: 信號品質 + 3GPP事件數據

### 分析精度
- **RSRP精度**: ±2dBm
- **頻率精度**: ±10Hz
- **事件檢測**: >95%準確率

## 🔍 驗證標準

### 輸入驗證
- 軌道數據完整性
- 時間序列連續性
- 可連線衛星數量合理性

### 計算驗證
- 信號公式標準合規
- 3GPP事件檢測邏輯
- 物理參數合理性

### 輸出驗證
- 信號品質數值範圍
- 事件檢測結果正確性
- 數據結構完整性

---
**下一處理器**: [時間序列預處理](./stage4-timeseries-preprocessing.md)
**相關文檔**: [v2.0重構計劃](../refactoring_plan_v2/stage3_signal_analysis.md)