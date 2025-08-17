# 衛星智能篩選系統 - 階段二開發

> **依據**：[@docs/satellite_data_preprocessing.md](../docs/satellite_data_preprocessing.md) 階段二處理順序優化

## 🎯 階段二：智能衛星篩選系統

**核心目的**：基於實際可見性和換手需求進行動態篩選，從 8,715 顆衛星篩選到目標配置數量

### 📋 實際職責範圍

- **輸入**：8,715 顆衛星完整軌道數據（階段一 SGP4 計算結果）
- **處理邏輯**：星座分離 → 地理篩選 → 換手適用性評分
- **輸出**：基於配置參數篩選的衛星子集（如 555 Starlink + 134 OneWeb）
- **效率提升**：減少約80%不相關衛星，大幅降低後續信號計算成本

### 🔧 技術模組架構

```
stage2_intelligent_filtering/
├── constellation_separation/     # 星座分離篩選邏輯
│   ├── constellation_separator.py
│   └── README.md
├── geographic_filtering/         # 地理相關性篩選  
│   ├── geographic_filter.py
│   └── README.md
├── handover_scoring/            # 換手適用性評分
│   ├── handover_scorer.py
│   └── README.md
└── README.md                    # 本文檔
```

## 📋 完整處理流程

### 🔄 階段 2.1：星座分離篩選
> **文檔**: [constellation_separation/README.md](./constellation_separation/README.md)

**核心原則**: Starlink 和 OneWeb **完全分離處理**，**禁用跨星座換手**

**技術特性**:
- **跨星座換手**: 技術上不可行，完全禁用
- **獨立篩選**: 每個星座採用各自最佳篩選策略  
- **星座特定配置**: 基於Ku/Ka頻段差異優化

**處理結果**:
```python
{
    "starlink": [...],  # ~8,064 顆 → 星座特定篩選
    "oneweb": [...]     # ~651 顆 → 星座特定篩選
}
```

### 🎯 階段 2.2：地理相關性篩選  
> **文檔**: [geographic_filtering/README.md](./geographic_filtering/README.md)

**目標位置**: 台灣 NTPU (24.9441°N, 121.3713°E)

**篩選標準**:
- **軌道傾角匹配**: 軌道傾角 > 觀測點緯度
- **可見性檢查**: 必須有可見時間點（仰角 ≥ 0°）
- **地理相關性評分**: 0-100 分綜合評估

**評分權重**:
- 軌道傾角適用性 (30%) + 可見性統計 (40%) + 高度優化 (20%) + 覆蓋持續性 (10%)

### 📊 階段 2.3：換手適用性評分
> **文檔**: [handover_scoring/README.md](./handover_scoring/README.md)

**星座特定評分邏輯**:

#### Starlink 評分 (針對 53°/550km 優化)
- 軌道傾角適用性 (30%) + 高度適用性 (25%) + 相位分散度 (20%) + 換手頻率 (15%) + 信號穩定性 (10%)

#### OneWeb 評分 (針對 87°/1200km 優化) 
- 軌道傾角適用性 (25%) + 高度適用性 (25%) + 極地覆蓋 (20%) + 軌道形狀 (20%) + 相位分散 (10%)

**選擇策略**:
- 按評分降序排列，選擇頂級衛星子集
- 支援靈活的數量配置（如 555+134, 150+50）

## 🚀 完整使用範例

```python
from constellation_separation.constellation_separator import ConstellationSeparator
from geographic_filtering.geographic_filter import GeographicFilter  
from handover_scoring.handover_scorer import HandoverScorer

# 完整階段二處理流程
def stage2_intelligent_filtering(stage1_data, selection_config):
    # Step 1: 星座分離
    separator = ConstellationSeparator()
    separated_data = separator.separate_constellations(stage1_data)
    constellation_filtered = separator.apply_constellation_specific_filtering(separated_data)
    
    # Step 2: 地理相關性篩選
    geo_filter = GeographicFilter()
    geo_filtered = geo_filter.apply_geographic_filtering(constellation_filtered)
    
    # Step 3: 換手適用性評分和選擇
    scorer = HandoverScorer()
    scored_data = scorer.apply_handover_scoring(geo_filtered)
    
    # 基於配置選擇頂級衛星
    selected_satellites = scorer.select_top_satellites(scored_data, selection_config)
    
    return selected_satellites

# 使用範例
stage1_output = load_stage1_data()  # 8,715 顆衛星數據
selection_config = {"starlink": 555, "oneweb": 134}

final_satellites = stage2_intelligent_filtering(stage1_output, selection_config)
```

## 📊 預期效果分析

### 篩選效率

```
處理流程效果:
├── 輸入: 8,715 顆衛星 (100%)
├── 星座分離: ~8,715 顆 → 分離處理
├── 地理篩選: ~減少 80% 不相關衛星
├── 換手評分: 評分排序和智能選擇
└── 輸出: 150-555 顆衛星 (依配置而定)
```

### 質量提升

- **篩選精度**: 基於真實軌道數據的多維度評估
- **星座優化**: 針對不同星座的特性優化
- **地理相關**: 針對 NTPU 觀測點的地理優化
- **換手適用**: 基於換手需求的智能評分選擇

## ⚠️ 重要澄清

**數量配置來源**：
- 150+50、555+134 等配置來自**系統參數**，非階段二決定
- 來自完整軌道週期分析結果（v4.0 突破）
- 階段二**接受**這些配置，實現對應的篩選邏輯

**階段二不負責**：
- ❌ 決定衛星數量配置
- ❌ 動態數量配置決策  
- ❌ 系統參數設定

**階段二負責**：
- ✅ 實現篩選算法
- ✅ 星座分離處理
- ✅ 地理相關性優化
- ✅ 換手適用性評分

## 📈 開發狀態

- ✅ **星座分離篩選**: 完整實現，支援 Starlink/OneWeb 分離處理
- ✅ **地理相關性篩選**: 完整實現，NTPU 觀測點優化  
- ✅ **換手適用性評分**: 完整實現，星座特定評分邏輯
- ✅ **統一介面**: 提供完整的階段二處理流程

---

**依據 @docs/satellite_data_preprocessing.md 的階段二處理順序優化架構完整實現**