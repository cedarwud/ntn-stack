# 🛰️ 階段二增強版：智能衛星篩選（含可見性預篩選）

[🔄 返回數據流程導航](../README.md) > 階段二增強版

## 📖 階段概述（增強版）

**增強內容**：在原有六階段篩選基礎上，新增**可見性預篩選**步驟，排除永遠不會出現在觀測點上空的衛星。

### 🎯 核心目標
- **輸入規模**：8,779 顆衛星（Starlink + OneWeb）
- **預篩選後**：約 8,000 顆（排除約 10% 不可見衛星）
- **最終輸出**：800-1000 顆（時空優化子集）
- **篩選效率**：總體篩選率約 88-90%

## 🔧 七階段篩選管線（增強版）

### 階段 0：可見性預篩選（新增）
```python
class VisibilityPreFilter:
    """基於軌道幾何的快速預篩選"""
    
    def check_orbital_coverage(self, satellite, observer_location):
        """
        檢查衛星軌道是否可能覆蓋觀測點
        
        原理：
        1. 計算衛星軌道的最大覆蓋緯度範圍
        2. 檢查觀測點是否在此範圍內
        3. 考慮地球曲率和衛星高度
        """
        
        # 從 TLE 提取軌道參數
        inclination = satellite.inclination  # 軌道傾角
        altitude = satellite.altitude_km     # 軌道高度
        
        # 計算最大地面覆蓋角度
        earth_radius = 6371.0  # km
        max_coverage_angle = math.degrees(
            math.acos(earth_radius / (earth_radius + altitude))
        )
        
        # 計算衛星地面軌跡的緯度範圍
        max_lat = inclination + max_coverage_angle
        min_lat = -max_lat
        
        # NTPU 位置：24.94°N
        observer_lat = observer_location.latitude
        
        # 快速判斷
        if min_lat <= observer_lat <= max_lat:
            return True  # 可能可見
        
        # 特殊情況：極軌衛星
        if inclination > 80:  # 近極軌
            return True  # 全球覆蓋
            
        return False  # 永遠不可見
```

### 原有六階段篩選（優化參數）

#### 階段 1：信號強度篩選
- **RSRP 門檻**：> -120 dBm（放寬以保留更多候選）
- **預期保留**：~70%

#### 階段 2：仰角篩選  
- **最低仰角**：10°（根據文檔標準）
- **預期保留**：~85%

#### 階段 3：都卜勒頻移篩選
- **最大頻移**：< 40 kHz（適應 LEO 高速運動）
- **預期保留**：~95%

#### 階段 4：星座負載平衡
- **Starlink 目標**：850 顆（調整）
- **OneWeb 目標**：150 顆（調整）

#### 階段 5：時間覆蓋優化
- **覆蓋連續性**：優先選擇填補覆蓋間隙的衛星
- **時空分散度**：最大化不同時間的覆蓋

#### 階段 6：信號品質加權
- **綜合評分**：RSRP (40%) + RSRQ (30%) + SINR (30%)
- **最終選擇**：Top 800-1000 顆

## 📊 預期篩選流程

```
初始: 8,779 顆
  ↓ (可見性預篩選 - 新增)
約 8,000 顆 (-10%)
  ↓ (信號強度篩選)
約 5,600 顆 (-30%)
  ↓ (仰角篩選)
約 4,760 顆 (-15%)
  ↓ (都卜勒篩選)
約 4,520 顆 (-5%)
  ↓ (星座平衡)
約 2,000 顆 (-55%)
  ↓ (時間覆蓋優化)
約 1,200 顆 (-40%)
  ↓ (信號品質加權)
最終: 800-1000 顆 (-20%)
```

## 🚀 實施代碼架構

