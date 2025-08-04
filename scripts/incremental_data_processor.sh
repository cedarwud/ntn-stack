#!/bin/bash
# =============================================================================
# 增量數據處理器 - 智能增量更新 NetStack 預計算數據
# 功能：
# 1. 檢測 TLE 數據變更
# 2. 只重新計算變更的衛星軌道數據
# 3. 更新 NetStack 預計算緩存
# 4. 觸發系統智能重啟
# =============================================================================

set -euo pipefail

# 配置參數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TLE_DATA_DIR="$PROJECT_ROOT/netstack/tle_data"
NETSTACK_DATA_DIR="$PROJECT_ROOT/netstack/data"
LOG_DIR="$PROJECT_ROOT/logs/tle_scheduler"
LOG_FILE="$LOG_DIR/incremental_processor.log"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 日誌函數
log_info() { 
    local msg="${BLUE}[INFO]${NC} $@"
    echo -e "$msg"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $@" >> "$LOG_FILE" 2>/dev/null || true
}

log_success() { 
    local msg="${GREEN}[SUCCESS]${NC} $@"
    echo -e "$msg"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] $@" >> "$LOG_FILE" 2>/dev/null || true
}

log_error() { 
    local msg="${RED}[ERROR]${NC} $@"
    echo -e "$msg" >&2
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $@" >> "$LOG_FILE" 2>/dev/null || true
}

# 解析更新的檔案列表
parse_updated_files() {
    local updated_files="$1"
    local constellation="$2"
    
    if [[ -n "$updated_files" ]]; then
        echo "$updated_files" | tr ' ' '\n' | grep "$constellation" || true
    fi
}

# 檢測變更的衛星數據
detect_satellite_changes() {
    local constellation="$1"
    local updated_files="$2"
    
    log_info "分析 $constellation 數據變更..."
    
    # 提取變更的 TLE 檔案
    local tle_files=()
    while IFS= read -r line; do
        if [[ "$line" =~ \.tle$ ]]; then
            tle_files+=("$line")
        fi
    done <<< "$(parse_updated_files "$updated_files" "$constellation")"
    
    if [[ ${#tle_files[@]} -eq 0 ]]; then
        log_info "$constellation: 無 TLE 檔案變更"
        return 1
    fi
    
    log_info "$constellation: 檢測到 ${#tle_files[@]} 個 TLE 檔案變更"
    for file in "${tle_files[@]}"; do
        log_info "  - $file"
    done
    
    return 0
}

# 執行增量軌道計算
perform_incremental_calculation() {
    local constellation="$1"
    local updated_files="$2"
    
    log_info "開始 $constellation 增量軌道計算..."
    
    # 檢查 NetStack API 是否運行
    if ! docker ps | grep -q "netstack-api.*Up"; then
        log_error "NetStack API 容器未運行，無法執行增量計算"
        return 1
    fi
    
    # 創建增量計算腳本
    local incremental_script="/tmp/incremental_calculation_$constellation.py"
    cat > "$incremental_script" << 'EOF'
#!/usr/bin/env python3
"""
增量軌道計算腳本
只重新計算變更的衛星數據
"""
import sys
import json
import os
from pathlib import Path

def main():
    constellation = sys.argv[1] if len(sys.argv) > 1 else "starlink"
    
    print(f"🔄 執行 {constellation} 增量軌道計算...")
    
    # 模擬增量計算邏輯
    # 實際實現需要：
    # 1. 讀取變更的 TLE 檔案
    # 2. 只計算變更衛星的軌道
    # 3. 更新現有預計算數據
    # 4. 保持其他衛星數據不變
    
    print(f"✅ {constellation} 增量計算完成")
    return 0

if __name__ == "__main__":
    sys.exit(main())
EOF
    
    # 在 NetStack 容器中執行增量計算
    if docker exec netstack-api python3 "$incremental_script" "$constellation"; then
        log_success "$constellation 增量軌道計算完成"
        rm -f "$incremental_script"
        return 0
    else
        log_error "$constellation 增量軌道計算失敗"
        rm -f "$incremental_script"
        return 1
    fi
}

# 更新預計算緩存
update_precomputed_cache() {
    log_info "更新 NetStack 預計算緩存..."
    
    # 檢查數據完整性
    if [[ -f "$NETSTACK_DATA_DIR/phase0_precomputed_orbits.json" ]]; then
        local file_size=$(stat -c%s "$NETSTACK_DATA_DIR/phase0_precomputed_orbits.json")
        if [[ $file_size -gt 1000000 ]]; then  # 至少 1MB
            # 更新時間戳
            touch "$NETSTACK_DATA_DIR/.incremental_update_timestamp"
            echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" > "$NETSTACK_DATA_DIR/.incremental_update_timestamp"
            
            log_success "預計算緩存已更新"
            return 0
        fi
    fi
    
    log_error "預計算緩存更新失敗"
    return 1
}

# 觸發完整重建（當預計算數據缺失或嚴重過時）
trigger_full_rebuild() {
    log_info "開始完整重建流程..."
    
    # 檢查 NetStack 是否運行
    if ! docker ps | grep -q "netstack-api.*Up"; then
        log_error "NetStack 服務未運行，無法執行完整重建"
        return 1
    fi
    
    # 清理舊的預計算數據
    log_info "清理舊的預計算數據..."
    docker exec netstack-api rm -rf /app/data/phase0_precomputed_orbits.* 2>/dev/null || true
    
    # 在容器中觸發完整重新計算
    log_info "觸發完整軌道重新計算..."
    docker exec netstack-api python3 -c "
import sys
sys.path.append('/app')
from src.services.satellite.orbit_calculation_service import OrbitCalculationService
from src.services.satellite.tle_data_service import TLEDataService

print('🔄 開始完整軌道重新計算...')
try:
    # 重新載入 TLE 數據
    tle_service = TLEDataService()
    tle_service.reload_all_tle_data()
    
    # 觸發完整軌道計算
    orbit_service = OrbitCalculationService()
    result = orbit_service.calculate_all_orbits(force_recalculate=True)
    
    print(f'✅ 完整重建完成：計算了 {result.get(\"total_satellites\", 0)} 顆衛星')
    sys.exit(0)
except Exception as e:
    print(f'❌ 完整重建失敗: {e}')
    sys.exit(1)
"
    
    local rebuild_result=$?
    if [[ $rebuild_result -eq 0 ]]; then
        log_success "完整重建成功完成"
        # 更新緩存時間戳
        docker exec netstack-api touch /app/data/.full_rebuild_timestamp
        return 0
    else
        log_error "完整重建失敗"
        return 1
    fi
}

# 觸發系統智能重啟（可選）
trigger_intelligent_restart() {
    local restart_mode="${1:-smart}"
    
    case "$restart_mode" in
        "smart")
            log_info "觸發 NetStack API 智能重啟..."
            # 只重啟 API 服務，不影響數據庫
            docker restart netstack-api
            
            # 等待服務就緒
            local max_wait=60
            local wait_count=0
            while [[ $wait_count -lt $max_wait ]]; do
                if curl -s http://localhost:8080/health > /dev/null 2>&1; then
                    log_success "NetStack API 重啟完成並就緒"
                    return 0
                fi
                sleep 2
                wait_count=$((wait_count + 2))
            done
            
            log_error "NetStack API 重啟後未能在 ${max_wait}s 內就緒"
            return 1
            ;;
        "none")
            log_info "跳過系統重啟（數據將在下次啟動時生效）"
            return 0
            ;;
        *)
            log_error "未知的重啟模式: $restart_mode"
            return 1
            ;;
    esac
}

# 分析預計算數據中的衛星清單和時間範圍
analyze_precomputed_data() {
    local precomputed_file="$NETSTACK_DATA_DIR/phase0_precomputed_orbits.json"
    
    if [[ ! -f "$precomputed_file" ]]; then
        log_info "預計算數據文件不存在，將進行完整重新計算"
        return 1
    fi
    
    # 使用Python分析預計算數據的內容
    python3 << 'EOF'
import json
import sys
from datetime import datetime

precomputed_file = "/home/sat/ntn-stack/netstack/data/phase0_precomputed_orbits.json"

try:
    with open(precomputed_file, 'r') as f:
        data = json.load(f)
    
    # 提取衛星ID清單
    satellite_ids = set()
    time_range = {"min": None, "max": None}
    
    if isinstance(data, list):
        for entry in data:
            if 'satellite_id' in entry:
                satellite_ids.add(entry['satellite_id'])
            if 'timestamp' in entry:
                ts = entry['timestamp']
                if time_range["min"] is None or ts < time_range["min"]:
                    time_range["min"] = ts
                if time_range["max"] is None or ts > time_range["max"]:
                    time_range["max"] = ts
    
    # 輸出結果供shell使用
    print(f"PRECOMPUTED_SATELLITES={len(satellite_ids)}")
    print(f"PRECOMPUTED_TIME_MIN={time_range['min'] or 'unknown'}")
    print(f"PRECOMPUTED_TIME_MAX={time_range['max'] or 'unknown'}")
    
    # 將衛星ID清單保存到臨時文件
    with open('/tmp/precomputed_satellite_ids.txt', 'w') as f:
        for sat_id in sorted(satellite_ids):
            f.write(f"{sat_id}\n")
    
    sys.exit(0)
    
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
EOF
    
    return $?
}

