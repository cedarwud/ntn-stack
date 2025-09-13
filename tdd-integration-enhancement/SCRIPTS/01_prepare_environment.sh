#!/bin/bash
# 🛠️ TDD整合環境準備腳本
# 版本: 1.0.0
# 用途: 準備TDD整合所需的環境和依賴

set -e  # 遇到錯誤立即退出

# =============================================================================
# 📋 全局變量定義
# =============================================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
TDD_ENHANCEMENT_DIR="$PROJECT_ROOT/tdd-integration-enhancement"
SATELLITE_SYSTEM_DIR="$PROJECT_ROOT/satellite-processing-system"

# 顏色輸出定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# 🔧 輔助函數
# =============================================================================
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

check_command() {
    if command -v "$1" >/dev/null 2>&1; then
        log_success "$1 已安裝"
        return 0
    else
        log_error "$1 未安裝"
        return 1
    fi
}

create_directory() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        log_success "創建目錄: $1"
    else
        log_info "目錄已存在: $1"
    fi
}

# =============================================================================
# 🎯 主要功能函數
# =============================================================================

check_prerequisites() {
    log_info "🔍 檢查系統前置條件..."
    
    local missing_commands=()
    
    # 檢查必要的命令
    if ! check_command "python3"; then missing_commands+=("python3"); fi
    if ! check_command "pip3"; then missing_commands+=("pip3"); fi
    if ! check_command "docker"; then missing_commands+=("docker"); fi
    if ! check_command "git"; then missing_commands+=("git"); fi
    
    # 可選但推薦的命令
    if ! check_command "pytest"; then 
        log_warning "pytest 未安裝，將嘗試安裝"
    fi
    
    if [ ${#missing_commands[@]} -gt 0 ]; then
        log_error "缺少必要命令: ${missing_commands[*]}"
        log_error "請安裝缺少的軟體後重新執行此腳本"
        exit 1
    fi
    
    log_success "系統前置條件檢查完成"
}

create_directory_structure() {
    log_info "📁 創建TDD整合目錄結構..."
    
    # 在satellite-processing-system中創建TDD相關目錄
    local tdd_dirs=(
        "$SATELLITE_SYSTEM_DIR/tests/tdd_integration"
        "$SATELLITE_SYSTEM_DIR/tests/tdd_integration/regression"
        "$SATELLITE_SYSTEM_DIR/tests/tdd_integration/performance"  
        "$SATELLITE_SYSTEM_DIR/tests/tdd_integration/integration"
        "$SATELLITE_SYSTEM_DIR/tests/tdd_integration/fixtures"
        "$SATELLITE_SYSTEM_DIR/data/tdd_test_results"
        "$SATELLITE_SYSTEM_DIR/data/performance_history"
        "$SATELLITE_SYSTEM_DIR/data/tdd_reports"
        "$SATELLITE_SYSTEM_DIR/logs/tdd_integration"
        "$SATELLITE_SYSTEM_DIR/config/tdd_integration"
    )
    
    for dir in "${tdd_dirs[@]}"; do
        create_directory "$dir"
    done
    
    log_success "TDD整合目錄結構創建完成"
}

setup_python_environment() {
    log_info "🐍 設置Python測試環境..."
    
    # 檢查是否在虛擬環境中
    if [[ -z "${VIRTUAL_ENV}" ]]; then
        log_warning "未檢測到虛擬環境，建議在虛擬環境中運行"
        read -p "是否要創建新的虛擬環境? (y/N): " create_venv
        
        if [[ $create_venv == "y" || $create_venv == "Y" ]]; then
            log_info "創建虛擬環境..."
            cd "$PROJECT_ROOT"
            python3 -m venv tdd_integration_env
            source tdd_integration_env/bin/activate
            log_success "虛擬環境創建並啟動"
        fi
    else
        log_success "檢測到虛擬環境: $VIRTUAL_ENV"
    fi
    
    # 升級pip
    log_info "升級pip..."
    pip3 install --upgrade pip
    
    # 安裝測試相關依賴
    log_info "安裝測試依賴..."
    local test_dependencies=(
        "pytest>=7.0.0"
        "pytest-html>=3.0.0"
        "pytest-cov>=4.0.0" 
        "pytest-benchmark>=4.0.0"
        "pytest-mock>=3.10.0"
        "pyyaml>=6.0"
        "jsonschema>=4.0.0"
    )
    
    for dep in "${test_dependencies[@]}"; do
        log_info "安裝: $dep"
        pip3 install "$dep"
    done
    
    log_success "Python測試環境設置完成"
}

copy_configuration_templates() {
    log_info "📄 複製配置模板..."
    
    local config_source="$TDD_ENHANCEMENT_DIR/CONFIG_TEMPLATES"
    local config_dest="$SATELLITE_SYSTEM_DIR/config/tdd_integration"
    
    if [ -d "$config_source" ]; then
        # 複製主要配置文件
        cp "$config_source/tdd_integration_config.yml" "$config_dest/"
        cp -r "$config_source/environment_profiles" "$config_dest/"
        
        # 設置預設環境配置
        local current_env="${TDD_ENV:-development}"
        if [ -f "$config_dest/environment_profiles/$current_env.yml" ]; then
            cp "$config_dest/environment_profiles/$current_env.yml" "$config_dest/current_environment.yml"
            log_success "設置當前環境配置: $current_env"
        fi
        
        log_success "配置模板複製完成"
    else
        log_error "配置模板目錄不存在: $config_source"
        exit 1
    fi
}

copy_test_templates() {
    log_info "🧪 複製測試模板..."
    
    local template_source="$TDD_ENHANCEMENT_DIR/TEST_TEMPLATES"
    local template_dest="$SATELLITE_SYSTEM_DIR/tests/tdd_integration"
    
    if [ -d "$template_source" ]; then
        # 複製測試模板文件
        find "$template_source" -name "*.py" -exec cp {} "$template_dest/" \;
        
        # 複製測試固定數據
        if [ -d "$template_source/fixtures" ]; then
            cp -r "$template_source/fixtures/"* "$template_dest/fixtures/"
        fi
        
        log_success "測試模板複製完成"
    else
        log_warning "測試模板目錄不存在: $template_source"
    fi
}

create_initial_files() {
    log_info "📝 創建初始化文件..."
    
    # 創建 __init__.py 文件
    local init_dirs=(
        "$SATELLITE_SYSTEM_DIR/tests/tdd_integration"
        "$SATELLITE_SYSTEM_DIR/tests/tdd_integration/regression"
        "$SATELLITE_SYSTEM_DIR/tests/tdd_integration/performance"
        "$SATELLITE_SYSTEM_DIR/tests/tdd_integration/integration"
    )
    
    for dir in "${init_dirs[@]}"; do
        touch "$dir/__init__.py"
    done
    
    # 創建pytest配置文件
    cat > "$SATELLITE_SYSTEM_DIR/tests/tdd_integration/pytest.ini" << 'EOF'
[tool:pytest]
minversion = 6.0
addopts = -ra -q --tb=short
testpaths = 
    regression
    performance  
    integration
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
markers =
    regression: regression test
    performance: performance test
    integration: integration test
    tdd: tdd integration test
EOF

    # 創建測試配置文件
    cat > "$SATELLITE_SYSTEM_DIR/tests/tdd_integration/conftest.py" << 'EOF'
"""TDD整合測試配置"""
import pytest
import yaml
from pathlib import Path

@pytest.fixture(scope="session")
def tdd_config():
    """載入TDD整合配置"""
    config_path = Path(__file__).parent.parent.parent / "config" / "tdd_integration" / "tdd_integration_config.yml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

@pytest.fixture
def validation_snapshots_dir():
    """驗證快照目錄"""
    return Path(__file__).parent.parent.parent / "data" / "validation_snapshots"

@pytest.fixture  
def test_results_dir():
    """測試結果目錄"""
    return Path(__file__).parent.parent.parent / "data" / "tdd_test_results"
EOF
    
    log_success "初始化文件創建完成"
}

setup_docker_integration() {
    log_info "🐳 設置Docker整合..."
    
    # 檢查Docker是否運行
    if ! docker info >/dev/null 2>&1; then
        log_warning "Docker未運行，跳過Docker整合設置"
        return 0
    fi
    
    # 檢查satellite-processing-system容器是否存在
    if docker ps -a --format "table {{.Names}}" | grep -q "satellite-processor"; then
        log_success "檢測到satellite-processor容器"
        
        # 在容器中創建TDD目錄
        docker exec satellite-processor mkdir -p /satellite-processing/tests/tdd_integration
        docker exec satellite-processor mkdir -p /satellite-processing/data/tdd_test_results
        
        log_success "Docker容器TDD目錄創建完成"
    else
        log_warning "未找到satellite-processor容器，跳過容器內設置"
    fi
}

validate_setup() {
    log_info "✅ 驗證設置..."
    
    local validation_errors=0
    
    # 檢查關鍵目錄是否存在
    local required_dirs=(
        "$SATELLITE_SYSTEM_DIR/tests/tdd_integration"
        "$SATELLITE_SYSTEM_DIR/config/tdd_integration"
        "$SATELLITE_SYSTEM_DIR/data/tdd_test_results"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            log_error "缺少目錄: $dir"
            validation_errors=$((validation_errors + 1))
        fi
    done
    
    # 檢查關鍵文件是否存在
    local required_files=(
        "$SATELLITE_SYSTEM_DIR/config/tdd_integration/tdd_integration_config.yml"
        "$SATELLITE_SYSTEM_DIR/tests/tdd_integration/conftest.py"
        "$SATELLITE_SYSTEM_DIR/tests/tdd_integration/pytest.ini"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "缺少文件: $file"
            validation_errors=$((validation_errors + 1))
        fi
    done
    
    # 檢查Python依賴
    if ! python3 -c "import pytest, yaml" >/dev/null 2>&1; then
        log_error "Python測試依賴未正確安裝"
        validation_errors=$((validation_errors + 1))
    fi
    
    if [ $validation_errors -eq 0 ]; then
        log_success "環境設置驗證通過"
        return 0
    else
        log_error "環境設置驗證失敗，發現 $validation_errors 個錯誤"
        return 1
    fi
}

# =============================================================================
# 🚀 主要執行流程
# =============================================================================

main() {
    echo "🧪 TDD整合環境準備腳本 v1.0.0"
    echo "============================================"
    echo ""
    
    # 執行各個設置步驟
    check_prerequisites
    echo ""
    
    create_directory_structure  
    echo ""
    
    setup_python_environment
    echo ""
    
    copy_configuration_templates
    echo ""
    
    copy_test_templates
    echo ""
    
    create_initial_files
    echo ""
    
    setup_docker_integration
    echo ""
    
    # 驗證設置
    if validate_setup; then
        echo ""
        log_success "🎉 TDD整合環境準備完成！"
        echo ""
        echo "下一步："
        echo "1. 檢查配置文件: $SATELLITE_SYSTEM_DIR/config/tdd_integration/"
        echo "2. 執行測試驗證: cd $SATELLITE_SYSTEM_DIR && python -m pytest tests/tdd_integration/ -v"
        echo "3. 查看整合文檔: $TDD_ENHANCEMENT_DIR/README.md"
        echo ""
    else
        echo ""
        log_error "❌ TDD整合環境準備失敗"
        echo "請檢查上述錯誤並重新執行腳本"
        exit 1
    fi
}

# =============================================================================
# 🎯 腳本入口點  
# =============================================================================

# 檢查是否為直接執行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi