#!/usr/bin/env python3
"""
數據完整性檢查和驗證系統 - Phase 0
支援 TLE 數據格式驗證、品質評分、完整性檢查
"""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import math

logger = logging.getLogger(__name__)

class DataIntegrityValidator:
    """數據完整性檢查和驗證系統"""
    
    def __init__(self, tle_data_dir: str = "/app/tle_data"):
        """
        初始化數據完整性驗證器
        
        Args:
            tle_data_dir: TLE 數據根目錄
        """
        self.tle_data_dir = Path(tle_data_dir)
        self.supported_constellations = ['starlink', 'oneweb']
        
        # 衛星軌道參數的合理範圍
        self.orbit_parameter_ranges = {
            'starlink': {
                'inclination': (52.0, 54.0),  # 傾角 (度)
                'eccentricity': (0.0, 0.02),  # 偏心率
                'period_minutes': (90, 110),   # 軌道週期 (分鐘)
                'altitude_km': (200, 600),     # 高度 (公里)
                'mean_motion': (14.5, 16.5)   # 平均運動 (每日公轉數)
            },
            'oneweb': {
                'inclination': (86.0, 88.0),  # 極地軌道
                'eccentricity': (0.0, 0.02),
                'period_minutes': (105, 115),
                'altitude_km': (1100, 1300),  # LEO 高軌道
                'mean_motion': (12.8, 14.0)
            }
        }
        
        logger.info(f"DataIntegrityValidator 初始化，數據目錄: {self.tle_data_dir}")
    
    def validate_tle_format(self, name_line: str, line1: str, line2: str) -> Dict[str, Any]:
        """
        驗證單個 TLE 條目的格式正確性
        
        Args:
            name_line: 衛星名稱行
            line1: TLE 第一行
            line2: TLE 第二行
            
        Returns:
            Dict: 驗證結果
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'extracted_data': {}
        }
        
        # 1. 基礎格式檢查
        if not line1.startswith('1 '):
            validation_result['valid'] = False
            validation_result['errors'].append("Line 1 must start with '1 '")
            
        if not line2.startswith('2 '):
            validation_result['valid'] = False
            validation_result['errors'].append("Line 2 must start with '2 '")
            
        if len(line1) != 69:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Line 1 must be 69 characters, got {len(line1)}")
            
        if len(line2) != 69:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Line 2 must be 69 characters, got {len(line2)}")
        
        # 2. 數據提取和驗證
        try:
            # 提取基本數據
            norad_id = int(line1[2:7].strip())
            classification = line1[7]
            international_designator = line1[9:17].strip()
            epoch_year = int(line1[18:20])
            epoch_day = float(line1[20:32])
            
            # Line 2 數據
            inclination = float(line2[8:16])
            raan = float(line2[17:25])  # 升交點赤經
            eccentricity = float('0.' + line2[26:33])
            arg_perigee = float(line2[34:42])  # 近地點角距
            mean_anomaly = float(line2[43:51])
            mean_motion = float(line2[52:63])
            revolution_number = int(line2[63:68])
            
            validation_result['extracted_data'] = {
                'norad_id': norad_id,
                'name': name_line.strip(),
                'classification': classification,
                'international_designator': international_designator,
                'epoch_year': epoch_year,
                'epoch_day': epoch_day,
                'inclination': inclination,
                'raan': raan,
                'eccentricity': eccentricity,
                'arg_perigee': arg_perigee,
                'mean_anomaly': mean_anomaly,
                'mean_motion': mean_motion,
                'revolution_number': revolution_number
            }
            
            # 3. 範圍驗證
            if not (1 <= norad_id <= 99999):
                validation_result['warnings'].append(f"Unusual NORAD ID: {norad_id}")
                
            if not (0 <= inclination <= 180):
                validation_result['errors'].append(f"Invalid inclination: {inclination}")
                validation_result['valid'] = False
                
            if not (0 <= eccentricity <= 1):
                validation_result['errors'].append(f"Invalid eccentricity: {eccentricity}")
                validation_result['valid'] = False
                
            if not (0 <= mean_motion <= 20):
                validation_result['warnings'].append(f"Unusual mean motion: {mean_motion}")
                
        except (ValueError, IndexError) as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"Data extraction error: {e}")
        
        return validation_result
    
    def validate_constellation_parameters(self, tle_data: Dict[str, Any], constellation: str) -> Dict[str, Any]:
        """
        驗證衛星是否符合指定星座的軌道參數特徵
        
        Args:
            tle_data: 從 TLE 提取的軌道數據
            constellation: 星座名稱
            
        Returns:
            Dict: 驗證結果
        """
        validation_result = {
            'constellation_match': True,
            'parameter_checks': {},
            'warnings': [],
            'confidence_score': 0.0
        }
        
        if constellation not in self.orbit_parameter_ranges:
            validation_result['constellation_match'] = False
            validation_result['warnings'].append(f"Unknown constellation: {constellation}")
            return validation_result
        
        ranges = self.orbit_parameter_ranges[constellation]
        checks_passed = 0
        total_checks = 0
        
        # 檢查傾角
        inclination = tle_data.get('inclination', 0)
        inc_min, inc_max = ranges['inclination']
        inc_check = inc_min <= inclination <= inc_max
        validation_result['parameter_checks']['inclination'] = {
            'value': inclination,
            'range': f"{inc_min}-{inc_max}°",
            'passed': inc_check
        }
        if inc_check:
            checks_passed += 1
        total_checks += 1
        
        # 檢查偏心率
        eccentricity = tle_data.get('eccentricity', 0)
        ecc_min, ecc_max = ranges['eccentricity']
        ecc_check = ecc_min <= eccentricity <= ecc_max
        validation_result['parameter_checks']['eccentricity'] = {
            'value': eccentricity,
            'range': f"{ecc_min}-{ecc_max}",
            'passed': ecc_check
        }
        if ecc_check:
            checks_passed += 1
        total_checks += 1
        
        # 檢查平均運動
        mean_motion = tle_data.get('mean_motion', 0)
        mm_min, mm_max = ranges['mean_motion']
        mm_check = mm_min <= mean_motion <= mm_max
        validation_result['parameter_checks']['mean_motion'] = {
            'value': mean_motion,
            'range': f"{mm_min}-{mm_max} rev/day",
            'passed': mm_check
        }
        if mm_check:
            checks_passed += 1
        total_checks += 1
        
        # 計算置信度分數
        validation_result['confidence_score'] = (checks_passed / total_checks) * 100
        
        # 判斷是否匹配星座特徵
        if validation_result['confidence_score'] < 60:
            validation_result['constellation_match'] = False
            validation_result['warnings'].append(f"Low constellation match confidence: {validation_result['confidence_score']:.1f}%")
        
        return validation_result
    
    def validate_file_integrity(self, file_path) -> Dict[str, Any]:
        """
        驗證 TLE 文件的完整性
        
        Args:
            file_path: TLE 文件路徑
            
        Returns:
            Dict: 驗證結果
        """
        # 確保 file_path 是 Path 物件
        if isinstance(file_path, str):
            file_path = Path(file_path)
            
        validation_result = {
            'file_path': str(file_path),
            'valid': True,
            'total_satellites': 0,
            'valid_satellites': 0,
            'errors': [],
            'warnings': [],
            'file_stats': {},
            'sample_validations': []
        }
        
        try:
            # 文件基本檢查
            if not file_path.exists():
                validation_result['valid'] = False
                validation_result['errors'].append("File does not exist")
                return validation_result
            
            file_size = file_path.stat().st_size
            if file_size == 0:
                validation_result['valid'] = False
                validation_result['errors'].append("File is empty")
                return validation_result
            
            validation_result['file_stats']['size_bytes'] = file_size
            validation_result['file_stats']['size_mb'] = file_size / (1024 * 1024)
            
            # 讀取並解析文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            lines = [line.strip() for line in lines if line.strip()]
            
            validation_result['file_stats']['total_lines'] = len(lines)
            
            # 解析 TLE 條目
            i = 0
            while i < len(lines):
                if i + 2 < len(lines):
                    name_line = lines[i]
                    line1 = lines[i + 1]
                    line2 = lines[i + 2]
                    
                    validation_result['total_satellites'] += 1
                    
                    # 驗證 TLE 格式
                    tle_validation = self.validate_tle_format(name_line, line1, line2)
                    
                    if tle_validation['valid']:
                        validation_result['valid_satellites'] += 1
                        
                        # 保存前5個樣本的驗證結果
                        if len(validation_result['sample_validations']) < 5:
                            validation_result['sample_validations'].append({
                                'satellite_name': name_line.strip(),
                                'validation': tle_validation
                            })
                    else:
                        validation_result['errors'].extend([
                            f"Satellite {name_line.strip()}: {error}" 
                            for error in tle_validation['errors']
                        ])
                    
                    i += 3
                else:
                    validation_result['warnings'].append(f"Incomplete TLE entry at line {i+1}")
                    i += 1
            
            # 計算統計數據
            if validation_result['total_satellites'] > 0:
                success_rate = (validation_result['valid_satellites'] / validation_result['total_satellites']) * 100
                validation_result['file_stats']['success_rate_percent'] = success_rate
                
                if success_rate < 95:
                    validation_result['warnings'].append(f"Low success rate: {success_rate:.1f}%")
                    
                if success_rate < 80:
                    validation_result['valid'] = False
                    validation_result['errors'].append(f"Unacceptable success rate: {success_rate:.1f}%")
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"File processing error: {e}")
        
        return validation_result
    
    def validate_data_continuity(self, constellation: str) -> Dict[str, Any]:
        """
        驗證數據的時間連續性
        
        Args:
            constellation: 星座名稱
            
        Returns:
            Dict: 連續性驗證結果
        """
        validation_result = {
            'constellation': constellation,
            'continuous': True,
            'date_gaps': [],
            'coverage_stats': {},
            'recommendations': []
        }
        
        tle_dir = self.tle_data_dir / constellation / "tle"
        if not tle_dir.exists():
            validation_result['continuous'] = False
            validation_result['recommendations'].append(f"Create TLE directory: {tle_dir}")
            return validation_result
        
        # 掃描所有可用日期
        available_dates = []
        import glob
        
        for tle_file in glob.glob(str(tle_dir / f"{constellation}_*.tle")):
            match = re.search(r'(\d{8})\.tle$', tle_file)
            if match:
                date_str = match.group(1)
                file_path = Path(tle_file)
                if file_path.exists() and file_path.stat().st_size > 0:
                    available_dates.append(date_str)
        
        available_dates.sort()
        
        if not available_dates:
            validation_result['continuous'] = False
            validation_result['recommendations'].append("No valid data files found")
            return validation_result
        
        validation_result['coverage_stats'] = {
            'total_days': len(available_dates),
            'start_date': available_dates[0],
            'end_date': available_dates[-1],
            'available_dates': available_dates
        }
        
        # 檢查日期間隔
        from datetime import datetime, timedelta
        
        expected_dates = []
        start_date = datetime.strptime(available_dates[0], '%Y%m%d')
        end_date = datetime.strptime(available_dates[-1], '%Y%m%d')
        
        current_date = start_date
        while current_date <= end_date:
            expected_dates.append(current_date.strftime('%Y%m%d'))
            current_date += timedelta(days=1)
        
        # 找出缺失的日期
        available_set = set(available_dates)
        expected_set = set(expected_dates)
        missing_dates = sorted(list(expected_set - available_set))
        
        if missing_dates:
            validation_result['continuous'] = False
            validation_result['date_gaps'] = missing_dates
            validation_result['recommendations'].extend([
                f"Collect data for missing date: {date}" for date in missing_dates[:5]
            ])
            if len(missing_dates) > 5:
                validation_result['recommendations'].append(f"... and {len(missing_dates) - 5} more dates")
        
        # 計算覆蓋率
        coverage_rate = (len(available_dates) / len(expected_dates)) * 100
        validation_result['coverage_stats']['coverage_rate_percent'] = coverage_rate
        
        if coverage_rate < 80:
            validation_result['continuous'] = False
            validation_result['recommendations'].append(f"Improve data coverage (current: {coverage_rate:.1f}%)")
        
        return validation_result
    
    def generate_comprehensive_report(self, constellation: str = None) -> Dict[str, Any]:
        """
        生成綜合數據完整性報告
        
        Args:
            constellation: 指定星座，None 表示檢查所有星座
            
        Returns:
            Dict: 綜合報告
        """
        report = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'data_directory': str(self.tle_data_dir),
            'constellations': {},
            'overall_summary': {
                'total_constellations': 0,
                'valid_constellations': 0,
                'total_files': 0,
                'valid_files': 0,
                'total_satellites': 0,
                'valid_satellites': 0
            },
            'recommendations': []
        }
        
        constellations_to_check = [constellation] if constellation else self.supported_constellations
        
        for const in constellations_to_check:
            logger.info(f"生成 {const} 星座報告...")
            
            constellation_report = {
                'name': const,
                'file_validations': [],
                'continuity_check': {},
                'summary': {
                    'total_files': 0,
                    'valid_files': 0,
                    'total_satellites': 0,
                    'valid_satellites': 0,
                    'overall_valid': True
                }
            }
            
            # 1. 文件完整性檢查
            tle_dir = self.tle_data_dir / const / "tle"
            if tle_dir.exists():
                import glob
                tle_files = glob.glob(str(tle_dir / f"{const}_*.tle"))
                
                for tle_file in tle_files:
                    file_validation = self.validate_file_integrity(Path(tle_file))
                    constellation_report['file_validations'].append(file_validation)
                    
                    constellation_report['summary']['total_files'] += 1
                    if file_validation['valid']:
                        constellation_report['summary']['valid_files'] += 1
                    else:
                        constellation_report['summary']['overall_valid'] = False
                    
                    constellation_report['summary']['total_satellites'] += file_validation['total_satellites']
                    constellation_report['summary']['valid_satellites'] += file_validation['valid_satellites']
            
            # 2. 時間連續性檢查
            continuity_result = self.validate_data_continuity(const)
            constellation_report['continuity_check'] = continuity_result
            
            if not continuity_result['continuous']:
                constellation_report['summary']['overall_valid'] = False
            
            # 3. 更新總體統計
            report['overall_summary']['total_constellations'] += 1
            if constellation_report['summary']['overall_valid']:
                report['overall_summary']['valid_constellations'] += 1
            
            report['overall_summary']['total_files'] += constellation_report['summary']['total_files']
            report['overall_summary']['valid_files'] += constellation_report['summary']['valid_files']
            report['overall_summary']['total_satellites'] += constellation_report['summary']['total_satellites']
            report['overall_summary']['valid_satellites'] += constellation_report['summary']['valid_satellites']
            
            report['constellations'][const] = constellation_report
        
        # 4. 生成建議
        overall_file_success_rate = (report['overall_summary']['valid_files'] / 
                                   max(1, report['overall_summary']['total_files'])) * 100
        overall_satellite_success_rate = (report['overall_summary']['valid_satellites'] / 
                                        max(1, report['overall_summary']['total_satellites'])) * 100
        
        if overall_file_success_rate < 95:
            report['recommendations'].append(f"Improve file validation rate (current: {overall_file_success_rate:.1f}%)")
            
        if overall_satellite_success_rate < 98:
            report['recommendations'].append(f"Improve satellite data quality (current: {overall_satellite_success_rate:.1f}%)")
        
        # 收集所有星座的建議
        for const_report in report['constellations'].values():
            if const_report['continuity_check'].get('recommendations'):
                report['recommendations'].extend(const_report['continuity_check']['recommendations'])
        
        logger.info(f"綜合報告生成完成，檢查了 {len(constellations_to_check)} 個星座")
        return report
    
    def export_report_to_file(self, report: Dict[str, Any], output_path: str = None) -> str:
        """
        將報告導出到文件
        
        Args:
            report: 驗證報告
            output_path: 輸出文件路徑，None 則自動生成
            
        Returns:
            str: 實際的輸出文件路徑
        """
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"/app/data/reports/data_integrity_report_{timestamp}.json"
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"數據完整性報告已導出到: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"導出報告失敗: {e}")
            raise

def main():
    """測試主程序"""
    print("🔍 Phase 0 數據完整性檢查和驗證系統")
    print("=" * 60)
    
    # 初始化驗證器
    validator = DataIntegrityValidator()
    
    # 生成綜合報告
    print("\n📋 生成綜合數據完整性報告...")
    report = validator.generate_comprehensive_report()
    
    # 顯示摘要
    print(f"\n📊 總體摘要:")
    print(f"  - 檢查星座數: {report['overall_summary']['total_constellations']}")
    print(f"  - 有效星座數: {report['overall_summary']['valid_constellations']}")
    print(f"  - 總文件數: {report['overall_summary']['total_files']}")
    print(f"  - 有效文件數: {report['overall_summary']['valid_files']}")
    print(f"  - 總衛星數: {report['overall_summary']['total_satellites']}")
    print(f"  - 有效衛星數: {report['overall_summary']['valid_satellites']}")
    
    # 顯示各星座狀態
    for const_name, const_report in report['constellations'].items():
        print(f"\n🛰️ {const_name.upper()} 星座:")
        print(f"  - 文件數: {const_report['summary']['total_files']}")
        print(f"  - 有效文件數: {const_report['summary']['valid_files']}")
        print(f"  - 衛星數: {const_report['summary']['total_satellites']}")
        print(f"  - 數據連續性: {'✅' if const_report['continuity_check']['continuous'] else '❌'}")
        print(f"  - 覆蓋率: {const_report['continuity_check']['coverage_stats'].get('coverage_rate_percent', 0):.1f}%")
    
    # 顯示建議
    if report['recommendations']:
        print(f"\n💡 改進建議:")
        for i, rec in enumerate(report['recommendations'][:5], 1):
            print(f"  {i}. {rec}")
        if len(report['recommendations']) > 5:
            print(f"  ... 以及其他 {len(report['recommendations']) - 5} 項建議")
    
    # 導出報告
    report_file = validator.export_report_to_file(report)
    print(f"\n📄 詳細報告已保存至: {report_file}")
    
    print("\n🎉 數據完整性檢查完成")

if __name__ == "__main__":
    main()