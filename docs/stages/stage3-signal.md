# 📡 階段三：信號品質分析與3GPP事件處理

[🔄 返回數據流程導航](../README.md) > 階段三

## 📖 階段概述

**目標**：對候選衛星進行精細信號品質分析及 3GPP NTN 事件處理  
**輸入**：智能篩選處理器記憶體傳遞的篩選結果  
**輸出**：信號品質數據 + 3GPP事件數據（約200MB）  
**實際處理**：391顆衛星 (358 Starlink + 33 OneWeb)
**處理時間**：約 3-5 分鐘

## 🎯 核心處理模組

### 1. 📊 信號品質分析模組

#### RSRP (Reference Signal Received Power) 計算
- **自由空間路徑損耗**：基於 ITU-R P.525 標準
- **大氣衰減模型**：ITU-R P.618 雨衰模型
- **都卜勒頻移補償**：基於相對速度計算

```python
# 信號品質計算公式
RSRP_dBm = Tx_Power_dBm - Path_Loss_dB - Atmospheric_Loss_dB - Antenna_Loss_dB
Path_Loss_dB = 32.45 + 20*log10(frequency_MHz) + 20*log10(distance_km)
```

#### 信號品質指標
- **RSRP範圍**：-140 ~ -50 dBm
- **RSRQ計算**：基於干擾加雜訊比
- **SINR估算**：考慮多衛星干擾

### 2. 🛰️ 3GPP NTN 事件處理

#### A4事件 (Serving cell becomes better than threshold)
- **觸發條件**：RSRP > -100 dBm 持續 3秒
- **用途**：服務衛星確認
- **頻率**：每顆衛星可見期間 1-3 次

#### A5事件 (Serving cell becomes worse than threshold1 and neighbour becomes better than threshold2)
- **觸發條件**：
  - 服務衛星 RSRP < -105 dBm
  - 鄰居衛星 RSRP > -100 dBm
- **用途**：換手觸發判斷
- **頻率**：平均每小時 15-25 次

#### D2事件 (Distance becomes larger than threshold)
- **觸發條件**：衛星距離 > 1,500 km
- **用途**：預防性換手準備
- **頻率**：每顆衛星週期 2-4 次

## 🏗️ 處理架構實現

### 主要實現位置
```bash
# 信號品質分析引擎
/netstack/src/stages/signal_quality_analysis_processor.py
├── SignalQualityAnalysisProcessor.calculate_signal_quality()      # 信號品質分析
├── SignalQualityAnalysisProcessor.analyze_3gpp_events()           # 3GPP事件生成
├── SignalQualityAnalysisProcessor.generate_final_recommendations() # 最終建議生成
└── SignalQualityAnalysisProcessor.process_signal_quality_analysis()  # 完整流程執行

# 3GPP事件生成器
/netstack/src/services/signal/gpp3_event_generator.py
├── GPP3EventGenerator.generate_a4_events()               # A4事件生成
├── GPP3EventGenerator.generate_a5_events()               # A5事件生成
└── GPP3EventGenerator.generate_d2_events()               # D2事件生成
```

### 處理流程詳解

1. **基礎信號計算** (391顆衛星 × 720個時間點)
   - 計算每個時間點的 RSRP/RSRQ/SINR
   - 生成信號品質時間序列
   - 統計信號品質分佈

2. **3GPP事件檢測**
   - 掃描信號時間序列
   - 識別符合條件的事件觸發點
   - 生成標準化事件記錄

3. **品質統計分析**
   - 計算每顆衛星的信號統計特徵
   - 生成信號品質熱力圖數據
   - 評估換手候選衛星優先級

## 📊 輸出數據格式

