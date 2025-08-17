# 📚 Phase 1 實作指南

**版本**: v1.0  
**更新日期**: 2025-08-15  
**適用範圍**: Phase 1 核心系統 (F1→F2→F3→A1)  

## 🎯 Phase 1 目標確認

### 核心目標規格
- **NTPU觀測點**: 24.9441°N, 121.3714°E
- **Starlink要求**: 10-15顆同時可見，5°仰角閾值
- **OneWeb要求**: 3-6顆同時可見，10°仰角閾值  
- **時空錯開**: 衛星出現時間和位置分散
- **A4/A5/D2**: 完整換手判斷事件支援
- **前端渲染**: navbar > 立體圖動畫支援
- **成功率**: 模擬退火85%機會達成目標

### 預期輸出規格
```json
{
  "starlink_pool": "~96顆時空錯開衛星",  // ⚠️ 預估值，待程式驗證
  "oneweb_pool": "~38顆時空錯開衛星",   // ⚠️ 預估值，待程式驗證
  "coverage_guarantee": "10-15/3-6顆隨時可見",
  "a4_a5_d2_events": "完整換手事件數據",
  "frontend_ready": true
}
```

⚠️ **重要說明**: 96顆Starlink和38顆OneWeb為基於理論分析的**預估池大小**，實際所需衛星數量需要在完成模擬退火演算法實現並進行動態覆蓋模擬後才能確定。

## 🏗️ 架構實作詳解

### F1: TLE載入引擎 (Week 1)

#### 核心功能實作
```python
class TLELoaderEngine:
    async def load_full_satellite_data(self):
        """載入8,735顆衛星完整TLE數據"""
        # 處理: Starlink ~5,000顆 + OneWeb ~800顆 + 其他星座
        # 來源: CelesTrak官方TLE數據
        
    async def calculate_orbital_positions(self, satellites, time_range_minutes=200):
        """SGP4計算200個時間點軌道位置"""
        # 時間解析度: 30秒間隔
        # 精度要求: 位置精度 < 100m
```

#### 關鍵實作細節
1. **TLE數據源**: 使用CelesTrak.org官方數據
2. **SGP4引擎**: Skyfield庫精確計算
3. **時間軸**: 200個時間點，30秒間隔，總計100分鐘
4. **座標系**: 地心地固座標系統(ECEF)
5. **觀測點**: NTPU固定觀測點，海拔50米

#### 性能要求
- **載入時間**: < 2分鐘 (8,735顆衛星)
- **計算精度**: 位置誤差 < 100米
- **記憶體使用**: < 2GB
- **錯誤處理**: 90%+成功率

### F2: 衛星篩選引擎 (Week 1)

#### 篩選策略
```python
class SatelliteFilterEngine:
    async def apply_comprehensive_filter(self, satellite_data):
        """從8,735顆篩選到554顆候選"""
        # Starlink目標: 350顆候選
        # OneWeb目標: 204顆候選
        
    async def _apply_geographic_filter(self, satellites, constellation):
        """地理相關性篩選"""
        # 軌道傾角 > 觀測點緯度 (24.94°)
        # 升交點經度相關性評分
        
    async def _calculate_starlink_score(self, satellite, params):
        """Starlink專用評分"""
        # 傾角適用性 (30%): 53°最佳
        # 高度適用性 (25%): 550km最佳
        # 相位分散度 (20%): 避免同時出現
        # 換手頻率 (15%): 96分鐘週期最佳
        # 信號穩定性 (10%): 低偏心率優先
```

#### 評分機制
1. **Starlink評分系統** (總分100):
   - 軌道傾角適用性: 30分 (53°最佳)
   - 高度適用性: 25分 (550km最佳)
   - 相位分散度: 20分 (避免聚集)
   - 換手頻率: 15分 (週期適中)
   - 信號穩定性: 10分 (軌道穩定)

2. **OneWeb評分系統** (總分100):
   - 軌道傾角適用性: 25分 (87.4°最佳)
   - 高度適用性: 25分 (1200km最佳)
   - 極地覆蓋: 20分 (高傾角優勢)
   - 軌道形狀: 20分 (近圓軌道)
   - 相位分散: 10分 (時間分佈)

#### 篩選驗證
- **地理相關性**: 60分以上門檻
- **軌道特性**: 70分以上門檻
- **最終候選**: 554顆 (350 Starlink + 204 OneWeb)

