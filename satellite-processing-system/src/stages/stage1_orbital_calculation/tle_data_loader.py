"""
TLE數據載入器 - Stage 1模組化組件

職責：
1. 掃描TLE數據文件
2. 載入和解析TLE數據
3. 數據健康檢查
4. 提供統一的數據訪問接口
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TLEDataLoader:
    """TLE數據載入器"""
    
    def __init__(self, tle_data_dir: str = None):
        # 自動檢測環境並設置TLE數據目錄
        if tle_data_dir is None:
            if os.path.exists("/satellite-processing") or Path(".").exists():
                tle_data_dir = "/satellite-processing/data/tle_data" if os.path.exists("/satellite-processing") else "data/tle_data"  # 容器環境
            else:
                tle_data_dir = "/tmp/ntn-stack-dev/tle_data"  # 開發環境
        
        self.tle_data_dir = Path(tle_data_dir)
        self.logger = logging.getLogger(f"{__name__}.TLEDataLoader")
        
        # 載入統計
        self.load_statistics = {
            "files_scanned": 0,
            "satellites_loaded": 0,
            "constellations_found": 0,
            "load_errors": 0
        }
    
    def scan_tle_data(self) -> Dict[str, Any]:
        """
        掃描所有可用的TLE數據文件
        
        Returns:
            掃描結果統計
        """
        self.logger.info("🔍 掃描TLE數據文件...")
        
        scan_result = {
            'constellations': {},
            'total_constellations': 0,
            'total_files': 0,
            'total_satellites': 0
        }
        
        # 掃描已知的星座目錄
        for constellation in ['starlink', 'oneweb']:
            constellation_result = self._scan_constellation(constellation)
            if constellation_result:
                scan_result['constellations'][constellation] = constellation_result
                scan_result['total_files'] += constellation_result['files_count']
                scan_result['total_satellites'] += constellation_result['satellite_count']
        
        scan_result['total_constellations'] = len(scan_result['constellations'])
        self.load_statistics["files_scanned"] = scan_result['total_files']
        self.load_statistics["constellations_found"] = scan_result['total_constellations']
        
        self.logger.info(f"🎯 TLE掃描完成: {scan_result['total_satellites']} 顆衛星")
        self.logger.info(f"   {scan_result['total_constellations']} 個星座, {scan_result['total_files']} 個文件")
        
        return scan_result
    
    def _scan_constellation(self, constellation: str) -> Optional[Dict[str, Any]]:
        """掃描特定星座的TLE數據"""
        tle_dir = self.tle_data_dir / constellation / "tle"
        
        if not tle_dir.exists():
            self.logger.warning(f"TLE目錄不存在: {tle_dir}")
            return None
        
        tle_files = list(tle_dir.glob(f"{constellation}_*.tle"))
        
        if not tle_files:
            self.logger.warning(f"未找到 {constellation} TLE文件")
            return None
        
        # 找出最新日期的文件
        latest_date = None
        latest_file = None
        latest_satellite_count = 0
        
        for tle_file in tle_files:
            date_str = tle_file.stem.split('_')[-1]
            if latest_date is None or date_str > latest_date:
                latest_date = date_str
                latest_file = tle_file
                
                # 計算衛星數量（每3行為一個衛星記錄）
                if tle_file.stat().st_size > 0:
                    try:
                        with open(tle_file, 'r', encoding='utf-8') as f:
                            lines = len([l for l in f if l.strip()])
                        latest_satellite_count = lines // 3
                    except Exception as e:
                        self.logger.warning(f"讀取文件 {tle_file} 時出錯: {e}")
                        latest_satellite_count = 0
        
        result = {
            'files_count': len(tle_files),
            'latest_date': latest_date,
            'latest_file': str(latest_file),
            'satellite_count': latest_satellite_count
        }
        
        self.logger.info(f"📡 {constellation} 掃描: {len(tle_files)} 文件, 最新({latest_date}): {latest_satellite_count} 衛星")
        return result
    
    def load_satellite_data(self, scan_result: Dict[str, Any], sample_mode: bool = False, sample_size: int = 500) -> List[Dict[str, Any]]:
        """
        載入衛星數據
        
        Args:
            scan_result: 掃描結果
            sample_mode: 是否使用採樣模式
            sample_size: 採樣大小
            
        Returns:
            衛星數據列表
        """
        self.logger.info(f"📥 開始載入衛星數據 (採樣模式: {sample_mode})")
        
        all_satellites = []
        
        for constellation, info in scan_result['constellations'].items():
            if not info['latest_file']:
                continue
                
            try:
                satellites = self._load_tle_file(info['latest_file'], constellation)
                all_satellites.extend(satellites)
                
                self.logger.info(f"✅ {constellation} 載入完成: {len(satellites)} 顆衛星")
                
            except Exception as e:
                self.logger.error(f"❌ 載入 {constellation} 數據失敗: {e}")
                self.load_statistics["load_errors"] += 1
                continue
        
        # 應用採樣
        if sample_mode and len(all_satellites) > sample_size:
            import random
            all_satellites = random.sample(all_satellites, sample_size)
            self.logger.info(f"🎲 已應用採樣: {len(all_satellites)} 顆衛星")
        
        self.load_statistics["satellites_loaded"] = len(all_satellites)
        self.logger.info(f"📊 總計載入 {len(all_satellites)} 顆衛星")
        
        return all_satellites
    
    def _load_tle_file(self, file_path: str, constellation: str) -> List[Dict[str, Any]]:
        """載入單個TLE文件"""
        satellites = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
            
            # 每3行為一組：衛星名稱、TLE Line 1、TLE Line 2
            for i in range(0, len(lines), 3):
                if i + 2 >= len(lines):
                    break
                
                satellite_name = lines[i]
                tle_line1 = lines[i + 1]
                tle_line2 = lines[i + 2]
                
                # 基本TLE格式驗證
                if not self._validate_tle_format(tle_line1, tle_line2):
                    self.logger.warning(f"跳過無效TLE: {satellite_name}")
                    continue
                
                satellite_data = {
                    "name": satellite_name,
                    "constellation": constellation,
                    "tle_line1": tle_line1,
                    "tle_line2": tle_line2,
                    "norad_id": self._extract_norad_id(tle_line1),
                    "source_file": file_path
                }
                
                satellites.append(satellite_data)
                
        except Exception as e:
            raise RuntimeError(f"載入TLE文件失敗 {file_path}: {e}")
        
        return satellites
    
    def _validate_tle_format(self, line1: str, line2: str) -> bool:
        """基本TLE格式驗證 - 寬鬆版本用於開發測試"""
        try:
            # 檢查最小長度 (允許稍短的測試數據)
            if len(line1) < 60 or len(line2) < 60:
                return False
            
            # 檢查行首
            if line1[0] != '1' or line2[0] != '2':
                return False
            
            # 檢查NORAD ID一致性 (允許更寬鬆的格式)
            if len(line1) >= 7 and len(line2) >= 7:
                norad_id1 = line1[2:7].strip()
                norad_id2 = line2[2:7].strip()
                return norad_id1 == norad_id2
            
            return True  # 如果長度不夠，暫時通過
            
        except Exception:
            return False
    
    def _extract_norad_id(self, tle_line1: str) -> str:
        """提取NORAD衛星ID"""
        try:
            return tle_line1[2:7].strip()
        except Exception:
            return "UNKNOWN"
    
    def get_load_statistics(self) -> Dict[str, Any]:
        """獲取載入統計信息"""
        return self.load_statistics.copy()
    
    def health_check(self) -> Dict[str, Any]:
        """執行TLE數據健康檢查"""
        health_status = {
            "overall_healthy": True,
            "base_path_exists": self.tle_data_dir.exists(),
            "total_tle_files": 0,
            "latest_files": {},
            "issues": []
        }
        
        if not health_status["base_path_exists"]:
            health_status["overall_healthy"] = False
            health_status["issues"].append(f"TLE基礎路徑不存在: {self.tle_data_dir}")
            return health_status
        
        # 檢查各星座數據
        for constellation in ['starlink', 'oneweb']:
            constellation_dir = self.tle_data_dir / constellation / "tle"
            
            if not constellation_dir.exists():
                health_status["issues"].append(f"{constellation} TLE目錄不存在")
                continue
            
            tle_files = list(constellation_dir.glob(f"{constellation}_*.tle"))
            health_status["total_tle_files"] += len(tle_files)
            
            if tle_files:
                # 找最新文件
                latest_file = max(tle_files, key=lambda f: f.stem.split('_')[-1])
                health_status["latest_files"][constellation] = latest_file.stem.split('_')[-1]
            else:
                health_status["issues"].append(f"{constellation} 無TLE文件")
        
        if health_status["issues"]:
            health_status["overall_healthy"] = False
        
        return health_status