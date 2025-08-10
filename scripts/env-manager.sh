#!/bin/bash
# 環境配置管理腳本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🌍 NetStack 環境配置管理器"
echo "============================"

# 檢查參數
ACTION=${1:-help}
ENV_NAME=${2:-development}

# 可用環境
AVAILABLE_ENVS=("development" "production")

# 顯示幫助
show_help() {
    echo "用法: $0 <action> [environment]"
    echo ""
    echo "Actions:"
    echo "  switch    - 切換到指定環境"
    echo "  current   - 顯示當前環境"
    echo "  validate  - 驗證環境配置"
    echo "  compare   - 比較環境配置差異"
    echo "  help      - 顯示此幫助信息"
    echo ""
    echo "Environments:"
    echo "  development  - 開發環境 (預設)"
    echo "  production   - 生產環境"
    echo ""
    echo "範例:"
    echo "  $0 switch production     # 切換到生產環境"
    echo "  $0 current              # 顯示當前環境"
    echo "  $0 validate development # 驗證開發環境配置"
}

# 驗證環境名稱
validate_env_name() {
    local env=$1
    for valid_env in "${AVAILABLE_ENVS[@]}"; do
        if [[ "$env" == "$valid_env" ]]; then
            return 0
        fi
    done
    echo "❌ 無效的環境名稱: $env"
    echo "可用環境: ${AVAILABLE_ENVS[*]}"
    return 1
}

# 切換環境
switch_environment() {
    local env=$1
    local env_file="$PROJECT_DIR/.env.$env"
    local current_env_file="$PROJECT_DIR/.env"
    
    echo "🔄 切換到 $env 環境..."
    
    if [[ ! -f "$env_file" ]]; then
        echo "❌ 環境配置文件不存在: $env_file"
        return 1
    fi
    
    # 備份當前 .env 文件
    if [[ -f "$current_env_file" ]]; then
        cp "$current_env_file" "$current_env_file.backup"
        echo "📋 已備份當前配置到 .env.backup"
    fi
    
    # 複製環境配置
    cp "$env_file" "$current_env_file"
    echo "✅ 已切換到 $env 環境"
    
    # 顯示關鍵配置
    echo ""
    echo "🔧 當前環境配置："
    echo "  環境: $(grep ENVIRONMENT= "$current_env_file" | cut -d= -f2)"
    echo "  日誌級別: $(grep LOG_LEVEL= "$current_env_file" | cut -d= -f2)"
    echo "  API Workers: $(grep API_WORKERS= "$current_env_file" | cut -d= -f2)"
    echo "  衛星數據模式: $(grep SATELLITE_DATA_MODE= "$current_env_file" | cut -d= -f2)"
    echo ""
    echo "💡 重新啟動服務以應用新配置："
    echo "   make netstack-restart"
}

# 顯示當前環境
show_current_environment() {
    local current_env_file="$PROJECT_DIR/.env"
    
    if [[ ! -f "$current_env_file" ]]; then
        echo "⚠️ 未找到當前環境配置文件 (.env)"
        echo "請使用 '$0 switch [environment]' 設置環境"
        return 1
    fi
    
    echo "📋 當前環境狀態："
    echo ""
    
    # 讀取主要配置
    local env_name=$(grep "^ENVIRONMENT=" "$current_env_file" 2>/dev/null | cut -d= -f2)
    local log_level=$(grep "^LOG_LEVEL=" "$current_env_file" 2>/dev/null | cut -d= -f2)
    local api_workers=$(grep "^API_WORKERS=" "$current_env_file" 2>/dev/null | cut -d= -f2)
    local satellite_mode=$(grep "^SATELLITE_DATA_MODE=" "$current_env_file" 2>/dev/null | cut -d= -f2)
    local debug=$(grep "^DEBUG=" "$current_env_file" 2>/dev/null | cut -d= -f2)
    
    echo "  🌍 環境: ${env_name:-未設定}"
    echo "  📊 日誌級別: ${log_level:-INFO}"
    echo "  ⚙️ API Workers: ${api_workers:-1}"
    echo "  🛰️ 衛星數據模式: ${satellite_mode:-instant_load}"
    echo "  🐛 除錯模式: ${debug:-false}"
    
    # 顯示配置文件修改時間
    local mod_time=$(stat -c %y "$current_env_file" 2>/dev/null | cut -d. -f1)
    echo "  ⏰ 配置更新: $mod_time"
    
    # 檢查是否與標準環境匹配
    echo ""
    echo "📝 環境匹配檢查："
    for env in "${AVAILABLE_ENVS[@]}"; do
        local env_file="$PROJECT_DIR/.env.$env"
        if [[ -f "$env_file" ]]; then
            if cmp -s "$current_env_file" "$env_file"; then
                echo "  ✅ 與 $env 環境完全匹配"
                return 0
            fi
        fi
    done
    echo "  ⚠️ 配置已修改，與標準環境不匹配"
}

