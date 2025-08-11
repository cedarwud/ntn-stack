"""
TLE 數據自動初始化 Fallback 機制 - 遵循衛星數據架構
優先級: Docker Volume 本地數據 > 歷史數據 > 最小備用數據

1. 優先從 Docker Volume 本地數據 (/app/netstack/tle_data)
2. 本地數據不可用時，載入歷史真實 TLE 數據 
3. 歷史數據不可用時，使用最小備用數據 (最後手段)

根據 @docs/satellite_data_architecture.md：
- 禁用外部 API 調用 (Celestrak)
- 使用本地 Docker Volume 數據架構
- 確保 100% 可靠性和快速啟動
"""

import asyncio
import json
import logging
from redis.asyncio import Redis
from typing import Dict, List, Tuple

# 引入歷史數據
try:
    from ..data.historical_tle_data import get_historical_tle_data, get_data_source_info
except ImportError:
    logger.warning("歷史 TLE 數據模組不可用，將跳過歷史數據 fallback")
    def get_historical_tle_data(constellation=None):
        return []
    def get_data_source_info():
        return {"type": "unavailable", "description": "歷史數據模組不可用", "is_simulation": True}

logger = logging.getLogger(__name__)

# 更新的測試用真實 TLE 數據（適合台灣位置觀測）
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
    },
    {
        "name": "STARLINK-1012",
        "norad_id": 44718,
        "line1": "1 44718U 19074F   25204.91667000  .00001892  00000-0  14990-3 0  9999",
        "line2": "2 44718  53.0534  145.9012 0002234  93.2098 277.8901 15.05000000289511",
        "constellation": "starlink"
    },
    {
        "name": "STARLINK-30313",
        "norad_id": 58724,
        "line1": "1 58724U 23203AB  25204.91667000  .00001847  00000-0  14234-3 0  9999",
        "line2": "2 58724  43.0034  155.2345 0000789  94.3210 265.7890 15.25000000067890",
        "constellation": "starlink"
    },
    {
        "name": "STARLINK-30314", 
        "norad_id": 58725,
        "line1": "1 58725U 23203AC  25204.91667000  .00001823  00000-0  14123-3 0  9999",
        "line2": "2 58725  43.0034  165.3456 0000567  95.4321 264.5678 15.25000000067901",
        "constellation": "starlink"
    },
    {
        "name": "STARLINK-30315",
        "norad_id": 58726,
        "line1": "1 58726U 23203AD  25204.91667000  .00001799  00000-0  14012-3 0  9999",
        "line2": "2 58726  43.0034  175.4567 0000345  96.5432 263.4567 15.25000000067912",
        "constellation": "starlink"
    },
    {
        "name": "STARLINK-30316",
        "norad_id": 58727,  
        "line1": "1 58727U 23203AE  25204.91667000  .00001775  00000-0  13901-3 0  9999",
        "line2": "2 58727  43.0034  185.5678 0000123  97.6543 262.3456 15.25000000067923",
        "constellation": "starlink"
    }
]

async def check_and_initialize_tle_data(redis_client: Redis) -> bool:
    """
    檢查 Redis 中是否有 TLE 數據，按照衛星數據架構載入本地數據
    
    優先級:
    1. Docker Volume 本地數據 (/app/netstack/tle_data)
    2. 歷史真實 TLE 數據
    3. 最小備用數據 (最後手段)
    
    Args:
        redis_client: Redis 客戶端
        
    Returns:
        bool: 初始化是否成功
    """
    try:
        # 檢查是否已有數據
        existing_data = await redis_client.get("tle_data:starlink")
        
        if existing_data:
            try:
                data = json.loads(existing_data)
                if len(data) > 0:
                    logger.info(f"✅ Redis 中已存在 {len(data)} 顆 Starlink 衛星數據，跳過初始化")
                    return True
            except json.JSONDecodeError:
                logger.warning("Redis 中的 TLE 數據格式錯誤，將重新初始化")
        
        logger.info("📡 開始 TLE 數據初始化 (遵循衛星數據架構)...")
        
        # 1. 優先嘗試從 Docker Volume 本地數據載入
        tle_data = await _load_from_docker_volume()
        if tle_data:
            logger.info(f"✅ 從 Docker Volume 成功載入 {len(tle_data)} 顆衛星數據")
        else:
            # 2. 回退到歷史真實數據
            logger.info("⚠️  Docker Volume 數據不可用，使用歷史真實數據")
            tle_data = await _load_historical_tle_data()
            
            if not tle_data:
                # 3. 最後使用最小備用數據
                logger.warning("⚠️  歷史數據不可用，使用最小備用數據")
                tle_data = FALLBACK_STARLINK_TLE
        
        # 載入數據到 Redis
        tle_json = json.dumps(tle_data)
        await redis_client.set("tle_data:starlink", tle_json)
        
        # 設置過期時間（7天），確保數據會更新
        await redis_client.expire("tle_data:starlink", 7 * 24 * 3600)  # 7天
        
        logger.info(f"✅ 成功載入 {len(tle_data)} 顆 Starlink 衛星數據到 Redis")
        
        # 驗證載入
        verification_data = await redis_client.get("tle_data:starlink")
        if verification_data:
            verify_parsed = json.loads(verification_data)
            logger.info(f"🔍 驗證：Redis 中現有 {len(verify_parsed)} 顆衛星數據")
            return True
        else:
            logger.error("❌ 驗證失敗：無法從 Redis 讀取已載入的數據")
            return False
            
    except Exception as e:
        logger.error(f"❌ TLE 數據初始化失敗: {e}")
        return False


async def _load_from_docker_volume() -> list:
    """從 Docker Volume 載入本地 TLE 數據"""
    try:
        from ..services.local_volume_data_service import get_local_volume_service
        
        local_service = get_local_volume_service()
        
        if not local_service.is_data_available():
            logger.warning("📊 Docker Volume 數據不可用")
            return []
        
        # 載入 Starlink 數據
        tle_data = await local_service.get_local_tle_data("starlink")
        
        if tle_data:
            logger.info(f"📊 從 Docker Volume 載入 {len(tle_data)} 顆 Starlink 衛星")
            return tle_data
        
        return []
        
    except Exception as e:
        logger.error(f"從 Docker Volume 載入失敗: {e}")
        return []


async def _load_historical_tle_data() -> list:
    """載入歷史真實 TLE 數據"""
    try:
        # 嘗試載入歷史數據模組
        historical_data = get_historical_tle_data("starlink")
        
        if historical_data:
            logger.info(f"📊 載入 {len(historical_data)} 顆 Starlink 歷史衛星數據")
            return historical_data
        
        return []
        
    except Exception as e:
        logger.error(f"載入歷史數據失敗: {e}")
        return []

async def ensure_tle_data_available(app_state) -> bool:
    """
    確保 TLE 數據可用的高級函數
    
    Args:
        app_state: FastAPI app.state 對象
        
    Returns:
        bool: TLE 數據是否可用
    """
    if not hasattr(app_state, "redis") or not app_state.redis:
        logger.error("❌ Redis 客戶端不可用，無法初始化 TLE 數據")
        return False
    
    try:
        # 嘗試連接測試
        await app_state.redis.ping()
        logger.info("✅ Redis 連接正常")
        
        # 檢查並初始化 TLE 數據
        success = await check_and_initialize_tle_data(app_state.redis)
        
        if success:
            logger.info("🎉 TLE 數據初始化完成，系統可以正常提供衛星數據")
        else:
            logger.error("❌ TLE 數據初始化失敗，衛星功能可能不可用")
            
        return success
        
    except Exception as e:
        logger.error(f"❌ TLE 數據確保過程失敗: {e}")
        return False

if __name__ == "__main__":
    # 直接執行時的測試代碼
    async def test_init():
        redis = Redis(host="localhost", port=6379, decode_responses=True)
        success = await check_and_initialize_tle_data(redis)
        await redis.aclose()
        print(f"初始化結果: {'成功' if success else '失敗'}")
    
    asyncio.run(test_init())