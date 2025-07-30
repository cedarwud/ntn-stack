#!/bin/bash

# NetStack 數據統一同步腳本
# 將 NetStack 預計算數據同步到需要的所有位置

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

NETSTACK_DATA_DIR="$PROJECT_ROOT/netstack/data"
SIMWORLD_FRONTEND_DATA_DIR="$PROJECT_ROOT/simworld/frontend/public/data"

echo "🔄 NetStack 數據統一同步開始..."
echo "📁 源目錄: $NETSTACK_DATA_DIR"
echo "📁 目標目錄: $SIMWORLD_FRONTEND_DATA_DIR"

# 檢查源目錄是否存在
if [ ! -d "$NETSTACK_DATA_DIR" ]; then
    echo "❌ NetStack 數據目錄不存在: $NETSTACK_DATA_DIR"
    echo "💡 請先運行 NetStack 建置流程生成預計算數據"
    exit 1
fi

# 創建目標目錄
mkdir -p "$SIMWORLD_FRONTEND_DATA_DIR"

# 定義需要同步的文件和目錄
SYNC_ITEMS=(
    "phase0_precomputed_orbits.json"
    "phase0_data_summary.json"
    "phase0_rl_dataset_metadata.json"
    "phase0_build_config.json"
    "layered_phase0/"
)

# 同步文件
for item in "${SYNC_ITEMS[@]}"; do
    SOURCE_PATH="$NETSTACK_DATA_DIR/$item"
    TARGET_PATH="$SIMWORLD_FRONTEND_DATA_DIR/$item"
    
    if [ -f "$SOURCE_PATH" ]; then
        cp "$SOURCE_PATH" "$TARGET_PATH"
        echo "✅ 同步文件: $item"
    elif [ -d "$SOURCE_PATH" ]; then
        cp -r "$SOURCE_PATH" "$TARGET_PATH"
        echo "✅ 同步目錄: $item"
    else
        echo "⚠️  跳過不存在的項目: $item"
    fi
done

# 檢查同步結果
echo ""
echo "📊 同步結果檢查:"
for item in "${SYNC_ITEMS[@]}"; do
    TARGET_PATH="$SIMWORLD_FRONTEND_DATA_DIR/$item"
    if [ -e "$TARGET_PATH" ]; then
        SIZE=$(du -sh "$TARGET_PATH" | cut -f1)
        echo "  ✅ $item ($SIZE)"
    else
        echo "  ❌ $item (未找到)"
    fi
done

echo ""
echo "🎉 NetStack 數據同步完成！"
echo "📖 使用說明:"
echo "  - 前端可通過 /data/ 路徑訪問這些文件"
echo "  - 建議在 NetStack 數據更新後重新運行此腳本"
echo "  - 可將此腳本加入到建置流程中實現自動同步"