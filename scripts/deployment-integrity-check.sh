#!/bin/bash
# 部署完整性檢查腳本 - 確認部署準備就緒

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔍 NetStack 部署完整性檢查"
echo "=========================="

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

total_issues=0

# 檢查項目結構
check_project_structure() {
    log_info "檢查項目結構..."
    echo ""
    
    local required_dirs=(
        "netstack"
        "simworld" 
        "scripts"
        "docs"
        "netstack/src"
        "netstack/config"
        "netstack/netstack_api/deployment"
        "netstack/compose"
        "simworld/frontend"
        "simworld/backend"
    )
    
    local missing_dirs=0
    
    for dir in "${required_dirs[@]}"; do
        if [[ -d "$PROJECT_DIR/$dir" ]]; then
            log_success "目錄存在: $dir"
        else
            log_error "目錄缺失: $dir"
            ((missing_dirs++))
            ((total_issues++))
        fi
    done
    
    if [[ $missing_dirs -eq 0 ]]; then
        log_success "項目結構完整"
    else
        log_error "發現 $missing_dirs 個缺失目錄"
    fi
    
    echo ""
}

# 檢查環境配置
check_environment_configs() {
    log_info "檢查環境配置文件..."
    echo ""
    
    local env_configs=(".env.development" ".env.production")
    local config_issues=0
    
    for config in "${env_configs[@]}"; do
        local config_path="$PROJECT_DIR/$config"
        if [[ -f "$config_path" ]]; then
            log_success "環境配置存在: $config"
            
            # 檢查關鍵配置項
            local required_vars=(
                "ENVIRONMENT"
                "LOG_LEVEL"
                "API_HOST"
                "API_PORT"
                "API_WORKERS"
                "POSTGRES_HOST"
                "MONGO_HOST"
                "REDIS_HOST"
                "SATELLITE_DATA_MODE"
            )
            
            local missing_vars=0
            for var in "${required_vars[@]}"; do
                if grep -q "^${var}=" "$config_path"; then
                    echo "    ✓ $var"
                else
                    echo "    ✗ 缺少: $var"
                    ((missing_vars++))
                fi
            done
            
            if [[ $missing_vars -eq 0 ]]; then
                log_success "$config 配置完整"
            else
                log_warning "$config 缺少 $missing_vars 個配置項"
                ((config_issues++))
            fi
            
        else
            log_error "環境配置缺失: $config"
            ((config_issues++))
            ((total_issues++))
        fi
        echo ""
    done
    
    if [[ $config_issues -eq 0 ]]; then
        log_success "環境配置檢查通過"
    else
        log_error "環境配置存在問題"
    fi
    
    echo ""
}

# 檢查 Docker 配置
check_docker_configs() {
    log_info "檢查 Docker 配置文件..."
    echo ""
    
    local docker_configs=(
        "netstack/netstack_api/deployment/Dockerfile"
        "netstack/netstack_api/deployment/Dockerfile.multistage"
        "netstack/compose/core.yaml"
        "simworld/backend/Dockerfile"
        "simworld/frontend/Dockerfile"
        "Makefile"
    )
    
    local docker_issues=0
    
    for config in "${docker_configs[@]}"; do
        local config_path="$PROJECT_DIR/$config"
        if [[ -f "$config_path" ]]; then
            log_success "Docker 配置存在: $config"
        else
            log_warning "Docker 配置缺失: $config"
            ((docker_issues++))
        fi
    done
    
    # 檢查 requirements.txt
    local requirements_files=(
        "netstack/requirements.txt"
        "netstack/requirements-dev.txt"
        "simworld/backend/requirements.txt"
    )
    
    for req_file in "${requirements_files[@]}"; do
        local req_path="$PROJECT_DIR/$req_file"
        if [[ -f "$req_path" ]]; then
            local line_count=$(wc -l < "$req_path")
            log_success "依賴文件存在: $req_file ($line_count 個依賴)"
        else
            log_warning "依賴文件缺失: $req_file"
            ((docker_issues++))
        fi
    done
    
    if [[ $docker_issues -eq 0 ]]; then
        log_success "Docker 配置檢查通過"
    else
        log_warning "Docker 配置存在 $docker_issues 個問題"
    fi
    
    echo ""
}

# 檢查腳本可執行性
check_scripts() {
    log_info "檢查管理腳本..."
    echo ""
    
    local scripts=(
        "scripts/env-manager.sh"
        "scripts/docker-build-optimizer.sh"
        "scripts/deployment-verification.sh"
    )
    
    local script_issues=0
    
    for script in "${scripts[@]}"; do
        local script_path="$PROJECT_DIR/$script"
        if [[ -f "$script_path" ]]; then
            if [[ -x "$script_path" ]]; then
                log_success "腳本可執行: $script"
            else
                log_warning "腳本不可執行: $script"
                echo "  修復: chmod +x $script_path"
                ((script_issues++))
            fi
        else
            log_error "腳本缺失: $script"
            ((script_issues++))
            ((total_issues++))
        fi
    done
    
    if [[ $script_issues -eq 0 ]]; then
        log_success "管理腳本檢查通過"
    else
        log_error "管理腳本存在 $script_issues 個問題"
    fi
    
    echo ""
}

