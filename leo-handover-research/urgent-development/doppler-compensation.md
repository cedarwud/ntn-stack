# 📡 多普勒頻移補償系統 (緊急開發)

## 🚨 緊急性說明

**優先級**: ⭐⭐⭐⭐⭐ (Critical)  
**問題**: 當前系統缺少 LEO 衛星 ±50-100kHz 多普勒補償  
**影響**: 嚴重影響 A4/A5 RSRP 測量精確度，導致事件觸發失效  
**預估開發時間**: 2 週  

---

## 📊 問題分析

### **LEO 衛星多普勒特性**
```
多普勒偏移範圍:    ±50-100kHz (Ku/Ka 頻段)
最大變化率:        1kHz/s
軌道速度:          ~7.5 km/s (550km 高度)
地面速度投影:      最高 ±5 km/s (天頂角依賴)
```

### **對 RSRP 測量的影響**
```
頻率偏移 → 接收機失鎖
信號功率 → 降低 5-15 dB
測量精度 → A4/A5 門檻判斷錯誤
事件觸發 → 誤觸發率 >20%
```

---

## 🏗️ 技術架構設計

### **階層式多普勒補償架構**

```python
class DopplerCompensationSystem:
    """
    階層式多普勒補償系統
    兩階段補償：粗補償 + 精補償
    """
    
    def __init__(self):
        self.coarse_compensator = CoarseDopplerCompensator()
        self.fine_compensator = FineDopplerCompensator()
        self.frequency_tracker = RealTimeFrequencyTracker()
        
    def compensate_doppler(self, satellite_data, ue_position, timestamp):
        """
        執行完整的多普勒補償
        """
        # 階段1: 粗補償 (基於星曆)
        coarse_offset = self.coarse_compensator.calculate_doppler_offset(
            satellite_data, ue_position, timestamp)
        
        # 階段2: 精補償 (基於導頻)
        fine_offset = self.fine_compensator.estimate_residual_offset(
            satellite_data, coarse_offset)
        
        # 總補償量
        total_compensation = coarse_offset + fine_offset
        
        return {
            'total_offset_hz': total_compensation,
            'coarse_offset_hz': coarse_offset,
            'fine_offset_hz': fine_offset,
            'compensation_accuracy': self._estimate_accuracy(satellite_data)
        }
```

### **粗補償實現**
```python
class CoarseDopplerCompensator:
    """
    粗補償階段：基於衛星軌道計算理論多普勒
    補償 80-95% 的頻移，響應時間毫秒級
    """
    
    def calculate_doppler_offset(self, satellite_data, ue_position, timestamp):
        """
        計算理論多普勒頻移
        """
        # 獲取衛星速度向量
        velocity_vector = self._get_satellite_velocity(satellite_data, timestamp)
        
        # 計算視線方向
        los_vector = self._calculate_line_of_sight(satellite_data, ue_position)
        
        # 徑向速度計算
        radial_velocity = np.dot(velocity_vector, los_vector)
        
        # 多普勒頻移 (Hz)
        carrier_frequency = satellite_data.get('carrier_freq_hz', 28e9)
        doppler_shift = (radial_velocity / self.LIGHT_SPEED) * carrier_frequency
        
        return doppler_shift
    
    def _get_satellite_velocity(self, satellite_data, timestamp):
        """
        從 SGP4 軌道模型獲取速度向量
        """
        # 使用 SGP4 計算衛星速度
        satellite_id = satellite_data['satellite_id']
        ephemeris = self.sib19_processor.get_ephemeris(satellite_id)
        
        position, velocity = sgp4_propagate(ephemeris, timestamp)
        return velocity  # km/s
    
    def _calculate_line_of_sight(self, satellite_data, ue_position):
        """
        計算 UE 到衛星的視線方向單位向量
        """
        sat_position = satellite_data['position']  # (lat, lon, alt)
        
        # 轉換為 ECEF 座標
        sat_ecef = self._lla_to_ecef(sat_position)
        ue_ecef = self._lla_to_ecef(ue_position)
        
        # 視線向量
        los_vector = np.array(sat_ecef) - np.array(ue_ecef)
        return los_vector / np.linalg.norm(los_vector)
```

