#!/bin/bash

# NTN Stack 測試文件清理腳本
# 用於清理散落在專案中的測試文件和報告

set -e

PROJECT_ROOT="/home/sat/ntn-stack"
TESTS_DIR="$PROJECT_ROOT/tests"

echo "🧹 開始清理 NTN Stack 測試文件..."

# 創建測試目錄結構
echo "📁 創建測試目錄結構..."
mkdir -p "$TESTS_DIR/integration"
mkdir -p "$TESTS_DIR/phase_tests"
mkdir -p "$TESTS_DIR/verification"
mkdir -p "$TESTS_DIR/reports"

# 移動有價值的測試文件到正確位置
echo "📦 移動測試文件..."

# 整合測試
find "$PROJECT_ROOT" -maxdepth 1 -name "*integration*test*.py" -exec mv {} "$TESTS_DIR/integration/" \; 2>/dev/null || true
find "$PROJECT_ROOT" -maxdepth 1 -name "test_all_phases*.py" -exec mv {} "$TESTS_DIR/integration/" \; 2>/dev/null || true

# 階段測試
find "$PROJECT_ROOT" -maxdepth 1 -name "test_phase*.py" -exec mv {} "$TESTS_DIR/phase_tests/" \; 2>/dev/null || true
find "$PROJECT_ROOT" -maxdepth 1 -name "*phase*_complete.py" -exec mv {} "$TESTS_DIR/phase_tests/" \; 2>/dev/null || true

# 驗證測試
find "$PROJECT_ROOT" -maxdepth 1 -name "*verification*.py" -exec mv {} "$TESTS_DIR/verification/" \; 2>/dev/null || true
find "$PROJECT_ROOT" -maxdepth 1 -name "test_coordinate*.py" -exec mv {} "$TESTS_DIR/verification/" \; 2>/dev/null || true
find "$PROJECT_ROOT" -maxdepth 1 -name "simple_test.py" -exec mv {} "$TESTS_DIR/verification/" \; 2>/dev/null || true
find "$PROJECT_ROOT" -maxdepth 1 -name "quick_*.py" -exec mv {} "$TESTS_DIR/verification/" \; 2>/dev/null || true

# 移動 netstack 中的測試文件
find "$PROJECT_ROOT/netstack" -maxdepth 1 -name "test_*.py" -exec mv {} "$TESTS_DIR/verification/" \; 2>/dev/null || true

# 移動測試報告
echo "📊 移動測試報告..."
find "$PROJECT_ROOT" -maxdepth 1 -name "*_results.json" -exec mv {} "$TESTS_DIR/reports/" \; 2>/dev/null || true
find "$PROJECT_ROOT" -maxdepth 1 -name "*_report.json" -exec mv {} "$TESTS_DIR/reports/" \; 2>/dev/null || true
find "$PROJECT_ROOT" -maxdepth 1 -name "*test*.md" -exec mv {} "$TESTS_DIR/reports/" \; 2>/dev/null || true
find "$PROJECT_ROOT" -maxdepth 1 -name "*verification*.md" -exec mv {} "$TESTS_DIR/reports/" \; 2>/dev/null || true

# 恢復重要的文檔到根目錄
mv "$TESTS_DIR/reports/README.md" "$PROJECT_ROOT/" 2>/dev/null || true
mv "$TESTS_DIR/reports/CLAUDE.md" "$PROJECT_ROOT/" 2>/dev/null || true

# 刪除不需要的文件
echo "🗑️  刪除不需要的文件..."

# 刪除根目錄中的測試文件
rm -f "$PROJECT_ROOT"/test_*.py 2>/dev/null || true
rm -f "$PROJECT_ROOT"/quick_*.py 2>/dev/null || true
rm -f "$PROJECT_ROOT"/phase*_*.py 2>/dev/null || true
rm -f "$PROJECT_ROOT"/*_test.py 2>/dev/null || true
rm -f "$PROJECT_ROOT"/*_verification.py 2>/dev/null || true

# 刪除 netstack 中的測試文件
rm -f "$PROJECT_ROOT/netstack"/test_*.py 2>/dev/null || true
rm -f "$PROJECT_ROOT/netstack"/quick_*.py 2>/dev/null || true
rm -f "$PROJECT_ROOT/netstack"/phase*_*.py 2>/dev/null || true
rm -f "$PROJECT_ROOT/netstack"/*_test.py 2>/dev/null || true
rm -f "$PROJECT_ROOT/netstack"/*_verification.py 2>/dev/null || true

# 刪除散落的報告文件
rm -f "$PROJECT_ROOT"/*.json 2>/dev/null || true
rm -f "$PROJECT_ROOT"/*.log 2>/dev/null || true

# 刪除 test_output 目錄（如果存在）
if [ -d "$PROJECT_ROOT/test_output" ]; then
    echo "🗂️  刪除 test_output 目錄..."
    rm -rf "$PROJECT_ROOT/test_output"
fi

# 顯示清理結果
echo "✅ 清理完成！"
echo ""
echo "📊 測試目錄結構："
tree "$TESTS_DIR" 2>/dev/null || ls -la "$TESTS_DIR"

echo ""
echo "🎯 清理摘要："
echo "- 整合測試: $(find "$TESTS_DIR/integration" -name "*.py" | wc -l) 個文件"
echo "- 階段測試: $(find "$TESTS_DIR/phase_tests" -name "*.py" | wc -l) 個文件"
echo "- 驗證測試: $(find "$TESTS_DIR/verification" -name "*.py" | wc -l) 個文件"
echo "- 測試報告: $(find "$TESTS_DIR/reports" -name "*" -type f | wc -l) 個文件"

echo ""
echo "🚀 可以使用以下命令運行測試："
echo "cd $PROJECT_ROOT && python -m pytest tests/ -v"
