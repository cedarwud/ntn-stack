# 📊 動態鏈路預算計算器 (緊急開發)

## 🚨 緊急性說明

**優先級**: ⭐⭐⭐⭐⭐ (Critical)  
**問題**: 缺少實時路徑損耗和大氣衰減模型  
**影響**: RSRP 計算不準確，A4/A5 事件觸發失效  
**預估開發時間**: 2 週  

---

## 📊 問題分析

### **當前 RSRP 計算缺陷**
```python
# ❌ 當前簡化實現
def _calculate_rsrp(self, satellite):
    base_rsrp = -100.0  # 固定值
    elevation_factor = satellite['elevation_deg'] / 90.0
    return base_rsrp + 20 * math.log10(elevation_factor)
```

### **缺失的關鍵要素**
```
自由空間路徑損耗:    未實現 → 距離相關損耗錯誤
大氣衰減模型:        未實現 → 仰角/天氣影響被忽略
頻率相關損耗:        未實現 → Ka 頻段特性未考慮
天線增益模式:        未實現 → 指向角度影響被忽略
```

---

## 🏗️ 技術架構設計

### **動態鏈路預算計算器**

```python
class DynamicLinkBudgetCalculator:
    """
    動態鏈路預算計算器
    基於 ITU-R P.618-14 標準實現
    """
    
    def __init__(self):
        self.atmospheric_model = ITU_R_P618_14_Model()
        self.antenna_model = AntennaPatternModel()
        self.weather_model = WeatherCompensationModel()
        
        # 基本系統參數
        self.satellite_eirp_dbm = 43.0        # 衛星 EIRP
        self.ue_antenna_gain_db = 25.0        # UE 天線增益
        self.system_noise_temp_k = 290.0      # 系統雜訊溫度
        self.boltzmann_constant = -228.6     # dBW/K/Hz
        
    def calculate_link_budget(self, satellite_data, ue_position, timestamp, weather_data=None):
        """
        計算完整的鏈路預算
        """
        # 基本參數提取
        distance_km = satellite_data['range_km']
        elevation_deg = satellite_data['elevation_deg']
        frequency_ghz = satellite_data.get('frequency_ghz', 28.0)
        
        # 1. 自由空間路徑損耗
        fspl_db = self._calculate_free_space_path_loss(distance_km, frequency_ghz)
        
        # 2. 大氣衰減 (ITU-R P.618-14)
        atmospheric_loss_db = self.atmospheric_model.calculate_atmospheric_loss(
            elevation_deg, frequency_ghz, weather_data)
        
        # 3. 天線增益 (考慮指向角度)
        antenna_gain_db = self.antenna_model.calculate_antenna_gain(
            satellite_data, ue_position)
        
        # 4. 極化損耗
        polarization_loss_db = self._calculate_polarization_loss(satellite_data)
        
        # 5. 其他損耗 (電纜、連接器等)
        implementation_loss_db = 2.0
        
        # 6. 接收信號功率計算
        received_power_dbm = (
            self.satellite_eirp_dbm +
            antenna_gain_db -
            fspl_db -
            atmospheric_loss_db -
            polarization_loss_db -
            implementation_loss_db
        )
        
        # 7. 信號品質指標
        noise_power_dbm = self._calculate_noise_power(frequency_ghz)
        snr_db = received_power_dbm - noise_power_dbm
        
        return {
            'received_power_dbm': received_power_dbm,
            'fspl_db': fspl_db,
            'atmospheric_loss_db': atmospheric_loss_db,
            'antenna_gain_db': antenna_gain_db,
            'polarization_loss_db': polarization_loss_db,
            'implementation_loss_db': implementation_loss_db,
            'snr_db': snr_db,
            'link_margin_db': snr_db - 10.0,  # 假設需要 10dB SNR
            'timestamp': timestamp,
            'calculation_method': 'ITU_R_P618_14'
        }
```

### **自由空間路徑損耗模型**
```python
def _calculate_free_space_path_loss(self, distance_km, frequency_ghz):
    """
    計算自由空間路徑損耗
    FSPL = 32.45 + 20*log10(d) + 20*log10(f)
    """
    if distance_km <= 0 or frequency_ghz <= 0:
        raise ValueError("距離和頻率必須為正值")
    
    fspl_db = 32.45 + 20 * math.log10(distance_km) + 20 * math.log10(frequency_ghz)
    
    return fspl_db

def _calculate_noise_power(self, frequency_ghz):
    """
    計算雜訊功率
    P_noise = k * T * B (dBm)
    """
    bandwidth_hz = 10e6  # 10 MHz 頻寬
    
    noise_power_dbm = (
        self.boltzmann_constant +
        10 * math.log10(self.system_noise_temp_k) +
        10 * math.log10(bandwidth_hz)
    )
    
    return noise_power_dbm
```

