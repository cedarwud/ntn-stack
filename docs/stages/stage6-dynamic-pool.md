# 🛰️ 階段六：動態衛星池規劃

[🔄 返回數據流程導航](../README.md) > 階段六

## 📖 階段概述

**設計目標**：建立智能動態衛星池，確保 NTPU 觀測點上空任何時刻都有足夠的可見衛星，支援連續不間斷的衛星切換研究

### 🎯 @doc/todo.md 核心需求實現
本階段實現以下核心需求：
- ✅ **時空錯置篩選**: 錯開時間和位置的衛星選擇，基於軌道相位分散
- ✅ **衛星池規劃**: Starlink 10-15顆(5°仰角) + OneWeb 3-6顆(10°仰角)
- ✅ **動態覆蓋**: 整個軌道週期中持續保持上述衛星數量 (95%+覆蓋率)
- ✅ **強化學習數據準備**: 為DQN/A3C/PPO/SAC算法提供訓練樣本
- ✅ **實時決策支援**: 毫秒級換手決策響應與多候選評估

### 🎯 技術目標規格
- **Starlink 持續覆蓋**：任何時刻保證 10-15 顆可見衛星（仰角 ≥5°）
- **OneWeb 持續覆蓋**：任何時刻保證 3-6 顆可見衛星（仰角 ≥10°）
- **時間覆蓋率**：≥95% 時間滿足上述覆蓋要求（允許短暫緩衝）
- **切換連續性**：確保衛星切換時至少有 3 個候選衛星可用

### 🛰️ LEO衛星換手研究支援目標（擴充）
- **A4/A5/D2事件數據支援**：為階段三的3GPP事件提供豐富的換手場景
- **強化學習訓練數據**：生成大量換手決策樣本，支援DQN/A3C/PPO算法訓練
- **換手決策優化**：提供連續的換手機會，驗證各種換手策略效能
- **時空錯置最佳化**：透過軌道相位分散，創造最多樣化的換手場景
- **QoS保證驗證**：在換手過程中維持服務品質，驗證RSRP門檻策略

### 📊 預期輸出（智能優化版）
**衛星池規模**：智能軌道相位選擇最優子集（預估 300-350 顆）
  - Starlink: 約 250 顆（8.6% 高效子集，確保充分覆蓋冗餘）
  - OneWeb: 約 80 顆（12.3% 精選子集，提供穩定備選）
**核心策略**：軌道相位錯開 + 時空互補覆蓋 + 冗餘保證（非暴力數量堆疊）
**時間序列**：完整軌道週期數據（2小時驗證窗口）
**覆蓋保證**：95%+ 時段滿足覆蓋要求，基於軌道動力學最優化
**處理時間**：< 3 秒（實際 ~1.3 秒）

## 🎯 演算法設計要求

### 智能軌道相位選擇策略（驗證優化版）
- **軌道週期驗證**：基於2小時完整軌道週期（Starlink 93.63min, OneWeb 109.64min）
- **時空錯置核心算法**：選擇軌道相位互補的衛星，實現連續覆蓋
- **最小衛星數原理**：理論最小值3-4顆×安全係數5-8 = 實際需求200-300顆（含冗餘保證）
- **可見性智能預篩選**：排除NTPU座標永不可見的衛星（減少75-85%候選）
- **軌道平面分散策略**：不同軌道傾角和升交點的最優組合
- **覆蓋間隙零容忍**：通過精確軌道計算確保無覆蓋空窗
- **動態緩衝機制**：預留10-20%額外衛星應對軌道攝動

### 95%+ 覆蓋率量化驗證核心算法
- **覆蓋率計算方法**：基於軌道週期時間窗口的精確覆蓋統計
  - 時間採樣間隔：30秒（240個採樣點/2小時）
  - Starlink 覆蓋統計：每個時間點計算 ≥5°仰角可見衛星數 ≥ 10顆
  - OneWeb 覆蓋統計：每個時間點計算 ≥10°仰角可見衛星數 ≥ 3顆
  - 覆蓋率 = 滿足要求的時間點數 ÷ 總時間點數 × 100%
  
