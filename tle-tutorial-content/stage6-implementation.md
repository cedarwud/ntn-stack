# 階段6：完整程式實作 Step by Step

## 課程目標與學習重點

### 完成本階段後您將能夠：
- 將架構設計轉換為完整可執行的Python程式
- 實現Stage1TLEProcessor的所有核心組件
- 掌握模組化開發和測試驅動開發方法
- 處理實際的TLE數據文件和大規模衛星計算
- 建立完整的開發到部署流程

### 職業發展價值：
- 具備完整衛星系統開發能力
- 掌握Python高性能計算技術
- 理解大型項目的模組化架構實現
- 具備生產級軟體開發經驗

## 開發環境準備與項目結構

### 項目目錄結構設計

**完整的項目結構：**
```
stage1_tle_processor/
├── src/
│   ├── stage1_tle_processor/
│   │   ├── __init__.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── processor.py          # 主要處理器
│   │   │   └── config.py             # 配置管理
│   │   ├── data/
│   │   │   ├── __init__.py
│   │   │   ├── loader.py             # TLE數據載入器
│   │   │   └── parser.py             # TLE解析器
│   │   ├── calculation/
│   │   │   ├── __init__.py
│   │   │   ├── sgp4_engine.py        # SGP4計算引擎
│   │   │   └── coordinate_converter.py # 座標轉換器
│   │   ├── output/
│   │   │   ├── __init__.py
│   │   │   ├── formatter.py          # 輸出格式化器
│   │   │   └── metadata_manager.py   # 元數據管理器
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── error_handler.py      # 錯誤處理器
│   │       ├── quality_validator.py  # 品質驗證器
│   │       └── batch_processor.py    # 批量處理器
├── tests/
│   ├── __init__.py
│   ├── unit/                         # 單元測試
│   ├── integration/                  # 整合測試
│   └── data/                         # 測試數據
├── data/
│   ├── tle_files/                    # TLE數據文件
│   └── outputs/                      # 輸出結果
├── docs/                             # 文檔
├── requirements.txt                  # 依賴套件
├── setup.py                          # 安裝配置
├── README.md                         # 項目說明
└── examples/                         # 使用範例
```

### 開發環境配置

**虛擬環境與依賴安裝：**
```bash
# 創建項目目錄
mkdir stage1_tle_processor
cd stage1_tle_processor

# 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安裝核心依賴
pip install skyfield numpy astropy pytz pandas scipy
pip install pytest pytest-cov black flake8 mypy  # 開發工具
```

**requirements.txt 文件內容：**
```text
# 核心計算套件
skyfield>=1.46
numpy>=1.21.0
astropy>=5.0
pytz>=2021.1

# 數據處理
pandas>=1.3.0
scipy>=1.7.0

# 開發和測試工具
pytest>=6.2.0
pytest-cov>=2.12.0
black>=21.0.0
flake8>=3.9.0
mypy>=0.910

# 可選的性能優化
numba>=0.53.0
```

## 核心組件逐步實現

### 1. TLEDataLoader 實現

