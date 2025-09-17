# 📁 階段五：數據整合與混合存儲

[🔄 返回數據流程導航](../README.md) > 階段五

## 📖 階段概述

**目標**：將所有處理結果整合並建立混合存儲架構  
**輸入**：階段三的信號分析數據（含仰角）+ 階段四的動畫數據（智能融合）  
**輸出**：PostgreSQL結構化數據 + Docker Volume檔案存儲 + 分層仰角數據  
**存儲總量**：~575MB (PostgreSQL ~2MB + Volume ~573MB)  
**處理時間**：約 1-2 分鐘  
**架構重點**：專注於純數據整合功能 (Phase 2組件已移至Stage 6)

### 🎯 @doc/todo.md 對應實現
本階段支援以下需求：
- 🔧 **分層數據準備**: 生成5°/10°/15°仰角分層數據，支援不同仰角門檻需求
- 💾 **混合存儲**: PostgreSQL快速查詢 + Volume大容量存儲，支援強化學習數據存取
- 🔗 **API接口準備**: 為動態池規劃和換手決策提供高效數據訪問接口

### 🆕 **實作新增功能** (2025-09-16 發現)

**智能數據融合引擎** (`intelligent_data_fusion_engine.py`):
- **多源數據整合**: 智能融合Stage3-4的多維度數據
- **數據一致性保證**: 確保跨階段數據的時間戳和格式一致性
- **衝突解決機制**: 自動處理數據衝突和異常值

**換手場景引擎** (`handover_scenario_engine.py`):
- **3GPP場景生成**: 自動生成A4/A5/D2換手場景數據
- **場景多樣化**: 創建豐富的換手訓練場景供RL使用
- **場景驗證**: 確保生成場景符合3GPP標準要求

**分層數據生成器** (`layered_data_generator.py`):
- **多層仰角數據**: 自動生成5°/10°/15°分層數據結構
- **動態門檻調整**: 支援環境因子的門檻動態調整
- **性能優化**: 減少重複計算，提升數據生成效率

**處理緩存管理器** (`processing_cache_manager.py`):
- **智能緩存策略**: 基於使用頻率的智能數據緩存
- **內存優化**: 防止大數據集造成的內存溢出
- **緩存一致性**: 確保緩存數據與源數據同步

**跨階段驗證器** (`cross_stage_validator.py`):
- **數據完整性驗證**: 確保Stage3-4數據完整傳遞到Stage5
- **格式一致性檢查**: 驗證跨階段數據格式標準化
- **學術標準合規**: 整合學術標準驗證機制

## 🏗️ 混合存儲架構

### 存儲策略分工
- **PostgreSQL**：結構化數據、索引查詢、統計分析
- **Docker Volume**：大型檔案、時間序列數據、前端資源

### 數據分類原則
```python
STORAGE_STRATEGY = {
    'postgresql': [
        'satellite_metadata',      # 衛星基本資訊
        'signal_statistics',       # 信號統計指標
        'event_summaries',         # 3GPP事件摘要
        'performance_metrics'      # 系統性能指標
    ],
    'volume_files': [
        'timeseries_data',         # 完整時間序列
        'animation_resources',     # 前端動畫數據
        'signal_heatmaps',        # 信號熱力圖
        'orbit_trajectories'       # 軌道軌跡數據
    ]
}
```

## 🚨 強制運行時檢查 (新增)

**2025-09-09 重大強化**: 新增階段五專門的運行時架構完整性檢查維度。

### 🔴 零容忍運行時檢查 (任何失敗都會停止執行)

#### 1. 數據整合處理器類型強制檢查
```python
# 🚨 嚴格檢查實際使用的數據整合處理器類型
assert isinstance(processor, DataIntegrationProcessor), f"錯誤數據整合處理器: {type(processor)}"
assert isinstance(storage_manager, HybridStorageManager), f"錯誤存儲管理器: {type(storage_manager)}"
# 原因: 確保使用完整的數據整合處理器，而非簡化版本
# 影響: 錯誤處理器可能導致數據整合不完整或存儲策略錯誤
```

#### 2. 多階段輸入數據完整性檢查  
```python
# 🚨 強制檢查來自階段三和階段四的輸入數據完整性
assert 'signal_analysis_results' in stage3_input, "缺少階段三信號分析結果"
assert 'timeseries_data' in stage4_input, "缺少階段四時間序列數據"

# 檢查階段三數據
stage3_satellites = stage3_input['signal_analysis_results']
assert len(stage3_satellites['starlink']) > 1000, f"Starlink信號數據不足: {len(stage3_satellites['starlink'])}"
assert len(stage3_satellites['oneweb']) > 100, f"OneWeb信號數據不足: {len(stage3_satellites['oneweb'])}"

# 檢查階段四數據
stage4_data = stage4_input['timeseries_data']
assert 'animation_enhanced_starlink' in stage4_data, "缺少Starlink動畫數據"
assert 'animation_enhanced_oneweb' in stage4_data, "缺少OneWeb動畫數據"
# 原因: 確保跨階段數據整合的輸入完整性
# 影響: 不完整的輸入會導致數據整合錯誤或功能缺失
```

