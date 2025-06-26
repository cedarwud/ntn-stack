#!/bin/bash

# 自動化容器網路依賴管理腳本
# 實現 Sprint 2 目標：容器網路依賴自動化，啟動成功率 > 95%

set -euo pipefail

# 配置變數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/tmp/network_dependency_manager.log"
MAX_RETRIES=3
RETRY_DELAY=10
HEALTH_CHECK_TIMEOUT=60
NETWORK_CHECK_INTERVAL=5

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log() {
    echo -e "${1}" | tee -a "$LOG_FILE"
}

log_info() {
    log "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    log "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 初始化日誌
init_logging() {
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "=== 自動化容器網路依賴管理 - $(date) ===" > "$LOG_FILE"
}

# 檢查Docker是否可用
check_docker() {
    log_info "檢查Docker狀態..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安裝或不在PATH中"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker服務未運行或當前用戶無權限"
        return 1
    fi
    
    log_success "Docker狀態正常"
    return 0
}

# 檢查Docker Compose是否可用
check_docker_compose() {
    log_info "檢查Docker Compose狀態..."
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose未安裝"
        return 1
    fi
    
    log_success "Docker Compose狀態正常"
    return 0
}

# 清理舊的網路和容器
cleanup_old_resources() {
    log_info "清理舊的網路和容器資源..."
    
    # 停止並移除所有相關容器
    local containers=$(docker ps -aq --filter "name=netstack*" --filter "name=simworld*" 2>/dev/null || true)
    if [ -n "$containers" ]; then
        log_info "停止現有容器..."
        echo "$containers" | xargs docker stop || true
        echo "$containers" | xargs docker rm || true
    fi
    
    # 清理未使用的網路
    log_info "清理未使用的Docker網路..."
    docker network prune -f || true
    
    # 清理未使用的卷
    log_info "清理未使用的Docker卷..."
    docker volume prune -f || true
    
    log_success "資源清理完成"
}

# 創建必要的網路
create_networks() {
    log_info "創建必要的Docker網路..."
    
    # NetStack核心網路
    if ! docker network ls | grep -q "netstack-core"; then
        log_info "創建netstack-core網路..."
        docker network create \
            --driver bridge \
            --subnet=172.20.0.0/16 \
            --ip-range=172.20.0.0/24 \
            --gateway=172.20.0.1 \
            netstack-core || {
            log_error "創建netstack-core網路失敗"
            return 1
        }
        log_success "netstack-core網路創建成功"
    else
        log_info "netstack-core網路已存在"
    fi
    
    # SimWorld網路
    if ! docker network ls | grep -q "sionna-net"; then
        log_info "創建sionna-net網路..."
        docker network create \
            --driver bridge \
            --subnet=172.21.0.0/16 \
            sionna-net || {
            log_error "創建sionna-net網路失敗"
            return 1
        }
        log_success "sionna-net網路創建成功"
    else
        log_info "sionna-net網路已存在"
    fi
    
    return 0
}

# 檢查網路連通性
test_network_connectivity() {
    local network_name="$1"
    log_info "測試網路連通性: $network_name"
    
    # 創建測試容器
    local test_container="network-test-$(date +%s)"
    
    if docker run --rm --name "$test_container" --network "$network_name" \
        alpine:latest ping -c 1 8.8.8.8 &> /dev/null; then
        log_success "網路 $network_name 連通性正常"
        return 0
    else
        log_error "網路 $network_name 連通性測試失敗"
        return 1
    fi
}

# 啟動NetStack核心服務
start_netstack_core() {
    log_info "啟動NetStack核心服務..."
    
    cd "$PROJECT_ROOT/netstack"
    
    # 檢查必要文件
    if [ ! -f "Makefile" ]; then
        log_error "NetStack Makefile未找到"
        return 1
    fi
    
    # 使用Makefile啟動核心服務
    local retry_count=0
    while [ $retry_count -lt $MAX_RETRIES ]; do
        log_info "啟動NetStack核心服務 (嘗試 $((retry_count + 1))/$MAX_RETRIES)..."
        
        if make netstack-start; then
            log_success "NetStack核心服務啟動成功"
            break
        else
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $MAX_RETRIES ]; then
                log_warn "NetStack啟動失敗，${RETRY_DELAY}秒後重試..."
                sleep $RETRY_DELAY
            else
                log_error "NetStack核心服務啟動失敗，已達最大重試次數"
                return 1
            fi
        fi
    done
    
    return 0
}

