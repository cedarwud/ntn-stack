#!/usr/bin/env python3
"""
階段一到階段二整合處理器

執行完整的階段一 TLE 軌道計算，並將數據直接傳遞給階段二進行智能篩選
完全遵循 v3.0 記憶體傳遞模式，避免大檔案產生
"""

import os
import sys
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

logger = logging.getLogger(__name__)

class Stage1ToStage2IntegratedProcessor:
    """階段一到階段二整合處理器"""
    
    def __init__(self):
        """初始化整合處理器"""
        logger.info("🚀 階段一到階段二整合處理器初始化")
        
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
        
        logger.info("✅ 整合處理器初始化完成")
        logger.info("  📊 階段一：TLE數據載入與SGP4軌道計算 (全量模式)")
        logger.info("  🎯 階段二：智能衛星篩選處理 (統一管理器)")
        
    def execute_integrated_processing(self, save_stage2_output: bool = True) -> Dict[str, Any]:
        """執行整合的階段一到階段二處理"""
        logger.info("=" * 80)
        logger.info("🚀 開始執行階段一到階段二整合處理")
        logger.info("=" * 80)
        
        # 階段一：TLE數據載入與SGP4軌道計算
        logger.info("📊 階段一：執行TLE數據載入與SGP4軌道計算...")
        stage1_start_time = datetime.now()
        
        try:
            stage1_data = self.stage1_processor.process_tle_orbital_calculation()
            stage1_end_time = datetime.now()
            stage1_duration = (stage1_end_time - stage1_start_time).total_seconds()
            
            # 驗證階段一數據
            total_satellites = stage1_data['metadata']['total_satellites']
            constellations = len(stage1_data['constellations'])
            
            logger.info("✅ 階段一處理完成")
            logger.info(f"  ⏱️  處理時間: {stage1_duration:.1f} 秒")
            logger.info(f"  📊 處理衛星數: {total_satellites}")
            logger.info(f"  🌐 星座數量: {constellations}")
            logger.info("  💾 使用記憶體傳遞模式 (無檔案產生)")
            
        except Exception as e:
            logger.error(f"❌ 階段一處理失敗: {e}")
            raise
        
        # 階段二：智能衛星篩選
        logger.info("🎯 階段二：執行智能衛星篩選...")
        stage2_start_time = datetime.now()
        
        try:
            # 直接使用階段一的記憶體數據
            stage2_data = self.stage2_processor.process_intelligent_filtering(
                orbital_data=stage1_data,
                save_output=save_stage2_output
            )
            stage2_end_time = datetime.now()
            stage2_duration = (stage2_end_time - stage2_start_time).total_seconds()
            
            # 驗證階段二數據
            filtering_results = stage2_data['metadata'].get('unified_filtering_results', {})
            total_processed = filtering_results.get('total_processed', 0)
            total_selected = filtering_results.get('total_selected', 0)
            starlink_selected = filtering_results.get('starlink_selected', 0)
            oneweb_selected = filtering_results.get('oneweb_selected', 0)
            retention_rate = filtering_results.get('overall_retention_rate', '0%')
            
            logger.info("✅ 階段二處理完成")
            logger.info(f"  ⏱️  處理時間: {stage2_duration:.1f} 秒")
            logger.info(f"  📊 原始數量: {total_processed}")
            logger.info(f"  🎯 篩選結果: {total_selected} ({retention_rate})")
            logger.info(f"    - Starlink: {starlink_selected}")
            logger.info(f"    - OneWeb: {oneweb_selected}")
            
        except Exception as e:
            logger.error(f"❌ 階段二處理失敗: {e}")
            raise
        
        # 總結處理結果
        total_duration = stage1_duration + stage2_duration
        logger.info("=" * 80)
        logger.info("🎉 階段一到階段二整合處理完成")
        logger.info("=" * 80)
        logger.info(f"⏱️  總處理時間: {total_duration:.1f} 秒")
        logger.info(f"    - 階段一: {stage1_duration:.1f} 秒")
        logger.info(f"    - 階段二: {stage2_duration:.1f} 秒")
        logger.info(f"📊 數據流向: {total_satellites} 顆衛星 → {total_selected} 顆精選衛星")
        logger.info(f"🎯 篩選效率: {retention_rate} 保留率")
        logger.info("💾 使用 v3.0 記憶體傳遞模式，避免大檔案產生")
        
        # 返回整合結果
        integrated_result = {
            'stage1_data': stage1_data,
            'stage2_data': stage2_data,
            'integration_metadata': {
                'total_processing_time_seconds': total_duration,
                'stage1_duration_seconds': stage1_duration,
                'stage2_duration_seconds': stage2_duration,
                'processing_timestamp': datetime.now(timezone.utc).isoformat(),
                'memory_transfer_mode': True,
                'files_generated': save_stage2_output,
                'integration_version': '1.0.0'
            }
        }
        
        return integrated_result

def main():
    """主函數"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        processor = Stage1ToStage2IntegratedProcessor()
        result = processor.execute_integrated_processing(save_stage2_output=True)
        
        logger.info("🎊 整合處理成功完成！")
        return True
        
    except Exception as e:
        logger.error(f"💥 整合處理失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)