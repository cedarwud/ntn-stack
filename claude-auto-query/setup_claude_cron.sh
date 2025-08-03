#!/bin/bash

# Claude API 智能重試定時查詢設定腳本

echo "⏰ 設定 Claude API 智能重試定時查詢..."
echo "🧠 系統會自動重試失敗的查詢，直到收到 'OK' 回應"
echo ""

# 檢查必要檔案
SCRIPT_DIR="/home/sat/ntn-stack/claude-auto-query"
QUERY_SCRIPT="$SCRIPT_DIR/claude_auto_query.sh"
PYTHON_SCRIPT="$SCRIPT_DIR/claude_api_caller.py"
RETRY_SCRIPT="$SCRIPT_DIR/claude_retry_system.py"

if [ ! -f "$QUERY_SCRIPT" ] || [ ! -f "$PYTHON_SCRIPT" ] || [ ! -f "$RETRY_SCRIPT" ]; then
    echo "❌ 缺少必要檔案，請確認以下檔案存在："
    echo "   - $QUERY_SCRIPT"
    echo "   - $PYTHON_SCRIPT"
    echo "   - $RETRY_SCRIPT"
    exit 1
fi

# 確保腳本可執行
chmod +x "$QUERY_SCRIPT" "$PYTHON_SCRIPT" "$RETRY_SCRIPT"

# 檢查環境變數
echo "🔍 檢查環境變數..."
if [ -z "$ANTHROPIC_BASE_URL" ]; then
    echo "❌ 缺少 ANTHROPIC_BASE_URL 環境變數"
    echo "💡 請設定: export ANTHROPIC_BASE_URL=你的API端點"
    exit 1
fi

if [ -z "$ANTHROPIC_AUTH_TOKEN" ]; then
    echo "❌ 缺少 ANTHROPIC_AUTH_TOKEN 環境變數"
    echo "💡 請設定: export ANTHROPIC_AUTH_TOKEN=你的認證Token"
    exit 1
fi

echo "✅ 環境變數檢查通過"
echo "🔗 API 端點: $ANTHROPIC_BASE_URL"
echo ""

# 選擇一次性執行時間
echo "📋 選擇一次性執行時間 (只執行一次，失敗才會自動重試)："
echo "1. 1個小時後"
echo "2. 2個小時後"
echo "3. 3個小時後"
echo "4. 4個小時後"
echo "5. 5個小時後"
echo "6. 自訂 (幾個小時後)"
echo "7. 退出設定"

read -p "請選擇 (1-7): " choice

case $choice in
    1) HOURS_LATER=1; DESC="1個小時後" ;;
    2) HOURS_LATER=2; DESC="2個小時後" ;;
    3) HOURS_LATER=3; DESC="3個小時後" ;;
    4) HOURS_LATER=4; DESC="4個小時後" ;;
    5) HOURS_LATER=5; DESC="5個小時後" ;;
    6) 
        read -p "請輸入幾個小時後執行 (1-24): " CUSTOM_HOURS
        if [[ "$CUSTOM_HOURS" =~ ^[1-9][0-9]?$ ]] && [ "$CUSTOM_HOURS" -le 24 ]; then
            HOURS_LATER=$CUSTOM_HOURS
            DESC="${CUSTOM_HOURS}個小時後"
        else
            echo "❌ 無效輸入，使用預設：1個小時後"
            HOURS_LATER=1
            DESC="1個小時後"
        fi
        ;;
    7) 
        echo "❌ 退出設定"
        exit 0
        ;;
    *) 
        echo "❌ 無效選項，使用預設：1個小時後"
        HOURS_LATER=1
        DESC="1個小時後"
        ;;
esac

# 計算執行時間
EXECUTE_TIME=$(date -d "+${HOURS_LATER} hours" '+%M %H %d %m *')
EXECUTE_TIME_DISPLAY=$(date -d "+${HOURS_LATER} hours" '+%Y-%m-%d %H:%M')
CRON_EXPR="$EXECUTE_TIME"

