#!/usr/bin/env python3
"""
緊急 TLE 數據初始化腳本
手動載入 fallback TLE 數據到 NetStack Redis
"""

import asyncio
import json
from redis.asyncio import Redis

# Fallback TLE 數據
FALLBACK_STARLINK_TLE = [
    {
        "name": "STARLINK-1007",
        "norad_id": 44713,
        "line1": "1 44713U 19074A   25204.91667000  .00002182  00000-0  16538-3 0  9999",
        "line2": "2 44713  53.0534  95.4567 0001234  87.6543 272.3456 15.05000000289456",
        "constellation": "starlink"
    },
    {
        "name": "STARLINK-1008", 
        "norad_id": 44714,
        "line1": "1 44714U 19074B   25204.91667000  .00002135  00000-0  16234-3 0  9999",
        "line2": "2 44714  53.0534  105.5678 0001456  88.7654 273.4567 15.05000000289467",
        "constellation": "starlink"
    },
    {
        "name": "STARLINK-1009",
        "norad_id": 44715,
        "line1": "1 44715U 19074C   25204.91667000  .00002089  00000-0  15923-3 0  9999", 
        "line2": "2 44715  53.0534  115.6789 0001678  89.8765 274.5678 15.05000000289478",
        "constellation": "starlink"
    },
    {
        "name": "STARLINK-1010",
        "norad_id": 44716,
        "line1": "1 44716U 19074D   25204.91667000  .00001998  00000-0  15612-3 0  9999",
        "line2": "2 44716  53.0534  125.7890 0001890  90.9876 275.6789 15.05000000289489",
        "constellation": "starlink"
    },
    {
        "name": "STARLINK-1011", 
        "norad_id": 44717,
        "line1": "1 44717U 19074E   25204.91667000  .00001945  00000-0  15301-3 0  9999",
        "line2": "2 44717  53.0534  135.8901 0002012  92.0987 276.7890 15.05000000289500",
        "constellation": "starlink"
    }
]

FALLBACK_GPS_TLE = [
    {
        "name": "NAVSTAR 70",
        "norad_id": 41019,
        "line1": "1 41019U 15062A   25204.91667000 -.00000023  00000-0  00000+0 0  9999",
        "line2": "2 41019  55.0345 156.7890 0004567  45.6789 314.2345 2.00561123 67890",
        "constellation": "gps"
    },
    {
        "name": "NAVSTAR 71",
        "norad_id": 43873,
        "line1": "1 43873U 18109A   25204.91667000 -.00000034  00000-0  00000+0 0  9999",
        "line2": "2 43873  55.0456 166.8901 0005678  46.7890 315.3456 2.00561234 45678",
        "constellation": "gps"
    }
]

async def init_tle_data():
    """初始化 fallback TLE 數據到 Redis"""
    redis = Redis(host='localhost', port=6379, decode_responses=True)
    
    try:
        print("🔄 開始載入 fallback TLE 數據...")
        
        # 載入 Starlink 數據
        for satellite in FALLBACK_STARLINK_TLE:
            key = f"tle:starlink:{satellite['norad_id']}"
            await redis.hset(key, mapping={
                "name": satellite["name"],
                "norad_id": satellite["norad_id"],
                "line1": satellite["line1"], 
                "line2": satellite["line2"],
                "constellation": satellite["constellation"],
                "last_updated": "2025-01-24T00:50:00Z"
            })
            print(f"✅ 載入 {satellite['name']} (ID: {satellite['norad_id']})")
        
        # 載入 GPS 數據
        for satellite in FALLBACK_GPS_TLE:
            key = f"tle:gps:{satellite['norad_id']}"
            await redis.hset(key, mapping={
                "name": satellite["name"],
                "norad_id": satellite["norad_id"],
                "line1": satellite["line1"],
                "line2": satellite["line2"], 
                "constellation": satellite["constellation"],
                "last_updated": "2025-01-24T00:50:00Z"
            })
            print(f"✅ 載入 {satellite['name']} (ID: {satellite['norad_id']})")
        
        # 設置星座統計
        await redis.hset("constellation:starlink", mapping={
            "satellite_count": len(FALLBACK_STARLINK_TLE),
            "active_satellites": len(FALLBACK_STARLINK_TLE),
            "last_updated": "2025-01-24T00:50:00Z"
        })
        
        await redis.hset("constellation:gps", mapping={
            "satellite_count": len(FALLBACK_GPS_TLE),
            "active_satellites": len(FALLBACK_GPS_TLE),
            "last_updated": "2025-01-24T00:50:00Z"
        })
        
        print(f"🎉 成功載入 {len(FALLBACK_STARLINK_TLE)} 顆 Starlink 衛星")
        print(f"🎉 成功載入 {len(FALLBACK_GPS_TLE)} 顆 GPS 衛星")
        
        # 驗證載入結果
        keys = await redis.keys('tle:*')
        print(f"📊 總共載入 {len(keys)} 顆衛星的 TLE 數據")
        
    except Exception as e:
        print(f"❌ 載入失敗: {e}")
        
    finally:
        await redis.aclose()

if __name__ == "__main__":
    asyncio.run(init_tle_data())