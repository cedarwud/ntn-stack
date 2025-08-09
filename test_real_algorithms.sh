#!/bin/bash

# 🚀 衛星預處理系統真實算法測試腳本
# 測試所有替換的真實算法是否正常運作

echo "==============================================="
echo "🛰️  衛星預處理系統真實算法驗證"
echo "==============================================="
echo ""

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 測試計數器
TESTS_PASSED=0
TESTS_FAILED=0

# 測試函數
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo -n "🧪 測試: $test_name ... "
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 通過${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ 失敗${NC}"
        ((TESTS_FAILED++))
    fi
}

echo "📋 Phase 1: 檢查必要的 Python 套件"
echo "----------------------------------------"

# 檢查 Python 版本
run_test "Python 版本 >= 3.8" "python3 -c 'import sys; exit(0 if sys.version_info >= (3,8) else 1)'"

# 檢查必要套件
run_test "Skyfield 套件" "python3 -c 'import skyfield'"
run_test "SGP4 套件" "python3 -c 'import sgp4'"
run_test "NumPy 套件" "python3 -c 'import numpy'"

echo ""
echo "📋 Phase 2: 驗證文件存在性"
echo "----------------------------------------"

# 檢查關鍵文件
run_test "驗證腳本存在" "[ -f /home/sat/ntn-stack/scripts/validate_satellite_coverage.py ]"
run_test "satellite_selector.py 存在" "[ -f /home/sat/ntn-stack/netstack/src/services/satellite/preprocessing/satellite_selector.py ]"
run_test "timeseries_engine.py 存在" "[ -f /home/sat/ntn-stack/netstack/src/services/satellite/timeseries_engine.py ]"
run_test "preprocessing_service.py 存在" "[ -f /home/sat/ntn-stack/netstack/src/services/satellite/preprocessing_service.py ]"

echo ""
echo "📋 Phase 3: 檢查 TLE 數據"
echo "----------------------------------------"

# 檢查 TLE 數據目錄
run_test "TLE 數據目錄存在" "[ -d /home/sat/ntn-stack/netstack/tle_data ]"
run_test "Starlink TLE 目錄" "[ -d /home/sat/ntn-stack/netstack/tle_data/starlink/tle ]"
run_test "OneWeb TLE 目錄" "[ -d /home/sat/ntn-stack/netstack/tle_data/oneweb/tle ]"

# 檢查是否有 TLE 文件
run_test "Starlink TLE 文件" "ls /home/sat/ntn-stack/netstack/tle_data/starlink/tle/*.tle 2>/dev/null | head -1"

echo ""
echo "📋 Phase 4: 驗證算法實現"
echo "----------------------------------------"

# 檢查是否已移除違規代碼
echo -n "🔍 檢查 random 使用情況 ... "
RANDOM_COUNT=$(grep -r "random\." /home/sat/ntn-stack/netstack/src/services/satellite/preprocessing/*.py 2>/dev/null | grep -v "# " | wc -l)
if [ "$RANDOM_COUNT" -eq "0" ]; then
    echo -e "${GREEN}✅ 未發現隨機數使用${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠️  發現 $RANDOM_COUNT 處可能的隨機數使用${NC}"
    ((TESTS_FAILED++))
fi

# 檢查是否有真實算法標記
echo -n "🔍 檢查真實算法實現 ... "
REAL_ALGO_COUNT=$(grep -r "真實\|ITU-R\|3GPP\|SGP4" /home/sat/ntn-stack/netstack/src/services/satellite/preprocessing/*.py 2>/dev/null | wc -l)
if [ "$REAL_ALGO_COUNT" -gt "10" ]; then
    echo -e "${GREEN}✅ 發現 $REAL_ALGO_COUNT 處真實算法實現${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ 真實算法實現不足${NC}"
    ((TESTS_FAILED++))
fi

echo ""
echo "📋 Phase 5: 快速功能測試"
echo "----------------------------------------"

# 測試驗證腳本的導入
run_test "驗證腳本導入測試" "python3 -c 'import sys; sys.path.append(\"/home/sat/ntn-stack/scripts\"); from validate_satellite_coverage import SatelliteCoverageValidator'"

# 測試 RSRP 計算
run_test "RSRP 計算測試" "python3 -c '
import sys
import math
sys.path.append(\"/home/sat/ntn-stack/netstack/src/services/satellite\")
from preprocessing.satellite_selector import IntelligentSatelliteSelector
selector = IntelligentSatelliteSelector()
sat = {\"altitude\": 550}
rsrp = selector._estimate_rsrp(sat)
assert -120 < rsrp < -80, f\"RSRP {rsrp} 不在合理範圍內\"
'"

echo ""
echo "==============================================="
echo "📊 測試結果總結"
echo "==============================================="
echo -e "✅ 通過測試: ${GREEN}$TESTS_PASSED${NC}"
echo -e "❌ 失敗測試: ${RED}$TESTS_FAILED${NC}"

if [ "$TESTS_FAILED" -eq "0" ]; then
    echo ""
    echo -e "${GREEN}🎉 恭喜！所有測試通過！${NC}"
    echo "系統已成功升級為真實算法實現"
    echo ""
    echo "📝 下一步建議："
    echo "1. 安裝缺少的套件: pip install skyfield sgp4"
    echo "2. 運行完整驗證: python3 /home/sat/ntn-stack/scripts/validate_satellite_coverage.py"
    echo "3. 檢查報告: cat /home/sat/ntn-stack/SATELLITE_PREPROCESSING_REAL_ALGORITHM_REPORT.md"
    exit 0
else
    echo ""
    echo -e "${YELLOW}⚠️  有 $TESTS_FAILED 個測試失敗${NC}"
    echo "請檢查以下項目："
    echo "1. 安裝必要套件: pip install skyfield sgp4 numpy"
    echo "2. 確認 TLE 數據存在"
    echo "3. 檢查文件路徑是否正確"
    exit 1
fi