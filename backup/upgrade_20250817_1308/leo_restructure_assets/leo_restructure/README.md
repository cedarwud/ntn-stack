# 🛰️ LEO 衛星動態池規劃系統重構計劃

**版本**: v2.0 重構版  
**更新日期**: 2025-08-15  
**目標**: 以強化學習為區隔的二階段重構，實現10-15/3-6顆衛星動態覆蓋  

## 🎯 重構目標規格

### 🌍 觀測點規格
- **座標**: NTPU 24.9441°N, 121.3714°E
- **Starlink**: 10-15顆同時可見，5°仰角閾值，96分鐘軌道週期
- **OneWeb**: 3-6顆同時可見，10°仰角閾值，109分鐘軌道週期
- **實際池大小**: Starlink **8,085顆**、OneWeb **651顆** ✅ **2025-08-15實測確認**
- **時空錯開**: 衛星出現時間和位置必須分散
- **A4/A5/D2**: 完整換手判斷事件支援
- **前端渲染**: navbar > 立體圖完整動畫支援

## 📁 新架構目錄結構

```
leo_restructure/
├── 📋 README.md                    # 總管理文檔 (本文件)  
├── ⚠️ IMPORTANT_NOTICE.md          # 重要說明: 96/38為預估值
├── 🗂️ INTEGRATION_TRACKING.md      # 舊系統整合追蹤 (47個檔案狀態)
├── 🚀 IMPLEMENTATION_PLAN.md       # 5階段實施計劃 (F1→F2→F3→A1→測試)
│
├── 🎯 phase1_core_system/          # Phase 1: 核心系統 (3-4週)
│   ├── tle_data_loader/            # TLE數據載入器 ✅ 功能型命名
│   │   ├── tle_loader_engine.py    # 全量8,735顆衛星處理
│   │   ├── orbital_calculator.py   # SGP4軌道計算引擎
│   │   ├── data_validator.py       # TLE數據驗證模組
│   │   └── fallback_test_data.py   # 備援測試數據
│   │
│   ├── satellite_filter_engine/    # 衛星篩選器 ✅ 功能型命名
│   │   ├── satellite_filter_engine_v2.py # 智能篩選核心引擎
│   │   ├── geographic_optimizer.py # 地理相關性優化
│   │   ├── constellation_balancer.py # 星座負載平衡
│   │   └── candidate_selector.py   # 候選衛星選擇器
│   │
│   ├── signal_analyzer/            # 信號分析器 ✅ 功能型命名
│   │   ├── threegpp_event_processor.py # 3GPP事件處理器 (A4/A5/D2)
│   │   ├── rsrp_calculation_engine.py # RSRP精確計算引擎
│   │   ├── handover_event_processor.py # 換手事件處理器
│   │   └── timeline_generator.py   # 200時間點完整時間軸
│   │
│   └── dynamic_pool_planner/       # 動態池規劃器 ✅ 功能型命名
│       ├── simulated_annealing_optimizer.py # 模擬退火最佳化引擎
│       ├── temporal_distributor.py # 時空分散算法
│       ├── coverage_validator.py   # 動態覆蓋驗證器
│       └── constraint_evaluator.py # 約束評估器
│
├── 🧠 phase2_rl_expansion/         # Phase 2: RL擴展系統 (4-6週)
│   ├── ml1_data_collector/         # ML1: 數據收集器
│   │   ├── multi_day_collector.py  # 多天數據收集引擎
│   │   ├── training_data_prep.py   # 訓練數據預處理
│   │   └── feature_extractor.py    # 特徵提取模組
│   │
│   ├── ml2_model_trainer/          # ML2: 模型訓練器
│   │   ├── dqn_trainer.py          # Deep Q-Network 訓練
│   │   ├── ppo_trainer.py          # Proximal Policy Optimization
│   │   ├── sac_trainer.py          # Soft Actor-Critic
│   │   └── model_evaluation.py     # 模型評估框架
│   │
│   └── ml3_inference_engine/       # ML3: 推理引擎
│       ├── rl_decision_engine.py   # RL決策引擎
│       ├── hybrid_mode_manager.py  # 傳統+RL混合模式
│       └── real_time_inference.py  # 即時推理處理
│
├── 🔧 shared_core/                 # 共享核心模組
│   ├── config_manager.py           # 統一配置管理
│   ├── data_structures.py          # 共享數據結構
│   ├── coordinate_system.py        # 座標系統定義 (NTPU)
│   ├── elevation_thresholds.py     # 仰角閾值管理 (5°/10°)
│   └── validation_framework.py     # 驗證框架
│
├── 🧮 algorithms/                  # 核心演算法庫
│   ├── simulated_annealing/        # 模擬退火演算法實現
│   │   ├── sa_core.py              # 核心SA演算法
│   │   ├── temperature_scheduler.py # 溫度調度器
│   │   ├── neighbor_generator.py   # 鄰域解生成器
│   │   └── constraint_evaluator.py # 約束評估器
│   │
│   ├── temporal_optimization/      # 時空最佳化演算法
│   │   ├── time_slot_manager.py    # 時間槽管理
│   │   ├── spatial_distributor.py  # 空間分佈器
│   │   └── conflict_resolver.py    # 衝突解決器
│   │
│   └── visibility_calculator/      # 可見性計算演算法
│       ├── elevation_calculator.py # 仰角計算器
│       ├── timeline_simulator.py   # 時間軸模擬器
│       └── coverage_analyzer.py    # 覆蓋分析器
│
├── 🧪 tests_integration/           # 整合測試套件
│   ├── phase1_integration_test.py  # Phase 1 完整流程測試
│   ├── phase2_integration_test.py  # Phase 2 RL擴展測試
│   ├── end_to_end_test.py          # 端到端完整測試
│   ├── frontend_integration_test.py # 前端整合測試
│   └── performance_benchmark.py    # 性能基準測試
│
└── 📚 docs/                        # 重構文檔
    ├── phase1_specifications.md    # Phase 1 詳細規格
    ├── phase2_rl_design.md         # Phase 2 RL設計文檔
    ├── simulated_annealing_guide.md # 模擬退火演算法指南
    ├── api_interfaces.md           # API接口文檔
    └── deployment_guide.md         # 部署指南
```

