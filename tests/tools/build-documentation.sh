#!/bin/bash
# NTN Stack 文檔建置腳本
# 自動生成完整的文檔體系，包括HTML、PDF等多種格式

set -e

# 設定變數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCS_DIR="$PROJECT_ROOT/docs"
BUILD_DIR="$PROJECT_ROOT/docs-build"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 記錄功能
log() {
    echo -e "${CYAN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 檢查依賴
check_dependencies() {
    log "檢查建置依賴..."
    
    local missing_deps=()
    
    # 檢查 Python 和 pip
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    if ! command -v pip3 &> /dev/null; then
        missing_deps+=("pip3")
    fi
    
    # 檢查 Node.js (用於某些文檔工具)
    if ! command -v node &> /dev/null; then
        missing_deps+=("nodejs")
    fi
    
    # 檢查 pandoc (用於格式轉換)
    if ! command -v pandoc &> /dev/null; then
        missing_deps+=("pandoc")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        error "缺少依賴: ${missing_deps[*]}"
        log "請安裝缺少的依賴:"
        echo "sudo apt-get update"
        echo "sudo apt-get install -y python3 python3-pip nodejs npm pandoc texlive-latex-base"
        exit 1
    fi
    
    success "所有依賴已滿足"
}

# 設置Python環境
setup_python_env() {
    log "設置Python文檔建置環境..."
    
    # 創建虛擬環境 (如果不存在)
    if [ ! -d "$PROJECT_ROOT/docs-venv" ]; then
        python3 -m venv "$PROJECT_ROOT/docs-venv"
    fi
    
    # 啟動虛擬環境
    source "$PROJECT_ROOT/docs-venv/bin/activate"
    
    # 安裝文檔建置工具
    pip3 install -q --upgrade pip
    pip3 install -q mkdocs mkdocs-material pymdown-extensions mkdocs-mermaid2-plugin
    pip3 install -q weasyprint reportlab markdown-pdf
    
    success "Python環境設置完成"
}

# 生成MkDocs配置
generate_mkdocs_config() {
    log "生成MkDocs配置檔..."
    
    cat > "$PROJECT_ROOT/mkdocs.yml" << 'EOF'
site_name: NTN Stack 系統文檔
site_description: 非地面網路堆疊系統完整文檔
site_author: NTN Stack 技術文檔組
repo_url: https://github.com/ntn-stack/documentation
edit_uri: edit/main/docs/

theme:
  name: material
  language: zh-TW
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - navigation.indexes
    - search.highlight
    - search.share
    - toc.integrate
  palette:
    - scheme: default
      primary: blue
      accent: cyan
      toggle:
        icon: material/brightness-7
        name: 切換到深色模式
    - scheme: slate
      primary: indigo
      accent: cyan
      toggle:
        icon: material/brightness-4
        name: 切換到淺色模式

nav:
  - 首頁: README.md
  - 系統架構:
    - 01-architecture/system-overview.md
    - 01-architecture/technical-architecture.md
    - 01-architecture/tactical-overview.md
  - 安裝部署:
    - 02-installation/quick-start.md
    - 02-installation/hardware-requirements.md
    - 02-installation/production-deployment.md
    - 02-installation/rapid-deployment.md
  - 用戶指南:
    - 03-user-guides/README.md
    - 03-user-guides/user-management.md
    - 03-user-guides/communication-setup.md
    - 03-user-guides/slice-management.md
  - API參考:
    - 04-api-reference/README.md
    - 04-api-reference/netstack-api.md
    - 04-api-reference/simworld-api.md
    - 04-api-reference/uav-api.md
  - 故障排除:
    - 05-troubleshooting/emergency-procedures.md
    - 05-troubleshooting/auto-recovery.md
    - 05-troubleshooting/performance-benchmarks.md
  - 培訓材料:
    - 06-training/basic-training.md
    - 06-training/advanced-administration.md
    - 06-training/tactical-scenarios.md
  - 運維手冊:
    - 07-operations/system-monitoring.md
    - 07-operations/daily-maintenance.md
    - 07-operations/backup-recovery.md
  - 安全指南:
    - 08-security/security-architecture.md
    - 08-security/access-control.md
    - 08-security/incident-response.md
  - 現場手冊:
    - 09-field-manual/emergency-startup.md
    - 09-field-manual/field-deployment.md
    - 09-field-manual/tactical-operations.md
  - 快速參考:
    - 10-reference/command-reference.md
    - 10-reference/operation-checklist.md
    - 10-reference/combat-checklist.md

plugins:
  - search
  - mermaid2

markdown_extensions:
  - admonition
  - codehilite
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.tabbed
  - pymdownx.details
  - pymdownx.emoji:
      emoji_index: !!python/name:materialx.emoji.twemoji
      emoji_generator: !!python/name:materialx.emoji.to_svg
  - toc:
      permalink: true

extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/ntn-stack
    - icon: fontawesome/solid/envelope
      link: mailto:docs@ntn-stack.mil

copyright: Copyright &copy; 2024 NTN Stack 技術文檔組
EOF

    success "MkDocs配置已生成"
}

# 創建缺失的文檔文件
create_missing_docs() {
    log "檢查並創建缺失的文檔..."
    
    # 定義所有需要的文檔文件
    local required_docs=(
        "01-architecture/technical-architecture.md"
        "01-architecture/tactical-overview.md"
        "02-installation/hardware-requirements.md"
        "02-installation/production-deployment.md"
        "02-installation/rapid-deployment.md"
        "03-user-guides/README.md"
        "03-user-guides/user-management.md"
        "03-user-guides/communication-setup.md"
        "03-user-guides/slice-management.md"
        "04-api-reference/netstack-api.md"
        "04-api-reference/simworld-api.md"
        "04-api-reference/uav-api.md"
        "05-troubleshooting/auto-recovery.md"
        "05-troubleshooting/performance-benchmarks.md"
        "06-training/advanced-administration.md"
        "06-training/tactical-scenarios.md"
        "07-operations/system-monitoring.md"
        "07-operations/daily-maintenance.md"
        "07-operations/backup-recovery.md"
        "08-security/security-architecture.md"
        "08-security/access-control.md"
        "08-security/incident-response.md"
        "09-field-manual/field-deployment.md"
        "09-field-manual/tactical-operations.md"
        "10-reference/command-reference.md"
        "10-reference/operation-checklist.md"
        "10-reference/combat-checklist.md"
    )
    
    for doc in "${required_docs[@]}"; do
        local doc_path="$DOCS_DIR/$doc"
        local doc_dir=$(dirname "$doc_path")
        
        # 創建目錄
        mkdir -p "$doc_dir"
        
        # 如果文件不存在，創建佔位符
        if [ ! -f "$doc_path" ]; then
            local title=$(basename "$doc" .md | sed 's/-/ /g' | sed 's/\b\w/\u&/g')
            cat > "$doc_path" << EOF
# $title

## 📖 文檔資訊
- **版本**: v1.0.0
- **最後更新**: $(date +"%Y-%m-%d")
- **狀態**: 🚧 建置中

## 📝 概述

此文檔正在建置中，請稍後查看更新內容。

---

**維護資訊**:
- 文檔負責人: 待指定
- 審核週期: 待定
- 下次更新: 待定
EOF
            warning "已創建佔位符文檔: $doc"
        fi
    done
    
    success "文檔文件檢查完成"
}

# 建置HTML文檔
build_html_docs() {
    log "建置HTML文檔..."
    
    # 啟動虛擬環境
    source "$PROJECT_ROOT/docs-venv/bin/activate"
    
    cd "$PROJECT_ROOT"
    
    # 建置文檔
    mkdocs build --clean --site-dir "$BUILD_DIR/html"
    
    success "HTML文檔建置完成: $BUILD_DIR/html"
}

# 生成PDF文檔
generate_pdf_docs() {
    log "生成PDF文檔..."
    
    local pdf_dir="$BUILD_DIR/pdf"
    mkdir -p "$pdf_dir"
    
    # 為每個主要章節生成PDF
    local sections=(
        "01-architecture:系統架構"
        "02-installation:安裝部署"
        "03-user-guides:用戶指南"
        "04-api-reference:API參考"
        "05-troubleshooting:故障排除"
        "06-training:培訓材料"
        "07-operations:運維手冊"
        "08-security:安全指南"
        "09-field-manual:現場手冊"
        "10-reference:快速參考"
    )
    
    for section in "${sections[@]}"; do
        local dir_name="${section%%:*}"
        local title="${section##*:}"
        local section_dir="$DOCS_DIR/$dir_name"
        
        if [ -d "$section_dir" ]; then
            log "生成 $title PDF..."
            
            # 合併該章節的所有Markdown文件
            local combined_md="$BUILD_DIR/temp_${dir_name}.md"
            echo "# $title" > "$combined_md"
            echo "" >> "$combined_md"
            
            find "$section_dir" -name "*.md" -type f | sort | while read md_file; do
                echo "" >> "$combined_md"
                cat "$md_file" >> "$combined_md"
                echo "" >> "$combined_md"
            done
            
            # 轉換為PDF
            pandoc "$combined_md" -o "$pdf_dir/${dir_name}.pdf" \
                --pdf-engine=xelatex \
                --variable mainfont="Noto Sans CJK TC" \
                --variable geometry:margin=2cm \
                --toc \
                --number-sections || warning "PDF生成失敗: $title"
                
            rm -f "$combined_md"
        fi
    done
    
    success "PDF文檔生成完成: $pdf_dir"
}

# 生成統計報告
generate_stats() {
    log "生成文檔統計報告..."
    
    local stats_file="$BUILD_DIR/documentation_stats.txt"
    
    cat > "$stats_file" << EOF
# NTN Stack 文檔統計報告
生成時間: $(date)
建置版本: $TIMESTAMP

## 文檔結構統計
EOF

    echo "總文檔數量: $(find "$DOCS_DIR" -name "*.md" -type f | wc -l)" >> "$stats_file"
    echo "總行數: $(find "$DOCS_DIR" -name "*.md" -type f -exec wc -l {} + | tail -1 | awk '{print $1}')" >> "$stats_file"
    echo "總字數: $(find "$DOCS_DIR" -name "*.md" -type f -exec wc -w {} + | tail -1 | awk '{print $1}')" >> "$stats_file"
    
    echo "" >> "$stats_file"
    echo "## 各章節文檔數量" >> "$stats_file"
    
    for dir in "$DOCS_DIR"/*; do
        if [ -d "$dir" ]; then
            local dir_name=$(basename "$dir")
            local count=$(find "$dir" -name "*.md" -type f | wc -l)
            echo "$dir_name: $count 個文檔" >> "$stats_file"
        fi
    done
    
    echo "" >> "$stats_file"
    echo "## 建置產出" >> "$stats_file"
    echo "HTML文檔: $BUILD_DIR/html/" >> "$stats_file"
    echo "PDF文檔: $BUILD_DIR/pdf/" >> "$stats_file"
    
    success "統計報告已生成: $stats_file"
}

# 創建部署包
create_deployment_package() {
    log "創建部署包..."
    
    local package_dir="$BUILD_DIR/deployment"
    local package_name="ntn-stack-docs-${TIMESTAMP}.tar.gz"
    
    mkdir -p "$package_dir"
    
    # 複製HTML文檔
    cp -r "$BUILD_DIR/html" "$package_dir/"
    
    # 複製PDF文檔
    if [ -d "$BUILD_DIR/pdf" ]; then
        cp -r "$BUILD_DIR/pdf" "$package_dir/"
    fi
    
    # 複製統計報告
    if [ -f "$BUILD_DIR/documentation_stats.txt" ]; then
        cp "$BUILD_DIR/documentation_stats.txt" "$package_dir/"
    fi
    
    # 創建部署說明
    cat > "$package_dir/DEPLOYMENT.md" << EOF
# NTN Stack 文檔部署說明

## 部署日期
$(date)

## 文檔版本
$TIMESTAMP

## 部署方式

### 1. 本地部署
\`\`\`bash
# 解壓縮
tar -xzf $package_name

# 啟動簡單HTTP服務器
cd ntn-stack-docs-$TIMESTAMP/html
python3 -m http.server 8000
\`\`\`

### 2. Nginx部署
\`\`\`bash
# 複製到web目錄
sudo cp -r html/* /var/www/ntn-stack-docs/

# 配置Nginx虛擬主機
# (參考項目內的nginx配置範例)
\`\`\`

### 3. Docker部署
\`\`\`bash
# 使用官方nginx鏡像
docker run -d -p 8080:80 \\
  -v \$(pwd)/html:/usr/share/nginx/html:ro \\
  --name ntn-stack-docs \\
  nginx:alpine
\`\`\`

## 文檔結構
- html/: 完整的HTML文檔網站
- pdf/: 各章節PDF文檔
- documentation_stats.txt: 文檔統計資訊

## 技術支援
- 文檔問題: docs@ntn-stack.mil
- 技術支援: tech-support@ntn-stack.mil
EOF

    # 創建壓縮包
    cd "$BUILD_DIR"
    tar -czf "$package_name" -C deployment .
    
    success "部署包已創建: $BUILD_DIR/$package_name"
}

# 清理建置環境
cleanup() {
    log "清理建置環境..."
    
    # 清理臨時文件
    rm -f "$PROJECT_ROOT"/temp_*.md
    
    success "清理完成"
}

# 主函數
main() {
    log "開始建置 NTN Stack 文檔系統..."
    
    # 創建建置目錄
    mkdir -p "$BUILD_DIR"
    
    # 執行建置步驟
    check_dependencies
    setup_python_env
    create_missing_docs
    generate_mkdocs_config
    build_html_docs
    
    # 可選的PDF生成 (需要額外依賴)
    if command -v pandoc &> /dev/null && command -v xelatex &> /dev/null; then
        generate_pdf_docs
    else
        warning "跳過PDF生成 (缺少 pandoc 或 xelatex)"
    fi
    
    generate_stats
    create_deployment_package
    cleanup
    
    echo ""
    success "========================="
    success "文檔建置完成！"
    success "========================="
    echo ""
    log "建置產出:"
    echo "  📁 HTML文檔: $BUILD_DIR/html/"
    echo "  📁 PDF文檔: $BUILD_DIR/pdf/"
    echo "  📦 部署包: $BUILD_DIR/ntn-stack-docs-${TIMESTAMP}.tar.gz"
    echo ""
    log "預覽文檔:"
    echo "  cd $BUILD_DIR/html && python3 -m http.server 8000"
    echo "  然後訪問: http://localhost:8000"
    echo ""
}

# 錯誤處理
trap cleanup EXIT

# 執行主函數
main "$@" 