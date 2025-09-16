# 學術級數據合規性驗證報告
# Academic Data Compliance Validation Report

**驗證時間**: 2025-09-13T18:13:40.776429+00:00
**掃描文件數**: 64

## 總體合規性摘要
- **總體合規等級**: C
- Grade A 檔案: 0
- Grade B 檔案: 0
- Grade C 違規: 6
- 嚴重問題總數: 102

## 各階段合規性詳情
### STAGE_1
- **合規等級**: C
- **掃描文件數**: 4
- **嚴重問題**: 2
- **高級問題**: 0
- **中等問題**: 0

### STAGE_2
- **合規等級**: C
- **掃描文件數**: 9
- **嚴重問題**: 42
- **高級問題**: 33
- **中等問題**: 0

### STAGE_3
- **合規等級**: C
- **掃描文件數**: 17
- **嚴重問題**: 6
- **高級問題**: 0
- **中等問題**: 0

### STAGE_4
- **合規等級**: C
- **掃描文件數**: 9
- **嚴重問題**: 6
- **高級問題**: 4
- **中等問題**: 0

### STAGE_5
- **合規等級**: C
- **掃描文件數**: 12
- **嚴重問題**: 20
- **高級問題**: 2
- **中等問題**: 0

### STAGE_6
- **合規等級**: C
- **掃描文件數**: 16
- **嚴重問題**: 26
- **高級問題**: 1
- **中等問題**: 0

## 主要違規詳情
- **Critical**: 在文件 tle_orbital_calculation_processor.py:651 發現隨機數生成
  - 文件: tle_orbital_calculation_processor.py
  - 行號: 651
  - 匹配文本: `random.sample`

- **Critical**: 在文件 tle_orbital_calculation_processor.py:778 發現隨機數生成
  - 文件: tle_orbital_calculation_processor.py
  - 行號: 778
  - 匹配文本: `random.sample`

- **Critical**: 在文件 unified_intelligent_filter.py:380 發現RSRP硬編碼值
  - 文件: unified_intelligent_filter.py
  - 行號: 380
  - 匹配文本: `-90`

- **Critical**: 在文件 unified_intelligent_filter.py:381 發現RSRP硬編碼值
  - 文件: unified_intelligent_filter.py
  - 行號: 381
  - 匹配文本: `-90`

- **Critical**: 在文件 unified_intelligent_filter.py:382 發現RSRP硬編碼值
  - 文件: unified_intelligent_filter.py
  - 行號: 382
  - 匹配文本: `-90`

- **Critical**: 在文件 unified_intelligent_filter.py:409 發現RSRP硬編碼值
  - 文件: unified_intelligent_filter.py
  - 行號: 409
  - 匹配文本: `-90`

- **High**: 在文件 unified_intelligent_filter.py:380 發現仰角硬編碼預設值
  - 文件: unified_intelligent_filter.py
  - 行號: 380
  - 匹配文本: `elevation_deg": min(elevations) if elevations else -90`

- **High**: 在文件 unified_intelligent_filter.py:381 發現仰角硬編碼預設值
  - 文件: unified_intelligent_filter.py
  - 行號: 381
  - 匹配文本: `elevation_deg": max(elevations) if elevations else -90`

- **High**: 在文件 unified_intelligent_filter.py:382 發現仰角硬編碼預設值
  - 文件: unified_intelligent_filter.py
  - 行號: 382
  - 匹配文本: `elevation_deg": sum(elevations) / len(elevations) if elevations else -90`

- **High**: 在文件 unified_intelligent_filter.py:409 發現仰角硬編碼預設值
  - 文件: unified_intelligent_filter.py
  - 行號: 409
  - 匹配文本: `elevation_deg", -90`

- **Critical**: 在文件 elevation_filter.py:238 發現RSRP硬編碼值
  - 文件: elevation_filter.py
  - 行號: 238
  - 匹配文本: `-90`

- **Critical**: 在文件 elevation_filter.py:343 發現RSRP硬編碼值
  - 文件: elevation_filter.py
  - 行號: 343
  - 匹配文本: `-90`

- **High**: 在文件 elevation_filter.py:238 發現仰角硬編碼預設值
  - 文件: elevation_filter.py
  - 行號: 238
  - 匹配文本: `elevation_deg", -90`

- **High**: 在文件 elevation_filter.py:343 發現仰角硬編碼預設值
  - 文件: elevation_filter.py
  - 行號: 343
  - 匹配文本: `elevation_deg", -90`

- **High**: 在文件 elevation_filter.py:238 發現仰角硬編碼預設值
  - 文件: elevation_filter.py
  - 行號: 238
  - 匹配文本: `get("elevation_deg", -90)`

- **High**: 在文件 elevation_filter.py:343 發現仰角硬編碼預設值
  - 文件: elevation_filter.py
  - 行號: 343
  - 匹配文本: `get("elevation_deg", -90)`

- **Critical**: 在文件 satellite_visibility_filter_processor.py:420 發現RSRP硬編碼值
  - 文件: satellite_visibility_filter_processor.py
  - 行號: 420
  - 匹配文本: `-90`

- **High**: 在文件 satellite_visibility_filter_processor.py:420 發現仰角硬編碼預設值
  - 文件: satellite_visibility_filter_processor.py
  - 行號: 420
  - 匹配文本: `elevation_deg = -90`

- **Critical**: 在文件 visibility_analyzer.py:155 發現RSRP硬編碼值
  - 文件: visibility_analyzer.py
  - 行號: 155
  - 匹配文本: `-90`

- **Critical**: 在文件 visibility_analyzer.py:176 發現RSRP硬編碼值
  - 文件: visibility_analyzer.py
  - 行號: 176
  - 匹配文本: `-90`
