#!/usr/bin/env python3
"""
🛰️ 真实轨道周期可见性验证器
===============================

验证在完整轨道周期内NTPU上空的卫星可见性：
- Starlink: 93.63分钟轨道周期
- OneWeb: 109.64分钟轨道周期  
- 使用真实SGP4轨道传播
- 统计任何时刻可见卫星数量
"""

import sys
import os
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
import numpy as np
from typing import Dict, List, Any, Tuple
import math

# 添加必要的路径
sys.path.insert(0, '/home/sat/ntn-stack/netstack/src')

try:
    from skyfield.api import load, Topos, EarthSatellite
    from skyfield.timelib import Time
    SKYFIELD_AVAILABLE = True
except ImportError:
    print("⚠️ Skyfield not available, using simplified orbit model")
    SKYFIELD_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OrbitalCoverageValidator:
    """真实轨道周期可见性验证器"""
    
    def __init__(self):
        # NTPU坐标 (台湾新北市)
        self.ntpu_lat = 24.943464  # 度
        self.ntpu_lon = 121.367699  # 度
        self.ntpu_elevation_m = 50  # 米
        self.min_elevation_deg = 10.0  # 最小仰角门槛
        
        # 轨道周期 (分钟)
        self.starlink_period_min = 93.63
        self.oneweb_period_min = 109.64
        
        # 时间步长 (秒) - 足够精细以捕捉快速变化
        self.time_step_sec = 30
        
        logger.info("🛰️ 轨道覆盖验证器初始化完成")
        logger.info(f"  NTPU坐标: ({self.ntpu_lat:.6f}°, {self.ntpu_lon:.6f}°)")
        logger.info(f"  最小仰角: {self.min_elevation_deg}°")
        logger.info(f"  Starlink周期: {self.starlink_period_min:.2f} 分钟")
        logger.info(f"  OneWeb周期: {self.oneweb_period_min:.2f} 分钟")
        
    def load_tle_data(self) -> Dict[str, List[str]]:
        """载入TLE轨道数据"""
        logger.info("📡 载入TLE轨道数据...")
        
        tle_data = {"starlink": [], "oneweb": []}
        
        # 尝试从实际TLE数据目录载入
        tle_paths = [
            "/home/sat/ntn-stack/netstack/tle_data",
            "/home/sat/ntn-stack/data/tle_data",
            "/tmp/satellite_data/tle_data", 
            "/home/sat/ntn-stack/tle_data"
        ]
        
        for tle_base_path in tle_paths:
            tle_dir = Path(tle_base_path)
            if not tle_dir.exists():
                continue
                
            logger.info(f"  检查TLE目录: {tle_dir}")
            
            # Starlink TLE - 查找子目录
            starlink_files = list(tle_dir.glob("**/starlink*.tle")) + list(tle_dir.glob("**/starlink*.txt"))
            if starlink_files:
                # 使用最新的文件
                starlink_file = sorted(starlink_files)[-1]
                logger.info(f"  载入Starlink TLE: {starlink_file}")
                tle_data["starlink"] = self._parse_tle_file(starlink_file)
                
            # OneWeb TLE - 查找子目录
            oneweb_files = list(tle_dir.glob("**/oneweb*.tle")) + list(tle_dir.glob("**/oneweb*.txt"))
            if oneweb_files:
                # 使用最新的文件
                oneweb_file = sorted(oneweb_files)[-1]
                logger.info(f"  载入OneWeb TLE: {oneweb_file}")
                tle_data["oneweb"] = self._parse_tle_file(oneweb_file)
                
            if tle_data["starlink"] or tle_data["oneweb"]:
                break
        
        logger.info(f"✅ TLE数据载入完成:")
        logger.info(f"  Starlink: {len(tle_data['starlink'])} 颗卫星")
        logger.info(f"  OneWeb: {len(tle_data['oneweb'])} 颗卫星")
        
        return tle_data
        
    def _parse_tle_file(self, tle_file_path: Path) -> List[str]:
        """解析TLE文件"""
        tle_lines = []
        try:
            with open(tle_file_path, 'r', encoding='utf-8') as f:
                lines = f.read().strip().split('\n')
                
            # TLE format: Name, Line1, Line2 (groups of 3)
            for i in range(0, len(lines) - 2, 3):
                if (lines[i].strip() and 
                    lines[i+1].startswith('1 ') and 
                    lines[i+2].startswith('2 ')):
                    tle_lines.append(lines[i].strip())
                    tle_lines.append(lines[i+1].strip()) 
                    tle_lines.append(lines[i+2].strip())
                    
        except Exception as e:
            logger.warning(f"解析TLE文件失败 {tle_file_path}: {e}")
            
        return tle_lines
        
    def calculate_visibility_over_period(self, constellation: str, tle_data: List[str], 
                                       period_minutes: float) -> Dict[str, Any]:
        """计算完整轨道周期内的可见性"""
        logger.info(f"🔄 计算{constellation}完整轨道周期({period_minutes:.2f}分钟)可见性...")
        
        if not SKYFIELD_AVAILABLE:
            return self._simplified_visibility_calculation(constellation, len(tle_data)//3, period_minutes)
            
        # 时间范围设定
        ts = load.timescale()
        start_time = ts.now()
        duration_seconds = int(period_minutes * 60)
        time_points = []
        
        # 生成时间序列
        for offset in range(0, duration_seconds, self.time_step_sec):
            time_points.append(start_time + timedelta(seconds=offset))
            
        logger.info(f"  时间点数: {len(time_points)} (步长: {self.time_step_sec}秒)")
        
        # NTPU观测点
        observer = Topos(latitude_degrees=self.ntpu_lat, 
                        longitude_degrees=self.ntpu_lon,
                        elevation_m=self.ntpu_elevation_m)
        
        # 解析卫星
        satellites = []
        for i in range(0, len(tle_data) - 2, 3):
            name = tle_data[i]
            line1 = tle_data[i + 1] 
            line2 = tle_data[i + 2]
            try:
                sat = EarthSatellite(line1, line2, name, ts)
                satellites.append((name, sat))
            except Exception as e:
                logger.warning(f"解析卫星{name}失败: {e}")
                
        logger.info(f"  成功解析: {len(satellites)} 颗卫星")
        
        # 计算每个时间点的可见卫星数
        visibility_timeline = []
        
        for time_point in time_points:
            visible_count = 0
            visible_satellites = []
            
            for sat_name, satellite in satellites:
                try:
                    # 计算卫星相对于观测点的位置
                    difference = satellite - observer
                    topocentric = difference.at(time_point)
                    alt, az, distance = topocentric.altaz()
                    
                    elevation_deg = alt.degrees
                    if elevation_deg >= self.min_elevation_deg:
                        visible_count += 1
                        visible_satellites.append({
                            'name': sat_name,
                            'elevation_deg': elevation_deg,
                            'azimuth_deg': az.degrees,
                            'range_km': distance.km
                        })
                        
                except Exception as e:
                    logger.debug(f"计算{sat_name}位置失败: {e}")
                    continue
                    
            visibility_timeline.append({
                'time': time_point.utc_iso(),
                'time_offset_minutes': len(visibility_timeline) * self.time_step_sec / 60,
                'visible_count': visible_count,
                'visible_satellites': visible_satellites
            })
            
        # 统计结果
        visible_counts = [point['visible_count'] for point in visibility_timeline]
        
        results = {
            'constellation': constellation,
            'orbital_period_minutes': float(period_minutes),
            'total_satellites': len(satellites),
            'analysis_duration_minutes': float(period_minutes),
            'time_points_analyzed': len(visibility_timeline),
            'visibility_statistics': {
                'min_visible': int(min(visible_counts)),
                'max_visible': int(max(visible_counts)), 
                'avg_visible': float(np.mean(visible_counts)),
                'median_visible': float(np.median(visible_counts)),
                'std_visible': float(np.std(visible_counts))
            },
            'coverage_analysis': {
                'always_covered': bool(min(visible_counts) > 0),
                'min_coverage_satellites': int(min(visible_counts)),
                'peak_coverage_satellites': int(max(visible_counts)),
                'coverage_stability': float(np.std(visible_counts))
            },
            'timeline': visibility_timeline[:10]  # 保存前10个时间点作为样本
        }
        
        logger.info(f"✅ {constellation}可见性分析完成:")
        logger.info(f"  可见卫星数: {results['visibility_statistics']['min_visible']}-{results['visibility_statistics']['max_visible']} (平均{results['visibility_statistics']['avg_visible']:.1f})")
        logger.info(f"  持续覆盖: {'是' if results['coverage_analysis']['always_covered'] else '否'}")
        
        return results
        
    def _simplified_visibility_calculation(self, constellation: str, satellite_count: int, 
                                          period_minutes: float) -> Dict[str, Any]:
        """简化的可见性计算 (当Skyfield不可用时)"""
        logger.warning(f"使用简化模型计算{constellation}可见性...")
        
        # 基于经验模型的简化计算
        if constellation == "starlink":
            # Starlink在较低轨道，更频繁过境
            base_visible = 3 + (satellite_count // 100)
            variation = 2
        else:  # OneWeb
            # OneWeb在更高轨道，过境时间更长但频率较低
            base_visible = 2 + (satellite_count // 80)
            variation = 1
            
        # 模拟时间变化
        time_points = int(period_minutes * 2)  # 每30秒一个点
        visible_counts = []
        
        for i in range(time_points):
            # 添加周期性变化
            phase = (i / time_points) * 2 * math.pi
            variation_factor = 1 + 0.3 * math.sin(phase) + 0.2 * math.sin(3 * phase)
            visible = max(0, int(base_visible * variation_factor))
            visible_counts.append(visible)
            
        results = {
            'constellation': constellation,
            'orbital_period_minutes': period_minutes,
            'total_satellites': satellite_count,
            'analysis_duration_minutes': period_minutes,
            'time_points_analyzed': len(visible_counts),
            'visibility_statistics': {
                'min_visible': min(visible_counts),
                'max_visible': max(visible_counts),
                'avg_visible': np.mean(visible_counts),
                'median_visible': np.median(visible_counts),
                'std_visible': np.std(visible_counts)
            },
            'coverage_analysis': {
                'always_covered': min(visible_counts) > 0,
                'min_coverage_satellites': min(visible_counts),
                'peak_coverage_satellites': max(visible_counts),
                'coverage_stability': np.std(visible_counts)
            },
            'note': 'simplified_calculation'
        }
        
        return results
        
    def run_full_validation(self) -> Dict[str, Any]:
        """运行完整的轨道周期可见性验证"""
        logger.info("🚀 开始真实轨道周期可见性验证")
        logger.info("=" * 80)
        
        # 1. 载入TLE数据
        tle_data = self.load_tle_data()
        
        validation_results = {
            'validation_timestamp': datetime.now(timezone.utc).isoformat(),
            'ntpu_coordinates': {
                'latitude': self.ntpu_lat,
                'longitude': self.ntpu_lon,
                'elevation_m': self.ntpu_elevation_m
            },
            'analysis_parameters': {
                'min_elevation_deg': self.min_elevation_deg,
                'time_step_sec': self.time_step_sec
            },
            'constellation_results': {}
        }
        
        # 2. Starlink轨道周期分析
        if tle_data['starlink']:
            logger.info(f"\n📡 分析Starlink轨道周期 ({self.starlink_period_min:.2f}分钟)")
            starlink_results = self.calculate_visibility_over_period(
                'starlink', 
                tle_data['starlink'], 
                self.starlink_period_min
            )
            validation_results['constellation_results']['starlink'] = starlink_results
            
        # 3. OneWeb轨道周期分析  
        if tle_data['oneweb']:
            logger.info(f"\n🌐 分析OneWeb轨道周期 ({self.oneweb_period_min:.2f}分钟)")
            oneweb_results = self.calculate_visibility_over_period(
                'oneweb',
                tle_data['oneweb'],
                self.oneweb_period_min
            )
            validation_results['constellation_results']['oneweb'] = oneweb_results
            
        # 4. 组合分析
        if 'starlink' in validation_results['constellation_results'] and 'oneweb' in validation_results['constellation_results']:
            logger.info(f"\n🔄 组合星座覆盖分析")
            
            starlink_avg = validation_results['constellation_results']['starlink']['visibility_statistics']['avg_visible']
            oneweb_avg = validation_results['constellation_results']['oneweb']['visibility_statistics']['avg_visible']
            combined_avg = starlink_avg + oneweb_avg
            
            starlink_min = validation_results['constellation_results']['starlink']['visibility_statistics']['min_visible']
            oneweb_min = validation_results['constellation_results']['oneweb']['visibility_statistics']['min_visible']
            combined_min = starlink_min + oneweb_min
            
            validation_results['combined_analysis'] = {
                'estimated_combined_average': combined_avg,
                'estimated_combined_minimum': combined_min,
                'meets_10_15_requirement': combined_min >= 10 and combined_avg <= 15,
                'meets_3_6_requirement': combined_min >= 3 and combined_avg <= 6,
                'coverage_assessment': 'excellent' if combined_min >= 10 else 'good' if combined_min >= 3 else 'insufficient'
            }
            
        # 5. 生成验证报告
        logger.info("\n" + "=" * 80)
        logger.info("📊 轨道周期可见性验证结果")
        logger.info("=" * 80)
        
        for const_name, results in validation_results['constellation_results'].items():
            logger.info(f"\n🛰️  {const_name.upper()}:")
            logger.info(f"   轨道周期: {results['orbital_period_minutes']:.2f} 分钟")
            logger.info(f"   总卫星数: {results['total_satellites']}")
            logger.info(f"   可见范围: {results['visibility_statistics']['min_visible']}-{results['visibility_statistics']['max_visible']} 颗")
            logger.info(f"   平均可见: {results['visibility_statistics']['avg_visible']:.1f} 颗")
            logger.info(f"   持续覆盖: {'✅' if results['coverage_analysis']['always_covered'] else '❌'}")
            
        if 'combined_analysis' in validation_results:
            logger.info(f"\n🔄 组合星座评估:")
            logger.info(f"   预估平均可见: {validation_results['combined_analysis']['estimated_combined_average']:.1f} 颗")
            logger.info(f"   预估最少可见: {validation_results['combined_analysis']['estimated_combined_minimum']} 颗")
            logger.info(f"   满足10-15颗要求: {'✅' if validation_results['combined_analysis']['meets_10_15_requirement'] else '❌'}")
            logger.info(f"   满足3-6颗要求: {'✅' if validation_results['combined_analysis']['meets_3_6_requirement'] else '❌'}")
            
        logger.info("=" * 80)
        
        return validation_results

def main():
    """主函数"""
    logger.info("🛰️ 真实轨道周期可见性验证器")
    logger.info("=" * 80)
    
    try:
        validator = OrbitalCoverageValidator()
        results = validator.run_full_validation()
        
        # 保存结果
        output_file = Path("/home/sat/ntn-stack/orbital_coverage_validation_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        logger.info(f"\n✅ 验证结果已保存: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 验证过程发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)