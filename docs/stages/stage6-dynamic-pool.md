# 🛰️ 階段六：動態衛星池規劃 (新增)

[🔄 返回數據流程導航](../data-flow-index.md) > 階段六

## 📖 階段概述

**目標**：為立體圖生成時空分散的動態衛星池，實現整個軌道週期的平衡覆蓋  
**輸入**：階段五的混合存儲數據  
**輸出**：動態衛星池規劃結果  
**處理對象**：從563顆候選中篩選動態覆蓋衛星池  
**處理時間**：約 3-5 分鐘

⚠️ **重要提醒**：本階段的衛星池數量（Starlink 45顆、OneWeb 20顆）僅為初步估算，實際數字需要開發完成並驗證後才能確認。

## 🎯 動態覆蓋需求

### 核心挑戰
- **不是**某個時間點的固定數量（如10-15顆）
- **而是**整個軌道週期內動態維持目標可見數量
- 需要**足夠大的衛星池**來實現自然的衛星進出
- 衛星需要**時空分散**，避免同時出現/消失的問題

### 目標覆蓋規格
```python
DYNAMIC_COVERAGE_TARGETS = {
    'starlink': {
        'min_elevation_deg': 5.0,
        'target_visible_range': (10, 15),  # 同時可見衛星數
        'target_handover_range': (6, 8),   # handover候選數
        'orbit_period_minutes': 96,
        'estimated_pool_size': 45  # ⚠️ 估算值，待驗證
    },
    'oneweb': {
        'min_elevation_deg': 10.0,
        'target_visible_range': (3, 6),
        'target_handover_range': (2, 3),
        'orbit_period_minutes': 109,
        'estimated_pool_size': 20  # ⚠️ 估算值，待驗證
    }
}
```

## 🧠 動態池規劃演算法

### 核心演算法架構
```python
class DynamicSatellitePoolPlanner:
    """動態衛星池規劃器 - 確保整個軌道週期的平衡覆蓋"""
    
    def __init__(self, config):
        self.observer_lat = 24.9441667   # NTPU座標
        self.observer_lon = 121.3713889
        self.time_resolution = 30        # 秒
        
    async def plan_dynamic_pools(self, satellite_data):
        """規劃動態衛星池"""
        
        # 1. 分析每顆衛星的可見時間窗口
        visibility_analysis = await self._analyze_visibility_windows(
            satellite_data
        )
        
        # 2. 時空分散演算法 - 關鍵創新
        starlink_pool = await self._plan_time_distributed_pool(
            visibility_analysis['starlink'],
            target_visible=(10, 15),
            orbit_period=96
        )
        
        oneweb_pool = await self._plan_time_distributed_pool(
            visibility_analysis['oneweb'],
            target_visible=(3, 6),
            orbit_period=109
        )
        
        # 3. 動態覆蓋驗證
        coverage_quality = await self._verify_dynamic_coverage(
            starlink_pool, oneweb_pool
        )
        
        return {
            'starlink_pool': starlink_pool,
            'oneweb_pool': oneweb_pool,
            'coverage_verification': coverage_quality
        }
```

### 時空分散演算法詳解

#### 1. 可見時間窗口分析
```python
async def _analyze_visibility_windows(self, satellites):
    """分析每顆衛星在完整軌道週期內的可見窗口"""
    
    windows = {}
    
    for satellite in satellites:
        satellite_windows = []
        in_view = False
        window_start = None
        
        # 掃描整個軌道週期 (96分鐘 × 2個週期 = 192分鐘)
        for minute in range(192):
            elevation = self._calculate_elevation_at_time(satellite, minute)
            
            if elevation >= satellite.min_elevation and not in_view:
                # 衛星進入可見範圍
                in_view = True
                window_start = minute
                
            elif elevation < satellite.min_elevation and in_view:
                # 衛星離開可見範圍
                in_view = False
                
                window = {
                    'start_minute': window_start,
                    'end_minute': minute,
                    'duration': minute - window_start,
                    'peak_elevation': self._get_peak_elevation(
                        satellite, window_start, minute
                    )
                }
                satellite_windows.append(window)
        
        windows[satellite.id] = {
            'windows': satellite_windows,
            'total_visible_time': sum(w['duration'] for w in satellite_windows),
            'coverage_ratio': sum(w['duration'] for w in satellite_windows) / 96
        }
    
    return windows
```

