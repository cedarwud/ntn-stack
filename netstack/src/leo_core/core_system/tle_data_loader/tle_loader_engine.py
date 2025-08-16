# 🛰️ Phase 1: TLE載入引擎增強版
"""
Enhanced TLE Loader Engine - Phase 1規格完整實現
功能: 載入8,735顆衛星TLE數據，SGP4精確軌道計算，數據驗證
規格: 
- 載入時間 < 2分鐘
- 計算精度 < 100m
- 記憶體使用 < 2GB  
- 錯誤處理 90%+成功率
- 時間軸: 200個時間點，30秒間隔
版本: Phase 1.1 Enhanced
"""

import asyncio
import logging
import aiohttp
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
from pathlib import Path
import json
import numpy as np

# 嘗試導入Skyfield，如果沒有則使用簡化計算
try:
    from skyfield.api import load, EarthSatellite, Topos
    from skyfield.timelib import Time
    SKYFIELD_AVAILABLE = True
except ImportError:
    SKYFIELD_AVAILABLE = False
    logging.warning("⚠️ Skyfield未安裝，將使用簡化軌道計算")

# Phase 1增強模組導入
try:
    from .orbital_calculator import EnhancedOrbitalCalculator, SGP4Parameters, OrbitalState
    from .data_validator import EnhancedTLEValidator, ValidationLevel, ValidationResult
    ENHANCED_MODULES_AVAILABLE = True
except ImportError:
    ENHANCED_MODULES_AVAILABLE = False
    logging.warning("⚠️ Phase 1增強模組未安裝，將使用基礎功能")

@dataclass
class TLEData:
    """TLE數據結構"""
    satellite_id: str
    satellite_name: str
    line1: str
    line2: str
    epoch: datetime
    constellation: str
    
    # SGP4軌道參數 (從TLE解析)
    inclination_deg: float
    raan_deg: float
    eccentricity: float
    arg_perigee_deg: float
    mean_anomaly_deg: float
    mean_motion_revs_per_day: float
    
    # 計算得出的參數
    semi_major_axis_km: float
    orbital_period_minutes: float
    apogee_altitude_km: float
    perigee_altitude_km: float
    
    # 兼容性別名屬性
    @property
    def apogee_km(self) -> float:
        return self.apogee_altitude_km
    
    @property
    def perigee_km(self) -> float:
        return self.perigee_altitude_km

@dataclass 
class SatellitePosition:
    """衛星位置數據"""
    timestamp: datetime
    latitude_deg: float
    longitude_deg: float
    altitude_km: float
    elevation_deg: float
    azimuth_deg: float
    distance_km: float
    velocity_km_s: float

