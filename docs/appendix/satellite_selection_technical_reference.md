# 🎯 衛星選擇技術參考

**版本**: 1.0.0  
**建立日期**: 2025-08-09  
**目的**: 保存核心的衛星選擇技術設計和評分機制  

## 🧮 衛星選擇評分機制

### Starlink 專用評分系統 (總分 100 分)
```python
starlink_scoring_system = {
    "軌道傾角適用性": {
        "權重": 30,
        "計算": "abs(inclination - 53.0) 的反向評分",
        "優化目標": "53° 傾角最佳"
    },
    "高度適用性": {
        "權重": 25,
        "計算": "abs(altitude - 550) 的反向評分",
        "優化目標": "550km 最佳高度"
    },
    "相位分散度": {
        "權重": 20,
        "計算": "相鄰衛星相位差距評分",
        "優化目標": "避免同步出現/消失"
    },
    "換手頻率": {
        "權重": 15,
        "計算": "軌道週期和通過頻率",
        "優化目標": "適中的切換頻率"
    },
    "信號穩定性": {
        "權重": 10,
        "計算": "軌道偏心率和穩定性",
        "優化目標": "軌道穩定性評估"
    }
}
```

### OneWeb 專用評分系統 (總分 100 分)
```python
oneweb_scoring_system = {
    "軌道傾角適用性": {
        "權重": 25,
        "計算": "abs(inclination - 87.4) 的反向評分",
        "優化目標": "87.4° 傾角優化"
    },
    "高度適用性": {
        "權重": 25,
        "計算": "abs(altitude - 1200) 的反向評分",
        "優化目標": "1200km 最佳"
    },
    "極地覆蓋": {
        "權重": 20,
        "計算": "高傾角覆蓋能力",
        "優化目標": "高傾角優勢"
    },
    "軌道形狀": {
        "權重": 20,
        "計算": "偏心率接近圓形評分",
        "優化目標": "近圓軌道"
    },
    "相位分散": {
        "權重": 10,
        "計算": "相位分佈均勻度",
        "優化目標": "避免同步出現"
    }
}
```

## 📊 動態篩選策略

### 篩選模式決策邏輯
```python
def select_filtering_strategy(estimated_visible, max_display):
    if estimated_visible < max_display * 0.5:
        return "relaxed_criteria"     # 放寬條件，確保最少數量
    elif estimated_visible <= max_display * 3:
        return "standard_filtering"   # 平衡品質和數量
    else:
        return "strict_filtering"     # 選擇最優衛星
```

### 各篩選模式特性
```yaml
filtering_strategies:
  relaxed_criteria:
    condition: "visible < 8"
    purpose: "確保最少換手候選數量"
    score_threshold: 60
    
  standard_filtering:
    condition: "8 ≤ visible ≤ 45"
    purpose: "平衡品質和數量"
    score_threshold: 75
    
  strict_filtering:
    condition: "visible > 45"
    purpose: "選擇最優衛星"
    score_threshold: 85
```

## 🔄 相位分散算法

### 相位分散計算
```python
def calculate_phase_dispersion_score(satellites):
    """
    計算衛星相位分散度評分
    避免衛星同時出現/消失的問題
    """
    phase_differences = []
    
    for i in range(len(satellites)):
        for j in range(i+1, len(satellites)):
            phase_diff = abs(satellites[i].mean_anomaly - satellites[j].mean_anomaly)
            # 處理360度環繞
            if phase_diff > 180:
                phase_diff = 360 - phase_diff
            phase_differences.append(phase_diff)
    
    # 最小相位差距越大越好
    min_phase_diff = min(phase_differences)
    
    if min_phase_diff >= 15:  # 理想間隔
        return 100
    elif min_phase_diff >= 10:  # 可接受
        return 70
    else:  # 需要改善
        return 30
```

## 🌍 地理相關性篩選

