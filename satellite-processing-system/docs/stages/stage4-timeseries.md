# 📊 階段四：時間序列預處理

[🔄 返回數據流程導航](../README.md) > 階段四

## 📖 階段概述

**目標**：將信號分析結果轉換為前端可用的時間序列數據  
**輸入**：階段三的信號品質數據（~200MB）  
**輸出**：前端時間序列數據（~60-75MB）  
**處理對象**：391顆衛星的時間序列最佳化  
**處理時間**：約 1-2 分鐘

### 🎯 @doc/todo.md 對應實現
本階段支援以下需求：
- 🔧 **數據最佳化**: 為前端動畫和強化學習可視化提供高效數據格式
- ⚡ **性能優化**: 壓縮數據大小70%，支援60 FPS流暢渲染
- 📊 **時間序列完整性**: 保持軌道週期數據完整，支援動態覆蓋驗證
- 🤖 **強化學習支援**: 保留仰角數據作為狀態空間關鍵信息，支援訓練數據生成

## 🎯 處理目標

### 前端動畫需求
- **時間軸控制**：支援 1x-60x 倍速播放
- **衛星軌跡**：平滑的軌道動畫路徑
- **信號變化**：即時信號強度視覺化
- **換手事件**：動態換手決策展示

### 數據最佳化需求
- **檔案大小**：壓縮至前端可接受範圍
- **載入速度**：支援快速初始化
- **動畫流暢**：60 FPS 渲染需求
- **記憶體效率**：瀏覽器記憶體友善

## 🏗️ 處理架構

### 主要實現位置
```bash
# 時間序列預處理器
/netstack/src/stages/timeseries_preprocessing_processor.py
├── TimeseriesPreprocessingProcessor.load_signal_analysis_output()      # 載入信號數據
├── TimeseriesPreprocessingProcessor.convert_to_enhanced_timeseries()   # 增強時間序列轉換
├── TimeseriesPreprocessingProcessor.save_enhanced_timeseries()         # 保存增強數據
└── TimeseriesPreprocessingProcessor.process_timeseries_preprocessing() # 完整流程執行

# Pure Cron 支援模組
/netstack/src/services/animation/cron_animation_builder.py
├── CronAnimationBuilder.build_satellite_tracks()         # 衛星軌跡建構
├── CronAnimationBuilder.build_signal_timelines()         # 信號時間線
└── CronAnimationBuilder.build_handover_sequences()       # 換手序列
```

## 🔄 Pure Cron 驅動架構實現

### Cron-First 設計理念
- **定時觸發**：每 6 小時自動更新
- **無依賴啟動**：容器啟動時數據立即可用
- **增量更新**：僅在 TLE 變更時重新計算

### Cron 任務配置
```bash
# /etc/cron.d/satellite-data-update
0 2,8,14,20 * * * root /scripts/incremental_data_processor.sh >/var/log/cron-satellite.log 2>&1
```

## 🚨 **學術級時間序列處理標準遵循** (Grade A/B 等級)

### 🟢 **Grade A 強制要求：數據完整性優先**

#### 時間序列精度保持原則
- **時間解析度保持**：嚴格維持30秒間隔，不得任意減少採樣點
- **軌道週期完整性**：保持完整的96分鐘軌道週期數據
- **精度不降級**：座標精度必須足以支持學術研究分析

#### 🟡 **Grade B 可接受：基於科學原理的優化**

#### 座標系統轉換 (基於標準算法)
- **WGS84地心座標 → 地理座標**：使用標準WGS84橢球體參數
- **時間系統同步**：維持GPS時間基準一致性
- **精度標準**：座標精度基於測量不確定度分析

#### 🔴 **Grade C 嚴格禁止項目** (零容忍)
- **❌ 任意數據點減量**：如"720點減至360點"等未經驗證的減少
- **❌ 任意壓縮比例**：如"70%壓縮率"等沒有科學依據的目標
- **❌ 信號強度"正規化"**：可能失真原始物理測量值
- **❌ 量化級數簡化**：如"16級量化"等可能導致精度損失
- **❌ 任意精度截斷**：如"小數點後4位"等未經分析的精度設定

### 📊 **替代方案：基於科學原理的數據處理**

