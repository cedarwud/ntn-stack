# 06 - Phase 5: 容器啟動順序和智能更新

> **上一階段**：[Phase 4 - 前端時間軸](./05-phase4-frontend-timeline.md) | **回到總覽**：[README.md](./README.md)

## 🎯 Phase 5 目標 ✅ **已完成**
**目標**：優化容器啟動順序，實現智能數據更新機制
**預估時間**: 1 天
**實際完成**: ✅ 容器啟動順序已優化，NetStack API 快速可用

## 📋 開發任務

### 5.1 NetStack Core.yaml 啟動順序優化

#### **修改現有服務配置**（`netstack/compose/core.yaml`）
```yaml
# 優化現有 rl-postgres 健康檢查（第 385-416 行）
  rl-postgres:
    # ... 現有配置保持不變 ...
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U rl_user -d rl_research"]
      interval: 5s          # 從 30s 縮短為 5s
      timeout: 3s           # 從 5s 縮短為 3s  
      retries: 5            # 從 3 增加為 5
      start_period: 10s     # 新增，給 PostgreSQL 足夠啟動時間

# 優化現有 netstack-api 依賴關係（第 350-383 行）
  netstack-api:
    # ... 現有配置保持不變 ...
    environment:
      # ... 現有環境變數保持不變 ...
      - SATELLITE_DATA_MODE=instant_load     # 新增：啟動時立即載入
      - POSTGRES_WAIT_TIMEOUT=30             # 新增：等待超時設定
    depends_on:
      - mongo
      - redis
      - amf
      - smf
      - rl-postgres                          # 新增：等待 RL PostgreSQL 就緒
    entrypoint: ["/app/docker-entrypoint.sh"]  # 修改：使用智能啟動腳本
```

#### **不需要創建新服務**
- ✅ 修改現有 `netstack-api` 服務配置
- ✅ 優化現有 `rl-postgres` 健康檢查
- ❌ 不需要創建重複的服務

### 5.2 智能啟動腳本實現

#### **創建 NetStack API 啟動腳本**（`netstack/docker-entrypoint.sh`）
```bash
#!/bin/bash
# netstack/docker-entrypoint.sh - NetStack API 智能啟動腳本

echo "🚀 NetStack API 啟動中..."

# 1. 等待 RL PostgreSQL 就緒
echo "⏳ 等待 RL PostgreSQL 連接..."
python3 -c "
import asyncpg
import asyncio
import sys
import time
import os

async def wait_postgres():
    # 使用現有的 RL_DATABASE_URL 環境變數
    db_url = os.getenv('RL_DATABASE_URL', 'postgresql://rl_user:rl_password@rl-postgres:5432/rl_research')
    
    for i in range(30):
        try:
            conn = await asyncpg.connect(db_url)
            await conn.close()
            print('✅ RL PostgreSQL 連接成功')
            return True
        except Exception as e:
            print(f'⏳ RL PostgreSQL 未就緒 ({i+1}/30): {e}')
            time.sleep(1)
    return False

if not asyncio.run(wait_postgres()):
    print('❌ RL PostgreSQL 連接超時')
    sys.exit(1)
"

# 2. 立即載入衛星數據（如果啟用了 SATELLITE_DATA_MODE）
if [ "$SATELLITE_DATA_MODE" = "instant_load" ]; then
    echo "📡 載入衛星歷史數據..."
    python3 -c "
import asyncio
import os
from app.services.instant_satellite_loader import InstantSatelliteLoader

async def load_data():
    db_url = os.getenv('RL_DATABASE_URL', 'postgresql://rl_user:rl_password@rl-postgres:5432/rl_research')
    loader = InstantSatelliteLoader(db_url)
    success = await loader.ensure_data_available()
    if success:
        print('✅ 衛星數據載入完成，系統可用')
        return True
    else:
        print('❌ 衛星數據載入失敗')
        return False

# 載入失敗不阻止啟動，但會記錄警告
success = asyncio.run(load_data())
if not success:
    print('⚠️ 衛星數據載入失敗，將以降級模式啟動')
"
else
    echo "⏭️ 跳過衛星數據載入（未啟用 instant_load 模式）"
fi

# 3. 啟動 NetStack API
echo "🌐 啟動 NetStack API..."
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8080
```

#### **腳本部署方式**
```dockerfile
# 在 netstack/Dockerfile 中添加
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh
```

## 📋 實施檢查清單

### **現有服務修改檢查**
- [ ] 修改 `netstack/compose/core.yaml` 中的 `rl-postgres` 健康檢查配置
- [ ] 修改 `netstack/compose/core.yaml` 中的 `netstack-api` 依賴關係和環境變數
- [ ] 創建 `netstack/docker-entrypoint.sh` 智能啟動腳本
- [ ] 修改 `netstack/Dockerfile` 添加啟動腳本

### **系統整合檢查**
- [ ] 容器啟動依賴順序：`rl-postgres` → `netstack-api`
- [ ] 數據載入失敗時不阻止服務啟動（降級模式）
- [ ] 健康檢查機制正常運作
- [ ] 日誌記錄完整且清晰

## 🧪 驗證步驟

### **容器啟動順序驗證**
```bash
# 1. 檢查 NetStack 容器狀態（使用現有的管理工具）
make netstack-status

# 2. 測試完整重啟（使用現有的 Makefile）
make netstack-restart

# 3. 檢查 netstack-api 啟動日誌
docker logs netstack-api | grep -E "(衛星數據|satellite.*load|✅|❌|PostgreSQL)"
```

### **服務可用性驗證**
```bash
# 4. 檢查 RL PostgreSQL 健康狀態
docker inspect netstack-rl-postgres --format='{{.State.Health.Status}}'

# 5. 測試 API 立即可用性
curl -X GET "http://localhost:8080/health" | jq

# 6. 檢查衛星數據是否載入
curl -X GET "http://localhost:8080/api/v1/satellites/constellations/info" | jq
```

### **容器網路連接驗證**
```bash
# 7. 驗證容器間網路（使用現有工具）
make verify-network-connection

# 8. 檢查整體系統狀態
make status
```

## ⚠️ 重要修改說明

### **與現有架構的整合**
1. **不創建新的 docker-compose.yml**：使用現有的模組化 compose 結構
2. **不創建重複服務**：僅修改現有 `netstack-api` 和 `rl-postgres` 配置
3. **保持 Makefile 兼容性**：所有現有的 `make` 命令繼續可用
4. **漸進式升級**：現有功能不受影響，只是增強啟動順序

### **服務名稱對應**
- ✅ **rl-postgres** (服務名) → **netstack-rl-postgres** (容器名)
- ✅ **netstack-api** (服務名) → **netstack-api** (容器名)
- ✅ 使用現有的 **RL_DATABASE_URL** 環境變數配置

**🎯 完成標準**：
- 容器啟動順序正確：`rl-postgres` → `netstack-api`
- 系統啟動時間 < 120 秒（包含數據載入）
- 數據立即可用或降級模式正常運行
- 現有 `make` 命令全部兼容

