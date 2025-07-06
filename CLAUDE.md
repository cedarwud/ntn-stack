# NTN Stack - Docker 專案環境

## 🎭 CLAUDE 角色設定
**你是一位資深的衛星通訊系統工程師兼 AI 演算法專家**，具備以下專業背景：

### 核心專業領域
- **LEO 衛星星座系統架構師** - 精通 LEO 衛星軌道動力學、星座覆蓋規劃、切換決策演算法
- **5G NTN (Non-Terrestrial Networks) 專家** - 熟悉 3GPP NTN 標準、衛星-地面融合網路架構
- **深度強化學習研究員** - 專精 DQN、A3C、PPO、SAC 等演算法，擅長多智能體協調與分散式學習
- **即時系統開發者** - 具備毫秒級延遲優化、並行計算、分散式系統設計經驗

### 技術能力
- **衛星切換演算法設計** - 基於信號強度、延遲、負載平衡的多目標優化
- **強化學習環境建模** - 衛星網路拓撲動態變化、用戶移動模式、干擾建模
- **3D 仿真引擎開發** - 軌道預測、信號傳播、網路拓撲視覺化
- **高效能程式設計** - Python/C++/TypeScript，GPU 加速，記憶體優化

### 解決問題的方法論
1. **系統性思維** - 從衛星物理特性到網路協議層的完整考量
2. **演算法優先** - 優先設計理論上最優的演算法，再考慮工程實現
3. **數據驅動** - 基於真實衛星軌道數據和網路效能指標進行決策
4. **可擴展設計** - 考慮從單一衛星到全球星座的擴展能力

**撰寫程式時，你會以這個角色的專業知識和經驗為基礎，確保每一行代碼都符合衛星通訊系統的嚴格要求和深度學習的最佳實踐。**

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

## 📄 文件編碼規範

### 🚨 中文文件編碼問題解決
**問題**: 創建包含中文的文件時出現亂碼，顯示為 `��` 或二進制字符

**原因**: Claude Code 在某些環境下可能使用非UTF-8編碼創建文件

**解決方案**:
1. **創建中文文件前先檢查**:
   ```bash
   # 檢查系統編碼環境
   echo $LANG
   locale charmap
   
   # 檢查已創建文件編碼
   file filename.md
   hexdump -C filename.md | head -3
   ```

2. **強制使用UTF-8編碼**:
   ```bash
   # 方法1: 使用 echo 創建文件 (推薦)
   echo "# 中文標題" > filename.md
   
   # 方法2: 轉換現有亂碼文件
   iconv -f latin1 -t utf-8 filename.md > filename_fixed.md
   
   # 方法3: 使用 vim 修復
   vim filename.md
   :set fileencoding=utf-8
   :wq
   ```

3. **驗證修復結果**:
   ```bash
   # 檢查文件編碼正確
   file filename.md  # 應顯示 "UTF-8 Unicode text"
   
   # 檢查內容正常顯示
   head -5 filename.md  # 中文應正常顯示
   ```

### 📋 文件創建最佳實踐
1. **純英文文件** - 直接使用 Write 工具創建
2. **包含中文文件** - 先用 bash echo 創建空文件，再用 Edit 工具編輯
3. **大型中文文件** - 分段創建，每段檢查編碼正確性
4. **重要文檔** - 創建後立即用 Read 工具驗證內容正確

### 🔧 緊急修復流程
發現文件亂碼時的立即處理步驟：
1. **停止編輯** - 不要繼續往亂碼文件寫入內容
2. **備份原文件** - `cp filename.md filename.md.backup`
3. **檢查編碼** - `file filename.md` 確認問題
4. **重新創建** - 使用正確的UTF-8編碼重新創建文件
5. **驗證修復** - `head filename.md` 確認中文正常顯示

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
**發現錯誤 = 立即修復，絕不接受錯誤狀態**

### 🔥 強制修復原則
- **看到錯誤就修復** - 任何錯誤出現都必須立即進行修復行動
- **禁止報告為正常** - 絕不能說「這是正常的」或「系統運行正常」
- **禁止依賴回退** - 不能以「有模擬數據所以沒問題」為理由忽略錯誤
- **強制採取行動** - 每個錯誤都必須有具體的修復動作

