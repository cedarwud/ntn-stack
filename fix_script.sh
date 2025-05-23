#!/bin/bash

# 創建新的UE配置，以替換原有的配置
cat > /home/sat/ntn-stack/ue_config.txt << EOF
    ues1:
        image: gradiant/ueransim:3.2.6
        container_name: ntn-stack-ues1-1  # 指定一個固定的容器名稱
        # 使用單行shell命令
        command: /bin/bash -c "sleep 20 && /entrypoint.sh ue --imsi imsi-999700000000001"
        cap_add:
            - all  # 保留原有的權限
        privileged: true  # 保留特權模式
        networks:
            - open5gs-net  # 確保網絡連接
        depends_on:
            - gnb1
            - subscriber-init  # 確保訂閱者已註冊
        # 添加額外的參數作為環境變量
        environment:
            GNB_HOSTNAME: gnb1
            APN: internet
            MCC: '999'
            MNC: '70'
            KEY: '465B5CE8B199B49FAA5F0A2EE238A6BC' # 與 MongoDB 資料一致
            OP_TYPE: OPC                             # 使用OPC而非OP
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
        # 使用單行shell命令
        command: /bin/bash -c "sleep 30 && /entrypoint.sh ue --imsi imsi-999700000000011 -n 3"
        cap_add:
            - all  # 保留原有的權限
        privileged: true  # 保留特權模式
        networks:
            - open5gs-net  # 確保網絡連接
        depends_on:
            - gnb2
            - subscriber-init  # 確保訂閱者已註冊
        # 使用環境變量控制UE數量
        environment:
            GNB_HOSTNAME: gnb2
            APN: internet
            MSISDN: '0000000011'
            MCC: '999'
            MNC: '70'
            KEY: '465B5CE8B199B49FAA5F0A2EE238A6BC'
            OP_TYPE: OPC
            OP: 'E8ED289DEBA952E4283B54E88E6183CA'
            SST: '1'
            SD: '0x010203'
            SIM_INSERTED: 'true'             # 確保SIM卡被視為已插入
            NR_UE_LOG_LEVEL: 'debug'         # 啟用詳細日誌以便排錯
EOF

# 用sed命令將docker-compose.yml中的UE部分替換為新的配置
sed -i '314,416c\\' /home/sat/ntn-stack/docker-compose.yml

# 將新的配置插入到docker-compose.yml中
sed -i '314r /home/sat/ntn-stack/ue_config.txt' /home/sat/ntn-stack/docker-compose.yml

# 清理臨時文件
rm /home/sat/ntn-stack/ue_config.txt

echo "已完成docker-compose.yml中UE服務部分的更新"