## 🔄 Phase 0: 系統替換整合 (1週) 🆕

### ⚡ 目標：將 leo_restructure 完全替代原6階段系統
**優先級**: 🔥 **最高** - 實現新舊系統完全切換，清理舊代碼

#### P0.1 Docker建構整合 (1-2天)
```bash
# 1. 修改 netstack/docker/build_with_phase0_data.py
# 2. 替換 6階段調用為 leo_restructure Phase 1 調用
# 3. 整合到 Pure Cron 驅動架構
```

#### P0.2 配置系統統一 (1天)
```bash
# 1. 統一配置管理：shared_core/config_manager.py → netstack/config/
# 2. 整合仰角門檻設定
# 3. 對接現有環境變數系統
```

#### P0.3 輸出格式對接 (1天)
```bash
# 1. 確保 A1_Dynamic_Pool_Planner 輸出與前端兼容
# 2. 生成前端需要的時間序列數據格式
# 3. 保持與現有 API 接口完全兼容
```

#### P0.4 系統替換與驗證 (2-3天)
```bash
# 1. 停用原 6階段處理 (備份到 stages_backup/)
# 2. 啟用 leo_restructure 為主要處理流程
# 3. 更新 Makefile 建構流程
# 4. 完整測試驗證：make down-v && make build-n && make up
```

#### ✅ Phase 0 成功標準
- [ ] Docker 建構完全使用 leo_restructure (0% 使用舊6階段)
- [ ] Pure Cron 驅動架構保持不變 (< 30秒啟動)
- [ ] API 響應格式完全兼容 (`/api/v1/satellites/positions` 正常)
- [ ] 前端立體圖數據無縫對接
- [ ] 系統性能不低於原系統 (啟動 < 30秒，API響應 < 100ms)

