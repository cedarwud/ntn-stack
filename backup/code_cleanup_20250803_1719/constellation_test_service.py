"""
衛星星座配置測試服務
實現不同衛星星座配置下的換手性能測試與分析
"""

import asyncio
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
from skyfield.api import load, wgs84
from skyfield.positionlib import Geocentric
import math

logger = logging.getLogger(__name__)

class ConstellationType(Enum):
    """衛星星座類型"""
    LEO_DENSE = "leo_dense"           # 低軌高密度
    LEO_SPARSE = "leo_sparse"         # 低軌稀疏
    MEO_CIRCULAR = "meo_circular"     # 中軌圓形
    HYBRID_LEO_MEO = "hybrid_leo_meo" # 混合軌道
    WALKER_DELTA = "walker_delta"     # Walker Delta星座
    POLAR_COVERAGE = "polar_coverage" # 極地覆蓋

@dataclass
class SatelliteParameters:
    """衛星參數"""
    altitude: float  # 軌道高度 (km)
    inclination: float  # 軌道傾斜角 (度)
    period: float  # 軌道週期 (分鐘)
    eccentricity: float = 0.0  # 軌道偏心率
    raan: float = 0.0  # 升交點赤經 (度)
    
@dataclass
class ConstellationConfig:
    """星座配置"""
    constellation_id: str
    constellation_type: ConstellationType
    satellite_count: int
    planes: int  # 軌道平面數
    satellites_per_plane: int
    satellite_params: SatelliteParameters
    coverage_requirements: Dict[str, float]
    created_at: datetime

@dataclass
class HandoverTestResult:
    """換手測試結果"""
    test_id: str
    constellation_id: str
    test_duration: float  # 測試時長 (秒)
    total_handovers: int
    successful_handovers: int
    failed_handovers: int
    average_latency: float  # 平均延遲 (ms)
    max_latency: float  # 最大延遲 (ms)
    min_latency: float  # 最小延遲 (ms)
    packet_loss_rate: float  # 封包遺失率 (%)
    coverage_percentage: float  # 覆蓋率 (%)
    availability_time: float  # 可用時間 (%)
    doppler_shift_variance: float  # 都卜勒頻移變異
    elevation_angles: List[float]  # 仰角記錄
    test_timestamp: datetime

@dataclass
class ConstellationPerformanceMetrics:
    """星座性能指標"""
    constellation_id: str
    average_elevation: float  # 平均仰角
    coverage_gaps: List[Tuple[float, float]]  # 覆蓋空隙 (時間區間)
    handover_frequency: float  # 換手頻率 (/小時)
    constellation_efficiency: float  # 星座效率 (0-1)
    geometry_dilution: float  # 幾何精度因子
    interference_potential: float  # 干擾潛力
    power_efficiency: float  # 功率效率
    spectrum_efficiency: float  # 頻譜效率