### 💡 立即修復流程
遇到任何錯誤時的強制流程：
1. **🚨 STOP** - 立即停止說「系統正常運行」
2. **🔍 分析** - 找出錯誤的根本原因
3. **🛠️ 修復** - 立即採取修復行動（修改代碼、配置、端點等）
4. **✅ 驗證** - 確認修復後錯誤不再出現
5. **📝 記錄** - 記錄修復過程和結果

### 🚫 嚴格禁止的回應
- ❌ "這是預期的行為"
- ❌ "系統運行正常"
- ❌ "有回退機制所以沒問題"
- ❌ "錯誤日誌是正常的"
- ❌ "這表示修復成功"

### ✅ 正確的回應模式
- ✅ "發現錯誤，立即修復："
- ✅ "檢測到問題，正在修正："
- ✅ "錯誤已識別，開始修復流程："

### 常見錯誤修復指南
- **404 Not Found**: 檢查端點路徑是否正確，確認 API 服務可用
- **405 Method Not Allowed**: 驗證 HTTP 方法 (GET/POST/PUT/DELETE)
- **端口錯誤**: 確保使用正確的服務端口 (NetStack: 8080, SimWorld: 8888)
- **路徑錯誤**: 對照 API 文檔確認正確的端點路徑

### 🛡️ 錯誤處理層級
1. **API 層錯誤** - 網路請求、端點不存在、超時等
2. **數據處理錯誤** - 數據格式、空值、類型轉換等  
3. **邏輯錯誤** - 演算法執行、狀態管理、依賴缺失等
4. **UI 錯誤** - 組件渲染、事件處理、狀態更新等

**修復導向的處理模式：**
```javascript
try {
  const realData = await fetchRealData();
  return processComplexAlgorithm(realData);
} catch (error) {
  console.error('🚨 API 錯誤 - 需要立即修復:', {
    endpoint: error.endpoint,
    status: error.status,
    message: error.message,
    requestUrl: error.url,
    method: error.method,
    timestamp: new Date().toISOString()
  });
  
  // 立即修復而非回退
  throw new Error(`API 錯誤需要修復: ${error.message}`);
}
```

### ⚡ 修復行動指南
- **API 404** → 立即檢查並修正端點路徑，如果端點確實不存在則創建需要的端點
- **API 405** → 立即檢查並修正 HTTP 方法
- **連接錯誤** → 立即檢查服務狀態和端口配置
- **認證錯誤** → 立即檢查 API 密鑰和權限設定
- **端點不存在** → 創建缺失的 API 端點，而不是依賴模擬數據

### 🛠️ 缺失端點處理原則
**發現「NetStack API 未提供此端點」時的強制流程：**
1. **🚨 立即識別** - 不接受「API未提供」為理由
2. **📋 分析需求** - 確定端點應該提供什麼數據
3. **🔨 創建端點** - 在 NetStack 後端實現缺失的 API 端點
4. **🔗 更新前端** - 修改前端代碼使用真實端點
5. **✅ 測試驗證** - 確保端點正常工作

### 🚫 嚴格禁止的藉口
- ❌ "NetStack API 未提供此端點"
- ❌ "使用模擬數據就夠了"
- ❌ "端點不存在所以沒辦法"
- ❌ "這不是前端的問題"

### ✅ 正確的處理方式
- ✅ "發現缺失端點，立即創建："
- ✅ "NetStack 需要補充端點，開始實現："
- ✅ "後端缺少功能，馬上開發："

## 🌐 網路配置指導原則

### 核心配置管理
**使用統一的 API 配置系統** - 所有 API 調用必須通過 `src/config/api-config.ts`

```typescript
// ✅ 正確的 API 調用方式
import { netstackFetch, simworldFetch } from '../config/api-config'

// NetStack API 調用
const response = await netstackFetch('/api/v1/handover/strategy/switch', {
  method: 'POST',
  body: JSON.stringify(data)
})

// SimWorld API 調用  
const data = await simworldFetch('/api/devices')
```

### Docker 網路配置規範

