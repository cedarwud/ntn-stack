#!/usr/bin/env python3
"""
🚀 LEO核心系統主流程控制器
==========================

統一六階段處理流程的主要控制器，整合所有階段並確保正確的執行順序：
1. TLE載入與SGP4軌道計算  
2. 智能衛星篩選
3. 信號品質分析與3GPP事件處理
4. 時間序列預處理
5. 數據整合與接口準備
6. 動態衛星池規劃 (增強版，整合模擬退火優化)

特色：
- 純六模組架構，保持系統完整性
- 整合shared_core技術棧和模擬退火演算法
- 完整的錯誤處理和狀態追蹤
- 支援單模組執行和完整流程執行
"""

import asyncio
import json
import logging
import time
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# 導入所有階段處理器
sys.path.insert(0, '/home/sat/ntn-stack/netstack/src')

from stages.tle_orbital_calculation_processor import Stage1TLEProcessor as TLEOrbitalCalculationProcessor
from stages.intelligent_satellite_filter_processor import IntelligentSatelliteFilterProcessor  
from stages.signal_quality_analysis_processor import SignalQualityAnalysisProcessor
from stages.timeseries_preprocessing_processor import TimeseriesPreprocessingProcessor
from stages.data_integration_processor import DataIntegrationProcessor, DataIntegrationConfig
from stages.enhanced_dynamic_pool_planner import EnhancedDynamicPoolPlanner, create_enhanced_dynamic_pool_planner

@dataclass
class PipelineConfig:
    """主流程配置"""
    # 基礎目錄配置
    base_data_dir: str = "/home/sat/ntn-stack/netstack/data"
    
    # 輸出目錄配置 - 功能描述性命名
    tle_calculation_output_dir: str = "tle_calculation_outputs"
    intelligent_filtering_output_dir: str = "intelligent_filtering_outputs" 
    signal_analysis_output_dir: str = "signal_analysis_outputs"
    timeseries_preprocessing_output_dir: str = "timeseries_preprocessing_outputs"
    data_integration_output_dir: str = "data_integration_outputs"
    dynamic_pool_planning_output_dir: str = "dynamic_pool_planning_outputs"
    
    # 執行配置
    enable_processor_validation: bool = True
    enable_intermediate_cleanup: bool = False
    save_all_intermediate_results: bool = True
    
    # 增強功能配置
    enable_enhanced_dynamic_pool_planner: bool = True
    enable_performance_monitoring: bool = True

