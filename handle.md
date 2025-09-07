# 六階段程式手動執行指南

## 概述
本指南說明如何手動單獨執行NetStack LEO衛星六階段數據處理管道中的每個階段，以及如何判斷執行是否成功。

## 執行環境
- 確保NetStack容器正在運行：`make status`
- 使用Docker exec進入容器執行：`docker exec netstack-api [command]`

---

## 階段一：軌道計算

### 輸入檔案來源
- **TLE數據**: 內建衛星軌道數據 (8791顆衛星)
  - Starlink: 8140顆
  - OneWeb: 651顆
- **觀測座標**: NTPU (24.9441667°N, 121.3713889°E, 50m)

### 執行命令
```bash
docker exec netstack-api python /app/src/stages/orbital_calculation_processor.py
```

### 清理命令
```bash
# 單一階段清理
docker exec netstack-api python -c "
from shared_core.cleanup_manager import auto_cleanup
result = auto_cleanup(current_stage=1)
print(f'清理完成: {result}')
"
```

### 產出檔案列表
✅ **直接輸出檔案** (統一輸出模式):
```bash
/app/data/tle_orbital_calculation_output.json  # 主輸出 (~1.4GB)
```

✅ **驗證快照**:
```bash
/app/data/validation_snapshots/stage1_validation.json
```

### 成功執行標準
✅ **輸出檔案檢查**：
```bash
docker exec netstack-api ls -la /app/data/tle_orbital_calculation_output.json
# 應該包含：
# - tle_orbital_calculation_output.json (大約 1.4GB)
# - 8791顆衛星數據 (8140 Starlink + 651 OneWeb)
```

✅ **驗證快照檢查**：
```bash
docker exec netstack-api cat /app/data/validation_snapshots/stage1_validation.json
# 應該顯示：
# - "status": "completed"
# - "validation": { "passed": true }
# - 關鍵指標包含總衛星數約8791顆
```

✅ **日誌檢查標準**：
- `✅ SGP4軌道計算完成: 8791 顆衛星`
- `✅ Stage 1 驗證快照已保存`
- 處理時間應在1-3分鐘內

---

## 階段二：智能過濾

### 輸入檔案來源
- **階段一輸出**: `/app/data/tle_orbital_calculation_output.json`
  - 8791顆衛星的軌道數據
- **仰角門檻配置**: 10°標準門檻 (來自統一配置系統)

### 執行命令
```bash
docker exec netstack-api python /app/src/stages/intelligent_filtering_processor.py
```

### 清理命令
```bash
# 單一階段清理
docker exec netstack-api python -c "
from shared_core.cleanup_manager import auto_cleanup
result = auto_cleanup(current_stage=2)
print(f'清理完成: {result}')
"
```

### 產出檔案列表
✅ **直接輸出檔案** (統一輸出模式):
```bash
/app/data/intelligent_filtered_output.json       # 主輸出 (~1.1GB)
/app/data/satellite_visibility_filtered_output.json  # 可見性數據 (~1.1GB)
```

✅ **驗證快照**:
```bash
/app/data/validation_snapshots/stage2_validation.json
```

### 成功執行標準
✅ **輸出檔案檢查**：
```bash
docker exec netstack-api ls -la /app/data/intelligent_filtered_output.json
# 應該包含：
# - intelligent_filtered_output.json (約 1.1GB)
# - 約3101顆可見衛星 (2899 Starlink + 202 OneWeb)
```

✅ **驗證快照檢查**：
```bash
docker exec netstack-api cat /app/data/validation_snapshots/stage2_validation.json | jq '.keyMetrics'
# 應該顯示：
# - "輸入衛星": 8791
# - "可見衛星": 3101
# - "過濾率": "35.3%"
```

✅ **日誌檢查標準**：
- `✅ NTPU可見性過濾完成: 3101/8791 顆衛星可見`
- `📊 過濾統計: 35.3% 可見率`
- 使用10°仰角門檻標準

---

## 階段三：信號品質分析

### 輸入檔案來源
- **階段二輸出**: `/app/data/satellite_visibility_filtered_output.json`
  - 3101顆可見衛星數據
- **ITU-R P.618標準**: 信號強度計算參數
- **3GPP NTN事件模型**: A4/A5/D2事件檢測邏輯

