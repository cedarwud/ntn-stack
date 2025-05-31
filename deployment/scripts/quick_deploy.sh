#!/bin/bash
"""
快速部署腳本
與現有Makefile集成，支援一鍵部署

使用方式:
./deployment/scripts/quick_deploy.sh --service netstack --env development
./deployment/scripts/quick_deploy.sh --service simworld --env production --gpu

根據 TODO.md 第18項「部署流程優化與自動化」要求設計
"""

set -e  # 遇到錯誤立即退出

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默認值
SERVICE=""
ENVIRONMENT="development"
GPU_ENABLED=false
FORCE_DEPLOY=false
BACKUP_BEFORE_DEPLOY=false
DRY_RUN=false

# 腳本根路徑
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEPLOYMENT_DIR="$PROJECT_ROOT/deployment"

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 顯示使用說明
show_help() {
    cat << EOF
快速部署腳本

使用方式:
    $0 [選項]

選項:
    -s, --service SERVICE       指定服務 (netstack|simworld)
    -e, --env ENVIRONMENT      指定環境 (development|testing|laboratory|production|field)
    -g, --gpu                  啟用GPU支援
    -f, --force                強制部署（跳過檢查）
    -b, --backup               部署前創建備份
    -d, --dry-run              僅模擬執行，不實際部署
    -h, --help                 顯示此幫助信息

示例:
    $0 --service netstack --env development
    $0 --service simworld --env production --gpu --backup
    $0 --service netstack --env testing --force --dry-run

EOF
}

# 解析命令行參數
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -s|--service)
                SERVICE="$2"
                shift 2
                ;;
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -g|--gpu)
                GPU_ENABLED=true
                shift
                ;;
            -f|--force)
                FORCE_DEPLOY=true
                shift
                ;;
            -b|--backup)
                BACKUP_BEFORE_DEPLOY=true
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知參數: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# 驗證參數
validate_args() {
    if [[ -z "$SERVICE" ]]; then
        log_error "必須指定服務 (--service)"
        show_help
        exit 1
    fi

    if [[ "$SERVICE" != "netstack" && "$SERVICE" != "simworld" ]]; then
        log_error "無效的服務: $SERVICE (支援: netstack, simworld)"
        exit 1
    fi

    if [[ "$ENVIRONMENT" != "development" && "$ENVIRONMENT" != "testing" && 
          "$ENVIRONMENT" != "laboratory" && "$ENVIRONMENT" != "production" && 
          "$ENVIRONMENT" != "field" ]]; then
        log_error "無效的環境: $ENVIRONMENT"
        exit 1
    fi
}

# 檢查依賴
check_dependencies() {
    log_info "檢查依賴..."

    # 檢查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "未找到 Docker，請先安裝 Docker"
        exit 1
    fi

    # 檢查 Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "未找到 Docker Compose，請先安裝 Docker Compose"
        exit 1
    fi

    # 檢查 Python
    if ! command -v python3 &> /dev/null; then
        log_error "未找到 Python 3，請先安裝 Python 3"
        exit 1
    fi

    # 檢查 Make
    if ! command -v make &> /dev/null; then
        log_error "未找到 Make，請先安裝 Make"
        exit 1
    fi

    log_success "依賴檢查通過"
}

# 檢查 GPU 支援
check_gpu_support() {
    if [[ "$GPU_ENABLED" == "true" ]]; then
        log_info "檢查 GPU 支援..."

        if ! command -v nvidia-docker &> /dev/null && ! docker info | grep -q "nvidia"; then
            log_warning "未檢測到 NVIDIA Docker 支援，GPU 功能可能無法正常工作"
        else
            log_success "GPU 支援檢查通過"
        fi
    fi
}

# 初始化部署環境
init_deployment_env() {
    log_info "初始化部署環境..."

    # 創建必要的目錄
    mkdir -p "$DEPLOYMENT_DIR/logs"
    mkdir -p "$DEPLOYMENT_DIR/configs"
    mkdir -p "$DEPLOYMENT_DIR/backups"

    # 檢查並安裝 Python 依賴
    if [[ -f "$DEPLOYMENT_DIR/requirements.txt" ]]; then
        log_info "安裝 Python 依賴..."
        python3 -m pip install -r "$DEPLOYMENT_DIR/requirements.txt" --quiet
    fi

    log_success "部署環境初始化完成"
}

# 創建備份
create_backup() {
    if [[ "$BACKUP_BEFORE_DEPLOY" == "true" ]]; then
        log_info "創建部署前備份..."

        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] 將創建 $SERVICE 服務的完整備份"
        else
            cd "$PROJECT_ROOT"
            python3 deployment/cli/deploy_cli.py backup --service "$SERVICE" --type full --comment "Pre-deployment backup"
            
            if [[ $? -eq 0 ]]; then
                log_success "備份創建完成"
            else
                log_error "備份創建失敗"
                exit 1
            fi
        fi
    fi
}

# 生成部署配置
generate_config() {
    log_info "生成部署配置..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將生成 $SERVICE-$ENVIRONMENT 配置"
        return
    fi

    cd "$PROJECT_ROOT"
    
    # 構建配置生成命令
    CONFIG_CMD="python3 deployment/cli/deploy_cli.py config generate --service $SERVICE --env $ENVIRONMENT"
    
    if [[ "$GPU_ENABLED" == "true" ]]; then
        CONFIG_CMD="$CONFIG_CMD --gpu"
    fi

    # 執行配置生成
    eval "$CONFIG_CMD"
    
    if [[ $? -eq 0 ]]; then
        log_success "配置生成完成"
    else
        log_error "配置生成失敗"
        exit 1
    fi
}

