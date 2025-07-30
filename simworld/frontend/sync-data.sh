#!/bin/bash

# 同步 NetStack 預計算數據到 Frontend
# 用於支援 D2 事件圖表的真實數據模式

NETSTACK_DATA_DIR="/home/sat/ntn-stack/netstack/data"
FRONTEND_DATA_DIR="/home/sat/ntn-stack/simworld/frontend/public/data"

echo "🔄 開始同步 NetStack 預計算數據..."

# 創建目標目錄
mkdir -p "$FRONTEND_DATA_DIR"

# 同步主要預計算文件
if [ -f "$NETSTACK_DATA_DIR/phase0_precomputed_orbits.json" ]; then
    cp "$NETSTACK_DATA_DIR/phase0_precomputed_orbits.json" "$FRONTEND_DATA_DIR/"
    echo "✅ 同步 phase0_precomputed_orbits.json"
else
    echo "⚠️  未找到 phase0_precomputed_orbits.json"
fi

# 同步分層分析數據
if [ -d "$NETSTACK_DATA_DIR/layered_phase0" ]; then
    cp -r "$NETSTACK_DATA_DIR/layered_phase0" "$FRONTEND_DATA_DIR/"
    echo "✅ 同步 layered_phase0/ 目錄"
else
    echo "⚠️  未找到 layered_phase0/ 目錄"
fi

# 同步其他相關文件
for file in "phase0_data_summary.json" "phase0_rl_dataset_metadata.json"; do
    if [ -f "$NETSTACK_DATA_DIR/$file" ]; then
        cp "$NETSTACK_DATA_DIR/$file" "$FRONTEND_DATA_DIR/"
        echo "✅ 同步 $file"
    fi
done

echo "🎉 NetStack 數據同步完成！"
echo "📁 同步的文件位於: $FRONTEND_DATA_DIR"
echo "🌐 前端可通過 /data/ 路徑訪問這些文件"