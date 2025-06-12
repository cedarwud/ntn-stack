# Claude Code 項目環境說明

## 🐳 完整 Docker 多容器架構

**重要**: 這是一個完全容器化的微服務架構專案，包含兩個主要子系統，共運行約 20+ 個容器

### 架構概覽
```
NTN Stack
├── NetStack (5G 核心網)     - 約 15+ 容器
└── SimWorld (3D 仿真引擎)   - 3 個容器
```

## 🏗️ 系統架構

### 1. NetStack (5G 核心網系統)
**位置**: `/netstack/`  
**管理**: `netstack/Makefile`  
**網路**: `compose_netstack-core` (172.20.0.0/16)

**核心容器**:
- `netstack-mongo` (172.20.0.10) - MongoDB 資料庫
- `netstack-nrf` (172.20.0.23) - Network Repository Function
- `netstack-amf` (172.20.0.20) - Access and Mobility Management
- `netstack-smf` (172.20.0.27) - Session Management Function
- `netstack-upf` (172.20.0.30) - User Plane Function
- `netstack-api` (172.20.0.40) - NetStack API 服務
- `netstack-redis` (172.20.0.50) - Redis 快取
- `netstack-prometheus` (172.20.0.60) - 監控系統
- 其他 5G 核心網組件 (ausf, bsf, nssf, pcf, udm, udr)

### 2. SimWorld (3D 仿真引擎)
**位置**: `/simworld/`  
**管理**: `simworld/docker-compose.yml`  
**網路**: `sionna-net` + 跨網路連接到 `netstack-core`

**核心容器**:
- `simworld_backend` - FastAPI 後端 (Python 3.11, TensorFlow 2.19.0, Sionna 1.1.0)
- `simworld_frontend` - React 前端 (Node.js, TypeScript)
- `simworld_postgis` - PostgreSQL + PostGIS 資料庫

## 🚀 啟動順序 (重要!)

**必須按順序啟動**，因為有網路依賴關係：

```bash
# 根目錄統一管理
make up          # 啟動所有服務 (自動處理順序)
make down        # 停止所有服務
make status      # 檢查所有容器狀態
make logs        # 查看所有日誌

# 或分別管理
make netstack-start    # 先啟動 NetStack (創建網路)
make simworld-start    # 再啟動 SimWorld (連接網路)
```

## 🌐 跨容器網路連接

SimWorld 的 backend 容器會自動連接到 NetStack 的網路，實現服務間通信：

```yaml
# simworld backend 同時連接兩個網路
networks:
  sionna-net:           # SimWorld 內部網路
  netstack-core:        # NetStack 外部網路
    aliases:
      - simworld-backend
      - backend
```

## 🔧 開發環境指令

### Python 相關 (在 simworld_backend 容器內)
```bash
# 檢查套件版本
docker exec simworld_backend pip freeze | grep <package>

# 執行 Python 代碼
docker exec simworld_backend python -c "<code>"

# 測試 AI-RAN 服務
docker exec simworld_backend python -c "
from app.domains.interference.services.ai_ran_service import AIRANService
service = AIRANService()
print(f'AI available: {service.ai_available}')
"

# 進入容器 shell
docker exec -it simworld_backend bash
```

### 檢查網路連接
```bash
# 驗證跨服務連接
make verify-network-connection

# 手動修復網路問題
make fix-network-connection
```

### 容器狀態檢查
```bash
# 查看所有容器
docker ps

# 查看特定系統容器
docker ps | grep netstack
docker ps | grep simworld

# 查看容器日誌
docker logs simworld_backend
docker logs netstack-api
```

## 📦 套件版本 (容器內實際環境)

### SimWorld Backend Container
- **Python**: 3.11
- **TensorFlow**: 2.19.0 ✅ (完全可用)
- **Sionna**: 1.1.0 ✅ (最新版)
- **FastAPI**: 最新版
- **typing-extensions**: 4.14.0
- **Keras**: 3.10.0

### NetStack API Container  
- **Python**: 3.11
- **MongoDB**: 6.0
- **Redis**: 7-alpine
- **Open5GS**: 2.7.5

## 🚫 重要注意事項

1. **永遠在容器內檢查套件和版本** - 主機環境不代表容器內環境
2. **啟動順序很重要** - NetStack 必須先啟動創建網路
3. **跨服務通信** - SimWorld ↔ NetStack 需要網路橋接
4. **AI 功能完全可用** - 容器內 TensorFlow 完全正常，無需 fallback
5. **數據持久化** - 使用 Docker volumes 儲存資料庫數據

## 🎯 常用開發工作流程

```bash
# 1. 啟動完整環境
make up

# 2. 檢查狀態
make status

# 3. 開發時查看日誌
make logs

# 4. 測試功能
docker exec simworld_backend python -c "your_test_code"

# 5. 重啟特定服務
make simworld-restart
make netstack-restart

# 6. 清理重建
make clean
make build
make up
```

## 🔗 服務訪問地址

- **NetStack API**: http://localhost:8080
- **NetStack Docs**: http://localhost:8080/docs  
- **SimWorld Backend**: http://localhost:8888
- **SimWorld Frontend**: http://localhost:5173
- **Open5GS WebUI**: http://localhost:9999
- **Prometheus**: http://localhost:9090

## 📁 項目結構
```
/ntn-stack/
├── Makefile                    # 統一管理入口
├── netstack/                   # 5G 核心網系統
│   ├── Makefile               # NetStack 管理
│   ├── compose/core.yaml      # 核心網服務定義
│   └── netstack_api/          # NetStack API 代碼
├── simworld/                   # 3D 仿真引擎
│   ├── docker-compose.yml     # SimWorld 服務定義
│   ├── backend/               # FastAPI 後端
│   └── frontend/              # React 前端
└── tests/                      # 統一測試系統
```

最後更新: 2024年12月6日