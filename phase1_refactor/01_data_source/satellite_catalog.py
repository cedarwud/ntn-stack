#!/usr/bin/env python3
"""
衛星目錄管理系統
負責維護完整的衛星資料庫和星座分類
符合 CLAUDE.md 原則：真實數據，完整算法
"""

import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from pathlib import Path

from tle_loader import TLERecord, TLELoader

logger = logging.getLogger(__name__)


@dataclass
class SatelliteInfo:
    """完整衛星信息"""
    satellite_id: str
    name: str
    constellation: str
    norad_id: int
    tle_record: Optional[TLERecord]
    
    # 軌道特性
    inclination_deg: float
    eccentricity: float
    mean_motion_revs_per_day: float
    altitude_km: float
    
    # 系統信息
    operational_status: str
    last_updated: datetime
    data_quality: str
    
    def to_dict(self) -> Dict:
        """轉換為字典格式，用於序列化"""
        result = asdict(self)
        result['last_updated'] = self.last_updated.isoformat()
        if self.tle_record:
            result['tle_record'] = asdict(self.tle_record)
            result['tle_record']['epoch'] = self.tle_record.epoch.isoformat()
        return result


@dataclass
class ConstellationStats:
    """星座統計信息"""
    name: str
    total_satellites: int
    operational_satellites: int
    avg_altitude_km: float
    avg_inclination_deg: float
    data_freshness_hours: float
    last_update: datetime
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['last_update'] = self.last_update.isoformat()
        return result


