# 🤖 LEO衛星換手決策RL系統架構 - todo.md前置作業

## 🚨 當前真實狀態評估 (2025-07-13 更新)

### ⚠️ **重要澄清：目前處於基礎模擬階段**

**實際完成度：約20%** (非原文件暗示的95%)

#### ✅ **已完成部分**
- **基礎API連通性**: RL監控前端可以啟動訓練按鈕
- **前端UI框架**: RL監控界面基本完成
- **模擬訓練流程**: DQN算法可以模擬30個episodes的訓練過程
- **圖表同步修復**: 解決了圖表更新頻率不同步的問題

#### ❌ **關鍵技術缺失** (影響todo.md實施)
- **❌ 真實神經網路訓練**: 目前只是時間延遲模擬，無實際AI訓練
- **❌ 數據持久化**: 目前系統正在進行 PostgreSQL → MongoDB 遷移
- **❌ 雙重RL系統問題**: NetStack RL 監控 (port 8080) 與 RL System (port 8001) 數據不同步
- **❌ 真實衛星環境模擬**: 缺乏實際的LEO衛星切換場景
- **❌ 決策數據生成**: 無法提供真實的決策分析數據

### 🔴 **Phase 1.3 核心問題確認**

#### **雙重 RL 系統架構問題**
```
前端 → NetStack RL 監控 (port 8080) → 內存存儲
                    ↓ 代理調用
            RL System (port 8001) → PostgreSQL 存儲
```

**具體問題**:
1. **API 不匹配**: 前端期望 `/api/v1/rl/training/start/dqn`，實際訓練在 `/api/rl/start/DQN`
2. **數據同步問題**: 兩個系統的訓練狀態不同步
3. **維護複雜度**: 需要維護兩套API和數據格式

### 🎯 **核心目標：支援todo.md決策流程視覺化**

本系統的最終目的是實現以下完整流程：
```
3GPP事件觸發 → 事件處理 → 候選篩選 → RL決策整合 → 3D動畫觸發 → 執行監控 → 前端同步
```

**當前狀態**: 只有最後一環"前端同步"基本可用，前面的環節都需要真實數據支撐。

## 🔄 **Phase 1.3 解決方案：統一架構** (基於 CLAUDE.md 原則)

### 🎯 **採用單一 Port 方案** (推薦)

根據 CLAUDE.md 的 **KISS 原則** 和 **強制修復原則**，採用統一到 Port 8080 的方案：

```
前端 (localhost:5173)
    ↓ HTTP 調用
NetStack API (localhost:8080)
    ├── /api/v1/rl/training/start/:algorithm
    ├── /api/v1/rl/training/status
    └── /api/v1/rl/training/stop
    ↓ 內部調用 (不是 HTTP)
RL Training Engine (內部模組)
    ├── DQN Algorithm
    ├── PPO Algorithm  
    └── MongoDB Repository
```

### 🔧 **Phase 1.3 具體實施步驟**

#### **Phase 1.3a: 代碼整合** (1週)
```typescript
// 統一的 RL 訓練服務
class RLTrainingService {
  constructor(
    private dqnAlgorithm: DQNAlgorithm,
    private ppoAlgorithm: PPOAlgorithm,
    private sacAlgorithm: SACAlgorithm,
    private repository: MongoRLRepository
  ) {}

  async startTraining(algorithm: string, config: any): Promise<TrainingResult> {
    // 直接調用內部算法，無需 HTTP 代理
    const algo = this.getAlgorithm(algorithm);
    const session = await this.repository.createSession(algorithm, config);
    return await algo.startTraining(session);
  }
}
```

#### **Phase 1.3b: 服務統一** (1週)
- [ ] 將 `netstack/rl_system/` 代碼整合到 `netstack/src/services/rl-training/`
- [ ] 移除 `docker-compose.yml` 中的 rl-system 服務
- [ ] 更新前端 API 配置，統一調用 port 8080
- [ ] 實現統一的 WebSocket 推送機制

#### **Phase 1.3c: 驗證與測試** (1週)
- [ ] 端到端測試所有 RL 訓練功能
- [ ] 驗證統一 API 的完整性
- [ ] 性能測試確保無性能降低
- [ ] 清理所有 port 8001 相關代碼