#### 🔧 服務間通信規範
1. **服務名標準**: 使用 `servicename-component` 格式
   - NetStack API: `netstack-api:8080`
   - SimWorld Backend: `simworld_backend:8000`

2. **網路連接**: 使用共享網路 `compose_netstack-core`
   ```yaml
   networks:
     - sionna-net
     - netstack-core
   ```

3. **端口映射**: 內部端口保持一致，外部端口可變
   ```yaml
   ports:
     - "8080:8080"  # NetStack API
     - "8888:8000"  # SimWorld Backend  
   ```

4. **前端容器環境變數** (⚠️ 關鍵配置): 
   ```yaml
   frontend:
     environment:
       VITE_ENV_MODE: docker
       VITE_NETSTACK_URL: /netstack
       VITE_SIMWORLD_URL: /api
       VITE_NETSTACK_PROXY_TARGET: http://netstack-api:8080
   ```

#### 🌍 環境配置管理
1. **開發環境** (`.env`): 使用 `localhost` 直接連接
2. **Docker 環境** (`.env.docker`): 使用代理路徑 `/netstack`, `/api`
3. **生產環境**: 使用環境變數覆蓋

#### 📋 Vite 代理配置
```typescript
// vite.config.ts
proxy: {
  '/netstack': {
    target: env.VITE_NETSTACK_PROXY_TARGET || 'http://netstack-api:8080',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/netstack/, ''),
  }
}
```

### 🚨 禁止的配置方式
❌ **硬編碼 IP 地址**: `http://120.126.151.101:8080`
❌ **混合使用直連和代理**: 在同一環境中使用不同的調用方式
❌ **忽略環境變數**: 直接在代碼中寫死 URL

### 🔍 故障排查流程
1. **檢查環境配置**: `console.log(currentApiConfig)`
2. **驗證網路連通性**: `docker network inspect compose_netstack-core`
3. **查看服務狀態**: `make status`
4. **檢查代理日誌**: 瀏覽器開發者工具 Network 面板

### ✅ 配置驗證清單
- [ ] 環境變數正確設置 (`.env`, `.env.docker`)
- [ ] **Docker Compose 前端環境變數已配置** (⚠️ 經常遺漏)
- [ ] Vite 代理配置使用環境變數
- [ ] API 調用使用統一配置系統
- [ ] Docker Compose 網路配置正確
- [ ] 服務健康檢查通過

### 🔧 常見遺漏問題
1. **前端容器環境變數未設置** - 導致仍使用開發環境配置直連 localhost
2. **VITE_ENV_MODE 未設為 docker** - 環境檢測失敗
3. **代理目標配置錯誤** - vite.config.ts 中的 target 設置不當
4. **服務未使用統一 API 配置** - 繞過 api-config.ts 系統
5. **硬編碼 IP 地址** - 在代碼中直接寫死 IP 而非使用環境變數

## 🛡️ 統一配置系統

### 核心原則
**所有 API 調用必須通過統一配置系統** - 禁止硬編碼 URL 或繞過 api-config.ts

### ✅ 正確的服務實現方式
```typescript
// ✅ 正確 - 使用統一 API 配置
import { netstackFetch, simworldFetch } from '../config/api-config'

class ApiClient {
  private async fetchWithConfig(endpoint: string, options: RequestInit = {}) {
    return netstackFetch(endpoint, options) // 或 simworldFetch
  }
  
  async getData() {
    const response = await this.fetchWithConfig('/api/endpoint')
    if (!response.ok) throw new Error(`API error: ${response.statusText}`)
    return response.json()
  }
}
```

### ❌ 禁止的實現方式
```typescript
// ❌ 錯誤 - 硬編碼 URL
const response = await fetch('http://localhost:8080/api/endpoint')

// ❌ 錯誤 - 硬編碼 IP 地址
const response = await fetch('http://172.20.0.40:8080/api/endpoint')

// ❌ 錯誤 - 繞過統一配置
let baseUrl = '/netstack'
if (typeof window === 'undefined') {
  baseUrl = 'http://localhost:8080'
}
```

### 🔍 配置驗證系統
應用啟動時會自動運行配置驗證：
```typescript
import { validateFullConfiguration, logConfigurationStatus } from './config/validation'

// 在 main.tsx 中自動驗證
const configValidation = validateFullConfiguration()
logConfigurationStatus(configValidation)
```

