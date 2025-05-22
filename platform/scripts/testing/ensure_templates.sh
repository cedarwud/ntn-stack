#!/bin/bash

# 模板同步腳本
# 此腳本確保配置模板在正確的位置並對配置API可訪問

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 腳本路徑常量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"

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

# 確保模板目錄存在
ensure_template_dir() {
    log_info "確保模板目錄結構..."
    
    # 確保模板目錄存在
    mkdir -p "$ROOT_DIR/config/ueransim"
    
    # 確保生成的配置目錄存在
    mkdir -p "$ROOT_DIR/config/generated"
    
    # 確保權限正確
    chmod -R 755 "$ROOT_DIR/config"
    
    log_success "目錄結構檢查完成"
}

# 檢查模板是否存在
check_templates() {
    log_info "檢查必要的模板文件..."
    
    local TEMPLATE_DIR="$ROOT_DIR/config/ueransim"
    local MISSING=0
    
    # 定義必須的模板
    local REQUIRED_TEMPLATES=(
        "gnb_leo.yaml"
        "gnb_geo.yaml" 
        "gnb_meo.yaml"
        "gnb_ground.yaml"
        "ue_leo.yaml"
        "ue_geo.yaml"
        "ue_meo.yaml"
        "ue_ground.yaml"
    )
    
    # 檢查每個必須的模板
    for template in "${REQUIRED_TEMPLATES[@]}"; do
        if [ ! -f "$TEMPLATE_DIR/$template" ]; then
            log_error "模板文件缺失: $template"
            MISSING=1
        else
            log_success "模板文件存在: $template"
        fi
    done
    
    return $MISSING
}

# 更新模板文件權限
update_permissions() {
    log_info "更新模板文件權限..."
    
    # 設置可讀寫權限
    chmod -R 644 "$ROOT_DIR/config/ueransim"/*.yaml
    
    log_success "權限更新完成"
}

# 主函數
main() {
    log_info "開始檢查和同步模板..."
    
    ensure_template_dir
    check_templates
    update_permissions
    
    log_success "模板檢查和同步完成"
}

# 執行主函數
main "$@" 