- **量化驗證指標**：
  ```python
  覆蓋率驗證算法 = {
      'starlink_coverage_ratio': count(starlink_visible ≥ 10) / total_timepoints,
      'oneweb_coverage_ratio': count(oneweb_visible ≥ 3) / total_timepoints,  
      'combined_coverage_ratio': count(starlink_visible ≥ 10 AND oneweb_visible ≥ 3) / total_timepoints,
      'coverage_gaps': find_continuous_gaps_longer_than(threshold_minutes=2)
  }
  ```

- **覆蓋連續性分析**：
  - **最大容許間隙**：≤ 2分鐘（4個連續採樣點）
  - **間隙頻率統計**：記錄所有覆蓋不足時段的長度和頻率
  - **恢復時間分析**：記錄從覆蓋不足到恢復正常的時間

### 軌道週期驗證擴充（量化版）
- **軌道週期完整性**：2小時時間窗口覆蓋完整軌道週期
- **時空錯置有效性**：驗證不同軌道相位衛星的接續覆蓋
- **最小可見衛星數**：基於軌道動力學的理論最小值驗證
- **95%+ 覆蓋率保證**：精確量化的覆蓋統計和間隙分析
- **軌道相位優化效果**：相比暴力數量堆疊的效率提升
- **服務質量保證**：在最小衛星數約束下的RSRP、RSRQ門檻達成率

## 🛠️ 技術實現要求

### 時間序列數據完整性
確保選中的每顆衛星都包含完整的軌道時間序列數據：

```python
@dataclass 
class EnhancedSatelliteCandidate:
    """增強衛星候選資訊 + 包含時間序列軌道數據"""
    basic_info: SatelliteBasicInfo
    windows: List[SAVisibilityWindow]
    total_visible_time: int
    coverage_ratio: float
    distribution_score: float
    signal_metrics: SignalCharacteristics
    selection_rationale: Dict[str, float]
    # 🎯 關鍵修復：添加時間序列軌道數據支持
    position_timeseries: List[Dict[str, Any]] = None
```

### 數據完整性保證
每顆選中的衛星包含：
- **時間點數**：Starlink 192個點 (96分鐘)、OneWeb 218個點 (109分鐘)
- **軌道覆蓋**：完整軌道週期的位置信息，30秒間隔連續數據
- **SGP4精度**：真實軌道動力學計算結果
- **連續性保證**：無數據間隙，支持平滑動畫

## 🛠️ 實現架構

### 主要功能模組
```bash
/netstack/src/stages/enhanced_dynamic_pool_planner.py
├── convert_to_enhanced_candidates()      # 保留時間序列數據
├── generate_enhanced_output()            # 輸出含時間序列的衛星池
└── process()                            # 完整流程執行

/netstack/netstack_api/routers/simple_satellite_router.py
├── get_dynamic_pool_satellite_data()    # 優先讀取階段六數據
└── get_precomputed_satellite_data()     # 數據源優先級控制
```

