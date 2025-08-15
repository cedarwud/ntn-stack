# 🛰️ LEO 衛星動態池規劃系統重構計劃

**版本**: v2.0 重構版  
**更新日期**: 2025-08-15  
**目標**: 以強化學習為區隔的二階段重構，實現10-15/3-6顆衛星動態覆蓋  

## 🎯 重構目標規格

### 🌍 觀測點規格
- **座標**: NTPU 24.9441°N, 121.3714°E
- **Starlink**: 10-15顆同時可見，5°仰角閾值，96分鐘軌道週期
- **OneWeb**: 3-6顆同時可見，10°仰角閾值，109分鐘軌道週期
- **池大小**: Starlink ~96顆、OneWeb ~38顆 ⚠️ **預估值，待程式驗證**
- **時空錯開**: 衛星出現時間和位置必須分散
- **A4/A5/D2**: 完整換手判斷事件支援
- **前端渲染**: navbar > 立體圖完整動畫支援

## 📁 新架構目錄結構

```
leo_restructure/
├── 📋 README.md                    # 總管理文檔 (本文件)
├── ⚠️ IMPORTANT_NOTICE.md          # 重要說明: 96/38為預估值
│
├── 🎯 phase1_core_system/          # Phase 1: 核心系統 (3-4週)
│   ├── f1_tle_loader/              # F1: TLE數據載入器
│   │   ├── tle_loader_engine.py    # 全量8,735顆衛星處理
│   │   ├── sgp4_calculator.py      # SGP4軌道計算引擎
│   │   └── data_validation.py      # TLE數據驗證模組
│   │
│   ├── f2_satellite_filter/        # F2: 衛星篩選器
│   │   ├── geographic_filter.py    # 地理相關性篩選
│   │   ├── constellation_filter.py # 星座特定篩選邏輯
│   │   └── candidate_selector.py   # 554顆候選衛星選擇
│   │
│   ├── f3_signal_analyzer/         # F3: 信號分析器
│   │   ├── a4_event_processor.py   # A4事件: 鄰近衛星 > -100dBm
│   │   ├── a5_event_processor.py   # A5事件: 服務<-110 & 鄰居>-100
│   │   ├── d2_event_processor.py   # D2事件: 距離換手 >5000km
│   │   ├── rsrp_calculator.py      # RSRP精確計算 (Ku頻段12GHz)
│   │   └── timeline_generator.py   # 200時間點完整時間軸
│   │
│   └── a1_dynamic_pool_planner/    # A1: 動態池規劃器
│       ├── simulated_annealing.py  # 模擬退火演算法核心
│       ├── temporal_distribution.py # 時空分散算法
│       ├── coverage_verifier.py    # 動態覆蓋驗證器
│       └── pool_optimizer.py       # 衛星池最佳化引擎
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

## 🎯 Phase 1: 核心系統 (3-4週)

### Week 1: F1_TLE_Loader + F2_Satellite_Filter
**目標**: 從8,735顆衛星篩選到554顆候選

#### F1_TLE_Loader 功能規格
```python
class TLELoaderEngine:
    """全量TLE數據載入和SGP4計算引擎"""
    
    async def load_full_satellite_data(self):
        """載入8,735顆衛星的完整TLE數據"""
        # 處理: Starlink ~5,000顆 + OneWeb ~800顆 + 其他星座
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
        
    async def select_candidates(self, satellites, target_count=554):
        """最終候選衛星選擇"""
        # 多維度評分: 地理相關性 + 軌道特性 + 信號品質
        # 輸出: 554顆高品質候選衛星
        pass
```

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

---

**重構理念**: 功能完整性優先，確保10-15/3-6顆衛星動態覆蓋目標100%達成，Phase 1成功後再進行Phase 2 RL擴展。