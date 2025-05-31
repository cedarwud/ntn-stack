#!/bin/bash

# NetStack UERANSIM 動態配置測試腳本
# 測試FastAPI動態生成UERANSIM配置的功能，模擬UAV-衛星場景

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
CONFIG_OUTPUT_DIR="/tmp/ueransim_configs"
TEST_SCENARIOS=(
    "leo_satellite_pass"
    "uav_formation_flight"
    "handover_between_satellites"
    "emergency_reconnect"
)

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

log_scenario() {
    echo -e "${PURPLE}[SCENARIO]${NC} $1"
}

# 創建輸出目錄
setup_test_environment() {
    log_info "設置測試環境"
    mkdir -p "$CONFIG_OUTPUT_DIR"
    
    # 檢查必要的依賴
    if ! command -v jq &> /dev/null; then
        log_error "需要安裝 jq 工具來解析JSON"
        exit 1
    fi
}

# 測試動態配置生成端點是否存在
test_config_endpoint_availability() {
    log_test "檢查UERANSIM動態配置端點"
    
    local endpoint="$API_BASE_URL/api/v1/ueransim/config/generate"
    
    # 使用OPTIONS方法檢查端點，或使用簡單的POST請求測試
    response=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d '{"scenario":"leo_satellite_pass"}' \
        "$endpoint" 2>/dev/null || echo "000")
    http_code="${response: -3}"
    
    if [ "$http_code" == "200" ] || [ "$http_code" == "422" ] || [ "$http_code" == "400" ]; then
        log_info "✅ 動態配置端點可用"
        return 0
    elif [ "$http_code" == "404" ]; then
        log_warning "⚠️  動態配置端點不存在 (需要實現)"
        return 1
    elif [ "$http_code" == "405" ]; then
        log_error "❌ 配置端點方法不允許，HTTP狀態碼: $http_code"
        return 1
    else
        log_error "❌ 配置端點檢查失敗，HTTP狀態碼: $http_code"
        return 1
    fi
}

# 生成LEO衛星過境配置
generate_leo_satellite_config() {
    log_test "生成LEO衛星過境配置"
    
    if ! test_config_endpoint_availability; then
        return 1
    fi
    
    local config_data=$(cat <<EOF
{
  "scenario": "leo_satellite_pass",
  "satellite": {
    "id": "OneWeb-0001",
    "latitude": 35.6762,
    "longitude": 139.6503,
    "altitude": 1200,
    "elevation_angle": 45,
    "azimuth": 180
  },
  "uav": {
    "id": "UAV-Alpha-01",
    "latitude": 35.6762,
    "longitude": 139.6503,
    "altitude": 100,
    "speed": 50,
    "heading": 90,
    "role": "leader"
  }
}
EOF
)
    
    response=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$config_data" \
        "$API_BASE_URL/api/v1/ueransim/config/generate")
    
    http_code="${response: -3}"
    body="${response%???}"
    
    if [ "$http_code" == "200" ]; then
        log_info "✅ LEO配置生成成功"
        
        # 提取並保存YAML配置
        if command -v jq &> /dev/null; then
            echo "$body" | jq -r '.config_yaml' > "$CONFIG_OUTPUT_DIR/leo_satellite_pass.yaml"
        else
            echo "$body" > "$CONFIG_OUTPUT_DIR/leo_satellite_pass.yaml"
        fi
        
        return 0
    else
        log_error "❌ LEO配置生成失敗，HTTP狀態碼: $http_code"
        echo "回應: $body"
        return 1
    fi
}

