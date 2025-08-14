# 📁 階段五：數據整合與混合存儲

[🔄 返回數據流程導航](../data-flow-index.md) > 階段五

## 📖 階段概述

**目標**：將所有處理結果整合並建立混合存儲架構  
**輸入**：階段四的前端時間序列數據（~85-100MB）  
**輸出**：PostgreSQL結構化數據 + Docker Volume檔案存儲  
**存儲總量**：~486MB (PostgreSQL ~86MB + Volume ~400MB)  
**處理時間**：約 2-3 分鐘

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
├── enhanced_timeseries/          # 前端動畫數據 (~85-100MB)
│   ├── animation_enhanced_starlink.json
│   └── animation_enhanced_oneweb.json
│
├── layered_phase0_enhanced/      # 分層處理結果 (~120MB)
│   ├── starlink_5deg_enhanced.json
│   ├── starlink_10deg_enhanced.json
│   ├── starlink_15deg_enhanced.json
│   ├── oneweb_10deg_enhanced.json
│   ├── oneweb_15deg_enhanced.json
│   └── oneweb_20deg_enhanced.json
│
├── handover_scenarios/           # 換手場景數據 (~80MB)
│   ├── a4_events_enhanced.json
│   ├── a5_events_enhanced.json
│   ├── d2_events_enhanced.json
│   └── best_handover_windows.json
│
├── signal_quality_analysis/      # 信號分析結果 (~90MB)
│   ├── signal_heatmap_data.json
│   ├── quality_metrics_summary.json
│   └── constellation_comparison.json
│
├── processing_cache/             # 處理緩存 (~50MB)
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

## 🔧 整合處理器實現

### 主要實現位置
```bash
# 整合處理器
/netstack/src/stages/stage5_integration_processor.py
├── Stage5IntegrationProcessor.setup_postgresql_schema()    # 資料庫架構設定
├── Stage5IntegrationProcessor.populate_metadata_tables()   # 元數據填入
├── Stage5IntegrationProcessor.generate_volume_files()      # Volume檔案生成
├── Stage5IntegrationProcessor.verify_mixed_storage()       # 混合存儲驗證
└── Stage5IntegrationProcessor.process_stage5()             # 完整流程執行

# 資料庫連接管理
/netstack/src/services/database/postgresql_manager.py
├── PostgreSQLManager.setup_connection_pool()              # 連接池管理
├── PostgreSQLManager.execute_batch_insert()               # 批次插入優化
└── PostgreSQLManager.create_indexes()                     # 索引建立
```

### 核心處理邏輯
```python
class Stage5IntegrationProcessor:
    
    async def process_stage5(self) -> Dict[str, Any]:
        """執行階段五完整整合處理"""
        
        results = {}
        
        # 1. 設定PostgreSQL架構
        await self._setup_postgresql_schema()
        logger.info("✅ PostgreSQL架構設定完成")
        
        # 2. 填入衛星元數據
        satellite_count = await self._populate_metadata_tables()
        results['postgresql_satellites'] = satellite_count
        logger.info(f"✅ PostgreSQL元數據: {satellite_count}顆衛星")
        
        # 3. 填入信號統計數據
        signal_records = await self._populate_signal_statistics()
        results['postgresql_signal_records'] = signal_records
        logger.info(f"✅ PostgreSQL信號統計: {signal_records}筆記錄")
        
        # 4. 填入換手事件摘要
        event_records = await self._populate_handover_events()
        results['postgresql_event_records'] = event_records
        logger.info(f"✅ PostgreSQL換手事件: {event_records}筆記錄")
        
        # 5. 生成Volume檔案
        volume_files = await self._generate_all_volume_files()
        results['volume_files'] = volume_files
        logger.info(f"✅ Volume檔案: {len(volume_files)}個檔案")
        
        # 6. 混合存儲驗證
        verification = await self._verify_mixed_storage_access()
        results['storage_verification'] = verification
        logger.info(f"✅ 混合存儲驗證完成")
        
        return results
    
    async def _populate_metadata_tables(self) -> int:
        """批次填入衛星元數據到PostgreSQL"""
        
        satellites = self.get_all_processed_satellites()
        
        insert_data = []
        for satellite in satellites:
            insert_data.append({
                'satellite_id': satellite['satellite_id'],
                'constellation': satellite['constellation'],
                'norad_id': satellite['norad_id'],
                'tle_epoch': satellite['tle_epoch'],
                'orbital_period_minutes': satellite['orbital_period_minutes'],
                'inclination_deg': satellite['inclination_deg'],
                'mean_altitude_km': satellite['mean_altitude_km']
            })
        
        # 批次插入優化
        await self.postgresql_manager.execute_batch_insert(
            'satellite_metadata',
            insert_data,
            batch_size=100
        )
        
        return len(insert_data)
```

## ⚙️ 性能最佳化策略

### PostgreSQL 最佳化
```python
# 連接池配置
POSTGRESQL_CONFIG = {
    'max_connections': 20,
    'connection_timeout': 30,
    'query_timeout': 60,
    'batch_insert_size': 100,
    'enable_connection_pooling': True
}

# 索引策略
INDEX_STRATEGY = {
    'primary_indexes': ['satellite_id', 'norad_id'],
    'composite_indexes': [
        ('satellite_id', 'analysis_period_start'),
        ('constellation', 'signal_quality_grade')
    ],
    'partial_indexes': [
        'signal_quality_grade WHERE signal_quality_grade = \'high\''
    ]
}
```

### 檔案I/O最佳化
```python
# Volume寫入策略
VOLUME_CONFIG = {
    'write_buffer_size': '64MB',
    'compression_enabled': True,
    'async_write_enabled': True,
    'file_integrity_check': True
}

# JSON序列化最佳化
JSON_CONFIG = {
    'ensure_ascii': False,
    'separators': (',', ':'),  # 緊湊格式
    'sort_keys': False,        # 保持原始順序
    'indent': None            # 無縮排節省空間
}
```

## 📈 存儲統計與監控

### 存儲使用分析
```python
# 預期存儲分佈
STORAGE_BREAKDOWN = {
    'postgresql_total_mb': 86,
    'postgresql_breakdown': {
        'satellite_metadata': 2,      # 563顆衛星 × 基本資訊
        'signal_statistics': 35,      # 563顆 × 統計數據
        'handover_events': 25,        # ~2,600個換手事件
        'indexes_overhead': 12,       # 索引空間
        'system_metadata': 12         # PostgreSQL系統開銷
    },
    'volume_total_mb': 400,
    'volume_breakdown': {
        'enhanced_timeseries': 100,   # 前端動畫數據
        'layered_phase0': 120,        # 分層處理結果  
        'handover_scenarios': 80,     # 換手場景
        'signal_analysis': 90,        # 信號分析
        'cache_files': 10            # 緩存檔案
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
if [ -f "/app/data/enhanced_timeseries/animation_enhanced_starlink.json" ]; then
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

## 🚨 故障排除

### 常見問題

1. **PostgreSQL連接失敗**
   - 檢查：容器狀態和連接字串
   - 解決：重啟PostgreSQL容器

2. **Volume檔案權限問題**
   - 檢查：檔案所有權和權限
   - 解決：`chown -R app:app /app/data`

3. **混合查詢性能差**
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

---
**上一階段**: [階段四：時間序列預處理](./stage4-timeseries.md)  
**下一階段**: [階段六：動態池規劃](./stage6-dynamic-pool.md)  
**相關文檔**: [PostgreSQL設定](../system_architecture.md#postgresql-configuration)