# 部署前檢查
pre_deployment_check() {
    log_info "執行部署前檢查..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將執行部署前檢查"
        return
    fi

    cd "$PROJECT_ROOT"

    # 檢查端口衝突
    if [[ "$SERVICE" == "netstack" ]]; then
        PORTS=(8080 27017)
    else
        PORTS=(8888 5173 5432)
    fi

    for port in "${PORTS[@]}"; do
        if netstat -tuln | grep -q ":$port "; then
            if [[ "$FORCE_DEPLOY" != "true" ]]; then
                log_error "端口 $port 已被佔用，使用 --force 強制部署"
                exit 1
            else
                log_warning "端口 $port 已被佔用，但使用強制模式繼續"
            fi
        fi
    done

    # 檢查磁碟空間
    AVAILABLE_SPACE=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
    REQUIRED_SPACE=5242880  # 5GB in KB

    if [[ $AVAILABLE_SPACE -lt $REQUIRED_SPACE ]]; then
        log_error "磁碟空間不足，至少需要 5GB 可用空間"
        exit 1
    fi

    log_success "部署前檢查通過"
}

# 停止現有服務
stop_existing_services() {
    log_info "停止現有服務..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將停止 $SERVICE 服務"
        return
    fi

    cd "$PROJECT_ROOT"

    # 使用 Makefile 停止服務
    if [[ "$SERVICE" == "netstack" ]]; then
        make netstack-stop || log_warning "NetStack 服務可能未在運行"
    else
        make simworld-stop || log_warning "SimWorld 服務可能未在運行"
    fi

    log_success "現有服務已停止"
}

# 執行部署
deploy_service() {
    log_info "部署 $SERVICE 服務 ($ENVIRONMENT 環境)..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將部署 $SERVICE 服務到 $ENVIRONMENT 環境"
        if [[ "$GPU_ENABLED" == "true" ]]; then
            log_info "[DRY RUN] GPU 支援: 啟用"
        fi
        if [[ "$FORCE_DEPLOY" == "true" ]]; then
            log_info "[DRY RUN] 強制模式: 啟用"
        fi
        return
    fi

    cd "$PROJECT_ROOT"

    # 構建部署命令
    DEPLOY_CMD="python3 deployment/cli/deploy_cli.py deploy --service $SERVICE --env $ENVIRONMENT"
    
    if [[ "$GPU_ENABLED" == "true" ]]; then
        DEPLOY_CMD="$DEPLOY_CMD --gpu"
    fi
    
    if [[ "$FORCE_DEPLOY" == "true" ]]; then
        DEPLOY_CMD="$DEPLOY_CMD --force"
    fi

    # 執行部署
    eval "$DEPLOY_CMD"
    
    if [[ $? -eq 0 ]]; then
        log_success "$SERVICE 服務部署完成"
    else
        log_error "$SERVICE 服務部署失敗"
        exit 1
    fi
}

# 部署後健康檢查
post_deployment_check() {
    log_info "執行部署後健康檢查..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] 將執行健康檢查"
        return
    fi

    cd "$PROJECT_ROOT"

    # 等待服務啟動
    log_info "等待服務啟動..."
    sleep 10

    # 執行健康檢查
    python3 deployment/cli/deploy_cli.py health --service "$SERVICE"
    
    if [[ $? -eq 0 ]]; then
        log_success "健康檢查通過"
    else
        log_warning "健康檢查失敗，請檢查服務狀態"
    fi
}

# 顯示部署結果
show_deployment_result() {
    log_info "部署結果摘要:"
    echo "================================"
    echo "服務: $SERVICE"
    echo "環境: $ENVIRONMENT"
    echo "GPU 支援: $GPU_ENABLED"
    echo "強制模式: $FORCE_DEPLOY"
    echo "備份: $BACKUP_BEFORE_DEPLOY"
    echo "模擬執行: $DRY_RUN"
    echo "================================"

    if [[ "$DRY_RUN" != "true" ]]; then
        # 顯示服務訪問信息
        if [[ "$SERVICE" == "netstack" ]]; then
            echo "NetStack API: http://localhost:8080"
            echo "API 文檔: http://localhost:8080/docs"
        else
            echo "SimWorld 後端: http://localhost:8888"
            echo "SimWorld 前端: http://localhost:5173"
        fi
    fi

    log_success "部署流程完成"
}

# 清理函數
cleanup() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        log_error "部署過程中發生錯誤"
        
        if [[ "$DRY_RUN" != "true" ]]; then
            log_info "可以使用以下命令查看詳細狀態:"
            echo "  python3 deployment/cli/deploy_cli.py status --detailed"
            echo "  python3 deployment/cli/deploy_cli.py list-deployments --service $SERVICE --limit 5"
        fi
    fi
}

# 主函數
main() {
    echo "🚀 NTN Stack 快速部署工具"
    echo "================================"

    # 設置錯誤處理
    trap cleanup EXIT

    # 解析參數
    parse_args "$@"
    
    # 驗證參數
    validate_args

    # 執行部署流程
    check_dependencies
    check_gpu_support
    init_deployment_env
    create_backup
    generate_config
    pre_deployment_check
    stop_existing_services
    deploy_service
    post_deployment_check
    show_deployment_result
}

# 執行主函數
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 