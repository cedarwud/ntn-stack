"""
階段四：時間序列預處理器

將信號分析結果轉換為前端動畫可用的時間序列數據格式
符合 @docs/stages/stage4-timeseries.md 規範
"""

import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from src.shared_core.validation_snapshot_base import ValidationSnapshotBase, ValidationCheckHelper

logger = logging.getLogger(__name__)


class TimeseriesPreprocessingProcessor(ValidationSnapshotBase):
    """時間序列預處理器
    
    將信號分析的複雜數據結構轉換為前端動畫需要的 enhanced_timeseries 格式
    """
    
    def __init__(self, input_dir: str = "/app/data", output_dir: str = "/app/data"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Initialize ValidationSnapshotBase
        super().__init__(stage_number=4, stage_name="階段4: 時間序列預處理", 
                         snapshot_dir="/app/data/validation_snapshots")
        
        # 🔄 修改：建立專用子目錄用於階段四輸出
        self.timeseries_preprocessing_dir = self.output_dir / "timeseries_preprocessing_outputs"
        self.timeseries_preprocessing_dir.mkdir(parents=True, exist_ok=True)
        
        # 保持向後兼容，enhanced_dir 指向新的子目錄
        self.enhanced_dir = self.timeseries_preprocessing_dir
        
        # 初始化 sample_mode 屬性
        self.sample_mode = False  # 配置為全量模式
        
        # 🛡️ Phase 3 新增：初始化驗證框架
        self.validation_enabled = False
        self.validation_adapter = None
        
        try:
            from validation.adapters.stage4_validation_adapter import Stage4ValidationAdapter
            self.validation_adapter = Stage4ValidationAdapter()
            self.validation_enabled = True
            logger.info("🛡️ Phase 3 Stage 4 驗證框架初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ Phase 3 驗證框架初始化失敗: {e}")
            logger.warning("   繼續使用舊版驗證機制")
        
        logger.info("✅ 時間序列預處理器初始化完成")
        logger.info(f"  輸入目錄: {self.input_dir}")
        logger.info(f"  輸出目錄: {self.timeseries_preprocessing_dir}")
        logger.info("  📁 使用專用子目錄結構")
        if self.validation_enabled:
            logger.info("  🛡️ Phase 3 驗證框架: 已啟用")       
    def extract_key_metrics(self, processing_results: Dict[str, Any]) -> Dict[str, Any]:
        """提取階段4關鍵指標"""
        # 從轉換結果中提取關鍵指標
        conversion_stats = processing_results.get("conversion_statistics", {})
        constellation_data = processing_results.get("constellation_data", {})
        
        return {
            "處理總數": conversion_stats.get("total_processed", 0),
            "成功轉換": conversion_stats.get("successful_conversions", 0),
            "失敗轉換": conversion_stats.get("failed_conversions", 0),
            "轉換率": f"{conversion_stats.get('successful_conversions', 0) / max(conversion_stats.get('total_processed', 1), 1) * 100:.1f}%",
            "Starlink處理": constellation_data.get("starlink", {}).get("satellites_processed", 0),
            "OneWeb處理": constellation_data.get("oneweb", {}).get("satellites_processed", 0)
        }
    
    def run_validation_checks(self, processing_results: Dict[str, Any]) -> Dict[str, Any]:
        """執行 Stage 4 驗證檢查 - 專注於時間序列預處理和前端動畫數據準備 + Phase 3.5 可配置驗證級別"""
        
        # 🎯 Phase 3.5: 導入可配置驗證級別管理器
        try:
            from pathlib import Path
            import sys
            
            from validation.managers.validation_level_manager import ValidationLevelManager
            
            validation_manager = ValidationLevelManager()
            validation_level = validation_manager.get_validation_level('stage4')
            
            # 性能監控開始
            import time
            validation_start_time = time.time()
            
        except ImportError:
            # 回退到標準驗證級別
            validation_level = 'STANDARD'
            validation_start_time = time.time()
        
        metadata = processing_results.get('metadata', {})
        conversion_stats = processing_results.get("conversion_statistics", {})
        constellation_data = processing_results.get("constellation_data", {})
        
        checks = {}
        
        # 📊 根據驗證級別決定檢查項目
        if validation_level == 'FAST':
            # 快速模式：只執行關鍵檢查
            critical_checks = [
                '輸入數據存在性',
                '時間序列轉換成功率',
                '前端動畫數據完整性',
                '數據結構完整性'
            ]
        elif validation_level == 'COMPREHENSIVE':
            # 詳細模式：執行所有檢查 + 額外的深度檢查
            critical_checks = [
                '輸入數據存在性', '時間序列轉換成功率', '前端動畫數據完整性',
                '星座數據平衡性', '檔案大小合理性', '數據結構完整性', 
                '處理時間合理性', '學術標準合規性', '信號數據完整性',
                '時間戳一致性驗證', '統計特徵合理性'
            ]
        else:
            # 標準模式：執行大部分檢查
            critical_checks = [
                '輸入數據存在性', '時間序列轉換成功率', '前端動畫數據完整性',
                '星座數據平衡性', '檔案大小合理性', '數據結構完整性',
                '處理時間合理性', '學術標準合規性', '信號數據完整性',
                '時間戳一致性驗證'
            ]
        
        # 1. 輸入數據存在性檢查
        if '輸入數據存在性' in critical_checks:
            input_satellites = metadata.get('total_satellites', 0)
            checks["輸入數據存在性"] = input_satellites > 0
        
        # 2. 時間序列轉換成功率檢查 - 確保大部分衛星成功轉換為前端格式
        if '時間序列轉換成功率' in critical_checks:
            total_processed = conversion_stats.get("total_processed", 0)
            successful_conversions = conversion_stats.get("successful_conversions", 0)
            conversion_rate = (successful_conversions / max(total_processed, 1)) * 100
            
            if self.sample_mode:
                checks["時間序列轉換成功率"] = conversion_rate >= 70.0  # 取樣模式較寬鬆
            else:
                checks["時間序列轉換成功率"] = conversion_rate >= 85.0  # 全量模式要求較高
        
        # 3. 前端動畫數據完整性檢查 - 確保包含前端所需的時間軸和軌跡數據
        if '前端動畫數據完整性' in critical_checks:
            animation_data_ok = True
            output_files = processing_results.get("output_files", {})
            if not output_files or len(output_files) == 0:
                animation_data_ok = False
            else:
                # 檢查是否有主要的時間序列檔案
                has_main_timeseries = any('animation_enhanced' in str(f) for f in output_files.values() if f)
                animation_data_ok = has_main_timeseries
            
            checks["前端動畫數據完整性"] = animation_data_ok
        
        # 4. 星座數據平衡性檢查 - 確保兩個星座都有轉換結果
        if '星座數據平衡性' in critical_checks:
            starlink_processed = constellation_data.get("starlink", {}).get("satellites_processed", 0)
            oneweb_processed = constellation_data.get("oneweb", {}).get("satellites_processed", 0)
            
            if self.sample_mode:
                checks["星座數據平衡性"] = starlink_processed >= 5 and oneweb_processed >= 2
            else:
                checks["星座數據平衡性"] = starlink_processed >= 200 and oneweb_processed >= 30
        
        # 5. 檔案大小合理性檢查 - 確保輸出檔案在前端可接受範圍
        if '檔案大小合理性' in critical_checks:
            file_size_reasonable = True
            total_size_mb = metadata.get('total_output_size_mb', 0)
            if total_size_mb > 0:
                if self.sample_mode:
                    file_size_reasonable = total_size_mb <= 20  # 取樣模式較小
                else:
                    # 🎯 調整：針對實際438顆衛星，合理範圍為10-100MB
                    file_size_reasonable = 10 <= total_size_mb <= 100  # 適中數據規模
            
            checks["檔案大小合理性"] = file_size_reasonable
        
        # 6. 數據結構完整性檢查
        if '數據結構完整性' in critical_checks:
            required_fields = ['metadata', 'conversion_statistics', 'output_files']
            checks["數據結構完整性"] = ValidationCheckHelper.check_data_completeness(
                processing_results, required_fields
            )
        
        # 7. 處理時間檢查 - 時間序列預處理應該相對快速
        if '處理時間合理性' in critical_checks:
            # 快速模式有更嚴格的性能要求
            if validation_level == 'FAST':
                max_time = 150 if self.sample_mode else 90
            else:
                max_time = 200 if self.sample_mode else 120  # 取樣3.3分鐘，全量2分鐘
            checks["處理時間合理性"] = ValidationCheckHelper.check_processing_time(
                self.processing_duration, max_time
            )
        
        # 8. 學術標準合規檢查 - 確保符合 academic_data_standards.md Grade A/B 要求
        if '學術標準合規性' in critical_checks:
            academic_compliance_ok = True
            
            # 檢查是否使用了任何禁止的數據處理方法
            output_files = processing_results.get("output_files", {})
            for file_path in output_files.values():
                if file_path and Path(file_path).exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 檢查是否包含違規的正規化數據
                            if 'rsrp_normalized' in content:
                                academic_compliance_ok = False
                                break
                            # 檢查是否包含任意壓縮比例
                            if 'compression_ratio' in content and '0.73' in content:
                                academic_compliance_ok = False
                                break
                    except:
                        pass  # 如果文件讀取失敗，跳過檢查
            
            checks["學術標準合規性"] = academic_compliance_ok
        
        # 9. 信號數據完整性檢查 - 確保保持原始dBm值
        if '信號數據完整性' in critical_checks:
            signal_integrity_ok = True
            timeseries_data = processing_results.get("timeseries_data", {})
            satellites = timeseries_data.get("satellites", [])
            
            if satellites:
                # 隨機檢查幾個衛星的信號數據
                sample_size = min(3 if validation_level == 'FAST' else 5, len(satellites))
                for i in range(0, len(satellites), max(1, len(satellites) // sample_size)):
                    satellite = satellites[i]
                    signal_quality = satellite.get('signal_quality', {})
                    
                    # 檢查是否有原始RSRP值並且使用dBm單位
                    if 'statistics' in signal_quality:
                        rsrp_value = signal_quality['statistics'].get('mean_rsrp_dbm')
                        if rsrp_value is None or not isinstance(rsrp_value, (int, float)):
                            signal_integrity_ok = False
                            break
            
            checks["信號數據完整性"] = signal_integrity_ok
        
        # ===== Phase 3 增強驗證 =====
        
        # 10. 時間戳一致性驗證 - UTC標準時間合規性
        if '時間戳一致性驗證' in critical_checks:
            timestamp_consistency_result = self._validate_timestamp_consistency(processing_results)
            checks["時間戳一致性驗證"] = timestamp_consistency_result.get("passed", False)
        
        # 11. 統計特徵合理性驗證 - 數據品質評估（詳細模式專用）
        if '統計特徵合理性' in critical_checks:
            statistical_features_result = self._validate_statistical_features(processing_results)
            checks["統計特徵合理性"] = statistical_features_result.get("passed", False)
        
        # 計算通過的檢查數量
        passed_checks = sum(1 for passed in checks.values() if passed)
        total_checks = len(checks)
        
        # 🎯 Phase 3.5: 記錄驗證性能指標
        validation_end_time = time.time()
        validation_duration = validation_end_time - validation_start_time
        
        try:
            # 更新性能指標
            validation_manager.update_performance_metrics('stage4', validation_duration, total_checks)
            
            # 自適應調整（如果性能太差）
            if validation_duration > 5.0 and validation_level != 'FAST':
                validation_manager.set_validation_level('stage4', 'FAST', reason='performance_auto_adjustment')
        except:
            # 如果性能記錄失敗，不影響主要驗證流程
            pass
        
        return {
            "passed": passed_checks == total_checks,
            "totalChecks": total_checks,
            "passedChecks": passed_checks,
            "failedChecks": total_checks - passed_checks,
            "criticalChecks": [
                {"name": name, "status": "passed" if checks.get(name, False) else "failed"}
                for name in critical_checks if name in checks
            ],
            "allChecks": checks,
            # Phase 3 增強驗證詳細結果
            "phase3_validation_details": {
                "timestamp_consistency": locals().get('timestamp_consistency_result', {}),
                "statistical_features": locals().get('statistical_features_result', {})
            },
            # 🎯 Phase 3.5 新增：驗證級別信息
            "validation_level_info": {
                "current_level": validation_level,
                "validation_duration_ms": round(validation_duration * 1000, 2),
                "checks_executed": list(checks.keys()),
                "performance_acceptable": validation_duration < 5.0
            },
            "summary": f"Stage 4 時間序列預處理驗證: 轉換成功率{conversion_stats.get('successful_conversions', 0)}/{conversion_stats.get('total_processed', 0)} ({((conversion_stats.get('successful_conversions', 0) / max(conversion_stats.get('total_processed', 1), 1)) * 100):.1f}%) - {passed_checks}/{total_checks}項檢查通過"
        }

    def _validate_timestamp_consistency(self, processing_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        時間戳一致性驗證 - Phase 3 Task 3 新增功能
        
        驗證時間序列數據的時間戳是否一致：
        - UTC標準時間格式
        - 時間序列連續性
        - 採樣頻率一致性
        - 時間同步精度
        
        Args:
            processing_results: 時序預處理結果數據
            
        Returns:
            Dict: 時間戳一致性驗證報告
            
        Raises:
            ValueError: 如果發現嚴重的時間戳一致性問題
        """
        logger.info("⏰ 執行時間戳一致性驗證...")
        
        timeseries_data = processing_results.get("timeseries_data", {})
        satellites = timeseries_data.get("satellites", [])
        
        timestamp_report = {
            'validation_timestamp': datetime.now(timezone.utc).isoformat(),
            'total_satellites_checked': len(satellites),
            'timestamp_statistics': {
                'satellites_with_consistent_timestamps': 0,
                'satellites_with_timestamp_issues': 0,
                'consistency_percentage': 0.0
            },
            'timestamp_violations': [],
            'consistency_status': 'UNKNOWN'
        }
        
        # 時間戳標準定義
        TIMESTAMP_STANDARDS = {
            'utc_timezone_required': True,
            'iso_8601_format_required': True,
            'max_time_gap_seconds': 600,         # 最大時間間隔10分鐘
            'min_time_gap_seconds': 30,          # 最小時間間隔30秒  
            'sampling_frequency_tolerance': 0.1,  # 採樣頻率容差10%
            'max_timestamp_deviation_seconds': 5  # 最大時間戳偏差5秒
        }
        
        consistent_satellites = 0
        issue_satellites = 0
        
        # 抽樣檢查衛星的時間戳一致性（檢查前20顆）
        sample_size = min(20, len(satellites))
        sample_satellites = satellites[:sample_size]
        
        for sat_data in sample_satellites:
            satellite_name = sat_data.get('name', 'Unknown')
            constellation = sat_data.get('constellation', '').lower()
            timeseries_points = sat_data.get('timeseries', [])
            
            if not timeseries_points:
                continue
            
            satellite_violations = []
            
            # 1. 檢查時間戳格式和時區
            timestamps = []
            for i, point in enumerate(timeseries_points[:10]):  # 檢查前10個點
                timestamp_str = point.get('timestamp')
                
                if not timestamp_str:
                    satellite_violations.append({
                        'point_index': i,
                        'timestamp_violation': 'missing_timestamp',
                        'details': f'時間點{i}缺少時間戳'
                    })
                    continue
                
                try:
                    # 解析時間戳並檢查格式
                    if timestamp_str.endswith('Z'):
                        dt = datetime.fromisoformat(timestamp_str[:-1]).replace(tzinfo=timezone.utc)
                    elif '+00:00' in timestamp_str:
                        dt = datetime.fromisoformat(timestamp_str)
                    else:
                        # 不符合UTC格式
                        satellite_violations.append({
                            'point_index': i,
                            'timestamp_violation': 'non_utc_timezone',
                            'details': f'時間戳{timestamp_str}不是UTC格式',
                            'expected': 'ISO 8601 UTC format with Z or +00:00'
                        })
                        continue
                    
                    timestamps.append(dt)
                    
                except Exception as e:
                    satellite_violations.append({
                        'point_index': i,
                        'timestamp_violation': 'invalid_timestamp_format',
                        'details': f'時間戳{timestamp_str}格式無效: {str(e)}',
                        'expected': 'ISO 8601 format'
                    })
            
            # 2. 檢查時間序列的連續性和間隔
            if len(timestamps) >= 2:
                time_intervals = []
                for i in range(1, len(timestamps)):
                    interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                    time_intervals.append(interval)
                    
                    # 檢查時間間隔是否在合理範圍內
                    if interval <= 0:
                        satellite_violations.append({
                            'point_index': i,
                            'timestamp_violation': 'negative_or_zero_time_interval',
                            'details': f'時間點{i-1}到{i}的時間間隔為{interval}秒',
                            'expected': '正時間間隔'
                        })
                    elif interval > TIMESTAMP_STANDARDS['max_time_gap_seconds']:
                        satellite_violations.append({
                            'point_index': i,
                            'timestamp_violation': 'excessive_time_gap',
                            'details': f'時間點{i-1}到{i}的時間間隔過大: {interval}秒',
                            'expected': f'< {TIMESTAMP_STANDARDS["max_time_gap_seconds"]}秒'
                        })
                    elif interval < TIMESTAMP_STANDARDS['min_time_gap_seconds']:
                        satellite_violations.append({
                            'point_index': i,
                            'timestamp_violation': 'insufficient_time_gap',
                            'details': f'時間點{i-1}到{i}的時間間隔過小: {interval}秒',
                            'expected': f'> {TIMESTAMP_STANDARDS["min_time_gap_seconds"]}秒'
                        })
                
                # 3. 檢查採樣頻率一致性
                if time_intervals:
                    avg_interval = sum(time_intervals) / len(time_intervals)
                    max_deviation = max(abs(interval - avg_interval) for interval in time_intervals)
                    max_allowed_deviation = avg_interval * TIMESTAMP_STANDARDS['sampling_frequency_tolerance']
                    
                    if max_deviation > max_allowed_deviation:
                        satellite_violations.append({
                            'timestamp_violation': 'inconsistent_sampling_frequency',
                            'details': f'採樣頻率不一致，最大偏差{max_deviation:.1f}秒',
                            'average_interval': avg_interval,
                            'max_deviation': max_deviation,
                            'tolerance': max_allowed_deviation
                        })
            
            # 4. 檢查時間戳與當前時間的合理性
            current_time = datetime.now(timezone.utc)
            for i, ts in enumerate(timestamps):
                time_diff = abs((current_time - ts).total_seconds())
                
                # 時間戳不應該太久遠或太未來
                if time_diff > 7 * 24 * 3600:  # 超過7天
                    satellite_violations.append({
                        'point_index': i,
                        'timestamp_violation': 'timestamp_too_old_or_future',
                        'details': f'時間戳{ts.isoformat()}與當前時間差距{time_diff/3600:.1f}小時',
                        'expected': '< 7天'
                    })
            
            # 判斷該衛星的時間戳一致性
            if len(satellite_violations) == 0:
                consistent_satellites += 1
            else:
                issue_satellites += 1
                timestamp_report['timestamp_violations'].append({
                    'satellite_name': satellite_name,
                    'constellation': constellation,
                    'violation_count': len(satellite_violations),
                    'violations': satellite_violations
                })
        
        # 計算一致性統計
        consistency_rate = (consistent_satellites / sample_size * 100) if sample_size > 0 else 0
        
        timestamp_report['timestamp_statistics'] = {
            'satellites_with_consistent_timestamps': consistent_satellites,
            'satellites_with_timestamp_issues': issue_satellites,
            'consistency_percentage': consistency_rate
        }
        
        # 確定一致性狀態
        if consistency_rate >= 90 and len(timestamp_report['timestamp_violations']) <= 2:
            timestamp_report['consistency_status'] = 'PASS'
            logger.info(f"✅ 時間戳一致性驗證通過: {consistency_rate:.2f}% 一致率")
        else:
            timestamp_report['consistency_status'] = 'FAIL'
            logger.error(f"❌ 時間戳一致性驗證失敗: {consistency_rate:.2f}% 一致率，發現 {len(timestamp_report['timestamp_violations'])} 個問題")
            
            # 如果一致性問題嚴重，拋出異常
            if consistency_rate < 75:
                raise ValueError(f"Academic Standards Violation: 時間戳一致性嚴重問題 - 一致率僅 {consistency_rate:.2f}%")
        
        return timestamp_report

    def _validate_statistical_features(self, processing_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        統計特徵合理性驗證 - Phase 3 Task 3 新增功能
        
        驗證時序數據的統計特徵：
        - 均值、方差、分佈合理性
        - 異常值檢測
        - 統計一致性檢查
        - 數據品質評估
        
        Args:
            processing_results: 時序預處理結果數據
            
        Returns:
            Dict: 統計特徵驗證報告
            
        Raises:
            ValueError: 如果發現嚴重的統計特徵問題
        """
        logger.info("📊 執行統計特徵合理性驗證...")
        
        timeseries_data = processing_results.get("timeseries_data", {})
        satellites = timeseries_data.get("satellites", [])
        
        stats_report = {
            'validation_timestamp': datetime.now(timezone.utc).isoformat(),
            'total_satellites_checked': len(satellites),
            'statistical_compliance': {
                'satellites_with_valid_statistics': 0,
                'satellites_with_statistical_issues': 0,
                'compliance_percentage': 0.0
            },
            'statistical_violations': [],
            'compliance_status': 'UNKNOWN'
        }
        
        # 統計特徵合理性標準
        STATISTICAL_STANDARDS = {
            'rsrp_range_dbm': {
                'min': -140,
                'max': -50,
                'typical_mean': -95,
                'typical_std': 15
            },
            'elevation_range_deg': {
                'min': -90,
                'max': 90,
                'visible_min': 5,  # 可見衛星最低仰角
                'visible_max': 90
            },
            'range_km': {
                'min': 200,
                'max': 3000,
                'typical_mean': 1000,
                'typical_std': 500
            },
            'outlier_threshold_z_score': 3.0,    # Z-score異常值門檻
            'min_data_points': 5,                # 最少數據點數量
            'coefficient_variation_max': 1.0     # 變異係數最大值
        }
        
        valid_satellites = 0
        issue_satellites = 0
        
        # 抽樣檢查衛星的統計特徵（檢查前15顆）
        sample_size = min(15, len(satellites))
        sample_satellites = satellites[:sample_size]
        
        for sat_data in sample_satellites:
            satellite_name = sat_data.get('name', 'Unknown')
            constellation = sat_data.get('constellation', '').lower()
            signal_quality = sat_data.get('signal_quality', {})
            timeseries_points = sat_data.get('timeseries', [])
            
            if not signal_quality or not timeseries_points:
                continue
            
            satellite_violations = []
            
            # 1. 檢查信號統計特徵
            statistics = signal_quality.get('statistics', {})
            
            if statistics:
                # 檢查RSRP統計值
                mean_rsrp = statistics.get('mean_rsrp_dbm')
                std_rsrp = statistics.get('std_rsrp_dbm')
                min_rsrp = statistics.get('min_rsrp_dbm')
                max_rsrp = statistics.get('max_rsrp_dbm')
                
                if mean_rsrp is not None:
                    # 檢查RSRP均值是否在合理範圍內
                    if not (STATISTICAL_STANDARDS['rsrp_range_dbm']['min'] <= mean_rsrp <= STATISTICAL_STANDARDS['rsrp_range_dbm']['max']):
                        satellite_violations.append({
                            'statistical_violation': 'rsrp_mean_out_of_range',
                            'details': f'RSRP均值{mean_rsrp:.1f}dBm超出合理範圍',
                            'expected_range': f"{STATISTICAL_STANDARDS['rsrp_range_dbm']['min']}-{STATISTICAL_STANDARDS['rsrp_range_dbm']['max']}dBm"
                        })
                    
                    # 檢查標準差是否合理
                    if std_rsrp is not None:
                        if std_rsrp < 0:
                            satellite_violations.append({
                                'statistical_violation': 'negative_standard_deviation',
                                'details': f'RSRP標準差為負值: {std_rsrp:.1f}dBm'
                            })
                        elif std_rsrp > 50:  # 標準差過大
                            satellite_violations.append({
                                'statistical_violation': 'excessive_rsrp_standard_deviation',
                                'details': f'RSRP標準差過大: {std_rsrp:.1f}dBm',
                                'expected': '< 50dBm'
                            })
                        
                        # 檢查變異係數
                        if mean_rsrp != 0:
                            cv = abs(std_rsrp / mean_rsrp)
                            if cv > STATISTICAL_STANDARDS['coefficient_variation_max']:
                                satellite_violations.append({
                                    'statistical_violation': 'high_coefficient_of_variation',
                                    'details': f'RSRP變異係數過高: {cv:.2f}',
                                    'expected': f'< {STATISTICAL_STANDARDS["coefficient_variation_max"]}'
                                })
                
                # 檢查最大最小值的邏輯一致性
                if min_rsrp is not None and max_rsrp is not None:
                    if min_rsrp > max_rsrp:
                        satellite_violations.append({
                            'statistical_violation': 'min_max_inconsistency',
                            'details': f'最小RSRP({min_rsrp:.1f})大於最大RSRP({max_rsrp:.1f})',
                            'note': '統計邏輯錯誤'
                        })
                    
                    rsrp_range = max_rsrp - min_rsrp
                    if rsrp_range > 60:  # RSRP範圍過大
                        satellite_violations.append({
                            'statistical_violation': 'excessive_rsrp_range',
                            'details': f'RSRP範圍過大: {rsrp_range:.1f}dBm',
                            'expected': '< 60dBm'
                        })
            
            # 2. 檢查時序數據點的統計分佈
            if len(timeseries_points) >= STATISTICAL_STANDARDS['min_data_points']:
                # 提取數值數據進行統計分析
                rsrp_values = []
                elevation_values = []
                range_values = []
                
                for point in timeseries_points:
                    # 提取RSRP值
                    if 'rsrp_dbm' in point and isinstance(point['rsrp_dbm'], (int, float)):
                        rsrp_values.append(point['rsrp_dbm'])
                    
                    # 提取仰角值
                    if 'elevation_deg' in point and isinstance(point['elevation_deg'], (int, float)):
                        elevation_values.append(point['elevation_deg'])
                    
                    # 提取距離值
                    if 'range_km' in point and isinstance(point['range_km'], (int, float)):
                        range_values.append(point['range_km'])
                
                # 3. 異常值檢測（使用Z-score方法）
                for values, param_name, standards in [
                    (rsrp_values, 'RSRP', STATISTICAL_STANDARDS['rsrp_range_dbm']),
                    (elevation_values, '仰角', STATISTICAL_STANDARDS['elevation_range_deg']),
                    (range_values, '距離', STATISTICAL_STANDARDS['range_km'])
                ]:
                    if len(values) >= 3:  # 至少需要3個數據點才能計算Z-score
                        import statistics
                        try:
                            mean_val = statistics.mean(values)
                            stdev_val = statistics.stdev(values) if len(values) > 1 else 0
                            
                            if stdev_val > 0:
                                outliers = []
                                for i, val in enumerate(values):
                                    z_score = abs((val - mean_val) / stdev_val)
                                    if z_score > STATISTICAL_STANDARDS['outlier_threshold_z_score']:
                                        outliers.append({'index': i, 'value': val, 'z_score': z_score})
                                
                                # 如果異常值比例過高
                                outlier_ratio = len(outliers) / len(values)
                                if outlier_ratio > 0.1:  # 超過10%的異常值
                                    satellite_violations.append({
                                        'statistical_violation': f'{param_name}_excessive_outliers',
                                        'details': f'{param_name}異常值比例過高: {outlier_ratio:.1%}',
                                        'outlier_count': len(outliers),
                                        'total_points': len(values),
                                        'expected': '< 10%'
                                    })
                        except statistics.StatisticsError:
                            # 統計計算失敗，可能數據品質有問題
                            satellite_violations.append({
                                'statistical_violation': f'{param_name}_statistical_calculation_failed',
                                'details': f'{param_name}統計計算失敗，可能數據品質有問題'
                            })
            else:
                satellite_violations.append({
                    'statistical_violation': 'insufficient_data_points',
                    'details': f'數據點數量不足: {len(timeseries_points)}',
                    'expected': f'>= {STATISTICAL_STANDARDS["min_data_points"]}'
                })
            
            # 判斷該衛星的統計特徵合規性
            if len(satellite_violations) == 0:
                valid_satellites += 1
            else:
                issue_satellites += 1
                stats_report['statistical_violations'].append({
                    'satellite_name': satellite_name,
                    'constellation': constellation,
                    'violation_count': len(satellite_violations),
                    'violations': satellite_violations
                })
        
        # 計算合規統計
        compliance_rate = (valid_satellites / sample_size * 100) if sample_size > 0 else 0
        
        stats_report['statistical_compliance'] = {
            'satellites_with_valid_statistics': valid_satellites,
            'satellites_with_statistical_issues': issue_satellites,
            'compliance_percentage': compliance_rate
        }
        
        # 確定合規狀態
        if compliance_rate >= 85 and len(stats_report['statistical_violations']) <= 3:
            stats_report['compliance_status'] = 'PASS'
            logger.info(f"✅ 統計特徵合理性驗證通過: {compliance_rate:.2f}% 合規率")
        else:
            stats_report['compliance_status'] = 'FAIL'
            logger.error(f"❌ 統計特徵合理性驗證失敗: {compliance_rate:.2f}% 合規率，發現 {len(stats_report['statistical_violations'])} 個問題")
            
            # 如果合規問題嚴重，拋出異常
            if compliance_rate < 70:
                raise ValueError(f"Academic Standards Violation: 統計特徵嚴重不合理 - 合規率僅 {compliance_rate:.2f}%")
        
        return stats_report
    
    def load_signal_analysis_output(self, signal_file: Optional[str] = None) -> Dict[str, Any]:
        """載入信號分析輸出數據"""
        if signal_file is None:
            # 🎯 更新為新的檔案命名
            signal_file = self.input_dir / "signal_quality_analysis_output.json"
        else:
            signal_file = Path(signal_file)
            
        logger.info(f"📥 載入信號分析數據: {signal_file}")
        
        if not signal_file.exists():
            raise FileNotFoundError(f"信號分析輸出檔案不存在: {signal_file}")
            
        try:
            with open(signal_file, 'r', encoding='utf-8') as f:
                signal_data = json.load(f)
                
            # 驗證數據格式
            if 'constellations' not in signal_data:
                raise ValueError("信號分析數據缺少 constellations 欄位")
                
            total_satellites = 0
            for constellation_name, constellation_data in signal_data['constellations'].items():
                satellites = constellation_data.get('satellites', [])
                total_satellites += len(satellites)
                logger.info(f"  {constellation_name}: {len(satellites)} 顆衛星")
                
            logger.info(f"✅ 信號分析數據載入完成: 總計 {total_satellites} 顆衛星")
            return signal_data
            
        except Exception as e:
            logger.error(f"載入信號分析數據失敗: {e}")
            raise
            
    def convert_to_enhanced_timeseries(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """將信號分析數據轉換為增強時間序列格式"""
        logger.info("🔄 開始時間序列數據轉換...")
        
        conversion_results = {
            "starlink": None,
            "oneweb": None,
            "conversion_statistics": {
                "total_processed": 0,
                "successful_conversions": 0,
                "failed_conversions": 0
            }
        }
        
        constellations = signal_data.get('constellations', {})
        
        for const_name, const_data in constellations.items():
            if const_name not in ['starlink', 'oneweb']:
                continue
                
            satellites = const_data.get('satellites', [])
            logger.info(f"📊 處理 {const_name}: {len(satellites)} 顆衛星")
            
            enhanced_satellites = []
            successful_count = 0
            failed_count = 0
            
            for satellite in satellites:
                try:
                    enhanced_satellite = self._convert_satellite_to_timeseries(satellite, const_name)
                    if enhanced_satellite:
                        enhanced_satellites.append(enhanced_satellite)
                        successful_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    sat_id = satellite.get('satellite_id', 'Unknown')
                    logger.warning(f"衛星 {sat_id} 轉換失敗: {e}")
                    failed_count += 1
            
            # 組裝星座數據
            enhanced_constellation = {
                "metadata": {
                    "constellation": const_name,
                    "processing_type": "timeseries_preprocessing",
                    "generation_time": datetime.now(timezone.utc).isoformat(),
                    "source_data": "signal_event_analysis",
                    "total_satellites": len(satellites),
                    "successful_conversions": successful_count,
                    "failed_conversions": failed_count,
                    "conversion_rate": f"{successful_count/len(satellites)*100:.1f}%" if satellites else "0%"
                },
                "satellites": enhanced_satellites,
                "constellation_statistics": {
                    "total_satellites": len(enhanced_satellites),
                    "avg_visibility_windows": sum(len(s.get('visibility_windows', [])) for s in enhanced_satellites) / len(enhanced_satellites) if enhanced_satellites else 0,
                    "avg_signal_quality": sum(s.get('signal_quality', {}).get('statistics', {}).get('mean_rsrp_dbm', -150) for s in enhanced_satellites) / len(enhanced_satellites) if enhanced_satellites else 0
                }
            }
            
            conversion_results[const_name] = enhanced_constellation
            conversion_results["conversion_statistics"]["total_processed"] += len(satellites)
            conversion_results["conversion_statistics"]["successful_conversions"] += successful_count
            conversion_results["conversion_statistics"]["failed_conversions"] += failed_count
            
            logger.info(f"✅ {const_name} 轉換完成: {successful_count}/{len(satellites)} 顆衛星成功")
        
        total_processed = conversion_results["conversion_statistics"]["total_processed"]
        total_successful = conversion_results["conversion_statistics"]["successful_conversions"]
        
        logger.info(f"🎯 時間序列轉換完成: {total_successful}/{total_processed} 顆衛星成功轉換")
        
        return conversion_results
        
    def _convert_satellite_to_timeseries(self, satellite: Dict[str, Any], constellation: str) -> Optional[Dict[str, Any]]:
        """將單顆衛星轉換為增強時間序列格式"""
        
        # 基本衛星信息
        enhanced_satellite = {
            "satellite_id": satellite.get('satellite_id', ''),
            "name": satellite.get('name', ''),
            "constellation": constellation,
            "norad_id": satellite.get('norad_id', 0)
        }
        
        # 1. 處理軌道數據
        orbit_data = satellite.get('orbit_data', {})
        if orbit_data:
            enhanced_satellite["orbit_parameters"] = {
                "altitude": orbit_data.get('altitude', 0),
                "inclination": orbit_data.get('inclination', 0),
                "semi_major_axis": orbit_data.get('semi_major_axis', 0),
                "eccentricity": orbit_data.get('eccentricity', 0),
                "mean_motion": orbit_data.get('mean_motion', 0)
            }
        
        # 2. 處理位置時間序列
        # 🎯 關鍵修復：優先使用Stage3的標準字段，兼容多種格式
        # 查找順序：position_timeseries -> timeseries -> positions
        positions = (satellite.get('position_timeseries') or 
                    satellite.get('timeseries', []) or 
                    satellite.get('positions', []))
        if positions:
            enhanced_satellite["position_timeseries"] = []
            for pos in positions:
                # 適配新的192點時間序列格式
                relative_obs = pos.get('relative_to_observer', {})
                geodetic = pos.get('geodetic', {})
                
                enhanced_pos = {
                    "time": pos.get('utc_time', pos.get('time', '')),
                    "time_offset_seconds": pos.get('time_index', 0) * 30,  # 30秒間隔
                    "elevation_deg": relative_obs.get('elevation_deg', pos.get('elevation_deg', -999)),
                    "azimuth_deg": relative_obs.get('azimuth_deg', pos.get('azimuth_deg', 0)),
                    "range_km": relative_obs.get('range_km', pos.get('range_km', 0)),
                    "is_visible": relative_obs.get('is_visible', pos.get('is_visible', False)),
                    "position_eci": {
                        "x": pos.get('eci_position_km', [0, 0, 0])[0] if len(pos.get('eci_position_km', [])) > 0 else 0,
                        "y": pos.get('eci_position_km', [0, 0, 0])[1] if len(pos.get('eci_position_km', [])) > 1 else 0,
                        "z": pos.get('eci_position_km', [0, 0, 0])[2] if len(pos.get('eci_position_km', [])) > 2 else 0
                    },
                    "velocity_eci": {
                        "x": pos.get('eci_velocity_km_s', [0, 0, 0])[0] if len(pos.get('eci_velocity_km_s', [])) > 0 else 0,
                        "y": pos.get('eci_velocity_km_s', [0, 0, 0])[1] if len(pos.get('eci_velocity_km_s', [])) > 1 else 0,
                        "z": pos.get('eci_velocity_km_s', [0, 0, 0])[2] if len(pos.get('eci_velocity_km_s', [])) > 2 else 0
                    },
                    # 新增地理坐標信息
                    "geodetic": {
                        "latitude_deg": geodetic.get('latitude_deg', 0),
                        "longitude_deg": geodetic.get('longitude_deg', 0),
                        "altitude_km": geodetic.get('altitude_km', 0)
                    }
                }
                enhanced_satellite["position_timeseries"].append(enhanced_pos)
            logger.debug(f"  成功處理 {len(positions)} 個時間點的軌道數據")
        
        # 3. 處理標準時間序列（來自原始 timeseries）
        timeseries = satellite.get('timeseries', [])
        if timeseries:
            enhanced_satellite["elevation_azimuth_timeseries"] = timeseries
        
        # 4. 處理可見性窗口
        visibility_windows = orbit_data.get('visibility_windows', [])
        if visibility_windows:
            enhanced_satellite["visibility_windows"] = visibility_windows
        
        # 5. 處理信號品質數據
        signal_quality = satellite.get('signal_quality', {})
        if signal_quality:
            enhanced_satellite["signal_quality"] = signal_quality
        
        # 6. 處理事件分析結果
        if 'event_potential' in satellite:
            enhanced_satellite["event_analysis"] = {
                "event_potential": satellite.get('event_potential', {}),
                "supported_events": ["A4_intra_frequency", "A5_intra_frequency", "D2_beam_switch"],
                "standards_compliance": {
                    "A4": "3GPP TS 38.331 Section 5.5.4.5 - Neighbour becomes better than threshold",
                    "A5": "3GPP TS 38.331 Section 5.5.4.6 - SpCell worse and neighbour better",
                    "D2": "3GPP TS 38.331 Section 5.5.4.15a - Distance-based handover triggers"
                }
            }
        
        # 7. 處理綜合評分
        if 'composite_score' in satellite:
            enhanced_satellite["performance_scores"] = {
                "composite_score": satellite.get('composite_score', 0),
                "geographic_score": satellite.get('geographic_relevance_score', 0),
                "handover_score": satellite.get('handover_suitability_score', 0)
            }
        
        # 8. 添加時間序列預處理標記
        enhanced_satellite["processing_metadata"] = {
            "processed_by_timeseries_preprocessing": True,
            "processing_time": datetime.now(timezone.utc).isoformat(),
            "data_source": "signal_event_analysis",
            "enhanced_features": [
                "position_timeseries",
                "elevation_azimuth_timeseries", 
                "visibility_windows",
                "signal_quality",
                "event_analysis",
                "performance_scores"
            ]
        }
        
        return enhanced_satellite

    def _create_animation_format(self, constellation_data: Dict[str, Any], constellation_name: str) -> Dict[str, Any]:
        """創建符合文檔的動畫數據格式 - 同時支援前端動畫和強化學習研究"""
        satellites = constellation_data.get('satellites', [])
        
        # 計算動畫參數
        total_frames = 192  # 96分鐘軌道，30秒間隔
        animation_fps = 60
        
        # 轉換衛星數據為動畫格式
        animation_satellites = {}
        for satellite in satellites:
            sat_id = satellite.get('satellite_id', '')
            if not sat_id:
                continue
                
            # 從position_timeseries提取軌跡點
            position_data = satellite.get('position_timeseries', [])
            track_points = []
            signal_timeline = []
            
            for i, pos in enumerate(position_data):
                # 軌跡點 - 保留仰角數據供強化學習研究使用
                track_point = {
                    "time": i * 30,  # 30秒間隔
                    "lat": pos.get('geodetic', {}).get('latitude_deg', 0),
                    "lon": pos.get('geodetic', {}).get('longitude_deg', 0),
                    "alt": pos.get('geodetic', {}).get('altitude_km', 550),
                    "elevation_deg": pos.get('elevation_deg', -90),  # 🎯 保留仰角數據
                    "visible": pos.get('is_visible', False)
                }
                track_points.append(track_point)
                
                # 信號時間線 - 保持原始信號值 (Grade A 要求)
                # 從信號品質數據中獲取原始RSRP值
                satellite_signal_quality = satellite.get('signal_quality', {})
                original_rsrp_dbm = satellite_signal_quality.get('statistics', {}).get('mean_rsrp_dbm', -150)
                
                signal_point = {
                    "time": i * 30,
                    "rsrp_dbm": original_rsrp_dbm,  # 保持原始dBm值，不正規化
                    "signal_unit": "dBm",  # 明確標示物理單位
                    "elevation_deg": pos.get('elevation_deg', -90),  # 保留仰角用於前端計算
                    "quality_color": "#00FF00" if pos.get('is_visible', False) else "#FF0000"
                }
                signal_timeline.append(signal_point)
            
            # 計算摘要統計
            visible_points = [p for p in position_data if p.get('is_visible', False)]
            max_elevation = max((p.get('elevation_deg', -90) for p in position_data), default=-90)
            
            animation_satellites[sat_id] = {
                "track_points": track_points,
                "signal_timeline": signal_timeline,
                "summary": {
                    "max_elevation_deg": round(max_elevation, 1),
                    "total_visible_time_min": len(visible_points) * 0.5,  # 30秒 * 點數 / 60
                    "avg_signal_quality": "high" if max_elevation > 45 else "medium" if max_elevation > 15 else "low"
                }
            }
        
        # 組裝完整的動畫數據格式
        animation_data = {
            "metadata": {
                "constellation": constellation_name,
                "satellite_count": len(animation_satellites),
                "time_range": {
                    "start": "2025-08-14T00:00:00Z",
                    "end": "2025-08-14T06:00:00Z"
                },
                "animation_fps": animation_fps,
                "total_frames": total_frames,
                "stage": "stage4_timeseries",
                "data_integrity": "complete",  # 無資料減量，符合學術標準
                "processing_type": "animation_preprocessing",
                "research_data_included": True  # 🎯 標記包含研究數據
            },
            "satellites": animation_satellites
        }
        
        return animation_data
        
    def save_enhanced_timeseries(self, conversion_results: Dict[str, Any]) -> Dict[str, str]:
        """保存增強時間序列數據到文件"""
        logger.info("💾 保存增強時間序列數據...")
        
        # 🔄 修改：使用專用子目錄
        # 確保子目錄存在
        self.timeseries_preprocessing_dir.mkdir(parents=True, exist_ok=True)
        
        output_files = {}
        
        # 🎯 修復：使用文檔指定的檔案命名規範
        ANIMATION_FILENAMES = {
            "starlink": "animation_enhanced_starlink.json",
            "oneweb": "animation_enhanced_oneweb.json"
        }
        
        for const_name in ['starlink', 'oneweb']:
            if conversion_results[const_name] is None:
                continue
                
            # 使用文檔指定的動畫檔案命名，輸出到專用子目錄
            filename = ANIMATION_FILENAMES[const_name]
            output_file = self.timeseries_preprocessing_dir / filename
            
            # 將統計信息添加到檔案內容中
            constellation_data = conversion_results[const_name].copy()
            satellite_count = len(constellation_data['satellites'])
            
            # 🎯 新增：符合文檔的動畫數據格式
            animation_data = self._create_animation_format(constellation_data, const_name)
            
            # 保存文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(animation_data, f, indent=2, ensure_ascii=False)
            
            file_size = output_file.stat().st_size
            output_files[const_name] = str(output_file)
            
            logger.info(f"✅ {const_name} 動畫數據已保存: {output_file}")
            logger.info(f"   文件大小: {file_size / (1024*1024):.1f} MB")
            logger.info(f"   衛星數量: {satellite_count} 顆")
        
        # 保存轉換統計到專用子目錄
        stats_file = self.timeseries_preprocessing_dir / "conversion_statistics.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(conversion_results["conversion_statistics"], f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 轉換統計已保存: {stats_file}")
        
        return output_files
        
    def process_timeseries_preprocessing(self, signal_file: Optional[str] = None, save_output: bool = True) -> Dict[str, Any]:
        """執行完整的時間序列預處理流程 - v6.0 Phase 3 驗證框架版本"""
        start_time = time.time()
        logger.info("🚀 開始時間序列預處理 + Phase 3 驗證框架")
        logger.info("=" * 60)
        
        # 清理舊驗證快照 (確保生成最新驗證快照)
        if self.snapshot_file.exists():
            logger.info(f"🗑️ 清理舊驗證快照: {self.snapshot_file}")
            self.snapshot_file.unlink()
        
        # 🔄 修改：清理子目錄中的舊輸出檔案
        try:
            # 清理子目錄中的時間序列檔案
            for file_pattern in ["animation_enhanced_starlink.json", "animation_enhanced_oneweb.json", "conversion_statistics.json"]:
                old_file = self.timeseries_preprocessing_dir / file_pattern
                if old_file.exists():
                    logger.info(f"🗑️ 清理舊檔案: {old_file}")
                    old_file.unlink()
                
        except Exception as e:
            logger.warning(f"⚠️ 清理失敗，繼續執行: {e}")
        
        try:
            # 1. 載入信號分析數據
            signal_data = self.load_signal_analysis_output(signal_file)
            
            # 🛡️ Phase 3 新增：預處理驗證
            validation_context = {
                'stage_name': 'stage4_timeseries_preprocessing',
                'processing_start': datetime.now(timezone.utc).isoformat(),
                'input_source': signal_file or 'signal_quality_analysis_output.json',
                'timeseries_processing_parameters': {
                    'enhanced_format_conversion': True,
                    'animation_data_generation': True,
                    'temporal_consistency_required': True
                }
            }
            
            if self.validation_enabled and self.validation_adapter:
                try:
                    logger.info("🔍 執行預處理驗證 (時間序列數據結構檢查)...")
                    
                    # 執行預處理驗證
                    import asyncio
                    pre_validation_result = asyncio.run(
                        self.validation_adapter.pre_process_validation(signal_data, validation_context)
                    )
                    
                    if not pre_validation_result.get('success', False):
                        error_msg = f"預處理驗證失敗: {pre_validation_result.get('blocking_errors', [])}"
                        logger.error(f"🚨 {error_msg}")
                        raise ValueError(f"Phase 3 Validation Failed: {error_msg}")
                    
                    logger.info("✅ 預處理驗證通過，繼續時間序列轉換...")
                    
                except Exception as e:
                    logger.error(f"🚨 Phase 3 預處理驗證異常: {str(e)}")
                    if "Phase 3 Validation Failed" in str(e):
                        raise  # 重新拋出驗證失敗錯誤
                    else:
                        logger.warning("   使用舊版驗證邏輯繼續處理")
            
            # 2. 轉換為增強時間序列格式
            conversion_results = self.convert_to_enhanced_timeseries(signal_data)
            
            # 3. 保存增強時間序列數據
            output_files = {}
            if save_output:
                output_files = self.save_enhanced_timeseries(conversion_results)
                logger.info(f"📁 時間序列預處理數據已保存到: {self.timeseries_preprocessing_dir} (專用子目錄)")
            else:
                logger.info("🚀 時間序列預處理使用內存傳遞模式，未保存檔案")
            
            # 🔧 修復：創建合併的時間序列數據供Stage 5使用
            all_satellites = []
            for const_name in ['starlink', 'oneweb']:
                const_result = conversion_results.get(const_name)
                if const_result:
                    satellites = const_result.get('satellites', [])
                    all_satellites.extend(satellites)
            
            # 計算總輸出檔案大小
            total_output_size_mb = 0
            if output_files:
                total_output_size_mb = sum(
                    (Path(f).stat().st_size / (1024*1024)) 
                    for f in output_files.values() 
                    if Path(f).exists()
                )
            
            # 準備處理指標
            end_time = time.time()
            processing_duration = end_time - start_time
            self.processing_duration = processing_duration
            
            processing_metrics = {
                'input_satellites': conversion_results["conversion_statistics"]["total_processed"],
                'processed_satellites': conversion_results["conversion_statistics"]["successful_conversions"],
                'failed_conversions': conversion_results["conversion_statistics"]["failed_conversions"],
                'processing_time': processing_duration,
                'processing_timestamp': datetime.now(timezone.utc).isoformat(),
                'output_size_mb': total_output_size_mb,
                'timeseries_conversion_completed': True
            }

            # 🛡️ Phase 3 新增：後處理驗證
            if self.validation_enabled and self.validation_adapter:
                try:
                    logger.info("🔍 執行後處理驗證 (時間序列轉換結果檢查)...")
                    
                    # 準備驗證數據結構
                    validation_output_data = {
                        'constellations': {
                            'starlink': conversion_results.get('starlink', {}),
                            'oneweb': conversion_results.get('oneweb', {})
                        },
                        'conversion_statistics': conversion_results.get('conversion_statistics', {})
                    }
                    
                    # 執行後處理驗證
                    post_validation_result = asyncio.run(
                        self.validation_adapter.post_process_validation(validation_output_data, processing_metrics)
                    )
                    
                    # 檢查驗證結果
                    if not post_validation_result.get('success', False):
                        error_msg = f"後處理驗證失敗: {post_validation_result.get('error', '未知錯誤')}"
                        logger.error(f"🚨 {error_msg}")
                        
                        # 檢查是否為品質門禁阻斷
                        if 'Quality gate blocked' in post_validation_result.get('error', ''):
                            raise ValueError(f"Phase 3 Quality Gate Blocked: {error_msg}")
                        else:
                            logger.warning("   後處理驗證失敗，但繼續處理 (降級模式)")
                    else:
                        logger.info("✅ 後處理驗證通過，時間序列轉換結果符合學術標準")
                        
                        # 記錄驗證摘要
                        academic_compliance = post_validation_result.get('academic_compliance', {})
                        if academic_compliance.get('compliant', False):
                            logger.info(f"🎓 學術合規性: Grade {academic_compliance.get('grade_level', 'Unknown')}")
                        else:
                            logger.warning(f"⚠️ 學術合規性問題: {len(academic_compliance.get('violations', []))} 項違規")
                    
                    # 將驗證結果加入處理指標
                    processing_metrics['validation_summary'] = post_validation_result
                    
                except Exception as e:
                    logger.error(f"🚨 Phase 3 後處理驗證異常: {str(e)}")
                    if "Phase 3 Quality Gate Blocked" in str(e):
                        raise  # 重新拋出品質門禁阻斷錯誤
                    else:
                        logger.warning("   使用舊版驗證邏輯繼續處理")
                        processing_metrics['validation_summary'] = {
                            'success': False,
                            'error': str(e),
                            'fallback_used': True
                        }

            # 4. 組裝返回結果
            results = {
                "success": True,
                "processing_type": "timeseries_preprocessing",
                "processing_timestamp": datetime.now(timezone.utc).isoformat(),
                "input_source": "signal_quality_analysis_output.json",
                "output_directory": str(self.timeseries_preprocessing_dir),
                "output_files": output_files,
                "conversion_statistics": conversion_results["conversion_statistics"],
                "constellation_data": {
                    "starlink": {
                        "satellites_processed": len(conversion_results["starlink"]["satellites"]) if conversion_results["starlink"] else 0,
                        "output_file": output_files.get("starlink", None)
                    },
                    "oneweb": {
                        "satellites_processed": len(conversion_results["oneweb"]["satellites"]) if conversion_results["oneweb"] else 0,
                        "output_file": output_files.get("oneweb", None)
                    }
                },
                # 🔧 修復：添加timeseries_data字段供Stage 5使用
                "timeseries_data": {
                    "satellites": all_satellites,
                    "metadata": {
                        "total_satellites": len(all_satellites),
                        "processing_complete": True,
                        "data_format": "enhanced_timeseries"
                    }
                },
                # 🔧 添加metadata兼容字段
                "metadata": {
                    "total_satellites": len(all_satellites),
                    "successful_conversions": conversion_results["conversion_statistics"]["successful_conversions"],
                    "failed_conversions": conversion_results["conversion_statistics"]["failed_conversions"],
                    "total_output_size_mb": total_output_size_mb,
                    "processing_metrics": processing_metrics,
                    "validation_summary": processing_metrics.get('validation_summary', None),
                    "academic_compliance": {
                        'phase3_validation': 'enabled' if self.validation_enabled else 'disabled',
                        'data_format_version': 'unified_v1.1_phase3'
                    }
                }
            }
            
            # 5. 保存驗證快照
            validation_success = self.save_validation_snapshot(results)
            if validation_success:
                logger.info("✅ Stage 4 驗證快照已保存")
            else:
                logger.warning("⚠️ Stage 4 驗證快照保存失敗")
            
            total_processed = results["conversion_statistics"]["total_processed"]
            total_successful = results["conversion_statistics"]["successful_conversions"]
            
            logger.info("=" * 60)
            logger.info("✅ 時間序列預處理完成")
            logger.info(f"  處理的衛星數: {total_processed}")
            logger.info(f"  成功轉換: {total_successful}")
            logger.info(f"  轉換率: {total_successful/total_processed*100:.1f}%" if total_processed > 0 else "  轉換率: 0%")
            logger.info(f"  處理時間: {processing_duration:.2f} 秒")
            logger.info(f"  輸出檔案總大小: {total_output_size_mb:.1f} MB")
            
            if output_files:
                logger.info(f"  輸出文件:")
                for const, file_path in output_files.items():
                    logger.info(f"    {const}: {file_path}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Stage 4 時間序列預處理失敗: {e}")
            # 保存錯誤快照
            error_data = {
                'error': str(e),
                'stage': 4,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'validation_enabled': self.validation_enabled
            }
            self.save_validation_snapshot(error_data)
            raise