**data/loader.py 完整實現：**
```python
#!/usr/bin/env python3
"""
TLE數據載入器
負責讀取和驗證TLE數據文件
"""

from typing import List, Generator, Optional, Tuple
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class TLEDataLoader:
    """TLE數據載入器"""
    
    def __init__(self, cache_enabled: bool = True):
        """
        初始化載入器
        
        Args:
            cache_enabled: 是否啟用數據快取
        """
        self.cache_enabled = cache_enabled
        self._cache = {}
        
    def load_tle_file(self, file_path: str) -> List[str]:
        """
        載入TLE檔案並返回所有TLE行
        
        Args:
            file_path: TLE檔案路徑
            
        Returns:
            List[str]: TLE行列表
            
        Raises:
            FileNotFoundError: 檔案不存在
            ValueError: 檔案格式錯誤
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"TLE檔案不存在: {file_path}")
        
        # 檢查快取
        if self.cache_enabled and file_path in self._cache:
            logger.info(f"從快取載入TLE數據: {file_path}")
            return self._cache[file_path]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = [line.strip() for line in file.readlines() if line.strip()]
                
            logger.info(f"成功載入TLE檔案: {file_path}, 共 {len(lines)} 行")
            
            # 更新快取
            if self.cache_enabled:
                self._cache[file_path] = lines
                
            return lines
            
        except UnicodeDecodeError:
            # 嘗試其他編碼
            with open(file_path, 'r', encoding='latin-1') as file:
                lines = [line.strip() for line in file.readlines() if line.strip()]
            return lines
            
        except Exception as e:
            raise ValueError(f"讀取TLE檔案失敗: {e}")
    
    def load_tle_stream(self, file_path: str) -> Generator[List[str], None, None]:
        """
        以流式方式載入TLE數據（節省記憶體）
        
        Args:
            file_path: TLE檔案路徑
            
        Yields:
            List[str]: 三行TLE數據組（衛星名稱 + 兩行TLE）
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"TLE檔案不存在: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            lines_buffer = []
            
            for line in file:
                line = line.strip()
                if not line:
                    continue
                    
                lines_buffer.append(line)
                
                # 每三行組成一個TLE記錄
                if len(lines_buffer) == 3:
                    if self.validate_tle_group(lines_buffer):
                        yield lines_buffer.copy()
                    else:
                        logger.warning(f"跳過無效的TLE記錄: {lines_buffer[0]}")
                    
                    lines_buffer.clear()
    
    def validate_tle_data(self, tle_lines: List[str]) -> bool:
        """
        驗證TLE數據格式完整性
        
        Args:
            tle_lines: TLE行列表
            
        Returns:
            bool: 是否有效
        """
        if len(tle_lines) % 3 != 0:
            logger.error(f"TLE數據行數不是3的倍數: {len(tle_lines)}")
            return False
        
        valid_groups = 0
        total_groups = len(tle_lines) // 3
        
        for i in range(0, len(tle_lines), 3):
            group = tle_lines[i:i+3]
            if self.validate_tle_group(group):
                valid_groups += 1
        
        success_rate = valid_groups / total_groups
        logger.info(f"TLE數據驗證完成: {valid_groups}/{total_groups} "
                   f"({success_rate:.2%}) 有效")
        
        return success_rate > 0.9  # 90%以上有效才認為整體有效
    
    def validate_tle_group(self, tle_group: List[str]) -> bool:
        """
        驗證單個TLE三行組
        
        Args:
            tle_group: 三行TLE數據
            
        Returns:
            bool: 是否有效
        """
        if len(tle_group) != 3:
            return False
        
        satellite_name, line1, line2 = tle_group
        
        # 檢查第一行（Line 1）格式
        if not (len(line1) == 69 and line1[0] == '1'):
            logger.debug(f"Line 1 格式錯誤: {line1}")
            return False
        
        # 檢查第二行（Line 2）格式
        if not (len(line2) == 69 and line2[0] == '2'):
            logger.debug(f"Line 2 格式錯誤: {line2}")
            return False
        
        # 驗證衛星編號一致性
        try:
            sat_num_line1 = int(line1[2:7].strip())
            sat_num_line2 = int(line2[2:7].strip())
            
            if sat_num_line1 != sat_num_line2:
                logger.debug(f"衛星編號不一致: {sat_num_line1} vs {sat_num_line2}")
                return False
        except ValueError:
            logger.debug("衛星編號格式錯誤")
            return False
        
        # 驗證檢查碼
        if not (self._verify_checksum(line1) and self._verify_checksum(line2)):
            logger.debug("檢查碼驗證失敗")
            return False
        
        return True
    
    def _verify_checksum(self, tle_line: str) -> bool:
        """
        驗證TLE行的檢查碼
        
        Args:
            tle_line: TLE行
            
        Returns:
            bool: 檢查碼是否正確
        """
        if len(tle_line) != 69:
            return False
        
        # 計算檢查碼（不包括最後一位）
        checksum = 0
        for char in tle_line[:-1]:
            if char.isdigit():
                checksum += int(char)
            elif char == '-':
                checksum += 1
        
        expected_checksum = checksum % 10
        actual_checksum = int(tle_line[-1])
        
        return expected_checksum == actual_checksum
    
    def get_satellite_count(self, file_path: str) -> int:
        """
        獲取TLE檔案中的衛星數量
        
        Args:
            file_path: TLE檔案路徑
            
        Returns:
            int: 衛星數量
        """
        try:
            lines = self.load_tle_file(file_path)
            return len(lines) // 3
        except Exception as e:
            logger.error(f"計算衛星數量失敗: {e}")
            return 0
    
    def clear_cache(self):
        """清除快取"""
        self._cache.clear()
        logger.info("TLE數據快取已清除")
```

