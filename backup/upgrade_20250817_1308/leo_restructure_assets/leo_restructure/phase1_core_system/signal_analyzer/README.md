# F3: 信號分析器

3GPP NTN標準換手事件檢測系統

## 核心功能
- A4事件檢測: 鄰近衛星信號優於門檻
- A5事件檢測: 服務衛星劣化且鄰近衛星良好
- D2事件檢測: LEO衛星距離優化換手
- 精確RSRP計算 (Ku頻段12GHz)

## 3GPP標準實現
### A4事件 (鄰居信號優於門檻)
- 門檻: -100 dBm
- 優先級: MEDIUM
- 觸發條件: neighbor_rsrp > threshold + hysteresis

### A5事件 (服務劣化+鄰居良好)
- 服務門檻: -110 dBm  
- 鄰居門檻: -100 dBm
- 優先級: HIGH
- 雙重條件檢查

### D2事件 (距離優化)
- 服務距離門檻: 5000 km
- 鄰居距離門檻: 3000 km
- 優先級: LOW

## 實現狀態
✅ a4_a5_d2_event_processor.py - 事件檢測核心
🔄 精確RSRP計算
🔄 信心分數評估

## 輸出格式
```python
HandoverEvent: 換手事件記錄
SatelliteSignalData: 衛星信號數據
```