#### 3. 混合存儲架構完整性檢查
```python
# 🚨 強制檢查混合存儲架構正確實施
storage_config = storage_manager.get_storage_configuration()
assert 'postgresql' in storage_config, "缺少PostgreSQL存儲配置"
assert 'volume_files' in storage_config, "缺少Volume文件存儲配置"

# 檢查PostgreSQL連接和表結構
db_connection = storage_manager.get_database_connection()
assert db_connection.is_connected(), "PostgreSQL連接失敗"
required_tables = ['satellite_metadata', 'signal_quality_statistics', 'handover_events_summary']
existing_tables = db_connection.get_table_list()
for table in required_tables:
    assert table in existing_tables, f"缺少必需的數據表: {table}"

# 檢查Volume存儲路徑
volume_path = storage_manager.get_volume_path()
assert os.path.exists(volume_path), f"Volume存儲路徑不存在: {volume_path}"
assert os.access(volume_path, os.W_OK), f"Volume路徑無寫入權限: {volume_path}"
# 原因: 確保混合存儲架構正確配置和可用
# 影響: 存儲架構問題會導致數據無法正確保存或讀取
```

#### 4. 分層仰角數據完整性檢查
```python
# 🚨 強制檢查分層仰角數據生成完整性
layered_data = processor.get_layered_elevation_data()
required_layers = ['5deg', '10deg', '15deg']
for constellation in ['starlink', 'oneweb']:
    for layer in required_layers:
        layer_key = f"{constellation}_{layer}_enhanced"
        assert layer_key in layered_data, f"缺少分層數據: {layer_key}"
        layer_satellites = layered_data[layer_key]
        assert len(layer_satellites) > 0, f"{layer_key}分層數據為空"
        
        # 檢查仰角門檻正確性
        expected_threshold = int(layer.replace('deg', ''))
        for satellite in layer_satellites[:3]:
            max_elevation = satellite.get('max_elevation_deg', 0)
            assert max_elevation >= expected_threshold, \
                f"{layer_key}衛星最大仰角{max_elevation}°低於門檻{expected_threshold}°"
# 原因: 確保分層仰角數據正確生成和符合門檻要求
# 影響: 錯誤的分層數據會影響換手決策和覆蓋分析
```

#### 5. 數據一致性跨階段檢查
```python
# 🚨 強制檢查跨階段數據一致性
stage3_satellite_ids = set(sat['satellite_id'] for constellation in stage3_input['signal_analysis_results'].values() 
                          for sat in constellation)
stage4_satellite_ids = set(stage4_input['timeseries_data']['satellite_ids'])
stage5_satellite_ids = set(processor.get_integrated_satellite_ids())

# 檢查衛星ID一致性
common_satellites = stage3_satellite_ids.intersection(stage4_satellite_ids)
assert len(common_satellites) > 1000, f"跨階段共同衛星數量不足: {len(common_satellites)}"
assert stage5_satellite_ids.issubset(common_satellites), "階段五包含了未在前階段出現的衛星"

# 檢查數據時間戳一致性
stage3_timestamp = stage3_input['metadata']['processing_timestamp']
stage4_timestamp = stage4_input['metadata']['processing_timestamp']
timestamp_diff = abs((stage3_timestamp - stage4_timestamp).total_seconds())
assert timestamp_diff < 3600, f"階段三四時間戳差異過大: {timestamp_diff}秒"
# 原因: 確保跨階段數據的一致性和同步性
# 影響: 數據不一致會導致整合結果錯誤或決策偏差
```

#### 6. 無簡化整合零容忍檢查
```python
# 🚨 禁止任何形式的簡化數據整合
forbidden_integration_modes = [
    "partial_integration", "simplified_storage", "mock_database",
    "estimated_statistics", "arbitrary_aggregation", "lossy_compression"
]
for mode in forbidden_integration_modes:
    assert mode not in str(processor.__class__).lower(), \
        f"檢測到禁用的簡化整合: {mode}"
    assert mode not in storage_manager.get_storage_methods(), \
        f"檢測到禁用的存儲方法: {mode}"
```

### 📋 Runtime Check Integration Points

**檢查時機**: 
- **初始化時**: 驗證數據整合處理器和存儲管理器類型
- **輸入處理時**: 檢查階段三四數據完整性和跨階段一致性
- **存儲配置時**: 驗證混合存儲架構正確配置和可用性
- **數據整合時**: 監控分層數據生成和數據一致性
- **輸出前**: 嚴格檢查整合結果完整性和存儲成功性

**失敗處理**:
- **立即停止**: 任何runtime check失敗都會立即終止執行
- **存儲檢查**: 驗證PostgreSQL和Volume存儲正確配置
- **一致性驗證**: 檢查跨階段數據時間戳和衛星ID一致性
- **無降級處理**: 絕不允許使用簡化整合或不完整存儲

