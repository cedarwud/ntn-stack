# 🛰️ 階段六：動態衛星池規劃

[🔄 返回數據流程導航](../README.md) > 階段六

## 📖 階段概述

**設計目標**：建立智能動態衛星池，確保 NTPU 觀測點上空任何時刻都有足夠的可見衛星，支援連續不間斷的衛星切換研究

### 🎯 核心目標
- **Starlink 持續覆蓋**：任何時刻保證 10-15 顆可見衛星（仰角 ≥10°）
- **OneWeb 持續覆蓋**：任何時刻保證 3-6 顆可見衛星（仰角 ≥10°）
- **時間覆蓋率**：100% 時間滿足上述覆蓋要求
- **切換連續性**：確保衛星切換時永遠有候選衛星可用

### 📊 預期輸出
**衛星池規模**：動態選擇最優衛星子集（預估 300-500 顆）
**時間序列**：完整軌道週期數據（30秒間隔）
**覆蓋保證**：全時段無覆蓋空洞
**處理時間**：< 5 秒

## 🎯 演算法設計要求

### 時空優化策略
- **軌道相位分散**：選擇不同軌道相位的衛星，確保覆蓋互補
- **時間窗口重疊**：優化衛星可見時間窗口的重疊分佈
- **信號品質權衡**：在覆蓋連續性和信號品質間取得平衡
- **動態調整機制**：根據時間變化動態調整衛星池組成

### 覆蓋驗證指標
- **最小可見衛星數**：每個時間點的最低保證
- **覆蓋連續性指標**：無中斷時間百分比
- **切換可行性評分**：可用候選衛星數量
- **服務質量保證**：RSRP、RSRQ、SINR 門檻達成率

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
    "starlink_satellites": ["STARLINK-1234", "..."],  // 120顆
    "oneweb_satellites": ["ONEWEB-0123", "..."],      // 36顆
    "total_count": 156,
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

## 📈 成功標準

### 必須達成的指標
1. **覆蓋率 ≥ 99%**：99%以上時間滿足最小衛星數要求
2. **無服務中斷**：不存在完全無衛星覆蓋的時段
3. **切換連續性**：任何切換時刻至少有3個候選衛星
4. **數據完整性**：每顆衛星包含完整軌道週期數據

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

### 系統整合效益
1. **前端視覺化**：支援流暢的 3D 衛星軌跡動畫
2. **API 效能**：預計算數據大幅降低即時運算負載
3. **研究彈性**：支援不同時間段的切換場景模擬
4. **數據可靠性**：基於真實 TLE 數據的準確軌道預測

---

**上一階段**: [階段五：數據整合](./stage5-integration.md)  
**目標狀態**: 建立可保證 100% 時間覆蓋的智能動態衛星池

---

🎯 **階段六終極目標**：實現「任何時刻 NTPU 上空都有 10-15 顆 Starlink + 3-6 顆 OneWeb 可見衛星」的完美覆蓋，為 LEO 衛星切換研究提供可靠的實驗環境。