class SatelliteCatalog:
    """
    完整衛星目錄管理系統
    符合 CLAUDE.md 原則的真實衛星數據管理
    """
    
    def __init__(self, tle_loader: TLELoader):
        self.tle_loader = tle_loader
        self.satellites: Dict[str, SatelliteInfo] = {}
        self.constellation_map: Dict[str, Set[str]] = {}
        self.stats: Dict[str, ConstellationStats] = {}
        self.last_updated = datetime.now(timezone.utc)
        
        logger.info("衛星目錄管理系統初始化完成")
    
    def load_complete_catalog(self) -> Tuple[bool, str]:
        """載入完整衛星目錄"""
        try:
            logger.info("開始載入完整衛星目錄...")
            
            # 載入 TLE 數據
            load_result = self.tle_loader.load_all_constellations()
            if not load_result.success:
                return False, f"TLE 數據載入失敗: {load_result.error_message}"
            
            # 處理每個 TLE 記錄
            processed_count = 0
            for tle_record in load_result.tle_records:
                satellite_info = self._create_satellite_info(tle_record)
                if satellite_info:
                    self.satellites[satellite_info.satellite_id] = satellite_info
                    self._update_constellation_mapping(satellite_info)
                    processed_count += 1
            
            # 生成統計信息
            self._generate_constellation_stats()
            self.last_updated = datetime.now(timezone.utc)
            
            logger.info(f"完整衛星目錄載入完成: {processed_count} 顆衛星")
            return True, f"成功載入 {processed_count} 顆衛星"
            
        except Exception as e:
            error_msg = f"載入衛星目錄時發生錯誤: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _create_satellite_info(self, tle_record: TLERecord) -> Optional[SatelliteInfo]:
        """從 TLE 記錄創建衛星信息"""
        try:
            # 解析軌道參數
            inclination = float(tle_record.line2[8:16])
            eccentricity = float(f"0.{tle_record.line2[26:33]}")
            mean_motion = float(tle_record.line2[52:63])
            
            # 計算軌道高度 (簡化計算)
            # 使用 Kepler's 第三定律: n = sqrt(μ/a³)
            # 其中 μ = 3.986004418e14 m³/s² (地球引力參數)
            mu = 3.986004418e14  # m³/s²
            n_rad_per_sec = mean_motion * 2 * 3.14159 / 86400  # 轉換為弧度/秒
            semi_major_axis_m = (mu / (n_rad_per_sec ** 2)) ** (1/3)
            altitude_km = (semi_major_axis_m - 6371000) / 1000  # 減去地球半徑
            
            # 確定星座類型
            constellation = self._determine_constellation(tle_record.satellite_name)
            
            # 評估數據品質
            age_days = (datetime.now(timezone.utc) - tle_record.epoch).total_seconds() / 86400
            if age_days < 3:
                data_quality = "excellent"
            elif age_days < 7:
                data_quality = "good"
            elif age_days < 14:
                data_quality = "acceptable"
            else:
                data_quality = "outdated"
            
            return SatelliteInfo(
                satellite_id=tle_record.satellite_id,
                name=tle_record.satellite_name,
                constellation=constellation,
                norad_id=int(tle_record.line1[2:7]),
                tle_record=tle_record,
                inclination_deg=inclination,
                eccentricity=eccentricity,
                mean_motion_revs_per_day=mean_motion,
                altitude_km=altitude_km,
                operational_status="operational" if data_quality in ["excellent", "good"] else "uncertain",
                last_updated=datetime.now(timezone.utc),
                data_quality=data_quality
            )
            
        except Exception as e:
            logger.warning(f"無法處理衛星 {tle_record.satellite_name}: {str(e)}")
            return None
    
    def _determine_constellation(self, satellite_name: str) -> str:
        """根據衛星名稱確定星座類型"""
        name_upper = satellite_name.upper()
        
        if "STARLINK" in name_upper:
            return "starlink"
        elif "ONEWEB" in name_upper:
            return "oneweb"
        elif "IRIDIUM" in name_upper:
            return "iridium"
        elif "GLOBALSTAR" in name_upper:
            return "globalstar"
        else:
            return "other"
    
    def _update_constellation_mapping(self, satellite_info: SatelliteInfo):
        """更新星座映射"""
        constellation = satellite_info.constellation
        if constellation not in self.constellation_map:
            self.constellation_map[constellation] = set()
        
        self.constellation_map[constellation].add(satellite_info.satellite_id)
    
    def _generate_constellation_stats(self):
        """生成星座統計信息"""
        self.stats.clear()
        
        for constellation, satellite_ids in self.constellation_map.items():
            satellites = [self.satellites[sid] for sid in satellite_ids]
            
            # 計算統計數據
            operational_count = sum(1 for sat in satellites if sat.operational_status == "operational")
            avg_altitude = sum(sat.altitude_km for sat in satellites) / len(satellites)
            avg_inclination = sum(sat.inclination_deg for sat in satellites) / len(satellites)
            
            # 計算數據新鮮度
            ages = [(datetime.now(timezone.utc) - sat.last_updated).total_seconds() / 3600 
                   for sat in satellites]
            avg_age_hours = sum(ages) / len(ages)
            
            self.stats[constellation] = ConstellationStats(
                name=constellation,
                total_satellites=len(satellites),
                operational_satellites=operational_count,
                avg_altitude_km=round(avg_altitude, 1),
                avg_inclination_deg=round(avg_inclination, 1),
                data_freshness_hours=round(avg_age_hours, 2),
                last_update=datetime.now(timezone.utc)
            )
        
        logger.info(f"生成了 {len(self.stats)} 個星座的統計信息")
    
    def get_constellation_satellites(self, constellation: str) -> List[SatelliteInfo]:
        """獲取指定星座的所有衛星"""
        if constellation not in self.constellation_map:
            return []
        
        satellite_ids = self.constellation_map[constellation]
        return [self.satellites[sid] for sid in satellite_ids]
    
    def get_satellite_by_id(self, satellite_id: str) -> Optional[SatelliteInfo]:
        """根據 ID 獲取衛星信息"""
        return self.satellites.get(satellite_id)
    
    def get_satellite_by_norad(self, norad_id: int) -> Optional[SatelliteInfo]:
        """根據 NORAD ID 獲取衛星信息"""
        for satellite in self.satellites.values():
            if satellite.norad_id == norad_id:
                return satellite
        return None
    
    def get_constellation_stats(self, constellation: str = None) -> Dict[str, ConstellationStats]:
        """獲取星座統計信息"""
        if constellation:
            return {constellation: self.stats.get(constellation)} if constellation in self.stats else {}
        return self.stats.copy()
    
    def get_catalog_summary(self) -> Dict:
        """獲取目錄摘要信息"""
        return {
            "total_satellites": len(self.satellites),
            "constellations": list(self.constellation_map.keys()),
            "constellation_counts": {
                constellation: len(satellite_ids) 
                for constellation, satellite_ids in self.constellation_map.items()
            },
            "last_updated": self.last_updated.isoformat(),
            "data_quality_distribution": self._get_quality_distribution(),
            "operational_status_distribution": self._get_status_distribution()
        }
    
    def _get_quality_distribution(self) -> Dict[str, int]:
        """獲取數據品質分佈"""
        distribution = {}
        for satellite in self.satellites.values():
            quality = satellite.data_quality
            distribution[quality] = distribution.get(quality, 0) + 1
        return distribution
    
    def _get_status_distribution(self) -> Dict[str, int]:
        """獲取運營狀態分佈"""
        distribution = {}
        for satellite in self.satellites.values():
            status = satellite.operational_status
            distribution[status] = distribution.get(status, 0) + 1
        return distribution
    
    def export_catalog(self, output_path: str) -> bool:
        """導出完整目錄到 JSON 文件"""
        try:
            catalog_data = {
                "metadata": {
                    "export_timestamp": datetime.now(timezone.utc).isoformat(),
                    "total_satellites": len(self.satellites),
                    "source": "Phase 1 Satellite Catalog System"
                },
                "summary": self.get_catalog_summary(),
                "constellation_stats": {
                    constellation: stats.to_dict() 
                    for constellation, stats in self.stats.items()
                },
                "satellites": {
                    satellite_id: satellite_info.to_dict()
                    for satellite_id, satellite_info in self.satellites.items()
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(catalog_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"衛星目錄已導出到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"導出衛星目錄失敗: {str(e)}")
            return False


def create_satellite_catalog(tle_loader: TLELoader) -> SatelliteCatalog:
    """創建衛星目錄管理實例"""
    return SatelliteCatalog(tle_loader)


# 測試代碼
if __name__ == "__main__":
    import sys
    import os
    
    # 設置路徑
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
    
    logging.basicConfig(level=logging.INFO)
    
    # 創建測試實例
    from tle_loader import create_tle_loader
    
    tle_loader = create_tle_loader("/netstack/tle_data")
    catalog = create_satellite_catalog(tle_loader)
    
    # 載入目錄
    success, message = catalog.load_complete_catalog()
    print(f"載入結果: {success}, 訊息: {message}")
    
    if success:
        # 顯示摘要
        summary = catalog.get_catalog_summary()
        print(f"目錄摘要: {json.dumps(summary, indent=2, ensure_ascii=False)}")
        
        # 顯示星座統計
        stats = catalog.get_constellation_stats()
        for constellation, stat in stats.items():
            print(f"{constellation}: {stat.total_satellites} 顆衛星, 平均高度 {stat.avg_altitude_km}km")