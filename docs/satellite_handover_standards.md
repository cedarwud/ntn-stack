# 🛰️ NTN Stack 衛星換手仰角門檻標準規範

## 🎯 標準制定依據

### 技術參考標準
- **3GPP TS 38.331**: NTN 無線資源控制
- **3GPP TR 38.811**: NTN 研究報告
- **ITU-R P.618-14**: 衛星鏈路大氣衰減模型
- **47 CFR § 25.205**: 美國 FCC 最低天線仰角規範

### 物理原理
- **仰角 ≥ 10°**: 大氣氣體吸收、雨衰減可通過 ITU-R 模型預測  
- **仰角 5° – 10°**: 衰減與多徑效應加劇  
- **仰角 < 5°**: 信號不穩，法律與工程上不建議常態通訊  

## 🔄 分層仰角門檻標準

| 門檻類型   | 仰角標準 | 用途             | 標準符合性      |
|----------|--------|----------------|--------------|
| **理想服務** | ≥ 15°  | 最佳服務品質        | ✅ 超越標準      |
| **標準服務** | ≥ 10°  | 正常換手操作        | ✅ 3GPP NTN    |
| **可用服務** | ≥ 5°   | 邊緣區域覆蓋保障      | ✅ FCC 合規    |
| **緊急通訊** | ≥ 3°   | 特殊情況下保留通訊    | ⚠️ 特殊授權    |

### 分層換手策略

#### 1. 預備階段 (仰角 15° → 12°)  
**目的**: 爭取 10–20 秒準備時間  
- 掃描並評估候選衛星  
- 預留信道與資源  
- 路由表預配置  

#### 2. 標準執行 (仰角 12° → 8°)  
**目的**: 符合 3GPP NTN 標準的穩定切換  
- 執行換手決策  
- 維持信號品質  
- 避免通話中斷  

#### 3. 邊緣保障 (仰角 8° → 5°)  
**目的**: 延長邊緣區域服務  
- 降級服務模式  
- 緊急換手  
- 準備強制中斷  

## 🌍 環境調整係數

| 環境類型   | 調整係數 | 實際門檻      | 適用場景         |
|----------|-------|-----------|--------------|
| **理想環境** | 0.9   | 9.0°        | 海洋、平原        |
| **標準環境** | 1.0   | 10.0°       | 一般陸地        |
| **城市環境** | 1.2   | 12.0°       | 市區建築遮蔽      |
| **複雜地形** | 1.5   | 15.0°       | 山區、高樓        |
| **惡劣天氣** | 1.8   | 18.0°       | 暴雨、雪災區域      |

### 動態調整原則
- **信號品質**: 根據 SNR/RSRP 自動微調  
- **天氣條件**: 結合實時氣象數據  
- **網路負載**: 繁忙時提高門檻  
- **時間限制**: 每 30 秒一次更新  

## 🔧 系統實施標準

### 統一配置參數

```yaml
CoordinateSpecificOrbitEngine:
  min_elevation: 10.0
  service_elevation: 15.0
  emergency_elevation: 5.0
  environment: standard

LayeredElevationEngine:
  pre_handover_trigger: 12.0
  execution_threshold: 10.0
  critical_threshold: 5.0
  dynamic_adjustment: true
  weather_awareness: true
```

### API 規範

**請求**  
```
GET /api/satellite/visibility/v2?
  min_elevation=10.0&
  service_level=standard&
  environment=urban&
  weather=clear&
  dynamic=true
```

**回應格式**  
```json
{
  "applied_threshold": 12.0,
  "compliance": {
    "3gpp_ntn": true,
    "itu_r_p618": true,
    "fcc_part25": true
  },
  "visible_satellites": {
    "ideal": 643,      // 2025年數據：仰角 ≥ 15° (高品質)
    "standard": 965,   // 2025年數據：仰角 ≥ 10° (商業級)
    "minimum": 1447,   // 2025年數據：仰角 ≥ 5° (研究用)
    "total": 8042      // 2025年 Starlink 總數
  },
  "handover_readiness": {
    "preparation": 10,
    "execution": 8,
    "critical": 3
  }
}
```

