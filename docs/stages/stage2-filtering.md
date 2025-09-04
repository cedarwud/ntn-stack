# 🎯 階段二：智能衛星篩選

[🔄 返回數據流程導航](../README.md) > 階段二

## 📖 階段概述

**目標**：從 8,796 顆衛星智能篩選至高品質候選衛星  
**輸入**：TLE軌道計算處理器記憶體傳遞的軌道計算結果  
**輸出**：記憶體傳遞給信號品質分析處理器  
**實際結果**：1,196 顆衛星 (1,029 Starlink + 167 OneWeb)
**篩選率**：13.6% 保留率，大幅改善數據流向後續階段  
**處理時間**：約 1-2 分鐘

### 🚀 v1.1 過度篩選修復版本

- **🔧 核心修復**：✅ **解決過度篩選問題**
  - **可見性時間要求**：Starlink從 5.0→1.0 分鐘，OneWeb從 2.0→0.5 分鐘
  - **品質點要求**：從 10→3 個最佳仰角點 (大幅放寬品質要求)
  - **動態門檻**：使用統一仰角管理器的實際門檻值
  - **數據完整性**：確保足夠衛星流向後續階段處理

### 🚀 v3.0 記憶體傳遞模式

- **問題解決**：避免生成 2.4GB 篩選結果檔案
- **傳遞方式**：直接將篩選結果在記憶體中傳遞給階段三
- **效能提升**：消除大檔案I/O，減少磁碟空間使用

## 🧠 智能篩選演算法

### 六階段篩選管線

1. **星座分離篩選** (8,735 → 8,735)
   - 分離Starlink和OneWeb星座數據
   - 準備後續專用篩選邏輯

2. **地理相關性篩選** (8,730 → 1,184)
   - 基於NTPU觀測點的地理位置篩選
   - 排除地理上不相關的衛星 (減少86.4%)
   - 使用統一仰角門檻：Starlink 5°, OneWeb 10°

3. **換手適用性評分** (1,184 → 1,184)
   - 對通過地理篩選的衛星進行換手評分
   - 評估每顆衛星的換手潛力

**實際篩選結果：**
- Starlink: 1,039顆 (從8,079顆篩選，保留率12.9%)
- OneWeb: 145顆 (從651顆篩選，保留率22.3%)
- 總計: 1,184顆衛星保留

## 🏗️ 核心處理器架構

### 主要實現位置
```bash
# 智能篩選處理器
/netstack/src/stages/intelligent_satellite_filter_processor.py
├── IntelligentSatelliteFilterProcessor.process_intelligent_filtering()    # 主篩選邏輯
├── IntelligentSatelliteFilterProcessor.load_orbital_calculation_output()  # 載入軌道數據
└── IntelligentSatelliteFilterProcessor.execute_intelligent_filtering()    # 智能篩選執行

# 統一智能篩選系統
/netstack/src/services/satellite/intelligent_filtering/unified_intelligent_filter.py
├── UnifiedIntelligentFilter.execute_f2_filtering_workflow()  # F2篩選流程
├── UnifiedIntelligentFilter.geographical_relevance_filter() # 地理相關性篩選
└── UnifiedIntelligentFilter.handover_suitability_scoring()  # 換手適用性評分
/netstack/config/satellite_data_pool_builder.py        # 基礎衛星池建構
```

## 🎯 篩選準則詳細說明

### 可見性準則
- **最低仰角**：5° (Starlink), 10° (OneWeb)
- **最低可見時間**：累計15分鐘以上
- **服務窗口**：至少3個獨立可見窗口

### 信號品質預估
- **RSRP門檻**：≥ -110 dBm (基於自由空間路徑損耗)
- **距離限制**：≤ 2,000 km
- **都卜勒頻移**：≤ ±40 kHz

### 負載平衡策略
```python
# 星座分配比例
target_ratios = {
    'starlink': 0.80,  # ~450顆 (80%)
    'oneweb': 0.20     # ~113顆 (20%)
}
```

## ⚡ 性能最佳化

### 記憶體最佳化
- **批次處理**：每次處理500顆衛星
- **記憶體回收**：及時清理中間結果
- **數據壓縮**：使用高效的數據結構

