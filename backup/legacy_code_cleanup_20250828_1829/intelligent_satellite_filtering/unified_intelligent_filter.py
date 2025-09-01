#!/usr/bin/env python3
"""
統一智能篩選系統 - 完整整合版本

整合所有功能模組，提供完整的三階段智能篩選流程：
1. 星座分離篩選
2. 地理相關性篩選  
3. 換手適用性評分
4. 信號品質評估 (新增)
5. 3GPP 事件分析 (新增)
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import sys

# 添加模組路徑
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 導入所有功能模組
from constellation_separation.constellation_separator import ConstellationSeparator
from geographic_filtering.geographic_filter import GeographicFilter
from handover_scoring.handover_scorer import HandoverScorer
from signal_calculation.rsrp_calculator import RSRPCalculator, create_rsrp_calculator
from event_analysis.gpp_event_analyzer import GPPEventAnalyzer, create_gpp_event_analyzer

logger = logging.getLogger(__name__)


class UnifiedIntelligentFilter:
    """統一智能篩選系統
    
    完整的模組化智能篩選架構，整合所有功能
    """
    
    def __init__(self, observer_lat: float = 24.9441667, observer_lon: float = 121.3713889):
        """
        初始化統一智能篩選系統
        
        Args:
            observer_lat: 觀測點緯度 (NTPU)
            observer_lon: 觀測點經度 (NTPU)
        """
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon
        
        # 初始化所有功能模組
        self.constellation_separator = ConstellationSeparator()
        self.geographic_filter = GeographicFilter()
        self.handover_scorer = HandoverScorer()
        self.rsrp_calculator = create_rsrp_calculator(observer_lat, observer_lon)
        self.event_analyzer = create_gpp_event_analyzer(self.rsrp_calculator)
        
        logger.info("🚀 統一智能篩選系統初始化完成")
        logger.info(f"📍 觀測點: NTPU ({observer_lat:.4f}°N, {observer_lon:.4f}°E)")
        logger.info("✅ 已載入: 星座分離 + 地理篩選 + 換手評分 + 信號計算 + 事件分析")
    
    def process_complete_filtering(self, 
                                 sgp4_data: Dict[str, Any], 
                                 selection_config: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """
        執行完整的智能篩選流程
        
        Args:
            sgp4_data: 階段一輸出的完整衛星軌道數據
            selection_config: 選擇配置。如果為None，則使用動態篩選（推薦）
            
        Returns:
            完整篩選後的數據，包含信號品質和事件分析
        """
        logger.info("🎯 開始完整智能篩選流程")
        
        # 提取衛星數據
        all_satellites = self._extract_satellites_from_sgp4_data(sgp4_data)
        total_input = len(all_satellites)
        logger.info(f"📡 輸入衛星總數: {total_input}")
        
        # === 階段 2.1：星座分離篩選 ===
        logger.info("⚙️ 執行階段 2.1: 星座分離篩選")
        separated_data = self.constellation_separator.separate_constellations(all_satellites)
        constellation_filtered = self.constellation_separator.apply_constellation_specific_filtering(separated_data)
        
        sep_stats = self.constellation_separator.get_separation_statistics(constellation_filtered)
        stage1_total = sum(len(sats) for sats in constellation_filtered.values())
        logger.info(f"✅ 星座分離完成: {stage1_total}/{total_input} 顆衛星保留 "
                   f"(Starlink: {len(constellation_filtered.get('starlink', []))}, "
                   f"OneWeb: {len(constellation_filtered.get('oneweb', []))})")
        
        # === 階段 2.2：地理相關性篩選 ===
        logger.info("🌍 執行階段 2.2: 地理相關性篩選")
        geo_filtered = self.geographic_filter.apply_geographic_filtering(constellation_filtered)
        
        geo_stats = self.geographic_filter.get_filtering_statistics(constellation_filtered, geo_filtered)
        stage2_total = sum(len(sats) for sats in geo_filtered.values())
        logger.info(f"✅ 地理篩選完成: {stage2_total}/{stage1_total} 顆衛星保留 "
                   f"(減少 {geo_stats['overall_reduction']['reduction_rate_percent']:.1f}%)")
        
        # === 階段 2.3：換手適用性評分 ===
        logger.info("📊 執行階段 2.3: 換手適用性評分")
        scored_data = self.handover_scorer.apply_handover_scoring(geo_filtered)
        
        scoring_stats = self.handover_scorer.get_scoring_statistics(scored_data)
        stage3_total = sum(len(sats) for sats in scored_data.values())
        logger.info(f"✅ 換手評分完成: {stage3_total} 顆衛星已評分")
        
        # === 階段 2.4：信號品質評估 (新增) ===
        logger.info("📡 執行階段 2.4: 信號品質評估")
        signal_enhanced_data = self._enhance_with_signal_quality(scored_data)
        
        # === 階段 2.5：3GPP 事件分析 (新增) ===
        logger.info("🎯 執行階段 2.5: 3GPP 事件分析")
        event_enhanced_data = self._enhance_with_event_analysis(signal_enhanced_data)
        
        # === 動態衛星選擇 ===
        if selection_config is None:
            logger.info("🎯 執行動態篩選模式 - 保留所有通過篩選的衛星")
            selected_satellites = event_enhanced_data  # 直接使用篩選後的數據
        else:
            logger.info("🏆 執行固定數量選擇模式")
            selected_satellites = self.handover_scorer.select_top_satellites(event_enhanced_data, selection_config)
        
        final_total = sum(len(sats) for sats in selected_satellites.values())
        logger.info(f"✅ 最終選擇: {final_total} 顆頂級衛星")
        
        # === 構建輸出數據 ===
        result = self._build_complete_output(
            sgp4_data, selected_satellites, {
                'input_statistics': {'total_input': total_input},
                'separation_stats': sep_stats,
                'geographic_stats': geo_stats, 
                'scoring_stats': scoring_stats,
                'selection_summary': {
                    'stage1_separated': stage1_total,
                    'stage2_geo_filtered': stage2_total,
                    'stage3_scored': stage3_total,
                    'final_selected': final_total,
                    'selection_config': selection_config
                }
            }
        )
        
        logger.info(f"🎉 完整智能篩選完成: {total_input} → {final_total} 顆衛星 "
                   f"(篩選率: {(1 - final_total/total_input)*100:.1f}%)")
        
        return result
    
    def _extract_satellites_from_sgp4_data(self, sgp4_data: Dict[str, Any]) -> List[Dict]:
        """從SGP4數據中提取衛星列表，兼容字典和列表格式"""
        all_satellites = []
        
        constellations = sgp4_data.get("constellations", {})
        for constellation_name, constellation_data in constellations.items():
            # 支援兩種格式：orbit_data.satellites (階段一) 或直接 satellites
            orbit_data = constellation_data.get("orbit_data", {})
            satellites_data = orbit_data.get("satellites", constellation_data.get("satellites", {}))
            
            # 處理字典格式（階段一輸出）
            if isinstance(satellites_data, dict):
                for satellite_id, satellite_data in satellites_data.items():
                    # 確保衛星有基本標識信息
                    satellite_data["satellite_id"] = satellite_id
                    satellite_data["constellation"] = constellation_name
                    
                    # 如果有positions數據，提取第一個位置作為代表，但保留原有的orbit_data
                    positions = satellite_data.get("positions", [])
                    if positions:
                        first_pos = positions[0]
                        # 保留現有的orbit_data，只添加位置信息
                        existing_orbit_data = satellite_data.get("orbit_data", {})
                        satellite_data["orbit_data"] = {
                            **existing_orbit_data,  # 保留原有軌道參數
                            "position": first_pos.get("position_eci", {}),
                            "velocity": first_pos.get("velocity_eci", {}),
                            "elevation_deg": first_pos.get("elevation_deg", 0),
                            "azimuth_deg": first_pos.get("azimuth_deg", 0),
                            "range_km": first_pos.get("range_km", 0)
                        }
                        satellite_data["timeseries"] = [
                            {
                                "time": pos.get("time"),
                                "elevation_deg": pos.get("elevation_deg", 0),
                                "azimuth_deg": pos.get("azimuth_deg", 0)
                            }
                            for pos in positions[:10]  # 只取前10個時間點進行測試
                        ]
                    
                    all_satellites.append(satellite_data)
            
            # 處理列表格式（階段二預期）
            elif isinstance(satellites_data, list):
                for satellite in satellites_data:
                    satellite["constellation"] = constellation_name
                    all_satellites.append(satellite)
        
        logger.info(f"📡 提取衛星數據: {len(all_satellites)} 顆衛星")
        for constellation_name in constellations.keys():
            constellation_sats = [s for s in all_satellites if s.get("constellation") == constellation_name]
            logger.info(f"   {constellation_name}: {len(constellation_sats)} 顆")
        
        return all_satellites
    
    def _enhance_with_signal_quality(self, scored_data: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """為衛星數據添加信號品質評估"""
        enhanced_data = {}
        
        for constellation, satellites in scored_data.items():
            enhanced_satellites = []
            
            for satellite in satellites:
                enhanced_satellite = satellite.copy()
                
                # 計算多個仰角下的 RSRP
                rsrp_values = []
                for elevation in [10, 30, 45, 60]:
                    rsrp = self.rsrp_calculator.calculate_rsrp(satellite, elevation)
                    rsrp_values.append(rsrp)
                
                # 添加信號品質指標
                enhanced_satellite['signal_quality'] = {
                    'rsrp_range': {
                        f'elev_{elev}deg': rsrp for elev, rsrp in zip([10, 30, 45, 60], rsrp_values)
                    },
                    'mean_rsrp_dbm': sum(rsrp_values) / len(rsrp_values),
                    'max_rsrp_dbm': max(rsrp_values),
                    'min_rsrp_dbm': min(rsrp_values),
                    'rsrp_stability': max(rsrp_values) - min(rsrp_values)  # 越小越穩定
                }
                
                enhanced_satellites.append(enhanced_satellite)
            
            enhanced_data[constellation] = enhanced_satellites
            logger.debug(f"✅ {constellation}: {len(satellites)} 顆衛星信號品質評估完成")
        
        return enhanced_data
    
    def _enhance_with_event_analysis(self, signal_enhanced_data: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """為衛星數據添加 3GPP 事件分析"""
        enhanced_data = {}
        
        for constellation, satellites in signal_enhanced_data.items():
            # 調試信息
            logger.debug(f"🔍 處理 {constellation}: {len(satellites)} 顆衛星")
            
            # 批量事件分析
            event_results = self.event_analyzer.analyze_batch_events(satellites)
            
            # 調試輸出格式
            logger.debug(f"🔍 事件分析結果欄位: {list(event_results.keys())}")
            
            if 'satellites_with_events' in event_results:
                enhanced_satellites = event_results['satellites_with_events']
                enhanced_data[constellation] = enhanced_satellites
                logger.debug(f"✅ {constellation}: {len(enhanced_satellites)} 顆衛星事件分析完成")
            else:
                logger.error(f"❌ {constellation} 事件分析結果缺少 satellites_with_events 欄位")
                logger.error(f"實際欄位: {list(event_results.keys())}")
                # 回退使用原始數據
                enhanced_data[constellation] = satellites
        
        return enhanced_data
    
    def _build_complete_output(self, 
                             sgp4_data: Dict[str, Any],
                             selected_satellites: Dict[str, List[Dict]],
                             processing_stats: Dict[str, Any]) -> Dict[str, Any]:
        """構建完整的輸出數據格式"""
        
        result = {
            "metadata": {
                **sgp4_data.get("metadata", {}),
                "unified_filtering_completion": "complete_modular_architecture",
                "unified_filtering_version": "2.1.0-integrated",
                "processing_pipeline": [
                    "phase1_sgp4_orbit_calculation",
                    "phase2.1_constellation_separation", 
                    "phase2.2_geographic_filtering",
                    "phase2.3_handover_scoring",
                    "phase2.4_signal_quality_assessment", 
                    "phase2.5_3gpp_event_analysis",
                    "phase2.6_top_satellite_selection"
                ],
                "unified_filtering_algorithms": {
                    "constellation_separation": "complete_starlink_oneweb_separation",
                    "geographic_filtering": "ntpu_location_optimized_filtering", 
                    "handover_scoring": "constellation_specific_scoring_system",
                    "signal_calculation": "itu_r_p618_standard_rsrp_calculation",
                    "event_analysis": "3gpp_ntn_a4_a5_d2_events"
                },
                "unified_filtering_results": {
                    "total_selected": sum(len(sats) for sats in selected_satellites.values()),
                    "starlink_selected": len(selected_satellites.get("starlink", [])),
                    "oneweb_selected": len(selected_satellites.get("oneweb", [])),
                    "processing_quality": "complete_integrated_filtering_system"
                },
                "processing_statistics": processing_stats
            },
            "constellations": {}
        }
        
        # 構建星座數據，包含所有增強信息
        original_constellations = sgp4_data.get("constellations", {})
        
        for constellation_name, selected_sats in selected_satellites.items():
            if constellation_name in original_constellations:
                constellation_data = original_constellations[constellation_name].copy()
                
                # 更新衛星數據為完整處理後的結果
                constellation_data["satellites"] = selected_sats
                constellation_data["satellite_count"] = len(selected_sats)
                constellation_data["selection_quality"] = "unified_intelligent_filtered"
                constellation_data["enhancements"] = [
                    "constellation_specific_filtering",
                    "geographic_relevance_scoring",
                    "handover_suitability_scoring", 
                    "signal_quality_assessment",
                    "3gpp_event_analysis"
                ]
                
                result["constellations"][constellation_name] = constellation_data
        
        return result
    
    def validate_filtering_results(self, result: Dict[str, Any]) -> Dict[str, bool]:
        """驗證篩選結果的品質"""
        validation = {
            'has_satellites': False,
            'constellation_balance': False,
            'signal_quality_ok': False,
            'event_capability_ok': False,
            'overall_quality': False
        }
        
        total_satellites = result['metadata']['unified_filtering_results']['total_selected']
        starlink_count = result['metadata']['unified_filtering_results']['starlink_selected']
        oneweb_count = result['metadata']['unified_filtering_results']['oneweb_selected']
        
        # 基本衛星數量檢查
        validation['has_satellites'] = total_satellites > 0
        
        # 星座平衡檢查
        if total_satellites > 0:
            starlink_ratio = starlink_count / total_satellites
            validation['constellation_balance'] = 0.3 <= starlink_ratio <= 0.9
        
        # 信號品質檢查
        signal_quality_count = 0
        event_capable_count = 0
        
        for constellation_data in result['constellations'].values():
            for satellite in constellation_data.get('satellites', []):
                # 檢查信號品質
                signal_quality = satellite.get('signal_quality', {})
                if signal_quality.get('mean_rsrp_dbm', -999) > -100:
                    signal_quality_count += 1
                
                # 檢查事件能力
                event_potential = satellite.get('event_potential', {})
                if event_potential.get('composite', 0) > 0.4:
                    event_capable_count += 1
        
        validation['signal_quality_ok'] = (signal_quality_count >= total_satellites * 0.7)
        validation['event_capability_ok'] = (event_capable_count >= total_satellites * 0.5)
        
        # 整體品質評估
        validation['overall_quality'] = all([
            validation['has_satellites'],
            validation['constellation_balance'], 
            validation['signal_quality_ok'],
            validation['event_capability_ok']
        ])
        
        logger.info(f"🔍 篩選結果驗證: 整體品質 {'✅' if validation['overall_quality'] else '❌'}")
        logger.info(f"   衛星數量: {total_satellites} ({'✅' if validation['has_satellites'] else '❌'})")
        logger.info(f"   星座平衡: {'✅' if validation['constellation_balance'] else '❌'}")
        logger.info(f"   信號品質: {signal_quality_count}/{total_satellites} ({'✅' if validation['signal_quality_ok'] else '❌'})")
        logger.info(f"   事件能力: {event_capable_count}/{total_satellites} ({'✅' if validation['event_capability_ok'] else '❌'})")
        
        return validation


def create_unified_intelligent_filter(observer_lat: float = 24.9441667, 
                                     observer_lon: float = 121.3713889) -> UnifiedIntelligentFilter:
    """創建統一智能篩選系統實例"""
    return UnifiedIntelligentFilter(observer_lat, observer_lon)


if __name__ == "__main__":
    # 測試統一智能篩選系統
    logger.info("🧪 測試統一智能篩選系統")
    
    # 模擬階段一數據
    test_sgp4_data = {
        "metadata": {
            "version": "2.0.0-phase1",
            "total_satellites": 8715,
            "total_constellations": 2
        },
        "constellations": {
            "starlink": {
                "satellites": [
                    {
                        "satellite_id": "STARLINK-1007",
                        "orbit_data": {
                            "altitude": 550,
                            "inclination": 53,
                            "position": {"x": 1234, "y": 5678, "z": 9012}
                        },
                        "timeseries": [
                            {"time": "2025-08-12T12:00:00Z", "elevation_deg": 45.0, "azimuth_deg": 180.0}
                        ]
                    }
                ]
            },
            "oneweb": {
                "satellites": [
                    {
                        "satellite_id": "ONEWEB-0123",
                        "orbit_data": {
                            "altitude": 1200,
                            "inclination": 87,
                            "position": {"x": 2345, "y": 6789, "z": 123}
                        },
                        "timeseries": [
                            {"time": "2025-08-12T12:00:00Z", "elevation_deg": 30.0, "azimuth_deg": 90.0}
                        ]
                    }
                ]
            }
        }
    }
    
    # 測試完整篩選流程
    filter_system = create_unified_intelligent_filter()
    selection_config = {"starlink": 1, "oneweb": 1}
    
    result = filter_system.process_complete_filtering(test_sgp4_data, selection_config)
    
    # 驗證結果
    validation = filter_system.validate_filtering_results(result)
    
    print("✅ 統一智能篩選系統測試完成")
    print(f"處理結果: {result.get('metadata', {}).get('unified_filtering_completion', 'Unknown')}")
    print(f"整體品質: {'通過' if validation['overall_quality'] else '需要改進'}")