# 第一階段：零容忍篩選系統設計

**狀態**: ✅ 已完成實施  
**完成日期**: 2025-08-01  
**實施檔案**: `/simworld/backend/rl_optimized_satellite_filter.py`

## 📋 設計目標

為 45 天強化學習訓練建立零容忍的衛星數據篩選系統，確保：
- **零錯誤數據** - 不容許任何不合理的軌道參數
- **高品質覆蓋** - 確保台灣地區的有效衛星覆蓋
- **RL 適用性** - 滿足強化學習訓練的嚴格要求

## 🏗️ 四階段驗證架構

### 1️⃣ 參數完整性驗證
```python
def _validate_parameters(self, sat_data: Dict) -> tuple[bool, str]:
    """驗證必要的軌道參數是否存在且有效"""
    required_params = [
        'INCLINATION', 'MEAN_MOTION', 'ECCENTRICITY',
        'RA_OF_ASC_NODE', 'ARG_OF_PERICENTER', 'MEAN_ANOMALY'
    ]
```

### 2️⃣ 物理合理性驗證
```python
def _validate_physics(self, sat_data: Dict) -> tuple[bool, str]:
    """驗證軌道參數的物理合理性"""
    # 軌道傾角：0-180度
    # 平均運動：LEO 合理範圍
    # 離心率：近圓軌道優先
```

### 3️⃣ 覆蓋能力驗證
```python
def _validate_coverage(self, sat_data: Dict) -> tuple[bool, str]:
    """使用 SGP4 計算驗證衛星覆蓋能力"""
    # 最低仰角：10度
    # 最短通過時間：180秒
    # 覆蓋頻率檢查
```

### 4️⃣ RL 適用性驗證
```python
def _validate_rl_suitability(self, sat_data: Dict) -> tuple[bool, str]:
    """驗證是否適合 RL 訓練"""
    # 每日通過次數：2-15次
    # 換手場景多樣性
    # 訓練價值評估
```

## 📊 篩選結果

| 星座 | 原始數量 | 篩選後 | 通過率 | 主要淘汰原因 |
|------|----------|---------|--------|--------------|
| **Starlink** | 8,044 | 1,707 | 21.2% | 覆蓋範圍限制 |
| **OneWeb** | 651 | 651 | 100% | 極地軌道全通過 |
| **總計** | 8,695 | 2,358 | 27.1% | - |

## 🔧 關鍵參數設置

```python
class RLOptimizedSatelliteFilter:
    def __init__(self):
        # RL 訓練的嚴格標準
        self.min_elevation = 10.0        # 最低可見仰角（度）
        self.min_pass_duration = 180     # 最短通過時間（秒）
        self.min_daily_passes = 2        # 每日最少通過次數
        self.max_daily_passes = 15       # 每日最多通過次數（極地軌道調整）
        
        # 軌道參數約束
        self.max_eccentricity = 0.1      # 最大離心率
        self.min_mean_motion = 11.0      # 最小平均運動（圈/天）
        self.max_mean_motion = 17.0      # 最大平均運動（圈/天）
```

## 💡 關鍵優化

### OneWeb 極地軌道問題解決
- **問題**: 初始設定每日通過上限 10 次，導致 OneWeb 全部被拒絕
- **分析**: OneWeb 87.9° 傾角，每日通過 10.53 次
- **解決**: 調整上限至 15 次，保留極地軌道的價值

### Starlink 覆蓋篩選
- **策略**: 重點選擇能覆蓋台灣地區的軌道平面
- **結果**: 78.8% 因覆蓋範圍不足被淘汰
- **保留**: 21.2% 高品質衛星供訓練使用

## 🚀 使用方式

```python
# 初始化篩選器
filter_system = RLOptimizedSatelliteFilter(
    target_lat=24.9441,  # 國立臺北大學
    target_lon=121.3714
)

# 執行篩選
accepted, rejected = filter_system.filter_satellites(
    all_satellites,
    show_rejection_details=True
)

# 分析結果
filter_system.analyze_filtering_results(accepted, rejected)
```

## ✅ 完成標準

- [x] 零參數失敗率
- [x] 零物理違規
- [x] OneWeb 100% 通過率
- [x] Starlink 合理篩選率
- [x] 詳細拒絕原因記錄
- [x] 可調整的參數系統

## 📚 相關文件

- 實施代碼：`/simworld/backend/rl_optimized_satellite_filter.py`
- 調試工具：`/simworld/backend/debug_oneweb_rejection.py`
- 驗證腳本：`/simworld/backend/validate_first_stage_filtering.py`
