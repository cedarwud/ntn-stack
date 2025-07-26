#!/bin/bash
set -e

# NetStack API 容器啟動腳本
# 確保衛星數據在啟動時立即可用

echo "🚀 NetStack API 容器啟動中..."

# 1. 等待 PostgreSQL 準備就緒
echo "⏳ 等待 PostgreSQL 數據庫準備..."
while ! nc -z ${DB_HOST:-rl-postgres} ${DB_PORT:-5432}; do
    echo "  PostgreSQL 尚未就緒，等待 3 秒..."
    sleep 3
done
echo "✅ PostgreSQL 連接正常"

# 2. 先初始化資料庫表結構
echo "🗄️ 初始化資料庫表結構..."
python3 -c "
import asyncio
import sys
sys.path.append('/app')

async def init_database():
    from netstack_api.services.database_init import ensure_database_initialized
    success = await ensure_database_initialized()
    if success:
        print('✅ 資料庫表結構初始化完成')
    else:
        print('❌ 資料庫表結構初始化失敗')
        sys.exit(1)

asyncio.run(init_database())
"

# 檢查資料庫初始化結果
if [ $? -eq 0 ]; then
    echo "✅ 資料庫初始化成功"
else
    echo "❌ 資料庫初始化失敗，停止啟動"
    exit 1
fi

# 3. 檢查衛星數據狀態（可選）
echo "📡 衛星數據將由 API 背景任務自動載入"
echo "✅ FastAPI 將快速啟動，衛星數據在背景處理中"

# 3. 啟動主應用程式
echo "🌟 啟動 NetStack API 服務..."
exec "$@"