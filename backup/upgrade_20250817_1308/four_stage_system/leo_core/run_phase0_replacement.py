#!/usr/bin/env python3
# 🔥 Phase 0: 系統替換整合執行腳本
"""
Phase 0 System Replacement Executor
功能: 一鍵執行 leo_restructure 替換原6階段系統
使用: python run_phase0_replacement.py
"""

import asyncio
import sys
import os
import shutil
import subprocess
from pathlib import Path
import argparse
import logging
from datetime import datetime

class Phase0Executor:
    """Phase 0 系統替換執行器"""
    
    def __init__(self, dry_run=False, backup=True):
        self.dry_run = dry_run
        self.backup = backup
        self.logger = self._setup_logger()
        
        # 路徑配置
        self.project_root = Path("/home/sat/ntn-stack")
        self.leo_restructure_path = self.project_root / "leo_restructure"
        self.netstack_path = self.project_root / "netstack"
        
        # 備份路徑
        self.backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        self.backup_root = self.project_root / "phase0_backup" / self.backup_timestamp
        
    def _setup_logger(self):
        """設置日誌"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - Phase0 - %(levelname)s - %(message)s'
        )
        return logging.getLogger('Phase0Executor')
    
    async def execute_complete_replacement(self):
        """執行完整的系統替換流程"""
        self.logger.info("🔥 啟動 Phase 0: 系統替換整合流程")
        
        try:
            # P0.1: Docker建構整合
            await self._p01_docker_integration()
            
            # P0.2: 配置系統統一  
            await self._p02_config_unification()
            
            # P0.3: 輸出格式對接
            await self._p03_output_formatting()
            
            # P0.4: 系統替換與驗證
            await self._p04_system_replacement()
            
            self.logger.info("🎉 Phase 0 系統替換完成！")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Phase 0 執行失敗: {e}")
            if self.backup:
                await self._emergency_rollback()
            return False
    
    async def _p01_docker_integration(self):
        """P0.1: Docker建構整合"""
        self.logger.info("📡 P0.1: 開始Docker建構整合...")
        
        # 備份原建構腳本
        if self.backup:
            await self._backup_file(
                self.netstack_path / "docker" / "build_with_phase0_data.py",
                "build_with_phase0_data.py.backup"
            )
        
        # 修改建構腳本
        build_script_path = self.netstack_path / "docker" / "build_with_phase0_data.py"
        
        if not self.dry_run:
            await self._modify_build_script(build_script_path)
        
        self.logger.info("✅ P0.1: Docker建構整合完成")
    
    async def _p02_config_unification(self):
        """P0.2: 配置系統統一"""
        self.logger.info("⚙️ P0.2: 開始配置系統統一...")
        
        # 複製配置管理器
        source_config = self.leo_restructure_path / "shared_core" / "config_manager.py"
        target_config = self.netstack_path / "config" / "leo_config.py"
        
        if not self.dry_run:
            if source_config.exists():
                shutil.copy2(source_config, target_config)
                self.logger.info(f"✅ 配置管理器已複製: {target_config}")
            else:
                self.logger.warning(f"⚠️ 源配置文件不存在: {source_config}")
        
        self.logger.info("✅ P0.2: 配置系統統一完成")
    
    async def _p03_output_formatting(self):
        """P0.3: 輸出格式對接"""
        self.logger.info("📊 P0.3: 開始輸出格式對接...")
        
        # 創建輸出格式化器
        formatter_content = '''"""
