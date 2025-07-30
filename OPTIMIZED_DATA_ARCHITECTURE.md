# 數據架構優化方案

## 問題分析

目前衛星預計算數據存在兩份：
- `@netstack/data/` - NetStack 容器內生成和使用
- `@simworld/frontend/public/data/` - 前端靜態文件服務用的副本

## 優化方案：共享 Volume

### 方案A：統一數據存儲 (推薦)

```yaml
# docker-compose 修改
volumes:
  satellite_data:
    driver: local

services:
  netstack-api:
    volumes:
      - satellite_data:/app/data  # NetStack 寫入數據

  simworld_frontend:
    volumes:
      - satellite_data:/app/public/data:ro  # 前端只讀訪問
```

### 架構優勢

1. **消除數據重複** - 只存在一份數據
2. **實時同步** - NetStack 更新數據時，前端立即可用
3. **責任清晰** - NetStack 負責生成，SimWorld 負責消費
4. **容器解耦** - 通過 volume 而非文件同步

### 實施步驟

#### 1. 修改 NetStack Compose 配置

```yaml
# netstack/compose/core.yaml
volumes:
  satellite_precomputed_data:
    driver: local

services:
  netstack-api:
    volumes:
      - satellite_precomputed_data:/app/data
      - ./tle_data:/app/tle_data:ro
```

#### 2. 修改 SimWorld Compose 配置

```yaml
# simworld/docker-compose.yml
volumes:
  satellite_precomputed_data:
    external: true  # 使用 NetStack 創建的 volume

services:
  frontend:
    volumes:
      - satellite_precomputed_data:/app/public/data:ro
```

#### 3. 移除同步腳本

```bash
# 不再需要
rm scripts/sync-netstack-data.sh
```

#### 4. 修改建置腳本

```python
# build_with_phase0_data.py - 移除自動同步邏輯
# 只需生成數據到 /app/data，volume 會自動共享
```

## 方案B：統一到 SimWorld (備選)

如果您希望將數據完全統一到 SimWorld：

```yaml
# 讓 NetStack 直接寫入到外部掛載的 SimWorld 目錄
services:
  netstack-api:
    volumes:
      - ../simworld/frontend/public/data:/app/data
```

### 比較表

| 特性 | 現況 | 方案A (共享Volume) | 方案B (統一到SimWorld) |
|------|-----|------------------|---------------------|
| 數據重複 | ❌ 有 | ✅ 無 | ✅ 無 |
| 維護複雜度 | ❌ 高 | ✅ 低 | ✅ 低 |
| 容器解耦 | ❌ 低 | ✅ 高 | ⚠️ 中 |
| 建構簡潔性 | ❌ 複雜 | ✅ 簡潔 | ✅ 簡潔 |
| Docker 最佳實踐 | ⚠️ 可接受 | ✅ 符合 | ⚠️ 可接受 |

## 推薦選擇

**推薦方案A (共享Volume)**，原因：

1. **符合 Docker 最佳實踐** - 使用 volumes 共享數據
2. **容器獨立性** - 每個容器職責清晰
3. **易於擴展** - 未來添加其他數據消費者容易
4. **部署靈活** - 可以獨立部署和重啟容器

## 實施影響評估

### 需要修改的文件
- `netstack/compose/core.yaml`
- `simworld/docker-compose.yml` 
- `build_with_phase0_data.py` (移除同步邏輯)
- `precomputedDataService.ts` (路徑保持不變)

### 不需要修改的文件
- NetStack API 代碼 (仍然讀取 `/app/data/`)
- 前端服務代碼 (仍然訪問 `/data/`)
- 同步腳本可以保留作為手動工具

### 遷移步驟
1. 停止所有容器
2. 更新 compose 配置
3. 重新建構 NetStack (會自動寫入共享 volume)
4. 啟動所有服務
5. 驗證前端可以訪問數據

### 回退方案
如果遇到問題，可以快速回退到現有的同步方案，不會影響服務可用性。