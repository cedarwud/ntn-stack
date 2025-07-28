#!/usr/bin/env python3
"""
測試本地 TLE 數據加載器 - Phase 0
"""

import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalTLELoader:
    """本地 TLE 數據加載器 - Phase 0 增強版本，支援實際日期命名"""
    
    def __init__(self, tle_data_dir: str = "/home/sat/ntn-stack/tle_data"):
        """
        初始化本地 TLE 數據加載器
        
        Args:
            tle_data_dir: TLE 數據根目錄，預設為 /home/sat/ntn-stack/tle_data
        """
        self.tle_data_dir = Path(tle_data_dir)
        logger.info(f"LocalTLELoader 初始化，數據目錄: {self.tle_data_dir}")
        
        # Phase 0 支援的星座
        self.supported_constellations = ['starlink', 'oneweb']
    
    def scan_available_dates(self, constellation: str) -> List[str]:
        """掃描指定星座的可用日期"""
        if constellation not in self.supported_constellations:
            logger.error(f"不支援的星座: {constellation}")
            return []
            
        tle_dir = self.tle_data_dir / constellation / "tle"
        if not tle_dir.exists():
            logger.warning(f"TLE 目錄不存在: {tle_dir}")
            return []
            
        available_dates = []
        pattern = f"{constellation}_*.tle"
        
        import glob
        import re
        
        for tle_file in glob.glob(str(tle_dir / pattern)):
            # 提取日期 (YYYYMMDD)
            match = re.search(r'(\d{8})\.tle$', tle_file)
            if match:
                date_str = match.group(1)
                # 驗證文件存在且非空
                if Path(tle_file).stat().st_size > 0:
                    available_dates.append(date_str)
                    
        available_dates.sort()
        logger.info(f"{constellation} 可用日期: {len(available_dates)} 天，範圍: {available_dates[0] if available_dates else 'N/A'} - {available_dates[-1] if available_dates else 'N/A'}")
        return available_dates
    
    def parse_tle_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """解析 TLE 文件"""
        satellites = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            lines = [line.strip() for line in lines if line.strip()]
            
            i = 0
            while i < len(lines):
                if i + 2 < len(lines):
                    name_line = lines[i].strip()
                    line1 = lines[i + 1].strip()
                    line2 = lines[i + 2].strip()
                    
                    # 驗證 TLE 格式
                    if (line1.startswith('1 ') and 
                        line2.startswith('2 ') and 
                        len(line1) >= 69 and 
                        len(line2) >= 69):
                        
                        try:
                            norad_id = int(line1[2:7].strip())
                            
                            satellite_data = {
                                'name': name_line,
                                'norad_id': norad_id,
                                'line1': line1,
                                'line2': line2,
                                'data_source': 'local_collection'
                            }
                            
                            satellites.append(satellite_data)
                            
                        except ValueError as e:
                            logger.warning(f"無法解析 NORAD ID: {line1[:10]} - {e}")
                    
                    i += 3
                else:
                    i += 1
                    
        except Exception as e:
            logger.error(f"解析 TLE 文件失敗 {file_path}: {e}")
            
        logger.debug(f"從 {file_path} 解析出 {len(satellites)} 顆衛星")
        return satellites
    
    def parse_json_file(self, file_path: Path) -> Optional[List[Dict[str, Any]]]:
        """解析 JSON 文件"""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                logger.debug(f"從 {file_path} 解析出 {len(data)} 筆 JSON 記錄")
                return data
            else:
                logger.warning(f"JSON 文件格式不正確: {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"解析 JSON 文件失敗 {file_path}: {e}")
            return None
    
    def load_collected_data(self, constellation: str = "starlink", 
                           start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """載入手動收集的TLE歷史數據"""
        if constellation not in self.supported_constellations:
            return {'error': f'不支援的星座: {constellation}'}
            
        tle_dir = self.tle_data_dir / constellation / "tle"
        json_dir = self.tle_data_dir / constellation / "json"
        
        if not tle_dir.exists():
            return {'error': f'TLE 目錄不存在: {tle_dir}'}
            
        collected_data = []
        available_dates = []
        
        import glob
        import re
        
        # 掃描所有可用的 TLE 檔案
        tle_pattern = str(tle_dir / f"{constellation}_*.tle")
        tle_files = glob.glob(tle_pattern)
        
        for tle_file in tle_files:
            # 提取實際日期 (YYYYMMDD)
            match = re.search(r'(\d{8})\.tle$', tle_file)
            if match:
                date_str = match.group(1)
                
                # 日期範圍過濾
                if start_date and date_str < start_date:
                    continue
                if end_date and date_str > end_date:
                    continue
                
                tle_path = Path(tle_file)
                json_path = json_dir / f"{constellation}_{date_str}.json"
                
                if tle_path.exists() and tle_path.stat().st_size > 0:
                    # 解析 TLE 數據
                    daily_tle_data = self.parse_tle_file(tle_path)
                    daily_json_data = None
                    
                    # 嘗試讀取對應的 JSON 數據
                    if json_path.exists() and json_path.stat().st_size > 0:
                        daily_json_data = self.parse_json_file(json_path)
                    
                    if daily_tle_data:
                        collected_data.append({
                            'date': date_str,
                            'tle_file': str(tle_path),
                            'json_file': str(json_path) if daily_json_data else None,
                            'satellites': daily_tle_data[:3],  # 只保留前3個作為樣本
                            'satellite_count': len(daily_tle_data),
                            'json_metadata': daily_json_data[:3] if daily_json_data else None,  # 只保留前3個作為樣本
                            'has_dual_format': daily_json_data is not None
                        })
                        available_dates.append(date_str)
        
        # 按日期排序
        collected_data.sort(key=lambda x: x['date'])
        available_dates.sort()
        
        return {
            'constellation': constellation,
            'total_days_collected': len(collected_data),
            'date_range': {
                'start': available_dates[0] if available_dates else None,
                'end': available_dates[-1] if available_dates else None,
                'available_dates': available_dates
            },
            'dual_format_coverage': sum(1 for d in collected_data if d['has_dual_format']),
            'coverage_percentage': len(collected_data) / len(available_dates) * 100 if available_dates else 0,
            'daily_data': collected_data
        }
    
    def get_data_coverage_status(self) -> Dict[str, Any]:
        """檢查手動收集數據的狀態和覆蓋率"""
        status = {'starlink': {}, 'oneweb': {}, 'overall': {}}
        
        # 獲取兩個星座的數據
        starlink_data = self.load_collected_data('starlink')
        oneweb_data = self.load_collected_data('oneweb')
        
        # 計算日期覆蓋範圍
        all_dates = set()
        starlink_dates = set()
        oneweb_dates = set()
        
        if 'date_range' in starlink_data and starlink_data['date_range']['available_dates']:
            starlink_dates = set(starlink_data['date_range']['available_dates'])
            all_dates.update(starlink_dates)
        
        if 'date_range' in oneweb_data and oneweb_data['date_range']['available_dates']:
            oneweb_dates = set(oneweb_data['date_range']['available_dates'])
            all_dates.update(oneweb_dates)
        
        status['starlink'] = {
            'days_collected': starlink_data.get('total_days_collected', 0),
            'dates': sorted(list(starlink_dates)),
            'dual_format_count': starlink_data.get('dual_format_coverage', 0),
            'dual_format_percentage': (starlink_data.get('dual_format_coverage', 0) / 
                                     starlink_data.get('total_days_collected', 1) * 100) if starlink_data.get('total_days_collected', 0) > 0 else 0
        }
        
        status['oneweb'] = {
            'days_collected': oneweb_data.get('total_days_collected', 0),
            'dates': sorted(list(oneweb_dates)),
            'dual_format_count': oneweb_data.get('dual_format_coverage', 0),
            'dual_format_percentage': (oneweb_data.get('dual_format_coverage', 0) / 
                                     oneweb_data.get('total_days_collected', 1) * 100) if oneweb_data.get('total_days_collected', 0) > 0 else 0
        }
        
        status['overall'] = {
            'total_unique_dates': len(all_dates),
            'date_range': {
                'start': min(all_dates) if all_dates else None,
                'end': max(all_dates) if all_dates else None
            },
            'common_dates': len(starlink_dates & oneweb_dates),
            'coverage_days': len(all_dates)
        }
        
        return status
    
    def validate_daily_data_quality(self, constellation: str, date_str: str) -> Dict[str, Any]:
        """驗證特定日期數據品質"""
        tle_path = self.tle_data_dir / constellation / "tle" / f"{constellation}_{date_str}.tle"
        json_path = self.tle_data_dir / constellation / "json" / f"{constellation}_{date_str}.json"
        
        if not tle_path.exists():
            return {'valid': False, 'error': 'TLE file not found', 'date': date_str}
            
        # 解析 TLE 數據
        satellites = self.parse_tle_file(tle_path)
        
        # 嘗試解析 JSON 數據
        json_data = None
        has_json = json_path.exists() and json_path.stat().st_size > 0
        if has_json:
            json_data = self.parse_json_file(json_path)
        
        validation_result = {
            'valid': True,
            'date': date_str,
            'satellite_count': len(satellites),
            'has_dual_format': has_json,
            'json_satellite_count': len(json_data) if json_data else 0,
            'format_errors': [],
            'orbit_warnings': [],
            'data_quality_score': 0
        }
        
        # 基礎驗證
        format_errors = 0
        orbit_warnings = 0
        
        for sat in satellites:
            # 簡單格式檢查
            if len(sat.get('line1', '')) < 69 or len(sat.get('line2', '')) < 69:
                format_errors += 1
                validation_result['format_errors'].append(f"Invalid TLE length: {sat.get('name', 'Unknown')}")
            
            # 基本軌道參數檢查
            try:
                if not (1 <= sat.get('norad_id', 0) <= 99999):
                    orbit_warnings += 1
                    validation_result['orbit_warnings'].append(f"Suspicious NORAD ID: {sat.get('name', 'Unknown')}")
            except:
                orbit_warnings += 1
        
        # 計算品質分數
        total_sats = len(satellites)
        if total_sats > 0:
            validation_result['data_quality_score'] = max(0, 
                100 - (format_errors * 10) - (orbit_warnings * 2))
        
        validation_result['valid'] = (format_errors == 0 and total_sats > 0)
        
        return validation_result

def main():
    """測試主程序"""
    print("🚀 Phase 0 本地 TLE 數據加載器測試")
    print("=" * 60)
    
    # 初始化加載器
    loader = LocalTLELoader()
    
    # 1. 檢查數據覆蓋狀態
    print("\n📊 數據覆蓋狀態檢查")
    print("-" * 30)
    status = loader.get_data_coverage_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))
    
    # 2. 載入 Starlink 數據
    print("\n🛰️ Starlink 數據載入測試")
    print("-" * 30)
    starlink_data = loader.load_collected_data('starlink')
    if 'error' not in starlink_data:
        print(f"✅ 總天數: {starlink_data.get('total_days_collected', 0)}")
        print(f"✅ 日期範圍: {starlink_data.get('date_range', {}).get('start', 'N/A')} - {starlink_data.get('date_range', {}).get('end', 'N/A')}")
        print(f"✅ 雙格式覆蓋: {starlink_data.get('dual_format_coverage', 0)} / {starlink_data.get('total_days_collected', 0)}")
        
        # 顯示樣本數據
        if starlink_data.get('daily_data'):
            sample_day = starlink_data['daily_data'][0]
            print(f"✅ 樣本日期: {sample_day['date']}")
            print(f"✅ 衛星數量: {sample_day['satellite_count']}")
            print(f"✅ 雙格式支援: {sample_day['has_dual_format']}")
    else:
        print(f"❌ 錯誤: {starlink_data['error']}")
    
    # 3. 載入 OneWeb 數據
    print("\n🌐 OneWeb 數據載入測試")
    print("-" * 30)
    oneweb_data = loader.load_collected_data('oneweb')
    if 'error' not in oneweb_data:
        print(f"✅ 總天數: {oneweb_data.get('total_days_collected', 0)}")
        print(f"✅ 日期範圍: {oneweb_data.get('date_range', {}).get('start', 'N/A')} - {oneweb_data.get('date_range', {}).get('end', 'N/A')}")
        print(f"✅ 雙格式覆蓋: {oneweb_data.get('dual_format_coverage', 0)} / {oneweb_data.get('total_days_collected', 0)}")
        
        # 顯示樣本數據
        if oneweb_data.get('daily_data'):
            sample_day = oneweb_data['daily_data'][0]
            print(f"✅ 樣本日期: {sample_day['date']}")
            print(f"✅ 衛星數量: {sample_day['satellite_count']}")
            print(f"✅ 雙格式支援: {sample_day['has_dual_format']}")
    else:
        print(f"❌ 錯誤: {oneweb_data['error']}")
    
    # 4. 數據品質檢查測試
    print("\n🔍 數據品質檢查測試")
    print("-" * 30)
    if starlink_data.get('daily_data'):
        test_date = starlink_data['daily_data'][0]['date']
        validation_result = loader.validate_daily_data_quality('starlink', test_date)
        print(f"✅ 測試日期: {test_date}")
        print(f"✅ 數據有效: {validation_result['valid']}")
        print(f"✅ 衛星數量: {validation_result['satellite_count']}")
        print(f"✅ 品質分數: {validation_result['data_quality_score']}")
    
    print("\n🎉 Phase 0 本地 TLE 數據加載器測試完成")

if __name__ == "__main__":
    main()