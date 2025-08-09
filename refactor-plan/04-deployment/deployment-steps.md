# 部署架構優化執行步驟

## 🎯 執行時程與優先級

### Step 1: Docker Compose架構重構 (Priority 1)
**時間:** 8 小時  
**風險:** 中等  
**影響:** 高

#### 1.1 創建分層compose架構
```bash
# 創建新的compose目錄結構
mkdir -p /home/sat/ntn-stack/docker/compose/
mkdir -p /home/sat/ntn-stack/docker/scripts/
mkdir -p /home/sat/ntn-stack/docker/sql/init/
mkdir -p /home/sat/ntn-stack/docker/mongo/init/

cd /home/sat/ntn-stack/docker/compose/
```

#### 1.2 創建基礎設施層compose
```yaml
# 文件: docker/compose/docker-compose.base.yaml

version: '3.8'

networks:
  netstack-network:
    name: netstack-network
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1

volumes:
  postgres_data:
    name: netstack_postgres_data
    driver: local
  mongo_data:
    name: netstack_mongo_data
    driver: local
  redis_data:
    name: netstack_redis_data
    driver: local
  satellite_data:
    name: netstack_satellite_data
    driver: local

services:
  postgres:
    image: postgres:16-alpine
    container_name: netstack-postgres
    hostname: postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-netstack_db}
      POSTGRES_USER: ${POSTGRES_USER:-netstack_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-netstack_password}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=C"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ../sql/init:/docker-entrypoint-initdb.d:ro
    networks:
      netstack-network:
        ipv4_address: 172.20.0.51
        aliases:
          - postgres
          - netstack-postgres
    ports:
      - "${POSTGRES_EXTERNAL_PORT:-5432}:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-netstack_user} -d ${POSTGRES_DB:-netstack_db}"]
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 30s

  mongo:
    image: mongo:7-jammy
    container_name: netstack-mongo
    hostname: mongo
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_ROOT_USER:-admin}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_ROOT_PASSWORD:-admin_password}
      MONGO_INITDB_DATABASE: ${MONGO_DB:-open5gs}
    volumes:
      - mongo_data:/data/db
      - ../mongo/init:/docker-entrypoint-initdb.d:ro
    networks:
      netstack-network:
        ipv4_address: 172.20.0.10
        aliases:
          - mongo
          - mongodb
    ports:
      - "${MONGO_EXTERNAL_PORT:-27017}:27017"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "mongosh", "--quiet", "--eval", "db.adminCommand('ping')"]
      interval: 15s
      timeout: 10s
      retries: 5
      start_period: 30s

  redis:
    image: redis:7-alpine
    container_name: netstack-redis
    hostname: redis
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-}
    environment:
      REDIS_PASSWORD: ${REDIS_PASSWORD:-}
    volumes:
      - redis_data:/data
    networks:
      netstack-network:
        ipv4_address: 172.20.0.50
        aliases:
          - redis
    ports:
      - "${REDIS_EXTERNAL_PORT:-6379}:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "--no-auth-warning", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
```

