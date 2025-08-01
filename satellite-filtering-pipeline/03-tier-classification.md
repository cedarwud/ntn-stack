# 第三階段：用途分層分類設計

**狀態**: 📋 待開發  
**計畫開始**: 2025-08-05  
**預計整合**: 統一預處理管道

## 📋 設計目標

將第二階段篩選的 500 顆衛星按用途進行分層標記，確保：
- **Tier 1**: 3D 動畫渲染最佳化 (20 顆)
- **Tier 2**: 換手事件圖表展示 (80 顆，包含 Tier 1)
- **Tier 3**: RL 訓練數據集 (500 顆，包含所有層級)

## 🏗️ 分層架構設計

### 層級定義與特性
```python
TIER_DEFINITIONS = {
    'tier_1': {
        'name': '3D Visualization',
        'count': 20,
        'criteria': {
            'visibility_duration': 'high',    # 長時間可見
            'orbital_stability': 'excellent', # 穩定軌道
            'signal_strength': 'strong',      # 強信號
            'handover_diversity': 'moderate'  # 適度換手場景
        }
    },
    'tier_2': {
        'name': 'Chart Display',
        'count': 80,
        'criteria': {
            'handover_scenarios': 'diverse',  # 多樣換手場景
            'event_types': 'complete',        # 涵蓋所有事件類型
            'temporal_coverage': 'balanced',  # 時間平衡
            'constellation_mix': 'optimal'    # 星座混合
        }
    },
    'tier_3': {
        'name': 'RL Training',
        'count': 500,
        'criteria': {
            'scenario_diversity': 'maximum',  # 最大場景多樣性
            'edge_cases': 'included',         # 包含邊緣案例
            'training_value': 'high',         # 高訓練價值
            'coverage_completeness': 'full'   # 完整覆蓋
        }
    }
}
```

## 📊 分層選擇策略

### Tier 1: 3D 可視化優選 (20 顆)
| 優先級 | 選擇標準 | 權重 | 說明 |
|--------|----------|------|------|
| 1 | 渲染效率 | 30% | WebGL 渲染負載考量 |
| 2 | 軌道代表性 | 25% | 不同軌道類型展示 |
| 3 | 視覺連續性 | 25% | 平滑的軌道轉換 |
| 4 | 換手展示價值 | 20% | 清晰的換手場景 |

### Tier 2: 圖表展示增強 (60 顆額外)
| 優先級 | 選擇標準 | 權重 | 說明 |
|--------|----------|------|------|
| 1 | 事件類型覆蓋 | 35% | D2/D1/A4/T1 完整性 |
| 2 | 時序分布 | 25% | 不同時段的事件 |
| 3 | 換手頻率變化 | 20% | 高低頻換手場景 |
| 4 | 數據完整性 | 20% | 完整軌道週期 |

### Tier 3: RL 訓練擴充 (420 顆額外)
| 優先級 | 選擇標準 | 權重 | 說明 |
|--------|----------|------|------|
| 1 | 場景多樣性 | 40% | 訓練泛化能力 |
| 2 | 邊緣案例 | 25% | 極端情況處理 |
| 3 | 負載平衡 | 20% | 不同負載場景 |
| 4 | 地理覆蓋 | 15% | 全區域訓練 |

## 🔧 核心算法設計

### 多目標優化選擇
```python
class TierClassifier:
    def __init__(self, satellites: List[Dict]):
        self.satellites = satellites
        self.tier_assignments = {}
        
    def classify_tiers(self):
        """執行分層分類"""
        # Step 1: 選擇 Tier 1 (最優 20 顆)
        tier1 = self._select_tier1_satellites()
        
        # Step 2: 選擇 Tier 2 (包含 Tier 1 + 60 顆)
        tier2 = self._select_tier2_satellites(tier1)
        
        # Step 3: 標記 Tier 3 (全部 500 顆)
        tier3 = self.satellites
        
        return self._create_tier_mapping(tier1, tier2, tier3)
```