### 2. TLEParser 實現

**data/parser.py 完整實現：**
```python
#!/usr/bin/env python3
"""
TLE解析器
負責解析TLE格式數據並提取軌道要素
"""

from dataclasses import dataclass
from typing import List, Optional
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

@dataclass
class TLEData:
    """TLE數據結構"""
    satellite_number: int
    satellite_name: str
    epoch_year: int
    epoch_day: float
    mean_motion: float                    # 平均運動 (revs/day)
    eccentricity: float                   # 離心率
    inclination: float                    # 傾角 (degrees)
    raan: float                          # 升交點赤經 (degrees)
    argument_of_perigee: float           # 近地點幅角 (degrees)
    mean_anomaly: float                  # 平近點角 (degrees)
    mean_motion_derivative: float        # 平均運動一次導數
    mean_motion_second_derivative: float # 平均運動二次導數
    bstar: float                        # BSTAR拖曳係數
    element_number: int                 # 要素號
    revolution_number: int              # 軌道圈數
    
    def get_epoch_datetime(self) -> datetime:
        """
        將TLE epoch時間轉換為datetime對象
        
        Returns:
            datetime: TLE epoch時間（UTC）
        """
        # 處理年份（2位數年份轉4位數）
        if self.epoch_year < 57:  # 假設57-99為1957-1999，00-56為2000-2056
            full_year = 2000 + self.epoch_year
        else:
            full_year = 1900 + self.epoch_year
        
        # 計算日期和時間
        base_date = datetime(full_year, 1, 1, tzinfo=timezone.utc)
        epoch_datetime = base_date + timedelta(days=self.epoch_day - 1)
        
        return epoch_datetime

class TLEParser:
    """TLE解析器"""
    
    def __init__(self):
        """初始化解析器"""
        pass
    
    def parse_tle_group(self, tle_group: List[str]) -> Optional[TLEData]:
        """
        解析單個TLE三行組
        
        Args:
            tle_group: 包含衛星名稱和兩行TLE數據的列表
            
        Returns:
            TLEData: 解析後的TLE數據，失敗返回None
        """
        if len(tle_group) != 3:
            logger.error("TLE組必須包含3行數據")
            return None
        
        satellite_name, line1, line2 = tle_group
        
        try:
            # 解析第一行（Line 1）
            line1_data = self._parse_line1(line1)
            
            # 解析第二行（Line 2）
            line2_data = self._parse_line2(line2)
            
            # 驗證衛星編號一致性
            if line1_data['satellite_number'] != line2_data['satellite_number']:
                logger.error(f"衛星編號不一致: {line1_data['satellite_number']} "
                           f"vs {line2_data['satellite_number']}")
                return None
            
            # 組合數據
            tle_data = TLEData(
                satellite_name=satellite_name.strip(),
                satellite_number=line1_data['satellite_number'],
                epoch_year=line1_data['epoch_year'],
                epoch_day=line1_data['epoch_day'],
                mean_motion_derivative=line1_data['mean_motion_derivative'],
                mean_motion_second_derivative=line1_data['mean_motion_second_derivative'],
                bstar=line1_data['bstar'],
                element_number=line1_data['element_number'],
                inclination=line2_data['inclination'],
                raan=line2_data['raan'],
                eccentricity=line2_data['eccentricity'],
                argument_of_perigee=line2_data['argument_of_perigee'],
                mean_anomaly=line2_data['mean_anomaly'],
                mean_motion=line2_data['mean_motion'],
                revolution_number=line2_data['revolution_number']
            )
            
            return tle_data
            
        except Exception as e:
            logger.error(f"解析TLE數據失敗: {e}")
            return None
    
    def _parse_line1(self, line1: str) -> dict:
        """
        解析TLE第一行
        
        Args:
            line1: TLE第一行
            
        Returns:
            dict: 解析後的數據
        """
        data = {}
        
        # 衛星編號 (columns 3-7)
        data['satellite_number'] = int(line1[2:7].strip())
        
        # 分類標識 (column 8)
        data['classification'] = line1[7]
        
        # 國際標識符 (columns 10-17)
        data['international_designator'] = line1[9:17].strip()
        
        # Epoch年份 (columns 19-20)
        data['epoch_year'] = int(line1[18:20])
        
        # Epoch日數 (columns 21-32)
        data['epoch_day'] = float(line1[20:32])
        
        # 平均運動一次導數 (columns 34-43)
        mean_motion_derivative_str = line1[33:43].strip()
        if mean_motion_derivative_str:
            data['mean_motion_derivative'] = float(mean_motion_derivative_str)
        else:
            data['mean_motion_derivative'] = 0.0
        
        # 平均運動二次導數 (columns 45-52)
        second_derivative_str = line1[44:52].strip()
        if second_derivative_str:
            # 處理科學記數法格式 (例如: 00000-0 = 0.00000e-0)
            if '-' in second_derivative_str:
                mantissa_part = second_derivative_str[:-2]
                exponent_part = second_derivative_str[-2:]
                if mantissa_part and exponent_part:
                    mantissa = float('0.' + mantissa_part)
                    exponent = int(exponent_part)
                    data['mean_motion_second_derivative'] = mantissa * (10 ** exponent)
                else:
                    data['mean_motion_second_derivative'] = 0.0
            else:
                data['mean_motion_second_derivative'] = 0.0
        else:
            data['mean_motion_second_derivative'] = 0.0
        
        # BSTAR拖曳係數 (columns 54-61)
        bstar_str = line1[53:61].strip()
        if bstar_str:
            # 處理科學記數法格式
            if '-' in bstar_str:
                mantissa_part = bstar_str[:-2]
                exponent_part = bstar_str[-2:]
                if mantissa_part and exponent_part:
                    mantissa = float('0.' + mantissa_part)
                    exponent = int(exponent_part)
                    data['bstar'] = mantissa * (10 ** exponent)
                else:
                    data['bstar'] = 0.0
            else:
                data['bstar'] = 0.0
        else:
            data['bstar'] = 0.0
        
        # 軌道型號 (column 63)
        data['ephemeris_type'] = int(line1[62]) if line1[62].isdigit() else 0
        
        # 要素號 (columns 65-68)
        element_num_str = line1[64:68].strip()
        data['element_number'] = int(element_num_str) if element_num_str else 0
        
        return data
    
    def _parse_line2(self, line2: str) -> dict:
        """
        解析TLE第二行
        
        Args:
            line2: TLE第二行
            
        Returns:
            dict: 解析後的數據
        """
        data = {}
        
        # 衛星編號 (columns 3-7)
        data['satellite_number'] = int(line2[2:7].strip())
        
        # 傾角 (columns 9-16)
        data['inclination'] = float(line2[8:16])
        
        # 升交點赤經 (columns 18-25)
        data['raan'] = float(line2[17:25])
        
        # 離心率 (columns 27-33)
        eccentricity_str = line2[26:33]
        data['eccentricity'] = float('0.' + eccentricity_str)
        
        # 近地點幅角 (columns 35-42)
        data['argument_of_perigee'] = float(line2[34:42])
        
        # 平近點角 (columns 44-51)
        data['mean_anomaly'] = float(line2[43:51])
        
        # 平均運動 (columns 53-63)
        data['mean_motion'] = float(line2[52:63])
        
        # 軌道圈數 (columns 64-68)
        revolution_str = line2[63:68].strip()
        data['revolution_number'] = int(revolution_str) if revolution_str else 0
        
        return data
    
    def parse_tle_file(self, tle_lines: List[str]) -> List[TLEData]:
        """
        解析完整的TLE檔案
        
        Args:
            tle_lines: TLE行列表
            
        Returns:
            List[TLEData]: 解析後的TLE數據列表
        """
        parsed_data = []
        errors = 0
        
        for i in range(0, len(tle_lines), 3):
            if i + 2 < len(tle_lines):
                tle_group = tle_lines[i:i+3]
                tle_data = self.parse_tle_group(tle_group)
                
                if tle_data:
                    parsed_data.append(tle_data)
                else:
                    errors += 1
                    logger.warning(f"跳過無效TLE記錄: {tle_lines[i]}")
        
        logger.info(f"TLE解析完成: {len(parsed_data)} 成功, {errors} 錯誤")
        return parsed_data
```

