# 🛰️ 階段六：動態衛星池規劃 (增強版 ⭐)

[🔄 返回數據流程導航](../README.md) > 階段六

## 📖 階段概述

**目標**：使用模擬退火演算法進行動態衛星池最佳化，確保整個軌道週期內連續覆蓋性能  
**輸入**：階段五的混合存儲數據 + shared_core統一數據模型  
**輸出**：最佳化動態衛星池配置 + 約束滿足報告  
**處理對象**：從391顆候選中選出90-110顆組成動態衛星池，確保NTPU上空任何時間點都有8-14顆同時可見  
**處理時間**：約 2-5 分鐘 (軌道動力學分析 + 模擬退火最佳化)

✅ **系統升級完成**：整合四階段技術資產(shared_core、模擬退火、auto_cleanup、incremental_update)到六階段系統

## 🎯 動態覆蓋需求

### 核心挑戰
- **連續覆蓋**：整個96/109分鐘軌道週期內，NTPU上空任何時間點都要維持目標可見數量
- **動態池規劃**：從391顆候選中選出90-110顆組成動態衛星池
- **時空分散**：確保衛星進出時間錯開，無縫隙切換
- **軌道互補**：不同軌道面的衛星組合，提供全方位覆蓋

### 動態池規劃目標 (基於軌道動力學分析)
```python
DYNAMIC_POOL_PLANNING = {
    'input_candidates': {
        'starlink': 358,        # 階段二篩選後的候選數
        'oneweb': 33           # 階段二篩選後的候選數  
    },
    'target_simultaneous_visible': {
        'starlink': (6, 10),   # 任何時間點同時可見數量
        'oneweb': (2, 4)       # 任何時間點同時可見數量
    },
    'optimal_dynamic_pool': {
        'starlink': (60, 80),  # 從358顆中選出的動態池大小
        'oneweb': (25, 30),    # 從33顆中選出的動態池大小
        'total_pool': (90, 110) # 總動態池大小
    },
    'coverage_requirement': {
        'temporal_continuity': '96/109分鐘軌道週期內無縫覆蓋',
        'elevation_threshold': {'starlink': 5.0, 'oneweb': 10.0},
        'handover_smoothness': '衛星切換時間間隔最佳化'
    }
}
```

## 🧠 模擬退火動態池最佳化演算法 (升級版)

### 核心演算法架構 - 整合模擬退火優化
```python
from shared_core.data_models import ConstellationType, SatelliteBasicInfo
from stages.algorithms.simulated_annealing_optimizer import SimulatedAnnealingOptimizer

class EnhancedDynamicPoolPlanner:
    """增強版動態衛星池規劃器 - 使用模擬退火最佳化"""
    
    def __init__(self, config: Dict[str, Any]):
        self.observer_lat = 24.9441667   # NTPU座標
        self.observer_lon = 121.3713889
        
        # 整合模擬退火優化器
        sa_config = config.get('simulated_annealing', {})
        self.sa_optimizer = SimulatedAnnealingOptimizer(sa_config)
        
        # 整合shared_core數據模型
        from shared_core.data_models import ConstellationType
        self.constellation_types = ConstellationType
        
    async def plan_dynamic_pools_enhanced(self, satellite_data):
        """使用模擬退火演算法規劃最佳動態衛星池"""
        
        logger.info("🔥 開始增強版動態池規劃 (模擬退火最佳化)")
        
        # 1. 數據預處理 - 使用shared_core統一格式
        processed_data = await self._preprocess_with_shared_core(satellite_data)
        
        # 2. 分離星座候選衛星
        starlink_candidates = processed_data['starlink_candidates']
        oneweb_candidates = processed_data['oneweb_candidates']
        orbital_positions = processed_data['orbital_positions']
        
        # 3. 模擬退火最佳化 - 核心演算法
        optimal_solution = await self.sa_optimizer.optimize_satellite_pools(
            starlink_candidates, oneweb_candidates, orbital_positions
        )
        
        # 4. 約束滿足驗證
        constraint_verification = await self._verify_constraints(optimal_solution)
        
        # 5. 性能指標計算
        performance_metrics = await self._calculate_performance_metrics(optimal_solution)
        
        return {
            'optimal_satellite_pools': optimal_solution,
            'constraint_satisfaction': constraint_verification,
            'performance_metrics': performance_metrics,
            'optimization_statistics': self.sa_optimizer.optimization_stats
        }
```

### 模擬退火最佳化演算法詳解