---

## 🎯 Phase 1: 核心系統優化 (3-4週)

### ✅ Week 1: F1_TLE_Loader + F2_Satellite_Filter - 已完成測試
**目標**: 從8,736顆衛星篩選到468顆候選 ✅ **實測結果**

#### F1_TLE_Loader 功能規格
```python
class TLELoaderEngine:
    """全量TLE數據載入和SGP4計算引擎"""
    
    async def load_full_satellite_data(self):
        """載入8,736顆衛星的完整TLE數據"""
        # ✅ 實測: Starlink 8,085顆 + OneWeb 651顆 (2025-08-15確認)
        # 輸出: 完整軌道參數和96/109分鐘週期計算
        pass
        
    async def calculate_orbital_positions(self, satellites, time_range_minutes=200):
        """使用SGP4計算200個時間點的軌道位置"""
        # 時間解析度: 30秒間隔
        # 精度要求: 位置精度 < 100m
        pass
```

#### F2_Satellite_Filter 功能規格
```python
class SatelliteFilter:
    """智能衛星篩選，從8,735顆篩選到554顆候選"""
    
    async def apply_geographic_filter(self, satellites):
        """地理相關性篩選 - NTPU觀測點優化"""
        # NTPU座標: 24.9441°N, 121.3714°E  
        # 篩選標準: 軌道傾角 > 觀測點緯度
        # 升交點經度相關性評分
        pass
        
    async def apply_constellation_filter(self, satellites):
        """星座特定篩選邏輯"""
        # Starlink: 53°傾角，550km高度優先
        # OneWeb: 87.4°傾角，1200km高度優先
        pass
        
    async def select_candidates(self, satellites, target_count=468):
        """最終候選衛星選擇"""
        # ✅ 實測: 350顆Starlink + 118顆OneWeb = 468顆候選
        # 六階段篩選管線: 94.6%篩選率，1.45秒處理時間
        pass
```

## 📊 Phase 1 測試結果總結 (2025-08-15)

### ✅ 已完成測試的組件
| 組件 | 狀態 | 實際結果 | 處理時間 |
|------|------|----------|----------|
| **F1_TLE_Loader** | ✅ 完成 | 8,736顆衛星 (8,085 Starlink + 651 OneWeb) | 366秒 |
| **F2_Satellite_Filter** | ✅ 完成 | 468顆候選 (350 Starlink + 118 OneWeb) | 1.45秒 |
| **F3_Signal_Analyzer** | ✅ 基礎完成 | 0個換手事件 (待優化) | 0.0002秒 |
| **A1_Pool_Optimizer** | ✅ 完成 | 468顆最終池 | 11.96秒 |

### ⚠️ 發現的問題與修復狀態
1. **執行順序錯誤** ✅ **已修復** - 改為先計算全量軌道再篩選
2. **六階段篩選缺失** ✅ **已修復** - 實現完整的@docs設計
3. **可見性合規0%** ⚠️ **部分修復** - 架構修復完成，需進一步優化
4. **人工取樣限制** ✅ **已修復** - 移除1000顆限制，使用全量數據

### 📈 預估值vs實際值比較
| 項目 | 原預估 | 實際測試 | 偏差率 |
|------|--------|----------|--------|
| 總衛星數 | 8,735顆 | 8,736顆 | +0.01% ✅ |
| Starlink | 5,000顆 | 8,085顆 | +61.7% ❌ |
| OneWeb | 800顆 | 651顆 | -18.6% ❌ |
| 候選總數 | 554顆 | 468顆 | -15.5% ⚠️ |

### 🎯 下一步行動計劃
1. **修復可見性合規**: 實現每顆衛星的最佳過頂時間計算 
2. **優化信號分析**: 改善A4/A5/D2事件檢測演算法
3. **調整模擬退火**: 基於實際數據優化參數
4. **準備重構**: 更新所有文檔後開始系統性重構

