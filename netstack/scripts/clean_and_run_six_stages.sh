#!/bin/bash
set -e

echo "🧹 開始清理舊的六階段預處理檔案..."

# 主機端清理
echo "📂 清理主機端數據目錄..."
DATA_DIR="/home/sat/ntn-stack/data/leo_outputs"

# 清理所有階段的輸出目錄
rm -rf "$DATA_DIR/tle_calculation_outputs" 2>/dev/null || true
rm -rf "$DATA_DIR/orbital_calculation_outputs" 2>/dev/null || true
rm -rf "$DATA_DIR/intelligent_filtering_outputs" 2>/dev/null || true
rm -rf "$DATA_DIR/signal_analysis_outputs" 2>/dev/null || true
rm -rf "$DATA_DIR/timeseries_preprocessing_outputs" 2>/dev/null || true
rm -rf "$DATA_DIR/data_integration_outputs" 2>/dev/null || true
rm -rf "$DATA_DIR/dynamic_pool_planning_outputs" 2>/dev/null || true
rm -rf "$DATA_DIR/signal_cache" 2>/dev/null || true
rm -f "$DATA_DIR/data_integration_output.json" 2>/dev/null || true
rm -f "$DATA_DIR/leo_optimization_final_report.json" 2>/dev/null || true

# 創建必要的目錄
mkdir -p "$DATA_DIR/tle_calculation_outputs"
mkdir -p "$DATA_DIR/orbital_calculation_outputs"
mkdir -p "$DATA_DIR/intelligent_filtering_outputs"
mkdir -p "$DATA_DIR/signal_analysis_outputs"
mkdir -p "$DATA_DIR/timeseries_preprocessing_outputs"
mkdir -p "$DATA_DIR/data_integration_outputs"
mkdir -p "$DATA_DIR/dynamic_pool_planning_outputs"

echo "✅ 舊檔案清理完成"

echo ""
echo "🚀 開始執行六階段預處理..."
echo "================================"

# 在容器內執行六階段處理
docker exec netstack-api bash -c "
cd /app
export PYTHONPATH='/app:/app/src:/app/netstack'
python scripts/run_six_stages.py --data-dir /app/data
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