#### 2. 時空分散選擇演算法
```python
async def _plan_time_distributed_pool(self, visibility_windows, target_visible, orbit_period):
    """核心時空分散演算法 - 確保衛星不會同時出現/消失"""
    
    # 創建時間槽網格（每分鐘一個槽）
    time_slots = [[] for _ in range(orbit_period)]
    selected_pool = []
    
    # 按多維度評分排序候選衛星
    scored_candidates = self._score_satellites_for_distribution(
        visibility_windows, target_visible
    )
    
    for candidate in scored_candidates:
        # 檢查時空衝突
        conflicts = self._check_temporal_conflicts(
            candidate, time_slots, target_visible[1]  # max_visible
        )
        
        if not conflicts:
            # 加入衛星池並更新時間槽
            self._add_to_time_slots(candidate, time_slots)
            selected_pool.append(candidate)
            
            # 檢查是否達到足夠覆蓋
            if self._check_coverage_adequate(time_slots, target_visible):
                break
    
    return selected_pool

def _score_satellites_for_distribution(self, windows, target_visible):
    """多維度評分確保最佳分散性"""
    
    scored = []
    
    for sat_id, window_data in windows.items():
        score = 0.0
        
        # 1. 可見時間品質 (30%)
        visibility_score = min(1.0, window_data['total_visible_time'] / 30)
        score += visibility_score * 0.3
        
        # 2. 時間分散性 (40%) - 關鍵指標
        dispersion_score = self._calculate_temporal_dispersion(window_data['windows'])
        score += dispersion_score * 0.4
        
        # 3. 信號品質 (20%)
        signal_score = self._get_signal_quality_score(sat_id)
        score += signal_score * 0.2
        
        # 4. 軌道多樣性 (10%)
        orbit_diversity = self._calculate_orbit_diversity_score(sat_id)
        score += orbit_diversity * 0.1
        
        scored.append({
            'satellite_id': sat_id,
            'distribution_score': score,
            'windows': window_data['windows'],
            'selection_rationale': {
                'visibility_score': visibility_score,
                'dispersion_score': dispersion_score,
                'signal_score': signal_score,
                'orbit_diversity': orbit_diversity
            }
        })
    
    # 按分散性評分降序排序
    return sorted(scored, key=lambda x: x['distribution_score'], reverse=True)
```

### 3. 動態覆蓋驗證

```python
async def _verify_dynamic_coverage(self, starlink_pool, oneweb_pool):
    """驗證整個軌道週期的動態覆蓋品質"""
    
    verification_results = {}
    
    # Starlink 覆蓋驗證
    starlink_timeline = self._simulate_coverage_timeline(
        starlink_pool, orbit_period=96, target_range=(10, 15)
    )
    
    # OneWeb 覆蓋驗證  
    oneweb_timeline = self._simulate_coverage_timeline(
        oneweb_pool, orbit_period=109, target_range=(3, 6)
    )
    
    verification_results = {
        'starlink': {
            'pool_size': len(starlink_pool),
            'coverage_timeline': starlink_timeline,
            'target_met_ratio': sum(1 for t in starlink_timeline if t['meets_target']) / len(starlink_timeline),
            'avg_visible': sum(t['visible_count'] for t in starlink_timeline) / len(starlink_timeline),
            'coverage_gaps': [t for t in starlink_timeline if not t['meets_target']]
        },
        'oneweb': {
            'pool_size': len(oneweb_pool),
            'coverage_timeline': oneweb_timeline,
            'target_met_ratio': sum(1 for t in oneweb_timeline if t['meets_target']) / len(oneweb_timeline),
            'avg_visible': sum(t['visible_count'] for t in oneweb_timeline) / len(oneweb_timeline),
            'coverage_gaps': [t for t in oneweb_timeline if not t['meets_target']]
        }
    }
    
    return verification_results
```

