#!/bin/bash

echo "🔧 最終處理未使用變數..."

# 為剩餘的未使用變數添加下劃線前綴
find src -name "*.tsx" -o -name "*.ts" | while read file; do
    # 直接替換具體的變數名
    sed -i 's/\bconst metrics\b/const _metrics/g' "$file"
    sed -i 's/\blet metrics\b/let _metrics/g' "$file"
    sed -i 's/const devices\b/const _devices/g' "$file"
    sed -i 's/let devices\b/let _devices/g' "$file"
    sed -i 's/const speedMultiplier\b/const _speedMultiplier/g' "$file"
    sed -i 's/const onSatelliteClick\b/const _onSatelliteClick/g' "$file"
    sed -i 's/setUseRealData\b/_setUseRealData/g' "$file"
    sed -i 's/\bindex\s*:/\_index:/g' "$file"
    sed -i 's/const isCurrent\b/const _isCurrent/g' "$file"
    sed -i 's/const isPredicted\b/const _isPredicted/g' "$file"
    sed -i 's/const opacity\b/const _opacity/g' "$file"
done

echo "✅ 未使用變數處理完成！"
