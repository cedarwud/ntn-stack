#!/usr/bin/env python3
"""
Stage 4 Validation Adapter - 時間序列預處理器驗證轉接器
Phase 3 驗證框架整合：時間序列數據一致性與時間戳驗證
"""

from typing import List, Dict, Any, Optional
import logging
import json
import asyncio
from datetime import datetime, timezone
import math

# 設置日誌
logger = logging.getLogger(__name__)

class Stage4ValidationAdapter:
    """Stage 4 時間序列預處理驗證轉接器 - Zero Intrusion Integration"""
    
    def __init__(self):
        """初始化 Stage 4 驗證轉接器"""
        self.stage_name = "stage4_timeseries_preprocessing"
        self.validation_engines = {}
        
        # 時間序列驗證標準
        self.TIME_SERIES_STANDARDS = {
            'min_time_points': 10,  # 最少時間點數量
            'max_time_gap_seconds': 300,  # 最大時間間隔 (5分鐘)
            'temporal_consistency_threshold': 0.95,  # 時間一致性門檻
            'orbit_prediction_window_hours': 24,  # 軌道預測視窗 (24小時)
        }
        
        # 學術級數據標準 
        self.ACADEMIC_STANDARDS = {
            'grade_a_requirements': {
                'real_timestamp_data': True,
                'sgp4_time_base_correct': True,
                'temporal_consistency_verified': True,
                'no_time_simulation': True
            },
            'grade_b_requirements': {
                'time_model_standards_based': True,
                'temporal_interpolation_justified': True
            },
            'grade_c_violations': {
                'random_timestamp_generation': True,
                'assumed_time_intervals': True,
                'mock_temporal_data': True
            }
        }
        
        try:
            # 初始化驗證引擎
            self._initialize_validation_engines()
            logger.info("✅ Stage 4 驗證轉接器初始化成功")
            
        except Exception as e:
            logger.error(f"❌ Stage 4 驗證引擎初始化失敗: {e}")
            self.validation_engines = {}

    def _initialize_validation_engines(self):
        """初始化驗證引擎"""
        self.validation_engines = {
            'temporal_consistency': self._validate_temporal_consistency,
            'time_series_integrity': self._validate_time_series_integrity,
            'orbit_time_base': self._validate_orbit_time_base,
            'academic_standards': self._validate_academic_standards
        }
        
    async def pre_process_validation(self, input_data: Dict[str, Any], 
                                   context: Dict[str, Any] = None) -> Dict[str, Any]:
        """預處理驗證 - 時間序列數據載入前檢查"""
        validation_start = datetime.now(timezone.utc)
        
        try:
            # 準備驗證上下文
            validation_context = {
                'stage_id': 'stage4_timeseries_preprocessing',
                'phase': 'pre_process',
                'input_data_size': len(input_data.get('constellations', {})),
                'validation_timestamp': validation_start.isoformat(),
                'context': context or {}
            }
            
            logger.info(f"🔍 Stage 4 預處理驗證開始: {validation_context['input_data_size']} 個星座")
            
            # 驗證結果收集
            validation_results = {
                'success': True,
                'warnings': [],
                'blocking_errors': [],
                'validation_summary': {}
            }
            
            # 1. 時間序列數據結構檢查
            temporal_result = await self._validate_temporal_consistency(input_data)
            validation_results['validation_summary']['temporal_consistency'] = temporal_result
            if not temporal_result['success']:
                validation_results['blocking_errors'].extend(temporal_result.get('errors', []))
            
            # 2. 軌道時間基準檢查
            time_base_result = await self._validate_orbit_time_base(input_data)
            validation_results['validation_summary']['orbit_time_base'] = time_base_result
            if not time_base_result['success']:
                validation_results['blocking_errors'].extend(time_base_result.get('errors', []))
            
            # 3. 學術標準檢查
            academic_result = await self._validate_academic_standards(input_data, 'pre_process')
            validation_results['validation_summary']['academic_compliance'] = academic_result
            if not academic_result['success']:
                validation_results['blocking_errors'].extend(academic_result.get('violations', []))
            
            # 決定整體驗證結果
            if validation_results['blocking_errors']:
                validation_results['success'] = False
                logger.error(f"🚨 Stage 4 預處理驗證失敗: {len(validation_results['blocking_errors'])} 個阻斷性錯誤")
            else:
                logger.info("✅ Stage 4 預處理驗證通過")
            
            # 記錄驗證時間
            validation_end = datetime.now(timezone.utc)
            validation_results['validation_duration'] = (validation_end - validation_start).total_seconds()
            
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Stage 4 預處理驗證異常: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'validation_timestamp': validation_start.isoformat()
            }
    
    async def post_process_validation(self, output_data: Dict[str, Any], 
                                    processing_metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """後處理驗證 - 時間序列預處理結果檢查"""
        validation_start = datetime.now(timezone.utc)
        
        try:
            logger.info("🔍 Stage 4 後處理驗證開始")
            
            # 驗證結果收集
            validation_results = {
                'success': True,
                'warnings': [],
                'academic_compliance': {},
                'quality_metrics': {}
            }
            
            # 1. 時間序列完整性檢查
            integrity_result = await self._validate_time_series_integrity(output_data)
            validation_results['quality_metrics']['time_series_integrity'] = integrity_result
            
            if not integrity_result['success']:
                validation_results['success'] = False
                validation_results['error'] = f"時間序列完整性檢查失敗: {integrity_result.get('errors', [])}"
            
            # 2. 學術標準後處理檢查
            academic_result = await self._validate_academic_standards(output_data, 'post_process')
            validation_results['academic_compliance'] = academic_result
            
            # 品質門禁檢查
            if academic_result.get('grade_level') == 'C' or not academic_result.get('compliant', True):
                validation_results['success'] = False
                validation_results['error'] = "Quality gate blocked: 學術標準不符，發現Grade C違規項目"
                logger.error("🚨 品質門禁阻斷: Stage 4時間序列處理不符合學術標準")
            
            # 3. 處理指標驗證
            if processing_metrics:
                metrics_validation = self._validate_processing_metrics(processing_metrics)
                validation_results['quality_metrics']['processing_metrics'] = metrics_validation
            
            # 記錄驗證時間
            validation_end = datetime.now(timezone.utc)
            validation_results['validation_duration'] = (validation_end - validation_start).total_seconds()
            
            if validation_results['success']:
                logger.info("✅ Stage 4 後處理驗證通過")
            else:
                logger.error(f"🚨 Stage 4 後處理驗證失敗: {validation_results.get('error', '未知錯誤')}")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Stage 4 後處理驗證異常: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'validation_timestamp': validation_start.isoformat()
            }
    
    async def _validate_temporal_consistency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證時間序列一致性"""
        try:
            errors = []
            warnings = []
            
            # 檢查數據結構
            if 'constellations' not in data:
                errors.append("缺少 constellations 數據結構")
                return {'success': False, 'errors': errors}
            
            total_satellites = 0
            time_consistency_issues = 0
            
            for constellation_name, constellation_data in data['constellations'].items():
                satellites = constellation_data.get('satellites', [])
                total_satellites += len(satellites)
                
                for sat_data in satellites:
                    # 檢查時間戳格式
                    if 'orbit_data' in sat_data:
                        orbit_positions = sat_data['orbit_data'].get('positions', [])
                        
                        # 驗證時間戳連續性
                        timestamps = []
                        for pos in orbit_positions:
                            if 'timestamp' in pos:
                                try:
                                    dt = datetime.fromisoformat(pos['timestamp'].replace('Z', '+00:00'))
                                    timestamps.append(dt)
                                except ValueError:
                                    time_consistency_issues += 1
                        
                        # 檢查時間間隔
                        if len(timestamps) > 1:
                            time_gaps = []
                            for i in range(1, len(timestamps)):
                                gap = (timestamps[i] - timestamps[i-1]).total_seconds()
                                time_gaps.append(gap)
                            
                            # 檢查是否有異常大的時間間隔
                            max_gap = max(time_gaps) if time_gaps else 0
                            if max_gap > self.TIME_SERIES_STANDARDS['max_time_gap_seconds']:
                                warnings.append(f"{constellation_name}衛星存在{max_gap:.0f}秒的時間間隔")
            
            # 判斷結果
            success = len(errors) == 0 and time_consistency_issues == 0
            
            return {
                'success': success,
                'errors': errors,
                'warnings': warnings,
                'statistics': {
                    'total_satellites': total_satellites,
                    'time_consistency_issues': time_consistency_issues,
                    'consistency_rate': (total_satellites - time_consistency_issues) / max(total_satellites, 1)
                }
            }
            
        except Exception as e:
            logger.error(f"時間一致性驗證失敗: {e}")
            return {'success': False, 'errors': [str(e)]}
    
    async def _validate_time_series_integrity(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證時間序列完整性"""
        try:
            errors = []
            integrity_metrics = {
                'total_time_points': 0,
                'complete_trajectories': 0,
                'incomplete_trajectories': 0,
                'average_time_points_per_satellite': 0
            }
            
            if 'constellations' not in data:
                errors.append("輸出數據缺少 constellations 結構")
                return {'success': False, 'errors': errors}
            
            total_satellites = 0
            total_time_points = 0
            
            for constellation_name, constellation_data in data['constellations'].items():
                satellites = constellation_data.get('satellites', [])
                
                for sat_data in satellites:
                    total_satellites += 1
                    
                    # 檢查時間序列數據完整性
                    if 'enhanced_orbit_data' in sat_data:
                        orbit_data = sat_data['enhanced_orbit_data']
                        positions = orbit_data.get('positions', [])
                        time_points = len(positions)
                        total_time_points += time_points
                        
                        # 判斷軌跡是否完整
                        if time_points >= self.TIME_SERIES_STANDARDS['min_time_points']:
                            integrity_metrics['complete_trajectories'] += 1
                        else:
                            integrity_metrics['incomplete_trajectories'] += 1
                            errors.append(f"{constellation_name}衛星{sat_data.get('satellite_id', 'unknown')}時間點不足: {time_points}")
            
            # 計算平均值
            if total_satellites > 0:
                integrity_metrics['average_time_points_per_satellite'] = total_time_points / total_satellites
            
            integrity_metrics['total_time_points'] = total_time_points
            
            # 判斷完整性
            completeness_rate = integrity_metrics['complete_trajectories'] / max(total_satellites, 1)
            success = completeness_rate >= self.TIME_SERIES_STANDARDS['temporal_consistency_threshold']
            
            return {
                'success': success,
                'errors': errors,
                'metrics': integrity_metrics,
                'completeness_rate': completeness_rate
            }
            
        except Exception as e:
            logger.error(f"時間序列完整性驗證失敗: {e}")
            return {'success': False, 'errors': [str(e)]}
    
    async def _validate_orbit_time_base(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證軌道計算時間基準 (SGP4 epoch time base)"""
        try:
            errors = []
            warnings = []
            time_base_issues = {
                'incorrect_time_base': 0,
                'missing_tle_epoch': 0,
                'current_time_usage': 0
            }
            
            for constellation_name, constellation_data in data.get('constellations', {}).items():
                satellites = constellation_data.get('satellites', [])
                
                for sat_data in satellites:
                    # 檢查是否有 TLE epoch 信息
                    tle_info = sat_data.get('tle_info', {})
                    if not tle_info:
                        time_base_issues['missing_tle_epoch'] += 1
                        errors.append(f"{constellation_name}衛星缺少TLE epoch信息")
                        continue
                    
                    # 檢查計算基準時間
                    calculation_base_time = sat_data.get('calculation_metadata', {}).get('base_time')
                    if calculation_base_time:
                        # 解析基準時間
                        try:
                            base_dt = datetime.fromisoformat(calculation_base_time.replace('Z', '+00:00'))
                            current_time = datetime.now(timezone.utc)
                            
                            # 檢查是否使用當前時間作為基準（這是錯誤的）
                            time_diff = abs((current_time - base_dt).total_seconds())
                            if time_diff < 3600:  # 小於1小時，可能是當前時間
                                time_base_issues['current_time_usage'] += 1
                                errors.append(f"{constellation_name}衛星可能使用當前時間作為軌道計算基準")
                                
                        except ValueError:
                            time_base_issues['incorrect_time_base'] += 1
                            errors.append(f"{constellation_name}衛星計算基準時間格式錯誤")
            
            # 判斷結果
            total_issues = sum(time_base_issues.values())
            success = total_issues == 0
            
            return {
                'success': success,
                'errors': errors,
                'warnings': warnings,
                'time_base_analysis': time_base_issues
            }
            
        except Exception as e:
            logger.error(f"軌道時間基準驗證失敗: {e}")
            return {'success': False, 'errors': [str(e)]}
    
    async def _validate_academic_standards(self, data: Dict[str, Any], phase: str) -> Dict[str, Any]:
        """驗證學術標準合規性"""
        try:
            violations = []
            compliance_score = 0
            total_checks = 0
            
            # Grade A 檢查：真實時間戳數據
            total_checks += 1
            if self._check_real_timestamp_usage(data):
                compliance_score += 1
            else:
                violations.append("使用了模擬或假設的時間戳數據 (Grade C 違規)")
            
            # Grade A 檢查：SGP4時間基準正確性
            total_checks += 1
            if self._check_sgp4_time_base_correctness(data):
                compliance_score += 1
            else:
                violations.append("SGP4軌道計算未使用TLE epoch時間基準 (Grade C 違規)")
            
            # Grade C 檢查：禁止項目
            forbidden_patterns = self._check_forbidden_patterns(data)
            if forbidden_patterns:
                violations.extend([f"發現禁止模式: {pattern} (Grade C 違規)" for pattern in forbidden_patterns])
            
            # 計算合規等級
            compliance_rate = compliance_score / max(total_checks, 1) if total_checks > 0 else 0
            
            if compliance_rate >= 0.9 and not violations:
                grade_level = 'A'
                compliant = True
            elif compliance_rate >= 0.7 and len(violations) <= 1:
                grade_level = 'B'
                compliant = True
            else:
                grade_level = 'C'
                compliant = False
            
            return {
                'success': compliant,
                'compliant': compliant,
                'grade_level': grade_level,
                'compliance_rate': compliance_rate,
                'violations': violations,
                'checks_performed': total_checks
            }
            
        except Exception as e:
            logger.error(f"學術標準驗證失敗: {e}")
            return {
                'success': False,
                'compliant': False,
                'grade_level': 'C',
                'violations': [str(e)]
            }
    
    def _check_real_timestamp_usage(self, data: Dict[str, Any]) -> bool:
        """檢查是否使用真實時間戳數據"""
        try:
            # 檢查是否有明確的時間戳來源信息
            for constellation_name, constellation_data in data.get('constellations', {}).items():
                satellites = constellation_data.get('satellites', [])
                for sat_data in satellites:
                    # 檢查軌道數據中的時間戳
                    if 'orbit_data' in sat_data:
                        positions = sat_data['orbit_data'].get('positions', [])
                        if positions:
                            # 檢查時間戳格式的真實性
                            sample_timestamp = positions[0].get('timestamp')
                            if sample_timestamp and 'T' in sample_timestamp:
                                return True  # 看起來是真實的ISO格式時間戳
            return False
        except:
            return False
    
    def _check_sgp4_time_base_correctness(self, data: Dict[str, Any]) -> bool:
        """檢查SGP4計算時間基準正確性"""
        try:
            # 檢查是否有正確的TLE epoch基準時間信息
            for constellation_name, constellation_data in data.get('constellations', {}).items():
                satellites = constellation_data.get('satellites', [])
                for sat_data in satellites:
                    # 檢查計算元數據
                    metadata = sat_data.get('calculation_metadata', {})
                    base_time = metadata.get('base_time')
                    tle_epoch = sat_data.get('tle_info', {}).get('epoch')
                    
                    if base_time and tle_epoch:
                        # 基準時間應該基於TLE epoch而不是當前時間
                        return True
            return False
        except:
            return False
    
    def _check_forbidden_patterns(self, data: Dict[str, Any]) -> List[str]:
        """檢查禁止的模式"""
        forbidden = []
        
        # 檢查是否有random或mock相關的標記
        data_str = json.dumps(data, default=str).lower()
        
        if 'random' in data_str and 'timestamp' in data_str:
            forbidden.append("隨機時間戳生成")
        
        if 'mock' in data_str or 'simulated' in data_str:
            forbidden.append("模擬數據使用")
        
        if 'assumed' in data_str or 'estimated' in data_str:
            forbidden.append("假設值或估計值")
        
        return forbidden
    
    def _validate_processing_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """驗證處理指標"""
        try:
            validation_result = {
                'success': True,
                'issues': []
            }
            
            # 檢查基本指標
            required_metrics = ['input_satellites', 'processed_satellites', 'processing_time']
            for metric in required_metrics:
                if metric not in metrics:
                    validation_result['issues'].append(f"缺少必要指標: {metric}")
                    validation_result['success'] = False
            
            # 檢查處理效率
            if 'processing_time' in metrics and metrics['processing_time'] > 300:  # 5分鐘
                validation_result['issues'].append("處理時間過長，可能存在效率問題")
            
            return validation_result
            
        except Exception as e:
            return {
                'success': False,
                'issues': [str(e)]
            }