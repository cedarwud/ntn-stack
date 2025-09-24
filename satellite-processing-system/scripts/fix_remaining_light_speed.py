#!/usr/bin/env python3
"""
批量修復剩餘的硬編碼光速常數
"""

import re
from pathlib import Path

def fix_light_speed_hardcode(file_path: Path):
    """修復單個文件中的硬編碼光速常數"""
    content = file_path.read_text(encoding='utf-8')
    original_content = content

    # 替換模式
    patterns = [
        # 基本硬編碼
        (r'299792458\.0', 'physics_consts.SPEED_OF_LIGHT'),
        (r'299792458', 'physics_consts.SPEED_OF_LIGHT'),

        # 特定上下文替換
        (r'wavelength_m = 299792458\.0 / \(frequency_ghz \* 1e9\)',
         'wavelength_m = physics_consts.SPEED_OF_LIGHT / (frequency_ghz * 1e9)'),

        (r'velocity_ms / 299792458\.0',
         'velocity_ms / physics_consts.SPEED_OF_LIGHT'),

        (r'LIGHT_SPEED_M_S = 299792458\.0',
         'LIGHT_SPEED_M_S = physics_consts.SPEED_OF_LIGHT'),

        (r'speed_of_light = 299792458\.0',
         'speed_of_light = physics_consts.SPEED_OF_LIGHT'),
    ]

    # 檢查是否需要添加import
    needs_import = False
    for pattern, replacement in patterns:
        if re.search(pattern, content):
            needs_import = True
            content = re.sub(pattern, replacement, content)

    # 添加import (如果需要且不存在)
    if needs_import and 'from shared.constants.physics_constants import PhysicsConstants' not in content:
        # 找到合適的位置插入import
        lines = content.split('\n')
        insert_index = 0

        # 找到import區域的結尾
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                insert_index = i + 1
            elif line.strip() == '' and insert_index > 0:
                break

        # 插入import和實例化
        import_lines = [
            '# 🚨 Grade A要求：使用學術級物理常數',
            'from shared.constants.physics_constants import PhysicsConstants',
            'physics_consts = PhysicsConstants()',
            ''
        ]

        for j, import_line in enumerate(import_lines):
            lines.insert(insert_index + j, import_line)

        content = '\n'.join(lines)

    # 如果內容有變化，寫回文件
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        print(f"✅ 修復: {file_path}")
        return True

    return False

def main():
    """主函數"""
    # 需要修復的文件列表
    files_to_fix = [
        "src/stages/stage3_signal_analysis/stage3_signal_analysis_processor.py",
        "src/stages/stage3_signal_analysis/physics_validator.py",
        "src/shared/utils.py",
        "src/shared/utils/math_utils.py",
        "src/shared/core_modules/signal_calculations_core.py"
    ]

    project_root = Path(__file__).parent.parent
    fixed_count = 0

    for file_path_str in files_to_fix:
        file_path = project_root / file_path_str
        if file_path.exists():
            if fix_light_speed_hardcode(file_path):
                fixed_count += 1
        else:
            print(f"⚠️ 文件不存在: {file_path}")

    print(f"\n📊 修復完成: {fixed_count} 個文件")

if __name__ == "__main__":
    main()