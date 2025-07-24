#!/usr/bin/env python3
"""
自動初始化衛星數據服務 - 實現正確的架構優先級
優先級順序 (按照 docs/architecture.md 設計):
1. PostgreSQL 預載歷史數據 (主要)
2. Docker 映像內建歷史數據
3. 外部 TLE 下載 (智能更新)
4. Redis 模擬數據 (最後手段)
"""

import asyncio
import os
import asyncpg
import structlog
from datetime import datetime, timezone

logger = structlog.get_logger(__name__)

async def check_and_init_satellite_data():
    """
    檢查並初始化衛星數據 - 實現正確的架構優先級
    按照 docs/architecture.md 中「不依賴網路即時連接」的設計原則
    """
    try:
        # 獲取數據庫連接
        db_url = os.getenv("RL_DATABASE_URL", "postgresql://rl_user:rl_password@netstack-rl-postgres:5432/rl_research")
        
        conn = await asyncpg.connect(db_url)
        
        # 檢查現有數據狀態
        tle_count = await conn.fetchval("SELECT COUNT(*) FROM satellite_tle_data WHERE is_active = TRUE")
        orbital_count = await conn.fetchval("SELECT COUNT(*) FROM satellite_orbital_cache")
        
        logger.info(f"📊 當前數據狀態: TLE {tle_count} 條, 軌道緩存 {orbital_count} 條")
        
        # 檢查是否需要完整預載 (符合架構設計的 ~518,400 條記錄)
        needs_full_preload = tle_count < 10 or orbital_count < 1000
        
        if needs_full_preload:
            logger.info("🚀 數據庫中數據不足，開始執行歷史數據預載...")
            
            # 優先級 1: PostgreSQL 預載歷史數據
            await _preload_historical_data(db_url)
            
            # 重新檢查數據量
            final_tle_count = await conn.fetchval("SELECT COUNT(*) FROM satellite_tle_data WHERE is_active = TRUE")
            final_orbital_count = await conn.fetchval("SELECT COUNT(*) FROM satellite_orbital_cache")
            
            if final_tle_count > 10 and final_orbital_count > 1000:
                logger.info(f"✅ 歷史數據預載成功: TLE {final_tle_count} 條, 軌道 {final_orbital_count} 條")
            else:
                logger.warning(f"⚠️ 歷史數據預載不完整，嘗試外部下載作為補充...")
                # 優先級 3: 外部下載作為補充
                await _fallback_external_download(db_url)
            
        else:
            logger.info(f"✅ 數據庫中已有足夠數據: TLE {tle_count} 條, 軌道 {orbital_count} 條")
            
            # 檢查數據新鮮度 (可選的智能更新)
            latest_update = await conn.fetchval(
                "SELECT MAX(last_updated) FROM satellite_tle_data WHERE is_active = TRUE"
            )
            
            if latest_update:
                age_hours = (datetime.now(timezone.utc) - latest_update).total_seconds() / 3600
                if age_hours > 168:  # 7 天
                    logger.info(f"💡 數據已有 {age_hours:.1f} 小時，可考慮智能更新")
                    # 這裡可以實現智能更新邏輯，但不是必需的
            
        await conn.close()
        
    except Exception as e:
        logger.error(f"❌ 衛星數據自動初始化失敗: {e}")

async def _preload_historical_data(db_url: str):
    """執行歷史數據預載 - 架構的核心功能"""
    try:
        from .historical_data_preloader import preload_historical_data
        
        logger.info("🏗️ 開始執行歷史數據預載 (按照 docs/architecture.md 設計)...")
        result = await preload_historical_data(db_url)
        
        if result["status"] == "already_preloaded":
            logger.info("✅ 歷史數據已預載完成")
        elif result["status"] == "preloaded":
            details = result["details"]
            logger.info(
                f"🎉 歷史數據預載完成: "
                f"TLE {details.get('tle_records_loaded', 0)} 條, "
                f"軌道 {details.get('orbital_records_precomputed', 0)} 條"
            )
        else:
            logger.warning(f"⚠️ 歷史數據預載狀態: {result['status']}")
            
    except ImportError as e:
        logger.error(f"❌ 無法導入歷史數據預載器: {e}")
        logger.info("💡 回退到外部下載模式...")
        await _fallback_external_download(db_url)
    except Exception as e:
        logger.error(f"❌ 歷史數據預載失敗: {e}")
        logger.info("💡 回退到外部下載模式...")
        await _fallback_external_download(db_url)

async def _fallback_external_download(db_url: str):
    """回退到外部下載模式"""
    try:
        logger.info("📡 嘗試外部下載 TLE 數據作為補充...")
        
        # 導入衛星數據管理器
        from .satellite_data_manager import SatelliteDataManager
        
        # 初始化管理器
        manager = SatelliteDataManager(db_url)
        await manager.initialize()
        
        # 下載主要星座的數據
        constellations = ["starlink", "oneweb", "gps", "galileo"]
        
        total_success = 0
        for constellation in constellations:
            try:
                logger.info(f"📡 下載 {constellation} TLE 數據...")
                result = await manager.update_tle_data(constellation)
                
                success_count = result.get("satellites_added", 0) + result.get("satellites_updated", 0)
                if success_count > 0:
                    logger.info(f"✅ {constellation} 成功載入 {success_count} 顆衛星")
                    total_success += success_count
                else:
                    logger.warning(f"⚠️ {constellation} 沒有成功載入衛星數據")
                    
            except Exception as e:
                logger.error(f"❌ {constellation} TLE 數據下載失敗: {e}")
                
        await manager.close()
        
        if total_success > 0:
            logger.info(f"🎉 外部下載完成，共載入 {total_success} 顆衛星")
        else:
            logger.warning("⚠️ 所有外部下載均失敗，系統將使用 Redis 模擬數據")
            
    except Exception as e:
        logger.error(f"❌ 外部下載失敗: {e}")
        logger.info("💡 系統將依賴 Redis 模擬數據運行")

def init_satellite_data_sync():
    """同步版本的初始化函數"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(check_and_init_satellite_data())
    finally:
        loop.close()

if __name__ == "__main__":
    init_satellite_data_sync()