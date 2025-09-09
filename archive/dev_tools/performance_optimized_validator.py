#!/usr/bin/env python3
"""
性能優化驗證器 - Phase 3.5
===========================

實施可配置的驗證級別以大幅降低性能開銷：
- 快速驗證 (FAST): 關鍵檢查項目 (~5% 開銷)
- 標準驗證 (STANDARD): 平衡檢查 (~10% 開銷) 
- 完整驗證 (COMPREHENSIVE): 所有檢查 (~15% 開銷)

包含智能緩存機制和並行驗證支持
"""

import asyncio
import time
import hashlib
from typing import Dict, Any, List, Optional, Set
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
import logging

# 設置日誌
logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """驗證級別枚舉"""
    FAST = "fast"                    # 快速驗證：僅關鍵檢查
    STANDARD = "standard"            # 標準驗證：平衡檢查
    COMPREHENSIVE = "comprehensive"  # 完整驗證：所有檢查

@dataclass
class ValidationResult:
    """驗證結果數據類別"""
    passed: bool
    level: ValidationLevel
    execution_time_ms: float
    checks_performed: int
    total_available_checks: int
    cached_results: int
    details: Dict[str, Any]
    issues: List[str]

class ValidationCache:
    """驗證結果緩存系統"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.cache = {}
        self.timestamps = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
    
    def _generate_key(self, data: Dict[str, Any], validation_type: str) -> str:
        """生成緩存鍵"""
        # 使用關鍵字段生成穩定的哈希值
        key_data = {
            'validation_type': validation_type,
            'satellite_count': len(data.get('satellites', [])),
            'metadata_hash': hash(str(data.get('metadata', {}))),
            'constellation_count': len(data.get('constellations', {}))
        }
        return hashlib.md5(str(key_data).encode()).hexdigest()
    
    def get(self, data: Dict[str, Any], validation_type: str) -> Optional[Dict[str, Any]]:
        """獲取緩存的驗證結果"""
        key = self._generate_key(data, validation_type)
        
        if key in self.cache:
            # 檢查是否過期
            if time.time() - self.timestamps[key] < self.ttl_seconds:
                logger.debug(f"緩存命中: {validation_type}")
                return self.cache[key]
            else:
                # 清理過期緩存
                del self.cache[key]
                del self.timestamps[key]
        
        return None
    
    def set(self, data: Dict[str, Any], validation_type: str, result: Dict[str, Any]):
        """設置緩存結果"""
        key = self._generate_key(data, validation_type)
        
        # 檢查緩存大小限制
        if len(self.cache) >= self.max_size:
            # 清理最舊的緩存項目
            oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
        
        self.cache[key] = result
        self.timestamps[key] = time.time()
        logger.debug(f"緩存設置: {validation_type}")

class PerformanceOptimizedValidator:
    """性能優化驗證器"""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.validation_level = validation_level
        self.cache = ValidationCache()
        self.performance_metrics = {
            'total_validations': 0,
            'cache_hits': 0,
            'average_execution_time': 0.0
        }
    
    def validate_stage1_optimized(self, processing_results: Dict[str, Any]) -> ValidationResult:
        """Stage 1 優化驗證 - 軌道計算"""
        start_time = time.time()
        
        # 檢查緩存
        cached_result = self.cache.get(processing_results, 'stage1')
        if cached_result:
            self.performance_metrics['cache_hits'] += 1
            return ValidationResult(
                passed=cached_result['passed'],
                level=self.validation_level,
                execution_time_ms=0.1,  # 緩存幾乎無時間開銷
                checks_performed=cached_result['checks_performed'],
                total_available_checks=cached_result['total_available_checks'],
                cached_results=1,
                details=cached_result['details'],
                issues=cached_result['issues']
            )
        
        checks = {}
        issues = []
        
        # 根據驗證級別選擇檢查項目
        if self.validation_level == ValidationLevel.FAST:
            checks.update(self._stage1_fast_checks(processing_results, issues))
        elif self.validation_level == ValidationLevel.STANDARD:
            checks.update(self._stage1_fast_checks(processing_results, issues))
            checks.update(self._stage1_standard_checks(processing_results, issues))
        else:  # COMPREHENSIVE
            checks.update(self._stage1_fast_checks(processing_results, issues))
            checks.update(self._stage1_standard_checks(processing_results, issues))
            checks.update(self._stage1_comprehensive_checks(processing_results, issues))
        
        # 計算結果
        passed_checks = sum(1 for passed in checks.values() if passed)
        total_checks = len(checks)
        overall_passed = passed_checks == total_checks
        
        execution_time = (time.time() - start_time) * 1000  # 轉換為毫秒
        
        # 緩存結果
        cache_data = {
            'passed': overall_passed,
            'checks_performed': total_checks,
            'total_available_checks': self._get_total_stage1_checks(),
            'details': checks,
            'issues': issues
        }
        self.cache.set(processing_results, 'stage1', cache_data)
        
        # 更新性能指標
        self.performance_metrics['total_validations'] += 1
        current_avg = self.performance_metrics['average_execution_time']
        total_validations = self.performance_metrics['total_validations']
        self.performance_metrics['average_execution_time'] = (
            (current_avg * (total_validations - 1) + execution_time) / total_validations
        )
        
        return ValidationResult(
            passed=overall_passed,
            level=self.validation_level,
            execution_time_ms=execution_time,
            checks_performed=total_checks,
            total_available_checks=self._get_total_stage1_checks(),
            cached_results=0,
            details=checks,
            issues=issues
        )
    
    def _stage1_fast_checks(self, processing_results: Dict[str, Any], issues: List[str]) -> Dict[str, bool]:
        """Stage 1 快速檢查 - 僅關鍵項目"""
        checks = {}
        
        # 1. 基本數據存在性檢查
        constellations = processing_results.get('constellations', {})
        checks["數據存在性"] = bool(constellations)
        
        if not constellations:
            issues.append("缺少星座數據")
            return checks
        
        # 2. 星座完整性檢查
        constellation_names = [name.lower() for name in constellations.keys()]
        required_constellations = ['starlink', 'oneweb']
        checks["星座完整性"] = all(name in constellation_names for name in required_constellations)
        
        if not checks["星座完整性"]:
            missing = [name for name in required_constellations if name not in constellation_names]
            issues.append(f"缺少星座數據: {', '.join(missing)}")
        
        # 3. 衛星數量合理性檢查
        total_satellites = sum(len(data.get('satellites', [])) for data in constellations.values())
        checks["衛星數量合理性"] = total_satellites > 100  # 最基本的數量檢查
        
        if not checks["衛星數量合理性"]:
            issues.append(f"衛星數量過少: {total_satellites}")
        
        return checks
    
    def _stage1_standard_checks(self, processing_results: Dict[str, Any], issues: List[str]) -> Dict[str, bool]:
        """Stage 1 標準檢查 - 平衡性能和覆蓋度"""
        checks = {}
        
        constellations = processing_results.get('constellations', {})
        
        # 4. SGP4計算完整性檢查 (抽樣)
        sample_satellites = []
        for constellation_data in constellations.values():
            satellites = constellation_data.get('satellites', [])
            # 抽樣檢查：每個星座最多檢查10顆衛星
            sample_satellites.extend(satellites[:10])
        
        sgp4_valid_count = 0
        for sat in sample_satellites[:20]:  # 總共最多檢查20顆衛星
            timeseries = sat.get('position_timeseries', [])
            if len(timeseries) >= 100:  # 基本完整性檢查
                sgp4_valid_count += 1
        
        checks["SGP4計算完整性"] = sgp4_valid_count >= len(sample_satellites) * 0.8 if sample_satellites else False
        
        if not checks["SGP4計算完整性"]:
            issues.append(f"SGP4計算完整性不足: {sgp4_valid_count}/{len(sample_satellites)}")
        
        # 5. ECI座標零值檢測 (重點檢查OneWeb)
        oneweb_data = constellations.get('oneweb', {})
        oneweb_satellites = oneweb_data.get('satellites', [])
        
        zero_eci_count = 0
        checked_oneweb = 0
        
        for sat in oneweb_satellites[:5]:  # 檢查前5顆OneWeb衛星
            timeseries = sat.get('position_timeseries', [])
            if timeseries:
                first_point = timeseries[0]
                position_eci = first_point.get('position_eci', {})
                if position_eci:
                    x, y, z = position_eci.get('x', 0), position_eci.get('y', 0), position_eci.get('z', 0)
                    if x == 0 and y == 0 and z == 0:
                        zero_eci_count += 1
                    checked_oneweb += 1
        
        checks["ECI零值檢測"] = zero_eci_count == 0 if checked_oneweb > 0 else True
        
        if not checks["ECI零值檢測"]:
            issues.append(f"發現 {zero_eci_count} 個零值ECI座標")
        
        return checks
    
    def _stage1_comprehensive_checks(self, processing_results: Dict[str, Any], issues: List[str]) -> Dict[str, bool]:
        """Stage 1 完整檢查 - 所有驗證項目"""
        checks = {}
        
        constellations = processing_results.get('constellations', {})
        
        # 6. 軌道參數物理邊界驗證
        physics_valid_count = 0
        total_checked = 0
        
        for constellation_data in constellations.values():
            satellites = constellation_data.get('satellites', [])
            for sat in satellites[:5]:  # 每個星座檢查5顆衛星
                timeseries = sat.get('position_timeseries', [])
                if timeseries:
                    first_point = timeseries[0]
                    position_eci = first_point.get('position_eci', {})
                    if position_eci:
                        x, y, z = position_eci.get('x', 0), position_eci.get('y', 0), position_eci.get('z', 0)
                        distance_km = (x*x + y*y + z*z)**0.5
                        
                        # LEO高度檢查 (200-2000km + 地球半徑6371km)
                        if 6500 <= distance_km <= 8400:
                            physics_valid_count += 1
                        total_checked += 1
        
        checks["軌道參數物理邊界"] = physics_valid_count >= total_checked * 0.9 if total_checked > 0 else True
        
        if not checks["軌道參數物理邊界"]:
            issues.append(f"軌道參數超出物理邊界: {total_checked - physics_valid_count}/{total_checked}")
        
        # 7. 時間基準準確性檢查
        metadata = processing_results.get('metadata', {})
        calculation_time = metadata.get('calculation_base_time')
        
        checks["時間基準準確性"] = bool(calculation_time and 'UTC' in str(calculation_time))
        
        if not checks["時間基準準確性"]:
            issues.append("時間基準不是UTC標準時間")
        
        # 8. 統一格式合規檢查
        old_format_satellites = processing_results.get('satellites', [])
        checks["統一格式合規"] = len(old_format_satellites) == 0
        
        if not checks["統一格式合規"]:
            issues.append(f"發現舊格式冗餘數據: {len(old_format_satellites)} 個衛星")
        
        return checks
    
    def _get_total_stage1_checks(self) -> int:
        """獲取 Stage 1 總檢查項目數"""
        return 8  # 當前實施的總檢查項目數
    
    async def validate_stage_async(self, stage_name: str, processing_results: Dict[str, Any]) -> ValidationResult:
        """異步驗證接口"""
        if stage_name == 'stage1':
            return await asyncio.get_event_loop().run_in_executor(
                None, self.validate_stage1_optimized, processing_results
            )
        else:
            raise ValueError(f"不支援的階段: {stage_name}")
    
    def get_performance_report(self) -> Dict[str, Any]:
        """獲取性能報告"""
        cache_hit_rate = (
            self.performance_metrics['cache_hits'] / self.performance_metrics['total_validations'] * 100
            if self.performance_metrics['total_validations'] > 0 else 0
        )
        
        return {
            'validation_level': self.validation_level.value,
            'total_validations': self.performance_metrics['total_validations'],
            'cache_hits': self.performance_metrics['cache_hits'],
            'cache_hit_rate_percent': cache_hit_rate,
            'average_execution_time_ms': self.performance_metrics['average_execution_time'],
            'cache_size': len(self.cache.cache),
            'estimated_performance_improvement': f"{cache_hit_rate:.1f}% 時間節省"
        }

class ValidationLevelManager:
    """驗證級別管理器"""
    
    def __init__(self):
        self.validators = {}
        self._create_validators()
    
    def _create_validators(self):
        """創建不同級別的驗證器"""
        for level in ValidationLevel:
            self.validators[level] = PerformanceOptimizedValidator(level)
    
    def get_validator(self, level: ValidationLevel) -> PerformanceOptimizedValidator:
        """獲取指定級別的驗證器"""
        return self.validators[level]
    
    def recommend_level(self, system_load: float, time_constraint: float) -> ValidationLevel:
        """根據系統負載和時間約束推薦驗證級別"""
        if system_load > 80 or time_constraint < 30:  # 高負載或時間緊迫
            return ValidationLevel.FAST
        elif system_load > 50 or time_constraint < 60:  # 中等負載
            return ValidationLevel.STANDARD
        else:  # 低負載且時間充裕
            return ValidationLevel.COMPREHENSIVE
    
    def get_all_performance_reports(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有級別的性能報告"""
        reports = {}
        for level, validator in self.validators.items():
            reports[level.value] = validator.get_performance_report()
        return reports

