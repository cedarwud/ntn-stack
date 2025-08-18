# 🔧 NTN Stack 技術實施指南

**版本**: 3.0.0  
**更新日期**: 2025-08-18  
**專案狀態**: ✅ 生產就緒  
**適用於**: LEO 衛星切換研究系統 - 完整技術實施

## 📋 概述

本指南提供 NTN Stack 的**完整技術實施細節**，包括部署配置、開發環境設置、系統調優和故障排除。涵蓋從零開始的系統搭建到生產環境的維護操作。

**📋 相關文檔**：
- **系統架構**：[系統架構總覽](./system_architecture.md) - 高層系統設計
- **數據處理流程**：[數據處理流程](./data_processing_flow.md) - Pure Cron 驅動架構
- **算法實現**：[算法實現手冊](./algorithms_implementation.md) - 核心算法細節
- **衛星標準**：[衛星換手標準](./satellite_handover_standards.md) - 3GPP NTN 標準
- **API 介面**：[API 參考手冊](./api_reference.md) - 端點文檔

## 🚀 快速部署指南

### 系統需求
```bash
# 硬體要求
CPU: 4 核心 @ 2.4GHz+
RAM: 16GB+ (推薦 32GB)  
存儲: 100GB+ SSD
網路: 100Mbps+ (TLE 數據下載)

# 軟體需求
Docker: 24.0+
Docker Compose: 2.20+
Python: 3.11+
Node.js: 18+
```

### ⚡ 30 秒快速啟動
```bash
# 1. 克隆專案
git clone <repository_url>
cd ntn-stack

# 2. 啟動所有服務
make up

# 3. 等待服務健康檢查 (約 30 秒)
make status

# 4. 驗證服務可用性
curl http://localhost:8080/health     # NetStack API
curl http://localhost:5173           # SimWorld 前端
curl http://localhost:8888/api/health # SimWorld 後端
```

### 🔧 詳細部署流程
```bash
# Step 1: 環境準備
sudo apt update && sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER
newgrp docker

# Step 2: 專案配置
cp .env.example .env                 # 複製環境配置
vim .env                            # 根據需要調整配置

# Step 3: 服務啟動
make up                             # 啟動所有容器
docker-compose logs -f              # 觀察啟動日誌

# Step 4: 驗證部署
make status                         # 檢查容器狀態
./scripts/deployment-verification.sh # 執行部署驗證腳本
```

## 🐳 Docker 配置詳解

### 核心服務配置
```yaml
# docker-compose.yml 關鍵配置
services:
  netstack-api:
    build: ./netstack
    ports: ["8080:8080"]
    depends_on:
      - netstack-postgres
      - netstack-redis
    volumes:
      - tle_data:/app/tle_data
      - leo_outputs:/app/data/leo_outputs
    environment:
      - SGP4_MODE=runtime_precision
      - POSTGRES_HOST=netstack-rl-postgres
      - REDIS_URL=redis://netstack-redis:6379
    
  simworld-backend:
    build: ./simworld/backend
    ports: ["8888:8888"]
    depends_on:
      - simworld-postgres
    volumes:
      - satellite_data:/app/satellite_data
      - leo_outputs:/app/data/leo_outputs
    
  simworld-frontend:
    build: ./simworld/frontend
    ports: ["5173:80"]
    nginx_config: |
      location /api {
        proxy_pass http://simworld-backend:8888;
      }
```

### Volume 存儲配置
```yaml
volumes:
  # 持久化數據
  postgres_data:
    driver: local
  rl_postgres_data:
    driver: local
    
  # 共享數據
  tle_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./netstack/tle_data
      
  satellite_data:
    driver: local
    driver_opts:
      type: none
      o: bind  
      device: ./data/satellite_data
      
  leo_outputs:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./data/leo_outputs
```

### 網路配置
```yaml
networks:
  ntn-network:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1
          
# 服務IP分配
services:
  netstack-api:
    networks:
      ntn-network:
        ipv4_address: 172.20.0.10
  
  netstack-rl-postgres:
    networks:
      ntn-network:
        ipv4_address: 172.20.0.51
  
  simworld-backend:
    networks:
      ntn-network:
        ipv4_address: 172.20.0.20
```

