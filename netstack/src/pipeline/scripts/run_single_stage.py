#!/usr/bin/env python3
"""
單階段除錯工具

這個工具允許開發者單獨執行任何階段，用於除錯和測試目的。
是六階段重構後最重要的除錯功能。

使用範例:
    python -m pipeline.scripts.run_single_stage --stage=5
    python -m pipeline.scripts.run_single_stage --stage=5 --input=test_data.json --debug=DEBUG
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# 添加項目根目錄到Python路徑
current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))

from pipeline.shared.pipeline_coordinator import PipelineCoordinator

class SingleStageDebugger:
    """單階段除錯工具"""
    
    def __init__(self, stage_number: int, debug_level: str = 'INFO'):
        self.stage_number = stage_number
        self.setup_logging(debug_level)
        self.coordinator = PipelineCoordinator()
    
    def setup_logging(self, debug_level: str):
        """設置日誌配置"""
        level = getattr(logging, debug_level.upper(), logging.INFO)
        
        # 配置根日誌記錄器
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        self.logger = logging.getLogger('SingleStageDebugger')
        self.logger.info(f"除錯工具初始化完成，日誌等級: {debug_level}")
    
    def load_previous_stage_output(self) -> Optional[Dict[str, Any]]:
        """載入前一階段的輸出數據"""
        if self.stage_number == 1:
            self.logger.info("Stage 1 無前置依賴，將使用空輸入")
            return None
        
        prev_stage = self.stage_number - 1
        prev_output_dir = Path(f"/app/data/stage{prev_stage}_outputs")
        
        # 尋找前一階段的輸出文件
        possible_files = [
            f"stage{prev_stage}_output.json",
            f"{self.get_stage_name(prev_stage)}_output.json",
            "output.json"
        ]
        
        for filename in possible_files:
            output_file = prev_output_dir / filename
            if output_file.exists():
                self.logger.info(f"找到前一階段輸出文件: {output_file}")
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.logger.info(f"成功載入前一階段數據，記錄數: {data.get('metadata', {}).get('total_records', 'unknown')}")
                    return data
                except Exception as e:
                    self.logger.error(f"載入前一階段輸出失敗: {e}")
                    continue
        
        self.logger.warning(f"未找到 Stage {prev_stage} 的輸出文件，將使用空輸入")
        return None
    
    def get_stage_name(self, stage_number: int) -> str:
        """獲取階段名稱"""
        stage_names = {
            1: "orbital_calculation",
            2: "visibility_filter", 
            3: "timeseries_preprocessing",
            4: "signal_analysis",
            5: "data_integration",
            6: "dynamic_planning"
        }
        return stage_names.get(stage_number, f"stage{stage_number}")
    
    def execute_stage_only(self, input_file: str = None, output_dir: str = None) -> Dict[str, Any]:
        """只執行指定階段"""
        print(f"🔍 開始除錯 Stage {self.stage_number}")
        print(f"⏰ 時間: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        # 載入輸入數據
        if input_file:
            self.logger.info(f"使用指定的輸入文件: {input_file}")
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    input_data = json.load(f)
                print(f"📥 已載入輸入數據: {input_file}")
                
                # 顯示輸入數據統計
                if isinstance(input_data, dict) and 'metadata' in input_data:
                    metadata = input_data['metadata']
                    print(f"   - 數據來源: Stage {metadata.get('stage_number', 'unknown')}")
                    print(f"   - 記錄數量: {metadata.get('total_records', 'unknown')}")
                    print(f"   - 處理時間: {metadata.get('processing_timestamp', 'unknown')}")
                
            except Exception as e:
                self.logger.error(f"載入輸入文件失敗: {e}")
                print(f"❌ 載入輸入文件失敗: {e}")
                return None
        else:
            # 從前一階段載入標準輸出
            self.logger.info("嘗試從前一階段載入輸出數據")
            input_data = self.load_previous_stage_output()
            
            if input_data:
                print(f"📥 已從 Stage {self.stage_number-1} 載入輸入數據")
            else:
                print(f"⚠️  未找到前一階段輸出，將使用空輸入")
        
        # 執行單階段
        try:
            print(f"🚀 開始執行 Stage {self.stage_number}...")
            
            # 檢查階段是否已實施
            if self.coordinator.stages_registry[self.stage_number] is None:
                error_msg = f"Stage {self.stage_number} 處理器尚未實施"
                print(f"❌ {error_msg}")
                print(f"💡 建議: 請先實施 Stage{self.stage_number}Processor 類")
                print(f"📁 位置: /netstack/src/pipeline/stages/stage{self.stage_number}_{self.get_stage_name(self.stage_number)}/")
                return None
            
            result = self.coordinator.execute_single_stage(
                self.stage_number, 
                input_data,
                debug_mode=True
            )
            
            # 顯示執行結果統計
            print(f"✅ Stage {self.stage_number} 除錯執行完成")
            
            if isinstance(result, dict) and 'metadata' in result:
                metadata = result['metadata']
                print(f"📊 執行統計:")
                print(f"   - 處理時間: {metadata.get('processing_duration', 'unknown')} 秒")
                print(f"   - 輸出記錄: {metadata.get('total_records', 'unknown')}")
                print(f"   - 輸出文件: {metadata.get('output_file', 'unknown')}")
            
            # 保存結果  
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                output_file = output_path / f"stage{self.stage_number}_debug_output.json"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                print(f"💾 結果已保存: {output_file}")
            
            return result
            
        except Exception as e:
            print(f"❌ Stage {self.stage_number} 執行失敗: {e}")
            self.print_debug_info(e)
            raise
    
    def print_debug_info(self, exception: Exception):
        """輸出詳細的除錯資訊"""
        import traceback
        
        print(f"\n🔍 詳細除錯資訊:")
        print(f"   階段: Stage {self.stage_number}")
        print(f"   錯誤類型: {type(exception).__name__}")
        print(f"   錯誤訊息: {str(exception)}")
        
        # 輸出堆疊追蹤
        if self.logger.isEnabledFor(logging.DEBUG):
            print(f"\n📋 完整堆疊追蹤:")
            traceback.print_exc()
        
        # 輸出可能的解決建議
        print(f"\n💡 除錯建議:")
        if "尚未實施" in str(exception):
            print(f"   1. 實施 Stage{self.stage_number}Processor 類")
            print(f"   2. 在 pipeline_coordinator.py 中註冊處理器")
            print(f"   3. 確保所有依賴項都已安裝")
        else:
            print(f"   1. 檢查輸入數據格式是否正確")
            print(f"   2. 驗證前一階段的輸出是否存在")
            print(f"   3. 查看日誌了解更多詳細資訊")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='單階段除錯工具 - 六階段重構的核心除錯功能',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  %(prog)s --stage=5                                    # 執行Stage 5，自動載入前一階段輸出
  %(prog)s --stage=5 --debug=DEBUG                     # 啟用詳細除錯日誌
  %(prog)s --stage=5 --input=test_data.json            # 使用自定義輸入數據
  %(prog)s --stage=5 --output-dir=/tmp/debug           # 指定輸出目錄
        """
    )
    
    parser.add_argument('--stage', type=int, required=True, 
                       choices=range(1, 7), metavar='N',
                       help='階段編號 (1-6)')
    parser.add_argument('--input', 
                       help='輸入數據文件路徑（JSON格式）')
    parser.add_argument('--output-dir', 
                       help='輸出目錄（保存除錯結果）')
    parser.add_argument('--debug', default='INFO', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='除錯等級 (預設: INFO)')
    
    args = parser.parse_args()
    
    try:
        # 創建除錯器並執行
        debugger = SingleStageDebugger(args.stage, args.debug)
        result = debugger.execute_stage_only(args.input, args.output_dir)
        
        if result is not None:
            print(f"\n🎉 Stage {args.stage} 除錯執行成功完成！")
            sys.exit(0)
        else:
            print(f"\n💥 Stage {args.stage} 除錯執行失敗")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⏹️  用戶中斷執行")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 除錯工具執行失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()