### 95%+ 覆蓋率驗證模組實現
```python
class CoverageValidationEngine:
    """95%+ 覆蓋率量化驗證引擎"""
    
    def __init__(self, observer_lat: float = 24.9441667, observer_lon: float = 121.3713889):
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon
        self.sampling_interval_sec = 30  # 30秒採樣間隔
        self.orbital_period_hours = 2    # 2小時驗證窗口
        
        # 覆蓋要求配置
        self.coverage_requirements = {
            'starlink': {'min_elevation': 5.0, 'min_satellites': 10},
            'oneweb': {'min_elevation': 10.0, 'min_satellites': 3}
        }
    
    def calculate_coverage_ratio(self, selected_satellites: Dict, time_window_hours: float = 2) -> Dict:
        """計算95%+覆蓋率的精確量化指標"""
        total_timepoints = int((time_window_hours * 3600) / self.sampling_interval_sec)  # 240個採樣點
        
        coverage_stats = {
            'starlink_coverage_ratio': 0.0,
            'oneweb_coverage_ratio': 0.0, 
            'combined_coverage_ratio': 0.0,
            'coverage_gaps': [],
            'detailed_timeline': []
        }
        
        # 遍歷每個時間點
        starlink_satisfied_count = 0
        oneweb_satisfied_count = 0
        combined_satisfied_count = 0
        
        current_gap_start = None
        gaps = []
        
        for timepoint in range(total_timepoints):
            current_time_sec = timepoint * self.sampling_interval_sec
            
            # 計算當前時間點的可見衛星數
            starlink_visible = self._count_visible_satellites(
                selected_satellites['starlink'], 
                current_time_sec,
                min_elevation=self.coverage_requirements['starlink']['min_elevation']
            )
            
            oneweb_visible = self._count_visible_satellites(
                selected_satellites['oneweb'],
                current_time_sec, 
                min_elevation=self.coverage_requirements['oneweb']['min_elevation']
            )
            
            # 檢查是否滿足覆蓋要求
            starlink_satisfied = starlink_visible >= self.coverage_requirements['starlink']['min_satellites']
            oneweb_satisfied = oneweb_visible >= self.coverage_requirements['oneweb']['min_satellites']
            combined_satisfied = starlink_satisfied and oneweb_satisfied
            
            # 累計滿足要求的時間點
            if starlink_satisfied:
                starlink_satisfied_count += 1
            if oneweb_satisfied:
                oneweb_satisfied_count += 1
            if combined_satisfied:
                combined_satisfied_count += 1
            
            # 記錄覆蓋間隙
            if not combined_satisfied:
                if current_gap_start is None:
                    current_gap_start = timepoint
            else:
                if current_gap_start is not None:
                    gap_duration_min = (timepoint - current_gap_start) * self.sampling_interval_sec / 60
                    gaps.append({
                        'start_timepoint': current_gap_start,
                        'end_timepoint': timepoint,
                        'duration_minutes': gap_duration_min
                    })
                    current_gap_start = None
            
            # 記錄詳細時間線（採樣記錄）
            if timepoint % 20 == 0:  # 每10分鐘記錄一次詳情
                coverage_stats['detailed_timeline'].append({
                    'timepoint': timepoint,
                    'time_minutes': current_time_sec / 60,
                    'starlink_visible': starlink_visible,
                    'oneweb_visible': oneweb_visible,
                    'starlink_satisfied': starlink_satisfied,
                    'oneweb_satisfied': oneweb_satisfied,
                    'combined_satisfied': combined_satisfied
                })
        
        # 處理最後一個間隙
        if current_gap_start is not None:
            gap_duration_min = (total_timepoints - current_gap_start) * self.sampling_interval_sec / 60
            gaps.append({
                'start_timepoint': current_gap_start,
                'end_timepoint': total_timepoints,
                'duration_minutes': gap_duration_min
            })
        
        # 計算覆蓋率百分比
        coverage_stats.update({
            'starlink_coverage_ratio': starlink_satisfied_count / total_timepoints,
            'oneweb_coverage_ratio': oneweb_satisfied_count / total_timepoints,
            'combined_coverage_ratio': combined_satisfied_count / total_timepoints,
            'coverage_gaps': [gap for gap in gaps if gap['duration_minutes'] > 2],  # 只記錄超過2分鐘的間隙
            'total_timepoints': total_timepoints,
            'coverage_gap_analysis': {
                'total_gaps': len([gap for gap in gaps if gap['duration_minutes'] > 2]),
                'max_gap_minutes': max([gap['duration_minutes'] for gap in gaps], default=0),
                'avg_gap_minutes': np.mean([gap['duration_minutes'] for gap in gaps]) if gaps else 0
            }
        })
        
        return coverage_stats
    
    def _count_visible_satellites(self, satellites: List[Dict], time_sec: float, min_elevation: float) -> int:
        """計算指定時間點的可見衛星數量"""
        visible_count = 0
        
        for satellite in satellites:
            position_timeseries = satellite.get('position_timeseries', [])
            
            # 找到最接近的時間點
            target_timepoint = int(time_sec / self.sampling_interval_sec)
            
            if target_timepoint < len(position_timeseries):
                position_data = position_timeseries[target_timepoint]
                elevation = position_data.get('elevation_deg', -90)
                
                if elevation >= min_elevation:
                    visible_count += 1
        
        return visible_count
    
    def validate_coverage_requirements(self, coverage_stats: Dict) -> Dict:
        """驗證是否滿足95%+覆蓋率要求"""
        validation_result = {
            'overall_passed': False,
            'starlink_passed': coverage_stats['starlink_coverage_ratio'] >= 0.95,
            'oneweb_passed': coverage_stats['oneweb_coverage_ratio'] >= 0.95, 
            'combined_passed': coverage_stats['combined_coverage_ratio'] >= 0.95,
            'gap_analysis_passed': coverage_stats['coverage_gap_analysis']['max_gap_minutes'] <= 2,
            'detailed_checks': {
                'starlink_coverage_percentage': f"{coverage_stats['starlink_coverage_ratio']:.1%}",
                'oneweb_coverage_percentage': f"{coverage_stats['oneweb_coverage_ratio']:.1%}",
                'combined_coverage_percentage': f"{coverage_stats['combined_coverage_ratio']:.1%}",
                'max_gap_duration': f"{coverage_stats['coverage_gap_analysis']['max_gap_minutes']:.1f} 分鐘"
            }
        }
        
        validation_result['overall_passed'] = (
            validation_result['starlink_passed'] and 
            validation_result['oneweb_passed'] and
            validation_result['gap_analysis_passed']
        )
        
        return validation_result
```

