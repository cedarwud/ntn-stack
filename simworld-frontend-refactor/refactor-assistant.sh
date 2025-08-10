#!/bin/bash

# SimWorld Frontend 重構執行腳本
# 用於快速開始重構工作

set -e

echo "🚀 SimWorld Frontend 重構助手"
echo "==============================="

# 檢查當前目錄
if [ ! -d "simworld/frontend" ]; then
    echo "❌ 錯誤: 請在 ntn-stack 根目錄執行此腳本"
    exit 1
fi

# 創建備份
BACKUP_DIR="simworld-frontend-backup-$(date +%Y%m%d_%H%M%S)"
echo "📦 創建備份到: $BACKUP_DIR"
cp -r simworld/frontend "$BACKUP_DIR"
echo "✅ 備份完成"

# 顯示重構階段選項
echo ""
echo "📋 請選擇要執行的重構階段:"
echo "1) Phase 1 - 移除過時組件 (推薦先執行)"
echo "2) Phase 2 - 整合重複 API"  
echo "3) Phase 3 - UI 組件優化"
echo "4) Phase 4 - 性能結構優化"
echo "5) 查看分析報告"
echo "6) 退出"

read -p "請輸入選項 (1-6): " choice

case $choice in
    1)
        echo "🔴 準備執行 Phase 1 - 移除過時組件"
        echo ""
        echo "⚠️  將要移除以下組件:"
        echo "   - UAV 群集協調功能"
        echo "   - 預測性維護組件" 
        echo "   - 其他無關分析工具"
        echo ""
        read -p "確認執行? (y/N): " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            echo "🚧 Phase 1 執行需要手動操作，請參考:"
            echo "   simworld-frontend-refactor/phase1-remove-legacy/phase1-plan.md"
        else
            echo "❌ 取消執行"
        fi
        ;;
    2)
        echo "🟡 Phase 2 - 整合重複 API"
        echo "請參考: simworld-frontend-refactor/phase2-consolidate-apis/phase2-plan.md"
        ;;
    3)
        echo "🟡 Phase 3 - UI 組件優化"
        echo "請參考: simworld-frontend-refactor/phase3-cleanup-ui/phase3-plan.md"
        ;;
    4)
        echo "🟢 Phase 4 - 性能結構優化"
        echo "請參考: simworld-frontend-refactor/phase4-optimize-structure/phase4-plan.md"
        ;;
    5)
        echo "📊 分析報告"
        if [ -f "simworld-frontend-refactor/component-analysis.md" ]; then
            echo "查看詳細分析: simworld-frontend-refactor/component-analysis.md"
        else
            echo "❌ 分析報告未找到"
        fi
        ;;
    6)
        echo "👋 退出重構助手"
        exit 0
        ;;
    *)
        echo "❌ 無效選項"
        exit 1
        ;;
esac

echo ""
echo "📚 完整重構計劃請查看: simworld-frontend-refactor/README.md"
echo "🔧 備份位置: $BACKUP_DIR"