### 3. SGP4Calculator 實現

**calculation/sgp4_engine.py 核心實現：**
```python
#!/usr/bin/env python3
"""
SGP4計算引擎
實現SGP4/SDP4軌道預測算法
"""

import numpy as np
import logging
from datetime import datetime, timedelta, timezone
from typing import Tuple, Dict, List
from skyfield.api import EarthSatellite, load
from skyfield.timelib import Time
from ..data.parser import TLEData

logger = logging.getLogger(__name__)

class SGP4Calculator:
    """SGP4計算引擎"""
    
    def __init__(self):
        """初始化SGP4計算引擎"""
        self.ts = load.timescale()
        self._satellite_cache = {}
    
    def calculate_satellite_position(self, 
                                   tle_data: TLEData, 
                                   calculation_time: datetime) -> Dict:
        """
        計算衛星在指定時間的位置和速度
        
        重要：使用TLE epoch時間作為基準，不使用當前時間！
        
        Args:
            tle_data: TLE數據
            calculation_time: 計算時間
            
        Returns:
            dict: 包含位置、速度、時間等信息
        """
        try:
            # 1. 獲取TLE epoch時間（極其重要！）
            tle_epoch = tle_data.get_epoch_datetime()
            
            # 2. 檢查時間差是否過大
            time_diff = (calculation_time - tle_epoch).total_seconds() / (24 * 3600)  # 天數
            if abs(time_diff) > 30:
                logger.warning(f"時間差過大: {time_diff:.1f}天，軌道預測可能不準確")
            
            # 3. 創建skyfield衛星對象
            satellite = self._create_satellite_object(tle_data)
            
            # 4. 轉換時間到skyfield格式
            skyfield_time = self.ts.from_datetime(calculation_time)
            
            # 5. 計算位置和速度
            geocentric = satellite.at(skyfield_time)
            
            # 6. 提取位置和速度（ECI座標系，km和km/s）
            position_km = geocentric.position.km
            velocity_km_per_s = geocentric.velocity.km_per_s
            
            result = {
                'position_eci_km': position_km.tolist(),
                'velocity_eci_kmps': velocity_km_per_s.tolist(),
                'calculation_time': calculation_time,
                'tle_epoch': tle_epoch,
                'time_since_epoch_minutes': time_diff * 24 * 60,  # 分鐘
                'time_since_epoch_days': time_diff,
                'satellite_number': tle_data.satellite_number,
                'satellite_name': tle_data.satellite_name
            }
            
            return result
            
        except Exception as e:
            logger.error(f"SGP4計算失敗 (衛星 {tle_data.satellite_number}): {e}")
            raise
    
    def _create_satellite_object(self, tle_data: TLEData) -> EarthSatellite:
        """
        創建skyfield衛星對象
        
        Args:
            tle_data: TLE數據
            
        Returns:
            EarthSatellite: skyfield衛星對象
        """
        # 檢查快取
        cache_key = f"{tle_data.satellite_number}_{tle_data.element_number}"
        if cache_key in self._satellite_cache:
            return self._satellite_cache[cache_key]
        
        # 重構TLE字符串
        line1 = self._construct_tle_line1(tle_data)
        line2 = self._construct_tle_line2(tle_data)
        
        # 創建衛星對象
        satellite = EarthSatellite(line1, line2, tle_data.satellite_name, self.ts)
        
        # 加入快取
        self._satellite_cache[cache_key] = satellite
        
        return satellite
    
    def _construct_tle_line1(self, tle_data: TLEData) -> str:
        """
        重構TLE第一行
        
        Args:
            tle_data: TLE數據
            
        Returns:
            str: TLE第一行
        """
        # 構建TLE第一行格式
        line1_parts = []
        line1_parts.append('1')  # Line number
        line1_parts.append(' ')
        line1_parts.append(f"{tle_data.satellite_number:05d}")  # Satellite number
        line1_parts.append('U')  # Classification
        line1_parts.append(' ')
        
        # International designator (8 characters)
        int_des = f"{tle_data.epoch_year:02d}001A  "[:8]
        line1_parts.append(int_des)
        line1_parts.append(' ')
        
        # Epoch
        epoch_str = f"{tle_data.epoch_year:02d}{tle_data.epoch_day:012.8f}"
        line1_parts.append(epoch_str)
        line1_parts.append(' ')
        
        # Mean motion derivative
        line1_parts.append(f"{tle_data.mean_motion_derivative:10.8f}")
        line1_parts.append(' ')
        
        # Mean motion second derivative (科學記數法)
        if tle_data.mean_motion_second_derivative != 0:
            second_deriv_str = f"{tle_data.mean_motion_second_derivative:.5e}"
            line1_parts.append(f"{second_deriv_str:8s}")
        else:
            line1_parts.append(' 00000-0')
        line1_parts.append(' ')
        
        # BSTAR drag term
        if tle_data.bstar != 0:
            bstar_str = f"{tle_data.bstar:.5e}"
            line1_parts.append(f"{bstar_str:8s}")
        else:
            line1_parts.append(' 00000-0')
        line1_parts.append(' ')
        
        # Ephemeris type and element number
        line1_parts.append('0')  # Ephemeris type
        line1_parts.append(' ')
        line1_parts.append(f"{tle_data.element_number:4d}")
        
        line1_base = ''.join(line1_parts)
        
        # 計算並添加檢查碼
        checksum = self._calculate_checksum(line1_base)
        line1 = line1_base + str(checksum)
        
        return line1
    
    def _construct_tle_line2(self, tle_data: TLEData) -> str:
        """
        重構TLE第二行
        
        Args:
            tle_data: TLE數據
            
        Returns:
            str: TLE第二行
        """
        # 構建TLE第二行格式
        line2_parts = []
        line2_parts.append('2')  # Line number
        line2_parts.append(' ')
        line2_parts.append(f"{tle_data.satellite_number:05d}")  # Satellite number
        line2_parts.append(' ')
        
        # Orbital elements
        line2_parts.append(f"{tle_data.inclination:8.4f}")  # Inclination
        line2_parts.append(' ')
        line2_parts.append(f"{tle_data.raan:8.4f}")  # RAAN
        line2_parts.append(' ')
        
        # Eccentricity (去掉小數點)
        ecc_str = f"{tle_data.eccentricity:.7f}"[2:]  # 去掉 "0."
        line2_parts.append(ecc_str[:7])
        line2_parts.append(' ')
        
        line2_parts.append(f"{tle_data.argument_of_perigee:8.4f}")  # Argument of perigee
        line2_parts.append(' ')
        line2_parts.append(f"{tle_data.mean_anomaly:8.4f}")  # Mean anomaly
        line2_parts.append(' ')
        line2_parts.append(f"{tle_data.mean_motion:11.8f}")  # Mean motion
        
        # Revolution number
        line2_parts.append(f"{tle_data.revolution_number:5d}")
        
        line2_base = ''.join(line2_parts)
        
        # 計算並添加檢查碼
        checksum = self._calculate_checksum(line2_base)
        line2 = line2_base + str(checksum)
        
        return line2
    
    def _calculate_checksum(self, line: str) -> int:
        """
        計算TLE行的檢查碼
        
        Args:
            line: TLE行（不含檢查碼）
            
        Returns:
            int: 檢查碼
        """
        checksum = 0
        for char in line:
            if char.isdigit():
                checksum += int(char)
            elif char == '-':
                checksum += 1
        
        return checksum % 10
    
    def calculate_batch_positions(self, 
                                tle_data_list: List[TLEData],
                                calculation_times: List[datetime]) -> List[Dict]:
        """
        批量計算多顆衛星在多個時間點的位置
        
        Args:
            tle_data_list: TLE數據列表
            calculation_times: 計算時間列表
            
        Returns:
            List[Dict]: 計算結果列表
        """
        results = []
        total_calculations = len(tle_data_list) * len(calculation_times)
        completed = 0
        
        logger.info(f"開始批量SGP4計算: {len(tle_data_list)}顆衛星 × "
                   f"{len(calculation_times)}個時間點 = {total_calculations}個計算")
        
        for tle_data in tle_data_list:
            satellite_results = []
            
            for calc_time in calculation_times:
                try:
                    result = self.calculate_satellite_position(tle_data, calc_time)
                    satellite_results.append(result)
                    completed += 1
                    
                    if completed % 1000 == 0:  # 每1000個計算報告一次進度
                        progress = completed / total_calculations * 100
                        logger.info(f"SGP4計算進度: {completed}/{total_calculations} "
                                  f"({progress:.1f}%)")
                        
                except Exception as e:
                    logger.error(f"跳過計算失敗的衛星 {tle_data.satellite_number}: {e}")
                    completed += 1
                    continue
            
            if satellite_results:
                results.extend(satellite_results)
        
        logger.info(f"批量SGP4計算完成: {len(results)}個有效結果")
        return results
    
    def clear_cache(self):
        """清除衛星對象快取"""
        self._satellite_cache.clear()
        logger.info("SGP4計算器快取已清除")
```