class LEOMainPipelineController:
    """LEO核心系統主流程控制器"""
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.pipeline_start_time = time.time()
        
        # 處理器執行狀態追蹤
        self.processor_status = {
            'tle_orbital_calculation': {'completed': False, 'output_file': None, 'processing_time': 0.0},
            'intelligent_satellite_filter': {'completed': False, 'output_file': None, 'processing_time': 0.0},
            'signal_quality_analysis': {'completed': False, 'output_file': None, 'processing_time': 0.0},
            'timeseries_preprocessing': {'completed': False, 'output_file': None, 'processing_time': 0.0},
            'data_integration': {'completed': False, 'output_file': None, 'processing_time': 0.0},
            'dynamic_pool_planning': {'completed': False, 'output_file': None, 'processing_time': 0.0}
        }
        
        # 確保輸出目錄存在
        self._setup_output_directories()
        
        self.logger.info("🚀 LEO核心系統主流程控制器初始化完成")
        self.logger.info("📋 六模組流程架構：TLE載入→智能篩選→信號分析→時間序列→數據整合→動態池規劃")
        
    def _setup_output_directories(self):
        """設置輸出目錄結構"""
        base_path = Path(self.config.base_data_dir)
        base_path.mkdir(exist_ok=True)
        
        # 功能描述性目錄命名
        output_dirs = [
            'tle_calculation_outputs', 'intelligent_filtering_outputs', 'signal_analysis_outputs',
            'timeseries_preprocessing_outputs', 'data_integration_outputs', 'dynamic_pool_planning_outputs'
        ]
        for output_dir in output_dirs:
            (base_path / output_dir).mkdir(exist_ok=True)
    
    async def execute_complete_pipeline(self) -> Dict[str, Any]:
        """執行完整的六模組流程"""
        try:
            self.logger.info("🌟 開始執行完整LEO核心系統六模組流程")
            self.logger.info("=" * 80)
            
            pipeline_results = {
                'pipeline_start_time': datetime.now(timezone.utc).isoformat(),
                'pipeline_architecture': 'six_processor_enhanced_with_simulated_annealing',
                'technology_stack': [
                    'shared_core_data_models',
                    'auto_cleanup_manager',
                    'incremental_update_manager', 
                    'simulated_annealing_optimizer'
                ],
                'processors': {},
                'pipeline_success': False,
                'total_processing_time': 0.0
            }
            
            # 1. TLE載入與SGP4軌道計算
            tle_result = await self._execute_tle_orbital_calculation()
            pipeline_results['processors']['tle_orbital_calculation'] = tle_result
            
            if not tle_result['success']:
                raise Exception("TLE軌道計算執行失敗")
            
            # 2. 智能衛星篩選 (v3.0記憶體傳遞模式)
            filter_result = await self._execute_intelligent_satellite_filter_memory(tle_result['satellite_data'])
            pipeline_results['processors']['intelligent_satellite_filter'] = filter_result
            
            if not filter_result['success']:
                raise Exception("智能衛星篩選執行失敗")
            
            # 3. 信號品質分析與3GPP事件處理 (混合模式：記憶體輸入，檔案輸出)
            signal_result = await self._execute_signal_quality_analysis_hybrid(filter_result['satellite_data'])
            pipeline_results['processors']['signal_quality_analysis'] = signal_result
            
            if not signal_result['success']:
                raise Exception("信號品質分析執行失敗")
            
            # 4. 時間序列預處理
            timeseries_result = await self._execute_timeseries_preprocessing(signal_result['output_file'])
            pipeline_results['processors']['timeseries_preprocessing'] = timeseries_result
            
            if not timeseries_result['success']:
                raise Exception("時間序列預處理執行失敗")
            
            # 5. 數據整合與接口準備
            integration_result = await self._execute_data_integration(timeseries_result['output_file'])
            pipeline_results['processors']['data_integration'] = integration_result
            
            if not integration_result['success']:
                raise Exception("數據整合執行失敗")
            
            # 6. 動態衛星池規劃 (增強版，整合模擬退火優化)
            pool_result = await self._execute_dynamic_pool_planning(integration_result['output_file'])
            pipeline_results['processors']['dynamic_pool_planning'] = pool_result
            
            if not pool_result['success']:
                raise Exception("動態池規劃執行失敗")
            
            self.logger.info("🎉 六模組完整流程執行成功！")
            self.logger.info("📊 模組1-2: 記憶體傳遞模式 (大數據高效)")
            self.logger.info("📊 模組3-6: 檔案儲存模式 (篩選後數據)")
            
            # 計算總處理時間
            total_time = time.time() - self.pipeline_start_time
            pipeline_results['total_processing_time'] = round(total_time, 2)
            pipeline_results['pipeline_success'] = True
            pipeline_results['pipeline_completion_time'] = datetime.now(timezone.utc).isoformat()
            
            # 生成流程總結
            pipeline_results['pipeline_summary'] = self._generate_pipeline_summary()
            
            self.logger.info("🎉 完整LEO核心系統六模組流程執行成功！")
            self.logger.info(f"⏱️ 總處理時間: {total_time:.2f} 秒")
            self.logger.info("=" * 80)
            
            return pipeline_results
            
        except Exception as e:
            self.logger.error(f"❌ 主流程執行失敗: {e}")
            return {
                'pipeline_success': False,
                'error': str(e),
                'total_processing_time': time.time() - self.pipeline_start_time,
                'completed_processors': [k for k, v in self.processor_status.items() if v['completed']]
            }
    
    async def _execute_tle_orbital_calculation(self) -> Dict[str, Any]:
        """執行TLE載入與SGP4軌道計算"""
        self.logger.info("🛰️ 執行 TLE載入與SGP4軌道計算")
        
        try:
            processor_start_time = time.time()
            
            processor = TLEOrbitalCalculationProcessor()
            tle_data = processor.process_tle_orbital_calculation()  # 返回記憶體數據
            
            processing_time = time.time() - processor_start_time
            
            # v3.0記憶體傳遞模式：不需要檔案路徑
            self.processor_status['tle_orbital_calculation'] = {
                'completed': True,
                'output_file': None,  # 記憶體傳遞模式
                'processing_time': processing_time
            }
            
            self.logger.info(f"✅ TLE軌道計算完成 - 處理時間: {processing_time:.2f}秒")
            
            return {
                'success': True,
                'processor': 'tle_orbital_calculation',
                'satellite_data': tle_data,  # 傳遞記憶體數據
                'processing_time': processing_time,
                'processor_description': 'TLE載入與SGP4軌道計算'
            }
            
        except Exception as e:
            self.logger.error(f"❌ TLE軌道計算執行失敗: {e}")
            return {
                'success': False,
                'processor': 'tle_orbital_calculation',
                'error': str(e)
            }
    
    async def _execute_intelligent_satellite_filter_memory(self, tle_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行智能衛星篩選 (v3.0記憶體傳遞模式)"""
        self.logger.info("🎯 執行 智能衛星篩選")
        
        try:
            processor_start_time = time.time()
            
            processor = IntelligentSatelliteFilterProcessor()
            # 使用記憶體傳遞模式，不儲存檔案
            filter_data = processor.process_intelligent_filtering(orbital_data=tle_data, save_output=False)
            
            processing_time = time.time() - processor_start_time
            
            # v3.0記憶體傳遞模式：不需要檔案路徑
            
            self.processor_status['intelligent_satellite_filter'] = {
                'completed': True,
                'output_file': None,  # 記憶體傳遞模式
                'processing_time': processing_time
            }
            
            self.logger.info(f"✅ 智能衛星篩選完成 - 處理時間: {processing_time:.2f}秒")
            
            return {
                'success': True,
                'processor': 'intelligent_satellite_filter', 
                'satellite_data': filter_data,  # 傳遞記憶體數據
                'processing_time': processing_time,
                'processor_description': '智能衛星篩選'
            }
            
        except Exception as e:
            self.logger.error(f"❌ 智能衛星篩選執行失敗: {e}")
            return {
                'success': False,
                'processor': 'intelligent_satellite_filter',
                'error': str(e)
            }
    
    async def _execute_signal_quality_analysis_hybrid(self, filter_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行信號品質分析與3GPP事件處理 (混合模式：記憶體輸入，檔案輸出)"""
        self.logger.info("📡 執行 信號品質分析與3GPP事件處理 (混合模式)")
        
        try:
            processor_start_time = time.time()
            
            processor = SignalQualityAnalysisProcessor()
            # 使用混合模式：傳入記憶體數據，並要求保存輸出檔案
            result = processor.process_signal_quality_analysis(filter_data=filter_data, save_output=True)
            
            processing_time = time.time() - processor_start_time
            
            # 信號分析的輸出檔案路徑 - 功能描述性命名
            signal_actual_output = Path(self.config.base_data_dir) / "signal_event_analysis_output.json"
            output_file = Path(self.config.base_data_dir) / self.config.signal_analysis_output_dir / "signal_event_analysis_output.json"
            
            # 如果檔案在data根目錄，移動到正確的輸出目錄
            if signal_actual_output.exists() and not output_file.exists():
                output_file.parent.mkdir(parents=True, exist_ok=True)
                signal_actual_output.rename(output_file)
            
            self.processor_status['signal_quality_analysis'] = {
                'completed': True,
                'output_file': str(output_file),
                'processing_time': processing_time
            }
            
            self.logger.info(f"✅ 信號品質分析 (混合模式) 完成 - 處理時間: {processing_time:.2f}秒")
            
            return {
                'success': True,
                'processor': 'signal_quality_analysis_hybrid',
                'output_file': str(output_file),
                'processing_time': processing_time,
                'processor_description': '信號品質分析與3GPP事件處理 (混合模式)'
            }
            
        except Exception as e:
            self.logger.error(f"❌ 信號品質分析 (混合模式) 執行失敗: {e}")
            return {
                'success': False,
                'processor': 'signal_quality_analysis_hybrid',
                'error': str(e)
            }
    
    async def _execute_stage3(self, stage2_output: str) -> Dict[str, Any]:
        """執行Stage3: 信號品質分析與3GPP事件處理"""
        self.logger.info("📡 執行 Stage3: 信號品質分析與3GPP事件處理")
        
        try:
            stage_start_time = time.time()
            
            processor = Stage3SignalProcessor()
            result = processor.process_stage3(stage2_output)
            
            processing_time = time.time() - stage_start_time
            
            output_file = Path(self.config.base_data_dir) / self.config.signal_analysis_output_dir / "signal_event_analysis_output.json"
            
            self.stage_status['stage3'] = {
                'completed': True,
                'output_file': str(output_file),
                'processing_time': processing_time
            }
            
            self.logger.info(f"✅ Stage3 完成 - 處理時間: {processing_time:.2f}秒")
            
            return {
                'success': True,
                'stage': 'stage3',
                'output_file': str(output_file),
                'processing_time': processing_time,
                'stage_description': '信號品質分析與3GPP事件處理'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Stage3 執行失敗: {e}")
            return {
                'success': False,
                'stage': 'stage3',
                'error': str(e)
            }
    
    async def _execute_timeseries_preprocessing(self, signal_analysis_output: str) -> Dict[str, Any]:
        """執行Stage4: 時間序列預處理"""
        self.logger.info("⏰ 執行 Stage4: 時間序列預處理")
        
        try:
            stage_start_time = time.time()
            
            processor = Stage4TimeseriesProcessor()
            result = processor.process_stage4(signal_analysis_output)
            
            processing_time = time.time() - stage_start_time
            
            output_file = Path(self.config.base_data_dir) / self.config.timeseries_preprocessing_output_dir / "enhanced_timeseries_output.json"
            
            self.stage_status['stage4'] = {
                'completed': True,
                'output_file': str(output_file),
                'processing_time': processing_time
            }
            
            self.logger.info(f"✅ Stage4 完成 - 處理時間: {processing_time:.2f}秒")
            
            return {
                'success': True,
                'stage': 'stage4',
                'output_file': str(output_file),
                'processing_time': processing_time,
                'stage_description': '時間序列預處理'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Stage4 執行失敗: {e}")
            return {
                'success': False,
                'stage': 'stage4',
                'error': str(e)
            }
    
    async def _execute_data_integration(self, timeseries_output: str) -> Dict[str, Any]:
        """執行Stage5: 數據整合與接口準備"""
        self.logger.info("🔗 執行 Stage5: 數據整合與接口準備")
        
        try:
            stage_start_time = time.time()
            
            # 配置Stage5
            stage5_config = Stage5Config()
            processor = Stage5IntegrationProcessor(stage5_config)
            
            result = await processor.process_enhanced_timeseries()
            
            processing_time = time.time() - stage_start_time
            
            output_file = Path(self.config.base_data_dir) / self.config.data_integration_output_dir / "data_integration_output.json"
            
            # 保存Stage5結果
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            self.stage_status['stage5'] = {
                'completed': True,
                'output_file': str(output_file),
                'processing_time': processing_time
            }
            
            self.logger.info(f"✅ Stage5 完成 - 處理時間: {processing_time:.2f}秒")
            
            return {
                'success': True,
                'stage': 'stage5',
                'output_file': str(output_file),
                'processing_time': processing_time,
                'stage_description': '數據整合與接口準備'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Stage5 執行失敗: {e}")
            return {
                'success': False,
                'stage': 'stage5',
                'error': str(e)
            }
    
    async def _execute_dynamic_pool_planning(self, integration_output: str) -> Dict[str, Any]:
        """執行Stage6: 動態衛星池規劃 (增強版，整合模擬退火優化)"""
        self.logger.info("🧠 執行 Stage6: 動態衛星池規劃 (增強版)")
        
        try:
            stage_start_time = time.time()
            
            # 創建增強版Stage6處理器
            processor = create_enhanced_stage6_processor()
            
            output_file = Path(self.config.base_data_dir) / self.config.dynamic_pool_planning_output_dir / "enhanced_dynamic_pools_output.json"
            
            # 執行Stage6處理
            result = processor.process(integration_output, str(output_file))
            
            processing_time = time.time() - stage_start_time
            
            self.stage_status['stage6'] = {
                'completed': True,
                'output_file': str(output_file),
                'processing_time': processing_time
            }
            
            self.logger.info(f"✅ Stage6 (增強版) 完成 - 處理時間: {processing_time:.2f}秒")
            self.logger.info("🎯 模擬退火優化演算法已成功整合")
            
            return {
                'success': True,
                'stage': 'stage6_enhanced',
                'output_file': str(output_file),
                'processing_time': processing_time,
                'stage_description': '動態衛星池規劃 (增強版 - 模擬退火優化)',
                'solution_details': result.get('solution', {}),
                'technology_enhancements': [
                    'shared_core_data_models',
                    'simulated_annealing_optimizer',
                    'auto_cleanup_manager',
                    'incremental_update_manager'
                ]
            }
            
        except Exception as e:
            self.logger.error(f"❌ Stage6 執行失敗: {e}")
            return {
                'success': False,
                'stage': 'stage6_enhanced',
                'error': str(e)
            }
    
    def _generate_pipeline_summary(self) -> Dict[str, Any]:
        """生成流程總結報告"""
        total_processing_time = sum(stage['processing_time'] for stage in self.stage_status.values())
        completed_stages = sum(1 for stage in self.stage_status.values() if stage['completed'])
        
        return {
            'pipeline_architecture': 'six_stage_enhanced_leo_core_system',
            'completed_stages': completed_stages,
            'total_stages': 6,
            'pipeline_success_rate': f"{(completed_stages / 6) * 100:.1f}%",
            'total_processing_time_seconds': round(total_processing_time, 2),
            'stage_breakdown': {
                stage: {
                    'completed': status['completed'],
                    'processing_time': status['processing_time'],
                    'output_file': status['output_file']
                }
                for stage, status in self.stage_status.items()
            },
            'technology_highlights': [
                '六階段完整流程架構',
                'shared_core統一數據模型',
                '模擬退火優化演算法',
                '智能清理管理系統',
                '增量更新管理機制'
            ],
            'performance_metrics': {
                'average_stage_time': round(total_processing_time / 6, 2),
                'fastest_stage': min(self.stage_status.items(), 
                                   key=lambda x: x[1]['processing_time'] if x[1]['completed'] else float('inf'))[0],
                'slowest_stage': max(self.stage_status.items(),
                                   key=lambda x: x[1]['processing_time'] if x[1]['completed'] else 0)[0]
            }
        }
    
    async def execute_single_stage(self, stage_name: str, input_file: Optional[str] = None) -> Dict[str, Any]:
        """執行單一階段 (用於測試和調試)"""
        self.logger.info(f"🔧 執行單一階段: {stage_name}")
        
        if stage_name == 'stage1':
            return await self._execute_stage1()
        elif stage_name == 'stage2':
            # 單階段模式下不支援Stage2，因為它需要Stage1的記憶體數據
            raise ValueError("Stage2 在單階段模式下不支援，需要Stage1的記憶體數據。請使用完整流程模式。")
        elif stage_name == 'stage3':
            if not input_file:
                raise ValueError("Stage3 需要提供 stage2 輸出檔案")
            return await self._execute_stage3(input_file)
        elif stage_name == 'stage4':
            if not input_file:
                raise ValueError("Stage4 需要提供 stage3 輸出檔案")
            return await self._execute_timeseries_preprocessing(input_file)
        elif stage_name == 'stage5':
            if not input_file:
                raise ValueError("Stage5 需要提供 stage4 輸出檔案")
            return await self._execute_data_integration(input_file)
        elif stage_name == 'stage6':
            if not input_file:
                raise ValueError("Stage6 需要提供 stage5 輸出檔案")
            return await self._execute_dynamic_pool_planning(input_file)
        else:
            raise ValueError(f"未知的階段名稱: {stage_name}")
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """獲取流程狀態"""
        return {
            'pipeline_running_time': time.time() - self.pipeline_start_time,
            'stage_status': self.stage_status,
            'completed_stages': [k for k, v in self.stage_status.items() if v['completed']],
            'pending_stages': [k for k, v in self.stage_status.items() if not v['completed']]
        }

# 便利函數
def create_leo_main_pipeline(base_data_dir: str = "/home/sat/ntn-stack/netstack/data") -> LEOMainPipelineController:
    """創建LEO主流程控制器實例"""
    config = PipelineConfig(base_data_dir=base_data_dir)
    return LEOMainPipelineController(config)

async def main():
    """主執行函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LEO核心系統主流程控制器")
    parser.add_argument("--mode", choices=['full', 'single'], default='full', 
                       help="執行模式: full=完整流程, single=單一階段")
    parser.add_argument("--stage", choices=['stage1', 'stage2', 'stage3', 'stage4', 'stage5', 'stage6'],
                       help="單一階段模式下指定要執行的階段")
    parser.add_argument("--input", help="單一階段模式下的輸入檔案")
    parser.add_argument("--data-dir", default="/home/sat/ntn-stack/netstack/data",
                       help="數據目錄路徑")
    
    args = parser.parse_args()
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 創建主流程控制器
    pipeline = create_leo_main_pipeline(args.data_dir)
    
    try:
        if args.mode == 'full':
            # 執行完整流程
            result = await pipeline.execute_complete_pipeline()
            print("\n🎯 完整流程執行結果:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
        elif args.mode == 'single':
            if not args.stage:
                print("❌ 單一階段模式需要指定 --stage 參數")
                sys.exit(1)
                
            # 執行單一階段
            result = await pipeline.execute_single_stage(args.stage, args.input)
            print(f"\n🎯 {args.stage} 執行結果:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        
        if result.get('success', False) or result.get('pipeline_success', False):
            print("\n✅ 執行成功完成！")
            sys.exit(0)
        else:
            print("\n❌ 執行失敗！")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 主流程執行異常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())