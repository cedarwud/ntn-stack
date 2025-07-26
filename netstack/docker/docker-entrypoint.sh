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

# 3. 載入衛星數據
echo "📡 初始化衛星數據載入器..."
python3 -c "
import asyncio
import os
import sys
sys.path.append('/app')

async def load_satellite_data():
    from netstack_api.services.instant_satellite_loader import InstantSatelliteLoader
    
    # 構建數據庫連接字符串 - 修正主機名
    db_host = os.getenv('DB_HOST', 'rl-postgres')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'rl_research')
    db_user = os.getenv('DB_USER', 'rl_user')
    db_password = os.getenv('DB_PASSWORD', 'rl_password')
    
    postgres_url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    
    # 初始化並載入數據
    loader = InstantSatelliteLoader(postgres_url)
    success = await loader.ensure_data_available()
    
    if success:
        print('✅ 衛星數據載入成功，系統準備就緒')
        sys.exit(0)
    else:
        print('❌ 衛星數據載入失敗，請檢查配置')
        sys.exit(1)

# 執行數據載入
asyncio.run(load_satellite_data())
"

# 檢查數據載入結果
if [ $? -eq 0 ]; then
    echo "✅ 衛星數據初始化完成"
else
    echo "⚠️ 衛星數據載入失敗，但容器將繼續啟動"
fi

# 3. 啟動主應用程式
echo "🌟 啟動 NetStack API 服務..."
exec "$@"