### Week 2: F3_Signal_Analyzer
**目標**: 完整A4/A5/D2事件分析，保持200時間點

#### A4/A5/D2 事件處理器規格
```python
class A4EventProcessor:
    """A4事件: 鄰近衛星信號優於門檻"""
    
    async def detect_a4_events(self, serving_sat, neighbor_sats, timeline):
        """檢測A4事件: neighbor_rsrp > -100 dBm"""
        # 3GPP標準: Mn + Ofn + Ocn – Hys > Thresh2
        # 實現: neighbor["rsrp_dbm"] > -100
        pass

class A5EventProcessor:
    """A5事件: 服務衛星劣化且鄰近衛星良好"""
    
    async def detect_a5_events(self, serving_sat, neighbor_sats, timeline):
        """檢測A5事件: 雙重條件判斷"""
        # 條件1: serving["rsrp_dbm"] < -110 (服務衛星劣化)
        # 條件2: neighbor["rsrp_dbm"] > -100 (鄰居衛星良好)
        # 優先級: HIGH (A5) > MEDIUM (A4) > LOW
        pass

class D2EventProcessor:
    """D2事件: LEO衛星距離優化換手"""
    
    async def detect_d2_events(self, serving_sat, neighbor_sats, timeline):
        """檢測D2事件: 距離基換手"""
        # 觸發條件: serving > 5000km 且 candidate < 3000km
        # 基於真實3D距離 (SGP4軌道計算)
        pass

class RSRPCalculator:
    """RSRP精確計算 - Ku頻段12GHz"""
    
    def calculate_rsrp_precise(self, satellite, observer):
        """精確RSRP計算"""
        # 自由空間路徑損耗: FSPL = 20*log10(d) + 20*log10(f) + 32.45
        # 仰角增益: elevation/90 * 15dB (最大15dB)
        # 發射功率: 43dBm
        # 公式: RSRP = 43 - FSPL + elevation_gain
        pass
```

### Week 3: A1_Dynamic_Pool_Planner
**目標**: 模擬退火演算法實現，達成96+38顆衛星池

