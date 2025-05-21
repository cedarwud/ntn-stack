// /scripts/mongo_init.js

// 切換到open5gs數據庫
db = db.getSiblingDB('open5gs');

// 清空現有訂閱者
db.subscribers.deleteMany({});

// 添加多個訂閱者
const subscribers = [
  {
    "imsi": "999700000000001",
    "subscribed_rau_tau_timer": 12,
    "network_access_mode": 2,
    "subscriber_status": 0,
    "access_restriction_data": 32,
    "security": {
      "k": "465B5CE8B199B49FAA5F0A2EE238A6BC",
      "opc": "E8ED289DEBA952E4283B54E88E6183CA",
      "amf": "8000",
      "op": null
    },
    "ambr": {
      "uplink": { "value": 1, "unit": 3 },
      "downlink": { "value": 1, "unit": 3 }
    },
    "slice": [
      {
        "sst": 1,
        "default_indicator": true,
        "session": [
          {
            "name": "internet",
            "type": 3,
            "qos": {
              "index": 9,
              "arp": {
                "priority_level": 8,
                "pre_emption_capability": 1,
                "pre_emption_vulnerability": 1
              }
            },
            "ambr": {
              "uplink": { "value": 1, "unit": 3 },
              "downlink": { "value": 1, "unit": 3 }
            }
          }
        ]
      }
    ]
  },
  {
    "imsi": "999700000000002",
    "subscribed_rau_tau_timer": 12,
    "network_access_mode": 2,
    "subscriber_status": 0,
    "access_restriction_data": 32,
    "security": {
      "k": "465B5CE8B199B49FAA5F0A2EE238A6BC",
      "opc": "E8ED289DEBA952E4283B54E88E6183CA",
      "amf": "8000",
      "op": null
    },
    "ambr": {
      "uplink": { "value": 1, "unit": 3 },
      "downlink": { "value": 1, "unit": 3 }
    },
    "slice": [
      {
        "sst": 1,
        "default_indicator": true,
        "session": [
          {
            "name": "internet",
            "type": 3,
            "qos": {
              "index": 9,
              "arp": {
                "priority_level": 8,
                "pre_emption_capability": 1,
                "pre_emption_vulnerability": 1
              }
            },
            "ambr": {
              "uplink": { "value": 1, "unit": 3 },
              "downlink": { "value": 1, "unit": 3 }
            }
          }
        ]
      }
    ]
  },
  {
    "imsi": "999700000000003",
    "subscribed_rau_tau_timer": 12,
    "network_access_mode": 2,
    "subscriber_status": 0,
    "access_restriction_data": 32,
    "security": {
      "k": "465B5CE8B199B49FAA5F0A2EE238A6BC",
      "opc": "E8ED289DEBA952E4283B54E88E6183CA",
      "amf": "8000",
      "op": null
    },
    "ambr": {
      "uplink": { "value": 1, "unit": 3 },
      "downlink": { "value": 1, "unit": 3 }
    },
    "slice": [
      {
        "sst": 1,
        "default_indicator": true,
        "session": [
          {
            "name": "internet",
            "type": 3,
            "qos": {
              "index": 9,
              "arp": {
                "priority_level": 8,
                "pre_emption_capability": 1,
                "pre_emption_vulnerability": 1
              }
            },
            "ambr": {
              "uplink": { "value": 1, "unit": 3 },
              "downlink": { "value": 1, "unit": 3 }
            }
          }
        ]
      }
    ]
  },
  {
    "imsi": "999700000000011",
    "subscribed_rau_tau_timer": 12,
    "network_access_mode": 2,
    "subscriber_status": 0,
    "access_restriction_data": 32,
    "security": {
      "k": "465B5CE8B199B49FAA5F0A2EE238A6BC",
      "opc": "E8ED289DEBA952E4283B54E88E6183CA",
      "amf": "8000",
      "op": null
    },
    "ambr": {
      "uplink": { "value": 1, "unit": 3 },
      "downlink": { "value": 1, "unit": 3 }
    },
    "slice": [
      {
        "sst": 1,
        "default_indicator": true,
        "session": [
          {
            "name": "internet",
            "type": 3,
            "qos": {
              "index": 9,
              "arp": {
                "priority_level": 8,
                "pre_emption_capability": 1,
                "pre_emption_vulnerability": 1
              }
            },
            "ambr": {
              "uplink": { "value": 1, "unit": 3 },
              "downlink": { "value": 1, "unit": 3 }
            }
          }
        ]
      }
    ]
  },
  {
    "imsi": "999700000000012",
    "subscribed_rau_tau_timer": 12,
    "network_access_mode": 2,
    "subscriber_status": 0,
    "access_restriction_data": 32,
    "security": {
      "k": "465B5CE8B199B49FAA5F0A2EE238A6BC",
      "opc": "E8ED289DEBA952E4283B54E88E6183CA",
      "amf": "8000",
      "op": null
    },
    "ambr": {
      "uplink": { "value": 1, "unit": 3 },
      "downlink": { "value": 1, "unit": 3 }
    },
    "slice": [
      {
        "sst": 1,
        "default_indicator": true,
        "session": [
          {
            "name": "internet",
            "type": 3,
            "qos": {
              "index": 9,
              "arp": {
                "priority_level": 8,
                "pre_emption_capability": 1,
                "pre_emption_vulnerability": 1
              }
            },
            "ambr": {
              "uplink": { "value": 1, "unit": 3 },
              "downlink": { "value": 1, "unit": 3 }
            }
          }
        ]
      }
    ]
  },
  {
    "imsi": "999700000000013",
    "subscribed_rau_tau_timer": 12,
    "network_access_mode": 2,
    "subscriber_status": 0,
    "access_restriction_data": 32,
    "security": {
      "k": "465B5CE8B199B49FAA5F0A2EE238A6BC",
      "opc": "E8ED289DEBA952E4283B54E88E6183CA",
      "amf": "8000",
      "op": null
    },
    "ambr": {
      "uplink": { "value": 1, "unit": 3 },
      "downlink": { "value": 1, "unit": 3 }
    },
    "slice": [
      {
        "sst": 1,
        "default_indicator": true,
        "session": [
          {
            "name": "internet",
            "type": 3,
            "qos": {
              "index": 9,
              "arp": {
                "priority_level": 8,
                "pre_emption_capability": 1,
                "pre_emption_vulnerability": 1
              }
            },
            "ambr": {
              "uplink": { "value": 1, "unit": 3 },
              "downlink": { "value": 1, "unit": 3 }
            }
          }
        ]
      }
    ]
  }
];

// 插入所有訂閱者
db.subscribers.insertMany(subscribers);

// 顯示訂閱者數量
print("已註冊訂閱者數量: " + db.subscribers.countDocuments());

// 顯示訂閱者列表
print("訂閱者列表：");
db.subscribers.find().forEach(function (doc) {
  print("IMSI: " + doc.imsi);
}); 