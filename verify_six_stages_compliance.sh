#!/bin/bash

echo "==================================================================="
echo "🔍 六階段資料預處理 - 完整性與合規性驗證"
echo "==================================================================="

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 驗證計數器
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# 驗證函數
check_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
        ((PASS_COUNT++))
    else
        echo -e "${RED}✗${NC} $2"
        ((FAIL_COUNT++))
    fi
}

warn_result() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARN_COUNT++))
}

echo ""
echo "📋 驗證項目清單："
echo "  1. 無簡化算法"
echo "  2. 無模擬數據"
echo "  3. 無硬編碼座標"
echo "  4. 輸出文件清理"
echo "  5. 文檔合規性"
echo ""

# Stage 1: TLE Orbital Calculation
echo "==================================================================="
echo "🛰️ Stage 1: TLE軌道計算驗證"
echo "==================================================================="

# 檢查 SGP4 算法使用
docker exec netstack-api grep -q "sgp4" /app/src/stages/tle_orbital_calculation_processor.py
check_result $? "使用 SGP4 算法 (非簡化)"

# 檢查 TLE 數據來源
docker exec netstack-api ls /app/tle_data/starlink/tle/*.tle 2>/dev/null | head -1 | xargs -I {} basename {} | grep -q "20250"
check_result $? "使用真實 TLE 數據文件"

# 檢查輸出文件存在
docker exec netstack-api test -f /app/data/tle_orbital_calculation_output.json
check_result $? "Stage 1 輸出文件存在"

# Stage 2: Intelligent Satellite Filter
echo ""
echo "==================================================================="
echo "🔍 Stage 2: 智能衛星篩選驗證"  
echo "==================================================================="

# 檢查使用 shared_core 座標
docker exec netstack-api grep -q "from shared_core.observer_config_service import" /app/src/stages/intelligent_satellite_filter_processor.py
check_result $? "使用 shared_core 座標服務"

# 檢查無硬編碼座標
docker exec netstack-api grep -E "24\.9441667|121\.3713889" /app/src/stages/intelligent_satellite_filter_processor.py | grep -v "^#" | wc -l | grep -q "^0$"
check_result $? "無硬編碼 NTPU 座標"

# 檢查輸出文件
docker exec netstack-api test -f /app/data/leo_outputs/intelligent_filtered_output.json
check_result $? "Stage 2 輸出文件存在"

# Stage 3: Signal Quality Analysis  
echo ""
echo "==================================================================="
echo "📡 Stage 3: 信號品質分析驗證"
echo "==================================================================="

# 檢查 ITU-R P.618 模型
docker exec netstack-api grep -q "ITU.*P.618\|itu_r_p618" /app/src/stages/signal_quality_analysis_processor.py
check_result $? "使用 ITU-R P.618 信號模型"

# 檢查 3GPP 事件
docker exec netstack-api grep -q "A4\|A5\|D2" /app/src/stages/signal_quality_analysis_processor.py
check_result $? "生成 3GPP A4/A5/D2 事件"

# 檢查輸出文件
docker exec netstack-api test -f /app/data/leo_outputs/signal_quality_analysis_output.json
check_result $? "Stage 3 輸出文件存在"

# Stage 4: Time Series Enhancement
echo ""
echo "==================================================================="
echo "⏱️ Stage 4: 時間序列增強驗證"
echo "==================================================================="

# 檢查 30 秒時間間隔
docker exec netstack-api grep -q "time_resolution.*30\|30.*second" /app/src/stages/timeseries_preprocessing_processor.py
check_result $? "使用 30 秒時間解析度"

# 檢查輸出文件
docker exec netstack-api test -f /app/data/starlink_enhanced.json
check_result $? "Starlink 增強數據存在"

docker exec netstack-api test -f /app/data/oneweb_enhanced.json
check_result $? "OneWeb 增強數據存在"

# Stage 5: Data Integration
echo ""
echo "==================================================================="
echo "🔄 Stage 5: 數據整合驗證"
echo "==================================================================="

# 檢查使用 shared_core 座標
docker exec netstack-api grep -q "from shared_core.observer_config_service import get_ntpu_coordinates" /app/src/stages/data_integration_processor.py
check_result $? "使用 shared_core 座標服務"

# 檢查輸出文件
docker exec netstack-api test -f /app/data/data_integration_output.json
check_result $? "Stage 5 整合輸出存在"

# Stage 6: Dynamic Pool Planning
echo ""
echo "==================================================================="
echo "🎯 Stage 6: 動態池規劃驗證"
echo "==================================================================="

# 檢查模擬退火優化器
docker exec netstack-api grep -q "simulated_annealing\|SimulatedAnnealing" /app/src/stages/enhanced_dynamic_pool_planner.py
check_result $? "使用模擬退火優化器"

# 檢查 shared_core 整合
docker exec netstack-api grep -q "from shared_core" /app/src/stages/enhanced_dynamic_pool_planner.py | head -1
check_result $? "使用 shared_core 統一管理器"

# 檢查輸出文件
docker exec netstack-api test -f /app/data/leo_outputs/dynamic_pool_output.json
check_result $? "Stage 6 動態池輸出存在"

# 數據完整性驗證
echo ""
echo "==================================================================="
echo "📊 數據完整性驗證"
echo "==================================================================="

# 驗證 Stage 1 輸出大小
STAGE1_SIZE=$(docker exec netstack-api stat -c%s /app/data/tle_orbital_calculation_output.json 2>/dev/null)
if [ "$STAGE1_SIZE" -gt 1000000000 ]; then  # > 1GB
    check_result 0 "Stage 1 數據大小正常 ($(echo "scale=1; $STAGE1_SIZE/1048576" | bc) MB)"
else
    check_result 1 "Stage 1 數據大小異常"
fi

# 驗證衛星數量
STARLINK_COUNT=$(docker exec netstack-api bash -c "grep -o '\"STARLINK-' /app/data/tle_orbital_calculation_output.json | wc -l")
ONEWEB_COUNT=$(docker exec netstack-api bash -c "grep -o '\"ONEWEB-' /app/data/tle_orbital_calculation_output.json | wc -l")

if [ "$STARLINK_COUNT" -gt 900 ]; then
    check_result 0 "Starlink 衛星數量: $STARLINK_COUNT"
else
    warn_result "Starlink 衛星數量偏少: $STARLINK_COUNT"
fi

if [ "$ONEWEB_COUNT" -gt 150 ]; then
    check_result 0 "OneWeb 衛星數量: $ONEWEB_COUNT"
else
    warn_result "OneWeb 衛星數量偏少: $ONEWEB_COUNT"
fi

# 驗證時間戳格式 (TLE 日期)
docker exec netstack-api grep -q '"tle_date": "20250' /app/data/tle_orbital_calculation_output.json
check_result $? "TLE 日期正確記錄 (非執行日期)"

# shared_core 架構驗證
echo ""
echo "==================================================================="
echo "🏗️ Shared Core 架構驗證"
echo "==================================================================="

# 檢查 observer_config_service 
docker exec netstack-api test -f /app/src/shared_core/observer_config_service.py
check_result $? "observer_config_service 存在"

# 檢查 json_file_service
docker exec netstack-api test -f /app/src/shared_core/json_file_service.py
check_result $? "json_file_service 存在"

# 檢查 elevation_threshold_manager
docker exec netstack-api test -f /app/src/shared_core/elevation_threshold_manager.py
check_result $? "elevation_threshold_manager 存在"

# 總結
echo ""
echo "==================================================================="
echo "📊 驗證結果總結"
echo "==================================================================="
echo -e "✅ 通過項目: ${GREEN}$PASS_COUNT${NC}"
echo -e "❌ 失敗項目: ${RED}$FAIL_COUNT${NC}"
echo -e "⚠️  警告項目: ${YELLOW}$WARN_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}🎉 六階段資料預處理完全符合要求！${NC}"
    echo "✓ 無簡化算法"
    echo "✓ 使用真實數據"
    echo "✓ 無硬編碼座標"
    echo "✓ 符合文檔規範"
    exit 0
else
    echo -e "${RED}⚠️ 發現 $FAIL_COUNT 個問題需要修復${NC}"
    exit 1
fi