# 驗證環境配置
validate_environment() {
    local env=$1
    local env_file="$PROJECT_DIR/.env.$env"
    
    echo "🔍 驗證 $env 環境配置..."
    echo ""
    
    if [[ ! -f "$env_file" ]]; then
        echo "❌ 環境配置文件不存在: $env_file"
        return 1
    fi
    
    echo "📋 配置文件檢查："
    echo "  ✅ 文件存在: $env_file"
    
    # 必需的配置項目
    local required_vars=(
        "ENVIRONMENT"
        "LOG_LEVEL" 
        "API_HOST"
        "API_PORT"
        "POSTGRES_HOST"
        "MONGO_HOST"
        "REDIS_HOST"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" "$env_file"; then
            local value=$(grep "^${var}=" "$env_file" | cut -d= -f2)
            echo "  ✅ $var = $value"
        else
            missing_vars+=("$var")
            echo "  ❌ 缺少: $var"
        fi
    done
    
    echo ""
    if [[ ${#missing_vars[@]} -eq 0 ]]; then
        echo "✅ $env 環境配置驗證通過"
        
        # 環境特定檢查
        if [[ "$env" == "development" ]]; then
            echo ""
            echo "🛠️ 開發環境特定檢查："
            if grep -q "DEBUG=true" "$env_file"; then
                echo "  ✅ 除錯模式已啟用"
            else
                echo "  ⚠️ 建議啟用除錯模式 (DEBUG=true)"
            fi
        elif [[ "$env" == "production" ]]; then
            echo ""
            echo "🏭 生產環境特定檢查："
            if grep -q "SECRET_KEY=.*change_me" "$env_file"; then
                echo "  ⚠️ 請更改預設的 SECRET_KEY"
            else
                echo "  ✅ SECRET_KEY 已自定義"
            fi
        fi
        
        return 0
    else
        echo "❌ $env 環境配置驗證失敗"
        echo "缺少必需配置: ${missing_vars[*]}"
        return 1
    fi
}

# 比較環境配置
compare_environments() {
    echo "📊 環境配置比較："
    echo ""
    
    for env in "${AVAILABLE_ENVS[@]}"; do
        local env_file="$PROJECT_DIR/.env.$env"
        if [[ -f "$env_file" ]]; then
            echo "📄 $env 環境："
            echo "  文件: $env_file"
            echo "  大小: $(wc -c < "$env_file") bytes"
            echo "  行數: $(wc -l < "$env_file") 行"
        else
            echo "❌ $env 環境: 配置文件不存在"
        fi
    done
    
    echo ""
    if [[ -f "$PROJECT_DIR/.env.development" ]] && [[ -f "$PROJECT_DIR/.env.production" ]]; then
        echo "🔍 主要配置差異："
        echo ""
        
        # 比較關鍵配置
        local dev_file="$PROJECT_DIR/.env.development"  
        local prod_file="$PROJECT_DIR/.env.production"
        
        local keys=("ENVIRONMENT" "LOG_LEVEL" "API_WORKERS" "SATELLITE_DATA_MODE" "DEBUG")
        
        printf "%-20s %-15s %-15s\n" "配置項" "Development" "Production"
        printf "%-20s %-15s %-15s\n" "----" "----" "----"
        
        for key in "${keys[@]}"; do
            local dev_val=$(grep "^${key}=" "$dev_file" 2>/dev/null | cut -d= -f2 || echo "未設定")
            local prod_val=$(grep "^${key}=" "$prod_file" 2>/dev/null | cut -d= -f2 || echo "未設定")
            printf "%-20s %-15s %-15s\n" "$key" "$dev_val" "$prod_val"
        done
    fi
}

# 主要邏輯
case $ACTION in
    switch)
        if validate_env_name "$ENV_NAME"; then
            switch_environment "$ENV_NAME"
        fi
        ;;
    current)
        show_current_environment
        ;;
    validate)
        if validate_env_name "$ENV_NAME"; then
            validate_environment "$ENV_NAME"
        fi
        ;;
    compare)
        compare_environments
        ;;
    help)
        show_help
        ;;
    *)
        echo "❌ 未知操作: $ACTION"
        echo ""
        show_help
        exit 1
        ;;
esac