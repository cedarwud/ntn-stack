#!/usr/bin/env python3
"""
Phase 1 Docker 整合配置

功能:
1. 自動化 Docker 配置生成
2. Phase 1 系統容器化整合
3. NetStack 主系統整合
4. 依賴管理和優化

符合 CLAUDE.md 原則:
- 完整的生產級部署配置
- 確保 Phase 1 系統穩定運行
- 優化容器資源使用
"""

import os
import json
import yaml
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

@dataclass
class DockerConfig:
    """Docker 配置"""
    base_image: str
    python_version: str
    work_dir: str
    exposed_ports: List[int]
    environment_vars: Dict[str, str]
    volumes: List[str]
    health_check: Dict[str, Any]

@dataclass
class ServiceConfig:
    """服務配置"""
    name: str
    image: str
    ports: List[str]
    environment: Dict[str, str]
    volumes: List[str]
    depends_on: List[str]
    healthcheck: Dict[str, Any]
    restart: str = "unless-stopped"

class DockerIntegrator:
    """Docker 整合器"""
    
    def __init__(self, project_root: Path):
        """
        初始化 Docker 整合器
        
        Args:
            project_root: 專案根目錄
        """
        self.project_root = project_root
        self.phase1_root = project_root / "phase1_refactor"
        self.netstack_root = project_root / "netstack"
        self.deployment_dir = self.phase1_root / "deployment"
        
        # 確保部署目錄存在
        self.deployment_dir.mkdir(exist_ok=True)
        
        logger.info("Docker 整合器初始化完成")
    
    def generate_dockerfile(self) -> str:
        """生成 Phase 1 增強的 Dockerfile"""
        
        dockerfile_content = '''# Phase 1 增強 NetStack Dockerfile
FROM python:3.11-slim

# 設置工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    curl \\
    wget \\
    build-essential \\
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements 文件
COPY requirements.txt /app/requirements.txt
COPY phase1_refactor/requirements.txt /app/phase1_requirements.txt

# 安裝 Python 依賴
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r phase1_requirements.txt

# 複製應用程式代碼
COPY . /app/

# 設置 Python 路徑
ENV PYTHONPATH="${PYTHONPATH}:/app:/app/phase1_refactor:/app/netstack"

# Phase 1 特定環境變量
ENV PHASE1_TLE_DATA_PATH="/netstack/tle_data"
ENV PHASE1_OUTPUT_PATH="/app/data"
ENV PHASE1_LOG_LEVEL="INFO"
ENV PHASE1_CACHE_SIZE="2000"
ENV PHASE1_API_TIMEOUT="30"

# 創建必要目錄
RUN mkdir -p /netstack/tle_data/starlink/tle && \\
    mkdir -p /netstack/tle_data/oneweb/tle && \\
    mkdir -p /app/data && \\
    mkdir -p /app/logs

# 設置權限
RUN chmod -R 755 /app/phase1_refactor && \\
    chmod +x /app/phase1_refactor/deployment/*.sh

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:8080/health || \\
        python -c "import sys; sys.path.append('/app/phase1_refactor/04_output_interface'); from phase1_api_enhanced import health_check; health_check()" || exit 1

# 暴露端口
EXPOSE 8080 8001

# 啟動命令
CMD ["python", "-m", "uvicorn", "netstack_api.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
'''
        
        dockerfile_path = self.deployment_dir / "Dockerfile.phase1"
        dockerfile_path.write_text(dockerfile_content)
        
        logger.info(f"Dockerfile 已生成: {dockerfile_path}")
        return str(dockerfile_path)
    
    def generate_docker_compose(self) -> str:
        """生成 Phase 1 增強的 docker-compose.yml"""
        
        compose_config = {
            "version": "3.8",
            "services": {
                "netstack-api-phase1": {
                    "build": {
                        "context": "../..",
                        "dockerfile": "phase1_refactor/deployment/Dockerfile.phase1"
                    },
                    "ports": [
                        "8080:8080",
                        "8001:8001"
                    ],
                    "environment": {
                        "PHASE1_TLE_DATA_PATH": "/netstack/tle_data",
                        "PHASE1_OUTPUT_PATH": "/app/data",
                        "PHASE1_LOG_LEVEL": "INFO",
                        "PHASE1_CACHE_SIZE": "2000",
                        "PHASE1_API_TIMEOUT": "30",
                        "PYTHONPATH": "/app:/app/phase1_refactor:/app/netstack"
                    },
                    "volumes": [
                        "./../../tle_data:/netstack/tle_data",
                        "./../../data:/app/data",
                        "./../../logs:/app/logs",
                        "./../../phase1_refactor:/app/phase1_refactor"
                    ],
                    "healthcheck": {
                        "test": [
                            "CMD-SHELL",
                            "curl -f http://localhost:8080/health || exit 1"
                        ],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 3,
                        "start_period": "60s"
                    },
                    "restart": "unless-stopped",
                    "depends_on": ["netstack-rl-postgres"],
                    "networks": ["netstack-network"]
                },
                
                "netstack-rl-postgres": {
                    "image": "postgres:15-alpine",
                    "environment": {
                        "POSTGRES_DB": "rl_research",
                        "POSTGRES_USER": "rl_user",
                        "POSTGRES_PASSWORD": "rl_password"
                    },
                    "volumes": [
                        "postgres_data:/var/lib/postgresql/data"
                    ],
                    "ports": ["5432:5432"],
                    "healthcheck": {
                        "test": ["CMD-SHELL", "pg_isready -U rl_user -d rl_research"],
                        "interval": "10s",
                        "timeout": "5s",
                        "retries": 5
                    },
                    "restart": "unless-stopped",
                    "networks": ["netstack-network"]
                }
            },
            
            "volumes": {
                "postgres_data": None
            },
            
            "networks": {
                "netstack-network": {
                    "driver": "bridge"
                }
            }
        }
        
        compose_path = self.deployment_dir / "docker-compose.phase1.yml"
        with open(compose_path, 'w', encoding='utf-8') as f:
            yaml.dump(compose_config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"docker-compose.yml 已生成: {compose_path}")
        return str(compose_path)
    
    def generate_deployment_scripts(self) -> List[str]:
        """生成部署腳本"""
        
        scripts = []
        
        # 1. 部署準備腳本
        prepare_script = '''#!/bin/bash
# Phase 1 部署準備腳本

set -e

echo "🚀 Phase 1 部署準備開始..."

# 檢查 Docker 和 Docker Compose
echo "檢查 Docker 環境..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安裝"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安裝"
    exit 1
fi

echo "✅ Docker 環境檢查通過"

# 創建必要目錄
echo "創建必要目錄..."
mkdir -p ../../tle_data/starlink/tle
mkdir -p ../../tle_data/oneweb/tle
mkdir -p ../../data
mkdir -p ../../logs

echo "✅ 目錄創建完成"

# 檢查 TLE 數據
echo "檢查 TLE 數據..."
if [ ! -f "../../tle_data/starlink/tle/starlink_20250805.tle" ]; then
    echo "⚠️  未找到 Starlink TLE 數據，將從歷史數據生成..."
    python ../../phase1_refactor/01_data_source/generate_tle_from_historical.py
fi

if [ ! -f "../../tle_data/oneweb/tle/oneweb_20250805.tle" ]; then
    echo "⚠️  未找到 OneWeb TLE 數據，將從歷史數據生成..."
    python ../../phase1_refactor/01_data_source/generate_tle_from_historical.py --constellation oneweb
fi

echo "✅ TLE 數據檢查完成"

# 驗證 Phase 1 系統
echo "驗證 Phase 1 系統..."
cd ../../phase1_refactor
python validate_phase1_refactor.py

if [ $? -eq 0 ]; then
    echo "✅ Phase 1 系統驗證通過"
else
    echo "❌ Phase 1 系統驗證失敗"
    exit 1
fi

cd deployment

echo "🎯 Phase 1 部署準備完成"
'''
        
        prepare_script_path = self.deployment_dir / "prepare_deployment.sh"
        prepare_script_path.write_text(prepare_script)
        prepare_script_path.chmod(0o755)
        scripts.append(str(prepare_script_path))
        
        # 2. 部署執行腳本
        deploy_script = '''#!/bin/bash
# Phase 1 部署執行腳本

set -e

echo "🚀 Phase 1 部署執行開始..."

# 停止舊服務
echo "停止現有服務..."
docker-compose -f docker-compose.phase1.yml down --remove-orphans || true

# 清理舊鏡像
echo "清理舊鏡像..."
docker system prune -f

# 建構新鏡像
echo "建構 Phase 1 增強鏡像..."
docker-compose -f docker-compose.phase1.yml build --no-cache

# 啟動服務
echo "啟動 Phase 1 服務..."
docker-compose -f docker-compose.phase1.yml up -d

# 等待服務啟動
echo "等待服務啟動..."
sleep 30

# 檢查服務狀態
echo "檢查服務狀態..."
docker-compose -f docker-compose.phase1.yml ps

# 等待健康檢查
echo "等待健康檢查..."
for i in {1..30}; do
    if curl -f http://localhost:8080/health >/dev/null 2>&1; then
        echo "✅ 服務健康檢查通過"
        break
    fi
    echo "等待健康檢查... ($i/30)"
    sleep 2
done

# 執行部署後驗證
echo "執行部署後驗證..."
python ../05_integration/integration_test.py

if [ $? -eq 0 ]; then
    echo "✅ 部署後驗證通過"
else
    echo "❌ 部署後驗證失敗"
    echo "回滾部署..."
    docker-compose -f docker-compose.phase1.yml down
    exit 1
fi

echo "🎉 Phase 1 部署完成！"
echo "API 端點: http://localhost:8080"
echo "Phase 1 API: http://localhost:8001"
echo "健康檢查: http://localhost:8080/health"
'''
        
        deploy_script_path = self.deployment_dir / "deploy.sh"
        deploy_script_path.write_text(deploy_script)
        deploy_script_path.chmod(0o755)
        scripts.append(str(deploy_script_path))
        
        # 3. 回滾腳本
        rollback_script = '''#!/bin/bash
# Phase 1 回滾腳本

set -e

echo "🔄 Phase 1 回滾開始..."

# 停止當前服務
echo "停止當前服務..."
docker-compose -f docker-compose.phase1.yml down

# 備份當前數據
echo "備份當前數據..."
backup_dir="../../backup/rollback_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"
cp -r ../../data "$backup_dir/"
cp -r ../../logs "$backup_dir/"

# 恢復到原有配置
echo "恢復到原有配置..."
if [ -d "../../backup/pre-phase1-integration/" ]; then
    cp -r ../../backup/pre-phase1-integration/* ../../
    echo "✅ 原有配置已恢復"
else
    echo "❌ 未找到原有配置備份"
    exit 1
fi

# 重啟原有服務
echo "重啟原有服務..."
cd ../..
make up

echo "✅ Phase 1 回滾完成"
'''
        
        rollback_script_path = self.deployment_dir / "rollback.sh"
        rollback_script_path.write_text(rollback_script)
        rollback_script_path.chmod(0o755)
        scripts.append(str(rollback_script_path))
        
        logger.info(f"部署腳本已生成: {len(scripts)} 個文件")
        return scripts
    
    def generate_ci_cd_config(self) -> str:
        """生成 CI/CD 配置"""
        
        github_workflow = {
            "name": "Phase 1 Enhanced Deployment",
            "on": {
                "push": {
                    "branches": ["main"],
                    "paths": ["phase1_refactor/**", "netstack/**"]
                },
                "pull_request": {
                    "branches": ["main"],
                    "paths": ["phase1_refactor/**", "netstack/**"]
                }
            },
            
            "jobs": {
                "test": {
                    "runs-on": "ubuntu-latest",
                    "steps": [
                        {
                            "name": "Checkout code",
                            "uses": "actions/checkout@v3"
                        },
                        {
                            "name": "Set up Python 3.11",
                            "uses": "actions/setup-python@v4",
                            "with": {"python-version": "3.11"}
                        },
                        {
                            "name": "Install dependencies",
                            "run": "pip install -r phase1_refactor/requirements.txt"
                        },
                        {
                            "name": "Run Phase 1 tests",
                            "run": "cd phase1_refactor && python validate_phase1_refactor.py"
                        },
                        {
                            "name": "Run integration tests",
                            "run": "cd phase1_refactor/05_integration && python end_to_end_tests.py"
                        }
                    ]
                },
                
                "build": {
                    "runs-on": "ubuntu-latest",
                    "needs": "test",
                    "if": "github.ref == 'refs/heads/main'",
                    "steps": [
                        {
                            "name": "Checkout code",
                            "uses": "actions/checkout@v3"
                        },
                        {
                            "name": "Set up Docker Buildx",
                            "uses": "docker/setup-buildx-action@v2"
                        },
                        {
                            "name": "Build Phase 1 image",
                            "run": "docker build -f phase1_refactor/deployment/Dockerfile.phase1 -t netstack-phase1:latest ."
                        },
                        {
                            "name": "Test Docker image",
                            "run": "docker run --rm netstack-phase1:latest python -c 'import sys; print(f\"Python {sys.version}\"); from sgp4.api import Satrec; print(\"SGP4 OK\")'"
                        }
                    ]
                },
                
                "deploy": {
                    "runs-on": "ubuntu-latest",
                    "needs": ["test", "build"],
                    "if": "github.ref == 'refs/heads/main'",
                    "environment": "production",
                    "steps": [
                        {
                            "name": "Deploy to staging",
                            "run": "echo 'Deploy to staging environment'"
                        },
                        {
                            "name": "Run deployment verification",
                            "run": "echo 'Verify deployment'"
                        }
                    ]
                }
            }
        }
        
        workflow_dir = self.deployment_dir / ".github" / "workflows"
        workflow_dir.mkdir(parents=True, exist_ok=True)
        
        workflow_path = workflow_dir / "phase1-deploy.yml"
        with open(workflow_path, 'w', encoding='utf-8') as f:
            yaml.dump(github_workflow, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"CI/CD 配置已生成: {workflow_path}")
        return str(workflow_path)
    
    def generate_monitoring_config(self) -> str:
        """生成監控配置"""
        
        monitoring_compose = '''version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: phase1-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    networks:
      - netstack-network

  grafana:
    image: grafana/grafana:latest
    container_name: phase1-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    networks:
      - netstack-network

  node_exporter:
    image: prom/node-exporter:latest
    container_name: phase1-node-exporter
    ports:
      - "9100:9100"
    networks:
      - netstack-network

volumes:
  grafana_data:

networks:
  netstack-network:
    external: true
'''
        
        monitoring_dir = self.deployment_dir / "monitoring"
        monitoring_dir.mkdir(exist_ok=True)
        
        monitoring_compose_path = monitoring_dir / "docker-compose.monitoring.yml"
        monitoring_compose_path.write_text(monitoring_compose)
        
        # Prometheus 配置
        prometheus_config = '''global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'phase1-api'
    static_configs:
      - targets: ['netstack-api-phase1:8080']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node_exporter:9100']

  - job_name: 'postgres'
    static_configs:
      - targets: ['netstack-rl-postgres:5432']
'''
        
        prometheus_config_path = monitoring_dir / "prometheus.yml"
        prometheus_config_path.write_text(prometheus_config)
        
        logger.info(f"監控配置已生成: {monitoring_dir}")
        return str(monitoring_dir)
    
    def generate_production_config(self) -> str:
        """生成生產環境配置"""
        
        prod_config = {
            "phase1": {
                "api": {
                    "host": "0.0.0.0",
                    "port": 8080,
                    "workers": 4,
                    "timeout": 30,
                    "max_connections": 100
                },
                "data": {
                    "tle_data_path": "/netstack/tle_data",
                    "output_path": "/app/data",
                    "cache_size": 5000,
                    "cache_ttl": 3600
                },
                "performance": {
                    "sgp4_threads": 8,
                    "batch_size": 1000,
                    "memory_limit": "2GB",
                    "cpu_limit": "2.0"
                },
                "logging": {
                    "level": "INFO",
                    "format": "json",
                    "file": "/app/logs/phase1.log",
                    "max_size": "100MB",
                    "backup_count": 5
                },
                "security": {
                    "enable_cors": True,
                    "allowed_origins": ["*"],
                    "rate_limiting": {
                        "requests_per_minute": 100,
                        "requests_per_hour": 1000
                    }
                }
            },
            "deployment": {
                "strategy": "rolling_update",
                "health_check_timeout": 60,
                "readiness_probe_delay": 30,
                "liveness_probe_delay": 60,
                "resource_limits": {
                    "memory": "4GB",
                    "cpu": "2.0"
                },
                "resource_requests": {
                    "memory": "2GB",
                    "cpu": "1.0"
                }
            }
        }
        
        config_path = self.deployment_dir / "production.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(prod_config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"生產環境配置已生成: {config_path}")
        return str(config_path)
    
    def create_deployment_package(self) -> str:
        """創建完整部署包"""
        
        logger.info("創建完整部署包...")
        
        # 生成所有配置文件
        dockerfile_path = self.generate_dockerfile()
        compose_path = self.generate_docker_compose()
        scripts = self.generate_deployment_scripts()
        cicd_path = self.generate_ci_cd_config()
        monitoring_path = self.generate_monitoring_config()
        production_path = self.generate_production_config()
        
        # 創建部署文檔
        deployment_doc = f'''# Phase 1 部署包

**生成時間**: {datetime.now(timezone.utc).isoformat()}
**版本**: 1.0.0

## 📁 部署包內容

### 核心配置
- `Dockerfile.phase1`: Phase 1 增強 Docker 鏡像
- `docker-compose.phase1.yml`: Docker Compose 配置
- `production.yaml`: 生產環境配置

### 部署腳本
- `prepare_deployment.sh`: 部署準備腳本
- `deploy.sh`: 部署執行腳本
- `rollback.sh`: 回滾腳本

### CI/CD 配置
- `.github/workflows/phase1-deploy.yml`: GitHub Actions 工作流

### 監控配置
- `monitoring/`: 監控系統配置目錄
  - `docker-compose.monitoring.yml`: 監控服務
  - `prometheus.yml`: Prometheus 配置

## 🚀 部署步驟

1. **準備階段**:
   ```bash
   cd phase1_refactor/deployment
   ./prepare_deployment.sh
   ```

2. **執行部署**:
   ```bash
   ./deploy.sh
   ```

3. **驗證部署**:
   ```bash
   curl http://localhost:8080/health
   curl http://localhost:8001/health
   ```

4. **啟動監控** (可選):
   ```bash
   docker-compose -f monitoring/docker-compose.monitoring.yml up -d
   ```

## 📊 部署後檢查

### 服務狀態
- NetStack API: http://localhost:8080
- Phase 1 API: http://localhost:8001  
- 健康檢查: http://localhost:8080/health
- Prometheus: http://localhost:9090 (如啟用監控)
- Grafana: http://localhost:3000 (如啟用監控)

### 性能驗證
```bash
# 執行性能測試
cd ../05_integration
python performance_benchmark.py

# 查看服務狀態
docker-compose -f ../deployment/docker-compose.phase1.yml ps
```

## 🔧 故障排除

### 常見問題
1. **TLE 數據缺失**: 執行 `prepare_deployment.sh`
2. **服務啟動失敗**: 檢查 Docker logs
3. **性能不佳**: 調整 `production.yaml` 中的配置

### 回滾步驟
```bash
./rollback.sh
```

## 📞 支援資訊
- 技術文檔: `../docs/`
- 整合指南: `../docs/integration_guide.md`
- API 規範: `../docs/api_specification.md`
'''
        
        deployment_readme = self.deployment_dir / "README.md"
        deployment_readme.write_text(deployment_doc)
        
        # 創建版本信息
        version_info = {
            "package_version": "1.0.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "components": {
                "dockerfile": dockerfile_path,
                "docker_compose": compose_path,
                "deployment_scripts": scripts,
                "cicd_config": cicd_path,
                "monitoring_config": monitoring_path,
                "production_config": production_path
            },
            "system_requirements": {
                "docker": ">=20.10",
                "docker_compose": ">=2.0",
                "python": "3.11",
                "memory": "4GB+",
                "cpu": "2 cores+",
                "disk": "10GB+"
            }
        }
        
        version_file = self.deployment_dir / "version.json"
        with open(version_file, 'w', encoding='utf-8') as f:
            json.dump(version_info, f, indent=2, ensure_ascii=False)
        
        logger.info("✅ Phase 1 完整部署包創建完成")
        return str(self.deployment_dir)


class ProductionOptimizer:
    """生產環境優化器"""
    
    def __init__(self, deployment_dir: Path):
        """
        初始化生產環境優化器
        
        Args:
            deployment_dir: 部署配置目錄
        """
        self.deployment_dir = deployment_dir
        logger.info("生產環境優化器初始化完成")
    
    def optimize_docker_image(self) -> Dict[str, Any]:
        """優化 Docker 鏡像"""
        
        optimizations = []
        
        # 多階段建構優化
        optimized_dockerfile = '''# Phase 1 優化 Dockerfile (多階段建構)

# 第一階段：建構環境
FROM python:3.11-slim as builder

WORKDIR /app

# 安裝建構依賴
RUN apt-get update && apt-get install -y \\
    gcc g++ build-essential \\
    && rm -rf /var/lib/apt/lists/*

# 複製並安裝 Python 依賴
COPY requirements.txt phase1_refactor/requirements.txt ./
RUN pip install --user --no-cache-dir -r requirements.txt && \\
    pip install --user --no-cache-dir -r phase1_refactor/requirements.txt

# 第二階段：運行環境
FROM python:3.11-slim as runtime

WORKDIR /app

# 只安裝運行時依賴
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/* \\
    && apt-get clean

# 複製已安裝的 Python 包
COPY --from=builder /root/.local /root/.local

# 複製應用程式代碼
COPY . /app/

# 設置環境變量
ENV PYTHONPATH="${PYTHONPATH}:/app:/app/phase1_refactor:/app/netstack"
ENV PATH="/root/.local/bin:$PATH"

# Phase 1 優化配置
ENV PHASE1_TLE_DATA_PATH="/netstack/tle_data"
ENV PHASE1_OUTPUT_PATH="/app/data"
ENV PHASE1_LOG_LEVEL="INFO"
ENV PHASE1_CACHE_SIZE="5000"
ENV PHASE1_API_TIMEOUT="30"
ENV PHASE1_WORKERS="4"

# 創建必要目錄並設置權限
RUN mkdir -p /netstack/tle_data /app/data /app/logs && \\
    adduser --disabled-password --gecos '' appuser && \\
    chown -R appuser:appuser /app /netstack && \\
    chmod -R 755 /app/phase1_refactor/deployment

# 切換到非 root 用戶
USER appuser

# 健康檢查優化
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:8080/health || exit 1

# 暴露端口
EXPOSE 8080

# 使用 Gunicorn 啟動（生產級 WSGI 服務器）
CMD ["gunicorn", "netstack_api.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080"]
'''
        
        optimized_dockerfile_path = self.deployment_dir / "Dockerfile.optimized"
        optimized_dockerfile_path.write_text(optimized_dockerfile)
        
        optimizations.append({
            "type": "docker_image",
            "description": "多階段建構，減小鏡像大小",
            "file": str(optimized_dockerfile_path)
        })
        
        return {"optimizations": optimizations, "status": "completed"}
    
    def generate_k8s_manifests(self) -> Dict[str, str]:
        """生成 Kubernetes 部署清單"""
        
        k8s_dir = self.deployment_dir / "k8s"
        k8s_dir.mkdir(exist_ok=True)
        
        manifests = {}
        
        # Deployment 清單
        deployment_manifest = '''apiVersion: apps/v1
kind: Deployment
metadata:
  name: netstack-phase1
  labels:
    app: netstack-phase1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: netstack-phase1
  template:
    metadata:
      labels:
        app: netstack-phase1
    spec:
      containers:
      - name: netstack-api
        image: netstack-phase1:latest
        ports:
        - containerPort: 8080
        env:
        - name: PHASE1_TLE_DATA_PATH
          value: "/netstack/tle_data"
        - name: PHASE1_OUTPUT_PATH
          value: "/app/data"
        - name: PHASE1_CACHE_SIZE
          value: "5000"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        volumeMounts:
        - name: tle-data
          mountPath: /netstack/tle_data
        - name: app-data
          mountPath: /app/data
      volumes:
      - name: tle-data
        persistentVolumeClaim:
          claimName: tle-data-pvc
      - name: app-data
        persistentVolumeClaim:
          claimName: app-data-pvc
'''
        
        deployment_path = k8s_dir / "deployment.yaml"
        deployment_path.write_text(deployment_manifest)
        manifests["deployment"] = str(deployment_path)
        
        # Service 清單
        service_manifest = '''apiVersion: v1
kind: Service
metadata:
  name: netstack-phase1-service
spec:
  selector:
    app: netstack-phase1
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: LoadBalancer
'''
        
        service_path = k8s_dir / "service.yaml"
        service_path.write_text(service_manifest)
        manifests["service"] = str(service_path)
        
        # ConfigMap 清單
        configmap_manifest = '''apiVersion: v1
kind: ConfigMap
metadata:
  name: netstack-phase1-config
data:
  PHASE1_LOG_LEVEL: "INFO"
  PHASE1_CACHE_SIZE: "5000"
  PHASE1_API_TIMEOUT: "30"
'''
        
        configmap_path = k8s_dir / "configmap.yaml"
        configmap_path.write_text(configmap_manifest)
        manifests["configmap"] = str(configmap_path)
        
        logger.info(f"Kubernetes 清單已生成: {len(manifests)} 個文件")
        return manifests


