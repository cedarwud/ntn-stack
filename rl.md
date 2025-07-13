# 🤖 LEO衛星換手決策RL系統架構 - todo.md前置作業

## 🚨 當前真實狀態評估 (2025-07-12)

### ⚠️ **重要澄清：目前處於基礎模擬階段**

**實際完成度：約20%** (非原文件暗示的95%)

#### ✅ **已完成部分**
- **基礎API連通性**: RL監控前端可以啟動訓練按鈕
- **前端UI框架**: RL監控界面基本完成
- **模擬訓練流程**: DQN算法可以模擬30個episodes的訓練過程
- **圖表同步修復**: 解決了圖表更新頻率不同步的問題

#### ❌ **關鍵技術缺失** (影響todo.md實施)
- **❌ 真實神經網路訓練**: 目前只是時間延遲模擬，無實際AI訓練
- **❌ PostgreSQL數據儲存**: 使用MockRepository，訓練數據無法持久化
- **❌ 真實衛星環境模擬**: 缺乏實際的LEO衛星切換場景
- **❌ 決策數據生成**: 無法提供真實的決策分析數據
- **❌ 模型保存與載入**: 缺乏訓練模型的實際儲存機制

### 🎯 **核心目標：支援todo.md決策流程視覺化**

本系統的最終目的是實現以下完整流程：
```
3GPP事件觸發 → 事件處理 → 候選篩選 → RL決策整合 → 3D動畫觸發 → 執行監控 → 前端同步
```

**當前狀態**: 只有最後一環"前端同步"基本可用，前面的環節都需要真實數據支撐。

## 🔗 與todo.md的前置依賴關係

### 📊 **todo.md需要的研究級數據** (目前無法提供)
- **PostgreSQL實驗數據**: 訓練會話、performance指標、baseline比較
- **真實決策分析**: 候選衛星評分、決策推理過程、置信度
- **WebSocket即時推送**: 真實的訓練更新、決策狀態變化
- **算法切換數據**: 不同RL算法的性能比較數據
- **統計分析支援**: 收斂性分析、統計顯著性測試數據

### ⚠️ **當前數據品質問題**
- **模擬數據**: MockRepository提供假數據，無學術研究價值
- **無歷史記錄**: 訓練完成後資源清除，無法支援實驗追蹤
- **缺乏統計基礎**: 無真實訓練指標，無法進行科學分析
- **決策透明度不足**: 無法提供Algorithm Explainability所需數據

## 🗄️ 真實數據儲存架構實施策略

### 🎓 **PostgreSQL研究級數據庫** (急需實施)

#### 核心數據表設計
```sql
-- 研究實驗會話表（支援todo.md實驗追蹤）
CREATE TABLE rl_experiment_sessions (
    id BIGSERIAL PRIMARY KEY,
    experiment_name VARCHAR(100) NOT NULL,
    algorithm_type VARCHAR(20) NOT NULL,
    scenario_type VARCHAR(50), -- urban, suburban, low_latency
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    total_episodes INTEGER DEFAULT 0,
    session_status VARCHAR(20) DEFAULT "running",
    hyperparameters JSONB, -- 完整的超參數記錄
    research_notes TEXT, -- 支援學術研究記錄
    INDEX idx_algorithm_scenario (algorithm_type, scenario_type)
);

-- 詳細訓練episode數據（支援決策透明化）
CREATE TABLE rl_training_episodes (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT REFERENCES rl_experiment_sessions(id),
    episode_number INTEGER NOT NULL,
    total_reward FLOAT,
    success_rate FLOAT,
    handover_latency_ms FLOAT, -- 支援todo.md性能分析
    decision_confidence FLOAT, -- 支援Algorithm Explainability
    candidate_satellites JSONB, -- 支援候選篩選視覺化
    decision_reasoning JSONB, -- 支援決策透明化
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 決策分析數據（支援todo.md視覺化）
CREATE TABLE rl_decision_analysis (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT REFERENCES rl_experiment_sessions(id),
    episode_number INTEGER,
    candidate_satellites JSONB, -- 所有候選衛星信息
    scoring_details JSONB, -- 每個候選的評分細節
    selected_satellite_id VARCHAR(50),
    decision_factors JSONB, -- 決策因子權重
    confidence_level FLOAT,
    reasoning_path JSONB, -- Algorithm Explainability數據
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 📊 **MockRepository → PostgreSQL 遷移計劃**
1. **Phase A1**: 實施真實PostgreSQL連接和基礎表創建
2. **Phase A2**: 替換MockRepository為真實數據庫操作
3. **Phase A3**: 實現複雜查詢支援，供todo.md使用
4. **Phase A4**: 添加WebSocket即時推送真實數據更新

## 🧠 真實RL算法實施計劃

### ❌ **當前DQN問題分析**
```python
# 當前實現：僅為模擬
def train(self):
    time.sleep(step_time)  # 只是時間延遲
    self._current_episode += 1  # 簡單計數
    self._last_reward = random.uniform(-10, 10)  # 隨機數
    # 無實際神經網路訓練
