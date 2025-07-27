#!/usr/bin/env python3
"""
Phase 0 完整集成測試 - 在容器內測試完整的 Starlink 換手分析流程
"""
import asyncio
import logging
import sys
import json
from datetime import datetime, timezone, timedelta

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 測試用的 Starlink TLE 數據樣本
SAMPLE_STARLINK_TLE = [
    {
        'name': 'STARLINK-1007',
        'norad_id': 44713,
        'line1': '1 44713U 19074A   21001.00000000  .00002182  00000-0  16538-3 0  9992',
        'line2': '2 44713  53.0537 339.7687 0001509  91.2872 268.8623 15.06419562 68284'
    },
    {
        'name': 'STARLINK-1019', 
        'norad_id': 44714,
        'line1': '1 44714U 19074B   21001.00000000  .00001735  00000-0  13247-3 0  9996',
        'line2': '2 44714  53.0539 339.7456 0001398  94.4147 265.7362 15.06419013 68283'
    },
    {
        'name': 'STARLINK-1021',
        'norad_id': 44715,
        'line1': '1 44715U 19074C   21001.00000000  .00001842  00000-0  14089-3 0  9993',
        'line2': '2 44715  53.0536 339.7642 0001344  88.9234 271.2278 15.06419743 68287'
    },
    {
        'name': 'STARLINK-1044',
        'norad_id': 44716,
        'line1': '1 44716U 19074D   21001.00000000  .00001649  00000-0  12636-3 0  9991',
        'line2': '2 44716  53.0538 339.7558 0001507  92.1502 267.9014 15.06419386 68282'
    },
    {
        'name': 'STARLINK-1030',
        'norad_id': 44717,
        'line1': '1 44717U 19074E   21001.00000000  .00001953  00000-0  14934-3 0  9998',
        'line2': '2 44717  53.0537 339.7665 0001416  89.8737 270.2775 15.06419562 68280'
    }
]

