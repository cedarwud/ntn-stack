#!/bin/bash

# NetStack NTN配置驗證測試腳本
# 驗證AMF、SMF、NSSF中的NTN特定配置是否正確加載和生效

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 測試設定
API_BASE_URL="http://localhost:8080"
CONFIG_DIR="./config"
TIMEOUT=30

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_test() {
    echo -e "${BLUE}[CONFIG-TEST]${NC} $1"
}

log_ntn() {
    echo -e "${PURPLE}[NTN]${NC} $1"
}

# 檢查配置文件是否存在
check_config_files() {
    log_test "檢查NTN配置文件"
    
    local config_files=(
        "$CONFIG_DIR/amf.yaml"
        "$CONFIG_DIR/smf.yaml"
        "$CONFIG_DIR/nssf.yaml"
    )
    
    for config_file in "${config_files[@]}"; do
        if [ -f "$config_file" ]; then
            log_info "  ✅ 配置文件存在: $(basename "$config_file")"
        else
            log_error "  ❌ 配置文件缺失: $(basename "$config_file")"
            return 1
        fi
    done
    
    return 0
}

# 驗證AMF的NTN計時器配置
validate_amf_ntn_timers() {
    log_test "驗證AMF NTN計時器配置"
    
    local amf_config="$CONFIG_DIR/amf.yaml"
    
    # 檢查關鍵NTN計時器
    local required_timers=(
        "t3502"
        "t3512" 
        "t3550"
        "t3560"
        "t3565"
        "t3346"
    )
    
    for timer in "${required_timers[@]}"; do
        if grep -q "$timer:" "$amf_config"; then
            local timer_value=$(grep -A1 "$timer:" "$amf_config" | grep "value:" | awk '{print $2}')
            log_info "  ✅ $timer: ${timer_value}秒"
            
            # 驗證計時器值是否適合NTN場景
            case $timer in
                "t3502")
                    if [ "$timer_value" -ge 1440 ]; then
                        log_info "    ✅ NTN優化: 值適合衛星軌道週期"
                    else
                        log_warning "    ⚠️  值可能不適合NTN場景"
                    fi
                    ;;
                "t3512")
                    if [ "$timer_value" -ge 1080 ]; then
                        log_info "    ✅ NTN優化: 值適合高延遲場景"
                    else
                        log_warning "    ⚠️  值可能不適合NTN場景"
                    fi
                    ;;
                "t3550"|"t3560"|"t3565")
                    if [ "$timer_value" -ge 10 ]; then
                        log_info "    ✅ NTN優化: 值適合衛星信令延遲"
                    else
                        log_warning "    ⚠️  值可能不適合NTN場景"
                    fi
                    ;;
            esac
        else
            log_error "  ❌ 缺少NTN計時器: $timer"
        fi
    done
    
    # 檢查衛星模式配置
    if grep -q "satellite_mode:" "$amf_config"; then
        log_info "  ✅ 衛星模式配置存在"
        
        # 檢查LEO軌道週期
        if grep -q "leo_orbit_period:" "$amf_config"; then
            local orbit_period=$(grep "leo_orbit_period:" "$amf_config" | awk '{print $2}')
            if [ "$orbit_period" -eq 6000 ]; then
                log_info "    ✅ LEO軌道週期配置正確: ${orbit_period}秒"
            else
                log_warning "    ⚠️  LEO軌道週期可能不正確: ${orbit_period}秒"
            fi
        fi
        
        # 檢查覆蓋預測
        if grep -q "coverage_prediction:" "$amf_config"; then
            log_info "    ✅ 覆蓋預測配置存在"
        else
            log_warning "    ⚠️  缺少覆蓋預測配置"
        fi
    else
        log_error "  ❌ 缺少衛星模式配置"
    fi
}