## ⚙️ 統一配置管理

### 🔧 核心配置系統
**實現位置**: `netstack/src/core/config/satellite_config.py`

```python
@dataclass
class SatelliteConfig:
    """衛星系統統一配置類"""
    
    # 3GPP NTN 合規配置
    MAX_CANDIDATE_SATELLITES: int = 8
    
    # 衛星篩選配置  
    PREPROCESS_SATELLITES: Dict[str, int] = field(default_factory=lambda: {
        "starlink": 0,  # 動態決策，非固定數量
        "oneweb": 0     # 動態決策，非固定數量  
    })
    
    # 智能篩選配置
    INTELLIGENT_SELECTION: bool = True
    GEOGRAPHIC_FILTERING: bool = True
    ELEVATION_THRESHOLD_DEG: float = 10.0
    
    # 軌道計算精度配置
    SGP4_MODE: str = "runtime_precision"  # 運行時精度模式
    PERTURBATION_MODELING: bool = True    # 啟用攝動建模
    HIGH_ORDER_TERMS: bool = True         # 高階項修正
    
    # Pure Cron 驅動配置
    CRON_UPDATE_INTERVAL: int = 6         # 6小時更新週期
    INCREMENTAL_PROCESSING: bool = True   # 增量處理
    DATA_VALIDATION: bool = True          # 數據驗證
```

### 環境變數配置
```bash
# .env 文件配置範例
# 系統配置
NODE_ENV=production
LOG_LEVEL=info

# NetStack 配置
NETSTACK_API_PORT=8080
NETSTACK_POSTGRES_HOST=netstack-rl-postgres
NETSTACK_POSTGRES_PORT=5432
NETSTACK_POSTGRES_DB=rl_research
NETSTACK_POSTGRES_USER=rl_user
NETSTACK_POSTGRES_PASSWORD=secure_password

# SimWorld 配置  
SIMWORLD_API_PORT=8888
SIMWORLD_FRONTEND_PORT=5173
SIMWORLD_POSTGRES_HOST=simworld-postgres

# 衛星配置
SGP4_MODE=runtime_precision
MAX_CANDIDATE_SATELLITES=8
OBSERVER_LAT=24.9441667
OBSERVER_LON=121.3713889
ELEVATION_THRESHOLD=10.0

# Cron 配置
CRON_UPDATE_INTERVAL=6
TLE_DATA_SOURCE=celestrak
INCREMENTAL_PROCESSING=true
```

### 分層仰角門檻系統
```python
elevation_thresholds = {
    # 基礎門檻 (度)
    "ideal_service": 15.0,        # 理想服務門檻 (≥99.9% 成功率)
    "standard_service": 10.0,     # 標準服務門檻 (≥99.5% 成功率)  
    "minimum_service": 5.0,       # 最低服務門檻 (≥98% 成功率)
    "emergency_only": 3.0,        # 緊急通訊門檻 (特殊授權)
    
    # 環境調整係數
    "environment_factors": {
        "open_area": 0.9,         # 海洋、平原
        "standard": 1.0,          # 一般陸地
        "urban": 1.2,             # 城市建築遮蔽
        "complex_terrain": 1.5,   # 山區、高樓
        "severe_weather": 1.8     # 暴雨、雪災
    }
}
```

## 🔄 Pure Cron 驅動系統

### Cron 調度配置
```bash
# /etc/cron.d/ntn-stack
# 每6小時更新TLE數據
0 */6 * * * /home/sat/ntn-stack/scripts/daily_tle_download_enhanced.sh >> /var/log/tle_update.log 2>&1

# 每日凌晨執行完整六階段處理
0 2 * * * cd /home/sat/ntn-stack && /home/sat/ntn-stack/netstack/src/leo_core/main.py >> /var/log/leo_processing.log 2>&1

# 每小時檢查系統健康狀態
0 * * * * curl -f http://localhost:8080/health || systemctl restart ntn-stack >> /var/log/health_check.log 2>&1

# 每週清理舊數據
0 3 * * 0 /home/sat/ntn-stack/scripts/safe_data_cleanup.sh >> /var/log/data_cleanup.log 2>&1
```

