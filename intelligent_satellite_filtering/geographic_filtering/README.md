# 地理相關性篩選模組

> **依據**：[@docs/satellite_data_preprocessing.md](../../docs/satellite_data_preprocessing.md) 階段 2.2 地理相關性篩選

## 🎯 目標位置

**觀測點**：台灣 NTPU (24.9441°N, 121.3713°E)

### 📍 觀測點配置
```python
observer_location = {
    "name": "National Taipei University",
    "latitude": 24.9441667,  # 度
    "longitude": 121.3713889,  # 度  
    "altitude": 100,  # 米，海拔高度
    "timezone": "Asia/Taipei"
}
```

## 🔍 篩選邏輯

### 地理相關性檢查

1. **軌道傾角匹配**：軌道傾角 > 觀測點緯度
2. **高度合理性**：200-2000km LEO 衛星範圍
3. **可見性檢查**：必須有可見時間點（仰角 ≥ 0°）

### 地理相關性評分系統 (0-100 分)

#### 📊 評分權重分配
- **軌道傾角適用性**: 30% - 針對觀測點緯度優化
- **可見性統計**: 40% - 可見比例、最大仰角、平均仰角
- **軌道高度優化**: 20% - 不同高度區間的適用程度
- **覆蓋持續性**: 10% - 可見時段的連續性

#### 🎯 評分標準

**軌道傾角適用性**：
- < 觀測點緯度：0分 (無法覆蓋)
- 觀測點緯度+10度內：50分 (勉強覆蓋)  
- 觀測點緯度+30度內：100分 (良好覆蓋)
- 極地軌道：80分 (略過頭但可用)

**軌道高度優化**：
- 400-600km：100分 (Starlink 最佳)
- 1100-1300km：90分 (OneWeb 最佳)
- 300-800km：80分 (良好 LEO)
- 800-1500km：70分 (可接受)

## 🔧 核心功能

### GeographicFilter 類

- `apply_geographic_filtering()`: 應用地理相關性篩選
- `_calculate_geographic_relevance_score()`: 計算地理相關性評分  
- `get_filtering_statistics()`: 獲取篩選統計信息

## 📊 預期效果

**篩選效果**：減少約 80% 不相關衛星

```
地理篩選結果:
├── 軌道傾角篩選: 移除無法覆蓋觀測點的軌道
├── 可見性篩選: 移除永不可見的衛星
├── 高度優化: 優先選擇適當高度的衛星  
└── 持續性評估: 評估覆蓋持續時間
```

## 🚀 使用範例

```python
from geographic_filter import GeographicFilter

geo_filter = GeographicFilter()

# 應用地理篩選
filtered_data = geo_filter.apply_geographic_filtering(constellation_data)
stats = geo_filter.get_filtering_statistics(original_data, filtered_data)

# 檢查評分
for satellite in filtered_data["starlink"]:
    geo_score = satellite["geographic_relevance_score"]
    print(f"衛星 {satellite['satellite_id']}: 地理評分 {geo_score}")
```

## 🎯 篩選標準

- **最低仰角門檻**：0° (地平線)
- **最大距離範圍**：5000km
- **地理相關區域**：50° 半徑
- **最低評分要求**：根據後續需求配置

---

**基於 NTPU 觀測點的智能地理優化**