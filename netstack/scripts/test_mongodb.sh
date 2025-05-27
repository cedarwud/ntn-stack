#!/bin/bash
# 測試直接向MongoDB插入不同SST的用戶

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}測試MongoDB用戶註冊腳本${NC}"

# MongoDB 連接設置
MONGO_URI="mongodb://172.20.0.10:27017/open5gs"
DOCKER_NETWORK="compose_netstack-core"

# 首先清空現有用戶
echo "清空現有用戶..."
docker run --rm --net "$DOCKER_NETWORK" mongo:6.0 mongosh "$MONGO_URI" --quiet --eval "db.subscribers.deleteMany({})"

# 檢查是否已清空
COUNT=$(docker run --rm --net "$DOCKER_NETWORK" mongo:6.0 mongosh "$MONGO_URI" --quiet --eval "print(db.subscribers.countDocuments({}))")
echo "清空後用戶數量: $COUNT"

# 定義三種不同SST值的用戶
declare -A users
users[1]="999700000001000:eMBB_用戶"
users[2]="999700000002000:uRLLC_用戶"
users[3]="999700000003000:mMTC_用戶"

# 註冊三種不同SST值的用戶
for sst in 1 2 3; do
    IFS=':' read -r imsi description <<< "${users[$sst]}"
    echo -e "${YELLOW}註冊 SST=$sst 的用戶: $imsi ($description)${NC}"
    
    # 構建特定於SST的SD值
    SD="0x$(printf "%06x" $((sst * 111111)))"
    
    # 直接執行MongoDB命令插入用戶
    output=$(docker run --rm --net "$DOCKER_NETWORK" mongo:6.0 mongosh "$MONGO_URI" --quiet --eval "
    try {
      var result = db.subscribers.insertOne({
        imsi: '$imsi',
        subscriber_status: 0,
        security: {
          k: '465B5CE8B199B49FAA5F0A2EE238A6BC',
          opc: 'E8ED289DEBA952E4283B54E88E6183CA',
          amf: '8000'
        },
        slice: [{
          sst: $sst,
          sd: '$SD',
          default_indicator: true,
          session: [{
            name: 'internet',
            type: 1,
            qos: { index: 9 }
          }]
        }]
      });
      
      print('結果: ' + (result.acknowledged ? '成功' : '失敗'));
    } catch (e) {
      print('錯誤: ' + e.message);
    }
    ")
    
    echo "MongoDB響應: $output"
    echo ""
done

# 驗證結果
echo -e "${GREEN}驗證結果${NC}"
docker run --rm --net "$DOCKER_NETWORK" mongo:6.0 mongosh "$MONGO_URI" --quiet --eval "
var total = db.subscribers.countDocuments({});
var embb = db.subscribers.countDocuments({'slice.sst': 1});
var urllc = db.subscribers.countDocuments({'slice.sst': 2});
var mmtc = db.subscribers.countDocuments({'slice.sst': 3});

print('總用戶數: ' + total);
print('eMBB用戶(SST=1): ' + embb);
print('uRLLC用戶(SST=2): ' + urllc);
print('mMTC用戶(SST=3): ' + mmtc);

// 顯示每個用戶的詳細信息
print('\n用戶詳細信息:');
db.subscribers.find().forEach(function(doc) {
  var slice = doc.slice && doc.slice[0] ? doc.slice[0] : {};
  var session = slice.session && slice.session[0] ? slice.session[0] : {};
  print('IMSI: ' + doc.imsi + ', SST: ' + slice.sst + ', SD: ' + slice.sd + ', APN: ' + session.name);
});
"

# 執行完成
echo -e "${GREEN}測試完成${NC}"