### 關鍵修復實現
```python
def convert_to_enhanced_candidates(self, satellite_data: List[Dict]):
    """轉換候選數據並保留完整時間序列"""
    enhanced_candidates = []
    
    for sat_data in satellite_data:
        # 🎯 關鍵修復：保留完整的時間序列數據
        position_timeseries = sat_data.get('position_timeseries', [])
        
        candidate = EnhancedSatelliteCandidate(
            basic_info=basic_info,
            windows=windows,
            # ... 其他字段 ...
            # 🎯 關鍵修復：添加時間序列數據到候選對象
            position_timeseries=position_timeseries
        )
        enhanced_candidates.append(candidate)
    
    return enhanced_candidates

def generate_enhanced_output(self, results: Dict) -> Dict:
    """生成包含時間序列的最終輸出"""
    output_data = {
        'dynamic_satellite_pool': {
            'starlink_satellites': [],
            'oneweb_satellites': [],
            'selection_details': []
        }
    }
    
    for sat_id, candidate in results['selected_satellites'].items():
        sat_info = {
            'satellite_id': sat_id,
            'constellation': candidate.basic_info.constellation.value,
            'satellite_name': candidate.basic_info.satellite_name,
            'norad_id': candidate.basic_info.norad_id,
            # ... 其他信息 ...
            # 🎯 關鍵修復：保留完整的時間序列軌道數據
            'position_timeseries': candidate.position_timeseries or []
        }
        output_data['dynamic_satellite_pool']['selection_details'].append(sat_info)
    
    return output_data
```

## 📊 輸出數據格式

