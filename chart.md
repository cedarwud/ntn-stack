# 信號分析圖表修復計劃

## 🔍 問題分析

### 根本原因
通過 ultrathink 深度分析，發現 navbar > 信號分析的4張圖表問題根源：

1. **後端API端點暫時禁用**
   - SINR Map API: 返回 503，提示數據庫遷移中
   - CFR Plot API: 返回 503，提示數據庫遷移中  
   - Doppler Plots API: 返回 503，提示數據庫遷移中
   - Channel Response API: 返回 503，提示數據庫遷移中

2. **前端架構問題**
   - 4個viewer組件沒有使用統一的API配置系統
   - 直接使用原生 fetch 而非 simworldFetch
   - 沒有正確處理 503 錯誤狀態

3. **Docker環境配置問題**
   - viewer組件不支持代理路徑配置
   - 硬編碼 API 路徑，無法適應不同環境

### 影響範圍
- 🔴 SINR MAP 圖表：完全無法顯示
- 🔴 Constellation & CFR 圖表：完全無法顯示
- 🔴 Delay-Doppler 圖表：完全無法顯示
- 🔴 Time-Frequency 圖表：完全無法顯示


## 🚀 詳細修復步驟流程

### Phase 1: 後端API端點重新啟用 (估計時間: 30分鐘)

#### 1.1 移除暫時禁用的503錯誤
- **文件**: `/home/sat/ntn-stack/simworld/backend/app/domains/simulation/api/simulation_api.py`
- **操作**: 移除所有4個API端點的503錯誤返回
- **目標**: 恢復CFR、SINR、Doppler、Channel Response API的正常功能

#### 1.2 實現MongoDB支持的圖表生成
- **檢查現有static圖像**: 使用現有的 `app/static/images/` 中的圖像
- **快速實現**: 直接返回靜態圖像文件，跳過複雜的Sionna運算
- **兼容性**: 保持API接口參數不變，確保前端兼容

#### 1.3 測試後端API端點
```bash
# 測試SINR Map API
curl -v 'http://localhost:8888/api/v1/simulations/sinr-map?scene=nycu'  < /dev/null |  head -20

# 測試CFR Plot API  
curl -v 'http://localhost:8888/api/v1/simulations/cfr-plot?scene=nycu' | head -20

# 測試Doppler Plots API
curl -v 'http://localhost:8888/api/v1/simulations/doppler-plots?scene=nycu' | head -20

# 測試Channel Response API
curl -v 'http://localhost:8888/api/v1/simulations/channel-response?scene=nycu' | head -20
```

**Phase 1 驗收標準：**
- [ ] 4個API端點都返回200狀態碼
- [ ] 返回有效的PNG圖像數據
- [ ] 無503錯誤訊息
- [ ] API響應時間 < 5秒


### Phase 2: 前端Viewer組件重構 (估計時間: 45分鐘)

#### 2.1 修復SINRViewer組件
- **文件**: `/home/sat/ntn-stack/simworld/frontend/src/components/domains/interference/detection/SINRViewer.tsx`
- **修改**: 
  - 導入 `simworldFetch` 替換原生 `fetch`
  - 使用統一的API配置系統
  - 改善503錯誤處理邏輯
- **代碼示例**:
```typescript
// 替換原有的 fetch 調用
import { simworldFetch } from '../../../../config/api-config'

// 在 loadSINRMapImage 函數中
const response = await simworldFetch(apiUrl)
```

#### 2.2 修復CFRViewer組件
- **文件**: `/home/sat/ntn-stack/simworld/frontend/src/components/domains/simulation/wireless/CFRViewer.tsx`
- **修改**: 同SINRViewer的修改邏輯
- **特別注意**: CFR圖表的參數處理

#### 2.3 修復DelayDopplerViewer組件
- **文件**: `/home/sat/ntn-stack/simworld/frontend/src/components/domains/simulation/wireless/DelayDopplerViewer.tsx`
- **修改**: 同SINRViewer的修改邏輯
- **特別注意**: Doppler圖表的高級配置參數

