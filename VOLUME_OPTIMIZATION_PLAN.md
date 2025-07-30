# Volume 優化完整實施計劃

## 問題總結

1. **數據重複**：@netstack/data/ 和 @simworld/frontend/public/data/ 存在相同數據
2. **生命週期問題**：volume 刪除後數據不會自動重生
3. **建構時機**：數據在建構時生成，但運行時可能被 volume 覆蓋

## 解決方案：智能數據管理 + 共享 Volume

### 階段1：建立可靠的數據重生機制

#### 1.1 修改 NetStack 啟動腳本
```bash
# 創建智能啟動腳本
cat > /home/sat/ntn-stack/netstack/docker/smart-entrypoint.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 NetStack 智能啟動開始..."

DATA_DIR="/app/data"
MARKER_FILE="$DATA_DIR/.data_ready"

# 檢查數據是否存在且完整
check_data_integrity() {
    if [ ! -f "$MARKER_FILE" ]; then
        echo "❌ 數據標記文件不存在"
        return 1
    fi
    
    if [ ! -f "$DATA_DIR/phase0_precomputed_orbits.json" ]; then
        echo "❌ 主要數據文件缺失"
        return 1
    fi
    
    # 檢查文件大小（應該 > 100MB）
    SIZE=$(stat -c%s "$DATA_DIR/phase0_precomputed_orbits.json" 2>/dev/null || echo 0)
    if [ "$SIZE" -lt 100000000 ]; then
        echo "❌ 數據文件太小，可能損壞"
        return 1
    fi
    
    echo "✅ 數據完整性檢查通過"
    return 0
}

# 重新生成數據
regenerate_data() {
    echo "🔄 開始重新生成預計算數據..."
    
    # 清理舊數據
    rm -rf "$DATA_DIR"/*
    
    # 執行預計算
    cd /app
    python build_with_phase0_data.py
    
    # 創建完成標記
    echo "$(date -Iseconds)" > "$MARKER_FILE"
    echo "✅ 數據重生完成"
}

# 主邏輯
if check_data_integrity; then
    echo "📊 使用現有數據"
else
    echo "⚠️ 數據不完整，需要重新生成"
    regenerate_data
fi

echo "🎯 啟動 NetStack API 服務..."
exec "$@"
EOF

chmod +x /home/sat/ntn-stack/netstack/docker/smart-entrypoint.sh
```

#### 1.2 修改 Dockerfile
```dockerfile
# 在 NetStack Dockerfile 中添加
COPY docker/smart-entrypoint.sh /usr/local/bin/smart-entrypoint.sh
RUN chmod +x /usr/local/bin/smart-entrypoint.sh

# 確保建構時數據生成但不依賴它
RUN python build_with_phase0_data.py || echo "建構時數據生成失敗，運行時會重試"

ENTRYPOINT ["/usr/local/bin/smart-entrypoint.sh"]
```

### 階段2：實施共享 Volume 架構

#### 2.1 修改 NetStack Compose 配置
```yaml
# netstack/compose/core.yaml
volumes:
  satellite_precomputed_data:
    driver: local
  netstack_models:
    driver: local
  netstack_results:
    driver: local
  netstack_scripts:
    driver: local

services:
  netstack-api:
    # ... 其他配置
    volumes:
      - satellite_precomputed_data:/app/data  # 改為 Docker volume
      - netstack_models:/app/models
      - netstack_results:/app/results  
      - netstack_scripts:/app/scripts
      # 移除原有的 ../data 掛載
```

#### 2.2 修改 SimWorld Compose 配置
```yaml
# simworld/docker-compose.yml
volumes:
  satellite_precomputed_data:
    external: true
    name: compose_satellite_precomputed_data

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    volumes:
      - satellite_precomputed_data:/app/public/data:ro  # 只讀訪問
    # ... 其他配置
```

### 階段3：測試和驗證

#### 3.1 完整重建測試
```bash
# 測試腳本
cat > /home/sat/ntn-stack/test-volume-optimization.sh << 'EOF'
#!/bin/bash
set -e

echo "🧪 開始 Volume 優化測試..."

# 1. 完全清理
echo "🧹 清理現有容器和 volumes..."
cd /home/sat/ntn-stack
make down
docker volume rm $(docker volume ls -q | grep -E "(satellite|netstack)") 2>/dev/null || true

# 2. 重新建構
echo "🔨 重新建構 NetStack..."
cd netstack
docker compose -f compose/core.yaml build netstack-api

# 3. 啟動 NetStack
echo "🚀 啟動 NetStack..."
docker compose -f compose/core.yaml up -d netstack-api

# 4. 等待數據生成完成
echo "⏳ 等待數據生成..."
timeout 300 bash -c '
while ! docker exec netstack-api ls /app/data/.data_ready >/dev/null 2>&1; do
    echo "等待數據生成..."
    sleep 10
done
'

# 5. 檢查數據
echo "🔍 檢查數據完整性..."
docker exec netstack-api ls -la /app/data/
docker exec netstack-api wc -c /app/data/phase0_precomputed_orbits.json

# 6. 啟動 SimWorld
echo "🌍 啟動 SimWorld..."
cd ../simworld
docker compose up -d frontend

# 7. 測試前端訪問
echo "🌐 測試前端數據訪問..."
sleep 10
curl -s -I http://localhost:5173/data/phase0_precomputed_orbits.json | head -n 1

echo "✅ Volume 優化測試完成！"
EOF

chmod +x /home/sat/ntn-stack/test-volume-optimization.sh
```

## 回答您的具體問題

### 1. **映像檔建立時會自動掛載正確的資料嗎？**
**會的，但需要智能處理**：
- 新的智能啟動腳本會檢查數據完整性
- 如果數據缺失或損壞，會自動重新生成
- 首次啟動時會自動生成所有必要數據

### 2. **容器/volume 刪掉再重啟會自動恢復嗎？**
**是的**：
- 智能啟動腳本會檢測數據狀態
- Volume 空時會自動執行數據生成
- 包含完整性檢查和自動修復機制

### 3. **可以刪除 @simworld/frontend/public/data/ 嗎？**
**可以，但建議分階段**：
```bash
# Phase 1: 實施 volume 方案後
mv /home/sat/ntn-stack/simworld/frontend/public/data /home/sat/ntn-stack/simworld/frontend/public/data.backup

# Phase 2: 測試穩定後
rm -rf /home/sat/ntn-stack/simworld/frontend/public/data.backup
```

### 4. **所有使用衛星數據的部分都要改成 volume 嗎？**
**是的，統一使用 volume**：

需要修改的服務：
- ✅ NetStack API (主要數據生產者)
- ✅ SimWorld Frontend (數據消費者)  
- ✅ SimWorld Backend (如果有使用到)

```bash
# 檢查 SimWorld Backend 是否使用衛星數據
grep -r "netstack.*data\|satellite.*data" /home/sat/ntn-stack/simworld/backend/ --include="*.py" | head -5
```

## 實施時程

### 立即可做 (低風險)
1. ✅ 創建智能啟動腳本
2. ✅ 準備測試腳本  
3. ✅ 備份現有數據

### 需要測試驗證 (中風險)
1. 🔄 修改 Docker Compose 配置
2. 🔄 測試 volume 生命週期
3. 🔄 驗證數據自動重生

### 清理階段 (完全穩定後)
1. 🗑️ 刪除 @simworld/frontend/public/data/
2. 🗑️ 移除同步腳本
3. 🗑️ 清理文檔中的舊引用

**您希望我開始實施這個方案嗎？我建議先從智能啟動腳本開始，確保數據重生機制可靠。**