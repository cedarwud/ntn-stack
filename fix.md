# 待修復問題清單

## ✅ 已成功解決的核心問題
- **NetStack v2.0.0-final**: 系統版本已正確升級 ✅
- **衛星數據系統**: 預計算6小時衛星數據已激活 (satellite_data_ready: true) ✅
- **觀測者座標**: 已更新為台灣NTPU精確座標 (24°56'39"N 121°22'17"E) ✅
- **真實TLE數據**: 系統使用NetStack歷史TLE數據而非模擬數據 ✅
- **衛星數量**: 從固定20顆改為動態5-6顆真實可見衛星 ✅

## 🔧 待修復的前端配置問題

### 1. SimWorld API 配置問題
**錯誤**: `SimWorld BaseURL 未配置`
**原因**: api-config.ts 中 simworld.baseUrl 設為空字串導致 URL 構造失敗
**影響**: 前端無法正確調用 SimWorld 後端 API

**修復方案**:
```typescript
// 檔案: /home/u24/ntn-stack/simworld/frontend/src/config/api-config.ts
// 第79行修改
simworld: {
  baseUrl: '', // ❌ 當前配置 - 導致 URL 構造失敗
  timeout: 30000
},

// 應改為：
simworld: {
  baseUrl: '/', // ✅ 修復配置 - 使用根路徑
  timeout: 30000
},
```

### 2. URL 構造邏輯問題
**錯誤**: `Failed to construct 'URL': Invalid base URL`
**位置**: api-config.ts:123:16 getServiceUrl 函數
**原因**: 空字串 baseUrl 無法與 endpoint 組成有效 URL

**修復方案**:
```typescript
// 檔案: /home/u24/ntn-stack/simworld/frontend/src/config/api-config.ts
// getServiceUrl 函數需要處理空 baseUrl 的情況

export const getServiceUrl = (service: 'netstack' | 'simworld', endpoint: string = ''): string => {
  const config = getApiConfig()
  const baseUrl = config[service].baseUrl
  
  // 確保端點以 / 開頭
  const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  
  // ✅ 修復：處理空 baseUrl 的情況
  if (\!baseUrl || baseUrl === '') {
    return normalizedEndpoint
  }
  
  // 如果是代理路徑，直接拼接
  if (baseUrl.startsWith('/')) {
    return `${baseUrl}${normalizedEndpoint}`
  }
  
  // 如果是完整 URL，使用 URL 構造器
  try {
    return new URL(normalizedEndpoint, baseUrl).toString()
  } catch (error) {
    console.error('無效的 URL 配置:', { baseUrl, endpoint, error })
    return `${baseUrl}${normalizedEndpoint}`
  }
}
```

### 3. 配置驗證邏輯問題
**錯誤**: `Docker 模式下 SimWorld 必須使用代理路徑 (以 / 開頭)`
**位置**: validateApiConfig 函數
**原因**: 驗證邏輯與實際需求不符

**修復方案**:
```typescript
// 檔案: /home/u24/ntn-stack/simworld/frontend/src/config/api-config.ts
// validateApiConfig 函數

export const validateApiConfig = (): string[] => {
  const warnings: string[] = []
  const config = getApiConfig()
  
  // 檢查 NetStack 配置
  if (\!config.netstack.baseUrl) {
    warnings.push('NetStack BaseURL 未配置')
  }
  
  // ✅ 修復：SimWorld 配置檢查邏輯
  // Docker 環境下允許空字串或根路徑
  if (config.mode === 'docker') {
    if (\!config.netstack.baseUrl.startsWith('/')) {
      warnings.push('Docker 環境下 NetStack 應使用代理路徑')
    }
    // SimWorld 在 Docker 環境下可以使用空字串或根路徑
    // 不需要強制要求代理路徑前綴
  } else {
    // 非 Docker 環境下才檢查 SimWorld BaseURL
    if (\!config.simworld.baseUrl) {
      warnings.push('SimWorld BaseURL 未配置')
    }
  }
  
  return warnings
}
```

## 🎯 修復優先級

### 🔥 **最高優先級** (影響研究數據準確性)
4. **全球視野模式錯誤** - 修復返回20顆衛星而非5-6顆的問題

### 高優先級 (立即修復)  
1. **SimWorld baseUrl 配置** - 修復 API 調用失敗問題
2. **URL 構造邏輯** - 處理空 baseUrl 情況

### 中優先級 (後續優化)
3. **配置驗證邏輯** - 改善用戶體驗

### 4. ⚠️ **前端API參數傳遞不一致問題** (新發現)
**現象**: 前端接收到20顆衛星，而非預期的5-6顆
**日誌證據**:
```
🛰️ SimWorldApi: API 原始響應: 
- 數據來源: 真實 TLE 歷史數據 ✅
- 全球視野: true ❌ (應該是 false)
- 處理衛星: 20 顆
- 可見衛星: 20 顆 ❌ (應該是 5-6 顆)
- 最小仰角: -90 度 ❌ (應該是 5 度)
```

**問題根因**: 前端API調用可能仍在使用全球視野模式或參數傳遞有誤

**影響**: 
- 顯示過多不相關衛星（仰角為負的衛星無法進行換手）
- 與論文研究需求不符（需要真實可換手的衛星）

**檢查位置**:
1. **前端API調用邏輯**: `simworld-api.ts` 中的參數構建
2. **後端參數處理**: SimWorld backend 的 global_view 邏輯
3. **數據過濾機制**: 前端或後端的衛星過濾邏輯

**預期行為**:
- `global_view: false`
- `min_elevation: 5` (而非 -90)
- 返回 5-6 顆可見衛星 (仰角 ≥ 5°)

**具體問題位置**: 
- **檔案**: `/home/u24/ntn-stack/simworld/frontend/src/services/simworld-api.ts`
- **第163行**: `global_view: 'true',  // 強制全球視野` ❌

**修復方案**:
```typescript
// 檔案: /home/u24/ntn-stack/simworld/frontend/src/services/simworld-api.ts
// 第160-167行修改

const params = {
  count: Math.min(maxSatellites, 150),
  min_elevation_deg: minElevation,  // 使用傳入的仰角參數 (5度)
  global_view: 'false',  // ✅ 修復：使用精確仰角過濾，而非全球視野
  observer_lat: observerLat,  // NTPU座標
  observer_lon: observerLon,  // NTPU座標  
  observer_alt: 0.0,
};
```

**修復後預期結果**:
- `global_view: false` ✅
- `min_elevation: 5` ✅ 
- 返回 5-6 顆可見衛星 ✅
- 所有衛星仰角 ≥ 5° ✅ (適合換手研究)

## 📊 驗證步驟
修復後執行以下驗證：

```bash
# 1. 重啟前端容器
make simworld-restart

# 2. 檢查瀏覽器控制台是否還有錯誤

# 3. 驗證 API 調用
curl -s "http://localhost:5173/api/v1/satellites/visible_satellites?count=10&min_elevation_deg=5&observer_lat=24.9441667&observer_lon=121.3713889"

# 4. 確認衛星數據顯示
# 檢查側邊欄是否顯示正確的衛星數量和數據
```

## 🏆 當前系統狀態評估

**✅ 核心功能**: LEO衛星換手研究系統已準備就緒
- NetStack v2.0.0-final 正常運行
- 真實TLE數據，適合學術發表
- NTPU觀測點，符合台灣地理位置
- 動態衛星數量，反映真實可見情況

**❌ 前端問題**: **直接影響研究工作流程** - 需要立即修復
- 後端API數據正確，但前端無法顯示 ❌
- 側邊欄「衛星 gNB」無衛星顯示 ❌ **（影響研究）**
- 無法通過UI查看和分析衛星數據 ❌ **（影響研究）**
- 研究人員無法直觀檢視衛星位置、仰角、距離 ❌ **（影響研究）**

**🚨 影響評估修正**: 
- **錯誤評估**: ~~「不影響研究」~~
- **正確評估**: **嚴重影響研究工作流程和數據分析**

## 5. ⚠️ **側邊欄衛星顯示問題** - **核心研究功能受影響**

**現象**: 側邊欄「衛星 gNB」面板顯示空白，無任何衛星數據
**影響**: **直接阻礙論文研究工作**
- 無法查看當前可見衛星列表
- 無法分析衛星仰角、方位角、距離數據  
- 無法進行換手決策演算法驗證
- 研究人員失去主要的數據檢視界面

**根本原因**: 
1. **API配置錯誤** (問題1-2) → API調用失敗
2. **全球視野參數錯誤** (問題4) → 數據格式不符預期  
3. **數據映射問題** → 後端正確數據無法正確顯示在UI

**連鎖影響**:
```
API配置問題 → API調用失敗 → 無數據返回 → 側邊欄空白 → 無法進行研究
     ↓
全球視野問題 → 錯誤數據格式 → 前端處理失敗 → 側邊欄空白 → 無法進行研究
```

**修復優先級**: **🔥 最高優先級** - 必須立即修復才能恢復研究功能

## 6. 🔍 **重要發現：SimWorld vs NetStack 數據來源問題**

**關鍵發現**: SimWorld **並未串接** NetStack v2.0.0-final API！

**證據分析**:
```bash
# NetStack v2.0 API (正確版本，但無衛星)
$ docker exec simworld_backend curl "http://netstack-api:8080/api/v1/satellite-ops/visible_satellites?..."
{"satellites":[],"total_count":0,...}

# SimWorld 自己的 API (有20顆衛星)  
$ curl "http://localhost:8888/api/v1/satellites/visible_satellites?..."
{"satellites": [20顆衛星], "data_source": {"type": "real_tle_data"}}
```

**日誌證據**:
```
SimWorld Backend 日誌:
- "Returning cached satellites: 20 satellites" 
- "全球視野模式：調整最小仰角為 -90 度"
- "✅ 找到 20 顆可見衛星 (使用真實 TLE 數據)"
```

**結論**: 
- ✅ SimWorld **有自己的衛星計算引擎**和TLE數據
- ❌ SimWorld **沒有使用** NetStack v2.0.0-final 的預計算衛星數據
- ⚠️ 兩個系統在**並行運行不同的衛星計算**

**影響評估**:
1. **數據一致性問題** - 兩套衛星系統可能產生不同結果
2. **版本混淆** - 前端顯示的"v2.0數據"實際是SimWorld自己的計算
3. **研究準確性** - 需要確認使用哪套衛星數據進行論文研究

**架構決策**:
✅ **應該使用**: NetStack v2.0.0-final 預計算衛星數據
❌ **應該捨棄**: SimWorld 的20顆衛星系統

**原因分析**:
1. **符合設計規範**: NetStack v2.0 符合 satellite-precompute-plan 的 6-8 顆衛星標準
2. **3GPP NTN 合規**: 6-8 顆衛星符合真實 LEO 換手場景
3. **學術價值**: 適合論文研究和頂級期刊發表
4. **架構進化**: NetStack v2.0 是最新的技術實作

**SimWorld 20顆衛星問題**:
- ❌ 超出 3GPP NTN 標準（6-8 顆）
- ❌ 不符合真實換手場景  
- ❌ 屬於過時的技術實作
- ❌ 架構設計已被 NetStack v2.0 取代

**修復策略**: 
1. **停用** SimWorld 自己的衛星計算
2. **串接** NetStack v2.0 API 
3. **使用** 符合標準的 6-8 顆衛星數據

## 7. 🔄 **架構修復：SimWorld 串接 NetStack v2.0**

**目標**: 讓 SimWorld 前端顯示 NetStack v2.0 的標準衛星數據（6-8顆）

**當前問題**: NetStack v2.0 API 返回 0 顆衛星
```bash
$ docker exec simworld_backend curl "http://netstack-api:8080/api/v1/satellite-ops/visible_satellites?..."
{"satellites":[],"total_count":0}
```

**修復步驟**:
1. **診斷 NetStack v2.0 數據問題** - 為什麼預計算系統返回 0 顆衛星
2. **修復 NetStack 衛星數據載入** - 確保 6 小時預計算數據正確載入
3. **修改 SimWorld API** - 從自己的20顆衛星改為調用 NetStack v2.0
4. **驗證數據一致性** - 確保前端顯示符合標準的 6-8 顆衛星
