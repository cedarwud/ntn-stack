"""
Open5GS 相關配置
"""

# MongoDB 連接配置
MONGO_URI = "mongodb://mongo:27017/open5gs"

# 訂閱者預設配置
DEFAULT_SUBSCRIBER_CONFIG = {
    "subscribed_rau_tau_timer": 12,
    "network_access_mode": 2,
    "subscriber_status": 0,
    "access_restriction_data": 32,
    "security": {"amf": "8000", "op": None},
    "ambr": {"uplink": {"value": 1, "unit": 3}, "downlink": {"value": 1, "unit": 3}},
    "slice_default": {
        "sst": 1,
        "default_indicator": True,
        "session": {
            "name": "internet",
            "type": 3,
            "qos": {
                "index": 9,
                "arp": {
                    "priority_level": 8,
                    "pre_emption_capability": 1,
                    "pre_emption_vulnerability": 1,
                },
            },
            "ambr": {
                "uplink": {"value": 1, "unit": 3},
                "downlink": {"value": 1, "unit": 3},
            },
        },
    },
}

# API 路由配置
API_PREFIX = "/api/v1/open5gs"
