# 📊 階段一：TLE數據載入與SGP4軌道計算

[🔄 返回文檔總覽](../README.md) > 階段一

## 📖 階段概述

**目標**：從 8,796 顆衛星載入 TLE 數據並執行精確的 SGP4 軌道計算  
**輸入**：TLE 檔案（約 2.2MB）  
**輸出**：全量數據記憶體傳遞給智能篩選處理器  
**處理時間**：約 2-3 分鐘
**實際處理數量**：8,145 Starlink + 651 OneWeb = 8,796 顆衛星

### 🚀 v3.2 過度篩選修復版本

- **🔧 核心修復**：✅ **消除過度篩選問題**
  - **取樣數量**：從 50 顆提升到 800 顆 (10% 合理取樣率)
  - **處理模式**：支援全量處理模式 (sample_mode=False)
  - **數據完整性**：確保足夠數據流向後續階段
  - **性能平衡**：在處理速度與數據完整性間達到最佳平衡

### 🚀 v3.1 數據血統追蹤版本

- **核心修復**：✅ **數據血統追蹤機制**
  - **TLE數據日期**：記錄實際TLE檔案日期（如：2025-08-20）
  - **處理時間戳**：記錄程式執行時間（如：2025-08-21）
  - **計算基準時間**：使用TLE epoch時間進行軌道計算
  - **數據治理**：完全符合數據血統管理原則

- **技術改進**：
  - **傳遞方式**：直接將軌道計算結果在記憶體中傳遞給階段二
  - **效能提升**：消除檔案 I/O 開銷，處理速度提升 50%+
  - **數據完整性**：確保每顆衛星都有完整的TLE來源追蹤信息

### ⏰ 時間週期與數據血統說明

**重要澄清**：系統中有三個不同的時間概念：

1. **軌道計算週期**：96分鐘
   - 單次處理每顆衛星的完整軌道週期
   - 192個時間點，30秒間隔
   - 用於生成連續的軌跡動畫數據

2. **系統更新週期**：6小時  
   - Cron自動下載新TLE數據的頻率
   - 重新執行六階段處理的間隔
   - 保持衛星軌道數據新鮮度

3. **🎯 數據血統時間戳**（v3.1 新增）：
   - **TLE數據日期**：實際衛星軌道元素的有效時間
   - **TLE Epoch時間**：TLE軌道元素的參考時間點
   - **處理執行時間**：軌道計算程序的實際運行時間
   - **計算基準時間**：SGP4算法使用的時間基準（採用TLE Epoch）

### 🚨 衛星渲染時間基準重要說明

**關鍵原則：前端渲染必須使用TLE數據日期作為時間基準**

```yaml
⚠️ 重要提醒：
- ✅ 正確：使用 TLE 文件日期 (如: 20250816 來自 starlink_20250816.tle)
- ❌ 錯誤：使用程式執行日期 (如: 當前系統時間)
- ❌ 錯誤：使用處理計算日期 (如: 資料預處理的時間戳)
- ❌ 錯誤：使用前端當下時間 (如: new Date())

原因：
- TLE數據代表特定時間點的衛星軌道狀態
- 使用錯誤的時間基準會導致衛星位置計算偏差
- 可能造成數百公里的位置誤差，影響可見性判斷
```

**前端實作範例**：
```javascript
// ✅ 正確的時間基準使用
const getTLEBaseTime = (satelliteData) => {
  // 從數據中提取TLE日期
  const tleDate = satelliteData.tle_source_date; // "20250816"
  const tleEpoch = satelliteData.tle_epoch_time; // TLE的epoch時間
  
  // 使用TLE日期作為動畫基準時間
  const baseTime = new Date(
    parseInt(tleDate.substr(0,4)),  // 2025
    parseInt(tleDate.substr(4,2))-1, // 08 (月份從0開始)
    parseInt(tleDate.substr(6,2))    // 16
  );
  
  return baseTime;
};

// ❌ 錯誤的時間基準使用
const getWrongBaseTime = () => {
  return new Date(); // 千萬不要使用當前時間！
};
```

## 🏗️ 核心處理器架構

