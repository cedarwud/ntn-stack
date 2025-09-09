#!/usr/bin/env python3
"""
Stage 5 Validation Adapter - 數據整合處理器驗證轉接器
Phase 3 驗證框架整合：多源數據整合一致性與完整性驗證
"""

from typing import List, Dict, Any, Optional
import logging
import json
import asyncio
from datetime import datetime, timezone
import math

# 設置日誌
logger = logging.getLogger(__name__)

class Stage5ValidationAdapter:
    """Stage 5 數據整合處理驗證轉接器 - Zero Intrusion Integration"""
    
    def __init__(self):
        """初始化 Stage 5 驗證轉接器"""
        self.stage_name = "stage5_data_integration"
        self.validation_engines = {}
        
        # 數據整合驗證標準
        self.INTEGRATION_STANDARDS = {
            'min_data_sources': 2,  # 最少數據來源數量
            'data_consistency_threshold': 0.95,  # 數據一致性門檻
            'temporal_alignment_tolerance_seconds': 60,  # 時間對齊容忍度 (1分鐘)
            'cross_validation_required': True,  # 需要交叉驗證
            'completeness_threshold': 0.9,  # 完整性門檻 90%
        }
        
        # 學術級數據標準 
        self.ACADEMIC_STANDARDS = {
            'grade_a_requirements': {
                'multi_source_cross_validation': True,
                'data_provenance_tracked': True,
                'integration_method_documented': True,
                'consistency_checks_verified': True
            },
            'grade_b_requirements': {
                'standard_integration_methods': True,
                'documented_data_sources': True,
                'basic_consistency_checks': True
            },
            'grade_c_violations': {
                'arbitrary_data_merging': True,
                'unverified_integration': True,
                'missing_source_attribution': True,
                'inconsistent_data_accepted': True
            }
        }
        
        try:
            # 初始化驗證引擎
            self._initialize_validation_engines()
            logger.info("✅ Stage 5 驗證轉接器初始化成功")
            
        except Exception as e:
            logger.error(f"❌ Stage 5 驗證引擎初始化失敗: {e}")
            self.validation_engines = {}

    def _initialize_validation_engines(self):
        """初始化驗證引擎"""
        self.validation_engines = {
            'data_source_validation': self._validate_data_sources,
            'integration_consistency': self._validate_integration_consistency,
            'temporal_alignment': self._validate_temporal_alignment,
            'cross_validation': self._validate_cross_validation,
            'academic_standards': self._validate_academic_standards
        }
        
    async def pre_process_validation(self, input_data: Dict[str, Any], 
                                   context: Dict[str, Any] = None) -> Dict[str, Any]:
        """預處理驗證 - 數據整合前檢查"""
        validation_start = datetime.now(timezone.utc)
        
        try:
            # 準備驗證上下文
            validation_context = {
                'stage_id': 'stage5_data_integration',
                'phase': 'pre_process',
                'data_sources_count': len(input_data.keys()) if input_data else 0,
                'validation_timestamp': validation_start.isoformat(),
                'context': context or {}
            }
            
            logger.info(f"🔍 Stage 5 預處理驗證開始: {validation_context['data_sources_count']} 個數據來源")
            
            # 驗證結果收集
            validation_results = {
                'success': True,
                'warnings': [],
                'blocking_errors': [],
                'validation_summary': {}
            }
            
            # 1. 數據來源驗證
            sources_result = await self._validate_data_sources(input_data)
            validation_results['validation_summary']['data_sources'] = sources_result
            if not sources_result['success']:
                validation_results['blocking_errors'].extend(sources_result.get('errors', []))
            
            # 2. 時間對齊預檢查
            temporal_result = await self._validate_temporal_alignment(input_data)
            validation_results['validation_summary']['temporal_alignment'] = temporal_result
            if not temporal_result['success']:
                validation_results['warnings'].extend(temporal_result.get('warnings', []))
            
            # 3. 學術標準檢查
            academic_result = await self._validate_academic_standards(input_data, 'pre_process')
            validation_results['validation_summary']['academic_compliance'] = academic_result
            if not academic_result['success']:
                validation_results['blocking_errors'].extend(academic_result.get('violations', []))
            
            # 決定整體驗證結果
            if validation_results['blocking_errors']:
                validation_results['success'] = False
                logger.error(f"🚨 Stage 5 預處理驗證失敗: {len(validation_results['blocking_errors'])} 個阻斷性錯誤")
            else:
                logger.info("✅ Stage 5 預處理驗證通過")
            
            # 記錄驗證時間
            validation_end = datetime.now(timezone.utc)
            validation_results['validation_duration'] = (validation_end - validation_start).total_seconds()
            
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Stage 5 預處理驗證異常: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'validation_timestamp': validation_start.isoformat()
            }
    
    async def post_process_validation(self, output_data: Dict[str, Any], 
                                    processing_metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """後處理驗證 - 數據整合結果檢查"""
        validation_start = datetime.now(timezone.utc)
        
        try:
            logger.info("🔍 Stage 5 後處理驗證開始")
            
            # 驗證結果收集
            validation_results = {
                'success': True,
                'warnings': [],
                'academic_compliance': {},
                'quality_metrics': {}
            }
            
            # 1. 整合一致性檢查
            consistency_result = await self._validate_integration_consistency(output_data)
            validation_results['quality_metrics']['integration_consistency'] = consistency_result
            
            if not consistency_result['success']:
                validation_results['success'] = False
                validation_results['error'] = f"數據整合一致性檢查失敗: {consistency_result.get('errors', [])}"
            
            # 2. 交叉驗證檢查
            cross_validation_result = await self._validate_cross_validation(output_data)
            validation_results['quality_metrics']['cross_validation'] = cross_validation_result
            
            # 3. 學術標準後處理檢查
            academic_result = await self._validate_academic_standards(output_data, 'post_process')
            validation_results['academic_compliance'] = academic_result
            
            # 品質門禁檢查
            if academic_result.get('grade_level') == 'C' or not academic_result.get('compliant', True):
                validation_results['success'] = False
                validation_results['error'] = "Quality gate blocked: 學術標準不符，發現Grade C違規項目"
                logger.error("🚨 品質門禁阻斷: Stage 5數據整合不符合學術標準")
            
            # 4. 處理指標驗證
            if processing_metrics:
                metrics_validation = self._validate_processing_metrics(processing_metrics)
                validation_results['quality_metrics']['processing_metrics'] = metrics_validation
            
            # 記錄驗證時間
            validation_end = datetime.now(timezone.utc)
            validation_results['validation_duration'] = (validation_end - validation_start).total_seconds()
            
            if validation_results['success']:
                logger.info("✅ Stage 5 後處理驗證通過")
            else:
                logger.error(f"🚨 Stage 5 後處理驗證失敗: {validation_results.get('error', '未知錯誤')}")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Stage 5 後處理驗證異常: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'validation_timestamp': validation_start.isoformat()
            }
    
    async def _validate_data_sources(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證數據來源"""
        try:
            errors = []
            warnings = []
            source_analysis = {
                'total_sources': 0,
                'valid_sources': 0,
                'invalid_sources': 0,
                'source_types': []
            }
            
            # 檢查數據來源數量
            if not data:
                errors.append("沒有輸入數據來源")
                return {'success': False, 'errors': errors}
            
            # 分析數據來源
            for source_key, source_data in data.items():
                source_analysis['total_sources'] += 1
                source_analysis['source_types'].append(source_key)
                
                # 檢查數據來源結構
                if isinstance(source_data, dict):
                    # 檢查是否有必要的元數據
                    if 'metadata' in source_data or 'satellites' in source_data or 'constellations' in source_data:
                        source_analysis['valid_sources'] += 1
                    else:
                        source_analysis['invalid_sources'] += 1
                        warnings.append(f"數據來源 {source_key} 缺少標準結構")
                else:
                    source_analysis['invalid_sources'] += 1
                    errors.append(f"數據來源 {source_key} 格式無效")
            
            # 檢查最少數據來源要求
            if source_analysis['total_sources'] < self.INTEGRATION_STANDARDS['min_data_sources']:
                errors.append(f"數據來源不足: {source_analysis['total_sources']} < {self.INTEGRATION_STANDARDS['min_data_sources']}")
            
            # 判斷結果
            success = len(errors) == 0 and source_analysis['valid_sources'] > 0
            
            return {
                'success': success,
                'errors': errors,
                'warnings': warnings,
                'source_analysis': source_analysis
            }
            
        except Exception as e:
            logger.error(f"數據來源驗證失敗: {e}")
            return {'success': False, 'errors': [str(e)]}
    
    async def _validate_integration_consistency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證數據整合一致性"""
        try:
            errors = []
            consistency_metrics = {
                'satellite_count_consistency': True,
                'timestamp_alignment': True,
                'data_format_consistency': True,
                'cross_reference_validity': True
            }
            
            # 檢查整合後的數據結構
            if 'integrated_data' in data:
                integrated_data = data['integrated_data']
                
                # 檢查衛星數量一致性
                if 'metadata' in integrated_data:
                    metadata = integrated_data['metadata']
                    declared_count = metadata.get('total_satellites', 0)
                    
                    # 計算實際衛星數量
                    actual_count = 0
                    if 'constellations' in integrated_data:
                        for const_name, const_data in integrated_data['constellations'].items():
                            satellites = const_data.get('satellites', [])
                            actual_count += len(satellites)
                    
                    if declared_count != actual_count:
                        consistency_metrics['satellite_count_consistency'] = False
                        errors.append(f"衛星數量不一致: 宣告 {declared_count} vs 實際 {actual_count}")
                
                # 檢查時間戳對齊
                timestamp_consistency = self._check_timestamp_consistency(integrated_data)
                if not timestamp_consistency:
                    consistency_metrics['timestamp_alignment'] = False
                    errors.append("發現時間戳不一致或未對齊的數據")
                
                # 檢查數據格式一致性
                format_consistency = self._check_data_format_consistency(integrated_data)
                if not format_consistency:
                    consistency_metrics['data_format_consistency'] = False
                    errors.append("發現數據格式不一致")
            else:
                errors.append("缺少 integrated_data 結構")
            
            # 判斷整體一致性
            overall_consistency = all(consistency_metrics.values())
            success = overall_consistency and len(errors) == 0
            
            return {
                'success': success,
                'errors': errors,
                'consistency_metrics': consistency_metrics,
                'overall_consistency_rate': sum(consistency_metrics.values()) / len(consistency_metrics)
            }
            
        except Exception as e:
            logger.error(f"整合一致性驗證失敗: {e}")
            return {'success': False, 'errors': [str(e)]}
    
    async def _validate_temporal_alignment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證時間對齊"""
        try:
            warnings = []
            temporal_analysis = {
                'sources_with_timestamps': 0,
                'max_time_deviation_seconds': 0,
                'alignment_quality': 'good'
            }
            
            # 收集所有時間戳
            all_timestamps = []
            
            for source_key, source_data in data.items():
                if isinstance(source_data, dict):
                    # 尋找時間戳
                    source_timestamps = self._extract_timestamps(source_data)
                    if source_timestamps:
                        temporal_analysis['sources_with_timestamps'] += 1
                        all_timestamps.extend(source_timestamps)
            
            # 分析時間偏差
            if len(all_timestamps) > 1:
                # 將字符串時間戳轉換為datetime對象
                dt_timestamps = []
                for ts in all_timestamps:
                    try:
                        if isinstance(ts, str):
                            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                            dt_timestamps.append(dt)
                    except ValueError:
                        continue
                
                if len(dt_timestamps) > 1:
                    # 計算最大時間偏差
                    min_time = min(dt_timestamps)
                    max_time = max(dt_timestamps)
                    max_deviation = (max_time - min_time).total_seconds()
                    temporal_analysis['max_time_deviation_seconds'] = max_deviation
                    
                    # 判斷對齊品質
                    if max_deviation > self.INTEGRATION_STANDARDS['temporal_alignment_tolerance_seconds']:
                        temporal_analysis['alignment_quality'] = 'poor'
                        warnings.append(f"時間對齊品質較差: 最大偏差 {max_deviation:.0f} 秒")
                    elif max_deviation > self.INTEGRATION_STANDARDS['temporal_alignment_tolerance_seconds'] / 2:
                        temporal_analysis['alignment_quality'] = 'fair'
                        warnings.append(f"時間對齊品質一般: 最大偏差 {max_deviation:.0f} 秒")
            
            success = temporal_analysis['alignment_quality'] != 'poor'
            
            return {
                'success': success,
                'warnings': warnings,
                'temporal_analysis': temporal_analysis
            }
            
        except Exception as e:
            logger.error(f"時間對齊驗證失敗: {e}")
            return {'success': False, 'errors': [str(e)]}
    
    async def _validate_cross_validation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證交叉驗證"""
        try:
            cross_validation_results = {
                'satellite_cross_references': 0,
                'data_point_cross_checks': 0,
                'inconsistencies_found': 0,
                'validation_coverage': 0.0
            }
            
            # 檢查整合後的交叉驗證標記
            if 'integrated_data' in data:
                integrated_data = data['integrated_data']
                
                # 統計交叉驗證標記
                validation_markers = self._count_validation_markers(integrated_data)
                cross_validation_results.update(validation_markers)
                
                # 計算驗證覆蓋率
                total_data_points = self._count_total_data_points(integrated_data)
                if total_data_points > 0:
                    cross_validation_results['validation_coverage'] = (
                        cross_validation_results['data_point_cross_checks'] / total_data_points
                    )
            
            # 判斷交叉驗證品質
            coverage_threshold = 0.8  # 80% 覆蓋率
            success = (
                cross_validation_results['validation_coverage'] >= coverage_threshold and
                cross_validation_results['inconsistencies_found'] == 0
            )
            
            return {
                'success': success,
                'cross_validation_results': cross_validation_results,
                'coverage_meets_threshold': cross_validation_results['validation_coverage'] >= coverage_threshold
            }
            
        except Exception as e:
            logger.error(f"交叉驗證失敗: {e}")
            return {'success': False, 'errors': [str(e)]}
    
    async def _validate_academic_standards(self, data: Dict[str, Any], phase: str) -> Dict[str, Any]:
        """驗證學術標準合規性"""
        try:
            violations = []
            compliance_score = 0
            total_checks = 0
            
            # Grade A 檢查：多源交叉驗證
            total_checks += 1
            if self._check_multi_source_cross_validation(data):
                compliance_score += 1
            else:
                violations.append("缺少多源數據交叉驗證 (Grade A 要求)")
            
            # Grade A 檢查：數據溯源跟踪
            total_checks += 1
            if self._check_data_provenance_tracking(data):
                compliance_score += 1
            else:
                violations.append("缺少數據溯源跟踪 (Grade A 要求)")
            
            # Grade A 檢查：整合方法記錄
            total_checks += 1
            if self._check_integration_method_documentation(data):
                compliance_score += 1
            else:
                violations.append("缺少整合方法記錄 (Grade A 要求)")
            
            # Grade C 檢查：禁止項目
            forbidden_patterns = self._check_forbidden_integration_patterns(data)
            if forbidden_patterns:
                violations.extend([f"發現禁止模式: {pattern} (Grade C 違規)" for pattern in forbidden_patterns])
            
            # 計算合規等級
            compliance_rate = compliance_score / max(total_checks, 1) if total_checks > 0 else 0
            
            if compliance_rate >= 0.9 and not violations:
                grade_level = 'A'
                compliant = True
            elif compliance_rate >= 0.7 and len(violations) <= 2:
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
    
    def _check_timestamp_consistency(self, integrated_data: Dict[str, Any]) -> bool:
        """檢查時間戳一致性"""
        try:
            # 檢查是否有統一的時間基準記錄
            metadata = integrated_data.get('metadata', {})
            if 'integration_timestamp' not in metadata:
                return False
            
            # 檢查各個星座的時間戳格式是否一致
            if 'constellations' in integrated_data:
                timestamp_formats = set()
                for const_name, const_data in integrated_data['constellations'].items():
                    satellites = const_data.get('satellites', [])
                    for sat in satellites:
                        if 'orbit_data' in sat and 'positions' in sat['orbit_data']:
                            positions = sat['orbit_data']['positions']
                            if positions and 'timestamp' in positions[0]:
                                ts = positions[0]['timestamp']
                                # 分析時間戳格式
                                if 'T' in ts and 'Z' in ts:
                                    timestamp_formats.add('iso_utc')
                                elif 'T' in ts:
                                    timestamp_formats.add('iso_local')
                                else:
                                    timestamp_formats.add('custom')
                
                # 如果有多種格式，說明不一致
                return len(timestamp_formats) <= 1
            
            return True
        except:
            return False
    
    def _check_data_format_consistency(self, integrated_data: Dict[str, Any]) -> bool:
        """檢查數據格式一致性"""
        try:
            # 檢查所有衛星是否有相同的基本結構
            required_fields = {'satellite_id', 'constellation'}
            
            if 'constellations' in integrated_data:
                for const_name, const_data in integrated_data['constellations'].items():
                    satellites = const_data.get('satellites', [])
                    for sat in satellites:
                        sat_fields = set(sat.keys())
                        if not required_fields.issubset(sat_fields):
                            return False
            
            return True
        except:
            return False
    
    def _extract_timestamps(self, data: Dict[str, Any]) -> List[str]:
        """提取數據中的時間戳"""
        timestamps = []
        
        def extract_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in ['timestamp', 'processing_timestamp', 'integration_timestamp']:
                        if isinstance(value, str):
                            timestamps.append(value)
                    elif isinstance(value, (dict, list)):
                        extract_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_recursive(item)
        
        extract_recursive(data)
        return timestamps
    
    def _count_validation_markers(self, integrated_data: Dict[str, Any]) -> Dict[str, int]:
        """統計驗證標記"""
        markers = {
            'satellite_cross_references': 0,
            'data_point_cross_checks': 0,
            'inconsistencies_found': 0
        }
        
        try:
            # 在數據中尋找驗證相關的標記或字段
            data_str = json.dumps(integrated_data, default=str).lower()
            
            # 計算交叉驗證標記
            if 'cross_validated' in data_str:
                markers['data_point_cross_checks'] = data_str.count('cross_validated')
            
            if 'verified' in data_str:
                markers['satellite_cross_references'] = data_str.count('verified')
            
            if 'inconsistent' in data_str or 'conflict' in data_str:
                markers['inconsistencies_found'] = data_str.count('inconsistent') + data_str.count('conflict')
        
        except:
            pass
        
        return markers
    
    def _count_total_data_points(self, integrated_data: Dict[str, Any]) -> int:
        """統計總數據點數量"""
        try:
            total = 0
            if 'constellations' in integrated_data:
                for const_name, const_data in integrated_data['constellations'].items():
                    satellites = const_data.get('satellites', [])
                    total += len(satellites)
            return total
        except:
            return 0
    
    def _check_multi_source_cross_validation(self, data: Dict[str, Any]) -> bool:
        """檢查多源交叉驗證"""
        try:
            # 檢查是否有多個數據來源的標記
            data_sources = len(data.keys()) if isinstance(data, dict) else 0
            
            # 檢查是否有交叉驗證標記
            data_str = json.dumps(data, default=str).lower()
            has_cross_validation = any(marker in data_str for marker in [
                'cross_validated', 'multi_source', 'validated_against', 'compared_with'
            ])
            
            return data_sources >= 2 and has_cross_validation
        except:
            return False
    
    def _check_data_provenance_tracking(self, data: Dict[str, Any]) -> bool:
        """檢查數據溯源跟踪"""
        try:
            # 檢查是否有數據來源記錄
            data_str = json.dumps(data, default=str).lower()
            provenance_indicators = [
                'source', 'origin', 'provenance', 'data_source', 'input_from'
            ]
            
            return any(indicator in data_str for indicator in provenance_indicators)
        except:
            return False
    
    def _check_integration_method_documentation(self, data: Dict[str, Any]) -> bool:
        """檢查整合方法記錄"""
        try:
            # 檢查是否有整合方法的記錄
            if isinstance(data, dict):
                metadata = data.get('metadata', {})
                integration_info = data.get('integration_info', {})
                
                # 檢查元數據中的整合方法記錄
                method_indicators = [
                    'integration_method', 'merge_strategy', 'combination_method',
                    'processing_algorithm', 'integration_algorithm'
                ]
                
                for indicator in method_indicators:
                    if indicator in metadata or indicator in integration_info:
                        return True
            
            return False
        except:
            return False
    
    def _check_forbidden_integration_patterns(self, data: Dict[str, Any]) -> List[str]:
        """檢查禁止的整合模式"""
        forbidden = []
        
        try:
            data_str = json.dumps(data, default=str).lower()
            
            if 'arbitrary' in data_str and 'merge' in data_str:
                forbidden.append("任意合併數據")
            
            if 'unverified' in data_str and 'integration' in data_str:
                forbidden.append("未驗證的整合")
            
            if 'mock' in data_str or 'simulated' in data_str:
                forbidden.append("模擬數據整合")
            
            if 'assumed' in data_str or 'estimated' in data_str:
                forbidden.append("基於假設的整合")
        
        except:
            pass
        
        return forbidden
    
    def _validate_processing_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """驗證處理指標"""
        try:
            validation_result = {
                'success': True,
                'issues': []
            }
            
            # 檢查基本指標
            required_metrics = ['input_sources', 'integrated_satellites', 'processing_time']
            for metric in required_metrics:
                if metric not in metrics:
                    validation_result['issues'].append(f"缺少必要指標: {metric}")
                    validation_result['success'] = False
            
            # 檢查整合效率
            if 'processing_time' in metrics and metrics['processing_time'] > 600:  # 10分鐘
                validation_result['issues'].append("數據整合時間過長，可能存在效率問題")
            
            # 檢查整合完整性
            if 'integration_completeness' in metrics and metrics['integration_completeness'] < 0.9:
                validation_result['issues'].append("數據整合完整性不足90%")
            
            return validation_result
            
        except Exception as e:
            return {
                'success': False,
                'issues': [str(e)]
            }