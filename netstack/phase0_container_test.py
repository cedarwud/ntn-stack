#!/usr/bin/env python3
"""
Phase 0 容器內測試 - 驗證 Starlink 數據下載和基本分析功能
"""
import asyncio
import logging
import sys
from datetime import datetime, timezone

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_skyfield_basic():
    """測試 skyfield 基本功能"""
    try:
        from skyfield.api import load, EarthSatellite, wgs84
        logger.info('✅ skyfield 導入成功')
        
        # 測試創建地球和時間尺度
        ts = load.timescale()
        earth = wgs84
        t = ts.now()
        
        # 測試 TLE 數據解析
        line1 = '1 44713U 19074A   21001.00000000  .00000000  00000-0  00000-0 0  9990'
        line2 = '2 44713  53.0000 180.0000 0000000   0.0000   0.0000 15.50000000000000'
        sat = EarthSatellite(line1, line2, 'TEST-SAT')
        
        # 測試位置計算
        geocentric = sat.at(t)
        logger.info(f'✅ 衛星位置計算成功: {geocentric.distance().km:.1f} km')
        
        # 測試觀察者位置
        observer = earth.latlon(24.9441667, 121.3713889)  # NTPU
        difference = sat - observer
        topocentric = difference.at(t)
        alt, az, distance = topocentric.altaz()
        
        logger.info(f'✅ 觀察者視角計算成功: 仰角 {alt.degrees:.1f}°, 方位角 {az.degrees:.1f}°')
        
        return True
    except Exception as e:
        logger.error(f'❌ skyfield 測試失敗: {e}')
        return False

async def test_tle_download():
    """測試 TLE 數據下載"""
    try:
        import aiohttp
        logger.info('✅ aiohttp 導入成功')
        
        # 測試下載少量 Starlink TLE 數據
        url = 'https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle'
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    lines = content.strip().split('\n')
                    
                    # 簡單解析 TLE 數據
                    satellites = []
                    for i in range(0, len(lines), 3):
                        if i + 2 < len(lines):
                            name = lines[i].strip()
                            line1 = lines[i + 1].strip()
                            line2 = lines[i + 2].strip()
                            
                            if line1.startswith('1 ') and line2.startswith('2 '):
                                satellites.append({'name': name, 'line1': line1, 'line2': line2})
                    
                    logger.info(f'✅ 成功下載 {len(satellites)} 顆 Starlink 衛星數據')
                    return len(satellites) > 0
                else:
                    logger.error(f'❌ TLE 下載失敗: HTTP {response.status}')
                    return False
                    
    except Exception as e:
        logger.error(f'❌ TLE 下載測試失敗: {e}')
        return False

async def test_prefilter_logic():
    """測試預篩選邏輯"""
    try:
        import math
        
        # 測試軌道參數預篩選邏輯
        observer_lat = 24.9441667  # NTPU 緯度
        
        # 模擬一些 Starlink 軌道參數
        test_orbits = [
            {'inclination': 53.0, 'altitude': 550},  # 標準 Starlink
            {'inclination': 70.0, 'altitude': 570},  # 極軌 Starlink
            {'inclination': 97.6, 'altitude': 540},  # 太陽同步軌道
            {'inclination': 0.0, 'altitude': 35786}, # 地球同步軌道 (應被排除)
        ]
        
        candidates = 0
        excluded = 0
        
        for orbit in test_orbits:
            # 簡單的緯度覆蓋檢查
            max_reachable_lat = orbit['inclination']
            if abs(observer_lat) <= max_reachable_lat + 10:  # 加10度容忍度
                candidates += 1
                logger.info(f'✅ 候選軌道: 傾角 {orbit["inclination"]}°, 高度 {orbit["altitude"]} km')
            else:
                excluded += 1
                logger.info(f'❌ 排除軌道: 傾角 {orbit["inclination"]}°, 高度 {orbit["altitude"]} km')
        
        reduction_ratio = excluded / len(test_orbits) * 100
        logger.info(f'✅ 預篩選測試完成: {candidates} 候選, {excluded} 排除 (減少 {reduction_ratio:.1f}%)')
        
        return True
        
    except Exception as e:
        logger.error(f'❌ 預篩選測試失敗: {e}')
        return False

async def test_optimal_timeframe_concept():
    """測試最佳時間段概念"""
    try:
        from datetime import datetime, timedelta
        
        # 模擬一個96分鐘時間窗內的最佳時間段搜索
        base_time = datetime.now(timezone.utc)
        
        best_score = 0
        best_timeframe = None
        
        # 掃描不同的時間段 (簡化版)
        for start_minutes in range(0, 96, 15):  # 每15分鐘檢查一次
            for duration in [30, 35, 40, 45]:
                if start_minutes + duration > 96:
                    continue
                
                # 模擬評分 (基於時間段中點接近中午時分數較高)
                midpoint = start_minutes + duration // 2
                score = max(0, 100 - abs(midpoint - 48))  # 48分鐘接近中點
                
                if score > best_score:
                    best_score = score
                    best_timeframe = {
                        'start_minutes': start_minutes,
                        'duration': duration,
                        'score': score
                    }
        
        if best_timeframe:
            start_time = base_time + timedelta(minutes=best_timeframe['start_minutes'])
            logger.info(f'✅ 找到最佳時間段: {start_time.strftime("%H:%M:%S")}, '
                       f'持續 {best_timeframe["duration"]} 分鐘, '
                       f'評分 {best_timeframe["score"]}')
            return True
        else:
            logger.error('❌ 未找到最佳時間段')
            return False
            
    except Exception as e:
        logger.error(f'❌ 最佳時間段測試失敗: {e}')
        return False

async def main():
    """主測試函數"""
    logger.info('🚀 開始 Phase 0 容器內功能測試')
    
    tests = [
        ('skyfield 基本功能', test_skyfield_basic),
        ('TLE 數據下載', test_tle_download),
        ('預篩選邏輯', test_prefilter_logic),
        ('最佳時間段概念', test_optimal_timeframe_concept),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f'\n=== 測試: {test_name} ===')
        try:
            result = await test_func()
            if result:
                passed += 1
                logger.info(f'✅ {test_name} 測試通過')
            else:
                logger.error(f'❌ {test_name} 測試失敗')
        except Exception as e:
            logger.error(f'❌ {test_name} 測試異常: {e}')
    
    success_rate = passed / total * 100
    logger.info(f'\n📊 測試總結: {passed}/{total} 通過 (成功率 {success_rate:.1f}%)')
    
    if success_rate >= 75:
        logger.info('🎉 Phase 0 容器內測試基本通過！')
        return True
    else:
        logger.error('💥 Phase 0 容器內測試未通過！')
        return False

if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)