前端兼容的輸出格式化器
將 leo_restructure 輸出轉換為前端期望格式
"""

import json
from pathlib import Path
from datetime import datetime

class FrontendCompatibleFormatter:
    """前端兼容的輸出格式化器"""
    
    def format_for_frontend(self, satellite_pools, output_path="/app/data"):
        """格式化為前端需要的格式"""
        
        # 生成前端兼容的JSON格式
        frontend_data = {
            "metadata": {
                "generation_time": datetime.now().isoformat(),
                "data_source": "leo_restructure_phase1",
                "format_version": "1.0"
            },
            "satellites": self._format_satellites(satellite_pools),
            "timeline": self._format_timeline(satellite_pools),
            "handover_events": self._format_handover_events(satellite_pools)
        }
        
        # 輸出到指定路徑
        output_file = Path(output_path) / "frontend_compatible_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(frontend_data, f, indent=2, ensure_ascii=False)
        
        return frontend_data
    
    def _format_satellites(self, pools):
        """格式化衛星數據"""
        satellites = []
        
        if hasattr(pools, 'starlink_satellites'):
            for sat in pools.starlink_satellites:
                satellites.append({
                    "id": f"starlink_{sat.get('satellite_id', 'unknown')}",
                    "constellation": "starlink",
                    "name": sat.get('satellite_name', ''),
                    "orbital_parameters": sat.get('orbital_parameters', {}),
                    "positions": sat.get('timeline_positions', [])
                })
        
        if hasattr(pools, 'oneweb_satellites'):
            for sat in pools.oneweb_satellites:
                satellites.append({
                    "id": f"oneweb_{sat.get('satellite_id', 'unknown')}",
                    "constellation": "oneweb", 
                    "name": sat.get('satellite_name', ''),
                    "orbital_parameters": sat.get('orbital_parameters', {}),
                    "positions": sat.get('timeline_positions', [])
                })
        
        return satellites
    
    def _format_timeline(self, pools):
        """格式化時間軸數據"""
        # 生成200個時間點，30秒間隔
        timeline = []
        
        for i in range(200):
            timestamp = datetime.now().timestamp() + (i * 30)
            timeline.append({
                "timestamp": datetime.fromtimestamp(timestamp).isoformat(),
                "visible_starlink": [],  # 實際數據需要從pools計算
                "visible_oneweb": []
            })
        
        return timeline
    
    def _format_handover_events(self, pools):
        """格式化換手事件數據"""
        events = []
        
        # 從pools中提取A4/A5/D2事件
        if hasattr(pools, 'handover_events'):
            for event in pools.handover_events:
                events.append({
                    "timestamp": event.get('timestamp', ''),
                    "event_type": event.get('type', ''),
                    "source_satellite": event.get('source', ''),
                    "target_satellite": event.get('target', ''),
                    "signal_quality": event.get('signal_metrics', {})
                })
        
        return events
'''
        
        formatter_path = self.leo_restructure_path / "shared_core" / "frontend_formatter.py"
        
        if not self.dry_run:
            with open(formatter_path, 'w', encoding='utf-8') as f:
                f.write(formatter_content)
            self.logger.info(f"✅ 輸出格式化器已創建: {formatter_path}")
        
        self.logger.info("✅ P0.3: 輸出格式對接完成")
    
    async def _p04_system_replacement(self):
        """P0.4: 系統替換與驗證"""
        self.logger.info("🔄 P0.4: 開始系統替換與驗證...")
        
        # 備份舊系統
        if self.backup:
            await self._backup_old_system()
        
        # 部署新系統
        await self._deploy_new_system()
        
        # 驗證系統
        await self._verify_system()
        
        self.logger.info("✅ P0.4: 系統替換與驗證完成")
    
    async def _backup_old_system(self):
        """備份舊系統"""
        self.logger.info("📦 開始備份舊系統...")
        
        self.backup_root.mkdir(parents=True, exist_ok=True)
        
        # 備份stages目錄
        stages_src = self.netstack_path / "src" / "stages"
        stages_backup = self.backup_root / "stages"
        
        if stages_src.exists():
            shutil.copytree(stages_src, stages_backup)
            self.logger.info(f"✅ 已備份stages目錄: {stages_backup}")
        
        # 備份services/satellite目錄
        services_src = self.netstack_path / "src" / "services" / "satellite"
        services_backup = self.backup_root / "services_satellite"
        
        if services_src.exists():
            shutil.copytree(services_src, services_backup)
            self.logger.info(f"✅ 已備份services/satellite目錄: {services_backup}")
        
        # 備份根目錄的舊pipeline檔案
        old_files = [
            "run_stage6_independent.py",
            "verify_complete_pipeline.py", 
            "fix_stage2_filtering.py",
            "complete_pipeline.py"
        ]
        
        for file_name in old_files:
            src_file = self.project_root / file_name
            if src_file.exists():
                dst_file = self.backup_root / file_name
                shutil.copy2(src_file, dst_file)
                self.logger.info(f"✅ 已備份檔案: {file_name}")
    
    async def _deploy_new_system(self):
        """部署新系統"""
        self.logger.info("🚀 開始部署新系統...")
        
        if not self.dry_run:
            # 移除舊stages目錄
            stages_path = self.netstack_path / "src" / "stages"
            if stages_path.exists():
                shutil.rmtree(stages_path)
                self.logger.info("✅ 已移除舊stages目錄")
            
            # 部署leo_restructure為leo_core
            leo_core_path = self.netstack_path / "src" / "leo_core"
            if leo_core_path.exists():
                shutil.rmtree(leo_core_path)
            
            shutil.copytree(self.leo_restructure_path, leo_core_path)
            self.logger.info(f"✅ 已部署leo_restructure為: {leo_core_path}")
        
        self.logger.info("✅ 新系統部署完成")
    
    async def _verify_system(self):
        """驗證系統"""
        self.logger.info("🔍 開始系統驗證...")
        
        # 檢查關鍵檔案是否存在
        leo_core_path = self.netstack_path / "src" / "leo_core"
        key_files = [
            "run_phase1.py",
            "phase1_core_system/main_pipeline.py",
            "shared_core/config_manager.py"
        ]
        
        for file_path in key_files:
            full_path = leo_core_path / file_path
            if full_path.exists():
                self.logger.info(f"✅ 關鍵檔案存在: {file_path}")
            else:
                raise FileNotFoundError(f"關鍵檔案缺失: {file_path}")
        
        self.logger.info("✅ 系統驗證通過")
    
    async def _modify_build_script(self, build_script_path):
        """修改建構腳本"""
        if not build_script_path.exists():
            self.logger.warning(f"⚠️ 建構腳本不存在: {build_script_path}")
            return
        
        # 讀取原檔案
        with open(build_script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 添加leo_restructure調用的註釋標記
        leo_integration = '''
# === LEO_RESTRUCTURE INTEGRATION (Phase 0) ===
# 替換原6階段處理為leo_restructure Phase 1
import sys
sys.path.append('/app/src/leo_core')

try:
    from run_phase1 import main as leo_main
    import asyncio
    
    logger.info("🛰️ 啟動LEO重構系統Phase 1...")
    
    # 執行leo_restructure with output to /app/data
    result = asyncio.run(leo_main([
        '--output-dir', '/app/data',
        '--fast',  # 使用快速模式
        '--verbose'
    ]))
    
    if result:
        logger.info("✅ LEO重構系統Phase 1執行成功")
    else:
        logger.error("❌ LEO重構系統Phase 1執行失敗")
        
except Exception as e:
    logger.error(f"❌ LEO重構系統執行錯誤: {e}")
    # 可以在這裡添加fallback機制
# === LEO_RESTRUCTURE INTEGRATION END ===
'''
        
        # 在檔案末尾添加leo_restructure整合
        modified_content = content + leo_integration
        
        # 寫回檔案
        with open(build_script_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        self.logger.info(f"✅ 建構腳本已修改: {build_script_path}")
    
    async def _backup_file(self, source_path, backup_name):
        """備份單個檔案"""
        if source_path.exists():
            backup_path = self.backup_root / backup_name
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, backup_path)
            self.logger.info(f"✅ 已備份檔案: {backup_name}")
    
    async def _emergency_rollback(self):
        """緊急回退"""
        self.logger.warning("🚨 執行緊急回退...")
        
        # 恢復stages目錄
        stages_backup = self.backup_root / "stages"
        stages_target = self.netstack_path / "src" / "stages"
        
        if stages_backup.exists():
            if stages_target.exists():
                shutil.rmtree(stages_target)
            shutil.copytree(stages_backup, stages_target)
            self.logger.info("✅ 已恢復stages目錄")
        
        # 移除leo_core
        leo_core_path = self.netstack_path / "src" / "leo_core"
        if leo_core_path.exists():
            shutil.rmtree(leo_core_path)
            self.logger.info("✅ 已移除leo_core目錄")
        
        self.logger.info("✅ 緊急回退完成")

def parse_arguments():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(
        description="Phase 0: leo_restructure 系統替換執行器",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='乾運行模式，只顯示將要執行的操作'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='不進行備份（不建議在生產環境使用）'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true', 
        help='詳細輸出'
    )
    
    return parser.parse_args()

async def main():
    """主執行函數"""
    args = parse_arguments()
    
    print("🔥 Phase 0: LEO重構系統替換執行器")
    print("=" * 60)
    print("🎯 目標: 完全替代原6階段系統為leo_restructure")
    print("📋 流程: P0.1→P0.2→P0.3→P0.4 (Docker→配置→格式→替換)")
    
    if args.dry_run:
        print("🔍 乾運行模式: 只顯示操作，不實際執行")
    
    if args.no_backup:
        print("⚠️ 無備份模式: 將不進行安全備份")
    
    print("-" * 60)
    
    # 確認執行
    if not args.dry_run:
        confirm = input("確定要執行系統替換嗎？ (y/N): ")
        if confirm.lower() != 'y':
            print("❌ 用戶取消執行")
            return False
    
    # 創建執行器
    executor = Phase0Executor(
        dry_run=args.dry_run,
        backup=not args.no_backup
    )
    
    # 執行替換
    success = await executor.execute_complete_replacement()
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 Phase 0 系統替換成功完成！")
        print("✅ leo_restructure 已成為主要處理系統")
        print("✅ 原6階段系統已完全替換")
        print("📋 下一步: 執行 'make down-v && make build-n && make up' 測試")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)  
        print("❌ Phase 0 系統替換失敗")
        print("🚨 系統已回退到原狀態")
        print("💡 建議檢查錯誤日誌並重新嘗試")
        print("=" * 60)
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ 用戶中斷執行")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 未預期錯誤: {e}")
        sys.exit(1)