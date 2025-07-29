#!/usr/bin/env python3
"""
台灣觀測點批次預計算腳本
完成 satellite-precompute-plan Phase 1-2 的最終實現

執行所有台灣觀測點的衛星軌道預計算，並存儲到 PostgreSQL
"""

import asyncio
import asyncpg
import structlog
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import os
import sys

# 添加 netstack_api 到路徑
sys.path.append('/app/netstack_api')

from netstack_api.services.precompute_satellite_history import (
    SatelliteHistoryPrecomputer, 
    ObserverPosition
)
from netstack_api.services.tle_data_manager import TLEDataManager

logger = structlog.get_logger(__name__)

class TaiwanBatchPrecomputer:
    """台灣觀測點批次預計算器"""
    
    def __init__(self):
        self.taiwan_observers = {
            'ntpu': ObserverPosition(24.94417, 121.37139, 50.0),  # NTPU
            'nycu': ObserverPosition(24.78717, 120.99717, 50.0),  # NYCU  
            'ntu': ObserverPosition(25.01713, 121.54187, 50.0),   # NTU
            'ncku': ObserverPosition(22.99617, 120.22167, 50.0),  # NCKU
        }
        
        # PostgreSQL 連接配置
        self.db_config = {
            'host': 'netstack-rl-postgres',
            'port': 5432,
            'database': 'rl_research',
            'user': 'rl_user',
            'password': 'rl_password'
        }
    
    async def get_db_connection(self):
        """獲取數據庫連接"""
        return await asyncpg.connect(**self.db_config)
    
    async def precompute_for_observer(
        self, 
        observer_name: str, 
        observer: ObserverPosition,
        constellation: str = 'starlink',
        hours: int = 6
    ):
        """為單個觀測點執行預計算"""
        
        logger.info(
            f"開始為 {observer_name} 預計算 {constellation} 衛星數據",
            observer_name=observer_name,
            constellation=constellation,
            hours=hours
        )
        
        # 設置時間範圍
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(hours=hours)
        
        try:
            # 載入 TLE 數據
            tle_manager = TLEDataManager()
            tle_data = await tle_manager.get_constellation_tle_data(constellation)
            
            if not tle_data:
                logger.error(f"無法載入 {constellation} TLE 數據")
                return
            
            # 創建預計算器
            precomputer = SatelliteHistoryPrecomputer(
                tle_data=tle_data,
                observer_coords=(observer.latitude, observer.longitude, observer.altitude),
                time_range=(start_time, end_time)
            )
            
            # 執行預計算
            results = await precomputer.compute_history_async(
                time_interval_seconds=30,  # 30秒間隔
                min_elevation=10.0,        # 10度最小仰角
                max_satellites=50          # 最多50顆衛星
            )
            
            # 存儲到數據庫
            await self.store_results(results, observer_name, observer)
            
            logger.info(
                f"完成 {observer_name} 預計算",
                observer_name=observer_name,
                results_count=len(results)
            )
            
        except Exception as e:
            logger.error(
                f"預計算失敗: {observer_name}",
                observer_name=observer_name,
                error=str(e)
            )
            raise
    
    async def store_results(
        self, 
        results: List[Dict[str, Any]], 
        observer_name: str,
        observer: ObserverPosition
    ):
        """存儲預計算結果到數據庫"""
        
        conn = await self.get_db_connection()
        
        try:
            # 準備批次插入數據
            insert_data = []
            
            for result in results:
                insert_data.append((
                    result['satellite_id'],
                    result['norad_id'],
                    result['constellation'],
                    result['timestamp'],
                    result['satellite_position']['x'],
                    result['satellite_position']['y'], 
                    result['satellite_position']['z'],
                    result['satellite_position']['latitude'],
                    result['satellite_position']['longitude'],
                    result['satellite_position']['altitude'],
                    result['satellite_position'].get('velocity_x'),
                    result['satellite_position'].get('velocity_y'),
                    result['satellite_position'].get('velocity_z'),
                    result['satellite_position'].get('orbital_period'),
                    result['satellite_position']['elevation_angle'],
                    result['satellite_position']['azimuth_angle'],
                    observer.latitude,   # observer_latitude
                    observer.longitude,  # observer_longitude  
                    observer.altitude,   # observer_altitude
                    result['signal_quality'].get('signal_strength'),
                    result['signal_quality'].get('path_loss_db')
                ))
            
            # 批次插入
            await conn.executemany("""
                INSERT INTO satellite_orbital_cache (
                    satellite_id, norad_id, constellation, timestamp,
                    position_x, position_y, position_z,
                    latitude, longitude, altitude,
                    velocity_x, velocity_y, velocity_z, orbital_period,
                    elevation_angle, azimuth_angle,
                    observer_latitude, observer_longitude, observer_altitude,
                    signal_strength, path_loss_db
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 
                         $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21)
                ON CONFLICT (satellite_id, timestamp) DO UPDATE SET
                    elevation_angle = EXCLUDED.elevation_angle,
                    azimuth_angle = EXCLUDED.azimuth_angle,
                    observer_latitude = EXCLUDED.observer_latitude,
                    observer_longitude = EXCLUDED.observer_longitude,
                    observer_altitude = EXCLUDED.observer_altitude,
                    signal_strength = EXCLUDED.signal_strength,
                    path_loss_db = EXCLUDED.path_loss_db
            """, insert_data)
            
            logger.info(
                f"成功存儲 {len(insert_data)} 條預計算記錄",
                observer_name=observer_name,
                records_count=len(insert_data)
            )
            
        finally:
            await conn.close()
    
    async def run_batch_precompute(self, constellations: List[str] = ['starlink']):
        """執行所有台灣觀測點的批次預計算"""
        
        logger.info("開始台灣觀測點批次預計算", constellations=constellations)
        
        for constellation in constellations:
            for observer_name, observer in self.taiwan_observers.items():
                try:
                    await self.precompute_for_observer(
                        observer_name=observer_name,
                        observer=observer,
                        constellation=constellation,
                        hours=6  # 預計算6小時數據
                    )
                except Exception as e:
                    logger.error(
                        f"觀測點預計算失敗: {observer_name}",
                        observer_name=observer_name,
                        constellation=constellation,
                        error=str(e)
                    )
                    continue
        
        logger.info("台灣觀測點批次預計算完成")

async def main():
    """主函數"""
    
    # 配置日誌
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # 創建批次預計算器
    batch_precomputer = TaiwanBatchPrecomputer()
    
    # 執行批次預計算
    await batch_precomputer.run_batch_precompute(['starlink', 'oneweb'])

if __name__ == "__main__":
    asyncio.run(main())