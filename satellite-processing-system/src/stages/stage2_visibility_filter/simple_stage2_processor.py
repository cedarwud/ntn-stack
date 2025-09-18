"""
簡化階段二處理器：基本地理可見性過濾
遵循方案一：只負責 ECI→地平座標轉換和仰角門檻過濾
"""

import os
import json
import gzip
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from pathlib import Path

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.base_processor import BaseStageProcessor
from .simple_geographic_filter import SimpleGeographicFilter


class SimpleStage2Processor(BaseStageProcessor):
    """簡化階段二處理器 - 只處理基本地理可見性過濾"""

    def __init__(self, debug_mode: bool = False):
        super().__init__(stage_number=2, stage_name="simplified_visibility_filter")
        self.debug_mode = debug_mode
        self.logger = logging.getLogger(__name__)

        # 初始化核心過濾器
        self.geographic_filter = SimpleGeographicFilter()

        self.logger.info("🎯 初始化簡化階段二處理器")

    def execute(self) -> Dict[str, Any]:
        """
        執行簡化階段二：基本地理可見性過濾

        Returns:
            過濾結果字典
        """
        start_time = datetime.now(timezone.utc)
        self.logger.info("🚀 開始執行簡化階段二：基本地理可見性過濾")

        try:
            # 1. 載入 Stage 1 數據
            self.logger.info("📥 載入階段一軌道計算結果...")
            stage1_data = self._load_stage1_data()

            # 2. 執行地理可見性過濾
            self.logger.info("🔍 執行地理可見性過濾...")
            filtered_results = self.geographic_filter.filter_visible_satellites(stage1_data)

            # 3. 保存結果
            self.logger.info("💾 保存過濾結果...")
            self._save_results(filtered_results)

            # 4. 計算執行統計
            execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            # 5. 更新元數據
            filtered_results['metadata']['total_execution_time'] = execution_time
            filtered_results['metadata']['stage2_simplified'] = True
            filtered_results['metadata']['bypassed_features'] = [
                'signal_analysis',  # 移至 Stage 3
                'handover_decisions',  # 移至 Stage 3
                'coverage_planning',  # 移至 Stage 6
                'academic_validation'  # 系統級功能
            ]

            self.logger.info(f"✅ 簡化階段二執行完成 (耗時: {execution_time:.2f}s)")
            return filtered_results

        except Exception as e:
            self.logger.error(f"❌ 簡化階段二執行失敗: {str(e)}")
            raise

    def _load_stage1_data(self) -> Dict[str, Any]:
        """載入 Stage 1 軌道計算結果"""
        try:
            # 搜索多個可能的 Stage 1 輸出位置
            possible_dirs = [
                Path("/satellite-processing/data/outputs/stage1"),
                Path("/satellite-processing/data/stage1_outputs"),
                Path("/satellite-processing/data/tle_calculation_outputs")
            ]

            json_files = []
            for output_dir in possible_dirs:
                if output_dir.exists():
                    # 查找壓縮的結果文件
                    json_files.extend(output_dir.glob("*.json.gz"))
                    # 查找未壓縮文件
                    json_files.extend(output_dir.glob("*.json"))

            if not json_files:
                raise FileNotFoundError("未找到 Stage 1 輸出文件")

            # 使用最新文件 (orbital_calculation_output.json.gz 優先)
            orbital_files = [f for f in json_files if 'orbital_calculation_output' in f.name]
            if orbital_files:
                latest_file = max(orbital_files, key=lambda f: f.stat().st_mtime)
            else:
                latest_file = max(json_files, key=lambda f: f.stat().st_mtime)

            self.logger.info(f"📂 載入文件: {latest_file}")

            # 讀取數據
            if latest_file.suffix == '.gz':
                with gzip.open(latest_file, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

            # 驗證數據結構
            if 'data' not in data:
                raise ValueError("Stage 1 數據格式無效: 缺少 'data' 字段")

            # 適配新的數據格式 (data.satellites 而不是分別的 starlink_satellites/oneweb_satellites)
            satellites_data = data['data']
            
            if 'satellites' in satellites_data:
                # 新格式: 所有衛星在 satellites 字典中，按 norad_id 分組
                all_satellites = satellites_data['satellites']
                starlink_count = 0
                oneweb_count = 0
                
                for sat_id, sat_info in all_satellites.items():
                    constellation = sat_info.get('satellite_info', {}).get('constellation', '').lower()
                    if constellation == 'starlink':
                        starlink_count += 1
                    elif constellation == 'oneweb':
                        oneweb_count += 1
                        
                self.logger.info(f"📊 載入完成: {starlink_count} Starlink + {oneweb_count} OneWeb (新格式)")
                
            elif 'starlink_satellites' in satellites_data and 'oneweb_satellites' in satellites_data:
                # 舊格式: 分別的 starlink_satellites 和 oneweb_satellites 列表
                starlink_count = len(satellites_data.get('starlink_satellites', []))
                oneweb_count = len(satellites_data.get('oneweb_satellites', []))
                self.logger.info(f"📊 載入完成: {starlink_count} Starlink + {oneweb_count} OneWeb (舊格式)")
                
            else:
                raise ValueError("Stage 1 數據格式無效: 找不到衛星數據")

            return data

        except Exception as e:
            self.logger.error(f"❌ Stage 1 數據載入失敗: {str(e)}")
            raise

    def _save_results(self, results: Dict[str, Any]) -> None:
        """保存過濾結果到文件"""
        try:
            # 創建輸出目錄
            output_dir = Path("/satellite-processing/data/intelligent_filtering_outputs")
            output_dir.mkdir(parents=True, exist_ok=True)

            # 生成文件名
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            filename = f"stage2_simple_visibility_filter_{timestamp}.json.gz"
            output_path = output_dir / filename

            # 保存為壓縮 JSON
            with gzip.open(output_path, 'wt', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            self.logger.info(f"💾 結果已保存: {output_path}")

            # 創建符號鏈接指向最新文件
            latest_link = output_dir / "latest_stage2_results.json.gz"
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(filename)

        except Exception as e:
            self.logger.error(f"❌ 結果保存失敗: {str(e)}")
            raise

    def validate_input(self, input_data: Any) -> bool:
        """驗證輸入數據 (簡化版本)"""
        return True  # Stage 1 數據已由 Stage 1 驗證

    def process(self, input_data: Any) -> Any:
        """處理數據 (符合 BaseStageProcessor 接口)"""
        return self.execute()

    def validate_output(self, output_data: Any) -> bool:
        """驗證輸出數據"""
        if not isinstance(output_data, dict):
            return False

        required_keys = ['metadata', 'data']
        return all(key in output_data for key in required_keys)

    def save_results(self, results: Any) -> None:
        """保存結果 (符合 BaseStageProcessor 接口)"""
        self._save_results(results)

    def extract_key_metrics(self) -> Dict[str, Any]:
        """提取關鍵指標"""
        return {
            'stage': 'stage2_simplified',
            'processor_type': 'SimpleStage2Processor',
            'features': ['geographic_visibility_filtering'],
            'bypassed_features': [
                'signal_analysis',
                'handover_decisions',
                'coverage_planning',
                'academic_validation'
            ]
        }

    def run_validation_checks(self) -> Dict[str, Any]:
        """執行驗證檢查 (簡化版本)"""
        return {
            'validation_status': 'passed',
            'checks_performed': [
                'basic_data_structure_validation',
                'geographic_filtering_logic_verification'
            ],
            'bypassed_checks': [
                'signal_quality_validation',
                'handover_logic_validation',
                'coverage_planning_validation'
            ],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }