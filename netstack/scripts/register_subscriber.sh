#!/bin/bash

# NetStack 用戶註冊腳本
# 註冊測試用戶到 Open5GS MongoDB 資料庫

# 使用更穩健的錯誤處理，避免單個錯誤導致整個腳本退出
set +e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
NC='\033[0m'

# 配置參數
MONGO_URI="${MONGO_URI:-mongodb://172.20.0.10:27017/open5gs}"
DOCKER_NETWORK="${DOCKER_NETWORK:-compose_netstack-core}"

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# 檢查 Docker 網路是否存在
check_docker_network() {
    if ! docker network ls --format "{{.Name}}" | grep -q "^${DOCKER_NETWORK}$"; then
        log_error "Docker 網路 $DOCKER_NETWORK 不存在"
        log_info "請先啟動 NetStack: make up"
        exit 1
    fi
}

# 註冊單一用戶
register_single_subscriber() {
    local imsi=$1
    local key=$2
    local opc=$3
    local apn=$4
    local sst=$5
    local sd=$6
    local description=$7
    
    log_info "註冊用戶: $imsi ($description) - SST=$sst, SD=$sd"
    
    # 直接使用 MongoDB 命令新增用戶
    output=$(docker run --rm \
        --net "$DOCKER_NETWORK" \
        mongo:6.0 \
        mongosh "$MONGO_URI" --quiet --eval "
        try {
          var result = db.subscribers.insertOne({
            imsi: '$imsi',
            subscriber_status: 0,
            access_restriction_data: 32,
            security: {
                k: '$key',
                opc: '$opc',
                amf: '8000',
                op: null
            },
            ambr: {
                downlink: { value: 1, unit: 3 },
                uplink: { value: 1, unit: 3 }
            },
            slice: [{
                sst: 1,
                default_indicator: true,
                session: [{
                    name: 'internet',
                    type: 1,
                    qos: {
                        index: 9,
                        arp: {
                            priority_level: 8,
                            pre_emption_capability: 1,
                            pre_emption_vulnerability: 1
                        }
                    },
                    ambr: {
                        downlink: { value: 1, unit: 3 },
                        uplink: { value: 1, unit: 3 }
                    },
                    pcc_rule: []
                }]
            }],
            schema_version: 1,
            __v: 0
          });
          if (result.acknowledged) { print('success'); } else { print('failed'); }
        } catch (e) {
          print('error: ' + e.message);
        }
        ")
    
    if [[ "$output" == *"success"* ]]; then
        log_success "✅ 用戶 $imsi 註冊成功"
        
        # 更新 Slice 配置
        update_subscriber_slice "$imsi" "$apn" "$sst" "$sd"
    else
        log_error "❌ 用戶 $imsi 註冊失敗"
        return 1
    fi
}

# 更新用戶 Slice 配置
update_subscriber_slice() {
    local imsi=$1
    local apn=$2
    local sst=$3
    local sd=$4
    
    log_info "更新用戶 $imsi 的 Slice 配置 (SST=$sst, SD=$sd)"
    
    # 使用 MongoDB 直接更新 Slice 配置
    output=$(docker run --rm \
        --net "$DOCKER_NETWORK" \
        mongo:6.0 \
        mongosh "$MONGO_URI" --quiet --eval "
        try {
          var result = db.subscribers.updateOne(
              { imsi: '$imsi' },
              {
                  \$set: {
                      'slice.0.sst': $sst,
                      'slice.0.sd': '$sd',
                      'slice.0.session.0.name': '$apn'
                  }
              }
          );
          if (result.acknowledged) { print('success'); } else { print('failed'); }
        } catch (e) {
          print('error: ' + e.message);
        }
        ")
    
    if [[ "$output" == *"success"* ]]; then
        log_success "✅ 用戶 $imsi Slice 配置更新成功"
    else
        log_error "❌ 用戶 $imsi Slice 配置更新失敗"
    fi
}

# 檢查用戶是否已存在
check_subscriber_exists() {
    local imsi=$1
    
    # 直接使用計數查詢，這種方式比查找單個文檔更可靠
    result=$(docker run --rm \
        --net "$DOCKER_NETWORK" \
        mongo:6.0 \
        mongosh "$MONGO_URI" --quiet --eval "
        try {
          // 直接使用計數查詢，避免文檔緩存問題
          var count = db.subscribers.countDocuments({ imsi: '$imsi' });
          print('count: ' + count);
        } catch (e) {
          print('error: ' + e.message);
        }
        " 2>/dev/null)
    
    # 解析計數結果
    if [[ "$result" == *"count: 0"* ]]; then
        log_info "檢測到用戶 $imsi 不存在"
        return 1
    elif [[ "$result" == *"count: "* ]]; then
        log_info "檢測到用戶 $imsi 已存在 ($result)"
        return 0
    else
        log_warning "無法確定用戶 $imsi 狀態，假設不存在: $result"
        return 1
    fi
}

# 註冊所有預定義用戶
register_all_subscribers() {
    log_info "開始註冊 NetStack 測試用戶..."
    
    # 先嘗試刪除所有可能殘留的用戶資料
    log_info "重置資料庫狀態..."
    reset_result=$(docker run --rm \
        --net "$DOCKER_NETWORK" \
        mongo:6.0 \
        mongosh "$MONGO_URI" --quiet --eval "
        try {
          // 刪除測試用戶前綴的用戶資料
          var result = db.subscribers.deleteMany({ imsi: /^99970/ });
          print('deleted: ' + result.deletedCount);
        } catch (e) {
          print('error: ' + e.message);
        }
        " 2>/dev/null)
    
    # 再次檢查資料庫狀態
    log_info "檢查資料庫連接和狀態..."
    count_result=$(docker run --rm \
        --net "$DOCKER_NETWORK" \
        mongo:6.0 \
        mongosh "$MONGO_URI" --quiet --eval "
        try {
          var count = db.subscribers.countDocuments({ imsi: /^99970/ });
          print('count: ' + count);
        } catch (e) {
          print('error: ' + e.message);
        }
        " 2>/dev/null)
    
    if [[ "$count_result" == *"error"* ]]; then
        log_error "資料庫連接出錯: $count_result"
        log_warning "繼續嘗試註冊，但可能會出現問題"
    else
        if [[ "$count_result" == *"count: 0"* ]]; then
            log_info "資料庫狀態檢查完成，目前測試用戶數: 0"
        else
            log_warning "資料庫可能存在殘留用戶: $count_result，執行強制清理"
            docker run --rm \
                --net "$DOCKER_NETWORK" \
                mongo:6.0 \
                mongosh "$MONGO_URI" --quiet --eval "db.subscribers.deleteMany({ imsi: /^99970/ });" 2>/dev/null
        fi
    fi
    
    # 用戶配置陣列
    # 格式: IMSI:Key:OPc:APN:SST:SD:Description
    local subscribers=(
        # eMBB 用戶 (SST=1) - 5個用戶
        "999700000000001:465B5CE8B199B49FAA5F0A2EE238A6BC:E8ED289DEBA952E4283B54E88E6183CA:internet:1:0x111111:eMBB 用戶 1 (手機)"
        "999700000000002:465B5CE8B199B49FAA5F0A2EE238A6BC:E8ED289DEBA952E4283B54E88E6183CA:internet:1:0x111111:eMBB 用戶 2 (平板)"
        "999700000000003:465B5CE8B199B49FAA5F0A2EE238A6BC:E8ED289DEBA952E4283B54E88E6183CA:internet:1:0x000001:eMBB 用戶 3 (筆電)" 
        "999700000000004:465B5CE8B199B49FAA5F0A2EE238A6BC:E8ED289DEBA952E4283B54E88E6183CA:internet:1:0x111111:eMBB 用戶 4 (智慧手錶)"
        "999700000000005:465B5CE8B199B49FAA5F0A2EE238A6BC:E8ED289DEBA952E4283B54E88E6183CA:internet:1:0x111111:eMBB 用戶 5 (車載系統)"

        # uRLLC 用戶 (SST=2) - 4個用戶
        "999700000000011:465B5CE8B199B49FAA5F0A2EE238A6BC:E8ED289DEBA952E4283B54E88E6183CA:internet:2:0x222222:uRLLC 用戶 1 (工業控制)"
        "999700000000012:465B5CE8B199B49FAA5F0A2EE238A6BC:E8ED289DEBA952E4283B54E88E6183CA:robotics:2:0x222222:uRLLC 用戶 2 (遠程醫療)"
        "999700000000013:465B5CE8B199B49FAA5F0A2EE238A6BC:E8ED289DEBA952E4283B54E88E6183CA:internet:2:0x000002:uRLLC 用戶 3 (無人機控制)"
        "999700000000014:465B5CE8B199B49FAA5F0A2EE238A6BC:E8ED289DEBA952E4283B54E88E6183CA:automotive:2:0x222222:uRLLC 用戶 4 (自動駕駛)"

        # mMTC 用戶 (SST=3) - 4個用戶
        "999700000000021:465B5CE8B199B49FAA5F0A2EE238A6BC:E8ED289DEBA952E4283B54E88E6183CA:iot:3:0x333333:mMTC 用戶 1 (智慧電錶)"
        "999700000000022:465B5CE8B199B49FAA5F0A2EE238A6BC:E8ED289DEBA952E4283B54E88E6183CA:sensors:3:0x333333:mMTC 用戶 2 (環境感測器)"
        "999700000000023:465B5CE8B199B49FAA5F0A2EE238A6BC:E8ED289DEBA952E4283B54E88E6183CA:wearables:3:0x000003:mMTC 用戶 3 (穿戴裝置)"
        "999700000000024:465B5CE8B199B49FAA5F0A2EE238A6BC:E8ED289DEBA952E4283B54E88E6183CA:iot:3:0x333333:mMTC 用戶 4 (智慧農業)"
        
        # 衛星-無人機 專用測試用戶
        "999700000000050:465B5CE8B199B49FAA5F0A2EE238A6BC:E8ED289DEBA952E4283B54E88E6183CA:internet:1:0x111111:衛星無人機 eMBB 用戶"
        "999700000000051:465B5CE8B199B49FAA5F0A2EE238A6BC:E8ED289DEBA952E4283B54E88E6183CA:internet:2:0x222222:衛星無人機 uRLLC 用戶"
        "999700000000052:465B5CE8B199B49FAA5F0A2EE238A6BC:E8ED289DEBA952E4283B54E88E6183CA:internet:3:0x333333:衛星無人機 mMTC 用戶"
        
        # 測試用戶 (可動態切換 Slice)
        "999700000000099:465B5CE8B199B49FAA5F0A2EE238A6BC:E8ED289DEBA952E4283B54E88E6183CA:internet:1:0x111111:測試用戶 (動態切換)"
    )
    
    local success_count=0
    local skip_count=0
    local error_count=0
    
    for subscriber_info in "${subscribers[@]}"; do
        IFS=':' read -r imsi key opc apn sst sd description <<< "$subscriber_info"
        
        log_info "--- Processing subscriber: IMSI=$imsi, Key=$key, OPc=$opc, APN=$apn, SST=$sst, SD=$sd, Desc=$description ---"

        # 檢查用戶是否已存在
        if check_subscriber_exists "$imsi"; then
            log_warning "用戶 $imsi 已存在，跳過註冊"
            ((skip_count++))
            continue
        fi
        
        # 註冊用戶
        log_info "Attempting to register: $imsi"
        if register_single_subscriber "$imsi" "$key" "$opc" "$apn" "$sst" "$sd" "$description"; then
            ((success_count++))
            log_info "Successfully processed (registered or updated): $imsi"
            echo ""
        else
            ((error_count++))
            log_warning "Failed or skipped processing for: $imsi"
            echo ""
            # 即使註冊失敗也繼續執行，不要退出腳本
        fi
        log_info "--- Finished processing subscriber: $imsi ---"
    done
    
    # 統計結果
    echo "=================================================="
    echo "📊 用戶註冊結果統計"
    echo "=================================================="
    echo -e "成功註冊: ${GREEN}$success_count${NC}"
    echo -e "跳過 (已存在): ${YELLOW}$skip_count${NC}"
    echo -e "註冊失敗: ${RED}$error_count${NC}"
    echo -e "總計: $((success_count + skip_count + error_count))"
    
    if [ $error_count -eq 0 ]; then
        log_success "🎉 所有用戶註冊完成！"
        return 0
    else
        log_warning "⚠️ 有 $error_count 個用戶註冊失敗，但其他用戶註冊成功"
        # 返回 0 而不是 1，這樣即使有少量錯誤也不會中斷整個註冊過程
        return 0
    fi
}

# 顯示用戶列表
show_subscribers() {
    log_info "查詢已註冊用戶..."
    
    docker run --rm \
        --net "$DOCKER_NETWORK" \
        mongo:6.0 \
        mongosh "$MONGO_URI" --quiet --eval "
        db.subscribers.find({}, {
            imsi: 1,
            'slice.sst': 1,
            'slice.sd': 1,
            'slice.session.name': 1,
            _id: 0
        }).forEach(function(doc) {
            var slice = doc.slice && doc.slice[0] ? doc.slice[0] : {};
            var session = slice.session && slice.session[0] ? slice.session[0] : {};
            var sliceType = slice.sst === 1 ? 'eMBB' : (slice.sst === 2 ? 'uRLLC' : (slice.sst === 3 ? 'mMTC' : 'Unknown'));
            print('IMSI: ' + doc.imsi + ', Slice: ' + sliceType + ' (SST=' + (slice.sst || 'N/A') + ', SD=' + (slice.sd || 'N/A') + '), APN: ' + (session.name || 'N/A'));
        });"
}

# 刪除所有測試用戶
delete_all_subscribers() {
    log_warning "⚠️  即將刪除所有以 IMSI 前綴 99970 開頭的測試用戶！"
    read -p "確定要繼續嗎？(y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "取消刪除操作"
        return 0
    fi
    
    log_info "正在刪除所有 IMSI 以 99970 開頭的用戶..."
    
    output=$(docker run --rm \
        --net "$DOCKER_NETWORK" \
        mongo:6.0 \
        mongosh "$MONGO_URI" --quiet --eval "
        try {
          var result = db.subscribers.deleteMany({ imsi: /^99970/ });
          print('deletedCount: ' + result.deletedCount);
        } catch (e) {
          print('error: ' + e.message);
        }
        ")
    
    if [[ "$output" == *"error"* ]]; then
        log_error "❌ 刪除用戶時發生錯誤: $output"
        return 1
    elif [[ "$output" == *"deletedCount"* ]]; then
        deleted_count=$(echo "$output" | grep -o 'deletedCount: [0-9]*' | awk '{print $2}')
        if [ -z "$deleted_count" ]; then # Handle case where grep might fail or awk gives empty
            deleted_count=0
        fi
        log_success "✅ 成功刪除 $deleted_count 個用戶"
    else
        log_warning "⚠️ 未能解析刪除結果，可能沒有用戶被刪除或發生未知問題: $output"
    fi
    
    log_info "刪除操作完成"
}

# 使用說明
show_usage() {
    echo "NetStack 用戶註冊腳本"
    echo ""
    echo "使用方式:"
    echo "  $0 [command] [options]"
    echo ""
    echo "命令:"
    echo "  register    註冊所有測試用戶 (預設)"
    echo "  show        顯示已註冊用戶列表"
    echo "  delete      刪除所有測試用戶"
    echo "  add         註冊單一用戶"
    echo "  help        顯示此說明"
    echo ""
    echo "單一用戶註冊範例:"
    echo "  $0 add 999700000000001 465B5CE8B199B49FAA5F0A2EE238A6BC E8ED289DEBA952E4283B54E88E6183CA internet 1 0x111111"
    echo ""
    echo "環境變數:"
    echo "  MONGO_URI      MongoDB 連接字串 (預設: mongodb://172.20.0.10:27017/open5gs)"
    echo "  DOCKER_NETWORK Docker 網路名稱 (預設: compose_netstack-core)"
}

# 主程式
main() {
    local command="${1:-register}"
    
    case "$command" in
        "register")
            check_docker_network
            register_all_subscribers
            ;;
        "show")
            check_docker_network
            show_subscribers
            ;;
        "delete")
            check_docker_network
            delete_all_subscribers
            ;;
        "add")
            if [ $# -lt 7 ]; then
                log_error "參數不足"
                echo "使用方式: $0 add <IMSI> <Key> <OPc> <APN> <SST> <SD>"
                exit 1
            fi
            check_docker_network
            register_single_subscriber "$2" "$3" "$4" "$5" "$6" "$7" "手動新增"
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            log_error "未知命令: $command"
            show_usage
            exit 1
            ;;
    esac
}

# 檢查依賴
if ! command -v docker &> /dev/null; then
    log_error "docker 命令未找到，請先安裝 Docker"
    exit 1
fi

# 執行主程式
main "$@"