```

### ✅ **真實DQN實施目標**
```python
# 目標實現：真實神經網路訓練
class RealDQNAlgorithm(IRLAlgorithm):
    def __init__(self, config):
        self.model = self._build_neural_network()  # 真實神經網路
        self.target_model = self._build_neural_network()
        self.memory = deque(maxlen=10000)  # 經驗回放
        self.environment = SatelliteHandoverEnvironment()  # 真實環境
        
    def train(self):
        # 真實的DQN訓練邏輯
        state = self.environment.reset()
        for step in range(max_steps):
            action = self._epsilon_greedy_action(state)
            next_state, reward, done = self.environment.step(action)
            self._store_experience(state, action, reward, next_state, done)
            self._train_network()  # 實際網路訓練
            state = next_state
```

### 🛰️ **LEO衛星環境模擬器** (支援真實決策數據)
```python
class SatelliteHandoverEnvironment:
    """真實的LEO衛星切換環境模擬"""
    
    def __init__(self):
        self.satellites = self._initialize_leo_constellation()  # 550顆衛星
        self.ground_terminals = self._initialize_terminals()
        self.current_connections = {}
        
    def step(self, handover_decision):
        """執行切換決策，生成真實的決策數據"""
        candidates = self._get_candidate_satellites()
        selected = candidates[handover_decision]
        
        # 計算切換性能指標
        latency = self._calculate_handover_latency(selected)
        success_rate = self._calculate_success_probability(selected)
        
        # 生成決策分析數據（供todo.md使用）
        decision_data = {
            "candidates": candidates,
            "selected": selected,
            "reasoning": self._generate_decision_reasoning(),
            "confidence": self._calculate_confidence_level()
        }
        
        return new_state, reward, done, decision_data