#### 1.3 創建應用服務層compose
```yaml
# 文件: docker/compose/docker-compose.apps.yaml

version: '3.8'

services:
  netstack-api:
    build:
      context: ../..
      dockerfile: docker/Dockerfile
      target: production
      args:
        - ENVIRONMENT=${ENVIRONMENT:-production}
      cache_from:
        - netstack-api:latest
        - netstack-api:build-cache
    image: netstack-api:${IMAGE_TAG:-latest}
    container_name: netstack-api
    hostname: netstack-api
    
    entrypoint: ["/usr/local/bin/smart-entrypoint.sh"]
    command: ["python", "-m", "netstack_api.main"]
    
    environment:
      # 應用配置
      - ENVIRONMENT=${ENVIRONMENT:-production}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - API_HOST=0.0.0.0
      - API_PORT=8080
      - API_WORKERS=${API_WORKERS:-1}
      
      # 數據庫連接配置
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=${POSTGRES_DB:-netstack_db}
      - POSTGRES_USER=${POSTGRES_USER:-netstack_user}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-netstack_password}
      
      - MONGO_HOST=mongo
      - MONGO_PORT=27017
      - MONGO_ROOT_USER=${MONGO_ROOT_USER:-admin}
      - MONGO_ROOT_PASSWORD=${MONGO_ROOT_PASSWORD:-admin_password}
      - MONGO_DB=${MONGO_DB:-open5gs}
      
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD:-}
      
      # 衛星系統配置
      - SATELLITE_DATA_MODE=${SATELLITE_DATA_MODE:-instant_load}
      - PRECOMPUTE_ON_STARTUP=${PRECOMPUTE_ON_STARTUP:-true}
      - POSTGRES_WAIT_TIMEOUT=${POSTGRES_WAIT_TIMEOUT:-30}
      
      # 性能配置
      - PYTHONPATH=/app/netstack
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
    
    volumes:
      - ../../netstack/config:/app/config:ro
      - satellite_data:/app/data
      - ../../netstack/tle_data:/app/tle_data:ro
      - ../../netstack/logs:/app/logs
    
    networks:
      netstack-network:
        ipv4_address: 172.20.0.40
        aliases:
          - netstack-api
          - api
    
    ports:
      - "${API_EXTERNAL_PORT:-8080}:8080"
    
    depends_on:
      postgres:
        condition: service_healthy
      mongo:
        condition: service_healthy
      redis:
        condition: service_healthy
    
    restart: unless-stopped
    
    healthcheck:
      test: ["CMD", "/usr/local/bin/health-check.sh"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 90s
    
    deploy:
      resources:
        limits:
          memory: ${API_MEMORY_LIMIT:-2G}
          cpus: ${API_CPU_LIMIT:-1.0}
        reservations:
          memory: ${API_MEMORY_RESERVE:-512M}
          cpus: ${API_CPU_RESERVE:-0.5}

networks:
  netstack-network:
    external: true

volumes:
  satellite_data:
    external: true
```

#### 1.4 創建master compose文件
```yaml
# 文件: docker-compose.yaml - 根目錄master文件

version: '3.8'

# 包含所有服務的主compose文件
include:
  - path: docker/compose/docker-compose.base.yaml
    env_file: .env.${ENVIRONMENT:-development}
  - path: docker/compose/docker-compose.apps.yaml  
    env_file: .env.${ENVIRONMENT:-development}

# 可以添加全域配置覆蓋
```

---

### Step 2: 多階段Dockerfile優化 (Priority 1)
**時間:** 6 小時  
**風險:** 中等  
**影響:** 高

#### 2.1 創建優化的多階段Dockerfile
```dockerfile
# 文件: docker/Dockerfile

# =====================================
# Stage 1: Base System
# =====================================
FROM python:3.11-slim as base

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    # 基本工具
    curl \
    wget \
    git \
    # 編譯工具
    gcc \
    g++ \
    make \
    # 數學函式庫 (SGP4需要)
    libatlas-base-dev \
    liblapack-dev \
    libopenblas-dev \
    # 網路工具
    netcat-openbsd \
    # 清理
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/*

# 升級pip和安裝基礎工具
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# =====================================  
# Stage 2: Python Dependencies
# =====================================
FROM base as python-deps

# 復制requirements文件 (依快取友善順序)
COPY netstack/requirements.txt requirements.txt

# 安裝Python依賴 (生產 + 核心)
RUN pip install --no-cache-dir -r requirements.txt

# =====================================
# Stage 3: Development Stage  
# =====================================
FROM python-deps as development

# 復制開發依賴
COPY netstack/requirements-dev.txt requirements-dev.txt

# 安裝開發工具
RUN pip install --no-cache-dir -r requirements-dev.txt

# 設置開發環境變數
ENV ENVIRONMENT=development
ENV PYTHONPATH=/app/netstack
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=development

# 開發用戶配置
RUN groupadd -r dev && useradd -r -g dev dev
RUN mkdir -p /app/logs /app/data && chown -R dev:dev /app
USER dev

# 開發啟動點
ENTRYPOINT ["/usr/local/bin/smart-entrypoint.sh"]
CMD ["python", "-m", "netstack_api.main", "--reload"]

# =====================================
# Stage 4: Production Stage
# =====================================
FROM python-deps as production

# 創建應用用戶
RUN groupadd -r netstack && useradd -r -g netstack -s /bin/bash netstack

# 復制應用代碼 (最晚復制以最大化快取效果)
COPY --chown=netstack:netstack netstack/ /app/netstack/

# 復制腳本文件
COPY --chown=netstack:netstack docker/scripts/smart-entrypoint.sh /usr/local/bin/
COPY --chown=netstack:netstack docker/scripts/health-check.sh /usr/local/bin/
COPY --chown=netstack:netstack docker/scripts/wait-for-service.sh /usr/local/bin/

# 設置腳本權限
RUN chmod +x /usr/local/bin/smart-entrypoint.sh && \
    chmod +x /usr/local/bin/health-check.sh && \
    chmod +x /usr/local/bin/wait-for-service.sh

# 創建必要目錄
RUN mkdir -p /app/logs /app/data /app/tmp && \
    chown -R netstack:netstack /app

# 設置生產環境變數
ENV ENVIRONMENT=production
ENV PYTHONPATH=/app/netstack
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHON_MALLOC_STATS=1

# 切換到應用用戶
USER netstack

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD ["/usr/local/bin/health-check.sh"]

# 生產啟動
ENTRYPOINT ["/usr/local/bin/smart-entrypoint.sh"]
CMD ["python", "-m", "netstack_api.main"]

# =====================================
# Stage 5: Testing Stage (可選)
# =====================================
FROM development as testing

# 復制測試文件
COPY --chown=dev:dev tests/ /app/tests/

# 設置測試環境
ENV ENVIRONMENT=testing
ENV PYTHONPATH=/app/netstack:/app/tests

# 測試啟動命令
CMD ["python", "-m", "pytest", "tests/", "-v"]
```