# 設定查詢內容 - 直接使用預設查詢
echo ""
echo "💬 查詢內容設定："
echo "系統會使用預設查詢 'Please respond with exactly \"OK\" and nothing else.'"
echo "這確保 Claude 會回應 'OK'，讓重試系統正常運作"

QUERY=""  # 空字串表示使用預設查詢
echo "🤖 使用預設查詢 (系統會自動處理)"

# 建立 cron 命令
ENV_VARS="ANTHROPIC_BASE_URL='$ANTHROPIC_BASE_URL' ANTHROPIC_AUTH_TOKEN='$ANTHROPIC_AUTH_TOKEN'"

# 如果使用預設查詢 (空字串)，不傳遞參數給腳本
if [ -z "$QUERY" ]; then
    CRON_CMD="$CRON_EXPR cd $SCRIPT_DIR && $ENV_VARS $QUERY_SCRIPT >> $SCRIPT_DIR/claude_cron.log 2>&1"
else
    CRON_CMD="$CRON_EXPR cd $SCRIPT_DIR && $ENV_VARS $QUERY_SCRIPT '$QUERY' >> $SCRIPT_DIR/claude_cron.log 2>&1"
fi

echo ""
echo "📝 即將添加的一次性任務："
echo "執行時間: $DESC ($EXECUTE_TIME_DISPLAY)"
if [ -z "$QUERY" ]; then
    echo "查詢: 預設查詢 (Please respond with exactly 'OK' and nothing else.)"
else
    echo "查詢: $QUERY"
fi
echo "Cron 表達式: $CRON_EXPR"
echo "⚠️  注意：這是一次性任務，只有失敗時才會自動重試"

read -p "確認添加？ (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "❌ 取消設定"
    exit 1
fi

# 更新 crontab
crontab -l > /tmp/crontab_backup 2>/dev/null || touch /tmp/crontab_backup

# 移除舊的 claude 任務
grep -v "claude_auto_query\|claude_api_trigger" /tmp/crontab_backup > /tmp/new_crontab

# 添加新任務
echo "$CRON_CMD" >> /tmp/new_crontab

# 安裝新的 crontab
crontab /tmp/new_crontab

echo ""
echo "✅ 一次性智能重試任務設定完成！"
echo "📅 執行時間: $DESC ($EXECUTE_TIME_DISPLAY)"
if [ -z "$QUERY" ]; then
    echo "💬 查詢內容: 預設查詢 (確保回應 'OK')"
else
    echo "💬 查詢內容: '$QUERY'"
fi
echo "🧠 重試邏輯: 只執行一次，失敗時自動重試 (1小時、2小時、3小時...)"
echo "📝 主要日誌: $SCRIPT_DIR/claude_cron.log"
echo "🔍 重試日誌: $SCRIPT_DIR/claude_retry.log"

echo ""
echo "💡 管理指令："
echo "  查看主要日誌: tail -f $SCRIPT_DIR/claude_cron.log"
echo "  查看重試日誌: tail -f $SCRIPT_DIR/claude_retry.log"
echo "  查看所有任務: crontab -l"
echo "  移除任務: crontab -l | grep -v claude_auto_query | grep -v claude_retry_system | crontab -"
echo "  查看重試狀態: cat $SCRIPT_DIR/retry_state.json"

# 清理
rm /tmp/crontab_backup /tmp/new_crontab

echo ""
echo "🧪 系統說明："
echo "• 一次性任務：只在指定時間執行一次"
echo "• 如果查詢成功並收到 'OK' 回應 → 任務完成，不再執行"
echo "• 如果查詢失敗或未收到 'OK' 回應 → 自動設定重試任務"
echo "• 重試間隔遞增：1小時後、2小時後、3小時後..."
echo "• 重試會持續到成功為止"

echo ""
read -p "是否立即測試一次？ (y/N): " test_now
if [[ $test_now =~ ^[Yy]$ ]]; then
    echo "🧪 執行測試..."
    cd "$SCRIPT_DIR"
    if [ -z "$QUERY" ]; then
        eval "$ENV_VARS bash $QUERY_SCRIPT"
    else
        eval "$ENV_VARS bash $QUERY_SCRIPT '$QUERY'"
    fi
fi