### 🛡️ 實施要求

- **跨階段一致性強制執行**: 必須確保階段三四五數據完全一致
- **混合存儲架構完整性**: PostgreSQL和Volume存儲必須同時正確配置
- **分層數據準確性**: 所有仰角層數據必須符合相應門檻要求
- **數據完整性保證**: 整合過程中不得丟失任何關鍵數據
- **性能影響控制**: 運行時檢查額外時間開銷 <3%

## 📊 PostgreSQL 數據結構

### 核心資料表設計

#### 1. satellite_metadata
```sql
CREATE TABLE satellite_metadata (
    satellite_id VARCHAR(50) PRIMARY KEY,
    constellation VARCHAR(20) NOT NULL,
    norad_id INTEGER UNIQUE,
    tle_epoch TIMESTAMP WITH TIME ZONE,
    orbital_period_minutes NUMERIC(8,3),
    inclination_deg NUMERIC(6,3),
    mean_altitude_km NUMERIC(8,3),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 索引優化
CREATE INDEX idx_satellite_constellation ON satellite_metadata(constellation);
CREATE INDEX idx_satellite_norad ON satellite_metadata(norad_id);
```

#### 2. signal_quality_statistics
```sql
CREATE TABLE signal_quality_statistics (
    id SERIAL PRIMARY KEY,
    satellite_id VARCHAR(50) REFERENCES satellite_metadata(satellite_id),
    analysis_period_start TIMESTAMP WITH TIME ZONE,
    analysis_period_end TIMESTAMP WITH TIME ZONE,
    mean_rsrp_dbm NUMERIC(6,2),
    std_rsrp_db NUMERIC(5,2),
    max_elevation_deg NUMERIC(5,2),
    total_visible_time_minutes INTEGER,
    handover_event_count INTEGER,
    signal_quality_grade VARCHAR(10), -- 'high', 'medium', 'low'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 複合索引
CREATE INDEX idx_signal_satellite_period ON signal_quality_statistics(satellite_id, analysis_period_start);
CREATE INDEX idx_signal_quality_grade ON signal_quality_statistics(signal_quality_grade);
```

#### 3. handover_events_summary
```sql
CREATE TABLE handover_events_summary (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(10) NOT NULL, -- 'A4', 'A5', 'D2'
    serving_satellite_id VARCHAR(50) REFERENCES satellite_metadata(satellite_id),
    neighbor_satellite_id VARCHAR(50) REFERENCES satellite_metadata(satellite_id),
    event_timestamp TIMESTAMP WITH TIME ZONE,
    trigger_rsrp_dbm NUMERIC(6,2),
    handover_decision VARCHAR(20), -- 'trigger', 'hold', 'reject'
    processing_latency_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 事件查詢索引
CREATE INDEX idx_handover_event_type ON handover_events_summary(event_type);
CREATE INDEX idx_handover_timestamp ON handover_events_summary(event_timestamp);
CREATE INDEX idx_handover_serving ON handover_events_summary(serving_satellite_id);
```

## 📁 Docker Volume 檔案結構

### Volume 組織架構
```bash
/app/data/
├── timeseries_preprocessing_outputs/    # 階段四輸出：前端動畫數據 (~60-75MB)
│   ├── animation_enhanced_starlink.json
│   ├── animation_enhanced_oneweb.json
│   └── conversion_statistics.json
│
├── layered_phase0_enhanced/      # 分層處理結果 (~85MB)
│   ├── starlink_5deg_enhanced.json
│   ├── starlink_10deg_enhanced.json
│   ├── starlink_15deg_enhanced.json
│   ├── oneweb_10deg_enhanced.json
│   ├── oneweb_15deg_enhanced.json
│   └── oneweb_20deg_enhanced.json
│
├── handover_scenarios/           # 換手場景數據 (~55MB)
│   ├── a4_events_enhanced.json
│   ├── a5_events_enhanced.json
│   ├── d2_events_enhanced.json
│   └── best_handover_windows.json
│
├── signal_quality_analysis/      # 信號分析結果 (~65MB)
│   ├── signal_heatmap_data.json
│   ├── quality_metrics_summary.json
│   └── constellation_comparison.json
│
├── processing_cache/             # 處理緩存 (~35MB)
│   ├── sgp4_calculation_cache.json
│   ├── filtering_results_cache.json
│   └── gpp3_event_cache.json
│
└── status_files/                 # 狀態標記檔案 (~1MB)
    ├── last_processing_time.txt
    ├── tle_checksum.txt
    ├── processing_status.json
    └── health_check.json
```

## 🔗 智能數據融合策略

### 雙數據源整合設計
階段五採用創新的**智能數據融合**方法，同時利用階段三和階段四的優勢：

