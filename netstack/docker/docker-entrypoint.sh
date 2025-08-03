#!/bin/bash
set -e

# NetStack API 容器啟動腳本
# 確保衛星數據在啟動時立即可用

echo "🚀 NetStack API 容器啟動中..."

# 1. 等待 MongoDB 準備就緒
echo "⏳ 等待 MongoDB 數據庫準備..."
while ! nc -z mongo 27017; do
    echo "  MongoDB 尚未就緒，等待 3 秒..."
    sleep 3
done
echo "✅ MongoDB 連接正常"

# 2. 檢查衛星數據狀態（可選）
echo "📡 衛星數據將由 API 背景任務自動載入"
echo "✅ FastAPI 將快速啟動，衛星數據在背景處理中"

# 3. 啟動主應用程式
echo "🌟 啟動 NetStack API 服務..."
exec "$@"