#### 學術級數據保持策略
```python
# ✅ 正確：基於數據完整性和科學精度要求
def preserve_academic_data_integrity(raw_data):
    """保持學術級數據完整性的時間序列處理"""
    
    processed = {}
    
    for satellite_id, data in raw_data.items():
        # 保持原始時間解析度 (不減量)
        full_timeseries = data['position_timeseries']  # 保持192個時間點
        
        # 精確座標系統轉換（基於WGS84標準）
        geo_coordinates = wgs84_eci_to_geographic_conversion(
            full_timeseries,
            reference_ellipsoid="WGS84"  # 標準橢球體
        )
        
        # 保持原始信號值（不正規化）
        original_rsrp = data['signal_quality']['rsrp_timeseries']  # 保持dBm單位
        
        processed[satellite_id] = {
            'position_timeseries': geo_coordinates,  # 完整時間序列
            'signal_timeseries': original_rsrp,     # 原始信號值
            'academic_metadata': {
                'time_resolution_sec': 30,           # 標準時間解析度
                'coordinate_precision': calculate_required_precision(),
                'signal_unit': 'dBm',                # 保持物理單位
                'reference_time': data['tle_epoch']  # TLE時間基準
            }
        }
    
    return processed

# ❌ 錯誤：任意數據處理
def arbitrary_data_processing():
    target_points = 360      # 任意減量
    compression_ratio = 0.7  # 任意壓縮
    quantization_levels = 16 # 任意量化
```

#### 前端性能優化的學術級方案
```python
# ✅ 正確：在保持數據完整性前提下的性能優化
def academic_frontend_optimization(full_data):
    """在不犧牲學術精度的前提下優化前端性能"""
    
    # 1. 分層數據結構（不減少數據）
    optimization = {
        'full_precision_data': full_data,           # 完整精度數據
        'display_optimized_data': {                 # 顯示優化（不影響計算）
            'coordinate_display_precision': 3,       # 僅影響顯示，不影響計算
            'time_display_format': 'iso_string',     # 顯示格式化
        },
        'streaming_strategy': {                     # 漸進式載入策略
            'batch_size': calculate_optimal_batch_size(),  # 基於網路延遲分析
            'prefetch_strategy': 'orbital_priority'        # 基於軌道可見性優先級
        }
    }
    
    return optimization

# 2. 基於測量不確定度的精度分析
def calculate_required_precision():
    """基於測量不確定度計算所需精度"""
    sgp4_position_uncertainty_km = 1.0    # SGP4典型精度
    required_coordinate_precision = calculate_precision_from_uncertainty(
        uncertainty_km=sgp4_position_uncertainty_km
    )
    return required_coordinate_precision
```

## 🚨 強制運行時檢查 (新增)

**2025-09-09 重大強化**: 新增階段四專門的運行時架構完整性檢查維度。

### 🔴 零容忍運行時檢查 (任何失敗都會停止執行)

#### 1. 時間序列處理器類型強制檢查
```python
# 🚨 嚴格檢查實際使用的時間序列處理器類型
assert isinstance(processor, TimeseriesPreprocessingProcessor), f"錯誤時間序列處理器: {type(processor)}"
assert isinstance(animation_builder, CronAnimationBuilder), f"錯誤動畫建構器: {type(animation_builder)}"
# 原因: 確保使用完整的時間序列預處理器，而非簡化版本
# 影響: 錯誤處理器可能導致數據壓縮不當或丟失關鍵信息
```

#### 2. 輸入數據完整性檢查  
```python
# 🚨 強制檢查輸入數據來自階段三的完整格式
assert 'signal_analysis_results' in input_data, "缺少信號分析結果"
assert input_data['metadata']['total_analyzed'] > 1000, f"分析衛星數量不足: {input_data['metadata']['total_analyzed']}"
for constellation in ['starlink', 'oneweb']:
    constellation_data = input_data['signal_analysis_results'][constellation]
    assert len(constellation_data) > 0, f"{constellation}信號數據為空"
    for satellite in constellation_data[:3]:
        assert 'signal_quality' in satellite, "缺少信號品質數據"
        assert 'event_potential' in satellite, "缺少3GPP事件潛力數據"
# 原因: 確保階段三的信號分析數據格式正確傳遞
# 影響: 不完整的輸入會導致時間序列轉換錯誤或數據丟失
```