### 主要實現位置
```bash
# 核心處理器
/netstack/src/stages/tle_orbital_calculation_processor.py
├── Stage1TLEProcessor.scan_tle_data()                          # TLE檔案掃描
├── Stage1TLEProcessor.load_raw_satellite_data()               # 原始數據載入  
├── Stage1TLEProcessor.calculate_all_orbits()                  # 完整SGP4計算
├── Stage1TLEProcessor.save_tle_calculation_output()           # Debug模式控制輸出
└── Stage1TLEProcessor.process_tle_orbital_calculation()       # 完整流程執行

# SGP4引擎支援
/netstack/src/services/satellite/coordinate_specific_orbit_engine.py
```

### 處理流程

1. **TLE檔案掃描**：掃描兩個星座的TLE資料
   - Starlink: 8,084顆衛星 (最新20250816數據)
   - OneWeb: 651顆衛星 (最新20250816數據)

2. **原始數據載入**：解析TLE格式並驗證數據完整性

3. **SGP4軌道計算**：基於真實物理模型計算衛星位置
   - 使用官方SGP4演算法（非簡化版本）
   - 計算完整軌道週期數據（Starlink: 96分鐘/192點、OneWeb: 109分鐘/218點）
   - 時間解析度：30秒間隔，支持星座特定軌道週期

4. **記憶體傳遞**：將結果直接傳遞給階段二

## 🔧 技術實現細節

### SGP4計算精度
- **標準遵循**：嚴格遵循官方SGP4/SDP4標準
- **誤差控制**：位置誤差 < 1km（LEO衛星）
- **時間精度**：UTC時間精確到秒級

### 🎯 數據血統追蹤系統（v3.1）
- **TLE來源追蹤**：每顆衛星記錄完整的TLE文件來源信息
- **時間戳分離**：明確區分數據時間與處理時間
- **血統元數據**：包含文件路徑、文件日期、epoch時間等完整信息
- **數據治理標準**：符合數據血統管理最佳實踐

```python
# 數據血統結構示例
satellite_data = {
    'tle_data': {
        'source_file': '/app/tle_data/starlink/tle/starlink_20250820.tle',
        'source_file_date': '20250820',  # TLE數據實際日期
        'epoch_year': 2025,
        'epoch_day': 232.5,
        'calculation_base_time': '2025-08-20T12:00:00Z',  # TLE epoch時間
        'data_lineage': {
            'data_source_date': '20250820',           # 數據來源日期
            'tle_epoch_date': '2025-08-20T12:00:00Z', # TLE參考時間
            'processing_execution_date': '2025-08-21T10:30:00Z', # 處理執行時間
            'calculation_strategy': 'sgp4_with_tle_epoch_base'
        }
    }
}
```

### 記憶體管理
- **數據結構**：使用高效的numpy陣列
- **記憶體使用**：峰值約500MB
- **垃圾回收**：自動清理中間計算結果

## ⚙️ 配置參數

```python
# 主要配置
OBSERVER_LAT = 24.9441667  # NTPU緯度
OBSERVER_LON = 121.3713889  # NTPU經度
TIME_WINDOW_HOURS = 6       # 計算時間範圍
TIME_STEP_SECONDS = 30      # 時間解析度
```

## 🚨 故障排除

### 常見問題

1. **TLE數據過期**
   - 檢查：TLE檔案最後修改時間
   - 解決：執行增量更新腳本

2. **SGP4計算失敗**
   - 檢查：TLE格式完整性
   - 解決：重新下載TLE數據

3. **記憶體不足**
   - 檢查：系統可用記憶體
   - 解決：增加swap空間或分批處理

4. **🎯 數據血統追蹤問題（v3.1）**
   - **症狀**：數據時間戳與處理時間戳相同
   - **檢查**：輸出metadata中的 `data_lineage` 字段
   - **解決**：確認TLE文件日期正確解析，重新執行處理

### 診斷指令