#### 數據來源分工
```python
DATA_FUSION_STRATEGY = {
    'stage3_data': {
        'source': '/app/data/signal_quality_analysis_output.json',
        'provides': [
            'position_timeseries',      # 完整軌道時序數據
            'elevation_deg',            # 真實仰角數據（位於relative_to_observer）
            'signal_quality',           # 詳細信號分析
            'visibility_analysis',      # 可見性判斷
            '3gpp_events'              # 3GPP標準事件
        ],
        'purpose': '提供科學計算所需的精確數據'
    },
    'stage4_data': {
        'source': '/app/data/timeseries_preprocessing_outputs/',
        'provides': [
            'track_points',            # 優化的軌跡動畫點
            'signal_timeline',         # 前端信號可視化
            'animation_metadata'       # 動畫性能數據
        ],
        'purpose': '提供前端動畫和可視化優化數據'
    }
}
```

#### 融合邏輯實現
```python
async def _load_enhanced_timeseries(self) -> Dict[str, Any]:
    """智能數據融合：結合階段三科學數據和階段四動畫數據"""
    
    # 1. 載入階段三數據（科學精確數據）
    stage3_data = self._load_stage3_signal_analysis()
    
    # 2. 載入階段四數據（動畫優化數據） 
    stage4_data = self._load_stage4_animation_data()
    
    # 3. 按衛星ID進行智能融合
    for constellation in ["starlink", "oneweb"]:
        for sat_id, stage3_sat in stage3_data[constellation]['satellites'].items():
            enhanced_satellite = {
                # 階段三提供：科學計算數據
                **stage3_sat,  # position_timeseries, signal_quality, etc.
                
                # 階段四提供：動畫優化數據（如果存在）
                'signal_timeline': stage4_data.get(sat_id, {}).get('signal_timeline', []),
                'track_points': stage4_data.get(sat_id, {}).get('track_points', []),
                'summary': stage4_data.get(sat_id, {}).get('summary', {})
            }
            
            enhanced_data[constellation]['satellites'][sat_id] = enhanced_satellite
    
    return enhanced_data
```

### 融合優勢
1. **科學精確性** - 使用階段三的真實仰角數據進行分層濾波
2. **動畫流暢性** - 保留階段四的前端優化數據
3. **功能完整性** - 同時滿足科學計算和可視化需求
4. **架構彈性** - 可獨立更新各數據源而不影響其他功能

## 🔧 整合處理器實現

### 主要實現位置
```bash
# 數據整合處理器
/netstack/src/stages/data_integration_processor.py
├── Stage5IntegrationProcessor.process_enhanced_timeseries()    # 增強時間序列處理
├── Stage5IntegrationProcessor._integrate_postgresql_data()     # PostgreSQL數據整合
├── Stage5IntegrationProcessor._generate_layered_data()         # 分層數據生成
├── Stage5IntegrationProcessor._generate_handover_scenarios()   # 換手場景生成
└── Stage5IntegrationProcessor._verify_mixed_storage_access()   # 混合存儲驗證

# 資料庫連接管理
/netstack/src/services/database/postgresql_manager.py
├── PostgreSQLManager.setup_connection_pool()              # 連接池管理
├── PostgreSQLManager.execute_batch_insert()               # 批次插入優化
└── PostgreSQLManager.create_indexes()                     # 索引建立
```

