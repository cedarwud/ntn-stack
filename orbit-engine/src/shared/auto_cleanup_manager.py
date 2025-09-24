#!/usr/bin/env python3
# 🧹 自動清理管理器
"""
Auto Cleanup Manager
功能: 智能清理舊數據文件，支持多種清理策略
"""

import os
import glob
import time
from pathlib import Path
from typing import List, Dict, Optional
import logging

class AutoCleanupManager:
    """自動清理管理器"""
    
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir) if output_dir else Path("data/processing_outputs")
        self.logger = logging.getLogger('AutoCleanup')
        
        # 🛡️ 受保護路徑 - 不清理 RL 訓練數據資料夾
        self.protected_paths = [
            '/home/sat/ntn-stack/netstack/tle_data/',
            '/netstack/tle_data/',
            'data/tle_data/'
        ]
        
        # 清理模式配置
        self.cleanup_patterns = {
            # 開發階段輸出
            'dev_outputs': [
                'data/dev_processing_outputs/*.json',
                'data/processing_outputs/*.json',
                str(self.output_dir / "*.json"),
                str(self.output_dir / "*.pkl"),
                str(self.output_dir / "*.cache")
            ],
            # 容器數據 (排除 RL 訓練數據)
            'container_data': [
                'data/stage*.json',
                'data/*_results.json',
                'temp/*'  # 僅臨時數據
            ],
            # 臨時快取 (僅外部緩存，不包含 RL 數據)
            'temp_cache': [
                'data/cache/tle_cache/*.tle',          # 外部臨時緩存
                'data/cache/sgp4_cache/*.pkl',         # SGP4 計算緩存
                'data/cache/leo_*.tmp',                # LEO 臨時文件
                'data/cache/orbit_cache/*.pkl'         # 軌道計算緩存
            ],
            # 全部清理
            'all': []  # 將在init中設置
        }
        
        # 合併所有模式
        self.cleanup_patterns['all'] = []
        for patterns in self.cleanup_patterns.values():
            if isinstance(patterns, list):
                self.cleanup_patterns['all'].extend(patterns)
    
    def cleanup_before_run(self, mode: str = 'dev_outputs') -> int:
        """執行前智能清理"""
        self.logger.info(f"🧹 開始清理模式: {mode}")
        
        patterns = self.cleanup_patterns.get(mode, self.cleanup_patterns['dev_outputs'])
        cleaned_files = 0
        
        for pattern in patterns:
            try:
                for file_path in glob.glob(pattern):
                    if self._safe_to_delete(file_path):
                        os.remove(file_path)
                        cleaned_files += 1
                        self.logger.debug(f"🧹 已清理: {file_path}")
            except Exception as e:
                self.logger.warning(f"⚠️ 清理失敗: {pattern} - {e}")
        
        if cleaned_files > 0:
            self.logger.info(f"✅ 清理完成，共清理 {cleaned_files} 個檔案")
        else:
            self.logger.info("📝 無舊檔案需要清理")
        
        # 確保輸出目錄存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        return cleaned_files
    
    def cleanup_by_age(self, hours: int = 24, mode: str = 'dev_outputs') -> int:
        """按時間清理舊檔案"""
        self.logger.info(f"🕒 清理 {hours} 小時前的檔案...")
        
        cutoff_time = time.time() - (hours * 3600)
        patterns = self.cleanup_patterns.get(mode, self.cleanup_patterns['dev_outputs'])
        cleaned_files = 0
        
        for pattern in patterns:
            try:
                for file_path in glob.glob(pattern):
                    if os.path.getmtime(file_path) < cutoff_time and self._safe_to_delete(file_path):
                        os.remove(file_path)
                        cleaned_files += 1
                        self.logger.debug(f"🕒 清理過期檔案: {file_path}")
            except Exception as e:
                self.logger.warning(f"⚠️ 清理失敗: {pattern} - {e}")
        
        self.logger.info(f"✅ 按時間清理完成，共清理 {cleaned_files} 個檔案")
        return cleaned_files
    
    def cleanup_by_size(self, max_total_mb: int = 1024, mode: str = 'dev_outputs') -> int:
        """按大小清理檔案，保持總大小在限制內"""
        self.logger.info(f"📏 清理以保持總大小 < {max_total_mb}MB...")
        
        patterns = self.cleanup_patterns.get(mode, self.cleanup_patterns['dev_outputs'])
        
        # 收集所有檔案和大小
        files_info = []
        for pattern in patterns:
            try:
                for file_path in glob.glob(pattern):
                    if self._safe_to_delete(file_path):
                        file_size = os.path.getsize(file_path)
                        file_mtime = os.path.getmtime(file_path)
                        files_info.append({
                            'path': file_path,
                            'size': file_size,
                            'mtime': file_mtime
                        })
            except Exception as e:
                self.logger.warning(f"⚠️ 檔案信息收集失敗: {pattern} - {e}")
        
        # 按時間排序，優先刪除舊檔案
        files_info.sort(key=lambda x: x['mtime'])
        
        # 計算總大小
        total_size_mb = sum(f['size'] for f in files_info) / 1024 / 1024
        max_total_bytes = max_total_mb * 1024 * 1024
        
        cleaned_files = 0
        current_size = sum(f['size'] for f in files_info)
        
        if current_size <= max_total_bytes:
            self.logger.info(f"📝 當前總大小 {total_size_mb:.1f}MB 在限制內，無需清理")
            return 0
        
        # 刪除舊檔案直到大小符合要求
        for file_info in files_info:
            if current_size <= max_total_bytes:
                break
            
            try:
                os.remove(file_info['path'])
                current_size -= file_info['size']
                cleaned_files += 1
                self.logger.debug(f"📏 清理大檔案: {file_info['path']}")
            except Exception as e:
                self.logger.warning(f"⚠️ 清理失敗: {file_info['path']} - {e}")
        
        final_size_mb = current_size / 1024 / 1024
        self.logger.info(f"✅ 按大小清理完成，共清理 {cleaned_files} 個檔案，現在總大小 {final_size_mb:.1f}MB")
        return cleaned_files
    
    def _safe_to_delete(self, file_path: str) -> bool:
        """檢查檔案是否可以安全刪除"""
        try:
            # 檢查檔案是否存在且是檔案
            if not os.path.isfile(file_path):
                return False
            
            # 🛡️ 簡單保護 RL 訓練數據資料夾
            for protected_path in self.protected_paths:
                if file_path.startswith(protected_path):
                    self.logger.warning(f"🛡️ 受保護路徑，跳過: {file_path}")
                    return False
            
            # 檢查檔案是否正在被使用（簡單檢查）
            try:
                with open(file_path, 'a'):
                    pass
                return True
            except IOError:
                self.logger.warning(f"⚠️ 檔案可能正在使用: {file_path}")
                return False
                
        except Exception:
            return False
    
    def get_cleanup_stats(self, mode: str = 'dev_outputs') -> Dict:
        """獲取清理統計信息"""
        patterns = self.cleanup_patterns.get(mode, self.cleanup_patterns['dev_outputs'])
        
        stats = {
            'total_files': 0,
            'total_size_mb': 0.0,
            'oldest_file': None,
            'newest_file': None,
            'file_types': {}
        }
        
        oldest_time = float('inf')
        newest_time = 0
        
        for pattern in patterns:
            try:
                for file_path in glob.glob(pattern):
                    if os.path.isfile(file_path):
                        stats['total_files'] += 1
                        
                        # 大小統計
                        file_size = os.path.getsize(file_path)
                        stats['total_size_mb'] += file_size / 1024 / 1024
                        
                        # 時間統計
                        file_mtime = os.path.getmtime(file_path)
                        if file_mtime < oldest_time:
                            oldest_time = file_mtime
                            stats['oldest_file'] = file_path
                        if file_mtime > newest_time:
                            newest_time = file_mtime
                            stats['newest_file'] = file_path
                        
                        # 檔案類型統計
                        file_ext = Path(file_path).suffix.lower()
                        stats['file_types'][file_ext] = stats['file_types'].get(file_ext, 0) + 1
                        
            except Exception as e:
                self.logger.warning(f"⚠️ 統計失敗: {pattern} - {e}")
        
        return stats
    
    def schedule_cleanup(self, interval_hours: int = 6, max_age_hours: int = 24) -> None:
        """調度定期清理（適合與Cron整合）"""
        self.logger.info(f"📅 調度清理: 每{interval_hours}小時，清理{max_age_hours}小時前檔案")
        
        # 這個方法主要用於生成Cron配置，實際調度由系統Cron完成
        cron_command = f"""
# LEO重構系統自動清理
# 每{interval_hours}小時清理一次
0 */{interval_hours} * * * cd /home/sat/ntn-stack/leo_restructure && python -c "
from shared.auto_cleanup_manager import AutoCleanupManager
manager = AutoCleanupManager()
manager.cleanup_by_age({max_age_hours})
" >> data/logs/auto_cleanup.log 2>&1
"""
        
        self.logger.info(f"📋 建議的Cron配置:\n{cron_command}")