#### 2.2 創建增強的啟動腳本
```bash
# 文件: docker/scripts/smart-entrypoint.sh

#!/bin/bash
set -e

echo "🚀 NetStack API Starting..."
echo "Environment: ${ENVIRONMENT:-development}"
echo "Log Level: ${LOG_LEVEL:-INFO}"

# 函數: 等待服務就緒
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local timeout=${4:-30}
    
    echo "⏳ 等待 $service_name 服務就緒 ($host:$port)..."
    
    local count=0
    while ! nc -z "$host" "$port"; do
        count=$((count + 1))
        if [ $count -gt $timeout ]; then
            echo "❌ $service_name 服務未就緒，超時退出"
            exit 1
        fi
        echo "   嘗試 $count/$timeout - $service_name 未就緒，等待1秒..."
        sleep 1
    done
    
    echo "✅ $service_name 服務就緒"
}

# 函數: 設置Python環境
setup_python_env() {
    echo "🐍 設置Python環境..."
    export PYTHONPATH="/app/netstack:$PYTHONPATH"
    export PYTHONUNBUFFERED=1
    
    # 檢查Python模塊是否可導入
    python -c "import sys; print(f'Python版本: {sys.version}')"
    python -c "import netstack_api.main; print('✅ NetStack API模塊載入成功')" || {
        echo "❌ NetStack API模塊載入失敗"
        exit 1
    }
}

# 函數: 等待數據庫就緒
wait_for_databases() {
    # PostgreSQL
    if [ -n "$POSTGRES_HOST" ]; then
        wait_for_service "$POSTGRES_HOST" "${POSTGRES_PORT:-5432}" "PostgreSQL" "${POSTGRES_WAIT_TIMEOUT:-30}"
        
        # 測試PostgreSQL連接
        echo "🔍 測試PostgreSQL連接..."
        python -c "
import asyncio
import asyncpg

async def test_postgres():
    try:
        conn = await asyncpg.connect(
            host='$POSTGRES_HOST',
            port=${POSTGRES_PORT:-5432},
            database='${POSTGRES_DB:-netstack_db}',
            user='${POSTGRES_USER:-netstack_user}',
            password='$POSTGRES_PASSWORD'
        )
        await conn.close()
        print('✅ PostgreSQL連接測試成功')
    except Exception as e:
        print(f'❌ PostgreSQL連接失敗: {e}')
        exit(1)

asyncio.run(test_postgres())
" || {
            echo "❌ PostgreSQL連接測試失敗"
            exit 1
        }
    fi
    
    # MongoDB
    if [ -n "$MONGO_HOST" ]; then
        wait_for_service "$MONGO_HOST" "${MONGO_PORT:-27017}" "MongoDB" 30
    fi
    
    # Redis
    if [ -n "$REDIS_HOST" ]; then
        wait_for_service "$REDIS_HOST" "${REDIS_PORT:-6379}" "Redis" 30
    fi
}

# 函數: 初始化應用數據
initialize_app_data() {
    echo "📊 初始化應用數據..."
    
    # 創建必要目錄
    mkdir -p /app/logs /app/data /app/tmp
    
    # 檢查衛星數據
    if [ "$PRECOMPUTE_ON_STARTUP" = "true" ]; then
        echo "🛰️ 預處理衛星數據..."
        python -c "
import asyncio
from netstack_api.app.services.satellite_service import SatelliteService

async def precompute_data():
    try:
        service = SatelliteService()
        await service.initialize()
        print('✅ 衛星數據預處理完成')
    except Exception as e:
        print(f'⚠️ 衛星數據預處理失敗: {e}')
        # 非致命錯誤，繼續啟動

asyncio.run(precompute_data())
" || echo "⚠️ 衛星數據預處理跳過"
    fi
}

# 主要執行流程
main() {
    echo "🔧 開始啟動程序..."
    
    # 1. 設置Python環境
    setup_python_env
    
    # 2. 等待依賴服務
    wait_for_databases
    
    # 3. 初始化應用數據 
    if [ "$ENVIRONMENT" != "development" ]; then
        initialize_app_data
    fi
    
    # 4. 執行用戶命令
    echo "🚀 啟動應用程式: $@"
    exec "$@"
}

# 捕獲信號處理
trap 'echo "🛑 收到終止信號，正在關閉..."; exit 143;' TERM

# 執行主程序
main "$@"
```