### 信號品質數據結構
```json
{
  "satellite_id": "STARLINK-1234",
  "signal_quality": {
    "statistics": {
      "mean_rsrp_dbm": -85.5,
      "std_rsrp_db": 12.3,
      "min_rsrp_dbm": -120.0,
      "max_rsrp_dbm": -65.0,
      "rsrp_stability_db": 8.2
    },
    "timeseries": [
      {"time": "2025-08-14T00:00:00Z", "rsrp_dbm": -85.5, "rsrq_db": -10.2},
      // ... 720個時間點
    ]
  }
}
```

### 3GPP事件數據結構
```json
{
  "event_type": "A5",
  "timestamp": "2025-08-14T08:15:30Z",
  "serving_satellite": "STARLINK-1234",
  "neighbor_satellite": "STARLINK-5678",
  "measurements": {
    "serving_rsrp_dbm": -108.0,
    "neighbor_rsrp_dbm": -98.5
  },
  "handover_recommendation": "trigger_handover"
}
```

## ⚙️ 配置參數

### 信號計算參數
```python
SIGNAL_CONFIG = {
    'frequency_ghz': 2.0,              # Ku波段頻率
    'tx_power_dbm': 30.0,              # 衛星發射功率  
    'antenna_gain_db': 35.0,           # 地面站天線增益
    'noise_figure_db': 2.5,            # 雜訊指數
    'interference_margin_db': 3.0       # 干擾餘量
}
```

### 3GPP事件門檻
```python
EVENT_THRESHOLDS = {
    'a4_rsrp_threshold_dbm': -100,     # A4事件RSRP門檻
    'a5_serving_threshold_dbm': -105,   # A5服務衛星門檻
    'a5_neighbor_threshold_dbm': -100,  # A5鄰居衛星門檻
    'd2_distance_threshold_km': 1500,   # D2距離門檻
    'hysteresis_db': 2.0,              # 滯後餘量
    'time_to_trigger_ms': 3000         # 觸發延遲時間
}
```

## 🔧 性能最佳化策略

### 計算最佳化
- **向量化計算**：使用numpy進行批次計算
- **記憶體預分配**：避免動態記憶體分配
- **快速數學庫**：使用優化的數學函式庫

### 數據結構最佳化
- **壓縮存儲**：使用適當的數據類型
- **索引最佳化**：建立時間和衛星索引
- **批次寫入**：減少磁碟I/O次數

## 📈 預期處理結果

### 信號品質統計
```
391顆衛星信號分析結果：
├── 高品質信號 (RSRP > -90 dBm): ~125顆 (32%)
├── 中等品質 (-90 ~ -110 dBm): ~172顆 (44%)  
└── 邊緣品質 (-110 ~ -125 dBm): ~94顆 (24%)
```

### 3GPP事件統計
```
6小時期間預期事件數量：
├── A4事件: ~1,200個 (衛星進入服務)
├── A5事件: ~800個 (換手觸發)
└── D2事件: ~600個 (距離警告)
```

## 🚨 故障排除

### 常見問題

1. **信號計算異常**
   - 檢查：衛星位置數據完整性
   - 解決：驗證階段二輸出格式

2. **3GPP事件數量異常**
   - 檢查：事件門檻設定
   - 解決：調整 EVENT_THRESHOLDS 參數

3. **處理時間過長**
   - 檢查：向量化計算是否啟用
   - 解決：檢查numpy/scipy安裝狀態

### 診斷指令

```bash
# 檢查信號品質分析模組
python -c "
from src.stages.signal_quality_analysis_processor import SignalQualityAnalysisProcessor
from src.services.signal.gpp3_event_generator import GPP3EventGenerator
print('✅ 信號品質分析模組載入成功')
"

# 驗證輸出檔案
ls -la /app/data/signal_quality_analysis/
ls -la /app/data/handover_scenarios/
```

---
**上一階段**: [階段二：智能篩選](./stage2-filtering.md)  
**下一階段**: [階段四：時間序列預處理](./stage4-timeseries.md)  
**相關文檔**: [3GPP NTN標準](../standards_implementation.md#3gpp-ntn)
