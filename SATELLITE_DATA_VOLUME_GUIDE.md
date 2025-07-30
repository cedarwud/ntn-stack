# 🛰️ NTN Stack 衛星數據 Volume 使用指南

## 📋 概述

由於 Celestrak API 訪問限制，NTN Stack 採用 Docker Volume 共享機制來管理衛星數據，避免即時 API 調用。

## 🏗️ 架構設計

### Volume 共享模式
```
NetStack (生產者) ──共享 Volume──→ SimWorld (消費者)
     ↓                                    ↓
/app/data/                         /app/public/data/
 ├── .data_ready                    ├── .data_ready
 ├── phase0_precomputed_orbits.json ├── phase0_precomputed_orbits.json
 └── layered_phase0/                └── layered_phase0/
```

### 數據分類

1. **預載 TLE 數據** (`/app/tle_data/`)
   - 手動收集的 Starlink/OneWeb TLE 文件
   - Docker 建置時複製到容器內
   - 來源：`netstack/tle_data/`

2. **預計算軌道數據** (`/app/data/`)
   - 運行時生成的軌道預測數據
   - 存儲於共享 Volume
   - 格式：JSON

## 📦 Volume 配置

### Docker Compose 配置

```yaml
# netstack/compose/core.yaml
services:
  netstack-api:
    volumes:
      - satellite_precomputed_data:/app/data  # 生產者掛載點
    entrypoint: ["/usr/local/bin/smart-entrypoint.sh"]
    
volumes:
  satellite_precomputed_data:
    driver: local
```

```yaml
# simworld/docker-compose.yml
services:
  frontend:
    volumes:
      - satellite_precomputed_data:/app/public/data:ro  # 消費者掛載點 (只讀)
      
volumes:
  satellite_precomputed_data:
    external: true
    name: compose_satellite_precomputed_data
```

## 🚀 數據生成流程

### 1. 容器啟動時

NetStack 容器使用 `smart-entrypoint.sh` 智能啟動：

```bash
# 檢查數據完整性
check_data_integrity() {
    if [ ! -f "$MARKER_FILE" ]; then
        echo "❌ 數據標記文件不存在"
        return 1
    fi
    
    SIZE=$(stat -c%s "$DATA_DIR/phase0_precomputed_orbits.json" 2>/dev/null || echo 0)
    if [ "$SIZE" -lt 100000000 ]; then  # 100MB 閾值
        echo "❌ 數據文件太小，可能損壞"
        return 1
    fi
}

# 重新生成數據
regenerate_data() {
    cd /app
    python simple_data_generator.py  # 或 build_with_phase0_data.py
    echo "$(date -Iseconds)" > "$MARKER_FILE"
}
```

### 2. 數據文件結構

```json
{
  "generated_at": "2025-07-30T00:42:47.463863",
  "computation_type": "simplified_test",
  "observer_location": {
    "lat": 24.94417,
    "lon": 121.37139,
    "alt": 50,
    "name": "NTPU"
  },
  "constellations": {
    "starlink": {
      "orbit_data": {
        "satellites": {
          "starlink_001": {
            "visibility_data": [...]
          }
        }
      }
    }
  }
}
```

## 🔧 使用方式

### NetStack (數據生產者)

```python
# 讀取本地 TLE 數據
from src.services.satellite.local_tle_loader import LocalTLELoader
tle_loader = LocalTLELoader("/app/tle_data")
starlink_data = tle_loader.load_collected_data('starlink')

# 生成預計算數據到 Volume
output_file = Path('/app/data/phase0_precomputed_orbits.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(precomputed_data, f, indent=2, ensure_ascii=False)
```

### SimWorld (數據消費者)

```typescript
// frontend/src/services/precomputedDataService.ts
const dataSources = [
    '/data/phase0_precomputed_orbits_test.json',
    '/data/phase0_precomputed_orbits.json',
    '/data/historical_precomputed_orbits.json'
]

async loadPrecomputedOrbitData(): Promise<PrecomputedOrbitData> {
    for (const dataSource of dataSources) {
        try {
            const response = await fetch(dataSource)
            if (response.ok) {
                return await response.json()
            }
        } catch (error) {
            console.warn(`Failed to load ${dataSource}:`, error)
        }
    }
    throw new Error('No precomputed data sources available')
}
```

## 🛠️ 維護操作

### 檢查 Volume 狀態

```bash
# 列出所有 volume
docker volume ls | grep satellite

# 檢查 volume 詳情
docker volume inspect compose_satellite_precomputed_data

# 查看 volume 內容
sudo ls -la /var/lib/docker/volumes/compose_satellite_precomputed_data/_data/
```

### 強制重新生成數據

```bash
# 刪除數據標記文件，觸發重新生成
docker exec netstack-api rm -f /app/data/.data_ready

# 重啟容器，自動重新生成
docker restart netstack-api
```

### 清理和重建

```bash
# 停止服務
make down

# 刪除 volume (將丟失所有預計算數據)
docker volume rm compose_satellite_precomputed_data

# 重新啟動 (將自動重新生成數據)
make up
```

## ⚠️ 重要注意事項

### 禁止事項
- ❌ **禁止直接調用 Celestrak API**
- ❌ **禁止使用即時下載功能**
- ❌ **禁止修改 Volume 內容 (除非你知道自己在做什麼)**

### 數據生命週期
1. **預載 TLE 數據**：Docker 建置時固定，需要重新建置映像檔才能更新
2. **預計算數據**：容器啟動時生成，Volume 刪除時丟失
3. **數據完整性**：由 `smart-entrypoint.sh` 自動檢查和修復

### 故障排除

| 問題 | 症狀 | 解決方案 |
|------|------|----------|
| 數據加載失敗 | 前端顯示 "Unexpected end of JSON input" | 檢查 Volume 中的 JSON 文件完整性 |
| 容器重啟循環 | NetStack 不斷重啟 | 檢查 `smart-entrypoint.sh` 日誌，可能是數據生成失敗 |
| Volume 為空 | 訪問 `/data/` 返回 404 | Volume 可能被意外刪除，重啟容器重新生成 |

## 🔄 更新 TLE 數據流程

當需要更新衛星 TLE 數據時：

1. **手動收集新數據**
   ```bash
   cd netstack/tle_data/
   # 使用 daily_tle_collector.py 手動下載
   python scripts/daily_tle_collector.py
   ```

2. **重新建置映像檔**
   ```bash
   make netstack-rebuild
   ```

3. **重啟服務**
   ```bash
   make netstack-restart
   ```

## 📊 監控與日誌

### 關鍵日誌位置
```bash
# NetStack 智能啟動日誌
docker logs netstack-api | grep "🚀 NetStack 智能啟動"

# 數據生成日誌
docker logs netstack-api | grep "數據生成完成"

# SimWorld 數據加載日誌  
docker logs simworld_frontend | grep "precomputed"
```

### 性能指標
- **預載 TLE 數據**：~10MB (固定)
- **預計算軌道數據**：427KB (簡化版) / <10MB (完整版)
- **數據生成時間**：<30秒 (簡化版) / 2-5分鐘 (完整版)
- **Volume 生命週期**：與容器無關，持久化存儲

---

**🔧 維護者**: NTN Stack 開發團隊  
**📅 更新時間**: 2025-07-30  
**📝 版本**: v1.0