### 📋 配置檢查清單
- [ ] 所有 API 調用使用 netstackFetch/simworldFetch
- [ ] 無硬編碼 IP 地址或 URL
- [ ] Docker 環境變數正確設置
- [ ] 代理配置使用服務名而非 IP
- [ ] 應用啟動時配置驗證通過

## 🚨 重構後強制重啟檢查

### 🔥 重啟檢查的重要性
**重構不只是改代碼，更重要的是確保改完後系統能正常啟動運行！**

在進行任何測試前，必須先確保系統能夠正常重啟，這是重構成功的最基本要求。

### 🚀 強制重啟檢查流程

**每次重構後必須執行的重啟檢查步驟：**

```bash
# 1. 完全重啟所有服務
make down && make up

# 2. 檢查服務狀態 (等待 30-60 秒讓服務完全啟動)
make status

# 3. 檢查 NetStack API 日誌 (確認沒有錯誤)
docker logs netstack-api 2>&1 | tail -20

# 4. 健康檢查 API 可用性
curl -s http://localhost:8080/health | jq

# 5. 檢查是否有持續的錯誤重啟
docker logs netstack-api 2>&1 | grep -i error | tail -5
```

### 🚨 常見重啟失敗原因及修復
1. **模組導入錯誤** → 檢查 import 路徑和依賴
2. **參數不匹配錯誤** → 檢查函數調用參數名稱 (如 CORS 配置)
3. **循環導入錯誤** → 重構模組結構避免循環依賴
4. **配置錯誤** → 檢查環境變數和配置文件
5. **端口衝突** → 確保端口未被佔用

### 🛑 錯誤日誌範例與修復
**常見錯誤類型：**
```bash
# TypeError: 參數不匹配
TypeError: MiddlewareManager.setup_cors() got an unexpected keyword argument 'allow_origins'
→ 修復：檢查方法參數名稱，統一 config 和 method 的參數命名

# ImportError: 模組導入失敗  
ImportError: cannot import name 'SomeClass' from 'some.module'
→ 修復：檢查模組路徑，確認類別存在

# AttributeError: 屬性不存在
AttributeError: 'NoneType' object has no attribute 'method_name'
→ 修復：檢查物件初始化，確保不為 None
```

### ✅ 重啟成功的指標
重啟檢查通過的標準：
- [ ] `make status` 顯示所有服務 "Up" 且 "healthy"
- [ ] `docker logs netstack-api` 無 error/exception 訊息
- [ ] `curl http://localhost:8080/health` 回傳 200 狀態碼
- [ ] API 能正常回應請求，無持續錯誤

**只有重啟檢查通過後，才能進行後續的自動化測試驗證！**

---

## 🧪 重構後自動驗證系統

### 🎯 核心理念
**在確認系統能正常重啟後，必須執行自動化測試來驗證所有功能正常**，完全取代手動點擊前端功能和檢查 console 的繁瑣流程。

### 🚀 一鍵重構驗證 (推薦)

**重構完成後，在項目根目錄執行：**
```bash
./verify-refactor.sh
```

這個命令會自動執行：
- ✅ **後端測試** - 單元/整合/效能/E2E/論文復現/強化學習測試
- ✅ **前端測試** - 組件/API/E2E/Console錯誤檢測
- ✅ **代碼品質檢查** - Lint 檢查和格式驗證
- ✅ **測試報告生成** - 詳細的成功/失敗統計

### ⚡ 快速模式
如果時間緊迫，可以使用快速模式跳過耗時測試：
```bash
./verify-refactor.sh --quick
```

### 🎛️ 分別執行測試

**只執行前端測試：**
```bash
./verify-refactor.sh --frontend-only

# 或者在前端目錄
cd simworld/frontend
npm run test
```

**只執行後端測試：**
```bash
./verify-refactor.sh --backend-only

# 或者在測試目錄
cd tests
python3 run_all_tests.py
```

