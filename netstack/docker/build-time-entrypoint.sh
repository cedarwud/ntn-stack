#!/bin/bash
set -e

echo "🏗️ NetStack 映像建構時預處理開始..."

# 確保環境變數設定
export PYTHONPATH="/app:/app/src:/app/netstack"
export BUILD_MODE=true
export DATA_DIR="/app/data"

# 創建數據目錄
mkdir -p "$DATA_DIR" /app/logs /app/tle_data

echo "🎯 執行完整六階段預處理系統..."
echo "   Stage 1: TLE數據載入與SGP4軌道計算"
echo "   Stage 2: 智能衛星篩選"  
echo "   Stage 3: 信號品質分析與3GPP事件"
echo "   Stage 4: 時間序列預處理"
echo "   Stage 5: 數據整合"
echo "   Stage 6: 動態池規劃"

# 檢查主流程控制器是否存在
if [ -f "/app/src/leo_core/main_pipeline_controller.py" ]; then
    echo "✅ 找到增強六階段主流程控制器"
    
    # 執行完整六階段預處理
    cd /app
    if timeout 2700 python src/leo_core/main_pipeline_controller.py --mode build --data-dir "$DATA_DIR"; then
        echo "✅ 建構時六階段預處理完成"
        
        # 創建建構時間戳
        echo "$(date -Iseconds)" > "$DATA_DIR/.build_timestamp"
        echo "BUILD_TIME_PREPROCESSING=true" > "$DATA_DIR/.build_mode"
        
        # 顯示生成的文件
        echo "📊 預處理輸出文件:"
        find "$DATA_DIR" -name "*.json" -type f | head -10
        
        # 計算總文件大小
        total_size=$(du -sh "$DATA_DIR" 2>/dev/null | cut -f1 || echo "未知")
        echo "📦 預處理數據總大小: $total_size"
        
        echo "🎉 映像檔建構時預處理成功完成！"
        exit 0
    else
        echo "❌ 建構時六階段預處理失敗或超時"
        echo "🔄 將回退到運行時處理模式"
        exit 1
    fi
else
    echo "⚠️ 主流程控制器不存在，跳過建構時預處理"
    exit 1
fi