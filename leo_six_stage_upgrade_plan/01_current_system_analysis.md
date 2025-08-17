# 🔍 Phase 1A: 當前四階段系統分析

**風險等級**: 🟢 低風險  
**預估時間**: 30分鐘  
**必要性**: ✅ 必要 - 了解現狀才能制定精確的恢復計劃

## 🎯 目標

全面分析當前的四階段系統 (F1→F2→F3→A1)，識別與原始六階段系統的差異，為恢復計劃提供準確的技術基礎。

## 📋 分析清單

### 1. 當前四階段系統結構掃描
基於已觀察到的結構：`/netstack/src/leo_core/core_system/`

```
leo_core/core_system/
├── tle_data_loader/           # F1: TLE數據載入
│   ├── tle_loader_engine.py
│   ├── orbital_calculator.py
│   ├── data_validator.py
│   └── fallback_test_data.py
├── satellite_filter_engine/   # F2: 衛星篩選
│   ├── satellite_filter_engine.py
│   ├── satellite_filter_engine_v2.py
│   └── README.md
├── signal_analyzer/           # F3: 信號分析
│   ├── threegpp_event_processor.py
│   └── README.md
├── dynamic_pool_planner/      # A1: 動態池規劃
│   ├── simulated_annealing_optimizer.py
│   └── README.md
└── main_pipeline.py          # 主控制器
```

### 2. 原始六階段系統對比
基於 docs 文檔的六階段設計：

```
原始六階段 vs 當前四階段:
─────────────────────────────────────────────
階段一: TLE載入        → F1: tle_data_loader/      ✅ 對應  
階段二: 智能篩選       → F2: satellite_filter/     ⚠️ 簡化
階段三: 信號分析       → F3: signal_analyzer/      ⚠️ 簡化  
階段四: 時間序列       → 🚫 缺失                    ❌ 無對應
階段五: 數據整合       → 🚫 缺失                    ❌ 無對應
階段六: 動態池規劃     → A1: dynamic_pool_planner/ ✅ 對應(升級)
```

## 🔍 詳細分析

### F1 分析：TLE數據載入器
**路徑**: `/netstack/src/leo_core/core_system/tle_data_loader/`

**關鍵檔案**:
- `tle_loader_engine.py` - 主載入引擎
- `orbital_calculator.py` - SGP4軌道計算
- `data_validator.py` - 數據驗證
- `fallback_test_data.py` - 備援數據

**與階段一的差異**:
- ✅ SGP4算法完整實現
- ✅ TLE數據驗證機制
- ⚠️ 可能缺失記憶體傳遞優化
- ⚠️ 可能缺失Pure Cron調度機制

### F2 分析：衛星篩選引擎
**路徑**: `/netstack/src/leo_core/core_system/satellite_filter_engine/`

**關鍵檔案**:
- `satellite_filter_engine.py` - 基礎篩選
- `satellite_filter_engine_v2.py` - v2版本篩選

**與階段二的差異**:
- ❌ **關鍵問題**: 使用 `satellite_filter_engine_v2.py` 而非 `unified_intelligent_filter.py`
- ❌ 缺失六階段篩選管線 (2.1-2.6)
- ❌ 93.6%篩選率可能降低
- ❌ 地理相關性評分可能簡化

### F3 分析：信號分析器
**路徑**: `/netstack/src/leo_core/core_system/signal_analyzer/`

**關鍵檔案**:
- `threegpp_event_processor.py` - 3GPP事件處理

**與階段三的差異**:
- ⚠️ 可能缺失完整的RSRP計算
- ⚠️ 可能缺失多仰角信號分析
- ⚠️ 可能缺失綜合評分機制

### A1 分析：動態池規劃器 (新增)
**路徑**: `/netstack/src/leo_core/core_system/dynamic_pool_planner/`

**關鍵檔案**:
- `simulated_annealing_optimizer.py` - 模擬退火優化

**特點**:
- ✅ 新技術：模擬退火演算法
- ✅ 動態池規劃能力
- ✅ 可替換原始階段六

## 📂 檔案引用關係分析

### 主控制器分析
**檔案**: `/netstack/src/leo_core/core_system/main_pipeline.py`

**預期引用**:
```python
from tle_data_loader.tle_loader_engine import TLELoaderEngine
from satellite_filter_engine.satellite_filter_engine_v2 import SatelliteFilterEngineV2  # ❌ 問題
from signal_analyzer.threegpp_event_processor import ThreeGPPEventProcessor
from dynamic_pool_planner.simulated_annealing_optimizer import SimulatedAnnealingOptimizer
```

### 前端數據流分析
**已知問題**: 前端可能讀取F2中間結果而非A1最終結果