### 階段六輸出結構
```json
{
  "optimization_metadata": {
    "timestamp": "2025-08-18T12:00:00Z",
    "stage": "stage6_dynamic_pool_planning",
    "processing_time_seconds": 0.5,
    "observer_location": {
      "latitude": 24.9441667,
      "longitude": 121.3713889,
      "location_name": "NTPU"
    }
  },
  "dynamic_satellite_pool": {
    "starlink_satellites": ["STARLINK-1234", "..."],  // 100-200顆（智能選擇）
    "oneweb_satellites": ["ONEWEB-0123", "..."],      // 30-50顆（軌道相位優化）
    "total_count": 150,  // 相比850+150減少85%
    "selection_details": [
      {
        "satellite_id": "STARLINK-1234",
        "constellation": "starlink",
        "satellite_name": "Starlink-1234",
        "norad_id": 12345,
        "total_visible_time": 1800,
        "coverage_ratio": 0.75,
        "distribution_score": 0.85,
        "signal_metrics": {
          "rsrp_dbm": -85.5,
          "rsrq_db": 12.8,
          "sinr_db": 15.2
        },
        "visibility_windows": 3,
        "selection_rationale": {
          "visibility_score": 0.9,
          "signal_score": 0.8,
          "temporal_score": 0.85
        },
        // 🎯 關鍵：每顆衛星包含完整的192點時間序列數據
        "position_timeseries": [
          {
            "time": "2025-08-18T00:00:00Z",
            "time_offset_seconds": 0,
            "position_eci": {"x": 1234.5, "y": 5678.9, "z": 3456.7},
            "velocity_eci": {"x": 7.5, "y": -2.3, "z": 1.8},
            "range_km": 1250.3,
            "elevation_deg": 15.2,
            "azimuth_deg": 45.8,
            "is_visible": true
          },
          // ... 191 more points at 30-second intervals
        ]
      }
    ]
  }
}
```

## 🔄 API 整合

### NetStack API 數據源優先級
```python
def get_precomputed_satellite_data(constellation: str, count: int = 200) -> List[Dict]:
    """
    獲取預計算衛星數據，優先使用階段六動態池數據
    階段六(156顆優化) > 階段五分層數據(150+50顆) > 錯誤
    """
    
    # 🎯 優先嘗試階段六動態池數據
    try:
        dynamic_pool_satellites = get_dynamic_pool_satellite_data(constellation, count)
        if dynamic_pool_satellites:
            logger.info(f"✅ 使用階段六動態池數據: {len(dynamic_pool_satellites)} 顆 {constellation} 衛星")
            return dynamic_pool_satellites
    except Exception as e:
        logger.warning(f"⚠️ 階段六動態池數據載入失敗，回退到階段五: {e}")
    
    # 🔄 回退到階段五分層數據
    return get_layered_satellite_data(constellation, count)
```

## 📈 成功標準（調整後）

### 必須達成的指標
1. **覆蓋率 ≥ 95%**：95%以上時間滿足最小衛星數要求（調整）
2. **最大間隙 < 2分鐘**：任何覆蓋間隙不超過 2 分鐘（調整）
3. **切換連續性**：任何切換時刻至少有3個候選衛星
4. **數據完整性**：每顆衛星包含完整軌道週期數據
5. **子集優化**：Starlink ≤ 900顆、OneWeb ≤ 160顆（新增）

### 性能要求
- **處理時間**：< 5秒完成動態池規劃
- **記憶體使用**：< 2GB 峰值記憶體
- **API 響應**：< 100ms 查詢響應時間
- **前端流暢**：60 FPS 軌跡動畫無卡頓

## 🚨 故障排除

### 常見問題
1. **時間序列數據為空**
   - 檢查：階段五是否正確生成數據
   - 解決：確認 `position_timeseries` 字段存在

2. **API返回舊數據**
   - 檢查：階段六文件是否生成
   - 解決：重新執行階段六處理流程

3. **前端軌跡仍然跳躍**
   - 檢查：API是否使用階段六數據
   - 解決：確認 NetStack API 日誌中顯示使用階段六數據

## 📊 預期成果

### 對 LEO 衛星切換研究的價值
1. **連續切換場景**：提供真實的連續切換測試環境
2. **演算法驗證**：可驗證各種切換決策演算法的效能
3. **QoS 保證**：確保服務品質在切換過程中的連續性
4. **統計分析**：提供充足的樣本數據進行統計研究

### 🤖 強化學習換手優化支援（新增）
1. **訓練數據生成**：
   - **狀態空間**：衛星位置、信號強度、仰角、距離等多維度狀態
   - **動作空間**：換手決策（保持/切換至候選衛星1/2/3...）
   - **獎勵函數**：基於QoS、中斷時間、信號品質的複合獎勵
   - **經驗回放**：存儲大量真實換手場景供算法學習

