#!/usr/bin/env python3
"""
歷史數據預載器 - 實現 docs/architecture.md 中的正確架構
優先級: PostgreSQL 預載數據 > Docker 歷史數據 > 外部下載 > Redis 模擬數據

核心功能:
1. 載入 Docker 映像內建的歷史 TLE 數據到 PostgreSQL
2. 預算 45 天的軌道數據 (~518,400 條記錄)
3. 建立時間序列緩存，實現快速查詢
"""

import asyncio
import asyncpg
import structlog
import sys
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

logger = structlog.get_logger(__name__)

# 導入 NetStack 的歷史數據
try:
    from ..data.historical_tle_data import (
        get_historical_tle_data, 
        get_data_source_info,
        ALL_HISTORICAL_TLE_DATA
    )
    HISTORICAL_DATA_AVAILABLE = True
    logger.info("✅ 成功導入 NetStack 歷史數據模組")
except ImportError as e:
    HISTORICAL_DATA_AVAILABLE = False
    logger.error(f"⚠️ 無法導入 NetStack 歷史數據模組: {e}")

from .orbit_calculation_engine import OrbitCalculationEngine, TLEData, TimeRange

class HistoricalDataPreloader:
    """歷史數據預載器 - 實現正確的架構設計"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.orbit_engine = OrbitCalculationEngine()
        self.db_pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self):
        """初始化數據庫連接池"""
        try:
            self.db_pool = await asyncpg.create_pool(
                self.db_url, min_size=2, max_size=10, command_timeout=60
            )
            logger.info("🛰️ 歷史數據預載器初始化完成")
        except Exception as e:
            logger.error(f"❌ 歷史數據預載器初始化失敗: {e}")
            raise
    
    async def preload_all_historical_data(self) -> Dict[str, Any]:
        """
        完整的歷史數據預載流程
        按照 docs/architecture.md 設計實現
        """
        logger.info("🚀 開始完整歷史數據預載流程...")
        
        start_time = datetime.now(timezone.utc)
        stats = {
            "start_time": start_time,
            "tle_records_loaded": 0,
            "orbital_records_precomputed": 0,
            "preload_jobs_created": 0,
            "errors": []
        }
        
        try:
            # Step 1: 載入歷史 TLE 數據到 PostgreSQL
            tle_stats = await self._load_historical_tle_data()
            stats["tle_records_loaded"] = tle_stats["records_loaded"]
            stats["errors"].extend(tle_stats.get("errors", []))
            
            if stats["tle_records_loaded"] == 0:
                stats["errors"].append("沒有成功載入任何 TLE 數據")
                return stats
            
            # Step 2: 預計算 45 天軌道數據
            orbital_stats = await self._precompute_orbital_data()
            stats["orbital_records_precomputed"] = orbital_stats["records_computed"]
            stats["errors"].extend(orbital_stats.get("errors", []))
            
            # Step 3: 記錄預載作業
            job_stats = await self._create_preload_job_record(stats)
            stats["preload_jobs_created"] = job_stats["jobs_created"]
            
            end_time = datetime.now(timezone.utc)
            stats["end_time"] = end_time
            stats["duration_seconds"] = (end_time - start_time).total_seconds()
            
            logger.info(
                f"✅ 歷史數據預載完成: "
                f"TLE {stats['tle_records_loaded']} 條, "
                f"軌道 {stats['orbital_records_precomputed']} 條, "
                f"耗時 {stats['duration_seconds']:.1f} 秒"
            )
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ 歷史數據預載失敗: {e}")
            stats["errors"].append(str(e))
            return stats
    
    async def _load_historical_tle_data(self) -> Dict[str, Any]:
        """載入歷史 TLE 數據到 PostgreSQL"""
        logger.info("📡 載入歷史 TLE 數據到 PostgreSQL...")
        
        stats = {"records_loaded": 0, "errors": []}
        
        if not HISTORICAL_DATA_AVAILABLE:
            stats["errors"].append("歷史數據模組不可用")
            return stats
        
        try:
            # 清空現有 TLE 數據以確保乾淨的開始
            async with self.db_pool.acquire() as conn:
                await conn.execute("TRUNCATE TABLE satellite_tle_data CASCADE")
                logger.info("🧹 已清空現有 TLE 數據表")
            
            # 載入所有星座的歷史數據
            for constellation, tle_list in ALL_HISTORICAL_TLE_DATA.items():
                constellation_count = 0
                
                async with self.db_pool.acquire() as conn:
                    async with conn.transaction():
                        for tle_entry in tle_list:
                            try:
                                # 解析 epoch 時間
                                line1 = tle_entry["line1"]
                                epoch_year = int(line1[18:20])
                                epoch_day = float(line1[20:32])
                                
                                # 轉換為完整年份
                                if epoch_year < 57:
                                    full_year = 2000 + epoch_year
                                else:
                                    full_year = 1900 + epoch_year
                                
                                # 計算 epoch 時間
                                epoch = datetime(full_year, 1, 1, tzinfo=timezone.utc) + timedelta(
                                    days=epoch_day - 1
                                )
                                
                                # 計算軌道參數 - 從 TLE line2 提取平均運動
                                line2 = tle_entry["line2"]
                                try:
                                    # TLE line2 format: mean motion is in columns 52-63
                                    mean_motion = float(line2[52:63].strip())
                                except (ValueError, IndexError):
                                    # 回退值
                                    mean_motion = 15.0
                                    
                                orbital_period = 1440.0 / mean_motion if mean_motion > 0 else 90.0
                                
                                # 插入數據
                                await conn.execute(
                                    """
                                    INSERT INTO satellite_tle_data (
                                        satellite_id, norad_id, satellite_name, constellation,
                                        line1, line2, epoch, mean_motion, orbital_period,
                                        is_active, last_updated
                                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                                    ON CONFLICT (norad_id) DO UPDATE SET
                                        satellite_name = EXCLUDED.satellite_name,
                                        line1 = EXCLUDED.line1,
                                        line2 = EXCLUDED.line2,
                                        epoch = EXCLUDED.epoch,
                                        last_updated = EXCLUDED.last_updated
                                    """,
                                    f"{constellation}_{tle_entry['norad_id']}",
                                    tle_entry["norad_id"],
                                    tle_entry["name"],
                                    constellation,
                                    tle_entry["line1"],
                                    tle_entry["line2"],
                                    epoch,
                                    mean_motion,
                                    orbital_period,
                                    True,
                                    datetime.now(timezone.utc)
                                )
                                
                                constellation_count += 1
                                stats["records_loaded"] += 1
                                
                            except Exception as e:
                                error_msg = f"載入 {constellation} 衛星 {tle_entry.get('name', 'Unknown')} 失敗: {e}"
                                logger.warning(error_msg)
                                stats["errors"].append(error_msg)
                
                logger.info(f"✅ {constellation}: 載入 {constellation_count} 顆衛星")
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ 歷史 TLE 數據載入失敗: {e}")
            stats["errors"].append(str(e))
            return stats
    
    async def _precompute_orbital_data(self) -> Dict[str, Any]:
        """預計算 45 天軌道數據 - 實現 ~518,400 條記錄"""
        logger.info("🌍 開始預計算 45 天軌道數據...")
        
        stats = {"records_computed": 0, "errors": []}
        
        try:
            # 清空現有軌道緩存
            async with self.db_pool.acquire() as conn:
                await conn.execute("TRUNCATE TABLE satellite_orbital_cache")
                logger.info("🧹 已清空現有軌道緩存")
            
            # 獲取所有 TLE 數據
            async with self.db_pool.acquire() as conn:
                tle_records = await conn.fetch(
                    """
                    SELECT satellite_id, norad_id, satellite_name, constellation,
                           line1, line2, epoch
                    FROM satellite_tle_data 
                    WHERE is_active = TRUE
                    ORDER BY constellation, norad_id
                    """
                )
            
            if not tle_records:
                stats["errors"].append("沒有找到可用的 TLE 數據")
                return stats
            
            logger.info(f"📊 將為 {len(tle_records)} 顆衛星預計算軌道數據")
            
            # 計算時間範圍: 45 天
            start_time = datetime.now(timezone.utc)
            end_time = start_time + timedelta(days=45)
            time_range = TimeRange(start=start_time, end=end_time)
            
            # 時間解析度: 30 秒 (符合 docs/overview.md)
            sample_interval_minutes = 0.5  # 30秒 = 0.5分鐘
            
            for tle_record in tle_records:
                try:
                    # 準備 TLE 數據
                    tle_data = TLEData(
                        satellite_id=str(tle_record["norad_id"]),
                        satellite_name=tle_record["satellite_name"],
                        line1=tle_record["line1"],
                        line2=tle_record["line2"],
                        epoch=tle_record["epoch"]
                    )
                    
                    # 添加到軌道引擎
                    self.orbit_engine.add_tle_data(tle_data)
                    
                    # 計算軌道路徑
                    orbit_path = self.orbit_engine.predict_orbit_path(
                        str(tle_record["norad_id"]), time_range, sample_interval_minutes
                    )
                    
                    if not orbit_path or not orbit_path.positions:
                        logger.warning(f"⚠️ 衛星 {tle_record['satellite_name']} 軌道計算失敗")
                        continue
                    
                    # 台灣觀測者位置 (符合 docs/overview.md)
                    observer_lat = 24.9564  # 24°56'39"N
                    observer_lon = 121.3717  # 121°22'17"E
                    observer_alt = 0.1  # 100m
                    
                    # 批量插入軌道數據
                    records_for_this_satellite = 0
                    async with self.db_pool.acquire() as conn:
                        async with conn.transaction():
                            for position in orbit_path.positions:
                                # 計算觀測者視角
                                elevation, azimuth, range_km = self._calculate_observer_view(
                                    observer_lat, observer_lon, observer_alt,
                                    position.latitude, position.longitude, position.altitude
                                )
                                
                                await conn.execute(
                                    """
                                    INSERT INTO satellite_orbital_cache (
                                        satellite_id, norad_id, constellation, timestamp,
                                        position_x, position_y, position_z,
                                        latitude, longitude, altitude,
                                        velocity_x, velocity_y, velocity_z,
                                        orbital_period, elevation_angle, azimuth_angle, range_rate,
                                        calculation_method, data_quality, created_at
                                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20)
                                    """,
                                    tle_record["satellite_id"],
                                    tle_record["norad_id"],  # 添加 norad_id
                                    tle_record["constellation"],
                                    position.timestamp,
                                    position.x,
                                    position.y,
                                    position.z,
                                    position.latitude,
                                    position.longitude,
                                    position.altitude,
                                    position.velocity_x,
                                    position.velocity_y,
                                    position.velocity_z,
                                    position.orbital_period,
                                    elevation,
                                    azimuth,
                                    0.0,  # range_rate (暫時設為0)
                                    'SGP4',
                                    1.0,
                                    datetime.now(timezone.utc)
                                )
                                
                                records_for_this_satellite += 1
                                stats["records_computed"] += 1
                    
                    logger.info(
                        f"✅ {tle_record['satellite_name']} ({tle_record['constellation']}): "
                        f"{records_for_this_satellite} 條軌道記錄"
                    )
                    
                except Exception as e:
                    error_msg = f"衛星 {tle_record['satellite_name']} 軌道預計算失敗: {e}"
                    logger.error(error_msg)
                    stats["errors"].append(error_msg)
            
            logger.info(f"🎉 軌道數據預計算完成: 總共 {stats['records_computed']} 條記錄")
            return stats
            
        except Exception as e:
            logger.error(f"❌ 軌道數據預計算失敗: {e}")
            stats["errors"].append(str(e))
            return stats
    
    def _calculate_observer_view(self, obs_lat, obs_lon, obs_alt, sat_lat, sat_lon, sat_alt):
        """計算觀測者視角 (仰角、方位角、距離)"""
        import math
        
        # 地球半徑 (km)
        R = 6371.0
        
        # 轉換為弧度
        obs_lat_rad = math.radians(obs_lat)
        obs_lon_rad = math.radians(obs_lon)
        sat_lat_rad = math.radians(sat_lat)
        sat_lon_rad = math.radians(sat_lon)
        
        # 衛星與觀測者的 ECEF 座標
        obs_x = (R + obs_alt) * math.cos(obs_lat_rad) * math.cos(obs_lon_rad)
        obs_y = (R + obs_alt) * math.cos(obs_lat_rad) * math.sin(obs_lon_rad)
        obs_z = (R + obs_alt) * math.sin(obs_lat_rad)
        
        sat_x = (R + sat_alt) * math.cos(sat_lat_rad) * math.cos(sat_lon_rad)
        sat_y = (R + sat_alt) * math.cos(sat_lat_rad) * math.sin(sat_lon_rad)
        sat_z = (R + sat_alt) * math.sin(sat_lat_rad)
        
        # 相對位置向量
        dx = sat_x - obs_x
        dy = sat_y - obs_y
        dz = sat_z - obs_z
        
        # 距離
        range_km = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        # 轉換到 ENU 座標系
        # 簡化計算，返回近似值
        elevation = math.degrees(math.asin(dz / range_km)) if range_km > 0 else -90
        azimuth = math.degrees(math.atan2(dy, dx)) % 360
        
        return elevation, azimuth, range_km
    
    async def _create_preload_job_record(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """創建預載作業記錄 - 匹配現有表結構"""
        try:
            duration_ms = stats.get("duration_seconds", 0) * 1000
            total_records = stats["tle_records_loaded"] + stats["orbital_records_precomputed"]
            
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO satellite_data_preload_jobs (
                        job_name, job_type, constellation, status,
                        started_at, completed_at, created_at,
                        satellites_processed, total_satellites, records_created,
                        execution_time_ms, created_by
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    """,
                    "historical_data_preload",
                    "full_preload",
                    "all_constellations", 
                    "completed" if not stats.get("errors") else "completed_with_errors",
                    stats["start_time"],
                    stats.get("end_time", datetime.now(timezone.utc)),
                    datetime.now(timezone.utc),
                    len(ALL_HISTORICAL_TLE_DATA) if HISTORICAL_DATA_AVAILABLE else 0,
                    len(ALL_HISTORICAL_TLE_DATA) if HISTORICAL_DATA_AVAILABLE else 0,
                    total_records,
                    int(duration_ms),
                    "historical_data_preloader"
                )
            
            logger.info("📋 預載作業記錄已創建")
            return {"jobs_created": 1}
            
        except Exception as e:
            logger.error(f"⚠️ 創建預載作業記錄失敗: {e}")
            return {"jobs_created": 0}
    
    async def check_preload_status(self) -> Dict[str, Any]:
        """檢查預載狀態 - 匹配現有表結構"""
        try:
            async with self.db_pool.acquire() as conn:
                # 檢查 TLE 數據
                tle_count = await conn.fetchval("SELECT COUNT(*) FROM satellite_tle_data WHERE is_active = TRUE")
                
                # 檢查軌道緩存
                orbital_count = await conn.fetchval("SELECT COUNT(*) FROM satellite_orbital_cache")
                
                # 檢查最新預載作業
                latest_job = await conn.fetchrow(
                    """
                    SELECT job_name, status, completed_at, records_created, satellites_processed
                    FROM satellite_data_preload_jobs
                    ORDER BY created_at DESC
                    LIMIT 1
                    """
                )
                
                return {
                    "tle_records": tle_count,
                    "orbital_records": orbital_count,
                    "latest_job": dict(latest_job) if latest_job else None,
                    "is_fully_preloaded": tle_count > 10 and orbital_count > 1000,
                    "expected_orbital_records": 518400  # 45天 × 24小時 × 120時間點 × 平均8顆衛星
                }
                
        except Exception as e:
            logger.error(f"❌ 檢查預載狀態失敗: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """關閉數據庫連接池"""
        if self.db_pool:
            await self.db_pool.close()
            logger.info("🛰️ 歷史數據預載器已關閉")


async def preload_historical_data(db_url: str) -> Dict[str, Any]:
    """
    主要接口函數 - 執行完整的歷史數據預載
    供 NetStack 啟動時調用
    """
    preloader = HistoricalDataPreloader(db_url)
    
    try:
        await preloader.initialize()
        
        # 檢查是否已經預載
        status = await preloader.check_preload_status()
        
        if status.get("is_fully_preloaded", False):
            logger.info(f"✅ 數據已預載: TLE {status['tle_records']} 條, 軌道 {status['orbital_records']} 條")
            return {"status": "already_preloaded", "details": status}
        
        # 執行完整預載
        logger.info("🚀 開始執行歷史數據預載...")
        result = await preloader.preload_all_historical_data()
        
        return {"status": "preloaded", "details": result}
        
    finally:
        await preloader.close()


if __name__ == "__main__":
    """直接執行測試"""
    import os
    
    db_url = os.getenv("RL_DATABASE_URL", "postgresql://rl_user:rl_password@localhost:5432/rl_research")
    
    async def test_preload():
        result = await preload_historical_data(db_url)
        print(f"預載結果: {result}")
    
    asyncio.run(test_preload())