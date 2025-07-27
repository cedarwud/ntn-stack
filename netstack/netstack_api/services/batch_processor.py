#!/usr/bin/env python3
"""
歷史數據批次處理器 - Phase 2 核心組件

負責將預計算的衛星軌道數據批次存儲到 PostgreSQL 數據庫。
實現高效的批次插入、增量更新和數據統計功能。
"""

import asyncio
import asyncpg
import structlog
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict

from .precompute_satellite_history import PrecomputeResult, ObserverPosition

logger = structlog.get_logger(__name__)


class HistoryBatchProcessor:
    """
    歷史數據批次處理器
    
    功能：
    1. 批次存儲預計算數據到 PostgreSQL
    2. 增量更新機制
    3. 數據品質驗證
    4. 統計信息生成
    5. 過期數據清理
    """
    
    def __init__(self, postgres_url: str, batch_size: int = 1000):
        """
        初始化批次處理器
        
        Args:
            postgres_url: PostgreSQL 連接字符串
            batch_size: 批次大小
        """
        self.postgres_url = postgres_url
        self.batch_size = batch_size
        self.logger = structlog.get_logger(__name__)
        self.connection_pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self) -> bool:
        """
        初始化數據庫連接池
        
        Returns:
            是否初始化成功
        """
        try:
            self.connection_pool = await asyncpg.create_pool(
                self.postgres_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            
            # 確保數據表存在
            await self._ensure_tables_exist()
            
            self.logger.info(
                "歷史數據批次處理器初始化完成",
                postgres_url=self.postgres_url.split('@')[1] if '@' in self.postgres_url else "隱藏",
                batch_size=self.batch_size
            )
            return True
            
        except Exception as e:
            self.logger.error("批次處理器初始化失敗", error=str(e))
            return False
    
    async def process_and_store(self, precomputed_data: List[PrecomputeResult]) -> Dict[str, Any]:
        """
        批次存儲預計算數據到 PostgreSQL
        
        Args:
            precomputed_data: 預計算結果列表
            
        Returns:
            處理統計信息
        """
        if not self.connection_pool:
            raise RuntimeError("批次處理器尚未初始化")
        
        if not precomputed_data:
            self.logger.info("沒有數據需要處理")
            return {"processed": 0, "failed": 0, "skipped": 0}
        
        self.logger.info(
            "開始批次存儲數據",
            total_records=len(precomputed_data),
            batch_size=self.batch_size
        )
        
        stats = {
            "processed": 0,
            "failed": 0,
            "skipped": 0,
            "processing_time": 0.0,
            "errors": []
        }
        
        start_time = datetime.now()
        
        async with self.connection_pool.acquire() as conn:
            try:
                # 開始事務
                async with conn.transaction():
                    # 分批處理數據
                    for i in range(0, len(precomputed_data), self.batch_size):
                        batch = precomputed_data[i:i + self.batch_size]
                        
                        try:
                            batch_result = await self._process_batch(conn, batch)
                            stats["processed"] += batch_result["processed"]
                            stats["failed"] += batch_result["failed"]
                            stats["skipped"] += batch_result["skipped"]
                            
                            if batch_result["errors"]:
                                stats["errors"].extend(batch_result["errors"])
                            
                            # 進度日誌
                            if (i + len(batch)) % 5000 == 0 or (i + len(batch)) >= len(precomputed_data):
                                self.logger.info(
                                    f"批次處理進度: {i + len(batch)}/{len(precomputed_data)} "
                                    f"({(i + len(batch))/len(precomputed_data)*100:.1f}%)"
                                )
                                
                        except Exception as e:
                            stats["failed"] += len(batch)
                            stats["errors"].append(f"批次 {i//self.batch_size + 1} 處理失敗: {str(e)}")
                            self.logger.error(f"批次處理失敗", batch_start=i, error=str(e))
                            continue
                    
                    stats["processing_time"] = (datetime.now() - start_time).total_seconds()
                    
                    self.logger.info(
                        "批次存儲完成",
                        processed=stats["processed"],
                        failed=stats["failed"],
                        skipped=stats["skipped"],
                        processing_time=f"{stats['processing_time']:.2f}s"
                    )
                    
            except Exception as e:
                stats["errors"].append(f"事務處理失敗: {str(e)}")
                self.logger.error("批次存儲事務失敗", error=str(e))
                raise
        
        return stats
    
    async def _process_batch(self, conn: asyncpg.Connection, 
                           batch: List[PrecomputeResult]) -> Dict[str, Any]:
        """
        處理單個批次
        
        Args:
            conn: 數據庫連接
            batch: 批次數據
            
        Returns:
            批次處理統計
        """
        batch_stats = {"processed": 0, "failed": 0, "skipped": 0, "errors": []}
        
        # 準備插入數據
        insert_records = []
        
        for record in batch:
            try:
                # 驗證數據品質
                if not self._validate_record(record):
                    batch_stats["skipped"] += 1
                    continue
                
                # 準備數據庫記錄
                db_record = self._prepare_db_record(record)
                insert_records.append(db_record)
                
            except Exception as e:
                batch_stats["failed"] += 1
                batch_stats["errors"].append(f"記錄準備失敗: {str(e)}")
                continue
        
        if insert_records:
            try:
                # 批次插入到 satellite_orbital_cache
                await conn.executemany("""
                    INSERT INTO satellite_orbital_cache (
                        satellite_id, norad_id, constellation, timestamp,
                        position_x, position_y, position_z,
                        latitude, longitude, altitude,
                        velocity_x, velocity_y, velocity_z, orbital_period,
                        elevation_angle, azimuth_angle, range_rate,
                        observer_latitude, observer_longitude, observer_altitude,
                        signal_strength, path_loss_db, sinr, link_margin,
                        calculation_method, data_quality, atmospheric_loss
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                        $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27
                    )
                    ON CONFLICT (satellite_id, timestamp) DO UPDATE SET
                        elevation_angle = EXCLUDED.elevation_angle,
                        azimuth_angle = EXCLUDED.azimuth_angle,
                        signal_strength = EXCLUDED.signal_strength,
                        path_loss_db = EXCLUDED.path_loss_db,
                        sinr = EXCLUDED.sinr,
                        link_margin = EXCLUDED.link_margin,
                        data_quality = EXCLUDED.data_quality
                """, insert_records)
                
                batch_stats["processed"] = len(insert_records)
                
            except Exception as e:
                batch_stats["failed"] = len(insert_records)
                batch_stats["errors"].append(f"數據庫插入失敗: {str(e)}")
                self.logger.error("批次插入失敗", error=str(e))
        
        return batch_stats
    
    def _validate_record(self, record: PrecomputeResult) -> bool:
        """
        驗證記錄數據品質
        
        Args:
            record: 預計算記錄
            
        Returns:
            是否有效
        """
        try:
            # 基本字段檢查
            if not record.satellite_id or not record.timestamp:
                return False
            
            # 位置合理性檢查
            pos = record.satellite_position
            if not (-90 <= pos["latitude"] <= 90):
                return False
            if not (-180 <= pos["longitude"] <= 180):
                return False
            if pos["altitude"] < 0 or pos["altitude"] > 2000000:  # 0-2000km
                return False
            
            # 角度合理性檢查
            if not (-90 <= pos["elevation"] <= 90):
                return False
            if not (0 <= pos["azimuth"] <= 360):
                return False
            
            # 距離合理性檢查
            if pos["range"] < 0 or pos["range"] > 3000:  # 0-3000km
                return False
            
            return True
            
        except (KeyError, TypeError, ValueError):
            return False
    
    def _prepare_db_record(self, record: PrecomputeResult) -> Tuple:
        """
        準備數據庫插入記錄
        
        Args:
            record: 預計算結果
            
        Returns:
            數據庫記錄元組
        """
        pos = record.satellite_position
        signal = record.signal_quality
        observer = record.observer_position
        
        # 計算 position_x, y, z (ECEF 坐標)
        # 簡化實現：基於地理坐標計算
        lat_rad = math.radians(pos["latitude"])
        lon_rad = math.radians(pos["longitude"])
        alt_km = pos["altitude"] / 1000.0
        
        # WGS84 地球半徑
        a = 6378.137  # km
        
        # 簡化的 ECEF 坐標計算
        position_x = (a + alt_km) * math.cos(lat_rad) * math.cos(lon_rad)
        position_y = (a + alt_km) * math.cos(lat_rad) * math.sin(lon_rad)
        position_z = (a + alt_km) * math.sin(lat_rad)
        
        return (
            record.satellite_id,                    # satellite_id
            record.norad_id,                       # norad_id
            record.constellation,                   # constellation
            record.timestamp,                       # timestamp
            position_x,                            # position_x
            position_y,                            # position_y
            position_z,                            # position_z
            pos["latitude"],                       # latitude
            pos["longitude"],                      # longitude
            pos["altitude"],                       # altitude (meters)
            0.0,                                   # velocity_x (暫時為0)
            0.0,                                   # velocity_y
            0.0,                                   # velocity_z
            None,                                  # orbital_period
            pos["elevation"],                      # elevation_angle
            pos["azimuth"],                        # azimuth_angle
            pos["range"],                          # range_rate
            observer.latitude,                     # observer_latitude
            observer.longitude,                    # observer_longitude
            observer.altitude,                     # observer_altitude
            signal.get("signal_strength", 0.0),    # signal_strength
            signal.get("path_loss_db", 0.0),       # path_loss_db
            signal.get("sinr", 0.0),               # sinr
            signal.get("link_margin", 0.0),        # link_margin
            record.calculation_method,             # calculation_method
            record.data_quality,                   # data_quality
            signal.get("atmospheric_loss", 0.0)    # atmospheric_loss
        )
    
    async def incremental_update(self, new_data: List[PrecomputeResult]) -> Dict[str, Any]:
        """
        增量更新數據（用於背景更新）
        
        Args:
            new_data: 新數據列表
            
        Returns:
            更新統計信息
        """
        if not new_data:
            self.logger.info("沒有新數據需要更新")
            return {"updated": 0, "message": "無新數據"}
        
        # 獲取現有數據的時間範圍
        observer = new_data[0].observer_position
        
        async with self.connection_pool.acquire() as conn:
            latest_time = await conn.fetchval("""
                SELECT MAX(timestamp) FROM satellite_orbital_cache 
                WHERE observer_latitude = $1 AND observer_longitude = $2
            """, observer.latitude, observer.longitude)
            
            if latest_time:
                # 只處理比現有數據更新的記錄
                new_records = [
                    record for record in new_data 
                    if record.timestamp > latest_time.replace(tzinfo=timezone.utc)
                ]
                
                if new_records:
                    result = await self.process_and_store(new_records)
                    self.logger.info(f"增量更新 {result['processed']} 條新記錄")
                    return {"updated": result["processed"], "details": result}
                else:
                    self.logger.info("數據已是最新，無需更新")
                    return {"updated": 0, "message": "數據已最新"}
            else:
                # 沒有現有數據，全部插入
                result = await self.process_and_store(new_data)
                self.logger.info(f"初次載入 {result['processed']} 條記錄")
                return {"updated": result["processed"], "details": result}
    
    async def cleanup_old_data(self, cutoff_date: datetime, 
                              observer_coords: Tuple[float, float]) -> int:
        """
        清理過期數據（保留指定日期之後的數據）
        
        Args:
            cutoff_date: 截止日期
            observer_coords: 觀測者坐標 (緯度, 經度)
            
        Returns:
            清理的記錄數
        """
        async with self.connection_pool.acquire() as conn:
            try:
                deleted_count = await conn.fetchval("""
                    DELETE FROM satellite_orbital_cache 
                    WHERE timestamp < $1 
                      AND observer_latitude = $2 
                      AND observer_longitude = $3
                    RETURNING COUNT(*)
                """, cutoff_date, observer_coords[0], observer_coords[1])
                
                deleted_count = deleted_count or 0
                self.logger.info(
                    f"清理了 {deleted_count} 條過期數據",
                    cutoff_date=cutoff_date.isoformat()
                )
                return deleted_count
                
            except Exception as e:
                self.logger.error("數據清理失敗", error=str(e))
                return 0
    
    async def get_data_statistics(self, observer_coords: Tuple[float, float]) -> Dict[str, Any]:
        """
        獲取數據統計信息
        
        Args:
            observer_coords: 觀測者坐標 (緯度, 經度)
            
        Returns:
            統計信息字典
        """
        async with self.connection_pool.acquire() as conn:
            try:
                stats = await conn.fetchrow("""
                    SELECT 
                        COUNT(*) as total_records,
                        COUNT(DISTINCT satellite_id) as unique_satellites,
                        COUNT(DISTINCT constellation) as constellations,
                        MIN(timestamp) as earliest_time,
                        MAX(timestamp) as latest_time,
                        AVG(signal_strength) as avg_signal_strength,
                        AVG(elevation_angle) as avg_elevation,
                        AVG(data_quality) as avg_data_quality
                    FROM satellite_orbital_cache 
                    WHERE observer_latitude = $1 AND observer_longitude = $2
                """, observer_coords[0], observer_coords[1])
                
                if stats and stats['total_records'] > 0:
                    duration_hours = 0
                    if stats['latest_time'] and stats['earliest_time']:
                        duration_hours = (
                            stats['latest_time'] - stats['earliest_time']
                        ).total_seconds() / 3600
                    
                    return {
                        "total_records": stats['total_records'],
                        "unique_satellites": stats['unique_satellites'],
                        "constellations": stats['constellations'],
                        "time_range": {
                            "start": stats['earliest_time'].isoformat() if stats['earliest_time'] else None,
                            "end": stats['latest_time'].isoformat() if stats['latest_time'] else None,
                            "duration_hours": round(duration_hours, 2)
                        },
                        "signal_quality": {
                            "avg_signal_strength": round(stats['avg_signal_strength'] or 0, 2),
                            "avg_elevation": round(stats['avg_elevation'] or 0, 2),
                            "avg_data_quality": round(stats['avg_data_quality'] or 0, 2)
                        }
                    }
                else:
                    return {
                        "total_records": 0,
                        "message": "無歷史數據"
                    }
                    
            except Exception as e:
                self.logger.error("統計信息獲取失敗", error=str(e))
                return {"error": str(e)}
    
    async def _ensure_tables_exist(self) -> None:
        """確保必要的數據表存在"""
        async with self.connection_pool.acquire() as conn:
            # 檢查並創建缺失的列
            try:
                await conn.execute("""
                    ALTER TABLE satellite_orbital_cache 
                    ADD COLUMN IF NOT EXISTS sinr REAL,
                    ADD COLUMN IF NOT EXISTS link_margin REAL,
                    ADD COLUMN IF NOT EXISTS atmospheric_loss REAL
                """)
                self.logger.info("數據表結構檢查完成")
            except Exception as e:
                self.logger.warning(f"數據表結構更新失敗: {e}")
    
    async def close(self) -> None:
        """關閉連接池"""
        if self.connection_pool:
            await self.connection_pool.close()
            self.logger.info("批次處理器連接池已關閉")


# 數學函數導入
import math