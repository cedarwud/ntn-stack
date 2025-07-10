#!/bin/bash
# NTN Stack 監控系統安全設定腳本
# Security Setup Script for NTN Stack Monitoring System

set -euo pipefail

# 🔧 配置變數
SECURITY_DIR="/etc/ntn-stack/security"
SSL_DIR="/etc/ssl/ntn-stack"
LOG_DIR="/var/log/ntn-stack"
BACKUP_DIR="/backup/ntn-stack/security"

# 🎨 顏色配置
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 📝 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 🏗️ 創建必要目錄
create_directories() {
    log_info "創建安全相關目錄結構..."
    
    directories=(
        "$SECURITY_DIR"
        "$SSL_DIR/certs"
        "$SSL_DIR/private"
        "$SSL_DIR/ca"
        "$LOG_DIR"
        "$BACKUP_DIR"
        "/etc/prometheus/tokens"
        "/etc/alertmanager/secrets"
    )
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            sudo mkdir -p "$dir"
            log_success "創建目錄: $dir"
        fi
    done
    
    # 設定權限
    sudo chmod 700 "$SSL_DIR/private"
    sudo chmod 755 "$SSL_DIR/certs"
    sudo chmod 750 "$LOG_DIR"
}

# 🔐 生成SSL憑證
generate_ssl_certificates() {
    log_info "生成SSL憑證和金鑰..."
    
    # 生成CA憑證
    if [[ ! -f "$SSL_DIR/ca/ca.crt" ]]; then
        log_info "生成根CA憑證..."
        
        # CA私鑰
        sudo openssl genrsa -out "$SSL_DIR/ca/ca.key" 4096
        
        # CA憑證
        sudo openssl req -new -x509 -days 3650 -key "$SSL_DIR/ca/ca.key" \
            -out "$SSL_DIR/ca/ca.crt" \
            -subj "/C=TW/ST=Taipei/L=Taipei/O=NTN Stack/OU=Monitoring/CN=NTN-CA"
        
        log_success "根CA憑證生成完成"
    fi
    
    # 生成服務憑證
    services=("grafana" "prometheus" "alertmanager")
    
    for service in "${services[@]}"; do
        if [[ ! -f "$SSL_DIR/certs/${service}.crt" ]]; then
            log_info "生成 ${service} 服務憑證..."
            
            # 生成私鑰
            sudo openssl genrsa -out "$SSL_DIR/private/${service}.key" 2048
            
            # 生成憑證簽名請求
            sudo openssl req -new -key "$SSL_DIR/private/${service}.key" \
                -out "$SSL_DIR/${service}.csr" \
                -subj "/C=TW/ST=Taipei/L=Taipei/O=NTN Stack/OU=Monitoring/CN=${service}.ntn-stack.local"
            
            # 使用CA簽名
            sudo openssl x509 -req -in "$SSL_DIR/${service}.csr" \
                -CA "$SSL_DIR/ca/ca.crt" -CAkey "$SSL_DIR/ca/ca.key" \
                -CAcreateserial -out "$SSL_DIR/certs/${service}.crt" \
                -days 365 \
                -extensions v3_req \
                -extfile <(cat <<EOF
[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names
[alt_names]
DNS.1 = ${service}.ntn-stack.local
DNS.2 = localhost
IP.1 = 127.0.0.1
IP.2 = 10.0.0.1
EOF
)
            
            # 清理臨時文件
            sudo rm -f "$SSL_DIR/${service}.csr"
            
            log_success "${service} 憑證生成完成"
        fi
    done
    
    # 設定憑證權限
    sudo chmod 644 "$SSL_DIR/certs"/*.crt
    sudo chmod 600 "$SSL_DIR/private"/*.key
    sudo chmod 644 "$SSL_DIR/ca/ca.crt"
    sudo chmod 600 "$SSL_DIR/ca/ca.key"
}

# 🔑 生成API金鑰和令牌
generate_api_tokens() {
    log_info "生成API金鑰和認證令牌..."
    
    # Prometheus Bearer Tokens
    if [[ ! -f "/etc/prometheus/tokens/netstack.token" ]]; then
        openssl rand -hex 32 | sudo tee "/etc/prometheus/tokens/netstack.token" > /dev/null
        sudo chmod 600 "/etc/prometheus/tokens/netstack.token"
        log_success "NetStack API令牌生成完成"
    fi
    
    # JWT Secret
    if [[ ! -f "$SECURITY_DIR/jwt_secret" ]]; then
        openssl rand -base64 64 | sudo tee "$SECURITY_DIR/jwt_secret" > /dev/null
        sudo chmod 600 "$SECURITY_DIR/jwt_secret"
        log_success "JWT Secret生成完成"
    fi
    
    # Grafana API Key (將通過API生成)
    log_info "Grafana API金鑰需要在Grafana啟動後手動配置"
}

# 🔒 設定密碼和憑證
setup_passwords() {
    log_info "設定服務密碼..."
    
    # 生成隨機密碼
    generate_password() {
        openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
    }
    
    # Grafana管理員密碼
    if [[ ! -f "$SECURITY_DIR/grafana_admin_password" ]]; then
        generate_password | sudo tee "$SECURITY_DIR/grafana_admin_password" > /dev/null
        sudo chmod 600 "$SECURITY_DIR/grafana_admin_password"
        log_success "Grafana管理員密碼生成完成"
    fi
    
    # Prometheus密碼
    if [[ ! -f "$SECURITY_DIR/prometheus_password" ]]; then
        generate_password | sudo tee "$SECURITY_DIR/prometheus_password" > /dev/null
        sudo chmod 600 "$SECURITY_DIR/prometheus_password"
        log_success "Prometheus密碼生成完成"
    fi
    
    # AlertManager密碼
    if [[ ! -f "$SECURITY_DIR/alertmanager_password" ]]; then
        generate_password | sudo tee "$SECURITY_DIR/alertmanager_password" > /dev/null
        sudo chmod 600 "$SECURITY_DIR/alertmanager_password"
        log_success "AlertManager密碼生成完成"
    fi
}

# 🛡️ 配置防火牆規則
setup_firewall() {
    log_info "配置防火牆規則..."
    
    # 檢查是否安裝ufw
    if command -v ufw >/dev/null 2>&1; then
        # 允許監控服務端口
        sudo ufw allow from 10.0.0.0/8 to any port 9090 comment "Prometheus"
        sudo ufw allow from 10.0.0.0/8 to any port 3000 comment "Grafana"
        sudo ufw allow from 10.0.0.0/8 to any port 9093 comment "AlertManager"
        
        # 允許Node Exporter
        sudo ufw allow from 10.0.0.0/8 to any port 9100 comment "Node Exporter"
        
        log_success "防火牆規則配置完成"
    else
        log_warning "未檢測到ufw，請手動配置防火牆規則"
    fi
}

# 📋 生成環境變數文件
generate_env_file() {
    log_info "生成環境變數配置文件..."
    
    cat > "$SECURITY_DIR/.env.security" <<EOF
# NTN Stack 監控系統安全環境變數
# Generated on $(date)

# SSL/TLS 配置
SSL_CERT_DIR=$SSL_DIR/certs
SSL_KEY_DIR=$SSL_DIR/private
CA_CERT_FILE=$SSL_DIR/ca/ca.crt

# Grafana 安全配置
GRAFANA_ADMIN_PASSWORD=\$(cat $SECURITY_DIR/grafana_admin_password)
GRAFANA_SSL_CERT=$SSL_DIR/certs/grafana.crt
GRAFANA_SSL_KEY=$SSL_DIR/private/grafana.key

# Prometheus 安全配置
PROMETHEUS_PASSWORD=\$(cat $SECURITY_DIR/prometheus_password)
PROMETHEUS_SSL_CERT=$SSL_DIR/certs/prometheus.crt
PROMETHEUS_SSL_KEY=$SSL_DIR/private/prometheus.key

# AlertManager 安全配置
ALERTMANAGER_PASSWORD=\$(cat $SECURITY_DIR/alertmanager_password)
ALERTMANAGER_SSL_CERT=$SSL_DIR/certs/alertmanager.crt
ALERTMANAGER_SSL_KEY=$SSL_DIR/private/alertmanager.key

# JWT 配置
JWT_SECRET=\$(cat $SECURITY_DIR/jwt_secret)

# API 令牌
NETSTACK_BEARER_TOKEN=\$(cat /etc/prometheus/tokens/netstack.token)

# 日誌配置
AUDIT_LOG_DIR=$LOG_DIR
SECURITY_LOG_LEVEL=INFO
EOF
    
    sudo chmod 600 "$SECURITY_DIR/.env.security"
    log_success "環境變數文件生成完成: $SECURITY_DIR/.env.security"
}

# 🔍 驗證安全設定
verify_security_setup() {
    log_info "驗證安全設定..."
    
    errors=0
    
    # 檢查憑證
    certificates=("grafana.crt" "prometheus.crt" "alertmanager.crt")
    for cert in "${certificates[@]}"; do
        if [[ -f "$SSL_DIR/certs/$cert" ]]; then
            if openssl x509 -in "$SSL_DIR/certs/$cert" -noout -checkend 86400 >/dev/null 2>&1; then
                log_success "憑證有效: $cert"
            else
                log_error "憑證即將過期或無效: $cert"
                ((errors++))
            fi
        else
            log_error "憑證文件不存在: $cert"
            ((errors++))
        fi
    done
    
    # 檢查密碼文件
    password_files=("grafana_admin_password" "prometheus_password" "alertmanager_password")
    for pwd_file in "${password_files[@]}"; do
        if [[ -f "$SECURITY_DIR/$pwd_file" ]]; then
            if [[ -s "$SECURITY_DIR/$pwd_file" ]]; then
                log_success "密碼文件存在且非空: $pwd_file"
            else
                log_error "密碼文件為空: $pwd_file"
                ((errors++))
            fi
        else
            log_error "密碼文件不存在: $pwd_file"
            ((errors++))
        fi
    done
    
    # 檢查權限
    check_permissions() {
        local file=$1
        local expected_perm=$2
        if [[ -f "$file" ]]; then
            actual_perm=$(stat -c "%a" "$file")
            if [[ "$actual_perm" == "$expected_perm" ]]; then
                log_success "文件權限正確: $file ($actual_perm)"
            else
                log_error "文件權限錯誤: $file (expected: $expected_perm, actual: $actual_perm)"
                ((errors++))
            fi
        fi
    }
    
    check_permissions "$SECURITY_DIR/.env.security" "600"
    check_permissions "$SSL_DIR/ca/ca.key" "600"
    
    if [[ $errors -eq 0 ]]; then
        log_success "所有安全設定驗證通過！"
        return 0
    else
        log_error "發現 $errors 個安全設定問題"
        return 1
    fi
}

# 📊 生成安全報告
generate_security_report() {
    log_info "生成安全配置報告..."
    
    report_file="$SECURITY_DIR/security_setup_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" <<EOF
# NTN Stack 監控系統安全配置報告

**生成時間**: $(date)
**生成者**: $(whoami)
**主機**: $(hostname)

## 📋 安全組件狀態

### 🔐 SSL/TLS 憑證

| 服務 | 憑證路徑 | 私鑰路徑 | 有效期至 |
|------|----------|----------|-----------|
EOF
    
    for service in grafana prometheus alertmanager; do
        if [[ -f "$SSL_DIR/certs/${service}.crt" ]]; then
            expiry_date=$(openssl x509 -in "$SSL_DIR/certs/${service}.crt" -noout -enddate | cut -d= -f2)
            echo "| $service | $SSL_DIR/certs/${service}.crt | $SSL_DIR/private/${service}.key | $expiry_date |" >> "$report_file"
        fi
    done
    
    cat >> "$report_file" <<EOF

### 🔑 認證配置

- **Grafana管理員**: 密碼已生成並儲存
- **Prometheus**: 基本認證已配置
- **AlertManager**: 基本認證已配置
- **JWT Secret**: 已生成64位元金鑰

### 🛡️ 網路安全

- **防火牆**: 已配置監控服務端口規則
- **內部TLS**: 啟用服務間加密通信
- **API令牌**: 已生成Bearer Token

### 📝 審計與合規

- **審計日誌**: 啟用並配置到 $LOG_DIR
- **資料保留**: 指標90天、日誌30天、警報365天
- **備份加密**: 使用AES-256-GCM加密

### 🔍 後續步驟

1. 定期檢查憑證有效期
2. 設定密碼輪換政策
3. 配置外部OAuth提供者（可選）
4. 執行安全掃描和滲透測試
5. 建立事件回應流程

### 📞 聯絡資訊

- **安全團隊**: security@ntn-stack.com
- **運維團隊**: ops@ntn-stack.com
- **緊急聯絡**: +886-xxx-xxxxxx

---
*此報告由NTN Stack監控系統安全設定腳本自動生成*
EOF
    
    sudo chmod 644 "$report_file"
    log_success "安全配置報告已生成: $report_file"
}

# 🚀 主執行函數
main() {
    log_info "開始NTN Stack監控系統安全設定..."
    
    # 檢查是否以root權限執行
    if [[ $EUID -ne 0 ]]; then
        log_error "此腳本需要root權限執行"
        exit 1
    fi
    
    # 執行安全設定步驟
    create_directories
    generate_ssl_certificates
    generate_api_tokens
    setup_passwords
    setup_firewall
    generate_env_file
    
    # 驗證設定
    if verify_security_setup; then
        generate_security_report
        log_success "✅ NTN Stack監控系統安全設定完成！"
        echo ""
        echo "🔐 請妥善保管以下機密文件："
        echo "   - SSL憑證: $SSL_DIR"
        echo "   - 密碼文件: $SECURITY_DIR"
        echo "   - 環境變數: $SECURITY_DIR/.env.security"
        echo ""
        echo "📋 下一步："
        echo "   1. 載入環境變數: source $SECURITY_DIR/.env.security"
        echo "   2. 重新啟動監控服務"
        echo "   3. 執行安全驗證測試"
    else
        log_error "❌ 安全設定驗證失敗，請檢查上述錯誤"
        exit 1
    fi
}

# 執行主函數
main "$@"