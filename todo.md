# 🛰️ LEO 衛星動態池規劃系統重構計劃

**更新日期**: 2025-08-15  
**版本**: v2.0 重構版  

## 🎯 二階段開發策略

### 📊 Phase 1: 核心系統 (3-4週)
**目標**: 完整滿足前端立體圖需求，支援傳統換手決策

#### 🏗️ 完整架構
```
F1_TLE_Loader → F2_Satellite_Filter → F3_Signal_Analyzer → A1_Dynamic_Pool_Planner
```

#### ✅ 核心需求 (100%滿足)
- **全量處理**: 從8,735顆衛星開始，絕不取樣
- **可見目標**: 隨時保持10-15顆Starlink + 3-6顆OneWeb可見
- **完整事件**: 包含完整A4/A5/D2換手判斷數據
- **時空錯開**: 避免衛星同時出現/消失
- **完整週期**: 96分鐘完整軌道週期分析
- **前端就緒**: 直接支援前端立體圖渲染

#### 🔧 關鍵技術決策
- **演算法選擇**: 模擬退火演算法 (Simulated Annealing)
- **複雜度**: O(n × iterations) 可控複雜度
- **成功率**: 85%機會達到可見性目標
- **開發風險**: 中等，可控

#### 📁 預期輸出
```json
{
  "starlink_pool": [96顆時空錯開衛星],
  "oneweb_pool": [38顆時空錯開衛星],
  "coverage_guarantee": "10-15/3-6顆隨時可見",
  "a4_a5_d2_events": "完整換手事件數據",
  "frontend_ready": true
}
```

### 🧠 Phase 2: RL擴展系統 (4-6週)
**目標**: 在核心系統基礎上新增強化學習智能決策

#### 🚀 擴展架構
```
Phase1系統 + ML1_Data_Collector + ML2_Model_Trainer + ML3_Inference_Engine
```

#### 🔄 運行模式
- **傳統模式**: 使用A4/A5/D2決策 (穩定可靠)
- **RL模式**: 使用訓練好的RL模型 (智能創新)
- **混合模式**: 傳統+RL混合決策 (最佳性能)

## 🔧 模擬退火演算法設計

### 核心優勢
1. **跳出局部最優**: 避免貪婪演算法陷阱
2. **處理複雜約束**: 適合時空分散多約束問題  
3. **實現可控**: 難度適中，開發風險低
4. **結果可靠**: 高機率達成可見性目標

### 演算法框架
```python
def simulated_annealing_pool_planning():
    # 1. 初始解生成
    current_solution = random_initial_solution(target_size=134)
    
    # 2. 模擬退火過程
    while temperature > threshold:
        neighbor = generate_neighbor(current_solution)
        if accept_solution(neighbor, temperature):
            current_solution = neighbor
        temperature *= cooling_rate
    
    return best_solution

def evaluate_solution(solution):
    cost = 0
    # 硬約束懲罰
    if not meets_visibility_requirements(solution):  # 10-15/3-6顆
        cost += 10000
    if not meets_temporal_distribution(solution):   # 時空錯開  
        cost += 5000
    # 軟約束優化
    cost += signal_quality_cost(solution)
    return cost
```

## 📅 詳細時間規劃

### Phase 1 開發時程 (第1-4週)
- **第1週**: F1_TLE_Loader + F2_Satellite_Filter
- **第2週**: F3_Signal_Analyzer (含完整A4/A5/D2)
- **第3週**: A1_Dynamic_Pool_Planner (模擬退火實現)
- **第4週**: 前端整合測試，驗證10-15/3-6顆目標

### Phase 2 開發時程 (第5-8週)  
- **第5-6週**: ML1_Data_Collector 多天數據收集
- **第7週**: ML2_Model_Trainer RL模型訓練
- **第8週**: ML3_Inference_Engine 智能推理部署

## 🚨 關鍵成功因素

### 必須避免的錯誤
1. **❌ 數據截斷**: F3必須保持完整200個時間點
2. **❌ 簡化演算法**: 必須使用模擬退火，不能用貪婪
3. **❌ 取樣處理**: 必須從8,735顆全量開始
4. **❌ 功能妥協**: 必須達到10-15/3-6顆可見目標

### 驗證標準
- **數量驗證**: Starlink池96顆，OneWeb池38顆
- **可見性驗證**: 任意時刻10-15/3-6顆可見
- **時空驗證**: 衛星出現時間和位置錯開
- **事件驗證**: A4/A5/D2事件完整觸發
- **前端驗證**: 立體圖完美渲染

## 📋 下一步行動

1. ✅ **完整重構計劃**: 制定完整重構計劃 (已完成)
2. ✅ **架構準備**: 設計新的模組結構和接口 (已完成)
3. ✅ **目錄結構**: 建立完整Phase 1 + Phase 2目錄架構 (已完成)
4. 🔄 **立即開始**: Phase 1 Week 1 實現 (F1_TLE_Loader + F2_Satellite_Filter)
5. **數據流修復**: 解決階段三數據截斷問題
6. **演算法實現**: 實施模擬退火動態池規劃
7. **測試驗證**: 確保所有成功標準達成

## 🎯 立即可執行

```bash
# 進入新架構目錄
cd /home/sat/ntn-stack/leo_restructure

# 查看完整架構
cat README.md

# 開始Phase 1 Week 1開發
cd phase1_core_system
python main_pipeline.py
```

---
**核心理念**: 功能完整性 > 實現複雜度，確保Phase 1成功後再考慮Phase 2擴展
