#!/bin/bash
set -e

echo "🧹 使用統一清理管理器清理舊的六階段預處理檔案..."

# 使用容器內的統一清理管理器
docker exec netstack-api python -c "
import sys
sys.path.insert(0, '/app/src')
from shared_core.cleanup_manager import cleanup_all_stages
result = cleanup_all_stages()
print(f'✅ 統一清理完成: {result[\"files\"]} 檔案, {result[\"directories\"]} 目錄已清理')
"

echo ""
echo "🚀 開始執行六階段預處理..."
echo "================================"

# 在容器內執行六階段處理（使用最新的統一執行腳本）
docker exec netstack-api bash -c "
cd /app
export PYTHONPATH='/app:/app/src:/app/netstack'
python scripts/run_leo_preprocessing.py --data-dir /app/data
"

# 檢查結果
echo ""
echo "📊 檢查處理結果..."
echo "================================"

# 檢查各階段輸出文件
echo "📁 Stage 1 - TLE計算輸出:"
ls -lh "$DATA_DIR/tle_calculation_outputs/" 2>/dev/null | head -3

echo ""
echo "📁 Stage 2 - 智能篩選輸出:"
ls -lh "$DATA_DIR/intelligent_filtering_outputs/" 2>/dev/null | head -3

echo ""
echo "📁 Stage 3 - 信號分析輸出:"
ls -lh "$DATA_DIR/signal_analysis_outputs/" 2>/dev/null | head -3

echo ""
echo "📁 Stage 4 - 時間序列輸出:"
ls -lh "$DATA_DIR/timeseries_preprocessing_outputs/" 2>/dev/null | head -3

echo ""
echo "📁 Stage 5 - 數據整合輸出:"
ls -lh "$DATA_DIR/data_integration_outputs/" 2>/dev/null | head -3

echo ""
echo "📁 Stage 6 - 動態池規劃輸出:"
ls -lh "$DATA_DIR/dynamic_pool_planning_outputs/" 2>/dev/null | head -3

# 檢查最終的衛星數量
if [ -f "$DATA_DIR/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json" ]; then
    echo ""
    echo "🛰️ Stage 6 最終衛星數量:"
    cat "$DATA_DIR/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json" | \
        jq -r '.dynamic_satellite_pool | {starlink: (.starlink_satellites | length), oneweb: (.oneweb_satellites | length), total: .total_selected}'
else
    echo ""
    echo "⚠️ Stage 6 輸出文件不存在"
fi

echo ""
echo "✅ 檢查完成！"