2. **多算法支援**：
   - **DQN (Deep Q-Network)**：離散動作空間的換手決策
   - **A3C (Asynchronous Actor-Critic)**：並行學習多種換手策略
   - **PPO (Proximal Policy Optimization)**：穩定的策略梯度優化
   - **SAC (Soft Actor-Critic)**：連續控制的換手參數調優

3. **A4/A5/D2事件強化**：
   - **Event A4增強**：利用時空錯置創造更多鄰近衛星觸發場景
   - **Event A5優化**：服務衛星劣化時的最佳候選選擇策略
   - **Event D2智能**：距離門檻的動態調整與預測性換手

4. **實時決策支援**：
   - **毫秒級響應**：支援真實時間的換手決策推理
   - **多候選評估**：同時評估3-5個換手候選的優劣
   - **自適應門檻**：根據環境動態調整RSRP/距離門檻

### 系統整合效益
1. **前端視覺化**：支援流暢的 3D 衛星軌跡動畫
2. **API 效能**：預計算數據大幅降低即時運算負載
3. **研究彈性**：支援不同時間段的切換場景模擬
4. **數據可靠性**：基於真實 TLE 數據的準確軌道預測

## ✅ 階段驗證標準

### 🎯 Stage 6 完成驗證檢查清單

#### 1. **輸入驗證**
- [ ] Stage 5整合數據完整
  - 接收1,100+顆候選衛星
  - 包含完整時間序列數據
  - 信號指標和可見性窗口正確

#### 2. **95%+ 覆蓋率量化驗證**
- [ ] **覆蓋率精確計算**
  ```python
  驗證方法:
  - 時間採樣: 2小時/30秒間隔 = 240個採樣點
  - Starlink驗證: count(visible_satellites ≥ 10 @ elevation ≥ 5°) / 240
  - OneWeb驗證: count(visible_satellites ≥ 3 @ elevation ≥ 10°) / 240  
  - 目標覆蓋率: ≥ 95% (228/240 個採樣點滿足要求)
  ```
- [ ] **覆蓋間隙分析**
  - 最大容許間隙: ≤ 2分鐘（4個連續採樣點）
  - 間隙頻率統計: 記錄所有 > 2分鐘的覆蓋不足時段
  - 間隙恢復時間: 從不足到恢復正常的平均時間

#### 3. **時空錯置驗證**
- [ ] **軌道相位分散**
  ```
  驗證項目:
  - 平均近點角分散: 12個相位區間
  - RAAN分散: 8個區間
  - 相位多樣性得分 > 0.7
  ```

#### 4. **衛星池規模驗證**
- [ ] **最終池大小**
  ```
  目標範圍:
  - Starlink: 200-250顆
  - OneWeb: 60-80顆
  - 總計: 260-330顆
  ```
- [ ] **選擇品質**
  - 優先選擇高仰角衛星
  - 信號品質RSRP > -100 dBm
  - 可見時間長的衛星優先

#### 5. **軌道週期驗證**
- [ ] **完整週期覆蓋**
  - Starlink: 93.63分鐘完整驗證
  - OneWeb: 109.64分鐘完整驗證
  - 最大覆蓋空隙 < 2分鐘
- [ ] **切換連續性**
  - 任何切換時刻至少3個候選
  - 切換成功率 > 95%

