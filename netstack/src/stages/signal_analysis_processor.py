#!/usr/bin/env python3
"""
信號品質分析與3GPP事件處理

完全遵循 @docs/satellite_data_preprocessing.md 規範：
- 接收智能篩選後的衛星數據
- 進行信號品質評估 (RSRP計算)
- 執行3GPP NTN事件分析
- 輸出最終的衛星選擇結果
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加必要路徑
sys.path.insert(0, '/app/netstack')
sys.path.insert(0, '/app')

# 引用重新組織後的模組
from src.services.satellite.intelligent_filtering.signal_calculation.rsrp_calculator import create_rsrp_calculator
from src.services.satellite.intelligent_filtering.event_analysis.gpp_event_analyzer import create_gpp_event_analyzer
from src.services.satellite.intelligent_filtering.unified_intelligent_filter import UnifiedIntelligentFilter

# 導入驗證基礎類別
from shared_core.validation_snapshot_base import ValidationSnapshotBase, ValidationCheckHelper

logger = logging.getLogger(__name__)

class SignalQualityAnalysisProcessor(ValidationSnapshotBase):
    """信號品質分析及3GPP事件處理器
    
    職責：
    1. 接收智能篩選後的衛星數據
    2. 計算所有衛星的RSRP信號強度
    3. 執行3GPP NTN標準事件分析
    4. 生成最終的衛星選擇建議
    5. 絕對不重複篩選邏輯
    """
    
    def __init__(self, input_dir: str = '/app/data', output_dir: str = '/app/data'):
        """初始化信號分析處理器"""
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # 確保輸出目錄存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 驗證快照管理
        self.snapshot_file = Path('/app/data/validation_snapshots/stage3_validation.json')
        self.snapshot_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 處理時間追蹤
        self.start_time = None
        self.processing_duration = None
        
        # 初始化共享核心服務
        try:
            # 🚫 移除不必要的 signal_cache - 未實際使用
            # from shared_core.signal_quality_cache import get_signal_quality_cache
            from shared_core.elevation_threshold_manager import get_elevation_threshold_manager
            
            # self.signal_cache = get_signal_quality_cache()  # 🚫 已移除
            self.elevation_manager = get_elevation_threshold_manager()
            
            logger.info("✅ 共享核心服務初始化完成")
            # logger.info("  - 信號品質緩存")  # 🚫 已移除
            logger.info("  - 仰角閾值管理器")
            
        except Exception as e:
            logger.warning(f"⚠️ 共享核心服務初始化失敗: {e}")
            logger.info("🔄 使用降級模式")
            # self.signal_cache = None  # 🚫 已移除
            self.elevation_manager = None
        
        logger.info(f"✅ 信號品質分析處理器初始化完成")
        logger.info(f"  輸入目錄: {self.input_dir}")
        logger.info(f"  輸出目錄: {self.output_dir}")
        logger.info(f"  驗證快照: {self.snapshot_file}")       
    def extract_key_metrics(self, processing_results: Dict[str, Any]) -> Dict[str, Any]:
        """提取階段3關鍵指標"""
        metadata = processing_results.get('metadata', {})
        
        # 統計各星座處理結果
        constellation_metrics = {}
        total_signal_processed = 0
        total_events_detected = 0
        
        for constellation_name, constellation_data in processing_results.get('constellations', {}).items():
            satellites = constellation_data.get('satellites', [])
            signal_processed = len([s for s in satellites if s.get('signal_quality')])
            events_detected = len([s for s in satellites if s.get('event_potential')])
            
            constellation_metrics[f"{constellation_name}信號處理"] = signal_processed
            constellation_metrics[f"{constellation_name}事件檢測"] = events_detected
            
            total_signal_processed += signal_processed
            total_events_detected += events_detected
        
        return {
            "輸入衛星": len(processing_results.get('satellites', [])),
            "信號處理總數": total_signal_processed,
            "3GPP事件檢測": total_events_detected,
            "推薦衛星數": metadata.get('final_recommended_total', 0),
            **constellation_metrics
        }
    
    def run_validation_checks(self, processing_results: Dict[str, Any]) -> Dict[str, Any]:
        """執行 Stage 3 驗證檢查 - 專注於信號品質分析和3GPP事件處理準確性"""
        metadata = processing_results.get('metadata', {})
        constellations = processing_results.get('constellations', {})
        satellites = processing_results.get('satellites', [])
        
        checks = {}
        
        # 1. 輸入數據存在性檢查 - 修復：使用 total_satellites 而非 input_satellites
        input_satellites = metadata.get('total_satellites', 0)
        checks["輸入數據存在性"] = input_satellites > 0
        
        # 2. 信號品質計算完整性檢查 - 修復：檢查衛星根級別的 signal_quality
        signal_quality_completed = True
        signal_satellites_count = 0
        if satellites:
            sample_size = min(10, len(satellites))
            for i in range(sample_size):
                sat = satellites[i]
                # 檢查衛星根級別是否有信號品質數據
                if 'signal_quality' in sat:
                    signal_data = sat['signal_quality']
                    # 檢查是否有 rsrp_by_elevation 和統計數據
                    if 'rsrp_by_elevation' in signal_data and 'statistics' in signal_data:
                        signal_satellites_count += 1
            
            signal_quality_completed = signal_satellites_count >= int(sample_size * 0.8)
        
        checks["信號品質計算完整性"] = signal_quality_completed
        
        # 3. 3GPP事件處理檢查 - 修復：檢查衛星根級別的 event_potential
        gpp_events_ok = True
        if satellites:
            sample_sat = satellites[0]
            # 檢查是否包含3GPP事件潛力數據
            if 'event_potential' in sample_sat:
                event_data = sample_sat['event_potential']
                # 檢查是否包含 A4, A5, D2 事件
                required_events = ['A4', 'A5', 'D2']
                events_found = all(event in event_data for event in required_events)
                gpp_events_ok = events_found
            else:
                gpp_events_ok = False
        
        checks["3GPP事件處理檢查"] = gpp_events_ok
        
        # 4. 信號範圍合理性檢查 - 修復：檢查 rsrp_by_elevation 中的數值
        signal_range_reasonable = True
        if satellites and signal_satellites_count > 0:
            sample_sat = satellites[0]
            if 'signal_quality' in sample_sat:
                signal_data = sample_sat['signal_quality']
                if 'rsrp_by_elevation' in signal_data:
                    rsrp_values = signal_data['rsrp_by_elevation']
                    if isinstance(rsrp_values, dict):
                        # 檢查RSRP值是否在合理範圍 -140 到 -50 dBm
                        for elevation, rsrp in rsrp_values.items():
                            if isinstance(rsrp, (int, float)):
                                if not (-140 <= rsrp <= -50):  # ITU-R標準範圍
                                    signal_range_reasonable = False
                                    break
        
        checks["信號範圍合理性檢查"] = signal_range_reasonable
        
        # 5. 星座完整性檢查 - 確保兩個星座都有信號分析
        constellation_names = list(constellations.keys())
        checks["星座完整性檢查"] = ValidationCheckHelper.check_constellation_presence(
            constellation_names, ['starlink', 'oneweb']
        )
        
        # 6. 數據結構完整性檢查 - 修復：使用實際存在的欄位
        required_fields = ['metadata', 'satellites', 'constellations']
        checks["數據結構完整性"] = ValidationCheckHelper.check_data_completeness(
            processing_results, required_fields
        )
        
        # 7. 處理時間檢查 - 信號分析需要一定時間但不應過長
        max_time = 400 if self.sample_mode else 300  # 取樣6.7分鐘，全量5分鐘
        checks["處理時間合理性"] = ValidationCheckHelper.check_processing_time(
            self.processing_duration, max_time
        )
        
        # 計算通過的檢查數量
        passed_checks = sum(1 for passed in checks.values() if passed)
        total_checks = len(checks)
        
        return {
            "passed": passed_checks == total_checks,
            "totalChecks": total_checks,
            "passedChecks": passed_checks,
            "failedChecks": total_checks - passed_checks,
            "criticalChecks": [
                {"name": "信號品質計算完整性", "status": "passed" if checks["信號品質計算完整性"] else "failed"},
                {"name": "3GPP事件處理檢查", "status": "passed" if checks["3GPP事件處理檢查"] else "failed"},
                {"name": "信號範圍合理性檢查", "status": "passed" if checks["信號範圍合理性檢查"] else "failed"},
                {"name": "星座完整性檢查", "status": "passed" if checks["星座完整性檢查"] else "failed"}
            ],
            "allChecks": checks
        }
    
    def load_intelligent_filtering_output(self, filtering_file: Optional[str] = None) -> Dict[str, Any]:
        """載入智能篩選輸出數據"""
        if filtering_file is None:
            # 🎯 更新為新的檔案命名
            filtering_file = self.input_dir / "satellite_visibility_filtered_output.json"
        else:
            filtering_file = Path(filtering_file)
            
        logger.info(f"📥 載入智能篩選數據: {filtering_file}")
        
        if not filtering_file.exists():
            raise FileNotFoundError(f"智能篩選輸出檔案不存在: {filtering_file}")
            
        try:
            with open(filtering_file, 'r', encoding='utf-8') as f:
                filtering_data = json.load(f)
                
            # 🎯 兼容新舊兩種格式：constellations 格式和 satellites 陣列格式
            if 'constellations' in filtering_data:
                # 舊格式：有 constellations 欄位
                total_satellites = 0
                for constellation_name, constellation_data in filtering_data['constellations'].items():
                    # Handle both file-based and memory-based data structures  
                    if 'satellites' in constellation_data:
                        satellites = constellation_data.get('satellites', [])
                    elif 'orbit_data' in constellation_data:
                        satellites = constellation_data.get('orbit_data', {}).get('satellites', [])
                    else:
                        satellites = []
                    total_satellites += len(satellites)
                    logger.info(f"  {constellation_name}: {len(satellites)} 顆衛星")
                    
            elif 'satellites' in filtering_data:
                # 🆕 新格式：直接有 satellites 陣列
                satellites = filtering_data.get('satellites', [])
                total_satellites = len(satellites)
                
                # 按星座分組統計
                constellation_counts = {}
                for sat in satellites:
                    const = sat.get('constellation', 'unknown')
                    constellation_counts[const] = constellation_counts.get(const, 0) + 1
                
                logger.info(f"  新格式檢測到 {total_satellites} 顆衛星:")
                for const, count in constellation_counts.items():
                    logger.info(f"    {const}: {count} 顆")
                    
                # 🔄 轉換為舊格式以兼容後續處理
                constellations_data = {}
                for sat in satellites:
                    const = sat.get('constellation', 'unknown')
                    if const not in constellations_data:
                        constellations_data[const] = {
                            'satellites': [],
                            'metadata': filtering_data.get('metadata', {})
                        }
                    constellations_data[const]['satellites'].append(sat)
                
                # 更新為兼容格式
                filtering_data['constellations'] = constellations_data
                logger.info("✅ 已轉換新格式為兼容格式")
                
            else:
                raise ValueError("智能篩選數據缺少 constellations 或 satellites 欄位")
                
            logger.info(f"✅ 智能篩選數據載入完成: 總計 {total_satellites} 顆衛星")
            return filtering_data
            
        except Exception as e:
            logger.error(f"載入智能篩選數據失敗: {e}")
            raise
            
    def calculate_signal_quality(self, filtering_data: Dict[str, Any]) -> Dict[str, Any]:
        """計算所有衛星的信號品質"""
        logger.info("📡 開始信號品質分析...")
        
        enhanced_data = {
            'metadata': filtering_data.get('metadata', {}),
            'constellations': {}
        }
        
        # 更新metadata
        enhanced_data['metadata'].update({
            'signal_processing': 'signal_quality_analysis',
            'signal_timestamp': datetime.now(timezone.utc).isoformat(),
            'signal_calculation_standard': 'ITU-R_P.618_20GHz_Ka_band'
        })
        
        total_processed = 0
        
        for constellation_name, constellation_data in filtering_data['constellations'].items():
            # Handle both file-based and memory-based data structures
            satellites_list = []
            
            # Debug constellation data structure
            logger.debug(f"Debug {constellation_name}: type={type(constellation_data)}")
            if 'orbit_data' in constellation_data:
                orbit_data = constellation_data.get('orbit_data', {})
                logger.debug(f"Debug orbit_data: type={type(orbit_data)}")
                satellites_data = orbit_data.get('satellites', {})
                logger.debug(f"Debug satellites_data: type={type(satellites_data)}, len={len(satellites_data) if hasattr(satellites_data, '__len__') else 'N/A'}")
                
                if isinstance(satellites_data, dict):
                    # Convert dictionary to list of satellite objects
                    satellites_list = list(satellites_data.values())
                    logger.debug(f"Converted to list: {len(satellites_list)} satellites")
                    # Check the first few satellites
                    for i, sat in enumerate(satellites_list[:3]):
                        logger.debug(f"Satellite {i}: type={type(sat)}, content={str(sat)[:100]}...")
                elif isinstance(satellites_data, list):
                    satellites_list = satellites_data
                else:
                    logger.warning(f"Unexpected satellites_data type: {type(satellites_data)}")
            elif 'satellites' in constellation_data:
                # File-based format: satellites is already a list
                satellites_data = constellation_data.get('satellites', [])
                if isinstance(satellites_data, list):
                    satellites_list = satellites_data
                elif isinstance(satellites_data, dict):
                    # Convert dictionary to list
                    satellites_list = list(satellites_data.values())
            
            if not satellites_list:
                logger.warning(f"跳過 {constellation_name}: 無可用衛星")
                continue
                
            logger.info(f"   處理 {constellation_name}: {len(satellites_list)} 顆衛星")
            
            enhanced_satellites = []
            
            for i, satellite in enumerate(satellites_list):
                try:
                    # Ensure satellite is a dictionary, not a string or other type
                    if not isinstance(satellite, dict):
                        logger.warning(f"跳過無效衛星數據類型 {i}: {type(satellite)} - {str(satellite)[:50]}...")
                        continue
                        
                    enhanced_satellite = satellite.copy()
                    
                    # 🎯 關鍵修復：確保保留時間序列數據
                    if 'position_timeseries' in satellite:
                        enhanced_satellite['position_timeseries'] = satellite['position_timeseries']
                    
                    # 計算多個仰角下的RSRP
                    rsrp_calculations = {}
                    rsrp_values = []
                    
                    for elevation_deg in [5, 10, 15, 30, 45, 60, 75, 90]:
                        rsrp = self.rsrp_calculator.calculate_rsrp(satellite, elevation_deg)
                        rsrp_calculations[f'elev_{elevation_deg}deg'] = round(rsrp, 2)
                        rsrp_values.append(rsrp)
                    
                    # 計算統計信息
                    mean_rsrp = sum(rsrp_values) / len(rsrp_values)
                    max_rsrp = max(rsrp_values)
                    min_rsrp = min(rsrp_values)
                    rsrp_stability = max_rsrp - min_rsrp  # 越小越穩定
                    
                    # 添加信號品質數據
                    enhanced_satellite['signal_quality'] = {
                        'rsrp_by_elevation': rsrp_calculations,
                        'statistics': {
                            'mean_rsrp_dbm': round(mean_rsrp, 2),
                            'max_rsrp_dbm': round(max_rsrp, 2),
                            'min_rsrp_dbm': round(min_rsrp, 2),
                            'rsrp_stability_db': round(rsrp_stability, 2),
                            'signal_quality_grade': self._grade_signal_quality(mean_rsrp)
                        },
                        'calculation_standard': 'ITU-R_P.618_Ka_band_20GHz',
                        'observer_location': {
                            'latitude': self.observer_lat,
                            'longitude': self.observer_lon
                        }
                    }
                    
                    enhanced_satellites.append(enhanced_satellite)
                    total_processed += 1
                    
                except Exception as e:
                    sat_id = "Unknown"
                    if isinstance(satellite, dict):
                        sat_id = satellite.get('satellite_id', 'Unknown')
                    logger.warning(f"衛星 {sat_id} (索引 {i}) 信號計算失敗: {e}")
                    logger.debug(f"Problem satellite type: {type(satellite)}, content: {str(satellite)[:100]}...")
                    
                    # 保留原始衛星數據，但標記錯誤
                    if isinstance(satellite, dict):
                        satellite_copy = satellite.copy()
                        satellite_copy['signal_quality'] = {
                            'error': str(e),
                            'status': 'calculation_failed'
                        }
                        enhanced_satellites.append(satellite_copy)
                    else:
                        # Create a placeholder for invalid data
                        enhanced_satellites.append({
                            'satellite_id': f'Invalid_{i}',
                            'error_type': str(type(satellite)),
                            'signal_quality': {
                                'error': str(e),
                                'status': 'invalid_data_type'
                            }
                        })
            
            # 更新星座數據
            enhanced_constellation_data = constellation_data.copy()
            enhanced_constellation_data['satellites'] = enhanced_satellites
            enhanced_constellation_data['signal_analysis_completed'] = True
            enhanced_constellation_data['signal_processed_count'] = len(enhanced_satellites)
            
            enhanced_data['constellations'][constellation_name] = enhanced_constellation_data
            
            logger.info(f"  {constellation_name}: {len(enhanced_satellites)} 顆衛星信號分析完成")
        
        enhanced_data['metadata']['signal_processed_total'] = total_processed
        
        logger.info(f"✅ 信號品質分析完成: {total_processed} 顆衛星")
        return enhanced_data
        
    def analyze_3gpp_events(self, signal_enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行3GPP NTN事件分析"""
        logger.info("🎯 開始3GPP事件分析...")
        
        event_enhanced_data = {
            'metadata': signal_enhanced_data.get('metadata', {}),
            'constellations': {}
        }
        
        # 更新metadata
        event_enhanced_data['metadata'].update({
            'event_analysis_type': '3GPP_NTN_A4_A5_D2_events',
            'event_analysis_timestamp': datetime.now(timezone.utc).isoformat(),
            'supported_events': ['A4_intra_frequency', 'A5_intra_frequency', 'D2_beam_switch']
        })
        
        total_analyzed = 0
        
        for constellation_name, constellation_data in signal_enhanced_data['constellations'].items():
            satellites = constellation_data.get('satellites', [])
            
            if not satellites:
                logger.warning(f"跳過 {constellation_name}: 無可用衛星")
                continue
                
            logger.info(f"   處理 {constellation_name}: {len(satellites)} 顆衛星事件分析")
            
            try:
                # 使用現有的事件分析器進行批量分析
                event_results = self.event_analyzer.analyze_batch_events(satellites)
                
                if 'satellites_with_events' in event_results:
                    event_analyzed_satellites = event_results['satellites_with_events']
                    
                    # 更新星座數據
                    event_constellation_data = constellation_data.copy()
                    event_constellation_data['satellites'] = event_analyzed_satellites
                    event_constellation_data['event_analysis_completed'] = True
                    event_constellation_data['event_statistics'] = event_results.get('statistics', {})
                    
                    event_enhanced_data['constellations'][constellation_name] = event_constellation_data
                    
                    total_analyzed += len(event_analyzed_satellites)
                    logger.info(f"  {constellation_name}: {len(event_analyzed_satellites)} 顆衛星事件分析完成")
                    
                else:
                    logger.error(f"❌ {constellation_name} 事件分析結果格式錯誤")
                    # 保留原始數據
                    event_enhanced_data['constellations'][constellation_name] = constellation_data
                    
            except Exception as e:
                logger.error(f"❌ {constellation_name} 事件分析失敗: {e}")
                # 保留原始數據，但標記錯誤
                error_constellation_data = constellation_data.copy()
                error_constellation_data['event_analysis_error'] = str(e)
                event_enhanced_data['constellations'][constellation_name] = error_constellation_data
        
        event_enhanced_data['metadata']['event_analyzed_total'] = total_analyzed
        
        logger.info(f"✅ 3GPP事件分析完成: {total_analyzed} 顆衛星")
        return event_enhanced_data
        
    def generate_final_recommendations(self, event_enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成最終的衛星選擇建議"""
        logger.info("🏆 生成最終衛星選擇建議...")
        
        final_data = {
            'metadata': event_enhanced_data.get('metadata', {}),
            'satellites': [],  # 扁平化的衛星陣列供後續階段使用
            'constellations': {},  # 保留星座分組資訊
            'selection_recommendations': {},
            'gpp_events': {  # 🔧 修復：明確包含3GPP事件統計
                'all_events': [],
                'event_summary': {
                    'A4': {'high_potential': 0, 'medium_potential': 0, 'low_potential': 0},
                    'A5': {'high_potential': 0, 'medium_potential': 0, 'low_potential': 0},
                    'D2': {'high_potential': 0, 'medium_potential': 0, 'low_potential': 0}
                },
                'total_event_triggers': 0
            }
        }
        
        # 更新metadata
        final_data['metadata'].update({
            'signal_analysis_completion': 'signal_and_event_analysis_complete',
            'final_processing_timestamp': datetime.now(timezone.utc).isoformat(),
            'processing_pipeline_complete': [
                'tle_orbital_calculation',
                'intelligent_filtering',
                'signal_event_analysis'
            ],
            'ready_for_handover_simulation': True
        })
        
        total_recommended = 0
        total_events = 0
        
        for constellation_name, constellation_data in event_enhanced_data['constellations'].items():
            satellites = constellation_data.get('satellites', [])
            
            if not satellites:
                continue
                
            # 對衛星進行綜合評分排序
            scored_satellites = []
            
            for satellite in satellites:
                score = self._calculate_composite_score(satellite)
                satellite_with_score = satellite.copy()
                satellite_with_score['composite_score'] = score
                scored_satellites.append(satellite_with_score)
                
                # 🔧 修復：收集3GPP事件統計
                event_potential = satellite.get('event_potential', {})
                if event_potential:
                    # 創建事件條目
                    event_entry = {
                        'satellite_id': satellite.get('satellite_id', 'unknown'),
                        'constellation': constellation_name,
                        'event_scores': event_potential,
                        'composite_score': event_potential.get('composite', 0)
                    }
                    final_data['gpp_events']['all_events'].append(event_entry)
                    total_events += 1
                    
                    # 更新事件統計
                    for event_type in ['A4', 'A5', 'D2']:
                        if event_type in event_potential:
                            score = event_potential[event_type]
                            if score >= 0.7:
                                final_data['gpp_events']['event_summary'][event_type]['high_potential'] += 1
                            elif score >= 0.4:
                                final_data['gpp_events']['event_summary'][event_type]['medium_potential'] += 1
                            else:
                                final_data['gpp_events']['event_summary'][event_type]['low_potential'] += 1
            
            # 按分數排序
            scored_satellites.sort(key=lambda x: x.get('composite_score', 0), reverse=True)
            
            # 更新星座數據
            final_constellation_data = constellation_data.copy()
            final_constellation_data['satellites'] = scored_satellites
            final_constellation_data['satellites_ranked'] = True
            final_constellation_data['top_satellite_score'] = scored_satellites[0].get('composite_score', 0) if scored_satellites else 0
            
            final_data['constellations'][constellation_name] = final_constellation_data
            
            # 將衛星加入扁平化陣列（供後續階段使用）
            for sat in scored_satellites:
                sat_flat = sat.copy()
                sat_flat['constellation'] = constellation_name  # 確保星座標籤存在
                final_data['satellites'].append(sat_flat)
            
            # 生成選擇建議
            top_satellites = scored_satellites[:5]  # 推薦前5顆
            final_data['selection_recommendations'][constellation_name] = {
                'top_5_satellites': [
                    {
                        'satellite_id': sat.get('satellite_id', 'Unknown'),
                        'composite_score': sat.get('composite_score', 0),
                        'signal_grade': sat.get('signal_quality', {}).get('statistics', {}).get('signal_quality_grade', 'Unknown'),
                        'event_potential': sat.get('event_potential', {}).get('composite', 0),
                        'handover_suitability': sat.get('handover_score', {}).get('overall_score', 0)
                    }
                    for sat in top_satellites
                ],
                'constellation_quality': self._assess_constellation_quality(scored_satellites),
                'recommended_for_handover': len([s for s in top_satellites if s.get('composite_score', 0) > 0.6])
            }
            
            total_recommended += len(scored_satellites)
            
            logger.info(f"  {constellation_name}: {len(scored_satellites)} 顆衛星完成最終評分")
        
        # 🔧 修復：更新3GPP事件總數
        final_data['gpp_events']['total_event_triggers'] = total_events
        final_data['metadata']['final_recommended_total'] = total_recommended
        final_data['metadata']['total_satellites'] = len(final_data['satellites'])  # 供後續階段使用
        final_data['metadata']['total_3gpp_events'] = total_events  # 明確標記3GPP事件數量
        
        logger.info(f"✅ 最終建議生成完成: {total_recommended} 顆衛星完成綜合評分")
        logger.info(f"  扁平化衛星陣列: {len(final_data['satellites'])} 顆")
        logger.info(f"  🎯 3GPP事件統計: {total_events} 個事件觸發")  # 新增日誌
        return final_data
        
    def save_signal_analysis_output(self, final_data: Dict[str, Any]) -> str:
        """保存信號分析輸出數據 - v4.0 基於功能的統一輸出規範版本"""
        # 🎯 更新為基於功能的檔案命名
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.output_dir / "signal_quality_analysis_output.json"
        
        # 🗑️ 清理可能的舊格式檔案
        old_format_files = [
            self.output_dir / "stage3_signal_analysis_output.json",
            self.output_dir / "signal_event_analysis_output.json",
            self.output_dir / "stage3_signal_event_analysis_output.json",
        ]
        
        for old_file in old_format_files:
            if old_file.exists():
                file_size = old_file.stat().st_size
                logger.info(f"🗑️ 清理舊格式檔案: {old_file}")
                logger.info(f"   檔案大小: {file_size / (1024*1024):.1f} MB")
                old_file.unlink()
                logger.info("✅ 舊格式檔案已清理")
        
        # 🗑️ 清理當前輸出檔案（如果存在）
        if output_file.exists():
            file_size = output_file.stat().st_size
            logger.info(f"🗑️ 清理當前輸出檔案: {output_file}")
            logger.info(f"   舊檔案大小: {file_size / (1024*1024):.1f} MB")
            output_file.unlink()
            logger.info("✅ 當前檔案已清理")
        
        # 添加基於功能的輸出規範標記
        final_data['metadata'].update({
            'signal_analysis_completion': 'signal_quality_analysis_complete',
            'signal_analysis_timestamp': datetime.now(timezone.utc).isoformat(),
            'ready_for_timeseries_preprocessing': True,
            'file_generation': 'functional_naming_standard_v4',  # 基於功能的命名規範v4.0
            'output_improvements': [
                'functional_based_file_naming',
                'consistent_signal_quality_prefix',
                'unified_leo_outputs_directory_structure'
            ]
        })
        
        # 📦 生成符合基於功能命名規範的檔案
        logger.info(f"📦 生成基於功能命名規範檔案: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
            
        # 檢查新檔案大小
        new_file_size = output_file.stat().st_size
        logger.info(f"✅ 階段三信號品質分析輸出已保存: {output_file}")
        logger.info(f"   新檔案大小: {new_file_size / (1024*1024):.1f} MB")
        logger.info(f"   包含衛星數: {final_data['metadata'].get('final_recommended_total', 'unknown')}")
        logger.info("   🎯 檔案規範: 基於功能的命名，統一leo_outputs目錄")
        
        return str(output_file)
        
    def process_signal_quality_analysis(self, filtering_file: Optional[str] = None, filtering_data: Optional[Dict[str, Any]] = None,
                      save_output: bool = True) -> Dict[str, Any]:
        """執行完整的信號品質分析處理流程"""
        start_time = time.time()
        logger.info("🚀 開始信號品質分析及3GPP事件處理")
        
        # 🔧 新版雙模式清理：使用統一清理管理器
        try:
            from shared_core.cleanup_manager import auto_cleanup
            cleaned_result = auto_cleanup(current_stage=3)
            logger.info(f"🗑️ 自動清理完成: {cleaned_result['files']} 檔案, {cleaned_result['directories']} 目錄")
        except ImportError as e:
            logger.warning(f"⚠️ 清理管理器導入失敗，使用傳統清理方式: {e}")
            # 清理舊驗證快照 (確保生成最新驗證快照)
            if self.snapshot_file.exists():
                logger.info(f"🗑️ 清理舊驗證快照: {self.snapshot_file}")
                self.snapshot_file.unlink()
        except Exception as e:
            logger.warning(f"⚠️ 自動清理失敗，繼續執行: {e}")
        
        try:
            # 1. 載入智能篩選數據（優先使用內存數據）
            if filtering_data is not None:
                logger.info("📥 使用提供的智能篩選內存數據")
                # 驗證內存數據格式
                if 'constellations' not in filtering_data:
                    raise ValueError("智能篩選數據缺少 constellations 欄位")
                total_satellites = 0
                for constellation_name, constellation_data in filtering_data['constellations'].items():
                    # Handle both file-based and memory-based data structures
                    if 'satellites' in constellation_data:
                        satellites = constellation_data.get('satellites', [])
                    elif 'orbit_data' in constellation_data:
                        satellites = constellation_data.get('orbit_data', {}).get('satellites', [])
                    else:
                        satellites = []
                    total_satellites += len(satellites)
                    logger.info(f"  {constellation_name}: {len(satellites)} 顆衛星")
                logger.info(f"✅ 智能篩選內存數據驗證完成: 總計 {total_satellites} 顆衛星")
            else:
                filtering_data = self.load_intelligent_filtering_output(filtering_file)
            
            # 2. 信號品質分析
            signal_enhanced_data = self.calculate_signal_quality(filtering_data)
            
            # 3. 3GPP事件分析
            event_enhanced_data = self.analyze_3gpp_events(signal_enhanced_data)
            
            # 4. 生成最終建議
            final_data = self.generate_final_recommendations(event_enhanced_data)
            
            # 5. 計算處理時間
            end_time = time.time()
            processing_duration = end_time - start_time
            
            # 6. 保存驗證快照
            validation_success = self.save_validation_snapshot(final_data)
            if validation_success:
                logger.info("✅ Stage 3 驗證快照已保存")
            else:
                logger.warning("⚠️ Stage 3 驗證快照保存失敗")
            
            # 7. 可選的輸出策略
            output_file = None
            if save_output:
                output_file = self.save_signal_analysis_output(final_data)
                logger.info(f"📁 信號分析數據已保存到: {output_file}")
            else:
                logger.info("🚀 信號分析使用內存傳遞模式，未保存檔案")
            
            logger.info("✅ 信號品質分析處理完成")
            logger.info(f"  分析的衛星數: {final_data['metadata'].get('final_recommended_total', 0)}")
            logger.info(f"  處理時間: {processing_duration:.2f} 秒")
            if output_file:
                logger.info(f"  輸出檔案: {output_file}")
            
            return final_data
            
        except Exception as e:
            logger.error(f"❌ Stage 3 信號分析處理失敗: {e}")
            # 保存錯誤快照
            error_data = {
                'error': str(e),
                'stage': 3,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            self.save_validation_snapshot(error_data)
            raise
        
    def _grade_signal_quality(self, mean_rsrp_dbm: float) -> str:
        """根據RSRP值評定信號品質等級"""
        if mean_rsrp_dbm >= -80:
            return "Excellent"
        elif mean_rsrp_dbm >= -90:
            return "Good"
        elif mean_rsrp_dbm >= -100:
            return "Fair"
        elif mean_rsrp_dbm >= -110:
            return "Poor"
        else:
            return "Very_Poor"
            
    def _calculate_composite_score(self, satellite: Dict[str, Any]) -> float:
        """計算衛星的綜合評分"""
        score = 0.0
        weights = {
            'signal_quality': 0.4,
            'event_potential': 0.3,
            'handover_score': 0.2,
            'geographic_score': 0.1
        }
        
        # 信號品質評分 (0-1)
        signal_quality = satellite.get('signal_quality', {}).get('statistics', {})
        mean_rsrp = signal_quality.get('mean_rsrp_dbm', -150)
        signal_score = max(0, min(1, (mean_rsrp + 120) / 40))  # -120到-80的範圍映射到0-1
        score += signal_score * weights['signal_quality']
        
        # 事件潛力評分 (0-1)
        event_potential = satellite.get('event_potential', {}).get('composite', 0)
        score += event_potential * weights['event_potential']
        
        # 換手評分 (0-1)
        handover_score = satellite.get('handover_score', {}).get('overall_score', 0)
        normalized_handover = handover_score / 100.0  # 假設原始評分是0-100
        score += normalized_handover * weights['handover_score']
        
        # 地理評分 (0-1)
        geographic_score = satellite.get('geographic_score', {}).get('overall_score', 0)
        normalized_geographic = geographic_score / 100.0  # 假設原始評分是0-100
        score += normalized_geographic * weights['geographic_score']
        
        return round(score, 3)
        
    def _assess_constellation_quality(self, satellites: List[Dict[str, Any]]) -> str:
        """評估星座整體品質"""
        if not satellites:
            return "No_Data"
            
        scores = [s.get('composite_score', 0) for s in satellites]
        avg_score = sum(scores) / len(scores)
        
        if avg_score >= 0.8:
            return "Excellent"
        elif avg_score >= 0.6:
            return "Good"
        elif avg_score >= 0.4:
            return "Fair"
        elif avg_score >= 0.2:
            return "Poor"
        else:
            return "Very_Poor"

def main():
    """主函數"""
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger.info("============================================================")
    logger.info("信號品質分析與3GPP事件處理")
    logger.info("============================================================")
    
    try:
        processor = SignalQualityAnalysisProcessor()
        result = processor.process_signal_quality_analysis()
        
        logger.info("🎉 信號品質分析處理成功完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 信號品質分析處理失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)