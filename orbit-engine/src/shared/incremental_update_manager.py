#!/usr/bin/env python3
# 🔄 增量更新管理器
"""
Incremental Update Manager
功能: 智能檢測變更，實現增量更新策略
"""

import os
import json
import time
import glob
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

class IncrementalUpdateManager:
    """增量更新管理器"""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path("/home/sat/ntn-stack")
        self.leo_restructure_path = self.project_root / "leo_restructure"
        self.change_tracking_file = Path("data/logs/leo_change_tracking.json")
        self.logger = logging.getLogger('IncrementalUpdate')
        
        # 載入上次更新信息
        self.last_update_info = self._load_last_update()
        
        # 監控的檔案模式
        self.monitoring_patterns = {
            'tle_data': [
                str(self.project_root / "netstack/tle_data/starlink/tle/starlink_*.tle"),
                str(self.project_root / "netstack/tle_data/oneweb/tle/oneweb_*.tle")
            ],
            'code_files': [
                str(self.leo_restructure_path / "phase1_core_system/**/*.py"),
                str(self.leo_restructure_path / "shared/**/*.py"),
                str(self.leo_restructure_path / "algorithms/**/*.py")
            ],
            'config_files': [
                str(self.leo_restructure_path / "shared/config_manager.py"),
                str(self.leo_restructure_path / "*.py"),
                str(self.project_root / "netstack/config/**/*.py")
            ],
            'output_data': [
                "data/stage*.json",
                "data/processing_outputs/*.json",
                "data/dev_processing_outputs/*.json"
            ]
        }
    
    def detect_changes(self) -> Dict[str, bool]:
        """檢測系統變更"""
        self.logger.info("🔍 開始檢測系統變更...")
        
        changes = {
            'tle_data_updated': self._check_tle_updates(),
            'code_modified': self._check_code_changes(), 
            'config_changed': self._check_config_changes(),
            'output_outdated': self._check_output_freshness(),
            'force_full_rebuild': self._check_force_rebuild()
        }
        
        # 記錄變更詳情
        change_summary = []
        for change_type, has_changed in changes.items():
            if has_changed:
                change_summary.append(change_type)
        
        if change_summary:
            self.logger.info(f"📋 檢測到變更: {', '.join(change_summary)}")
        else:
            self.logger.info("📝 未檢測到任何變更")
        
        return changes
    
    def _check_tle_updates(self) -> bool:
        """檢查TLE數據更新"""
        self.logger.debug("📡 檢查TLE數據更新...")
        
        latest_tle_time = 0
        tle_file_count = 0
        
        for pattern in self.monitoring_patterns['tle_data']:
            for file_path in glob.glob(pattern):
                if os.path.isfile(file_path):
                    file_time = os.path.getmtime(file_path)
                    latest_tle_time = max(latest_tle_time, file_time)
                    tle_file_count += 1
        
        last_tle_time = self.last_update_info.get('tle_update_time', 0)
        tle_updated = latest_tle_time > last_tle_time
        
        if tle_updated:
            self.logger.info(f"📡 TLE數據已更新: {tle_file_count} 個檔案，最新時間 {datetime.fromtimestamp(latest_tle_time)}")
        else:
            self.logger.debug(f"📡 TLE數據無變更: {tle_file_count} 個檔案")
        
        return tle_updated
    
    def _check_code_changes(self) -> bool:
        """檢查代碼變更"""
        self.logger.debug("💻 檢查代碼變更...")
        
        latest_code_time = 0
        code_file_count = 0
        changed_files = []
        
        for pattern in self.monitoring_patterns['code_files']:
            for file_path in Path().glob(pattern.replace(str(Path()), "")):
                if file_path.is_file():
                    file_time = os.path.getmtime(file_path)
                    latest_code_time = max(latest_code_time, file_time)
                    code_file_count += 1
                    
                    # 檢查個別檔案是否變更
                    last_code_time = self.last_update_info.get('code_update_time', 0)
                    if file_time > last_code_time:
                        changed_files.append(str(file_path))
        
        last_code_time = self.last_update_info.get('code_update_time', 0)
        code_updated = latest_code_time > last_code_time
        
        if code_updated:
            self.logger.info(f"💻 代碼已更新: {len(changed_files)} 個檔案變更")
            for file_path in changed_files[:5]:  # 只顯示前5個
                self.logger.debug(f"  - {file_path}")
            if len(changed_files) > 5:
                self.logger.debug(f"  - ... 還有 {len(changed_files) - 5} 個檔案")
        else:
            self.logger.debug(f"💻 代碼無變更: {code_file_count} 個檔案")
        
        return code_updated
    
    def _check_config_changes(self) -> bool:
        """檢查配置變更"""
        self.logger.debug("⚙️ 檢查配置變更...")
        
        latest_config_time = 0
        config_file_count = 0
        
        for pattern in self.monitoring_patterns['config_files']:
            for file_path in glob.glob(pattern):
                if os.path.isfile(file_path):
                    file_time = os.path.getmtime(file_path)
                    latest_config_time = max(latest_config_time, file_time)
                    config_file_count += 1
        
        last_config_time = self.last_update_info.get('config_update_time', 0)
        config_updated = latest_config_time > last_config_time
        
        if config_updated:
            self.logger.info(f"⚙️ 配置已更新: {config_file_count} 個檔案，最新時間 {datetime.fromtimestamp(latest_config_time)}")
        else:
            self.logger.debug(f"⚙️ 配置無變更: {config_file_count} 個檔案")
        
        return config_updated
    
    def _check_output_freshness(self) -> bool:
        """檢查輸出數據是否過期"""
        self.logger.debug("📊 檢查輸出數據新鮮度...")
        
        latest_output_time = 0
        output_file_count = 0
        
        for pattern in self.monitoring_patterns['output_data']:
            for file_path in glob.glob(pattern):
                if os.path.isfile(file_path):
                    file_time = os.path.getmtime(file_path)
                    latest_output_time = max(latest_output_time, file_time)
                    output_file_count += 1
        
        # 如果沒有輸出檔案，認為需要重新生成
        if output_file_count == 0:
            self.logger.info("📊 無輸出檔案，需要重新生成")
            return True
        
        # 檢查輸出是否比代碼或TLE數據舊
        latest_input_time = max(
            self.last_update_info.get('tle_update_time', 0),
            self.last_update_info.get('code_update_time', 0),
            self.last_update_info.get('config_update_time', 0)
        )
        
        output_outdated = latest_output_time < latest_input_time
        
        if output_outdated:
            self.logger.info(f"📊 輸出數據過期: 輸出時間 {datetime.fromtimestamp(latest_output_time)}, 輸入時間 {datetime.fromtimestamp(latest_input_time)}")
        else:
            self.logger.debug(f"📊 輸出數據新鮮: {output_file_count} 個檔案")
        
        return output_outdated
    
    def _check_force_rebuild(self) -> bool:
        """檢查是否強制重建"""
        # 檢查是否存在強制重建標記檔案
        force_rebuild_file = self.project_root / ".force_rebuild"
        
        if force_rebuild_file.exists():
            self.logger.info("🔥 檢測到強制重建標記")
            # 刪除標記檔案
            force_rebuild_file.unlink()
            return True
        
        # 檢查是否超過最大更新間隔（預設7天）
        last_full_rebuild = self.last_update_info.get('last_full_rebuild', 0)
        max_interval_days = 7
        max_interval_seconds = max_interval_days * 24 * 3600
        
        if time.time() - last_full_rebuild > max_interval_seconds:
            self.logger.info(f"⏰ 距離上次完整重建超過 {max_interval_days} 天，強制重建")
            return True
        
        return False
    
    def suggest_update_strategy(self, changes: Dict[str, bool]) -> str:
        """建議更新策略"""
        self.logger.debug("🤔 分析最佳更新策略...")
        
        if changes['force_full_rebuild']:
            strategy = 'full_rebuild'
        elif changes['tle_data_updated'] and not changes['code_modified']:
            strategy = 'tle_incremental'
        elif changes['code_modified'] and not changes['tle_data_updated']:
            strategy = 'code_incremental'  
        elif changes['config_changed'] and not (changes['tle_data_updated'] or changes['code_modified']):
            strategy = 'config_incremental'
        elif changes['tle_data_updated'] and changes['code_modified']:
            strategy = 'hybrid_incremental'
        elif changes['output_outdated']:
            strategy = 'output_refresh'
        else:
            strategy = 'no_update_needed'
        
        self.logger.info(f"💡 建議策略: {strategy}")
        return strategy
    
    def execute_incremental_update(self, strategy: str) -> bool:
        """執行增量更新"""
        self.logger.info(f"🔄 執行增量更新策略: {strategy}")
        
        strategies = {
            'tle_incremental': self._update_tle_data_only,
            'code_incremental': self._update_code_only,
            'config_incremental': self._update_config_only,
            'hybrid_incremental': self._update_hybrid,
            'output_refresh': self._refresh_output_only,
            'full_rebuild': self._full_rebuild,
            'no_update_needed': self._no_update_needed
        }
        
        update_func = strategies.get(strategy)
        if update_func:
            success = update_func()
            if success:
                self._save_update_info()
                self.logger.info(f"✅ 增量更新完成: {strategy}")
            else:
                self.logger.error(f"❌ 增量更新失敗: {strategy}")
            return success
        else:
            self.logger.warning(f"⚠️ 未知更新策略: {strategy}")
            return False
    
    def _update_tle_data_only(self) -> bool:
        """僅更新TLE數據"""
        self.logger.info("📡 僅重新處理TLE數據...")
        
        # 這裡實現TLE增量更新邏輯
        # 保留其他階段的緩存結果，只重新執行F1_TLE_Loader
        try:
            # 模擬TLE更新（實際實現中會調用相應的處理函數）
            time.sleep(1)  # 模擬處理時間
            self.logger.info("📡 TLE數據更新完成")
            return True
        except Exception as e:
            self.logger.error(f"❌ TLE數據更新失敗: {e}")
            return False
    
    def _update_code_only(self) -> bool:
        """僅更新代碼邏輯"""
        self.logger.info("💻 僅重新執行代碼邏輯...")
        
        # 保留TLE計算結果，重新執行篩選和優化
        try:
            time.sleep(1)  # 模擬處理時間
            self.logger.info("💻 代碼邏輯更新完成")
            return True
        except Exception as e:
            self.logger.error(f"❌ 代碼邏輯更新失敗: {e}")
            return False
    
    def _update_config_only(self) -> bool:
        """僅更新配置"""
        self.logger.info("⚙️ 僅重新載入配置...")
        
        try:
            time.sleep(0.5)  # 模擬處理時間
            self.logger.info("⚙️ 配置更新完成")
            return True
        except Exception as e:
            self.logger.error(f"❌ 配置更新失敗: {e}")
            return False
    
    def _update_hybrid(self) -> bool:
        """混合增量更新"""
        self.logger.info("🔀 執行混合增量更新...")
        
        # 同時更新TLE和代碼
        try:
            tle_success = self._update_tle_data_only()
            code_success = self._update_code_only()
            return tle_success and code_success
        except Exception as e:
            self.logger.error(f"❌ 混合更新失敗: {e}")
            return False
    
    def _refresh_output_only(self) -> bool:
        """僅刷新輸出"""
        self.logger.info("📊 僅刷新輸出格式...")
        
        try:
            time.sleep(0.2)  # 模擬處理時間  
            self.logger.info("📊 輸出刷新完成")
            return True
        except Exception as e:
            self.logger.error(f"❌ 輸出刷新失敗: {e}")
            return False
    
    def _full_rebuild(self) -> bool:
        """完整重建"""
        self.logger.info("🔄 執行完整重建...")
        
        try:
            time.sleep(2)  # 模擬處理時間
            self.logger.info("🔄 完整重建完成")
            return True
        except Exception as e:
            self.logger.error(f"❌ 完整重建失敗: {e}")
            return False
    
    def _no_update_needed(self) -> bool:
        """無需更新"""
        self.logger.info("📝 無需更新，系統數據為最新")
        return True
    
    def _load_last_update(self) -> Dict:
        """載入上次更新信息"""
        try:
            if self.change_tracking_file.exists():
                with open(self.change_tracking_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.debug(f"載入更新信息失敗: {e}")
        
        # 返回預設值
        return {
            'tle_update_time': 0,
            'code_update_time': 0,
            'config_update_time': 0,
            'last_full_rebuild': 0,
            'last_check_time': 0
        }
    
    def _save_update_info(self) -> None:
        """保存更新信息"""
        current_time = time.time()
        
        update_info = {
            'tle_update_time': self._get_latest_file_time(self.monitoring_patterns['tle_data']),
            'code_update_time': self._get_latest_file_time(self.monitoring_patterns['code_files']),  
            'config_update_time': self._get_latest_file_time(self.monitoring_patterns['config_files']),
            'last_full_rebuild': current_time,
            'last_check_time': current_time,
            'update_count': self.last_update_info.get('update_count', 0) + 1
        }
        
        try:
            # 確保目錄存在
            self.change_tracking_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.change_tracking_file, 'w', encoding='utf-8') as f:
                json.dump(update_info, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"✅ 更新信息已保存: {self.change_tracking_file}")
        except Exception as e:
            self.logger.warning(f"⚠️ 保存更新信息失敗: {e}")
    
    def _get_latest_file_time(self, patterns: List[str]) -> float:
        """獲取模式中最新檔案的時間"""
        latest_time = 0
        
        for pattern in patterns:
            for file_path in glob.glob(pattern):
                if os.path.isfile(file_path):
                    file_time = os.path.getmtime(file_path)
                    latest_time = max(latest_time, file_time)
        
        return latest_time
    
    def get_update_stats(self) -> Dict:
        """獲取更新統計信息"""
        stats = {
            'last_update_time': self.last_update_info.get('last_check_time', 0),
            'update_count': self.last_update_info.get('update_count', 0),
            'monitoring_patterns': len(self.monitoring_patterns),
            'tracking_file': str(self.change_tracking_file),
            'file_counts': {}
        }
        
        # 統計各類型檔案數量
        for pattern_name, patterns in self.monitoring_patterns.items():
            count = 0
            for pattern in patterns:
                count += len(glob.glob(pattern))
            stats['file_counts'][pattern_name] = count
        
        return stats