### **精補償實現**
```python
class FineDopplerCompensator:
    """
    精補償階段：基於導頻信號估計殘餘頻偏
    補償剩餘 5-20% 的頻移，適應性調整
    """
    
    def __init__(self):
        self.pilot_tracker = PilotSignalTracker()
        self.phase_detector = PhaseFrequencyDetector()
        
    def estimate_residual_offset(self, satellite_data, coarse_offset):
        """
        基於導頻信號估計殘餘頻偏
        """
        # 模擬導頻信號檢測 (實際需要 SDR 硬體)
        pilot_signal = self._extract_pilot_signal(satellite_data)
        
        # 頻率誤差檢測
        frequency_error = self.phase_detector.detect_frequency_error(
            pilot_signal, coarse_offset)
        
        # 迴路濾波
        filtered_error = self._loop_filter(frequency_error)
        
        return filtered_error
    
    def _extract_pilot_signal(self, satellite_data):
        """
        從接收信號中提取導頻信號
        """
        # 模擬實現：基於 RSRP 和信號品質估計
        rsrp = satellite_data.get('rsrp_dbm', -100)
        snr = self._estimate_snr(rsrp)
        
        # 導頻信號品質指標
        pilot_quality = {
            'signal_strength': rsrp,
            'snr_db': snr,
            'phase_noise': self._estimate_phase_noise(snr),
            'pilot_correlation': max(0.1, min(1.0, (rsrp + 120) / 40))
        }
        
        return pilot_quality
    
    def _loop_filter(self, frequency_error):
        """
        迴路濾波器：平滑頻率估計
        """
        # 二階迴路濾波器
        alpha = 0.1  # 迴路頻寬
        beta = alpha ** 2 / 4
        
        # 狀態更新
        self.phase_error += frequency_error
        filtered_error = alpha * frequency_error + beta * self.phase_error
        
        return filtered_error
```

### **實時頻率追蹤**
```python
class RealTimeFrequencyTracker:
    """
    實時頻率追蹤器
    持續追蹤和補償頻率變化
    """
    
    def __init__(self):
        self.tracking_window_ms = 100  # 100ms 追蹤窗口
        self.frequency_history = []
        self.prediction_model = FrequencyPredictionModel()
        
    def track_frequency_change(self, satellite_data, current_offset):
        """
        追蹤頻率變化並預測
        """
        timestamp = time.time()
        
        # 記錄歷史
        self.frequency_history.append({
            'timestamp': timestamp,
            'frequency_offset': current_offset,
            'satellite_id': satellite_data['satellite_id']
        })
        
        # 保持窗口大小
        if len(self.frequency_history) > 50:
            self.frequency_history.pop(0)
        
        # 預測未來頻率
        predicted_offset = self.prediction_model.predict_next_offset(
            self.frequency_history)
        
        return {
            'current_offset': current_offset,
            'predicted_offset': predicted_offset,
            'change_rate_hz_per_sec': self._calculate_change_rate(),
            'tracking_confidence': self._estimate_tracking_confidence()
        }
    
    def _calculate_change_rate(self):
        """
        計算頻率變化率 (Hz/s)
        """
        if len(self.frequency_history) < 2:
            return 0.0
        
        recent_data = self.frequency_history[-10:]  # 最近 1 秒數據
        
        if len(recent_data) < 2:
            return 0.0
        
        # 線性回歸計算變化率
        times = [d['timestamp'] for d in recent_data]
        freqs = [d['frequency_offset'] for d in recent_data]
        
        # 簡化的線性回歸
        n = len(times)
        sum_t = sum(times)
        sum_f = sum(freqs)
        sum_tf = sum(t * f for t, f in zip(times, freqs))
        sum_t2 = sum(t * t for t in times)
        
        # 斜率 = 變化率
        denominator = n * sum_t2 - sum_t * sum_t
        if abs(denominator) < 1e-10:
            return 0.0
        
        slope = (n * sum_tf - sum_t * sum_f) / denominator
        return slope
```

---

## 🔧 系統整合

### **與 RSRP 計算整合**
```python
def calculate_doppler_corrected_rsrp(self, satellite_data, ue_position, timestamp):
    """
    計算多普勒校正後的 RSRP
    """
    # 原始 RSRP 計算
    base_rsrp = self._calculate_base_rsrp(satellite_data)
    
    # 多普勒補償
    doppler_info = self.doppler_system.compensate_doppler(
        satellite_data, ue_position, timestamp)
    
    # 頻率偏移對 RSRP 的影響
    frequency_loss = self._calculate_frequency_loss(
        doppler_info['total_offset_hz'])
    
    # 補償精度對信號品質的影響
    compensation_gain = self._calculate_compensation_gain(
        doppler_info['compensation_accuracy'])
    
    # 校正後的 RSRP
    corrected_rsrp = base_rsrp - frequency_loss + compensation_gain
    
    return {
        'corrected_rsrp_dbm': corrected_rsrp,
        'base_rsrp_dbm': base_rsrp,
        'frequency_loss_db': frequency_loss,
        'compensation_gain_db': compensation_gain,
        'doppler_info': doppler_info
    }

def _calculate_frequency_loss(self, frequency_offset_hz):
    """
    計算頻率偏移造成的信號損失
    """
    # 接收機頻寬：假設 10 MHz
    receiver_bandwidth = 10e6
    
    # 頻率偏移比例
    offset_ratio = abs(frequency_offset_hz) / receiver_bandwidth
    
    # 信號損失模型（簡化）
    if offset_ratio < 0.01:  # <1% 偏移
        return 0.0
    elif offset_ratio < 0.05:  # <5% 偏移  
        return 3.0 * offset_ratio
    else:  # >5% 偏移
        return min(15.0, 3.0 + 8.0 * (offset_ratio - 0.05))

def _calculate_compensation_gain(self, accuracy):
    """
    計算補償精度帶來的增益
    """
    # 補償精度 0-1，對應增益 0-8dB
    return 8.0 * accuracy
```