### ✅ **符合 CLAUDE.md 原則的優勢**
- **✅ KISS 原則**: 單一端點，簡化架構
- **✅ 強制修復**: 徹底解決雙重系統問題
- **✅ 避免過度工程化**: 不需要複雜的服務間通訊
- **✅ 單一職責**: NetStack 負責 API，RL Engine 負責訓練

## 🔗 與todo.md的前置依賴關係

### 📊 **todo.md需要的研究級數據** (目前無法提供)
- **MongoDB實驗數據**: 訓練會話、performance指標、baseline比較
- **真實決策分析**: 候選衛星評分、決策推理過程、置信度
- **WebSocket即時推送**: 真實的訓練更新、決策狀態變化
- **算法切換數據**: 不同RL算法的性能比較數據
- **統計分析支援**: 收斂性分析、統計顯著性測試數據

### ⚠️ **當前數據品質問題**
- **模擬數據**: 目前提供假數據，無學術研究價值
- **數據庫遷移**: 正在進行 PostgreSQL → MongoDB 遷移
- **無歷史記錄**: 訓練完成後資源清除，無法支援實驗追蹤
- **決策透明度不足**: 無法提供Algorithm Explainability所需數據

## 🗄️ MongoDB 研究級數據庫架構

### 🎓 **研究級數據集合設計**

```javascript
// 研究實驗會話集合（支援todo.md實驗追蹤）
const rlExperimentSessions = {
  _id: ObjectId,
  experimentName: String,
  algorithmType: String, // "DQN", "PPO", "SAC"
  scenarioType: String, // "urban", "suburban", "low_latency"
  startTime: Date,
  endTime: Date,
  totalEpisodes: Number,
  sessionStatus: String, // "running", "stopped", "completed"
  hyperparameters: Object, // 完整的超參數記錄
  researchNotes: String, // 支援學術研究記錄
  createdAt: Date,
  updatedAt: Date
};

// 詳細訓練episode數據（支援決策透明化）
const rlTrainingEpisodes = {
  _id: ObjectId,
  sessionId: ObjectId,
  episodeNumber: Number,
  totalReward: Number,
  successRate: Number,
  handoverLatencyMs: Number, // 支援todo.md性能分析
  decisionConfidence: Number, // 支援Algorithm Explainability
  candidateSatellites: Array, // 支援候選篩選視覺化
  decisionReasoning: Object, // 支援決策透明化
  createdAt: Date
};

// 決策分析數據（支援todo.md視覺化）
const rlDecisionAnalysis = {
  _id: ObjectId,
  sessionId: ObjectId,
  episodeNumber: Number,
  candidateSatellites: Array, // 所有候選衛星信息
  scoringDetails: Object, // 每個候選的評分細節
  selectedSatelliteId: String,
  decisionFactors: Object, // 決策因子權重
  confidenceLevel: Number,
  reasoningPath: Object, // Algorithm Explainability數據
  createdAt: Date
};
```

## 📋 重新調整的開發階段 (基於 CLAUDE.md 原則)

### 🚧 **當前狀態：Phase 0 - 基礎模擬階段** (已完成)
- ✅ API連通性驗證
- ✅ 前端界面框架
- ✅ 基礎訓練流程模擬
- ⚠️ **使用模擬數據，無學術研究價值**

### 📊 **Phase 1: 架構統一與數據庫遷移** (7週)
**目標**: 解決雙重系統問題，建立統一架構

#### 1.1 MongoDB 基礎實施 (2週)
- [ ] 完成 NetStack PostgreSQL → MongoDB 遷移
- [ ] 實現 MongoDB 版本的 RL 數據存儲
- [ ] 建立研究級數據集合結構
- [ ] 實現數據遷移和備份機制

#### 1.2 數據持久化實現 (2週)
- [ ] 實現訓練會話的完整記錄
- [ ] 建立 episode 級別的詳細數據儲存
- [ ] 實現決策分析數據的結構化儲存
- [ ] 添加數據查詢和分析API

#### 1.3 統一架構實施 (3週)
- [ ] **1.3a**: 代碼整合 (1週)
- [ ] **1.3b**: 服務統一 (1週)
- [ ] **1.3c**: 驗證與測試 (1週)