## 📊 效能基準與驗證

| 門檻設定 | 可見衛星數 (2025) | 成功率   | 平均延遲  | 信號穩定性 |
|--------|-----------------|--------|--------|--------|
| 15°    | 643             | ≥ 99.9% | < 10 ms | < 1 dB |
| 10°    | 965             | ≥ 99.5% | < 20 ms | < 2 dB |
| 5°     | 1447            | ≥ 98%   | < 50 ms | < 4 dB |

## 🔄 3GPP 換手事件標準實現

### A4/A5/D2 事件定義與實現

#### 📊 Event A4: 鄰近衛星信號優於門檻
**標準參考**: 3GPP TS 38.331 Section 5.5.4.3
- **觸發條件**: `Mn + Ofn + Ocn - Hys > Threshold2`
- **離開條件**: `Mn + Ofn + Ocn + Hys < Threshold2`
- **實現門檻**: RSRP ≥ -100 dBm (鄰居衛星)
- **用途**: 識別新的優質換手候選

#### 📊 Event A5: 服務衛星劣化且鄰近衛星良好
**標準參考**: 3GPP TS 38.331 Section 5.5.4.4
- **觸發條件**: 
  - `Mp + Hys < Threshold1` (服務衛星劣化)
  - `Mn + Ofn + Ocn - Hys > Threshold2` (鄰居衛星良好)
- **實現門檻**: 
  - 服務衛星 RSRP < -110 dBm
  - 鄰居衛星 RSRP ≥ -100 dBm
- **用途**: 觸發緊急換手決策

#### 📊 Event D2: 基於距離的換手觸發
**標準參考**: 3GPP TS 38.331 Section 5.5.4.8
- **觸發條件**: 
  - 服務衛星距離 > 5000 km
  - 候選衛星距離 < 3000 km
- **用途**: LEO 衛星特有的距離優化換手

### 事件優先級與決策邏輯
```python
# 事件優先級排序 (實現於 satellite_ops_router.py:399)
A5 事件 → HIGH 優先級    # 服務品質劣化，需緊急換手
A4 事件 → MEDIUM 優先級  # 發現優質候選，可考慮換手  
D2 事件 → LOW 優先級     # 距離優化，非緊急換手
```

### RSRP 計算實現
**實現位置**: `satellite_ops_router.py:317-323`
```python
def calculate_rsrp_simple(sat):
    # 自由空間路徑損耗 (Ku頻段 12 GHz)
    fspl_db = 20 * math.log10(sat.distance_km) + 20 * math.log10(12.0) + 32.45
    elevation_gain = min(sat.elevation_deg / 90.0, 1.0) * 15  # 最大15dB增益
    tx_power = 43.0  # 43dBm發射功率
    return tx_power - fspl_db + elevation_gain
```

**RSRP 取值範圍**: -150 到 -50 dBm (基於真實 3D 距離計算)

### API 端點實現
**完整 API**: `POST /api/v1/satellite-ops/evaluate_handover`
- **輸入**: 服務衛星 ID、觀測者位置、篩選參數
- **輸出**: A4/A5/D2 事件分析、換手建議、信號品質評估
- **詳細文檔**: 參見 [API 接口使用指南](./api_reference.md#切換決策-api-netstack)

## ⚠️ 注意事項

1. **3°–5°** 僅限特殊授權或實驗  
2. **調整係數 ≤ 2.0**，以免過度保守  
3. **更新頻率 ≤ 30 秒**，保障系統穩定  
4. **緊急模式 ≤ 5 分鐘**，避免品質下降
5. **A4/A5/D2 事件**: 嚴格遵循 3GPP 標準實現，確保學術研究可信度

---  
以上為完整的 LEO 衛星換手仰角門檻標準規範，包含 3GPP 事件標準實現，提供各層級門檻、環境調整與系統實施細節，供程式開發與部署參考。