```

## 📋 重新定義的開發階段 (實際進度)

### 🚧 **當前狀態：Phase 0 - 基礎模擬階段** (已完成)
- ✅ API連通性驗證
- ✅ 前端界面框架
- ✅ 基礎訓練流程模擬
- ⚠️ **使用模擬數據，無學術研究價值**

### 📊 **Phase 1: PostgreSQL真實數據儲存** (4-6週)
**目標**: 建立研究級數據儲存，支援todo.md

#### 1.1 PostgreSQL基礎實施 (2週)
- [ ] 建立真實PostgreSQL數據庫連接
- [ ] 實現完整的研究級數據表結構
- [ ] 替換MockRepository為真實數據庫操作
- [ ] 建立數據遷移和備份機制

#### 1.2 數據持久化實現 (2週)  
- [ ] 實現訓練會話的完整記錄
- [ ] 建立episode級別的詳細數據儲存
- [ ] 實現決策分析數據的結構化儲存
- [ ] 添加數據查詢和分析API

#### 1.3 WebSocket真實推送 (1-2週)
- [ ] 實現基於真實數據的WebSocket推送
- [ ] 建立訓練進度的即時更新機制
- [ ] 實現決策數據的即時廣播
- [ ] 測試高頻數據推送的性能

**Phase 1 驗收標準：**
- [ ] PostgreSQL數據庫完全運作，無MockRepository
- [ ] 訓練數據完整持久化，支援歷史查詢
- [ ] WebSocket推送真實數據，支援todo.md即時更新
- [ ] 數據品質達到學術研究標準

### 🧠 **Phase 2: 真實RL算法實現** (6-8週)
**目標**: 實現真正的神經網路訓練，產生有價值的決策數據

#### 2.1 LEO衛星環境模擬器 (3週)
- [ ] 建立真實的LEO衛星軌道模型
- [ ] 實現衛星-地面站的真實通訊模擬
- [ ] 建立切換場景和性能指標計算
- [ ] 實現多種場景類型(urban, suburban, maritime)

#### 2.2 真實DQN神經網路 (2-3週)
- [ ] 實現完整的DQN神經網路架構
- [ ] 建立經驗回放和目標網路更新
- [ ] 實現ε-greedy探索策略
- [ ] 添加訓練收斂性監控

#### 2.3 PPO和SAC算法 (2-3週)
- [ ] 實現PPO的Actor-Critic架構
- [ ] 實現SAC的雙評論家網路
- [ ] 建立算法切換機制
- [ ] 實現算法性能比較分析

**Phase 2 驗收標準：**
- [ ] 真實神經網路訓練，無時間延遲模擬
- [ ] 生成有意義的決策數據和學習曲線
- [ ] 算法可以產生不同的切換策略
- [ ] 支援Algorithm Explainability所需數據

### 🎯 **Phase 3: 決策數據生成** (2-3週)
**目標**: 產生todo.md所需的決策分析數據

#### 3.1 候選篩選分析 (1週)
- [ ] 實現候選衛星的多維度評分
- [ ] 建立評分因子權重調整機制
- [ ] 生成評分置信度和統計數據
- [ ] 支援比較分析和篩選透明化

#### 3.2 決策推理數據 (1-2週)
- [ ] 實現決策推理路徑的記錄
- [ ] 建立決策樹和分支分析
- [ ] 生成Algorithm Explainability數據
- [ ] 支援What-if分析和反事實推理

**Phase 3 驗收標準：**
- [ ] 完整的候選衛星評分數據
- [ ] 支援todo.md候選篩選視覺化
- [ ] 提供決策透明化所需的所有數據
- [ ] 支援Algorithm Explainability研究

### 🔗 **Phase 4: todo.md整合支援** (2週)
**目標**: 為todo.md提供完整的數據支援

#### 4.1 研究級API開發 (1週)
- [ ] 實現複雜查詢API支援統計分析
- [ ] 建立baseline比較數據API
- [ ] 實現實驗歷史查詢和回放API
- [ ] 添加數據匯出功能支援論文撰寫

#### 4.2 整合測試與驗證 (1週)
- [ ] 端到端的決策流程數據測試
- [ ] 確保數據品質達到學術研究標準
- [ ] 驗證todo.md所需的所有數據接口
- [ ] 性能測試和穩定性驗證

**Phase 4 驗收標準：**
- [ ] 完全支援todo.md的數據需求
- [ ] 決策流程產生完整、準確的研究數據
- [ ] 系統可支援長期的學術研究實驗
- [ ] 數據品質符合論文發表標準

## ⏰ 實際時間估計

### 📅 **完整時間線**
| 階段 | 內容 | 預估時間 | 累計時間 |
|-----|------|---------|----------|
| Phase 0 | 基礎模擬階段 | ✅ 已完成 | - |
| Phase 1 | PostgreSQL真實儲存 | 4-6週 | 6週 |
| Phase 2 | 真實RL算法實現 | 6-8週 | 12-14週 |
| Phase 3 | 決策數據生成 | 2-3週 | 15-16週 |
| Phase 4 | todo.md整合支援 | 2週 | 17-18週 |

**總計：約4-5個月** 才能完全支援todo.md的學術研究需求

### ⚠️ **關鍵風險**
- **神經網路訓練複雜度**: 真實DQN/PPO/SAC實現比預期困難
- **衛星環境模擬精度**: LEO軌道和通訊模型的實現挑戰
- **數據品質保證**: 確保生成的數據符合學術研究標準
- **性能優化需求**: 真實訓練可能比模擬慢數十倍

## 🎯 todo.md整合計劃

### 📊 **數據依賴關係**
```
PostgreSQL研究數據 (Phase 1)
    ↓
真實RL訓練數據 (Phase 2)  
    ↓
決策分析數據 (Phase 3)
    ↓
todo.md視覺化支援 (Phase 4)
    ↓
完整決策流程視覺化
```

### 🔗 **關鍵整合點**
1. **Phase 1完成**: todo.md可開始使用真實PostgreSQL數據
2. **Phase 2完成**: 提供真實的RL訓練指標和學習曲線
3. **Phase 3完成**: 支援完整的Algorithm Explainability
4. **Phase 4完成**: 完全支援決策流程視覺化

### ⚡ **平行開發策略**
- **todo.md前期**: 使用mock data進行視覺化開發
- **RL系統中期**: 專注於真實數據生成品質
- **整合後期**: 替換mock data為真實數據，驗證完整流程

## 🚫 不使用模擬數據的重要性

### ❌ **模擬數據的學術問題**
- **無統計意義**: 隨機生成的數據無法支援統計分析
- **缺乏收斂性**: 無法展示真實的學習過程和收斂特性
- **決策邏輯缺失**: 無法提供真實的決策推理過程
- **無比較基礎**: 無法與baseline算法進行有意義的比較

### ✅ **真實數據的研究價值**
- **統計顯著性**: 支援學術論文的統計分析需求
- **算法透明化**: 提供真實的Algorithm Explainability數據
- **實驗可重現性**: 確保研究結果的可重現性
- **學術貢獻價值**: 支援高品質論文發表和學術展示

## 🏆 最終目標：支援完整決策流程

### 🎯 **目標流程實現**
```
3GPP事件觸發 → 事件處理 → 候選篩選 → RL決策整合 → 3D動畫觸發 → 執行監控 → 前端同步
     ↓              ↓           ↓            ↓              ↓           ↓          ↓
  真實事件      處理邏輯    候選評分數據   真實RL決策     視覺化數據    性能指標   研究數據
     ↓              ↓           ↓            ↓              ↓           ↓          ↓
