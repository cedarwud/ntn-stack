# 📁 階段五：數據整合與混合存儲

[🔄 返回數據流程導航](../README.md) > 階段五

## 📖 階段概述

**目標**：將所有處理結果整合並建立混合存儲架構  
**輸入**：階段四的前端時間序列數據（~60-75MB）  
**輸出**：PostgreSQL結構化數據 + Docker Volume檔案存儲  
**存儲總量**：~365MB (PostgreSQL ~65MB + Volume ~300MB)  
**處理時間**：約 2-3 分鐘

### 🎯 @doc/todo.md 對應實現
本階段支援以下需求：
- 🔧 **分層數據準備**: 生成5°/10°/15°仰角分層數據，支援不同仰角門檻需求
- 💾 **混合存儲**: PostgreSQL快速查詢 + Volume大容量存儲，支援強化學習數據存取
- 🔗 **API接口準備**: 為動態池規劃和換手決策提供高效數據訪問接口

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
├── enhanced_timeseries/          # 前端動畫數據 (~60-75MB)
│   ├── animation_enhanced_starlink.json
│   └── animation_enhanced_oneweb.json
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
        """執行階段五完整整合處理"""
        
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
            # 1. 載入增強時間序列數據
            enhanced_data = await self._load_enhanced_timeseries()
            
            # 2. PostgreSQL 數據整合
            results["postgresql_integration"] = await self._integrate_postgresql_data(enhanced_data)
            
            # 3. 生成分層數據增強
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
        """生成分層數據增強 - 修正後的版本"""
        
        self.logger.info("🔄 生成分層仰角數據")
        
        layered_results = {}
        
        for threshold in self.config.elevation_thresholds:
            threshold_dir = Path(self.config.output_layered_dir) / f"elevation_{threshold}deg"
            threshold_dir.mkdir(parents=True, exist_ok=True)
            
            layered_results[f"elevation_{threshold}deg"] = {}
            
            for constellation, data in enhanced_data.items():
                if not data:
                    continue
                
                # 篩選符合仰角門檻的數據
                filtered_satellites = []
                
                for satellite in data.get('satellites', []):
                    filtered_timeseries = []
                    
                    # 修正：使用正確的時序數據欄位名稱
                    timeseries_data = satellite.get('position_timeseries', satellite.get('timeseries', []))
                    
                    for point in timeseries_data:
                        if point.get('elevation_deg', 0) >= threshold:
                            filtered_timeseries.append(point)
                    
                    if filtered_timeseries:
                        filtered_satellites.append({
                            **satellite,
                            'position_timeseries': filtered_timeseries  # 保持原始欄位名稱
                        })
                
                # 生成分層數據檔案
                layered_data = {
                    "metadata": {
                        **data.get('metadata', {}),
                        "elevation_threshold_deg": threshold,
                        "filtered_satellites_count": len(filtered_satellites),
                        "stage5_processing_time": datetime.now(timezone.utc).isoformat()
                    },
                    "satellites": filtered_satellites
                }
                
                output_file = threshold_dir / f"{constellation}_with_3gpp_events.json"
                
                with open(output_file, 'w') as f:
                    json.dump(layered_data, f, indent=2)
                
                file_size_mb = output_file.stat().st_size / (1024 * 1024)
                
                layered_results[f"elevation_{threshold}deg"][constellation] = {
                    "file_path": str(output_file),
                    "satellites_count": len(filtered_satellites),
                    "file_size_mb": round(file_size_mb, 2)
                }
                
                self.logger.info(f"✅ {constellation} {threshold}度: {len(filtered_satellites)} 顆衛星, {file_size_mb:.1f}MB")
        
        return layered_results
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