### 執行命令
```bash
docker exec netstack-api python /app/src/stages/signal_analysis_processor.py
```

### 清理命令
```bash
# 單一階段清理
docker exec netstack-api python -c "
from shared_core.cleanup_manager import auto_cleanup
result = auto_cleanup(current_stage=3)
print(f'清理完成: {result}')
"
```

### 產出檔案列表
✅ **直接輸出檔案** (統一輸出模式):
```bash
/app/data/signal_event_analysis_output.json     # 主輸出 (~1.1GB)
/app/data/signal_quality_analysis_output.json   # 信號品質數據 (~1.1GB)
```

✅ **驗證快照**:
```bash
/app/data/validation_snapshots/stage3_validation.json
```

### 成功執行標準
✅ **輸出檔案檢查**：
```bash
docker exec netstack-api ls -la /app/data/signal_event_analysis_output.json
# 應該包含：
# - signal_event_analysis_output.json (約 1.1GB)
# - 3101顆衛星的信號品質分析數據
```

✅ **驗證快照檢查**：
```bash
docker exec netstack-api cat /app/data/validation_snapshots/stage3_validation.json | jq '.validation.passed'
# 應該顯示：true
```

✅ **日誌檢查標準**：
- `✅ 信號品質分析完成: 3101 顆衛星`
- `📊 3GPP NTN事件檢測: A4/A5/D2事件`
- `✅ RSRP計算完成 (ITU-R P.618標準)`

---

## 階段四：時間序列預處理

### 輸入檔案來源
- **階段三輸出**: `/app/data/signal_quality_analysis_output.json`
  - 3101顆衛星的信號品質分析結果
- **時間序列配置**: 192點時間序列 (96分鐘軌道，30秒間隔)

### 執行命令
```bash
docker exec netstack-api python /app/src/stages/timeseries_preprocessing_processor.py
```

### 清理命令
```bash
# 單一階段清理  
docker exec netstack-api python -c "
from shared_core.cleanup_manager import auto_cleanup
result = auto_cleanup(current_stage=4)
print(f'清理完成: {result}')
"
```

### 產出檔案列表
✅ **直接輸出檔案** (統一輸出模式):
```bash
/app/data/animation_enhanced_starlink.json  # Starlink動畫數據 (~166MB)
/app/data/animation_enhanced_oneweb.json    # OneWeb動畫數據 (~11MB)
/app/data/conversion_statistics.json       # 轉換統計資料
```

✅ **驗證快照**:
```bash
/app/data/validation_snapshots/stage4_validation.json
```

### 成功執行標準
✅ **輸出檔案檢查**：
```bash
docker exec netstack-api ls -la /app/data/animation_enhanced_*.json
# 應該包含：
# - animation_enhanced_starlink.json (~166MB)
# - animation_enhanced_oneweb.json (~11MB)
# - conversion_statistics.json
```

✅ **驗證快照檢查**：
```bash
docker exec netstack-api cat /app/data/validation_snapshots/stage4_validation.json | jq '.keyMetrics'
# 應該顯示：
# - "處理總數": 3101
# - "成功轉換": 3101
# - "轉換率": "100.0%"
```

✅ **日誌檢查標準**：
- `🎯 時間序列轉換完成: 3101/3101 顆衛星成功轉換`
- `💾 保存增強時間序列數據...`
- `📁 時間序列預處理數據已保存`

---

## 階段五：數據整合

### 輸入檔案來源
- **階段四輸出**: `/app/data/animation_enhanced_starlink.json` & `/app/data/animation_enhanced_oneweb.json`
  - 3101顆衛星的動畫時間序列數據
- **PostgreSQL連接**: netstack-postgres 數據庫
- **分層仰角配置**: 5°、10°、15° 三個門檻層級

### 執行命令
```bash
docker exec netstack-api python /app/src/stages/data_integration_processor.py
```

### 清理命令
```bash
# 單一階段清理
docker exec netstack-api python -c "
from shared_core.cleanup_manager import auto_cleanup
result = auto_cleanup(current_stage=5)
print(f'清理完成: {result}')
"
```

### 產出檔案列表
✅ **直接輸出檔案** (統一輸出模式):
```bash
/app/data/data_integration_output.json  # 主整合輸出 (~205MB)
/app/data/integrated_data_output.json   # 備用整合數據
```