### **與事件檢測整合**
```python
def detect_doppler_enhanced_a4_events(self, timeline_data):
    """
    多普勒增強的 A4 事件檢測
    """
    a4_events = []
    
    for timestamp, satellites in timeline_data.items():
        for satellite in satellites:
            # 計算多普勒校正 RSRP
            corrected_rsrp_info = self.calculate_doppler_corrected_rsrp(
                satellite, self.ue_position, timestamp)
            
            corrected_rsrp = corrected_rsrp_info['corrected_rsrp_dbm']
            
            # A4 觸發條件（使用校正值）
            if corrected_rsrp - self.hysteresis > self.a4_threshold:
                a4_event = {
                    'timestamp': timestamp,
                    'event_type': 'A4',
                    'satellite': satellite,
                    'rsrp_info': corrected_rsrp_info,
                    'doppler_enhanced': True,
                    'compensation_quality': 'high' if corrected_rsrp_info['doppler_info']['compensation_accuracy'] > 0.8 else 'medium'
                }
                
                a4_events.append(a4_event)
    
    return a4_events
```

---

## 📊 性能目標

### **補償精度目標**
```
粗補償精度:    80-95% (基於軌道計算)
精補償精度:    >95% (基於導頻追蹤)
總體精度:      >98% (殘餘偏移 <100Hz)
響應時間:      <10ms (實時補償)
```

### **RSRP 測量改善**
```
修復前:        RSRP 誤差 ±5dB
修復後:        RSRP 誤差 ±1dB
精度提升:      5x 改善
事件準確率:    60% → 95% (+35%)
```

---

## 🧪 測試驗證

### **單元測試**
```python
def test_coarse_doppler_compensation():
    """測試粗補償精度"""
    satellite_data = {
        'satellite_id': 'sat1',
        'position': (25.0, 122.0, 550),
        'carrier_freq_hz': 28e9
    }
    ue_position = (24.9696, 121.2654, 0.1)
    
    compensator = CoarseDopplerCompensator()
    offset = compensator.calculate_doppler_offset(
        satellite_data, ue_position, time.time())
    
    # 驗證偏移量在合理範圍內
    assert -100000 <= offset <= 100000  # ±100kHz

def test_frequency_tracking():
    """測試頻率追蹤性能"""
    tracker = RealTimeFrequencyTracker()
    
    # 模擬頻率變化
    for i in range(100):
        offset = 50000 + 1000 * i  # 1kHz/s 變化
        result = tracker.track_frequency_change(
            {'satellite_id': 'sat1'}, offset)
        
        if i > 10:  # 有足夠歷史數據後
            assert abs(result['change_rate_hz_per_sec'] - 1000) < 100
```

### **整合測試**
```python
def test_doppler_enhanced_rsrp():
    """測試多普勒增強 RSRP 計算"""
    satellite_data = {
        'elevation_deg': 45.0,
        'range_km': 800,
        'satellite_id': 'sat1'
    }
    
    # 無多普勒補償
    base_rsrp = calculate_base_rsrp(satellite_data)
    
    # 多普勒補償
    corrected_rsrp_info = calculate_doppler_corrected_rsrp(
        satellite_data, (24.9696, 121.2654, 0.1), time.time())
    
    # 驗證補償效果
    assert corrected_rsrp_info['corrected_rsrp_dbm'] > base_rsrp
    assert 'doppler_info' in corrected_rsrp_info
```

---

## 📅 開發計劃

### **Week 1: 核心實現**
- [ ] 粗補償器實現
- [ ] SGP4 速度計算整合
- [ ] 基礎測試案例
- [ ] 與 RSRP 計算整合

### **Week 2: 精補償與優化**
- [ ] 精補償器實現  
- [ ] 實時追蹤器
- [ ] 性能優化
- [ ] 完整整合測試

---

## ✅ 成功標準

### **技術指標**
- [ ] 多普勒補償精度 >98%
- [ ] RSRP 測量誤差 <1dB
- [ ] 系統響應時間 <10ms
- [ ] A4/A5 事件準確率 >95%

### **整合指標**
- [ ] 與現有系統無縫整合
- [ ] Docker 容器支援
- [ ] 健康檢查監控
- [ ] 3GPP 標準合規

---

*Doppler Compensation System - Urgent Development - Generated: 2025-08-01*