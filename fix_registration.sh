#!/bin/bash

echo "===== 開始修復 UE 註冊問題 ====="

# 1. 停止 UE 容器
echo "停止現有的 UE 容器..."
docker stop ntn-stack-ues1-1 ntn-stack-ues2-1

# 2. 修改 MongoDB 中的訂閱者資料，使其匹配 UE 容器中的安全金鑰
echo "更新 MongoDB 中的訂閱者安全金鑰..."
docker exec -it open5gs-mongo mongosh --eval "
db = db.getSiblingDB('open5gs');
db.subscribers.updateMany(
  {},
  {
    \$set: {
      'security.k': '465b5ce8b199b49faa5f0a2ee238a6bc',
      'security.op': 'e8ed289deba952e4283b54e88e6183ca',
      'security.opc': null,
      'security.sqn': 0 
    }
  }
);
"

# 3. 添加 UE 容器中使用的 IMSI
echo "添加 UE 容器使用的 IMSI 到訂閱者資料庫..."
# 注意：open5gs-dbctl 通常位於 /opt/open5gs/bin/ 或類似路徑，並且需要在 open5gs-mongo 容器內執行
# 這裡假設 open5gs-dbctl 已經在 PATH 中，或者需要提供完整路徑
# 並且，IMSI 應該是純數字，不帶 "imsi-" 前綴
docker exec -it open5gs-mongo bash -c "open5gs-dbctl add 999700000000001 465B5CE8B199B49FAA5F0A2EE238A6BC E8ED289DEBA952E4283B54E88E6183CA"
docker exec -it open5gs-mongo bash -c "open5gs-dbctl add 999700000000011 465B5CE8B199B49FAA5F0A2EE238A6BC E8ED289DEBA952E4283B54E88E6183CA"
docker exec -it open5gs-mongo bash -c "open5gs-dbctl add 999700000000012 465B5CE8B199B49FAA5F0A2EE238A6BC E8ED289DEBA952E4283B54E88E6183CA"
docker exec -it open5gs-mongo bash -c "open5gs-dbctl add 999700000000013 465B5CE8B199B49FAA5F0A2EE238A6BC E8ED289DEBA952E4283B54E88E6183CA"


# 4. 創建更新後的 UE 配置並更新 docker-compose.yml
echo "更新 docker-compose.yml 中的 UE 容器配置..."
cat > /home/sat/ntn-stack/updated_ue_config.txt << EOF
    ues1:
        image: gradiant/ueransim:3.2.6
        container_name: ntn-stack-ues1-1  # 指定一個固定的容器名稱
        command: ["ue", "--imsi", "imsi-999700000000001"]
        cap_add:
            - all  # 保留原有的權限
        privileged: true  # 保留特權模式
        networks:
            - open5gs-net  # 確保網絡連接
        depends_on:
            - gnb1
        # 添加額外的參數作為環境變量
        environment:
            GNB_HOSTNAME: gnb1
            APN: internet
            MCC: '999'
            MNC: '70'
            KEY: '465B5CE8B199B49FAA5F0A2EE238A6BC' # 與 MongoDB 資料一致
            OP_TYPE: OP                             # 由 OPC 改為 OP
            OP: 'E8ED289DEBA952E4283B54E88E6183CA'   # 與 MongoDB 資料一致
            SST: '1'
            SD: '0x010203' # 與 MongoDB 資料一致
            SIM_INSERTED: 'true'                     # 確保SIM卡被視為已插入
            NR_UE_LOG_LEVEL: 'debug'                 # 啟用詳細日誌以便排錯

    gnb2:
        image: gradiant/ueransim:3.2.6
        container_name: gnb2
        command:
            - gnb
        environment:
            AMF_HOSTNAME: amf
            GNB_HOSTNAME: gnb2
            TAC: '1'
            MCC: '999'
            MNC: '70'
            SST: '1'
            SD: '0x010203'
        cap_add:
            - NET_ADMIN
        networks:
            - open5gs-net
        depends_on:
            - amf

    ues2:
        image: gradiant/ueransim:3.2.6
        container_name: ntn-stack-ues2-1  # 指定一個固定的容器名稱
        command: ["ue", "--imsi", "imsi-999700000000011", "-n", "3"]
        cap_add:
            - all  # 保留原有的權限
        privileged: true  # 保留特權模式
        networks:
            - open5gs-net  # 確保網絡連接
        depends_on:
            - gnb2
        # 使用環境變量控制UE數量
        environment:
            GNB_HOSTNAME: gnb2
            APN: internet
            MSISDN: '0000000011'
            MCC: '999'
            MNC: '70'
            KEY: '465B5CE8B199B49FAA5F0A2EE238A6BC'
            OP_TYPE: OP # 由 OPC 改為 OP
            OP: 'E8ED289DEBA952E4283B54E88E6183CA'
            SST: '1'
            SD: '0x010203'
            SIM_INSERTED: 'true'             # 確保SIM卡被視為已插入
            NR_UE_LOG_LEVEL: 'debug'         # 啟用詳細日誌以便排錯
EOF

# 用 sed 命令將 docker-compose.yml 中的 UE 部分替換為新的配置
# 確保行號範圍正確，或者使用更可靠的標記來定位替換區域
# 這裡假設 gnb1 的定義在 ues1 之前，ues2 的定義在 gnb2 之後
# 並且 docker-compose.yml 的結構相對穩定

# 找到 ues1 開始的行號
UES1_START_LINE=$(grep -n "ues1:" /home/sat/ntn-stack/docker-compose.yml | cut -d: -f1)
# 找到 ues2 環境變數結束的下一行，作為 ues2 配置的結束標記 (假設 TZ 是 ues2 最後一個環境變數)
# 或者找到下一個服務的開始，例如 config-api
UES2_END_LINE=$(grep -n "config-api:" /home/sat/ntn-stack/docker-compose.yml | cut -d: -f1)
UES2_END_LINE=$((UES2_END_LINE - 1)) # 減1得到ues2的最後一行

if [ -n "$UES1_START_LINE" ] && [ -n "$UES2_END_LINE" ] && [ "$UES1_START_LINE" -lt "$UES2_END_LINE" ]; then
    sed -i "${UES1_START_LINE},${UES2_END_LINE}c\\" /home/sat/ntn-stack/docker-compose.yml
    sed -i "${UES1_START_LINE}r /home/sat/ntn-stack/updated_ue_config.txt" /home/sat/ntn-stack/docker-compose.yml
else
    echo "錯誤：無法在 docker-compose.yml 中定位 UE 配置。請手動檢查。"
fi

# 清理臨時文件
rm /home/sat/ntn-stack/updated_ue_config.txt

# 5. 重啟 UE 容器
echo "重啟 UE 容器..."
# 使用 docker compose (v2) 而不是 docker-compose (v1)
docker compose -f /home/sat/ntn-stack/docker-compose.yml up -d --remove-orphans ues1 ues2 gnb1 gnb2

echo "===== UE 註冊問題修復完成 ====="
echo "請使用 'docker logs ntn-stack-ues1-1' 和 'docker logs ntn-stack-ues2-1' 查看 UE 容器日誌"