# 驗證SMF的NTN QoS配置
validate_smf_ntn_qos() {
    log_test "驗證SMF NTN QoS配置"
    
    local smf_config="$CONFIG_DIR/smf.yaml"
    
    # 檢查NTN配置區塊
    if grep -q "ntn_config:" "$smf_config"; then
        log_info "  ✅ NTN配置區塊存在"
        
        # 檢查延遲補償
        if grep -q "delay_compensation:" "$smf_config"; then
            log_info "    ✅ 延遲補償配置存在"
            
            local min_delay=$(grep "min_delay_ms:" "$smf_config" | awk '{print $2}')
            local max_delay=$(grep "max_delay_ms:" "$smf_config" | awk '{print $2}')
            
            if [ "$min_delay" -eq 20 ] && [ "$max_delay" -eq 50 ]; then
                log_info "      ✅ 衛星延遲範圍配置正確: ${min_delay}-${max_delay}ms"
            else
                log_warning "      ⚠️  衛星延遲範圍可能不正確"
            fi
        fi
        
        # 檢查QoS配置文件
        if grep -q "qos_profiles:" "$smf_config"; then
            log_info "    ✅ QoS配置文件存在"
            
            # 檢查三個切片的QoS配置
            local slice_types=("eMBB" "uRLLC" "mMTC")
            local slice_ssts=(1 2 3)
            
            for i in "${!slice_types[@]}"; do
                local slice_type="${slice_types[$i]}"
                local sst="${slice_ssts[$i]}"
                
                if grep -A10 "slice_sst: $sst" "$smf_config" | grep -q "packet_delay_budget:"; then
                    local delay_budget=$(grep -A10 "slice_sst: $sst" "$smf_config" | grep "packet_delay_budget:" | awk '{print $2}')
                    log_info "      ✅ $slice_type (SST=$sst) 延遲預算: ${delay_budget}ms"
                    
                    # 驗證延遲預算是否適合NTN
                    case $sst in
                        1) # eMBB
                            if [ "$delay_budget" -ge 300 ]; then
                                log_info "        ✅ NTN優化: eMBB延遲預算適合衛星場景"
                            fi
                            ;;
                        2) # uRLLC
                            if [ "$delay_budget" -le 10 ]; then
                                log_info "        ✅ uRLLC低延遲要求保持"
                            fi
                            ;;
                        3) # mMTC
                            if [ "$delay_budget" -ge 1000 ]; then
                                log_info "        ✅ mMTC寬鬆延遲適合IoT場景"
                            fi
                            ;;
                    esac
                fi
            done
        fi
        
        # 檢查會話管理超時
        if grep -q "session_management:" "$smf_config"; then
            log_info "    ✅ 會話管理優化存在"
            
            local pdu_timeout=$(grep "pdu_session_establishment_timeout:" "$smf_config" | awk '{print $2}')
            if [ "$pdu_timeout" -ge 60 ]; then
                log_info "      ✅ PDU會話建立超時適合NTN: ${pdu_timeout}秒"
            fi
        fi
        
        # 檢查流量整形
        if grep -q "traffic_shaping:" "$smf_config"; then
            log_info "    ✅ 流量整形配置存在"
            
            local uplink_limit=$(grep -A5 "uplink:" "$smf_config" | grep "rate_limit_mbps:" | awk '{print $2}')
            local downlink_limit=$(grep -A5 "downlink:" "$smf_config" | grep "rate_limit_mbps:" | awk '{print $2}')
            
            log_info "      ✅ 上行限制: ${uplink_limit}Mbps, 下行限制: ${downlink_limit}Mbps"
        fi
    else
        log_error "  ❌ 缺少NTN配置區塊"
        return 1
    fi
}

# 驗證NSSF的NTN切片選擇配置
validate_nssf_ntn_selection() {
    log_test "驗證NSSF NTN切片選擇配置"
    
    local nssf_config="$CONFIG_DIR/nssf.yaml"
    
    # 檢查NTN切片選擇區塊
    if grep -q "ntn_slice_selection:" "$nssf_config"; then
        log_info "  ✅ NTN切片選擇配置存在"
        
        # 檢查UAV類型映射
        if grep -q "uav_types:" "$nssf_config"; then
            log_info "    ✅ UAV類型切片映射存在"
            
            local uav_patterns=("UAV-Alpha-" "UAV-Beta-" "UAV-Gamma-")
            for pattern in "${uav_patterns[@]}"; do
                if grep -q "$pattern" "$nssf_config"; then
                    log_info "      ✅ $pattern 映射配置存在"
                fi
            done
        fi
        
        # 檢查衛星覆蓋策略
        if grep -q "satellite_coverage:" "$nssf_config"; then
            log_info "    ✅ 衛星覆蓋切片策略存在"
            
            local elevation_types=("high_elevation" "medium_elevation" "low_elevation")
            for elevation in "${elevation_types[@]}"; do
                if grep -q "$elevation:" "$nssf_config"; then
                    log_info "      ✅ $elevation 策略配置存在"
                fi
            done
        fi
        
        # 檢查任務優先級映射
        if grep -q "mission_priority:" "$nssf_config"; then
            log_info "    ✅ 任務優先級切片映射存在"
            
            local priority_levels=("critical" "high" "normal" "low")
            for priority in "${priority_levels[@]}"; do
                if grep -q "$priority:" "$nssf_config"; then
                    log_info "      ✅ $priority 優先級配置存在"
                fi
            done
        fi
        
        # 檢查動態重選
        if grep -q "dynamic_reselection:" "$nssf_config"; then
            log_info "    ✅ 動態切片重選配置存在"
            
            # 檢查觸發條件
            local triggers=("signal_strength_threshold" "latency_threshold" "packet_loss_threshold")
            for trigger in "${triggers[@]}"; do
                if grep -q "$trigger:" "$nssf_config"; then
                    local threshold=$(grep "$trigger:" "$nssf_config" | awk '{print $2}')
                    log_info "      ✅ $trigger: $threshold"
                fi
            done
        fi
        
        # 檢查切片連續性
        if grep -q "slice_continuity:" "$nssf_config"; then
            log_info "    ✅ 切片連續性配置存在"
        fi
        
        # 檢查負載均衡
        if grep -q "load_balancing:" "$nssf_config"; then
            log_info "    ✅ 負載均衡配置存在"
        fi
    else
        log_error "  ❌ 缺少NTN切片選擇配置"
        return 1
    fi
}

