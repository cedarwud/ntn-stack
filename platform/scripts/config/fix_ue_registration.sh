#!/bin/bash

# 腳本：修復UE註冊問題
# 目的：重新設置UE和訂閱者配置確保註冊成功

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日誌函數
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 顯示腳本用途
echo "===== UE 註冊問題修復腳本 ====="
log_info "此腳本將修復UE註冊問題，包括:"
log_info "1. 確保訂閱者信息與UE配置一致"
log_info "2. 重置有問題的UE"
log_info "3. 重新啟動相關服務"

# 檢查 Docker 是否可用
if ! command -v docker &> /dev/null; then
    log_error "Docker 命令不可用，請確保 Docker 已正確安裝"
    exit 1
fi

# 檢查容器運行狀態
log_info "檢查容器運行狀態..."
REQUIRED_CONTAINERS=("ntn-stack-ues1-1" "ntn-stack-amf-1" "open5gs-mongo")
MISSING_CONTAINERS=0

for container in "${REQUIRED_CONTAINERS[@]}"; do
    if ! docker ps | grep -q "$container"; then
        log_warning "容器 $container 未運行"
        MISSING_CONTAINERS=$((MISSING_CONTAINERS + 1))
    else
        log_success "容器 $container 正在運行"
    fi
done

if [ $MISSING_CONTAINERS -gt 0 ]; then
    log_warning "有 $MISSING_CONTAINERS 個必需的容器未運行"
    log_info "是否要繼續? [y/N]"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log_info "腳本已取消"
        exit 0
    fi
fi

# 重設 MongoDB 中的訂閱者信息
log_info "正在重設 MongoDB 中的訂閱者信息..."
docker exec open5gs-mongo mongosh --quiet open5gs --eval "db.subscribers.drop()" || {
    log_error "無法刪除訂閱者集合"
    exit 1
}
log_success "訂閱者集合已刪除"

# 添加新的訂閱者信息，確保與UE配置一致
log_info "添加新的訂閱者信息..."
docker run -ti --rm \
    --network=ntn-stack_open5gs-net \
    -e DB_URI=mongodb://open5gs-mongo/open5gs \
    gradiant/open5gs-dbctl:0.10.3 \
    open5gs-dbctl add 999700000000001 465B5CE8B199B49FAA5F0A2EE238A6BC E8ED289DEBA952E4283B54E88E6183CA && \
log_success "訂閱者 999700000000001 已添加"

# 獲取並顯示訂閱者信息
log_info "顯示訂閱者列表..."
docker run -ti --rm \
    --network=ntn-stack_open5gs-net \
    -e DB_URI=mongodb://open5gs-mongo/open5gs \
    gradiant/open5gs-dbctl:0.10.3 \
    open5gs-dbctl showfiltered

# 重新啟動UE容器
log_info "重新啟動UE容器..."
docker restart ntn-stack-ues1-1
log_success "UE容器已重新啟動"

# 等待UE容器完全啟動
log_info "等待UE容器完全啟動 (10秒)..."
sleep 10

# 檢查UE註冊狀態
log_info "檢查UE註冊狀態..."
UE_STATUS=$(docker exec ntn-stack-ues1-1 /usr/local/bin/nr-cli imsi-999700000000001 -e "status" 2>&1 || echo "命令執行失敗")

echo "====== UE 狀態 ======"
echo "$UE_STATUS"
echo "======================"

# 檢查註冊是否成功
if echo "$UE_STATUS" | grep -q "5GMM-REGISTERED"; then
    log_success "UE已成功註冊到網絡"
else
    log_warning "UE尚未註冊到網絡，可能需要更多時間或進一步調試"
    
    # 提供手動嘗試註冊的命令
    echo 
    log_info "您可以嘗試手動註冊UE，運行以下命令:"
    echo "docker exec ntn-stack-ues1-1 /usr/local/bin/nr-cli imsi-999700000000001 -e \"deregister normal\""
    echo "sleep 5"
    echo "docker exec ntn-stack-ues1-1 /usr/local/bin/nr-cli imsi-999700000000001 -e \"register\""
fi

echo
log_info "修復操作完成"
echo "===== 腳本執行結束 ====="