class EnhancedTLELoaderEngine:
    """Phase 1增強TLE載入和SGP4計算引擎"""
    
    def __init__(self, config: Dict, full_config: Dict = None):
        self.config = config
        self.full_config = full_config or config  # 保存完整配置以訪問其他模組設定
        self.logger = logging.getLogger(__name__)
        
        # NTPU觀測點座標
        self.observer_lat = 24.9441667
        self.observer_lon = 121.3713889
        self.observer_alt_m = 50.0  # NTPU海拔高度
        
        # Phase 1增強組件
        self.orbital_calculator = None
        self.data_validator = None
        
        # Phase 1性能目標
        self.phase1_targets = {
            'max_load_time_seconds': 120.0,       # <2分鐘載入
            'max_calculation_accuracy_m': 100.0,  # <100米精度
            'max_memory_usage_gb': 2.0,           # <2GB記憶體
            'min_success_rate': 0.90,             # 90%+成功率
            'time_points': 200,                   # 200個時間點
            'time_resolution_seconds': 30         # 30秒間隔
        }
        
        # 🔧 修復：動態查找最新本地TLE數據文件
        self.local_tle_sources = self._get_latest_local_tle_files()
        
        # ✅ 新增：從完整配置中讀取sample_limits
        self.sample_limits = {}
        if self.full_config and 'satellite_filter' in self.full_config:
            filter_config = self.full_config['satellite_filter']
            if 'sample_limits' in filter_config:
                self.sample_limits = filter_config['sample_limits']
                self.logger.info(f"🎯 樣本限制配置: {self.sample_limits}")
        
        # 載入統計
        self.load_statistics = {
            'total_satellites': 0,
            'starlink_count': 0,
            'oneweb_count': 0,
            'other_constellation_count': 0,
            'load_duration_seconds': 0.0,
            'calculation_duration_seconds': 0.0,
            'error_count': 0,
            'successful_tle_parsing': 0
        }
        
        # 內部數據存儲
        self.tle_database: Dict[str, TLEData] = {}
        self.orbital_positions: Dict[str, List[SatellitePosition]] = {}
        
        # Skyfield對象 (如果可用)
        self.ts = None
        self.observer_location = None

    def _get_latest_local_tle_files(self) -> Dict[str, str]:
        """動態查找最新的本地TLE數據文件"""
        # 🔧 修復：使用正確的本地TLE數據路徑
        tle_base_path = Path("/home/sat/ntn-stack/netstack/tle_data")
        latest_files = {}
        
        try:
            # 查找 Starlink 最新文件
            starlink_dir = tle_base_path / "starlink" / "tle"
            if starlink_dir.exists():
                starlink_files = list(starlink_dir.glob("starlink_*.tle"))
                if starlink_files:
                    latest_starlink = max(starlink_files, key=lambda f: f.stat().st_mtime)
                    latest_files['starlink'] = str(latest_starlink)
                    self.logger.info(f"🔍 找到最新Starlink TLE: {latest_starlink.name}")
            
            # 查找 OneWeb 最新文件
            oneweb_dir = tle_base_path / "oneweb" / "tle"
            if oneweb_dir.exists():
                oneweb_files = list(oneweb_dir.glob("oneweb_*.tle"))
                if oneweb_files:
                    latest_oneweb = max(oneweb_files, key=lambda f: f.stat().st_mtime)
                    latest_files['oneweb'] = str(latest_oneweb)
                    self.logger.info(f"🔍 找到最新OneWeb TLE: {latest_oneweb.name}")
            
            if not latest_files:
                self.logger.warning("⚠️ 未找到本地TLE文件，將使用fallback數據")
                
        except Exception as e:
            self.logger.error(f"❌ 查找本地TLE文件失敗: {e}")
            
        return latest_files
        
    async def initialize(self):
        """初始化Phase 1增強TLE載入引擎"""
        self.logger.info("🚀 初始化Phase 1增強TLE載入引擎...")
        
        # 基礎Skyfield初始化
        if SKYFIELD_AVAILABLE:
            try:
                self.ts = load.timescale()
                # 創建NTPU觀測點
                self.observer_location = Topos(
                    latitude_degrees=self.observer_lat,
                    longitude_degrees=self.observer_lon,
                    elevation_m=self.observer_alt_m
                )
                self.logger.info("✅ Skyfield SGP4引擎初始化成功")
            except Exception as e:
                self.logger.warning(f"⚠️ Skyfield初始化失敗: {e}")
                globals()['SKYFIELD_AVAILABLE'] = False
        
        # Phase 1增強模組初始化
        if ENHANCED_MODULES_AVAILABLE:
            try:
                # 初始化增強軌道計算器
                self.orbital_calculator = EnhancedOrbitalCalculator(
                    self.observer_lat, self.observer_lon, self.observer_alt_m
                )
                await self.orbital_calculator.initialize()
                
                # 初始化數據驗證器
                self.data_validator = EnhancedTLEValidator(ValidationLevel.ENHANCED)
                
                self.logger.info("✅ Phase 1增強模組初始化成功")
                self.logger.info(f"   - 增強軌道計算器: 精度目標 <{self.phase1_targets['max_calculation_accuracy_m']}m")
                self.logger.info(f"   - 數據驗證器: 目標成功率 ≥{self.phase1_targets['min_success_rate']*100:.0f}%")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Phase 1增強模組初始化失敗: {e}")
                globals()['ENHANCED_MODULES_AVAILABLE'] = False
        
        self.logger.info(f"📍 觀測點: NTPU ({self.observer_lat:.6f}°N, {self.observer_lon:.6f}°E, {self.observer_alt_m}m)")
        self.logger.info(f"🎯 Phase 1目標: 載入8,735顆衛星，SGP4精度<100m，成功率≥90%")
    
    async def load_full_satellite_data(self) -> Dict[str, List[TLEData]]:
        """載入全量衛星TLE數據"""
        self.logger.info("📡 開始載入全量衛星TLE數據...")
        load_start_time = datetime.now(timezone.utc)
        
        satellite_data = {
            'starlink': [],
            'oneweb': [],
            'other_constellations': []
        }
        
        try:
            # 並行載入多個星座的本地TLE數據
            loading_tasks = []
            for constellation, local_path in self.local_tle_sources.items():
                task = self._load_local_constellation_tle(constellation, local_path)
                loading_tasks.append(task)
            
            # 等待所有載入任務完成
            constellation_results = await asyncio.gather(*loading_tasks, return_exceptions=True)
            
            # 處理載入結果
            for constellation, result in zip(self.local_tle_sources.keys(), constellation_results):
                if isinstance(result, Exception):
                    self.logger.error(f"❌ {constellation} TLE載入失敗: {result}")
                    self.load_statistics['error_count'] += 1
                    continue
                
                tle_list = result
                
                if constellation == 'starlink':
                    satellite_data['starlink'] = tle_list
                    self.load_statistics['starlink_count'] = len(tle_list)
                elif constellation == 'oneweb':
                    satellite_data['oneweb'] = tle_list  
                    self.load_statistics['oneweb_count'] = len(tle_list)
                else:
                    satellite_data['other_constellations'].extend(tle_list)
                    self.load_statistics['other_constellation_count'] += len(tle_list)
                
                # 添加到內部數據庫
                for tle_data in tle_list:
                    self.tle_database[tle_data.satellite_id] = tle_data
            
            # 計算總統計
            self.load_statistics['total_satellites'] = (
                self.load_statistics['starlink_count'] + 
                self.load_statistics['oneweb_count'] + 
                self.load_statistics['other_constellation_count']
            )
            
            # 檢查是否需要使用fallback數據
            if self.load_statistics['total_satellites'] == 0:
                self.logger.warning("⚠️ 網路載入失敗，使用fallback測試數據...")
                return await self._load_fallback_data()
            
            load_duration = (datetime.now(timezone.utc) - load_start_time).total_seconds()
            self.load_statistics['load_duration_seconds'] = load_duration
            
            self.logger.info(f"✅ TLE數據載入完成 ({load_duration:.1f}秒)")
            self.logger.info(f"📊 載入統計:")
            self.logger.info(f"   總衛星數: {self.load_statistics['total_satellites']}顆")
            self.logger.info(f"   Starlink: {self.load_statistics['starlink_count']}顆")
            self.logger.info(f"   OneWeb: {self.load_statistics['oneweb_count']}顆")
            self.logger.info(f"   其他星座: {self.load_statistics['other_constellation_count']}顆")
            
            return satellite_data
            
        except Exception as e:
            self.logger.error(f"❌ 全量TLE數據載入失敗: {e}")
            self.logger.warning("⚠️ 嘗試使用fallback測試數據...")
            return await self._load_fallback_data()
    
    async def _load_local_constellation_tle(self, constellation: str, local_path: str) -> List[TLEData]:
        """載入本地TLE數據文件"""
        self.logger.info(f"📂 載入{constellation}本地TLE數據: {local_path}")
        
        try:
            # 檢查文件是否存在
            if not Path(local_path).exists():
                raise FileNotFoundError(f"TLE文件不存在: {local_path}")
            
            # 讀取本地TLE文件
            with open(local_path, 'r', encoding='utf-8') as f:
                tle_content = f.read()
            
            self.logger.info(f"📋 本地TLE文件載入成功: {constellation}")
            
            # 解析TLE數據
            tle_list = self._parse_tle_content(tle_content, constellation)
            
            self.logger.info(f"✅ {constellation}載入{len(tle_list)}顆衛星")
            return tle_list
            
        except Exception as e:
            self.logger.error(f"❌ {constellation}本地TLE載入失敗: {e}")
            return []
    
    async def _load_constellation_tle(self, constellation: str, url: str) -> List[TLEData]:
        """載入單個星座的TLE數據"""
        self.logger.info(f"🔄 載入{constellation}星座TLE數據...")
        
        try:
            # 檢查是否有本地緩存
            cache_path = Path(f"/tmp/tle_cache_{constellation}.txt")
            tle_content = ""
            
            if cache_path.exists() and self._is_cache_valid(cache_path):
                # 使用緩存數據
                with open(cache_path, 'r') as f:
                    tle_content = f.read()
                self.logger.info(f"📂 使用緩存TLE數據: {constellation}")
            else:
                # 從網路下載
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status == 200:
                            tle_content = await response.text()
                            
                            # 保存到緩存
                            with open(cache_path, 'w') as f:
                                f.write(tle_content)
                            
                            self.logger.info(f"🌐 下載TLE數據完成: {constellation}")
                        else:
                            raise Exception(f"HTTP {response.status}")
            
            # 解析TLE數據
            tle_list = self._parse_tle_content(tle_content, constellation)
            
            self.logger.info(f"✅ {constellation}載入{len(tle_list)}顆衛星")
            return tle_list
            
        except Exception as e:
            self.logger.error(f"❌ {constellation} TLE載入失敗: {e}")
            return []
    
    def _is_cache_valid(self, cache_path: Path, max_age_hours: int = 6) -> bool:
        """檢查TLE緩存是否有效"""
        try:
            file_age = datetime.now(timezone.utc) - datetime.fromtimestamp(
                cache_path.stat().st_mtime, tz=timezone.utc
            )
            return file_age.total_seconds() < (max_age_hours * 3600)
        except:
            return False
    
    def _parse_tle_content(self, content: str, constellation: str) -> List[TLEData]:
        """解析TLE內容"""
        tle_list = []
        lines = content.strip().split('\n')  # ✅ 修復：移除多餘的反斜杠
        
        # ✅ 檢查樣本限制
        sample_limit = None
        if self.sample_limits:
            limit_key = f"{constellation}_sample"
            if limit_key in self.sample_limits:
                sample_limit = self.sample_limits[limit_key]
                self.logger.info(f"🎯 應用樣本限制: {constellation} = {sample_limit}顆")
        
        try:
            i = 0
            parsed_count = 0
            
            while i < len(lines) - 2:
                # ✅ 檢查是否達到樣本限制
                if sample_limit is not None and parsed_count >= sample_limit:
                    self.logger.info(f"✅ {constellation}達到樣本限制({sample_limit}顆)，停止解析")
                    break
                
                # TLE格式: 衛星名稱 + Line1 + Line2
                name_line = lines[i].strip()
                line1 = lines[i + 1].strip()
                line2 = lines[i + 2].strip()
                
                # 驗證TLE格式
                if (line1.startswith('1 ') and line2.startswith('2 ') and 
                    len(line1) == 69 and len(line2) == 69):
                    
                    try:
                        tle_data = self._parse_single_tle(name_line, line1, line2, constellation)
                        tle_list.append(tle_data)
                        parsed_count += 1
                        self.load_statistics['successful_tle_parsing'] += 1
                    except Exception as e:
                        self.logger.warning(f"⚠️ TLE解析失敗 {name_line}: {e}")
                        self.load_statistics['error_count'] += 1
                
                i += 3
        
        except Exception as e:
            self.logger.error(f"❌ TLE內容解析失敗: {e}")
        
        # ✅ 記錄樣本限制應用結果
        if sample_limit is not None:
            self.logger.info(f"📊 {constellation}樣本限制結果: 解析{len(tle_list)}顆 (限制:{sample_limit}顆)")
        else:
            self.logger.info(f"📊 {constellation}全量解析: {len(tle_list)}顆衛星")
        
        return tle_list
    
    def _parse_single_tle(self, name: str, line1: str, line2: str, constellation: str) -> TLEData:
        """解析單個TLE記錄"""
        
        # 從Line1提取數據
        satellite_number = int(line1[2:7])
        epoch_year = int(line1[18:20])
        epoch_day = float(line1[20:32])
        
        # 從Line2提取軌道參數
        inclination = float(line2[8:16])
        raan = float(line2[17:25])
        eccentricity = float('0.' + line2[26:33])
        arg_perigee = float(line2[34:42])
        mean_anomaly = float(line2[43:51])
        mean_motion = float(line2[52:63])
        
        # 計算epoch時間
        current_year = datetime.now(timezone.utc).year
        full_year = 2000 + epoch_year if epoch_year < 50 else 1900 + epoch_year
        epoch_date = datetime(full_year, 1, 1, tzinfo=timezone.utc) + timedelta(days=epoch_day - 1)
        
        # 計算軌道參數
        semi_major_axis = (398600.4418 / (mean_motion * 2 * np.pi / 86400) ** 2) ** (1/3)
        orbital_period = 2 * np.pi * np.sqrt(semi_major_axis ** 3 / 398600.4418) / 60  # 分鐘
        
        earth_radius = 6371.0  # km
        apogee_alt = semi_major_axis * (1 + eccentricity) - earth_radius
        perigee_alt = semi_major_axis * (1 - eccentricity) - earth_radius
        
        return TLEData(
            satellite_id=f"{constellation}_{satellite_number}",
            satellite_name=name.strip(),
            line1=line1,
            line2=line2,
            epoch=epoch_date,
            constellation=constellation,
            inclination_deg=inclination,
            raan_deg=raan,
            eccentricity=eccentricity,
            arg_perigee_deg=arg_perigee,
            mean_anomaly_deg=mean_anomaly,
            mean_motion_revs_per_day=mean_motion,
            semi_major_axis_km=semi_major_axis,
            orbital_period_minutes=orbital_period,
            apogee_altitude_km=apogee_alt,
            perigee_altitude_km=perigee_alt
        )
    
    async def calculate_orbital_positions(self, 
                                        satellites: List[TLEData], 
                                        time_range_minutes: int = 200) -> Dict[str, List[SatellitePosition]]:
        """計算衛星軌道位置"""
        self.logger.info(f"🧮 開始計算軌道位置 ({len(satellites)}顆衛星, {time_range_minutes}分鐘)")
        
        if len(satellites) == 0:
            self.logger.warning("⚠️ 沒有衛星數據進行計算")
            return {}
            
        calc_start_time = datetime.now(timezone.utc)
        
        positions_database = {}
        
        try:
            # 📅 按照@docs設計：200個時間點，30秒間隔，總計100分鐘
            start_time = datetime.now(timezone.utc)
            time_points = []
            self.logger.info(f"🕐 軌道計算時間窗口: {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')} (覆蓋{time_range_minutes}分鐘)")
            self.logger.info(f"📐 時間解析度: 30秒間隔，{time_range_minutes*2}個時間點 (符合@docs設計)")
            
            for i in range(0, time_range_minutes * 2):  # 30秒間隔
                time_point = start_time + timedelta(seconds=i * 30)
                time_points.append(time_point)
            
            # 批量計算衛星位置
            calculation_tasks = []
            for satellite in satellites:
                task = self._calculate_satellite_positions(satellite, time_points)
                calculation_tasks.append(task)
            
            # 並行計算 (分批處理避免記憶體過載)
            batch_size = 100  # 增加批量大小以提高處理效率
            total_batches = (len(calculation_tasks) + batch_size - 1) // batch_size
            self.logger.info(f"📊 分批處理: {total_batches}批次，每批{batch_size}顆衛星")
            
            for batch_idx in range(0, len(calculation_tasks), batch_size):
                batch = calculation_tasks[batch_idx:batch_idx + batch_size]
                results = await asyncio.gather(*batch, return_exceptions=True)
                
                current_batch_num = (batch_idx // batch_size) + 1
                self.logger.info(f"   處理批次 {current_batch_num}/{total_batches} ({len(batch)}顆衛星)")
                
                for j, result in enumerate(results):
                    if isinstance(result, Exception):
                        satellite_id = satellites[batch_idx + j].satellite_id
                        self.logger.warning(f"⚠️ {satellite_id}位置計算失敗: {result}")
                        continue
                    
                    satellite_id, positions = result
                    positions_database[satellite_id] = positions
            
            calc_duration = (datetime.now(timezone.utc) - calc_start_time).total_seconds()
            self.load_statistics['calculation_duration_seconds'] = calc_duration
            
            self.logger.info(f"✅ 軌道位置計算完成 ({calc_duration:.1f}秒)")
            self.logger.info(f"📊 計算統計:")
            self.logger.info(f"   計算衛星數: {len(positions_database)}")
            self.logger.info(f"   時間點數: {len(time_points)}")
            self.logger.info(f"   總位置數據點: {sum(len(pos) for pos in positions_database.values())}")
            
            # 存儲到內部資料庫
            self.orbital_positions.update(positions_database)
            
            return positions_database
            
        except Exception as e:
            self.logger.error(f"❌ 軌道位置計算失敗: {e}")
            raise
    
    async def _calculate_satellite_positions(self, 
                                           satellite: TLEData, 
                                           time_points: List[datetime]) -> Tuple[str, List[SatellitePosition]]:
        """計算單顆衛星的位置序列"""
        
        positions = []
        
        try:
            if SKYFIELD_AVAILABLE:
                # 使用Skyfield進行精確計算
                positions = await self._calculate_positions_skyfield(satellite, time_points)
            else:
                # 使用簡化SGP4計算
                positions = await self._calculate_positions_simplified(satellite, time_points)
                
        except Exception as e:
            self.logger.warning(f"⚠️ {satellite.satellite_id}位置計算失敗: {e}")
        
        return satellite.satellite_id, positions
    
    async def _calculate_positions_skyfield(self, 
                                      satellite: TLEData, 
                                      time_points: List[datetime]) -> List[SatellitePosition]:
        """使用Skyfield計算精確位置"""
        positions = []
        
        try:
            # 導入Skyfield的UTC時區
            from skyfield.api import utc
            
            # 創建衛星對象
            earth_satellite = EarthSatellite(satellite.line1, satellite.line2, 
                                           satellite.satellite_name, self.ts)
            
            success_count = 0
            error_count = 0
            
            for i, time_point in enumerate(time_points):
                try:
                    # 確保時間點有UTC時區 - 使用Skyfield的utc對象
                    if time_point.tzinfo is None:
                        time_point = time_point.replace(tzinfo=utc)
                    elif time_point.tzinfo != utc:
                        time_point = time_point.astimezone(utc)
                    
                    # 轉換為Skyfield時間 - 直接傳遞帶時區的datetime
                    t = self.ts.from_datetime(time_point)
                    
                    # 計算衛星位置
                    geocentric = earth_satellite.at(t)
                    subpoint = geocentric.subpoint()
                    
                    # 計算相對觀測者的位置 - 修復：正確解包altaz()結果
                    difference = earth_satellite.at(t) - self.observer_location.at(t)
                    elevation, azimuth, distance = difference.altaz()
                    
                    # 計算速度
                    dt = 1.0 / 86400  # 1秒
                    t_plus = self.ts.from_datetime(time_point + timedelta(seconds=1))
                    pos_plus = earth_satellite.at(t_plus)
                    velocity_vector = (pos_plus.position.km - geocentric.position.km) / dt
                    velocity_magnitude = np.linalg.norm(velocity_vector)
                    
                    position = SatellitePosition(
                        timestamp=time_point,
                        latitude_deg=subpoint.latitude.degrees,
                        longitude_deg=subpoint.longitude.degrees,
                        altitude_km=subpoint.elevation.km,
                        elevation_deg=elevation.degrees,  # 修復：使用正確的elevation對象
                        azimuth_deg=azimuth.degrees,      # 修復：使用正確的azimuth對象
                        distance_km=distance.km,          # 修復：使用正確的distance對象
                        velocity_km_s=velocity_magnitude
                    )
                    
                    positions.append(position)
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    if error_count <= 3:  # 只記錄前3個錯誤避免日誌泛濫
                        self.logger.warning(f"⚠️ {satellite.satellite_id} SGP4計算時間點{i} 失敗: {e}")
                    continue
            
            if success_count > 0:
                self.logger.debug(f"✅ {satellite.satellite_id}: SGP4計算成功 {success_count}/{len(time_points)} 點")
            else:
                self.logger.error(f"❌ {satellite.satellite_id}: 所有時間點SGP4計算失敗")
                    
        except Exception as e:
            self.logger.error(f"❌ {satellite.satellite_id} Skyfield初始化失敗: {e}")
            
        return positions
    
    async def _calculate_positions_simplified(self, 
                                        satellite: TLEData, 
                                        time_points: List[datetime]) -> List[SatellitePosition]:
        """簡化SGP4位置計算"""
        positions = []
        
        try:
            success_count = 0
            error_count = 0
            
            for i, time_point in enumerate(time_points):
                try:
                    # 簡化的軌道計算
                    time_since_epoch = (time_point - satellite.epoch).total_seconds()
                    mean_motion_rad_s = satellite.mean_motion_revs_per_day * 2 * np.pi / 86400
                    
                    # 簡化的平均異常角計算
                    current_mean_anomaly = (satellite.mean_anomaly_deg + 
                                          np.degrees(mean_motion_rad_s * time_since_epoch)) % 360
                    
                    # 簡化的位置計算 (假設圓軌道)
                    true_anomaly = current_mean_anomaly  # 簡化
                    
                    # 地心座標
                    r = satellite.semi_major_axis_km
                    x = r * np.cos(np.radians(true_anomaly))
                    y = r * np.sin(np.radians(true_anomaly))
                    z = 0  # 簡化為赤道平面
                    
                    # 簡化的地理座標轉換
                    latitude = np.degrees(np.arcsin(z / r)) if r > 0 else 0
                    longitude = np.degrees(np.arctan2(y, x))
                    altitude = r - 6371.0  # 地球半徑
                    
                    # 簡化的觀測者相對位置
                    lat_diff = latitude - self.observer_lat
                    lon_diff = longitude - self.observer_lon
                    distance = np.sqrt(lat_diff**2 + lon_diff**2) * 111.32  # 粗略距離
                    elevation = np.degrees(np.arctan2(altitude, distance)) if distance > 0 else 90.0
                    azimuth = np.degrees(np.arctan2(lon_diff, lat_diff))
                    
                    position = SatellitePosition(
                        timestamp=time_point,
                        latitude_deg=latitude,
                        longitude_deg=longitude,
                        altitude_km=altitude,
                        elevation_deg=elevation,
                        azimuth_deg=azimuth % 360,
                        distance_km=distance + altitude,
                        velocity_km_s=7.8  # 典型LEO速度
                    )
                    
                    positions.append(position)
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    if error_count <= 3:  # 只記錄前3個錯誤
                        self.logger.warning(f"⚠️ {satellite.satellite_id} 簡化計算時間點{i} 失敗: {e}")
                    continue
            
            if error_count > 0:
                self.logger.warning(f"⚠️ {satellite.satellite_id} 簡化計算: {success_count}成功/{error_count}失敗")
            
            if success_count == 0:
                self.logger.error(f"❌ {satellite.satellite_id}: 簡化計算完全失敗")
                self.logger.error(f"   軌道參數: 周期{satellite.orbital_period_minutes:.1f}min, 高度{satellite.apogee_altitude_km:.0f}km")
                
        except Exception as e:
            self.logger.error(f"❌ {satellite.satellite_id} 簡化計算失敗: {e}")
            
        return positions
    
    async def _load_fallback_data(self) -> Dict[str, List[TLEData]]:
        """載入fallback測試數據"""
        try:
            from .fallback_test_data import create_fallback_tle_data, get_fallback_statistics
            
            self.logger.info("📂 載入fallback測試數據...")
            
            # 獲取fallback數據
            fallback_data = create_fallback_tle_data()
            fallback_stats = get_fallback_statistics()
            
            # 更新統計
            self.load_statistics.update(fallback_stats)
            
            # 添加到內部數據庫
            for constellation, satellites in fallback_data.items():
                for satellite in satellites:
                    self.tle_database[satellite.satellite_id] = satellite
            
            self.logger.info("✅ Fallback數據載入完成")
            self.logger.info(f"📊 測試數據統計:")
            self.logger.info(f"   總衛星數: {fallback_stats['total_satellites']}顆")
            self.logger.info(f"   Starlink: {fallback_stats['starlink_count']}顆")
            self.logger.info(f"   OneWeb: {fallback_stats['oneweb_count']}顆")
            self.logger.warning(f"⚠️ {fallback_stats['fallback_reason']}")
            
            return fallback_data
            
        except Exception as e:
            self.logger.error(f"❌ Fallback數據載入失敗: {e}")
            # 返回空數據但不拋出異常，讓系統繼續運行
            return {
                'starlink': [],
                'oneweb': [],
                'other_constellations': []
            }
    
    async def export_load_statistics(self, output_path: str):
        """匯出載入統計信息"""
        try:
            export_data = {
                'f1_tle_loader_statistics': {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'load_statistics': self.load_statistics,
                    'configuration': {
                        'observer_coordinates': {
                            'latitude': self.observer_lat,
                            'longitude': self.observer_lon,
                            'altitude_m': self.observer_alt_m
                        },
                        'local_tle_sources': self.local_tle_sources,
                        'skyfield_available': SKYFIELD_AVAILABLE
                    },
                    'constellation_breakdown': {
                        'starlink': {
                            'count': self.load_statistics['starlink_count'],
                            'percentage': self.load_statistics['starlink_count'] / max(1, self.load_statistics['total_satellites']) * 100
                        },
                        'oneweb': {
                            'count': self.load_statistics['oneweb_count'],
                            'percentage': self.load_statistics['oneweb_count'] / max(1, self.load_statistics['total_satellites']) * 100
                        },
                        'others': {
                            'count': self.load_statistics['other_constellation_count'],
                            'percentage': self.load_statistics['other_constellation_count'] / max(1, self.load_statistics['total_satellites']) * 100
                        }
                    }
                }
            }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"📊 F1載入統計已匯出至: {output_path}")
            
        except Exception as e:
            self.logger.error(f"❌ 載入統計匯出失敗: {e}")
    