## 測試驅動開發方法

### 單元測試實現

**tests/unit/test_sgp4_calculator.py：**
```python
#!/usr/bin/env python3
import unittest
from datetime import datetime, timezone, timedelta
import numpy as np

from stage1_tle_processor.calculation.sgp4_engine import SGP4Calculator
from stage1_tle_processor.data.parser import TLEData

class TestSGP4Calculator(unittest.TestCase):
    """SGP4計算引擎測試"""
    
    def setUp(self):
        """測試設置"""
        self.calculator = SGP4Calculator()
        
        # 創建測試TLE數據（使用真實的ISS數據）
        self.test_tle = TLEData(
            satellite_number=25544,
            satellite_name="ISS (ZARYA)",
            epoch_year=25,
            epoch_day=245.12345678,
            mean_motion=15.54225995,
            eccentricity=0.0003363,
            inclination=51.6461,
            raan=339.7760,
            argument_of_perigee=31.3921,
            mean_anomaly=328.8071,
            mean_motion_derivative=0.00002182,
            mean_motion_second_derivative=0.0,
            bstar=0.00014829,
            element_number=999,
            revolution_number=12345
        )
    
    def test_calculate_satellite_position(self):
        """測試衛星位置計算"""
        # 使用TLE epoch時間作為計算時間
        tle_epoch = self.test_tle.get_epoch_datetime()
        calc_time = tle_epoch + timedelta(minutes=30)
        
        result = self.calculator.calculate_satellite_position(
            self.test_tle, calc_time)
        
        # 驗證結果結構
        self.assertIn('position_eci_km', result)
        self.assertIn('velocity_eci_kmps', result)
        self.assertIn('calculation_time', result)
        self.assertIn('tle_epoch', result)
        
        # 驗證數值合理性
        position = np.array(result['position_eci_km'])
        velocity = np.array(result['velocity_eci_kmps'])
        
        # ISS軌道高度約400km，距離地心約6800km
        distance = np.linalg.norm(position)
        self.assertGreater(distance, 6000)  # > 6000 km
        self.assertLess(distance, 8000)     # < 8000 km
        
        # ISS軌道速度約7.7 km/s
        speed = np.linalg.norm(velocity)
        self.assertGreater(speed, 6)        # > 6 km/s
        self.assertLess(speed, 9)           # < 9 km/s
    
    def test_time_basis_accuracy(self):
        """測試時間基準準確性"""
        # 使用TLE epoch時間
        tle_epoch = self.test_tle.get_epoch_datetime()
        
        # 在epoch時間計算位置
        result_at_epoch = self.calculator.calculate_satellite_position(
            self.test_tle, tle_epoch)
        
        # 在epoch + 1軌道週期計算位置
        orbital_period = 24 * 60 / self.test_tle.mean_motion  # 分鐘
        calc_time = tle_epoch + timedelta(minutes=orbital_period)
        
        result_after_period = self.calculator.calculate_satellite_position(
            self.test_tle, calc_time)
        
        # 一個軌道週期後位置應該接近（但不完全相同，因為軌道擾動）
        pos1 = np.array(result_at_epoch['position_eci_km'])
        pos2 = np.array(result_after_period['position_eci_km'])
        
        position_difference = np.linalg.norm(pos2 - pos1)
        
        # 差異應該在合理範圍內（<100km，考慮擾動）
        self.assertLess(position_difference, 100)
    
    def test_batch_calculation(self):
        """測試批量計算"""
        tle_list = [self.test_tle]
        
        tle_epoch = self.test_tle.get_epoch_datetime()
        calc_times = [
            tle_epoch,
            tle_epoch + timedelta(minutes=30),
            tle_epoch + timedelta(minutes=60)
        ]
        
        results = self.calculator.calculate_batch_positions(
            tle_list, calc_times)
        
        self.assertEqual(len(results), 3)  # 1衛星 × 3時間點
        
        for result in results:
            self.assertIn('position_eci_km', result)
            self.assertIn('velocity_eci_kmps', result)

if __name__ == '__main__':
    unittest.main()
```

