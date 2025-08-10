# Phase 2: 整合重複的 API 服務

## 🎯 目標
統一和整合重複的 API 服務層，提升代碼維護性

## 🔄 發現的重複 API 服務

### NetStack API 服務重複
- `services/netstack-api.ts` - 新版本，專注於衛星存取預測
- `services/netstackApi.ts` - 舊版本，包含 UAV 數據和重試邏輯
- `services/netstack-precomputed-api.ts` - 預計算數據專用

**建議**: 
- 保留 `netstack-api.ts` 作為主要接口
- 將 `netstackApi.ts` 中的重試邏輯遷移到新版本
- 整合預計算API功能

### 基礎 API 服務重複
- `services/api.ts` - 基礎 API 客戶端
- `services/api-client.ts` - 另一個 API 客戶端
- `services/base-api.ts` - 基礎 API 抽象層

**建議**: 統一為單一的基礎 API 服務

### 預計算服務重複
- `services/precomputedDataService.ts`
- `services/PrecomputedOrbitService.ts`

**建議**: 合併為統一的軌道預計算服務

## 📋 整合計劃

### 第一階段: NetStack API 整合
1. 分析兩個 NetStack API 的功能差異
2. 創建統一的 NetStack API 接口
3. 遷移重試邏輯和錯誤處理
4. 更新所有導入引用

### 第二階段: 基礎 API 統一
1. 選擇最完整的基礎 API 實現
2. 整合其他版本的功能
3. 創建統一的配置和攔截器
4. 更新所有服務層引用

### 第三階段: 預計算服務合併
1. 比較兩個預計算服務的功能
2. 合併為單一軌道預計算服務
3. 確保與衛星渲染器的兼容性

## ✅ 驗證檢查點
- [ ] API 響應格式保持一致
- [ ] 錯誤處理邏輯完整
- [ ] 所有引用都已更新
- [ ] 功能測試通過
- [ ] 無重複的 TypeScript 類型定義