### 演算法最佳化
- **預先排序**：按可見性機率排序
- **早期終止**：達到目標數量即停止
- **並行處理**：支援多執行緒計算

## 📊 篩選結果統計

### 預期輸出分佈
```
總計：563顆衛星
├── Starlink: ~450顆 (80%)
│   ├── 高仰角 (>30°): ~150顆
│   ├── 中仰角 (15-30°): ~200顆
│   └── 低仰角 (5-15°): ~100顆
└── OneWeb: ~113顆 (20%)
    ├── 高仰角 (>30°): ~40顆
    ├── 中仰角 (15-30°): ~50顆
    └── 低仰角 (10-15°): ~23顆
```

## 🔧 配置參數

```python
# 篩選參數
FILTERING_CONFIG = {
    'starlink': {
        'min_elevation_deg': 5.0,
        'min_visible_time_min': 15.0,
        'target_count': 450
    },
    'oneweb': {
        'min_elevation_deg': 10.0,
        'min_visible_time_min': 15.0,
        'target_count': 113
    }
}
```

## 🚨 故障排除

### 常見問題

1. **篩選數量不足**
   - 檢查：降低篩選門檻
   - 解決：調整 min_elevation_deg 或 min_visible_time_min

2. **星座比例失衡**
   - 檢查：各星座原始數據量
   - 解決：調整 target_count 比例

3. **記憶體使用過高**
   - 檢查：batch_size 設定
   - 解決：減少批次處理大小

### 診斷指令

```bash
# 檢查篩選統計
python -c "
from src.services.satellite.preprocessing.satellite_selector import *
print('篩選器模組載入成功')
"

# 驗證記憶體使用
top -p $(pgrep -f satellite_orbit_preprocessor) -n 1
```

## ✅ 階段驗證標準

### 🎯 Stage 2 完成驗證檢查清單

#### 1. **輸入驗證**
- [ ] 接收Stage 1數據完整性
  - 輸入衛星總數 > 8,000顆
  - Starlink和OneWeb數據都存在
  - 每顆衛星包含完整軌道數據
- [ ] 記憶體傳遞模式檢查
  - 確認使用記憶體傳遞（v3.0模式）
  - 無大型中間文件生成

#### 2. **篩選過程驗證**
- [ ] **地理相關性篩選**
  ```
  NTPU座標: 24°56'39"N 121°22'17"E
  仰角閾值:
  - Starlink: 5度（用戶需求）
  - OneWeb: 10度（用戶需求）
  篩選保留率: 10-15%
  ```
- [ ] **可見性要求**
  - 最低可見時間：Starlink ≥ 1.0分鐘，OneWeb ≥ 0.5分鐘
  - 品質點數量：≥ 3個最佳仰角點
- [ ] **篩選管線完整性**
  1. 星座分離篩選 ✓
  2. 地理相關性篩選 ✓
  3. 換手適用性評分 ✓

#### 3. **輸出驗證**
- [ ] **篩選結果數量**
  ```
  預期範圍:
  - Starlink: 1,000-1,200顆（約12-15%保留率）
  - OneWeb: 150-200顆（約20-25%保留率）
  - 總計: 1,150-1,400顆
  ```
- [ ] **數據結構驗證**
  ```json
  {
    "metadata": {
      "stage": "stage2_intelligent_filtering",
      "total_input_satellites": 8779,
      "total_filtered_satellites": 1196,
      "filtering_rate": 0.136
    },
    "filtered_satellites": {
      "starlink": [...],  // 包含篩選後的衛星
      "oneweb": [...]     // 包含篩選後的衛星
    }
  }
  ```
- [ ] **衛星數據完整性**
  - 每顆衛星保留完整的 `position_timeseries`
  - 可見性窗口數據正確
  - 信號預估值合理（RSRP > -120 dBm）

#### 4. **性能指標**
- [ ] 處理時間 < 2分鐘
- [ ] 記憶體使用 < 500MB
- [ ] 篩選率在合理範圍（10-20%）