#### 2.4 修復TimeFrequencyViewer組件
- **文件**: `/home/sat/ntn-stack/simworld/frontend/src/components/domains/simulation/wireless/TimeFrequencyViewer.tsx`
- **修改**: 同SINRViewer的修改邏輯
- **特別注意**: Time-Frequency圖表的響應處理

**Phase 2 驗收標準：**
- [ ] 所有4個viewer組件都使用 `simworldFetch`
- [ ] 支持Docker環境的代理路徑配置
- [ ] 改善的503錯誤處理和用戶提示
- [ ] 前端編譯無錯誤：`npm run build`


### Phase 3: 整合測試與最終驗證 (估計時間: 15分鐘)

#### 3.1 系統重啟與健康檢查
```bash
# 完全重啟系統
make down && make up

# 等待系統啟動
sleep 30

# 檢查系統狀態
make status

# 檢查後端服務健康
curl -s http://localhost:8888/health  < /dev/null |  jq
```

#### 3.2 前端圖表功能測試
- **測試環境**: http://localhost:5173
- **測試步驟**:
  1. 點擊 navbar > 信號分析 dropdown
  2. 依次測試4個圖表選項
  3. 驗證圖表能正常顯示
  4. 檢查刷新功能是否正常

#### 3.3 Docker環境配置驗證
```bash
# 檢查API配置
grep -n 'VITE_ENV_MODE' simworld/frontend/.env.docker

# 檢查代理配置
grep -n 'simworld' simworld/frontend/vite.config.ts

# 檢查容器網路
docker network ls | grep ntn-stack
```

**Phase 3 驗收標準：**
- [ ] `make status` 所有服務顯示 "healthy"
- [ ] 4個信號分析圖表都能正常顯示
- [ ] 圖表刷新功能正常
- [ ] 無console錯誤訊息
- [ ] Docker環境配置正確


## 📋 總結與實施要點

### 🎯 修復目標
- 恢復navbar > 信號分析的4張圖表功能
- 使用統一的API配置系統
- 改善錯誤處理和用戶體驗
- 確保Docker環境兼容性

### ⚡ 關鍵實施原則
1. **遵循CLAUDE.md錯誤處理原則**：發現錯誤立即修復，絕不接受錯誤狀態
2. **禁止模擬數據回退**：必須解決真實的API問題，不使用MockRepository
3. **統一API配置**：所有API調用必須通過 `simworldFetch` 函數
4. **Docker環境優先**：確保在Docker環境中正常工作

### 🔧 技術債務清理
- **移除硬編碼URL**：所有viewer組件使用統一配置
- **改善錯誤處理**：正確處理503狀態碼和網路錯誤
- **統一重試機制**：所有組件使用一致的重試邏輯
- **記憶體洩漏防護**：正確管理URL.createObjectURL

### 📊 預期效果
- 🟢 SINR MAP 圖表：正常顯示
- 🟢 Constellation & CFR 圖表：正常顯示  
- 🟢 Delay-Doppler 圖表：正常顯示
- 🟢 Time-Frequency 圖表：正常顯示
- 🟢 Docker環境：完全兼容
- 🟢 錯誤處理：用戶友好的提示

### 🚨 風險控制
1. **在修復過程中保持系統穩定**
2. **每個Phase完成後進行驗證**
3. **遇到問題立即回滾到前一個穩定狀態**
4. **確保不影響其他系統功能**

### 📝 完成標準
- [ ] 所有4個圖表都能正常顯示
- [ ] 系統健康檢查全部通過
- [ ] 前端無console錯誤
- [ ] Docker環境完全兼容
- [ ] API響應時間符合要求
- [ ] 用戶體驗明顯改善

---

**⚠️ 重要提醒：根據CLAUDE.md原則，必須解決根本問題，不接受任何形式的模擬數據或功能降級！**

**🚀 預計總修復時間：90分鐘**