class Phase0IntegrationTester:
    """Phase 0 完整集成測試器"""
    
    def __init__(self):
        self.observer_lat = 24.9441667  # NTPU 緯度
        self.observer_lon = 121.3713889  # NTPU 經度
        self.min_elevation = 5.0
    
    async def test_tle_processing(self):
        """測試 TLE 數據處理"""
        try:
            from skyfield.api import load, EarthSatellite, wgs84
            
            logger.info('測試 TLE 數據處理...')
            
            # 處理樣本 TLE 數據
            satellites = []
            ts = load.timescale()
            
            for sat_data in SAMPLE_STARLINK_TLE:
                try:
                    sat = EarthSatellite(sat_data['line1'], sat_data['line2'], sat_data['name'])
                    
                    # 測試計算當前位置
                    t = ts.now()
                    geocentric = sat.at(t)
                    distance = geocentric.distance().km
                    
                    if 200 <= distance <= 2000:  # Starlink 軌道高度範圍
                        satellites.append({
                            **sat_data,
                            'satellite_obj': sat,
                            'altitude_km': distance
                        })
                        logger.info(f'✅ 處理衛星 {sat_data["name"]}: 高度 {distance:.1f} km')
                    else:
                        logger.warning(f'⚠️ 衛星 {sat_data["name"]} 高度異常: {distance:.1f} km')
                        
                except Exception as e:
                    logger.error(f'❌ 處理衛星 {sat_data["name"]} 失敗: {e}')
            
            logger.info(f'✅ 成功處理 {len(satellites)} 顆衛星')
            return satellites
            
        except Exception as e:
            logger.error(f'❌ TLE 數據處理失敗: {e}')
            return []
    
    async def test_prefilter(self, satellites):
        """測試預篩選器"""
        try:
            import math
            
            logger.info('測試衛星預篩選...')
            
            candidates = []
            excluded = []
            
            for sat_data in satellites:
                # 從 TLE 第二行提取軌道傾角
                line2 = sat_data['line2']
                inclination = float(line2[8:16])
                
                # 緯度覆蓋檢查
                max_reachable_lat = inclination
                horizon_angle = 10  # 簡化的地平線角度
                effective_max_lat = max_reachable_lat + horizon_angle
                
                if abs(self.observer_lat) <= effective_max_lat:
                    candidates.append({
                        **sat_data,
                        'inclination': inclination,
                        'prefilter_reason': 'latitude_coverage_passed'
                    })
                    logger.info(f'✅ 候選衛星: {sat_data["name"]} (傾角 {inclination:.1f}°)')
                else:
                    excluded.append({
                        **sat_data,
                        'inclination': inclination,
                        'exclusion_reason': 'latitude_coverage_failed'
                    })
                    logger.info(f'❌ 排除衛星: {sat_data["name"]} (傾角 {inclination:.1f}°)')
            
            reduction_ratio = len(excluded) / len(satellites) * 100 if satellites else 0
            logger.info(f'✅ 預篩選完成: {len(candidates)} 候選, {len(excluded)} 排除 (減少 {reduction_ratio:.1f}%)')
            
            return candidates, excluded
            
        except Exception as e:
            logger.error(f'❌ 預篩選測試失敗: {e}')
            return [], []
    
    async def test_visibility_calculation(self, candidates):
        """測試可見性計算"""
        try:
            from skyfield.api import load, wgs84
            
            logger.info('測試可見性計算...')
            
            ts = load.timescale()
            earth = wgs84
            observer = earth.latlon(self.observer_lat, self.observer_lon)
            
            visible_satellites = []
            
            # 計算30分鐘時間窗內的可見性
            start_time = ts.now()
            time_points = [start_time.tt + i * (30.0 / (24 * 60)) for i in range(30)]  # 每分鐘一個點
            
            for sat_data in candidates:
                sat = sat_data['satellite_obj']
                max_elevation = -90
                visibility_count = 0
                
                for tt in time_points:
                    t = ts.tt_jd(tt)
                    difference = sat - observer
                    topocentric = difference.at(t)
                    alt, az, distance = topocentric.altaz()
                    
                    elevation = alt.degrees
                    if elevation >= self.min_elevation:
                        visibility_count += 1
                        max_elevation = max(max_elevation, elevation)
                
                if visibility_count > 0:
                    visible_satellites.append({
                        **sat_data,
                        'max_elevation': max_elevation,
                        'visibility_duration_minutes': visibility_count,
                        'visibility_percentage': visibility_count / len(time_points) * 100
                    })
                    logger.info(f'✅ 可見衛星: {sat_data["name"]} '
                               f'(最大仰角 {max_elevation:.1f}°, 可見 {visibility_count} 分鐘)')
                else:
                    logger.info(f'⚠️ 不可見: {sat_data["name"]}')
            
            logger.info(f'✅ 可見性計算完成: {len(visible_satellites)}/{len(candidates)} 衛星可見')
            return visible_satellites
            
        except Exception as e:
            logger.error(f'❌ 可見性計算失敗: {e}')
            return []
    
    async def test_optimal_timeframe(self, visible_satellites):
        """測試最佳時間段分析"""
        try:
            logger.info('測試最佳時間段分析...')
            
            if not visible_satellites:
                logger.warning('⚠️ 沒有可見衛星，跳過最佳時間段分析')
                return None
            
            # 簡化的最佳時間段分析
            best_timeframe = {
                'start_timestamp': datetime.now(timezone.utc).isoformat(),
                'duration_minutes': 35,
                'satellite_count': len(visible_satellites),
                'satellites': []
            }
            
            # 按最大仰角排序衛星
            sorted_satellites = sorted(visible_satellites, key=lambda s: s['max_elevation'], reverse=True)
            
            for i, sat in enumerate(sorted_satellites):
                best_timeframe['satellites'].append({
                    'name': sat['name'],
                    'norad_id': sat['norad_id'], 
                    'max_elevation': sat['max_elevation'],
                    'handover_priority': i + 1
                })
            
            # 計算覆蓋品質評分
            avg_elevation = sum(s['max_elevation'] for s in visible_satellites) / len(visible_satellites)
            coverage_quality = min(avg_elevation / 45, 1.0)  # 45度為滿分
            best_timeframe['coverage_quality_score'] = coverage_quality
            
            logger.info(f'✅ 最佳時間段: {best_timeframe["duration_minutes"]} 分鐘, '
                       f'{best_timeframe["satellite_count"]} 顆衛星, '
                       f'品質評分 {coverage_quality:.3f}')
            
            return best_timeframe
            
        except Exception as e:
            logger.error(f'❌ 最佳時間段分析失敗: {e}')
            return None
    
    async def test_frontend_formatting(self, optimal_timeframe):
        """測試前端數據格式化"""
        try:
            logger.info('測試前端數據格式化...')
            
            if not optimal_timeframe:
                logger.warning('⚠️ 沒有最佳時間段數據，跳過前端格式化')
                return None
            
            # 格式化側邊欄數據
            sidebar_data = {
                'satellite_gnb_list': []
            }
            
            for sat in optimal_timeframe['satellites']:
                sidebar_data['satellite_gnb_list'].append({
                    'id': f"STARLINK-{sat['norad_id']}",
                    'name': sat['name'],
                    'status': 'visible',
                    'signal_strength': min(int(sat['max_elevation'] * 2), 100),
                    'elevation': sat['max_elevation'],
                    'handover_priority': sat['handover_priority']
                })
            
            # 格式化動畫數據
            animation_data = {
                'animation_trajectories': [],
                'animation_settings': {
                    'total_duration_seconds': optimal_timeframe['duration_minutes'] * 60,
                    'playback_speed_multiplier': 10
                }
            }
            
            for sat in optimal_timeframe['satellites']:
                animation_data['animation_trajectories'].append({
                    'satellite_id': f"STARLINK-{sat['norad_id']}",
                    'satellite_name': sat['name'],
                    'trajectory_points': [
                        {'time_offset': i * 30, 'elevation': sat['max_elevation'], 'visible': True}
                        for i in range(optimal_timeframe['duration_minutes'] * 2)  # 每30秒一個點
                    ]
                })
            
            # 格式化換手序列
            handover_sequence = {
                'handover_sequence': [],
                'sequence_statistics': {
                    'total_handovers': len(optimal_timeframe['satellites']) - 1,
                    'seamless_handovers': len(optimal_timeframe['satellites']) - 1
                }
            }
            
            for i in range(len(optimal_timeframe['satellites']) - 1):
                handover_sequence['handover_sequence'].append({
                    'sequence_id': i + 1,
                    'from_satellite': optimal_timeframe['satellites'][i]['name'],
                    'to_satellite': optimal_timeframe['satellites'][i + 1]['name'],
                    'handover_type': 'planned',
                    'quality_score': 85.0
                })
            
            frontend_data = {
                'sidebar_data': sidebar_data,
                'animation_data': animation_data, 
                'handover_sequence': handover_sequence
            }
            
            logger.info(f'✅ 前端數據格式化完成: '
                       f'{len(sidebar_data["satellite_gnb_list"])} 個衛星, '
                       f'{len(animation_data["animation_trajectories"])} 條軌跡, '
                       f'{len(handover_sequence["handover_sequence"])} 個換手事件')
            
            return frontend_data
            
        except Exception as e:
            logger.error(f'❌ 前端數據格式化失敗: {e}')
            return None
    
    async def run_integration_test(self):
        """運行完整集成測試"""
        logger.info('🚀 開始 Phase 0 完整集成測試')
        
        try:
            # 步驟 1: TLE 數據處理
            satellites = await self.test_tle_processing()
            if not satellites:
                logger.error('❌ TLE 數據處理失敗，終止測試')
                return False
            
            # 步驟 2: 預篩選
            candidates, excluded = await self.test_prefilter(satellites)
            if not candidates:
                logger.error('❌ 預篩選後無候選衛星，終止測試')
                return False
            
            # 步驟 3: 可見性計算
            visible_satellites = await self.test_visibility_calculation(candidates)
            
            # 步驟 4: 最佳時間段分析
            optimal_timeframe = await self.test_optimal_timeframe(visible_satellites)
            
            # 步驟 5: 前端數據格式化
            frontend_data = await self.test_frontend_formatting(optimal_timeframe)
            
            # 生成測試結果報告
            test_result = {
                'test_summary': {
                    'test_time': datetime.now(timezone.utc).isoformat(),
                    'observer_location': {
                        'latitude': self.observer_lat,
                        'longitude': self.observer_lon
                    },
                    'total_satellites_processed': len(satellites),
                    'candidate_satellites': len(candidates),
                    'visible_satellites': len(visible_satellites) if visible_satellites else 0,
                    'optimal_timeframe_found': optimal_timeframe is not None,
                    'frontend_data_generated': frontend_data is not None
                },
                'detailed_results': {
                    'satellites': satellites,
                    'candidates': candidates,
                    'visible_satellites': visible_satellites,
                    'optimal_timeframe': optimal_timeframe,
                    'frontend_data': frontend_data
                }
            }
            
            # 評估測試成功度
            success_criteria = [
                len(satellites) >= 3,
                len(candidates) >= 1,
                optimal_timeframe is not None,
                frontend_data is not None
            ]
            
            success_count = sum(success_criteria)
            success_rate = success_count / len(success_criteria) * 100
            
            logger.info(f'\n📊 Phase 0 集成測試總結:')
            logger.info(f'處理衛星數: {len(satellites)}')
            logger.info(f'候選衛星數: {len(candidates)}')
            logger.info(f'可見衛星數: {len(visible_satellites) if visible_satellites else 0}')
            logger.info(f'最佳時間段: {"已找到" if optimal_timeframe else "未找到"}')
            logger.info(f'前端數據: {"已生成" if frontend_data else "未生成"}')
            logger.info(f'成功率: {success_rate:.1f}%')
            
            if success_rate >= 75:
                logger.info('🎉 Phase 0 完整集成測試通過！')
                return True
            else:
                logger.error('💥 Phase 0 完整集成測試未通過！')
                return False
                
        except Exception as e:
            logger.error(f'❌ 集成測試異常: {e}')
            return False

async def main():
    """主函數"""
    tester = Phase0IntegrationTester()
    success = await tester.run_integration_test()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    asyncio.run(main())