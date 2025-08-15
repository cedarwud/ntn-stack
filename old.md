# 📊 NTN Stack 數據預處理6階段架構總覽

> **基於 @docs/README.md 與文檔分析的完整架構表**

## 🔄 Pure Cron 驅動六階段處理流程

### 📋 處理階段概述
```
階段一 → 階段二 → 階段三 → 階段四 → 階段五 → 階段六
TLE載入   智能篩選   信號分析   時間序列   數據整合   動態池規劃
2-3分鐘  1-2分鐘   3-5分鐘   1-2分鐘   2-3分鐘   3-5分鐘
```


---

## 📁 階段一：TLE載入與SGP4軌道計算

### 🎯 處理目標
- **輸入**: TLE檔案（約2.2MB，8,735顆衛星）
- **輸出**: 記憶體傳遞給階段二（避免2.2GB檔案）
- **處理時間**: 約2-3分鐘

### 📂 核心程式檔案
```
/netstack/src/stages/stage1_tle_processor.py
├── Stage1TLEProcessor.scan_tle_data()
├── Stage1TLEProcessor.load_raw_satellite_data()
├── Stage1TLEProcessor.calculate_all_orbits()
└── Stage1TLEProcessor.process_stage1()

/netstack/src/services/satellite/coordinate_specific_orbit_engine.py
└── SGP4軌道計算引擎
```

### 📊 TLE數據檔案
```
/netstack/tle_data/starlink/tle/starlink_20250805.tle
/netstack/tle_data/starlink/json/starlink_*.json
├── starlink_20250810.json
├── starlink_20250806.json
├── starlink_20250805.json
└── [其他日期檔案]
```

---

## 📁 階段二：智能衛星篩選

### 🎯 處理目標
- **輸入**: 階段一記憶體傳遞的軌道計算結果
- **輸出**: 記憶體傳遞給階段三（避免2.4GB檔案）
- **篩選率**: 93.6%（8,735 → 563顆高品質衛星）
- **處理時間**: 約1-2分鐘

### 📂 核心程式檔案
```
/netstack/src/stages/stage2_filter_processor.py
└── Stage2FilterProcessor（智能篩選邏輯）

/netstack/src/services/satellite/preprocessing/satellite_selector.py
├── SatelliteSelector.apply_intelligent_filtering()
├── SatelliteSelector._geographical_filtering()
├── SatelliteSelector._visibility_time_filtering()
├── SatelliteSelector._elevation_quality_filtering()
└── SatelliteSelector._load_balancing_optimization()

/netstack/config/satellite_data_pool_builder.py
└── 基礎衛星池建構
```

### 🎯 篩選結果分佈
- **Starlink**: ~450顆（80%）
- **OneWeb**: ~113顆（20%）

---

## 📁 階段三：信號品質分析與3GPP事件處理

### 🎯 處理目標
- **輸入**: 階段二記憶體傳遞的篩選結果
- **輸出**: 信號品質數據 + 3GPP事件數據（~295MB）
- **處理對象**: 563顆高品質衛星
- **處理時間**: 約3-5分鐘

### 📂 核心程式檔案
```
/netstack/src/stages/stage3_signal_processor.py
├── Stage3SignalProcessor.analyze_signal_quality()
├── Stage3SignalProcessor.generate_3gpp_events()
├── Stage3SignalProcessor.calculate_rsrp_timeseries()
└── Stage3SignalProcessor.process_stage3()

/netstack/src/services/signal/gpp3_event_generator.py
├── GPP3EventGenerator.generate_a4_events()
├── GPP3EventGenerator.generate_a5_events()
└── GPP3EventGenerator.generate_d2_events()
```

### 📊 輸出數據檔案
```
/app/data/signal_quality_analysis/
├── signal_heatmap_data.json
├── quality_metrics_summary.json
└── constellation_comparison.json

/app/data/handover_scenarios/
├── a4_events_enhanced.json
├── a5_events_enhanced.json
├── d2_events_enhanced.json
└── best_handover_windows.json
```

---

## 📁 階段四：時間序列預處理

### 🎯 處理目標
- **輸入**: 階段三的信號品質數據（~295MB）
- **輸出**: 前端時間序列數據（~85-100MB）
- **最佳化**: 數據減量65%（720點→360點）
- **處理時間**: 約1-2分鐘

### 📂 核心程式檔案
```
/netstack/src/stages/stage4_timeseries_processor.py
├── Stage4TimeseriesProcessor.optimize_for_frontend()
├── Stage4TimeseriesProcessor.generate_animation_data()
├── Stage4TimeseriesProcessor.compress_timeseries()
└── Stage4TimeseriesProcessor.process_stage4()

/netstack/src/services/animation/cron_animation_builder.py
├── CronAnimationBuilder.build_satellite_tracks()
├── CronAnimationBuilder.build_signal_timelines()
└── CronAnimationBuilder.build_handover_sequences()
```

### 📊 輸出數據檔案
```
/app/data/enhanced_timeseries/
├── animation_enhanced_starlink.json (~60MB)
└── animation_enhanced_oneweb.json (~25-40MB)
```

---

## 📁 階段五：數據整合與混合存儲

### 🎯 處理目標
- **輸入**: 階段四的前端時間序列數據（~85-100MB）
- **輸出**: PostgreSQL結構化數據 + Docker Volume檔案存儲
- **存儲總量**: ~486MB（PostgreSQL ~86MB + Volume ~400MB）
- **處理時間**: 約2-3分鐘

