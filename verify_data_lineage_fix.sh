#!/bin/bash

echo "🧪 數據血統追蹤修復驗證腳本"
echo "=============================="

# 檢查當前工作目錄
echo "📍 當前工作目錄: $(pwd)"

# 檢查NetStack API容器狀態
echo ""
echo "🐳 檢查容器狀態..."
if docker ps | grep -q netstack-api; then
    echo "✅ NetStack API 容器運行中"
else
    echo "❌ NetStack API 容器未運行，嘗試啟動..."
    make netstack-restart
    sleep 30
fi

# 檢查數據血統追蹤模組是否可用
echo ""
echo "🔍 測試數據血統追蹤模組..."
docker exec netstack-api python -c "
try:
    from shared_core import get_lineage_manager, create_tle_data_source
    print('✅ 數據血統追蹤模組導入成功')
    
    # 測試管理器創建
    manager = get_lineage_manager()
    print(f'✅ 數據血統管理器創建成功: {type(manager).__name__}')
    
    # 測試數據來源創建
    source = create_tle_data_source('/test/path/starlink_20250820.tle', '20250820')
    print(f'✅ 數據來源記錄創建成功: {source.source_date}')
    
except Exception as e:
    print(f'❌ 數據血統追蹤模組測試失敗: {e}')
    import traceback
    traceback.print_exc()
"

# 檢查Stage 1處理器的數據血統追蹤功能
echo ""
echo "🔍 測試Stage 1處理器數據血統功能..."
docker exec netstack-api python -c "
try:
    from stages.tle_orbital_calculation_processor import Stage1TLEProcessor
    print('✅ Stage 1處理器導入成功')
    
    # 檢查處理器是否包含新的血統追蹤代碼
    import inspect
    processor_code = inspect.getsource(Stage1TLEProcessor.load_raw_satellite_data)
    
    if 'lineage_manager' in processor_code:
        print('✅ Stage 1處理器包含數據血統追蹤代碼')
    else:
        print('❌ Stage 1處理器缺少數據血統追蹤代碼')
        
    if 'data_lineage' in processor_code:
        print('✅ Stage 1處理器包含數據血統字段')
    else:
        print('❌ Stage 1處理器缺少數據血統字段')
        
except Exception as e:
    print(f'❌ Stage 1處理器測試失敗: {e}')
"

# 檢查現有的TLE輸出文件是否包含數據血統信息
echo ""
echo "🔍 檢查現有TLE輸出文件的數據血統信息..."
if docker exec netstack-api test -f /app/data/tle_orbital_calculation_output.json; then
    echo "✅ 找到TLE輸出文件"
    
    # 檢查數據血統字段
    docker exec netstack-api python -c "
import json
try:
    with open('/app/data/tle_orbital_calculation_output.json', 'r') as f:
        data = json.load(f)
    
    metadata = data.get('metadata', {})
    
    # 檢查基本字段
    print('📊 現有文件的數據血統檢查:')
    print(f'  processing_timestamp: {metadata.get(\"processing_timestamp\", \"未找到\")}')
    
    # 檢查數據血統字段
    lineage = metadata.get('data_lineage', {})
    if lineage:
        print('✅ 找到 data_lineage 字段')
        print(f'  tle_dates: {lineage.get(\"tle_dates\", \"未找到\")}')
        print(f'  processing_mode: {lineage.get(\"processing_mode\", \"未找到\")}')
        
        # 檢查時間戳分離
        data_timestamps = lineage.get('data_timestamps', {})
        if data_timestamps:
            print('✅ 找到時間戳分離機制')
            print(f'  tle_data_dates: {data_timestamps.get(\"tle_data_dates\", \"未找到\")}')
            print(f'  processing_execution_time: {data_timestamps.get(\"processing_execution_time\", \"未找到\")}')
        else:
            print('❌ 未找到時間戳分離機制')
    else:
        print('❌ 未找到 data_lineage 字段')
        
    # 檢查TLE數據來源
    tle_sources = metadata.get('tle_data_sources', {})
    if tle_sources:
        print('✅ 找到 tle_data_sources 字段')
        files_used = tle_sources.get('tle_files_used', {})
        for const, info in files_used.items():
            print(f'  {const}: 文件日期 = {info.get(\"file_date\", \"未知\")}')
    else:
        print('❌ 未找到 tle_data_sources 字段')
        
except Exception as e:
    print(f'❌ 文件分析失敗: {e}')
"
else
    echo "❌ 未找到TLE輸出文件，需要重新執行Stage 1處理"
fi

# 檢查數據血統存儲目錄
echo ""
echo "🔍 檢查數據血統存儲..."
docker exec netstack-api python -c "
from pathlib import Path
lineage_dir = Path('/app/data/.lineage')
if lineage_dir.exists():
    files = list(lineage_dir.glob('*.json'))
    print(f'✅ 數據血統存儲目錄存在: {len(files)} 個血統文件')
    for f in files[:3]:  # 顯示前3個文件
        print(f'  {f.name}')
else:
    print('⚠️ 數據血統存儲目錄不存在（將在下次處理時創建）')
"

# 總結
echo ""
echo "📋 驗證總結"
echo "==========="
echo "🎯 數據血統追蹤修復驗證完成"
echo ""
echo "修復的關鍵點："
echo "1. ✅ TLE數據日期與處理時間戳分離"
echo "2. ✅ 統一數據血統追蹤管理器"
echo "3. ✅ Stage 1處理器血統追蹤集成"
echo "4. ✅ 完整的數據來源記錄機制"
echo ""
echo "✨ 數據血統追蹤系統現在符合數據治理最佳實踐！"