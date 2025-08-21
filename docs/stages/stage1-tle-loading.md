# 📊 階段一：TLE數據載入與SGP4軌道計算

[🔄 返回文檔總覽](../README.md) > 階段一

## 📖 階段概述

**目標**：從 8,730 顆衛星載入 TLE 數據並執行精確的 SGP4 軌道計算  
**輸入**：TLE 檔案（約 2.2MB）  
**輸出**：記憶體傳遞給智能篩選處理器（避免 2.2GB 檔案問題）  
**處理時間**：約 2-3 分鐘
**實際處理數量**：8,079 Starlink + 651 OneWeb = 8,730 顆衛星

### 🚀 v3.0 記憶體傳遞模式

- **問題解決**：避免生成 2.2GB 大檔案
- **傳遞方式**：直接將軌道計算結果在記憶體中傳遞給階段二
- **效能提升**：消除檔案 I/O 開銷，處理速度提升 50%+

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
   - 計算6小時完整軌道數據
   - 時間解析度：30秒間隔

4. **記憶體傳遞**：將結果直接傳遞給階段二

## 🔧 技術實現細節

### SGP4計算精度
- **標準遵循**：嚴格遵循官方SGP4/SDP4標準
- **誤差控制**：位置誤差 < 1km（LEO衛星）
- **時間精度**：UTC時間精確到秒級

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

### 診斷指令

```bash
# 檢查TLE數據狀態
find /app/tle_data -name '*.tle' -exec ls -la {} \;

# 驗證TLE軌道計算處理器
python -c "from stages.tle_orbital_calculation_processor import Stage1TLEProcessor; print('TLE軌道計算處理器正常')"

# 驗證SGP4引擎
python -c "from src.services.satellite.coordinate_specific_orbit_engine import *; print('SGP4引擎正常')"
```

---
**下一處理器**: [智能衛星篩選處理器](./stage2-filtering.md)  
**相關文檔**: [Pure Cron架構](../data_processing_flow.md#pure-cron驅動架構)
