#!/usr/bin/env python3
"""
調試版階段一到階段三處理器

完整追蹤數據流向，找出378→399衛星數量異常的原因
仔細記錄每個階段的輸入輸出數據，定位問題所在
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

logger = logging.getLogger(__name__)

class DebugStage1ToStage3Processor:
    """調試版階段一到階段三處理器"""
    
    def __init__(self):
        """初始化調試處理器"""
        logger.info("🔍 調試版階段一到階段三處理器初始化")
        
        # 初始化階段一處理器（全量模式）
        self.stage1_processor = Stage1TLEProcessor(
            tle_data_dir="/app/tle_data",
            output_dir="/app/data",
            sample_mode=False  # 全量處理模式
        )
        
        # 初始化階段二處理器
        self.stage2_processor = IntelligentSatelliteFilterProcessor(
            input_dir="/app/data",
            output_dir="/app/data"
        )
        
        # 初始化階段三處理器
        self.stage3_processor = SignalQualityAnalysisProcessor(
            input_dir="/app/data",
            output_dir="/app/data"
        )
        
        logger.info("✅ 調試處理器初始化完成")
        
    def analyze_data_structure(self, data: Dict[str, Any], stage_name: str) -> Dict[str, Any]:
        """詳細分析數據結構"""
        logger.info(f"🔍 分析 {stage_name} 數據結構...")
        
        analysis = {
            'stage': stage_name,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data_structure': {},
            'satellite_counts': {},
            'total_satellites': 0
        }
        
        # 分析metadata
        metadata = data.get('metadata', {})
        analysis['data_structure']['has_metadata'] = bool(metadata)
        if metadata:
            analysis['data_structure']['metadata_keys'] = list(metadata.keys())
            analysis['total_satellites_from_metadata'] = metadata.get('total_satellites', 0)
        
        # 分析constellations
        constellations = data.get('constellations', {})
        analysis['data_structure']['has_constellations'] = bool(constellations)
        analysis['data_structure']['constellation_names'] = list(constellations.keys())
        
        total_actual = 0
        for const_name, const_data in constellations.items():
            logger.info(f"  🔍 詳細分析星座: {const_name}")
            logger.info(f"    const_data 類型: {type(const_data)}")
            logger.info(f"    const_data 鍵: {list(const_data.keys()) if isinstance(const_data, dict) else 'not_dict'}")
            
            # 檢查不同的數據結構模式
            satellites_count = 0
            
            # 🔧 修復：檢查 orbit_data.satellites (階段一輸出是字典格式)
            if 'orbit_data' in const_data and 'satellites' in const_data['orbit_data']:
                satellites = const_data['orbit_data']['satellites']
                logger.info(f"    🔍 orbit_data.satellites 類型: {type(satellites)}")
                
                if isinstance(satellites, dict):
                    # 階段一輸出格式：{satellite_id: satellite_data}
                    satellites_count = len(satellites)
                    logger.info(f"    ✅ {const_name} orbit_data.satellites: 字典格式，{satellites_count} 顆衛星")
                    # 顯示前3個鍵作為樣本
                    sample_keys = list(satellites.keys())[:3]
                    logger.info(f"    📝 樣本鍵: {sample_keys}")
                    
                elif isinstance(satellites, list):
                    satellites_count = len(satellites)
                    logger.info(f"    ✅ {const_name} orbit_data.satellites: 列表格式，{satellites_count} 顆衛星")
                else:
                    satellites_count = 0
                    logger.warning(f"    ❌ {const_name} orbit_data.satellites: {type(satellites).__name__} 格式，無法計算數量")
                    
            # 然後檢查直接的 satellites 欄位 (階段三可能使用的結構)
            elif 'satellites' in const_data:
                satellites = const_data['satellites']
                logger.info(f"    🔍 直接 satellites 類型: {type(satellites)}")
                
                if isinstance(satellites, (dict, list)):
                    satellites_count = len(satellites)
                    logger.info(f"    ✅ {const_name} satellites: {type(satellites).__name__} 格式，{satellites_count} 顆衛星")
                else:
                    satellites_count = 0
                    logger.warning(f"    ❌ {const_name} satellites: {type(satellites).__name__} 格式，無法計算數量")
            else:
                logger.warning(f"    ⚠️ {const_name}: 未找到 orbit_data.satellites 或 satellites 欄位")
            
            analysis['satellite_counts'][const_name] = satellites_count
            total_actual += satellites_count
            
            logger.info(f"  {const_name}: {satellites_count} 顆衛星")
        
        analysis['total_satellites'] = total_actual
        
        logger.info(f"  總計: {total_actual} 顆衛星")
        logger.info(f"  metadata顯示: {metadata.get('total_satellites', '未找到')} 顆衛星")
        
        return analysis
        
    def execute_stage1_debug(self) -> Dict[str, Any]:
        """執行階段一並詳細記錄"""
        logger.info("=" * 80)
        logger.info("🔍 階段一：TLE數據載入與SGP4軌道計算 (調試模式)")
        logger.info("=" * 80)
        
        stage1_start_time = datetime.now()
        
        try:
            stage1_data = self.stage1_processor.process_tle_orbital_calculation()
            stage1_end_time = datetime.now()
            stage1_duration = (stage1_end_time - stage1_start_time).total_seconds()
            
            # 詳細分析階段一輸出
            stage1_analysis = self.analyze_data_structure(stage1_data, "階段一輸出")
            
            logger.info("✅ 階段一處理完成")
            logger.info(f"  ⏱️  處理時間: {stage1_duration:.1f} 秒")
            logger.info(f"  📊 實際衛星數: {stage1_analysis['total_satellites']}")
            
            return {
                'stage1_data': stage1_data,
                'stage1_analysis': stage1_analysis,
                'processing_time': stage1_duration
            }
            
        except Exception as e:
            logger.error(f"❌ 階段一處理失敗: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        
    def execute_stage2_debug(self, stage1_result: Dict[str, Any]) -> Dict[str, Any]:
        """執行階段二並詳細記錄"""
        logger.info("=" * 80)
        logger.info("🔍 階段二：智能衛星篩選 (調試模式)")
        logger.info("=" * 80)
        
        stage1_data = stage1_result['stage1_data']
        stage1_analysis = stage1_result['stage1_analysis']
        
        logger.info(f"📥 階段二輸入數據: {stage1_analysis['total_satellites']} 顆衛星")
        
        stage2_start_time = datetime.now()
        
        try:
            # 直接使用階段一的記憶體數據
            stage2_data = self.stage2_processor.process_intelligent_filtering(
                orbital_data=stage1_data,
                save_output=False  # 不保存檔案，使用記憶體傳遞
            )
            stage2_end_time = datetime.now()
            stage2_duration = (stage2_end_time - stage2_start_time).total_seconds()
            
            # 詳細分析階段二輸出
            stage2_analysis = self.analyze_data_structure(stage2_data, "階段二輸出")
            
            # 檢查篩選效果
            input_count = stage1_analysis['total_satellites']
            output_count = stage2_analysis['total_satellites']
            retention_rate = (output_count / input_count * 100) if input_count > 0 else 0
            
            logger.info("✅ 階段二處理完成")
            logger.info(f"  ⏱️  處理時間: {stage2_duration:.1f} 秒")
            logger.info(f"  📊 篩選結果: {input_count} → {output_count} 顆衛星")
            logger.info(f"  📈 保留率: {retention_rate:.1f}%")
            
            # 詳細比較階段一和階段二
            logger.info("🔍 詳細數據對比:")
            for const_name in stage1_analysis['satellite_counts']:
                stage1_count = stage1_analysis['satellite_counts'].get(const_name, 0)
                stage2_count = stage2_analysis['satellite_counts'].get(const_name, 0)
                logger.info(f"  {const_name}: {stage1_count} → {stage2_count}")
            
            return {
                'stage2_data': stage2_data,
                'stage2_analysis': stage2_analysis,
                'processing_time': stage2_duration,
                'data_flow_verification': {
                    'input_count': input_count,
                    'output_count': output_count,
                    'retention_rate': retention_rate,
                    'expected_reduction': True,
                    'actual_reduction': output_count < input_count
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 階段二處理失敗: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        
    def execute_stage3_debug(self, stage2_result: Dict[str, Any]) -> Dict[str, Any]:
        """執行階段三並詳細追蹤每個步驟"""
        logger.info("=" * 80)
        logger.info("🔍 階段三：信號品質分析與3GPP事件處理 (詳細調試模式)")
        logger.info("=" * 80)
        
        stage2_data = stage2_result['stage2_data']
        stage2_analysis = stage2_result['stage2_analysis']
        
        logger.info(f"📥 階段三輸入數據: {stage2_analysis['total_satellites']} 顆衛星")
        
        # 在執行階段三之前，詳細檢查輸入數據
        logger.info("🔍 階段三執行前輸入數據驗證:")
        input_verification = self.verify_stage3_input(stage2_data)
        
        stage3_start_time = datetime.now()
        
        try:
            # 使用詳細追蹤模式執行階段三
            stage3_data = self.execute_stage3_with_detailed_tracking(stage2_data)
            stage3_end_time = datetime.now()
            stage3_duration = (stage3_end_time - stage3_start_time).total_seconds()
            
            # 詳細分析階段三輸出
            stage3_analysis = self.analyze_data_structure(stage3_data, "階段三輸出")
            
            # 檢查數據變化
            input_count = stage2_analysis['total_satellites']
            output_count = stage3_analysis['total_satellites']
            
            logger.info("✅ 階段三處理完成")
            logger.info(f"  ⏱️  處理時間: {stage3_duration:.1f} 秒")
            logger.info(f"  📊 處理結果: {input_count} → {output_count} 顆衛星")
            
            # 🚨 重要：分析數量變化
            if output_count != input_count:
                logger.warning("🚨 發現數量異常變化！")
                logger.warning(f"  輸入: {input_count} 顆")
                logger.warning(f"  輸出: {output_count} 顆")
                logger.warning(f"  差異: {output_count - input_count:+} 顆")
                
                # 詳細星座對比
                logger.warning("🔍 星座數量變化詳情:")
                for const_name in set(stage2_analysis['satellite_counts'].keys()) | set(stage3_analysis['satellite_counts'].keys()):
                    input_const = stage2_analysis['satellite_counts'].get(const_name, 0)
                    output_const = stage3_analysis['satellite_counts'].get(const_name, 0)
                    diff = output_const - input_const
                    logger.warning(f"  {const_name}: {input_const} → {output_const} ({diff:+})")
            else:
                logger.info("✅ 衛星數量保持一致，符合預期")
            
            return {
                'stage3_data': stage3_data,
                'stage3_analysis': stage3_analysis,
                'processing_time': stage3_duration,
                'input_verification': input_verification,
                'data_flow_verification': {
                    'input_count': input_count,
                    'output_count': output_count,
                    'count_change': output_count - input_count,
                    'unexpected_change': output_count != input_count
                }
            }
            
        except Exception as e:
            logger.error(f"❌ 階段三處理失敗: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        
    def verify_stage3_input(self, stage2_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證階段三輸入數據的完整性"""
        logger.info("🔍 驗證階段三輸入數據...")
        
        verification = {
            'has_metadata': 'metadata' in stage2_data,
            'has_constellations': 'constellations' in stage2_data,
            'constellations_count': len(stage2_data.get('constellations', {})),
            'constellation_details': {}
        }
        
        constellations = stage2_data.get('constellations', {})
        for const_name, const_data in constellations.items():
            satellites = const_data.get('satellites', [])
            verification['constellation_details'][const_name] = {
                'satellite_count': len(satellites),
                'has_satellites_field': 'satellites' in const_data,
                'satellites_is_list': isinstance(satellites, list),
                'first_satellite_keys': list(satellites[0].keys()) if satellites else []
            }
            
            logger.info(f"  {const_name}: {len(satellites)} 顆衛星")
            if satellites:
                logger.info(f"    第一顆衛星包含欄位: {list(satellites[0].keys())[:5]}...")
        
        return verification
        
    def execute_stage3_with_detailed_tracking(self, stage2_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行階段三並詳細追蹤每個內部步驟"""
        logger.info("🔍 開始階段三詳細追蹤執行...")
        
        # 步驟1: 載入數據
        logger.info("🔍 步驟1: 階段三數據載入...")
        logger.info(f"  輸入數據類型: {type(stage2_data)}")
        logger.info(f"  輸入數據主要鍵: {list(stage2_data.keys())}")
        
        # 步驟2: 信號品質分析
        logger.info("🔍 步驟2: 執行信號品質分析...")
        signal_enhanced_data = self.stage3_processor.calculate_signal_quality(stage2_data)
        signal_analysis = self.analyze_data_structure(signal_enhanced_data, "信號品質分析後")
        logger.info(f"  信號分析後衛星數: {signal_analysis['total_satellites']}")
        
        # 步驟3: 3GPP事件分析
        logger.info("🔍 步驟3: 執行3GPP事件分析...")
        event_enhanced_data = self.stage3_processor.analyze_3gpp_events(signal_enhanced_data)
        event_analysis = self.analyze_data_structure(event_enhanced_data, "3GPP事件分析後")
        logger.info(f"  3GPP分析後衛星數: {event_analysis['total_satellites']}")
        
        # 步驟4: 生成最終建議
        logger.info("🔍 步驟4: 生成最終建議...")
        final_data = self.stage3_processor.generate_final_recommendations(event_enhanced_data)
        final_analysis = self.analyze_data_structure(final_data, "最終建議生成後")
        logger.info(f"  最終建議後衛星數: {final_analysis['total_satellites']}")
        
        # 檢查每個步驟的數據變化
        input_analysis = self.analyze_data_structure(stage2_data, "階段三原始輸入")
        
        logger.info("🔍 階段三內部數據流追蹤:")
        logger.info(f"  原始輸入: {input_analysis['total_satellites']} 顆")
        logger.info(f"  信號分析後: {signal_analysis['total_satellites']} 顆")
        logger.info(f"  3GPP分析後: {event_analysis['total_satellites']} 顆")  
        logger.info(f"  最終建議後: {final_analysis['total_satellites']} 顆")
        
        # 🚨 找出數據增加的確切位置
        steps = [
            ("原始輸入", input_analysis['total_satellites']),
            ("信號分析後", signal_analysis['total_satellites']),
            ("3GPP分析後", event_analysis['total_satellites']),
            ("最終建議後", final_analysis['total_satellites'])
        ]
        
        for i in range(1, len(steps)):
            prev_step, prev_count = steps[i-1]
            curr_step, curr_count = steps[i]
            if curr_count != prev_count:
                logger.warning(f"🚨 發現數據變化：{prev_step} ({prev_count}) → {curr_step} ({curr_count})")
                logger.warning(f"  變化量: {curr_count - prev_count:+} 顆衛星")
        
        return final_data
        
    def execute_complete_debug_flow(self) -> Dict[str, Any]:
        """執行完整的調試流程"""
        logger.info("🔍 開始完整的階段一到三調試執行")
        
        # 階段一
        stage1_result = self.execute_stage1_debug()
        
        # 階段二  
        stage2_result = self.execute_stage2_debug(stage1_result)
        
        # 階段三
        stage3_result = self.execute_stage3_debug(stage2_result)
        
        # 生成完整調試報告
        debug_report = self.generate_debug_report(stage1_result, stage2_result, stage3_result)
        
        return {
            'stage1_result': stage1_result,
            'stage2_result': stage2_result, 
            'stage3_result': stage3_result,
            'debug_report': debug_report
        }
        
    def generate_debug_report(self, stage1_result: Dict, stage2_result: Dict, stage3_result: Dict) -> Dict[str, Any]:
        """生成詳細的調試報告"""
        logger.info("📝 生成詳細調試報告...")
        
        s1_count = stage1_result['stage1_analysis']['total_satellites']
        s2_count = stage2_result['stage2_analysis']['total_satellites']
        s3_count = stage3_result['stage3_analysis']['total_satellites']
        
        report = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'data_flow_summary': {
                'stage1_output': s1_count,
                'stage2_output': s2_count,
                'stage3_output': s3_count,
                'stage1_to_2_change': s2_count - s1_count,
                'stage2_to_3_change': s3_count - s2_count,
                'total_change': s3_count - s1_count
            },
            'anomaly_detection': {
                'stage1_to_2_normal': s2_count <= s1_count,  # 篩選應該減少
                'stage2_to_3_normal': s3_count == s2_count,   # 信號分析不應該增加
                'overall_flow_normal': s3_count <= s1_count
            },
            'processing_times': {
                'stage1_seconds': stage1_result['processing_time'],
                'stage2_seconds': stage2_result['processing_time'],
                'stage3_seconds': stage3_result['processing_time'],
                'total_seconds': stage1_result['processing_time'] + stage2_result['processing_time'] + stage3_result['processing_time']
            }
        }
        
        # 判斷是否有異常
        if not report['anomaly_detection']['stage2_to_3_normal']:
            report['critical_issue'] = {
                'detected': True,
                'issue_type': 'unexpected_satellite_count_increase_in_stage3',
                'description': f'階段三不應該增加衛星數量，但發現從 {s2_count} 增加到 {s3_count}',
                'requires_investigation': True
            }
        else:
            report['critical_issue'] = {
                'detected': False,
                'description': '數據流正常'
            }
        
        logger.info("✅ 調試報告生成完成")
        return report

def main():
    """主函數"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        processor = DebugStage1ToStage3Processor()
        result = processor.execute_complete_debug_flow()
        
        debug_report = result['debug_report']
        
        logger.info("=" * 80)
        logger.info("🔍 調試執行完成 - 數據流摘要")
        logger.info("=" * 80)
        
        flow = debug_report['data_flow_summary']
        logger.info(f"📊 完整數據流: {flow['stage1_output']} → {flow['stage2_output']} → {flow['stage3_output']}")
        logger.info(f"📈 階段變化: S1→S2({flow['stage1_to_2_change']:+}) S2→S3({flow['stage2_to_3_change']:+})")
        
        if debug_report['critical_issue']['detected']:
            logger.error("🚨 發現關鍵問題:")
            logger.error(f"  {debug_report['critical_issue']['description']}")
        else:
            logger.info("✅ 數據流驗證通過")
        
        return True, result
        
    except Exception as e:
        logger.error(f"💥 調試執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False, None

if __name__ == "__main__":
    success, result = main()
    sys.exit(0 if success else 1)