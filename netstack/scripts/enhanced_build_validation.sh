#!/bin/bash
# 增強的建構時驗證腳本
# 集成六階段處理和驗證快照檢查

set -e

DATA_DIR="/app/data"
BUILD_LOG="/tmp/six_stage_build.log"
VALIDATION_LOG="/tmp/validation_check.log"

echo "🏗️ 開始增強建構驗證流程..."

# 0. 預處理：清理舊的建構報告
echo "🗑️ 清理舊的建構報告..."
rm -f "$DATA_DIR/.build_status" "$DATA_DIR/.build_validation_status" "$DATA_DIR/.final_build_report.json" "$DATA_DIR/.build_summary.txt"
echo "✅ 舊報告清理完成"

# 1. 執行六階段處理 - 使用即時驗證版本
echo "📡 執行六階段數據處理 (階段即時驗證版本)..."
echo "⚠️ 重要: 使用新的即時驗證架構，每階段完成後立即驗證"
timeout 1800 python scripts/run_six_stages_with_validation.py --data-dir "$DATA_DIR" > "$BUILD_LOG" 2>&1
BUILD_EXIT_CODE=$?

echo "📊 六階段即時驗證處理結果:"
if [ $BUILD_EXIT_CODE -eq 0 ]; then
    echo "✅ 六階段處理與即時驗證完全成功！"
    echo "最後10行日誌:"
    tail -10 "$BUILD_LOG"
    
    # 即時驗證架構不需要額外的後續驗證，因為每階段已經驗證過了
    echo "🎯 即時驗證架構: 所有階段已在處理時完成驗證"
    echo "BUILD_SUCCESS=true" > "$DATA_DIR/.build_status"
    echo "BUILD_IMMEDIATE_VALIDATION_PASSED=true" >> "$DATA_DIR/.build_status"
    echo "BUILD_VALIDATION_MODE=immediate" >> "$DATA_DIR/.build_status"
    echo "BUILD_TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$DATA_DIR/.build_status"
    
    # 生成可從主機直接查看的建構報告
    echo "🔍 生成建構狀態報告..."
    python scripts/generate_build_report.py --data-dir "$DATA_DIR"
    
    echo "✅ 建構與即時驗證完全成功！"
    echo "📄 建構報告已生成: $DATA_DIR/BUILD_REPORT.md"
    echo "📄 快速狀態檔案: $DATA_DIR/.build_quick_status"
    exit 0
    
elif [ $BUILD_EXIT_CODE -eq 124 ]; then
    echo "⏰ 六階段處理超時(30分鐘)"
    echo "BUILD_TIMEOUT=true" > "$DATA_DIR/.build_status"
    echo "RUNTIME_PROCESSING_REQUIRED=true" >> "$DATA_DIR/.build_status"
    echo "BUILD_TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$DATA_DIR/.build_status"
    echo "最後20行日誌:"
    tail -20 "$BUILD_LOG"
    exit 3  # 超時退出碼
else
    echo "❌ 六階段即時驗證處理失敗(退出碼:$BUILD_EXIT_CODE)"
    echo "🚨 即時驗證架構: 某個階段驗證失敗，後續階段已自動停止"
    echo "BUILD_IMMEDIATE_VALIDATION_FAILED=true" > "$DATA_DIR/.build_status"
    echo "BUILD_EXIT_CODE=$BUILD_EXIT_CODE" >> "$DATA_DIR/.build_status"
    echo "BUILD_VALIDATION_MODE=immediate" >> "$DATA_DIR/.build_status"
    echo "RUNTIME_PROCESSING_REQUIRED=true" >> "$DATA_DIR/.build_status"
    echo "BUILD_TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$DATA_DIR/.build_status"
    echo "最後20行日誌:"
    tail -20 "$BUILD_LOG"
    
    # 分析具体是哪个阶段失败了
    echo "🔍 分析失敗階段..."
    if grep -q "階段1" "$BUILD_LOG"; then
        echo "FAILED_STAGE=1" >> "$DATA_DIR/.build_status"
        echo "❌ 失敗階段: 1 (SGP4軌道計算)"
    elif grep -q "階段2" "$BUILD_LOG"; then
        echo "FAILED_STAGE=2" >> "$DATA_DIR/.build_status"
        echo "❌ 失敗階段: 2 (智能衛星篩選)"
    elif grep -q "階段3" "$BUILD_LOG"; then
        echo "FAILED_STAGE=3" >> "$DATA_DIR/.build_status"
        echo "❌ 失敗階段: 3 (信號品質分析)"
    elif grep -q "階段4" "$BUILD_LOG"; then
        echo "FAILED_STAGE=4" >> "$DATA_DIR/.build_status"
        echo "❌ 失敗階段: 4 (時間序列預處理)"
    elif grep -q "階段5" "$BUILD_LOG"; then
        echo "FAILED_STAGE=5" >> "$DATA_DIR/.build_status"
        echo "❌ 失敗階段: 5 (數據整合)"
    elif grep -q "階段6" "$BUILD_LOG"; then
        echo "FAILED_STAGE=6" >> "$DATA_DIR/.build_status"
        echo "❌ 失敗階段: 6 (動態池規劃)"
    else
        echo "FAILED_STAGE=unknown" >> "$DATA_DIR/.build_status"
        echo "❌ 失敗階段: 未知"
    fi
    
    exit 4  # 處理失敗退出碼
fi

# 最終步驟：無論成功或失敗，都執行最終建構驗證並生成報告
echo ""
echo "📋 執行最終建構驗證並生成報告..."
echo "------------------------------------------------------------"

# 執行最終建構驗證腳本
python scripts/final_build_validation.py --data-dir "$DATA_DIR" --clear-old > "$VALIDATION_LOG" 2>&1
FINAL_VALIDATION_EXIT_CODE=$?

echo "📊 最終建構驗證結果:"
cat "$VALIDATION_LOG"

# 根據最終驗證結果決定最終退出碼
if [ $FINAL_VALIDATION_EXIT_CODE -eq 0 ]; then
    echo ""
    echo "🎉 最終建構驗證完成！"
    echo "📄 建構報告已生成在 $DATA_DIR 目錄中"
    echo "   - .final_build_report.json (詳細JSON報告)"
    echo "   - .build_status (狀態檔案)"  
    echo "   - .build_summary.txt (文本摘要)"
    
    # 顯示最終摘要
    if [ -f "$DATA_DIR/.build_summary.txt" ]; then
        echo ""
        echo "📋 建構摘要:"
        echo "----------------------------------------"
        cat "$DATA_DIR/.build_summary.txt"
    fi
    
    # 保持原來的退出碼邏輯
    if [ $BUILD_EXIT_CODE -eq 0 ]; then
        exit 0  # 建構和驗證都成功
    else
        exit 2  # 建構失敗但報告生成成功
    fi
else
    echo "❌ 最終建構驗證腳本執行失敗"
    echo "建構報告生成可能不完整"
    exit 5  # 驗證腳本執行失敗
fi