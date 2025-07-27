#!/usr/bin/env python3
"""
Starlink TLE Data Downloader - Phase 0 Implementation
完整的 Starlink TLE 數據下載、緩存和驗證系統

功能:
1. 從 CelesTrak 下載所有當前 Starlink TLE 數據（~6000 顆衛星）
2. 本地存儲完整數據集，避免重複下載
3. 數據驗證和完整性檢查
4. 支援增量更新和快取機制
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import re

import aiohttp
import aiofiles
from skyfield.api import EarthSatellite, utc, load
from skyfield.sgp4lib import EarthSatellite as SGP4Satellite


# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StarlinkTLEDownloader:
    """完整的 Starlink TLE 數據下載器"""
    
    def __init__(self, cache_dir: str = "data/starlink_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # CelesTrak Starlink TLE 數據源
        self.starlink_urls = [
            "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle",
            "https://celestrak.org/NORAD/elements/supplemental/starlink.txt",
            "https://celestrak.org/NORAD/elements/starlink.txt"
        ]
        
        # 緩存文件路徑
        self.cache_file = self.cache_dir / "starlink_complete_tle.json"
        self.metadata_file = self.cache_dir / "metadata.json"
        
        # 天體軌道加載器
        self.ts = load.timescale()
        
    async def download_tle_from_url(self, url: str, timeout: int = 30) -> List[str]:
        """從指定 URL 下載 TLE 數據"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        logger.info(f"成功從 {url} 下載 TLE 數據，大小: {len(content)} 字符")
                        return content.strip().split('\n')
                    else:
                        logger.error(f"下載失敗 {url}: HTTP {response.status}")
                        return []
        except Exception as e:
            logger.error(f"下載 {url} 時發生錯誤: {e}")
            return []
    
    def parse_tle_lines(self, lines: List[str]) -> List[Dict[str, str]]:
        """解析 TLE 行數據為衛星資訊"""
        satellites = []
        
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
                            'download_time': datetime.now(timezone.utc).isoformat()
                        }
                        
                        satellites.append(satellite_data)
                        logger.debug(f"解析衛星: {name_line} (ID: {norad_id})")
                        
                    except ValueError as e:
                        logger.warning(f"無法解析 NORAD ID: {line1[:10]} - {e}")
                
                i += 3
            else:
                i += 1
        
        return satellites
    
    async def download_all_starlink_data(self) -> List[Dict[str, str]]:
        """從所有來源下載完整的 Starlink TLE 數據"""
        logger.info("開始下載所有 Starlink TLE 數據...")
        
        all_satellites = {}  # 使用 NORAD ID 作為 key 避免重複
        
        # 並行下載所有數據源
        download_tasks = [
            self.download_tle_from_url(url) for url in self.starlink_urls
        ]
        
        results = await asyncio.gather(*download_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"下載源 {i+1} 失敗: {result}")
                continue
            
            if not result:
                logger.warning(f"下載源 {i+1} 返回空數據")
                continue
            
            # 解析 TLE 數據
            satellites = self.parse_tle_lines(result)
            logger.info(f"從源 {i+1} 解析到 {len(satellites)} 顆衛星")
            
            # 合併數據，避免重複
            for sat in satellites:
                norad_id = sat['norad_id']
                if norad_id not in all_satellites:
                    all_satellites[norad_id] = sat
                else:
                    # 保留最新的數據
                    existing_time = datetime.fromisoformat(all_satellites[norad_id]['download_time'])
                    new_time = datetime.fromisoformat(sat['download_time'])
                    if new_time > existing_time:
                        all_satellites[norad_id] = sat
        
        unique_satellites = list(all_satellites.values())
        logger.info(f"總共獲得 {len(unique_satellites)} 顆唯一的 Starlink 衛星")
        
        return unique_satellites
    
    def validate_satellite_data(self, satellite: Dict[str, str]) -> bool:
        """驗證單顆衛星的 TLE 數據有效性"""
        try:
            # 使用 Skyfield 驗證 TLE 數據
            sat = EarthSatellite(satellite['line1'], satellite['line2'], satellite['name'])
            
            # 測試計算當前位置
            t = self.ts.now()
            geocentric = sat.at(t)
            
            # 檢查計算結果是否合理（地球軌道範圍）
            distance_km = geocentric.distance().km
            if 200 <= distance_km <= 2000:  # Starlink 軌道高度範圍
                return True
            else:
                logger.warning(f"衛星 {satellite['name']} 軌道高度異常: {distance_km:.1f} km")
                return False
                
        except Exception as e:
            logger.error(f"驗證衛星 {satellite['name']} 失敗: {e}")
            return False
    
    async def cache_tle_data(self, satellites: List[Dict[str, str]]) -> None:
        """緩存 TLE 數據到本地文件"""
        logger.info(f"緩存 {len(satellites)} 顆衛星數據到 {self.cache_file}")
        
        # 準備緩存數據
        cache_data = {
            'metadata': {
                'download_time': datetime.now(timezone.utc).isoformat(),
                'total_satellites': len(satellites),
                'data_sources': self.starlink_urls,
                'cache_version': '1.0'
            },
            'satellites': satellites
        }
        
        # 寫入緩存文件
        async with aiofiles.open(self.cache_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(cache_data, indent=2, ensure_ascii=False))
        
        # 寫入元數據文件
        async with aiofiles.open(self.metadata_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(cache_data['metadata'], indent=2, ensure_ascii=False))
        
        logger.info("TLE 數據緩存完成")
    
    async def load_cached_data(self) -> Optional[List[Dict[str, str]]]:
        """從緩存加載 TLE 數據"""
        if not self.cache_file.exists():
            logger.info("緩存文件不存在")
            return None
        
        try:
            async with aiofiles.open(self.cache_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                cache_data = json.loads(content)
            
            # 檢查緩存時間
            cache_time = datetime.fromisoformat(cache_data['metadata']['download_time'])
            age_hours = (datetime.now(timezone.utc) - cache_time).total_seconds() / 3600
            
            if age_hours > 24:  # 緩存超過24小時則重新下載
                logger.info(f"緩存數據已過期 ({age_hours:.1f} 小時)，需要重新下載")
                return None
            
            logger.info(f"載入緩存數據: {len(cache_data['satellites'])} 顆衛星 (緩存時間: {age_hours:.1f} 小時前)")
            return cache_data['satellites']
            
        except Exception as e:
            logger.error(f"載入緩存失敗: {e}")
            return None
    
    async def get_starlink_tle_data(self, force_download: bool = False) -> List[Dict[str, str]]:
        """獲取 Starlink TLE 數據（優先使用緩存）"""
        if not force_download:
            cached_data = await self.load_cached_data()
            if cached_data:
                return cached_data
        
        # 下載新數據
        satellites = await self.download_all_starlink_data()
        
        if satellites:
            await self.cache_tle_data(satellites)
            return satellites
        else:
            logger.error("無法下載任何 Starlink 數據")
            return []
    
    async def verify_complete_dataset(self, satellites: List[Dict[str, str]]) -> Dict[str, Any]:
        """驗證完整數據集的品質和完整性"""
        logger.info("開始驗證完整數據集...")
        
        validation_result = {
            'total_satellites': len(satellites),
            'valid_satellites': 0,
            'invalid_satellites': 0,
            'validation_errors': [],
            'orbital_statistics': {
                'min_altitude_km': float('inf'),
                'max_altitude_km': 0,
                'avg_altitude_km': 0
            }
        }
        
        valid_satellites = []
        altitudes = []
        
        for i, satellite in enumerate(satellites):
            if i % 100 == 0:
                logger.info(f"驗證進度: {i}/{len(satellites)}")
            
            try:
                if self.validate_satellite_data(satellite):
                    validation_result['valid_satellites'] += 1
                    valid_satellites.append(satellite)
                    
                    # 計算軌道統計
                    sat = EarthSatellite(satellite['line1'], satellite['line2'], satellite['name'])
                    t = self.ts.now()
                    geocentric = sat.at(t)
                    altitude = geocentric.distance().km
                    altitudes.append(altitude)
                    
                    validation_result['orbital_statistics']['min_altitude_km'] = min(
                        validation_result['orbital_statistics']['min_altitude_km'], altitude)
                    validation_result['orbital_statistics']['max_altitude_km'] = max(
                        validation_result['orbital_statistics']['max_altitude_km'], altitude)
                else:
                    validation_result['invalid_satellites'] += 1
                    validation_result['validation_errors'].append(f"衛星 {satellite['name']} 驗證失敗")
                    
            except Exception as e:
                validation_result['invalid_satellites'] += 1
                validation_result['validation_errors'].append(f"衛星 {satellite['name']} 驗證錯誤: {e}")
        
        # 計算平均高度
        if altitudes:
            validation_result['orbital_statistics']['avg_altitude_km'] = sum(altitudes) / len(altitudes)
        
        logger.info(f"數據集驗證完成: {validation_result['valid_satellites']}/{len(satellites)} 顆衛星有效")
        
        return validation_result


async def main():
    """主函數 - 演示完整下載流程"""
    downloader = StarlinkTLEDownloader()
    
    # 下載所有 Starlink TLE 數據
    logger.info("=== Phase 0.1: 完整 Starlink TLE 數據下載器 ===")
    
    satellites = await downloader.get_starlink_tle_data(force_download=True)
    
    if satellites:
        logger.info(f"成功下載 {len(satellites)} 顆 Starlink 衛星數據")
        
        # 驗證數據集
        validation_result = await downloader.verify_complete_dataset(satellites)
        
        # 輸出驗證結果
        print("\n=== 驗證結果 ===")
        print(f"總衛星數量: {validation_result['total_satellites']}")
        print(f"有效衛星: {validation_result['valid_satellites']}")
        print(f"無效衛星: {validation_result['invalid_satellites']}")
        print(f"軌道高度範圍: {validation_result['orbital_statistics']['min_altitude_km']:.1f} - {validation_result['orbital_statistics']['max_altitude_km']:.1f} km")
        print(f"平均軌道高度: {validation_result['orbital_statistics']['avg_altitude_km']:.1f} km")
        
        if validation_result['validation_errors']:
            print(f"\n前10個驗證錯誤:")
            for error in validation_result['validation_errors'][:10]:
                print(f"  - {error}")
        
        print(f"\n數據已保存到: {downloader.cache_file}")
        
    else:
        logger.error("下載失敗")


if __name__ == "__main__":
    asyncio.run(main())