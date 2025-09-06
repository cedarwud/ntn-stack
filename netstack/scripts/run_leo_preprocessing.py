#!/usr/bin/env python3
"""
LEO衛星六階段數據預處理主執行腳本
================================
統一標準版本 - 整合所有修復後的處理邏輯

Author: NTN Stack Team
Version: 4.0.0
Date: 2025-09-04

處理流程：
1. TLE載入與SGP4軌道計算
2. 智能衛星可見性篩選
3. 信號品質分析與3GPP事件
4. 時間序列預處理
5. 數據整合
6. 動態衛星池規劃
"""

import sys
import os
import json
import time
import logging
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# 確保能找到模組
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/src')

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LEOPreprocessingPipeline:
    """LEO衛星數據預處理管線"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化處理管線
        
        Args:
            config: 可選配置參數
        """
        self.config = config or {}
        self.data_dir = Path(self.config.get('data_dir', '/app/data'))
        self.tle_dir = Path(self.config.get('tle_dir', '/app/tle_data'))
        self.sample_mode = self.config.get('sample_mode', False)
        self.results = {}
        
        # 確保數據目錄存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ LEO預處理管線初始化完成")
        logger.info(f"  數據目錄: {self.data_dir}")
        logger.info(f"  TLE目錄: {self.tle_dir}")
        logger.info(f"  處理模式: {'取樣' if self.sample_mode else '全量'}")
    
    def cleanup_previous_outputs(self) -> int:
        """清理舊輸出檔案"""
        logger.info("🗑️ 清理舊輸出檔案...")
        
        try:
            from stages.dynamic_pool_planner import EnhancedDynamicPoolPlanner
            temp_planner = EnhancedDynamicPoolPlanner({'cleanup_only': True})
            cleaned_count = temp_planner.cleanup_all_stage6_outputs()
            logger.info(f"✅ 清理完成: {cleaned_count} 項目已清理")
            return cleaned_count
        except Exception as e:
            logger.warning(f"⚠️ 清理警告: {e}")
            return 0
    
    def run_stage1_tle_loading(self) -> bool:
        """階段一：TLE載入與SGP4計算"""
        logger.info("\n" + "="*60)
        logger.info("📡 階段一：TLE載入與SGP4軌道計算")
        logger.info("-"*60)
        
        try:
            from stages.orbital_calculation_processor import Stage1TLEProcessor
            
            stage1 = Stage1TLEProcessor(
                tle_data_dir=str(self.tle_dir),
                output_dir=str(self.data_dir / 'tle_calculation_outputs'),
                sample_mode=self.sample_mode
            )
            
            self.results['stage1'] = stage1.process_tle_orbital_calculation()
            
            if not self.results['stage1']:
                logger.error("❌ 階段一失敗")
                return False
                
            total_sats = self.results['stage1']['metadata']['total_satellites']
            logger.info(f"✅ 階段一完成: {total_sats} 顆衛星載入")
            return True
            
        except Exception as e:
            logger.error(f"❌ 階段一錯誤: {e}")
            return False
    
    def run_stage2_filtering(self) -> bool:
        """階段二：智能衛星篩選"""
        logger.info("\n" + "="*60)
        logger.info("🎯 階段二：智能衛星篩選")
        logger.info("-"*60)
        
        try:
            from stages.satellite_visibility_filter_processor import SatelliteVisibilityFilterProcessor
            
            stage2 = SatelliteVisibilityFilterProcessor(
                input_dir=str(self.data_dir),
                output_dir=str(self.data_dir / 'intelligent_filtering_outputs'),
                sample_mode=self.sample_mode
            )
            
            self.results['stage2'] = stage2.process_intelligent_filtering(
                orbital_data=self.results['stage1'],
                save_output=True
            )
            
            if not self.results['stage2']:
                logger.error("❌ 階段二失敗")
                return False
            
            # 計算篩選數量
            filtered_count = self._count_filtered_satellites(self.results['stage2'])
            logger.info(f"✅ 階段二完成: {filtered_count} 顆衛星通過篩選")
            return True
            
        except Exception as e:
            logger.error(f"❌ 階段二錯誤: {e}")
            return False
    
    def run_stage3_signal_analysis(self) -> bool:
        """階段三：信號品質分析"""
        logger.info("\n" + "="*60)
        logger.info("📡 階段三：信號品質分析與3GPP事件")
        logger.info("-"*60)
        
        try:
            from stages.signal_analysis_processor import SignalQualityAnalysisProcessor
            
            stage3 = SignalQualityAnalysisProcessor(
                input_dir=str(self.data_dir),
                output_dir=str(self.data_dir / 'signal_analysis_outputs')
            )
            
            self.results['stage3'] = stage3.process_signal_analysis(
                filtering_data=self.results['stage2'],
                save_output=True
            )
            
            if not self.results['stage3']:
                logger.error("❌ 階段三失敗")
                return False
            
            event_count = self._count_3gpp_events(self.results['stage3'])
            logger.info(f"✅ 階段三完成: {event_count} 個3GPP事件")
            return True
            
        except Exception as e:
            logger.error(f"❌ 階段三錯誤: {e}")
            return False
    
    def run_stage4_timeseries(self) -> bool:
        """階段四：時間序列預處理"""
        logger.info("\n" + "="*60)
        logger.info("⏰ 階段四：時間序列預處理")
        logger.info("-"*60)
        
        try:
            from stages.timeseries_optimization_processor import TimeseriesPreprocessingProcessor
            
            stage4 = TimeseriesPreprocessingProcessor(
                input_dir=str(self.data_dir),
                output_dir=str(self.data_dir / 'timeseries_preprocessing_outputs')
            )
            
            signal_file = self.data_dir / 'signal_analysis_outputs' / 'signal_event_analysis_output.json'
            self.results['stage4'] = stage4.process_timeseries_preprocessing(
                signal_file=str(signal_file),
                save_output=True
            )
            
            if not self.results['stage4']:
                logger.error("❌ 階段四失敗")
                return False
            
            ts_count = self._count_timeseries_satellites(self.results['stage4'])
            logger.info(f"✅ 階段四完成: {ts_count} 顆衛星時間序列")
            return True
            
        except Exception as e:
            logger.error(f"❌ 階段四錯誤: {e}")
            return False
    
    def run_stage5_integration(self) -> bool:
        """階段五：數據整合"""
        logger.info("\n" + "="*60)
        logger.info("🔄 階段五：數據整合")
        logger.info("-"*60)
        
        try:
            from stages.data_integration_processor import Stage5IntegrationProcessor, Stage5Config
            
            stage5_config = Stage5Config(
                input_enhanced_timeseries_dir=str(self.data_dir),
                output_data_integration_dir=str(self.data_dir / 'data_integration_outputs'),
                elevation_thresholds=[5, 10, 15]
            )
            
            stage5 = Stage5IntegrationProcessor(stage5_config)
            
            # 使用asyncio執行async方法
            self.results['stage5'] = asyncio.run(stage5.process_enhanced_timeseries())
            
            if not self.results['stage5']:
                logger.error("❌ 階段五失敗")
                return False
            
            integrated_count = self.results['stage5'].get('metadata', {}).get('total_satellites', 0)
            logger.info(f"✅ 階段五完成: {integrated_count} 顆衛星整合")
            return True
            
        except Exception as e:
            logger.error(f"❌ 階段五錯誤: {e}")
            return False
    
    def run_stage6_dynamic_pool(self) -> bool:
        """階段六：動態池規劃"""
        logger.info("\n" + "="*60)
        logger.info("🎯 階段六：動態池規劃")
        logger.info("-"*60)
        
        try:
            from stages.dynamic_pool_planner import EnhancedDynamicPoolPlanner
            
            stage6_config = {
                'input_dir': str(self.data_dir),
                'output_dir': str(self.data_dir / 'dynamic_pool_planning_outputs')
            }
            
            stage6 = EnhancedDynamicPoolPlanner(stage6_config)
            
            output_file = self.data_dir / 'dynamic_pool_planning_outputs' / 'enhanced_dynamic_pools_output.json'
            self.results['stage6'] = stage6.process(
                input_data=self.results['stage5'],
                output_file=str(output_file)
            )
            
            if not self.results['stage6']:
                logger.error("❌ 階段六失敗")
                return False
            
            pool_stats = self._extract_pool_stats(self.results['stage6'])
            logger.info(f"✅ 階段六完成: 總計 {pool_stats['total']} 顆衛星")
            logger.info(f"   - Starlink: {pool_stats['starlink']} 顆")
            logger.info(f"   - OneWeb: {pool_stats['oneweb']} 顆")
            return True
            
        except Exception as e:
            logger.error(f"❌ 階段六錯誤: {e}")
            return False
    
    def _count_filtered_satellites(self, data: Dict) -> int:
        """計算篩選後衛星數量"""
        count = 0
        if 'constellations' in data:
            for const_data in data['constellations'].values():
                count += const_data.get('satellite_count', 0)
        elif 'metadata' in data:
            count = data['metadata'].get('total_satellites', 0)
        return count
    
    def _count_3gpp_events(self, data: Dict) -> int:
        """計算3GPP事件數量"""
        if 'gpp_events' in data:
            return len(data['gpp_events'].get('all_events', []))
        elif 'metadata' in data:
            return data['metadata'].get('total_3gpp_events', 0)
        return 0
    
    def _count_timeseries_satellites(self, data: Dict) -> int:
        """計算時間序列衛星數量"""
        if 'timeseries_data' in data:
            return len(data['timeseries_data'].get('satellites', []))
        elif 'metadata' in data:
            return data['metadata'].get('total_satellites', 0)
        return 0
    
    def _extract_pool_stats(self, data: Dict) -> Dict[str, int]:
        """提取衛星池統計"""
        pool_data = data.get('dynamic_satellite_pool', {})
        
        # 處理可能是整數或列表的情況
        def extract_count(value):
            return len(value) if isinstance(value, list) else value
        
        return {
            'total': pool_data.get('total_selected', 0),
            'starlink': extract_count(pool_data.get('starlink_satellites', 0)),
            'oneweb': extract_count(pool_data.get('oneweb_satellites', 0))
        }
    
    def save_final_report(self, elapsed_time: float):
        """保存最終報告"""
        report = {
            'execution_time': datetime.now(timezone.utc).isoformat(),
            'processing_time_seconds': elapsed_time,
            'processing_time_minutes': elapsed_time / 60,
            'stages_completed': len(self.results),
            'sample_mode': self.sample_mode,
            'pipeline_summary': {},
            'final_satellite_pool': {},
            'success': True
        }
        
        # 添加每階段統計
        if 'stage1' in self.results:
            report['pipeline_summary']['stage1_loaded'] = \
                self.results['stage1']['metadata']['total_satellites']
        if 'stage2' in self.results:
            report['pipeline_summary']['stage2_filtered'] = \
                self._count_filtered_satellites(self.results['stage2'])
        if 'stage3' in self.results:
            report['pipeline_summary']['stage3_events'] = \
                self._count_3gpp_events(self.results['stage3'])
        if 'stage4' in self.results:
            report['pipeline_summary']['stage4_timeseries'] = \
                self._count_timeseries_satellites(self.results['stage4'])
        if 'stage5' in self.results:
            report['pipeline_summary']['stage5_integrated'] = \
                self.results['stage5'].get('metadata', {}).get('total_satellites', 0)
        if 'stage6' in self.results:
            pool_stats = self._extract_pool_stats(self.results['stage6'])
            report['pipeline_summary']['stage6_selected'] = pool_stats['total']
            report['final_satellite_pool'] = pool_stats
        
        # 保存報告
        report_path = self.data_dir / 'leo_optimization_final_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✅ 最終報告已保存: {report_path}")
    
    def run_pipeline(self) -> bool:
        """執行完整處理管線"""
        print("\n" + "="*80)
        print("🚀 LEO衛星六階段數據預處理系統")
        print("="*80)
        print(f"開始時間: {datetime.now(timezone.utc).isoformat()}")
        print(f"處理模式: {'取樣模式' if self.sample_mode else '全量模式'}")
        print("="*80)
        
        start_time = time.time()
        
        try:
            # 清理舊輸出
            self.cleanup_previous_outputs()
            
            # 依序執行六階段
            stages = [
                ("階段一", self.run_stage1_tle_loading),
                ("階段二", self.run_stage2_filtering),
                ("階段三", self.run_stage3_signal_analysis),
                ("階段四", self.run_stage4_timeseries),
                ("階段五", self.run_stage5_integration),
                ("階段六", self.run_stage6_dynamic_pool)
            ]
            
            for stage_name, stage_func in stages:
                if not stage_func():
                    logger.error(f"❌ {stage_name}執行失敗，處理中止")
                    return False
            
            # 處理完成
            elapsed_time = time.time() - start_time
            
            print("\n" + "="*80)
            print("📊 LEO衛星預處理完成總結")
            print("="*80)
            print(f"✅ 所有階段成功完成！")
            print(f"⏱️ 總耗時: {elapsed_time:.2f} 秒 ({elapsed_time/60:.2f} 分鐘)")
            print("="*80)
            
            # 保存最終報告
            self.save_final_report(elapsed_time)
            
            return True
            
        except Exception as e:
            logger.error(f"\n❌ 管線執行錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """主程序入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='LEO衛星六階段數據預處理系統',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 全量處理
  python run_leo_preprocessing.py
  
  # 取樣模式處理
  python run_leo_preprocessing.py --sample-mode
  
  # 指定數據目錄
  python run_leo_preprocessing.py --data-dir /custom/data
  
  # 跳過部分階段（開發測試用）
  python run_leo_preprocessing.py --skip-stages 1 2
        """
    )
    
    parser.add_argument(
        '--data-dir',
        default='/app/data',
        help='數據目錄路徑 (預設: /app/data)'
    )
    
    parser.add_argument(
        '--tle-dir',
        default='/app/tle_data',
        help='TLE數據目錄路徑 (預設: /app/tle_data)'
    )
    
    parser.add_argument(
        '--sample-mode',
        action='store_true',
        help='使用取樣模式（處理少量衛星用於測試）'
    )
    
    parser.add_argument(
        '--skip-stages',
        nargs='+',
        type=int,
        choices=[1, 2, 3, 4, 5, 6],
        help='跳過指定階段（僅供開發測試）'
    )
    
    args = parser.parse_args()
    
    # 配置參數
    config = {
        'data_dir': args.data_dir,
        'tle_dir': args.tle_dir,
        'sample_mode': args.sample_mode
    }
    
    # 創建管線並執行
    pipeline = LEOPreprocessingPipeline(config)
    
    # 如果指定跳過階段，給出警告
    if args.skip_stages:
        logger.warning(f"⚠️ 注意：將跳過階段 {args.skip_stages}")
        logger.warning("此功能僅供開發測試，生產環境請執行完整流程")
    
    # 執行管線
    success = pipeline.run_pipeline()
    
    # 返回狀態碼
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()