### 智能增量處理機制
**實現位置**: `netstack/src/shared_core/incremental_update_manager.py`

```python
class IncrementalUpdateManager:
    def detect_tle_changes(self, old_tle_data, new_tle_data):
        """智能TLE變更偵測"""
        changes = []
        
        # 建立快速查找索引
        old_index = {tle.satellite_id: tle for tle in old_tle_data}
        new_index = {tle.satellite_id: tle for tle in new_tle_data}
        
        # 檢測變更
        for sat_id in new_index:
            if sat_id not in old_index:
                changes.append({
                    'type': 'ADDED',
                    'satellite_id': sat_id,
                    'new_tle': new_index[sat_id]
                })
            elif self._is_tle_significantly_different(
                old_index[sat_id], new_index[sat_id]
            ):
                changes.append({
                    'type': 'MODIFIED', 
                    'satellite_id': sat_id,
                    'old_tle': old_index[sat_id],
                    'new_tle': new_index[sat_id]
                })
        
        return changes
    
    def _is_tle_significantly_different(self, old_tle, new_tle):
        """判斷TLE是否有顯著變更"""
        # epoch時間差異
        epoch_diff = abs(old_tle.epoch - new_tle.epoch)
        if epoch_diff > 0.1:  # 0.1天
            return True
        
        # 軌道參數變化
        param_changes = [
            abs(old_tle.inclination - new_tle.inclination) > 0.001,
            abs(old_tle.mean_motion - new_tle.mean_motion) > 0.0001,
            abs(old_tle.eccentricity - new_tle.eccentricity) > 0.00001
        ]
        
        return any(param_changes)
```

### 自動清理管理
```python
# 實現位置: netstack/src/shared_core/auto_cleanup_manager.py  
class AutoCleanupManager:
    def cleanup_old_outputs(self):
        """清理過期輸出"""
        cutoff_time = datetime.now() - timedelta(days=7)
        
        for stage_dir in self.output_directories:
            for file_path in glob.glob(f"{stage_dir}/*.json"):
                if os.path.getmtime(file_path) < cutoff_time.timestamp():
                    os.remove(file_path)
    
    def preserve_critical_data(self):
        """保護重要數據"""
        # 保留最新的成功處理結果
        latest_files = self._find_latest_successful_outputs()
        for file_path in latest_files:
            self._mark_as_protected(file_path)
    
    def optimize_storage_usage(self):
        """優化存儲使用"""
        # 壓縮舊數據檔案
        old_files = self._find_compressible_files()
        for file_path in old_files:
            self._compress_file(file_path)
```

## 🔧 開發環境設置

### 本地開發環境
```bash
# 1. Python 虛擬環境設置
cd /home/sat/ntn-stack
python3 -m venv ntn_dev_env
source ntn_dev_env/bin/activate

# 2. 安裝開發依賴
pip install -r netstack/requirements.txt
pip install -r netstack/requirements-dev.txt  # 開發工具

# 3. 前端開發環境
cd simworld/frontend
npm install
npm run dev  # 開發模式啟動

# 4. 代碼品質工具
pip install flake8 black pytest mypy
npm install -g eslint prettier
```

### IDE 配置 (VS Code)
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./ntn_dev_env/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    
    "typescript.preferences.importModuleSpecifier": "relative",
    "eslint.workingDirectories": ["simworld/frontend"],
    
    "files.associations": {
        "*.tle": "plaintext",
        "*.json": "jsonc"
    }
}

// .vscode/launch.json 
{
    "configurations": [
        {
            "name": "NetStack API Debug",
            "type": "python",
            "request": "launch",
            "program": "netstack/main.py",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/netstack",
                "ENV": "development"
            }
        }
    ]
}
```

### 測試環境配置
```bash
# 單元測試
cd netstack
python -m pytest tests/unit/ -v

# 整合測試  
python -m pytest tests/integration/ -v --slow