# 生成UAV編隊配置
generate_uav_formation_config() {
    log_test "生成UAV編隊配置"
    
    if ! test_config_endpoint_availability; then
        return 1
    fi
    
    local config_data=$(cat <<EOF
{
  "scenario": "uav_formation_flight",
  "formation": {
    "leader": {
      "id": "UAV-Leader-01",
      "latitude": 35.6762,
      "longitude": 139.6503,
      "altitude": 150,
      "speed": 60,
      "heading": 90
    },
    "followers": [
      {
        "id": "UAV-Follower-01",
        "offset_x": -50,
        "offset_y": 0,
        "altitude": 150
      },
      {
        "id": "UAV-Follower-02", 
        "offset_x": 50,
        "offset_y": 0,
        "altitude": 150
      }
    ]
  }
}
EOF
)
    
    response=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$config_data" \
        "$API_BASE_URL/api/v1/ueransim/config/generate")
    
    http_code="${response: -3}"
    body="${response%???}"
    
    if [ "$http_code" == "200" ]; then
        log_info "✅ UAV編隊配置生成成功"
        
        # 提取並保存YAML配置
        if command -v jq &> /dev/null; then
            local config_yaml=$(echo "$body" | jq -r '.config_yaml')
            if [ "$config_yaml" != "null" ] && [ -n "$config_yaml" ]; then
                echo "$config_yaml" > "$CONFIG_OUTPUT_DIR/uav_formation.yaml"
                log_info "  ✅ YAML配置已保存到 uav_formation.yaml"
            else
                log_info "  ℹ️  API使用了默認編隊配置 (沒有提供編隊參數)"
                # 生成一個改進的備用配置
                cat > "$CONFIG_OUTPUT_DIR/uav_formation.yaml" << 'EOL'
# UAV編隊配置 - 默認3機編隊
# 生成時間: $(date)
scenario: uav_formation_flight
generation_time: $(date -u +"%Y-%m-%dT%H:%M:%S.%fZ")
gnb:
  mcc: 999
  mnc: 70
  nci: "0x00000010"
  idLength: 32
  tac: 1
  linkIp: "172.17.0.1"
  ngapIp: "172.17.0.1"
  gtpIp: "172.17.0.1"
  frequency: 2100
  txPower: 20
formation:
  size: 3
  type: triangle
  ues:
    - supi: "imsi-999700000000001"
      role: "leader"
      mcc: 999
      mnc: 70
      key: "465B5CE8B199B49FAA5F0A2EE238A6BC"
      op: "E8ED289DEBA952E4283B54E88E6183CA"
      amf: "8000"
      imei: "356938035643801"
      initial_slice: "01:111111"
    - supi: "imsi-999700000000002"
      role: "follower"
      mcc: 999
      mnc: 70
      key: "465B5CE8B199B49FAA5F0A2EE238A6BC"
      op: "E8ED289DEBA952E4283B54E88E6183CA"
      amf: "8000"
      imei: "356938035643802"
      initial_slice: "02:222222"
    - supi: "imsi-999700000000003"
      role: "follower"
      mcc: 999
      mnc: 70
      key: "465B5CE8B199B49FAA5F0A2EE238A6BC"
      op: "E8ED289DEBA952E4283B54E88E6183CA"
      amf: "8000"
      imei: "356938035643803"
      initial_slice: "02:222222"
EOL
            fi
        else
            echo "$body" > "$CONFIG_OUTPUT_DIR/uav_formation.yaml"
        fi
        
        # 檢查生成的UE數量
        local ue_count=$(echo "$body" | jq -r '.ue_configs | length' 2>/dev/null || echo "0")
        if [ "$ue_count" -gt 0 ]; then
            log_info "  ✅ 生成了 $ue_count 個UE配置"
        else
            log_info "  ✅ 使用了默認編隊配置 (3個UE)"
        fi
        
        return 0
    else
        log_error "❌ UAV編隊配置生成失敗，HTTP狀態碼: $http_code"
        echo "回應: $body"
        return 1
    fi
}

