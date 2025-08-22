#!/bin/bash

# Volume-based 持久化架構驗證腳本
# 驗證修復後的架構是否符合文檔設計

set -e

echo "🔍 Volume-based 持久化架構驗證開始..."
echo "=========================================="

# 顏色定義
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
RESET='\033[0m'

# 驗證計數
PASS=0
FAIL=0

verify_step() {
    local description="$1"
    local command="$2"
    
    printf "${BLUE}🔍 檢查: $description${RESET}\n"
    
    if eval "$command" >/dev/null 2>&1; then
        printf "${GREEN}✅ PASS: $description${RESET}\n"
        ((PASS++))
    else
        printf "${RED}❌ FAIL: $description${RESET}\n"
        printf "${YELLOW}   命令: $command${RESET}\n"
        ((FAIL++))
    fi
    printf "\n"
}

echo -e "${YELLOW}📋 階段一：文件和配置驗證${RESET}"
echo "=========================================="

verify_step "volume-based-entrypoint.sh腳本存在" \
    "test -f /home/sat/ntn-stack/netstack/docker/volume-based-entrypoint.sh"

verify_step "volume-based-entrypoint.sh腳本可執行" \
    "test -x /home/sat/ntn-stack/netstack/docker/volume-based-entrypoint.sh"

verify_step "core-simple.yaml配置文件存在" \
    "test -f /home/sat/ntn-stack/netstack/compose/core-simple.yaml"

verify_step "Dockerfile包含volume-based-entrypoint.sh" \
    "grep -q 'volume-based-entrypoint.sh' /home/sat/ntn-stack/netstack/docker/Dockerfile"

verify_step "core-simple.yaml使用volume-based-entrypoint.sh" \
    "grep -q 'volume-based-entrypoint.sh' /home/sat/ntn-stack/netstack/compose/core-simple.yaml"

verify_step "shared_core增量更新管理器存在" \
    "test -f /home/sat/ntn-stack/netstack/src/shared_core/incremental_update_manager.py"

echo -e "${YELLOW}📋 階段二：架構設計驗證${RESET}"
echo "=========================================="

verify_step "Volume配置正確掛載到/app/data" \
    "grep -A5 -B5 'satellite_precomputed_data:/app/data' /home/sat/ntn-stack/netstack/compose/core-simple.yaml"

verify_step "環境變數包含VOLUME_BASED_PERSISTENCE" \
    "grep -q 'VOLUME_BASED_PERSISTENCE=true' /home/sat/ntn-stack/netstack/compose/core-simple.yaml"

verify_step "智能增量更新檢查已啟用" \
    "grep -q 'SKIP_DATA_UPDATE_CHECK=false' /home/sat/ntn-stack/netstack/compose/core-simple.yaml"

verify_step "六階段主控制器存在" \
    "test -f /home/sat/ntn-stack/netstack/src/leo_core/main_pipeline_controller.py"

echo -e "${YELLOW}📋 階段三：關鍵文件驗證${RESET}"
echo "=========================================="

verify_step "BUILD_TIME_PREPROCESSING_FIX_REPORT.md存在" \
    "test -f /home/sat/ntn-stack/BUILD_TIME_PREPROCESSING_FIX_REPORT.md"

verify_step "data_processing_flow.md文檔存在" \
    "test -f /home/sat/ntn-stack/docs/data_processing_flow.md"

verify_step "六階段處理器完整" \
    "test -d /home/sat/ntn-stack/netstack/src/stages && ls /home/sat/ntn-stack/netstack/src/stages/*.py | wc -l | grep -q '[6-9]'"

echo -e "${YELLOW}📋 階段四：Docker環境驗證${RESET}"
echo "=========================================="

# 檢查Docker是否運行
if command -v docker >/dev/null 2>&1; then
    verify_step "Docker服務運行中" \
        "docker info"
    
    # 檢查是否有現有的Volume
    if docker volume ls | grep -q satellite_precomputed_data; then
        echo -e "${BLUE}📦 發現現有Volume: satellite_precomputed_data${RESET}"
        
        # 檢查Volume內容
        if docker run --rm -v satellite_precomputed_data:/data alpine ls /data | head -5; then
            echo -e "${GREEN}✅ Volume內容可訪問${RESET}"
            ((PASS++))
        else
            echo -e "${YELLOW}⚠️ Volume為空或不可訪問${RESET}"
            ((FAIL++))
        fi
    else
        echo -e "${YELLOW}💡 Volume尚未創建（首次運行時會創建）${RESET}"
    fi
else
    echo -e "${RED}❌ Docker未安裝或不可用${RESET}"
    ((FAIL++))
fi

echo
echo "=========================================="
echo -e "${BLUE}📊 驗證結果總結${RESET}"
echo "=========================================="
echo -e "${GREEN}✅ 通過: $PASS 項${RESET}"
echo -e "${RED}❌ 失敗: $FAIL 項${RESET}"

if [ $FAIL -eq 0 ]; then
    echo
    echo -e "${GREEN}🎉 Volume-based 持久化架構驗證完全通過！${RESET}"
    echo
    echo -e "${YELLOW}🚀 準備就緒，可以測試架構運行：${RESET}"
    echo "   1. make netstack-build-n  # 重建包含新entrypoint的映像檔"
    echo "   2. make up                # 啟動服務測試Volume持久化"
    echo "   3. make status            # 檢查服務健康狀況"
    echo
    echo -e "${BLUE}📋 預期行為：${RESET}"
    echo "   • 首次啟動：45分鐘數據生成並緩存到Volume"
    echo "   • 後續啟動：< 10秒從Volume快速載入"
    echo "   • 智能增量更新：僅在TLE數據更新時執行"
    echo "   • 跨容器重啟：數據持久保留"
    
    exit 0
else
    echo
    echo -e "${RED}❌ Volume-based 持久化架構驗證失敗${RESET}"
    echo -e "${YELLOW}💡 請先解決上述問題再進行測試${RESET}"
    
    exit 1
fi