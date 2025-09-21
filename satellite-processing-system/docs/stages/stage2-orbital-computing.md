# 🛰️ 階段二：軌道計算層

[🔄 返回文檔總覽](../README.md) > 階段二

## 📖 階段概述

**目標**：接收Stage 1的TLE數據，執行SGP4軌道計算和初步可見性篩選
**輸入**：Stage 1的驗證TLE數據 + 時間基準（記憶體傳遞）
**輸出**：軌道計算結果 + 可見性分析 → 記憶體傳遞至階段三
**核心工作**：
1. 使用標準SGP4/SDP4算法進行軌道傳播計算
2. TEME→ITRF→WGS84座標系統精確轉換
3. 計算相對NTPU觀測點的仰角、方位角、距離
4. 初步可見性篩選（仰角門檻篩選）

**實際結果**：約500-1000顆可見衛星含完整軌道數據
**時間基準**：嚴格使用Stage 1提供的TLE epoch時間
**處理時間**：約2-3分鐘 (完整SGP4軌道計算)

### 🏗️ v2.0 模組化架構

Stage 2 採用4模組設計，專注於軌道計算核心職責：

```
┌─────────────────────────────────────────────────────────────┐
│                   Stage 2: 軌道計算層                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │SGP4 Calculator│  │Coordinate   │  │Visibility   │       │
│  │             │  │Converter    │  │Filter       │       │
│  │ • SGP4傳播   │  │             │  │             │       │
│  │ • SDP4深空   │  │ • TEME→ITRF │  │ • 仰角篩選   │       │
│  │ • 精度控制   │  │ • ITRF→WGS84│  │ • 距離篩選   │       │
│  │ • 批次計算   │  │ • 地心轉換   │  │ • 地理邊界   │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│           │              │               │                │
│           └──────────────┼───────────────┘                │
│                          ▼                                │
│           ┌─────────────────────────────────┐            │
│           │   Stage2 Orbital Processor     │            │
│           │                                 │            │
│           │ • 計算流程協調                   │            │
│           │ • 時間序列管理                   │            │
│           │ • 並行處理控制                   │            │
│           │ • 結果品質驗證                   │            │
│           └─────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### 核心原則
- **計算精度**: 使用標準SGP4/SDP4算法確保軌道計算精度
- **時間基準**: 嚴格使用TLE epoch時間作為計算基準
- **座標標準**: 支援多種座標系統的精確轉換
- **篩選效率**: 高效率的可見性預篩選

## 📦 模組設計

### 1. SGP4 Calculator (`sgp4_calculator.py`)

#### 功能職責
- 實現標準SGP4/SDP4軌道傳播算法
- 處理近地和深空衛星軌道
- 提供高精度位置和速度計算
- 支援批次計算和時間序列生成

#### 核心方法
```python
class SGP4Calculator:
    def calculate_position(self, tle_data, time_since_epoch):
        """計算指定時間的衛星位置"""

    def batch_calculate(self, tle_data_list, time_series):
        """批次計算多顆衛星的軌道"""

    def validate_calculation_accuracy(self, results):
        """驗證計算精度"""
```

### 2. Coordinate Converter (`coordinate_converter.py`)

#### 功能職責
- TEME到ITRF座標系統轉換
- ITRF到WGS84地理座標轉換
- 地心到地平座標系統轉換
- 支援高精度時間和極移參數

#### 核心方法
```python
class CoordinateConverter:
    def teme_to_itrf(self, position, velocity, time):
        """TEME到ITRF轉換"""

    def itrf_to_wgs84(self, position):
        """ITRF到WGS84轉換"""

    def calculate_look_angles(self, sat_pos, observer_pos):
        """計算觀測角度"""
```

### 3. Visibility Filter (`visibility_filter.py`)

#### 功能職責
- 仰角門檻篩選
- 距離範圍檢查
- 地理邊界驗證
- 可見性時間窗口計算

#### 核心方法
```python
class VisibilityFilter:
    def apply_elevation_threshold(self, satellites, min_elevation):
        """應用仰角門檻篩選"""

    def calculate_visibility_windows(self, satellite_positions):
        """計算可見性時間窗口"""
```

### 4. Stage2 Orbital Processor (`stage2_orbital_computing_processor.py`)

#### 功能職責
- 協調整個軌道計算流程
- 管理時間序列生成
- 控制並行處理
- 驗證結果品質

## 🔄 數據流程

### 輸入處理
```python
# 從Stage 1接收數據
stage1_output = {
    'tle_records': [...],  # 驗證過的TLE數據
    'base_time': '2025-09-21T04:00:00Z',  # 時間基準
    'metadata': {...}
}
```

### 處理流程
1. **TLE數據驗證**: 確認從Stage 1接收的數據完整性
2. **SGP4軌道計算**: 使用標準算法計算軌道位置
3. **座標系統轉換**: TEME→ITRF→WGS84→地平座標
4. **可見性分析**: 計算仰角、方位角，應用篩選條件
5. **結果整合**: 組織輸出數據格式

### 輸出格式
```python
stage2_output = {
    'stage': 'stage2_orbital_computing',
    'satellites': {
        'satellite_id': {
            'positions': [...],  # 時間序列位置數據
            'visibility_windows': [...],  # 可見性窗口
            'orbital_parameters': {...}  # 軌道參數
        }
    },
    'metadata': {
        'processing_time': '2025-09-21T04:05:00Z',
        'calculation_base_time': '2025-09-21T04:00:00Z',
        'total_satellites': 8837,
        'visible_satellites': 756
    }
}
```

## ⚙️ 配置參數

### 軌道計算配置
```yaml
orbital_calculation:
  algorithm: "SGP4"           # 使用標準SGP4算法
  time_resolution: 30         # 30秒時間解析度
  prediction_horizon: 24      # 24小時預測窗口
  coordinate_system: "TEME"   # 初始座標系統
```

### 可見性篩選配置
```yaml
visibility_filter:
  min_elevation_deg: 10.0     # 最小仰角門檻
  max_distance_km: 2000       # 最大距離限制
  observer_location:          # 觀測者位置
    latitude: 24.9
    longitude: 121.3
    altitude_km: 0.035
```

## 🎯 性能指標

### 處理效能
- **輸入數據**: 8,837顆衛星TLE數據
- **計算時間**: 2-3分鐘
- **記憶體使用**: <1GB
- **輸出數據**: 約500-1000顆可見衛星

### 精度要求
- **位置精度**: <1km誤差
- **時間精度**: <1秒誤差
- **角度精度**: <0.1度誤差

## 🔍 驗證標準

### 輸入驗證
- TLE數據格式完整性
- 時間基準一致性
- 數據血統追蹤

### 計算驗證
- SGP4算法標準合規
- 座標轉換精度檢查
- 可見性邏輯正確性

### 輸出驗證
- 數據結構完整性
- 可見衛星數量合理性
- 處理時間性能達標

---
**下一處理器**: [信號品質分析](./stage3-signal-analysis.md)
**相關文檔**: [v2.0重構計劃](../refactoring_plan_v2/stage2_orbital_computing.md)