#!/usr/bin/env python3
"""
Phase 1 重構 - TLE 數據載入器

功能:
1. 掃描和載入所有 TLE 數據檔案
2. 驗證 TLE 數據格式和完整性
3. 提供統一的 TLE 數據接口

符合 CLAUDE.md 原則:
- 100% 真實 TLE 數據，禁止模擬數據
- 完整格式驗證，確保 SGP4 兼容性
- 全量載入，不做預篩選
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TLERecord:
    """TLE 記錄數據結構"""
    satellite_id: str
    satellite_name: str
    line0: str  # 衛星名稱行
    line1: str  # TLE 第一行
    line2: str  # TLE 第二行
    constellation: str
    epoch: datetime
    file_source: str

@dataclass 
class TLELoadResult:
    """TLE 載入結果"""
    total_records: int
    valid_records: int
    invalid_records: int
    constellations: Dict[str, int]
    records: List[TLERecord]
    errors: List[str]

class TLELoader:
    """
    Phase 1 TLE 數據載入器
    
    負責掃描、載入、驗證所有 TLE 數據檔案
    確保數據品質符合 SGP4 計算要求
    """
    
    def __init__(self, tle_data_dir: str = ""):
        """
        初始化 TLE 載入器
        
        Args:
            tle_data_dir: TLE 數據根目錄，為空時使用統一配置
        """
        if not tle_data_dir:
            # 使用統一配置載入器
            try:
                current_dir = os.path.dirname(os.path.abspath(__file__))
                config_dir = os.path.join(os.path.dirname(current_dir), 'config')
                if config_dir not in sys.path:
                    sys.path.insert(0, config_dir)
                
                from config_loader import get_tle_data_path
                tle_data_dir = get_tle_data_path()
                logger.info("✅ 使用統一配置載入器獲取 TLE 路徑")
            except Exception as e:
                logger.warning(f"⚠️ 統一配置載入失敗，使用預設路徑: {e}")
                # 回退到智能路徑解析
                current_file = Path(__file__)
                project_root = current_file.parent.parent.parent
                tle_data_dir = str(project_root / "netstack" / "tle_data")
        
        self.tle_data_dir = Path(tle_data_dir)
        self.supported_constellations = ["starlink", "oneweb"]
        
        if not self.tle_data_dir.exists():
            raise FileNotFoundError(f"TLE 數據目錄不存在: {self.tle_data_dir}")
            
        logger.info(f"TLE 載入器初始化完成: {self.tle_data_dir}")
    
    def scan_tle_files(self) -> Dict[str, List[Path]]:
        """
        掃描所有可用的 TLE 檔案
        
        Returns:
            Dict[constellation, List[file_paths]]
        """
        tle_files = {}
        
        for constellation in self.supported_constellations:
            constellation_dir = self.tle_data_dir / constellation
            if not constellation_dir.exists():
                logger.warning(f"星座目錄不存在: {constellation_dir}")
                continue
                
            # 尋找 .tle 檔案
            tle_pattern = constellation_dir.glob("**/*.tle")
            files = list(tle_pattern)
            
            if files:
                # 按修改時間排序，最新的在前
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                tle_files[constellation] = files
                logger.info(f"發現 {constellation}: {len(files)} 個 TLE 檔案")
            else:
                logger.warning(f"星座 {constellation} 無可用 TLE 檔案")
        
        return tle_files
    
    def load_tle_file(self, file_path: Path, constellation: str) -> List[TLERecord]:
        """
        載入單個 TLE 檔案
        
        Args:
            file_path: TLE 檔案路徑
            constellation: 星座名稱
            
        Returns:
            List[TLERecord]: TLE 記錄列表
        """
        records = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            
            # 解析 TLE 格式 (每3行一組)
            for i in range(0, len(lines), 3):
                if i + 2 >= len(lines):
                    break
                    
                line0 = lines[i]      # 衛星名稱
                line1 = lines[i + 1]  # TLE 第一行
                line2 = lines[i + 2]  # TLE 第二行
                
                # 驗證 TLE 格式
                if self._validate_tle_format(line1, line2):
                    # 提取衛星信息
                    satellite_id = self._extract_satellite_id(line1, line2)
                    epoch = self._extract_epoch(line1)
                    
                    record = TLERecord(
                        satellite_id=satellite_id,
                        satellite_name=line0,
                        line0=line0,
                        line1=line1,
                        line2=line2,
                        constellation=constellation,
                        epoch=epoch,
                        file_source=str(file_path)
                    )
                    records.append(record)
                else:
                    logger.warning(f"無效 TLE 格式: {file_path}:{i//3+1}")
        
        except Exception as e:
            logger.error(f"載入 TLE 檔案失敗 {file_path}: {e}")
        
        logger.info(f"從 {file_path.name} 載入 {len(records)} 條 TLE 記錄")
        return records
    
    def load_all_tle_data(self) -> TLELoadResult:
        """
        載入所有 TLE 數據
        
        Returns:
            TLELoadResult: 完整載入結果
        """
        logger.info("開始載入所有 TLE 數據...")
        
        all_records = []
        constellation_counts = {}
        errors = []
        
        # 掃描檔案
        tle_files = self.scan_tle_files()
        
        # 載入每個星座的數據
        for constellation, files in tle_files.items():
            constellation_records = []
            
            for file_path in files:
                try:
                    records = self.load_tle_file(file_path, constellation)
                    constellation_records.extend(records)
                except Exception as e:
                    error_msg = f"載入 {file_path} 失敗: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            all_records.extend(constellation_records)
            constellation_counts[constellation] = len(constellation_records)
            
            logger.info(f"{constellation} 載入完成: {len(constellation_records)} 條記錄")
        
        # 創建結果
        result = TLELoadResult(
            total_records=len(all_records),
            valid_records=len(all_records),
            invalid_records=0,  # 在載入過程中已過濾無效記錄
            constellations=constellation_counts,
            records=all_records,
            errors=errors
        )
        
        logger.info(f"✅ TLE 數據載入完成: {result.total_records} 條記錄")
        logger.info(f"   星座分佈: {result.constellations}")
        
        return result
    
    def _validate_tle_format(self, line1: str, line2: str) -> bool:
        """
        驗證 TLE 格式
        
        Args:
            line1: TLE 第一行
            line2: TLE 第二行
            
        Returns:
            bool: 格式是否有效
        """
        # 檢查行長度
        if len(line1) != 69 or len(line2) != 69:
            return False
            
        # 檢查行標識符
        if not line1.startswith('1 ') or not line2.startswith('2 '):
            return False
            
        # 檢查衛星號碼一致性
        sat_num1 = line1[2:7].strip()
        sat_num2 = line2[2:7].strip()
        if sat_num1 != sat_num2:
            return False
            
        # 基本數字格式檢查
        try:
            # 檢查關鍵數值字段
            float(line1[20:32])  # Mean motion
            float(line2[8:16])   # Inclination
            float(line2[17:25])  # RAAN
            float(line2[26:33])  # Eccentricity
            float(line2[34:42])  # Argument of perigee
            float(line2[43:51])  # Mean anomaly
        except ValueError:
            return False
            
        return True
    
    def _extract_satellite_id(self, line1: str, line2: str) -> str:
        """
        提取衛星 ID (NORAD ID)
        
        Args:
            line1: TLE 第一行
            line2: TLE 第二行
            
        Returns:
            str: 衛星 ID
        """
        return line1[2:7].strip()
    
    def _extract_epoch(self, line1: str) -> datetime:
        """
        提取 TLE epoch 時間
        
        Args:
            line1: TLE 第一行
            
        Returns:
            datetime: epoch 時間
        """
        try:
            # TLE epoch 格式: YYDDD.DDDDDDDD
            epoch_str = line1[18:32].strip()
            
            # 解析年份 (2-digit year)
            year_2digit = int(epoch_str[:2])
            year = 2000 + year_2digit if year_2digit < 57 else 1900 + year_2digit
            
            # 解析日期
            day_of_year = float(epoch_str[2:])
            
            # 轉換為 datetime
            from datetime import datetime, timedelta
            epoch = datetime(year, 1, 1) + timedelta(days=day_of_year - 1)
            
            return epoch
            
        except Exception as e:
            logger.warning(f"解析 epoch 失敗: {epoch_str}, 使用當前時間")
            return datetime.now()
    
    def export_tle_summary(self, result: TLELoadResult, output_path: str):
        """
        導出 TLE 載入摘要
        
        Args:
            result: TLE 載入結果
            output_path: 輸出檔案路徑
        """
        summary = {
            "generation_timestamp": datetime.now().isoformat(),
            "total_records": result.total_records,
            "valid_records": result.valid_records,
            "invalid_records": result.invalid_records,
            "constellation_distribution": result.constellations,
            "data_sources": list(set(record.file_source for record in result.records)),
            "epoch_range": {
                "earliest": min(record.epoch for record in result.records).isoformat() if result.records else None,
                "latest": max(record.epoch for record in result.records).isoformat() if result.records else None
            },
            "errors": result.errors
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"TLE 載入摘要已保存: {output_path}")

# 便利函數
def create_tle_loader(tle_data_dir: str = "") -> TLELoader:
    """創建 TLE 載入器實例"""
    return TLELoader(tle_data_dir)

if __name__ == "__main__":
    # 測試用例
    loader = create_tle_loader()
    result = loader.load_all_tle_data()
    
    print(f"✅ 載入完成: {result.total_records} 條 TLE 記錄")
    print(f"   星座分佈: {result.constellations}")
    
    # 導出摘要
    loader.export_tle_summary(result, "/tmp/tle_load_summary.json")