# 測試服務健康狀態
test_services_health() {
    log_test "測試服務健康狀態"
    
    # 檢查API健康狀態
    local health_response=$(curl -s -w "%{http_code}" "$API_BASE_URL/health" --max-time $TIMEOUT 2>/dev/null || echo "000")
    local http_code="${health_response: -3}"
    
    if [ "$http_code" == "200" ]; then
        log_info "  ✅ NetStack API健康狀態正常"
        
        # 解析健康檢查回應
        local body="${health_response%???}"
        if echo "$body" | grep -q "mongodb" && echo "$body" | grep -q "redis"; then
            log_info "    ✅ 數據庫連接正常"
        fi
    else
        log_warning "  ⚠️  NetStack API健康檢查異常，HTTP狀態碼: $http_code"
    fi
}

# 測試NTN特定API端點
test_ntn_api_endpoints() {
    log_test "測試NTN特定API端點"
    
    # 測試UERANSIM配置生成端點
    local config_endpoint="$API_BASE_URL/api/v1/ueransim/config/generate"
    local test_payload=$(cat <<EOF
{
  "scenario": "leo_satellite_pass",
  "satellite": {
    "id": "OneWeb-Test-001",
    "latitude": 35.6762,
    "longitude": 139.6503,
    "altitude": 1200,
    "elevation_angle": 45,
    "azimuth": 180
  },
  "uav": {
    "id": "UAV-Test-Alpha-01",
    "latitude": 35.6762,
    "longitude": 139.6503,
    "altitude": 100,
    "speed": 50,
    "heading": 90
  },
  "network_params": {
    "frequency": 2100,
    "bandwidth": 20,
    "tx_power": 23,
    "expected_sinr": 15
  }
}
EOF
)
    
    local response=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$test_payload" \
        "$config_endpoint" \
        --max-time $TIMEOUT 2>/dev/null || echo "000")
    
    local http_code="${response: -3}"
    
    if [ "$http_code" == "200" ]; then
        log_info "  ✅ UERANSIM動態配置端點工作正常"
        
        local body="${response%???}"
        if echo "$body" | grep -q "success.*true"; then
            log_info "    ✅ 配置生成成功"
        fi
        
        if echo "$body" | grep -q "leo_satellite_pass"; then
            log_info "    ✅ 場景類型正確識別"
        fi
    elif [ "$http_code" == "404" ]; then
        log_warning "  ⚠️  UERANSIM配置端點不存在 (需要啟動API服務)"
    else
        log_error "  ❌ UERANSIM配置端點異常，HTTP狀態碼: $http_code"
    fi
    
    # 測試場景類型端點
    local scenarios_response=$(curl -s -w "%{http_code}" "$API_BASE_URL/api/v1/ueransim/scenarios" --max-time $TIMEOUT 2>/dev/null || echo "000")
    local scenarios_code="${scenarios_response: -3}"
    
    if [ "$scenarios_code" == "200" ]; then
        log_info "  ✅ 支援場景查詢端點工作正常"
        
        local scenarios_body="${scenarios_response%???}"
        if echo "$scenarios_body" | grep -q "leo_satellite_pass\|uav_formation_flight\|handover_between_satellites"; then
            log_info "    ✅ NTN場景類型配置正確"
        fi
    elif [ "$scenarios_code" == "404" ]; then
        log_warning "  ⚠️  場景查詢端點不存在"
    fi
}

# 驗證配置語法
validate_yaml_syntax() {
    log_test "驗證YAML配置語法"
    
    local config_files=(
        "$CONFIG_DIR/amf.yaml"
        "$CONFIG_DIR/smf.yaml"  
        "$CONFIG_DIR/nssf.yaml"
    )
    
    local yaml_errors=0
    
    for config_file in "${config_files[@]}"; do
        local config_name=$(basename "$config_file" | sed 's/\.yaml//')
        
        # 檢查YAML語法
        if command -v yq &> /dev/null; then
            if yq . "$config_file" > /dev/null 2>&1; then
                log_info "  ✅ $config_name 語法正確"
            else
                log_error "  ❌ $config_name 語法錯誤"
                yaml_errors=$((yaml_errors + 1))
            fi
        else
            log_warning "  ⚠️  無法檢查YAML語法 (yq未安裝)"
        fi
    done
    
    return $yaml_errors
}

