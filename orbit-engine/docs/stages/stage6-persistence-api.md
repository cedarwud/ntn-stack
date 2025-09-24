# 🌐 階段六：持久化與API層

[🔄 返回文檔總覽](../README.md) > 階段六

## 📖 階段概述

**目標**：提供數據持久化、快取管理和API服務
**輸入**：Stage 5數據整合層記憶體傳遞的多格式數據包
**輸出**：RESTful API、WebSocket、文件服務 → 前端應用和外部系統
**核心工作**：
1. 統一數據存儲和備份管理
2. 多層快取策略和性能優化
3. RESTful API和GraphQL服務
4. 實時WebSocket事件推送

**實際服務**：約150-250顆衛星的API和實時數據服務
**響應時間**：<100ms（快取）、<500ms（存儲）

### 🏗️ v2.0 模組化架構

Stage 6 大幅簡化架構，從44個檔案精簡到約14個核心檔案：

```
┌─────────────────────────────────────────────────────────────┐
│                 Stage 6: 持久化與API層                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │Storage      │  │Cache        │  │API Service  │       │
│  │Manager      │  │Manager      │  │             │       │
│  │             │  │             │  │ • RESTful   │       │
│  │ • 混合存儲   │  │ • 多層快取   │  │ • GraphQL   │       │
│  │ • 備份管理   │  │ • 失效策略   │  │ • 實時API   │       │
│  │ • 壓縮優化   │  │ • 預載策略   │  │ • 批次API   │       │
│  │ • 版本控制   │  │ • 性能監控   │  │ • 訂閱服務   │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│           │              │               │                │
│           └──────────────┼───────────────┘                │
│                          ▼                                │
│           ┌─────────────────────────────────┐            │
│           │     WebSocket Service           │            │
│           │                                 │            │
│           │ • 實時數據推送                   │            │
│           │ • 事件通知                       │            │
│           │ • 連接管理                       │            │
│           │ • 訂閱管理                       │            │
│           └─────────────────────────────────┘            │
│                          ▼                                │
│           ┌─────────────────────────────────┐            │
│           │ Stage6 Persistence Processor    │            │
│           │                                 │            │
│           │ • 服務協調                       │            │
│           │ • 負載均衡                       │            │
│           │ • 健康檢查                       │            │
│           │ • 性能監控                       │            │
│           └─────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

### 核心原則
- **簡化優先**: 大幅減少檔案數量和複雜度
- **服務導向**: 專注於API服務和數據提供
- **高性能**: 優化的快取和存儲策略
- **可擴展**: 支援水平擴展和負載均衡

### 🎯 重大簡化對比

| 功能類別 | 舊架構檔案數 | 新架構檔案數 | 簡化說明 |
|----------|-------------|-------------|----------|
| 備份管理 | 8個backup_*檔案 | 1個storage_manager.py | 統一存儲管理 |
| API服務 | 分散在15+個檔案 | 2個檔案 | api_service.py + websocket_service.py |
| 快取管理 | 混合在各處 | 1個cache_manager.py | 統一快取策略 |
| 動態池功能 | 15個檔案 | 4個檔案 | 保留核心優化和驗證功能 |
| 其他雜項 | 15+個檔案 | 3個支援檔案 | 保留核心功能 |
| **總計** | **44個檔案** | **~14個檔案** | **68%減少** |

## 📦 模組設計

### 1. Storage Manager (`storage_manager.py`)
*替代原本8個backup_*檔案*

#### 功能職責
- 統一存儲管理（替代8個分散的備份模組）
- 多種存儲後端支援
- 數據版本控制
- 自動備份和恢復

#### 核心方法
```python
class StorageManager:
    def store_data(self, data_type, data, metadata):
        """存儲數據到主要存儲"""

    def backup_data(self, data_id, backup_policy):
        """根據策略備份數據"""

    def retrieve_data(self, data_id, version=None):
        """檢索數據"""

    def cleanup_old_data(self, retention_policy):
        """清理舊數據"""

    def get_storage_statistics(self):
        """獲取存儲統計信息"""

    def list_stored_data(self):
        """列出已存儲的數據"""