### 📂 核心程式檔案
```
/netstack/src/stages/stage5_integration_processor.py
├── Stage5IntegrationProcessor.setup_postgresql_schema()
├── Stage5IntegrationProcessor.populate_metadata_tables()
├── Stage5IntegrationProcessor.generate_volume_files()
├── Stage5IntegrationProcessor.verify_mixed_storage()
└── Stage5IntegrationProcessor.process_stage5()

/netstack/src/services/database/postgresql_manager.py
├── PostgreSQLManager.setup_connection_pool()
├── PostgreSQLManager.execute_batch_insert()
└── PostgreSQLManager.create_indexes()
```

### 📊 PostgreSQL 資料表
```sql
satellite_metadata                 -- 衛星基本資訊
signal_quality_statistics          -- 信號統計指標
handover_events_summary            -- 3GPP事件摘要
```

### 📊 Docker Volume 檔案結構
```
/app/data/
├── enhanced_timeseries/          (~85-100MB)
├── layered_phase0_enhanced/      (~120MB)
├── handover_scenarios/           (~80MB)
├── signal_quality_analysis/      (~90MB)
├── processing_cache/             (~50MB)
└── status_files/                 (~1MB)
```

---

## 📁 階段六：動態衛星池規劃 🆕

### 🎯 處理目標
- **輸入**: 階段五的混合存儲數據
- **輸出**: 動態衛星池規劃結果
- **目標**: 立體圖時空分散的動態覆蓋
- **處理時間**: 約3-5分鐘

### 📂 核心程式檔案（✅ 已實現）
```
/netstack/src/stages/stage6_dynamic_pool_planner.py
├── Stage6DynamicPoolPlanner.plan_dynamic_pools()
├── Stage6DynamicPoolPlanner.analyze_visibility_windows()
├── Stage6DynamicPoolPlanner.plan_time_distributed_pool()
├── Stage6DynamicPoolPlanner.verify_dynamic_coverage()
├── Stage6DynamicPoolPlanner._score_satellites_for_distribution()
├── Stage6DynamicPoolPlanner._calculate_temporal_dispersion()
├── Stage6DynamicPoolPlanner._simulate_coverage_timeline()
└── Stage6DynamicPoolPlanner._save_pool_results()

/netstack/src/services/satellite/preprocessing/phase_distribution.py
├── PhaseDistributionOptimizer.optimize_phase_distribution()
├── PhaseDistributionOptimizer._calculate_phase_info()
├── PhaseDistributionOptimizer._greedy_phase_selection()
├── PhaseDistributionOptimizer._calculate_interval_score()
└── PhaseDistributionOptimizer.evaluate_phase_quality()
```

### 🎯 動態池估算（待驗證）
- **Starlink**: ~45顆（目標10-15顆同時可見）
- **OneWeb**: ~20顆（目標3-6顆同時可見）

### 📊 輸出數據檔案（✅ 已實現）
```
/app/data/dynamic_satellite_pools/
└── pools.json  # 動態池規劃結果（含Starlink/OneWeb分別規劃）

# 動態池結果格式：
{
  "metadata": { "generation_time", "observer_location", "algorithm_version" },
  "starlink": { 
    "actual_pool_size", "coverage_statistics", "selected_satellites[]"
  },
  "oneweb": { 
    "actual_pool_size", "coverage_statistics", "selected_satellites[]"
  }
}
```

---

## 📋 已存在的關鍵JSON檔案

### 🛰️ 增強型數據檔案
```
✅ /simworld/backend/data/starlink_120min_d2_enhanced.json
✅ /simworld/backend/data/oneweb_120min_d2_enhanced.json
✅ /netstack/data/enhanced_data_summary.json
✅ /netstack/data/enhanced_satellite_data.json
✅ /netstack/data/enhanced_build_config.json
```

### 📊 時間序列數據檔案
```
✅ /simworld/backend/data/starlink_120min_timeseries.json
✅ /simworld/backend/data/oneweb_120min_timeseries.json
```

---

## 🔧 Pure Cron 驅動機制

### ⏰ Cron任務配置
```bash
# 每6小時自動更新（2:00, 8:00, 14:00, 20:00）
0 2,8,14,20 * * * root /scripts/incremental_data_processor.sh
```

### 🚀 啟動順序
1. **TLE檢查與下載**（如需要）
2. **階段一：SGP4軌道計算**
3. **階段二：智能篩選**（記憶體傳遞）
4. **階段三：信號分析**（記憶體傳遞）
5. **階段四：時間序列最佳化**
6. **階段五：混合存儲整合**
7. **階段六：動態池規劃**（新增）

---

## 📈 性能指標總覽

| 階段 | 輸入大小 | 輸出大小 | 處理時間 | 主要優化 |
|------|----------|----------|----------|----------|
| 一   | 2.2MB    | 記憶體   | 2-3分鐘  | 記憶體傳遞 |
| 二   | 記憶體   | 記憶體   | 1-2分鐘  | 智能篩選93.6% |
| 三   | 記憶體   | 295MB    | 3-5分鐘  | 3GPP事件處理 |
| 四   | 295MB    | 85-100MB | 1-2分鐘  | 數據減量65% |
| 五   | 85-100MB | 486MB    | 2-3分鐘  | 混合存儲 |
| 六   | 486MB    | TBD      | 3-5分鐘  | 動態池規劃 |

### 🎯 總處理時間：約12-20分鐘
### 💾 總存儲需求：~486MB + PostgreSQL

---

**📋 狀態說明**：
- ✅ **階段一至六**：已完全實現並運行
- ✅ **動態池規劃**：包含時空分散演算法、相位分散優化
- ⚠️ **動態池數字**：45顆/20顆為估算值，需實際驗證

---
*最後更新：2025-08-15 | 基於 @docs v2.2.0*
