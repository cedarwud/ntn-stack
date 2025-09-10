"""
數據注入除錯工具

用於創建標準化的測試數據，支援不同的測試場景。
這是重構後除錯功能的重要組成部分。
"""

from typing import Dict, Any, List
from datetime import datetime, timezone
import json
import random
from pathlib import Path

class DebugDataInjector:
    """數據注入除錯工具"""
    
    def __init__(self):
        self.data_format_version = "unified_v1.2_phase3"
        self.base_timestamp = datetime.now(timezone.utc).isoformat()
    
    def create_stage_test_data(self, stage_number: int, scenario: str = 'normal') -> Dict[str, Any]:
        """
        創建特定階段的測試數據
        
        Args:
            stage_number: 目標階段編號 (1-6)
            scenario: 測試場景 ('normal', 'error', 'performance', 'small')
            
        Returns:
            標準化的測試數據
        """
        method_map = {
            1: self.create_stage1_test_data,
            2: self.create_stage2_test_data,
            3: self.create_stage3_test_data,
            4: self.create_stage4_test_data,
            5: self.create_stage5_test_data,
            6: self.create_stage6_test_data
        }
        
        if stage_number not in method_map:
            raise ValueError(f"無效的階段編號: {stage_number}")
        
        return method_map[stage_number](scenario)
    
    def create_stage1_test_data(self, scenario: str) -> Dict[str, Any]:
        """創建Stage 1（軌道計算）測試數據"""
        # Stage 1 不需要輸入數據，返回None
        return None
    
    def create_stage2_test_data(self, scenario: str) -> Dict[str, Any]:
        """創建Stage 2（可見性過濾）測試數據"""
        base_data = {
            "data": {
                "orbital_calculations": self._generate_orbital_data(scenario),
                "satellites": self._generate_satellite_list(scenario)
            },
            "metadata": {
                "stage_number": 1,
                "stage_name": "orbital_calculation",
                "processing_timestamp": self.base_timestamp,
                "total_records": 100 if scenario != 'performance' else 10000,
                "data_format_version": self.data_format_version,
                "data_lineage": {
                    "source": "tle_data_loader",
                    "processing_steps": ["sgp4_calculation", "position_calculation"]
                }
            }
        }
        
        return base_data
    
    def create_stage3_test_data(self, scenario: str) -> Dict[str, Any]:
        """創建Stage 3（時間序列預處理）測試數據"""
        base_data = {
            "data": {
                "visible_satellites": self._generate_visible_satellites(scenario),
                "visibility_windows": self._generate_visibility_windows(scenario)
            },
            "metadata": {
                "stage_number": 2,
                "stage_name": "visibility_filter",
                "processing_timestamp": self.base_timestamp,
                "total_records": 80 if scenario != 'performance' else 8000,
                "data_format_version": self.data_format_version,
                "elevation_threshold": 10.0,
                "data_lineage": {
                    "source": "orbital_calculation",
                    "processing_steps": ["elevation_filter", "visibility_calculation"]
                }
            }
        }
        
        return base_data
    
    def create_stage4_test_data(self, scenario: str) -> Dict[str, Any]:
        """創建Stage 4（信號分析）測試數據"""
        base_data = {
            "data": {
                "timeseries_data": self._generate_timeseries_data(scenario),
                "satellite_trajectories": self._generate_trajectories(scenario)
            },
            "metadata": {
                "stage_number": 3,
                "stage_name": "timeseries_preprocessing",
                "processing_timestamp": self.base_timestamp,
                "total_records": 60 if scenario != 'performance' else 6000,
                "data_format_version": self.data_format_version,
                "sampling_rate": 192,
                "data_lineage": {
                    "source": "visibility_filter", 
                    "processing_steps": ["interpolation", "smoothing", "validation"]
                }
            }
        }
        
        return base_data
    
    def create_stage5_test_data(self, scenario: str) -> Dict[str, Any]:
        """創建Stage 5（數據整合）測試數據"""
        starlink_count = 20 if scenario == 'small' else 100
        oneweb_count = 15 if scenario == 'small' else 75
        
        if scenario == 'performance':
            starlink_count = 1000
            oneweb_count = 750
        
        base_data = {
            "data": {
                "starlink": self._generate_constellation_data("Starlink", starlink_count, scenario),
                "oneweb": self._generate_constellation_data("OneWeb", oneweb_count, scenario),
                "signal_analysis": {
                    "rsrp_measurements": self._generate_rsrp_data(scenario),
                    "doppler_calculations": self._generate_doppler_data(scenario)
                }
            },
            "metadata": {
                "stage_number": 4,
                "stage_name": "signal_analysis",
                "processing_timestamp": self.base_timestamp,
                "total_records": starlink_count + oneweb_count,
                "data_format_version": self.data_format_version,
                "signal_quality_threshold": 0.6,
                "data_lineage": {
                    "source": "timeseries_preprocessing",
                    "processing_steps": ["signal_calculation", "quality_assessment", "filtering"]
                }
            }
        }
        
        # 根據場景調整數據
        if scenario == 'error':
            # 注入錯誤數據用於測試錯誤處理
            if base_data['data']['starlink']:
                base_data['data']['starlink'][0]['tle_data'] = None  # 缺少TLE數據
                base_data['data']['starlink'][1]['signal_quality'] = None  # 缺少信號質量
        
        return base_data
    
    def create_stage6_test_data(self, scenario: str) -> Dict[str, Any]:
        """創建Stage 6（動態規劃）測試數據"""
        base_data = {
            "data": {
                "integrated_satellites": self._generate_integrated_satellites(scenario),
                "handover_candidates": self._generate_handover_candidates(scenario)
            },
            "metadata": {
                "stage_number": 5,
                "stage_name": "data_integration", 
                "processing_timestamp": self.base_timestamp,
                "total_records": 50 if scenario != 'performance' else 5000,
                "data_format_version": self.data_format_version,
                "integration_completeness": 0.95,
                "data_lineage": {
                    "source": "signal_analysis",
                    "processing_steps": ["data_merger", "consistency_check", "quality_validation"]
                }
            }
        }
        
        return base_data
    
    def _generate_orbital_data(self, scenario: str) -> List[Dict[str, Any]]:
        """生成軌道數據"""
        count = 10 if scenario == 'small' else 50
        if scenario == 'performance':
            count = 500
        
        orbital_data = []
        for i in range(count):
            orbital_data.append({
                "satellite_id": f"SAT-{i:04d}",
                "positions": [
                    {
                        "time": f"2021-10-02T10:{30+j:02d}:00Z",
                        "latitude": random.uniform(-90, 90),
                        "longitude": random.uniform(-180, 180),
                        "altitude": random.uniform(400, 600)
                    }
                    for j in range(192)  # 192個時間點
                ],
                "orbital_elements": {
                    "semi_major_axis": random.uniform(6800, 7000),
                    "eccentricity": random.uniform(0.0001, 0.002),
                    "inclination": random.uniform(50, 60)
                }
            })
        
        return orbital_data
    
    def _generate_satellite_list(self, scenario: str) -> List[str]:
        """生成衛星列表"""
        count = 10 if scenario == 'small' else 50
        if scenario == 'performance':
            count = 500
        
        return [f"SAT-{i:04d}" for i in range(count)]
    
    def _generate_visible_satellites(self, scenario: str) -> List[Dict[str, Any]]:
        """生成可見衛星數據"""
        count = 8 if scenario == 'small' else 40
        if scenario == 'performance':
            count = 400
        
        visible_satellites = []
        for i in range(count):
            visible_satellites.append({
                "satellite_id": f"SAT-{i:04d}",
                "elevation": random.uniform(10, 90),  # 大於10度仰角
                "azimuth": random.uniform(0, 360),
                "range_km": random.uniform(500, 2000),
                "visibility_duration": random.uniform(300, 1200)  # 5-20分鐘
            })
        
        return visible_satellites
    
    def _generate_visibility_windows(self, scenario: str) -> List[Dict[str, Any]]:
        """生成可見性時間窗口"""
        count = 8 if scenario == 'small' else 40
        if scenario == 'performance':
            count = 400
        
        windows = []
        for i in range(count):
            start_time = f"2021-10-02T{10+i%12:02d}:00:00Z"
            end_time = f"2021-10-02T{10+i%12:02d}:15:00Z"
            
            windows.append({
                "satellite_id": f"SAT-{i:04d}",
                "start_time": start_time,
                "end_time": end_time,
                "max_elevation": random.uniform(15, 90),
                "pass_type": random.choice(["ascending", "descending"])
            })
        
        return windows
    
    def _generate_timeseries_data(self, scenario: str) -> Dict[str, Any]:
        """生成時間序列數據"""
        return {
            "sampling_points": 192,
            "interpolated_positions": True,
            "data_quality": 0.95 if scenario != 'error' else 0.60
        }
    
    def _generate_trajectories(self, scenario: str) -> List[Dict[str, Any]]:
        """生成軌跡數據"""
        count = 6 if scenario == 'small' else 30
        if scenario == 'performance':
            count = 300
        
        trajectories = []
        for i in range(count):
            trajectories.append({
                "satellite_id": f"SAT-{i:04d}",
                "trajectory_points": 192,
                "smoothing_applied": True,
                "trajectory_quality": 0.90 if scenario != 'error' else 0.50
            })
        
        return trajectories
    
    def _generate_constellation_data(self, constellation: str, count: int, scenario: str) -> List[Dict[str, Any]]:
        """生成星座數據"""
        satellites = []
        
        for i in range(count):
            satellite = {
                "satellite_id": f"{constellation.upper()}-{i:04d}",
                "name": f"{constellation}-{i:04d}",
                "tle_data": {
                    "tle_line1": f"1 {44713+i}U 19074A   21275.91667824  .00001874  00000-0  13717-3 0  9995",
                    "tle_line2": f"2 {44713+i}  53.0000 123.4567   0.0013 269.3456 162.7890 15.05000000123456"
                } if scenario != 'error' or i > 0 else None,  # 第一顆衛星在error場景下缺少TLE
                "orbital_positions": [
                    {
                        "timestamp": f"2021-10-02T10:{j:02d}:00Z",
                        "lat": random.uniform(-90, 90),
                        "lon": random.uniform(-180, 180),
                        "alt": random.uniform(400, 600)
                    }
                    for j in range(min(192, 10 if scenario == 'small' else 192))
                ],
                "signal_quality": random.uniform(0.7, 0.95) if scenario != 'error' or i > 1 else None,
                "constellation": constellation
            }
            
            satellites.append(satellite)
        
        return satellites
    
    def _generate_rsrp_data(self, scenario: str) -> Dict[str, Any]:
        """生成RSRP測量數據"""
        return {
            "measurements_count": 100 if scenario != 'performance' else 10000,
            "average_rsrp": -85.5,
            "rsrp_range": [-120, -60],
            "quality_threshold": -95.0
        }
    
    def _generate_doppler_data(self, scenario: str) -> Dict[str, Any]:
        """生成都卜勒數據"""
        return {
            "calculations_count": 100 if scenario != 'performance' else 10000,
            "frequency_shift_range": [-50000, 50000],  # Hz
            "carrier_frequency": 2.4e9  # 2.4 GHz
        }
    
    def _generate_integrated_satellites(self, scenario: str) -> List[Dict[str, Any]]:
        """生成整合後的衛星數據"""
        count = 5 if scenario == 'small' else 25
        if scenario == 'performance':
            count = 250
        
        satellites = []
        for i in range(count):
            satellites.append({
                "satellite_id": f"INTEGRATED-{i:04d}",
                "constellation": random.choice(["Starlink", "OneWeb"]),
                "integration_score": random.uniform(0.8, 0.99),
                "data_completeness": 0.95,
                "validation_status": "passed"
            })
        
        return satellites
    
    def _generate_handover_candidates(self, scenario: str) -> List[Dict[str, Any]]:
        """生成換手候選數據"""
        count = 3 if scenario == 'small' else 15
        if scenario == 'performance':
            count = 150
        
        candidates = []
        for i in range(count):
            candidates.append({
                "source_satellite": f"INTEGRATED-{i:04d}",
                "target_satellite": f"INTEGRATED-{i+1:04d}",
                "handover_score": random.uniform(0.7, 0.95),
                "estimated_duration": random.uniform(30, 180)  # 秒
            })
        
        return candidates
    
    def save_test_data(self, stage_number: int, scenario: str, output_file: str = None) -> str:
        """
        保存測試數據到文件
        
        Args:
            stage_number: 階段編號
            scenario: 測試場景
            output_file: 輸出文件路徑
            
        Returns:
            保存的文件路徑
        """
        test_data = self.create_stage_test_data(stage_number, scenario)
        
        if output_file is None:
            output_file = f"stage{stage_number}_{scenario}_test_data.json"
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2, ensure_ascii=False)
        
        print(f"測試數據已保存: {output_path}")
        return str(output_path)