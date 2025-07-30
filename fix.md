# 🛠️ NTN Stack 衛星數據系統修復計劃

**修復日期**: 2025-07-30  
**問題狀態**: 待修復  
**優先級**: 高

## 🚨 核心問題分析

### 1. **數據來源檢測失效**
- **問題**: simworld-api.ts 無法正確識別數據來源類型
- **症狀**: 顯示 "數據來源未知 (客戶端檢測)"
- **原因**: 檢測邏輯基於過時的 NORAD ID 範圍，未使用 computation_type

### 2. **使用測試數據而非真實數據**
- **問題**: 系統使用 simple_data_generator.py 產生的測試數據
- **症狀**: 只有 3 顆衛星，computation_type: "simplified_test"
- **原因**: smart-entrypoint.sh:65 硬編碼使用簡化生成器

### 3. **星座選擇器失效**
- **問題**: 無法切換 Starlink/OneWeb 星座
- **症狀**: OneWeb 選擇無效果，API 返回空數據
- **原因**: 預計算數據只包含 Starlink 測試數據

### 4. **數據同步問題**
- **問題**: 立體圖與側邊欄數據來源可能不一致
- **症狀**: 用戶報告立體圖顯示超過 3 顆衛星
- **需要驗證**: 確認兩者是否真的使用不同數據源

## 🎯 修復方案

### Phase 1: 修復數據來源檢測 (立即)

#### 1.1 更新 simworld-api.ts 檢測邏輯
位置: /simworld/frontend/src/services/simworld-api.ts:218-233
修復: 基於 computation_metadata 而非 NORAD ID 檢測
替換現有的數據來源檢測邏輯為:

```typescript
const detectDataSource = (data: any) => {
  // 優先檢查後端提供的數據來源信息
  if (data.computation_metadata?.data_source) {
    return {
      type: data.computation_metadata.data_source,
      description: '後端提供的數據來源信息',
      isSimulation: data.computation_metadata.data_source.includes('simulation')
    }
  }
  
  // 檢查計算類型
  if (data.computation_metadata?.computation_type) {
    const compType = data.computation_metadata.computation_type
    return {
      type: compType,
      description: compType === 'simplified_test' 
        ? '簡化測試數據 (limited dataset)' 
        : '真實預計算數據 (from TLE files)',
      isSimulation: compType === 'simplified_test'
    }
  }
  
  // 檢查數據大小和衛星數量
  const satelliteCount = data.filtered_satellites?.length || 0
  if (satelliteCount <= 5) {
    return {
      type: 'limited_test',
      description: '有限測試數據 (客戶端推斷)',
      isSimulation: true
    }
  }
  
  return {
    type: 'unknown',
    description: '無法確定數據來源',
    isSimulation: null
  }
}
```

#### 1.2 添加詳細數據來源日志

```typescript
const dataSource = detectDataSource(data)
console.log(`📊 數據來源: ${dataSource.type}`)
console.log(`📝 描述: ${dataSource.description}`)
console.log(`🎭 模擬數據: ${dataSource.isSimulation ? '是' : '否'}`)
console.log(`🔢 衛星數量: ${data.filtered_satellites?.length || 0}`)
console.log(`⚙️ 計算類型: ${data.computation_metadata?.computation_type || 'unknown'}`)
```

### Phase 2: 生成真實衛星數據 (重要)

#### 2.1 修復數據生成腳本

位置: /netstack/docker/smart-entrypoint.sh:64-65
修復: 使用真實數據生成器

替換現有行:
```bash
# echo "🔨 執行簡化數據生成 (測試 Volume 架構)..."
# python simple_data_generator.py
```

修復為:
```bash
echo "🔨 執行真實數據生成 (Phase 0 完整數據)..."
python build_with_phase0_data.py
```