**檢查檔案**:
- `/simworld/frontend/src/services/realSatelliteService.ts`
- `/simworld/frontend/src/config/apiRoutes.ts`
- `/netstack/netstack_api/routers/leo_frontend_data_router.py`

### 後端API路由分析
**檢查檔案**:
- `/simworld/backend/app/api/routes/satellite_redis.py`
- `/netstack/netstack_api/routers/orbit_calculation_router.py`

## 🚨 發現的關鍵問題

### 1. 篩選引擎錯誤
- **問題**: 使用 `satellite_filter_engine_v2.py` 而非 `unified_intelligent_filter.py`
- **影響**: 篩選效率從93.6%大幅降低
- **位置**: `/netstack/src/leo_core/core_system/satellite_filter_engine/`

### 2. 缺失階段四和五
- **問題**: 時間序列預處理和數據整合完全缺失
- **影響**: 前端動畫數據可能不完整
- **影響**: PostgreSQL+Volume混合存儲缺失

### 3. 檔案命名問題
- **問題**: 使用 `F1/F2/F3/A1` 和 `phase1_core_system` 命名
- **違反**: CLAUDE.md 檔案命名規範

### 4. 潛在的硬編碼路徑
- **問題**: 可能存在Linux專用路徑
- **風險**: Windows/macOS兼容性問題

## 📊 四階段vs六階段功能對比

| 功能模組 | 四階段 | 六階段 | 差異分析 |
|----------|--------|--------|----------|
| **TLE載入** | F1 ✅ | 階段一 ✅ | 基本對應，需檢查優化 |
| **智能篩選** | F2 ❌ | 階段二 ✅ | 使用錯誤引擎 |
| **信號分析** | F3 ⚠️ | 階段三 ✅ | 功能可能不完整 |
| **時間序列** | 🚫 | 階段四 ✅ | 完全缺失 |
| **數據整合** | 🚫 | 階段五 ✅ | 完全缺失 |
| **動態池規劃** | A1 ✅ | 階段六 ⚠️ | 新技術，可升級原階段六 |

## 📋 備份目錄分析

### 已發現的備份
```
/netstack/src/leo_core.backup.20250816_014835/  # 第一次備份
/netstack/src/leo_core.backup.20250816_014956/  # 第二次備份
```

這表明：
- ✅ 已有自動備份機制
- ⚠️ 需要驗證備份內容的完整性
- ⚠️ 需要確認哪個是最原始的六階段系統

## 🔧 實際檔案掃描指令

### 掃描四階段檔案結構
```bash
echo "=== 四階段系統檔案掃描 ===" > analysis_report.txt
find /home/sat/ntn-stack/netstack/src/leo_core -name "*.py" -type f >> analysis_report.txt
echo "" >> analysis_report.txt

echo "=== 檔案命名問題掃描 ===" >> analysis_report.txt
find /home/sat/ntn-stack -name "*stage*" -o -name "*phase*" -o -name "*F1*" -o -name "*F2*" -o -name "*F3*" -o -name "*A1*" >> analysis_report.txt
echo "" >> analysis_report.txt
```

### 檢查引用關係
```bash
echo "=== 引用關係分析 ===" >> analysis_report.txt
grep -r "satellite_filter_engine_v2" /home/sat/ntn-stack/netstack/src/ >> analysis_report.txt
grep -r "unified_intelligent_filter" /home/sat/ntn-stack/netstack/src/ >> analysis_report.txt
echo "" >> analysis_report.txt
```

### 檢查hardcoded路徑
```bash
echo "=== 硬編碼路徑檢查 ===" >> analysis_report.txt
grep -r "/home/sat" /home/sat/ntn-stack/netstack/src/leo_core/ >> analysis_report.txt
grep -r "\\\\\\\\|C:\\\\" /home/sat/ntn-stack/netstack/src/leo_core/ >> analysis_report.txt
echo "" >> analysis_report.txt
```

## ✅ 分析結果記錄表

完成分析後填寫：

### 系統結構
- [ ] 四階段檔案結構已掃描
- [ ] 六階段對比表已完成
- [ ] 引用關係已分析

### 問題識別
- [ ] 篩選引擎問題已確認
- [ ] 缺失階段已識別
- [ ] 檔案命名問題已列出
- [ ] 硬編碼路徑已檢查

### 備份狀況
- [ ] 現有備份已評估
- [ ] 最原始版本已確認

## 🔗 輸出與下一步

### 分析報告輸出
生成檔案：`analysis_report.txt` 包含：
1. 完整檔案結構掃描
2. 問題識別清單
3. 引用關係分析
4. 硬編碼路徑檢查結果

### 下一步行動
分析完成後，繼續執行：
→ `02_file_inventory_and_naming.md`

---
**📝 分析總結**: 四階段系統有基礎功能但存在關鍵問題，需要完整恢復六階段並整合優秀的模擬退火技術。