## 📊 輸出數據格式

### 動態池規劃結果
```json
{
  "metadata": {
    "generation_time": "2025-08-14T12:00:00Z",
    "stage": "stage6_dynamic_pool_planning",
    "observer_location": {
      "latitude": 24.9441667,
      "longitude": 121.3713889,
      "location_name": "NTPU"
    },
    "planning_algorithm_version": "v1.0.0"
  },
  "starlink": {
    "estimated_pool_size": 45,
    "actual_pool_size": "TBD",
    "orbit_period_minutes": 96,
    "target_visible_range": [10, 15],
    "target_handover_range": [6, 8],
    "min_elevation_deg": 5.0,
    "coverage_statistics": {
      "target_met_ratio": "TBD",
      "avg_visible_satellites": "TBD",
      "coverage_gaps_count": "TBD"
    },
    "selected_satellites": [
      {
        "satellite_id": "STARLINK-XXXX",
        "selection_score": "TBD",
        "visibility_windows": [],
        "selection_rationale": "time_space_distribution"
      }
    ]
  },
  "oneweb": {
    "estimated_pool_size": 20,
    "actual_pool_size": "TBD",
    "orbit_period_minutes": 109,
    "target_visible_range": [3, 6],
    "target_handover_range": [2, 3],
    "min_elevation_deg": 10.0,
    "coverage_statistics": {
      "target_met_ratio": "TBD",
      "avg_visible_satellites": "TBD",
      "coverage_gaps_count": "TBD"
    },
    "selected_satellites": []
  },
  "integration_notes": {
    "frontend_integration": "立體圖使用selected_satellites進行動畫渲染",
    "handover_simulation": "使用coverage_timeline進行換手場景模擬",
    "performance_expectations": "維持目標可見數量的95%+時間覆蓋"
  }
}
```

## 🏗️ 實現架構

### 主要實現位置
```bash
# 動態池規劃處理器
/netstack/src/stages/stage6_dynamic_pool_planner.py
├── Stage6DynamicPoolPlanner.plan_dynamic_pools()           # 主規劃邏輯
├── Stage6DynamicPoolPlanner.analyze_visibility_windows()   # 時間窗口分析
├── Stage6DynamicPoolPlanner.plan_time_distributed_pool()   # 時空分散選擇
└── Stage6DynamicPoolPlanner.verify_dynamic_coverage()      # 動態覆蓋驗證

# 時空分散演算法
/netstack/src/algorithms/spatial_temporal_distribution.py
├── TemporalDistributionAnalyzer.calculate_dispersion()     # 時間分散性計算
├── SpatialCoverageOptimizer.optimize_coverage()           # 空間覆蓋最佳化
└── DynamicCoverageVerifier.simulate_timeline()            # 動態覆蓋模擬
```

## 🔧 與現有架構整合

### 整合到階段五
```python
class Stage5IntegrationProcessor:
    
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

## ⚠️ 開發注意事項

### 數字估算說明
1. **Starlink 45顆**：基於96分鐘軌道週期和10-15顆目標的初步估算
2. **OneWeb 20顆**：基於109分鐘軌道週期和3-6顆目標的初步估算
3. **實際數字**：需要完整實現演算法並進行動態覆蓋模擬才能確定

### 開發驗證步驟
1. 實現可見時間窗口分析
2. 開發時空分散選擇演算法
3. 進行動態覆蓋模擬驗證
4. 調整衛星池大小以達到目標覆蓋率
5. 最佳化演算法性能

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
**相關文檔**: [new.md需求](../new.md)  
**實現狀態**: 🔄 規劃階段，待開發實現

---
⚠️ **重要提醒**：本文檔中的所有數字（45顆、20顆等）均為基於理論分析的初步估算，實際的衛星池大小需要在完成演算法實現並進行動態覆蓋模擬後才能確定。