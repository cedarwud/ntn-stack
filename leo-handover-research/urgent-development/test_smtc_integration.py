#!/usr/bin/env python3
"""
🧪 SMTC 測量優化系統整合測試
================================

測試 SMTC 優化系統與 HandoverEventDetector 的整合

作者: Claude Sonnet 4 (SuperClaude)
版本: v1.0
日期: 2025-08-01
"""

import sys
import os
import time
import logging

# 添加必要的路徑
sys.path.append('/home/sat/ntn-stack/netstack/src/services/satellite')

def test_smtc_integration():
    """測試 SMTC 系統整合"""
    logger = logging.getLogger(__name__)
    logger.info("🧪 開始 SMTC 測量優化系統整合測試")
    
    try:
        # 導入 HandoverEventDetector
        from handover_event_detector import HandoverEventDetector
        
        # 創建檢測器實例
        detector = HandoverEventDetector(scene_id="ntpu")
        
        # 創建測試衛星數據
        satellite_data = {
            'STARLINK-1234': {
                'elevation_deg': 45.0,
                'azimuth_deg': 180.0,
                'orbit_period_sec': 5400,
                'position': (25.0, 122.0, 550),
                'range_km': 800.0,
                'frequency_ghz': 28.0,
                'rsrp_dbm': -95.0
            },
            'STARLINK-5678': {
                'elevation_deg': 30.0,
                'azimuth_deg': 90.0,
                'orbit_period_sec': 5400,
                'position': (24.0, 121.0, 550),
                'range_km': 850.0,
                'frequency_ghz': 28.0,
                'rsrp_dbm': -105.0
            },
            'STARLINK-9999': {
                'elevation_deg': 60.0,
                'azimuth_deg': 270.0,
                'orbit_period_sec': 5400,
                'position': (26.0, 120.0, 550),
                'range_km': 750.0,
                'frequency_ghz': 28.0,
                'rsrp_dbm': -88.0  
            }
        }
        
        # 測量需求配置
        measurement_requirements = {
            'high_accuracy_mode': True,
            'power_efficiency_mode': False,
            'priority_satellites': ['STARLINK-1234', 'STARLINK-9999']
        }
        
        # 功耗預算
        power_budget = 4000.0  # 4W
        
        # 執行 SMTC 配置優化
        logger.info("🔄 執行 SMTC 配置優化...")
        smtc_result = detector.optimize_smtc_configuration(
            satellite_data, measurement_requirements, power_budget)
        
        # 輸出結果
        logger.info("✅ SMTC 配置優化完成")
        logger.info(f"📊 配置概要:")
        config = smtc_result['smtc_config']
        logger.info(f"  • 配置ID: {config['config_id']}")
        logger.info(f"  • 週期性: {config['periodicity_ms']} ms")
        logger.info(f"  • 偏移量: {config['offset_ms']} ms")
        logger.info(f"  • 持續時間: {config['duration_ms']} ms")
        logger.info(f"  • 總功耗: {config['total_power_consumption']:.1f} mW")
        logger.info(f"  • 效率評分: {config['efficiency_score']:.2f}")
        
        # 測量窗口詳情
        windows = smtc_result['measurement_windows']
        logger.info(f"📋 測量窗口 ({len(windows)} 個):")
        for i, window in enumerate(windows):
            logger.info(f"  窗口 {i+1}: {window['window_id']}")
            logger.info(f"    ⏰ 開始時間: {window['start_time']:.1f}")
            logger.info(f"    ⏱️  持續時間: {window['duration_ms']} ms")
            logger.info(f"    📡 目標衛星: {window['target_satellites']}")
            logger.info(f"    📊 測量類型: {window['measurement_types']}")
            logger.info(f"    🎯 優先級: {window['priority']}")
            logger.info(f"    ⚡ 功耗: {window['power_budget']:.1f} mW")
        
        # 配置建議
        if smtc_result['configuration_advice']:
            logger.info(f"💡 配置建議:")
            for advice in smtc_result['configuration_advice']:
                logger.info(f"  • {advice}")
        
        # 自適應參數
        if smtc_result['adaptive_parameters']:
            logger.info(f"🔧 自適應參數:")
            params = smtc_result['adaptive_parameters']
            if 'average_elevation_deg' in params:
                logger.info(f"  • 平均仰角: {params['average_elevation_deg']:.1f}°")
            if 'average_confidence' in params:
                logger.info(f"  • 平均信心度: {params['average_confidence']:.2f}")
            if 'priority_distribution' in params:
                logger.info(f"  • 優先級分布: {params['priority_distribution']}")
        
        # 驗證結果合理性
        assert config['periodicity_ms'] > 0, "週期性應大於0"
        assert config['efficiency_score'] >= 0, "效率評分應非負"
        assert len(windows) > 0, "應有至少一個測量窗口"
        assert config['total_power_consumption'] <= power_budget, "功耗不應超過預算"
        
        logger.info("✅ 所有驗證通過")
        logger.info("🎉 SMTC 測量優化系統整合測試成功")
        
        return smtc_result
        
    except ImportError as e:
        logger.error(f"❌ 模組導入失敗: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ 測試執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_measurement_efficiency():
    """測試測量效率改善"""
    logger = logging.getLogger(__name__)
    logger.info("📈 測試測量效率改善")
    
    try:
        from handover_event_detector import HandoverEventDetector
        
        detector = HandoverEventDetector(scene_id="ntpu")
        
        # 模擬不同場景的衛星數據
        scenarios = {
            'low_elevation': {
                'STARLINK-1234': {
                    'elevation_deg': 15.0,
                    'position': (25.0, 122.0, 550),
                    'rsrp_dbm': -115.0
                }
            },
            'high_elevation': {
                'STARLINK-5678': {
                    'elevation_deg': 70.0,
                    'position': (24.0, 121.0, 550),
                    'rsrp_dbm': -85.0
                }
            },
            'mixed_elevation': {
                'STARLINK-1234': {
                    'elevation_deg': 45.0,
                    'position': (25.0, 122.0, 550),
                    'rsrp_dbm': -95.0
                },
                'STARLINK-5678': {
                    'elevation_deg': 25.0,
                    'position': (24.0, 121.0, 550),
                    'rsrp_dbm': -108.0
                },
                'STARLINK-9999': {
                    'elevation_deg': 65.0,
                    'position': (26.0, 120.0, 550),
                    'rsrp_dbm': -88.0
                }
            }
        }
        
        efficiency_results = {}
        
        for scenario_name, sat_data in scenarios.items():
            logger.info(f"🔄 測試場景: {scenario_name}")
            
            # 高精度模式
            high_accuracy_req = {
                'high_accuracy_mode': True,
                'power_efficiency_mode': False
            }
            
            # 效率模式
            efficiency_req = {
                'high_accuracy_mode': False,
                'power_efficiency_mode': True
            }
            
            # 比較兩種模式
            high_acc_result = detector.optimize_smtc_configuration(
                sat_data, high_accuracy_req, 5000.0)
            
            efficiency_result = detector.optimize_smtc_configuration(
                sat_data, efficiency_req, 3000.0)
            
            efficiency_results[scenario_name] = {
                'high_accuracy': {
                    'efficiency_score': high_acc_result['smtc_config']['efficiency_score'],
                    'power_consumption': high_acc_result['smtc_config']['total_power_consumption'],
                    'window_count': len(high_acc_result['measurement_windows'])
                },
                'power_efficiency': {
                    'efficiency_score': efficiency_result['smtc_config']['efficiency_score'],
                    'power_consumption': efficiency_result['smtc_config']['total_power_consumption'],
                    'window_count': len(efficiency_result['measurement_windows'])
                }
            }
            
            logger.info(f"  高精度模式: 效率={high_acc_result['smtc_config']['efficiency_score']:.2f}, "
                       f"功耗={high_acc_result['smtc_config']['total_power_consumption']:.1f}mW")
            logger.info(f"  效率模式: 效率={efficiency_result['smtc_config']['efficiency_score']:.2f}, "
                       f"功耗={efficiency_result['smtc_config']['total_power_consumption']:.1f}mW")
        
        # 分析效率改善
        logger.info("📊 效率改善分析:")
        for scenario, results in efficiency_results.items():
            high_acc = results['high_accuracy']
            power_eff = results['power_efficiency']
            
            power_saving = ((high_acc['power_consumption'] - power_eff['power_consumption']) / 
                           high_acc['power_consumption']) * 100
            
            logger.info(f"  {scenario}: 功耗節省 {power_saving:.1f}%")
        
        logger.info("✅ 測量效率測試完成")
        return efficiency_results
        
    except Exception as e:
        logger.error(f"❌ 效率測試失敗: {e}")
        return None


if __name__ == "__main__":
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    # 執行測試
    logger.info("🚀 開始 SMTC 測量優化系統整合測試套件")
    
    # 基本整合測試
    result1 = test_smtc_integration()
    
    # 效率改善測試
    result2 = test_measurement_efficiency()
    
    if result1 and result2:
        logger.info("🎉 所有測試通過！SMTC 測量優化系統整合成功")
    else:
        logger.error("❌ 測試失敗")
        sys.exit(1)