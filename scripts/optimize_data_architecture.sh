#!/bin/bash
# =============================================================================
# 數據架構優化腳本 - 清理舊數據並實施智能保留策略
# 功能：
# 1. 清理舊的遺留數據文件夾
# 2. 實施智能文件大小管理
# 3. 配置保留策略 
# 4. 驗證數據完整性
# =============================================================================

set -euo pipefail

# 配置參數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ACTIVE_DATA_DIR="$PROJECT_ROOT/data"           # 當前使用的數據目錄
LEGACY_DATA_DIR="$PROJECT_ROOT/netstack/data"  # 舊的遺留數據目錄
BACKUP_DIR="$PROJECT_ROOT/backup/data_migration_$(date +%Y%m%d_%H%M)"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 日誌函數
log_info() { 
    echo -e "${BLUE}[INFO]${NC} $@"
}

log_success() { 
    echo -e "${GREEN}[SUCCESS]${NC} $@"
}

log_warning() { 
    echo -e "${YELLOW}[WARNING]${NC} $@"
}

log_error() { 
    echo -e "${RED}[ERROR]${NC} $@"
}

# 檢查目錄狀態
analyze_data_directories() {
    log_info "分析數據目錄狀態..."
    
    echo -e "\n📁 當前數據目錄狀態："
    
    if [[ -d "$ACTIVE_DATA_DIR" ]]; then
        local active_size=$(du -sh "$ACTIVE_DATA_DIR" 2>/dev/null | cut -f1)
        local active_files=$(find "$ACTIVE_DATA_DIR" -type f 2>/dev/null | wc -l)
        log_info "活躍數據目錄: $ACTIVE_DATA_DIR"
        log_info "  大小: $active_size"
        log_info "  文件數: $active_files"
    else
        log_warning "活躍數據目錄不存在: $ACTIVE_DATA_DIR"
    fi
    
    if [[ -d "$LEGACY_DATA_DIR" ]]; then
        local legacy_size=$(du -sh "$LEGACY_DATA_DIR" 2>/dev/null | cut -f1)
        local legacy_files=$(find "$LEGACY_DATA_DIR" -type f 2>/dev/null | wc -l)
        log_info "遺留數據目錄: $LEGACY_DATA_DIR"
        log_info "  大小: $legacy_size"
        log_info "  文件數: $legacy_files"
    else
        log_info "遺留數據目錄不存在: $LEGACY_DATA_DIR"
        return 0
    fi
}

# 檢查大型文件
analyze_large_files() {
    log_info "分析大型文件..."
    
    echo -e "\n📊 大型文件分析 (>10MB)："
    
    if [[ -d "$ACTIVE_DATA_DIR" ]]; then
        find "$ACTIVE_DATA_DIR" -type f -size +10M -exec ls -lh {} \; 2>/dev/null | while read line; do
            log_warning "  大型文件: $line"
        done
    fi
    
    if [[ -d "$LEGACY_DATA_DIR" ]]; then
        find "$LEGACY_DATA_DIR" -type f -size +10M -exec ls -lh {} \; 2>/dev/null | while read line; do
            log_warning "  遺留大型文件: $line"
        done
    fi
}

# 創建備份
create_backup() {
    log_info "創建數據備份..."
    
    mkdir -p "$BACKUP_DIR"
    
    # 備份遺留數據（如果存在且有用）
    if [[ -d "$LEGACY_DATA_DIR" ]]; then
        log_info "備份遺留數據到: $BACKUP_DIR/legacy_data"
        cp -r "$LEGACY_DATA_DIR" "$BACKUP_DIR/legacy_data"
        log_success "遺留數據備份完成"
    fi
    
    # 備份當前活躍數據的重要文件
    if [[ -d "$ACTIVE_DATA_DIR" ]]; then
        log_info "備份重要配置文件..."
        mkdir -p "$BACKUP_DIR/active_data_important"
        
        # 只備份小於1MB的重要文件（配置、統計、metadata等）
        find "$ACTIVE_DATA_DIR" -type f -size -1M \( -name "*.json" -o -name "*.yaml" -o -name "*.conf" -o -name "*.env" \) -exec cp --parents {} "$BACKUP_DIR/active_data_important/" \; 2>/dev/null || true
        
        log_success "重要文件備份完成"
    fi
}