#### 3. 時間序列完整性強制檢查
```python
# 🚨 強制檢查時間序列數據完整性
for satellite_result in output_results:
    timeseries = satellite_result['track_points']
    assert len(timeseries) >= 192, f"時間序列長度不足: {len(timeseries)}"
    assert all('time' in point for point in timeseries), "時間點數據不完整"
    assert all('elevation_deg' in point for point in timeseries), "缺少仰角數據"
    assert all(point['time'] >= 0 for point in timeseries), "時間序列順序錯誤"
# 原因: 確保時間序列數據保持軌道週期完整性
# 影響: 不完整的時間序列會影響前端動畫和強化學習訓練
```

#### 4. 學術標準數據精度檢查
```python
# 🚨 強制檢查數據精度符合學術標準
for satellite_data in output_results:
    academic_metadata = satellite_data.get('academic_metadata', {})
    assert academic_metadata.get('time_resolution_sec') == 30, "時間解析度被異常修改"
    assert academic_metadata.get('signal_unit') == 'dBm', "信號單位被異常修改"
    
    # 檢查座標精度
    track_points = satellite_data['track_points']
    lat_precision = check_decimal_precision([p['lat'] for p in track_points[:10]])
    lon_precision = check_decimal_precision([p['lon'] for p in track_points[:10]])
    assert lat_precision >= 3, f"緯度精度不足: {lat_precision}位小數"
    assert lon_precision >= 3, f"經度精度不足: {lon_precision}位小數"
# 原因: 確保數據處理不降低學術研究所需精度
# 影響: 精度不足會影響學術研究的可信度和準確性
```

#### 5. 前端性能優化合規檢查
```python
# 🚨 強制檢查性能優化不犧牲數據完整性
optimization_config = processor.get_optimization_config()
assert optimization_config.get('preserve_full_data') == True, "數據完整性保護被關閉"
assert 'arbitrary_compression' not in optimization_config, "檢測到任意壓縮配置"
assert 'data_quantization' not in optimization_config, "檢測到數據量化處理"

# 檢查輸出文件大小合理性
output_file_sizes = get_output_file_sizes()
for constellation, size_mb in output_file_sizes.items():
    expected_range = get_expected_file_size_range(constellation)
    assert expected_range[0] <= size_mb <= expected_range[1], \
        f"{constellation}輸出文件大小異常: {size_mb}MB (預期: {expected_range}MB)"
# 原因: 確保性能優化基於科學原理，不是任意壓縮
# 影響: 不當優化會導致數據丟失或前端功能異常
```

#### 6. 無簡化處理零容忍檢查
```python
# 🚨 禁止任何形式的簡化時間序列處理
forbidden_processing_modes = [
    "arbitrary_downsampling", "fixed_compression_ratio", "uniform_quantization",
    "simplified_coordinates", "mock_timeseries", "estimated_positions"
]
for mode in forbidden_processing_modes:
    assert mode not in str(processor.__class__).lower(), \
        f"檢測到禁用的簡化處理: {mode}"
    assert mode not in processor.get_processing_methods(), \
        f"檢測到禁用的處理方法: {mode}"
```

### 📋 Runtime Check Integration Points

**檢查時機**: 
- **初始化時**: 驗證時間序列處理器和動畫建構器類型
- **輸入處理時**: 檢查階段三數據完整性和格式正確性
- **數據轉換時**: 監控時間序列完整性和精度保持
- **優化處理時**: 驗證優化策略不犧牲數據完整性
- **輸出前**: 嚴格檢查學術標準合規和文件大小合理性

**失敗處理**:
- **立即停止**: 任何runtime check失敗都會立即終止執行
- **精度檢查**: 驗證學術級數據精度要求
- **完整性驗證**: 檢查時間序列和信號數據完整性
- **無降級處理**: 絕不允許使用簡化處理或任意壓縮

### 🛡️ 實施要求

- **學術標準強制執行**: 數據處理必須100%符合Grade A學術級要求
- **時間序列完整性**: 必須保持完整的軌道週期和時間解析度
- **精度不降級原則**: 座標和信號精度不得低於學術研究要求
- **跨階段數據一致性**: 確保與階段三輸出數據格式100%兼容
- **性能影響控制**: 運行時檢查額外時間開銷 <2%

## 📁 輸出檔案結構

### timeseries_preprocessing_outputs/ 目錄
```bash
/app/data/timeseries_preprocessing_outputs/
├── animation_enhanced_starlink.json    # Starlink動畫數據 (~45MB)
├── animation_enhanced_oneweb.json      # OneWeb動畫數據 (~15-20MB)
└── conversion_statistics.json          # 轉換統計數據
```

