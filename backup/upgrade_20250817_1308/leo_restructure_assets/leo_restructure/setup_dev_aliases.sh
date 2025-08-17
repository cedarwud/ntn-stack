#!/bin/bash
# 🛠️ LEO重構開發工具別名設置腳本
# 根據 DEVELOPMENT_STRATEGY.md 創建開發別名

echo "🛠️ 設置LEO重構開發工具別名..."

# 檢查是否在正確目錄
if [ ! -f "run_phase1.py" ]; then
    echo "❌ 錯誤: 請在leo_restructure目錄中執行此腳本"
    exit 1
fi

# 獲取當前目錄的絕對路徑
LEO_DIR=$(pwd)

# 創建別名配置檔案
ALIAS_FILE="$HOME/.leo_dev_aliases"

cat > "$ALIAS_FILE" << 'EOF'
# 🛰️ LEO重構系統開發別名
# 由 setup_dev_aliases.sh 自動生成

# 切換到LEO重構目錄
alias leo-cd='cd /home/sat/ntn-stack/leo_restructure'

# Stage D1: 超快速開發模式 (30-60秒)
alias leo-dev='cd /home/sat/ntn-stack/leo_restructure && python run_phase1.py --ultra-fast --auto-cleanup'

# Stage D2: 開發驗證模式 (3-5分鐘)  
alias leo-test='cd /home/sat/ntn-stack/leo_restructure && python run_phase1.py --dev-mode --auto-cleanup'

# Stage D3: 全量測試模式 (10-15分鐘)
alias leo-full='cd /home/sat/ntn-stack/leo_restructure && python run_phase1.py --full-test --auto-cleanup'

# Stage D4: 容器建構驗證 (20-30分鐘)
alias leo-build='cd /home/sat/ntn-stack && make down-v && make build-n && make up'

# 一鍵開發流程 (依序執行所有階段)
alias leo-workflow='leo-dev && echo "✅ D1完成" && leo-test && echo "✅ D2完成" && leo-full && echo "✅ D3完成" && leo-build && echo "✅ D4完成"'

# 快速清理
alias leo-clean='cd /home/sat/ntn-stack/leo_restructure && python -c "from shared_core.auto_cleanup_manager import create_auto_cleanup_manager; manager = create_auto_cleanup_manager(); manager.cleanup_before_run(\"all\")"'

# 增量更新檢查
alias leo-check='cd /home/sat/ntn-stack/leo_restructure && python -c "from shared_core.incremental_update_manager import create_incremental_update_manager; manager = create_incremental_update_manager(); changes = manager.detect_changes(); strategy = manager.suggest_update_strategy(changes); print(f\"建議策略: {strategy}\")"'

# 顯示統計信息
alias leo-stats='cd /home/sat/ntn-stack/leo_restructure && python shared_core/auto_cleanup_manager.py --stats && python shared_core/incremental_update_manager.py --stats'

# 快速測試 (限制衛星數量)
alias leo-quick='cd /home/sat/ntn-stack/leo_restructure && python run_phase1.py --ultra-fast --auto-cleanup --satellites-limit 5'

# 增量模式
alias leo-inc='cd /home/sat/ntn-stack/leo_restructure && python run_phase1.py --incremental --auto-cleanup'

# 故障排除模式
alias leo-debug='cd /home/sat/ntn-stack/leo_restructure && python run_phase1.py --ultra-fast --auto-cleanup --verbose'

# 顯示幫助
alias leo-help='echo "
🛰️ LEO重構系統開發別名

🚀 開發模式:
  leo-dev      - Stage D1: 超快速開發 (30-60秒)
  leo-test     - Stage D2: 開發驗證 (3-5分鐘)  
  leo-full     - Stage D3: 全量測試 (10-15分鐘)
  leo-build    - Stage D4: 容器建構 (20-30分鐘)
  leo-workflow - 一鍵完整流程

🛠️ 工具:
  leo-clean    - 清理舊數據
  leo-check    - 檢查更新策略
  leo-stats    - 顯示統計信息
  leo-quick    - 5顆衛星快速測試
  leo-inc      - 增量更新模式
  leo-debug    - 故障排除模式

📂 導航:
  leo-cd       - 切換到LEO目錄
  leo-help     - 顯示此幫助
"'

EOF

# 檢查shell類型並添加到相應配置檔案
SHELL_NAME=$(basename "$SHELL")

case "$SHELL_NAME" in
    "bash")
        SHELL_RC="$HOME/.bashrc"
        ;;
    "zsh")
        SHELL_RC="$HOME/.zshrc"
        ;;
    *)
        SHELL_RC="$HOME/.profile"
        ;;
esac

# 檢查是否已經添加過
if ! grep -q "leo_dev_aliases" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "# LEO重構系統開發別名" >> "$SHELL_RC"
    echo "if [ -f \"$ALIAS_FILE\" ]; then" >> "$SHELL_RC"
    echo "    source \"$ALIAS_FILE\"" >> "$SHELL_RC"
    echo "fi" >> "$SHELL_RC"
    
    echo "✅ 別名已添加到 $SHELL_RC"
else
    echo "📝 別名配置已存在於 $SHELL_RC"
fi

echo "✅ 別名配置檔案已創建: $ALIAS_FILE"
echo ""
echo "🔄 請執行以下命令重新載入別名："
echo "  source $SHELL_RC"
echo ""
echo "或者重新打開終端機"
echo ""
echo "📋 使用 'leo-help' 查看所有可用別名"
echo ""
echo "🚀 快速開始："
echo "  leo-dev    # 30秒快速測試"
echo "  leo-test   # 5分鐘開發驗證"
echo "  leo-full   # 15分鐘完整測試"