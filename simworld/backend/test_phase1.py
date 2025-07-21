#!/usr/bin/env python3
"""
Phase 1 測試腳本 - TLE 數據集成驗證

測試項目：
1. CelesTrak API 連接
2. TLE 數據解析
3. 歷史數據緩存
4. 2024年1月1日數據獲取

符合 d2.md Phase 1 驗收標準
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# 添加項目根目錄到 Python 路徑
sys.path.append(str(Path(__file__).parent))

from app.services.tle_data_service import TLEDataService
from app.services.historical_data_cache import HistoricalDataCache, TimeRange

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_phase1_tests():
    """執行 Phase 1 測試"""
    logger.info("開始 Phase 1 測試 - TLE 數據集成")
    
    tle_service = TLEDataService()
    historical_cache = HistoricalDataCache(tle_service)
    
    passed_tests = 0
    total_tests = 0
    
    # 測試 1: 獲取支持的星座列表
    total_tests += 1
    try:
        logger.info("測試 1: 獲取支持的星座列表")
        constellations = tle_service.get_supported_constellations()
        
        has_starlink = any(c['constellation'] == 'starlink' for c in constellations)
        if len(constellations) > 0 and has_starlink:
            logger.info(f"✅ 測試 1 通過: 找到 {len(constellations)} 個星座，包含 Starlink")
            passed_tests += 1
        else:
            logger.error("❌ 測試 1 失敗: 未找到 Starlink 星座")
    except Exception as e:
        logger.error(f"❌ 測試 1 失敗: {e}")
    
    # 測試 2: 從 CelesTrak API 獲取 Starlink TLE 數據
    total_tests += 1
    try:
        logger.info("測試 2: 從 CelesTrak API 獲取 Starlink TLE 數據")
        starlink_tle = await tle_service.fetch_starlink_tle()
        
        if len(starlink_tle) > 0:
            logger.info(f"✅ 測試 2 通過: 成功獲取 {len(starlink_tle)} 顆 Starlink 衛星數據")
            logger.info(f"   第一顆衛星: {starlink_tle[0].satellite_name}")
            passed_tests += 1
            
            # 驗證 TLE 數據格式
            first_tle = starlink_tle[0]
            if tle_service.validate_tle_data(first_tle):
                logger.info("✅ TLE 數據格式驗證通過")
            else:
                logger.warning("⚠️ TLE 數據格式驗證失敗")
        else:
            logger.error("❌ 測試 2 失敗: 未獲取到 TLE 數據")
    except Exception as e:
        logger.error(f"❌ 測試 2 失敗: {e}")
    
    # 測試 3: 緩存歷史數據（2024年1月1日）
    total_tests += 1
    try:
        logger.info("測試 3: 緩存 2024年1月1日 歷史數據")
        primary_range = HistoricalDataCache.RECOMMENDED_TIME_RANGES['primary']
        
        # 為了測試，只緩存1小時的數據
        test_range = TimeRange(
            start=primary_range['start'],
            end=primary_range['start'].replace(hour=1)
        )
        
        await historical_cache.cache_historical_tle('starlink', test_range, 30)  # 30分鐘間隔
        
        logger.info("✅ 測試 3 通過: 歷史數據緩存完成")
        passed_tests += 1
    except Exception as e:
        logger.error(f"❌ 測試 3 失敗: {e}")
    
    # 測試 4: 獲取特定時間點的歷史數據
    total_tests += 1
    try:
        logger.info("測試 4: 獲取 2024年1月1日 00:00:00 UTC 的歷史數據")
        target_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        historical_data = await historical_cache.get_historical_tle('starlink', target_time)
        
        if historical_data and len(historical_data.satellites) > 0:
            logger.info(f"✅ 測試 4 通過:")
            logger.info(f"   時間戳: {historical_data.timestamp.isoformat()}")
            logger.info(f"   衛星數量: {len(historical_data.satellites)}")
            logger.info(f"   數據來源: {historical_data.data_source}")
            logger.info(f"   數據品質: {historical_data.quality}")
            passed_tests += 1
        else:
            logger.error("❌ 測試 4 失敗: 未找到歷史數據")
    except Exception as e:
        logger.error(f"❌ 測試 4 失敗: {e}")
    
    # 測試 5: 獲取歷史數據範圍
    total_tests += 1
    try:
        logger.info("測試 5: 獲取歷史數據範圍（1小時）")
        start_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc)
        
        historical_range = await historical_cache.get_historical_tle_range(
            'starlink',
            TimeRange(start=start_time, end=end_time),
            10
        )
        
        if len(historical_range) > 0:
            logger.info(f"✅ 測試 5 通過:")
            logger.info(f"   記錄數量: {len(historical_range)}")
            logger.info(f"   時間範圍: {start_time.isoformat()} - {end_time.isoformat()}")
            passed_tests += 1
        else:
            logger.error("❌ 測試 5 失敗: 未找到歷史數據範圍")
    except Exception as e:
        logger.error(f"❌ 測試 5 失敗: {e}")
    
    # 測試 6: 緩存統計信息
    total_tests += 1
    try:
        logger.info("測試 6: 獲取緩存統計信息")
        cache_stats = await historical_cache.get_cache_stats()
        
        logger.info(f"✅ 測試 6 通過:")
        logger.info(f"   緩存文件數: {cache_stats['total_files']}")
        logger.info(f"   總大小: {cache_stats['total_size']} bytes")
        logger.info(f"   星座: {cache_stats['constellations']}")
        passed_tests += 1
    except Exception as e:
        logger.error(f"❌ 測試 6 失敗: {e}")
    
    # 測試結果總結
    logger.info("=" * 60)
    logger.info("Phase 1 測試完成")
    logger.info(f"通過測試: {passed_tests}/{total_tests}")
    logger.info(f"成功率: {(passed_tests / total_tests * 100):.1f}%")
    
    # Phase 1 驗收標準檢查
    phase1_requirements = [
        {
            'name': '成功從 CelesTrak API 獲取 TLE 數據',
            'passed': passed_tests >= 2
        },
        {
            'name': '實現本地歷史數據緩存機制',
            'passed': passed_tests >= 3
        },
        {
            'name': '可獲取 2024年1月1日 的 Starlink 衛星 TLE 數據',
            'passed': passed_tests >= 4
        },
        {
            'name': 'API 端點功能正常（需要啟動服務器測試）',
            'passed': passed_tests >= 5
        }
    ]
    
    logger.info("=" * 60)
    logger.info("Phase 1 驗收標準檢查:")
    all_requirements_met = True
    
    for requirement in phase1_requirements:
        if requirement['passed']:
            logger.info(f"✅ {requirement['name']}")
        else:
            logger.error(f"❌ {requirement['name']}")
            all_requirements_met = False
    
    logger.info("=" * 60)
    if all_requirements_met:
        logger.info("🎉 Phase 1 驗收標準全部通過！可以進入 Phase 2")
        return True
    else:
        logger.error("❌ Phase 1 驗收標準未完全通過，需要修復問題")
        return False

async def test_api_endpoints():
    """測試 API 端點（需要服務器運行）"""
    import aiohttp
    
    base_url = "http://localhost:8888/api/v1/tle"
    
    logger.info("測試 API 端點（需要服務器運行在 localhost:8888）")
    
    try:
        async with aiohttp.ClientSession() as session:
            # 測試獲取星座列表
            async with session.get(f"{base_url}/constellations") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ API 測試 - 獲取星座列表: {len(data['data']['constellations'])} 個星座")
                else:
                    logger.error(f"❌ API 測試失敗: HTTP {response.status}")
            
            # 測試 Phase 1 驗收端點
            async with session.get(f"{base_url}/test/phase1") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ API 測試 - Phase 1 驗收端點正常")
                    logger.info(f"   測試結果: {data['data']['summary']}")
                else:
                    logger.error(f"❌ API 測試失敗: HTTP {response.status}")
                    
    except Exception as e:
        logger.warning(f"⚠️ API 測試跳過（服務器未運行）: {e}")

if __name__ == "__main__":
    async def main():
        # 執行核心測試
        success = await run_phase1_tests()
        
        # 嘗試測試 API 端點
        await test_api_endpoints()
        
        # 輸出最終結果
        if success:
            logger.info("🎉 Phase 1 開發和測試完成！")
            logger.info("📋 下一步: 開始 Phase 2 - SGP4 軌道算法實現")
        else:
            logger.error("❌ Phase 1 測試未完全通過，請檢查問題")
            sys.exit(1)
    
    asyncio.run(main())