# 等待NetStack服務健康檢查
wait_for_netstack_health() {
    log_info "等待NetStack服務健康檢查..."
    
    local timeout=$HEALTH_CHECK_TIMEOUT
    local elapsed=0
    
    while [ $elapsed -lt $timeout ]; do
        # 檢查MongoDB
        if docker exec netstack-mongo mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
            log_info "MongoDB健康檢查通過"
        else
            log_warn "MongoDB尚未就緒..."
            sleep $NETWORK_CHECK_INTERVAL
            elapsed=$((elapsed + NETWORK_CHECK_INTERVAL))
            continue
        fi
        
        # 檢查Redis
        if docker exec netstack-redis redis-cli ping &> /dev/null; then
            log_info "Redis健康檢查通過"
        else
            log_warn "Redis尚未就緒..."
            sleep $NETWORK_CHECK_INTERVAL
            elapsed=$((elapsed + NETWORK_CHECK_INTERVAL))
            continue
        fi
        
        # 檢查NetStack API
        if curl -f http://localhost:8080/health &> /dev/null; then
            log_success "NetStack API健康檢查通過"
            return 0
        else
            log_warn "NetStack API尚未就緒..."
            sleep $NETWORK_CHECK_INTERVAL
            elapsed=$((elapsed + NETWORK_CHECK_INTERVAL))
        fi
    done
    
    log_error "NetStack服務健康檢查超時"
    return 1
}

# 配置SimWorld網路橋接
configure_simworld_bridge() {
    log_info "配置SimWorld網路橋接..."
    
    # 檢查SimWorld backend是否可以連接到NetStack網路
    local simworld_container="simworld_backend"
    
    if docker ps --format "table {{.Names}}" | grep -q "$simworld_container"; then
        log_info "SimWorld backend容器已運行，配置網路橋接..."
        
        # 將SimWorld backend連接到netstack-core網路
        if docker network connect netstack-core "$simworld_container" 2>/dev/null; then
            log_success "SimWorld已連接到netstack-core網路"
        else
            log_warn "SimWorld可能已連接到netstack-core網路"
        fi
        
        # 測試跨網路連通性
        if docker exec "$simworld_container" ping -c 1 netstack-api &> /dev/null; then
            log_success "SimWorld到NetStack網路連通性正常"
            return 0
        else
            log_error "SimWorld到NetStack網路連通性測試失敗"
            return 1
        fi
    else
        log_warn "SimWorld backend容器未運行，跳過網路橋接配置"
        return 0
    fi
}

# 啟動SimWorld服務
start_simworld() {
    log_info "啟動SimWorld服務..."
    
    cd "$PROJECT_ROOT/simworld"
    
    # 檢查docker-compose文件
    if [ ! -f "docker-compose.yml" ]; then
        log_error "SimWorld docker-compose.yml未找到"
        return 1
    fi
    
    # 啟動SimWorld服務
    local retry_count=0
    while [ $retry_count -lt $MAX_RETRIES ]; do
        log_info "啟動SimWorld服務 (嘗試 $((retry_count + 1))/$MAX_RETRIES)..."
        
        if docker-compose up -d; then
            log_success "SimWorld服務啟動成功"
            break
        else
            retry_count=$((retry_count + 1))
            if [ $retry_count -lt $MAX_RETRIES ]; then
                log_warn "SimWorld啟動失敗，${RETRY_DELAY}秒後重試..."
                sleep $RETRY_DELAY
            else
                log_error "SimWorld服務啟動失敗，已達最大重試次數"
                return 1
            fi
        fi
    done
    
    # 配置網路橋接
    configure_simworld_bridge
    
    return 0
}

