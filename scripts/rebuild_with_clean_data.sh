#!/bin/bash
# 完整重建並清理所有舊數據的腳本

echo "🧹 完整清理並重建 NTN Stack"
echo "================================"

# 1. 停止所有容器
echo "🛑 停止所有容器..."
cd /home/sat/ntn-stack
make down

# 2. 清理主機上的舊數據
echo "🗑️ 清理主機上的六階段預處理數據..."
sudo rm -rf /home/sat/ntn-stack/data/leo_outputs/tle_calculation_outputs
sudo rm -rf /home/sat/ntn-stack/data/leo_outputs/orbital_calculation_outputs
sudo rm -rf /home/sat/ntn-stack/data/leo_outputs/intelligent_filtering_outputs
sudo rm -rf /home/sat/ntn-stack/data/leo_outputs/signal_analysis_outputs
sudo rm -rf /home/sat/ntn-stack/data/leo_outputs/timeseries_preprocessing_outputs
sudo rm -rf /home/sat/ntn-stack/data/leo_outputs/data_integration_outputs
sudo rm -rf /home/sat/ntn-stack/data/leo_outputs/dynamic_pool_planning_outputs
sudo rm -rf /home/sat/ntn-stack/data/leo_outputs/signal_cache
sudo rm -f /home/sat/ntn-stack/data/leo_outputs/data_integration_output.json
sudo rm -f /home/sat/ntn-stack/data/leo_outputs/leo_optimization_final_report.json

# 創建必要的目錄
mkdir -p /home/sat/ntn-stack/data/leo_outputs
chmod 777 /home/sat/ntn-stack/data/leo_outputs

echo "✅ 舊數據清理完成"

# 3. 重建映像檔
echo "🏗️ 重建 Docker 映像檔..."
make build

# 4. 啟動容器
echo "🚀 啟動容器..."
make up

# 5. 等待服務就緒
echo "⏳ 等待服務就緒..."
sleep 30

# 6. 執行六階段預處理
echo "🎯 執行六階段預處理..."
docker exec netstack-api bash -c "
cd /app
export PYTHONPATH='/app:/app/src:/app/netstack'
python scripts/run_six_stages.py --data-dir /app/data
"

echo ""
echo "✅ 完成！"
echo ""
echo "📊 檢查結果："
ls -lh /home/sat/ntn-stack/data/leo_outputs/*/

# 檢查最終的衛星數量
if [ -f "/home/sat/ntn-stack/data/leo_outputs/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json" ]; then
    echo ""
    echo "🛰️ Stage 6 最終衛星數量:"
    cat /home/sat/ntn-stack/data/leo_outputs/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json | \
        jq -r '.dynamic_satellite_pool | {starlink: (.starlink_satellites | length), oneweb: (.oneweb_satellites | length), total: .total_selected}'
fi