**Phase 1 驗收標準：**
- [ ] 單一 Port 8080 統一架構
- [ ] MongoDB 完全運作，支援研究級數據
- [ ] 訓練數據完整持久化，支援歷史查詢
- [ ] WebSocket 推送真實數據，支援 todo.md 即時更新

### 🧠 **Phase 2: 簡化版真實訓練** (4-5週)
**目標**: 實現真實但簡化的神經網路訓練 (符合 KISS 原則)

#### 2.1 輕量級神經網路實現 (2週)
```python
# 符合 KISS 原則的簡化 DQN
class SimplifiedDQN(IRLAlgorithm):
    def __init__(self, config):
        # 簡單的 3 層神經網路
        self.network = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(state_size,)),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(action_size, activation='linear')
        ])
        self.memory = deque(maxlen=1000)
        
    def train(self):
        # 真實訓練，但簡化版本
        if len(self.memory) >= 32:
            self._train_network()
```

#### 2.2 基礎環境模擬 (2週)
- [ ] 建立基礎 LEO 衛星環境模擬
- [ ] 實現基本的切換場景生成
- [ ] 建立性能指標計算機制
- [ ] 生成 todo.md 需要的決策數據

#### 2.3 算法整合測試 (1週)
- [ ] 整合 DQN、PPO、SAC 的簡化版本
- [ ] 實現算法切換機制
- [ ] 測試訓練數據生成品質
- [ ] 驗證決策透明度數據

**Phase 2 驗收標準：**
- [ ] 真實神經網路訓練，無時間延遲模擬
- [ ] 生成有意義的決策數據
- [ ] 支援 Algorithm Explainability 基礎數據
- [ ] 算法可以產生不同的決策特徵

### 🎯 **Phase 3: 決策數據優化** (2週)
**目標**: 專門優化 todo.md 視覺化需求的數據

#### 3.1 視覺化數據格式 (1週)
- [ ] 實現候選衛星的多維度評分
- [ ] 建立決策推理路徑記錄
- [ ] 生成 Algorithm Explainability 數據
- [ ] 支援決策透明化視覺展示

#### 3.2 API 端點完善 (1週)
- [ ] 實現複雜查詢 API
- [ ] 建立 baseline 比較數據 API
- [ ] 添加實驗歷史查詢功能
- [ ] 優化 WebSocket 即時推送

**Phase 3 驗收標準：**
- [ ] 完整的候選衛星評分數據
- [ ] 支援 todo.md 候選篩選視覺化
- [ ] 提供決策透明化所需的所有數據
- [ ] API 響應時間 < 100ms (符合 CLAUDE.md 性能要求)

### 🔗 **Phase 4: todo.md 整合支援** (2週)
**目標**: 完整支援 todo.md 的視覺化需求

#### 4.1 數據接口驗證 (1週)
- [ ] 端到端決策流程數據測試
- [ ] 驗證 todo.md 所需的所有數據接口
- [ ] 確保數據品質達到學術研究標準
- [ ] 實現數據匯出功能

#### 4.2 整合測試與優化 (1週)
- [ ] 完整的決策流程數據測試
- [ ] 性能測試和穩定性驗證
- [ ] 用戶體驗測試和優化
- [ ] 文檔完善和交付準備

**Phase 4 驗收標準：**
- [ ] 完全支援 todo.md 的數據需求
- [ ] 決策流程產生完整、準確的研究數據
- [ ] 系統性能符合 CLAUDE.md 要求
- [ ] 數據品質符合論文發表標準

## ⏰ 調整後的時間估計

### 📅 **完整時間線**
| 階段 | 內容 | 預估時間 | 累計時間 | 主要改動 |
|-----|------|---------|----------|----------|
| Phase 0 | 基礎模擬階段 | ✅ 已完成 | - | - |
| Phase 1 | 架構統一與數據庫遷移 | 7週 | 7週 | **+3週** Phase 1.3 統一架構 |
| Phase 2 | 簡化版真實訓練 | 4-5週 | 11-12週 | **-2週** 簡化實現複雜度 |
| Phase 3 | 決策數據優化 | 2週 | 13-14週 | **-1週** 專注視覺化需求 |
| Phase 4 | todo.md 整合支援 | 2週 | 15-16週 | 保持不變 |

**總計：約15-16週 (3.5-4個月)** 相比原本節省 1-2週