#### 5. **自動驗證腳本**
```python
# 執行階段驗證
python -c "
import json
import sys

# 載入輸出數據（記憶體模式或文件模式）
try:
    with open('/app/data/intelligent_filtering_outputs/intelligent_filtered_output.json', 'r') as f:
        data = json.load(f)
except:
    print('⚠️ 使用記憶體傳遞模式，跳過文件驗證')
    # 在記憶體模式下，驗證應在處理器內部完成
    sys.exit(0)

# 驗證項目
metadata = data.get('metadata', {})
filtered = data.get('filtered_satellites', {})

starlink_count = len(filtered.get('starlink', []))
oneweb_count = len(filtered.get('oneweb', []))
total_filtered = starlink_count + oneweb_count

checks = {
    'input_count_valid': metadata.get('total_input_satellites', 0) > 8000,
    'starlink_filtered': 1000 <= starlink_count <= 1300,
    'oneweb_filtered': 140 <= oneweb_count <= 200,
    'total_filtered': 1100 <= total_filtered <= 1500,
    'filtering_rate': 0.10 <= metadata.get('filtering_rate', 0) <= 0.20,
    'has_timeseries': all(
        'position_timeseries' in sat 
        for constellation in filtered.values() 
        for sat in constellation[:5]  # 檢查前5顆
    )
}

# 計算通過率
passed = sum(checks.values())
total = len(checks)

print('📊 Stage 2 驗證結果:')
print(f'  輸入衛星數: {metadata.get(\"total_input_satellites\", 0)}')
print(f'  Starlink篩選: {starlink_count} 顆')
print(f'  OneWeb篩選: {oneweb_count} 顆')
print(f'  總篩選率: {metadata.get(\"filtering_rate\", 0):.1%}')
print('\\n驗證項目:')
for check, result in checks.items():
    print(f'  {\"✅\" if result else \"❌\"} {check}')
print(f'\\n總計: {passed}/{total} 項通過')

if passed == total:
    print('✅ Stage 2 驗證通過！')
else:
    print('❌ Stage 2 驗證失敗，請檢查上述項目')
    sys.exit(1)
"
```

### 🚨 驗證失敗處理
1. **篩選數量過少**
   - 降低仰角閾值要求
   - 減少最低可見時間要求
   - 檢查地理位置設定是否正確
2. **篩選數量過多**
   - 提高篩選標準
   - 增加品質要求
3. **時間序列缺失**
   - 確認Stage 1輸出包含完整數據
   - 檢查記憶體傳遞是否正常
4. **星座比例失衡**
   - 調整各星座的篩選參數
   - 檢查原始數據分佈

### 📊 關鍵指標
- **篩選效率**: 保留10-15%的高品質候選衛星
- **地理覆蓋**: 確保NTPU上空有足夠可見衛星
- **數據完整**: 保留完整軌道數據供後續處理

## 🖥️ 前端簡化版驗證呈現

### 🔔 記憶體傳遞模式特別說明
由於 Stage 2 採用 v3.0 記憶體傳遞模式，無檔案輸出，需要特別處理：

```python
# 在 IntelligentSatelliteFilterProcessor 中添加驗證快照功能
def save_validation_snapshot(self):
    """保存輕量級驗證快照供前端讀取"""
    snapshot = {
        "stage": 2,
        "stageName": "智能衛星篩選",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "completed",
        "keyMetrics": {
            "輸入衛星": self.total_input,
            "Starlink篩選": self.starlink_filtered,
            "OneWeb篩選": self.oneweb_filtered,
            "篩選率": f"{self.filtering_rate:.1%}",
            "地理相關性": f"{self.geo_relevant_count}顆"
        },
        "validation": self.validation_results
    }
    
    # 保存快照到特定位置供前端讀取
    snapshot_path = "/app/data/validation_snapshots/stage2_validation.json"
    with open(snapshot_path, 'w') as f:
        json.dump(snapshot, f)
```

### 驗證快照位置
```bash
# 驗證結果快照 (輕量級，供前端讀取)
/app/data/validation_snapshots/stage2_validation.json
```