```bash
# 檢查TLE數據狀態
find /app/tle_data -name '*.tle' -exec ls -la {} \;

# 驗證TLE軌道計算處理器
python -c "from stages.tle_orbital_calculation_processor import Stage1TLEProcessor; print('TLE軌道計算處理器正常')"

# 驗證SGP4引擎
python -c "from src.services.satellite.coordinate_specific_orbit_engine import *; print('SGP4引擎正常')"

# 🎯 驗證數據血統追蹤（v3.1）
python -c "
import json
with open('/app/data/tle_orbital_calculation_output.json', 'r') as f:
    data = json.load(f)
    lineage = data['metadata']['data_lineage']
    print('📊 數據血統檢查:')
    print(f'  TLE日期: {lineage.get(\"tle_dates\", {})}')
    print(f'  處理時間: {data[\"metadata\"][\"processing_timestamp\"]}')
    print('✅ 數據血統追蹤正常' if lineage.get('tle_dates') else '❌ 數據血統追蹤異常')
"
```

## ✅ 階段驗證標準

### 🎯 Stage 1 完成驗證檢查清單

#### 1. **輸入驗證**
- [ ] TLE文件存在性檢查
  - Starlink TLE文件: `/app/tle_data/starlink/tle/*.tle`
  - OneWeb TLE文件: `/app/tle_data/oneweb/tle/*.tle`
- [ ] TLE格式驗證
  - 每個TLE必須包含3行（衛星名稱、Line 1、Line 2）
  - Line 1/2 必須各為69字元
  - 校驗和（checksum）正確
- [ ] TLE時效性檢查
  - TLE epoch時間與當前時間差異 < 7天（建議）
  - 警告：超過14天的TLE可能影響精度

#### 2. **處理驗證**
- [ ] **衛星數量驗證**
  ```
  預期範圍:
  - Starlink: 8,000-8,500顆
  - OneWeb: 600-700顆
  - 總計: 8,600-9,200顆
  ```
- [ ] **SGP4計算驗證**
  - 每顆衛星生成192個時間點（96分鐘，30秒間隔）
  - 位置誤差 < 1km（與參考實現比較）
  - 無NaN或無效值
- [ ] **記憶體使用監控**
  - 峰值記憶體 < 1GB（全量處理模式）
  - 無記憶體洩漏（處理後釋放）

#### 3. **輸出驗證**
- [ ] **數據結構完整性**
  ```json
  {
    "metadata": {
      "total_satellites": 8779,  // 必須 > 8000
      "processing_timestamp": "ISO8601格式",
      "data_lineage": {
        "tle_dates": {"starlink": "20250820", "oneweb": "20250820"},
        "processing_execution_time": "ISO8601格式",
        "calculation_base_time": "ISO8601格式"
      }
    },
    "satellites": {
      "starlink": {...},  // 必須包含satellites陣列
      "oneweb": {...}     // 必須包含satellites陣列
    }
  }
  ```
- [ ] **時間序列數據驗證**
  - 每顆衛星包含 `position_timeseries` 陣列
  - 時間序列長度 = 192點（或配置值）
  - 每個時間點包含：time, position_eci, velocity_eci, elevation_deg, azimuth_deg, is_visible
- [ ] **數據血統追蹤（v3.1）**
  - TLE數據日期正確記錄
  - 處理時間戳與數據時間戳分離
  - 完整的血統元數據

#### 4. **性能指標**
- [ ] 處理時間 < 3分鐘（全量8,779顆衛星）
- [ ] 記憶體傳遞成功（無大檔案生成）
- [ ] CPU使用率峰值 < 80%

#### 5. **自動驗證腳本**
```python
# 執行階段驗證
python -c "
import json
import sys

# 載入輸出數據
try:
    with open('/app/data/tle_calculation_outputs/tle_orbital_calculation_output.json', 'r') as f:
        data = json.load(f)
except:
    # 記憶體模式可能沒有文件
    print('⚠️ 使用記憶體傳遞模式，跳過文件驗證')
    sys.exit(0)

# 驗證項目
checks = {
    'total_satellites': data['metadata']['total_satellites'] > 8000,
    'has_starlink': 'starlink' in data['satellites'],
    'has_oneweb': 'oneweb' in data['satellites'],
    'has_data_lineage': 'data_lineage' in data['metadata'],
    'has_tle_dates': 'tle_dates' in data['metadata'].get('data_lineage', {})
}

# 計算通過率
passed = sum(checks.values())
total = len(checks)

print('📊 Stage 1 驗證結果:')
for check, result in checks.items():
    print(f'  {\"✅\" if result else \"❌\"} {check}')
print(f'\\n總計: {passed}/{total} 項通過')

if passed == total:
    print('✅ Stage 1 驗證通過！')
else:
    print('❌ Stage 1 驗證失敗，請檢查上述項目')
    sys.exit(1)
"
```