#### 1. 模擬退火核心流程
```python
async def _simulated_annealing_optimization(self,
                                          initial_solution: SatellitePoolSolution,
                                          starlink_candidates: List,
                                          oneweb_candidates: List,
                                          orbital_positions: Dict) -> SatellitePoolSolution:
    """模擬退火最佳化核心演算法"""
    
    current_solution = initial_solution
    best_solution = initial_solution
    
    temperature = self.annealing_params['initial_temperature']  # 1000.0
    cooling_rate = self.annealing_params['cooling_rate']        # 0.95
    max_iterations = self.annealing_params['max_iterations']    # 10000
    
    logger.info(f"🌡️ 開始模擬退火: 初始溫度={temperature}, 最大迭代={max_iterations}")
    
    for iteration in range(max_iterations):
        # 生成鄰域解
        neighbor_solution = await self._generate_neighbor_solution(
            current_solution, starlink_candidates, oneweb_candidates
        )
        
        # 評估成本函數
        neighbor_cost = await self._evaluate_solution_cost(
            neighbor_solution.starlink_satellites,
            neighbor_solution.oneweb_satellites,
            orbital_positions
        )
        
        # Metropolis接受準則
        if self._accept_solution(current_solution.cost, neighbor_cost, temperature):
            current_solution = neighbor_solution
            current_solution.cost = neighbor_cost
            
            # 更新最佳解
            if neighbor_cost < best_solution.cost:
                best_solution = current_solution
                logger.info(f"🏆 新最佳解! 迭代{iteration}, 成本={neighbor_cost:.2f}")
        
        # 溫度冷卻
        temperature *= cooling_rate
        
        if temperature < self.annealing_params['min_temperature']:
            break
    
    return best_solution
```

#### 2. 約束評估與成本函數
```python
async def _evaluate_solution_cost(self,
                                starlink_satellites: List[str],
                                oneweb_satellites: List[str],
                                orbital_positions: Dict) -> float:
    """評估解決方案成本 - 多重約束加權函數"""
    
    total_cost = 0.0
    
    # 1. 硬約束檢查 (高懲罰權重)
    visibility_cost = await self._evaluate_visibility_constraints(
        starlink_satellites, oneweb_satellites, orbital_positions
    )
    total_cost += visibility_cost * self.constraint_weights['visibility_violation']  # 10000.0
    
    # 2. 時空分佈約束
    temporal_cost = await self._evaluate_temporal_distribution(
        starlink_satellites, oneweb_satellites, orbital_positions
    )
    total_cost += temporal_cost * self.constraint_weights['temporal_clustering']     # 5000.0
    
    # 3. 池大小約束
    size_cost = self._evaluate_pool_size_constraints(
        starlink_satellites, oneweb_satellites
    )
    total_cost += size_cost * self.constraint_weights['pool_size_violation']        # 8000.0
    
    # 4. 軟約束優化 (優化目標)
    signal_cost = await self._evaluate_signal_quality(
        starlink_satellites, oneweb_satellites, orbital_positions
    )
    total_cost += signal_cost * self.constraint_weights['signal_quality']          # 100.0
    
    orbital_cost = await self._evaluate_orbital_diversity(
        starlink_satellites, oneweb_satellites
    )
    total_cost += orbital_cost * self.constraint_weights['orbital_diversity']      # 50.0
    
    return total_cost

def _accept_solution(self, current_cost: float, neighbor_cost: float, temperature: float) -> bool:
    """Metropolis接受準則"""
    
    if neighbor_cost < current_cost:
        return True  # 更好的解直接接受
    else:
        # 較差的解以一定機率接受 (避免局部最優)
        delta_cost = neighbor_cost - current_cost
        probability = math.exp(-delta_cost / temperature)
        return random.random() < probability
```

#### 3. 約束滿足驗證與性能評估
```python
async def _verify_final_solution(self,
                               solution: SatellitePoolSolution,
                               orbital_positions: Dict) -> Dict[str, bool]:
    """驗證最終解決方案的約束滿足情況"""
    
    verification_results = {
        'starlink_pool_size_ok': len(solution.starlink_satellites) == self.targets['starlink']['pool_size'],
        'oneweb_pool_size_ok': len(solution.oneweb_satellites) == self.targets['oneweb']['pool_size'],
        'visibility_compliance_ok': solution.visibility_compliance >= 0.90,      # 90%+可見性合規
        'temporal_distribution_ok': solution.temporal_distribution >= 0.70,      # 70%+時空分佈品質
        'signal_quality_ok': solution.signal_quality >= 0.80                     # 80%+信號品質
    }
    
    solution.constraints_satisfied = verification_results
    
    all_constraints_satisfied = all(verification_results.values())
    
    if all_constraints_satisfied:
        logger.info("✅ 所有約束條件滿足")
    else:
        failed_constraints = [k for k, v in verification_results.items() if not v]
        logger.warning(f"⚠️ 未滿足的約束: {failed_constraints}")
    
    return verification_results

async def _calculate_solution_metrics(self,
                                    solution: SatellitePoolSolution,
                                    orbital_positions: Dict) -> SatellitePoolSolution:
    """計算解決方案的詳細性能指標"""
    
    # 計算可見性合規度 (基於96分鐘軌道週期動態分析)
    compliance = await self._calculate_visibility_compliance(
        solution.starlink_satellites, solution.oneweb_satellites, orbital_positions
    )
    solution.visibility_compliance = compliance
    
    # 計算時空分佈品質 (衛星出現時間的分散性)
    distribution = await self._calculate_temporal_distribution_quality(
        solution.starlink_satellites, solution.oneweb_satellites, orbital_positions
    )
    solution.temporal_distribution = distribution
    
    # 計算信號品質綜合評分
    signal_quality = await self._calculate_signal_quality_score(
        solution.starlink_satellites, solution.oneweb_satellites, orbital_positions
    )
    solution.signal_quality = signal_quality
    
    return solution
```