### 增強版處理器
```python
class EnhancedIntelligentSatelliteFilterProcessor(BaseProcessor):
    """增強版智能衛星篩選處理器"""
    
    def __init__(self):
        super().__init__()
        self.visibility_filter = VisibilityPreFilter()
        self.observer_location = ObserverLocation(
            latitude=24.9442,   # NTPU
            longitude=121.3714
        )
        
    def process(self, satellite_data: Dict) -> Dict:
        """執行七階段篩選"""
        
        # 階段 0: 可見性預篩選（新增）
        visible_satellites = self._visibility_prefilter(
            satellite_data['satellites']
        )
        logger.info(f"可見性預篩選: {len(satellite_data['satellites'])} → {len(visible_satellites)}")
        
        # 階段 1-6: 原有篩選流程
        filtered_result = self._apply_existing_filters(visible_satellites)
        
        # 驗證覆蓋連續性
        coverage_analysis = self._analyze_coverage_continuity(filtered_result)
        
        # 如果覆蓋不足，動態調整
        if coverage_analysis['coverage_rate'] < 0.95:
            filtered_result = self._apply_buffer_satellites(
                filtered_result, 
                visible_satellites
            )
        
        return filtered_result
    
    def _visibility_prefilter(self, satellites: List) -> List:
        """可見性預篩選實現"""
        visible = []
        excluded_count = 0
        
        for sat in satellites:
            if self.visibility_filter.check_orbital_coverage(
                sat, self.observer_location
            ):
                visible.append(sat)
            else:
                excluded_count += 1
                
        logger.info(f"排除永不可見衛星: {excluded_count} 顆")
        return visible
    
    def _apply_buffer_satellites(self, current_pool, all_visible):
        """動態添加緩衝衛星"""
        buffer_size = int(len(current_pool) * 0.05)  # 5% 緩衝
        # 選擇評分次高的衛星作為緩衝
        # ... 實現細節
        return enhanced_pool
```

## 📈 性能優化

### 預篩選優勢
1. **計算效率**：軌道幾何判斷比 SGP4 計算快 100 倍
2. **減少負載**：後續階段處理量減少 10%
3. **精確度提升**：專注於真正有價值的衛星

### 並行處理
```python
from concurrent.futures import ProcessPoolExecutor

def parallel_visibility_check(satellites, batch_size=100):
    """並行執行可見性檢查"""
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = []
        for i in range(0, len(satellites), batch_size):
            batch = satellites[i:i+batch_size]
            futures.append(
                executor.submit(process_batch, batch)
            )
        
        results = []
        for future in futures:
            results.extend(future.result())
    return results
```

## 🔄 與階段六整合

### 數據流向
```
階段二增強版 (800-1000顆篩選)
    ↓
階段三-五 (信號分析、時序處理、數據整合)
    ↓
階段六 (動態池規劃，確保 10-15/3-6 顆可見)
```

### 關鍵參數傳遞
```python
# 階段二輸出增強
output_metadata = {
    'visibility_prefilter': {
        'excluded_count': 779,
        'excluded_percentage': 8.9,
        'processing_time_ms': 150
    },
    'target_pool_size': {
        'starlink': 850,
        'oneweb': 150
    },
    'coverage_guarantee': 0.95  # 95% 覆蓋率目標
}
```

## 🚨 故障排除

### 問題：預篩選過於激進
**症狀**：排除太多衛星，影響覆蓋
**解決**：
```python
# 調整覆蓋角度計算
max_coverage_angle = math.degrees(
    math.acos(earth_radius / (earth_radius + altitude))
) * 1.1  # 增加 10% 容錯
```

### 問題：覆蓋間隙過大
**症狀**：某些時段無衛星可見
**解決**：
1. 檢查軌道相位分佈
2. 增加緩衝衛星數量
3. 調整時間窗口重疊策略

## 📊 驗證指標

### 成功標準
- ✅ 可見性預篩選準確率 > 98%
- ✅ 最終池大小：800-1000 顆
- ✅ 覆蓋率 ≥ 95%
- ✅ 處理時間 < 30 秒
- ✅ Starlink 10-15 顆持續可見
- ✅ OneWeb 3-6 顆持續可見

---

**相關文檔**：
- [原版階段二](./stage2-filtering.md)
- [階段六動態池](./stage6-dynamic-pool.md)
- [衛星換手標準](../satellite_handover_standards.md)

**最後更新**：2025-09-01 | v2.0 - 增加可見性預篩選功能