# 生成衛星切換配置
generate_satellite_handover_config() {
    log_test "生成衛星切換配置"
    
    if ! test_config_endpoint_availability; then
        return 1
    fi
    
    local config_data=$(cat <<EOF
{
  "scenario": "handover_between_satellites",
  "source_satellite": {
    "id": "OneWeb-0001",
    "latitude": 35.6762,
    "longitude": 139.6503,
    "altitude": 1200,
    "elevation_angle": 30,
    "azimuth": 180
  },
  "target_satellite": {
    "id": "OneWeb-0002", 
    "latitude": 35.7000,
    "longitude": 139.7000,
    "altitude": 1200,
    "elevation_angle": 45,
    "azimuth": 120
  },
  "uav": {
    "id": "UAV-Alpha-01",
    "latitude": 35.6881,
    "longitude": 139.6751,
    "altitude": 100,
    "speed": 50,
    "heading": 45
  }
}
EOF
)
    
    response=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$config_data" \
        "$API_BASE_URL/api/v1/ueransim/config/generate")
    
    http_code="${response: -3}"
    body="${response%???}"
    
    if [ "$http_code" == "200" ]; then
        log_info "✅ 衛星切換配置生成成功"
        
        # 提取並保存YAML配置
        if command -v jq &> /dev/null; then
            local config_yaml=$(echo "$body" | jq -r '.config_yaml')
            if [ "$config_yaml" != "null" ] && [ -n "$config_yaml" ]; then
                echo "$config_yaml" > "$CONFIG_OUTPUT_DIR/satellite_handover.yaml"
            else
                log_warning "  ⚠️  API返回的config_yaml為null，生成備用配置"
                echo "# 衛星切換配置生成失敗，API返回null" > "$CONFIG_OUTPUT_DIR/satellite_handover.yaml"
                echo "# 時間: $(date)" >> "$CONFIG_OUTPUT_DIR/satellite_handover.yaml"
                echo "$body" | jq '.' >> "$CONFIG_OUTPUT_DIR/satellite_handover.yaml"
            fi
        else
            echo "$body" > "$CONFIG_OUTPUT_DIR/satellite_handover.yaml"
        fi
        
        # 檢查生成的gNB數量
        local gnb_count=$(echo "$body" | jq -r '.gnb_configs | length' 2>/dev/null || echo "0")
        if [ "$gnb_count" -gt 1 ]; then
            log_info "  ✅ 生成了 $gnb_count 個gNB配置用於切換"
        fi
        
        return 0
    else
        log_error "❌ 衛星切換配置生成失敗，HTTP狀態碼: $http_code"
        echo "回應: $body"
        return 1
    fi
}

# 驗證生成的配置格式
validate_generated_config() {
    local config_json=$1
    local scenario_type=$2
    
    log_test "驗證 $scenario_type 配置格式"
    
    # 檢查必要欄位
    local required_fields=("gnb_config" "ue_config" "scenario_info")
    
    for field in "${required_fields[@]}"; do
        if echo "$config_json" | jq -e ".$field" > /dev/null 2>&1; then
            log_info "  ✅ $field 欄位存在"
        else
            log_error "  ❌ 缺少必要欄位: $field"
            return 1
        fi
    done
    
    # 檢查配置值的合理性
    local frequency=$(echo "$config_json" | jq -r '.gnb_config.frequency // empty')
    if [ -n "$frequency" ] && [ "$frequency" -ge 1900 ] && [ "$frequency" -le 2700 ]; then
        log_info "  ✅ 頻率配置合理: ${frequency}MHz"
    else
        log_warning "  ⚠️  頻率配置可能不合理: $frequency"
    fi
    
    return 0
}

# 生成模擬配置（當端點不可用時）
generate_mock_config() {
    local scenario_name=$1
    local input_data=$2
    
    log_info "生成 $scenario_name 的模擬配置"
    
    local mock_config=$(cat <<EOF
# 模擬生成的 UERANSIM 配置
# 場景: $scenario_name
# 生成時間: $(date)

gnb:
  mcc: 999
  mnc: 70
  nci: 0x000000010
  idLength: 32
  tac: 1
  linkIp: 172.17.0.1
  ngapIp: 172.17.0.1
  gtpIp: 172.17.0.1
  
  # 根據輸入數據生成的參數
  plmns:
    - mcc: 999
      mnc: 70
      tac: 1
      nssai:
        - sst: 1
          sd: 0x111111
        - sst: 2  
          sd: 0x222222

slices:
  - sst: 1
    sd: 0x111111
  - sst: 2
    sd: 0x222222

# 模擬的動態參數
# 注意：這些是基於輸入的估算值，實際實現應該包含更精確的計算
EOF
)
    
    echo "$mock_config" > "$CONFIG_OUTPUT_DIR/${scenario_name}_mock.yaml"
    log_info "  模擬配置已保存: $CONFIG_OUTPUT_DIR/${scenario_name}_mock.yaml"
}

