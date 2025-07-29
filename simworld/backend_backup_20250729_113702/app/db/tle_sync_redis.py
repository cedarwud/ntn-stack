"""
簡化的 TLE 同步服務，僅使用 Redis
移除了 PostgreSQL 依賴
"""

import logging
import aiohttp
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


async def synchronize_constellation_tles(
    constellation: str, 
    session_factory: Optional[Any], # 保持兼容性，但忽略此參數
    redis_client: Redis
) -> bool:
    """
    同步星座 TLE 數據到 Redis
    
    Args:
        constellation: 星座名稱 (starlink, kuiper 等)
        session_factory: PostgreSQL 會話工廠 (忽略，保持兼容性)
        redis_client: Redis 客戶端
        
    Returns:
        bool: 同步是否成功
    """
    if not redis_client:
        logger.error("Redis 客戶端未提供")
        return False
        
    try:
        logger.info(f"開始同步 {constellation.upper()} 衛星 TLE 數據...")
        
        # Celestrak TLE URLs
        tle_urls = {
            "starlink": "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle",
            "kuiper": "https://celestrak.org/NORAD/elements/gp.php?GROUP=kuiper&FORMAT=tle",
            "oneweb": "https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle"
        }
        
        if constellation not in tle_urls:
            logger.error(f"不支持的星座: {constellation}")
            return False
            
        url = tle_urls[constellation]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"下載 {constellation} TLE 數據失敗: HTTP {response.status}")
                    return False
                    
                tle_data = await response.text()
                
        # 解析 TLE 數據
        lines = tle_data.strip().split('\n')
        satellites = []
        
        for i in range(0, len(lines), 3):
            if i + 2 < len(lines):
                name = lines[i].strip()
                line1 = lines[i + 1].strip()
                line2 = lines[i + 2].strip()
                
                try:
                    # 提取 NORAD ID
                    norad_id = int(line1[2:7])
                    
                    satellite_data = {
                        "name": name,
                        "norad_id": norad_id,
                        "line1": line1,
                        "line2": line2,
                        "constellation": constellation,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    satellites.append(satellite_data)
                    
                except (ValueError, IndexError) as e:
                    logger.warning(f"跳過無效的 TLE 數據: {e}")
                    continue
        
        if not satellites:
            logger.warning(f"未找到有效的 {constellation} TLE 數據")
            return False
            
        # 儲存到 Redis
        redis_key = f"tle_data:{constellation}"
        await redis_client.set(
            redis_key, 
            json.dumps(satellites), 
            ex=86400 * 7  # 7 天過期
        )
        
        # 更新統計信息
        stats_key = f"tle_stats:{constellation}"
        stats = {
            "count": len(satellites),
            "last_updated": datetime.utcnow().isoformat(),
            "source": "celestrak"
        }
        await redis_client.set(stats_key, json.dumps(stats), ex=86400 * 7)
        
        logger.info(f"從 Celestrak 獲取了 {len(satellites)} 條 {constellation} 類別的 TLE 數據")
        logger.info(f"成功同步 {len(satellites)} 個 {constellation.upper()} 衛星 TLE 數據")
        
        return True
        
    except Exception as e:
        logger.error(f"同步 {constellation} TLE 數據時發生錯誤: {e}", exc_info=True)
        return False