#### 2.3 創建健康檢查腳本
```bash
# 文件: docker/scripts/health-check.sh

#!/bin/bash

# 健康檢查腳本
API_URL="${API_URL:-http://localhost:8080}"
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-/health}"

# 檢查API健康狀態
check_api_health() {
    local url="$API_URL$HEALTH_ENDPOINT"
    local response
    local http_code
    
    # 使用curl檢查API健康狀態
    response=$(curl -s -w "%{http_code}" "$url" -o /tmp/health_response)
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "200" ]; then
        # 檢查響應內容
        if grep -q "healthy\|ok" /tmp/health_response 2>/dev/null; then
            echo "✅ API健康檢查通過"
            return 0
        else
            echo "❌ API響應不健康"
            cat /tmp/health_response 2>/dev/null
            return 1
        fi
    else
        echo "❌ API健康檢查失敗 (HTTP: $http_code)"
        return 1
    fi
}

# 檢查關鍵進程
check_processes() {
    # 檢查Python進程是否運行
    if pgrep -f "netstack_api.main" > /dev/null; then
        echo "✅ NetStack API進程運行中"
        return 0
    else
        echo "❌ NetStack API進程未運行"
        return 1
    fi
}

# 檢查資源使用
check_resources() {
    # 檢查記憶體使用率
    local memory_usage=$(free | awk '/^Mem:/{printf("%.1f"), $3/$2 * 100}')
    echo "📊 記憶體使用率: ${memory_usage}%"
    
    # 檢查磁碟空間
    local disk_usage=$(df /app | awk 'NR==2{printf("%.1f"), $5}' | sed 's/%//')
    echo "💾 磁碟使用率: ${disk_usage}%"
    
    # 警告檢查
    if (( $(echo "$memory_usage > 90" | bc -l) )); then
        echo "⚠️ 記憶體使用率過高: ${memory_usage}%"
    fi
    
    if (( $(echo "$disk_usage > 90" | bc -l) )); then
        echo "⚠️ 磁碟使用率過高: ${disk_usage}%"
    fi
}

# 主健康檢查函數
main() {
    echo "🔍 執行健康檢查..."
    
    # 1. 檢查進程
    if ! check_processes; then
        exit 1
    fi
    
    # 2. 檢查API健康
    if ! check_api_health; then
        exit 1
    fi
    
    # 3. 檢查資源 (僅警告，不影響健康狀態)
    check_resources
    
    echo "✅ 所有健康檢查通過"
    exit 0
}

# 執行健康檢查
main "$@"
```

---

### Step 3: 環境配置管理 (Priority 2)
**時間:** 4 小時  
**風險:** 低  
**影響:** 中等

#### 3.1 創建環境配置文件
```bash
# 文件: .env.production

# =================================
# 生產環境配置
# =================================

# 環境標識
ENVIRONMENT=production

# 應用配置
LOG_LEVEL=INFO
API_WORKERS=2
API_MEMORY_LIMIT=2G
API_CPU_LIMIT=1.0
API_MEMORY_RESERVE=512M
API_CPU_RESERVE=0.5

# 外部端口
API_EXTERNAL_PORT=8080
POSTGRES_EXTERNAL_PORT=5432
MONGO_EXTERNAL_PORT=27017
REDIS_EXTERNAL_PORT=6379

# PostgreSQL配置
POSTGRES_DB=netstack_db
POSTGRES_USER=netstack_user
POSTGRES_PASSWORD=SecureProductionPassword123!
POSTGRES_WAIT_TIMEOUT=30

# MongoDB配置
MONGO_ROOT_USER=admin
MONGO_ROOT_PASSWORD=SecureMongoPassword123!
MONGO_DB=open5gs

# Redis配置
REDIS_PASSWORD=SecureRedisPassword123!

# 衛星系統配置
SATELLITE_DATA_MODE=instant_load
PRECOMPUTE_ON_STARTUP=true

# Docker映像標籤
IMAGE_TAG=latest
```

