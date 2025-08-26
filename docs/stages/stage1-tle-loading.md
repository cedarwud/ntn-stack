# 📊 階段一：TLE數據載入與SGP4軌道計算

[🔄 返回文檔總覽](../README.md) > 階段一

## 📖 階段概述

**目標**：從 8,730 顆衛星載入 TLE 數據並執行精確的 SGP4 軌道計算  
**輸入**：TLE 檔案（約 2.2MB）  
**輸出**：記憶體傳遞給智能篩選處理器（避免 2.2GB 檔案問題）  
**處理時間**：約 2-3 分鐘
**實際處理數量**：8,079 Starlink + 651 OneWeb = 8,730 顆衛星

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

---
**下一處理器**: [智能衛星篩選處理器](./stage2-filtering.md)  
**相關文檔**: [Pure Cron架構](../data_processing_flow.md#pure-cron驅動架構)
