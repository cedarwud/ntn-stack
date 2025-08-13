# 星座分離篩選模組

> **依據**：[@docs/satellite_data_preprocessing.md](../../docs/satellite_data_preprocessing.md) 階段 2.1 星座分離篩選

## 🎯 核心原則

**完全分離處理**：Starlink 和 OneWeb **完全分離處理**，**禁用跨星座換手**

### 📋 技術邏輯

- **跨星座換手**：**技術上不可行** - 不同星座間無法換手
- **獨立篩選**：每個星座採用各自最佳的篩選策略
- **星座特定優化**：基於各星座的技術特性進行優化

## 🛰️ 星座特性配置

### Starlink 配置
```python
starlink_config = {
    "frequency_ghz": 12.0,          # Ku 頻段
    "altitude_km": 550,             # 平均軌道高度
    "inclination_deg": 53,          # 軌道傾角
    "orbital_period_min": 96,       # 軌道週期
    "tx_power_dbm": 43.0,          # 發射功率
    "antenna_gain_db": 15.0        # 最大天線增益
}
```

### OneWeb 配置
```python
oneweb_config = {
    "frequency_ghz": 20.0,          # Ka 頻段
    "altitude_km": 1200,            # 平均軌道高度
    "inclination_deg": 87,          # 極地軌道傾角
    "orbital_period_min": 109,      # 軌道週期
    "tx_power_dbm": 40.0,          # 發射功率
    "antenna_gain_db": 18.0        # 高增益天線
}
```

## 🔧 核心功能

### ConstellationSeparator 類

- `separate_constellations()`: 將混合衛星數據分離為獨立星座
- `apply_constellation_specific_filtering()`: 應用星座特定篩選邏輯
- `get_separation_statistics()`: 獲取分離統計信息

## 📊 預期效果

**輸入**：8,715 顆混合衛星數據  
**輸出**：按星座分離的衛星數據集

```
分離結果:
├── Starlink: ~8,064 顆 → 星座特定篩選
├── OneWeb: ~651 顆 → 星座特定篩選
└── 總計: 8,715 顆 → 獨立處理流程
```

## 🚀 使用範例

```python
from constellation_separator import ConstellationSeparator

separator = ConstellationSeparator()

# 分離星座
separated = separator.separate_constellations(stage1_data)
filtered = separator.apply_constellation_specific_filtering(separated)
stats = separator.get_separation_statistics(filtered)
```

---

**星座完全分離：技術約束導向的設計決策**