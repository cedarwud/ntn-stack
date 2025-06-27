# Claude Code 項目環境說明

## ⚠️ 核心重點

**🐳 這是完全 Docker 容器化專案 - 絕對不要執行 npm run dev 或 npm start 等本地指令**

所有服務都在容器內運行，使用 Docker Compose 管理，共約 20+ 個容器。

---

## 🏗️ 系統架構

```
NTN Stack
├── NetStack (5G 核心網)     - 15+ 容器
└── SimWorld (3D 仿真引擎)   - 3 個容器
```

### 核心容器
- **netstack-api** (172.20.0.40) - NetStack API 服務
- **simworld_backend** - FastAPI 後端 (Python 3.11, TensorFlow 2.19.0)
- **simworld_frontend** - React 前端 (Node.js, TypeScript)
- **netstack-mongo/redis** - 資料庫服務

---

## 🚀 標準操作指令

### 基本管理
```bash
# 根目錄統一管理
make up          # 啟動所有服務
make down        # 停止所有服務
make status      # 檢查容器狀態
make logs        # 查看所有日誌

# 分別管理
make netstack-start    # 啟動 NetStack
make simworld-start    # 啟動 SimWorld
```

### 開發工作流程
```bash
# 1. 啟動環境
make up

# 2. 檢查狀態
make status

# 3. 查看日誌
docker logs simworld_backend
docker logs netstack-api

# 4. 在容器內執行命令
docker exec simworld_backend python -c "your_code"
docker exec -it simworld_backend bash

# 5. 重建服務
make netstack-restart
make simworld-restart
```

---

## 📍 服務訪問地址

- **NetStack API**: http://localhost:8080
- **SimWorld Backend**: http://localhost:8888  
- **SimWorld Frontend**: http://localhost:5173
- **API 文檔**: http://localhost:8080/docs

---

## 🚨 故障排除

### 快速診斷
```bash
# 檢查容器狀態
docker ps | grep "netstack\|simworld"

# 檢查健康狀況
curl -f http://localhost:8080/health
curl -f http://localhost:8888/health

# 查看錯誤日誌
docker logs netstack-api 2>&1 | tail -20
docker logs simworld_backend 2>&1 | tail -20
```

### 常見修復方法
```bash
# 1. 快速重啟
make down && make up

# 2. 完全重建
make clean && make build && make up

# 3. 單個服務重建
docker restart netstack-api
docker restart simworld_backend

# 4. 緊急重置
make down
docker system prune -f
make up
```

---

## 🔧 重要注意事項

### ✅ 正確做法
- 使用 `make` 指令管理服務
- 在容器內執行 Python/Node.js 代碼
- 使用 Docker logs 查看日誌
- 通過 localhost 端口訪問服務

### ❌ 絕對禁止
- **npm run dev / npm start** - 本地環境指令
- **pip install** - 容器外安裝套件
- **直接修改容器內文件** - 重啟會丟失
- **繞過 Docker 執行程式**

### 🔍 檢查方式
```bash
# 檢查套件版本 (容器內)
docker exec simworld_backend pip freeze | grep tensorflow
docker exec simworld_backend node --version

# 測試服務功能
docker exec simworld_backend python -c "import tensorflow as tf; print(tf.__version__)"
```

---

## 📁 重要文件路徑

```
/ntn-stack/
├── Makefile                    # 統一管理入口  
├── netstack/
│   ├── Makefile               # NetStack 管理
│   ├── compose/core.yaml      # 容器配置
│   └── netstack_api/          # API 代碼
├── simworld/
│   ├── docker-compose.yml     # SimWorld 配置
│   ├── backend/               # 後端代碼
│   └── frontend/              # 前端代碼
└── scripts/                    # 診斷腳本
```

---

## 🎯 問題定位流程

1. **檢查容器狀態**: `docker ps`
2. **測試 API 健康**: `curl localhost:8080/health`
3. **查看錯誤日誌**: `docker logs <container>`
4. **重啟服務**: `make <service>-restart`
5. **完全重建**: `make clean && make up`

---

**最後更新**: 2025年6月27日  
**重點**: 🐳 完全容器化 - 不使用本地 npm/pip 指令