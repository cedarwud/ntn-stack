#!/bin/bash
# 衛星處理系統 - 本地CI/CD測試執行器
# 🚀 一鍵執行完整測試套件

set -e  # 任何錯誤都中斷執行

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 項目根目錄
PROJECT_ROOT="/home/sat/ntn-stack/satellite-processing-system"
cd "$PROJECT_ROOT"

echo -e "${BLUE}🚀 衛星處理系統 - 本地CI/CD測試管道${NC}"
echo "================================================================"
echo "開始時間: $(date '+%Y-%m-%d %H:%M:%S')"
echo "項目路徑: $PROJECT_ROOT"
echo "================================================================"

# 檢查Python環境
echo -e "\n${YELLOW}📋 檢查測試環境...${NC}"
python --version
pip show pytest >/dev/null 2>&1 || {
    echo -e "${RED}❌ pytest未安裝${NC}"
    echo "請執行: pip install -r requirements.txt"
    exit 1
}

# 檢查TLE數據
echo -e "\n${YELLOW}📊 檢查測試數據...${NC}"
if [ ! -d "data/tle_data/starlink/tle" ] || [ -z "$(ls -A data/tle_data/starlink/tle/*.tle 2>/dev/null)" ]; then
    echo -e "${RED}❌ 真實TLE數據不存在${NC}"
    echo "請確保 data/tle_data/starlink/tle/ 目錄包含 *.tle 文件"
    exit 1
else
    TLE_COUNT=$(ls data/tle_data/starlink/tle/*.tle | wc -l)
    echo -e "${GREEN}✅ TLE數據檢查通過 ($TLE_COUNT 個文件)${NC}"
fi

# 創建測試報告目錄
mkdir -p tests/reports

# 執行測試套件
echo -e "\n${YELLOW}🧪 執行測試套件...${NC}"
echo "----------------------------------------------------------------"

# SGP4軌道引擎測試 (關鍵測試)
echo -e "${BLUE}🛰️ SGP4軌道引擎測試${NC}"
python -m pytest tests/unit/algorithms/test_sgp4_orbital_engine.py \
    -v \
    --tb=short \
    --html=tests/reports/sgp4_report.html \
    --self-contained-html \
    --cov=src.shared.engines.sgp4_orbital_engine \
    --cov-report=html:tests/reports/sgp4_coverage \
    --cov-report=term-missing

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ SGP4測試通過${NC}"
else
    echo -e "${RED}❌ SGP4測試失敗${NC}"
    exit 1
fi

# 執行所有單元測試
echo -e "\n${BLUE}🔬 所有單元測試${NC}"
python -m pytest tests/unit/ \
    -v \
    --tb=short \
    --html=tests/reports/unit_tests_report.html \
    --self-contained-html \
    --cov=src \
    --cov-report=html:tests/reports/coverage_html \
    --cov-report=term-missing \
    --cov-fail-under=80

UNIT_TEST_RESULT=$?

# 性能基準測試
echo -e "\n${BLUE}⚡ 性能基準測試${NC}"
python -m pytest tests/unit/algorithms/test_sgp4_orbital_engine.py::TestSGP4OrbitalEngine::test_sgp4_calculation_performance \
    -v \
    --tb=short

PERF_TEST_RESULT=$?

# 生成綜合報告
echo -e "\n${YELLOW}📊 生成測試報告...${NC}"
echo "================================================================"
echo "測試完成時間: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

if [ $UNIT_TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ 單元測試: 通過${NC}"
else
    echo -e "${RED}❌ 單元測試: 失敗${NC}"
fi

if [ $PERF_TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ 性能測試: 通過${NC}"
else
    echo -e "${YELLOW}⚠️ 性能測試: 有警告${NC}"
fi

echo ""
echo "📈 測試報告位置:"
echo "  - 單元測試報告: tests/reports/unit_tests_report.html"
echo "  - SGP4專項報告: tests/reports/sgp4_report.html" 
echo "  - 覆蓋率報告: tests/reports/coverage_html/index.html"
echo ""

# 最終結果
if [ $UNIT_TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}🎉 所有測試通過！項目質量良好！${NC}"
    exit 0
else
    echo -e "${RED}💥 測試失敗！請修復問題後重新測試${NC}"
    exit 1
fi