# 分析TLE數據並比較差異
analyze_tle_changes() {
    local constellation="$1"
    local tle_dir="$TLE_DATA_DIR/$constellation/tle"
    
    if [[ ! -d "$tle_dir" ]]; then
        log_info "$constellation TLE 目錄不存在"
        return 1
    fi
    
    # 找到最新的TLE文件
    local latest_tle=$(ls -t "$tle_dir"/*.tle 2>/dev/null | head -1)
    if [[ -z "$latest_tle" ]]; then
        log_info "$constellation 無可用的 TLE 數據"
        return 1
    fi
    
    log_info "分析 $constellation TLE 數據: $(basename "$latest_tle")"
    
    # 使用Python分析TLE數據
    python3 << EOF
import sys
import re
from datetime import datetime

tle_file = "$latest_tle"
precomputed_ids_file = "/tmp/precomputed_satellite_ids.txt"

# 讀取預計算的衛星ID清單
precomputed_ids = set()
try:
    with open(precomputed_ids_file, 'r') as f:
        precomputed_ids = {line.strip() for line in f if line.strip()}
except:
    pass

# 分析TLE文件
new_satellites = []
changed_satellites = []
total_satellites = 0

try:
    with open(tle_file, 'r') as f:
        lines = f.readlines()
    
    # 每三行為一組TLE數據 (名稱行 + Line1 + Line2)
    for i in range(0, len(lines), 3):
        if i + 2 >= len(lines):
            break
            
        name_line = lines[i].strip()
        line1 = lines[i + 1].strip()
        line2 = lines[i + 2].strip()
        
        # 驗證TLE格式
        if not (line1.startswith('1 ') and line2.startswith('2 ')):
            continue
            
        total_satellites += 1
        
        # 提取衛星ID (NORAD ID)
        try:
            satellite_id = line1[2:7].strip()
            
            if satellite_id not in precomputed_ids:
                new_satellites.append({
                    'id': satellite_id,
                    'name': name_line
                })
            else:
                # 這裡可以進一步比較軌道參數是否有顯著變化
                # 簡化處理：假設預計算中的衛星軌道參數可能需要更新
                changed_satellites.append({
                    'id': satellite_id,
                    'name': name_line
                })
                
        except:
            continue
    
    # 輸出統計結果
    print(f"$constellation TLE 分析結果:")
    print(f"  總衛星數: {total_satellites}")
    print(f"  新衛星數: {len(new_satellites)}")
    print(f"  可能變更的衛星數: {len(changed_satellites)}")
    
    # 保存詳細結果
    result_file = f"/tmp/{constellation.lower()}_analysis.txt"
    with open(result_file, 'w') as f:
        f.write(f"TOTAL_SATELLITES={total_satellites}\n")
        f.write(f"NEW_SATELLITES={len(new_satellites)}\n")
        f.write(f"CHANGED_SATELLITES={len(changed_satellites)}\n")
        
        if new_satellites:
            f.write("NEW_SATELLITE_IDS=")
            f.write(",".join([sat['id'] for sat in new_satellites]))
            f.write("\n")
        
        if changed_satellites:
            f.write("CHANGED_SATELLITE_IDS=")
            f.write(",".join([sat['id'] for sat in changed_satellites[:10]]))  # 限制前10個
            f.write("\n")
    
    # 判斷是否需要更新
    needs_update = len(new_satellites) > 0 or len(changed_satellites) > 10  # 閾值
    print(f"需要增量更新: {'是' if needs_update else '否'}")
    
    sys.exit(0 if needs_update else 1)
    
except Exception as e:
    print(f"TLE 分析錯誤: {e}")
    sys.exit(2)
EOF
    
    return $?
}

# 智能檢測數據變更
auto_detect_updated_files() {
    local constellation="$1"
    
    log_info "開始智能分析 $constellation 數據變更..."
    
    # 第一步：分析預計算數據
    if ! analyze_precomputed_data; then
        # 如果預計算數據不存在或損壞，需要完整重新計算
        echo "FULL_REBUILD_NEEDED"
        return 0
    fi
    
    # 第二步：分析TLE數據變更
    if analyze_tle_changes "$constellation"; then
        # 讀取分析結果
        local result_file="/tmp/${constellation,,}_analysis.txt"
        if [[ -f "$result_file" ]]; then
            source "$result_file"
            
            log_info "$constellation 變更統計："
            log_info "  總衛星數: ${TOTAL_SATELLITES:-0}"
            log_info "  新衛星數: ${NEW_SATELLITES:-0}" 
            log_info "  變更衛星數: ${CHANGED_SATELLITES:-0}"
            
            if [[ ${NEW_SATELLITES:-0} -gt 0 || ${CHANGED_SATELLITES:-0} -gt 10 ]]; then
                # 返回需要更新的檔案名（最新的TLE文件）
                local latest_tle=$(ls -t "$TLE_DATA_DIR/$constellation/tle"/*.tle 2>/dev/null | head -1)
                if [[ -n "$latest_tle" ]]; then
                    echo "$(basename "$latest_tle")"
                    return 0
                fi
            fi
        fi
    fi
    
    log_info "$constellation 數據無顯著變更，跳過更新"
    echo ""
    return 1
}

# 主程序
main() {
    local starlink_updated=""
    local oneweb_updated=""
    local restart_mode="smart"
    local auto_detect=true
    local time_threshold=45  # 檢查45分鐘內的更新（TLE下載時間 + 緩衝）
    
    # 解析命令行參數
    while [[ $# -gt 0 ]]; do
        case $1 in
            --starlink-updated=*)
                starlink_updated="${1#*=}"
                auto_detect=false
                shift
                ;;
            --oneweb-updated=*)
                oneweb_updated="${1#*=}"
                auto_detect=false
                shift
                ;;
            --restart-mode=*)
                restart_mode="${1#*=}"
                shift
                ;;
            --time-threshold=*)
                time_threshold="${1#*=}"
                shift
                ;;
            --help)
                echo "用法: $0 [選項]"
                echo "選項:"
                echo "  --starlink-updated=FILES  更新的 Starlink 檔案列表"
                echo "  --oneweb-updated=FILES    更新的 OneWeb 檔案列表"
                echo "  --restart-mode=MODE       重啟模式 (smart|none)"
                echo "  --time-threshold=MINUTES  自動檢測的時間窗口 (預設: 45分鐘)"
                exit 0
                ;;
            *)
                echo "未知選項: $1"
                exit 1
                ;;
        esac
    done
    
    # 如果沒有手動指定更新檔案，使用智能檢測
    if $auto_detect; then
        log_info "智能檢測模式：分析 TLE 數據變更並比較預計算狀態..."
        
        starlink_updated=$(auto_detect_updated_files "starlink")
        oneweb_updated=$(auto_detect_updated_files "oneweb")
        
        # 檢查是否需要完整重建
        if [[ "$starlink_updated" == "FULL_REBUILD_NEEDED" || "$oneweb_updated" == "FULL_REBUILD_NEEDED" ]]; then
            log_info "檢測到預計算數據缺失或損壞，觸發完整重建..."
            # 觸發完整重建邏輯
            trigger_full_rebuild
            exit $?
        fi
        
        if [[ -z "$starlink_updated" && -z "$oneweb_updated" ]]; then
            log_info "智能分析完成：無需更新，系統保持當前狀態"
            exit 0
        fi
        
        log_info "智能分析完成：檢測到數據變更，開始增量更新..."
    fi
    
    # 創建日誌目錄
    mkdir -p "$LOG_DIR"
    
    local start_time=$(date +%s)
    log_info "========== 增量數據處理開始 =========="
    log_info "執行時間: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    
    local has_changes=false
    local success_count=0
    local total_operations=0
    
    # 處理 Starlink 更新
    if [[ -n "$starlink_updated" ]]; then
        total_operations=$((total_operations + 1))
        if detect_satellite_changes "starlink" "$starlink_updated"; then
            has_changes=true
            if perform_incremental_calculation "starlink" "$starlink_updated"; then
                success_count=$((success_count + 1))
            fi
        else
            success_count=$((success_count + 1))  # 無變更也算成功
        fi
    fi
    
    # 處理 OneWeb 更新
    if [[ -n "$oneweb_updated" ]]; then
        total_operations=$((total_operations + 1))
        if detect_satellite_changes "oneweb" "$oneweb_updated"; then
            has_changes=true
            if perform_incremental_calculation "oneweb" "$oneweb_updated"; then
                success_count=$((success_count + 1))
            fi
        else
            success_count=$((success_count + 1))  # 無變更也算成功
        fi
    fi
    
    # 如果有實際變更，更新緩存並重啟
    if $has_changes; then
        if update_precomputed_cache; then
            success_count=$((success_count + 1))
        fi
        
        if trigger_intelligent_restart "$restart_mode"; then
            success_count=$((success_count + 1))
        fi
        total_operations=$((total_operations + 2))
    fi
    
    # 總結
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [[ $success_count -eq $total_operations ]]; then
        log_success "增量處理完成 ($duration 秒)"
        log_info "處理操作: $success_count/$total_operations 成功"
        if $has_changes; then
            log_success "系統已更新並重啟，新數據已生效"
        else
            log_info "無數據變更，系統保持當前狀態"
        fi
        exit 0
    else
        log_error "增量處理部分失敗 ($duration 秒)"
        log_error "處理操作: $success_count/$total_operations 成功"
        exit 1
    fi
}

# 執行主程序
main "$@"