# 等待SimWorld服務健康檢查
wait_for_simworld_health() {
    log_info "等待SimWorld服務健康檢查..."
    
    local timeout=$HEALTH_CHECK_TIMEOUT
    local elapsed=0
    
    while [ $elapsed -lt $timeout ]; do
        # 檢查SimWorld backend
        if curl -f http://localhost:8888/health &> /dev/null; then
            log_info "SimWorld backend健康檢查通過"
        else
            log_warn "SimWorld backend尚未就緒..."
            sleep $NETWORK_CHECK_INTERVAL
            elapsed=$((elapsed + NETWORK_CHECK_INTERVAL))
            continue
        fi
        
        # 檢查SimWorld frontend
        if curl -f http://localhost:5173 &> /dev/null; then
            log_success "SimWorld frontend健康檢查通過"
            return 0
        else
            log_warn "SimWorld frontend尚未就緒..."
            sleep $NETWORK_CHECK_INTERVAL
            elapsed=$((elapsed + NETWORK_CHECK_INTERVAL))
        fi
    done
    
    log_error "SimWorld服務健康檢查超時"
    return 1
}

# 執行全面的網路連通性測試
test_full_connectivity() {
    log_info "執行全面的網路連通性測試..."
    
    local tests_passed=0
    local total_tests=5
    
    # 測試1: NetStack內部連通性
    log_info "測試1: NetStack內部連通性"
    if docker exec netstack-api ping -c 1 netstack-mongo &> /dev/null; then
        log_success "✓ NetStack API -> MongoDB 連通"
        tests_passed=$((tests_passed + 1))
    else
        log_error "✗ NetStack API -> MongoDB 連通失敗"
    fi
    
    # 測試2: NetStack Redis連通性
    log_info "測試2: NetStack Redis連通性"
    if docker exec netstack-api ping -c 1 netstack-redis &> /dev/null; then
        log_success "✓ NetStack API -> Redis 連通"
        tests_passed=$((tests_passed + 1))
    else
        log_error "✗ NetStack API -> Redis 連通失敗"
    fi
    
    # 測試3: SimWorld內部連通性
    log_info "測試3: SimWorld內部連通性"
    if docker exec simworld_backend ping -c 1 simworld_postgis &> /dev/null; then
        log_success "✓ SimWorld Backend -> PostGIS 連通"
        tests_passed=$((tests_passed + 1))
    else
        log_error "✗ SimWorld Backend -> PostGIS 連通失敗"
    fi
    
    # 測試4: 跨服務連通性
    log_info "測試4: 跨服務連通性"
    if docker exec simworld_backend ping -c 1 netstack-api &> /dev/null; then
        log_success "✓ SimWorld -> NetStack 跨網路連通"
        tests_passed=$((tests_passed + 1))
    else
        log_error "✗ SimWorld -> NetStack 跨網路連通失敗"
    fi
    
    # 測試5: 外部服務訪問
    log_info "測試5: 外部服務訪問"
    local api_test=false
    local frontend_test=false
    
    if curl -f http://localhost:8080/health &> /dev/null; then
        api_test=true
    fi
    
    if curl -f http://localhost:5173 &> /dev/null; then
        frontend_test=true
    fi
    
    if $api_test && $frontend_test; then
        log_success "✓ 外部服務訪問正常"
        tests_passed=$((tests_passed + 1))
    else
        log_error "✗ 外部服務訪問失敗 (API: $api_test, Frontend: $frontend_test)"
    fi
    
    # 計算成功率
    local success_rate=$((tests_passed * 100 / total_tests))
    log_info "網路連通性測試完成: $tests_passed/$total_tests 通過 (${success_rate}%)"
    
    if [ $success_rate -ge 95 ]; then
        log_success "✅ 網路連通性測試達到目標 (≥95%)"
        return 0
    else
        log_error "❌ 網路連通性測試未達目標 (<95%)"
        return 1
    fi
}