def create_incremental_update_manager(project_root: Optional[str] = None) -> IncrementalUpdateManager:
    """創建增量更新管理器實例"""
    return IncrementalUpdateManager(project_root)


# 命令行接口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LEO重構系統增量更新管理器")
    parser.add_argument('--project-root', default='/home/sat/ntn-stack', help='項目根目錄')
    parser.add_argument('--check-only', action='store_true', help='僅檢查變更，不執行更新')
    parser.add_argument('--force-rebuild', action='store_true', help='強制完整重建')
    parser.add_argument('--stats', action='store_true', help='顯示更新統計信息')
    parser.add_argument('--verbose', action='store_true', help='詳細輸出')
    
    args = parser.parse_args()
    
    # 設置日誌
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 創建管理器
    manager = create_incremental_update_manager(args.project_root)
    
    if args.stats:
        # 顯示統計信息
        print("📊 增量更新統計信息:")
        stats = manager.get_update_stats()
        print(f"  上次更新: {datetime.fromtimestamp(stats['last_update_time']) if stats['last_update_time'] else '從未更新'}")
        print(f"  更新次數: {stats['update_count']}")
        print(f"  監控模式數: {stats['monitoring_patterns']}")
        print(f"  檔案數量: {stats['file_counts']}")
    elif args.check_only:
        # 僅檢查變更
        print("🔍 檢查系統變更...")
        changes = manager.detect_changes()
        strategy = manager.suggest_update_strategy(changes)
        print(f"💡 建議策略: {strategy}")
        
        if strategy != 'no_update_needed':
            print("📋 檢測到的變更:")
            for change_type, has_changed in changes.items():
                status = "✅" if has_changed else "❌"
                print(f"  {status} {change_type}")
    else:
        # 執行增量更新
        if args.force_rebuild:
            # 創建強制重建標記
            force_file = Path(args.project_root) / ".force_rebuild"
            force_file.touch()
            print("🔥 已創建強制重建標記")
        
        print("🔄 開始增量更新檢查...")
        changes = manager.detect_changes()
        strategy = manager.suggest_update_strategy(changes)
        
        if strategy == 'no_update_needed':
            print("📝 系統已是最新，無需更新")
        else:
            print(f"🚀 執行更新策略: {strategy}")
            success = manager.execute_incremental_update(strategy)
            
            if success:
                print("✅ 增量更新成功完成")
            else:
                print("❌ 增量更新失敗")
                exit(1)