```bash
# 文件: .env.development

# =================================
# 開發環境配置
# =================================

# 環境標識
ENVIRONMENT=development

# 應用配置
LOG_LEVEL=DEBUG
API_WORKERS=1
API_MEMORY_LIMIT=1G
API_CPU_LIMIT=0.5

# 外部端口 (避免與生產衝突)
API_EXTERNAL_PORT=8081
POSTGRES_EXTERNAL_PORT=5433
MONGO_EXTERNAL_PORT=27018
REDIS_EXTERNAL_PORT=6380

# PostgreSQL配置 (開發用)
POSTGRES_DB=netstack_dev_db
POSTGRES_USER=dev_user
POSTGRES_PASSWORD=dev_password
POSTGRES_WAIT_TIMEOUT=15

# MongoDB配置 (開發用)
MONGO_ROOT_USER=dev_admin
MONGO_ROOT_PASSWORD=dev_password
MONGO_DB=open5gs_dev

# Redis配置 (無密碼)
REDIS_PASSWORD=

# 衛星系統配置 (輕量化)
SATELLITE_DATA_MODE=simple_load
PRECOMPUTE_ON_STARTUP=false

# Docker映像標籤
IMAGE_TAG=dev
```

```bash
# 文件: .env.testing

# =================================
# 測試環境配置
# =================================

# 環境標識
ENVIRONMENT=testing

# 應用配置
LOG_LEVEL=WARNING
API_WORKERS=1

# 外部端口 (測試專用)
API_EXTERNAL_PORT=8082
POSTGRES_EXTERNAL_PORT=5434
MONGO_EXTERNAL_PORT=27019
REDIS_EXTERNAL_PORT=6381

# PostgreSQL配置 (測試用)
POSTGRES_DB=netstack_test_db
POSTGRES_USER=test_user
POSTGRES_PASSWORD=test_password

# MongoDB配置 (測試用)
MONGO_ROOT_USER=test_admin
MONGO_ROOT_PASSWORD=test_password
MONGO_DB=open5gs_test

# Redis配置 (測試專用)
REDIS_PASSWORD=test_redis

# 衛星系統配置 (最小化)
SATELLITE_DATA_MODE=simple_load
PRECOMPUTE_ON_STARTUP=false

# Docker映像標籤
IMAGE_TAG=test
```

