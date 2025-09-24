#!/usr/bin/env python3
"""
Orbit Engine 路徑遷移腳本

批量更新所有文件中的路徑引用，從 satellite-processing 遷移到 orbit-engine
確保所有 68 個文件都得到正確更新
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# 定義路徑映射關係
PATH_MAPPINGS = {
    # 容器路徑映射
    "/orbit-engine": "/orbit-engine",
    "orbit-engine-dev": "orbit-engine-dev",
    "orbit-postgres-dev": "orbit-postgres-dev",
    "orbit-engine-dev-network": "orbit-engine-dev-network",

    # 特定路徑映射
    "/orbit-engine/src": "/orbit-engine/src",
    "/orbit-engine/data": "/orbit-engine/data",
    "/orbit-engine/config": "/orbit-engine/config",
    "/orbit-engine/scripts": "/orbit-engine/scripts",
    "/orbit-engine/tests": "/orbit-engine/tests",
    "/orbit-engine/docs": "/orbit-engine/docs",

    # 數據路徑映射
    "/orbit-engine/data/outputs": "/orbit-engine/data/outputs",
    "/orbit-engine/data/tle_data": "/orbit-engine/data/tle_data",
    "/orbit-engine/data/validation_snapshots": "/orbit-engine/data/validation_snapshots",
    "/orbit-engine/data/logs": "/orbit-engine/data/logs",

    # 階段輸出路徑映射 (舊不統一路徑 → 新統一路徑)
    "/orbit-engine/data/stage1_outputs": "/orbit-engine/data/outputs/stage1",
    "/orbit-engine/data/stage2_outputs": "/orbit-engine/data/outputs/stage2",
    "/orbit-engine/data/stage3_outputs": "/orbit-engine/data/outputs/stage3",
    "/orbit-engine/data/stage4_outputs": "/orbit-engine/data/outputs/stage4",
    "/orbit-engine/data/stage5_outputs": "/orbit-engine/data/outputs/stage5",
    "/orbit-engine/data/stage6_outputs": "/orbit-engine/data/outputs/stage6",

    # 舊的分散路徑 → 新統一路徑
    "/orbit-engine/data/outputs/stage1": "/orbit-engine/data/outputs/stage1",
    "/orbit-engine/data/outputs/stage2": "/orbit-engine/data/outputs/stage2",
    "/orbit-engine/data/outputs/stage3": "/orbit-engine/data/outputs/stage3",
    "/orbit-engine/data/outputs/stage4": "/orbit-engine/data/outputs/stage4",
    "/orbit-engine/data/outputs/stage5": "/orbit-engine/data/outputs/stage5",
    "/orbit-engine/data/outputs/stage6": "/orbit-engine/data/outputs/stage6",

    # 環境變量和配置
    "ORBIT_ENGINE_HOME": "ORBIT_ENGINE_HOME",
    "orbit_engine_system": "orbit_engine_system",
}

# 需要特別處理的文字替換
TEXT_REPLACEMENTS = {
    "orbit-engine-system": "orbit-engine-system",
    "Orbit Engine System": "Orbit Engine System",
    "軌道引擎系統": "軌道引擎系統",
    "六階段軌道引擎系統": "Orbit Engine 六階段處理系統",
    "orbit engine": "orbit engine",
    "Orbit Engine": "Orbit Engine",
}

def get_all_files_to_update(base_path: Path) -> List[Path]:
    """獲取所有需要更新的文件"""

    # 定義要處理的文件類型
    file_patterns = [
        "**/*.py",      # Python 文件
        "**/*.yml",     # YAML 配置文件
        "**/*.yaml",    # YAML 配置文件
        "**/*.json",    # JSON 配置文件
        "**/*.md",      # Markdown 文檔
        "**/*.sh",      # Shell 腳本
        "Dockerfile",   # Dockerfile
        "docker-compose.yml",  # Docker compose
        "Makefile",     # Makefile
        ".env*",        # 環境變量文件
    ]

    # 排除的目錄和文件
    exclude_patterns = [
        "**/__pycache__/**",
        "**/node_modules/**",
        "**/venv/**",
        "**/env/**",
        "**/.git/**",
        "**/backup/**",
        "**/logs/**",
        "**/.pytest_cache/**",
    ]

    all_files = []

    for pattern in file_patterns:
        files = list(base_path.glob(pattern))

        # 過濾排除的文件
        filtered_files = []
        for file in files:
            should_exclude = False
            for exclude_pattern in exclude_patterns:
                if file.match(exclude_pattern):
                    should_exclude = True
                    break

            if not should_exclude and file.is_file():
                filtered_files.append(file)

        all_files.extend(filtered_files)

    # 去重並排序
    unique_files = list(set(all_files))
    unique_files.sort()

    return unique_files

def update_file_content(file_path: Path) -> Tuple[bool, int]:
    """更新單個文件的內容"""
    try:
        # 讀取文件內容
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        updated_content = original_content
        changes_count = 0

        # 應用路徑映射
        for old_path, new_path in PATH_MAPPINGS.items():
            if old_path in updated_content:
                updated_content = updated_content.replace(old_path, new_path)
                changes_count += original_content.count(old_path)

        # 應用文字替換
        for old_text, new_text in TEXT_REPLACEMENTS.items():
            if old_text in updated_content:
                updated_content = updated_content.replace(old_text, new_text)
                changes_count += original_content.count(old_text)

        # 如果有變更，寫回文件
        if updated_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            return True, changes_count

        return False, 0

    except Exception as e:
        print(f"❌ 更新文件失敗 {file_path}: {e}")
        return False, 0

def main():
    """主執行函數"""
    print("🚀 開始 Orbit Engine 路徑遷移...")

    # 獲取當前腳本所在的項目根目錄
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    print(f"📂 項目根目錄: {project_root}")

    # 獲取所有需要更新的文件
    files_to_update = get_all_files_to_update(project_root)

    print(f"📋 找到 {len(files_to_update)} 個文件需要檢查更新")

    # 統計信息
    updated_files = 0
    total_changes = 0

    # 逐個處理文件
    for file_path in files_to_update:
        relative_path = file_path.relative_to(project_root)

        was_updated, changes_count = update_file_content(file_path)

        if was_updated:
            updated_files += 1
            total_changes += changes_count
            print(f"✅ 更新: {relative_path} ({changes_count} 處修改)")
        else:
            print(f"⚪ 跳過: {relative_path} (無需修改)")

    print(f"\n🎯 遷移完成統計:")
    print(f"📁 檢查文件數: {len(files_to_update)}")
    print(f"✅ 實際更新文件數: {updated_files}")
    print(f"🔄 總修改次數: {total_changes}")

    if updated_files > 0:
        print(f"\n🎉 Orbit Engine 路徑遷移成功完成！")
        print(f"🔧 建議接下來執行:")
        print(f"   1. docker-compose down")
        print(f"   2. docker-compose up --build")
        print(f"   3. docker exec orbit-engine-dev python /orbit-engine/scripts/run_six_stages_with_validation.py")
    else:
        print(f"\n⚪ 沒有文件需要更新，可能已經完成遷移")

if __name__ == "__main__":
    main()