# 性能測試
python -m pytest tests/performance/ -v --benchmark-only

# 前端測試
cd simworld/frontend
npm test                    # 單元測試
npm run test:e2e           # 端到端測試
npm run test:coverage      # 覆蓋率報告
```

## 📊 性能監控與調優

### 系統監控指標
```python
# 性能基準配置
performance_benchmarks = {
    "api_response_time": {
        "satellite_position": "< 50ms",
        "handover_decision": "< 100ms", 
        "trajectory_query": "< 200ms"
    },
    "algorithm_latency": {
        "sgp4_calculation": "< 15ms",
        "fine_grained_handover": "< 25ms",
        "ml_prediction": "< 50ms"
    },
    "system_resources": {
        "cpu_usage": "< 80%",
        "memory_usage": "< 85%",
        "disk_io": "< 80%",
        "network_latency": "< 10ms"
    },
    "accuracy_metrics": {
        "position_accuracy": "< 100m",
        "prediction_accuracy": "> 94%", 
        "handover_success_rate": "> 99%"
    }
}
```

### 監控儀表板配置
```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus:latest
    ports: ["9090:9090"]
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    
  grafana:
    image: grafana/grafana:latest
    ports: ["3000:3000"]
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/dashboards:/etc/grafana/provisioning/dashboards

  node-exporter:
    image: prom/node-exporter:latest
    ports: ["9100:9100"]
    
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    ports: ["8081:8080"]
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
```

### 性能調優指南
```bash
# 1. 數據庫優化
# PostgreSQL 配置調優
sudo vim /etc/postgresql/14/main/postgresql.conf
```

```sql
-- PostgreSQL 性能配置
shared_buffers = 4GB                    -- 25% 的系統記憶體
effective_cache_size = 12GB             -- 75% 的系統記憶體
maintenance_work_mem = 1GB
work_mem = 256MB
random_page_cost = 1.1                  -- SSD 優化
effective_io_concurrency = 200

-- 索引優化
CREATE INDEX CONCURRENTLY idx_satellite_orbital_cache_timestamp 
ON satellite_orbital_cache (timestamp);

CREATE INDEX CONCURRENTLY idx_satellite_tle_data_constellation 
ON satellite_tle_data (constellation, satellite_id);
```

```bash
# 2. Docker 容器優化
# docker-compose.yml 資源限制
services:
  netstack-api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G

# 3. Python 應用優化
# 使用 gunicorn 多進程模式
gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker \
         --bind 0.0.0.0:8080 --max-requests 1000 \
         netstack.main:app

# 4. 前端優化
cd simworld/frontend
npm run build                           # 生產構建
npm run analyze                         # 包大小分析
```

## 🔍 故障排除指南

### 常見問題診斷
```bash
# 1. 服務啟動問題
make status                             # 檢查容器狀態
docker-compose logs netstack-api        # 查看 API 日誌
docker-compose logs simworld-backend    # 查看後端日誌

# 2. 數據庫連接問題
docker exec -it netstack-rl-postgres psql -U rl_user -d rl_research
\dt                                     # 檢查表結構
SELECT COUNT(*) FROM satellite_orbital_cache;  # 檢查數據

# 3. TLE 數據更新問題
tail -f /var/log/tle_update.log         # TLE 更新日誌
ls -la netstack/tle_data/starlink/tle/  # 檢查 TLE 文件
curl -I https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink  # 測試數據源