### 核心處理邏輯
```python
class Stage5IntegrationProcessor:
    
    async def process_enhanced_timeseries(self) -> Dict[str, Any]:
        """執行階段五完整整合處理 - 智能數據融合版"""
        
        results = {
            "stage": "stage5_integration",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "postgresql_integration": {},
            "layered_data_enhancement": {},
            "handover_scenarios": {},
            "signal_quality_analysis": {},
            "processing_cache": {},
            "status_files": {},
            "mixed_storage_verification": {}
        }
        
        try:
            # 1. 智能數據融合：同時載入階段三（仰角）和階段四（動畫）數據
            enhanced_data = await self._load_enhanced_timeseries()
            
            # 2. PostgreSQL 數據整合
            results["postgresql_integration"] = await self._integrate_postgresql_data(enhanced_data)
            
            # 3. 使用真實仰角生成分層數據
            results["layered_data_enhancement"] = await self._generate_layered_data(enhanced_data)
            
            # 4. 生成換手場景專用數據
            results["handover_scenarios"] = await self._generate_handover_scenarios(enhanced_data)
            
            # 5. 創建信號品質分析目錄結構
            results["signal_quality_analysis"] = await self._setup_signal_analysis_structure(enhanced_data)
            
            # 6. 創建處理緩存
            results["processing_cache"] = await self._create_processing_cache(enhanced_data)
            
            # 7. 生成狀態文件
            results["status_files"] = await self._create_status_files()
            
            # 8. 驗證混合存儲訪問模式
            results["mixed_storage_verification"] = await self._verify_mixed_storage_access()
            
            results["success"] = True
            
        except Exception as e:
            logger.error(f"❌ 階段五處理失敗: {e}")
            results["success"] = False
            results["error"] = str(e)
            
        return results
    
    async def _generate_layered_data(self, enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成分層數據增強 - 使用真實仰角數據"""
        
        self.logger.info("🔄 生成分層仰角數據（使用階段三真實仰角數據）")
        
        layered_results = {}
        
        for threshold in self.config.elevation_thresholds:
            threshold_dir = Path(self.config.output_layered_dir) / f"elevation_{threshold}deg"
            threshold_dir.mkdir(parents=True, exist_ok=True)
            
            layered_results[f"elevation_{threshold}deg"] = {}
            
            for constellation, data in enhanced_data.items():
                if not data or 'satellites' not in data:
                    continue
                
                satellites_data = data.get('satellites', {})
                filtered_satellites = {}
                total_satellites = len(satellites_data)
                
                for sat_id, satellite in satellites_data.items():
                    # 使用階段三的position_timeseries數據（包含真實仰角）
                    position_timeseries = satellite.get('position_timeseries', [])
                    
                    # 篩選符合仰角門檻的時序點
                    filtered_timeseries = []
                    for point in position_timeseries:
                        if isinstance(point, dict):
                            # 從relative_to_observer中獲取真實仰角數據
                            relative_data = point.get('relative_to_observer', {})
                            if isinstance(relative_data, dict):
                                elevation_deg = relative_data.get('elevation_deg')
                                is_visible = relative_data.get('is_visible', False)
                                
                                # 只保留可見且符合仰角門檻的點
                                if is_visible and elevation_deg is not None and elevation_deg >= threshold:
                                    filtered_timeseries.append(point)
                    
                    # 如果有符合條件的時序點，保留該衛星
                    if filtered_timeseries:
                        filtered_satellite = {
                            **satellite,  # 保留所有原有數據
                            'position_timeseries': filtered_timeseries,  # 更新為篩選後的時序數據
                            'satellite_id': sat_id,
                            'layered_stats': {
                                'elevation_threshold': threshold,
                                'filtered_points': len(filtered_timeseries),
                                'original_points': len(position_timeseries)
                            }
                        }
                        filtered_satellites[sat_id] = filtered_satellite
                
                # 生成分層數據檔案
                retention_rate = round(len(filtered_satellites) / max(total_satellites, 1) * 100, 1)
                layered_data = {
                    "metadata": {
                        **data.get('metadata', {}),
                        "elevation_threshold_deg": threshold,
                        "total_input_satellites": total_satellites,
                        "filtered_satellites_count": len(filtered_satellites),
                        "filter_retention_rate": retention_rate,
                        "stage5_processing_time": datetime.now(timezone.utc).isoformat(),
                        "constellation": constellation,
                        "filtering_method": "real_elevation_data_from_position_timeseries"
                    },
                    "satellites": filtered_satellites
                }
                
                output_file = threshold_dir / f"{constellation}_with_3gpp_events.json"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(layered_data, f, indent=2, ensure_ascii=False)
                
                file_size_mb = output_file.stat().st_size / (1024 * 1024)
                
                layered_results[f"elevation_{threshold}deg"][constellation] = {
                    "file_path": str(output_file),
                    "total_input_satellites": total_satellites,
                    "satellites_count": len(filtered_satellites),
                    "retention_rate_percent": retention_rate,
                    "file_size_mb": round(file_size_mb, 2),
                    "filtering_method": "real_elevation_from_position_timeseries"
                }
                
                self.logger.info(f"✅ {constellation} {threshold}° 門檻: {len(filtered_satellites)}/{total_satellites} 顆衛星 ({retention_rate}%), {file_size_mb:.1f}MB")
        
        return layered_results
```

## 🚨 **學術級數據整合標準遵循** (Grade A/B 等級)

### 🟢 **Grade A 強制要求：數據完整性優先**

#### 數據整合完整性原則
- **無損數據整合**：任何階段的原始數據都不得在整合過程中丟失
- **時間序列一致性**：保持所有數據源的時間戳同步和準確性
- **血統追蹤保持**：維持每個數據點的來源和處理歷史

#### 🟡 **Grade B 可接受：基於效能分析的配置**

#### 資料庫配置 (基於負載分析)
```python
# ✅ 正確：基於實際負載和硬體能力分析
POSTGRESQL_CONFIG = {
    'max_connections': calculate_optimal_connections(),  # 基於CPU核心數分析
    'connection_timeout': 30,                           # 基於網路延遲測試
    'query_timeout': calculate_query_timeout(),         # 基於查詢複雜度分析
    'batch_insert_size': optimize_batch_size(),         # 基於記憶體和IO測試
    'enable_connection_pooling': True                   # 標準最佳實踐
}

def calculate_optimal_connections():
    """基於硬體資源計算最佳連接數"""
    cpu_cores = os.cpu_count()
    available_memory_gb = psutil.virtual_memory().total / (1024**3)
    # PostgreSQL建議：2-4倍CPU核心數，受記憶體限制
    return min(cpu_cores * 3, int(available_memory_gb / 0.1))  # 每連接約100MB

# ❌ 錯誤：任意設定數值
ARBITRARY_CONFIG = {
    'max_connections': 20,      # 任意數字
    'batch_insert_size': 100,   # 未經測試的批次大小
}
```

