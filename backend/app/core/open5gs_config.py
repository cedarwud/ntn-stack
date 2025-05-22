"""
Open5GS MongoDB 配置
包含連接 MongoDB 所需的常量和訂閱者範本
"""

# MongoDB 連接 URI
MONGO_URI = "mongodb://localhost:27017/open5gs"

# 默認訂閱者配置模板
DEFAULT_SUBSCRIBER_CONFIG = {
    "imsi": "001010000000000",  # 將被覆蓋
    "security": {
        "k": "465B5CE8B199B49FAA5F0A2EE238A6BC",  # 將被覆蓋
        "amf": "8000",
        "op": None,
        "opc": "E8ED289DEBA952E4283B54E88E6183CA",  # 將被覆蓋
    },
    "ambr": {"downlink": {"value": 1, "unit": 3}, "uplink": {"value": 1, "unit": 3}},
    "slice_default": {
        "session": {
            "qos": {
                "index": 9,
                "arp": {
                    "priority_level": 8,
                    "pre_emption_capability": 1,
                    "pre_emption_vulnerability": 1,
                },
            },
            "ambr": {
                "downlink": {"value": 1, "unit": 3},
                "uplink": {"value": 1, "unit": 3},
            },
        }
    },
    "subscribed-rau-tau-timer": 12,
    "access_restriction_data": 32,
    "subscriber_status": 0,
    "network_access_mode": 0,
    "__v": 0,
}