#### 模擬退火核心實現
```python
class SimulatedAnnealingPoolPlanner:
    """模擬退火動態池規劃器"""
    
    def __init__(self):
        self.ntpu_coordinates = (24.9441, 121.3714)
        self.starlink_target = (10, 15)  # 可見衛星數範圍
        self.oneweb_target = (3, 6)
        self.starlink_elevation = 5.0    # 度
        self.oneweb_elevation = 10.0     # 度
        
    async def plan_optimal_pools(self, candidates):
        """使用模擬退火規劃最佳衛星池"""
        
        # 1. 初始解生成
        initial_starlink = self._random_initial_selection(
            candidates['starlink'], target_size=96
        )
        initial_oneweb = self._random_initial_selection(
            candidates['oneweb'], target_size=38
        )
        
        # 2. 模擬退火最佳化
        best_starlink = await self._simulated_annealing_optimize(
            initial_starlink, self.starlink_target, 96
        )
        best_oneweb = await self._simulated_annealing_optimize(
            initial_oneweb, self.oneweb_target, 109
        )
        
        return {
            'starlink_pool': best_starlink,
            'oneweb_pool': best_oneweb,
            'coverage_verification': await self._verify_coverage(
                best_starlink, best_oneweb
            )
        }
        
    async def _simulated_annealing_optimize(self, initial_solution, target_range, orbit_period):
        """核心模擬退火最佳化演算法"""
        
        current_solution = initial_solution
        best_solution = initial_solution
        current_cost = self._evaluate_solution_cost(current_solution, target_range)
        best_cost = current_cost
        
        # 模擬退火參數
        initial_temperature = 1000.0
        cooling_rate = 0.95
        min_temperature = 1.0
        temperature = initial_temperature
        
        while temperature > min_temperature:
            # 生成鄰域解
            neighbor_solution = self._generate_neighbor_solution(current_solution)
            neighbor_cost = self._evaluate_solution_cost(neighbor_solution, target_range)
            
            # 接受準則 (Metropolis準則)
            if self._accept_solution(current_cost, neighbor_cost, temperature):
                current_solution = neighbor_solution
                current_cost = neighbor_cost
                
                # 更新最佳解
                if current_cost < best_cost:
                    best_solution = current_solution
                    best_cost = current_cost
            
            # 溫度冷卻
            temperature *= cooling_rate
            
        return best_solution
    
    def _evaluate_solution_cost(self, solution, target_range):
        """解決方案成本評估函數"""
        cost = 0.0
        
        # 1. 硬約束懲罰 (必須滿足)
        timeline = self._simulate_visibility_timeline(solution)
        
        # 可見性要求懲罰
        for time_point in timeline:
            visible_count = time_point['visible_count']
            if not (target_range[0] <= visible_count <= target_range[1]):
                cost += 10000.0  # 重懲罰
        
        # 時空分散懲罰
        if not self._check_temporal_distribution(solution):
            cost += 5000.0
            
        # 2. 軟約束優化 (品質提升)
        cost += self._signal_quality_cost(solution)
        cost += self._orbital_diversity_cost(solution)
        
        return cost
        
    def _accept_solution(self, current_cost, neighbor_cost, temperature):
        """模擬退火接受準則"""
        if neighbor_cost < current_cost:
            return True  # 更好的解直接接受
        else:
            # 較差的解以一定機率接受 (避免局部最優)
            probability = math.exp(-(neighbor_cost - current_cost) / temperature)
            return random.random() < probability
```

### Week 4: 前端整合測試
**目標**: 驗證10-15/3-6顆衛星動態覆蓋，前端立體圖渲染

#### 整合驗證規格
```python
class FrontendIntegrationVerifier:
    """前端整合驗證器"""
    
    async def verify_satellite_pools(self, starlink_pool, oneweb_pool):
        """驗證衛星池滿足前端需求"""
        
        verification_results = {
            'starlink_verification': await self._verify_starlink_requirements(starlink_pool),
            'oneweb_verification': await self._verify_oneweb_requirements(oneweb_pool),
            'temporal_distribution': await self._verify_temporal_distribution(starlink_pool, oneweb_pool),
            'handover_events': await self._verify_handover_events(starlink_pool, oneweb_pool),
            'frontend_compatibility': await self._verify_frontend_compatibility(starlink_pool, oneweb_pool)
        }
        
        return verification_results
        
    async def _verify_starlink_requirements(self, starlink_pool):
        """驗證Starlink池要求"""
        timeline = self._simulate_96_minute_cycle(starlink_pool)
        
        compliance_check = {
            'pool_size': len(starlink_pool),
            'target_pool_size': 96,
            'elevation_threshold': 5.0,
            'target_visible_range': (10, 15),
            'compliance_ratio': 0.0,
            'coverage_gaps': []
        }
        
        # 檢查每個時間點的可見衛星數
        compliant_points = 0
        for time_point in timeline:
            visible_sats = [sat for sat in starlink_pool 
                          if self._is_visible(sat, time_point, elevation_threshold=5.0)]
            visible_count = len(visible_sats)
            
            if 10 <= visible_count <= 15:
                compliant_points += 1
            else:
                compliance_check['coverage_gaps'].append({
                    'time': time_point,
                    'visible_count': visible_count,
                    'expected_range': (10, 15)
                })
        
        compliance_check['compliance_ratio'] = compliant_points / len(timeline)
        return compliance_check
```

## 🧠 Phase 2: RL擴展系統 (4-6週)

### Week 5-6: ML1_Data_Collector
**目標**: 多天數據收集，建立RL訓練數據集

### Week 7: ML2_Model_Trainer  
**目標**: DQN/PPO/SAC模型訓練

