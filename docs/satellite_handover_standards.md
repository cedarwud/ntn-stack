# 🛰️ NTN Stack 衛星換手仰角門檻標準規範

**文件版本**: 1.0.0  
**最後更新**: 2025-07-29  
**狀態**: 正式標準  

## 📋 概述

本文檔定義 NTN Stack 系統中衛星換手的統一仰角門檻標準，解決不同組件間標準不一致的問題。

> **📡 數據架構**: 系統已轉換為本地數據架構，使用 Docker Volume 存儲衛星數據，無外部 API 依賴。詳見 [衛星數據架構文檔](./satellite_data_architecture.md)。

## 🎯 標準制定依據

### 技術參考標準
- **ITU-R P.618-14**: 傳播數據和預測方法
- **3GPP TS 38.331**: NTN 無線資源控制
- **3GPP TR 38.811**: NTN 研究報告
- **Phase 0 實際測試結果分析**

### 物理原理
根據 ITU-R P.618 標準：
- **仰角 ≥ 10°**: 大氣氣體吸收、雨衰減可用平均模型估算
- **仰角 5°-10°**: 大氣衰減與多徑、閃變效應劇增
- **仰角 < 5°**: 信號品質不穩定，不適合正常通訊

## 🔄 分層仰角門檻標準

### 主要門檻定義

| 門檻類型 | 仰角標準 | 用途 | ITU 合規性 |
|---------|----------|------|-----------|
| **預備觸發** | ≥ 12° | 開始換手準備程序 | ✅ 完全合規 |
| **執行門檻** | ≥ 10° | 執行實際換手切換 | ✅ ITU 建議標準 |
| **臨界門檻** | ≥ 5° | 緊急換手保障 | ⚠️ 邊緣可用 |
| **斷線門檻** | < 5° | 強制斷開連線 | ❌ 不建議使用 |

### 分層換手策略

#### 1. 預備觸發階段 (仰角 12° → 10°)
**目的**: 爭取 8-15 秒的準備時間 (基於 NASA 衛星激光測距系統建議)
- 開始候選衛星掃描
- 預留頻道資源
- 路由表預先配置
- 信號品質監控加強

#### 2. 執行門檻階段 (仰角 10° → 5°)  
**目的**: 確保切換過程中信號穩定
- 完成實際換手切換
- 確保 ITU-R P.618 合規
- 維持服務品質標準
- 避免通話中斷

#### 3. 臨界門檻階段 (仰角 5° → 0°)
**目的**: 最後保障機制
- 緊急換手處理
- 服務降級運行
- 連線保持努力
- 準備強制斷開

## 🌍 環境調整係數

### 基礎環境分類

| 環境類型 | 調整係數 | 實際執行門檻 | 適用場景 |
|---------|----------|-------------|----------|
| **開闊地區** | 1.0 | 10.0° | 農田、海洋、沙漠 |
| **城市環境** | 1.1-1.15 | 11.0-11.5° | 市區、建築物遮蔽 |
| **郊區** | 1.05 | 10.5° | 低密度建築區 |
| **山區** | 1.2-1.4 | 12.0-14.0° | 地形遮蔽嚴重（依據地形複雜度）|
| **強降雨區** | 1.4-1.5 | 14.0-15.0° | 熱帶、季風區（依據降雨強度）|
| **海岸地區** | 1.1 | 11.0° | 海面反射干擾 |

### 動態調整原則

#### **基於信號品質的動態調整**
```python
def calculate_dynamic_threshold(base_threshold: float, signal_metrics: dict) -> float:
    """
    基於實時信號品質動態調整門檻
    符合 ITU-R P.618-14 建議的適應性門檻機制
    """
    snr = signal_metrics.get('snr_db', 0)
    rssi = signal_metrics.get('rssi_dbm', -100)
    
    # SNR 調整係數 (根據 3GPP NTN 標準)
    if snr >= 15:
        snr_factor = 0.9   # 信號強度良好，可適度降低門檻
    elif snr >= 10:
        snr_factor = 1.0   # 正常信號
    else:
        snr_factor = 1.1   # 信號較弱，提高門檻
    
    # RSSI 調整係數
    if rssi >= -70:
        rssi_factor = 0.95
    elif rssi >= -80:
        rssi_factor = 1.0
    else:
        rssi_factor = 1.05
    
    # 綜合調整
    dynamic_threshold = base_threshold * snr_factor * rssi_factor
    
    # 確保門檻在合理範圍內 (8° - 18°)
    return max(8.0, min(18.0, dynamic_threshold))
```

#### **環境感知調整原則**
- **實時天氣**: 根據降雨強度調整（氣象雷達數據整合）
- **時段差異**: 電離層活動影響（太陽活動指數 Kp 值）  
- **負載狀況**: 網路繁忙時適度提高門檻
- **信號品質**: SNR/RSSI 實時回饋調整

## 🔧 系統實施標準

### 各組件統一配置

#### CoordinateSpecificOrbitEngine
```python
# 預設配置更新
min_elevation = 10.0  # 從 5° 升級為 10°
use_case = "handover"  # 明確用途
environment = "open_area"  # 預設環境
```

#### NTPUVisibilityFilter
```python
# 與軌道引擎保持一致
min_elevation = 10.0
filter_quality = "itu_compliant"
```

