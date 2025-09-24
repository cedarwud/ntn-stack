#!/usr/bin/env python3
"""
TLE 數據解析器
=============

用於解析 Two-Line Element (TLE) 數據格式的工具模組。
"""

import re
from datetime import datetime, timezone
from typing import List, Dict, Any, NamedTuple, Optional
from pathlib import Path


class TLEData(NamedTuple):
    """TLE 數據結構"""
    satellite_name: str
    satellite_id: str  # NORAD ID
    classification: str
    international_id: str
    epoch_year: int
    epoch_day: float
    first_derivative: float
    second_derivative: float
    bstar: float
    element_number: int
    inclination: float
    raan: float  # Right Ascension of Ascending Node
    eccentricity: float
    arg_perigee: float
    mean_anomaly: float
    mean_motion: float
    revolution_number: int
    checksum1: int
    checksum2: int
    
    @property
    def epoch_datetime(self) -> datetime:
        """將 TLE 的 epoch 時間轉換為 datetime 對象"""
        # 處理年份 (2位數轉4位數)
        if self.epoch_year < 57:  # 假設 57年後為 20xx
            year = 2000 + self.epoch_year
        else:
            year = 1900 + self.epoch_year
            
        # 轉換日期
        base_date = datetime(year, 1, 1, tzinfo=timezone.utc)
        epoch_date = base_date.replace(day=1) + \
                    datetime.timedelta(days=self.epoch_day - 1)
        return epoch_date


