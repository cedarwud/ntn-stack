#!/usr/bin/env python3
"""
SimWorld Backend TLE 服務移除遷移腳本
根據 Sky Project Phase 1 完成狀態，安全移除重複的 TLE 服務

執行前提：
1. 前端已統一使用 NetStack API (Phase 1 已完成)
2. SimWorld 不再需要自己的 TLE 計算服務
3. 所有衛星軌道計算已遷移到 NetStack
"""

import os
import shutil
from pathlib import Path
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def backup_files(files_to_remove, backup_dir):
    """備份要移除的文件"""
    backup_path = Path(backup_dir)
    backup_path.mkdir(exist_ok=True)
    
    for file_path in files_to_remove:
        if Path(file_path).exists():
            backup_file = backup_path / Path(file_path).name
            shutil.copy2(file_path, backup_file)
            logger.info(f"✅ 備份: {file_path} -> {backup_file}")

def remove_tle_services():
    """移除 TLE 相關服務"""
    
    # 要移除的服務文件
    services_to_remove = [
        "app/services/tle_data_service.py",
        "app/services/historical_data_cache.py",
        "app/api/routes/tle.py"
    ]
    
    # 要移除的數據目錄
    data_dirs_to_remove = [
        "data/tle_cache",
        "data/tle_historical", 
        "data/batch_cache"
    ]
    
    # 創建備份
    backup_dir = f"migration_backup_{int(__import__('time').time())}"
    backup_files(services_to_remove, backup_dir)
    
    # 移除服務文件
    for service_file in services_to_remove:
        if Path(service_file).exists():
            os.remove(service_file)
            logger.info(f"🗑️ 移除服務: {service_file}")
    
    # 移除數據目錄
    for data_dir in data_dirs_to_remove:
        if Path(data_dir).exists():
            shutil.rmtree(data_dir)
            logger.info(f"🗑️ 移除數據目錄: {data_dir}")
    
    logger.info("✅ TLE 服務移除完成")

def update_router():
    """更新路由配置，移除 TLE 路由"""
    router_file = "app/api/v1/router.py"
    
    if not Path(router_file).exists():
        logger.warning(f"路由文件不存在: {router_file}")
        return
    
    # 讀取原文件
    with open(router_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 移除 TLE 相關導入和註冊
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        # 跳過 TLE 相關的行
        if ('tle_router' in line or 
            'from app.api.routes.tle import' in line or
            'TLE Data' in line):
            logger.info(f"🗑️ 移除路由行: {line.strip()}")
            continue
        new_lines.append(line)
    
    # 寫回文件
    with open(router_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    logger.info(f"✅ 更新路由配置: {router_file}")

def update_requirements():
    """更新 requirements.txt，移除不需要的依賴"""
    req_file = "requirements.txt"
    
    if not Path(req_file).exists():
        logger.warning(f"Requirements 文件不存在: {req_file}")
        return
    
    # 讀取當前依賴
    with open(req_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 移除 TLE 相關依賴（如果有的話）
    # 注意：skyfield 等依賴可能還被其他服務使用，需要謹慎處理
    logger.info("📋 Requirements.txt 保持不變（其他服務可能還需要相關依賴）")

def main():
    """主遷移流程"""
    logger.info("🚀 開始 SimWorld TLE 服務移除遷移")
    
    # 檢查當前目錄
    if not Path("app").exists():
        logger.error("❌ 請在 simworld/backend 目錄下執行此腳本")
        return
    
    try:
        # 1. 移除 TLE 服務
        remove_tle_services()
        
        # 2. 更新路由配置
        update_router()
        
        # 3. 檢查 requirements
        update_requirements()
        
        logger.info("✅ 遷移完成！")
        logger.info("📋 後續步驟:")
        logger.info("   1. 重啟 SimWorld backend 容器")
        logger.info("   2. 測試前端功能是否正常")
        logger.info("   3. 確認 NetStack API 調用正常")
        
    except Exception as e:
        logger.error(f"❌ 遷移失敗: {e}")
        raise

if __name__ == "__main__":
    main()