✅ **多檔案子目錄** (合理的組織結構):
```bash
# 分層仰角數據 (依功能分類)
/app/data/layered_elevation_enhanced/elevation_5deg/starlink_with_3gpp_events.json
/app/data/layered_elevation_enhanced/elevation_5deg/oneweb_with_3gpp_events.json
/app/data/layered_elevation_enhanced/elevation_10deg/starlink_with_3gpp_events.json
/app/data/layered_elevation_enhanced/elevation_10deg/oneweb_with_3gpp_events.json
/app/data/layered_elevation_enhanced/elevation_15deg/starlink_with_3gpp_events.json
/app/data/layered_elevation_enhanced/elevation_15deg/oneweb_with_3gpp_events.json

# 切換場景數據
/app/data/handover_scenarios/a4_events_enhanced.json
/app/data/handover_scenarios/a5_events_enhanced.json  
/app/data/handover_scenarios/d2_events_enhanced.json
/app/data/handover_scenarios/best_handover_windows.json

# 信號品質分析
/app/data/signal_quality_analysis/signal_heatmap_data.json
/app/data/signal_quality_analysis/quality_metrics_summary.json
/app/data/signal_quality_analysis/constellation_comparison.json

# 處理緩存
/app/data/processing_cache/sgp4_calculation_cache.json
/app/data/processing_cache/filtering_results_cache.json
/app/data/processing_cache/gpp3_event_cache.json

# 狀態文件
/app/data/status_files/stage5_processing_status.json
/app/data/status_files/postgresql_integration_status.json
/app/data/status_files/mixed_storage_validation.json
/app/data/status_files/data_quality_report.json
```

✅ **驗證快照**:
```bash
/app/data/validation_snapshots/stage5_validation.json
```

### 成功執行標準
✅ **輸出檔案檢查**：
```bash
docker exec netstack-api ls -la /app/data/data_integration_output.json
# 檔案大小應約205MB

# 檢查分層仰角數據
docker exec netstack-api ls -la /app/data/layered_elevation_enhanced/
# 應包含5°、10°、15°三個仰角層級的數據
```

✅ **驗證快照檢查**：
```bash
docker exec netstack-api cat /app/data/validation_snapshots/stage5_validation.json | jq '.keyMetrics'
# 應該顯示：
# - "總衛星數": 3101
# - "成功整合": 3101
# - "Starlink整合": 2899
# - "OneWeb整合": 202
```

✅ **日誌檢查標準**：
- `📊 PostgreSQL整合完成: 11362 筆記錄`
- `✅ 生成分層仰角數據 (5°/10°/15°)`
- `🔍 混合存儲驗證: verified`

---

## 階段六：動態池規劃

### 輸入檔案來源
- **階段五輸出**: `/app/data/data_integration_output.json`
  - 3101顆衛星的完整整合數據
- **優化算法**: 模擬退火演算法配置  
- **池規劃參數**: Starlink池250顆、OneWeb池80顆

### 執行命令
```bash
docker exec netstack-api python -c "
from stages.dynamic_pool_planner import EnhancedDynamicPoolPlanner
config = {'input_dir': '/app/data', 'output_dir': '/app/data'}
planner = EnhancedDynamicPoolPlanner(config)
result = planner.process_dynamic_pool_planning({}, save_output=True)
print('✅ 階段六執行完成')
"
```

### 清理命令
```bash
# 單一階段清理
docker exec netstack-api python -c "
from shared_core.cleanup_manager import auto_cleanup
result = auto_cleanup(current_stage=6)
print(f'清理完成: {result}')
"
```

### 產出檔案列表
✅ **直接輸出檔案** (統一輸出模式):
```bash
/app/data/enhanced_dynamic_pools_output.json    # 主池規劃輸出 (~13MB)
/app/data/dynamic_pools.json                    # API使用的池數據
/app/data/stage6_dynamic_pool.json             # 階段六專用輸出
```

✅ **驗證快照**:
```bash
/app/data/validation_snapshots/stage6_validation.json
```

### 成功執行標準
✅ **輸出檔案檢查**：
```bash
docker exec netstack-api ls -la /app/data/enhanced_dynamic_pools_output.json
# 檔案應存在且大小 > 1MB
```

✅ **驗證快照檢查**：
```bash
docker exec netstack-api cat /app/data/validation_snapshots/stage6_validation.json | jq '.stage'
# 應該顯示：6
```