## 階段總結

### 階段6學習成果確認：

**掌握的核心技術：**
- Python大型項目結構設計和組織
- TLE數據的完整載入、解析、驗證流程
- SGP4算法的實際實現和批量處理
- 測試驅動開發(TDD)方法論
- 性能優化和記憶體管理技術

**完成的實現工作：**
- TLEDataLoader完整實現（流式讀取、快取、驗證）
- TLEParser完整實現（格式解析、錯誤處理）
- SGP4Calculator完整實現（基於skyfield、批量處理）
- 完整的單元測試套件
- 專業級的錯誤處理和日誌記錄

**實際應用能力：**
- 能夠處理8000+顆衛星的實際TLE數據
- 具備生產級Python軟體開發能力
- 掌握複雜系統的模組化設計方法
- 理解和實現高性能計算系統

**下一步行動計畫：**
- 進入階段7：數據驗證和品質控制
- 實現座標轉換和輸出格式化
- 建立完整的品質保證體系
- 進行大規模測試和性能調優

**重要提醒：確保所有測試通過再繼續下一階段！**

## 關鍵實現要點

### 時間基準處理（核心原則）
- 所有軌道計算必須使用TLE epoch時間作為基準
- 實現中通過`tle_data.get_epoch_datetime()`獲取正確的基準時間
- 避免使用`datetime.now()`進行軌道計算

### 性能優化策略
- 使用快取減少重複的衛星對象創建
- 實現流式處理避免大文件一次載入
- 批量處理提高計算效率
- 適當的錯誤處理避免無效計算

### 代碼品質保證
- 完整的類型提示和文檔字符串
- 結構化的錯誤處理和日誌記錄
- 全面的單元測試覆蓋
- 符合Python PEP 8編碼規範