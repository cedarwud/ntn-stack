#!/bin/bash

# Dashboard 啟動檢查腳本
echo "🔍 檢查 Dashboard 狀態..."

# 檢查配置檔案
if [ -f "dashboard.config.js" ]; then
    echo "✅ Dashboard 配置檔案存在"
else
    echo "❌ Dashboard 配置檔案缺失"
    exit 1
fi

# 檢查路由配置
if [ -f "simworld/frontend/src/main.tsx" ]; then
    if grep -q "NTNStackDashboard" "simworld/frontend/src/main.tsx"; then
        echo "✅ Dashboard 路由配置正確"
    else
        echo "❌ Dashboard 路由配置錯誤"
        exit 1
    fi
else
    echo "❌ 找不到 main.tsx 檔案"
    exit 1
fi

echo "🎉 Dashboard 配置檢查通過！"
