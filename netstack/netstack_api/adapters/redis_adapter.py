"""
Redis 適配器

處理快取、統計資料和即時狀態管理
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import redis.asyncio as redis
import structlog

logger = structlog.get_logger(__name__)


class RedisAdapter:
    """Redis 快取適配器"""
    
    def __init__(self, connection_string: str):
        """
        初始化 Redis 適配器
        
        Args:
            connection_string: Redis 連接字串
        """
        self.connection_string = connection_string
        self.client: Optional[redis.Redis] = None
        
    async def connect(self) -> None:
        """建立 Redis 連接"""
        try:
            self.client = redis.from_url(
                self.connection_string,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # 測試連接
            await self.client.ping()
            
            logger.info("Redis 連接成功", connection_string=self.connection_string)
            
        except Exception as e:
            logger.error("Redis 連接失敗", error=str(e))
            raise
            
    async def disconnect(self) -> None:
        """關閉 Redis 連接"""
        if self.client:
            await self.client.close()
            logger.info("Redis 連接已關閉")
            
    async def health_check(self) -> Dict[str, Any]:
        """檢查 Redis 健康狀態"""
        try:
            start_time = datetime.now()
            await self.client.ping()
            response_time = (datetime.now() - start_time).total_seconds()
            
            info = await self.client.info()
            
            return {
                "status": "healthy",
                "response_time": response_time,
                "version": info.get("redis_version"),
                "memory_usage": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients")
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
            
    async def cache_ue_info(
        self, 
        imsi: str, 
        ue_info: Dict[str, Any], 
        ttl: int = 300
    ) -> None:
        """
        快取 UE 資訊
        
        Args:
            imsi: UE IMSI
            ue_info: UE 資訊
            ttl: 快取存活時間 (秒)
        """
        try:
            key = f"ue:info:{imsi}"
            await self.client.setex(
                key,
                ttl,
                json.dumps(ue_info, default=str)
            )
            logger.debug("UE 資訊已快取", imsi=imsi, ttl=ttl)
        except Exception as e:
            logger.error("快取 UE 資訊失敗", imsi=imsi, error=str(e))
            
    async def get_cached_ue_info(self, imsi: str) -> Optional[Dict[str, Any]]:
        """
        取得快取的 UE 資訊
        
        Args:
            imsi: UE IMSI
            
        Returns:
            快取的 UE 資訊，如果不存在則回傳 None
        """
        try:
            key = f"ue:info:{imsi}"
            cached_data = await self.client.get(key)
            
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error("取得快取 UE 資訊失敗", imsi=imsi, error=str(e))
            return None
            
    async def update_ue_stats(
        self, 
        imsi: str, 
        stats: Dict[str, Any]
    ) -> None:
        """
        更新 UE 統計資料
        
        Args:
            imsi: UE IMSI
            stats: 統計資料
        """
        try:
            key = f"ue:stats:{imsi}"
            
            # 取得現有統計資料
            existing_stats = await self.client.hgetall(key)
            
            # 更新統計資料
            updated_stats = {**existing_stats, **stats}
            updated_stats["last_updated"] = datetime.now().isoformat()
            
            await self.client.hset(key, mapping=updated_stats)
            
            # 設定過期時間 (24 小時)
            await self.client.expire(key, 86400)
            
            logger.debug("UE 統計資料已更新", imsi=imsi)
        except Exception as e:
            logger.error("更新 UE 統計資料失敗", imsi=imsi, error=str(e))
            
    async def get_ue_stats(self, imsi: str) -> Optional[Dict[str, Any]]:
        """
        取得 UE 統計資料
        
        Args:
            imsi: UE IMSI
            
        Returns:
            UE 統計資料
        """
        try:
            key = f"ue:stats:{imsi}"
            stats = await self.client.hgetall(key)
            
            if stats:
                # 轉換數值類型
                for field in ["connection_time", "bytes_uploaded", "bytes_downloaded", "slice_switches"]:
                    if field in stats:
                        stats[field] = int(stats[field])
                        
                if "rtt_ms" in stats:
                    stats["rtt_ms"] = float(stats["rtt_ms"])
                    
                return stats
            return None
        except Exception as e:
            logger.error("取得 UE 統計資料失敗", imsi=imsi, error=str(e))
            return None
            
    async def record_slice_switch(
        self, 
        imsi: str, 
        from_slice: str, 
        to_slice: str
    ) -> None:
        """
        記錄 Slice 切換事件
        
        Args:
            imsi: UE IMSI
            from_slice: 原始 Slice
            to_slice: 目標 Slice
        """
        try:
            # 記錄切換歷史
            switch_record = {
                "imsi": imsi,
                "from_slice": from_slice,
                "to_slice": to_slice,
                "timestamp": datetime.now().isoformat()
            }
            
            # 加入切換歷史列表
            history_key = f"slice:switches:{imsi}"
            await self.client.lpush(
                history_key,
                json.dumps(switch_record)
            )
            
            # 只保留最近 100 筆記錄
            await self.client.ltrim(history_key, 0, 99)
            
            # 更新統計計數器
            stats_key = f"ue:stats:{imsi}"
            await self.client.hincrby(stats_key, "slice_switches", 1)
            
            # 全域統計
            global_key = f"global:slice_switches:{from_slice}:{to_slice}"
            await self.client.incr(global_key)
            await self.client.expire(global_key, 86400)  # 24 小時過期
            
            logger.info(
                "Slice 切換已記錄",
                imsi=imsi,
                from_slice=from_slice,
                to_slice=to_slice
            )
        except Exception as e:
            logger.error(
                "記錄 Slice 切換失敗",
                imsi=imsi,
                from_slice=from_slice,
                to_slice=to_slice,
                error=str(e)
            )
            
    async def get_slice_switch_history(
        self, 
        imsi: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        取得 Slice 切換歷史
        
        Args:
            imsi: UE IMSI
            limit: 回傳記錄數量限制
            
        Returns:
            切換歷史列表
        """
        try:
            key = f"slice:switches:{imsi}"
            history_data = await self.client.lrange(key, 0, limit - 1)
            
            history = []
            for record_str in history_data:
                try:
                    record = json.loads(record_str)
                    history.append(record)
                except json.JSONDecodeError:
                    continue
                    
            return history
        except Exception as e:
            logger.error("取得 Slice 切換歷史失敗", imsi=imsi, error=str(e))
            return []
            
    async def update_rtt_measurement(
        self, 
        imsi: str, 
        rtt_ms: float, 
        slice_type: str
    ) -> None:
        """
        更新 RTT 測量結果
        
        Args:
            imsi: UE IMSI
            rtt_ms: RTT 延遲 (毫秒)
            slice_type: Slice 類型
        """
        try:
            # 更新 UE 統計
            stats_key = f"ue:stats:{imsi}"
            await self.client.hset(stats_key, mapping={
                "rtt_ms": rtt_ms,
                "last_rtt_test": datetime.now().isoformat()
            })
            
            # 記錄 Slice 類型的 RTT 統計
            slice_rtt_key = f"slice:rtt:{slice_type}"
            await self.client.lpush(slice_rtt_key, rtt_ms)
            await self.client.ltrim(slice_rtt_key, 0, 999)  # 保留最近 1000 筆
            
            logger.debug(
                "RTT 測量已更新",
                imsi=imsi,
                rtt_ms=rtt_ms,
                slice_type=slice_type
            )
        except Exception as e:
            logger.error(
                "更新 RTT 測量失敗",
                imsi=imsi,
                rtt_ms=rtt_ms,
                slice_type=slice_type,
                error=str(e)
            )
            
    async def get_slice_rtt_stats(self, slice_type: str) -> Dict[str, float]:
        """
        取得 Slice RTT 統計
        
        Args:
            slice_type: Slice 類型
            
        Returns:
            RTT 統計資料 (平均值、最小值、最大值)
        """
        try:
            key = f"slice:rtt:{slice_type}"
            rtt_values = await self.client.lrange(key, 0, -1)
            
            if not rtt_values:
                return {"avg": 0.0, "min": 0.0, "max": 0.0, "count": 0}
                
            rtt_floats = [float(val) for val in rtt_values]
            
            return {
                "avg": sum(rtt_floats) / len(rtt_floats),
                "min": min(rtt_floats),
                "max": max(rtt_floats),
                "count": len(rtt_floats)
            }
        except Exception as e:
            logger.error("取得 Slice RTT 統計失敗", slice_type=slice_type, error=str(e))
            return {"avg": 0.0, "min": 0.0, "max": 0.0, "count": 0}
            
    async def set_ue_online_status(self, imsi: str, online: bool) -> None:
        """
        設定 UE 線上狀態
        
        Args:
            imsi: UE IMSI
            online: 是否線上
        """
        try:
            key = f"ue:online:{imsi}"
            
            if online:
                await self.client.setex(key, 300, "1")  # 5 分鐘過期
            else:
                await self.client.delete(key)
                
            logger.debug("UE 線上狀態已更新", imsi=imsi, online=online)
        except Exception as e:
            logger.error("設定 UE 線上狀態失敗", imsi=imsi, online=online, error=str(e))
            
    async def is_ue_online(self, imsi: str) -> bool:
        """
        檢查 UE 是否線上
        
        Args:
            imsi: UE IMSI
            
        Returns:
            UE 是否線上
        """
        try:
            key = f"ue:online:{imsi}"
            result = await self.client.exists(key)
            return bool(result)
        except Exception as e:
            logger.error("檢查 UE 線上狀態失敗", imsi=imsi, error=str(e))
            return False 