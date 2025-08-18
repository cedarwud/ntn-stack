#!/usr/bin/env python3
"""
LEO核心系統主入口腳本
將主流程控制器功能封裝為容器啟動時的入口點
"""

import sys
import asyncio
import argparse
from pathlib import Path

# 確保導入路徑
sys.path.insert(0, '/app/src')

from leo_core.main_pipeline_controller import create_leo_main_pipeline

async def main():
    """主執行函數"""
    parser = argparse.ArgumentParser(description="LEO核心系統主流程")
    parser.add_argument("--mode", choices=['full', 'single'], default='full', 
                       help="執行模式: full=完整流程, single=單一階段")
    parser.add_argument("--stage", choices=['stage1', 'stage2', 'stage3', 'stage4', 'stage5', 'stage6'],
                       help="單一階段模式下指定要執行的階段")
    parser.add_argument("--input", help="單一階段模式下的輸入檔案")
    parser.add_argument("--output-dir", default="/app/data", help="輸出目錄")
    parser.add_argument("--fast", action="store_true", help="快速模式（取樣處理）")
    
    args = parser.parse_args()
    
    print("🚀 LEO核心系統六階段流程啟動")
    print("=" * 80)
    print(f"執行模式: {args.mode}")
    print(f"輸出目錄: {args.output_dir}")
    print(f"快速模式: {'是' if args.fast else '否'}")
    print("=" * 80)
    
    try:
        # 創建主流程控制器
        pipeline = create_leo_main_pipeline(args.output_dir)
        
        if args.mode == 'full':
            # 執行完整流程
            print("🔥 執行完整六階段流程...")
            result = await pipeline.execute_complete_pipeline()
            
            if result.get('pipeline_success'):
                print("✅ 完整流程執行成功！")
                
                # 顯示每個階段的處理結果
                for stage_name, stage_result in result.get('stages', {}).items():
                    if stage_result.get('success'):
                        print(f"✅ {stage_name}: {stage_result.get('stage_description', '')}")
                        print(f"   處理時間: {stage_result.get('processing_time', 0):.2f}秒")
                    else:
                        print(f"❌ {stage_name}: {stage_result.get('error', '未知錯誤')}")
                
                # 總體統計
                summary = result.get('pipeline_summary', {})
                print(f"\n📈 總處理時間: {summary.get('total_processing_time_seconds', 0)}秒")
                print(f"📈 成功率: {summary.get('pipeline_success_rate', '0%')}")
                
                return True
            else:
                print("❌ 完整流程執行失敗")
                print(f"錯誤: {result.get('error', '未知錯誤')}")
                return False
                
        elif args.mode == 'single':
            if not args.stage:
                print("❌ 單一階段模式需要指定 --stage 參數")
                return False
                
            # 執行單一階段
            print(f"🔧 執行單一階段: {args.stage}")
            result = await pipeline.execute_single_stage(args.stage, args.input)
            
            if result.get('success'):
                print(f"✅ {args.stage} 執行成功")
                print(f"   處理時間: {result.get('processing_time', 0):.2f}秒")
                print(f"   輸出檔案: {result.get('output_file', 'N/A')}")
                return True
            else:
                print(f"❌ {args.stage} 執行失敗")
                print(f"錯誤: {result.get('error', '未知錯誤')}")
                return False
        
    except Exception as e:
        print(f"💥 執行異常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)