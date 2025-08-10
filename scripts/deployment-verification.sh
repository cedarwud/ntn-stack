#!/bin/bash
# 部署流程驗證腳本 - Stage 4.4

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 NetStack 部署流程驗證"
echo "=========================="

# 驗證類型
VERIFICATION_TYPE=${1:-full}

show_help() {
    echo "用法: $0 [verification_type]"
    echo ""
    echo "驗證類型："
    echo "  full       - 完整部署驗證 (預設)"
    echo "  quick      - 快速健康檢查"
    echo "  config     - 配置文件驗證"
    echo "  services   - 服務狀態檢查"
    echo "  api        - API 端點測試"
    echo "  help       - 顯示此幫助"
    echo ""
    echo "範例："
    echo "  $0 full     # 完整驗證"
    echo "  $0 quick    # 快速檢查"
    echo "  $0 api      # 僅測試API"
}

# 檢查是否需要幫助
if [[ "$1" == "help" ]] || [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    show_help
    exit 0
fi

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 檢查 Docker 環境
check_docker() {
    log_info "檢查 Docker 環境..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安裝"
        return 1
    fi
    
    if ! docker ps &> /dev/null; then
        log_error "Docker daemon 未運行或權限不足"
        return 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose 未安裝"
        return 1
    fi
    
    log_success "Docker 環境正常"
    return 0
}

# 檢查配置文件
check_config_files() {
    log_info "檢查配置文件..."
    
    local issues=0
    
    # 檢查環境配置文件
    for env in "development" "production"; do
        local env_file="$PROJECT_DIR/.env.$env"
        if [[ -f "$env_file" ]]; then
            log_success "環境配置存在: $env"
            
            # 檢查必要的配置項
            local required_vars=("ENVIRONMENT" "API_HOST" "API_PORT" "POSTGRES_HOST" "MONGO_HOST" "REDIS_HOST")
            for var in "${required_vars[@]}"; do
                if ! grep -q "^${var}=" "$env_file"; then
                    log_warning "缺少配置項 $var 在 $env 環境"
                    ((issues++))
                fi
            done
        else
            log_error "環境配置文件不存在: $env_file"
            ((issues++))
        fi
    done
    
    # 檢查 Docker Compose 文件
    local compose_files=("docker-compose.yml" "netstack/compose/core.yaml" "simworld/compose/simworld-complete.yml")
    for compose_file in "${compose_files[@]}"; do
        local full_path="$PROJECT_DIR/$compose_file"
        if [[ -f "$full_path" ]]; then
            log_success "Compose 文件存在: $compose_file"
        else
            log_warning "Compose 文件不存在: $compose_file"
        fi
    done
    
    return $issues
}

# 檢查服務狀態
check_services() {
    log_info "檢查服務狀態..."
    
    cd "$PROJECT_DIR"
    
    # 檢查服務是否運行
    local services=$(docker-compose ps --services 2>/dev/null || docker compose ps --services 2>/dev/null || echo "")
    
    if [[ -z "$services" ]]; then
        log_warning "無法獲取服務列表，可能尚未啟動"
        return 1
    fi
    
    local healthy_count=0
    local total_count=0
    
    echo ""
    echo "📊 服務狀態檢查："
    echo "=================="
    
    while IFS= read -r service; do
        if [[ -n "$service" ]]; then
            ((total_count++))
            local status=$(docker-compose ps "$service" --format "{{.State}}" 2>/dev/null || docker compose ps "$service" --format "{{.State}}" 2>/dev/null || echo "unknown")
            
            if [[ "$status" == *"Up"* ]] && [[ "$status" != *"unhealthy"* ]]; then
                log_success "$service: $status"
                ((healthy_count++))
            else
                log_error "$service: $status"
            fi
        fi
    done <<< "$services"
    
    echo ""
    log_info "服務狀態總結: $healthy_count/$total_count 個服務正常"
    
    if [[ $healthy_count -eq $total_count ]] && [[ $total_count -gt 0 ]]; then
        return 0
    else
        return 1
    fi
}

# API 端點測試
test_api_endpoints() {
    log_info "測試 API 端點..."
    
    local api_host="localhost"
    local netstack_port="8080"
    local simworld_port="8888"
    
    # 等待服務啟動
    log_info "等待服務啟動 (最多 30 秒)..."
    local wait_count=0
    while [[ $wait_count -lt 30 ]]; do
        if curl -s "http://$api_host:$netstack_port/health" > /dev/null 2>&1; then
            break
        fi
        sleep 1
        ((wait_count++))
    done
    
    local endpoint_errors=0
    
    # NetStack API 測試
    echo ""
    echo "🔍 NetStack API 測試："
    echo "====================="
    
    local netstack_endpoints=(
        "/health:健康檢查"
        "/api/v1/info:系統信息"
        "/api/v1/satellites/constellations/info:衛星星座信息"
    )
    
    for endpoint_info in "${netstack_endpoints[@]}"; do
        IFS=':' read -r endpoint description <<< "$endpoint_info"
        local url="http://$api_host:$netstack_port$endpoint"
        
        if curl -s -f "$url" > /dev/null 2>&1; then
            log_success "$description: $endpoint"
        else
            log_error "$description: $endpoint (無法訪問)"
            ((endpoint_errors++))
        fi
    done
    
    # SimWorld API 測試 (如果運行中)
    echo ""
    echo "🔍 SimWorld API 測試："
    echo "====================="
    
    if curl -s "http://$api_host:$simworld_port/health" > /dev/null 2>&1; then
        local simworld_endpoints=(
            "/health:健康檢查"
            "/api/system/info:系統信息"
        )
        
        for endpoint_info in "${simworld_endpoints[@]}"; do
            IFS=':' read -r endpoint description <<< "$endpoint_info"
            local url="http://$api_host:$simworld_port$endpoint"
            
            if curl -s -f "$url" > /dev/null 2>&1; then
                log_success "$description: $endpoint"
            else
                log_error "$description: $endpoint (無法訪問)"
                ((endpoint_errors++))
            fi
        done
    else
        log_warning "SimWorld API 未運行或無法訪問"
    fi
    
    return $endpoint_errors
}

# 性能基準測試
performance_benchmark() {
    log_info "執行基本性能測試..."
    
    local api_url="http://localhost:8080/health"
    
    # 測試響應時間
    log_info "測試 API 響應時間..."
    local response_times=()
    for i in {1..5}; do
        local start_time=$(date +%s.%N)
        if curl -s "$api_url" > /dev/null 2>&1; then
            local end_time=$(date +%s.%N)
            local duration=$(echo "$end_time - $start_time" | bc -l)
            response_times+=($duration)
        fi
    done
    
    if [[ ${#response_times[@]} -gt 0 ]]; then
        local total=0
        for time in "${response_times[@]}"; do
            total=$(echo "$total + $time" | bc -l)
        done
        local avg=$(echo "scale=3; $total / ${#response_times[@]}" | bc -l)
        log_success "平均響應時間: ${avg} 秒"
        
        if (( $(echo "$avg < 0.5" | bc -l) )); then
            log_success "響應時間良好 (< 0.5秒)"
        elif (( $(echo "$avg < 1.0" | bc -l) )); then
            log_warning "響應時間可接受 (< 1.0秒)"
        else
            log_warning "響應時間較慢 (> 1.0秒)"
        fi
    fi
}

# 資源使用檢查
check_resource_usage() {
    log_info "檢查資源使用狀況..."
    
    # Docker 容器資源使用
    echo ""
    echo "📊 容器資源使用："
    echo "================="
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" 2>/dev/null | head -10
    
    # 磁盤使用
    echo ""
    echo "💾 磁盤使用："
    echo "============"
    df -h "$PROJECT_DIR" | tail -1
    
    # Docker 映像大小
    echo ""
    echo "🐳 Docker 映像："
    echo "==============="
    docker images | grep -E "(netstack|simworld)" | head -5
}

# 主要驗證函數
run_verification() {
    local verification_type=$1
    local total_errors=0
    
    echo ""
    log_info "開始驗證類型: $verification_type"
    echo ""
    
    case $verification_type in
        "quick")
            check_docker || ((total_errors++))
            check_services || ((total_errors++))
            ;;
        "config")
            check_config_files || ((total_errors++))
            ;;
        "services")
            check_docker || ((total_errors++))
            check_services || ((total_errors++))
            ;;
        "api")
            test_api_endpoints || ((total_errors++))
            ;;
        "full")
            check_docker || ((total_errors++))
            check_config_files || ((total_errors++))
            check_services || ((total_errors++))
            test_api_endpoints || ((total_errors++))
            performance_benchmark
            check_resource_usage
            ;;
        *)
            log_error "未知的驗證類型: $verification_type"
            show_help
            return 1
            ;;
    esac
    
    echo ""
    echo "=============================="
    if [[ $total_errors -eq 0 ]]; then
        log_success "驗證完成！所有檢查都通過"
        echo "🎉 系統部署狀態良好"
    else
        log_error "驗證完成，發現 $total_errors 個問題"
        echo "🔧 請檢查上述問題並進行修復"
        return 1
    fi
    
    echo ""
    echo "💡 建議的後續步驟："
    echo "  1. 定期執行健康檢查: $0 quick"
    echo "  2. 監控系統資源使用情況"
    echo "  3. 查看服務日誌: docker-compose logs [service_name]"
    echo "  4. 備份重要配置和數據"
    
    return 0
}

# 主執行邏輯
main() {
    # 切換到項目目錄
    cd "$PROJECT_DIR"
    
    # 執行驗證
    run_verification "$VERIFICATION_TYPE"
    
    return $?
}

# 執行主函數
main "$@"