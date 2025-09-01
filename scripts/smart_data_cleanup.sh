#!/bin/bash
# 智能數據清理腳本
# 用途: 定期清理大型臨時文件，保留重要數據

ACTIVE_DATA_DIR="/home/sat/ntn-stack/data"
LOG_FILE="$ACTIVE_DATA_DIR/.cleanup_log"

# 記錄清理開始
echo "$(date): 開始智能清理" >> "$LOG_FILE"

# 清理7天前的大型備份文件 (>100MB)
find "$ACTIVE_DATA_DIR" -name "*.json" -size +100M -mtime +7 -exec rm -f {} \; -exec echo "$(date): 清理過期大型文件 {}" \; >> "$LOG_FILE" 2>/dev/null

# 清理30天前的日誌文件
find "$ACTIVE_DATA_DIR" -name "*.log" -mtime +30 -delete 2>/dev/null

# 壓縮14天前的中等大小文件 (10-100MB)
find "$ACTIVE_DATA_DIR" -name "*.json" -size +10M -size -100M -mtime +14 -exec gzip {} \; 2>/dev/null

echo "$(date): 智能清理完成" >> "$LOG_FILE"