#### 🔴 **Grade C 嚴格禁止項目** (零容忍)
- **❌ 任意批次大小設定**：如"100筆批次"等未經效能測試的數值
- **❌ 固定連接池配置**：不考慮硬體資源的固定連接數
- **❌ 數據完整性犧牲**：為效能而省略必要的數據驗證
- **❌ 時間戳不一致**：整合過程中改變原始時間戳
- **❌ 任意壓縮設定**：可能損失精度的壓縮參數

### 📊 **替代方案：基於科學原理的效能優化**

#### 學術級資料庫配置策略
```python
# ✅ 正確：基於資料庫理論和硬體分析
class AcademicDatabaseOptimizer:
    def __init__(self):
        self.system_resources = self.analyze_system_resources()
        self.data_characteristics = self.analyze_data_characteristics()
    
    def calculate_index_strategy(self):
        """基於查詢模式分析計算索引策略"""
        query_patterns = self.analyze_query_patterns()
        return {
            'primary_indexes': self.identify_primary_keys(),
            'composite_indexes': self.optimize_composite_indexes(query_patterns),
            'partial_indexes': self.calculate_selective_indexes()
        }
    
    def optimize_batch_processing(self):
        """基於IO和記憶體特性優化批次處理"""
        memory_available = self.system_resources['memory_mb']
        io_bandwidth = self.system_resources['io_mbps']
        data_row_size = self.data_characteristics['avg_row_size_bytes']
        
        # 基於記憶體限制計算最佳批次大小
        max_batch_memory = memory_available * 0.1  # 使用10%記憶體
        optimal_batch_size = int(max_batch_memory * 1024 * 1024 / data_row_size)
        
        return min(optimal_batch_size, 10000)  # 上限10K防止長事務
```

#### 數據完整性驗證機制
```python
# ✅ 正確：確保學術級數據完整性
def verify_data_integration_integrity(source_data, integrated_data):
    """驗證數據整合過程的完整性和準確性"""
    
    integrity_checks = {
        'record_count_preservation': verify_record_counts(source_data, integrated_data),
        'time_series_continuity': verify_time_series_completeness(source_data, integrated_data),
        'measurement_accuracy': verify_measurement_values(source_data, integrated_data),
        'metadata_preservation': verify_metadata_completeness(source_data, integrated_data),
        'data_lineage_tracking': verify_lineage_information(integrated_data)
    }
    
    return integrity_checks

def calculate_required_precision_for_storage():
    """基於測量不確定度計算存儲精度要求"""
    measurement_uncertainties = {
        'satellite_position': 1.0,      # SGP4 ±1km典型精度
        'signal_strength': 0.5,         # RSRP ±0.5dB測量精度
        'elevation_angle': 0.1,         # ±0.1度角度精度
        'time_stamp': 0.001             # ±1ms時間精度
    }
    
    # 基於測量不確定度計算所需數值精度
    storage_precision = {}
    for measurement, uncertainty in measurement_uncertainties.items():
        # 存儲精度應至少比測量不確定度高一個數量級
        required_precision = -int(math.floor(math.log10(uncertainty))) + 1
        storage_precision[measurement] = required_precision
    
    return storage_precision
```

## 📈 存儲統計與監控

### 存儲使用分析
```python
# 預期存儲分佈
STORAGE_BREAKDOWN = {
    'postgresql_total_mb': 65,
    'postgresql_breakdown': {
        'satellite_metadata': 1.5,     # 391顆衛星 × 基本資訊
        'signal_statistics': 25,       # 391顆 × 統計數據
        'handover_events': 18,         # ~1,800個換手事件
        'indexes_overhead': 9,         # 索引空間
        'system_metadata': 11.5        # PostgreSQL系統開銷
    },
    'volume_total_mb': 300,
    'volume_breakdown': {
        'enhanced_timeseries': 75,     # 前端動畫數據
        'layered_phase0': 85,          # 分層處理結果  
        'handover_scenarios': 55,      # 換手場景
        'signal_analysis': 65,         # 信號分析
        'cache_files': 20             # 緩存檔案
    }
}
```