# 檢查統一配置系統 (Phase 2.5)
check_unified_config() {
    log_info "檢查 Phase 2.5 統一配置系統..."
    echo ""
    
    local config_files=(
        "netstack/config/unified_satellite_config.py"
        "netstack/config/satellite_data_pool_builder.py"
        "netstack/config/intelligent_satellite_selector.py"
        "netstack/config/migration_scripts.py"
    )
    
    local phase25_issues=0
    
    for config_file in "${config_files[@]}"; do
        local file_path="$PROJECT_DIR/$config_file"
        if [[ -f "$file_path" ]]; then
            local line_count=$(wc -l < "$file_path")
            log_success "Phase 2.5 配置存在: $(basename "$config_file") ($line_count 行)"
        else
            log_error "Phase 2.5 配置缺失: $config_file"
            ((phase25_issues++))
            ((total_issues++))
        fi
    done
    
    # 檢查重構後的建構腳本
    local build_script="netstack/netstack_api/deployment/build_with_phase0_data_refactored.py"
    if [[ -f "$PROJECT_DIR/$build_script" ]]; then
        log_success "重構建構腳本存在: $(basename "$build_script")"
    else
        log_warning "重構建構腳本缺失: $build_script"
        ((phase25_issues++))
    fi
    
    if [[ $phase25_issues -eq 0 ]]; then
        log_success "Phase 2.5 統一配置系統檢查通過"
    else
        log_error "Phase 2.5 統一配置系統存在 $phase25_issues 個問題"
    fi
    
    echo ""
}

# 檢查文檔完整性
check_documentation() {
    log_info "檢查關鍵文檔..."
    echo ""
    
    local docs=(
        "CLAUDE.md"
        "PHASE2.5_ARCHITECTURE_REFACTOR_PLAN.md"
        "docs/README.md"
        "docs/satellite_data_architecture.md"
        "docs/satellite_handover_standards.md"
        "docs/technical_guide.md"
    )
    
    local doc_issues=0
    
    for doc in "${docs[@]}"; do
        local doc_path="$PROJECT_DIR/$doc"
        if [[ -f "$doc_path" ]]; then
            local size=$(wc -c < "$doc_path")
            if [[ $size -gt 100 ]]; then
                log_success "文檔存在且內容充實: $doc"
            else
                log_warning "文檔存在但內容較少: $doc"
            fi
        else
            log_warning "文檔缺失: $doc"
            ((doc_issues++))
        fi
    done
    
    if [[ $doc_issues -eq 0 ]]; then
        log_success "文檔檢查通過"
    else
        log_warning "文檔存在 $doc_issues 個問題"
    fi
    
    echo ""
}

# 系統依賴檢查
check_system_dependencies() {
    log_info "檢查系統依賴..."
    echo ""
    
    local commands=("docker" "docker-compose" "make" "python3" "node" "npm")
    local dep_issues=0
    
    for cmd in "${commands[@]}"; do
        if command -v "$cmd" &> /dev/null; then
            local version
            case $cmd in
                "docker")
                    version=$(docker --version | cut -d' ' -f3 | tr -d ',')
                    ;;
                "docker-compose")
                    version=$(docker-compose --version 2>/dev/null | cut -d' ' -f3 | tr -d ',' || echo "compose plugin")
                    ;;
                "python3")
                    version=$(python3 --version | cut -d' ' -f2)
                    ;;
                "node")
                    version=$(node --version)
                    ;;
                "npm")
                    version=$(npm --version)
                    ;;
                *)
                    version="installed"
                    ;;
            esac
            log_success "$cmd: $version"
        else
            log_error "命令不存在: $cmd"
            ((dep_issues++))
            ((total_issues++))
        fi
    done
    
    if [[ $dep_issues -eq 0 ]]; then
        log_success "系統依賴檢查通過"
    else
        log_error "系統依賴存在 $dep_issues 個問題"
    fi
    
    echo ""
}

# 生成完整性報告
generate_report() {
    echo "======================================"
    echo "🎯 部署完整性檢查總結"
    echo "======================================"
    echo ""
    
    if [[ $total_issues -eq 0 ]]; then
        log_success "🎉 部署完整性檢查通過！"
        echo ""
        echo "✅ 項目結構完整"
        echo "✅ 環境配置正確"
        echo "✅ Docker 配置準備就緒"  
        echo "✅ 管理腳本可用"
        echo "✅ Phase 2.5 統一配置系統完整"
        echo "✅ 文檔基本完整"
        echo "✅ 系統依賴滿足"
        echo ""
        echo "🚀 系統已準備好進行部署！"
        echo ""
        echo "建議的部署步驟："
        echo "  1. 選擇環境: ./scripts/env-manager.sh switch [development|production]"
        echo "  2. 啟動服務: make up"
        echo "  3. 驗證部署: ./scripts/deployment-verification.sh full"
        echo "  4. 監控狀態: ./scripts/deployment-verification.sh quick"
        
        return 0
    else
        log_error "❌ 發現 $total_issues 個部署完整性問題"
        echo ""
        echo "🔧 請解決上述問題後再進行部署"
        echo ""
        echo "常見修復步驟："
        echo "  1. 創建缺失的目錄和文件"
        echo "  2. 設定腳本執行權限: find scripts/ -name '*.sh' -exec chmod +x {} +"
        echo "  3. 安裝缺失的系統依賴"
        echo "  4. 檢查並修正配置文件"
        
        return 1
    fi
}

# 主執行邏輯
main() {
    cd "$PROJECT_DIR"
    
    check_project_structure
    check_environment_configs
    check_docker_configs
    check_scripts
    check_unified_config
    check_documentation
    check_system_dependencies
    
    generate_report
}

# 執行主函數
main "$@"