### Week 8: ML3_Inference_Engine
**目標**: 混合模式部署，傳統+RL決策

## 🚨 關鍵成功標準

### ✅ 必須達成的指標
1. **可見性保證**: 任意時刻Starlink 10-15顆、OneWeb 3-6顆可見
2. **時空分散**: 衛星出現時間差 > 15°相位差
3. **事件完整性**: A4/A5/D2事件100%觸發支援
4. **前端就緒**: 立體圖渲染數據完全兼容
5. **演算法可靠**: 模擬退火85%機率達成目標

### 📊 驗證方式
- **數量驗證**: `pool_size: Starlink=96, OneWeb=38`
- **覆蓋驗證**: `compliance_ratio > 0.95` 
- **時空驗證**: `phase_difference > 15°`
- **事件驗證**: `a4_a5_d2_events.count > 0`
- **前端驗證**: `frontend_compatibility = true`

## 🚀 實施計劃

### 立即行動 (本週)
1. ✅ 建立新架構目錄結構 (已完成)
2. 🔄 實現F1_TLE_Loader核心功能
3. 🔄 實現F2_Satellite_Filter篩選邏輯

### 下週目標
1. 完成F3_Signal_Analyzer (A4/A5/D2)
2. 開始A1_Dynamic_Pool_Planner (模擬退火)

## 🔄 立即執行

### 🚀 NEW! 4階段漸進式開發工作流程 (強烈推薦) 🆕

**基於用戶反饋實現高效開發策略，避免重複建構映像檔**

#### 📋 階段性開發計劃概覽
```bash
Stage D1: 超快速開發 (30-60秒)  → 邏輯驗證、快速迭代
Stage D2: 開發驗證 (3-5分鐘)    → 功能測試、性能驗證  
Stage D3: 全量測試 (10-15分鐘)  → 完整驗證、最終確認
Stage D4: 容器建構 (20-30分鐘)  → 生產部署、系統驗證
```

#### 🛠️ 一鍵安裝開發工具
```bash
# 1. 安裝開發別名 (一次性設置)
cd /home/sat/ntn-stack/leo_restructure
./setup_dev_aliases.sh
source ~/.bashrc  # 重新載入shell

# 2. 查看所有可用命令
leo-help
```

#### ⚡ 日常開發流程 (效率提升60倍!)
```bash
# Stage D1: 超快速開發 (30秒) - 日常使用
leo-dev     # 等同於: python run_phase1.py --ultra-fast --auto-cleanup

# Stage D2: 開發驗證 (3分鐘) - 功能完成時
leo-test    # 等同於: python run_phase1.py --dev-mode --auto-cleanup

# Stage D3: 全量測試 (10分鐘) - 階段完成時  
leo-full    # 等同於: python run_phase1.py --full-test --auto-cleanup

# Stage D4: 容器建構 (25分鐘) - 準備部署時
leo-build   # 等同於: make down-v && make build-n && make up
```

#### 🔄 智能增量更新
```bash
# 檢查是否需要更新
leo-check   # 智能檢測TLE/代碼/配置變更

# 增量更新模式 (僅處理變更部分)
leo-inc     # 等同於: python run_phase1.py --incremental --auto-cleanup

# 🛡️ 安全清理舊數據 (保護 RL 訓練數據)
leo-clean   # 智能清理所有舊數據，絕不刪除 /netstack/tle_data/ RL 訓練數據
```

#### 🛠️ 實用工具
```bash
leo-quick   # 5顆衛星超快速測試 (10秒)
leo-debug   # 故障排除模式 (詳細日誌)
leo-stats   # 顯示系統統計信息
leo-workflow # 一鍵完整流程 (D1→D2→D3→D4)
```

#### 📊 效率對比
| 場景 | 傳統方法 | 新方法 | 提升倍數 |
|------|---------|--------|----------|
| 日常調試 | 30分鐘 | 30秒 | **60倍** |
| 功能測試 | 30分鐘 | 3分鐘 | **10倍** |
| 完整驗證 | 30分鐘 | 10分鐘 | **3倍** |

