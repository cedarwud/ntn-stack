#!/usr/bin/env python3
"""
TLE 數據管理系統

實現統一改進主準則中的 TLE 數據管理功能：
1. TLE 數據存儲和檢索
2. 自動更新機制
3. 數據驗證和錯誤處理
4. 多星座支援 (Starlink/OneWeb/GPS)
5. 數據備份和恢復
"""

import asyncio
import aiofiles
import aiohttp
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import structlog
from urllib.parse import urljoin
import hashlib

from .orbit_calculation_engine import TLEData

logger = structlog.get_logger(__name__)


@dataclass
class TLESource:
    """TLE 數據源配置"""
    name: str
    url: str
    constellation: str  # starlink, oneweb, gps, etc.
    update_interval_hours: int = 24
    api_key: Optional[str] = None
    is_active: bool = True
    last_updated: Optional[datetime] = None
    
    
@dataclass
class TLEUpdateResult:
    """TLE 更新結果"""
    source_name: str
    satellites_updated: int
    satellites_added: int  
    satellites_failed: int
    update_time: datetime
    errors: List[str]
    success: bool
    

@dataclass
class ConstellationInfo:
    """星座資訊"""
    name: str
    satellite_count: int
    active_satellites: int
    last_updated: datetime
    coverage_area: str  # global, regional, etc.
    operator: str