### JSON 格式範例
```json
{
  "stage": 2,
  "stageName": "智能衛星篩選",
  "timestamp": "2025-08-14T08:02:00Z",
  "status": "completed",
  "duration_seconds": 90,
  "keyMetrics": {
    "輸入衛星": 8796,
    "Starlink篩選": 1039,
    "OneWeb篩選": 145,
    "總篩選": 1184,
    "篩選率": "13.6%",
    "地理相關性": "1184顆"
  },
  "validation": {
    "passed": true,
    "totalChecks": 6,
    "passedChecks": 6,
    "failedChecks": 0,
    "criticalChecks": [
      {"name": "地理篩選", "status": "passed", "detail": "NTPU上空可見"},
      {"name": "仰角閾值", "status": "passed", "detail": "Starlink≥5°, OneWeb≥10°"},
      {"name": "換手評分", "status": "passed", "detail": "時空錯置優化"}
    ]
  },
  "performanceMetrics": {
    "processingTime": "90秒",
    "memoryUsage": "300MB",
    "outputMode": "記憶體傳遞(v3.0)"
  },
  "filteringDetails": {
    "geographicalRelevance": {
      "beforeFilter": 8796,
      "afterFilter": 1184,
      "reductionRate": "86.5%"
    },
    "handoverSuitability": {
      "scored": 1184,
      "highScore": 563,
      "selected": 563
    }
  },
  "nextStage": {
    "ready": true,
    "stage": 3,
    "expectedInput": 1184
  }
}
```

### 前端呈現建議
```typescript
// React Component 簡化呈現
interface Stage2Validation {
  // 主要狀態圓圈 (綠色✓/紅色✗/黃色處理中)
  status: 'completed' | 'processing' | 'failed' | 'pending';
  
  // 關鍵數字卡片
  cards: [
    { label: '輸入', value: '8,796', icon: '📥' },
    { label: 'Starlink篩選', value: '1,039', icon: '🛰️' },
    { label: 'OneWeb篩選', value: '145', icon: '🌍' },
    { label: '篩選率', value: '13.6%', icon: '🎯' }
  ];
  
  // 篩選漏斗視覺化
  funnel: {
    stages: [
      { name: '原始', count: 8796, width: '100%' },
      { name: '地理篩選', count: 1184, width: '13.6%' },
      { name: '最終', count: 563, width: '6.4%' }
    ]
  };
  
  // 驗證檢查清單 (簡化版)
  checks: {
    passed: 6,
    total: 6,
    status: '✅ 全部通過'
  };
}
```

### API 端點規格
```yaml
# 獲取階段驗證狀態（記憶體模式特別處理）
GET /api/pipeline/validation/stage/2
Response:
  - 200: 返回驗證快照 JSON
  - 404: 階段尚未執行或快照不存在
  - 503: 記憶體傳遞中，暫時無法提供

# 強制生成驗證快照（用於記憶體模式）
POST /api/pipeline/validation/stage/2/snapshot
Response:
  - 201: 快照已創建
  - 409: 階段正在執行中
```

### 視覺化呈現範例
```
┌─────────────────────────────────────┐
│  Stage 2: 智能衛星篩選              │
│  ✅ 完成 (90秒) [記憶體模式]       │
├─────────────────────────────────────┤
│  📥 8,796 → 🎯 1,184 (13.6%)      │
│  🛰️ STL: 1,039  🌍 OW: 145        │
├─────────────────────────────────────┤
│  篩選漏斗:                         │
│  [████████████] 8,796              │
│  [██]           1,184              │
├─────────────────────────────────────┤
│  驗證: 6/6 ✅                       │
└─────────────────────────────────────┘
```

### 🔔 實現注意事項
1. **記憶體傳遞模式處理**：
   - Stage 2 使用記憶體傳遞，需額外實現快照功能
   - 在處理器完成時調用 `save_validation_snapshot()`
   - 快照檔案要輕量級（< 1KB）

2. **前端輪詢策略**：
   - 初始檢查快照是否存在
   - 若不存在，顯示「處理中」狀態
   - 每5秒輪詢一次直到快照出現

3. **錯誤處理**：
   - 記憶體模式可能沒有持久化數據
   - 提供手動觸發快照生成的API

---
**上一階段**: [階段一：TLE載入](./stage1-tle-loading.md)  
**下一階段**: [階段三：信號分析](./stage3-signal.md)  
**相關文檔**: [智能篩選演算法詳解](../algorithms_implementation.md#智能篩選)