# 4. API 響應問題  
curl -v http://localhost:8080/health    # API 健康檢查
curl -v http://localhost:8888/api/health # 後端健康檢查
netstat -tulpn | grep :8080             # 檢查端口占用
```

### 錯誤處理流程
```python
# 系統錯誤處理策略
class SystemErrorHandler:
    def handle_database_connection_error(self, error):
        """數據庫連接錯誤處理"""
        # 1. 記錄錯誤詳情
        logger.error(f"Database connection failed: {error}")
        
        # 2. 嘗試重新連接 (指數退避)
        for attempt in range(5):
            time.sleep(2 ** attempt)  # 1, 2, 4, 8, 16 秒
            if self._test_database_connection():
                return True
        
        # 3. 使用緩存數據作為備用
        return self._use_cached_data()
    
    def handle_tle_download_failure(self, url, error):
        """TLE 下載失敗處理"""
        # 1. 記錄失敗詳情
        logger.warning(f"TLE download failed from {url}: {error}")
        
        # 2. 嘗試備用數據源
        backup_urls = self._get_backup_tle_sources()
        for backup_url in backup_urls:
            if self._download_tle_data(backup_url):
                return True
        
        # 3. 使用本地緩存數據
        return self._use_local_tle_cache()
    
    def handle_sgp4_calculation_error(self, tle_data, error):
        """SGP4 計算錯誤處理"""
        # 1. 記錄錯誤和 TLE 數據
        logger.error(f"SGP4 calculation failed for {tle_data.satellite_id}: {error}")
        
        # 2. 檢查 TLE 數據有效性
        if not self._validate_tle_data(tle_data):
            return self._skip_invalid_satellite(tle_data)
        
        # 3. 使用簡化算法作為備用
        return self._fallback_to_simplified_calculation(tle_data)
```

### 系統恢復程序
```bash
# 完整系統重啟程序
./scripts/system-recovery.sh
```

```bash
#!/bin/bash
# scripts/system-recovery.sh - 系統恢復腳本

echo "🚨 開始系統恢復程序..."

# 1. 停止所有服務
echo "📍 停止所有容器..."
make down
sleep 10

# 2. 清理無用資源
echo "📍 清理 Docker 資源..."
docker system prune -f
docker volume prune -f

# 3. 檢查數據完整性
echo "📍 檢查數據完整性..."
if [ ! -f "netstack/tle_data/starlink/tle/starlink_$(date +%Y%m%d).tle" ]; then
    echo "⚠️  TLE 數據缺失，重新下載..."
    ./scripts/daily_tle_download_enhanced.sh
fi

# 4. 重新啟動服務
echo "📍 重啟系統服務..."
make up

# 5. 等待服務就緒
echo "📍 等待服務健康檢查..."
sleep 30

# 6. 驗證系統狀態
echo "📍 驗證系統狀態..."
make status

# 7. 執行健康檢查
echo "📍 執行完整健康檢查..."
curl -f http://localhost:8080/health || exit 1
curl -f http://localhost:8888/api/health || exit 1

echo "✅ 系統恢復完成！"
```

### 日誌管理
```bash
# 日誌輪轉配置 (/etc/logrotate.d/ntn-stack)
/var/log/ntn-stack/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 sat sat
    postrotate
        docker-compose restart rsyslog || true
    endscript
}

# 日誌收集命令
./scripts/collect-logs.sh
```

```bash
#!/bin/bash
# scripts/collect-logs.sh - 日誌收集腳本

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="logs_$TIMESTAMP"
mkdir -p "$LOG_DIR"

# 收集 Docker 日誌
echo "收集 Docker 容器日誌..."
for service in netstack-api simworld-backend simworld-frontend; do
    docker-compose logs --tail=1000 "$service" > "$LOG_DIR/${service}.log" 2>&1
done

# 收集系統日誌
echo "收集系統日誌..."
cp /var/log/tle_update.log "$LOG_DIR/" 2>/dev/null
cp /var/log/leo_processing.log "$LOG_DIR/" 2>/dev/null
cp /var/log/health_check.log "$LOG_DIR/" 2>/dev/null

# 收集性能數據
echo "收集性能數據..."
docker stats --no-stream > "$LOG_DIR/docker_stats.txt"
df -h > "$LOG_DIR/disk_usage.txt"
free -h > "$LOG_DIR/memory_usage.txt"
ps aux --sort=-%cpu | head -20 > "$LOG_DIR/cpu_usage.txt"

