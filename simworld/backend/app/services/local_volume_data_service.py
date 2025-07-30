"""
本地 Docker Volume 數據服務
按照衛星數據架構文檔，SimWorld 應該使用 Docker Volume 本地數據而非直接 API 調用
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LocalVolumeDataService:
    """本地 Docker Volume 數據服務 - 遵循衛星數據架構"""
    
    def __init__(self):
        """初始化本地數據服務"""
        # Docker Volume 掛載路徑
        self.netstack_data_path = Path("/app/data")  # 主要預計算數據
        self.netstack_tle_data_path = Path("/app/netstack/tle_data")  # TLE 原始數據
        
        # 檢查路徑是否存在
        self._check_volume_paths()
    
    def _check_volume_paths(self):
        """檢查 Docker Volume 路徑是否正確掛載"""
        paths = [
            (self.netstack_data_path, "預計算軌道數據"),
            (self.netstack_tle_data_path, "TLE 原始數據")
        ]
        
        for path, description in paths:
            if path.exists():
                logger.info(f"✅ {description} 路徑可用: {path}")
            else:
                logger.warning(f"⚠️  {description} 路徑不存在: {path}")
    
    async def get_precomputed_orbit_data(
        self,
        location: str = "ntpu",
        constellation: str = "starlink"
    ) -> Optional[Dict[str, Any]]:
        """
        從本地 Docker Volume 獲取預計算軌道數據
        優先級: phase0 數據 > layered 數據 > 無數據
        """
        try:
            # 主要預計算數據文件
            main_data_file = self.netstack_data_path / "phase0_precomputed_orbits.json"
            
            if main_data_file.exists():
                logger.info(f"📊 從本地 Volume 載入預計算軌道數據: {main_data_file}")
                
                with open(main_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 檢查數據完整性
                if self._validate_precomputed_data(data):
                    logger.info(f"✅ 成功載入 {len(data.get('orbit_points', []))} 個軌道點")
                    return data
                else:
                    logger.warning("⚠️  預計算數據格式驗證失敗")
            else:
                logger.warning(f"📊 主要預計算數據文件不存在: {main_data_file}")
            
            # 嘗試分層數據作為備用
            layered_data_dir = self.netstack_data_path / "layered_phase0"
            if layered_data_dir.exists():
                return await self._load_layered_data(layered_data_dir, location, constellation)
            
            logger.error("❌ 無可用的本地預計算數據")
            return None
            
        except Exception as e:
            logger.error(f"❌ 載入本地預計算數據失敗: {e}")
            return None
    
    async def _load_layered_data(
        self,
        layered_dir: Path,
        location: str,
        constellation: str
    ) -> Optional[Dict[str, Any]]:
        """載入分層門檻數據"""
        try:
            # 尋找對應的分層數據文件
            pattern = f"{location}_{constellation}_*.json"
            data_files = list(layered_dir.glob(pattern))
            
            if data_files:
                # 選擇最新的文件
                latest_file = max(data_files, key=lambda p: p.stat().st_mtime)
                logger.info(f"📊 從分層數據載入: {latest_file}")
                
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if self._validate_precomputed_data(data):
                    return data
            
            logger.warning(f"⚠️  未找到 {location}_{constellation} 的分層數據")
            return None
            
        except Exception as e:
            logger.error(f"❌ 載入分層數據失敗: {e}")
            return None
    
    def _validate_precomputed_data(self, data: Dict[str, Any]) -> bool:
        """驗證預計算數據格式"""
        try:
            required_fields = ["orbit_points", "metadata"]
            for field in required_fields:
                if field not in data:
                    logger.warning(f"缺少必要字段: {field}")
                    return False
            
            orbit_points = data.get("orbit_points", [])
            if not orbit_points:
                logger.warning("orbit_points 為空")
                return False
            
            # 檢查第一個軌道點的格式
            first_point = orbit_points[0]
            point_fields = ["timestamp", "latitude", "longitude", "altitude_km"]
            for field in point_fields:
                if field not in first_point:
                    logger.warning(f"軌道點缺少字段: {field}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"數據驗證失敗: {e}")
            return False
    
    async def get_local_tle_data(self, constellation: str = "starlink") -> List[Dict[str, Any]]:
        """
        從本地 Docker Volume 獲取 TLE 數據
        替代直接 API 調用
        """
        try:
            # 尋找對應星座的最新 TLE 數據
            constellation_dir = self.netstack_tle_data_path / constellation
            
            if not constellation_dir.exists():
                logger.warning(f"星座目錄不存在: {constellation_dir}")
                return []
            
            # 檢查 JSON 格式數據
            json_dir = constellation_dir / "json"
            if json_dir.exists():
                json_files = sorted(json_dir.glob(f"{constellation}_*.json"), reverse=True)
                if json_files:
                    latest_file = json_files[0]
                    logger.info(f"📡 從本地 Volume 載入 TLE 數據: {latest_file}")
                    
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        tle_data = json.load(f)
                    
                    logger.info(f"✅ 成功載入 {len(tle_data)} 顆 {constellation} 衛星數據")
                    return tle_data
            
            # 檢查 TLE 格式數據
            tle_dir = constellation_dir / "tle"
            if tle_dir.exists():
                tle_files = sorted(tle_dir.glob(f"{constellation}_*.tle"), reverse=True)
                if tle_files:
                    latest_file = tle_files[0]
                    logger.info(f"📡 從本地 Volume 解析 TLE 文件: {latest_file}")
                    
                    tle_data = await self._parse_tle_file(latest_file, constellation)
                    logger.info(f"✅ 解析得到 {len(tle_data)} 顆 {constellation} 衛星數據")
                    return tle_data
            
            logger.warning(f"❌ 未找到 {constellation} 的本地 TLE 數據")
            return []
            
        except Exception as e:
            logger.error(f"❌ 載入本地 TLE 數據失敗: {e}")
            return []
    
    async def _parse_tle_file(self, tle_file: Path, constellation: str) -> List[Dict[str, Any]]:
        """解析 TLE 文件格式數據"""
        try:
            tle_data = []
            
            with open(tle_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 按照 TLE 格式解析 (3行一組)
            for i in range(0, len(lines), 3):
                if i + 2 < len(lines):
                    name = lines[i].strip()
                    line1 = lines[i + 1].strip()
                    line2 = lines[i + 2].strip()
                    
                    if line1.startswith("1 ") and line2.startswith("2 "):
                        try:
                            norad_id = int(line1[2:7])
                            satellite_data = {
                                "name": name,
                                "norad_id": norad_id,
                                "line1": line1,
                                "line2": line2,
                                "constellation": constellation,
                                "source": "local_volume_tle_file",
                                "file_path": str(tle_file)
                            }
                            tle_data.append(satellite_data)
                        except (ValueError, IndexError) as e:
                            logger.warning(f"解析 TLE 行失敗: {e}")
                            continue
            
            return tle_data
            
        except Exception as e:
            logger.error(f"解析 TLE 文件失敗: {e}")
            return []
    
    async def check_data_freshness(self) -> Dict[str, Any]:
        """檢查本地數據的新鮮度"""
        try:
            freshness_info = {
                "precomputed_data": None,
                "tle_data": {},
                "data_ready": False
            }
            
            # 檢查數據完成標記
            data_ready_file = self.netstack_data_path / ".data_ready"
            if data_ready_file.exists():
                freshness_info["data_ready"] = True
                
                # 讀取數據生成時間
                try:
                    with open(data_ready_file, 'r') as f:
                        ready_info = f.read().strip()
                    freshness_info["data_ready_info"] = ready_info
                except:
                    pass
            
            # 檢查主要預計算數據
            main_data_file = self.netstack_data_path / "phase0_precomputed_orbits.json"
            if main_data_file.exists():
                stat = main_data_file.stat()
                freshness_info["precomputed_data"] = {
                    "file": str(main_data_file),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "age_hours": (datetime.now().timestamp() - stat.st_mtime) / 3600
                }
            
            # 檢查 TLE 數據
            for constellation in ["starlink", "oneweb"]:
                constellation_dir = self.netstack_tle_data_path / constellation
                if constellation_dir.exists():
                    freshness_info["tle_data"][constellation] = {
                        "directory": str(constellation_dir),
                        "json_files": len(list((constellation_dir / "json").glob("*.json"))) if (constellation_dir / "json").exists() else 0,
                        "tle_files": len(list((constellation_dir / "tle").glob("*.tle"))) if (constellation_dir / "tle").exists() else 0
                    }
            
            return freshness_info
            
        except Exception as e:
            logger.error(f"檢查數據新鮮度失敗: {e}")
            return {"error": str(e)}
    
    def is_data_available(self) -> bool:
        """檢查是否有可用的本地數據"""
        try:
            # 檢查主要數據文件
            main_data_file = self.netstack_data_path / "phase0_precomputed_orbits.json"
            if main_data_file.exists() and main_data_file.stat().st_size > 0:
                return True
            
            # 檢查分層數據
            layered_data_dir = self.netstack_data_path / "layered_phase0"
            if layered_data_dir.exists():
                json_files = list(layered_data_dir.glob("*.json"))
                if json_files:
                    return True
            
            # 檢查 TLE 數據
            for constellation in ["starlink", "oneweb"]:
                constellation_dir = self.netstack_tle_data_path / constellation
                if constellation_dir.exists():
                    if (constellation_dir / "json").exists() or (constellation_dir / "tle").exists():
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"檢查數據可用性失敗: {e}")
            return False


# 全局實例
_local_volume_service = None


def get_local_volume_service() -> LocalVolumeDataService:
    """獲取本地 Volume 數據服務實例"""
    global _local_volume_service
    if _local_volume_service is None:
        _local_volume_service = LocalVolumeDataService()
    return _local_volume_service