# 全局驗證級別管理器實例
validation_manager = ValidationLevelManager()

# 便捷函數
def validate_with_level(stage_name: str, processing_results: Dict[str, Any], 
                       level: ValidationLevel = ValidationLevel.STANDARD) -> ValidationResult:
    """使用指定級別進行驗證"""
    validator = validation_manager.get_validator(level)
    if stage_name == 'stage1':
        return validator.validate_stage1_optimized(processing_results)
    else:
        raise ValueError(f"不支援的階段: {stage_name}")

def get_recommended_level(system_load: float = 50.0, time_constraint: float = 120.0) -> ValidationLevel:
    """獲取推薦的驗證級別"""
    return validation_manager.recommend_level(system_load, time_constraint)

if __name__ == "__main__":
    # 測試範例
    import json
    
    # 模擬測試數據
    test_data = {
        'constellations': {
            'starlink': {
                'satellites': [
                    {
                        'position_timeseries': [
                            {
                                'position_eci': {'x': 7000, 'y': 0, 'z': 0},
                                'relative_to_observer': {'elevation_deg': 45}
                            }
                        ] * 150
                    }
                ] * 100
            },
            'oneweb': {
                'satellites': [
                    {
                        'position_timeseries': [
                            {
                                'position_eci': {'x': 7500, 'y': 0, 'z': 0},
                                'relative_to_observer': {'elevation_deg': 30}
                            }
                        ] * 150
                    }
                ] * 50
            }
        },
        'metadata': {
            'calculation_base_time': '2025-09-09T12:00:00Z UTC'
        }
    }
    
    # 測試不同驗證級別
    print("🧪 性能優化驗證器測試")
    print("=" * 50)
    
    for level in ValidationLevel:
        print(f"\n測試驗證級別: {level.value.upper()}")
        
        start_time = time.time()
        result = validate_with_level('stage1', test_data, level)
        end_time = time.time()
        
        print(f"  ✅ 驗證通過: {result.passed}")
        print(f"  ⏱️  執行時間: {result.execution_time_ms:.2f}ms")
        print(f"  📊 檢查項目: {result.checks_performed}/{result.total_available_checks}")
        print(f"  🚫 發現問題: {len(result.issues)}")
        
        if result.issues:
            for issue in result.issues:
                print(f"     - {issue}")
    
    print(f"\n📈 性能報告:")
    reports = validation_manager.get_all_performance_reports()
    for level, report in reports.items():
        if report['total_validations'] > 0:
            print(f"  {level.upper()}: {report['average_execution_time_ms']:.2f}ms 平均執行時間")