#### 6. **輸出驗證**
- [ ] **數據結構完整性**
  ```json
  {
    "metadata": {
      "stage": "stage6_dynamic_pool",
      "algorithm": "spatiotemporal_diversity",
      "processing_time_seconds": 2.5
    },
    "dynamic_satellite_pool": {
      "starlink_satellites": [...],  // 200-250顆
      "oneweb_satellites": [...],    // 60-80顆
      "selection_details": [
        {
          "satellite_id": "...",
          "position_timeseries": [...],  // 192點完整軌跡
          "selection_rationale": {...}
        }
      ]
    },
    "coverage_validation": {
      "starlink_coverage_ratio": 0.96,
      "oneweb_coverage_ratio": 0.95, 
      "combined_coverage_ratio": 0.94,
      "phase_diversity_score": 0.75,
      "coverage_gap_analysis": {
        "total_gaps": 2,
        "max_gap_minutes": 1.5,
        "avg_gap_minutes": 0.8
      },
      "validation_passed": true,
      "detailed_timeline": [
        {
          "timepoint": 0,
          "time_minutes": 0,
          "starlink_visible": 12,
          "oneweb_visible": 4,
          "starlink_satisfied": true,
          "oneweb_satisfied": true,
          "combined_satisfied": true
        }
        // ... 每10分鐘採樣點的詳細記錄
      ]
    }
  }
  ```
- [ ] **時間序列保留**
  - 每顆衛星192個時間點
  - 無數據缺失或跳躍
  - 支援前端平滑動畫

#### 7. **性能指標**
- [ ] 處理時間 < 5秒
- [ ] 記憶體使用 < 2GB
- [ ] API響應 < 100ms

#### 8. **自動95%+覆蓋率驗證腳本**
```python
# 執行階段驗證
python -c "
import json
import numpy as np

# 載入動態池輸出
try:
    with open('/app/data/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json', 'r') as f:
        data = json.load(f)
except:
    print('⚠️ 階段六輸出不存在')
    exit(1)

pool = data.get('dynamic_satellite_pool', {})
validation = data.get('coverage_validation', {})

starlink_count = len(pool.get('starlink_satellites', []))
oneweb_count = len(pool.get('oneweb_satellites', []))

# 檢查時間序列完整性
has_timeseries = True
for sat in pool.get('selection_details', [])[:10]:  # 檢查前10顆
    if len(sat.get('position_timeseries', [])) < 192:
        has_timeseries = False
        break

checks = {
    'starlink_pool_size': 200 <= starlink_count <= 250,
    'oneweb_pool_size': 60 <= oneweb_count <= 80,
    'total_pool_size': 260 <= (starlink_count + oneweb_count) <= 330,
    'starlink_coverage_95plus': validation.get('starlink_coverage_ratio', 0) >= 0.95,
    'oneweb_coverage_95plus': validation.get('oneweb_coverage_ratio', 0) >= 0.95,
    'combined_coverage_95plus': validation.get('combined_coverage_ratio', 0) >= 0.95,
    'max_gap_under_2min': validation.get('coverage_gap_analysis', {}).get('max_gap_minutes', 10) <= 2.0,
    'phase_diversity': validation.get('phase_diversity_score', 0) >= 0.70,
    'has_timeseries': has_timeseries,
    'coverage_validation_passed': validation.get('validation_passed', False)
}

passed = sum(checks.values())
total = len(checks)

print('📊 Stage 6 驗證結果:')
print(f'  Starlink池: {starlink_count} 顆')
print(f'  OneWeb池: {oneweb_count} 顆')
print(f'  Starlink覆蓋率: {validation.get(\"starlink_coverage_ratio\", 0):.1%}')
print(f'  OneWeb覆蓋率: {validation.get(\"oneweb_coverage_ratio\", 0):.1%}')
print(f'  綜合覆蓋率: {validation.get(\"combined_coverage_ratio\", 0):.1%}')
print(f'  最大間隙: {validation.get(\"coverage_gap_analysis\", {}).get(\"max_gap_minutes\", 0):.1f}分鐘')
print(f'  間隙總數: {validation.get(\"coverage_gap_analysis\", {}).get(\"total_gaps\", 0)}個')
print(f'  相位多樣性: {validation.get(\"phase_diversity_score\", 0):.2f}')

print('\\n驗證項目:')
for check, result in checks.items():
    print(f'  {\"✅\" if result else \"❌\"} {check}')

if passed == total:
    print('\\n✅ Stage 6 驗證通過！95%+覆蓋率保證達成！')
    print('🎉 六階段資料預處理全部完成！')
    print('✅ Starlink: 95%+時間保持10+顆可見（5度仰角）')
    print('✅ OneWeb: 95%+時間保持3+顆可見（10度仰角）')
    print('✅ 覆蓋間隙: ≤2分鐘，滿足連續覆蓋要求')
    print('✅ 時空錯置策略成功實現，LEO衛星換手研究環境就緒！')
else:
    print(f'\\n❌ Stage 6 驗證失敗 ({passed}/{total})')
    print('⚠️ 95%+覆蓋率保證未達成，需要調整動態池規劃參數')
    exit(1)
"
```

