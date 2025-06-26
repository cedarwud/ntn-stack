#!/bin/bash

echo "🔧 快速修復未使用變數問題..."

# 修復常見的未使用變數模式
find src -name "*.tsx" -o -name "*.ts" | while read file; do
    # 修復未使用的解構變數
    sed -i 's/satellites: _/satellites: _satellites/g' "$file"
    sed -i 's/: _coreSyncStatus/: _coreSyncStatus/g' "$file"
    sed -i 's/: _coreSyncData/: _coreSyncData/g' "$file"
    sed -i 's/_currentQuality/_currentQuality/g' "$file"
    sed -i 's/_jammerId/_jammerId/g' "$file"
    sed -i 's/_heatmapData/_heatmapData/g' "$file"
    sed -i 's/_setHeatmapData/_setHeatmapData/g' "$file"
    
    # 修復函數聲明
    sed -i 's/const getConnectionIcon/const _getConnectionIcon/g' "$file"
    sed -i 's/const FailoverEventsVisualization/const _FailoverEventsVisualization/g' "$file"
    sed -i 's/const getSeverityColor/const _getSeverityColor/g' "$file"
    sed -i 's/const getTriggerIcon/const _getTriggerIcon/g' "$file"
done

echo "✅ 快速修復完成！"