```

#### 實現特色
- **完整錯誤處理**: 包含數據損壞、存儲空間不足、權限錯誤等異常處理
- **統計追蹤**: 實時追蹤存儲使用量、備份狀態、操作次數
- **壓縮優化**: 自動數據壓縮，節省70%存儲空間
- **版本控制**: 支援數據版本回滾和增量備份
- **存儲監控**: 持續監控存儲健康狀態和性能指標

### 2. Cache Manager (`cache_manager.py`)
*整合原本分散在各處的快取邏輯*

#### 功能職責
- 多層快取管理（L1記憶體、L2 Redis、L3磁碟）
- 智能預載策略
- 快取失效管理
- 性能優化

#### 核心方法
```python
class CacheManager:
    def get(self, key, data_type):
        """多層快取獲取"""

    def set(self, key, value, ttl=None):
        """設置快取"""

    def invalidate(self, pattern):
        """快取失效"""

    def preload_frequent_data(self):
        """預載熱門數據"""

    def get_cache_statistics(self):
        """獲取快取統計信息"""

    def clear_all_cache(self):
        """清空所有快取層"""
```

#### 實現特色
- **智能快取策略**: L1(記憶體)→L2(Redis)→L3(磁碟)三層自動調度
- **熱點數據分析**: 自動識別頻繁訪問數據並預載到高速快取
- **失效模式**: 支援模式匹配快取失效和TTL自動過期
- **統計監控**: 實時追蹤命中率、響應時間、快取容量使用情況
- **容錯機制**: Redis不可用時自動降級到記憶體快取
- **性能優化**: 支援批量操作和異步預載策略

### 3. API Service (`api_service.py`)
*整合原本分散的API功能*

#### 功能職責
- RESTful API服務
- GraphQL查詢支援
- API版本管理
- 請求限流和認證

#### 核心方法
```python
class APIService:
    def setup_routes(self):
        """設置API路由"""

    def get_satellite_pools(self, query_params):
        """獲取衛星池數據"""

    def get_animation_data(self, query_params):
        """獲取動畫數據"""

    def get_handover_events(self, query_params):
        """獲取換手事件"""

    def get_api_statistics(self):
        """獲取API統計信息"""

    def start_server(self):
        """啟動API服務器"""
```

#### 實現特色
- **請求限流**: 基於IP和用戶的智能限流機制，防止API濫用
- **錯誤處理**: 標準化HTTP狀態碼和錯誤響應格式
- **請求驗證**: 自動驗證請求參數和數據格式
- **統計追蹤**: 實時監控API調用量、響應時間、錯誤率
- **快取整合**: 智能使用快取系統提升響應速度
- **查詢優化**: 支援複雜查詢和數據過濾功能

#### 主要API端點
```
GET /api/v1/satellite-pools          # 獲取當前衛星池
GET /api/v1/satellite-pools/{id}     # 獲取池詳情
GET /api/v1/animation-data           # 獲取動畫數據
GET /api/v1/handover-events          # 獲取換手事件
GET /api/v1/status                   # 系統狀態
GET /api/v1/health                   # 健康檢查
POST /api/v1/query                   # 自定義查詢
```

### 4. WebSocket Service (`websocket_service.py`)

#### 功能職責
- 實時數據推送
- 事件通知服務
- 連接管理
- 訂閱管理

#### 核心方法
```python
class WebSocketService:
    def handle_connection(self, websocket):
        """處理新連接"""

    def handle_subscription(self, client_id, subscription):
        """處理訂閱請求"""

    def broadcast_satellite_update(self, update):
        """廣播衛星更新"""

    def broadcast_handover_event(self, event):
        """廣播換手事件"""

    def get_websocket_statistics(self):
        """獲取WebSocket統計信息"""

    def start_server(self):
        """啟動WebSocket服務器"""

    def stop_server(self):
        """停止WebSocket服務器"""