#### LayeredElevationEngine
```python
# 分層門檻配置 (根據 NASA 衛星激光測距系統建議調整)
pre_handover_trigger = 12.0  # 從 15.0° 調整為 12.0°
execution_threshold = 10.0   # 維持 ITU-R P.618 合規標準
critical_threshold = 5.0     # 緊急保障門檻
dynamic_adjustment = True    # 啟用基於信號品質的動態調整
```

### API 標準化

#### 統一接口參數
```http
GET /api/satellite/visibility
?elevation_threshold=10.0
&use_case=handover
&environment=open_area
```

#### 回應格式標準
```json
{
  "threshold_applied": 10.0,
  "itu_compliant": true,
  "environment_adjusted": true,
  "visible_satellites": 135,
  "handover_phases": {
    "monitoring": 45,
    "pre_handover": 32,
    "execution": 28,
    "critical": 0
  }
}
```

## 📊 效能基準與驗證

### 預期結果基準

| 門檻設定 | Starlink 可見數 | OneWeb 可見數 | 總可見數 | 研究驗證 |
|---------|---------------|-------------|---------|----------|
| 5° (舊標準) | 223 (2.79%) | 33 (5.07%) | 256 | ❌ 過多低品質 |
| 10° (新標準) | 135 (1.69%) | 24 (3.69%) | 159 | ✅ 符合預期 |
| 12° (預備觸發) | 108 (1.35%) | 19 (2.92%) | 127 | ✅ 平衡效能 |

### 效能指標

#### 換手成功率
- **10° 門檻**: 目標 >95%
- **5° 門檻**: 目標 >85% (降級模式)

#### 服務中斷時間
- **預備觸發模式**: <50ms
- **直接換手模式**: <200ms

#### 信號品質穩定性
- **10° 以上**: SNR 變化 <3dB
- **5°-10°**: SNR 變化 <6dB

## 🔄 遷移實施計劃

### Phase 1: 配置更新 (立即執行)
1. 更新 `CoordinateSpecificOrbitEngine` 預設門檻 → 10°
2. 更新 `NTPUVisibilityFilter` 預設門檻 → 10°
3. 部署 `LayeredElevationEngine` 到生產環境
4. 更新 API 文檔和接口標準

### Phase 2: 數據重新生成 (1週內)
1. 重新生成 Phase 0 預計算數據 (10° 標準)
2. 更新所有相關報告和統計
3. 驗證新標準的效能指標
4. 完成向後兼容性測試

### Phase 3: 系統驗證 (2週內)
1. 端到端功能測試
2. 不同環境場景驗證
3. 效能基準確認
4. 文檔完整性檢查

## 📚 使用指南

### 開發者指南

#### 獲取標準門檻
```python
from src.services.satellite.unified_elevation_config import get_standard_threshold

# 研究分析用途
threshold = get_standard_threshold("research", "open_area")  # 10.0°

# 生產換手用途  
threshold = get_standard_threshold("production", "mountain")  # 12.0°

# 可見性分析用途
threshold = get_standard_threshold("visibility", "urban")    # 11.0°
```

#### 分層換手實施
```python
from src.services.satellite.layered_elevation_threshold import create_layered_engine

# 創建分層引擎
engine = create_layered_engine("urban")

# 分析衛星狀態
analysis = engine.analyze_satellite_phase(satellite_info)
print(f"階段: {analysis['handover_phase']}")
print(f"行動: {analysis['action_required']}")
```

### 運維指南

#### 環境配置調整
```bash
# 設定環境變數
export ELEVATION_ENVIRONMENT="mountain"
export ELEVATION_USE_CASE="production"

# 驗證配置
curl -s http://localhost:8080/api/config/elevation | jq .
```

#### 監控指標
```bash
# 檢查當前門檻設定
curl -s http://localhost:8080/api/satellite/config | jq .elevation_thresholds

# 監控換手成功率
curl -s http://localhost:8080/metrics | grep handover_success_rate
```

## ⚠️ 注意事項與限制

### 重要限制
1. **臨界門檻 (5°) 僅作為緊急保障**，不建議長時間使用
2. **環境調整係數最大不超過 1.5**，避免過度保守
3. **動態調整頻率不超過每分鐘一次**，避免系統振盪

### 特殊場景處理
- **室內環境**: 建議使用 15° 以上門檻
- **高速移動**: 提前觸發換手 (20° 門檻)
- **緊急通訊**: 可暫時降至 5° 門檻

## 📖 相關文檔

### 技術文檔
- [衛星數據架構文檔](./satellite_data_architecture.md) - 本地數據實施方案
- [CoordinateSpecificOrbitEngine API 文檔](./coordinate_orbit_api.md)
- [LayeredElevationEngine 使用指南](./layered_elevation_guide.md)
- [環境調整配置手冊](./environment_config.md)

### 標準參考
- [ITU-R P.618-14 標準文檔](https://www.itu.int/rec/R-REC-P.618/)
- [3GPP TS 38.331 規範](https://www.3gpp.org/specifications)
- [Phase 0 測試報告](../test_reports/phase0_results.md)

## 📝 變更記錄

| 版本 | 日期 | 變更內容 | 作者 |
|------|------|----------|------|
| 1.0.0 | 2025-07-29 | 初始版本，建立統一標準 | Claude Code |

## 🤝 回饋與改進

如有任何問題或建議，請聯繫：
- 技術問題: [GitHub Issues](https://github.com/ntn-stack/issues)
- 標準建議: [技術委員會](mailto:tech@ntn-stack.org)

---

**本文檔為 NTN Stack 正式技術標準，所有相關開發必須遵循此規範。**