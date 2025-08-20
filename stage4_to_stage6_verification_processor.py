#!/usr/bin/env python3
"""
階段四到六完整驗證處理器

使用修復後的階段三產出數據，執行階段四、五、六的完整驗證
重點關注階段六時序保存率0%問題的修復狀況
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

# 設定 Python 路徑
sys.path.insert(0, '/home/sat/ntn-stack/netstack')
sys.path.insert(0, '/home/sat/ntn-stack/netstack/src')

# 引用處理器
from src.stages.tle_orbital_calculation_processor import Stage1TLEProcessor
from src.stages.intelligent_satellite_filter_processor import IntelligentSatelliteFilterProcessor
from src.stages.signal_quality_analysis_processor import SignalQualityAnalysisProcessor
from src.stages.timeseries_preprocessing_processor import TimeseriesPreprocessingProcessor
from src.stages.data_integration_processor import DataIntegrationProcessor
from src.stages.enhanced_dynamic_pool_planner import EnhancedDynamicPoolPlanner

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class Stage4To6VerificationProcessor:
    """階段四到六完整驗證處理器"""
    
    def __init__(self):
        """初始化驗證處理器"""
        logger.info("🔍 階段四到六驗證處理器初始化")
        
        # 初始化所有處理器
        self.stage1_processor = Stage1TLEProcessor(
            tle_data_dir="/app/tle_data",
            output_dir="/app/data",
            sample_mode=False  # 全量處理模式
        )
        
        self.stage2_processor = IntelligentSatelliteFilterProcessor(
            input_dir="/app/data",
            output_dir="/app/data"
        )
        
        self.stage3_processor = SignalQualityAnalysisProcessor(
            input_dir="/app/data",
            output_dir="/app/data"
        )
        
        self.stage4_processor = TimeseriesPreprocessingProcessor(
            input_dir="/app/data",
            output_dir="/app/data"
        )
        
        self.stage5_processor = DataIntegrationProcessor(
            input_dir="/app/data",
            output_dir="/app/data"
        )
        
        self.stage6_processor = EnhancedDynamicPoolPlanner(
            input_dir="/app/data",
            output_dir="/app/data"
        )
        
        logger.info("✅ 所有處理器初始化完成")
        
    def analyze_data_structure(self, data: Dict[str, Any], stage_name: str) -> Dict[str, Any]:
        """分析數據結構 - 修復版本"""
        logger.info(f"🔍 分析 {stage_name} 數據結構...")
        
        analysis = {
            'stage': stage_name,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'satellites_count': 0,
            'constellations': {},
            'total_constellations': 0,
            'data_structure': 'unknown'
        }
        
        try:
            # 檢查metadata
            metadata = data.get('metadata', {})
            analysis['has_metadata'] = bool(metadata)
            if metadata:
                analysis['metadata_satellites'] = metadata.get('total_satellites', 0)
                analysis['processing_stage'] = metadata.get('processing_stage', 'unknown')
            
            # 檢查constellations
            constellations = data.get('constellations', {})
            analysis['total_constellations'] = len(constellations)
            
            total_satellites = 0
            for const_name, const_data in constellations.items():
                logger.info(f"  🔍 分析星座: {const_name}")
                logger.info(f"    數據鍵: {list(const_data.keys()) if isinstance(const_data, dict) else 'not_dict'}")
                
                satellites_count = 0
                
                # 檢查orbit_data.satellites (字典格式)
                if 'orbit_data' in const_data and 'satellites' in const_data['orbit_data']:
                    satellites = const_data['orbit_data']['satellites']
                    if isinstance(satellites, dict):
                        satellites_count = len(satellites)
                        logger.info(f"    ✅ orbit_data.satellites: 字典格式，{satellites_count} 顆衛星")
                    elif isinstance(satellites, list):
                        satellites_count = len(satellites)
                        logger.info(f"    ✅ orbit_data.satellites: 列表格式，{satellites_count} 顆衛星")
                    else:
                        logger.info(f"    ⚠️ orbit_data.satellites: {type(satellites).__name__} 格式")
                        
                # 檢查直接satellites欄位
                elif 'satellites' in const_data:
                    satellites = const_data['satellites']
                    if isinstance(satellites, (dict, list)):
                        satellites_count = len(satellites)
                        logger.info(f"    ✅ satellites: {type(satellites).__name__} 格式，{satellites_count} 顆衛星")
                    else:
                        logger.info(f"    ⚠️ satellites: {type(satellites).__name__} 格式")
                        
                # 檢查其他可能的結構
                else:
                    # 檢查是否有其他包含衛星數據的欄位
                    for key, value in const_data.items():
                        if isinstance(value, (dict, list)) and len(str(key).lower()) > 3:
                            if 'satellite' in key.lower() or 'data' in key.lower():
                                if isinstance(value, (dict, list)) and len(value) > 0:
                                    satellites_count = len(value)
                                    logger.info(f"    ✅ 找到 {key}: {type(value).__name__} 格式，{satellites_count} 項目")
                                    break
                
                analysis['constellations'][const_name] = satellites_count
                total_satellites += satellites_count
                
            analysis['satellites_count'] = total_satellites
            
        except Exception as e:
            logger.error(f"分析數據結構時發生錯誤: {e}")
            analysis['error'] = str(e)
            
        logger.info(f"  📊 {stage_name} 總計: {analysis['satellites_count']} 顆衛星")
        return analysis
        
    def check_file_cleanup(self, stage_name: str, expected_files: List[str]) -> Dict[str, Any]:
        """檢查檔案清理機制"""
        logger.info(f"🗑️ 檢查 {stage_name} 檔案清理機制...")
        
        cleanup_result = {
            'stage': stage_name,
            'files_checked': [],
            'files_cleaned': 0,
            'cleanup_success': True
        }
        
        base_path = Path("/app/data")
        
        for filename in expected_files:
            file_path = base_path / filename
            
            file_info = {
                'filename': filename,
                'exists_before': file_path.exists(),
                'size_before': 0,
                'cleaned': False
            }
            
            if file_path.exists():
                file_info['size_before'] = file_path.stat().st_size
                logger.info(f"  📁 發現舊檔案: {filename} ({file_info['size_before']} bytes)")
                
                # 模擬清理檢查 - 檢查是否會被處理器清理
                file_info['should_be_cleaned'] = True
            else:
                logger.info(f"  ✅ 無舊檔案: {filename}")
                file_info['should_be_cleaned'] = False
                
            cleanup_result['files_checked'].append(file_info)
            
        return cleanup_result
        
    def execute_stage4_verification(self, stage3_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行階段四驗證"""
        logger.info("================================================================================")
        logger.info("🔍 階段四：時序預處理驗證")
        logger.info("================================================================================")
        
        start_time = datetime.now()
        
        # 分析輸入數據
        input_analysis = self.analyze_data_structure(stage3_data, "階段四輸入")
        
        # 檢查檔案清理
        cleanup_check = self.check_file_cleanup("階段四", [
            "starlink_enhanced.json",
            "oneweb_enhanced.json", 
            "conversion_statistics.json"
        ])
        
        # 執行階段四處理
        logger.info("🚀 執行階段四時序預處理...")
        try:
            stage4_output = self.stage4_processor.process_timeseries_preprocessing(stage3_data)
            processing_success = True
            error_message = None
        except Exception as e:
            logger.error(f"階段四處理失敗: {e}")
            stage4_output = None
            processing_success = False
            error_message = str(e)
        
        # 分析輸出數據
        if stage4_output:
            output_analysis = self.analyze_data_structure(stage4_output, "階段四輸出")
        else:
            output_analysis = {'satellites_count': 0, 'error': error_message}
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = {
            'stage': 'stage4',
            'processing_time': processing_time,
            'processing_success': processing_success,
            'input_analysis': input_analysis,
            'output_analysis': output_analysis,
            'cleanup_check': cleanup_check,
            'data_flow': f"{input_analysis['satellites_count']} → {output_analysis['satellites_count']}",
            'error_message': error_message
        }
        
        logger.info(f"✅ 階段四驗證完成")
        logger.info(f"  ⏱️  處理時間: {processing_time:.2f} 秒")
        logger.info(f"  📊 數據流: {result['data_flow']}")
        
        return result, stage4_output
        
    def execute_stage5_verification(self, stage4_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行階段五驗證"""
        logger.info("================================================================================")
        logger.info("🔍 階段五：數據整合驗證")
        logger.info("================================================================================")
        
        start_time = datetime.now()
        
        # 分析輸入數據
        input_analysis = self.analyze_data_structure(stage4_data, "階段五輸入")
        
        # 檢查檔案清理
        cleanup_check = self.check_file_cleanup("階段五", [
            "data_integration_output.json",
            "integration_statistics.json"
        ])
        
        # 執行階段五處理
        logger.info("🚀 執行階段五數據整合...")
        try:
            stage5_output = self.stage5_processor.process_data_integration(stage4_data)
            processing_success = True
            error_message = None
        except Exception as e:
            logger.error(f"階段五處理失敗: {e}")
            stage5_output = None
            processing_success = False
            error_message = str(e)
        
        # 分析輸出數據
        if stage5_output:
            output_analysis = self.analyze_data_structure(stage5_output, "階段五輸出")
        else:
            output_analysis = {'satellites_count': 0, 'error': error_message}
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = {
            'stage': 'stage5',
            'processing_time': processing_time,
            'processing_success': processing_success,
            'input_analysis': input_analysis,
            'output_analysis': output_analysis,
            'cleanup_check': cleanup_check,
            'data_flow': f"{input_analysis['satellites_count']} → {output_analysis['satellites_count']}",
            'error_message': error_message
        }
        
        logger.info(f"✅ 階段五驗證完成")
        logger.info(f"  ⏱️  處理時間: {processing_time:.2f} 秒")
        logger.info(f"  📊 數據流: {result['data_flow']}")
        
        return result, stage5_output
        
    def execute_stage6_verification(self, stage5_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行階段六驗證 - 重點關注時序保存率問題"""
        logger.info("================================================================================")
        logger.info("🔍 階段六：動態池規劃驗證 (重點檢查時序保存率)")
        logger.info("================================================================================")
        
        start_time = datetime.now()
        
        # 分析輸入數據
        input_analysis = self.analyze_data_structure(stage5_data, "階段六輸入")
        
        # 檢查檔案清理
        cleanup_check = self.check_file_cleanup("階段六", [
            "enhanced_dynamic_pools_output.json",
            "dynamic_planning_statistics.json"
        ])
        
        # 特別檢查時序數據結構
        logger.info("🔍 特別檢查時序數據結構...")
        timeseries_analysis = self.analyze_timeseries_structure(stage5_data)
        
        # 執行階段六處理
        logger.info("🚀 執行階段六動態池規劃...")
        try:
            stage6_output = self.stage6_processor.process_enhanced_dynamic_pool_planning(stage5_data)
            processing_success = True
            error_message = None
        except Exception as e:
            logger.error(f"階段六處理失敗: {e}")
            stage6_output = None
            processing_success = False
            error_message = str(e)
        
        # 分析輸出數據
        if stage6_output:
            output_analysis = self.analyze_data_structure(stage6_output, "階段六輸出")
            # 特別檢查時序保存率
            timeseries_preservation = self.check_timeseries_preservation(stage5_data, stage6_output)
        else:
            output_analysis = {'satellites_count': 0, 'error': error_message}
            timeseries_preservation = {'preservation_rate': 0.0, 'error': error_message}
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = {
            'stage': 'stage6',
            'processing_time': processing_time,
            'processing_success': processing_success,
            'input_analysis': input_analysis,
            'output_analysis': output_analysis,
            'cleanup_check': cleanup_check,
            'timeseries_analysis': timeseries_analysis,
            'timeseries_preservation': timeseries_preservation,
            'data_flow': f"{input_analysis['satellites_count']} → {output_analysis['satellites_count']}",
            'error_message': error_message
        }
        
        logger.info(f"✅ 階段六驗證完成")
        logger.info(f"  ⏱️  處理時間: {processing_time:.2f} 秒")
        logger.info(f"  📊 數據流: {result['data_flow']}")
        logger.info(f"  📈 時序保存率: {timeseries_preservation.get('preservation_rate', 0):.1%}")
        
        return result, stage6_output
        
    def analyze_timeseries_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析時序數據結構"""
        logger.info("📊 分析時序數據結構...")
        
        timeseries_info = {
            'has_timeseries': False,
            'timeseries_fields': [],
            'total_timestamps': 0,
            'constellations_with_timeseries': {}
        }
        
        try:
            constellations = data.get('constellations', {})
            
            for const_name, const_data in constellations.items():
                const_timeseries = {
                    'has_timeseries': False,
                    'timestamps': 0,
                    'satellites_with_timeseries': 0
                }
                
                # 檢查各種可能的時序結構
                satellites_data = None
                
                if 'orbit_data' in const_data and 'satellites' in const_data['orbit_data']:
                    satellites_data = const_data['orbit_data']['satellites']
                elif 'satellites' in const_data:
                    satellites_data = const_data['satellites']
                
                if satellites_data and isinstance(satellites_data, dict):
                    for sat_id, sat_data in satellites_data.items():
                        if isinstance(sat_data, dict):
                            # 檢查常見的時序欄位
                            timeseries_fields = ['positions', 'orbit_data', 'trajectory', 'timestamps']
                            for field in timeseries_fields:
                                if field in sat_data:
                                    field_data = sat_data[field]
                                    if isinstance(field_data, list) and len(field_data) > 0:
                                        const_timeseries['has_timeseries'] = True
                                        const_timeseries['timestamps'] = max(const_timeseries['timestamps'], len(field_data))
                                        const_timeseries['satellites_with_timeseries'] += 1
                                        if field not in timeseries_info['timeseries_fields']:
                                            timeseries_info['timeseries_fields'].append(field)
                                        break
                
                timeseries_info['constellations_with_timeseries'][const_name] = const_timeseries
                if const_timeseries['has_timeseries']:
                    timeseries_info['has_timeseries'] = True
                    timeseries_info['total_timestamps'] += const_timeseries['timestamps']
                
                logger.info(f"    {const_name}: {const_timeseries['satellites_with_timeseries']} 衛星有時序數據，{const_timeseries['timestamps']} 時間點")
                
        except Exception as e:
            logger.error(f"分析時序結構時發生錯誤: {e}")
            timeseries_info['error'] = str(e)
        
        logger.info(f"  📊 時序分析: 有時序數據={timeseries_info['has_timeseries']}, 總時間點={timeseries_info['total_timestamps']}")
        
        return timeseries_info
        
    def check_timeseries_preservation(self, input_data: Dict[str, Any], output_data: Dict[str, Any]) -> Dict[str, Any]:
        """檢查時序保存率"""
        logger.info("📈 檢查時序保存率...")
        
        preservation = {
            'preservation_rate': 0.0,
            'input_timeseries_count': 0,
            'output_timeseries_count': 0,
            'details': {}
        }
        
        try:
            input_ts = self.analyze_timeseries_structure(input_data)
            output_ts = self.analyze_timeseries_structure(output_data)
            
            preservation['input_timeseries_count'] = input_ts['total_timestamps']
            preservation['output_timeseries_count'] = output_ts['total_timestamps']
            
            if preservation['input_timeseries_count'] > 0:
                preservation['preservation_rate'] = preservation['output_timeseries_count'] / preservation['input_timeseries_count']
            
            preservation['details'] = {
                'input_analysis': input_ts,
                'output_analysis': output_ts
            }
            
        except Exception as e:
            logger.error(f"檢查時序保存率時發生錯誤: {e}")
            preservation['error'] = str(e)
        
        logger.info(f"  📈 時序保存率: {preservation['preservation_rate']:.1%} ({preservation['output_timeseries_count']}/{preservation['input_timeseries_count']})")
        
        return preservation
        
    def execute_full_verification(self) -> Dict[str, Any]:
        """執行完整的階段四到六驗證"""
        logger.info("🚀 開始完整的階段四到六驗證執行")
        logger.info("================================================================================")
        
        start_time = datetime.now()
        
        # 首先執行階段一到三獲取數據
        logger.info("🔄 重新執行階段一到三獲取基礎數據...")
        stage1_data = self.stage1_processor.process_tle_orbital_calculation()
        stage2_data = self.stage2_processor.process_intelligent_satellite_filter(stage1_data)
        stage3_data = self.stage3_processor.process_signal_quality_analysis(stage2_data)
        
        logger.info("✅ 基礎數據準備完成，開始階段四到六驗證")
        
        # 執行階段四驗證
        stage4_result, stage4_data = self.execute_stage4_verification(stage3_data)
        
        # 執行階段五驗證
        if stage4_data:
            stage5_result, stage5_data = self.execute_stage5_verification(stage4_data)
        else:
            logger.error("階段四失敗，跳過階段五")
            stage5_result = {'stage': 'stage5', 'processing_success': False, 'error_message': 'Stage4 failed'}
            stage5_data = None
        
        # 執行階段六驗證
        if stage5_data:
            stage6_result, stage6_data = self.execute_stage6_verification(stage5_data)
        else:
            logger.error("階段五失敗，跳過階段六")
            stage6_result = {'stage': 'stage6', 'processing_success': False, 'error_message': 'Stage5 failed'}
            stage6_data = None
        
        total_time = (datetime.now() - start_time).total_seconds()
        
        # 生成總結報告
        verification_report = {
            'verification_timestamp': datetime.now(timezone.utc).isoformat(),
            'total_processing_time': total_time,
            'stages_results': {
                'stage4': stage4_result,
                'stage5': stage5_result,
                'stage6': stage6_result
            },
            'overall_success': all([
                stage4_result.get('processing_success', False),
                stage5_result.get('processing_success', False),
                stage6_result.get('processing_success', False)
            ]),
            'data_flow_summary': f"S4:{stage4_result.get('data_flow', 'failed')} | S5:{stage5_result.get('data_flow', 'failed')} | S6:{stage6_result.get('data_flow', 'failed')}",
            'timeseries_preservation_rate': stage6_result.get('timeseries_preservation', {}).get('preservation_rate', 0.0)
        }
        
        logger.info("================================================================================")
        logger.info("🎯 階段四到六驗證執行完成")
        logger.info("================================================================================")
        logger.info(f"⏱️  總處理時間: {total_time:.2f} 秒")
        logger.info(f"📊 整體成功率: {verification_report['overall_success']}")
        logger.info(f"📈 時序保存率: {verification_report['timeseries_preservation_rate']:.1%}")
        logger.info(f"🔄 數據流摘要: {verification_report['data_flow_summary']}")
        
        return verification_report

def main():
    """主函數"""
    try:
        processor = Stage4To6VerificationProcessor()
        report = processor.execute_full_verification()
        
        # 保存驗證報告
        report_path = Path("/app/data/stage4_to_6_verification_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📄 驗證報告已保存: {report_path}")
        
        return report
        
    except Exception as e:
        logger.error(f"驗證執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()