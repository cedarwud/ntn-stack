#!/bin/bash

# Claude API 智能重試查詢腳本
# 使用智能重試系統，失敗時自動設定下次重試

SCRIPT_DIR="/home/sat/ntn-stack/claude-auto-query"
LOG_FILE="$SCRIPT_DIR/claude_auto_query.log"

# 使用會讓 Claude 回應 "OK" 的預設查詢
DEFAULT_QUERY="Please respond with exactly 'OK' and nothing else."
QUERY="${1:-$DEFAULT_QUERY}"  # 預設查詢，可從參數覆蓋

echo "[$(date)] 🚀 Claude 智能查詢啟動..." | tee -a "$LOG_FILE"
echo "[$(date)] 🎯 查詢內容: '$QUERY'" | tee -a "$LOG_FILE"

# 檢查環境變數
if [ -z "$ANTHROPIC_BASE_URL" ]; then
    echo "[$(date)] ❌ 缺少 ANTHROPIC_BASE_URL 環境變數" | tee -a "$LOG_FILE"
    exit 1
fi

if [ -z "$ANTHROPIC_AUTH_TOKEN" ]; then
    echo "[$(date)] ❌ 缺少 ANTHROPIC_AUTH_TOKEN 環境變數" | tee -a "$LOG_FILE"
    exit 1
fi

echo "[$(date)] ✅ 環境變數檢查通過" | tee -a "$LOG_FILE"

# 檢查 Python 是否可用
if ! command -v python3 &> /dev/null; then
    echo "[$(date)] ❌ Python3 未安裝" | tee -a "$LOG_FILE"
    exit 1
fi

# 切換到腳本目錄
cd "$SCRIPT_DIR" || exit 1

# 調用智能重試系統
echo "[$(date)] 🧠 啟動智能重試系統..." | tee -a "$LOG_FILE"

# 如果沒有參數，直接執行 Python 腳本 (會使用預設查詢)
# 如果有參數，傳遞參數給 Python 腳本
if [ $# -eq 0 ]; then
    python3 "$SCRIPT_DIR/claude_retry_system.py" 2>&1 | tee -a "$LOG_FILE"
else
    python3 "$SCRIPT_DIR/claude_retry_system.py" "$QUERY" 2>&1 | tee -a "$LOG_FILE"
fi
exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "[$(date)] ✅ 查詢成功完成" | tee -a "$LOG_FILE"
else
    echo "[$(date)] ⏳ 查詢未完成，已設定重試" | tee -a "$LOG_FILE"
fi

echo "[$(date)] 🏁 智能查詢結束" | tee -a "$LOG_FILE"
exit $exit_code