✅ **日誌檢查標準**：
- `✅ Stage 6 驗證快照已保存`
- `✅ 轉換完成: 3101 個增強衛星候選`
- `🚀 增強動態池規劃器準備就緒`

---

## 完整管道執行

### 階段1-3執行
```bash
docker exec netstack-api python /app/scripts/run_three_stages.py
```

### 階段4-6執行
```bash
docker exec netstack-api python /app/scripts/run_stages_4_to_6.py
```

### 完整六階段執行
```bash
docker exec netstack-api python /app/scripts/run_six_stages_with_validation.py
```

---

## 通用成功檢查

### 1. 驗證快照完整性
```bash
docker exec netstack-api ls -la /app/data/validation_snapshots/
# 應該包含：
# stage1_validation.json - 軌道計算
# stage2_validation.json - 智能過濾  
# stage3_validation.json - 信號分析
# stage4_validation.json - 時間序列預處理
# stage5_validation.json - 數據整合
# stage6_validation.json - 動態池規劃
```

### 2. 數據流驗證
```bash
# 檢查數據大小遞進
docker exec netstack-api du -sh /app/data/*_output.json
# tle_calculation_output.json     ~30MB
# ntpu_filtered_satellites.json   ~15MB  
# signal_event_analysis_output.json ~80MB
# data_integration_output.json    ~205MB
# enhanced_dynamic_pools_output.json ~12MB
```

### 3. 日誌無ERROR檢查
```bash
docker logs netstack-api 2>&1 | grep -i "error\|exception\|failed" | tail -10
# 應該沒有嚴重錯誤或異常
```

---

## 錯誤排查

### 常見問題
1. **權限錯誤**: 確保容器有寫入權限
2. **內存不足**: 處理大數據時可能需要增加容器內存
3. **依賴缺失**: 檢查是否所有Python套件已安裝
4. **輸入文件缺失**: 確保前階段已成功執行

### 快速診斷命令
```bash
# 檢查容器狀態
make status

# 檢查磁盤空間
docker exec netstack-api df -h

# 檢查Python環境
docker exec netstack-api python -c "import sys; print(sys.path)"
```

---

## 效能基準

### 預期處理時間
- **階段1**: 1-3分鐘 (SGP4軌道計算)
- **階段2**: 30-60秒 (可見性過濾)
- **階段3**: 10-20秒 (信號分析)
- **階段4**: 10-15秒 (時間序列轉換)
- **階段5**: 4-10秒 (數據整合)  
- **階段6**: 1-2秒 (池規劃)

### 內存使用
- 峰值內存使用約1-2GB
- 磁盤空間需求約500MB-1GB

---

## 清理程式執行指南

### 全階段清理 (清空所有數據)
```bash
# 方法一：使用專用清理腳本
docker exec netstack-api python -c "
from shared_core.cleanup_manager import cleanup_all_stages
result = cleanup_all_stages()
print(f'全階段清理完成: {result}')
"

# 方法二：逐階段清理
docker exec netstack-api python -c "
from shared_core.cleanup_manager import auto_cleanup
for stage in range(1, 7):
    result = auto_cleanup(current_stage=stage)
    print(f'階段{stage}清理: {result}')
"

# 方法三：暴力清理 (謹慎使用)
docker exec netstack-api find /app/data -name "*.json" -not -path "*/tle_data/*" -delete
docker exec netstack-api find /app/data -type d -empty -delete
```

### 選擇性清理

#### 清理特定階段範圍
```bash
# 清理階段1-3
docker exec netstack-api python -c "
from shared_core.cleanup_manager import auto_cleanup
for stage in [1, 2, 3]:
    result = auto_cleanup(current_stage=stage)
    print(f'階段{stage}清理: {result}')
"

# 清理階段4-6
docker exec netstack-api python -c "
from shared_core.cleanup_manager import auto_cleanup  
for stage in [4, 5, 6]:
    result = auto_cleanup(current_stage=stage)
    print(f'階段{stage}清理: {result}')
"
```

#### 清理驗證快照
```bash
# 只清理驗證快照
docker exec netstack-api rm -f /app/data/validation_snapshots/stage*_validation.json

# 重建驗證快照目錄
docker exec netstack-api mkdir -p /app/data/validation_snapshots
```