# 打包日誌
tar -czf "ntn_stack_logs_$TIMESTAMP.tar.gz" "$LOG_DIR"
echo "日誌已收集到: ntn_stack_logs_$TIMESTAMP.tar.gz"
```

## 🚨 維護與運維

### 日常維護檢查清單
```bash
# 每日檢查 (自動化)
- [ ] 檢查所有容器健康狀態
- [ ] 驗證 API 端點回應正常
- [ ] 檢查 TLE 數據更新狀態
- [ ] 監控系統資源使用率
- [ ] 檢查錯誤日誌數量

# 每週檢查 (手動)
- [ ] 檢查磁碟空間使用率
- [ ] 驗證數據備份完整性
- [ ] 檢查性能指標趨勢
- [ ] 更新安全補丁
- [ ] 清理舊數據和日誌

# 每月檢查 (手動)
- [ ] 檢查系統性能基準
- [ ] 驗證算法準確性
- [ ] 檢查依賴套件更新
- [ ] 執行災難恢復測試
- [ ] 更新文檔和配置
```

### 備份與恢復策略
```bash
# 數據備份腳本
./scripts/backup-system.sh
```

```bash
#!/bin/bash
# scripts/backup-system.sh - 系統備份腳本

BACKUP_DIR="/backup/ntn-stack/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "🗂️  開始系統備份..."

# 1. 備份 PostgreSQL 數據庫
echo "📦 備份數據庫..."
docker exec netstack-rl-postgres pg_dump -U rl_user rl_research > "$BACKUP_DIR/rl_research.sql"
docker exec simworld-postgres pg_dump -U postgres simworld > "$BACKUP_DIR/simworld.sql"

# 2. 備份配置文件
echo "📦 備份配置文件..."
cp -r netstack/src/core/config/ "$BACKUP_DIR/config/"
cp .env "$BACKUP_DIR/"
cp docker-compose.yml "$BACKUP_DIR/"

# 3. 備份重要數據
echo "📦 備份數據文件..."
cp -r data/leo_outputs/ "$BACKUP_DIR/leo_outputs/" 2>/dev/null || true
cp -r netstack/tle_data/ "$BACKUP_DIR/tle_data/" 2>/dev/null || true

# 4. 創建恢復腳本
cat > "$BACKUP_DIR/restore.sh" << 'EOF'
#!/bin/bash
echo "開始恢復系統..."
# 恢復數據庫
docker exec -i netstack-rl-postgres psql -U rl_user rl_research < rl_research.sql
docker exec -i simworld-postgres psql -U postgres simworld < simworld.sql
echo "系統恢復完成！"
EOF
chmod +x "$BACKUP_DIR/restore.sh"

echo "✅ 備份完成: $BACKUP_DIR"
```

### 安全最佳實務
```bash
# 1. 容器安全配置
# docker-compose.security.yml
services:
  netstack-api:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
    user: 1000:1000
    
# 2. 網路安全配置  
# 只暴露必要端口
ports:
  - "127.0.0.1:8080:8080"  # 僅本地訪問
  
# 使用 secrets 管理敏感資訊
secrets:
  postgres_password:
    file: ./secrets/postgres_password.txt
    
# 3. 存取控制
# 設定適當的檔案權限
chmod 600 .env
chmod 600 secrets/*
chmod 755 scripts/*.sh

# 4. 日誌安全
# 禁止在日誌中記錄敏感信息
logging:
  options:
    max-size: "100m"
    max-file: "5"
```

## 🔮 生產環境最佳實踐

### 高可用配置
```yaml
# docker-compose.prod.yml
services:
  netstack-api:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    
  # 負載均衡器
  nginx-lb:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - netstack-api
```

### CI/CD 流程整合
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
    
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build and Test
        run: |
          make test
          make build
          
      - name: Deploy to Production
        run: |
          docker-compose -f docker-compose.prod.yml up -d
          ./scripts/deployment-verification.sh
          
      - name: Notify on Success
        if: success()
        run: |
          curl -X POST "$SLACK_WEBHOOK" \
            -d '{"text":"✅ NTN Stack 部署成功！"}'
```

---

**本技術實施指南確保 NTN Stack 的完整部署、配置和維護，為研究人員和開發團隊提供可靠的技術支援基礎。**

*最後更新：2025-08-18 | 技術實施指南版本 3.0.0*