class TLEParser:
    """TLE 數據解析器"""
    
    def __init__(self):
        self.logger = self._get_logger()
        
    def _get_logger(self):
        """獲取日誌記錄器"""
        import logging
        return logging.getLogger(__name__)
    
    def parse_tle_file(self, file_path: Path) -> List[TLEData]:
        """
        解析 TLE 文件
        
        Args:
            file_path: TLE 文件路徑
            
        Returns:
            List[TLEData]: 解析後的 TLE 數據列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
                
        except Exception as e:
            self.logger.error(f"讀取 TLE 文件失敗 {file_path}: {e}")
            raise
            
        tle_data_list = []
        
        # 每三行為一組 TLE 數據
        for i in range(0, len(lines), 3):
            if i + 2 >= len(lines):
                break
                
            try:
                satellite_name = lines[i]
                line1 = lines[i + 1]
                line2 = lines[i + 2]
                
                # 驗證 TLE 格式
                if not self._validate_tle_format(line1, line2):
                    self.logger.warning(f"無效的 TLE 格式，跳過: {satellite_name}")
                    continue
                    
                tle_data = self._parse_tle_lines(satellite_name, line1, line2)
                tle_data_list.append(tle_data)
                
            except Exception as e:
                self.logger.error(f"解析 TLE 數據失敗: {e}")
                continue
                
        self.logger.info(f"成功解析 {len(tle_data_list)} 條 TLE 數據")
        return tle_data_list
    
    def _validate_tle_format(self, line1: str, line2: str) -> bool:
        """驗證 TLE 格式"""
        if len(line1) != 69 or len(line2) != 69:
            return False
            
        if not line1.startswith('1 ') or not line2.startswith('2 '):
            return False
            
        return True
    
    def _parse_tle_lines(self, satellite_name: str, line1: str, line2: str) -> TLEData:
        """解析 TLE 的兩行數據"""
        
        # Line 1 解析
        satellite_id = line1[2:7].strip()
        classification = line1[7]
        international_id = line1[9:17].strip()
        epoch_year = int(line1[18:20])
        epoch_day = float(line1[20:32])
        first_derivative = float(line1[33:43])
        
        # 處理第二階導數的特殊格式
        second_derivative_str = line1[44:52].strip()
        if second_derivative_str:
            # 格式如 "12345-3" 表示 0.12345e-3
            match = re.match(r'([+-]?\d+)([+-]\d+)', second_derivative_str)
            if match:
                mantissa = float(f"0.{match.group(1)[1:]}" if match.group(1).startswith(('-', '+')) else f"0.{match.group(1)}")
                exponent = int(match.group(2))
                second_derivative = mantissa * (10 ** exponent)
            else:
                second_derivative = 0.0
        else:
            second_derivative = 0.0
            
        # BSTAR 拖拽係數 (類似第二階導數格式)
        bstar_str = line1[53:61].strip()
        if bstar_str:
            match = re.match(r'([+-]?\d+)([+-]\d+)', bstar_str)
            if match:
                mantissa = float(f"0.{match.group(1)[1:]}" if match.group(1).startswith(('-', '+')) else f"0.{match.group(1)}")
                exponent = int(match.group(2))
                bstar = mantissa * (10 ** exponent)
            else:
                bstar = 0.0
        else:
            bstar = 0.0
            
        element_number = int(line1[64:68])
        checksum1 = int(line1[68])
        
        # Line 2 解析
        inclination = float(line2[8:16])
        raan = float(line2[17:25])
        eccentricity = float(f"0.{line2[26:33]}")  # 去掉小數點
        arg_perigee = float(line2[34:42])
        mean_anomaly = float(line2[43:51])
        mean_motion = float(line2[52:63])
        revolution_number = int(line2[63:68])
        checksum2 = int(line2[68])
        
        return TLEData(
            satellite_name=satellite_name,
            satellite_id=satellite_id,
            classification=classification,
            international_id=international_id,
            epoch_year=epoch_year,
            epoch_day=epoch_day,
            first_derivative=first_derivative,
            second_derivative=second_derivative,
            bstar=bstar,
            element_number=element_number,
            inclination=inclination,
            raan=raan,
            eccentricity=eccentricity,
            arg_perigee=arg_perigee,
            mean_anomaly=mean_anomaly,
            mean_motion=mean_motion,
            revolution_number=revolution_number,
            checksum1=checksum1,
            checksum2=checksum2
        )
    
    def filter_by_constellation(self, tle_data_list: List[TLEData], 
                               constellation: str) -> List[TLEData]:
        """
        根據星座名稱過濾 TLE 數據
        
        Args:
            tle_data_list: TLE 數據列表
            constellation: 星座名稱 (starlink/oneweb)
            
        Returns:
            List[TLEData]: 過濾後的 TLE 數據
        """
        if constellation.lower() == 'starlink':
            return [tle for tle in tle_data_list 
                   if 'starlink' in tle.satellite_name.lower()]
        elif constellation.lower() == 'oneweb':
            return [tle for tle in tle_data_list 
                   if 'oneweb' in tle.satellite_name.lower()]
        else:
            return tle_data_list
    
    def get_latest_epoch_tle(self, tle_data_list: List[TLEData]) -> Optional[TLEData]:
        """
        獲取最新 epoch 時間的 TLE 數據
        
        Args:
            tle_data_list: TLE 數據列表
            
        Returns:
            Optional[TLEData]: 最新的 TLE 數據
        """
        if not tle_data_list:
            return None
            
        return max(tle_data_list, key=lambda tle: tle.epoch_datetime)
    
    def export_to_dict(self, tle_data: TLEData) -> Dict[str, Any]:
        """
        將 TLE 數據轉換為字典格式
        
        Args:
            tle_data: TLE 數據
            
        Returns:
            Dict[str, Any]: 字典格式的數據
        """
        return {
            'satellite_name': tle_data.satellite_name,
            'satellite_id': tle_data.satellite_id,
            'classification': tle_data.classification,
            'international_id': tle_data.international_id,
            'epoch': {
                'year': tle_data.epoch_year,
                'day': tle_data.epoch_day,
                'datetime': tle_data.epoch_datetime.isoformat()
            },
            'orbital_elements': {
                'inclination': tle_data.inclination,
                'raan': tle_data.raan,
                'eccentricity': tle_data.eccentricity,
                'arg_perigee': tle_data.arg_perigee,
                'mean_anomaly': tle_data.mean_anomaly,
                'mean_motion': tle_data.mean_motion
            },
            'drag_terms': {
                'first_derivative': tle_data.first_derivative,
                'second_derivative': tle_data.second_derivative,
                'bstar': tle_data.bstar
            },
            'metadata': {
                'element_number': tle_data.element_number,
                'revolution_number': tle_data.revolution_number
            }
        }