class TLEDataManager:
    """
    TLE 數據管理系統
    
    功能：
    1. 管理多個 TLE 數據源
    2. 自動更新 TLE 數據
    3. 數據驗證和清理
    4. 提供 TLE 檢索 API
    5. 備份和恢復機制
    """
    
    def __init__(self, data_dir: str = "/tmp/tle_data"):
        """
        初始化 TLE 數據管理器
        
        Args:
            data_dir: 數據存儲目錄
        """
        self.logger = structlog.get_logger(__name__)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # TLE 數據存儲
        self.tle_database: Dict[str, TLEData] = {}
        self.constellation_info: Dict[str, ConstellationInfo] = {}
        
        # 數據源配置
        self.tle_sources: Dict[str, TLESource] = {}
        self.update_tasks: Dict[str, asyncio.Task] = {}
        
        # 配置文件路徑
        self.config_file = self.data_dir / "tle_config.json"
        self.backup_dir = self.data_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # 統計信息
        self.update_history: List[TLEUpdateResult] = []
        self.max_history_entries = 100
        
        self.logger.info(
            "TLE 數據管理器初始化完成",
            data_dir=str(self.data_dir),
            backup_dir=str(self.backup_dir)
        )
        
    async def initialize_default_sources(self) -> None:
        """初始化默認的 TLE 數據源"""
        try:
            default_sources = [
                TLESource(
                    name="celestrak_starlink",
                    url="https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle",
                    constellation="starlink",
                    update_interval_hours=12
                ),
                TLESource(
                    name="celestrak_oneweb", 
                    url="https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle",
                    constellation="oneweb",
                    update_interval_hours=24
                ),
                TLESource(
                    name="celestrak_gps",
                    url="https://celestrak.org/NORAD/elements/gp.php?GROUP=gps-ops&FORMAT=tle", 
                    constellation="gps",
                    update_interval_hours=168  # 每週更新
                ),
                TLESource(
                    name="spacetrack_active",
                    url="https://www.space-track.org/basicspacedata/query/class/gp/",
                    constellation="mixed",
                    update_interval_hours=24,
                    is_active=False  # 需要 API 密鑰
                )
            ]
            
            for source in default_sources:
                await self.add_tle_source(source)
                
            self.logger.info(
                "默認 TLE 數據源初始化完成",
                sources_count=len(default_sources)
            )
            
        except Exception as e:
            self.logger.error("默認數據源初始化失敗", error=str(e))
            
    async def add_tle_source(self, source: TLESource) -> bool:
        """
        添加 TLE 數據源
        
        Args:
            source: TLE 數據源配置
            
        Returns:
            是否成功添加
        """
        try:
            self.tle_sources[source.name] = source
            
            # 如果數據源激活，啟動自動更新任務
            if source.is_active:
                await self._start_update_task(source.name)
                
            self.logger.info(
                "TLE 數據源添加成功",
                source_name=source.name,
                constellation=source.constellation,
                url=source.url,
                update_interval_hours=source.update_interval_hours
            )
            
            # 保存配置
            await self._save_config()
            return True
            
        except Exception as e:
            self.logger.error(
                "TLE 數據源添加失敗",
                source_name=source.name,
                error=str(e)
            )
            return False
            
    async def update_tle_from_source(self, source_name: str) -> TLEUpdateResult:
        """
        從指定數據源更新 TLE 數據
        
        Args:
            source_name: 數據源名稱
            
        Returns:
            更新結果
        """
        result = TLEUpdateResult(
            source_name=source_name,
            satellites_updated=0,
            satellites_added=0,
            satellites_failed=0,
            update_time=datetime.now(timezone.utc),
            errors=[],
            success=False
        )
        
        try:
            if source_name not in self.tle_sources:
                result.errors.append(f"數據源 {source_name} 不存在")
                return result
                
            source = self.tle_sources[source_name]
            
            if not source.is_active:
                result.errors.append(f"數據源 {source_name} 未激活")
                return result
                
            self.logger.info(
                "開始更新 TLE 數據",
                source_name=source_name,
                url=source.url,
                constellation=source.constellation
            )
            
            # 下載 TLE 數據
            tle_content = await self._download_tle_data(source.url, source.api_key)
            
            if not tle_content:
                result.errors.append("TLE 數據下載失敗")
                return result
                
            # 解析 TLE 數據
            parsed_tles = await self._parse_tle_content(tle_content, source.constellation)
            
            # 更新數據庫
            for tle_data in parsed_tles:
                try:
                    if tle_data.satellite_id in self.tle_database:
                        # 更新現有衛星
                        if self._is_newer_tle(tle_data, self.tle_database[tle_data.satellite_id]):
                            self.tle_database[tle_data.satellite_id] = tle_data
                            result.satellites_updated += 1
                    else:
                        # 新增衛星
                        self.tle_database[tle_data.satellite_id] = tle_data
                        result.satellites_added += 1
                        
                except Exception as e:
                    result.satellites_failed += 1
                    result.errors.append(f"處理衛星 {tle_data.satellite_id} 失敗: {str(e)}")
                    
            # 更新星座資訊
            await self._update_constellation_info(source.constellation)
            
            # 更新數據源最後更新時間
            source.last_updated = result.update_time
            
            # 備份數據
            await self._backup_tle_data(source_name)
            
            result.success = True
            
            self.logger.info(
                "TLE 數據更新完成",
                source_name=source_name,
                satellites_updated=result.satellites_updated,
                satellites_added=result.satellites_added,
                satellites_failed=result.satellites_failed
            )
            
        except Exception as e:
            result.errors.append(f"更新過程異常: {str(e)}")
            self.logger.error(
                "TLE 數據更新失敗",
                source_name=source_name,
                error=str(e)
            )
            
        # 記錄更新歷史
        self.update_history.append(result)
        if len(self.update_history) > self.max_history_entries:
            self.update_history = self.update_history[-self.max_history_entries:]
            
        return result
        
    async def get_tle_data(self, satellite_id: str) -> Optional[TLEData]:
        """
        獲取指定衛星的 TLE 數據
        
        Args:
            satellite_id: 衛星ID
            
        Returns:
            TLE 數據或 None
        """
        return self.tle_database.get(satellite_id)
        
    async def get_constellation_satellites(self, constellation: str) -> List[TLEData]:
        """
        獲取指定星座的所有衛星 TLE 數據
        
        Args:
            constellation: 星座名稱
            
        Returns:
            TLE 數據列表
        """
        result = []
        for tle_data in self.tle_database.values():
            # 根據衛星名稱或ID判斷星座
            if self._get_constellation_from_satellite(tle_data) == constellation.lower():
                result.append(tle_data)
                
        return result
        
    async def get_active_satellites(self, max_age_hours: int = 48) -> List[TLEData]:
        """
        獲取活躍的衛星 TLE 數據
        
        Args:
            max_age_hours: 最大數據年齡（小時）
            
        Returns:
            活躍衛星的 TLE 數據列表
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        result = []
        for tle_data in self.tle_database.values():
            if tle_data.last_updated >= cutoff_time:
                result.append(tle_data)
                
        return result
        
    async def get_constellation_info(self) -> Dict[str, ConstellationInfo]:
        """獲取所有星座資訊"""
        return self.constellation_info.copy()
        
    async def get_update_status(self) -> Dict[str, Any]:
        """獲取更新狀態"""
        return {
            "total_satellites": len(self.tle_database),
            "constellations": len(self.constellation_info),
            "active_sources": len([s for s in self.tle_sources.values() if s.is_active]),
            "last_updates": {
                name: source.last_updated.isoformat() if source.last_updated else None
                for name, source in self.tle_sources.items()
            },
            "recent_results": [asdict(r) for r in self.update_history[-5:]]
        }
        
    async def force_update_all(self) -> List[TLEUpdateResult]:
        """強制更新所有激活的數據源"""
        results = []
        
        active_sources = [name for name, source in self.tle_sources.items() if source.is_active]
        
        self.logger.info("開始強制更新所有數據源", sources=active_sources)
        
        # 並行更新所有數據源
        tasks = [self.update_tle_from_source(source_name) for source_name in active_sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理異常結果
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = TLEUpdateResult(
                    source_name=active_sources[i],
                    satellites_updated=0,
                    satellites_added=0,
                    satellites_failed=0,
                    update_time=datetime.now(timezone.utc),
                    errors=[str(result)],
                    success=False
                )
                valid_results.append(error_result)
            else:
                valid_results.append(result)
                
        return valid_results
        
    async def _download_tle_data(self, url: str, api_key: Optional[str] = None) -> Optional[str]:
        """下載 TLE 數據"""
        try:
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
                
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        content = await response.text()
                        return content
                    else:
                        self.logger.error(
                            "TLE 數據下載失敗",
                            url=url,
                            status=response.status
                        )
                        return None
                        
        except Exception as e:
            self.logger.error("TLE 數據下載異常", url=url, error=str(e))
            return None
            
    async def _parse_tle_content(self, content: str, constellation: str) -> List[TLEData]:
        """解析 TLE 內容"""
        try:
            lines = content.strip().split('\n')
            tle_data_list = []
            
            i = 0
            while i < len(lines):
                # 跳過空行
                if not lines[i].strip():
                    i += 1
                    continue
                    
                # 檢查是否有足夠的行來組成 TLE
                if i + 2 >= len(lines):
                    break
                    
                # 嘗試解析 3 行格式 (名稱 + TLE1 + TLE2)
                name_line = lines[i].strip()
                tle1_line = lines[i + 1].strip()
                tle2_line = lines[i + 2].strip()
                
                # 驗證 TLE 格式
                if (len(tle1_line) == 69 and tle1_line.startswith('1') and
                    len(tle2_line) == 69 and tle2_line.startswith('2')):
                    
                    # 提取衛星 ID
                    satellite_id = self._extract_satellite_id(name_line, tle1_line, constellation)
                    
                    # 提取 epoch 時間
                    epoch = self._extract_epoch_from_tle(tle1_line)
                    
                    tle_data = TLEData(
                        satellite_id=satellite_id,
                        satellite_name=name_line,
                        line1=tle1_line,
                        line2=tle2_line,
                        epoch=epoch,
                        last_updated=datetime.now(timezone.utc)
                    )
                    
                    tle_data_list.append(tle_data)
                    i += 3
                else:
                    i += 1
                    
            self.logger.info(
                "TLE 內容解析完成",
                constellation=constellation,
                satellites_parsed=len(tle_data_list)
            )
            
            return tle_data_list
            
        except Exception as e:
            self.logger.error("TLE 內容解析失敗", constellation=constellation, error=str(e))
            return []
            
    def _extract_satellite_id(self, name: str, tle1: str, constellation: str) -> str:
        """從 TLE 提取衛星 ID"""
        try:
            # 從 TLE1 第3-7位提取衛星編號
            catalog_number = tle1[2:7].strip()
            
            # 根據星座生成標準化 ID
            constellation_prefix = {
                "starlink": "sl",
                "oneweb": "ow", 
                "gps": "gps",
                "mixed": "sat"
            }.get(constellation.lower(), "sat")
            
            return f"{constellation_prefix}_{catalog_number}"
            
        except Exception:
            # 備用方案：使用名稱hash
            return f"sat_{hashlib.md5(name.encode()).hexdigest()[:8]}"
            
    def _extract_epoch_from_tle(self, tle1: str) -> datetime:
        """從 TLE1 提取 epoch 時間"""
        try:
            # TLE1 第19-32位是 epoch
            epoch_str = tle1[18:32]
            
            # 年份 (2位數)
            year_2digit = int(epoch_str[:2])
            year = 2000 + year_2digit if year_2digit < 57 else 1900 + year_2digit
            
            # 年內第幾天 (含小數)
            day_of_year = float(epoch_str[2:])
            
            # 轉換為 datetime
            epoch = datetime(year, 1, 1, tzinfo=timezone.utc) + timedelta(days=day_of_year - 1)
            
            return epoch
            
        except Exception:
            # 備用方案：返回當前時間
            return datetime.now(timezone.utc)
            
    def _is_newer_tle(self, new_tle: TLEData, existing_tle: TLEData) -> bool:
        """檢查新 TLE 是否比現有的更新"""
        return new_tle.epoch > existing_tle.epoch
        
    def _get_constellation_from_satellite(self, tle_data: TLEData) -> str:
        """從衛星數據推斷星座"""
        name = tle_data.satellite_name.lower()
        
        if "starlink" in name:
            return "starlink"
        elif "oneweb" in name:
            return "oneweb"
        elif "gps" in name or "navstar" in name:
            return "gps"
        else:
            return "unknown"
            
    async def _update_constellation_info(self, constellation: str) -> None:
        """更新星座資訊"""
        try:
            satellites = await self.get_constellation_satellites(constellation)
            active_satellites = await self.get_active_satellites()
            
            active_count = len([s for s in active_satellites 
                              if self._get_constellation_from_satellite(s) == constellation])
            
            constellation_info = ConstellationInfo(
                name=constellation,
                satellite_count=len(satellites),
                active_satellites=active_count,
                last_updated=datetime.now(timezone.utc),
                coverage_area="global" if constellation in ["starlink", "oneweb"] else "regional",
                operator=self._get_constellation_operator(constellation)
            )
            
            self.constellation_info[constellation] = constellation_info
            
        except Exception as e:
            self.logger.error("星座資訊更新失敗", constellation=constellation, error=str(e))
            
    def _get_constellation_operator(self, constellation: str) -> str:
        """獲取星座運營商"""
        operators = {
            "starlink": "SpaceX",
            "oneweb": "OneWeb",
            "gps": "US Space Force",
            "galileo": "European GNSS Agency",
            "beidou": "China Satellite Navigation Office"
        }
        return operators.get(constellation.lower(), "Unknown")
        
    async def _start_update_task(self, source_name: str) -> None:
        """啟動自動更新任務"""
        try:
            if source_name in self.update_tasks:
                self.update_tasks[source_name].cancel()
                
            source = self.tle_sources[source_name]
            
            async def update_loop():
                while True:
                    try:
                        await asyncio.sleep(source.update_interval_hours * 3600)
                        await self.update_tle_from_source(source_name)
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        self.logger.error(
                            "自動更新任務異常",
                            source_name=source_name,
                            error=str(e)
                        )
                        
            task = asyncio.create_task(update_loop())
            self.update_tasks[source_name] = task
            
            self.logger.info(
                "自動更新任務啟動",
                source_name=source_name,
                interval_hours=source.update_interval_hours
            )
            
        except Exception as e:
            self.logger.error("自動更新任務啟動失敗", source_name=source_name, error=str(e))
            
    async def _backup_tle_data(self, source_name: str) -> None:
        """備份 TLE 數據"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"tle_backup_{source_name}_{timestamp}.json"
            
            # 只備份相關星座的數據
            source = self.tle_sources[source_name]
            constellation_satellites = await self.get_constellation_satellites(source.constellation)
            
            backup_data = {
                "source_name": source_name,
                "constellation": source.constellation,
                "backup_time": datetime.now(timezone.utc).isoformat(),
                "satellites": [asdict(tle) for tle in constellation_satellites]
            }
            
            async with aiofiles.open(backup_file, 'w') as f:
                await f.write(json.dumps(backup_data, indent=2, default=str))
                
            self.logger.info(
                "TLE 數據備份完成",
                source_name=source_name,
                backup_file=str(backup_file),
                satellites_count=len(constellation_satellites)
            )
            
        except Exception as e:
            self.logger.error("TLE 數據備份失敗", source_name=source_name, error=str(e))
            
    async def _save_config(self) -> None:
        """保存配置文件"""
        try:
            config_data = {
                "sources": {name: asdict(source) for name, source in self.tle_sources.items()},
                "last_saved": datetime.now(timezone.utc).isoformat()
            }
            
            async with aiofiles.open(self.config_file, 'w') as f:
                await f.write(json.dumps(config_data, indent=2, default=str))
                
        except Exception as e:
            self.logger.error("配置保存失敗", error=str(e))
            
    async def load_config(self) -> bool:
        """載入配置文件"""
        try:
            if not self.config_file.exists():
                return False
                
            async with aiofiles.open(self.config_file, 'r') as f:
                content = await f.read()
                config_data = json.loads(content)
                
            for name, source_data in config_data.get("sources", {}).items():
                # 重建 TLESource 對象
                source = TLESource(**source_data)
                self.tle_sources[name] = source
                
                if source.is_active:
                    await self._start_update_task(name)
                    
            self.logger.info("配置載入成功", sources_count=len(self.tle_sources))
            return True
            
        except Exception as e:
            self.logger.error("配置載入失敗", error=str(e))
            return False