```

#### 實現特色
- **連接管理**: 自動處理連接生命週期、心跳檢測、異常重連
- **訂閱系統**: 靈活的事件訂閱和過濾機制
- **事件分發**: 高效的事件廣播和點對點消息傳遞
- **統計監控**: 實時追蹤連接數量、消息吞吐量、錯誤率
- **安全機制**: 連接驗證和消息過濾防護
- **性能優化**: 支援消息批處理和異步事件處理

#### WebSocket事件類型
- `satellite_pool_update`: 衛星池更新
- `handover_event`: 換手事件通知
- `signal_quality_change`: 信號品質變化
- `system_status_update`: 系統狀態更新
- `error_notification`: 錯誤通知

### 5. Stage6 Persistence Processor (`stage6_main_processor.py`)

#### 功能職責
- 服務協調和管理
- 負載均衡
- 健康檢查
- 性能監控

#### 核心方法
```python
class Stage6PersistenceProcessor:
    def process(self, input_data):
        """執行完整的持久化和API處理流程"""

    def validate_input(self, input_data):
        """驗證輸入數據格式和完整性"""

    def validate_output(self, output_data):
        """驗證輸出數據格式和完整性"""

    def run_validation_checks(self, data):
        """運行完整的驗證檢查流程"""

    def extract_key_metrics(self, result_data):
        """提取關鍵性能指標"""

    def save_results(self, results):
        """保存處理結果到存儲系統"""
```

#### 實現特色
- **完整驗證流程**: 包含輸入驗證、輸出驗證、服務健康檢查、性能標準驗證
- **錯誤恢復機制**: 自動處理服務故障和數據異常情況
- **統計追蹤系統**: 實時監控處理統計、性能指標、服務狀態
- **學術級驗證**: 符合學術標準的數據驗證和合規性檢查
- **服務協調**: 統一管理四大核心模組的生命週期和狀態
- **性能監控**: 持續監控響應時間、快取命中率、服務可用性

### 6. Pool Optimization Engine (`pool_optimization_engine.py`)

#### 功能職責
- 衛星池優化算法
- 性能指標計算
- 資源配置優化
- 覆蓋範圍優化

### 7. Pool Generation Engine (`pool_generation_engine.py`)

#### 功能職責
- 動態衛星池生成
- 候選衛星篩選
- 池配置管理
- 負載均衡策略

### 8. Scientific Validation Engine (`scientific_validation_engine.py`)

#### 功能職責
- 學術級驗證標準
- 性能基準測試
- 算法正確性驗證
- 科學計算合規檢查

### 9. Coverage Validation Engine (`coverage_validation_engine.py`)

#### 功能職責
- 覆蓋範圍驗證
- 服務品質評估
- 地理覆蓋分析
- 性能指標驗證

## 🛡️ 錯誤處理與監控機制

### 錯誤處理策略
Stage 6 實現了完整的錯誤處理和恢復機制：

#### 1. 分層錯誤處理
```python
# 存儲層錯誤處理
try:
    self.storage_manager.store_data(data_type, data, metadata)
except StorageSpaceError:
    # 自動清理舊數據並重試
    self.storage_manager.cleanup_old_data()
except DataCorruptionError:
    # 使用備份數據恢復
    self.storage_manager.restore_from_backup()
```

#### 2. 服務降級機制
- **快取服務**: Redis不可用時自動降級到記憶體快取
- **API服務**: 負載過高時啟用限流和排隊機制
- **WebSocket服務**: 連接異常時自動重連和狀態恢復

#### 3. 統計追蹤系統
實時監控和統計以下指標：

```python
# 處理統計
processing_stats = {
    'data_persistence_operations': 0,
    'api_requests_served': 0,
    'websocket_events_sent': 0,
    'cache_operations': 0,
    'processing_time_seconds': 0
}

