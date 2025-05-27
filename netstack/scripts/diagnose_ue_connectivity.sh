#!/bin/bash

# NetStack UE 連線診斷腳本
# 快速診斷 UE 無法連線的問題

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置
UE_CONTAINERS=("netstack-ues1" "netstack-ues2" "netstack-ue-test")
TEST_IMSIS=("999700000000001" "999700000000002" "999700000000099")

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

echo "=========================================="
echo "🔍 NetStack UE 連線診斷工具"
echo "=========================================="

# 步驟1: 檢查核心網服務狀態
log_step "1. 檢查核心網服務狀態"
echo ""

core_services=("netstack-amf" "netstack-smf" "netstack-upf" "netstack-udm" "netstack-udr" "netstack-ausf" "netstack-mongo")
all_core_running=true

for service in "${core_services[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^$service$"; then
        log_info "✅ $service 運行中"
    else
        log_error "❌ $service 未運行"
        all_core_running=false
    fi
done

if [ "$all_core_running" = false ]; then
    echo ""
    log_error "❌ 核心網服務未完全啟動"
    log_warning "解決方案: 執行 'make up' 啟動核心網"
    exit 1
fi

echo ""

# 步驟2: 檢查 MongoDB 用戶註冊狀態
log_step "2. 檢查 MongoDB 用戶註冊狀態"
echo ""

mongo_available=$(docker run --rm --net compose_netstack-core mongo:6.0 mongosh "mongodb://172.20.0.10:27017/open5gs" --quiet --eval "print('connected')" 2>/dev/null || echo "failed")

if [ "$mongo_available" != "connected" ]; then
    log_error "❌ 無法連接到 MongoDB"
    log_warning "解決方案: 檢查 MongoDB 容器狀態"
    exit 1
fi

user_count=$(docker run --rm --net compose_netstack-core mongo:6.0 mongosh "mongodb://172.20.0.10:27017/open5gs" --quiet --eval "print(db.subscribers.countDocuments({}))" 2>/dev/null || echo "0")

if [ "$user_count" = "0" ]; then
    log_error "❌ 資料庫中沒有註冊用戶"
    log_warning "解決方案: 執行 'make register-subscribers'"
    exit 1
else
    log_info "✅ 資料庫中有 $user_count 個註冊用戶"
fi

# 檢查測試用戶是否存在
missing_users=()
for imsi in "${TEST_IMSIS[@]}"; do
    exists=$(docker run --rm --net compose_netstack-core mongo:6.0 mongosh "mongodb://172.20.0.10:27017/open5gs" --quiet --eval "print(db.subscribers.countDocuments({imsi: '$imsi'}))" 2>/dev/null || echo "0")
    if [ "$exists" = "0" ]; then
        missing_users+=("$imsi")
    else
        log_info "✅ 測試用戶 $imsi 已註冊"
    fi
done

if [ ${#missing_users[@]} -gt 0 ]; then
    log_warning "⚠️ 缺少測試用戶: ${missing_users[*]}"
    log_warning "解決方案: 執行 'make register-subscribers'"
fi

echo ""

# 步驟3: 檢查 RAN 模擬器狀態
log_step "3. 檢查 RAN 模擬器狀態"
echo ""

ran_services=("netstack-gnb1" "netstack-gnb2")
all_ran_running=true

for service in "${ran_services[@]}"; do
    if docker ps --format '{{.Names}}' | grep -q "^$service$"; then
        log_info "✅ $service 運行中"
    else
        log_error "❌ $service 未運行"
        all_ran_running=false
    fi
done

if [ "$all_ran_running" = false ]; then
    echo ""
    log_error "❌ RAN 模擬器未完全啟動"
    log_warning "解決方案: 執行 'make start-ran'"
fi

echo ""

# 步驟4: 檢查 UE 容器狀態和日誌
log_step "4. 檢查 UE 容器狀態和連線"
echo ""

for container in "${UE_CONTAINERS[@]}"; do
    echo "檢查 $container:"
    
    if docker ps --format '{{.Names}}' | grep -q "^$container$"; then
        log_info "  ✅ 容器運行中"
        
        # 檢查網路介面
        interface=$(docker exec "$container" ip route | grep uesimtun | head -1 | awk '{print $3}' 2>/dev/null || echo "")
        if [ -n "$interface" ]; then
            log_info "  ✅ 網路介面: $interface"
            
            # 檢查 IP 地址
            ip_addr=$(docker exec "$container" ip addr show "$interface" | grep "inet " | awk '{print $2}' 2>/dev/null || echo "無")
            log_info "  ✅ IP 地址: $ip_addr"
        else
            log_error "  ❌ 沒有 uesimtun 網路介面"
            
            # 顯示最近的日誌
            echo "  最近的日誌 (最後5行):"
            docker logs "$container" --tail 5 2>/dev/null | sed 's/^/    /'
        fi
    else
        log_error "  ❌ 容器未運行"
    fi
    echo ""
done

# 步驟5: 檢查 AMF 日誌中的錯誤
log_step "5. 檢查 AMF 日誌中的認證錯誤"
echo ""

recent_errors=$(docker logs netstack-amf --tail 20 2>/dev/null | grep -E "(Cannot find SUCI|Registration reject)" || echo "")

if [ -n "$recent_errors" ]; then
    log_error "❌ AMF 中發現認證錯誤:"
    echo "$recent_errors" | sed 's/^/    /'
    echo ""
    log_warning "這通常表示用戶未在資料庫中註冊或服務需要重啟"
else
    log_info "✅ AMF 日誌中沒有發現認證錯誤"
fi

echo ""

# 步驟6: 提供解決建議
log_step "6. 解決建議"
echo ""

if [ ${#missing_users[@]} -gt 0 ] || [ "$recent_errors" != "" ]; then
    log_warning "🔧 建議的解決流程:"
    echo "  1. 重新註冊用戶: make register-subscribers"
    echo "  2. 重啟 RAN 模擬器: make stop-ran && make start-ran"
    echo "  3. 等待 15 秒讓服務穩定"
    echo "  4. 測試連線: make test-connectivity"
    echo ""
    log_warning "如果問題仍然存在:"
    echo "  1. 完全重啟環境: make clean-keep-data && make up"
    echo "  2. 重新註冊和啟動: make register-subscribers && make start-ran"
elif [ "$all_core_running" = false ] || [ "$all_ran_running" = false ]; then
    log_warning "🔧 建議的解決流程:"
    echo "  1. 啟動缺失的服務: make up && make start-ran"
    echo "  2. 等待服務完全啟動 (約60秒)"
    echo "  3. 測試連線: make test-connectivity"
else
    log_info "✅ 所有檢查項目都正常，UE 應該能夠正常連線"
    log_info "如果仍有問題，請檢查網路配置或硬體相容性"
fi

echo ""
echo "=========================================="
echo "🔍 診斷完成"
echo "==========================================" 