### JSON 數據格式
```json
{
  "metadata": {
    "constellation": "starlink",
    "satellite_count": 358,
    "time_range": {
      "start": "2025-08-14T00:00:00Z",
      "end": "2025-08-14T06:00:00Z"
    },
    "animation_fps": 60,
    "total_frames": 21600
  },
  "satellites": {
    "STARLINK-1234": {
      "track_points": [
        {"time": 0, "lat": 24.944, "lon": 121.371, "alt": 550, "elevation_deg": 45.2, "visible": true},
        // ... 360個優化點，現在包含仰角數據供強化學習使用
      ],
      "signal_timeline": [
        {"time": 0, "rsrp_normalized": 0.75, "quality_color": "#00FF00"},
        // ... 對應信號點
      ],
      "summary": {
        "max_elevation_deg": 85.5,
        "total_visible_time_min": 180,
        "avg_signal_quality": "high"
      }
    }
  }
}
```

## ⚙️ 最佳化配置

### 時間序列參數
```python
TIMESERIES_CONFIG = {
    'target_points_per_satellite': 360,    # 從720減至360點
    'coordinate_precision': 4,             # 座標小數位數
    'signal_quantization_levels': 16,      # 信號量化級數
    'animation_target_fps': 60,            # 目標幀率
    'compression_ratio': 0.4               # 目標壓縮比
}
```

### 前端載入最佳化
```javascript
// 前端數據載入策略
const loadTimeseriesData = async (constellation) => {
  // 漸進式載入
  const metadata = await fetch(`/data/enhanced_timeseries/${constellation}_metadata.json`);
  
  // 按需載入衛星數據
  const batchSize = 50;  // 每批50顆衛星
  for (let batch = 0; batch < satelliteCount / batchSize; batch++) {
    await loadSatelliteBatch(constellation, batch);
  }
};
```

## 📖 **學術標準參考文獻**

### 座標系統轉換標準
- **WGS84座標系統**: World Geodetic System 1984 - 全球標準座標系統
- **IERS Conventions (2010)**: 國際地球自轉和參考系統服務 - 座標轉換標準
- **ITU-R P.834**: 地球站與衛星軌道計算中的座標系統效應

### 時間系統標準
- **GPS Time Standard**: GPS時間系統規範 - 時間同步基準
- **UTC Time Coordination**: 協調世界時標準 - 時間轉換規範
- **IERS Technical Note No. 36**: 地球定向參數和時間系統

### 數據精度與不確定度
- **ISO/IEC Guide 98-3**: 測量不確定度表達指南
- **NIST Special Publication 811**: 度量單位使用指南
- **IEEE Std 754-2019**: 浮點算術標準 - 數值精度標準

### 軌道精度標準
- **SGP4/SDP4精度分析**: AIAA 2006-6753 - 軌道計算精度評估
- **NASA/TP-2010-216239**: 軌道確定精度分析
- **衛星追蹤精度**: USSTRATCOM軌道精度標準

### 時間序列數據處理
- **數字信號處理**: Oppenheim & Schafer - 時間序列處理理論
- **測量數據處理**: ISO 5725 - 測量方法和結果的準確度
- **科學數據管理**: 數據血統追蹤和完整性保持標準

## 📈 性能指標

### 處理性能
- **數據減量率**：65% (720點 → 360點)
- **檔案大小減少**：70% (200MB → 60-75MB)
- **載入速度提升**：3倍 (前端首次載入)
- **記憶體使用**：瀏覽器端 < 150MB

### 動畫品質
- **幀率穩定性**：60 FPS 穩定渲染
- **軌跡平滑度**：無跳躍，平滑插值
- **時間同步**：所有衛星時間戳精確同步
- **視覺保真度**：保持 95% 視覺資訊

## 🚨 故障排除

### 常見問題

1. **動畫卡頓**
   - 檢查：數據點密度
   - 解決：增加 target_points_per_satellite

2. **檔案過大**
   - 檢查：壓縮比設定
   - 解決：調高 compression_ratio

3. **時間同步問題**
   - 檢查：時間戳對齊
   - 解決：重新執行時間對齊處理

### 診斷指令

```bash
# 檢查輸出檔案大小
du -h /app/data/enhanced_timeseries/

# 驗證JSON格式
python -c "
import json
with open('/app/data/enhanced_timeseries/animation_enhanced_starlink.json') as f:
    data = json.load(f)
    print(f'✅ JSON格式正確，包含 {len(data["satellites"])} 顆衛星')
"

# 測試前端載入性能
curl -w '%{time_total}s' -o /dev/null -s http://localhost:5173/data/enhanced_timeseries/animation_enhanced_starlink.json
```

## ✅ 階段驗證標準

### 🎯 Stage 4 完成驗證檢查清單

#### 1. **輸入驗證**
- [ ] Stage 3信號分析結果完整
  - 接收約1,100-1,400顆衛星數據
  - 包含信號指標和3GPP事件 (✅ 完全符合TS 38.331標準)
  - 時間序列數據連續無斷點

#### 2. **數據壓縮驗證**
- [ ] **檔案大小優化**
  ```
  目標範圍:
  - Starlink: 30-40MB
  - OneWeb: 20-30MB
  - 總計: 50-70MB
  壓縮率: > 70%
  ```
- [ ] **時間解析度保持**
  - 30秒間隔不變
  - 96分鐘軌道數據完整
  - 192個時間點保留

#### 3. **前端優化驗證**
- [ ] **數據結構優化**
  - 座標精度: 小數點後3位
  - 仰角精度: 小數點後1位
  - 冗餘字段移除
- [ ] **動畫流暢度要求**
  - 支援60 FPS渲染
  - 無跳幀現象
  - 軌跡連續平滑

#### 4. **輸出驗證**
- [ ] **JSON數據格式**
  ```json
  {
    "metadata": {
      "stage": "stage4_timeseries",
      "total_frames": 192,
      "time_resolution": 30,
      "compression_ratio": 0.73
    },
    "animation_data": {
      "starlink": {
        "frame_count": 192,
        "satellites": [...]
      },
      "oneweb": {
        "frame_count": 192,
        "satellites": [...]
      }
    }
  }
  ```
- [ ] **載入性能**
  - 初始載入 < 2秒
  - 記憶體占用 < 200MB
  - 瀏覽器相容性

#### 5. **性能指標**
- [ ] 處理時間 < 1分鐘
- [ ] 輸出檔案 < 100MB總計
- [ ] 壓縮率 > 70%

#### 6. **自動驗證腳本**
```python
# 執行階段驗證
python -c "
import json
import os

# 檢查輸出檔案
output_dir = '/app/data/timeseries_preprocessing_outputs/'
files = {
    'starlink': f'{output_dir}starlink_enhanced.json',
    'oneweb': f'{output_dir}oneweb_enhanced.json'
}

checks = {}
total_size = 0

for constellation, file_path in files.items():
    if os.path.exists(file_path):
        size_mb = os.path.getsize(file_path) / (1024*1024)
        total_size += size_mb
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        frame_count = len(data.get('frames', []))
        sat_count = len(data.get('satellites', []))
        
        checks[f'{constellation}_exists'] = True
        checks[f'{constellation}_size_ok'] = size_mb < 50
        # 星座特定幀數檢查 (修正版)
        expected_frames = 192 if constellation == 'starlink' else 218 if constellation == 'oneweb' else None
        checks[f'{constellation}_frames'] = frame_count == expected_frames if expected_frames else False
        checks[f'{constellation}_has_sats'] = sat_count > 0
    else:
        print(f'⚠️ {constellation} 檔案不存在')

checks['total_size_ok'] = total_size < 100
checks['compression_achieved'] = total_size < 100  # 原始 > 300MB

passed = sum(checks.values())
total = len(checks)

print('📊 Stage 4 驗證結果:')
print(f'  總檔案大小: {total_size:.1f} MB')
print(f'  壓縮率: {(1 - total_size/300)*100:.1f}%')

for check, result in checks.items():
    print(f'  {\"✅\" if result else \"❌\"} {check}')

if passed == total:
    print('✅ Stage 4 驗證通過！')
else:
    print(f'❌ Stage 4 驗證失敗 ({passed}/{total})')
    exit(1)
"
```

### 🚨 驗證失敗處理
1. **檔案過大**: 增加壓縮、減少精度
2. **時間點缺失**: 檢查數據完整性
3. **載入過慢**: 優化JSON結構、考慮分頁載入

### 📊 關鍵指標
- **壓縮效率**: 70%以上壓縮率
- **前端友善**: < 100MB總大小
- **動畫流暢**: 192點完整軌跡

---
**上一階段**: [階段三：信號分析](./stage3-signal.md)  
**下一階段**: [階段五：數據整合](./stage5-integration.md)  
**相關文檔**: [Pure Cron架構](../data_processing_flow.md#pure-cron驅動架構)