### F3: A4/A5/D2事件處理器 (Week 2)

#### 3GPP事件實作
```python
class A4A5D2EventProcessor:
    async def _detect_a4_event(self, serving, neighbor):
        """A4事件: 鄰近衛星信號優於門檻"""
        # 3GPP標準: Mn + Ofn + Ocn – Hys > Thresh2
        # 實現: neighbor_rsrp > -100 dBm
        
    async def _detect_a5_event(self, serving, neighbor):
        """A5事件: 服務衛星劣化且鄰近衛星良好"""
        # 條件1: serving_rsrp < -110 dBm (劣化)
        # 條件2: neighbor_rsrp > -100 dBm (良好)
        
    async def _detect_d2_event(self, serving, neighbor):
        """D2事件: LEO衛星距離優化換手"""
        # 條件1: serving_distance > 5000km
        # 條件2: neighbor_distance < 3000km
```

#### RSRP精確計算
```python
async def calculate_precise_rsrp(self, satellite_data):
    """Ku頻段12GHz精確RSRP計算"""
    # 1. 自由空間路徑損耗: FSPL = 20*log10(d) + 20*log10(f) + 32.45
    # 2. 仰角增益: elevation/90 * 15dB (最大15dB)
    # 3. 發射功率: 43dBm
    # 4. 天線增益: 35dBi (衛星) + 30dBi (地面)
    # 5. 系統損耗: 大氣2dB + 系統噪聲5dB
    # RSRP = 43 + 35 + 30 + elevation_gain - FSPL - 2 - 5
```

#### 事件優先級
- **HIGH**: A5事件 (緊急換手)
- **MEDIUM**: A4事件 (標準換手)  
- **LOW**: D2事件 (優化換手)

#### 處理要求
- **時間軸**: 完整200個時間點處理
- **事件檢測**: 實時逐點檢測
- **星座限制**: 僅允許星座內換手
- **統計輸出**: A4/A5/D2事件分類統計

### A1: 模擬退火最佳化器 (Week 3)

#### 核心演算法
```python
class SimulatedAnnealingOptimizer:
    async def _simulated_annealing_optimization(self, initial_solution):
        """模擬退火核心演算法"""
        while temperature > min_temperature:
            neighbor = generate_neighbor_solution(current)
            if accept_solution(neighbor, temperature):
                current = neighbor
                if current.cost < best.cost:
                    best = current
            temperature *= cooling_rate
        return best
        
    def _accept_solution(self, current_cost, neighbor_cost, temperature):
        """Metropolis接受準則"""
        if neighbor_cost < current_cost:
            return True
        else:
            probability = exp(-(neighbor_cost - current_cost) / temperature)
            return random() < probability
```

#### 約束評估
```python
def _evaluate_solution_cost(self, starlink_sats, oneweb_sats):
    """解決方案成本評估"""
    cost = 0.0
    
    # 硬約束 (重懲罰)
    if not meets_visibility_requirements():  # 10-15/3-6顆
        cost += 10000.0
    if not meets_temporal_distribution():   # 時空錯開
        cost += 5000.0
    if not meets_pool_size():              # 96/38顆
        cost += 8000.0
        
    # 軟約束 (優化)
    cost += signal_quality_cost() * 100.0
    cost += orbital_diversity_cost() * 50.0
    
    return cost
```

#### 最佳化參數
- **初始溫度**: 1000.0
- **冷卻率**: 0.95  
- **最小溫度**: 1.0
- **最大迭代**: 10,000次
- **停滯容忍**: 100次無改善自動停止

#### 收斂標準
- **可見性合規**: ≥90% 時間點滿足10-15/3-6顆要求
- **時空分佈**: ≥70% 分佈品質評分
- **信號品質**: ≥80% 信號品質評分
- **池大小**: 精確達到96/38顆目標

## 🧪 測試與驗證

### 單元測試
```bash
# F1測試
cd phase1_core_system/f1_tle_loader
python -m pytest test_tle_loader.py -v

# F2測試  
cd ../f2_satellite_filter
python -m pytest test_satellite_filter.py -v

# F3測試
cd ../f3_signal_analyzer  
python -m pytest test_a4_a5_d2_processor.py -v

# A1測試
cd ../a1_dynamic_pool_planner
python -m pytest test_simulated_annealing.py -v
```

