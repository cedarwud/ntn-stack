#!/usr/bin/env python3
"""
統一日誌管理器
統一管理六階段處理的日誌和報告輸出
"""

import json
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
import uuid

class UnifiedLogManager:
    """統一日誌管理器"""
    
    def __init__(self, project_root: str = "/home/sat/ntn-stack", container_data_dir: str = "/app/data"):
        """
        初始化統一日誌管理器
        
        Args:
            project_root: 項目根目錄
            container_data_dir: 容器內數據目錄
        """
        self.project_root = Path(project_root)
        self.container_data_dir = Path(container_data_dir)
        
        # 創建 logs 目錄結構
        self.logs_dir = self.project_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # 子目錄結構
        self.execution_logs_dir = self.logs_dir / "execution"
        self.stage_reports_dir = self.logs_dir / "stage_reports" 
        self.validation_logs_dir = self.logs_dir / "validation"
        self.summary_reports_dir = self.logs_dir / "summary"
        
        # 創建所有子目錄
        for dir_path in [self.execution_logs_dir, self.stage_reports_dir, 
                        self.validation_logs_dir, self.summary_reports_dir]:
            dir_path.mkdir(exist_ok=True)
            
        # 當前執行ID
        self.execution_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.execution_start_time = datetime.now(timezone.utc)
        
        # 日誌配置
        self.logger = logging.getLogger(f"unified_log_manager_{self.execution_id}")
        
        # 執行狀態追蹤
        self.execution_status = {
            'execution_id': self.execution_id,
            'start_time': self.execution_start_time.isoformat(),
            'tle_sources': {},
            'stage_results': {},
            'validation_results': {},
            'total_processing_time': 0
        }
        
    def clear_old_logs(self):
        """清理舊的日誌和報告"""
        print("🗑️ 清理舊的日誌和報告...")
        
        # 清理 logs 目錄下的舊文件
        for subdir in [self.execution_logs_dir, self.stage_reports_dir, 
                      self.validation_logs_dir, self.summary_reports_dir]:
            if subdir.exists():
                for file in subdir.glob("*"):
                    try:
                        if file.is_file():
                            file.unlink()
                        elif file.is_dir():
                            shutil.rmtree(file)
                        print(f"   ✅ 已刪除: {file}")
                    except Exception as e:
                        print(f"   ⚠️ 刪除失敗: {file} - {e}")
        
        # 清理容器內的舊報告文件
        old_reports = [
            ".build_status",
            ".build_validation_status", 
            ".final_build_report.json",
            ".build_summary.txt"
        ]
        
        for report_file in old_reports:
            report_path = self.container_data_dir / report_file
            if report_path.exists():
                try:
                    report_path.unlink()
                    print(f"   ✅ 已刪除舊報告: {report_file}")
                except Exception as e:
                    print(f"   ⚠️ 刪除失敗: {report_file} - {e}")
                    
        print("✅ 舊日誌清理完成")
        
    def initialize_execution_log(self, tle_sources: Dict[str, str]):
        """
        初始化執行日誌
        
        Args:
            tle_sources: TLE數據來源字典 {'starlink': 'starlink_20241201.tle', 'oneweb': 'oneweb_20241201.tle'}
        """
        self.execution_status['tle_sources'] = tle_sources
        
        # 寫入執行開始日誌
        execution_log = self.execution_logs_dir / f"execution_{self.execution_id}.log"
        with open(execution_log, 'w', encoding='utf-8') as f:
            f.write(f"📊 六階段數據處理執行日誌\n")
            f.write(f"=" * 50 + "\n")
            f.write(f"🆔 執行ID: {self.execution_id}\n")
            f.write(f"⏰ 開始時間: {self.execution_start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            f.write(f"🛰️ 使用的TLE數據:\n")
            for constellation, tle_file in tle_sources.items():
                f.write(f"   {constellation.upper()}: {tle_file}\n")
            f.write("\n")
            
        print(f"📝 已初始化執行日誌: {execution_log}")
        
    def log_stage_start(self, stage_num: int, stage_name: str):
        """記錄階段開始"""
        stage_start_time = datetime.now(timezone.utc)
        
        self.execution_status['stage_results'][f'stage_{stage_num}'] = {
            'stage_name': stage_name,
            'start_time': stage_start_time.isoformat(),
            'status': 'running'
        }
        
        # 追加到執行日誌
        execution_log = self.execution_logs_dir / f"execution_{self.execution_id}.log"
        with open(execution_log, 'a', encoding='utf-8') as f:
            f.write(f"🚀 階段{stage_num}開始: {stage_name}\n")
            f.write(f"   開始時間: {stage_start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            
        print(f"🚀 階段{stage_num}開始: {stage_name}")
        
    def log_stage_completion(self, stage_num: int, stage_name: str, 
                           processing_results: Dict[str, Any], 
                           validation_passed: bool, validation_message: str):
        """
        記錄階段完成
        
        Args:
            stage_num: 階段編號
            stage_name: 階段名稱
            processing_results: 處理結果
            validation_passed: 驗證是否通過
            validation_message: 驗證訊息
        """
        stage_end_time = datetime.now(timezone.utc)
        stage_key = f'stage_{stage_num}'
        
        # 計算階段執行時間
        if stage_key in self.execution_status['stage_results']:
            start_time_str = self.execution_status['stage_results'][stage_key]['start_time']
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            duration_seconds = (stage_end_time - start_time).total_seconds()
            duration_minutes = duration_seconds / 60
        else:
            duration_minutes = 0
            
        # 更新執行狀態
        self.execution_status['stage_results'][stage_key].update({
            'end_time': stage_end_time.isoformat(),
            'duration_minutes': duration_minutes,
            'status': 'completed' if validation_passed else 'failed',
            'validation_passed': validation_passed,
            'validation_message': validation_message,
            'output_count': len(processing_results) if processing_results else 0
        })
        
        # 記錄驗證結果
        self.execution_status['validation_results'][stage_key] = {
            'passed': validation_passed,
            'message': validation_message,
            'timestamp': stage_end_time.isoformat()
        }
        
        # 寫入階段報告
        stage_report_file = self.stage_reports_dir / f"stage_{stage_num}_{self.execution_id}.json"
        stage_report = {
            'execution_id': self.execution_id,
            'stage_number': stage_num,
            'stage_name': stage_name,
            'start_time': self.execution_status['stage_results'][stage_key]['start_time'],
            'end_time': stage_end_time.isoformat(),
            'duration_minutes': duration_minutes,
            'processing_results_count': len(processing_results) if processing_results else 0,
            'validation': {
                'passed': validation_passed,
                'message': validation_message
            },
            'processing_summary': self._generate_processing_summary(processing_results)
        }
        
        with open(stage_report_file, 'w', encoding='utf-8') as f:
            json.dump(stage_report, f, ensure_ascii=False, indent=2)
            
        # 追加到執行日誌
        execution_log = self.execution_logs_dir / f"execution_{self.execution_id}.log"
        with open(execution_log, 'a', encoding='utf-8') as f:
            status_emoji = "✅" if validation_passed else "❌"
            f.write(f"{status_emoji} 階段{stage_num}完成: {stage_name}\n")
            f.write(f"   結束時間: {stage_end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            f.write(f"   執行時間: {duration_minutes:.2f} 分鐘\n")
            f.write(f"   驗證結果: {validation_message}\n")
            f.write(f"   輸出數量: {len(processing_results) if processing_results else 0}\n\n")
            
        print(f"{'✅' if validation_passed else '❌'} 階段{stage_num}完成 - {duration_minutes:.2f}分鐘")
        
    def generate_final_summary_report(self):
        """生成最終綜合報告"""
        end_time = datetime.now(timezone.utc)
        total_duration = (end_time - self.execution_start_time).total_seconds() / 60
        
        self.execution_status.update({
            'end_time': end_time.isoformat(),
            'total_processing_time': total_duration,
            'overall_status': self._determine_overall_status()
        })
        
        # 生成綜合報告
        summary_report = {
            'execution_metadata': {
                'execution_id': self.execution_id,
                'start_time': self.execution_start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'total_duration_minutes': total_duration,
                'report_generation_time': datetime.now(timezone.utc).isoformat()
            },
            'tle_data_sources': self.execution_status['tle_sources'],
            'stage_execution_summary': self.execution_status['stage_results'],
            'validation_summary': self.execution_status['validation_results'],
            'overall_status': self.execution_status['overall_status'],
            'statistics': self._generate_execution_statistics()
        }
        
        # 寫入JSON詳細報告
        summary_json = self.summary_reports_dir / f"final_summary_{self.execution_id}.json"
        with open(summary_json, 'w', encoding='utf-8') as f:
            json.dump(summary_report, f, ensure_ascii=False, indent=2)
            
        # 寫入人類可讀摘要
        summary_text = self.summary_reports_dir / f"final_summary_{self.execution_id}.txt"
        with open(summary_text, 'w', encoding='utf-8') as f:
            f.write(self._generate_human_readable_summary(summary_report))
            
        # 寫入執行日誌最終狀態
        execution_log = self.execution_logs_dir / f"execution_{self.execution_id}.log"
        with open(execution_log, 'a', encoding='utf-8') as f:
            f.write("=" * 50 + "\n")
            f.write(f"🏁 執行完成\n")
            f.write(f"⏰ 結束時間: {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            f.write(f"⏱️ 總執行時間: {total_duration:.2f} 分鐘\n")
            f.write(f"📊 整體狀態: {self.execution_status['overall_status']}\n")
            f.write("=" * 50 + "\n")
            
        print(f"📊 最終報告已生成:")
        print(f"   詳細報告: {summary_json}")
        print(f"   摘要報告: {summary_text}")
        print(f"   執行日誌: {execution_log}")
        
        return summary_report
        
    def _generate_processing_summary(self, processing_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成處理結果摘要"""
        if not processing_results:
            return {'status': 'no_results'}
            
        summary = {
            'total_items': len(processing_results),
            'has_data': bool(processing_results),
            'keys': list(processing_results.keys())[:10]  # 只記錄前10個鍵
        }
        
        # 如果是衛星數據，計算一些統計
        if isinstance(processing_results, dict) and 'satellites' in str(processing_results).lower():
            summary['data_type'] = 'satellite_data'
            
        return summary
        
    def _determine_overall_status(self) -> str:
        """確定整體執行狀態"""
        stage_results = self.execution_status['stage_results']
        validation_results = self.execution_status['validation_results']
        
        if not stage_results:
            return 'NO_EXECUTION'
            
        completed_stages = 0
        failed_stages = 0
        
        for stage_key, stage_data in stage_results.items():
            if stage_data.get('status') == 'completed':
                completed_stages += 1
            elif stage_data.get('status') == 'failed':
                failed_stages += 1
                
        total_expected = 6
        
        if completed_stages == total_expected:
            return 'FULLY_SUCCESS'
        elif completed_stages > 0:
            return f'PARTIAL_SUCCESS_{completed_stages}_{total_expected}'
        else:
            return 'COMPLETE_FAILURE'
            
    def _generate_execution_statistics(self) -> Dict[str, Any]:
        """生成執行統計資料"""
        stage_results = self.execution_status['stage_results']
        validation_results = self.execution_status['validation_results']
        
        stats = {
            'total_stages': len(stage_results),
            'completed_stages': sum(1 for s in stage_results.values() if s.get('status') == 'completed'),
            'failed_stages': sum(1 for s in stage_results.values() if s.get('status') == 'failed'),
            'validation_passed': sum(1 for v in validation_results.values() if v.get('passed')),
            'validation_failed': sum(1 for v in validation_results.values() if not v.get('passed')),
            'average_stage_duration': 0
        }
        
        # 計算平均執行時間
        durations = [s.get('duration_minutes', 0) for s in stage_results.values()]
        if durations:
            stats['average_stage_duration'] = sum(durations) / len(durations)
            
        return stats
        
    def _generate_human_readable_summary(self, summary_report: Dict[str, Any]) -> str:
        """生成人類可讀的摘要報告"""
        metadata = summary_report['execution_metadata']
        tle_sources = summary_report['tle_data_sources']
        stages = summary_report['stage_execution_summary']
        overall_status = summary_report['overall_status']
        stats = summary_report['statistics']
        
        lines = [
            "📊 六階段數據處理執行摘要報告",
            "=" * 60,
            f"🆔 執行ID: {metadata['execution_id']}",
            f"⏰ 執行時間: {metadata['start_time']} ~ {metadata['end_time']}",
            f"⏱️ 總耗時: {metadata['total_duration_minutes']:.2f} 分鐘",
            f"📊 整體狀態: {overall_status}",
            "",
            "🛰️ 使用的TLE數據源:",
        ]
        
        for constellation, tle_file in tle_sources.items():
            lines.append(f"   {constellation.upper()}: {tle_file}")
            
        lines.extend([
            "",
            "⚡ 各階段執行詳情:",
            "-" * 40
        ])
        
        for stage_key, stage_data in stages.items():
            stage_num = stage_key.split('_')[1]
            status_emoji = "✅" if stage_data.get('validation_passed') else "❌"
            lines.append(
                f"{status_emoji} 階段{stage_num}: {stage_data['stage_name']} "
                f"({stage_data.get('duration_minutes', 0):.2f}分鐘)"
            )
            
        lines.extend([
            "",
            "📈 執行統計:",
            f"   完成階段: {stats['completed_stages']}/{stats['total_stages']}",
            f"   驗證通過: {stats['validation_passed']}/{stats['validation_failed'] + stats['validation_passed']}",
            f"   平均耗時: {stats['average_stage_duration']:.2f} 分鐘/階段",
            "",
            "📁 相關檔案位置:",
            f"   詳細JSON報告: logs/summary/final_summary_{metadata['execution_id']}.json",
            f"   執行日誌: logs/execution/execution_{metadata['execution_id']}.log",
            f"   階段報告: logs/stage_reports/stage_*_{metadata['execution_id']}.json",
            "",
            f"📝 報告生成時間: {metadata['report_generation_time']}",
            "=" * 60
        ])
        
        return "\n".join(lines)

def create_unified_log_manager(project_root: str = "/home/sat/ntn-stack", 
                             container_data_dir: str = "/app/data") -> UnifiedLogManager:
    """創建統一日誌管理器實例"""
    return UnifiedLogManager(project_root, container_data_dir)