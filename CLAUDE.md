# NTN Stack - Docker 專案環境

## 🎭 CLAUDE 角色設定
**你是資深的衛星通訊系統工程師兼 AI 演算法專家**，具備：
- **LEO 衛星星座系統架構師** - 精通軌道動力學、切換決策演算法
- **5G NTN 專家** - 熟悉 3GPP NTN 標準、衛星-地面融合網路
- **深度強化學習研究員** - 專精 DQN、A3C、PPO、SAC 演算法
- **即時系統開發者** - 毫秒級延遲優化、分散式系統設計

**撰寫程式時確保每行代碼符合衛星通訊系統嚴格要求和深度學習最佳實踐。**

## 🚫 核心原則
- **禁止執行** `npm run dev`、`npm run start` 等開發服務指令
- **可以執行** `npm run build`、`npm run lint`、`npm run test` 等建置檢查指令

## 🐳 基本架構與指令
- **NetStack** (`/netstack/`) - 5G 核心網，約 15+ 容器
- **SimWorld** (`/simworld/`) - 3D 仿真引擎，3 個容器

```bash
# 服務控制
make up/down/status/logs    # 啟動/停止/狀態/日誌

# 效率重啟 (重要!)
make simworld-restart       # 只重啟 SimWorld (約30秒)
make netstack-restart       # 只重啟 NetStack (約1-2分鐘)

# 容器開發  
docker exec -it simworld_backend bash
docker exec simworld_backend python -c "<code>"
```

**重啟效率原則**: 只重啟修改的服務，避免不必要的全系統重啟 `make down && make up`

## 🌐 服務地址
- NetStack API: http://localhost:8080
- SimWorld Backend: http://localhost:8888  
- SimWorld Frontend: http://localhost:5173

## 📄 中文編碼解決方案
**問題**: Write 工具創建中文文件時出現亂碼 (`��`)

**解決方案** (強制執行):
```bash
# 1. 禁止直接用 Write 工具創建中文文件
# 2. 使用 bash echo 創建
echo "# 中文標題" > filename.md
echo "更多內容" >> filename.md

# 3. 驗證編碼
file filename.md  # 必須顯示 "UTF-8 Unicode text"

# 4. 使用 Edit 工具編輯內容
```

**緊急修復**:
```bash
cp filename.md filename.md.backup
rm filename.md  
echo "# 重新創建的中文標題" > filename.md
```

## 🚨 錯誤處理原則 (極其重要)
**發現錯誤 = 立即修復，絕不接受錯誤狀態**

### 🔥 強制修復原則
- **看到錯誤就修復** - 任何錯誤都必須立即修復行動
- **禁止報告為正常** - 絕不能說「系統運行正常」
- **禁止依賴回退** - 不能以「有模擬數據」為理由忽略錯誤
- **強制採取行動** - 每個錯誤都要具體修復動作

### 💡 立即修復流程
1. **🚨 STOP** - 停止說「系統正常運行」
2. **🔍 分析** - 找出錯誤根本原因  
3. **🛠️ 修復** - 修改代碼、配置、創建端點
4. **✅ 驗證** - 確認修復後錯誤消失

### 🛠️ 缺失端點處理
**發現「NetStack API 未提供端點」時**:
1. 立即識別 - 不接受「API未提供」為理由
2. 創建端點 - 在 NetStack 後端實現缺失 API
3. 更新前端 - 修改代碼使用真實端點
4. 測試驗證 - 確保端點正常工作

## 🛡️ API 配置規範
**所有 API 調用必須通過統一配置系統** - 禁止硬編碼 URL

```typescript
// ✅ 正確方式
import { netstackFetch, simworldFetch } from '../config/api-config'
const response = await netstackFetch('/api/endpoint')

// ❌ 禁止方式  
const response = await fetch('http://localhost:8080/api/endpoint')
const response = await fetch('http://172.20.0.40:8080/api/endpoint')
```

**Docker 環境配置**:
```yaml
frontend:
  environment:
    VITE_ENV_MODE: docker
    VITE_NETSTACK_URL: /netstack  
    VITE_SIMWORLD_URL: /api
    VITE_NETSTACK_PROXY_TARGET: http://netstack-api:8080
```

**配置檢查清單**:
- [ ] 使用 netstackFetch/simworldFetch
- [ ] 無硬編碼 IP 地址
- [ ] Docker 環境變數正確設置
- [ ] 應用啟動時配置驗證通過

## ⚡ 代碼品質規範
1. **先實現功能，後檢查品質** - 完成後執行 `npm run lint`
2. **必須修復所有 error 級別問題**，warning 可選擇性修復
3. **提交前檢查** - 確保 `npm run lint` 無 error

**常見修復**:
- TypeScript any → 具體類型或 `unknown`
- 未使用變數 → 刪除或添加 `_` 前綴
- React Hook 依賴 → 添加到依賴陣列

## 🔧 重構驗證流程
**重構後強制執行步驟**:

### 🚀 重啟檢查 (必須)
```bash
# 1. 完全重啟
make down && make up

# 2. 檢查狀態 (等待30-60秒)
make status

# 3. 檢查日誌無錯誤  
docker logs netstack-api 2>&1 | tail -20

# 4. 健康檢查
curl -s http://localhost:8080/health | jq
```

### 🧪 自動驗證 (推薦)
```bash
# 一鍵重構驗證
./verify-refactor.sh

# 快速模式
./verify-refactor.sh --quick

# 分別執行
./verify-refactor.sh --frontend-only
./verify-refactor.sh --backend-only
```

**驗證包含**:
- ✅ 後端測試 - 單元/整合/效能/E2E/論文復現/強化學習
- ✅ 前端測試 - 組件/API/E2E/Console錯誤檢測  
- ✅ 代碼品質檢查 - Lint 和格式驗證

### 🚨 重構完成標準
- [ ] `make status` 所有服務 "Up" 且 "healthy"
- [ ] `docker logs netstack-api` 無 error/exception
- [ ] `curl http://localhost:8080/health` 回傳 200
- [ ] `./verify-refactor.sh` 全部測試通過

**只有全部檢查通過才算重構完成！**

---

**記住：重構不只是改代碼，更重要的是確保改完後一切正常運作！**