### **ITU-R P.618-14 大氣衰減模型**
```python
class ITU_R_P618_14_Model:
    """
    ITU-R P.618-14 大氣衰減模型
    包含雨衰、氣體吸收、雲衰等
    """
    
    def __init__(self):
        # ITU-R P.618-14 參數
        self.rain_rate_exceeded_001_percent = 42.0  # mm/h (台灣)
        self.water_vapor_density = 7.5  # g/m³
        self.oxygen_partial_pressure = 0.2095  # 21%
        
    def calculate_atmospheric_loss(self, elevation_deg, frequency_ghz, weather_data=None):
        """
        計算總大氣衰減
        """
        # 1. 氣體吸收衰減
        gas_absorption_db = self._calculate_gas_absorption(
            elevation_deg, frequency_ghz)
        
        # 2. 雨衰衰減
        rain_attenuation_db = self._calculate_rain_attenuation(
            elevation_deg, frequency_ghz, weather_data)
        
        # 3. 雲和霧衰減
        cloud_attenuation_db = self._calculate_cloud_attenuation(
            elevation_deg, frequency_ghz, weather_data)
        
        # 4. 閃爍衰減
        scintillation_db = self._calculate_scintillation(
            elevation_deg, frequency_ghz)
        
        total_attenuation = (
            gas_absorption_db +
            rain_attenuation_db +
            cloud_attenuation_db +
            scintillation_db
        )
        
        return total_attenuation
    
    def _calculate_gas_absorption(self, elevation_deg, frequency_ghz):
        """
        計算氣體吸收衰減 (ITU-R P.676-12)
        """
        # 簡化的氣體吸收模型
        # 氧氣吸收 (O2)
        oxygen_absorption = self._oxygen_absorption_coefficient(frequency_ghz)
        
        # 水蒸氣吸收 (H2O)
        water_vapor_absorption = self._water_vapor_absorption_coefficient(frequency_ghz)
        
        # 路徑長度修正 (基於仰角)
        elevation_rad = math.radians(elevation_deg)
        if elevation_deg > 10.0:
            path_length_factor = 1.0 / math.sin(elevation_rad)
        else:
            # 低仰角修正
            path_length_factor = 1.0 / (math.sin(elevation_rad) + 0.15 * (elevation_deg + 3.885)**(-1.1))
        
        total_absorption = (oxygen_absorption + water_vapor_absorption) * path_length_factor
        
        return min(total_absorption, 30.0)  # 最大 30dB 限制
    
    def _oxygen_absorption_coefficient(self, frequency_ghz):
        """
        氧氣吸收係數 (dB/km)
        """
        # ITU-R P.676-12 簡化模型
        if frequency_ghz < 54:
            return 0.0067 * frequency_ghz**2
        elif frequency_ghz < 60:
            # 60GHz 氧氣吸收峰附近
            return 0.5 + 0.1 * (frequency_ghz - 54)
        else:
            return 0.5 * math.exp(-(frequency_ghz - 60)/5)
    
    def _water_vapor_absorption_coefficient(self, frequency_ghz):
        """
        水蒸氣吸收係數 (dB/km)
        """
        # ITU-R P.676-12 水蒸氣吸收線
        if frequency_ghz < 22:
            return 0.001 * self.water_vapor_density * frequency_ghz**2
        elif frequency_ghz < 25:
            # 22.235 GHz 水蒸氣吸收線
            return 0.05 * self.water_vapor_density * (frequency_ghz - 22)**2
        else:
            return 0.01 * self.water_vapor_density * frequency_ghz
    
    def _calculate_rain_attenuation(self, elevation_deg, frequency_ghz, weather_data):
        """
        計算雨衰衰減 (ITU-R P.618-14)
        """
        # 獲取雨量資料
        if weather_data and 'rain_rate_mm_per_h' in weather_data:
            rain_rate = weather_data['rain_rate_mm_per_h']
        else:
            # 使用統計值：0.01% 時間超過的雨量
            rain_rate = self.rain_rate_exceeded_001_percent
        
        if rain_rate <= 0:
            return 0.0
        
        # ITU-R P.838-3 雨衰係數
        k, alpha = self._get_rain_attenuation_coefficients(frequency_ghz)
        
        # 特定雨衰 (dB/km)
        specific_attenuation = k * (rain_rate ** alpha)
        
        # 有效路徑長度
        effective_path_length = self._calculate_effective_path_length(
            elevation_deg, rain_rate)
        
        rain_attenuation = specific_attenuation * effective_path_length
        
        return rain_attenuation
    
    def _get_rain_attenuation_coefficients(self, frequency_ghz):
        """
        獲取雨衰係數 k 和 α (ITU-R P.838-3)
        """
        # 簡化的係數表 (垂直極化)
        if frequency_ghz <= 10:
            k = 0.0001 * frequency_ghz**2
            alpha = 1.0
        elif frequency_ghz <= 20:
            k = 0.001 * frequency_ghz**1.5
            alpha = 1.1
        elif frequency_ghz <= 30:
            k = 0.01 * frequency_ghz
            alpha = 1.2
        else:
            k = 0.1
            alpha = 1.3
        
        return k, alpha
    
    def _calculate_effective_path_length(self, elevation_deg, rain_rate):
        """
        計算有效雨區路徑長度
        """
        # 雨高度 (km) - 台灣地區典型值
        rain_height_km = 4.0
        
        # 地面高度 (km)
        ground_height_km = 0.1
        
        # 幾何路徑長度
        elevation_rad = math.radians(elevation_deg)
        if elevation_deg > 5:
            geometric_path_km = (rain_height_km - ground_height_km) / math.sin(elevation_rad)
        else:
            # 低仰角修正
            geometric_path_km = 2 * (rain_height_km - ground_height_km) / math.sqrt(
                (math.sin(elevation_rad))**2 + 2.35e-4) + math.sin(elevation_rad)
        
        # 路徑縮減因子
        reduction_factor = 1.0 / (1.0 + geometric_path_km / 35.0)
        
        return geometric_path_km * reduction_factor
```