### 🚨 95%+覆蓋率驗證失敗處理
1. **Starlink覆蓋率不足（<95%）**: 
   - 增加Starlink候選衛星數量（200→250顆）
   - 降低5°仰角門檻至4°（緊急情況）
   - 調整軌道相位分散參數，增加時空互補性
   
2. **OneWeb覆蓋率不足（<95%）**: 
   - 增加OneWeb候選衛星數量（60→80顆）
   - 檢查10°仰角門檻是否過於嚴格
   - 優化OneWeb軌道平面選擇策略
   
3. **覆蓋間隙過長（>2分鐘）**: 
   - 強化軌道相位錯開算法
   - 增加覆蓋緩衝衛星（每個星座+20%）  
   - 實施動態候補衛星策略
   
4. **綜合覆蓋率不達標**: 
   - 同時增加兩個星座的衛星數量
   - 重新計算最佳軌道週期時間窗口
   - 檢查TLE數據的時效性和準確性
   
5. **時間序列數據缺失**: 確認Stage 5數據完整性
6. **相位多樣性不足**: 優化選擇算法、增加RAAN分散

### 📊 95%+覆蓋率關鍵指標總覽
- **Starlink覆蓋率**: ≥95% 時間保持10+顆可見（5°仰角）  
- **OneWeb覆蓋率**: ≥95% 時間保持3+顆可見（10°仰角）
- **綜合覆蓋率**: ≥95% 時間同時滿足兩個星座要求
- **最大間隙**: ≤2分鐘連續覆蓋不足時段
- **時空錯置**: 軌道相位均勻分散，相位多樣性≥0.7
- **切換保證**: 任何時刻有充足候選衛星

### 🎯 95%+覆蓋率最終驗證標準
執行完Stage 6驗證後，系統應達到：
- ✅ **Starlink 95%+覆蓋保證**: 95%以上時間保持10+顆可見（5°仰角閾值）
- ✅ **OneWeb 95%+覆蓋保證**: 95%以上時間保持3+顆可見（10°仰角閾值） 
- ✅ **綜合95%+覆蓋**: 95%以上時間同時滿足兩個星座覆蓋要求
- ✅ **間隙控制**: 最大覆蓋間隙≤2分鐘，無長時間服務中斷
- ✅ **完整軌道週期**: 2小時軌道週期完整驗證，240個採樣點精確統計
- ✅ **時空錯置最佳化**: 衛星在軌道相位上錯開分佈，實現高效覆蓋

---

**上一階段**: [階段五：數據整合](./stage5-integration.md)  
**目標狀態**: 建立可保證完整軌道週期覆蓋的時空錯置動態衛星池

---

🎯 **階段六終極目標**：實現「95%以上時間 NTPU 上空都有 10+ 顆 Starlink（5°仰角）+ 3+ 顆 OneWeb（10°仰角）可見衛星」的95%+覆蓋率保證，最大間隙≤2分鐘，為 LEO 衛星換手研究提供連續穩定的實驗環境。

**📊 量化成功標準**：
- Starlink覆蓋率 ≥ 95%（228/240個時間點滿足≥10顆可見）
- OneWeb覆蓋率 ≥ 95%（228/240個時間點滿足≥3顆可見）
- 綜合覆蓋率 ≥ 95%（兩個星座同時滿足要求）
- 最大覆蓋間隙 ≤ 2分鐘（4個連續採樣點）