### Tier 1 選擇算法
```python
def _select_tier1_satellites(self) -> List[Dict]:
    """選擇 3D 可視化最佳衛星"""
    scores = []
    
    for sat in self.satellites:
        score = self._calculate_visualization_score(sat)
        scores.append((score, sat))
    
    # 選擇分數最高的 20 顆
    scores.sort(reverse=True)
    selected = [sat for score, sat in scores[:20]]
    
    # 確保基本的星座平衡
    return self._ensure_constellation_balance(selected)

def _calculate_visualization_score(self, sat: Dict) -> float:
    """計算 3D 可視化適用性分數"""
    scores = {
        'rendering_efficiency': self._eval_rendering_efficiency(sat) * 0.30,
        'orbital_representation': self._eval_orbital_diversity(sat) * 0.25,
        'visual_continuity': self._eval_visual_continuity(sat) * 0.25,
        'handover_clarity': self._eval_handover_clarity(sat) * 0.20
    }
    return sum(scores.values())
```

### Tier 2 擴展算法
```python
def _select_tier2_satellites(self, tier1: List[Dict]) -> List[Dict]:
    """擴展選擇圖表展示衛星"""
    tier2 = tier1.copy()  # 包含所有 Tier 1
    remaining = [s for s in self.satellites if s not in tier1]
    
    # 計算事件類型覆蓋缺口
    event_coverage = self._analyze_event_coverage(tier1)
    needed_satellites = []
    
    for sat in remaining:
        if len(tier2) >= 80:
            break
            
        # 評估對事件覆蓋的貢獻
        contribution = self._evaluate_event_contribution(sat, event_coverage)
        if contribution > THRESHOLD:
            tier2.append(sat)
            self._update_event_coverage(event_coverage, sat)
    
    return tier2
```

### 分層標記系統
```python
def _create_tier_mapping(self, tier1, tier2, tier3):
    """創建衛星的分層標記"""
    tier_map = {}
    
    for sat in tier3:  # 所有衛星
        sat_id = sat['satellite_id']
        
        if sat in tier1:
            tier_map[sat_id] = ['tier_1', 'tier_2', 'tier_3']
        elif sat in tier2:
            tier_map[sat_id] = ['tier_2', 'tier_3']
        else:
            tier_map[sat_id] = ['tier_3']
            
        # 添加用途標記
        sat['tier_labels'] = tier_map[sat_id]
        sat['primary_tier'] = tier_map[sat_id][0]
    
    return tier_map
```

## 💡 關鍵設計考量

### 1. 層級包含關係
- Tier 1 ⊆ Tier 2 ⊆ Tier 3
- 確保數據一致性和可追溯性
- 簡化前端使用邏輯

### 2. 動態調整機制
```python
# 根據實際需求調整層級大小
TIER_SIZE_CONSTRAINTS = {
    'tier_1': {
        'min': 15,
        'max': 25,
        'optimal': 20
    },
    'tier_2': {
        'min': 60,
        'max': 100,
        'optimal': 80
    }
}
```

### 3. 星座平衡策略
```python
def _ensure_constellation_balance(self, selected):
    """確保 Starlink/OneWeb 合理比例"""
    starlink_count = sum(1 for s in selected if s['constellation'] == 'starlink')
    oneweb_count = len(selected) - starlink_count
    
    # 目標比例約 7:3 (反映實際星座規模)
    target_ratio = 0.7
    actual_ratio = starlink_count / len(selected)
    
    if abs(actual_ratio - target_ratio) > 0.2:
        return self._rebalance_selection(selected, target_ratio)
    
    return selected
```

## 🚀 整合方案

### 統一輸出格式
```json
{
  "satellite": {
    "id": "STARLINK-1234",
    "constellation": "starlink",
    "tier_labels": ["tier_1", "tier_2", "tier_3"],
    "primary_tier": "tier_1",
    "tier_scores": {
      "visualization": 92.5,
      "chart_display": 88.3,
      "rl_training": 85.7
    },
    "orbital_data": {...},
    "handover_events": {...}
  }
}
```

### API 使用範例
```python
# 前端調用範例
# 3D 動畫只載入 Tier 1
GET /api/v1/satellites/unified/timeseries?tier=tier_1

# 圖表展示載入 Tier 2
GET /api/v1/satellites/unified/timeseries?tier=tier_2

# RL 訓練載入全部
GET /api/v1/satellites/unified/timeseries?tier=tier_3
```

## ✅ 完成標準

- [ ] 精確分層：20/80/500 顆
- [ ] 層級包含關係正確
- [ ] 事件類型完整覆蓋
- [ ] API 支援分層查詢
- [ ] 性能影響 < 5%

## 📚 相關文件

- 軌道多樣性篩選：`02-orbital-diversity-filter.md`
- 統一預處理設計：`04-unified-preprocessing.md`
- 實施計畫：`06-implementation-plan.md`