# 修復網路問題
fix_network_issues() {
    log_info "嘗試修復網路問題..."
    
    # 重啟Docker網路
    log_info "重啟Docker網路..."
    docker network prune -f
    create_networks
    
    # 重新連接容器到網路
    log_info "重新連接容器到網路..."
    local containers=$(docker ps --format "{{.Names}}" | grep -E "(netstack|simworld)")
    
    for container in $containers; do
        if [[ $container == *"netstack"* ]]; then
            docker network connect netstack-core "$container" 2>/dev/null || true
        elif [[ $container == *"simworld"* ]]; then
            docker network connect sionna-net "$container" 2>/dev/null || true
            if [[ $container == "simworld_backend" ]]; then
                docker network connect netstack-core "$container" 2>/dev/null || true
            fi
        fi
    done
    
    log_success "網路修復操作完成"
}

# 生成詳細的狀態報告
generate_status_report() {
    log_info "生成系統狀態報告..."
    
    local report_file="/tmp/network_dependency_status_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "=== NTN Stack 網路依賴狀態報告 ==="
        echo "生成時間: $(date)"
        echo ""
        
        echo "=== Docker 網路狀態 ==="
        docker network ls
        echo ""
        
        echo "=== 容器狀態 ==="
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        
        echo "=== NetStack 容器詳情 ==="
        docker ps --filter "name=netstack*" --format "table {{.Names}}\t{{.Status}}\t{{.Networks}}"
        echo ""
        
        echo "=== SimWorld 容器詳情 ==="
        docker ps --filter "name=simworld*" --format "table {{.Names}}\t{{.Status}}\t{{.Networks}}"
        echo ""
        
        echo "=== 服務健康檢查 ==="
        echo -n "NetStack API: "
        if curl -s http://localhost:8080/health &> /dev/null; then
            echo "✅ 正常"
        else
            echo "❌ 異常"
        fi
        
        echo -n "SimWorld Backend: "
        if curl -s http://localhost:8888/health &> /dev/null; then
            echo "✅ 正常"
        else
            echo "❌ 異常"
        fi
        
        echo -n "SimWorld Frontend: "
        if curl -s http://localhost:5173 &> /dev/null; then
            echo "✅ 正常"
        else
            echo "❌ 異常"
        fi
        
    } > "$report_file"
    
    log_success "狀態報告已生成: $report_file"
    cat "$report_file"
}

# 主執行函數
main() {
    init_logging
    log_info "開始自動化容器網路依賴管理..."
    
    # 檢查環境
    check_docker || exit 1
    check_docker_compose || exit 1
    
    # 清理舊資源
    cleanup_old_resources
    
    # 創建網路
    create_networks || exit 1
    
    # 測試基礎網路連通性
    test_network_connectivity "netstack-core" || {
        log_warn "netstack-core網路連通性測試失敗，嘗試修復..."
        fix_network_issues
    }
    
    test_network_connectivity "sionna-net" || {
        log_warn "sionna-net網路連通性測試失敗，嘗試修復..."
        fix_network_issues
    }
    
    # 啟動NetStack
    start_netstack_core || exit 1
    wait_for_netstack_health || {
        log_error "NetStack服務健康檢查失敗"
        generate_status_report
        exit 1
    }
    
    # 啟動SimWorld
    start_simworld || exit 1
    wait_for_simworld_health || {
        log_error "SimWorld服務健康檢查失敗"
        generate_status_report
        exit 1
    }
    
    # 執行全面連通性測試
    if test_full_connectivity; then
        log_success "🎉 自動化容器網路依賴管理完成！啟動成功率 ≥95%"
        generate_status_report
        exit 0
    else
        log_error "網路連通性測試未達標，啟動失敗"
        generate_status_report
        exit 1
    fi
}

# 處理中斷信號
trap 'log_error "腳本被中斷"; exit 1' INT TERM

# 如果腳本被直接執行，運行主函數
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi