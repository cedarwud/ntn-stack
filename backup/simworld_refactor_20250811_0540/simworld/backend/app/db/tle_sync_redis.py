"""
簡化的 TLE 同步服務，僅使用 Redis
支援 NetStack 本地文件和 Celestrak 備用源
"""

import logging
import aiohttp
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime
from redis.asyncio import Redis
from pathlib import Path

logger = logging.getLogger(__name__)


async def sync_netstack_tle_to_redis(
    constellation: str, 
    redis_client: Redis,
    netstack_tle_base_path: str = "/app/netstack/tle_data"
) -> bool:
    """將 NetStack TLE 數據文件同步到 Redis"""
    try:
        logger.info(f"開始從 NetStack 同步 {constellation} TLE 數據到 Redis")
        
        # 檢查 NetStack 最新 TLE 文件
        tle_dir = Path(f"{netstack_tle_base_path}/{constellation}/tle")
        tle_files = sorted(tle_dir.glob(f"{constellation}_*.tle"), reverse=True)
        
        if not tle_files:
            logger.error(f"NetStack 找不到 {constellation} TLE 文件")
            return False
        
        latest_file = tle_files[0]
        logger.info(f"處理文件: {latest_file}")
        
        # 解析 TLE 數據
        satellites = []
        with open(latest_file, 'r') as f:
            lines = f.readlines()
        
        for i in range(0, len(lines), 3):
            if i + 2 < len(lines):
                name = lines[i].strip()
                line1 = lines[i + 1].strip()
                line2 = lines[i + 2].strip()
                
                try:
                    norad_id = int(line1[2:7])
                    satellite_data = {
                        "name": name,
                        "norad_id": norad_id,
                        "line1": line1,
                        "line2": line2,
                        "constellation": constellation,
                        "updated_at": datetime.utcnow().isoformat(),
                        "source": "netstack_local_file",
                        "file_path": str(latest_file)
                    }
                    satellites.append(satellite_data)
                except (ValueError, IndexError) as e:
                    logger.warning(f"解析 TLE 失敗: {e}")
                    continue
        
        if not satellites:
            logger.warning(f"沒有找到有效的 {constellation} 衛星數據")
            return False
        
        # 儲存到 Redis
        redis_key = f"netstack_tle_data:{constellation}"
        await redis_client.set(
            redis_key,
            json.dumps(satellites),
            ex=86400 * 3  # 3天過期
        )
        
        # 儲存統計資訊
        stats_key = f"netstack_tle_stats:{constellation}"
        stats = {
            "count": len(satellites),
            "last_updated": datetime.utcnow().isoformat(),
            "source": "netstack_local_file",
            "file_path": str(latest_file),
            "data_freshness": "real_time"
        }
        await redis_client.set(stats_key, json.dumps(stats), ex=86400 * 3)
        
        logger.info(f"成功同步 {len(satellites)} 個 {constellation} 衛星到 Redis")
        return True
        
    except Exception as e:
        logger.error(f"NetStack 到 Redis 同步失敗: {e}", exc_info=True)
        return False


async def synchronize_constellation_tles(
    constellation: str, 
    session_factory: Optional[Any], # 保持兼容性，但忽略此參數
    redis_client: Redis
) -> bool:
    """
    同步星座 TLE 數據到 Redis - 優先使用 NetStack 本地文件
    
    Args:
        constellation: 星座名稱 (starlink, oneweb 等)
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

        # 優先使用 NetStack 本地文件
        success = await sync_netstack_tle_to_redis(constellation, redis_client)
        if success:
            return True

        # 如果 NetStack 同步失敗，回退到 Celestrak
        logger.warning(f"NetStack 同步失敗，回退到 Celestrak 獲取 {constellation} 數據")
        
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
                        "updated_at": datetime.utcnow().isoformat(),
                        "source": "celestrak_fallback"
                    }
                    satellites.append(satellite_data)
                    
                except (ValueError, IndexError) as e:
                    logger.warning(f"跳過無效的 TLE 數據: {e}")
                    continue
        
        if not satellites:
            logger.warning(f"未找到有效的 {constellation} TLE 數據")
            return False
            
        # 儲存到 Redis (使用原始 key 格式保持兼容性)
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
            "source": "celestrak_fallback"
        }
        await redis_client.set(stats_key, json.dumps(stats), ex=86400 * 7)
        
        logger.info(f"從 Celestrak 獲取了 {len(satellites)} 條 {constellation} 類別的 TLE 數據")
        logger.info(f"成功同步 {len(satellites)} 個 {constellation.upper()} 衛星 TLE 數據")
        
        return True
        
    except Exception as e:
        logger.error(f"同步 {constellation} TLE 數據時發生錯誤: {e}", exc_info=True)
        return False
