#!/bin/bash

# NetStack 用戶顯示腳本
# 顯示已註冊用戶的詳細資訊

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[1;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
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

# 檢查 Docker 網路是否存在
check_docker_network() {
    if ! docker network ls --format "{{.Name}}" | grep -q "^${DOCKER_NETWORK}$"; then
        log_error "Docker 網路 $DOCKER_NETWORK 不存在"
        log_info "請先啟動 NetStack: make up"
        exit 1
    fi
}

# 顯示用戶統計
show_subscribers_summary() {
    log_info "用戶統計摘要"
    
    docker run --rm \
        --net "$DOCKER_NETWORK" \
        mongo:6.0 \
        mongosh "$MONGO_URI" --quiet --eval "
        var total = db.subscribers.countDocuments({});
        var embb = db.subscribers.countDocuments({'slice.sst': 1});
        var urllc = db.subscribers.countDocuments({'slice.sst': 2});
        var mmtc = db.subscribers.countDocuments({'slice.sst': 3});
        var other = total - embb - urllc - mmtc;
        
        print('='.repeat(50));
        print('📊 NetStack 用戶統計');
        print('='.repeat(50));
        print('總用戶數: ' + total);
        print('eMBB 用戶: ' + embb + ' (SST=1) 📱 高數據率');
        print('uRLLC 用戶: ' + urllc + ' (SST=2) ⚡ 低延遲');
        print('mMTC 用戶: ' + mmtc + ' (SST=3) 🔗 物聯網');
        if (other > 0) {
            print('其他 Slice: ' + other);
        }
        print('='.repeat(50));
        "
}

# 顯示詳細用戶列表
show_subscribers_detail() {
    log_info "詳細用戶列表"
    
    docker run --rm \
        --net "$DOCKER_NETWORK" \
        mongo:6.0 \
        mongosh "$MONGO_URI" --quiet --eval "
        print('\n📋 已註冊用戶詳細資訊:');
        print('-'.repeat(80));
        
        db.subscribers.find({}).sort({imsi: 1}).forEach(function(doc) {
            var slice = doc.slice && doc.slice[0] ? doc.slice[0] : {};
            var session = slice.session && slice.session[0] ? slice.session[0] : {};
            var qos = session.qos ? session.qos : {};
            
            // 判斷 Slice 類型
            var sliceType = 'Unknown';
            var sliceIcon = '❓';
            if (slice.sst === 1) {
                sliceType = 'eMBB';
                sliceIcon = '📱';
            } else if (slice.sst === 2) {
                sliceType = 'uRLLC';
                sliceIcon = '⚡';
            } else if (slice.sst === 3) {
                sliceType = 'mMTC';
                sliceIcon = '🔗';
            }
            
            print(sliceIcon + ' IMSI: ' + doc.imsi);
            print('   Slice: ' + sliceType + ' (SST=' + (slice.sst || 'N/A') + ', SD=' + (slice.sd || 'N/A') + ')');
            print('   APN: ' + (session.name || 'N/A'));
            print('   QoS Index: ' + (qos.index || 'N/A'));
            
            if (session.ambr) {
                var dl = session.ambr.downlink || {};
                var ul = session.ambr.uplink || {};
                print('   AMBR: DL=' + (dl.value || 'N/A') + (dl.unit ? getUnitName(dl.unit) : '') + 
                      ', UL=' + (ul.value || 'N/A') + (ul.unit ? getUnitName(ul.unit) : ''));
            }
            
            if (doc.security) {
                print('   Security: K=' + (doc.security.k ? doc.security.k.substring(0, 8) + '...' : 'N/A') + 
                      ', OPc=' + (doc.security.opc ? doc.security.opc.substring(0, 8) + '...' : 'N/A'));
            }
            
            if (doc.created) {
                print('   建立時間: ' + new Date(doc.created).toLocaleString());
            }
            
            print('-'.repeat(80));
        });
        
        // 單位轉換函數
        function getUnitName(unit) {
            switch(unit) {
                case 0: return 'bps';
                case 1: return 'Kbps';
                case 2: return 'Mbps';
                case 3: return 'Gbps';
                case 4: return 'Tbps';
                default: return '';
            }
        }
        "
}

# 顯示特定 Slice 的用戶
show_slice_subscribers() {
    local slice_type=$1
    
    if [ "$slice_type" == "eMBB" ]; then
        sst=1
        icon="📱"
    elif [ "$slice_type" == "uRLLC" ]; then
        sst=2
        icon="⚡"
    elif [ "$slice_type" == "mMTC" ]; then
        sst=3
        icon="🔗"
    else
        log_error "無效的 Slice 類型: $slice_type (支援: eMBB, uRLLC, mMTC)"
        return 1
    fi
    
    log_info "$icon $slice_type Slice 用戶列表"
    
    docker run --rm \
        --net "$DOCKER_NETWORK" \
        mongo:6.0 \
        mongosh "$MONGO_URI" --quiet --eval "
        var count = 0;
        print('\n$icon $slice_type Slice 用戶 (SST=$sst):');
        print('-'.repeat(60));
        
        db.subscribers.find({'slice.sst': $sst}).sort({imsi: 1}).forEach(function(doc) {
            var slice = doc.slice && doc.slice[0] ? doc.slice[0] : {};
            var session = slice.session && slice.session[0] ? slice.session[0] : {};
            
            count++;
            print(count + '. IMSI: ' + doc.imsi);
            print('   APN: ' + (session.name || 'N/A'));
            print('   SD: ' + (slice.sd || 'N/A'));
            print('');
        });
        
        if (count === 0) {
            print('❌ 沒有找到 $slice_type Slice 的用戶');
        } else {
            print('✅ 共找到 ' + count + ' 個 $slice_type Slice 用戶');
        }
        "
}

# 搜尋特定用戶
search_subscriber() {
    local imsi=$1
    
    log_info "搜尋用戶: $imsi"
    
    docker run --rm \
        --net "$DOCKER_NETWORK" \
        mongo:6.0 \
        mongosh "$MONGO_URI" --quiet --eval "
        var doc = db.subscribers.findOne({imsi: '$imsi'});
        
        if (!doc) {
            print('❌ 找不到 IMSI: $imsi 的用戶');
        } else {
            var slice = doc.slice && doc.slice[0] ? doc.slice[0] : {};
            var session = slice.session && slice.session[0] ? slice.session[0] : {};
            var qos = session.qos ? session.qos : {};
            var ambr = session.ambr || {};
            var security = doc.security || {};
            
            var sliceType = slice.sst === 1 ? 'eMBB' : (slice.sst === 2 ? 'uRLLC' : (slice.sst === 3 ? 'mMTC' : 'Unknown'));
            var sliceIcon = slice.sst === 1 ? '📱' : (slice.sst === 2 ? '⚡' : (slice.sst === 3 ? '🔗' : '❓'));
            
            print('✅ 找到用戶資訊:');
            print('='.repeat(50));
            print(sliceIcon + ' IMSI: ' + doc.imsi);
            print('📍 Slice 資訊:');
            print('   類型: ' + sliceType);
            print('   SST: ' + (slice.sst || 'N/A'));
            print('   SD: ' + (slice.sd || 'N/A'));
            print('   預設指標: ' + (slice.default_indicator ? '是' : '否'));
            
            print('🌐 會話資訊:');
            print('   APN: ' + (session.name || 'N/A'));
            print('   類型: ' + (session.type === 3 ? 'IPv4' : session.type === 2 ? 'IPv6' : session.type === 1 ? 'IPv4v6' : 'Unknown'));
            print('   QoS Index: ' + (qos.index || 'N/A'));
            
            if (qos.arp) {
                print('   ARP Priority: ' + (qos.arp.priority_level || 'N/A'));
            }
            
            if (ambr.downlink || ambr.uplink) {
                print('📊 AMBR 設定:');
                if (ambr.downlink) {
                    print('   下行: ' + (ambr.downlink.value || 'N/A') + getUnitName(ambr.downlink.unit));
                }
                if (ambr.uplink) {
                    print('   上行: ' + (ambr.uplink.value || 'N/A') + getUnitName(ambr.uplink.unit));
                }
            }
            
            print('🔐 安全資訊:');
            print('   K: ' + (security.k || 'N/A'));
            print('   AMF: ' + (security.amf || 'N/A'));
            print('   OPc: ' + (security.opc || 'N/A'));
            print('   SQN: ' + (security.sqn || 'N/A'));
            
            if (doc.created) {
                print('📅 建立時間: ' + new Date(doc.created).toLocaleString());
            }
            
            if (doc.modified) {
                print('📅 修改時間: ' + new Date(doc.modified).toLocaleString());
            }
        }
        
        function getUnitName(unit) {
            switch(unit) {
                case 0: return 'bps';
                case 1: return 'Kbps';
                case 2: return 'Mbps';
                case 3: return 'Gbps';
                case 4: return 'Tbps';
                default: return '';
            }
        }
        "
}

# 導出用戶資料
export_subscribers() {
    local output_file="${1:-subscribers_export.json}"
    
    log_info "導出用戶資料到: $output_file"
    
    docker run --rm \
        --net "$DOCKER_NETWORK" \
        -v "$(pwd):/output" \
        mongo:6.0 \
        mongosh "$MONGO_URI" --quiet --eval "
        var subscribers = db.subscribers.find({}).toArray();
        var exportData = {
            export_time: new Date(),
            total_count: subscribers.length,
            subscribers: subscribers
        };
        
        // 輸出 JSON 格式
        print(JSON.stringify(exportData, null, 2));
        " > "$output_file"
    
    if [ $? -eq 0 ]; then
        log_info "✅ 用戶資料已導出到: $output_file"
        log_info "檔案大小: $(du -h "$output_file" | cut -f1)"
    else
        log_error "❌ 用戶資料導出失敗"
    fi
}

# 使用說明
show_usage() {
    echo -e "${CYAN}NetStack 用戶顯示腳本${NC}"
    echo ""
    echo "使用方式:"
    echo "  $0 [command] [options]"
    echo ""
    echo "命令:"
    echo -e "  ${BLUE}summary${NC}     顯示用戶統計摘要 (預設)"
    echo -e "  ${BLUE}list${NC}        顯示詳細用戶列表"
    echo -e "  ${BLUE}slice${NC}       顯示特定 Slice 的用戶"
    echo -e "  ${BLUE}search${NC}      搜尋特定用戶"
    echo -e "  ${BLUE}export${NC}      導出用戶資料"
    echo -e "  ${BLUE}help${NC}        顯示此說明"
    echo ""
    echo "範例:"
    echo "  $0 summary                      # 顯示統計摘要"
    echo "  $0 list                         # 顯示所有用戶"
    echo "  $0 slice eMBB                   # 顯示 eMBB Slice 用戶"
    echo "  $0 slice uRLLC                  # 顯示 uRLLC Slice 用戶"
    echo "  $0 search 999700000000001       # 搜尋特定用戶"
    echo "  $0 export users.json            # 導出用戶資料"
    echo ""
    echo "環境變數:"
    echo "  MONGO_URI      MongoDB 連接字串 (預設: mongodb://mongo:27017/open5gs)"
    echo "  DOCKER_NETWORK Docker 網路名稱 (預設: netstack_netstack-core)"
}

# 主程式
main() {
    local command="${1:-summary}"
    
    case "$command" in
        "summary")
            check_docker_network
            show_subscribers_summary
            ;;
        "list")
            check_docker_network
            show_subscribers_detail
            ;;
        "slice")
            if [ -z "$2" ]; then
                log_error "請指定 Slice 類型 (eMBB、uRLLC 或 mMTC)"
                exit 1
            fi
            check_docker_network
            show_slice_subscribers "$2"
            ;;
        "search")
            if [ -z "$2" ]; then
                log_error "請指定要搜尋的 IMSI"
                exit 1
            fi
            check_docker_network
            search_subscriber "$2"
            ;;
        "export")
            check_docker_network
            export_subscribers "$2"
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