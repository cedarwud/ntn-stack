# 45天TLE數據收集指南

## 📂 目錄結構

```
/home/sat/ntn-stack/tle_data/
├── README.md
├── starlink/                    # Starlink 數據目錄
│   ├── tle/                     # TLE 格式 (主要數據)
│   │   ├── starlink_day_01.tle ~ starlink_day_45.tle
│   └── json/                    # JSON 格式 (補充數據)
│       ├── starlink_day_01.json ~ starlink_day_45.json
└── oneweb/                      # OneWeb 數據目錄
    ├── tle/                     # TLE 格式 (主要數據)
    │   ├── oneweb_day_01.tle ~ oneweb_day_45.tle
    └── json/                    # JSON 格式 (補充數據)
        ├── oneweb_day_01.json ~ oneweb_day_45.json
```

**數據格式說明**:
- **TLE**: 標準軌道參數，用於 SGP4 軌道計算 (必需)
- **JSON**: 結構化數據，包含額外元數據 (建議)

## 📋 每日數據收集流程

### 1. 獲取 Starlink 數據
```bash
# TLE 格式 (必需)
curl "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle" > starlink/tle/starlink_day_XX.tle

# JSON 格式 (建議)
curl "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=json" > starlink/json/starlink_day_XX.json
```

### 2. 獲取 OneWeb 數據
```bash
# TLE 格式 (必需)
curl "https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle" > oneweb/tle/oneweb_day_XX.tle

# JSON 格式 (建議)
curl "https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=json" > oneweb/json/oneweb_day_XX.json
```

### 3. 檔案命名規則
**TLE 格式**:
- Starlink: `starlink/tle/starlink_day_01.tle` ~ `starlink_day_45.tle`
- OneWeb: `oneweb/tle/oneweb_day_01.tle` ~ `oneweb_day_45.tle`

**JSON 格式**:
- Starlink: `starlink/json/starlink_day_01.json` ~ `starlink_day_45.json`
- OneWeb: `oneweb/json/oneweb_day_01.json` ~ `oneweb_day_45.json`

- 使用2位數字補零 (01, 02, ..., 45)

### 4. 數據品質檢查
```bash
# 檢查 TLE 檔案大小
ls -la starlink/tle/starlink_day_*.tle
ls -la oneweb/tle/oneweb_day_*.tle

# 檢查 JSON 檔案大小
ls -la starlink/json/starlink_day_*.json
ls -la oneweb/json/oneweb_day_*.json

# 檢查 TLE 格式
head -6 starlink/tle/starlink_day_XX.tle

# 計算衛星數量
wc -l starlink/tle/starlink_day_XX.tle

# 驗證 JSON 格式
python3 -c "import json; print(json.load(open('starlink/json/starlink_day_XX.json'))[:2])"
```

## 🎯 使用目的

這些手動收集的45天TLE歷史數據將用於：

1. **RL強化學習研究** - 提供45天真實軌道演化數據
2. **換手模式分析** - 識別重複的最佳換手時間段  
3. **雙星座對比** - Starlink vs OneWeb 性能比較
4. **學術論文數據** - 確保研究數據的真實性和可信度

## ⚠️ 注意事項

- 每天固定時間收集數據（建議UTC 00:00）
- 確保網路連接穩定，避免下載不完整
- 定期備份已收集的數據
- 檢查檔案大小，異常小的檔案可能下載失敗

## 🔧 故障排除

### 下載失敗
```bash
# 檢查網路連接
ping celestrak.org

# 使用不同下載方法重試
curl -v "URL" > filename.tle
```

### 格式驗證
```bash
# 檢查TLE格式正確性
python3 -c "
from skyfield.api import EarthSatellite
with open('starlink_day_XX.tle', 'r') as f:
    lines = f.readlines()
    for i in range(0, len(lines), 3):
        if i+2 < len(lines):
            sat = EarthSatellite(lines[i+1], lines[i+2], lines[i])
            print(f'✅ {lines[i].strip()}')
"
```

## 📈 進度追蹤

### Starlink 收集狀態
```bash
# 檢查已收集天數 (TLE)
ls starlink/tle/ | wc -l

# 檢查已收集天數 (JSON)
ls starlink/json/ | wc -l

# 檢查缺失的 TLE 文件
for i in {01..45}; do 
  if [ ! -s "starlink/tle/starlink_day_$i.tle" ]; then 
    echo "缺失或空檔: starlink/tle/starlink_day_$i.tle"
  fi
done

# 檢查缺失的 JSON 文件
for i in {01..45}; do 
  if [ ! -s "starlink/json/starlink_day_$i.json" ]; then 
    echo "缺失或空檔: starlink/json/starlink_day_$i.json"
  fi
done
```

### OneWeb 收集狀態
```bash
# 檢查已收集天數 (TLE)
ls oneweb/tle/ | wc -l

# 檢查已收集天數 (JSON)  
ls oneweb/json/ | wc -l

# 檢查缺失的 TLE 文件
for i in {01..45}; do 
  if [ ! -s "oneweb/tle/oneweb_day_$i.tle" ]; then 
    echo "缺失或空檔: oneweb/tle/oneweb_day_$i.tle"
  fi
done

# 檢查缺失的 JSON 文件
for i in {01..45}; do 
  if [ ! -s "oneweb/json/oneweb_day_$i.json" ]; then 
    echo "缺失或空檔: oneweb/json/oneweb_day_$i.json"
  fi
done
```

## 🚀 自動化建議

### 每日收集腳本範例
```bash
#!/bin/bash
# 位置: /home/sat/scripts/daily_tle_collection.sh

DATE=$(date +%Y%m%d)
DAY_NUM=$(( ($(date +%s) - $(date -d "2025-01-01" +%s)) / 86400 + 1 ))
DAY_FORMATTED=$(printf "%02d" $DAY_NUM)

cd /home/sat/ntn-stack/tle_data

echo "🚀 開始第 $DAY_FORMATTED 天數據收集: $DATE"

# 下載 Starlink TLE
curl "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle" > "starlink/tle/starlink_day_${DAY_FORMATTED}.tle"

# 下載 Starlink JSON
curl "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=json" > "starlink/json/starlink_day_${DAY_FORMATTED}.json"

# 下載 OneWeb TLE
curl "https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle" > "oneweb/tle/oneweb_day_${DAY_FORMATTED}.tle"

# 下載 OneWeb JSON
curl "https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=json" > "oneweb/json/oneweb_day_${DAY_FORMATTED}.json"

# 驗證下載
echo "📊 數據驗證:"
echo "Starlink TLE: $(wc -l < starlink/tle/starlink_day_${DAY_FORMATTED}.tle) 行"
echo "Starlink JSON: $(wc -c < starlink/json/starlink_day_${DAY_FORMATTED}.json) 字節"
echo "OneWeb TLE: $(wc -l < oneweb/tle/oneweb_day_${DAY_FORMATTED}.tle) 行"
echo "OneWeb JSON: $(wc -c < oneweb/json/oneweb_day_${DAY_FORMATTED}.json) 字節"

echo "✅ 第 $DAY_FORMATTED 天數據收集完成: $DATE"
```

---

**🎯 目標**: 在45天內收集完整的雙星座TLE歷史數據，支援RL研究和學術論文撰寫