### 健康檢查機制
```bash
# 存儲健康檢查腳本
#!/bin/bash
echo "📊 混合存儲健康檢查"

# PostgreSQL連接檢查
docker exec netstack-rl-postgres psql -U rl_user -d rl_research -c "SELECT COUNT(*) FROM satellite_metadata;" > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL: 正常"
else
    echo "❌ PostgreSQL: 異常"
fi

# Volume檔案檢查
if [ -f "/app/data/timeseries_preprocessing_outputs/animation_enhanced_starlink.json" ]; then
    echo "✅ Volume檔案: 正常"
else
    echo "❌ Volume檔案: 遺失"
fi

# 存儲空間檢查
volume_usage=$(df -h /app/data | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $volume_usage -lt 80 ]; then
    echo "✅ 存儲空間: ${volume_usage}% (正常)"
else
    echo "⚠️ 存儲空間: ${volume_usage}% (警告)"
fi
```

## 📖 **學術標準參考文獻**

### 數據整合標準
- **ISO/IEC 25012**: "Data quality model" - 數據品質管理標準
- **IEEE Std 1320.2**: "Standard for Conceptual Modeling Language" - 數據模型設計標準
- **FAIR Data Principles**: 可發現、可訪問、可互操作、可重用的數據原則

### 資料庫系統標準
- **ANSI/SPARC三層架構**: 資料庫系統架構標準
- **ACID Properties**: 事務處理原子性、一致性、隔離性、持久性要求
- **PostgreSQL Documentation**: 官方效能調優和配置指南

### 數據血統與追溯
- **W3C PROV Data Model**: 數據來源追蹤標準
- **Dublin Core Metadata**: 數據元數據標準
- **ISO 8601**: 日期時間格式國際標準

### 測量不確定度與精度
- **ISO/IEC Guide 98-3**: 測量不確定度表達指南
- **JCGM 100:2008**: 測量不確定度評估和表達指導
- **IEEE Std 754**: 浮點算術標準 - 數值精度保證

### 存儲系統效能標準
- **TPC-C Benchmark**: 交易處理性能評估標準
- **SPEC SFS**: 存儲系統性能評估規範
- **PostgreSQL Performance**: 官方性能調優文檔

### 數據完整性驗證
- **Checksum Algorithms**: MD5、SHA-256等數據完整性驗證算法
- **Database Integrity Constraints**: 關聯式資料庫完整性約束
- **Data Validation Techniques**: 數據驗證理論和實務

## 🔧 重要修復記錄 (2025-08-18)

### 已修復的關鍵問題

#### 1. PostgreSQL連接配置錯誤
**問題**：Stage5Config 使用 `localhost` 而非容器網路名稱  
**症狀**：PostgreSQL整合失敗，連接被拒  
**修正**：
```python
# 修正前
postgres_host: str = "localhost"

# 修正後  
postgres_host: str = "netstack-postgres"
```

#### 2. 時序數據欄位名稱不一致
**問題**：代碼查找 `timeseries` 但數據使用 `position_timeseries`  
**症狀**：分層濾波產生0顆衛星  
**修正**：
```python
# 修正前
for point in satellite.get('timeseries', []):

# 修正後
timeseries_data = satellite.get('position_timeseries', satellite.get('timeseries', []))
for point in timeseries_data:
```

#### 3. 分層濾波邏輯完整修正
**成果**：
- elevation_5deg: 399顆衛星 (100%保留)
- elevation_10deg: 351顆衛星 (87.9%保留) 
- elevation_15deg: 277顆衛星 (69.4%保留)

**檔案大小**：
- Starlink: 4.9MB (5°) → 3.5MB (10°) → 2.5MB (15°)
- OneWeb: 560KB (5°) → 477KB (10°) → 339KB (15°)

### 修復驗證
```bash
# 驗證分層數據生成
ls -lh /app/data/layered_phase0_enhanced/elevation_*/

# 驗證PostgreSQL配置
python -c "from stages.data_integration_processor import Stage5Config; print(Stage5Config().postgres_host)"

# 驗證數據完整性
python -c "import json; data=json.load(open('starlink_with_3gpp_events.json')); print(f'衛星數: {len(data[\"satellites\"])}')"
```

## 🚨 故障排除

### 常見問題

1. **PostgreSQL連接失敗**
   - 檢查：容器狀態和連接字串
   - 解決：確認使用 `netstack-postgres` 而非 `localhost`

2. **分層濾波產生空結果** 
   - 檢查：時序數據欄位名稱一致性
   - 解決：使用 `position_timeseries` 欄位

3. **Volume檔案權限問題**
   - 檢查：檔案所有權和權限
   - 解決：`chown -R app:app /app/data`

4. **混合查詢性能差**
   - 檢查：PostgreSQL索引使用
   - 解決：分析查詢計劃並優化索引

### 診斷指令

```bash
# 檢查PostgreSQL數據
docker exec netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT 
    constellation,
    COUNT(*) as satellite_count,
    AVG(mean_rsrp_dbm) as avg_signal
FROM satellite_metadata sm 
LEFT JOIN signal_quality_statistics sqs ON sm.satellite_id = sqs.satellite_id
GROUP BY constellation;
"

# 檢查Volume檔案完整性
find /app/data -name "*.json" -exec echo "檢查: {}" \; -exec python -m json.tool {} > /dev/null \;

# 檢查整合狀態
curl -s http://localhost:8080/api/v1/data-integration/status | jq
```

