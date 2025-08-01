# 數據遷移策略

**文件版本**: 1.0.0  
**最後更新**: 2025-08-01  
**關鍵任務**: 數據位置調整與格式升級

## 📋 遷移概述

### 主要目標
1. **數據位置統一** - 從 `/data` 遷移至 `/netstack/data`
2. **格式升級** - 支援分層標記和多事件類型
3. **向後兼容** - 確保現有系統正常運行
4. **零停機部署** - 平滑過渡策略

## 🔍 現狀分析

### 當前數據位置
```bash
/home/sat/ntn-stack/data/
├── starlink_120min_timeseries.json      # 35MB
├── starlink_120min_d2_enhanced.json     # 12MB
├── oneweb_120min_timeseries.json        # 26MB
├── oneweb_120min_d2_enhanced.json       # 8MB
├── starlink_120min_timeseries_sgp4.json # 35MB
└── oneweb_120min_timeseries_sgp4.json   # 26MB
```

### 目標位置
```bash
/home/sat/ntn-stack/netstack/data/
├── satellites/
│   ├── filtered/                    # 篩選後的數據
│   │   ├── tier1_satellites.json   # 20 顆
│   │   ├── tier2_satellites.json   # 80 顆
│   │   └── tier3_satellites.json   # 500 顆
│   └── preprocessed/               # 預處理數據
│       ├── unified_timeseries_v2.json
│       └── metadata.json
├── layered_phase0/                 # 保留現有
└── .migration_status              # 遷移狀態追蹤
```

## 🚀 遷移步驟

### Phase 1: 準備階段

#### Step 1.1: 數據備份
```bash
#!/bin/bash
# backup_data.sh

BACKUP_DIR="/home/sat/ntn-stack/backups/$(date +%Y%m%d_%H%M%S)"
SOURCE_DIR="/home/sat/ntn-stack/data"
NETSTACK_DATA="/home/sat/ntn-stack/netstack/data"

echo "🔄 開始數據備份..."

# 創建備份目錄
mkdir -p "$BACKUP_DIR"

# 備份現有數據
cp -r "$SOURCE_DIR" "$BACKUP_DIR/data_backup"
cp -r "$NETSTACK_DATA" "$BACKUP_DIR/netstack_data_backup"

# 計算校驗和
find "$BACKUP_DIR" -type f -name "*.json" -exec md5sum {} \; > "$BACKUP_DIR/checksums.txt"

echo "✅ 備份完成: $BACKUP_DIR"
```

#### Step 1.2: 兼容性測試
```python
# test_data_compatibility.py

def test_backward_compatibility():
    """測試數據格式向後兼容性"""
    old_format = load_json("/data/starlink_120min_timeseries.json")
    new_format = convert_to_new_format(old_format)
    
    # 驗證關鍵字段
    assert 'positions' in new_format['satellites'][0]
    assert 'tier_labels' in new_format['satellites'][0]
    
    # 測試 API 兼容性
    response = test_api_with_old_format()
    assert response.status_code == 200
```

### Phase 2: 數據轉換

#### Step 2.1: 格式升級腳本
```python
# migrate_data_format.py

class DataMigrator:
    def __init__(self):
        self.source_dir = "/home/sat/ntn-stack/data"
        self.target_dir = "/home/sat/ntn-stack/netstack/data"
        
    def migrate(self):
        """執行數據遷移"""
        # 1. 讀取現有數據
        satellites = self._load_existing_data()
        
        # 2. 執行三階段篩選
        filtered = self._apply_filtering_pipeline(satellites)
        
        # 3. 轉換為新格式
        unified_data = self._convert_to_unified_format(filtered)
        
        # 4. 保存到新位置
        self._save_migrated_data(unified_data)
        
        # 5. 更新狀態
        self._update_migration_status()
```

#### Step 2.2: 新數據格式
```json
{
  "version": "2.0.0",
  "migration_info": {
    "migrated_at": "2025-08-15T10:00:00Z",
    "source_version": "1.0.0",
    "compatibility_mode": true
  },
  "satellites": [{
    "id": "STARLINK-1234",
    "tier_labels": ["tier_1", "tier_2", "tier_3"],
    "legacy_fields": {
      "positions": [...],  // 保留舊格式
      "visibility_data": [...]  // 兼容性
    },
    "new_fields": {
      "orbital_data": {...},
      "signal_data": {...},
      "handover_events": {
        "d2": [...],
        "d1": [...],
        "a4": [...],
        "t1": [...]
      }
    }
  }]
}
```

### Phase 3: 系統更新

#### Step 3.1: Docker 配置更新
```dockerfile
# Dockerfile 更新
FROM python:3.9-slim

# 數據目錄調整
RUN mkdir -p /app/data/satellites/filtered \
             /app/data/satellites/preprocessed \
             /app/data/layered_phase0

# 複製遷移後的數據
COPY ./netstack/data /app/data

# 環境變量更新
ENV DATA_PATH=/app/data
ENV LEGACY_SUPPORT=true
```