class ConstellationTestService:
    """衛星星座配置測試服務"""
    
    def __init__(self):
        self.test_results: Dict[str, List[HandoverTestResult]] = {}
        self.constellation_configs: Dict[str, ConstellationConfig] = {}
        self.performance_metrics: Dict[str, ConstellationPerformanceMetrics] = {}
        self.earth_radius = 6371.0  # 地球半徑 (km)
        
        # 預定義星座配置
        self._initialize_predefined_constellations()
    
    def _initialize_predefined_constellations(self):
        """初始化預定義星座配置"""
        
        # Starlink風格 LEO高密度星座
        starlink_config = ConstellationConfig(
            constellation_id="starlink_like",
            constellation_type=ConstellationType.LEO_DENSE,
            satellite_count=1584,
            planes=72,
            satellites_per_plane=22,
            satellite_params=SatelliteParameters(
                altitude=550.0,
                inclination=53.0,
                period=96.0
            ),
            coverage_requirements={
                "min_elevation": 25.0,
                "target_availability": 99.5,
                "max_handover_interval": 300.0
            },
            created_at=datetime.now()
        )
        
        # OneWeb風格 LEO中密度星座
        oneweb_config = ConstellationConfig(
            constellation_id="oneweb_like",
            constellation_type=ConstellationType.LEO_SPARSE,
            satellite_count=648,
            planes=18,
            satellites_per_plane=36,
            satellite_params=SatelliteParameters(
                altitude=1200.0,
                inclination=87.9,
                period=109.0
            ),
            coverage_requirements={
                "min_elevation": 30.0,
                "target_availability": 98.0,
                "max_handover_interval": 600.0
            },
            created_at=datetime.now()
        )
        
        # Walker Delta星座
        walker_config = ConstellationConfig(
            constellation_id="walker_delta",
            constellation_type=ConstellationType.WALKER_DELTA,
            satellite_count=288,
            planes=8,
            satellites_per_plane=36,
            satellite_params=SatelliteParameters(
                altitude=780.0,
                inclination=55.0,
                period=101.0
            ),
            coverage_requirements={
                "min_elevation": 20.0,
                "target_availability": 97.0,
                "max_handover_interval": 450.0
            },
            created_at=datetime.now()
        )
        
        # MEO混合星座
        meo_hybrid_config = ConstellationConfig(
            constellation_id="meo_hybrid",
            constellation_type=ConstellationType.HYBRID_LEO_MEO,
            satellite_count=144,
            planes=6,
            satellites_per_plane=24,
            satellite_params=SatelliteParameters(
                altitude=8000.0,
                inclination=55.0,
                period=458.0
            ),
            coverage_requirements={
                "min_elevation": 15.0,
                "target_availability": 95.0,
                "max_handover_interval": 1800.0
            },
            created_at=datetime.now()
        )
        
        self.constellation_configs.update({
            starlink_config.constellation_id: starlink_config,
            oneweb_config.constellation_id: oneweb_config,
            walker_config.constellation_id: walker_config,
            meo_hybrid_config.constellation_id: meo_hybrid_config
        })
    
    async def create_constellation_config(
        self,
        constellation_type: ConstellationType,
        satellite_count: int,
        orbital_params: Dict[str, float],
        coverage_requirements: Dict[str, float]
    ) -> str:
        """創建星座配置"""
        
        constellation_id = f"custom_{constellation_type.value}_{int(datetime.now().timestamp())}"
        
        # 計算軌道平面和每平面衛星數
        planes = self._calculate_optimal_planes(satellite_count, orbital_params["altitude"])
        satellites_per_plane = satellite_count // planes
        
        satellite_params = SatelliteParameters(
            altitude=orbital_params["altitude"],
            inclination=orbital_params["inclination"],
            period=self._calculate_orbital_period(orbital_params["altitude"]),
            eccentricity=orbital_params.get("eccentricity", 0.0)
        )
        
        config = ConstellationConfig(
            constellation_id=constellation_id,
            constellation_type=constellation_type,
            satellite_count=satellite_count,
            planes=planes,
            satellites_per_plane=satellites_per_plane,
            satellite_params=satellite_params,
            coverage_requirements=coverage_requirements,
            created_at=datetime.now()
        )
        
        self.constellation_configs[constellation_id] = config
        
        logger.info(f"創建星座配置: {constellation_id}, 衛星數: {satellite_count}, 軌道平面: {planes}")
        
        return constellation_id
    
    def _calculate_optimal_planes(self, satellite_count: int, altitude: float) -> int:
        """計算最優軌道平面數"""
        # 根據高度和衛星總數計算最優平面數
        if altitude < 600:  # LEO
            return min(max(int(np.sqrt(satellite_count / 4)), 4), 72)
        elif altitude < 2000:  # MEO lower
            return min(max(int(np.sqrt(satellite_count / 6)), 3), 24)
        else:  # MEO higher
            return min(max(int(np.sqrt(satellite_count / 8)), 3), 12)
    
    def _calculate_orbital_period(self, altitude: float) -> float:
        """計算軌道週期 (分鐘)"""
        # 使用開普勒第三定律
        GM = 398600.4418  # 地球重力參數 km³/s²
        r = self.earth_radius + altitude  # 軌道半徑
        period_seconds = 2 * np.pi * np.sqrt(r**3 / GM)
        return period_seconds / 60  # 轉換為分鐘
    
    async def run_handover_performance_test(
        self,
        constellation_id: str,
        test_duration_hours: float = 24.0,
        ue_positions: List[Tuple[float, float]] = None,
        mobility_pattern: str = "stationary"
    ) -> str:
        """運行換手性能測試"""
        
        if constellation_id not in self.constellation_configs:
            raise ValueError(f"星座配置不存在: {constellation_id}")
        
        config = self.constellation_configs[constellation_id]
        test_id = f"test_{constellation_id}_{int(datetime.now().timestamp())}"
        
        logger.info(f"開始換手性能測試: {test_id}, 星座: {constellation_id}, 時長: {test_duration_hours}小時")
        
        # 默認測試位置 (台灣地區)
        if ue_positions is None:
            ue_positions = [
                (25.0330, 121.5654),  # 台北
                (22.6273, 120.3014),  # 高雄
                (24.1477, 120.6736),  # 台中
                (23.8103, 120.9674)   # 嘉義
            ]
        
        # 生成衛星軌道
        satellite_positions = await self._generate_satellite_orbits(config, test_duration_hours)
        
        # 模擬換手過程
        handover_events = await self._simulate_handover_events(
            config, satellite_positions, ue_positions, test_duration_hours, mobility_pattern
        )
        
        # 分析測試結果
        test_result = await self._analyze_handover_performance(
            test_id, constellation_id, handover_events, test_duration_hours
        )
        
        # 存儲測試結果
        if constellation_id not in self.test_results:
            self.test_results[constellation_id] = []
        self.test_results[constellation_id].append(test_result)
        
        # 計算性能指標
        await self._calculate_constellation_metrics(constellation_id, satellite_positions)
        
        logger.info(f"完成換手性能測試: {test_id}, 總換手: {test_result.total_handovers}, 成功率: {test_result.successful_handovers/test_result.total_handovers*100:.1f}%")
        
        return test_id
    
    async def _generate_satellite_orbits(
        self, 
        config: ConstellationConfig, 
        duration_hours: float
    ) -> Dict[str, List[Tuple[float, float, float]]]:
        """生成衛星軌道數據"""
        
        satellite_positions = {}
        time_steps = int(duration_hours * 60)  # 每分鐘一個數據點
        
        for plane in range(config.planes):
            for sat_in_plane in range(config.satellites_per_plane):
                sat_id = f"sat_{plane}_{sat_in_plane}"
                positions = []
                
                # 計算初始軌道參數
                raan = (360.0 / config.planes) * plane  # 升交點赤經
                mean_anomaly_offset = (360.0 / config.satellites_per_plane) * sat_in_plane
                
                for minute in range(time_steps):
                    # 計算衛星位置 (簡化軌道計算)
                    time_fraction = minute / (config.satellite_params.period)
                    mean_anomaly = (mean_anomaly_offset + (time_fraction * 360)) % 360
                    
                    # 轉換為地理坐標
                    lat, lon, alt = self._orbital_to_geographic(
                        config.satellite_params.altitude,
                        config.satellite_params.inclination,
                        raan,
                        mean_anomaly
                    )
                    
                    positions.append((lat, lon, alt))
                
                satellite_positions[sat_id] = positions
        
        return satellite_positions
    
    def _orbital_to_geographic(
        self, 
        altitude: float, 
        inclination: float, 
        raan: float, 
        mean_anomaly: float
    ) -> Tuple[float, float, float]:
        """軌道參數轉地理坐標（簡化計算）"""
        
        # 簡化的軌道計算
        inc_rad = np.radians(inclination)
        raan_rad = np.radians(raan)
        ma_rad = np.radians(mean_anomaly)
        
        # 軌道平面內的位置
        x_orbital = np.cos(ma_rad)
        y_orbital = np.sin(ma_rad)
        z_orbital = 0
        
        # 轉換到地心坐標系
        x_ecef = (x_orbital * np.cos(raan_rad) - y_orbital * np.cos(inc_rad) * np.sin(raan_rad))
        y_ecef = (x_orbital * np.sin(raan_rad) + y_orbital * np.cos(inc_rad) * np.cos(raan_rad))
        z_ecef = y_orbital * np.sin(inc_rad)
        
        # 轉換為經緯度
        lon = np.degrees(np.arctan2(y_ecef, x_ecef))
        lat = np.degrees(np.arcsin(z_ecef))
        
        return lat, lon, altitude
    
    async def _simulate_handover_events(
        self,
        config: ConstellationConfig,
        satellite_positions: Dict[str, List[Tuple[float, float, float]]],
        ue_positions: List[Tuple[float, float]],
        duration_hours: float,
        mobility_pattern: str
    ) -> List[Dict[str, Any]]:
        """模擬換手事件"""
        
        handover_events = []
        time_steps = int(duration_hours * 60)
        min_elevation = config.coverage_requirements.get("min_elevation", 20.0)
        
        for ue_idx, (ue_lat, ue_lon) in enumerate(ue_positions):
            current_satellite = None
            connection_start_time = 0
            
            for minute in range(time_steps):
                # 計算UE當前位置（考慮移動模式）
                current_ue_lat, current_ue_lon = self._calculate_ue_position(
                    ue_lat, ue_lon, minute, mobility_pattern
                )
                
                # 找到最佳可見衛星
                best_satellite = self._find_best_visible_satellite(
                    current_ue_lat, current_ue_lon, satellite_positions, minute, min_elevation
                )
                
                # 檢查是否需要換手
                if best_satellite != current_satellite:
                    if current_satellite is not None:
                        # 記錄換手事件
                        connection_duration = minute - connection_start_time
                        handover_latency = self._calculate_handover_latency(config, connection_duration)
                        handover_success = self._determine_handover_success(handover_latency, config)
                        
                        handover_events.append({
                            "ue_id": f"ue_{ue_idx}",
                            "timestamp": minute,
                            "from_satellite": current_satellite,
                            "to_satellite": best_satellite,
                            "ue_position": (current_ue_lat, current_ue_lon),
                            "handover_latency": handover_latency,
                            "success": handover_success,
                            "connection_duration": connection_duration,
                            "trigger_reason": "signal_quality"
                        })
                    
                    current_satellite = best_satellite
                    connection_start_time = minute
        
        return handover_events
    
    def _calculate_ue_position(
        self, 
        initial_lat: float, 
        initial_lon: float, 
        time_minute: int, 
        mobility_pattern: str
    ) -> Tuple[float, float]:
        """計算UE位置（考慮移動模式）"""
        
        if mobility_pattern == "stationary":
            return initial_lat, initial_lon
        elif mobility_pattern == "linear":
            # 線性移動，每小時移動0.1度
            speed = 0.1 / 60  # 度/分鐘
            return initial_lat + time_minute * speed * 0.5, initial_lon + time_minute * speed
        elif mobility_pattern == "circular":
            # 圓形移動
            radius = 0.05  # 度
            angular_speed = 2 * np.pi / (60 * 4)  # 4小時一圈
            angle = time_minute * angular_speed
            return (
                initial_lat + radius * np.cos(angle),
                initial_lon + radius * np.sin(angle)
            )
        else:
            return initial_lat, initial_lon
    
    def _find_best_visible_satellite(
        self,
        ue_lat: float,
        ue_lon: float,
        satellite_positions: Dict[str, List[Tuple[float, float, float]]],
        time_index: int,
        min_elevation: float
    ) -> Optional[str]:
        """找到最佳可見衛星"""
        
        best_satellite = None
        best_elevation = min_elevation
        
        for sat_id, positions in satellite_positions.items():
            if time_index < len(positions):
                sat_lat, sat_lon, sat_alt = positions[time_index]
                
                # 計算仰角
                elevation = self._calculate_elevation_angle(
                    ue_lat, ue_lon, sat_lat, sat_lon, sat_alt
                )
                
                if elevation > best_elevation:
                    best_elevation = elevation
                    best_satellite = sat_id
        
        return best_satellite
    
    def _calculate_elevation_angle(
        self,
        ue_lat: float,
        ue_lon: float,
        sat_lat: float,
        sat_lon: float,
        sat_alt: float
    ) -> float:
        """計算衛星仰角"""
        
        # 將經緯度轉換為弧度
        ue_lat_rad = np.radians(ue_lat)
        ue_lon_rad = np.radians(ue_lon)
        sat_lat_rad = np.radians(sat_lat)
        sat_lon_rad = np.radians(sat_lon)
        
        # 計算UE到衛星的向量
        delta_lon = sat_lon_rad - ue_lon_rad
        
        # 使用球面三角法計算距離和仰角
        central_angle = np.arccos(
            np.sin(ue_lat_rad) * np.sin(sat_lat_rad) +
            np.cos(ue_lat_rad) * np.cos(sat_lat_rad) * np.cos(delta_lon)
        )
        
        # 計算地面距離
        ground_distance = self.earth_radius * central_angle
        
        # 計算仰角
        slant_range = np.sqrt(ground_distance**2 + sat_alt**2)
        elevation_rad = np.arctan(sat_alt / ground_distance)
        
        return np.degrees(elevation_rad)
    
    def _calculate_handover_latency(
        self, 
        config: ConstellationConfig, 
        connection_duration: float
    ) -> float:
        """計算換手延遲"""
        
        # 基礎延遲 + 隨機變化
        base_latency = 50.0  # ms
        
        # 根據星座類型調整
        if config.constellation_type == ConstellationType.LEO_DENSE:
            base_latency = 30.0
        elif config.constellation_type == ConstellationType.MEO_CIRCULAR:
            base_latency = 80.0
        
        # 連接時間越長，換手延遲可能越低（預測更準確）
        duration_factor = max(0.5, 1.0 - (connection_duration / 1000.0))
        
        # 添加隨機變化
        random_factor = np.random.normal(1.0, 0.2)
        
        return base_latency * duration_factor * random_factor
    
    def _determine_handover_success(
        self, 
        handover_latency: float, 
        config: ConstellationConfig
    ) -> bool:
        """判斷換手是否成功"""
        
        max_acceptable_latency = config.coverage_requirements.get("max_handover_interval", 500.0)
        
        # 延遲越高，失敗機率越大
        failure_probability = min(0.3, handover_latency / (max_acceptable_latency * 2))
        
        return np.random.random() > failure_probability
    
    async def _analyze_handover_performance(
        self,
        test_id: str,
        constellation_id: str,
        handover_events: List[Dict[str, Any]],
        test_duration_hours: float
    ) -> HandoverTestResult:
        """分析換手性能"""
        
        total_handovers = len(handover_events)
        successful_handovers = sum(1 for event in handover_events if event["success"])
        failed_handovers = total_handovers - successful_handovers
        
        if total_handovers > 0:
            latencies = [event["handover_latency"] for event in handover_events]
            average_latency = np.mean(latencies)
            max_latency = np.max(latencies)
            min_latency = np.min(latencies)
            
            # 計算封包遺失率
            packet_loss_rate = (failed_handovers / total_handovers) * 100
        else:
            average_latency = max_latency = min_latency = 0.0
            packet_loss_rate = 0.0
        
        # 估算覆蓋率和可用性
        coverage_percentage = min(100.0, (successful_handovers / max(1, total_handovers)) * 100)
        availability_time = coverage_percentage  # 簡化計算
        
        # 計算都卜勒頻移變異（模擬）
        doppler_shift_variance = np.random.normal(2.5, 0.5)
        
        # 記錄仰角數據（模擬）
        elevation_angles = [np.random.normal(45, 15) for _ in range(min(100, total_handovers))]
        
        return HandoverTestResult(
            test_id=test_id,
            constellation_id=constellation_id,
            test_duration=test_duration_hours * 3600,
            total_handovers=total_handovers,
            successful_handovers=successful_handovers,
            failed_handovers=failed_handovers,
            average_latency=average_latency,
            max_latency=max_latency,
            min_latency=min_latency,
            packet_loss_rate=packet_loss_rate,
            coverage_percentage=coverage_percentage,
            availability_time=availability_time,
            doppler_shift_variance=doppler_shift_variance,
            elevation_angles=elevation_angles,
            test_timestamp=datetime.now()
        )
    
    async def _calculate_constellation_metrics(
        self,
        constellation_id: str,
        satellite_positions: Dict[str, List[Tuple[float, float, float]]]
    ):
        """計算星座性能指標"""
        
        config = self.constellation_configs[constellation_id]
        
        # 計算平均仰角
        elevations = []
        for positions in satellite_positions.values():
            for lat, lon, alt in positions[:100]:  # 取樣前100個位置
                elevation = self._calculate_elevation_angle(25.0, 121.5, lat, lon, alt)
                if elevation > 0:
                    elevations.append(elevation)
        
        average_elevation = np.mean(elevations) if elevations else 0.0
        
        # 計算覆蓋空隙（簡化）
        coverage_gaps = []
        if len(elevations) > 50:
            low_elevation_indices = [i for i, e in enumerate(elevations) if e < 10]
            if low_elevation_indices:
                coverage_gaps.append((low_elevation_indices[0] * 0.1, low_elevation_indices[-1] * 0.1))
        
        # 計算換手頻率
        handover_frequency = len(elevations) / 24.0  # 每小時換手次數
        
        # 計算星座效率
        theoretical_max_sats = config.satellite_count
        effective_sats = len([e for e in elevations if e > 20])
        constellation_efficiency = effective_sats / theoretical_max_sats if theoretical_max_sats > 0 else 0
        
        # 其他指標（模擬計算）
        geometry_dilution = np.random.normal(2.5, 0.5)
        interference_potential = np.random.normal(0.3, 0.1)
        power_efficiency = np.random.normal(0.8, 0.1)
        spectrum_efficiency = np.random.normal(0.7, 0.1)
        
        metrics = ConstellationPerformanceMetrics(
            constellation_id=constellation_id,
            average_elevation=average_elevation,
            coverage_gaps=coverage_gaps,
            handover_frequency=handover_frequency,
            constellation_efficiency=constellation_efficiency,
            geometry_dilution=geometry_dilution,
            interference_potential=interference_potential,
            power_efficiency=power_efficiency,
            spectrum_efficiency=spectrum_efficiency
        )
        
        self.performance_metrics[constellation_id] = metrics
    
    async def compare_constellation_performance(
        self,
        constellation_ids: List[str]
    ) -> Dict[str, Any]:
        """比較不同星座的性能"""
        
        comparison_result = {
            "comparison_timestamp": datetime.now().isoformat(),
            "constellations": {},
            "performance_ranking": [],
            "recommendations": []
        }
        
        for constellation_id in constellation_ids:
            if constellation_id not in self.test_results or not self.test_results[constellation_id]:
                continue
            
            # 獲取最新測試結果
            latest_result = self.test_results[constellation_id][-1]
            config = self.constellation_configs[constellation_id]
            metrics = self.performance_metrics.get(constellation_id)
            
            constellation_data = {
                "config": asdict(config),
                "latest_test_result": asdict(latest_result),
                "performance_metrics": asdict(metrics) if metrics else None,
                "performance_score": self._calculate_overall_performance_score(latest_result, metrics)
            }
            
            comparison_result["constellations"][constellation_id] = constellation_data
        
        # 性能排名
        ranked_constellations = sorted(
            comparison_result["constellations"].items(),
            key=lambda x: x[1]["performance_score"],
            reverse=True
        )
        
        comparison_result["performance_ranking"] = [
            {
                "rank": i + 1,
                "constellation_id": const_id,
                "performance_score": data["performance_score"],
                "constellation_type": data["config"]["constellation_type"]
            }
            for i, (const_id, data) in enumerate(ranked_constellations)
        ]
        
        # 生成建議
        comparison_result["recommendations"] = self._generate_optimization_recommendations(
            ranked_constellations
        )
        
        return comparison_result
    
    def _calculate_overall_performance_score(
        self,
        test_result: HandoverTestResult,
        metrics: Optional[ConstellationPerformanceMetrics]
    ) -> float:
        """計算綜合性能分數"""
        
        score = 0.0
        
        # 換手成功率 (40%)
        success_rate = test_result.successful_handovers / max(1, test_result.total_handovers)
        score += success_rate * 40
        
        # 延遲性能 (25%)
        latency_score = max(0, 1 - (test_result.average_latency / 200.0))
        score += latency_score * 25
        
        # 覆蓋率 (20%)
        score += (test_result.coverage_percentage / 100.0) * 20
        
        # 星座效率 (15%)
        if metrics:
            score += metrics.constellation_efficiency * 15
        
        return min(100.0, max(0.0, score))
    
    def _generate_optimization_recommendations(
        self,
        ranked_constellations: List[Tuple[str, Dict[str, Any]]]
    ) -> List[str]:
        """生成優化建議"""
        
        recommendations = []
        
        if len(ranked_constellations) < 2:
            return ["需要更多星座配置進行比較分析"]
        
        best_constellation = ranked_constellations[0][1]
        worst_constellation = ranked_constellations[-1][1]
        
        # 基於最佳性能的建議
        best_config = best_constellation["config"]
        if best_config["constellation_type"] == "leo_dense":
            recommendations.append("建議採用高密度LEO星座配置以獲得最佳換手性能")
        elif best_config["constellation_type"] == "walker_delta":
            recommendations.append("Walker Delta星座配置在覆蓋均勻性方面表現優異")
        
        # 基於性能差異的建議
        score_diff = best_constellation["performance_score"] - worst_constellation["performance_score"]
        if score_diff > 30:
            recommendations.append("不同星座配置間性能差異顯著，建議優化軌道參數")
        
        # 基於具體指標的建議
        best_latency = best_constellation["latest_test_result"]["average_latency"]
        if best_latency < 50:
            recommendations.append("當前最佳配置已達到低延遲要求，可考慮進一步優化覆蓋率")
        elif best_latency > 100:
            recommendations.append("建議增加衛星數量或調整軌道高度以降低換手延遲")
        
        return recommendations
    
    async def get_constellation_status(self, constellation_id: str) -> Dict[str, Any]:
        """獲取星座狀態信息"""
        
        if constellation_id not in self.constellation_configs:
            raise ValueError(f"星座配置不存在: {constellation_id}")
        
        config = self.constellation_configs[constellation_id]
        test_results = self.test_results.get(constellation_id, [])
        metrics = self.performance_metrics.get(constellation_id)
        
        return {
            "constellation_id": constellation_id,
            "config": asdict(config),
            "test_count": len(test_results),
            "latest_test_result": asdict(test_results[-1]) if test_results else None,
            "performance_metrics": asdict(metrics) if metrics else None,
            "status": "active" if test_results else "configured"
        }
    
    async def get_all_constellation_summaries(self) -> List[Dict[str, Any]]:
        """獲取所有星座的摘要信息"""
        
        summaries = []
        
        for constellation_id in self.constellation_configs:
            config = self.constellation_configs[constellation_id]
            test_results = self.test_results.get(constellation_id, [])
            metrics = self.performance_metrics.get(constellation_id)
            
            summary = {
                "constellation_id": constellation_id,
                "constellation_type": config.constellation_type.value,
                "satellite_count": config.satellite_count,
                "test_count": len(test_results),
                "latest_performance_score": 0.0,
                "status": "active" if test_results else "configured"
            }
            
            if test_results and metrics:
                latest_result = test_results[-1]
                summary["latest_performance_score"] = self._calculate_overall_performance_score(
                    latest_result, metrics
                )
            
            summaries.append(summary)
        
        return sorted(summaries, key=lambda x: x["latest_performance_score"], reverse=True)
    
    async def export_test_results(self, constellation_id: str, format: str = "json") -> str:
        """導出測試結果"""
        
        if constellation_id not in self.test_results:
            raise ValueError(f"沒有找到星座 {constellation_id} 的測試結果")
        
        export_data = {
            "constellation_id": constellation_id,
            "config": asdict(self.constellation_configs[constellation_id]),
            "test_results": [asdict(result) for result in self.test_results[constellation_id]],
            "performance_metrics": asdict(self.performance_metrics.get(constellation_id)) if constellation_id in self.performance_metrics else None,
            "export_timestamp": datetime.now().isoformat()
        }
        
        if format.lower() == "json":
            return json.dumps(export_data, indent=2, default=str)
        else:
            raise ValueError(f"不支援的匯出格式: {format}")

# 全域服務實例
constellation_test_service = ConstellationTestService()