#### 3.2 創建部署自動化腳本
```bash
# 文件: docker/scripts/deploy.sh

#!/bin/bash
set -e

# =====================================
# NetStack 統一部署腳本
# =====================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENVIRONMENT=${1:-development}
ACTION=${2:-up}

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函數: 彩色輸出
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# 函數: 顯示幫助信息
show_help() {
    echo "NetStack 部署腳本"
    echo ""
    echo "使用方法:"
    echo "  $0 [environment] [action]"
    echo ""
    echo "環境:"
    echo "  development (預設)  - 開發環境"
    echo "  production          - 生產環境"
    echo "  testing             - 測試環境"
    echo ""
    echo "動作:"
    echo "  up (預設)           - 啟動服務"
    echo "  down                - 停止服務"
    echo "  restart             - 重啟服務"
    echo "  build               - 重新建置映像"
    echo "  logs                - 查看日誌"
    echo "  status              - 檢查服務狀態"
    echo "  health              - 健康檢查"
    echo "  clean               - 清理資源"
    echo ""
    echo "範例:"
    echo "  $0                          # 啟動開發環境"
    echo "  $0 production up            # 啟動生產環境"
    echo "  $0 development build        # 建置開發映像"
    echo "  $0 production health        # 生產環境健康檢查"
}

# 函數: 驗證環境
validate_environment() {
    local env=$1
    case $env in
        development|production|testing)
            return 0
            ;;
        *)
            log_error "不支援的環境: $env"
            log_info "支援的環境: development, production, testing"
            exit 1
            ;;
    esac
}

# 函數: 載入環境配置
load_environment() {
    local env=$1
    local env_file="$PROJECT_ROOT/.env.$env"
    
    if [ -f "$env_file" ]; then
        log_info "載入環境配置: $env_file"
        export $(grep -v '^#' "$env_file" | grep -v '^$' | xargs)
        log_success "環境配置載入完成"
    else
        log_error "環境配置文件不存在: $env_file"
        exit 1
    fi
}

# 函數: 檢查先決條件
check_prerequisites() {
    log_info "檢查先決條件..."
    
    # 檢查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安裝"
        exit 1
    fi
    
    # 檢查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安裝"
        exit 1
    fi
    
    # 檢查項目結構
    local required_dirs=("docker/compose" "netstack" "netstack/config")
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$PROJECT_ROOT/$dir" ]; then
            log_error "必要目錄不存在: $dir"
            exit 1
        fi
    done
    
    log_success "先決條件檢查通過"
}

# 函數: 建置映像
build_images() {
    local env=$1
    log_info "建置 $env 環境映像..."
    
    cd "$PROJECT_ROOT"
    
    # 建置應用映像
    docker build \
        -f docker/Dockerfile \
        --target production \
        --build-arg ENVIRONMENT="$env" \
        -t "netstack-api:$env" \
        -t "netstack-api:latest" \
        .
    
    log_success "映像建置完成"
}

# 函數: 啟動服務
start_services() {
    local env=$1
    log_info "啟動 $env 環境服務..."
    
    cd "$PROJECT_ROOT"
    
    # 1. 啟動基礎設施
    log_info "啟動基礎設施服務..."
    docker-compose -f docker/compose/docker-compose.base.yaml up -d
    
    # 等待基礎設施就緒
    log_info "等待基礎設施就緒..."
    sleep 10
    
    # 檢查基礎設施健康
    local retries=0
    local max_retries=30
    while [ $retries -lt $max_retries ]; do
        if docker-compose -f docker/compose/docker-compose.base.yaml exec -T postgres pg_isready -q; then
            log_success "PostgreSQL就緒"
            break
        fi
        retries=$((retries + 1))
        log_info "等待PostgreSQL... ($retries/$max_retries)"
        sleep 2
    done
    
    if [ $retries -ge $max_retries ]; then
        log_error "PostgreSQL未能及時就緒"
        exit 1
    fi
    
    # 2. 啟動應用服務
    log_info "啟動應用服務..."
    docker-compose -f docker/compose/docker-compose.apps.yaml up -d
    
    log_success "服務啟動完成"
}

# 函數: 停止服務
stop_services() {
    local env=$1
    log_info "停止 $env 環境服務..."
    
    cd "$PROJECT_ROOT"
    
    # 停止應用服務
    docker-compose -f docker/compose/docker-compose.apps.yaml down
    
    # 停止基礎設施
    docker-compose -f docker/compose/docker-compose.base.yaml down
    
    log_success "服務停止完成"
}

# 函數: 重啟服務
restart_services() {
    local env=$1
    log_info "重啟 $env 環境服務..."
    
    stop_services "$env"
    sleep 5
    start_services "$env"
    
    log_success "服務重啟完成"
}

# 函數: 查看服務狀態
show_status() {
    local env=$1
    log_info "$env 環境服務狀態:"
    
    cd "$PROJECT_ROOT"
    
    echo ""
    echo "基礎設施服務:"
    docker-compose -f docker/compose/docker-compose.base.yaml ps
    
    echo ""
    echo "應用服務:"
    docker-compose -f docker/compose/docker-compose.apps.yaml ps
}

# 函數: 健康檢查
health_check() {
    local env=$1
    log_info "執行 $env 環境健康檢查..."
    
    local api_url="http://localhost:${API_EXTERNAL_PORT:-8080}"
    local health_endpoint="/health"
    
    # API健康檢查
    log_info "檢查API健康狀態..."
    if curl -f -s "$api_url$health_endpoint" > /dev/null; then
        log_success "API健康檢查通過"
    else
        log_error "API健康檢查失敗"
        return 1
    fi
    
    # 容器健康檢查
    log_info "檢查容器健康狀態..."
    local unhealthy_containers=$(docker ps --filter "health=unhealthy" -q | wc -l)
    if [ "$unhealthy_containers" -eq 0 ]; then
        log_success "所有容器健康狀態正常"
    else
        log_error "發現 $unhealthy_containers 個不健康的容器"
        docker ps --filter "health=unhealthy"
        return 1
    fi
    
    log_success "健康檢查完成"
}

# 函數: 查看日誌
show_logs() {
    local env=$1
    log_info "顯示 $env 環境日誌..."
    
    cd "$PROJECT_ROOT"
    
    # 顯示應用服務日誌
    docker-compose -f docker/compose/docker-compose.apps.yaml logs -f
}

# 函數: 清理資源
clean_resources() {
    local env=$1
    log_warning "清理 $env 環境資源..."
    
    read -p "確定要清理所有資源嗎？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$PROJECT_ROOT"
        
        # 停止並移除所有容器
        docker-compose -f docker/compose/docker-compose.apps.yaml down -v
        docker-compose -f docker/compose/docker-compose.base.yaml down -v
        
        # 清理映像
        docker image prune -f
        
        # 清理Volume (可選)
        read -p "是否也清理數據Volume？(y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker volume prune -f
            log_success "數據Volume已清理"
        fi
        
        log_success "資源清理完成"
    else
        log_info "清理操作已取消"
    fi
}

# 主函數
main() {
    # 顯示幫助
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_help
        exit 0
    fi
    
    # 驗證參數
    validate_environment "$ENVIRONMENT"
    
    log_info "NetStack部署腳本啟動"
    log_info "環境: $ENVIRONMENT"
    log_info "動作: $ACTION"
    
    # 載入環境配置
    load_environment "$ENVIRONMENT"
    
    # 檢查先決條件
    check_prerequisites
    
    # 執行對應動作
    case $ACTION in
        up)
            start_services "$ENVIRONMENT"
            ;;
        down)
            stop_services "$ENVIRONMENT"
            ;;
        restart)
            restart_services "$ENVIRONMENT"
            ;;
        build)
            build_images "$ENVIRONMENT"
            ;;
        logs)
            show_logs "$ENVIRONMENT"
            ;;
        status)
            show_status "$ENVIRONMENT"
            ;;
        health)
            health_check "$ENVIRONMENT"
            ;;
        clean)
            clean_resources "$ENVIRONMENT"
            ;;
        *)
            log_error "不支援的動作: $ACTION"
            show_help
            exit 1
            ;;
    esac
    
    log_success "部署腳本執行完成"
}

# 執行主函數
main "$@"
```