def create_auto_cleanup_manager(output_dir: Optional[str] = None) -> AutoCleanupManager:
    """創建自動清理管理器實例"""
    return AutoCleanupManager(output_dir)


# 命令行接口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LEO重構系統自動清理管理器")
    parser.add_argument('--mode', default='dev_outputs', choices=['dev_outputs', 'container_data', 'temp_cache', 'all'])
    parser.add_argument('--age-hours', type=int, default=24, help='清理多少小時前的檔案')
    parser.add_argument('--max-size-mb', type=int, default=1024, help='最大總大小(MB)')
    parser.add_argument('--output-dir', default='data/processing_outputs', help='輸出目錄')
    parser.add_argument('--stats-only', action='store_true', help='僅顯示統計信息')
    parser.add_argument('--verbose', action='store_true', help='詳細輸出')
    
    args = parser.parse_args()
    
    # 設置日誌
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 創建管理器
    manager = create_auto_cleanup_manager(args.output_dir)
    
    if args.stats_only:
        # 僅顯示統計信息
        print("📊 清理統計信息:")
        stats = manager.get_cleanup_stats(args.mode)
        print(f"  總檔案數: {stats['total_files']}")
        print(f"  總大小: {stats['total_size_mb']:.1f}MB")
        print(f"  最舊檔案: {stats['oldest_file']}")
        print(f"  最新檔案: {stats['newest_file']}")
        print(f"  檔案類型: {stats['file_types']}")
    else:
        # 執行清理
        print(f"🧹 開始自動清理 (模式: {args.mode})...")
        cleaned_before = manager.cleanup_before_run(args.mode)
        cleaned_age = manager.cleanup_by_age(args.age_hours, args.mode)
        cleaned_size = manager.cleanup_by_size(args.max_size_mb, args.mode)
        
        total_cleaned = cleaned_before + cleaned_age + cleaned_size
        print(f"✅ 清理完成，總共清理 {total_cleaned} 個檔案")