PostgreSQL記錄  統計分析   透明化評分   Algorithm    todo.md支援  監控整合   論文數據
```

### 📊 **成功標準**
- [ ] **真實神經網路訓練**: 無任何模擬或時間延遲
- [ ] **完整數據持久化**: PostgreSQL儲存所有研究數據
- [ ] **決策透明化**: Algorithm Explainability完全實現
- [ ] **學術研究就緒**: 支援論文撰寫和學術展示
- [ ] **todo.md完全支援**: 提供所需的所有視覺化數據

---

**🎯 目標：建立真正的學術研究級LEO衛星RL決策系統，完全摒棄模擬數據，為todo.md提供高品質的研究級數據支援**

**📊 當前進度：20% | 預估完成時間：4-5個月 | 關鍵依賴：PostgreSQL + 真實神經網路訓練**

## 🚨 當前狀態更新 (2025-07-13 數據庫遷移期間)

### ⚠️ **RL 監控功能暫時不可用**

**問題**: RL 監控系統依賴 PostgreSQL 數據庫，但目前系統正在進行 PostgreSQL → MongoDB 遷移

**影響範圍**:
- ❌ Navbar "🧠 RL 監控" 功能暫時禁用
- ❌ DQN、PPO、SAC 算法訓練無法正常啟動和狀態追蹤
- ❌ 訓練數據無法持久化到數據庫
- ❌ 實時監控圖表和性能指標無法顯示

**用戶體驗**:
- ✅ 點擊 "🧠 RL 監控" 顯示友好的暫時不可用消息
- ✅ 明確說明預計恢復時間 (3-4 週)
- ✅ 解釋技術原因和遷移進度

### 📋 **修復計劃與時間表**

#### **Phase 3: RL 系統數據庫遷移** (2-3 週)
**目標**: 將 NetStack RL 系統從 PostgreSQL 遷移到 MongoDB

**具體任務**:
- [ ] 修復 NetStack RL API 的數據庫連接問題
- [ ] 將 RL 訓練會話管理從 PostgreSQL 遷移到 MongoDB
- [ ] 更新 RL 決策引擎的數據庫依賴
- [ ] 實現 MongoDB 版本的訓練狀態持久化
- [ ] 修復前端 RL 監控的 API 連接

**關鍵依賴**:
- NetStack PostgreSQL → MongoDB 整體遷移
- RL 系統架構的數據庫抽象層重構

#### **Phase 4: RL 監控功能驗證** (1 週)
**目標**: 恢復並驗證完整的 RL 監控功能

**具體任務**:
- [ ] 測試 DQN、PPO、SAC 訓練啟動和停止
- [ ] 驗證訓練狀態實時同步
- [ ] 確認訓練數據正確持久化到 MongoDB
- [ ] 測試前端監控圖表和性能指標顯示
- [ ] 端到端功能測試和性能優化

**驗收標準**:
- [ ] Navbar "🧠 RL 監控" 正常工作
- [ ] 所有 RL 算法可以正常啟動和監控
- [ ] 訓練數據完整存儲在 MongoDB 中
- [ ] 前端實時圖表正常更新
- [ ] 無 PostgreSQL 相關錯誤

### 🔧 **當前解決方案**

#### **前端修改** (已完成)
- ✅ 暫時禁用  Hook 以停止無限 API 輪詢
- ✅ 在 RL 監控 Modal 中顯示友好的不可用消息
- ✅ 提供明確的技術說明和預計恢復時間
- ✅ 避免用戶混淆和系統資源浪費

#### **技術債務記錄**


### 📊 **與圖表分析系統的相似性**

 < /dev/null |  功能 | 問題類型 | 解決方案 | 完成狀態 |
|---|---|---|---|
| **仿真圖片** (SINR/CFR/Doppler) | PostgreSQL → MongoDB 遷移 | 503 友好錯誤 + Phase 3 修復 | ✅ 已完成 |
| **RL 監控系統** | PostgreSQL → MongoDB 遷移 | 暫時禁用 + Phase 3 修復 | ✅ 已完成 |
| **設備管理** | PostgreSQL → MongoDB 遷移 | 直接遷移到 MongoDB | ✅ 已完成 |
| **衛星追蹤** | PostgreSQL → MongoDB 遷移 | 使用 Redis TLE 數據 | ✅ 已完成 |

**一致的用戶體驗策略**: 所有受數據庫遷移影響的功能都提供清楚的說明和預期恢復時間，確保用戶了解系統狀態而不感到困惑。