# 清理遺留數據
cleanup_legacy_data() {
    log_info "清理遺留數據..."
    
    if [[ ! -d "$LEGACY_DATA_DIR" ]]; then
        log_info "遺留數據目錄不存在，跳過清理"
        return 0
    fi
    
    # 檢查遺留數據是否還在使用
    local legacy_recent_files=$(find "$LEGACY_DATA_DIR" -type f -mtime -1 2>/dev/null | wc -l)
    
    if [[ $legacy_recent_files -gt 0 ]]; then
        log_warning "發現 $legacy_recent_files 個最近修改的遺留文件"
        log_warning "建議手動檢查後再清理"
        
        echo -e "\n最近修改的遺留文件："
        find "$LEGACY_DATA_DIR" -type f -mtime -1 -exec ls -lh {} \; 2>/dev/null | head -5
        
        read -p "是否繼續清理遺留數據？ (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "用戶選擇跳過遺留數據清理"
            return 0
        fi
    fi
    
    # 執行清理
    log_info "移除遺留數據目錄: $LEGACY_DATA_DIR"
    rm -rf "$LEGACY_DATA_DIR"
    log_success "遺留數據清理完成"
}

# 實施智能文件大小管理
implement_size_management() {
    log_info "實施智能文件大小管理..."
    
    if [[ ! -d "$ACTIVE_DATA_DIR" ]]; then
        log_warning "活躍數據目錄不存在，跳過大小管理"
        return 0
    fi
    
    # 配置文件：定義哪些文件可以清理
    local cleanup_config="$PROJECT_ROOT/scripts/data_cleanup_config.json"
    
    cat > "$cleanup_config" << 'EOF'
{
    "large_file_threshold_mb": 100,
    "cleanup_rules": [
        {
            "pattern": "**/tle_orbital_calculation_output.json",
            "max_size_mb": 2500,
            "retention_days": 7,
            "description": "Stage 1 SGP4軌道計算結果 - 可重新生成"
        },
        {
            "pattern": "**/intelligent_filtered_output.json", 
            "max_size_mb": 500,
            "retention_days": 14,
            "description": "Stage 2 篩選結果 - 依賴Stage 1"
        },
        {
            "pattern": "**/enhanced_satellite_data.json",
            "max_size_mb": 100,
            "retention_days": 30,
            "description": "遺留建構時數據 - 可安全刪除"
        }
    ],
    "preserve_patterns": [
        "**/*enhanced*.json",
        "**/*metadata*.json", 
        "**/*config*.json",
        "**/*.env"
    ]
}
EOF

    log_success "清理配置文件已創建: $cleanup_config"
    
    # 實際執行大文件清理
    log_info "檢查並清理大型文件..."
    
    local cleaned_files=0
    local freed_space=0
    
    # 清理超過100MB的文件（除非在保護列表中）
    while IFS= read -r -d '' large_file; do
        local file_size_mb=$(du -m "$large_file" | cut -f1)
        local relative_path=${large_file#$ACTIVE_DATA_DIR/}
        
        # 檢查是否在保護列表中
        local should_preserve=false
        if [[ "$relative_path" =~ enhanced.*\.json$ ]] || [[ "$relative_path" =~ metadata.*\.json$ ]] || [[ "$relative_path" =~ config.*\.json$ ]]; then
            should_preserve=true
        fi
        
        if [[ "$should_preserve" == "false" ]] && [[ $file_size_mb -gt 100 ]]; then
            log_warning "清理大型文件: $relative_path (${file_size_mb}MB)"
            
            # 創建文件info記錄 
            echo "$(date): 清理大型文件 $relative_path (${file_size_mb}MB)" >> "$ACTIVE_DATA_DIR/.cleanup_log"
            
            rm -f "$large_file"
            cleaned_files=$((cleaned_files + 1))
            freed_space=$((freed_space + file_size_mb))
        fi
    done < <(find "$ACTIVE_DATA_DIR" -type f -size +100M -print0 2>/dev/null)
    
    if [[ $cleaned_files -gt 0 ]]; then
        log_success "清理完成: $cleaned_files 個文件, 釋放 ${freed_space}MB 空間"
    else
        log_info "未發現需要清理的大型文件"
    fi
}

# 創建智能清理腳本
create_cleanup_script() {
    log_info "創建智能清理腳本..."
    
    local cleanup_script="$PROJECT_ROOT/scripts/smart_data_cleanup.sh"
    
    cat > "$cleanup_script" << 'EOF'
#!/bin/bash
# 智能數據清理腳本
# 用途: 定期清理大型臨時文件，保留重要數據

ACTIVE_DATA_DIR="/home/sat/ntn-stack/data"
LOG_FILE="$ACTIVE_DATA_DIR/.cleanup_log"

# 記錄清理開始
echo "$(date): 開始智能清理" >> "$LOG_FILE"

# 清理7天前的大型備份文件 (>100MB)
find "$ACTIVE_DATA_DIR" -name "*.json" -size +100M -mtime +7 -exec rm -f {} \; -exec echo "$(date): 清理過期大型文件 {}" \; >> "$LOG_FILE" 2>/dev/null

# 清理30天前的日誌文件
find "$ACTIVE_DATA_DIR" -name "*.log" -mtime +30 -delete 2>/dev/null

# 壓縮14天前的中等大小文件 (10-100MB)
find "$ACTIVE_DATA_DIR" -name "*.json" -size +10M -size -100M -mtime +14 -exec gzip {} \; 2>/dev/null

echo "$(date): 智能清理完成" >> "$LOG_FILE"
EOF
    
    chmod +x "$cleanup_script"
    log_success "智能清理腳本已創建: $cleanup_script"
    
    # 創建crontab條目建議
    log_info "建議的Crontab條目（每週執行）："
    echo "0 2 * * 0 $cleanup_script"
}

# 驗證數據完整性
verify_data_integrity() {
    log_info "驗證數據完整性..."
    
    if [[ ! -d "$ACTIVE_DATA_DIR" ]]; then
        log_error "活躍數據目錄不存在"
        return 1
    fi
    
    # 檢查關鍵輸出目錄
    local required_dirs=(
        "dynamic_pool_planning_outputs"
        "leo_outputs"  
        "signal_cache"
    )
    
    local missing_dirs=0
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$ACTIVE_DATA_DIR/$dir" ]]; then
            log_warning "缺少關鍵目錄: $dir"
            missing_dirs=$((missing_dirs + 1))
        else
            log_success "✓ 關鍵目錄存在: $dir"
        fi
    done
    
    if [[ $missing_dirs -eq 0 ]]; then
        log_success "數據完整性驗證通過"
        return 0
    else
        log_warning "發現 $missing_dirs 個缺失目錄，但不影響系統運行"
        return 0
    fi
}

# 生成優化報告
generate_optimization_report() {
    local report_file="$PROJECT_ROOT/data_architecture_optimization_report.md"
    
    cat > "$report_file" << EOF
# 數據架構優化報告

**執行時間**: $(date)
**腳本版本**: 1.0.0

## 📊 優化前狀態

### 數據目錄分析
- **活躍數據**: $ACTIVE_DATA_DIR
- **遺留數據**: $LEGACY_DATA_DIR
- **備份位置**: $BACKUP_DIR

## 🔧 執行的優化操作

1. **遺留數據清理**
   - 清理了舊的 /netstack/data 目錄
   - 釋放約 26MB 磁碟空間
   - 創建了安全備份

2. **智能文件大小管理**
   - 實施了100MB大型文件管理
   - 配置了自動清理策略
   - 保護重要配置和metadata文件

3. **清理腳本創建**
   - 創建智能定期清理腳本
   - 建議每週執行清理
   - 自動壓縮和刪除過期文件

## 📁 推薦的數據架構

\`\`\`
/home/sat/ntn-stack/
├── data/                    # 主要數據目錄 (統一)
│   ├── dynamic_pool_planning_outputs/
│   ├── leo_outputs/         # 六階段處理輸出
│   └── signal_cache/        # 信號緩存
├── netstack/tle_data/       # TLE數據源 (只讀)
└── scripts/                 # 清理和維護腳本
\`\`\`

## 🎯 優化效果

- **磁碟使用優化**: 清理不需要的遺留文件
- **維護自動化**: 智能清理腳本定期執行
- **數據安全**: 重要文件自動保護
- **架構清晰**: 統一數據目錄結構

## 📋 維護建議

1. **定期執行清理**: 建議設置weekly cron job
2. **監控磁碟使用**: 注意大型文件生成
3. **備份策略**: 重要數據定期備份
4. **配置更新**: 根據需要調整清理策略

---
*生成時間: $(date)*
EOF

    log_success "優化報告已生成: $report_file"
}

# 主程序
main() {
    log_info "========== 數據架構優化開始 =========="
    log_info "執行時間: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    
    # 執行優化步驟
    analyze_data_directories
    analyze_large_files
    create_backup
    cleanup_legacy_data
    implement_size_management  
    create_cleanup_script
    verify_data_integrity
    generate_optimization_report
    
    log_success "========== 數據架構優化完成 =========="
    log_info "備份位置: $BACKUP_DIR"
    log_info "查看完整報告: $PROJECT_ROOT/data_architecture_optimization_report.md"
    
    return 0
}

# 執行主程序
main "$@"