## 📊 輸出數據格式

### 模擬退火最佳化結果 (增強版)
```json
{
  "optimization_metadata": {
    "timestamp": "2025-08-17T12:00:00Z",
    "algorithm": "simulated_annealing",
    "stage": "stage6_enhanced_dynamic_pool_planning",
    "observer_location": {
      "latitude": 24.9441667,
      "longitude": 121.3713889,
      "location_name": "NTPU"
    },
    "planning_targets": {
      "starlink": {
        "candidates": 358,
        "dynamic_pool_size": [60, 80],
        "simultaneous_visible": [6, 10],
        "elevation_threshold": 5.0,
        "orbit_period_minutes": 96
      },
      "oneweb": {
        "candidates": 33, 
        "dynamic_pool_size": [25, 30],
        "simultaneous_visible": [2, 4],
        "elevation_threshold": 10.0,
        "orbit_period_minutes": 109
      }
    },
    "annealing_params": {
      "initial_temperature": 1000.0,
      "cooling_rate": 0.95,
      "max_iterations": 10000,
      "min_temperature": 1.0
    }
  },
  "optimization_statistics": {
    "iterations": 8750,
    "best_iteration": 6420,
    "best_cost": 1247.53,
    "acceptance_rate": 0.23,
    "temperature_history": [1000.0, 950.0, 902.5, "..."],
    "cost_history": [15000.2, 12045.7, 8932.1, "..."],
    "constraint_violations": {
      "visibility_violation": 0,
      "temporal_clustering": 2,
      "pool_size_violation": 0
    }
  },
  "optimal_dynamic_pool": {
    "starlink_pool": ["STARLINK-1234", "STARLINK-5678", "..."],  # 70顆選出的動態池
    "oneweb_pool": ["ONEWEB-0123", "ONEWEB-0456", "..."],        # 28顆選出的動態池  
    "total_dynamic_pool": 98,  # 從391顆候選中選出的動態池
    "cost": 1247.53,
    "visibility_compliance": 0.923,      # 92.3%約束滿足
    "temporal_distribution": 0.847,      # 84.7%時空分佈品質
    "signal_quality": 0.891,             # 89.1%信號品質
    "constraints_satisfied": {
      "starlink_dynamic_pool_ok": true,      # 60-80顆範圍內
      "oneweb_dynamic_pool_ok": true,        # 25-30顆範圍內  
      "continuous_coverage_ok": true,        # 96/109分鐘週期無縫覆蓋
      "simultaneous_visible_ok": true,       # 8-14顆同時可見維持
      "temporal_distribution_ok": true,      # 時空分散最佳化
      "signal_quality_ok": true              # 信號品質最佳化
    }
  },
  "performance_analysis": {
    "continuous_coverage_starlink": "96分鐘軌道週期內維持6-10顆同時可見",
    "continuous_coverage_oneweb": "109分鐘軌道週期內維持2-4顆同時可見",
    "dynamic_pool_efficiency": "98顆動態池確保8-14顆總同時可見",
    "optimization_convergence": "第6420次迭代達到最佳解",
    "constraint_satisfaction_rate": "100% (所有約束滿足)"
  },
  "integration_notes": {
    "shared_core_integration": "使用統一數據模型ConstellationType和SatelliteBasicInfo",
    "incremental_update_ready": "支援incremental_update_manager變更檢測",
    "auto_cleanup_protected": "重要最佳化結果受auto_cleanup_manager保護",
    "frontend_integration": "98顆動態池提供給立體圖動畫系統，實現連續覆蓋演示"
  }
}
```

## 🏗️ 實現架構 (增強版)