### **天線增益模型**
```python
class AntennaPatternModel:
    """
    天線增益模型
    考慮天線指向角度的影響
    """
    
    def __init__(self):
        self.ue_max_gain_db = 25.0
        self.satellite_max_gain_db = 50.0
        
    def calculate_antenna_gain(self, satellite_data, ue_position):
        """
        計算總天線增益
        """
        # UE 天線增益 (考慮指向角度)
        ue_gain = self._calculate_ue_antenna_gain(satellite_data, ue_position)
        
        # 衛星天線增益 (簡化為固定值)
        satellite_gain = self.satellite_max_gain_db
        
        total_gain = ue_gain + satellite_gain
        
        return total_gain
    
    def _calculate_ue_antenna_gain(self, satellite_data, ue_position):
        """
        計算 UE 天線增益
        """
        elevation_deg = satellite_data['elevation_deg']
        azimuth_deg = satellite_data.get('azimuth_deg', 0)
        
        # 仰角損失 (天線主波束偏離)
        elevation_loss = self._calculate_elevation_loss(elevation_deg)
        
        # 最大增益減去指向損失
        ue_gain = self.ue_max_gain_db - elevation_loss
        
        return max(ue_gain, 0.0)  # 最小 0dB
    
    def _calculate_elevation_loss(self, elevation_deg):
        """
        計算仰角指向損失
        """
        # 假設最佳指向角度為 45°
        optimal_elevation = 45.0
        elevation_error = abs(elevation_deg - optimal_elevation)
        
        # 簡化的指向損失模型
        if elevation_error <= 10:
            return 0.0
        elif elevation_error <= 30:
            return 0.1 * (elevation_error - 10)
        else:
            return 2.0 + 0.2 * (elevation_error - 30)
```

---

## 🔧 系統整合

### **增強的 RSRP 計算**
```python
def calculate_enhanced_rsrp(self, satellite_data, ue_position, timestamp, weather_data=None):
    """
    基於動態鏈路預算的增強 RSRP 計算
    """
    # 計算完整鏈路預算
    link_budget = self.link_calculator.calculate_link_budget(
        satellite_data, ue_position, timestamp, weather_data)
    
    # RSRP = 接收功率 (已包含所有損耗和增益)
    base_rsrp = link_budget['received_power_dbm']
    
    # 添加快衰落和陰影衰落
    fast_fading = random.gauss(0, 2.0)  # 快衰落 σ=2dB
    shadow_fading = random.gauss(0, 4.0)  # 陰影衰落 σ=4dB
    
    final_rsrp = base_rsrp + fast_fading + shadow_fading
    
    return {
        'rsrp_dbm': final_rsrp,
        'base_rsrp_dbm': base_rsrp,
        'fast_fading_db': fast_fading,
        'shadow_fading_db': shadow_fading,
        'link_budget': link_budget,
        'calculation_method': 'enhanced_link_budget'
    }
```

