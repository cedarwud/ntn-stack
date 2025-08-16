# 演算法庫

LEO衛星動態池規劃核心演算法集合

## 演算法概覽

### 1. 模擬退火演算法 `simulated_annealing/`
**用途**: Phase 1動態池最佳化
**特點**: 
- 全域搜尋避免局部最優
- 溫度調節接受劣解
- 適合大規模組合最佳化問題

**核心公式**:
```
接受機率 = exp(-(cost_new - cost_current) / temperature)
溫度更新 = temperature * cooling_rate
```

**參數配置**:
- 初始溫度: 1000.0
- 冷卻率: 0.95
- 最大迭代: 10,000次
- 停滯容忍: 100次

### 2. SGP4軌道預測 `sgp4_propagation/`
**用途**: 精確衛星位置計算
**特點**:
- 基於NORAD TLE數據
- 考慮大氣阻力、J2攝動
- 亞公里級精度

**實現要點**:
```python
position, velocity = sgp4(satellite, julian_date)
lat, lon, alt = geodetic_coordinates(position)
elevation, azimuth = observer_angles(position, observer)
```

### 3. 地理相關性評分 `geographic_scoring/`
**用途**: 衛星篩選評分系統
**特點**:
- NTPU觀測點優化
- 多維度權重評分
- 星座特定調整

**評分公式**:
```
總分 = Σ(維度_i * 權重_i)
維度 = [傾角適用性, 高度適用性, 相位分散, 信號穩定性]
```

### 4. A4/A5/D2事件檢測 `event_detection/`
**用途**: 3GPP NTN換手事件識別
**特點**:
- 符合3GPP TS 38.331標準
- 多類型事件同時檢測
- 信心分數評估

**觸發條件**:
- **A4**: neighbor_rsrp > -100 dBm
- **A5**: serving_rsrp < -110 dBm AND neighbor_rsrp > -100 dBm  
- **D2**: serving_distance > 5000 km AND neighbor_distance < 3000 km

### 5. 可見性計算 `visibility_calculation/`
**用途**: 衛星可見性判定
**特點**:
- 仰角門檻檢查
- 大氣遮蔽考慮
- 實時計算優化

**計算流程**:
```python
1. 地心座標轉換
2. 觀測者相對位置
3. 仰角計算: arctan(altitude / ground_distance)
4. 遮蔽檢查: elevation >= threshold
```

### 6. RSRP精確計算 `rsrp_calculation/`
**用途**: Ku頻段12GHz信號強度計算
**特點**:
- 自由空間路徑損耗
- 仰角增益補償
- 大氣衰減修正

**計算公式**:
```
RSRP = Tx_Power + Antenna_Gain - Path_Loss - Atmospheric_Loss
Path_Loss = 20*log10(distance) + 20*log10(frequency) + 32.45
```

### 7. 時空分佈優化 `temporal_distribution/`
**用途**: 確保衛星時空分散
**特點**:
- 避免同時出現/消失
- 時間聚集懲罰
- 相位分散最佳化

**分佈指標**:
```python
聚集懲罰 = Σ max(0, (min_gap - actual_gap) / min_gap)
分散品質 = standard_deviation(appearance_times) / max_possible_std
```

## 演算法比較

| 演算法 | 時間複雜度 | 空間複雜度 | 適用場景 | 準確度 |
|--------|------------|------------|----------|--------|
| 模擬退火 | O(n*k) | O(n) | 組合最佳化 | 85-95% |
| SGP4 | O(1) | O(1) | 軌道預測 | >99% |
| 地理評分 | O(n) | O(1) | 衛星篩選 | 80-90% |
| 事件檢測 | O(m*n) | O(m) | 換手決策 | >95% |
| 可見性計算 | O(1) | O(1) | 即時判定 | >99% |

## 參數調優指南

### 模擬退火調優
```python
# 高品質解 (慢)
initial_temperature = 1000.0
cooling_rate = 0.95
max_iterations = 10000

# 快速收斂 (快)  
initial_temperature = 500.0
cooling_rate = 0.90
max_iterations = 5000
```

### 篩選門檻調優
```python
# 嚴格篩選 (少候選)
geographic_threshold = 80.0
min_score_threshold = 85.0

# 寬鬆篩選 (多候選)
geographic_threshold = 60.0
min_score_threshold = 70.0
```

### 事件門檻調優
```python
# 敏感檢測 (頻繁換手)
a4_threshold = -105.0  # 更低門檻
hysteresis = 2.0       # 更小滯後

# 穩定檢測 (減少換手)
a4_threshold = -95.0   # 更高門檻  
hysteresis = 5.0       # 更大滯後
```

## 驗證方法

### 1. 單元測試
```bash
pytest algorithms/tests/test_simulated_annealing.py
pytest algorithms/tests/test_sgp4_propagation.py
pytest algorithms/tests/test_event_detection.py
```

### 2. 基準測試
```python
# 與業界標準對比
sgp4_accuracy = compare_with_orekit()
event_detection_f1 = compare_with_3gpp_reference()
optimization_quality = compare_with_genetic_algorithm()
```

### 3. 性能分析
```python
# 執行時間分析
%timeit simulated_annealing_optimize(candidates)
%timeit sgp4_propagate(satellite, time_points)
%timeit detect_handover_events(timeline)
```

## 擴展演算法

### 未來演算法
- **遺傳演算法**: 作為模擬退火的替代方案
- **粒子群最佳化**: 多目標最佳化
- **蟻群演算法**: 動態路徑規劃
- **深度Q網路**: Phase 2強化學習

### 研究方向
- **多目標最佳化**: 同時優化信號品質、能耗、延遲
- **動態調整**: 根據實時狀況調整演算法參數
- **混合演算法**: 結合多種演算法的優勢
- **分散式計算**: 支援大規模衛星星座

---

**演算法庫是整個LEO衛星系統的計算核心，提供精確、高效的數學工具支援。**