#### 2.2 確保包含多星座數據
檢查: /netstack/build_with_phase0_data.py
確保支援:
- Starlink 完整星座 (4000+ 衛星)
- OneWeb 完整星座 (600+ 衛星)  
- 真實 TLE 數據源 (/app/tle_data/)

#### 2.3 更新 Docker 建置流程
```bash
# 執行數據重新生成
cd /home/sat/ntn-stack/netstack
make down
# 強制重新生成數據
docker exec netstack-api rm -f /app/data/.data_ready 2>/dev/null || true
make up
```

### Phase 3: 修復星座選擇控制 (同步)

#### 3.1 驗證數據包含多星座
```bash
# 檢查生成的數據是否包含 OneWeb
docker exec netstack-api jq '.constellations | keys' /app/data/phase0_precomputed_orbits.json
# 預期輸出: ["starlink", "oneweb"]
```

#### 3.2 測試星座選擇器
```bash
# 測試 Starlink API
curl "http://localhost:8080/api/v1/satellites/precomputed/ntpu?constellation=starlink&count=10"

# 測試 OneWeb API  
curl "http://localhost:8080/api/v1/satellites/precomputed/ntpu?constellation=oneweb&count=10"
```

#### 3.3 確保前端星座切換生效
檢查: DataSyncContext 和 SatelliteAnimationController
確認: constellation 參數正確傳遞到 API 調用

### Phase 4: 統一數據同步 (驗證)

#### 4.1 確認數據源一致性
檢查位置:
- DataSyncContext.tsx:240-241 (useVisibleSatellites)
- SatelliteAnimationController.tsx:100-105 (orbitService)
- PrecomputedOrbitService.ts:62-64 (netstackFetch)

確認: 所有組件都調用相同的 NetStack API 端點

#### 4.2 統一衛星數量顯示
確保側邊欄和立體圖使用相同的衛星數據計數
檢查是否有額外的模擬衛星被添加到立體圖中

## 🔄 執行步驟

### Step 1: 立即修復 (5分鐘)
1. 修復數據來源檢測邏輯 - 編輯 simworld-api.ts
2. 修復數據生成腳本 - 編輯 smart-entrypoint.sh

### Step 2: 數據重新生成 (10分鐘)
1. 停止服務: make down
2. 清理舊數據，強制重新生成
3. 重新啟動，觸發真實數據生成: make up
4. 等待數據生成完成 (約5-8分鐘)

### Step 3: 驗證修復 (5分鐘)
1. 檢查數據來源類型不再是 "simplified_test"
2. 檢查衛星數量 > 10 顆衛星
3. 檢查星座選擇 OneWeb 有效
4. 檢查前端數據同步

## 🎯 預期結果

### 數據來源檢測修復後:
```
📊 數據來源: phase0_precomputed  
📝 描述: 真實預計算數據 (from TLE files)
🎭 模擬數據: 否
🔢 衛星數量: 45
⚙️ 計算類型: real_constellation_data
```

### 星座選擇修復後:
- **Starlink**: 30-50 顆可見衛星
- **OneWeb**: 15-25 顆可見衛星
- **切換生效**: 側邊欄和立體圖同步更新

### 數據同步修復後:
- **側邊欄衛星 gNB**: 顯示實際 API 返回數量
- **立體圖衛星**: 顯示相同數量  
- **一致性**: 100% 數據同步

## ⚠️ 注意事項

### 數據生成時間
- **完整數據生成**: 約 5-8 分鐘
- **首次生成**: 可能需要 10-15 分鐘
- **監控方式**: docker logs netstack-api -f

### 回滾機制
如果修復失敗，可以回滾到測試數據:
```bash
# 恢復簡化生成器
git checkout HEAD -- /netstack/docker/smart-entrypoint.sh
make netstack-restart
```

### 數據驗證
確保生成的數據文件大小 > 100MB，包含真實的 NORAD ID 範圍 44000-48000。

---

**此修復計劃將解決所有衛星數據相關問題，確保系統使用真實數據並實現完全數據同步。**
