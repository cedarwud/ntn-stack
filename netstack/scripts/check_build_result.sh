#!/bin/bash
# 建構結果檢查腳本
# 用於檢查映像檔建構後的最終狀態報告

DATA_DIR="${1:-/app/data}"

echo "🔍 檢查映像檔建構結果"
echo "========================================"
echo "📁 數據目錄: $DATA_DIR"
echo ""

# 1. 檢查是否有最終建構報告
if [ -f "$DATA_DIR/.final_build_report.json" ]; then
    echo "✅ 找到最終建構報告"
    
    # 顯示文本摘要
    if [ -f "$DATA_DIR/.build_summary.txt" ]; then
        echo ""
        echo "📋 建構狀態摘要:"
        echo "----------------------------------------"
        cat "$DATA_DIR/.build_summary.txt"
        echo "----------------------------------------"
    fi
    
    # 檢查JSON報告中的關鍵資訊
    if command -v python3 >/dev/null 2>&1; then
        echo ""
        echo "📊 詳細狀態資訊:"
        python3 -c "
import json
with open('$DATA_DIR/.final_build_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

overall = report.get('overall_status', {})
print(f\"   狀態: {overall.get('status_message', '未知')} ({overall.get('status', 'UNKNOWN')})\")
print(f\"   完成階段: {overall.get('completed_stages', 0)}/{overall.get('total_expected_stages', 6)}\")
print(f\"   有效輸出: {overall.get('valid_outputs', 0)}/{overall.get('total_expected_outputs', 6)}\")

processing_time = overall.get('total_processing_time_minutes', 0)
print(f\"   處理時間: {processing_time:.1f} 分鐘\")

metadata = report.get('build_validation_metadata', {})
gen_time = metadata.get('report_generation_time', '')
if gen_time:
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(gen_time.replace('Z', '+00:00'))
        print(f\"   報告時間: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}\")
    except:
        print(f\"   報告時間: {gen_time}\")
"
    fi
    
    echo ""
    echo "📄 報告檔案位置:"
    echo "   詳細JSON報告: $DATA_DIR/.final_build_report.json"
    echo "   狀態檔案: $DATA_DIR/.build_status"
    echo "   文本摘要: $DATA_DIR/.build_summary.txt"
    
elif [ -f "$DATA_DIR/.build_status" ]; then
    echo "⚠️ 找到基本建構狀態檔案，但缺少詳細報告"
    echo ""
    echo "📋 基本狀態資訊:"
    echo "----------------------------------------"
    cat "$DATA_DIR/.build_status"
    echo "----------------------------------------"
    
    echo ""
    echo "💡 建議: 執行完整的狀態檢查來獲得詳細資訊"
    echo "   docker exec netstack-api python /app/scripts/check_build_status.py"
    
else
    echo "❌ 未找到任何建構狀態報告"
    echo ""
    echo "可能原因:"
    echo "   1. 建構尚未完成"
    echo "   2. 建構腳本未正確執行"
    echo "   3. 報告檔案被意外刪除"
    echo ""
    echo "💡 建議操作:"
    echo "   1. 檢查建構是否正在進行:"
    echo "      docker ps | grep netstack"
    echo ""
    echo "   2. 執行手動狀態檢查:"
    echo "      docker exec netstack-api python /app/scripts/check_build_status.py"
    echo ""
    echo "   3. 如果建構已完成，可能需要重新生成報告:"
    echo "      docker exec netstack-api python /app/scripts/final_build_validation.py"
fi

echo ""
echo "🔧 其他有用指令:"
echo "   快速狀態檢查: docker exec netstack-api bash /app/scripts/quick_build_check.sh"
echo "   詳細狀態分析: docker exec netstack-api python /app/scripts/check_build_status.py"
echo "   重新生成報告: docker exec netstack-api python /app/scripts/final_build_validation.py"