# 性能指標
performance_metrics = {
    'api_response_time_ms': 0,
    'cache_hit_rate': 0.0,
    'active_connections': 0,
    'storage_usage_gb': 0.0
}
```

### 驗證檢查流程
Stage 6 實現了四層驗證機制：

1. **服務健康檢查**: 驗證所有4個核心服務狀態
2. **API功能驗證**: 確保所有7個API端點正常運作
3. **持久化完整性**: 驗證數據存儲和檢索的一致性
4. **性能標準驗證**: 確保響應時間和吞吐量達標

### 學術級合規驗證
- **數據完整性**: 確保無數據丟失或損壞
- **性能基準**: 嚴格遵循文檔定義的性能標準
- **錯誤處理**: 所有異常情況都有明確的處理策略
- **統計準確性**: 所有統計數據都經過驗證和校對

## 🔄 數據流程

### 輸入處理
```python
# 從Stage 5接收數據
stage5_output = {
    'timeseries_data': {...},     # 時間序列數據
    'animation_data': {...},      # 動畫數據
    'hierarchical_data': {...},   # 分層數據
    'formatted_outputs': {...},   # 多格式輸出
    'metadata': {...}             # 處理元數據
}
```

### 處理流程
1. **數據持久化**: 將多格式數據存儲到主要存儲系統
2. **快取設置**: 建立多層快取和預載策略
3. **API服務啟動**: 啟動RESTful和GraphQL服務
4. **WebSocket初始化**: 啟動實時通知服務
5. **服務監控**: 開始健康檢查和性能監控

### 輸出格式
```python
stage6_output = {
    'stage': 'stage6_persistence_api',
    'api_endpoints': [
        {'url': '/api/v1/satellite-pools', 'method': 'GET'},
        {'url': '/api/v1/animation-data', 'method': 'GET'},
        {'url': '/api/v1/handover-events', 'method': 'GET'}
    ],
    'websocket_endpoints': [
        {'url': 'ws://localhost:8081/events', 'type': 'events'}
    ],
    'service_status': {
        'api_service': 'healthy',
        'websocket_service': 'healthy',
        'storage_service': 'healthy',
        'cache_service': 'healthy'
    },
    'performance_metrics': {
        'api_response_time_ms': 45,
        'cache_hit_rate': 0.85,
        'active_connections': 127,
        'storage_usage_gb': 2.3
    },
    'statistics': {
        'data_persistence_operations': 4,
        'api_requests_served': 127,
        'websocket_events_sent': 45,
        'cache_operations': 234,
        'processing_time_seconds': 2.34
    },
    'metadata': {
        'processing_time': '2025-09-21T04:10:00Z',
        'api_version': 'v1.0',
        'service_uptime': '2h 15m',
        'total_requests_handled': 15847,
        'architecture_version': 'v2.0_modular_simplified',
        'compliance_status': 'COMPLIANT_with_documentation'
    }
}
```

## ⚙️ 配置參數

### 存儲配置
```yaml
storage:
  primary_backend: "postgresql"     # 主要存儲後端
  backup_backend: "s3"              # 備份存儲後端
  compression_enabled: true         # 啟用壓縮
  retention_days: 30               # 數據保留天數
  backup_frequency: "daily"        # 備份頻率
```

### 快取配置
```yaml
cache:
  l1_cache:                        # L1記憶體快取
    type: "memory"
    size_mb: 256
    ttl_seconds: 300
  l2_cache:                        # L2 Redis快取
    type: "redis"
    host: "localhost"
    port: 6379
    ttl_seconds: 3600
  l3_cache:                        # L3磁碟快取
    type: "disk"
    path: "/var/cache/stage6"
    size_gb: 10
```

### API配置
```yaml
api:
  port: 8080                       # API服務端口
  workers: 4                       # 工作進程數
  rate_limit: 100                  # 請求限制（每分鐘）
  enable_cors: true               # 啟用CORS
  api_version: "v1.0"             # API版本
```

## 🎯 性能指標

### 服務效能
- **API響應時間**: <100ms（快取命中）、<500ms（存儲查詢）
- **WebSocket延遲**: <50ms
- **併發連接**: 支援1000+同時連接
- **數據吞吐量**: >10MB/s

### 可用性指標
- **服務可用性**: >99.9%
- **快取命中率**: >80%
- **API成功率**: >99.5%
- **WebSocket連接穩定性**: >95%

## 🔍 驗證標準

### 服務驗證
- API端點可訪問性
- WebSocket連接穩定性
- 數據持久化完整性

### 性能驗證
- 響應時間達標
- 併發處理能力
- 快取效率檢查

### 可用性驗證
- 服務健康檢查
- 故障恢復能力
- 數據一致性保證

---
**系統完成**: 六階段處理管道已全部設計完成
**相關文檔**: [v2.0重構計劃](../refactoring_plan_v2/stage6_persistence_api.md)