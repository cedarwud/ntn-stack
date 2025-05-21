// /scripts/mongo_init.js

// 切換到open5gs數據庫
db = db.getSiblingDB('open5gs');

// 創建訂閱者集合，如果不存在
if (!db.getCollectionNames().includes('subscribers')) {
  db.createCollection('subscribers');
}

// 創建帳戶集合，如果不存在
if (!db.getCollectionNames().includes('accounts')) {
  db.createCollection('accounts');
}

// 檢查是否已有管理員帳戶
const adminExists = db.accounts.findOne({ "username": "admin" });
if (!adminExists) {
  // 創建默認管理員帳戶
  db.accounts.insert({
    username: "admin",
    password: "$2a$10$vH2n2GyjR1WLpSz8zSl7eesVEUG3nKF/vAFJl.ZOA1YOu8FnYh9sm", // 密碼: 1423
    roles: ["admin"],
    salt: "vH2n2GyjR1WLpSz8zSl7eee",
  });
  print("已創建默認管理員帳戶: admin/1423");
}

// 檢查是否已有測試訂閱者
const subscribersExist = db.subscribers.countDocuments({});
if (subscribersExist === 0) {
  // 添加默認測試訂閱者
  // IMSI: 999700000000001, 密鑰: 8baf473f2f8fd09487cccbd7097c6862, OP/OPC: 8e27b6af0e692e750f32667a3b14605d
  db.subscribers.insert({
    imsi: "999700000000001",
    msisdn: ["1122334455"],
    imeisv: "4370816125816151",
    mme_host: ["open5gs-mme"],
    mme_realm: ["open5gs.org"],
    purge_flag: false,
    security: {
      k: "8baf473f2f8fd09487cccbd7097c6862",
      op: "8e27b6af0e692e750f32667a3b14605d",
      opc: null,
      amf: "8000",
      sqn: 25235,
    },
    ambr: {
      downlink: 1024000,
      uplink: 1024000
    },
    slice: [{
      sst: 1,
      sd: "010203",
      default_indicator: true,
      session: [{
        name: "internet",
        type: 3,
        "qos": {
          "index": 9,
          "arp": {
            "priority_level": 8,
            "pre_emption_capability": 1,
            "pre_emption_vulnerability": 1
          }
        },
        ambr: {
          "downlink": 1024000,
          "uplink": 1024000
        },
        "pcc_rule": [],
        "_id": new ObjectId()
      }],
      _id: new ObjectId()
    }],
    access_restriction_data: 32,
    subscriber_status: 0,
    network_access_mode: 0,
    subscribed_rau_tau_timer: 12,
    __v: 0
  });

  // 添加更多測試訂閱者，從IMSI: 999700000000002 ~ 999700000000006
  let baseImsi = "99970000000000";
  for (let i = 2; i <= 6; i++) {
    let imsi = baseImsi + i;
    db.subscribers.insert({
      imsi: imsi,
      msisdn: ["1122334455"],
      imeisv: "4370816125816151",
      mme_host: ["open5gs-mme"],
      mme_realm: ["open5gs.org"],
      purge_flag: false,
      security: {
        k: "8baf473f2f8fd09487cccbd7097c6862",
        op: "8e27b6af0e692e750f32667a3b14605d",
        opc: null,
        amf: "8000",
        sqn: 25235,
      },
      ambr: {
        downlink: 1024000,
        uplink: 1024000
      },
      slice: [{
        sst: 1,
        sd: "010203",
        default_indicator: true,
        session: [{
          name: "internet",
          type: 3,
          "qos": {
            "index": 9,
            "arp": {
              "priority_level": 8,
              "pre_emption_capability": 1,
              "pre_emption_vulnerability": 1
            }
          },
          ambr: {
            "downlink": 1024000,
            "uplink": 1024000
          },
          "pcc_rule": [],
          "_id": new ObjectId()
        }],
        _id: new ObjectId()
      }],
      access_restriction_data: 32,
      subscriber_status: 0,
      network_access_mode: 0,
      subscribed_rau_tau_timer: 12,
      __v: 0
    });
  }

  print("已創建6個測試訂閱者 (IMSI: 999700000000001 ~ 999700000000006)");
}

// 創建索引
db.subscribers.createIndex({ "imsi": 1 }, { unique: true });
db.accounts.createIndex({ "username": 1 }, { unique: true });

print("MongoDB初始化完成!"); 