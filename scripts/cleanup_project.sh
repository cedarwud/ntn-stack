#!/bin/bash
# NTN Stack 專案清理腳本
# 移除不必要的檔案和目錄，優化專案結構

set -e

echo "🧹 開始清理 NTN Stack 專案..."

# 清理 venv 目錄（在 Docker 環境中不需要）
echo "📁 清理本地 venv 目錄..."
find . -name "venv" -type d -exec rm -rf {} + 2>/dev/null || true

# 清理 __pycache__ 目錄
echo "🐍 清理 Python 快取..."
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 清理 .pytest_cache 目錄
echo "🧪 清理 pytest 快取..."
find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true

# 清理測試報告
echo "📊 清理測試報告..."
find . -name "test-reports" -type d -exec rm -rf {} + 2>/dev/null || true
find . -path "*/tests/reports" -type d -exec rm -rf {} + 2>/dev/null || true

# 清理日誌檔案
echo "📝 清理日誌檔案..."
find . -name "*.log" -type f -delete 2>/dev/null || true

# 清理 Docker 相關檔案
echo "🐳 清理 Docker 快取..."
docker system prune -f 2>/dev/null || echo "Docker 未運行，跳過清理"

# 清理 Node.js 相關（如果存在）
echo "📦 清理 Node.js 快取..."
find . -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null || true

echo "✅ 專案清理完成！"
echo ""
echo "📋 建議接下來執行："
echo "  make build    # 重新建置服務"
echo "  make up       # 啟動服務"
echo "  make status   # 檢查狀態" 