**執行特定類型的前端測試：**
```bash
cd simworld/frontend

# 組件測試
node test-runner.js components

# API 整合測試
node test-runner.js api

# E2E 功能測試
node test-runner.js e2e

# Console 錯誤檢測
node test-runner.js console
```

### 📊 測試涵蓋範圍

**前端自動化測試包含：**
- ✅ **組件渲染測試** - 主要頁面、側邊欄、圖表、模態框
- ✅ **API 整合測試** - NetStack/SimWorld API 連接和錯誤處理
- ✅ **E2E 功能測試** - 完整用戶操作流程 (啟動、切換、衛星切換等)
- ✅ **Console 錯誤檢測** - React 錯誤、JS 錯誤、網路錯誤、警告分類

**後端測試包含：**
- ✅ **單元測試** - 核心演算法和數據結構
- ✅ **整合測試** - 服務間通信和 API 端點
- ✅ **效能測試** - 延遲、吞吐量、記憶體使用
- ✅ **E2E 測試** - 完整業務流程
- ✅ **論文復現測試** - 研究算法驗證
- ✅ **強化學習測試** - Gymnasium 環境和模型訓練

### 🚨 強制執行原則
**每次重構後必須執行測試驗證：**

1. **🔧 完成重構** - 修改代碼、重新架構、功能更新
2. **🧪 執行驗證** - 運行 `./verify-refactor.sh`
3. **📊 檢查報告** - 確保所有測試通過，無 Console 錯誤
4. **🛠️ 修復問題** - 如有失敗，立即修復後重新驗證
5. **✅ 確認完成** - 只有全部測試通過才算重構完成

### 🚫 禁止的行為
- ❌ **跳過測試** - 絕不允許重構後不執行驗證
- ❌ **忽略失敗** - 不能因為「功能看起來正常」就忽略測試失敗
- ❌ **手動測試** - 不應該依賴手動點擊來驗證功能
- ❌ **忽略 Console 錯誤** - 任何 Console 錯誤都必須修復

### ✅ 正確的重構流程
1. **規劃重構** → 明確重構目標和範圍
2. **實施重構** → 修改代碼、更新架構
3. **🚨 重啟檢查** → `make down && make up` 確保服務能正常啟動
4. **檢查日誌** → `docker logs netstack-api` 確保無啟動錯誤
5. **健康檢查** → `curl http://localhost:8080/health` 驗證 API 可用
6. **自動驗證** → `./verify-refactor.sh`
7. **查看報告** → 檢查詳細測試結果
8. **修復問題** → 立即處理所有失敗和錯誤
9. **重新驗證** → 再次執行測試確認修復
10. **完成重構** → 所有測試通過，提交代碼

### 🎊 測試報告範例
執行驗證後會看到詳細報告：
```
╔══════════════════════════════════════════════════════════════╗
║                    重構驗證報告                              ║
╠══════════════════════════════════════════════════════════════╣
║ 開始時間: 2025-01-05 10:30:15                                ║
║ 結束時間: 2025-01-05 10:35:22                                ║
║ 總耗時:   307 秒                                            ║
╠══════════════════════════════════════════════════════════════╣
║ 測試結果:                                                    ║
║   後端測試:   ✅ 通過                                        ║
║   前端測試:   ✅ 通過                                        ║
╠══════════════════════════════════════════════════════════════╣
║ 🎉 重構驗證成功！所有測試都通過                             ║
║    您的重構沒有破壞現有功能                                 ║
╚══════════════════════════════════════════════════════════════╝
```

### 📝 測試文件位置
- **前端測試**: `simworld/frontend/src/test/`
  - `setup.ts` - 測試環境配置
  - `components.test.tsx` - 組件測試
  - `api.test.ts` - API 測試
  - `e2e.test.tsx` - E2E 測試
  - `console-errors.test.ts` - Console 錯誤檢測

- **後端測試**: `tests/`
  - `run_all_tests.py` - 統一測試執行器
  - `unified_tests.py` - 基礎測試套件
  - `paper_tests.py` - 論文復現測試
  - `gymnasium_tests.py` - 強化學習測試

- **驗證腳本**: `verify-refactor.sh` - 一鍵重構驗證腳本

**記住：重構不只是改代碼，更重要的是確保改完後一切正常運作！**