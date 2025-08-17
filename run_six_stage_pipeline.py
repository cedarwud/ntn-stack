#!/usr/bin/env python3
"""
六階段LEO衛星系統完整管線執行器
恢復原始六階段架構，實現8,735→563衛星的93.6%篩選效率

架構流程：
Stage 1: TLE載入與SGP4軌道計算 → 8,735顆衛星軌道數據
Stage 2: 智能篩選系統 → 93.6%篩選效率 → ~563顆候選衛星
Stage 3: 信號分析與3GPP事件檢測 → A4/A5/D2切換事件
Stage 4: 時間序列數據生成 → 前端立體圖動畫數據
Stage 5: 數據整合 → PostgreSQL+Volume混合存儲
Stage 6: 動態池規劃 → 強化學習訓練數據
"""

import os
import sys
import json
import logging
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

# 設置系統路徑
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/netstack')
sys.path.insert(0, '/app/netstack/src')

# 引用六階段處理器
from src.stages.stage1_tle_processor import Stage1TLEProcessor
from src.stages.stage2_filter_processor import Stage2FilterProcessor
from src.stages.stage3_signal_processor import Stage3SignalProcessor
from src.stages.stage4_timeseries_processor import Stage4TimeseriesProcessor
from src.stages.stage5_integration_processor import Stage5IntegrationProcessor
from src.stages.stage6_dynamic_pool_planner import Stage6DynamicPoolPlanner

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SixStagePipelineOrchestrator:
    """六階段LEO衛星系統完整管線協調器"""
    
    def __init__(self, data_dir: str = "/app/data", observer_lat: float = 24.9441667, 
                 observer_lon: float = 121.3713889, sample_mode: bool = False):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.observer_lat = observer_lat
        self.observer_lon = observer_lon
        self.sample_mode = sample_mode
        
        # 執行結果統計
        self.execution_stats = {
            "start_time": datetime.now(timezone.utc),
            "stages_completed": [],
            "stages_failed": [],
            "total_satellites": 0,
            "filtered_satellites": 0,
            "filtering_efficiency": 0.0
        }
        
        logger.info("🚀 六階段LEO衛星系統初始化完成")
        logger.info(f"📍 觀測點座標: ({observer_lat}, {observer_lon})")
        logger.info(f"📂 數據目錄: {data_dir}")
        logger.info(f"🎛️ 運行模式: {'取樣模式' if sample_mode else '全量模式'}")
    
    def execute_stage1_tle_loading(self) -> bool:
        """執行階段一：TLE數據載入與SGP4軌道計算"""
        try:
            logger.info("📡 Stage 1: 開始TLE數據載入與軌道計算...")
            
            processor = Stage1TLEProcessor(
                tle_data_dir="/app/tle_data",
                output_dir=str(self.data_dir),
                sample_mode=self.sample_mode
            )
            
            result = processor.process()
            
            if result and 'output_file' in result:
                self.execution_stats["total_satellites"] = result.get("total_satellites", 0)
                self.execution_stats["stages_completed"].append("stage1")
                logger.info(f"✅ Stage 1 完成: 處理 {self.execution_stats['total_satellites']} 顆衛星")
                return True
            else:
                logger.error("❌ Stage 1 失敗：處理器返回空結果")
                return False
                
        except Exception as e:
            logger.error(f"❌ Stage 1 異常: {e}")
            logger.error(traceback.format_exc())
            self.execution_stats["stages_failed"].append("stage1")
            return False
    
    def execute_stage2_intelligent_filtering(self) -> bool:
        """執行階段二：智能衛星篩選（93.6%篩選效率）"""
        try:
            logger.info("🔍 Stage 2: 開始智能衛星篩選...")
            
            processor = Stage2FilterProcessor(
                observer_lat=self.observer_lat,
                observer_lon=self.observer_lon,
                input_dir=str(self.data_dir),
                output_dir=str(self.data_dir)
            )
            
            result = processor.process()
            
            if result and 'output_file' in result:
                self.execution_stats["filtered_satellites"] = result.get("filtered_count", 0)
                if self.execution_stats["total_satellites"] > 0:
                    self.execution_stats["filtering_efficiency"] = (
                        1.0 - self.execution_stats["filtered_satellites"] / self.execution_stats["total_satellites"]
                    ) * 100
                
                self.execution_stats["stages_completed"].append("stage2")
                logger.info(f"✅ Stage 2 完成: 篩選出 {self.execution_stats['filtered_satellites']} 顆衛星")
                logger.info(f"📊 篩選效率: {self.execution_stats['filtering_efficiency']:.1f}%")
                return True
            else:
                logger.error("❌ Stage 2 失敗：篩選處理器返回空結果")
                return False
                
        except Exception as e:
            logger.error(f"❌ Stage 2 異常: {e}")
            logger.error(traceback.format_exc())
            self.execution_stats["stages_failed"].append("stage2")
            return False
    
    def execute_stage3_signal_analysis(self) -> bool:
        """執行階段三：信號分析與3GPP事件檢測"""
        try:
            logger.info("📶 Stage 3: 開始信號分析與事件檢測...")
            
            processor = Stage3SignalProcessor(
                input_dir=str(self.data_dir),
                output_dir=str(self.data_dir)
            )
            
            result = processor.process()
            
            if result and 'output_file' in result:
                self.execution_stats["stages_completed"].append("stage3")
                logger.info("✅ Stage 3 完成: 3GPP A4/A5/D2事件檢測完成")
                return True
            else:
                logger.error("❌ Stage 3 失敗：信號分析處理器返回空結果")
                return False
                
        except Exception as e:
            logger.error(f"❌ Stage 3 異常: {e}")
            logger.error(traceback.format_exc())
            self.execution_stats["stages_failed"].append("stage3")
            return False
    
    def execute_stage4_timeseries_generation(self) -> bool:
        """執行階段四：時間序列數據生成（前端立體圖）"""
        try:
            logger.info("📈 Stage 4: 開始時間序列數據生成...")
            
            processor = Stage4TimeseriesProcessor(
                input_dir=str(self.data_dir),
                output_dir=str(self.data_dir)
            )
            
            result = processor.process()
            
            if result and 'output_file' in result:
                self.execution_stats["stages_completed"].append("stage4")
                logger.info("✅ Stage 4 完成: 前端動畫時間序列數據生成完成")
                return True
            else:
                logger.error("❌ Stage 4 失敗：時間序列處理器返回空結果")
                return False
                
        except Exception as e:
            logger.error(f"❌ Stage 4 異常: {e}")
            logger.error(traceback.format_exc())
            self.execution_stats["stages_failed"].append("stage4")
            return False
    
    def execute_stage5_data_integration(self) -> bool:
        """執行階段五：數據整合（PostgreSQL+Volume）"""
        try:
            logger.info("🗄️ Stage 5: 開始數據整合...")
            
            processor = Stage5IntegrationProcessor(
                input_dir=str(self.data_dir),
                output_dir=str(self.data_dir)
            )
            
            result = processor.process()
            
            if result and 'output_file' in result:
                self.execution_stats["stages_completed"].append("stage5")
                logger.info("✅ Stage 5 完成: PostgreSQL+Volume數據整合完成")
                return True
            else:
                logger.error("❌ Stage 5 失敗：數據整合處理器返回空結果")
                return False
                
        except Exception as e:
            logger.error(f"❌ Stage 5 異常: {e}")
            logger.error(traceback.format_exc())
            self.execution_stats["stages_failed"].append("stage5")
            return False
    
    def execute_stage6_dynamic_pool_planning(self) -> bool:
        """執行階段六：動態池規劃（強化學習數據）"""
        try:
            logger.info("🧠 Stage 6: 開始動態池規劃...")
            
            processor = Stage6DynamicPoolPlanner(
                input_dir=str(self.data_dir),
                output_dir=str(self.data_dir)
            )
            
            result = processor.process()
            
            if result and 'output_file' in result:
                self.execution_stats["stages_completed"].append("stage6")
                logger.info("✅ Stage 6 完成: 動態池規劃與RL數據準備完成")
                return True
            else:
                logger.error("❌ Stage 6 失敗：動態池規劃處理器返回空結果")
                return False
                
        except Exception as e:
            logger.error(f"❌ Stage 6 異常: {e}")
            logger.error(traceback.format_exc())
            self.execution_stats["stages_failed"].append("stage6")
            return False
    
    def execute_complete_pipeline(self) -> Dict[str, Any]:
        """執行完整的六階段管線"""
        logger.info("🚀 開始執行六階段LEO衛星系統完整管線")
        logger.info("=" * 60)
        
        # 執行所有階段
        stages = [
            ("Stage 1: TLE載入", self.execute_stage1_tle_loading),
            ("Stage 2: 智能篩選", self.execute_stage2_intelligent_filtering),
            ("Stage 3: 信號分析", self.execute_stage3_signal_analysis),
            ("Stage 4: 時間序列", self.execute_stage4_timeseries_generation),
            ("Stage 5: 數據整合", self.execute_stage5_data_integration),
            ("Stage 6: 動態池規劃", self.execute_stage6_dynamic_pool_planning)
        ]
        
        for stage_name, stage_func in stages:
            logger.info(f"🔄 執行 {stage_name}...")
            success = stage_func()
            
            if not success:
                logger.error(f"❌ {stage_name} 失敗，停止管線執行")
                break
            
            logger.info(f"✅ {stage_name} 成功完成")
            logger.info("-" * 40)
        
        # 生成執行報告
        self.execution_stats["end_time"] = datetime.now(timezone.utc)
        self.execution_stats["total_duration"] = (
            self.execution_stats["end_time"] - self.execution_stats["start_time"]
        ).total_seconds()
        
        success = len(self.execution_stats["stages_failed"]) == 0
        
        logger.info("=" * 60)
        logger.info("📊 六階段管線執行報告")
        logger.info(f"🎯 執行狀態: {'✅ 完全成功' if success else '❌ 部分失敗'}")
        logger.info(f"⏱️ 總執行時間: {self.execution_stats['total_duration']:.1f} 秒")
        logger.info(f"📡 處理衛星總數: {self.execution_stats['total_satellites']}")
        logger.info(f"🔍 篩選後衛星數: {self.execution_stats['filtered_satellites']}")
        logger.info(f"📈 篩選效率: {self.execution_stats['filtering_efficiency']:.1f}%")
        logger.info(f"✅ 成功階段: {', '.join(self.execution_stats['stages_completed'])}")
        
        if self.execution_stats["stages_failed"]:
            logger.info(f"❌ 失敗階段: {', '.join(self.execution_stats['stages_failed'])}")
        
        # 保存執行報告
        report_file = self.data_dir / "six_stage_execution_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            # 轉換datetime對象為字符串
            stats_copy = self.execution_stats.copy()
            stats_copy["start_time"] = stats_copy["start_time"].isoformat()
            stats_copy["end_time"] = stats_copy["end_time"].isoformat()
            json.dump(stats_copy, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 執行報告已保存: {report_file}")
        
        return {
            "success": success,
            "stats": self.execution_stats,
            "report_file": str(report_file)
        }

def main():
    """主執行函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="六階段LEO衛星系統完整管線執行器")
    parser.add_argument("--data-dir", default="/app/data", help="數據目錄路徑")
    parser.add_argument("--observer-lat", type=float, default=24.9441667, help="觀測點緯度")
    parser.add_argument("--observer-lon", type=float, default=121.3713889, help="觀測點經度")
    parser.add_argument("--sample-mode", action="store_true", help="啟用取樣模式")
    
    args = parser.parse_args()
    
    try:
        orchestrator = SixStagePipelineOrchestrator(
            data_dir=args.data_dir,
            observer_lat=args.observer_lat,
            observer_lon=args.observer_lon,
            sample_mode=args.sample_mode
        )
        
        result = orchestrator.execute_complete_pipeline()
        
        if result["success"]:
            logger.info("🎉 六階段管線執行完全成功！")
            sys.exit(0)
        else:
            logger.error("💥 六階段管線執行失敗！")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"💥 管線執行器異常: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()