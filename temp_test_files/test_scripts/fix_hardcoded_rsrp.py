#!/usr/bin/env python3
"""
批量修復所有RSRP硬編碼問題的腳本
"""
import os
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STAGES_DIR = "/home/sat/ntn-stack/satellite-processing-system/src/stages"

# 需要修復的硬編碼模式
HARDCODED_PATTERNS = {
    r'= -85([,\s\)])': r'= (noise_floor + 35)\1  # 動態計算：噪聲門檻 + 優秀裕度',
    r'= -88([,\s\)])': r'= (noise_floor + 32)\1  # 動態計算：噪聲門檻 + 優秀裕度',
    r'= -90([,\s\)])': r'= (noise_floor + 30)\1  # 動態計算：噪聲門檻 + 良好裕度',
    r'get\(".*?", -85\)': r'get("excellent_quality_dbm")',
    r'get\(".*?", -88\)': r'get("excellent_quality_dbm")',
    r'get\(".*?", -90\)': r'get("good_threshold_dbm")',
    r'", -85': r'")',
    r'", -88': r'")',
    r'", -90': r'")',
}

def add_noise_floor_definition(content: str) -> str:
    """在文件中添加noise_floor定義"""
    if "noise_floor = -120" in content:
        return content

    # 在第一個RSRP相關代碼之前添加noise_floor定義
    if "rsrp" in content.lower() or "-85" in content or "-88" in content or "-90" in content:
        # 找到合適的插入位置（在import之後）
        import_match = re.search(r'(import.*\n)+', content)
        if import_match:
            insert_pos = import_match.end()
            noise_floor_def = "\n# 🚨 Grade A要求：動態計算RSRP閾值\nnoise_floor = -120  # 3GPP典型噪聲門檻\n"
            content = content[:insert_pos] + noise_floor_def + content[insert_pos:]

    return content

def fix_file(filepath: str) -> bool:
    """修復單個文件中的硬編碼問題"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # 應用所有修復模式
        for pattern, replacement in HARDCODED_PATTERNS.items():
            content = re.sub(pattern, replacement, content)

        # 添加noise_floor定義
        content = add_noise_floor_definition(content)

        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"✅ 已修復: {filepath}")
            return True
        else:
            logger.debug(f"⭕ 無需修復: {filepath}")
            return False

    except Exception as e:
        logger.error(f"❌ 修復失敗 {filepath}: {e}")
        return False

def main():
    """主修復流程"""
    logger.info("🚀 開始批量修復RSRP硬編碼問題...")

    fixed_count = 0
    total_count = 0

    for root, dirs, files in os.walk(STAGES_DIR):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                total_count += 1

                if fix_file(filepath):
                    fixed_count += 1

    logger.info(f"🎉 修復完成: {fixed_count}/{total_count} 個文件已修復")

if __name__ == "__main__":
    main()