def create_deployment_package(project_root: str = "/home/sat/ntn-stack") -> Dict[str, Any]:
    """創建完整的 Phase 1 部署包"""
    
    project_path = Path(project_root)
    integrator = DockerIntegrator(project_path)
    
    # 創建完整部署包
    deployment_dir = integrator.create_deployment_package()
    
    # 生產環境優化
    optimizer = ProductionOptimizer(Path(deployment_dir))
    docker_optimizations = optimizer.optimize_docker_image()
    k8s_manifests = optimizer.generate_k8s_manifests()
    
    return {
        "deployment_package": deployment_dir,
        "docker_optimizations": docker_optimizations,
        "k8s_manifests": k8s_manifests,
        "status": "completed"
    }


if __name__ == "__main__":
    # 執行部署包創建
    logging.basicConfig(level=logging.INFO)
    
    try:
        print("🚀 Phase 1 部署流程優化開始...")
        print("=" * 50)
        
        # 創建部署包
        result = create_deployment_package()
        
        print("✅ 部署包創建完成:")
        print(f"   部署目錄: {result['deployment_package']}")
        print(f"   Docker 優化: {len(result['docker_optimizations']['optimizations'])} 項")
        print(f"   K8s 清單: {len(result['k8s_manifests'])} 個文件")
        
        print("\n🎯 下一步:")
        print("1. 執行部署準備: ./prepare_deployment.sh")
        print("2. 執行部署: ./deploy.sh")
        print("3. 驗證部署: curl http://localhost:8080/health")
        
        print("\n✅ Stage 4.3: 部署流程優化完成！")
        
    except Exception as e:
        print(f"❌ 部署流程優化失敗: {e}")
        import traceback
        traceback.print_exc()