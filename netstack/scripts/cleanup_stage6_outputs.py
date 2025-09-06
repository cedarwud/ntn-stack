#!/usr/bin/env python3
"""
🗑️ 階段六輸出清理工具
在執行六階段處理前清理所有階段六相關的舊輸出檔案
"""

import sys
import os
import logging
from pathlib import Path
import shutil

# 確保能找到模組
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/src')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def cleanup_all_stage6_outputs():
    """
    🗑️ 全面清理階段六所有輸出檔案和目錄
    獨立的清理工具，可在六階段處理前調用
    """
    logger.info("🗑️ 開始全面清理階段六輸出...")
    logger.info("=" * 60)
    
    # 定義所有可能的階段六輸出路徑
    cleanup_paths = [
        # 容器內路徑
        # 舊的子目錄路徑（向下兼容）
        Path("/app/data/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json"),
        Path("/app/data/enhanced_dynamic_pools_output.json"),
        Path("/app/data/stage6_dynamic_pool_output.json"),
        Path("/app/data/stage6_dynamic_pool.json"),
        Path("/app/data/dynamic_pools.json"),
        # 主機路徑（如果存在映射）
        # 舊的子目錄路徑（向下兼容）
        Path("/home/sat/ntn-stack/data/dynamic_pool_planning_outputs/enhanced_dynamic_pools_output.json"),
        Path("/home/sat/ntn-stack/data/enhanced_dynamic_pools_output.json"),
        Path("/home/sat/ntn-stack/data/stage6_dynamic_pool_output.json"),
        Path("/home/sat/ntn-stack/data/stage6_dynamic_pool.json"),
        Path("/home/sat/ntn-stack/data/dynamic_pools.json"),
    ]
    
    # 清理目錄
    cleanup_directories = [
        # 容器內目錄
        # 舊的子目錄（向下兼容）
        Path("/app/data/dynamic_pool_planning_outputs"),
        # 主機目錄（如果存在）
        # 舊的子目錄（向下兼容）
        Path("/home/sat/ntn-stack/data/dynamic_pool_planning_outputs"),
    ]
    
    cleaned_files = 0
    cleaned_dirs = 0
    total_size_mb = 0.0
    
    logger.info("🗑️ 清理檔案...")
    
    # 清理檔案
    for file_path in cleanup_paths:
        try:
            if file_path.exists():
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                total_size_mb += file_size_mb
                file_path.unlink()
                cleaned_files += 1
                logger.info(f"  ✅ 已刪除檔案: {file_path} ({file_size_mb:.1f} MB)")
        except Exception as e:
            logger.warning(f"  ⚠️ 刪除檔案失敗 {file_path}: {e}")
    
    logger.info("🗑️ 清理目錄...")
    
    # 清理並重新創建目錄
    for dir_path in cleanup_directories:
        try:
            if dir_path.exists() and dir_path.is_dir():
                # 統計目錄內檔案數
                files_in_dir = list(dir_path.rglob("*"))
                file_count = len([f for f in files_in_dir if f.is_file()])
                
                if file_count > 0:
                    # 計算目錄大小
                    dir_size_mb = sum(f.stat().st_size for f in files_in_dir if f.is_file()) / (1024 * 1024)
                    total_size_mb += dir_size_mb
                    
                    shutil.rmtree(dir_path)
                    dir_path.mkdir(parents=True, exist_ok=True)
                    cleaned_dirs += 1
                    logger.info(f"  🗂️ 已清理目錄: {dir_path} ({file_count} 檔案, {dir_size_mb:.1f} MB)")
                else:
                    logger.info(f"  📁 目錄已存在且為空: {dir_path}")
            else:
                # 創建目錄
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"  📁 已創建目錄: {dir_path}")
        except Exception as e:
            logger.warning(f"  ⚠️ 目錄處理失敗 {dir_path}: {e}")
    
    logger.info("=" * 60)
    logger.info("🗑️ 清理結果統計:")
    logger.info(f"  📁 清理的檔案數: {cleaned_files}")
    logger.info(f"  🗂️ 清理的目錄數: {cleaned_dirs}")
    logger.info(f"  💾 釋放的空間: {total_size_mb:.1f} MB")
    
    if cleaned_files > 0 or cleaned_dirs > 0:
        logger.info("✅ 階段六清理完成！現在可以安全執行六階段處理")
        return True
    else:
        logger.info("ℹ️ 沒有發現需要清理的階段六檔案")
        return False


def main():
    """主函數"""
    logger.info("🗑️ 階段六輸出清理工具")
    logger.info("=" * 60)
    logger.info("⚠️  此工具將刪除所有階段六的舊輸出檔案")
    logger.info("💡 建議在執行六階段處理前運行此工具")
    logger.info("=" * 60)
    
    try:
        success = cleanup_all_stage6_outputs()
        
        if success:
            logger.info("🎉 清理完成！階段六已準備好重新處理")
            sys.exit(0)
        else:
            logger.info("✅ 無需清理，階段六環境乾淨")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"❌ 清理過程發生錯誤: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()