## ✅ 階段驗證標準

### 🎯 Stage 5 完成驗證檢查清單

#### 1. **輸入驗證**
- [ ] 多源數據完整性
  - Stage 3信號分析結果
  - Stage 4時間序列數據
  - 基礎衛星元數據
- [ ] 數據時間戳一致性
  - 各階段數據時間對齊
  - 無時間差異錯誤

#### 2. **分層數據生成驗證**
- [ ] **仰角分層正確性**
  ```
  分層門檻:
  - 5度層: 全部衛星
  - 10度層: 仰角≥10°的衛星
  - 15度層: 仰角≥15°的衛星
  數量遞減驗證: 5度 > 10度 > 15度
  ```
- [ ] **每層數據完整性**
  - 時間序列保留
  - 信號指標完整
  - 可見性窗口正確

#### 3. **PostgreSQL整合驗證**
- [ ] **數據庫連接**
  - 連接成功（172.20.0.51:5432）
  - 資料表創建完成
  - 索引建立正確
- [ ] **數據寫入驗證**
  ```sql
  預期記錄數:
  - satellite_tle_data: 1,100+筆
  - satellite_signal_metrics: 200,000+筆
  - handover_events: 300+筆
  ```

#### 4. **輸出驗證**
- [ ] **混合存儲結構**
  ```json
  {
    "metadata": {
      "stage": "stage5_data_integration",
      "storage_mode": "hybrid",
      "postgresql_status": "connected",
      "volume_status": "active"
    },
    "integration_summary": {
      "elevation_5deg": {"count": 1196},
      "elevation_10deg": {"count": 900},
      "elevation_15deg": {"count": 600}
    }
  }
  ```
- [ ] **存儲分佈合理**
  - PostgreSQL: < 50MB（結構化數據）
  - Volume: < 450MB（時間序列）
  - 總計: < 500MB

#### 5. **性能指標**
- [ ] 處理時間 < 1分鐘
- [ ] 資料庫寫入速度 > 1000筆/秒
- [ ] 記憶體使用 < 500MB

#### 6. **自動驗證腳本**
```python
# 執行階段驗證
python -c "
import json
import os
import psycopg2

# 檢查輸出檔案
output_file = '/app/data/data_integration_outputs/integrated_data_output.json'
if os.path.exists(output_file):
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    metadata = data.get('metadata', {})
    summary = data.get('integration_summary', {})
    
    # 檢查分層數據
    elev_5 = summary.get('elevation_5deg', {}).get('count', 0)
    elev_10 = summary.get('elevation_10deg', {}).get('count', 0)
    elev_15 = summary.get('elevation_15deg', {}).get('count', 0)
else:
    elev_5 = elev_10 = elev_15 = 0

# 檢查PostgreSQL
try:
    conn = psycopg2.connect(
        host='172.20.0.51',
        database='rl_research',
        user='rl_user',
        password='rl_password'
    )
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM satellite_tle_data')
    db_count = cur.fetchone()[0]
    conn.close()
    db_connected = True
except:
    db_count = 0
    db_connected = False

checks = {
    'output_exists': os.path.exists(output_file),
    'elevation_layers': elev_5 > elev_10 > elev_15 > 0,
    'layer_5deg_ok': elev_5 > 1000,
    'layer_10deg_ok': elev_10 > 800,
    'layer_15deg_ok': elev_15 > 500,
    'db_connected': db_connected,
    'db_has_data': db_count > 1000
}

passed = sum(checks.values())
total = len(checks)

print('📊 Stage 5 驗證結果:')
print(f'  分層數據: 5度({elev_5}) > 10度({elev_10}) > 15度({elev_15})')
print(f'  資料庫狀態: {\"連接成功\" if db_connected else \"連接失敗\"}')
print(f'  資料庫記錄: {db_count}筆')

for check, result in checks.items():
    print(f'  {\"✅\" if result else \"❌\"} {check}')

if passed == total:
    print('✅ Stage 5 驗證通過！')
else:
    print(f'❌ Stage 5 驗證失敗 ({passed}/{total})')
    exit(1)
"
```

### 🚨 驗證失敗處理
1. **分層數據異常**: 檢查仰角門檻設定
2. **資料庫連接失敗**: 確認PostgreSQL服務狀態
3. **存儲超限**: 優化數據結構、增加壓縮

### 📊 關鍵指標
- **分層正確性**: 5度 > 10度 > 15度遞減
- **混合存儲**: PostgreSQL + Volume協同
- **性能平衡**: 查詢速度與存儲效率

---
**上一階段**: [階段四：時間序列預處理](./stage4-timeseries.md)  
**下一階段**: [階段六：動態池規劃](./stage6-dynamic-pool.md)  
**相關文檔**: [PostgreSQL設定](../system_architecture.md#postgresql-configuration)