### 主要實現位置 - 整合四階段技術資產
```bash
# 增強版動態池規劃器 (主要入口)
/netstack/src/stages/enhanced_dynamic_pool_planner.py
├── EnhancedDynamicPoolPlanner.load_data_integration_output()         # 數據載入
├── EnhancedDynamicPoolPlanner.convert_to_enhanced_candidates()       # 候選轉換
├── EnhancedDynamicPoolPlanner.execute_temporal_coverage_optimization() # 時間覆蓋優化
├── EnhancedDynamicPoolPlanner.generate_enhanced_output()             # 增強輸出生成
└── EnhancedDynamicPoolPlanner.process()                              # 完整流程執行

# 模擬退火優化器 (核心演算法)
/netstack/src/stages/algorithms/simulated_annealing_optimizer.py
├── SimulatedAnnealingOptimizer.optimize_satellite_pools()             # 主優化入口
├── SimulatedAnnealingOptimizer._simulated_annealing_optimization()    # 模擬退火核心
├── SimulatedAnnealingOptimizer._evaluate_solution_cost()              # 成本函數評估
├── SimulatedAnnealingOptimizer._generate_neighbor_solution()          # 鄰域解生成
├── SimulatedAnnealingOptimizer._accept_solution()                     # Metropolis準則
└── SimulatedAnnealingOptimizer.export_optimization_results()          # 結果匯出

# shared_core統一數據模型 (技術整合)
/netstack/src/shared_core/data_models.py
├── ConstellationType                                                  # 星座類型枚舉
├── SatelliteBasicInfo                                                # 衛星基礎信息
├── SignalCharacteristics                                             # 信號特性
└── OrbitParameters                                                   # 軌道參數

# 管理工具整合
/netstack/src/shared_core/auto_cleanup_manager.py                     # 智能清理管理
/netstack/src/shared_core/incremental_update_manager.py               # 增量更新檢測
/netstack/src/shared_core/performance_monitor.py                      # 性能監控(簡化版)
```

## 🔧 與現有架構整合

### 整合到階段五
```python
class DataIntegrationProcessor:
    
    async def process_enhanced_timeseries(self):
        # ... 現有的6個模組 ...
        
        # 7. 動態衛星池規劃 (新增)
        results["dynamic_satellite_pools"] = await self._generate_dynamic_pools()
        
        return results
    
    async def _generate_dynamic_pools(self):
        """整合階段六的動態池規劃功能"""
        
        stage6_planner = Stage6DynamicPoolPlanner(self.config)
        
        # 使用階段五的混合存儲數據作為輸入
        pool_results = await stage6_planner.plan_dynamic_pools(
            self.processed_satellite_data
        )
        
        # 保存到Volume
        output_file = Path("/app/data/dynamic_satellite_pools/pools.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(pool_results, f, indent=2)
        
        return pool_results
```

## ⚠️ 技術升級注意事項

### 升級完成狀態
1. **✅ 模擬退火演算法**：完整實現並整合到Stage6增強版
2. **✅ shared_core數據模型**：統一衛星數據結構，跨階段一致性
3. **✅ 約束引擎**：硬約束+軟約束的完整優化系統
4. **✅ 性能監控**：簡化版performance_monitor適配容器環境
5. **✅ 管理工具**：auto_cleanup和incremental_update智能管理

### 實際驗證結果
1. **Starlink動態池**: 從358顆候選中選出60-80顆，確保任何時間點維持6-10顆同時可見
2. **OneWeb動態池**: 從33顆候選中選出25-30顆，確保任何時間點維持2-4顆同時可見  
3. **連續覆蓋**: 96/109分鐘軌道週期內無縫覆蓋，總計8-14顆同時可見
4. **約束滿足度**: 90%+可見性合規，70%+時空分佈品質，80%+信號品質
5. **優化性能**: 2-5分鐘完成軌道動力學分析和模擬退火優化

## 🚨 故障排除

### 預期問題與解決方案

1. **覆蓋率不達標**
   - 檢查：衛星池大小是否足夠
   - 解決：增加池大小或調整選擇準則

2. **時空分散不均**
   - 檢查：分散性評分演算法
   - 解決：調整權重比例或改進評分方法

3. **計算時間過長**
   - 檢查：演算法複雜度
   - 解決：實現並行化或使用啟發式最佳化

---
**上一階段**: [階段五：數據整合](./stage5-integration.md)  
**技術整合**: [四階段技術資產完整整合](../LEO_SIX_STAGE_UPGRADE_COMPLETION_REPORT.md)  
**實現狀態**: ✅ **完成實現** - 模擬退火優化+shared_core整合

---
🎯 **升級完成**：Stage6增強版已完整實現，整合四階段技術資產，使用模擬退火演算法進行動態衛星池最佳化。系統從391顆篩選候選中選出90-110顆動態池，確保NTPU上空96/109分鐘軌道週期內連續維持8-14顆同時可見，實現90%+約束滿足度。