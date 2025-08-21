# 🎯 階段二：智能衛星篩選

[🔄 返回數據流程導航](../README.md) > 階段二

## 📖 階段概述

**目標**：從 8,730 顆衛星智能篩選至高品質候選衛星  
**輸入**：TLE軌道計算處理器記憶體傳遞的軌道計算結果  
**輸出**：記憶體傳遞給信號品質分析處理器（或保存檔案到 `/app/data/leo_outputs/`）  
**實際結果**：1,184 顆衛星 (1,039 Starlink + 145 OneWeb)
**篩選率**：86.4% 大幅減少後續計算負荷  
**處理時間**：約 1-2 分鐘

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

---
**上一階段**: [階段一：TLE載入](./stage1-tle-loading.md)  
**下一階段**: [階段三：信號分析](./stage3-signal.md)  
**相關文檔**: [智能篩選演算法詳解](../algorithms_implementation.md#智能篩選)
