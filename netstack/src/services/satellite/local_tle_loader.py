#!/usr/bin/env python3
"""
本地 TLE 文字檔載入器
支援從本地文字檔載入 Starlink TLE 數據

使用方法：
1. 將 TLE 文字檔放在 data/ 目錄
2. 支援的檔案名：starlink.txt, starlink.tle, starlink_tle.txt
3. 格式：標準 TLE 三行格式
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class LocalTLELoader:
    """本地 TLE 文字檔載入器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 支援的檔案名列表
        self.supported_filenames = [
            "starlink.txt",
            "starlink.tle", 
            "starlink_tle.txt",
            "celestrak_starlink.txt",
            "starlink_latest.txt"
        ]
        
    def find_tle_file(self) -> Optional[Path]:
        """尋找可用的 TLE 檔案"""
        for filename in self.supported_filenames:
            file_path = self.data_dir / filename
            if file_path.exists():
                logger.info(f"找到 TLE 檔案: {file_path}")
                return file_path
        
        logger.warning(f"未找到 TLE 檔案，查找路徑: {self.data_dir}")
        logger.info(f"支援的檔案名: {', '.join(self.supported_filenames)}")
        return None
    
    def load_tle_from_file(self, file_path: Path) -> List[Dict[str, str]]:
        """從檔案載入 TLE 數據"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"成功讀取檔案: {file_path} ({len(content)} 字符)")
            
            # 解析 TLE 數據
            satellites = self.parse_tle_content(content)
            
            logger.info(f"解析完成: {len(satellites)} 顆衛星")
            return satellites
            
        except Exception as e:
            logger.error(f"讀取檔案失敗 {file_path}: {e}")
            return []
    
    def parse_tle_content(self, content: str) -> List[Dict[str, str]]:
        """解析 TLE 內容"""
        satellites = []
        lines = content.strip().split('\n')
        
        # 清理空行
        lines = [line.strip() for line in lines if line.strip()]
        
        i = 0
        while i < len(lines):
            # TLE 格式: 名稱行 + 第一行 + 第二行
            if i + 2 < len(lines):
                name_line = lines[i].strip()
                line1 = lines[i + 1].strip()
                line2 = lines[i + 2].strip()
                
                # 驗證 TLE 格式
                if (line1.startswith('1 ') and 
                    line2.startswith('2 ') and 
                    len(line1) >= 69 and 
                    len(line2) >= 69):
                    
                    # 提取 NORAD ID
                    try:
                        norad_id = int(line1[2:7].strip())
                        
                        satellite_data = {
                            'name': name_line,
                            'norad_id': norad_id,
                            'line1': line1,
                            'line2': line2,
                            'download_time': datetime.now(timezone.utc).isoformat(),
                            'data_source': 'local_file'
                        }
                        
                        satellites.append(satellite_data)
                        logger.debug(f"解析衛星: {name_line} (ID: {norad_id})")
                        
                    except ValueError as e:
                        logger.warning(f"無法解析 NORAD ID: {line1[:10]} - {e}")
                
                i += 3
            else:
                i += 1
        
        return satellites
    
    def get_starlink_tle_data(self) -> List[Dict[str, str]]:
        """獲取 Starlink TLE 數據"""
        # 1. 先尋找本地檔案
        tle_file = self.find_tle_file()
        
        if tle_file:
            satellites = self.load_tle_from_file(tle_file)
            if satellites:
                logger.info(f"成功從本地檔案載入 {len(satellites)} 顆 Starlink 衛星")
                return satellites
        
        # 2. 如果沒有本地檔案，回退到歷史數據
        logger.warning("本地檔案不可用，回退到歷史數據")
        return self.load_historical_data()
    
    def load_historical_data(self) -> List[Dict[str, str]]:
        """載入歷史數據作為備用"""
        try:
            import sys
            sys.path.append('/app/netstack_api')
            from netstack_api.data.historical_tle_data import get_historical_tle_data
            
            historical_starlink = get_historical_tle_data('starlink')
            
            # 轉換為標準格式
            satellites = []
            for sat_data in historical_starlink:
                satellite = {
                    'name': sat_data['name'],
                    'norad_id': sat_data['norad_id'],
                    'line1': sat_data['line1'],
                    'line2': sat_data['line2'],
                    'download_time': datetime.now(timezone.utc).isoformat(),
                    'data_source': 'historical_data'
                }
                satellites.append(satellite)
            
            logger.info(f"載入歷史數據: {len(satellites)} 顆衛星")
            return satellites
            
        except Exception as e:
            logger.error(f"載入歷史數據失敗: {e}")
            return []
    
    def save_sample_file(self) -> None:
        """創建範例 TLE 檔案"""
        sample_content = """STARLINK-1007
1 44713U 19074A   24300.50000000  .00001234  00000-0  12345-3 0  9990
2 44713  53.0540 123.4567 0001890  89.1234 270.8765 15.05432187 12345
STARLINK-1008
1 44714U 19074B   24300.50000000  .00001189  00000-0  11987-3 0  9991
2 44714  53.0540 133.5678 0001123  90.2345 269.7654 15.05432207 12346
STARLINK-1009
1 44715U 19074C   24300.50000000  .00001156  00000-0  11634-3 0  9992
2 44715  53.0540 143.6789 0001234  91.3456 268.6543 15.05432227 12347"""
        
        sample_file = self.data_dir / "starlink_sample.txt"
        
        try:
            with open(sample_file, 'w', encoding='utf-8') as f:
                f.write(sample_content)
            
            logger.info(f"範例檔案已創建: {sample_file}")
            print(f"📄 範例 TLE 檔案已創建: {sample_file}")
            print(f"💡 你可以將真實的 TLE 數據保存為以下任一檔案名:")
            for filename in self.supported_filenames:
                print(f"   - {self.data_dir / filename}")
                
        except Exception as e:
            logger.error(f"創建範例檔案失敗: {e}")

def main():
    """主函數 - 演示本地 TLE 載入"""
    print("📄 本地 TLE 文字檔載入器")
    print("=" * 40)
    
    loader = LocalTLELoader()
    
    # 創建範例檔案
    loader.save_sample_file()
    
    # 嘗試載入數據
    satellites = loader.get_starlink_tle_data()
    
    if satellites:
        print(f"\n✅ 成功載入 {len(satellites)} 顆衛星數據")
        print(f"📊 數據來源: {satellites[0].get('data_source', 'unknown')}")
        
        # 顯示前幾顆衛星
        print(f"\n📝 前5顆衛星:")
        for i, sat in enumerate(satellites[:5]):
            print(f"  {i+1}. {sat['name']} (ID: {sat['norad_id']})")
    else:
        print("❌ 未載入任何數據")

if __name__ == "__main__":
    main()