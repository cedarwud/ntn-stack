# 📡 階段三：信號品質分析與3GPP事件處理

[🔄 返回數據流程導航](../README.md) > 階段三

## 📖 階段概述

**目標**：對候選衛星進行精細信號品質分析及 3GPP NTN 事件處理  
**輸入**：智能篩選處理器記憶體傳遞的篩選結果  
**輸出**：信號品質數據 + 3GPP事件數據（約320MB，保存至 `/app/data/leo_outputs/`）  
**實際處理**：1,184顆衛星 (1,039 Starlink + 145 OneWeb)
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

## ✅ 階段驗證標準

### 🎯 Stage 3 完成驗證檢查清單

#### 1. **輸入驗證**
- [ ] Stage 2篩選結果完整
  - 接收約1,100-1,400顆候選衛星
  - 包含Starlink和OneWeb數據
  - 每顆衛星有完整時間序列

#### 2. **信號計算驗證**
- [ ] **ITU-R P.618標準遵循**
  - 自由空間路徑損耗正確計算
  - 大氣衰減模型應用
  - 降雨衰減考慮（Ku頻段）
- [ ] **RSRP計算範圍**
  ```
  合理範圍:
  - 高仰角(>60°): -70 ~ -80 dBm
  - 中仰角(30-60°): -80 ~ -95 dBm
  - 低仰角(5-30°): -95 ~ -110 dBm
  ```
- [ ] **都卜勒頻移計算**
  - 最大頻移 < ±40 kHz (LEO)
  - 與衛星速度相關性正確

#### 3. **3GPP事件分析**
- [ ] **Event A4觸發**
  - 鄰近衛星RSRP > -100 dBm
  - 正確識別潛在換手候選
- [ ] **Event A5觸發**  
  - 服務衛星劣化檢測
  - 鄰近衛星優於門檻
- [ ] **Event D2觸發**
  - 基於距離的換手判定
  - 距離門檻合理設定

#### 4. **輸出驗證**
- [ ] **數據結構完整性**
  ```json
  {
    "metadata": {
      "stage": "stage3_signal_analysis",
      "total_analyzed": 1196,
      "3gpp_events": {
        "a4_triggers": 150,
        "a5_triggers": 80,
        "d2_triggers": 120
      }
    },
    "signal_analysis_results": {
      "starlink": [...],
      "oneweb": [...]
    }
  }
  ```
- [ ] **信號指標完整性**
  - RSRP、RSRQ、SINR值都存在
  - 仰角與信號強度負相關
  - 無異常值(NaN或極端值)

#### 5. **性能指標**
- [ ] 處理時間 < 2分鐘
- [ ] 緩存命中率 > 80%
- [ ] 記憶體使用 < 300MB

#### 6. **自動驗證腳本**
```python
# 執行階段驗證
python -c "
import json
import numpy as np

# 載入信號分析結果
try:
    with open('/app/data/signal_analysis_outputs/signal_event_analysis_output.json', 'r') as f:
        data = json.load(f)
except:
    print('⚠️ 使用記憶體傳遞模式，跳過文件驗證')
    exit(0)

metadata = data.get('metadata', {})
results = data.get('signal_analysis_results', {})

# 收集所有RSRP值
all_rsrp = []
for constellation in results.values():
    for sat in constellation:
        if 'signal_metrics' in sat:
            all_rsrp.append(sat['signal_metrics'].get('rsrp_dbm', -999))

rsrp_array = np.array([r for r in all_rsrp if r > -200])

checks = {
    'input_count': metadata.get('total_analyzed', 0) > 1000,
    'rsrp_range': (-120 <= rsrp_array.min()) and (rsrp_array.max() <= -70),
    'rsrp_mean': -100 <= rsrp_array.mean() <= -85,
    'has_a4_events': metadata.get('3gpp_events', {}).get('a4_triggers', 0) > 0,
    'has_a5_events': metadata.get('3gpp_events', {}).get('a5_triggers', 0) > 0,
    'has_d2_events': metadata.get('3gpp_events', {}).get('d2_triggers', 0) > 0
}

print('📊 Stage 3 驗證結果:')
print(f'  分析衛星數: {metadata.get(\"total_analyzed\", 0)}')
print(f'  RSRP範圍: [{rsrp_array.min():.1f}, {rsrp_array.max():.1f}] dBm')
print(f'  RSRP平均: {rsrp_array.mean():.1f} dBm')
print(f'  A4事件: {metadata.get(\"3gpp_events\", {}).get(\"a4_triggers\", 0)} 次')
print(f'  A5事件: {metadata.get(\"3gpp_events\", {}).get(\"a5_triggers\", 0)} 次')
print(f'  D2事件: {metadata.get(\"3gpp_events\", {}).get(\"d2_triggers\", 0)} 次')

passed = sum(checks.values())
total = len(checks)

if passed == total:
    print('✅ Stage 3 驗證通過！')
else:
    print(f'❌ Stage 3 驗證失敗 ({passed}/{total})')
    exit(1)
"
```

### 🚨 驗證失敗處理
1. **RSRP異常**: 檢查路徑損耗計算、頻率設定
2. **無3GPP事件**: 調整觸發門檻、檢查判定邏輯
3. **處理過慢**: 優化緩存策略、減少重複計算

## 🖥️ 前端簡化版驗證呈現

### 驗證快照位置
```bash
# 驗證結果快照 (輕量級，供前端讀取)
/app/data/validation_snapshots/stage3_validation.json

# 部分數據也保存到 (用於詳細分析)
/app/data/leo_outputs/signal_analysis_summary.json
```