#### 清理特定類型檔案
```bash
# 只清理大型輸出檔案 (保留配置和小文件)
docker exec netstack-api find /app/data -name "*_output.json" -size +10M -delete

# 只清理動畫數據
docker exec netstack-api rm -f /app/data/animation_enhanced_*.json

# 只清理子目錄數據 (保留主目錄檔案)
docker exec netstack-api rm -rf /app/data/layered_elevation_enhanced/*
docker exec netstack-api rm -rf /app/data/handover_scenarios/*
docker exec netstack-api rm -rf /app/data/signal_quality_analysis/*
```

### 清理驗證

#### 檢查清理結果
```bash
# 檢查主要輸出檔案
docker exec netstack-api ls -la /app/data/*_output.json

# 檢查子目錄結構
docker exec netstack-api find /app/data -type d -name "*_*" | sort

# 檢查磁盤使用量
docker exec netstack-api du -sh /app/data/
docker exec netstack-api du -sh /app/data/*/ 2>/dev/null | sort -hr
```

#### 確認清理完成
```bash
# 驗證關鍵檔案已清理
docker exec netstack-api python -c "
import os
from pathlib import Path

data_dir = Path('/app/data')
critical_files = [
    'tle_orbital_calculation_output.json',
    'intelligent_filtered_output.json', 
    'signal_event_analysis_output.json',
    'data_integration_output.json',
    'enhanced_dynamic_pools_output.json'
]

print('🔍 檢查關鍵檔案清理狀態:')
for file in critical_files:
    file_path = data_dir / file
    status = '❌ 存在' if file_path.exists() else '✅ 已清理'
    print(f'  {file}: {status}')
"
```

---

## 完整數據流檢查

### 數據大小進展檢查
```bash
# 檢查每階段數據大小變化
docker exec netstack-api python -c "
import os
from pathlib import Path

files_to_check = [
    ('Stage1', '/app/data/tle_orbital_calculation_output.json', '~1.4GB'),
    ('Stage2', '/app/data/satellite_visibility_filtered_output.json', '~1.1GB'),
    ('Stage3', '/app/data/signal_quality_analysis_output.json', '~1.1GB'),
    ('Stage4 Starlink', '/app/data/animation_enhanced_starlink.json', '~166MB'),
    ('Stage4 OneWeb', '/app/data/animation_enhanced_oneweb.json', '~11MB'),
    ('Stage5', '/app/data/data_integration_output.json', '~205MB'),
    ('Stage6', '/app/data/enhanced_dynamic_pools_output.json', '~13MB'),
]

print('📊 數據流大小檢查:')
for stage, file_path, expected in files_to_check:
    if os.path.exists(file_path):
        size_mb = os.path.getsize(file_path) / (1024*1024)
        print(f'✅ {stage}: {size_mb:.1f}MB {expected}')
    else:
        print(f'❌ {stage}: 文件不存在 {file_path}')
"
```

### 衛星數量檢查
```bash
# 檢查每階段衛星數量變化
docker exec netstack-api python -c "
import json
import os

stages_info = [
    ('Stage1', '/app/data/validation_snapshots/stage1_validation.json', 'total_satellites'),
    ('Stage2', '/app/data/validation_snapshots/stage2_validation.json', 'filtered_satellites'), 
    ('Stage3', '/app/data/validation_snapshots/stage3_validation.json', 'analyzed_satellites'),
    ('Stage4', '/app/data/validation_snapshots/stage4_validation.json', 'converted_satellites'),
    ('Stage5', '/app/data/validation_snapshots/stage5_validation.json', 'integrated_satellites'),
    ('Stage6', '/app/data/validation_snapshots/stage6_validation.json', 'pool_candidates')
]

print('🛰️ 衛星數量流檢查:')
for stage, file_path, key in stages_info:
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            count = data.get('keyMetrics', {}).get(key, 0)
            print(f'✅ {stage}: {count} 顆衛星')
        except:
            print(f'⚠️ {stage}: 驗證檔案讀取失敗')
    else:
        print(f'❌ {stage}: 驗證檔案不存在')
"
```

---

**注意**: 
- 所有階段都應該生成對應的驗證快照，且狀態為"completed"或驗證通過，才算成功執行
- 清理程式會永久刪除數據，使用前請確認備份需求
- 建議在執行新的管道前先執行全階段清理，確保數據一致性