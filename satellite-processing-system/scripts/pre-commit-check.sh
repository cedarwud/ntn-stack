#!/bin/bash
# Git 預提交檢查腳本
# 🛡️ 確保每次提交都通過基本質量檢查

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="/home/sat/ntn-stack/satellite-processing-system"
cd "$PROJECT_ROOT"

echo -e "${BLUE}🛡️ Git 預提交檢查開始${NC}"
echo "================================================================"

# 預先清理快取防止權限問題
find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# 檢查Python語法
echo -e "${YELLOW}🐍 檢查Python語法...${NC}"
export PYTHONDONTWRITEBYTECODE=1  # 禁止生成.pyc文件
python -m py_compile src/shared/engines/sgp4_orbital_engine.py
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Python語法檢查通過${NC}"
else
    echo -e "${RED}❌ Python語法錯誤，請修復後提交${NC}"
    exit 1
fi

# 執行關鍵測試 (快速檢查)
echo -e "\n${YELLOW}🧪 執行關鍵測試...${NC}"
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/unit/algorithms/test_sgp4_orbital_engine.py::TestSGP4OrbitalEngine::test_tle_epoch_time_usage_mandatory \
    -v \
    --tb=short \
    -q

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 關鍵TLE時間基準測試通過${NC}"
else
    echo -e "${RED}❌ 關鍵測試失敗，禁止提交${NC}"
    echo "請執行完整測試: ./scripts/test-runner.sh"
    exit 1
fi

# 檢查測試覆蓋率基本要求 (僅SGP4核心)
echo -e "\n${YELLOW}📊 檢查核心模組覆蓋率...${NC}"
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests/unit/algorithms/test_sgp4_orbital_engine.py \
    --cov=src.shared.engines.sgp4_orbital_engine \
    --cov-fail-under=90 \
    -q \
    > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 核心模組覆蓋率 ≥90%${NC}"
else
    echo -e "${YELLOW}⚠️ 核心模組覆蓋率不足90%${NC}"
    echo "建議執行完整測試檢查: ./scripts/test-runner.sh"
fi

# 檢查是否有禁用的模擬數據
echo -e "\n${YELLOW}🚫 檢查學術合規性...${NC}"
FORBIDDEN_PATTERNS="np\.random|random\.normal|mock|fake|假設|模擬"
VIOLATIONS=$(grep -rE "$FORBIDDEN_PATTERNS" src/ tests/ --include="*.py" || true)

if [ -z "$VIOLATIONS" ]; then
    echo -e "${GREEN}✅ 學術合規檢查通過${NC}"
else
    echo -e "${RED}❌ 發現禁用模式:${NC}"
    echo "$VIOLATIONS"
    echo -e "${RED}請移除模擬數據，使用真實數據${NC}"
    exit 1
fi

# 清理 Python 快取文件 (防止權限問題)
echo -e "\n${YELLOW}🧹 清理Python快取...${NC}"
find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
echo -e "${GREEN}✅ 快取清理完成${NC}"

echo ""
echo -e "${GREEN}🎉 預提交檢查全部通過！${NC}"
echo "================================================================"
echo "提交前建議執行完整測試: ./scripts/test-runner.sh"
echo "================================================================"