### 整合測試
```bash
# 完整管道測試
python main_pipeline.py

# 驗證輸出
ls /tmp/phase1_outputs/
# 預期文件:
# - stage1_tle_loading_results.json
# - stage2_filtering_results.json  
# - stage3_event_analysis_results.json
# - stage4_optimization_results.json
# - phase1_final_report.json
```

### 性能基準測試
```python
async def performance_benchmark():
    """性能基準測試"""
    
    # Stage 1: TLE載入 (目標: <120秒)
    stage1_time = measure_stage1_performance()
    assert stage1_time < 120, f"Stage 1超時: {stage1_time}秒"
    
    # Stage 2: 篩選 (目標: <60秒)
    stage2_time = measure_stage2_performance()
    assert stage2_time < 60, f"Stage 2超時: {stage2_time}秒"
    
    # Stage 3: 事件分析 (目標: <180秒)
    stage3_time = measure_stage3_performance()
    assert stage3_time < 180, f"Stage 3超時: {stage3_time}秒"
    
    # Stage 4: 最佳化 (目標: <300秒)
    stage4_time = measure_stage4_performance()
    assert stage4_time < 300, f"Stage 4超時: {stage4_time}秒"
```

## 🔧 部署與執行

### 環境準備
```bash
# 1. 安裝依賴
pip install skyfield numpy scipy matplotlib

# 2. 創建輸出目錄
mkdir -p /tmp/phase1_outputs

# 3. 下載TLE數據
wget -O starlink.tle https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink
wget -O oneweb.tle https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb
```

### 執行流程
```bash
# 1. 進入Phase 1目錄
cd /home/sat/ntn-stack/leo_restructure/phase1_core_system

# 2. 執行完整管道
python main_pipeline.py

# 3. 檢查輸出
cat /tmp/phase1_outputs/phase1_final_report.json | jq .phase1_completion_report.final_results

# 4. 驗證成功
echo "檢查可見性合規是否 ≥ 90%"
echo "檢查Starlink池是否 = 96顆"  
echo "檢查OneWeb池是否 = 38顆"
```

### 錯誤處理
```python
# 常見錯誤和解決方案
ERROR_SOLUTIONS = {
    "TLE數據載入失敗": "檢查網路連接，確認CelesTrak可訪問",
    "SGP4計算錯誤": "檢查TLE數據格式，確認時間參數正確", 
    "篩選候選不足": "降低評分門檻或增加地理範圍",
    "事件檢測失敗": "檢查衛星位置數據完整性",
    "最佳化不收斂": "調整溫度參數或增加迭代次數",
    "可見性不達標": "增加衛星池大小或調整仰角閾值"
}
```

## 📊 成功驗證標準

### 必達指標
- ✅ **Starlink池**: ~96顆衛星 ⚠️ **預估值，待程式驗證確定實際數量**
- ✅ **OneWeb池**: ~38顆衛星 ⚠️ **預估值，待程式驗證確定實際數量**  
- ✅ **可見性合規**: ≥90% 時間滿足10-15/3-6顆
- ✅ **時空分佈**: ≥70% 分散品質
- ✅ **A4/A5/D2**: 完整事件檢測和分類
- ✅ **前端相容**: JSON格式完全兼容

### 性能指標
- ✅ **總執行時間**: <10分鐘
- ✅ **記憶體使用**: <4GB
- ✅ **成功率**: >85% (模擬退火收斂)
- ✅ **錯誤率**: <5%

### 品質指標
- ✅ **位置精度**: SGP4誤差 <100米
- ✅ **RSRP計算**: Ku頻段精確模型
- ✅ **事件準確率**: >95% 正確分類
- ✅ **時空分散**: 相位差 >15°

## 🚀 下週計劃 (Week 4)

### 前端整合測試
1. **數據格式驗證**: 確保JSON輸出兼容前端立體圖
2. **動畫測試**: 驗證96分鐘週期動畫流暢性
3. **可見性驗證**: 實時檢查10-15/3-6顆要求
4. **事件觸發**: 驗證A4/A5/D2事件正確觸發

### 最終調優
1. **性能調優**: 最佳化執行時間和記憶體使用
2. **參數調校**: 模擬退火參數精調
3. **錯誤處理**: 完善異常處理和恢復機制
4. **文檔完善**: 完整API文檔和使用指南

---

**成功標準**: Week 4結束時，Phase 1必須100%達成所有目標，為Phase 2 RL擴展奠定堅實基礎。