# 生成配置驗證報告
generate_validation_report() {
    log_test "生成NTN配置驗證報告"
    
    local report_file="/tmp/ntn_config_validation_report.txt"
    
    {
        echo "NetStack NTN配置驗證報告"
        echo "生成時間: $(date)"
        echo "=========================================="
        echo ""
        
        echo "配置文件檢查:"
        for config in amf.yaml smf.yaml nssf.yaml; do
            if [ -f "$CONFIG_DIR/$config" ]; then
                echo "  ✅ $config"
            else
                echo "  ❌ $config (缺失)"
            fi
        done
        echo ""
        
        echo "NTN特定配置項目:"
        echo "  AMF計時器優化: $(grep -c "t35[0-9][0-9]:" "$CONFIG_DIR/amf.yaml" 2>/dev/null || echo 0) 項"
        echo "  衛星模式配置: $(grep -c "satellite_mode:" "$CONFIG_DIR/amf.yaml" 2>/dev/null && echo "已啟用" || echo "未配置")"
        echo "  SMF QoS優化: $(grep -c "qos_profiles:" "$CONFIG_DIR/smf.yaml" 2>/dev/null && echo "已配置" || echo "未配置")"
        echo "  NSSF切片選擇: $(grep -c "ntn_slice_selection:" "$CONFIG_DIR/nssf.yaml" 2>/dev/null && echo "已配置" || echo "未配置")"
        echo ""
        
        echo "建議改進項目:"
        echo "  - 考慮添加更多衛星軌道預測參數"
        echo "  - 增加UAV移動模式的自適應配置"
        echo "  - 完善干擾避讓機制的配置"
        echo "  - 添加更詳細的NTN性能監控指標"
        
    } > "$report_file"
    
    log_info "驗證報告已生成: $report_file"
    cat "$report_file"
}

# 主測試函數
main() {
    log_ntn "🛰️  NetStack NTN配置驗證測試開始"
    echo "=========================================="
    
    local test_results=()
    
    # 測試1: 配置文件檢查
    log_test "測試1: 配置文件存在性檢查"
    if check_config_files; then
        test_results+=("配置文件檢查: PASS")
    else
        test_results+=("配置文件檢查: FAIL")
    fi
    
    echo ""
    # 測試2: YAML語法驗證
    log_test "測試2: YAML語法驗證"
    if validate_yaml_syntax; then
        test_results+=("YAML語法驗證: PASS")
    else
        test_results+=("YAML語法驗證: FAIL")
    fi
    
    echo ""
    # 測試3: AMF NTN配置驗證
    log_test "測試3: AMF NTN計時器配置驗證"
    if validate_amf_ntn_timers; then
        test_results+=("AMF NTN配置: PASS")
    else
        test_results+=("AMF NTN配置: FAIL")
    fi
    
    echo ""
    # 測試4: SMF NTN配置驗證
    log_test "測試4: SMF NTN QoS配置驗證"
    if validate_smf_ntn_qos; then
        test_results+=("SMF NTN配置: PASS")
    else
        test_results+=("SMF NTN配置: FAIL")
    fi
    
    echo ""
    # 測試5: NSSF NTN配置驗證
    log_test "測試5: NSSF NTN切片選擇配置驗證"
    if validate_nssf_ntn_selection; then
        test_results+=("NSSF NTN配置: PASS")
    else
        test_results+=("NSSF NTN配置: FAIL")
    fi
    
    echo ""
    # 測試6: 服務健康狀態
    log_test "測試6: 服務健康狀態檢查"
    if test_services_health; then
        test_results+=("服務健康狀態: PASS")
    else
        test_results+=("服務健康狀態: WARN")
    fi
    
    echo ""
    # 測試7: NTN API端點
    log_test "測試7: NTN特定API端點測試"
    if test_ntn_api_endpoints; then
        test_results+=("NTN API端點: PASS")
    else
        test_results+=("NTN API端點: WARN")
    fi
    
    echo ""
    # 生成驗證報告
    generate_validation_report
    
    # 測試結果總結
    echo ""
    echo "=========================================="
    log_ntn "🛰️  NTN配置驗證測試結果總結："
    
    for result in "${test_results[@]}"; do
        if [[ $result == *"PASS"* ]]; then
            echo -e "  ${GREEN}✅ $result${NC}"
        elif [[ $result == *"WARN"* ]]; then
            echo -e "  ${YELLOW}⚠️  $result${NC}"
        else
            echo -e "  ${RED}❌ $result${NC}"
        fi
    done
    
    echo "=========================================="
    log_ntn "NTN配置驗證測試完成"
}

# 執行主測試
main "$@" 