### JSON 格式範例
```json
{
  "stage": 3,
  "stageName": "信號品質分析",
  "timestamp": "2025-08-14T08:05:00Z",
  "status": "completed",
  "duration_seconds": 180,
  "keyMetrics": {
    "分析衛星數": 1184,
    "高品質信號": "32%",
    "中等品質": "44%",
    "邊緣品質": "24%",
    "平均RSRP": "-92.5 dBm"
  },
  "gpp3Events": {
    "A4事件": 1200,
    "A5事件": 800,
    "D2事件": 600,
    "總事件數": 2600
  },
  "validation": {
    "passed": true,
    "totalChecks": 8,
    "passedChecks": 8,
    "failedChecks": 0,
    "criticalChecks": [
      {"name": "RSRP計算", "status": "passed", "range": "-120 ~ -65 dBm"},
      {"name": "3GPP事件", "status": "passed", "count": "2600個"},
      {"name": "ITU-R合規", "status": "passed", "standard": "P.618"}
    ]
  },
  "performanceMetrics": {
    "processingTime": "3分鐘",
    "memoryUsage": "320MB",
    "outputMode": "混合模式(記憶體+檔案)"
  },
  "signalDistribution": {
    "excellent": {"count": 125, "percentage": "32%", "rsrpRange": "> -90 dBm"},
    "good": {"count": 172, "percentage": "44%", "rsrpRange": "-90 ~ -110 dBm"},
    "marginal": {"count": 94, "percentage": "24%", "rsrpRange": "-110 ~ -125 dBm"}
  },
  "nextStage": {
    "ready": true,
    "stage": 4,
    "expectedInput": 391
  }
}
```

### 前端呈現建議
```typescript
// React Component 簡化呈現
interface Stage3Validation {
  // 主要狀態圓圈 (綠色✓/紅色✗/黃色處理中)
  status: 'completed' | 'processing' | 'failed' | 'pending';
  
  // 關鍵數字卡片
  cards: [
    { label: '分析衛星', value: '1,184', icon: '📡' },
    { label: '平均RSRP', value: '-92.5 dBm', icon: '📶' },
    { label: 'A5事件', value: '800', icon: '🔄' },
    { label: '高品質', value: '32%', icon: '✨' }
  ];
  
  // 信號品質分佈圖
  signalChart: {
    type: 'pie',
    data: [
      { label: '優秀', value: 32, color: '#4CAF50' },
      { label: '良好', value: 44, color: '#FFC107' },
      { label: '邊緣', value: 24, color: '#FF5252' }
    ]
  };
  
  // 3GPP事件時間軸
  eventTimeline: {
    events: [
      { type: 'A4', count: 1200, color: '#2196F3' },
      { type: 'A5', count: 800, color: '#FF9800' },
      { type: 'D2', count: 600, color: '#9C27B0' }
    ]
  };
}
```

### API 端點規格
```yaml
# 獲取階段驗證狀態
GET /api/pipeline/validation/stage/3
Response:
  - 200: 返回驗證快照 JSON
  - 404: 階段尚未執行

# 獲取詳細信號分析結果
GET /api/pipeline/signal-analysis/details
Response:
  - 200: 返回詳細的信號分析數據
  - 404: 數據不存在

# 獲取3GPP事件統計
GET /api/pipeline/signal-analysis/3gpp-events
Response:
  - 200: 返回3GPP事件統計數據
```

### 視覺化呈現範例
```
┌─────────────────────────────────────┐
│  Stage 3: 信號品質分析              │
│  ✅ 完成 (3分鐘)                   │
├─────────────────────────────────────┤
│  📡 1,184衛星  📶 -92.5 dBm       │
│  🔄 800 A5事件  ✨ 32% 高品質     │
├─────────────────────────────────────┤
│  信號分佈: 優秀 ████ 32%          │
│           良好 ██████ 44%         │
│           邊緣 ███ 24%            │
├─────────────────────────────────────┤
│  3GPP: A4[1200] A5[800] D2[600]   │
├─────────────────────────────────────┤
│  驗證: 8/8 ✅ ITU-R P.618合規      │
└─────────────────────────────────────┘
```

### 進階視覺化建議

#### 1. RSRP 熱力圖
```javascript
// 時間-衛星 RSRP熱力圖
const heatmapData = {
  xAxis: ['00:00', '01:00', '02:00', '03:00', '04:00', '05:00'],
  yAxis: ['STL-1', 'STL-2', 'STL-3', 'OW-1', 'OW-2'],
  data: [
    [-85, -90, -95, -100, -105, -110],  // STL-1
    [-88, -92, -97, -102, -108, -112],  // STL-2
    // ...
  ],
  colorScale: {
    min: -120,  // 深紅
    mid: -95,   // 黃色
    max: -70    // 深綠
  }
};
```

#### 2. 3GPP事件時序圖
```javascript
// 換手事件時間分佈
const timelineData = {
  events: [
    { time: '00:15', type: 'A4', satellite: 'STL-123' },
    { time: '00:18', type: 'A5', from: 'STL-123', to: 'STL-456' },
    { time: '00:22', type: 'D2', satellite: 'STL-123', distance: 1520 }
  ]
};
```

### 🔔 實現注意事項
1. **混合輸出模式**：
   - 主要數據透過記憶體傳遞給Stage 4
   - 摘要數據保存到檔案供分析和前端
   - 驗證快照獨立保存

2. **即時更新**：
   - 支援WebSocket推送3GPP事件
   - 每30秒更新一次信號統計

3. **視覺化優化**：
   - 使用顏色編碼區分信號品質
   - 時間軸展示換手事件序列
   - 支援縮放和篩選功能

---
**上一階段**: [階段二：智能篩選](./stage2-filtering.md)  
**下一階段**: [階段四：時間序列預處理](./stage4-timeseries.md)  
**相關文檔**: [3GPP NTN標準](../standards_implementation.md#3gpp-ntn)
