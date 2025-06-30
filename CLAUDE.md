# NTN Stack - Docker 專案環境

## 🚫 核心原則
**不要執行開發服務指令** - 不要執行 `npm run dev`、`npm run start` 等啟動服務的指令
**可以執行** - `npm run build`、`npm run lint`、`npm run test` 等建置/檢查指令

## 🐳 架構
- **NetStack** (`/netstack/`) - 5G 核心網，約 15+ 容器
- **SimWorld** (`/simworld/`) - 3D 仿真引擎，3 個容器

## 🚀 核心指令
```bash
# 啟動/停止 (根目錄)
make up      # 啟動所有服務
make down    # 停止所有服務  
make status  # 檢查狀態
make logs    # 查看日誌

# 容器內開發
docker exec -it simworld_backend bash    # 進入後端容器
docker exec simworld_backend python -c "<code>"  # 執行代碼
```

## 🌐 服務地址
- NetStack API: http://localhost:8080
- SimWorld Backend: http://localhost:8888  
- SimWorld Frontend: http://localhost:5173

## 📝 重要提醒
1. **服務啟動用 Docker** - 使用 `make up` 啟動服務，不要用 `npm run dev/start`
2. **建置檢查可用 npm** - `npm run build/lint/test` 等指令可以執行
3. **Python 開發在容器內** - 使用 `docker exec simworld_backend` 執行代碼

## ⚡ 代碼品質規範

### 開發流程
1. **先實現功能，後檢查品質** - 專注於功能實現，完成後執行 `npm run lint` 統一處理
2. **必須修復所有 error 級別問題**，warning 可選擇性修復
3. **提交前檢查** - 確保 `npm run lint` 無 error 才可提交

### 常見問題修復指南
1. **TypeScript any 類型**：
   - 使用具體類型替代 `any`
   - 如不確定類型，使用 `unknown` 
   - 示例：`data: any` → `data: Record<string, unknown>`

2. **未使用變數**：
   - 刪除不需要的變數
   - 必要時添加下劃線前綴：`_unusedVar`
   - 解構時使用：`{ data, ...rest }` 或 `{ data, _error }`

3. **React Hook 依賴**：
   - 添加缺失依賴到依賴陣列
   - 使用 `useCallback` 包裝函數
   - 使用 `useMemo` 包裝複雜計算

4. **組件導出問題**：
   - 組件檔案只導出 React 組件
   - 常數和工具函數移至獨立檔案
   - 使用 `export const` 而非 `export default` 導出常數

### Lint 規則優先級
- **Error (必修)**：型別錯誤、未使用變數、Hook 依賴
- **Warning (選修)**：組件導出、代碼風格、效能優化

## 🚨 錯誤處理原則 (極其重要)
**遇到 API 錯誤或任何錯誤時的處理優先順序：**
1. **優先使用 console.log 列印詳細錯誤信息** - 不要減少錯誤日誌的噪音
2. **回退使用模擬數據** - 確保應用程式繼續運行
3. **保持原始演算法複雜度** - 不要為了錯誤處理而簡化演算法
4. **維持真實數據處理邏輯** - 即使使用模擬數據也要保持完整的處理流程

**範例處理模式：**
```javascript
try {
  const realData = await fetchRealData();
  return processComplexAlgorithm(realData);
} catch (error) {
  console.log('API 錯誤詳細信息:', error);
  console.log('回退至模擬數據模式');
  const mockData = generateMockData();
  return processComplexAlgorithm(mockData); // 保持相同演算法
}
```