# 使用範例
async def main():
    """F1_TLE_Loader使用範例"""
    
    config = {
        'tle_sources': {
            'starlink': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle',
            'oneweb': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle'
        },
        'calculation_params': {
            'time_range_minutes': 200,
            'time_resolution_seconds': 30
        }
    }
    
    # 初始化TLE載入器
    tle_loader = TLELoaderEngine(config)
    await tle_loader.initialize()
    
    # 載入全量衛星數據
    satellite_data = await tle_loader.load_full_satellite_data()
    
    # 計算軌道位置 (選擇前100顆進行測試)
    test_satellites = []
    if satellite_data.get('starlink'):
        test_satellites.extend(satellite_data['starlink'][:50])
    if satellite_data.get('oneweb'):
        test_satellites.extend(satellite_data['oneweb'][:50])
    
    orbital_positions = await tle_loader.calculate_orbital_positions(
        test_satellites, time_range_minutes=200
    )
    
    # 匯出統計
    await tle_loader.export_load_statistics('/tmp/f1_tle_loader_stats.json')
    
    print(f"✅ F1_TLE_Loader測試完成")
    print(f"   載入衛星數: {tle_loader.load_statistics['total_satellites']}")
    print(f"   計算位置數: {len(orbital_positions)}")

# 向後兼容性別名
TLELoaderEngine = EnhancedTLELoaderEngine

if __name__ == "__main__":
    asyncio.run(main())