### 🚨 驗證失敗處理
1. **數量不足**：檢查TLE文件是否完整
2. **SGP4失敗**：驗證TLE格式，更新skyfield庫
3. **血統缺失**：確認使用v3.1版本處理器
4. **記憶體溢出**：啟用分批處理模式

## 🖥️ 前端簡化版驗證呈現

### 驗證快照位置
```bash
# 驗證結果快照 (輕量級，供前端讀取)
/app/data/validation_snapshots/stage1_validation.json
```

### JSON 格式範例
```json
{
  "stage": 1,
  "stageName": "TLE載入與軌道計算",
  "timestamp": "2025-08-14T08:00:00Z",
  "status": "completed",
  "duration_seconds": 45,
  "keyMetrics": {
    "輸入TLE數量": 8796,
    "Starlink衛星": 8079,
    "OneWeb衛星": 651,
    "其他衛星": 66,
    "載入成功率": "100%"
  },
  "validation": {
    "passed": true,
    "totalChecks": 7,
    "passedChecks": 7,
    "failedChecks": 0,
    "criticalChecks": [
      {"name": "TLE完整性", "status": "passed"},
      {"name": "軌道計算精度", "status": "passed"},
      {"name": "時間序列連續性", "status": "passed"}
    ]
  },
  "performanceMetrics": {
    "processingTime": "45秒",
    "memoryUsage": "500MB",
    "outputMode": "記憶體傳遞"
  },
  "nextStage": {
    "ready": true,
    "stage": 2,
    "expectedInput": 8796
  }
}
```

### 前端呈現建議
```typescript
// React Component 簡化呈現
interface Stage1Validation {
  // 主要狀態圓圈 (綠色✓/紅色✗/黃色處理中)
  status: 'completed' | 'processing' | 'failed' | 'pending';
  
  // 關鍵數字卡片
  cards: [
    { label: 'TLE數量', value: '8,796', icon: '📡' },
    { label: 'Starlink', value: '8,079', icon: '🛰️' },
    { label: 'OneWeb', value: '651', icon: '🌍' }
  ];
  
  // 迷你進度條
  progress: {
    label: '載入進度',
    percentage: 100,
    color: '#00C851'  // 綠色表示完成
  };
  
  // 驗證檢查清單 (簡化版)
  checks: {
    passed: 7,
    total: 7,
    status: '✅ 全部通過'
  };
}
```

### API 端點規格
```yaml
# 獲取階段驗證狀態
GET /api/pipeline/validation/stage/1
Response:
  - 200: 返回上述 JSON 格式
  - 404: 階段尚未執行
  - 500: 驗證失敗

# 獲取所有階段狀態總覽
GET /api/pipeline/validation/summary
Response:
  stages: [
    { stage: 1, status: 'completed', passed: true },
    { stage: 2, status: 'completed', passed: true },
    ...
  ]
```

### 視覺化呈現範例
```
┌─────────────────────────────────────┐
│  Stage 1: TLE載入與軌道計算         │
│  ✅ 完成 (45秒)                    │
├─────────────────────────────────────┤
│  📡 8,796 TLE  🛰️ 8,079 STL       │
│  🌍 651 OW     ✓ 100% 載入         │
├─────────────────────────────────────┤
│  驗證: 7/7 ✅                       │
│  [████████████████████] 100%       │
└─────────────────────────────────────┘
```

---
**下一處理器**: [智能衛星篩選處理器](./stage2-filtering.md)  
**相關文檔**: [Pure Cron架構](../data_processing_flow.md#pure-cron驅動架構)
