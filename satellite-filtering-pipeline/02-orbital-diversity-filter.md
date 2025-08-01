# 第二階段：軌道多樣性篩選設計

**狀態**: 🚧 待開發  
**計畫開始**: 2025-08-02  
**預計檔案**: `/simworld/backend/orbital_diversity_filter.py`

## 📋 設計目標

從第一階段篩選的 2,358 顆衛星中，進一步精選 500 顆具有最佳軌道多樣性的衛星：
- **軌道平面分布** - 確保不同 RAAN 的均勻覆蓋
- **時間覆蓋平衡** - 24 小時內無衛星空窗期
- **品質優先** - 選擇每個軌道平面的最佳代表
- **星座平衡** - 維持 Starlink/OneWeb 合理比例

## 🏗️ 篩選架構設計

### 1️⃣ 軌道平面分群
```python
class OrbitalDiversityFilter:
    def __init__(self):
        self.raan_bins = 36  # 每 10 度一個區間
        self.target_satellites_per_bin = {
            'starlink': 3-5,    # 每組選 3-5 顆
            'oneweb': 2-3       # 每組選 2-3 顆
        }
```

### 2️⃣ 品質評分系統
```python
def calculate_quality_score(satellite):
    """計算衛星品質分數 (0-100)"""
    scores = {
        'orbital_stability': 25,    # 軌道穩定性
        'coverage_uniformity': 25,  # 覆蓋均勻性
        'handover_frequency': 25,   # 換手機會頻率
        'signal_quality': 25        # 預估信號品質
    }
    return weighted_sum(scores)
```

### 3️⃣ 時間覆蓋分析
```python
def analyze_temporal_coverage(selected_satellites):
    """確保 24 小時覆蓋無空窗"""
    time_slots = create_24h_slots(interval_minutes=10)
    coverage_map = {}
    
    for slot in time_slots:
        visible_satellites = calculate_visible(selected_satellites, slot)
        if len(visible_satellites) < MIN_VISIBLE_SATELLITES:
            return False, f"空窗期: {slot}"
    
    return True, "全時段覆蓋"
```

### 4️⃣ 多樣性優化
```python
def optimize_diversity(candidates):
    """最大化軌道參數多樣性"""
    diversity_metrics = {
        'inclination_diversity': [],     # 傾角多樣性
        'altitude_diversity': [],        # 高度多樣性
        'raan_coverage': [],            # RAAN 覆蓋度
        'phase_distribution': []        # 相位分布
    }
```

## 📊 預期篩選分配

| 類別 | 輸入數量 | 目標數量 | 選擇策略 |
|------|----------|----------|----------|
| **Starlink** | 1,707 | ~350 | 軌道平面均勻選擇 |
| **OneWeb** | 651 | ~150 | 極地軌道價值保留 |
| **總計** | 2,358 | 500 | 多樣性最大化 |

## 🔧 核心算法設計

### 軌道平面分群算法
```python
def group_by_orbital_plane(satellites):
    """按 RAAN 將衛星分組"""
    groups = defaultdict(list)
    
    for sat in satellites:
        raan = sat['RA_OF_ASC_NODE']
        bin_index = int(raan / 10)  # 10度一組
        groups[bin_index].append(sat)
    
    return groups
```

### 品質評分細節
```python
def evaluate_orbital_stability(satellite):
    """評估軌道穩定性 (0-25 分)"""
    eccentricity_score = (0.1 - satellite['ECCENTRICITY']) / 0.1 * 10
    altitude_consistency = calculate_altitude_variance(satellite)
    return min(25, eccentricity_score + altitude_consistency)

def evaluate_coverage_uniformity(satellite):
    """評估覆蓋均勻性 (0-25 分)"""
    pass_intervals = calculate_pass_intervals(satellite)
    uniformity = 1 - (np.std(pass_intervals) / np.mean(pass_intervals))
    return uniformity * 25
```

### 時間覆蓋優化
```python
def ensure_temporal_coverage(satellite_groups):
    """確保無衛星空窗期"""
    selected = []
    time_coverage = np.zeros(24 * 6)  # 10分鐘為單位
    
    for group in satellite_groups:
        # 計算每顆衛星的覆蓋貢獻
        for sat in sorted(group, key=lambda x: x['quality_score'], reverse=True):
            coverage_gain = calculate_coverage_gain(sat, time_coverage)
            if coverage_gain > THRESHOLD:
                selected.append(sat)
                update_coverage(time_coverage, sat)
```

## 💡 關鍵設計決策

### 1. 動態配額調整
- 根據實際覆蓋需求調整每組衛星數量
- 優先填補時間空窗期
- 保持最小冗餘度

### 2. 星座特性考量
- **Starlink**: 多軌道平面，重點確保 RAAN 分布
- **OneWeb**: 極地軌道，重點保留不同相位

### 3. 品質與數量平衡
- 寧缺毋濫：品質低於閾值不選
- 確保基本覆蓋後追求多樣性
- 預留 buffer 應對異常情況

## 🚀 實施計畫

### Phase 1: 基礎框架 (第1天)
- [ ] 建立 `OrbitalDiversityFilter` 類
- [ ] 實現軌道平面分群
- [ ] 基礎品質評分系統

### Phase 2: 核心算法 (第2天)
- [ ] 實現時間覆蓋分析
- [ ] 多樣性優化算法
- [ ] 動態配額調整

### Phase 3: 整合測試 (第3天)
- [ ] 與第一階段篩選整合
- [ ] 性能優化
- [ ] 結果驗證

## ✅ 完成標準

- [ ] 精確篩選至 500±10 顆衛星
- [ ] 無 10 分鐘以上衛星空窗期
- [ ] RAAN 覆蓋度 > 90%
- [ ] 平均品質分數 > 75
- [ ] 處理時間 < 30 秒

## 📚 相關參考

- 第一階段篩選：`01-zero-tolerance-filter.md`
- 用途分層設計：`03-tier-classification.md`
- SGP4 計算器：`/simworld/backend/app/services/sgp4_calculator.py`