### **環境自適應調整**
```python
def apply_environment_adjustments(self, rsrp_info, environment_type):
    """
    根據環境類型調整 RSRP
    """
    # 環境調整因子
    environment_factors = {
        'ideal': 1.0,      # 海洋、平原
        'standard': 1.1,   # 一般陸地
        'urban': 1.3,      # 市區建築
        'complex': 1.6,    # 山區、高樓
        'severe': 2.0      # 惡劣天氣
    }
    
    factor = environment_factors.get(environment_type, 1.1)
    
    # 調整大氣衰減
    adjusted_atmospheric_loss = rsrp_info['link_budget']['atmospheric_loss_db'] * factor
    
    # 重新計算 RSRP
    loss_increase = adjusted_atmospheric_loss - rsrp_info['link_budget']['atmospheric_loss_db']
    adjusted_rsrp = rsrp_info['rsrp_dbm'] - loss_increase
    
    return {
        **rsrp_info,
        'adjusted_rsrp_dbm': adjusted_rsrp,
        'environment_factor': factor,
        'environment_loss_increase_db': loss_increase,
        'environment_type': environment_type
    }
```

---

## 📊 性能目標

### **計算精度目標**
```
RSRP 計算誤差:      ±1dB (vs 當前 ±5dB)
大氣衰減精度:       符合 ITU-R P.618-14 標準
路徑損耗精度:       <0.5dB 誤差
環境補償精度:       動態調整 ±20%
```

### **性能指標**
```
計算速度:          <5ms 每次計算
記憶體使用:        <50MB 額外使用
CPU 負載:          <5% 增加
準確度提升:        5x 改善
```

---

## 🧪 測試驗證

### **精度驗證**
```python
def test_free_space_path_loss():
    """測試自由空間路徑損耗計算"""
    calculator = DynamicLinkBudgetCalculator()
    
    # 測試案例：800km, 28GHz
    fspl = calculator._calculate_free_space_path_loss(800, 28)
    
    # 理論值：32.45 + 20*log10(800) + 20*log10(28) ≈ 180.4 dB
    expected = 32.45 + 20 * math.log10(800) + 20 * math.log10(28)
    assert abs(fspl - expected) < 0.1

def test_atmospheric_loss_calculation():
    """測試大氣衰減計算"""
    model = ITU_R_P618_14_Model()
    
    # 測試不同仰角
    for elevation in [10, 30, 60, 90]:
        loss = model.calculate_atmospheric_loss(elevation, 28.0)
        
        # 驗證合理範圍
        assert 0 <= loss <= 30  # dB
        
        # 驗證仰角趨勢 (仰角越高，衰減越小)
        if elevation > 10:
            loss_low = model.calculate_atmospheric_loss(10, 28.0)
            assert loss <= loss_low

def test_enhanced_rsrp_calculation():
    """測試增強 RSRP 計算"""
    satellite_data = {
        'range_km': 800,
        'elevation_deg': 45,
        'frequency_ghz': 28.0,
        'satellite_id': 'sat1'
    }
    
    ue_position = (24.9696, 121.2654, 0.1)
    
    rsrp_info = calculate_enhanced_rsrp(
        satellite_data, ue_position, time.time())
    
    # 驗證結果結構
    assert 'rsrp_dbm' in rsrp_info
    assert 'link_budget' in rsrp_info
    assert 'calculation_method' in rsrp_info
    
    # 驗證 RSRP 範圍合理
    assert -150 <= rsrp_info['rsrp_dbm'] <= -50
```

### **基準測試**
```python
def benchmark_link_budget_calculation():
    """鏈路預算計算性能基準"""
    calculator = DynamicLinkBudgetCalculator()
    
    satellite_data = {
        'range_km': 800,
        'elevation_deg': 45,
        'frequency_ghz': 28.0
    }
    
    ue_position = (24.9696, 121.2654, 0.1)
    
    # 性能測試
    start_time = time.time()
    for _ in range(1000):
        calculator.calculate_link_budget(
            satellite_data, ue_position, time.time())
    end_time = time.time()
    
    avg_time_ms = (end_time - start_time) * 1000 / 1000
    print(f"平均計算時間: {avg_time_ms:.2f} ms")
    
    # 驗證性能目標
    assert avg_time_ms < 5.0
```

---

## 📅 開發計劃

### **Week 1: 核心實現**
- [ ] 動態鏈路預算計算器框架
- [ ] ITU-R P.618-14 大氣模型實現
- [ ] 天線增益模型
- [ ] 基礎整合測試

### **Week 2: 優化與整合**
- [ ] 環境自適應調整
- [ ] 性能優化
- [ ] 與現有 RSRP 計算整合
- [ ] 完整驗證測試

---

## ✅ 成功標準

### **精度標準**
- [ ] RSRP 計算誤差 <1dB
- [ ] ITU-R P.618-14 標準合規
- [ ] 大氣衰減模型精度驗證
- [ ] 環境補償效果驗證

### **性能標準**
- [ ] 計算速度 <5ms
- [ ] 記憶體增量 <50MB
- [ ] CPU 負載增量 <5%
- [ ] A4/A5 事件準確率 >95%

---

*Dynamic Link Budget Calculator - Urgent Development - Generated: 2025-08-01*