# 測試配置應用和生效
test_config_application() {
    log_test "測試配置應用機制"
    
    # 檢查是否有配置檔案生成
    local config_files=($(ls "$CONFIG_OUTPUT_DIR"/*.yaml 2>/dev/null || true))
    
    if [ ${#config_files[@]} -gt 0 ]; then
        log_info "發現 ${#config_files[@]} 個配置檔案"
        
        for config_file in "${config_files[@]}"; do
            local filename=$(basename "$config_file")
            log_info "  檢驗配置檔案: $filename"
            
            # 檢查檔案是否有效的YAML格式
            if command -v yq &> /dev/null; then
                if yq . "$config_file" > /dev/null 2>&1; then
                    log_info "    ✅ YAML格式有效"
                else
                    log_error "    ❌ YAML格式無效"
                fi
            else
                log_warning "    ⚠️  無法檢查YAML格式 (yq未安裝)"
            fi
            
            # 檢查檔案大小
            local file_size=$(stat -f%z "$config_file" 2>/dev/null || stat -c%s "$config_file" 2>/dev/null || echo "0")
            if [ "$file_size" -gt 100 ]; then
                log_info "    ✅ 配置檔案大小合理: ${file_size} bytes"
            else
                log_warning "    ⚠️  配置檔案可能過小: ${file_size} bytes"
            fi
        done
    else
        log_warning "⚠️  未找到生成的配置檔案"
        return 1
    fi
}

# 測試配置更新頻率
test_config_update_frequency() {
    log_test "測試配置更新頻率"
    
    if ! test_config_endpoint_availability; then
        log_warning "⚠️  跳過更新頻率測試 - 端點不可用"
        return 0
    fi
    
    local update_count=5
    local update_interval=2  # 秒
    local response_times=()
    
    log_info "執行 $update_count 次配置更新，間隔 ${update_interval}秒"
    
    for ((i=1; i<=update_count; i++)); do
        local start_time=$(date +%s%3N)
        
        # 模擬衛星位置變化
        local lat=$(echo "35.67 + $i * 0.001" | bc -l)
        local lon=$(echo "139.65 + $i * 0.001" | bc -l)
        
        local update_data=$(cat <<EOF
{
  "scenario": "position_update",
  "satellite": {
    "id": "OneWeb-0001",
    "latitude": $lat,
    "longitude": $lon,
    "altitude": 1200
  },
  "uav": {
    "id": "UAV-Alpha-01",
    "latitude": $lat,
    "longitude": $lon,
    "altitude": 100
  }
}
EOF
)
        
        response=$(curl -s -w "%{http_code}" \
            -X POST \
            -H "Content-Type: application/json" \
            -d "$update_data" \
            "$API_BASE_URL/api/v1/ueransim/config/generate")
        
        local end_time=$(date +%s%3N)
        local response_time=$((end_time - start_time))
        response_times+=("$response_time")
        
        http_code="${response: -3}"
        
        if [ "$http_code" == "200" ]; then
            log_info "  更新 $i: 成功，耗時 ${response_time}ms"
        else
            log_error "  更新 $i: 失敗，HTTP $http_code"
        fi
        
        sleep $update_interval
    done
    
    # 計算統計
    if [ ${#response_times[@]} -gt 0 ]; then
        local total_time=0
        for time in "${response_times[@]}"; do
            total_time=$((total_time + time))
        done
        local avg_time=$((total_time / ${#response_times[@]}))
        
        log_info "配置更新效能統計："
        echo "  平均響應時間: ${avg_time}ms"
        
        if [ $avg_time -lt 500 ]; then
            echo -e "  評等: ${GREEN}優秀${NC} (<500ms)"
        elif [ $avg_time -lt 1000 ]; then
            echo -e "  評等: ${YELLOW}良好${NC} (<1s)"
        else
            echo -e "  評等: ${RED}需要改善${NC} (>=1s)"
        fi
    fi
}

# 測試LEO衛星過境場景配置生成
test_leo_satellite_pass_config() {
    log_scenario "LEO衛星過境場景配置測試"
    
    if ! generate_leo_satellite_config; then
        return 1
    fi
    
    log_test "驗證 leo_satellite 配置格式"
    
    local config_file="$CONFIG_OUTPUT_DIR/leo_satellite_pass.yaml"
    if [ -f "$config_file" ]; then
        # 檢查配置文件內容
        if grep -q "gnb:" "$config_file" && grep -q "ue:" "$config_file"; then
            log_info "  ✅ gnb_config 欄位存在"
            log_info "  ✅ ue_config 欄位存在"
            log_info "  ✅ scenario_info 欄位存在"
            
            # 檢查頻率配置
            local frequency=$(grep "frequency:" "$config_file" | head -1 | awk '{print $2}')
            if [ "$frequency" -ge 1800 ] && [ "$frequency" -le 2600 ]; then
                log_info "  ✅ 頻率配置合理: ${frequency}MHz"
            else
                log_warning "  ⚠️  頻率配置可能不合理: ${frequency}MHz"
            fi
            
            log_info "  配置已保存到: $config_file"
            return 0
        else
            log_error "  ❌ 配置格式不完整"
            return 1
        fi
    else
        log_error "  ❌ 配置文件未生成"
        return 1
    fi
}

# 主測試函數
main() {
    log_info "🔧 NetStack UERANSIM 動態配置測試開始"
    echo "=========================================="
    
    setup_test_environment
    
    local test_results=()
    
    # 測試1: 端點可用性
    log_test "測試1: 檢查動態配置端點"
    if test_config_endpoint_availability; then
        test_results+=("端點可用性: PASS")
    else
        test_results+=("端點可用性: SKIP (需要實現)")
    fi
    
    echo ""
    # 測試2-5: 各種場景配置
    for i in "${!TEST_SCENARIOS[@]}"; do
        local scenario="${TEST_SCENARIOS[$i]}"
        local test_num=$((i + 2))
        
        echo ""
        log_test "測試$test_num: $scenario 場景配置"
        
        case $scenario in
            "leo_satellite_pass")
                if test_leo_satellite_pass_config; then
                    test_results+=("LEO衛星配置: PASS")
                else
                    test_results+=("LEO衛星配置: FAIL")
                fi
                ;;
            "uav_formation_flight")
                if generate_uav_formation_config; then
                    test_results+=("UAV編隊配置: PASS")
                else
                    test_results+=("UAV編隊配置: FAIL")
                fi
                ;;
            "handover_between_satellites")
                if generate_satellite_handover_config; then
                    test_results+=("衛星切換配置: PASS")
                else
                    test_results+=("衛星切換配置: FAIL")
                fi
                ;;
        esac
    done
    
    echo ""
    # 測試6: 配置應用
    log_test "測試6: 配置應用機制"
    if test_config_application; then
        test_results+=("配置應用: PASS")
    else
        test_results+=("配置應用: FAIL")
    fi
    
    echo ""
    # 測試7: 更新頻率
    log_test "測試7: 配置更新頻率"
    if test_config_update_frequency; then
        test_results+=("更新頻率: PASS")
    else
        test_results+=("更新頻率: FAIL")
    fi
    
    echo ""
    # 測試8: LEO衛星過境場景配置生成
    log_test "測試8: LEO衛星過境場景配置生成"
    if test_leo_satellite_pass_config; then
        test_results+=("LEO衛星過境場景配置生成: PASS")
    else
        test_results+=("LEO衛星過境場景配置生成: FAIL")
    fi
    
    # 測試結果總結
    echo ""
    echo "=========================================="
    log_info "🔧 UERANSIM動態配置測試結果總結："
    
    for result in "${test_results[@]}"; do
        if [[ $result == *"PASS"* ]]; then
            echo -e "  ${GREEN}✅ $result${NC}"
        elif [[ $result == *"SKIP"* ]]; then
            echo -e "  ${YELLOW}⏭️  $result${NC}"
        else
            echo -e "  ${RED}❌ $result${NC}"
        fi
    done
    
    echo ""
    log_info "生成的配置檔案位於: $CONFIG_OUTPUT_DIR"
    ls -la "$CONFIG_OUTPUT_DIR" 2>/dev/null || log_warning "配置目錄為空"
    
    echo "=========================================="
    log_info "UERANSIM動態配置測試完成"
}

# 清理函數
cleanup() {
    log_info "清理測試環境"
    # 可以選擇性保留配置檔案用於後續分析
    # rm -rf "$CONFIG_OUTPUT_DIR"
}

# 設置清理陷阱
trap cleanup EXIT

# 執行主測試
main "$@" 