---

### Step 4: 驗證與測試 (Priority 1)
**時間:** 6 小時  
**風險:** 低  
**影響:** 高

#### 4.1 部署驗證測試
```bash
#!/bin/bash
# 文件: docker/scripts/validate-deployment.sh

set -e

echo "🧪 部署驗證測試開始..."

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_RESULTS=()

# 函數: 執行測試並記錄結果
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo ""
    echo "🔍 執行測試: $test_name"
    
    if eval "$test_command"; then
        echo "✅ $test_name - 通過"
        TEST_RESULTS+=("✅ $test_name")
        return 0
    else
        echo "❌ $test_name - 失敗"
        TEST_RESULTS+=("❌ $test_name")
        return 1
    fi
}

# 測試1: 環境配置驗證
test_env_config() {
    local env=${1:-development}
    local env_file="$PROJECT_ROOT/.env.$env"
    
    # 檢查環境文件存在
    [ -f "$env_file" ] || return 1
    
    # 檢查必要配置項
    local required_vars=(
        "ENVIRONMENT"
        "POSTGRES_DB"
        "POSTGRES_USER"
        "POSTGRES_PASSWORD"
        "API_EXTERNAL_PORT"
    )
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" "$env_file"; then
            echo "缺少配置項: $var"
            return 1
        fi
    done
    
    return 0
}

# 測試2: Docker Compose文件語法
test_compose_syntax() {
    cd "$PROJECT_ROOT"
    
    # 檢查基礎設施compose
    docker-compose -f docker/compose/docker-compose.base.yaml config > /dev/null || return 1
    
    # 檢查應用compose
    docker-compose -f docker/compose/docker-compose.apps.yaml config > /dev/null || return 1
    
    return 0
}

# 測試3: Docker建置測試
test_docker_build() {
    cd "$PROJECT_ROOT"
    
    # 建置生產映像
    docker build -f docker/Dockerfile --target production -t netstack-api:test . || return 1
    
    # 檢查映像是否創建成功
    docker images netstack-api:test | grep -q netstack-api || return 1
    
    return 0
}

# 測試4: 容器啟動測試
test_container_startup() {
    cd "$PROJECT_ROOT"
    
    # 載入測試環境
    export $(grep -v '^#' .env.testing | xargs)
    
    # 啟動基礎設施
    docker-compose -f docker/compose/docker-compose.base.yaml up -d
    
    # 等待基礎設施就緒
    local retries=0
    while [ $retries -lt 30 ]; do
        if docker-compose -f docker/compose/docker-compose.base.yaml exec -T postgres pg_isready -q; then
            break
        fi
        retries=$((retries + 1))
        sleep 2
    done
    
    [ $retries -lt 30 ] || return 1
    
    # 啟動應用服務  
    docker-compose -f docker/compose/docker-compose.apps.yaml up -d
    
    # 等待應用就緒
    local api_port=${API_EXTERNAL_PORT:-8082}
    retries=0
    while [ $retries -lt 30 ]; do
        if curl -f -s "http://localhost:$api_port/health" > /dev/null; then
            break
        fi
        retries=$((retries + 1))
        sleep 3
    done
    
    [ $retries -lt 30 ] || return 1
    
    return 0
}

# 測試5: API功能測試
test_api_functionality() {
    local api_port=${API_EXTERNAL_PORT:-8082}
    
    # 健康檢查端點
    curl -f -s "http://localhost:$api_port/health" | grep -q "healthy\|ok" || return 1
    
    # 衛星端點測試
    curl -f -s "http://localhost:$api_port/api/v1/satellites/constellations/info" > /dev/null || return 1
    
    return 0
}

# 測試6: 資源使用測試
test_resource_usage() {
    # 檢查記憶體使用
    local memory_usage=$(docker stats --no-stream netstack-api | awk 'NR==2{print $4}' | sed 's/%//')
    [ $(echo "$memory_usage < 80" | bc) -eq 1 ] || return 1
    
    # 檢查CPU使用
    local cpu_usage=$(docker stats --no-stream netstack-api | awk 'NR==2{print $3}' | sed 's/%//')
    [ $(echo "$cpu_usage < 90" | bc) -eq 1 ] || return 1
    
    return 0
}

# 清理測試環境
cleanup_test_env() {
    echo ""
    echo "🧹 清理測試環境..."
    
    cd "$PROJECT_ROOT"
    
    # 停止測試容器
    docker-compose -f docker/compose/docker-compose.apps.yaml down -v 2>/dev/null || true
    docker-compose -f docker/compose/docker-compose.base.yaml down -v 2>/dev/null || true
    
    # 清理測試映像
    docker rmi netstack-api:test 2>/dev/null || true
    
    echo "✅ 測試環境清理完成"
}

# 主測試流程
main() {
    echo "開始部署驗證測試..."
    
    # 設置陷阱以清理環境
    trap cleanup_test_env EXIT
    
    # 執行所有測試
    run_test "環境配置驗證" "test_env_config testing"
    run_test "Docker Compose語法檢查" "test_compose_syntax"
    run_test "Docker映像建置" "test_docker_build"
    run_test "容器啟動測試" "test_container_startup"
    run_test "API功能測試" "test_api_functionality"
    run_test "資源使用測試" "test_resource_usage"
    
    # 測試結果總結
    echo ""
    echo "📊 測試結果總結:"
    echo "===================="
    for result in "${TEST_RESULTS[@]}"; do
        echo "$result"
    done
    
    # 計算通過率
    local total_tests=${#TEST_RESULTS[@]}
    local passed_tests=$(echo "${TEST_RESULTS[@]}" | grep -o "✅" | wc -l)
    local pass_rate=$((passed_tests * 100 / total_tests))
    
    echo ""
    echo "通過率: $passed_tests/$total_tests ($pass_rate%)"
    
    if [ $pass_rate -eq 100 ]; then
        echo "🎉 所有測試通過！部署配置正確"
        exit 0
    else
        echo "💥 部分測試失敗，請檢查配置"
        exit 1
    fi
}

# 執行主程序
main "$@"
```

## 📈 預期效果與成功指標

### 部署效率提升
- **首次部署時間:** 15-20分鐘 → 5-8分鐘
- **增量部署時間:** 10-15分鐘 → 2-3分鐘  
- **映像大小:** 2GB → 800MB
- **建置快取命中率:** 20% → 80%

### 可靠性提升
- **部署成功率:** 70% → 95%
- **容器啟動失敗率:** 30% → <5%
- **配置錯誤率:** 25% → <3%

### 維護成本降低
- **環境配置維護:** 2x → 1x (統一配置)
- **問題排查時間:** 2-4小時 → 30分鐘
- **新環境建立時間:** 4-6小時 → 1小時

---

**部署優化執行計劃**  
*總執行時間: 24 小時*  
*建議執行期: 3-4 工作天*  
*優先級: 高 - 提升系統可靠性的關鍵*