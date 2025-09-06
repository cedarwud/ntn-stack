#!/bin/bash
# 快速建構狀態檢查器
# 用於快速檢查映像檔建構時的六階段處理狀態

set -e

DATA_DIR="${1:-/app/data}"
echo "🔍 快速建構狀態檢查 - $DATA_DIR"
echo "========================================"

# 1. 檢查建構狀態檔案
if [ -f "$DATA_DIR/.build_status" ]; then
    echo "📄 建構狀態檔案存在"
    
    if grep -q "BUILD_SUCCESS=true" "$DATA_DIR/.build_status"; then
        echo "✅ 建構成功標記: 是"
        
        if grep -q "BUILD_IMMEDIATE_VALIDATION_PASSED=true" "$DATA_DIR/.build_status"; then
            echo "✅ 即時驗證通過: 是"
            BUILD_OVERALL_SUCCESS="true"
        else
            echo "⚠️ 即時驗證通過: 未確認"
            BUILD_OVERALL_SUCCESS="partial"
        fi
        
    elif grep -q "BUILD_IMMEDIATE_VALIDATION_FAILED=true" "$DATA_DIR/.build_status"; then
        echo "❌ 建構狀態: 即時驗證失敗"
        FAILED_STAGE=$(grep "FAILED_STAGE=" "$DATA_DIR/.build_status" | cut -d'=' -f2)
        echo "❌ 失敗階段: $FAILED_STAGE"
        BUILD_OVERALL_SUCCESS="false"
        
    elif grep -q "BUILD_TIMEOUT=true" "$DATA_DIR/.build_status"; then
        echo "⏰ 建構狀態: 處理超時"
        BUILD_OVERALL_SUCCESS="timeout"
        
    else
        echo "❓ 建構狀態: 未知"
        BUILD_OVERALL_SUCCESS="unknown"
    fi
else
    echo "❌ 建構狀態檔案不存在"
    BUILD_OVERALL_SUCCESS="missing"
fi

# 2. 檢查驗證快照
echo ""
echo "🔍 檢查驗證快照:"
COMPLETED_STAGES=0

if [ -d "$DATA_DIR/validation_snapshots" ]; then
    for stage in {1..6}; do
        snapshot_file="$DATA_DIR/validation_snapshots/stage${stage}_validation.json"
        if [ -f "$snapshot_file" ]; then
            # 檢查是否包含成功標記
            if grep -q '"status": "completed"' "$snapshot_file" && grep -q '"passed": true' "$snapshot_file"; then
                echo "  ✅ 階段$stage: 完成且驗證通過"
                COMPLETED_STAGES=$((COMPLETED_STAGES + 1))
            else
                echo "  ❌ 階段$stage: 驗證失敗或未完成"
                break  # 即時驗證架構下，失敗階段後不會有後續階段
            fi
        else
            echo "  ❌ 階段$stage: 驗證快照不存在"
            break  # 沒有驗證快照意味著該階段未執行
        fi
    done
else
    echo "  ❌ 驗證快照目錄不存在"
fi

# 3. 檢查關鍵輸出檔案
echo ""
echo "📁 檢查關鍵輸出檔案:"

key_outputs=(
    "tle_calculation_outputs/tle_orbital_calculation_output.json:階段1軌道計算"
    "intelligent_filtering_outputs/intelligent_filtered_output.json:階段2智能篩選"  
    "signal_analysis_outputs/signal_event_analysis_output.json:階段3信號分析"
    "timeseries_preprocessing_outputs:階段4時間序列目錄"
    "data_integration_outputs/data_integration_output.json:階段5數據整合"
    "dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json:階段6動態池規劃"
)

OUTPUT_FILES_OK=0
for output_info in "${key_outputs[@]}"; do
    IFS=':' read -r output_path description <<< "$output_info"
    full_path="$DATA_DIR/$output_path"
    
    if [ -e "$full_path" ]; then
        if [ -f "$full_path" ]; then
            size=$(du -h "$full_path" | cut -f1)
            echo "  ✅ $description: 存在 ($size)"
            OUTPUT_FILES_OK=$((OUTPUT_FILES_OK + 1))
        elif [ -d "$full_path" ]; then
            file_count=$(find "$full_path" -name "*.json" | wc -l)
            if [ "$file_count" -gt 0 ]; then
                echo "  ✅ $description: 存在 ($file_count 個檔案)"
                OUTPUT_FILES_OK=$((OUTPUT_FILES_OK + 1))
            else
                echo "  ❌ $description: 目錄存在但無檔案"
            fi
        fi
    else
        echo "  ❌ $description: 不存在"
    fi
done

# 4. 最終狀態總結
echo ""
echo "========================================"
echo "📋 快速檢查結果總結"
echo "========================================"

if [ "$BUILD_OVERALL_SUCCESS" = "true" ] && [ "$COMPLETED_STAGES" -eq 6 ] && [ "$OUTPUT_FILES_OK" -eq 6 ]; then
    echo "🎉 狀態: 完全成功"
    echo "✅ 建構成功: 是"
    echo "✅ 驗證通過: 全部6階段"
    echo "✅ 輸出檔案: 全部6個關鍵檔案"
    echo ""
    echo "💡 建議: 無需額外操作，系統已就緒"
    exit 0
    
elif [ "$COMPLETED_STAGES" -gt 0 ]; then
    echo "⚠️ 狀態: 部分成功"
    echo "⚠️ 建構狀態: $BUILD_OVERALL_SUCCESS"
    echo "⚠️ 完成階段: $COMPLETED_STAGES/6"
    echo "⚠️ 輸出檔案: $OUTPUT_FILES_OK/6"
    echo ""
    echo "💡 建議: 在容器啟動後執行運行時重新處理"
    echo "   docker exec netstack-api python /app/scripts/run_six_stages_with_validation.py"
    exit 1
    
else
    echo "❌ 狀態: 建構失敗"
    echo "❌ 建構狀態: $BUILD_OVERALL_SUCCESS"
    echo "❌ 完成階段: $COMPLETED_STAGES/6"
    echo "❌ 輸出檔案: $OUTPUT_FILES_OK/6"
    echo ""
    echo "💡 建議: 重新建構映像檔或檢查建構配置"
    echo "   - 檢查 Dockerfile 中的六階段處理調用"  
    echo "   - 檢查 TLE 數據是否正確載入到容器"
    echo "   - 檢查建構腳本是否正確配置"
    exit 2
fi