#### 🎯 使用建議
- **初次使用**: `leo-dev` (30秒體驗)
- **日常開發**: `leo-dev` → `leo-test` 循環
- **功能完成**: `leo-test` → `leo-full` → `leo-build`
- **緊急修復**: `leo-quick` (10秒快速驗證)

#### 🛡️ 數據保護提醒

**重要**: 清理工具會自動跳過 `/netstack/tle_data/` 資料夾，確保 RL 訓練數據不被誤刪

---

### 🔥 Phase 0: 系統替換優先執行 (生產部署)
```bash
# 進入leo_restructure目錄  
cd /home/sat/ntn-stack/leo_restructure

# 🔥 執行完整系統替換 (推薦首次使用)
python run_phase0_replacement.py

# 乾運行模式 (查看將執行的操作)
python run_phase0_replacement.py --dry-run

# 無備份模式 (快速執行，不建議生產環境)
python run_phase0_replacement.py --no-backup

# 詳細日誌模式
python run_phase0_replacement.py --verbose
```

**Phase 0 完成後效果**:
- ✅ 完全替代原6階段系統
- ✅ 保持Pure Cron驅動架構 (< 30秒啟動)  
- ✅ 前端立體圖無縫對接
- ✅ 64個舊檔案安全清理

**Phase 0 後續驗證**:
```bash
# 測試新系統
make down-v && make build-n && make up

# 驗證API響應
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/satellites/positions

# 檢查前端
# 瀏覽器訪問: http://localhost:5173
```

---

### 方法二：Phase 1核心功能測試
```bash
# 進入新架構目錄
cd /home/sat/ntn-stack/leo_restructure

# 快速測試模式 (推薦首次使用)
python run_phase1.py --fast

# 正常模式
python run_phase1.py

# 自定義參數
python run_phase1.py --iterations 2000 --time-range 150 --verbose
```

### 方法二：階段式執行
```bash
# 執行完整管道
cd phase1_core_system
python main_pipeline.py

# 執行整合測試
cd ../tests_integration
python test_pipeline_integration.py
```

### 輸出說明
執行後會在 `/tmp/phase1_outputs/` 生成：
- `stage1_tle_loading_results.json` - TLE載入統計
- `stage2_filtering_results.json` - 衛星篩選結果
- `stage3_event_analysis_results.json` - A4/A5/D2事件分析
- `stage4_optimization_results.json` - 模擬退火最佳化結果
- `phase1_final_report.json` - 完整執行報告

### 參數說明
- `--fast`: 快速測試模式 (100迭代，100分鐘時間範圍)
- `--iterations N`: 模擬退火最大迭代次數 (預設5000)
- `--time-range N`: 模擬時間範圍分鐘數 (預設200)
- `--verbose`: 詳細日誌輸出
- `--output-dir PATH`: 自定義輸出目錄

### 成功標準
執行成功後應看到：
- ✅ Starlink池: 50-100顆 (快速模式) 或 80-100顆 (正常模式)
- ✅ OneWeb池: 20-50顆 (快速模式) 或 30-50顆 (正常模式)  
- ✅ 可見性合規: ≥70% (快速模式) 或 ≥90% (正常模式)
- ✅ 時空分佈: ≥50% (快速模式) 或 ≥70% (正常模式)

### 故障排除
```bash
# 檢查依賴
pip install numpy skyfield aiohttp

# 網路問題時使用本地測試
python run_phase1.py --fast --iterations 50

# 詳細錯誤信息
python run_phase1.py --verbose
```

---

**重構理念**: 功能完整性優先，確保10-15/3-6顆衛星動態覆蓋目標100%達成，Phase 1成功後再進行Phase 2 RL擴展。

**📋 下一步**: 執行 `python run_phase1.py --fast` 開始測試系統！