#### Step 3.2: API 適配層
```python
# api_adapter.py

class DataPathAdapter:
    """處理新舊數據路徑的適配器"""
    
    def __init__(self):
        self.new_path = "/app/data/satellites"
        self.legacy_path = "/app/data"
        self.compatibility_mode = os.getenv("LEGACY_SUPPORT", "true") == "true"
        
    def get_satellite_data(self, tier=None):
        """智能選擇數據源"""
        # 優先使用新數據
        if self._new_data_exists():
            return self._load_new_format(tier)
        
        # 回退到舊數據
        if self.compatibility_mode:
            logger.warning("Using legacy data format")
            return self._load_legacy_format()
        
        raise DataNotFoundError("No valid data source found")
```

### Phase 4: 驗證與切換

#### Step 4.1: 並行運行測試
```bash
#!/bin/bash
# parallel_test.sh

echo "🔄 開始並行測試..."

# 啟動使用舊數據的實例
docker run -d --name old_system \
  -v /home/sat/ntn-stack/data:/app/data \
  -p 8080:8080 \
  netstack:legacy

# 啟動使用新數據的實例
docker run -d --name new_system \
  -v /home/sat/ntn-stack/netstack/data:/app/data \
  -p 8081:8080 \
  netstack:v2

# 執行對比測試
python compare_results.py

# 清理
docker stop old_system new_system
docker rm old_system new_system
```

#### Step 4.2: 流量切換
```nginx
# nginx 配置漸進式切換
upstream backend {
    server old_system:8080 weight=90;  # 90% 流量
    server new_system:8080 weight=10;  # 10% 流量
}

# 逐步調整權重
# Day 1: 90/10
# Day 2: 70/30
# Day 3: 50/50
# Day 4: 30/70
# Day 5: 0/100
```

## 🔧 回滾計畫

### 快速回滾腳本
```bash
#!/bin/bash
# rollback.sh

BACKUP_DIR=$1

if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: ./rollback.sh <backup_directory>"
    exit 1
fi

echo "⚠️ 開始回滾到: $BACKUP_DIR"

# 停止服務
make down

# 恢復數據
rm -rf /home/sat/ntn-stack/data
rm -rf /home/sat/ntn-stack/netstack/data/satellites

cp -r "$BACKUP_DIR/data_backup" /home/sat/ntn-stack/data
cp -r "$BACKUP_DIR/netstack_data_backup/satellites" /home/sat/ntn-stack/netstack/data/

# 恢復配置
git checkout -- docker-compose.yml
git checkout -- Dockerfile

# 重啟服務
make up

echo "✅ 回滾完成"
```

## 📊 遷移檢查清單

### 遷移前檢查
- [ ] 完整備份完成
- [ ] 測試環境驗證通過
- [ ] 回滾腳本測試成功
- [ ] 團隊成員知悉計畫
- [ ] 維護窗口已安排

### 遷移中監控
- [ ] 數據完整性校驗
- [ ] API 響應時間正常
- [ ] 錯誤日誌監控
- [ ] 資源使用率正常
- [ ] 用戶影響評估

### 遷移後驗證
- [ ] 所有 API 端點正常
- [ ] 3D 渲染正常顯示
- [ ] 圖表數據正確
- [ ] 性能指標達標
- [ ] 無異常錯誤日誌

## 🚨 特殊注意事項

### Docker Volume 處理
```yaml
# docker-compose.yml 更新
services:
  netstack-api:
    volumes:
      # 新數據位置
      - ./netstack/data:/app/data
      # 臨時保留舊位置 (兼容期)
      - ./data:/app/legacy_data:ro
```

### 環境變量配置
```bash
# .env 文件
DATA_MIGRATION_MODE=progressive
LEGACY_DATA_PATH=/app/legacy_data
NEW_DATA_PATH=/app/data
COMPATIBILITY_PERIOD_DAYS=7
```

## 📅 時間線

| 日期 | 階段 | 關鍵任務 |
|------|------|----------|
| Day 1 | 準備 | 備份、測試環境準備 |
| Day 2 | 轉換 | 數據格式升級 |
| Day 3 | 測試 | 並行運行測試 |
| Day 4-8 | 漸進切換 | 流量逐步遷移 |
| Day 9 | 清理 | 移除舊數據和兼容代碼 |

## ✅ 成功標準

1. **零數據丟失** - 所有數據完整遷移
2. **零停機時間** - 服務持續可用
3. **性能不降級** - 響應時間維持或改善
4. **完全兼容** - 現有功能正常運作
5. **可追溯性** - 完整的遷移日誌

## 📚 相關文件

- 數據架構文檔：`/docs/satellite_data_architecture.md`
- 測試計畫：`08-validation-testing.md`
- API 更新指南：待創建