### ✅ **改善重點**
1. **降低複雜度**: 簡化神經網路實現，專注決策數據生成
2. **統一架構**: 解決雙重系統問題，降低維護成本
3. **專注目標**: 重點支援 todo.md，避免過度工程化
4. **風險控制**: 符合 CLAUDE.md 原則，穩定可靠

### ⚠️ **關鍵風險 (已降低)**
- **架構複雜度**: ✅ 統一到單一 Port，降低複雜度
- **數據庫遷移**: ✅ 利用現有 MongoDB 遷移，降低風險
- **算法實現**: ✅ 簡化版神經網路，降低實現難度
- **整合測試**: ✅ 漸進式開發，每階段都可驗證

## 🎯 todo.md 整合計劃

### 📊 **數據依賴關係 (優化後)**
```
統一架構 + MongoDB (Phase 1)
    ↓
簡化版真實訓練數據 (Phase 2)  
    ↓
視覺化優化數據 (Phase 3)
    ↓
todo.md 完整支援 (Phase 4)
    ↓
完整決策流程視覺化
```

### 🔗 **關鍵整合點**
1. **Phase 1 完成**: 統一架構，消除雙重系統問題
2. **Phase 2 完成**: 提供真實但簡化的訓練數據
3. **Phase 3 完成**: 支援完整的決策透明化
4. **Phase 4 完成**: 完全支援 todo.md 視覺化需求

### ⚡ **平行開發策略**
- **Phase 1 期間**: todo.md 可開始基礎架構開發
- **Phase 2 期間**: todo.md 可使用 mock 數據進行視覺化開發
- **Phase 3-4 期間**: 替換為真實數據，驗證完整流程

## 🏆 最終目標：支援完整決策流程

### 🎯 **目標流程實現**
```
3GPP事件觸發 → 事件處理 → 候選篩選 → RL決策整合 → 3D動畫觸發 → 執行監控 → 前端同步
     ↓              ↓           ↓            ↓              ↓           ↓          ↓
  真實事件      處理邏輯    候選評分數據   簡化RL決策     視覺化數據    性能指標   研究數據
     ↓              ↓           ↓            ↓              ↓           ↓          ↓
MongoDB記錄      統計分析   透明化評分   Algorithm      todo.md支援   監控整合   論文數據
```

### 📊 **成功標準 (符合 CLAUDE.md)**
- [ ] **統一架構**: 單一 Port 8080，無雙重系統問題
- [ ] **真實訓練**: 簡化但真實的神經網路訓練
- [ ] **完整數據**: MongoDB 儲存所有研究數據
- [ ] **決策透明**: Algorithm Explainability 基礎實現
- [ ] **性能達標**: API 響應 < 100ms，系統穩定性 > 99%
- [ ] **todo.md 支援**: 提供所需的所有視覺化數據

---

**🎯 目標：建立符合 CLAUDE.md 軟體開發原則的學術研究級 LEO 衛星 RL 決策系統，統一架構，簡化實現，為 todo.md 提供高品質的研究級數據支援**

**📊 當前進度：20% | 預估完成時間：3.5-4個月 | 關鍵里程碑：統一架構 + MongoDB + 簡化版真實訓練**

## 🚨 當前狀態更新 (2025-07-13)

### ⚠️ **RL 監控功能暫時不可用**

**問題**: RL 監控系統依賴數據庫，且存在雙重系統架構問題

**影響範圍**:
- ❌ Navbar "🧠 RL 監控" 功能暫時禁用
- ❌ 雙重 RL 系統數據不同步問題
- ❌ PostgreSQL → MongoDB 遷移進行中
- ❌ 訓練數據無法正確持久化

**用戶體驗**:
- ✅ 點擊 "🧠 RL 監控" 顯示友好的暫時不可用消息
- ✅ 明確說明預計恢復時間 (7週，配合 Phase 1 完成)
- ✅ 解釋技術原因：架構統一和數據庫遷移

### 📋 **完整修復計劃**

**Phase 1 完成後**:
- ✅ 統一架構，無雙重系統問題
- ✅ MongoDB 完全運作
- ✅ 單一 Port 8080 服務
- ✅ 前端 RL 監控功能完全恢復
- ✅ 真實數據持久化和即時推送

**一致的用戶體驗策略**: 提供清楚的技術說明和realistic的恢復時間預期，確保用戶了解系統正在進行重要的架構改善。