### NTPU 觀測點優化
```python
ntpu_coordinates = {
    "latitude": 24.9441667,
    "longitude": 121.3713889,
    "altitude": 50  # 米
}

def geographic_relevance_score(satellite, observer):
    """
    計算衛星對特定觀測點的地理相關性
    """
    # 軌道傾角匹配 - 傾角需要大於觀測點緯度
    inclination_match = satellite.inclination > observer.latitude
    
    # 升交點經度匹配 - 特定範圍內
    longitude_range = abs(satellite.raan - observer.longitude)
    if longitude_range > 180:
        longitude_range = 360 - longitude_range
        
    longitude_relevance = max(0, 100 - longitude_range * 2)
    
    return {
        "inclination_bonus": 20 if inclination_match else -10,
        "longitude_score": longitude_relevance,
        "total_geographic_score": longitude_relevance + (20 if inclination_match else -10)
    }
```

## 🎯 換手適用性評分

### 換手場景分析
```python
def handover_suitability_analysis(satellites, time_window_minutes=120):
    """
    分析衛星組合的換手適用性
    基於NTPU單一觀測點的時間序列換手
    """
    handover_events = []
    
    for timestamp in time_range(time_window_minutes, interval=30):  # 30秒間隔
        visible_sats = [sat for sat in satellites if is_visible(sat, timestamp)]
        
        # 檢查換手機會
        for current_sat in visible_sats:
            for candidate_sat in visible_sats:
                if current_sat != candidate_sat:
                    # 星座內換手檢查（禁用跨星座）
                    if same_constellation(current_sat, candidate_sat):
                        handover_quality = evaluate_handover_quality(
                            current_sat, candidate_sat, timestamp
                        )
                        if handover_quality > 0.7:  # 高質量換手
                            handover_events.append({
                                "time": timestamp,
                                "from": current_sat,
                                "to": candidate_sat,
                                "quality": handover_quality
                            })
    
    return {
        "total_handover_opportunities": len(handover_events),
        "average_quality": sum(event["quality"] for event in handover_events) / len(handover_events),
        "handover_rate_per_hour": len(handover_events) / (time_window_minutes / 60)
    }

def same_constellation(sat1, sat2):
    """檢查兩顆衛星是否屬於同一星座"""
    return get_constellation(sat1.name) == get_constellation(sat2.name)
```

## 📈 性能評估指標

### 選擇品質指標
```yaml
quality_metrics:
  coverage_consistency:
    description: "覆蓋一致性 - 不同時間點可見衛星數量的穩定性"
    calculation: "標準差 / 平均值"
    target: "< 0.3"
    
  handover_opportunities:
    description: "換手機會數量 - 每小時換手事件數"
    calculation: "總換手事件 / 總時長"
    target: "> 5 events/hour"
    
  phase_distribution:
    description: "相位分佈均勻度 - 衛星出現時間的分散程度"
    calculation: "最小相位差距"
    target: "> 15°"
    
  constellation_balance:
    description: "星座平衡度 - 不同星座的貢獻平衡"
    calculation: "各星座換手比例的方差"
    target: "根據星座規模調整"
```

## 🛠️ 實現參考

### 核心選擇邏輯
```python
def intelligent_satellite_selection(all_satellites, target_config):
    """
    智能衛星選擇主邏輯
    """
    results = {}
    
    for constellation in ['starlink', 'oneweb']:
        constellation_sats = filter_by_constellation(all_satellites, constellation)
        
        # 第一階段：地理相關性篩選
        geographically_relevant = geographic_filtering(constellation_sats, ntpu_coordinates)
        
        # 第二階段：軌道特性評分
        scored_satellites = []
        for sat in geographically_relevant:
            if constellation == 'starlink':
                score = calculate_starlink_score(sat)
            else:  # oneweb
                score = calculate_oneweb_score(sat)
            scored_satellites.append((sat, score))
        
        # 第三階段：動態篩選策略
        estimated_visible = estimate_visible_count(constellation_sats, ntpu_coordinates)
        strategy = select_filtering_strategy(estimated_visible, target_config[constellation])
        
        # 第四階段：相位分散優化
        selected_satellites = phase_dispersion_optimization(
            scored_satellites, target_config[constellation], strategy
        )
        
        results[constellation] = selected_satellites
    
    return results
```

---

**本技術參考文檔保存了衛星選擇系統的核心算法和設計理念，為未來的技術維護和改進提供詳細的技術基礎。**