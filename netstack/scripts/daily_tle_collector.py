#!/usr/bin/env python3
"""
Phase 3: 45天歷史數據收集自動化
每日自動收集 TLE 數據，建立完整的 45 天數據集
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import hashlib
import sys
import os

# 添加路徑以導入 Phase 0 模組
sys.path.append('/app/src')
sys.path.append('/app')

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daily_tle_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DailyTLECollector:
    """45天歷史數據收集器"""
    
    def __init__(self, target_days: int = 45):
        self.target_days = target_days
        self.base_dir = Path("netstack/tle_data")
        self.backup_dir = self.base_dir / "backups"
        
        # 確保目錄存在
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 支援的星座配置
        self.constellations = {
            'starlink': {
                'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle',
                'backup_url': 'https://www.celestrak.com/NORAD/elements/starlink.txt'
            },
            'oneweb': {
                'url': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle',
                'backup_url': 'https://www.celestrak.com/NORAD/elements/oneweb.txt'
            }
        }
        
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'NTN-Stack/1.0 Research Tool'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    def get_date_range(self) -> List[datetime]:
        """獲取需要收集的日期範圍"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=self.target_days - 1)
        
        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(datetime.combine(current_date, datetime.min.time()))
            current_date += timedelta(days=1)
        
        return dates
    
    def get_existing_data_status(self) -> Dict[str, Dict[str, bool]]:
        """檢查現有數據狀態"""
        status = {}
        
        for constellation in self.constellations.keys():
            status[constellation] = {}
            
            # 檢查 TLE 文件
            for date in self.get_date_range():
                date_str = date.strftime('%Y%m%d')
                tle_file = self.base_dir / constellation / f"{constellation}_{date_str}.tle"
                json_file = self.base_dir / constellation / f"{constellation}_{date_str}.json"
                
                status[constellation][date_str] = {
                    'tle_exists': tle_file.exists(),
                    'json_exists': json_file.exists(),
                    'tle_size': tle_file.stat().st_size if tle_file.exists() else 0,
                    'json_size': json_file.stat().st_size if json_file.exists() else 0
                }
        
        return status
    
    async def download_tle_data(self, constellation: str, url: str) -> Optional[str]:
        """下載 TLE 數據"""
        try:
            logger.info(f"📡 下載 {constellation} TLE 數據: {url}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # 驗證 TLE 格式
                    if self.validate_tle_format(content):
                        logger.info(f"✅ {constellation} TLE 數據下載成功 ({len(content)} 字符)")
                        return content
                    else:
                        logger.warning(f"⚠️ {constellation} TLE 格式驗證失敗")
                        return None
                else:
                    logger.error(f"❌ {constellation} TLE 下載失敗: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ {constellation} TLE 下載異常: {e}")
            return None
    
    def validate_tle_format(self, content: str) -> bool:
        """驗證 TLE 格式"""
        lines = content.strip().split('\n')
        
        # 基本檢查：應該有衛星名稱和兩行 TLE 數據
        if len(lines) < 3:
            return False
        
        # 檢查 TLE 行格式
        tle_lines = [line for line in lines if line.startswith(('1 ', '2 '))]
        
        if len(tle_lines) < 2:
            return False
        
        # 檢查第一行和第二行的格式
        for line in tle_lines[:2]:
            if len(line) != 69:  # TLE 行應該是 69 個字符
                return False
        
        return True
    
    def parse_tle_to_json(self, tle_content: str, constellation: str) -> Dict:
        """將 TLE 數據解析為 JSON 格式"""
        lines = tle_content.strip().split('\n')
        satellites = []
        
        i = 0
        while i < len(lines) - 2:
            if lines[i + 1].startswith('1 ') and lines[i + 2].startswith('2 '):
                satellite_name = lines[i].strip()
                line1 = lines[i + 1].strip()
                line2 = lines[i + 2].strip()
                
                # 提取 NORAD ID
                norad_id = line1.split()[1].rstrip('U')
                
                satellites.append({
                    'name': satellite_name,
                    'norad_id': norad_id,
                    'line1': line1,
                    'line2': line2,
                    'constellation': constellation
                })
                
                i += 3
            else:
                i += 1
        
        return {
            'constellation': constellation,
            'collection_date': datetime.now().isoformat(),
            'satellite_count': len(satellites),
            'satellites': satellites
        }
    
    async def save_daily_data(self, constellation: str, date: datetime, tle_content: str) -> bool:
        """保存每日數據"""
        try:
            date_str = date.strftime('%Y%m%d')
            constellation_dir = self.base_dir / constellation
            constellation_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存 TLE 文件
            tle_file = constellation_dir / f"{constellation}_{date_str}.tle"
            with open(tle_file, 'w', encoding='utf-8') as f:
                f.write(tle_content)
            
            # 轉換並保存 JSON 文件
            json_data = self.parse_tle_to_json(tle_content, constellation)
            json_file = constellation_dir / f"{constellation}_{date_str}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            # 創建備份
            backup_dir = self.backup_dir / constellation / date_str
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 計算文件哈希
            tle_hash = hashlib.md5(tle_content.encode()).hexdigest()
            
            # 保存元數據
            metadata = {
                'constellation': constellation,
                'date': date.isoformat(),
                'tle_file': str(tle_file),
                'json_file': str(json_file),
                'satellite_count': json_data['satellite_count'],
                'file_hash': tle_hash,
                'file_size': len(tle_content)
            }
            
            metadata_file = backup_dir / 'metadata.json'
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 {constellation} {date_str} 數據保存成功 ({json_data['satellite_count']} 顆衛星)")
            return True
            
        except Exception as e:
            logger.error(f"❌ {constellation} {date_str} 數據保存失敗: {e}")
            return False
    
    async def collect_daily_data(self) -> Dict[str, int]:
        """每日自動收集 TLE 數據"""
        logger.info(f"🚀 開始收集 {self.target_days} 天歷史 TLE 數據")
        
        results = {'success': 0, 'failed': 0, 'skipped': 0}
        existing_status = self.get_existing_data_status()
        
        today = datetime.now()
        
        for constellation, config in self.constellations.items():
            logger.info(f"📡 處理 {constellation} 星座")
            
            # 下載今日數據
            tle_content = await self.download_tle_data(constellation, config['url'])
            
            if not tle_content:
                # 嘗試備用 URL
                logger.info(f"🔄 嘗試備用 URL: {config['backup_url']}")
                tle_content = await self.download_tle_data(constellation, config['backup_url'])
            
            if tle_content:
                # 保存今日數據
                if await self.save_daily_data(constellation, today, tle_content):
                    results['success'] += 1
                else:
                    results['failed'] += 1
            else:
                logger.error(f"❌ {constellation} 數據下載完全失敗")
                results['failed'] += 1
        
        logger.info(f"📊 收集結果: 成功 {results['success']}, 失敗 {results['failed']}, 跳過 {results['skipped']}")
        return results
    
    def validate_45day_completeness(self) -> Dict:
        """驗證45天數據集完整性"""
        logger.info("🔍 驗證 45 天數據集完整性")
        
        status = self.get_existing_data_status()
        report = {
            'target_days': self.target_days,
            'validation_date': datetime.now().isoformat(),
            'constellations': {},
            'overall_completeness': 0.0
        }
        
        total_expected = self.target_days * len(self.constellations)
        total_complete = 0
        
        for constellation, dates in status.items():
            constellation_complete = 0
            constellation_report = {
                'expected_days': self.target_days,
                'available_days': 0,
                'missing_dates': [],
                'incomplete_dates': [],
                'total_satellites': 0
            }
            
            for date_str, file_status in dates.items():
                if file_status['tle_exists'] and file_status['json_exists']:
                    if file_status['tle_size'] > 1000 and file_status['json_size'] > 100:
                        constellation_complete += 1
                        total_complete += 1
                    else:
                        constellation_report['incomplete_dates'].append(date_str)
                else:
                    constellation_report['missing_dates'].append(date_str)
            
            constellation_report['available_days'] = constellation_complete
            constellation_report['completeness'] = (constellation_complete / self.target_days) * 100
            
            report['constellations'][constellation] = constellation_report
            
            logger.info(f"📊 {constellation}: {constellation_complete}/{self.target_days} 天 ({constellation_report['completeness']:.1f}%)")
        
        report['overall_completeness'] = (total_complete / total_expected) * 100
        
        # 保存驗證報告
        report_file = self.base_dir / 'completeness_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 整體完整性: {report['overall_completeness']:.1f}%")
        logger.info(f"💾 驗證報告已保存: {report_file}")
        
        return report

async def main():
    """主函數"""
    async with DailyTLECollector(target_days=45) as collector:
        # 收集今日數據
        results = await collector.collect_daily_data()
        
        # 驗證數據完整性
        completeness_report = collector.validate_45day_completeness()
        
        print(f"\n🎯 收集結果摘要:")
        print(f"成功: {results['success']}")
        print(f"失敗: {results['failed']}")
        print(f"整體完整性: {completeness_report['overall_completeness']:.1f}%")

if __name__ == "__main__":
    asyncio.run(main())
