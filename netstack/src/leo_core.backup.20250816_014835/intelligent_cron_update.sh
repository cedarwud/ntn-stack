#!/bin/bash
# 🕒 LEO重構系統智能Cron更新腳本
# 根據 DEVELOPMENT_STRATEGY.md 實現智能增量更新

# 設置日誌
LOG_FILE="/tmp/intelligent_update.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "🕒 $(date '+%Y-%m-%d %H:%M:%S') - 開始智能增量更新檢查..."

# 檢查必要環境
if [ ! -d "/home/sat/ntn-stack/leo_restructure" ]; then
    echo "❌ LEO重構目錄不存在: /home/sat/ntn-stack/leo_restructure"
    exit 1
fi

cd /home/sat/ntn-stack/leo_restructure

# 檢查Python環境
if ! python -c "import sys; print(f'Python {sys.version}')" 2>/dev/null; then
    echo "❌ Python環境不可用"
    exit 1
fi

# 檢查關鍵模組
if ! python -c "from shared_core.incremental_update_manager import create_incremental_update_manager" 2>/dev/null; then
    echo "❌ 增量更新管理器模組不可用"
    exit 1
fi

echo "✅ 環境檢查通過"

# 1. 檢測變更並獲取建議策略
echo "🔍 檢測系統變更..."

UPDATE_STRATEGY=$(python -c "
from shared_core.incremental_update_manager import create_incremental_update_manager
import sys

try:
    manager = create_incremental_update_manager()
    changes = manager.detect_changes()
    strategy = manager.suggest_update_strategy(changes)
    print(strategy)
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
")

if [ $? -ne 0 ]; then
    echo "❌ 變更檢測失敗"
    exit 1
fi

echo "💡 檢測結果: $UPDATE_STRATEGY"

# 2. 根據策略執行相應的更新
case "$UPDATE_STRATEGY" in
    "no_update_needed")
        echo "📝 無需更新，系統數據為最新"
        echo "✅ $(date '+%Y-%m-%d %H:%M:%S') - 智能更新檢查完成 (無需更新)"
        ;;
    
    "tle_incremental")
        echo "📡 執行TLE增量更新..."
        start_time=$(date +%s)
        
        if python run_phase1.py --incremental --auto-cleanup --tle-only 2>&1 | tee -a "$LOG_FILE"; then
            end_time=$(date +%s)
            duration=$((end_time - start_time))
            echo "✅ TLE增量更新完成 (${duration}秒)"
        else
            echo "❌ TLE增量更新失敗"
            exit 1
        fi
        ;;
    
    "code_incremental")
        echo "💻 執行代碼增量更新..."
        start_time=$(date +%s)
        
        if python run_phase1.py --incremental --auto-cleanup --code-only 2>&1 | tee -a "$LOG_FILE"; then
            end_time=$(date +%s)
            duration=$((end_time - start_time))
            echo "✅ 代碼增量更新完成 (${duration}秒)"
        else
            echo "❌ 代碼增量更新失敗"
            exit 1
        fi
        ;;
    
    "config_incremental")
        echo "⚙️ 執行配置增量更新..."
        start_time=$(date +%s)
        
        if python run_phase1.py --incremental --auto-cleanup --config-only 2>&1 | tee -a "$LOG_FILE"; then
            end_time=$(date +%s)
            duration=$((end_time - start_time))
            echo "✅ 配置增量更新完成 (${duration}秒)"
        else
            echo "❌ 配置增量更新失敗"
            exit 1
        fi
        ;;
    
    "hybrid_incremental")
        echo "🔀 執行混合增量更新..."
        start_time=$(date +%s)
        
        if python run_phase1.py --dev-mode --auto-cleanup --incremental 2>&1 | tee -a "$LOG_FILE"; then
            end_time=$(date +%s)
            duration=$((end_time - start_time))
            echo "✅ 混合增量更新完成 (${duration}秒)"
        else
            echo "❌ 混合增量更新失敗"
            exit 1
        fi
        ;;
    
    "output_refresh")
        echo "📊 執行輸出刷新..."
        start_time=$(date +%s)
        
        if python run_phase1.py --ultra-fast --auto-cleanup 2>&1 | tee -a "$LOG_FILE"; then
            end_time=$(date +%s)
            duration=$((end_time - start_time))
            echo "✅ 輸出刷新完成 (${duration}秒)"
        else
            echo "❌ 輸出刷新失敗"
            exit 1
        fi
        ;;
    
    "full_rebuild")
        echo "🔄 執行完整重建..."
        start_time=$(date +%s)
        
        if python run_phase1.py --full-test --auto-cleanup 2>&1 | tee -a "$LOG_FILE"; then
            end_time=$(date +%s)
            duration=$((end_time - start_time))
            echo "✅ 完整重建完成 (${duration}秒)"
        else
            echo "❌ 完整重建失敗"
            exit 1
        fi
        ;;
    
    *)
        echo "⚠️ 未知更新策略: $UPDATE_STRATEGY"
        echo "🔄 回退到安全模式..."
        
        if python run_phase1.py --ultra-fast --auto-cleanup 2>&1 | tee -a "$LOG_FILE"; then
            echo "✅ 安全模式執行完成"
        else
            echo "❌ 安全模式執行失敗"
            exit 1
        fi
        ;;
esac

# 3. 更新統計和清理
echo "📊 更新執行統計..."

# 清理過期日誌（保留7天）
find /tmp -name "intelligent_update*.log" -type f -mtime +7 -delete 2>/dev/null

# 清理過期臨時檔案
find /tmp -name "leo_*.tmp" -type f -mtime +1 -delete 2>/dev/null

# 記錄成功完成
echo "✅ $(date '+%Y-%m-%d %H:%M:%S') - 智能增量更新成功完成 (策略: $UPDATE_STRATEGY)"

# 4. 可選：發送通知 (如果配置了通知系統)
if [ -f "/home/sat/ntn-stack/scripts/send_notification.sh" ]; then
    /home/sat/ntn-stack/scripts/send_notification.sh "LEO重構智能更新" "策略: $UPDATE_STRATEGY 執行成功" 2>/dev/null || true
fi

echo "📋 最近5次更新記錄："
tail -n 20 "$LOG_FILE" | grep "智能增量更新.*完成" | tail -n 5