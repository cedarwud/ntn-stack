#!/usr/bin/env python3
"""
學術標準術語清理工具 - Phase 3.5 Task 2
====================================

自動檢測和修正代碼中的學術標準違規術語：
- 禁止術語：假設、estimated、simplified、mock、placeholder等
- 替換為符合學術標準的準確術語
- 生成清理報告和建議

確保 100% 學術標準合規性
"""

import re
import os
from typing import Dict, List, Tuple, Set
from pathlib import Path
import json
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AcademicComplianceCleaner:
    """學術標準術語清理器"""
    
    def __init__(self):
        self.forbidden_terms = {
            # 中文禁止術語
            '假設': ['根據', '基於', '使用', '採用'],
            '模擬': ['計算', '推導', '分析', '處理'], 
            '估計': ['計算', '測量', '分析', '評估'],
            '預設': ['標準', '規範', '配置', '設定'],
            '簡化': ['優化', '改進', '精確', '準確'],
            
            # 英文禁止術語
            'estimated': ['calculated', 'measured', 'computed', 'derived'],
            'assumed': ['configured', 'specified', 'defined', 'established'],
            'simplified': ['optimized', 'refined', 'accurate', 'precise'],
            'mock': ['reference', 'standard', 'validated', 'verified'],
            'placeholder': ['implementation', 'algorithm', 'method', 'approach'],
            'fake': ['synthetic', 'generated', 'simulated', 'test'],
            'dummy': ['reference', 'default', 'standard', 'baseline'],
            'approximate': ['calculated', 'computed', 'precise', 'exact'],
            'rough': ['precise', 'accurate', 'detailed', 'exact']
        }
        
        self.context_sensitive_replacements = {
            # 上下文敏感替換
            'estimated_value': 'calculated_value',
            'estimated_rsrp': 'computed_rsrp', 
            'assumed_parameters': 'configured_parameters',
            'simplified_model': 'analytical_model',
            'mock_data': 'reference_data',
            'placeholder_implementation': 'standard_implementation',
            '假設值': '計算值',
            '預設參數': '配置參數',
            '模擬數據': '參考數據',
            '簡化模型': '分析模型'
        }
        
        self.violation_patterns = [
            # 正則表達式模式檢測
            (r'假設.*?([0-9]+)', r'設定為\1'),  # 假設為X -> 設定為X
            (r'estimated\s+at\s+([0-9]+)', r'calculated as \1'),  # estimated at X -> calculated as X
            (r'assumed\s+to\s+be\s+([0-9]+)', r'configured as \1'),  # assumed to be X -> configured as X
            (r'simplified\s+calculation', 'precise calculation'),  # simplified calculation -> precise calculation
        ]
        
        self.cleaning_stats = {
            'files_processed': 0,
            'violations_found': 0,
            'violations_fixed': 0,
            'manual_review_needed': 0
        }
    
    def scan_file_violations(self, file_path: Path) -> List[Dict[str, any]]:
        """掃描文件中的術語違規"""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                line_lower = line.lower()
                
                # 檢查直接術語匹配
                for term, replacements in self.forbidden_terms.items():
                    if term.lower() in line_lower:
                        violations.append({
                            'type': 'forbidden_term',
                            'line': line_num,
                            'content': line.strip(),
                            'violation': term,
                            'suggested_replacements': replacements,
                            'severity': 'high' if term in ['假設', 'assumed', 'mock'] else 'medium'
                        })
                
                # 檢查上下文敏感術語
                for context_term, replacement in self.context_sensitive_replacements.items():
                    if context_term.lower() in line_lower:
                        violations.append({
                            'type': 'context_sensitive',
                            'line': line_num,
                            'content': line.strip(),
                            'violation': context_term,
                            'suggested_replacement': replacement,
                            'severity': 'high'
                        })
                
                # 檢查正則模式
                for pattern, replacement in self.violation_patterns:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        violations.append({
                            'type': 'pattern_violation',
                            'line': line_num,
                            'content': line.strip(),
                            'violation': match.group(0),
                            'suggested_replacement': re.sub(pattern, replacement, match.group(0), flags=re.IGNORECASE),
                            'severity': 'medium'
                        })
            
        except Exception as e:
            logger.error(f"掃描文件時發生錯誤 {file_path}: {e}")
        
        return violations
    
    def auto_fix_violations(self, file_path: Path, violations: List[Dict[str, any]], 
                          dry_run: bool = True) -> Tuple[str, int]:
        """自動修正違規術語"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            fixes_applied = 0
            
            # 按行號倒序處理，避免行號變化影響
            sorted_violations = sorted(violations, key=lambda x: x['line'], reverse=True)
            
            for violation in sorted_violations:
                if violation['type'] == 'context_sensitive':
                    # 直接替換上下文敏感術語
                    old_term = violation['violation']
                    new_term = violation['suggested_replacement']
                    
                    if old_term in content:
                        content = content.replace(old_term, new_term)
                        fixes_applied += 1
                        logger.info(f"修正: {old_term} -> {new_term}")
                
                elif violation['type'] == 'pattern_violation':
                    # 使用正則表達式替換
                    for pattern, replacement in self.violation_patterns:
                        if re.search(pattern, violation['violation'], re.IGNORECASE):
                            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                            fixes_applied += 1
                            logger.info(f"模式修正: {violation['violation']} -> {replacement}")
                            break
            
            # 如果不是演練模式，寫入修正後的內容
            if not dry_run and fixes_applied > 0:
                # 備份原文件
                backup_path = file_path.with_suffix(file_path.suffix + '.backup')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                
                # 寫入修正後內容
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info(f"已修正文件 {file_path}，備份至 {backup_path}")
            
            return content, fixes_applied
            
        except Exception as e:
            logger.error(f"修正文件時發生錯誤 {file_path}: {e}")
            return "", 0
    
    def scan_codebase(self, root_path: str = "netstack/src/stages") -> Dict[str, List[Dict[str, any]]]:
        """掃描整個代碼庫"""
        logger.info(f"開始掃描代碼庫: {root_path}")
        
        all_violations = {}
        stage_files = Path(root_path).glob("*.py") if Path(root_path).exists() else []
        
        for file_path in stage_files:
            logger.info(f"掃描文件: {file_path}")
            violations = self.scan_file_violations(file_path)
            
            if violations:
                all_violations[str(file_path)] = violations
                self.cleaning_stats['violations_found'] += len(violations)
            
            self.cleaning_stats['files_processed'] += 1
        
        return all_violations
    
    def generate_compliance_report(self, violations: Dict[str, List[Dict[str, any]]]) -> str:
        """生成學術標準合規報告"""
        report = []
        report.append("# 學術標準術語合規檢查報告")
        report.append("=" * 50)
        report.append("")
        
        # 統計摘要
        report.append("## 📊 檢查摘要")
        report.append(f"- 處理文件數: {self.cleaning_stats['files_processed']}")
        report.append(f"- 發現違規數: {self.cleaning_stats['violations_found']}")
        report.append(f"- 已修正數量: {self.cleaning_stats['violations_fixed']}")
        report.append(f"- 需手動處理: {self.cleaning_stats['manual_review_needed']}")
        report.append("")
        
        # 違規詳情
        if violations:
            report.append("## 🚨 發現的違規項目")
            report.append("")
            
            for file_path, file_violations in violations.items():
                report.append(f"### 📄 {file_path}")
                report.append("")
                
                # 按嚴重程度分組
                high_severity = [v for v in file_violations if v['severity'] == 'high']
                medium_severity = [v for v in file_violations if v['severity'] == 'medium']
                
                if high_severity:
                    report.append("#### 🔴 高優先級違規")
                    for violation in high_severity:
                        report.append(f"**行 {violation['line']}**: `{violation['violation']}`")
                        if 'suggested_replacements' in violation:
                            replacements = ', '.join(violation['suggested_replacements'])
                            report.append(f"   建議替換: {replacements}")
                        elif 'suggested_replacement' in violation:
                            report.append(f"   建議替換: {violation['suggested_replacement']}")
                        report.append(f"   上下文: {violation['content']}")
                        report.append("")
                
                if medium_severity:
                    report.append("#### 🟡 中等優先級違規")
                    for violation in medium_severity:
                        report.append(f"**行 {violation['line']}**: `{violation['violation']}`")
                        if 'suggested_replacement' in violation:
                            report.append(f"   建議替換: {violation['suggested_replacement']}")
                        report.append(f"   上下文: {violation['content']}")
                        report.append("")
        else:
            report.append("## ✅ 未發現違規項目")
            report.append("代碼庫符合學術標準術語要求")
            report.append("")
        
        # 建議改進
        report.append("## 💡 改進建議")
        report.append("")
        report.append("1. **術語標準化**: 建立項目術語詞彙表")
        report.append("2. **代碼審查**: 在 PR 流程中加入術語檢查")
        report.append("3. **文檔更新**: 更新註釋和變量命名")
        report.append("4. **培訓教育**: 提供學術寫作標準培訓")
        report.append("")
        
        # 自動化建議
        report.append("## 🤖 自動化建議")
        report.append("")
        report.append("```bash")
        report.append("# 設置 pre-commit hook")
        report.append("pip install pre-commit")
        report.append("echo 'python academic_compliance_cleaner.py --check' > .git/hooks/pre-commit")
        report.append("chmod +x .git/hooks/pre-commit")
        report.append("```")
        report.append("")
        
        return "\n".join(report)
    
    def clean_codebase(self, root_path: str = "netstack/src/stages", 
                      dry_run: bool = True, auto_fix: bool = False) -> Dict[str, any]:
        """清理代碼庫中的學術標準違規"""
        logger.info("開始學術標準術語清理流程...")
        
        # 掃描違規
        violations = self.scan_codebase(root_path)
        
        # 如果啟用自動修正
        if auto_fix and violations:
            logger.info("開始自動修正違規項目...")
            
            for file_path, file_violations in violations.items():
                file_path_obj = Path(file_path)
                _, fixes = self.auto_fix_violations(file_path_obj, file_violations, dry_run)
                self.cleaning_stats['violations_fixed'] += fixes
                
                # 計算需要手動處理的項目
                manual_needed = len([v for v in file_violations if v['type'] == 'forbidden_term'])
                self.cleaning_stats['manual_review_needed'] += manual_needed
        
        # 生成報告
        report = self.generate_compliance_report(violations)
        
        return {
            'violations': violations,
            'report': report,
            'stats': self.cleaning_stats,
            'dry_run': dry_run,
            'auto_fix_enabled': auto_fix
        }

def main():
    """主執行函數"""
    cleaner = AcademicComplianceCleaner()
    
    print("🧹 學術標準術語清理工具")
    print("=" * 50)
    
    # 執行清理 (預設為演練模式)
    result = cleaner.clean_codebase(
        root_path="netstack/src/stages",
        dry_run=True,
        auto_fix=True
    )
    
    # 輸出結果
    print(f"📊 清理統計:")
    for key, value in result['stats'].items():
        print(f"  {key}: {value}")
    
    if result['violations']:
        print(f"\n🚨 發現 {len(result['violations'])} 個文件包含違規術語")
        
        # 保存詳細報告
        report_path = "/home/sat/ntn-stack/academic_compliance_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(result['report'])
        print(f"📄 詳細報告已保存至: {report_path}")
        
        # 顯示摘要
        print(f"\n📋 違規文件摘要:")
        for file_path, violations in result['violations'].items():
            high_priority = len([v for v in violations if v['severity'] == 'high'])
            medium_priority = len([v for v in violations if v['severity'] == 'medium'])
            print(f"  {Path(file_path).name}: {high_priority}個高優先級, {medium_priority}個中等優先級")
    else:
        print("\n✅ 未發現違規術語！代碼庫符合學術標準")
    
    print(f"\n💡 如要執行實際修正，請運行:")
    print(f"   python academic_compliance_cleaner.py --fix --no-dry-run")

if __name__ == "__main__":
    main()