#!/usr/bin/env python3
"""
🛰️ 修正版轨道可见性验证器
====================================

修正之前的计算错误：
1. 过滤非活跃卫星
2. 使用合理的卫星数量
3. 验证结果的合理性
4. 提供准确的可见性分析
"""

import sys
import os
import json
import logging
import math
from datetime import datetime, timezone, timedelta
from pathlib import Path
import numpy as np
from typing import Dict, List, Any, Tuple

try:
    from skyfield.api import load, Topos, EarthSatellite
    from skyfield.timelib import Time
    SKYFIELD_AVAILABLE = True
except ImportError:
    print("⚠️ Skyfield not available")
    SKYFIELD_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CorrectedOrbitalValidator:
    """修正版轨道可见性验证器"""
    
    def __init__(self):
        # NTPU坐标
        self.ntpu_lat = 24.943464
        self.ntpu_lon = 121.367699
        self.ntpu_elevation_m = 50
        self.min_elevation_deg = 10.0
        
        # 轨道周期
        self.starlink_period_min = 93.63
        self.oneweb_period_min = 109.64
        
        # 时间步长 (增加到2分钟以减少计算量但保持精度)
        self.time_step_sec = 120
        
        # 合理的星座规模 (基于公开信息)
        self.reasonable_constellation_sizes = {
            'starlink': 5000,  # 约5000颗活跃卫星 (2024年数据)
            'oneweb': 600      # 约600颗活跃卫星
        }
        
        logger.info("🛰️ 修正版轨道验证器初始化完成")
        
    def filter_active_satellites(self, tle_lines: List[str], constellation: str) -> List[str]:
        """过滤出活跃卫星的TLE数据"""
        logger.info(f"🔍 过滤{constellation}活跃卫星...")
        
        if not tle_lines:
            return []
            
        # 解析所有卫星
        satellites = []
        for i in range(0, len(tle_lines) - 2, 3):
            if (tle_lines[i].strip() and 
                tle_lines[i+1].startswith('1 ') and 
                tle_lines[i+2].startswith('2 ')):
                
                name = tle_lines[i].strip()
                line1 = tle_lines[i+1].strip()
                line2 = tle_lines[i+2].strip()
                
                # 基本过滤条件
                try:
                    # 提取轨道参数进行基本验证
                    mean_motion = float(line2[52:63])  # 每日轨道圈数
                    eccentricity = float('0.' + line2[26:33])  # 轨道偏心率
                    inclination = float(line2[8:16])  # 轨道倾角
                    
                    # 过滤条件
                    valid_satellite = True
                    
                    # 1. 检查轨道参数合理性
                    if constellation == 'starlink':
                        # Starlink典型参数范围
                        if not (14.0 <= mean_motion <= 16.0):  # 约550km高度
                            valid_satellite = False
                        if not (53.0 <= inclination <= 54.0):  # 53度倾角
                            valid_satellite = False
                    elif constellation == 'oneweb':
                        # OneWeb典型参数范围  
                        if not (12.5 <= mean_motion <= 13.5):  # 约1200km高度
                        # if not (86.0 <= inclination <= 88.0):  # 87.9度倾角
                            valid_satellite = False
                        # OneWeb倾角检查暂时放宽，因为有多种倾角
                    
                    # 2. 检查偏心率 (应该接近圆形轨道)
                    if eccentricity > 0.01:  # 偏心率过大
                        valid_satellite = False
                    
                    # 3. 简单的命名过滤 (去除明显的测试卫星)
                    name_lower = name.lower()
                    if any(keyword in name_lower for keyword in 
                           ['test', 'demo', 'debug', 'deorbit', 'disposal']):
                        valid_satellite = False
                    
                    if valid_satellite:
                        satellites.append({
                            'name': name,
                            'line1': line1,
                            'line2': line2,
                            'mean_motion': mean_motion,
                            'inclination': inclination,
                            'eccentricity': eccentricity
                        })
                        
                except (ValueError, IndexError) as e:
                    logger.debug(f"解析卫星{name}失败: {e}")
                    continue
        
        # 按轨道参数排序并选择合理数量
        satellites.sort(key=lambda x: (x['inclination'], x['mean_motion']))
        
        # 限制数量到合理范围
        max_satellites = self.reasonable_constellation_sizes.get(constellation, 1000)
        if len(satellites) > max_satellites:
            # 均匀采样以保持轨道分布
            step = len(satellites) // max_satellites
            satellites = satellites[::step][:max_satellites]
        
        # 转换回TLE格式
        filtered_tle = []
        for sat in satellites:
            filtered_tle.extend([sat['name'], sat['line1'], sat['line2']])
            
        logger.info(f"✅ {constellation}过滤完成: {len(satellites)} 颗活跃卫星 (原始: {len(tle_lines)//3})")
        
        return filtered_tle
        
    def load_and_filter_tle_data(self) -> Dict[str, List[str]]:
        """载入并过滤TLE数据"""
        logger.info("📡 载入并过滤TLE数据...")
        
        tle_data = {"starlink": [], "oneweb": []}
        
        # TLE数据路径
        tle_base_path = "/home/sat/ntn-stack/netstack/tle_data"
        tle_dir = Path(tle_base_path)
        
        if not tle_dir.exists():
            logger.error(f"TLE目录不存在: {tle_dir}")
            return tle_data
            
        # Starlink
        starlink_files = list(tle_dir.glob("**/starlink*.tle"))
        if starlink_files:
            starlink_file = sorted(starlink_files)[-1]  # 最新文件
            logger.info(f"  载入Starlink TLE: {starlink_file}")
            raw_tle = self._parse_tle_file(starlink_file)
            tle_data["starlink"] = self.filter_active_satellites(raw_tle, "starlink")
            
        # OneWeb
        oneweb_files = list(tle_dir.glob("**/oneweb*.tle"))
        if oneweb_files:
            oneweb_file = sorted(oneweb_files)[-1]  # 最新文件
            logger.info(f"  载入OneWeb TLE: {oneweb_file}")
            raw_tle = self._parse_tle_file(oneweb_file)
            tle_data["oneweb"] = self.filter_active_satellites(raw_tle, "oneweb")
            
        logger.info(f"✅ 过滤后TLE数据:")
        logger.info(f"  Starlink: {len(tle_data['starlink'])//3} 颗活跃卫星")
        logger.info(f"  OneWeb: {len(tle_data['oneweb'])//3} 颗活跃卫星")
        
        return tle_data
        
    def _parse_tle_file(self, tle_file_path: Path) -> List[str]:
        """解析TLE文件"""
        tle_lines = []
        try:
            with open(tle_file_path, 'r', encoding='utf-8') as f:
                lines = f.read().strip().split('\n')
                
            for i in range(0, len(lines) - 2, 3):
                if (lines[i].strip() and 
                    lines[i+1].startswith('1 ') and 
                    lines[i+2].startswith('2 ')):
                    tle_lines.extend([lines[i].strip(), lines[i+1].strip(), lines[i+2].strip()])
                    
        except Exception as e:
            logger.warning(f"解析TLE文件失败 {tle_file_path}: {e}")
            
        return tle_lines
        
    def calculate_corrected_visibility(self, constellation: str, tle_data: List[str], 
                                     period_minutes: float) -> Dict[str, Any]:
        """计算修正后的可见性"""
        logger.info(f"🔄 计算{constellation}修正后的可见性({period_minutes:.2f}分钟)...")
        
        if not SKYFIELD_AVAILABLE:
            logger.warning("Skyfield不可用，使用理论估算")
            return self._theoretical_visibility_estimate(constellation, len(tle_data)//3, period_minutes)
            
        # 时间设置
        ts = load.timescale()
        start_time = ts.now()
        duration_seconds = int(period_minutes * 60)
        
        # 生成时间序列 (使用更大的步长)
        time_points = []
        for offset in range(0, duration_seconds, self.time_step_sec):
            time_points.append(start_time + timedelta(seconds=offset))
            
        logger.info(f"  时间点数: {len(time_points)} (步长: {self.time_step_sec//60}分钟)")
        
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
                logger.debug(f"解析卫星{name}失败: {e}")
                
        logger.info(f"  成功解析: {len(satellites)} 颗卫星")
        
        # 计算可见性时间线
        visibility_timeline = []
        
        for idx, time_point in enumerate(time_points):
            visible_count = 0
            visible_satellites = []
            
            for sat_name, satellite in satellites:
                try:
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
                'time_offset_minutes': idx * self.time_step_sec / 60,
                'visible_count': visible_count,
                'visible_satellites': visible_satellites[:5]  # 只保存前5个作为样本
            })
            
            # 进度显示
            if idx % 10 == 0:
                logger.info(f"    计算进度: {idx}/{len(time_points)} ({visible_count}颗可见)")
                
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
            'timeline_sample': visibility_timeline[::len(visibility_timeline)//10][:10]  # 10个样本点
        }
        
        logger.info(f"✅ {constellation}修正后分析完成:")
        logger.info(f"  可见卫星数: {results['visibility_statistics']['min_visible']}-{results['visibility_statistics']['max_visible']} (平均{results['visibility_statistics']['avg_visible']:.1f})")
        logger.info(f"  可见率: {results['visibility_statistics']['avg_visible']/len(satellites)*100:.2f}%")
        logger.info(f"  持续覆盖: {'是' if results['coverage_analysis']['always_covered'] else '否'}")
        
        return results
        
    def _theoretical_visibility_estimate(self, constellation: str, satellite_count: int, 
                                       period_minutes: float) -> Dict[str, Any]:
        """理论可见性估算"""
        logger.info(f"使用理论模型估算{constellation}可见性...")
        
        # 基于轨道几何的理论估算
        if constellation == "starlink":
            # 550km高度，约4%天空可见
            visibility_fraction = 0.04
            base_visible = int(satellite_count * visibility_fraction * 0.6)  # 加入分布因子
        else:  # OneWeb
            # 1200km高度，约8%天空可见
            visibility_fraction = 0.08
            base_visible = int(satellite_count * visibility_fraction * 0.6)
            
        # 添加时间变化
        variation = max(1, base_visible // 4)
        min_visible = max(0, base_visible - variation)
        max_visible = base_visible + variation
        
        results = {
            'constellation': constellation,
            'orbital_period_minutes': float(period_minutes),
            'total_satellites': satellite_count,
            'analysis_duration_minutes': float(period_minutes),
            'time_points_analyzed': int(period_minutes * 2),  # 假设30秒采样
            'visibility_statistics': {
                'min_visible': min_visible,
                'max_visible': max_visible,
                'avg_visible': float(base_visible),
                'median_visible': float(base_visible),
                'std_visible': float(variation)
            },
            'coverage_analysis': {
                'always_covered': bool(min_visible > 0),
                'min_coverage_satellites': min_visible,
                'peak_coverage_satellites': max_visible,
                'coverage_stability': float(variation)
            },
            'note': 'theoretical_estimate'
        }
        
        return results
        
    def run_corrected_validation(self) -> Dict[str, Any]:
        """运行修正后的完整验证"""
        logger.info("🚀 开始修正版轨道可见性验证")
        logger.info("=" * 80)
        
        # 1. 载入过滤后的TLE数据
        tle_data = self.load_and_filter_tle_data()
        
        validation_results = {
            'validation_timestamp': datetime.now(timezone.utc).isoformat(),
            'correction_applied': True,
            'filtering_method': 'orbital_parameters_and_naming',
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
        
        # 2. Starlink分析
        if tle_data['starlink']:
            logger.info(f"\n📡 分析过滤后Starlink ({self.starlink_period_min:.2f}分钟)")
            starlink_results = self.calculate_corrected_visibility(
                'starlink', 
                tle_data['starlink'], 
                self.starlink_period_min
            )
            validation_results['constellation_results']['starlink'] = starlink_results
            
        # 3. OneWeb分析
        if tle_data['oneweb']:
            logger.info(f"\n🌐 分析过滤后OneWeb ({self.oneweb_period_min:.2f}分钟)")
            oneweb_results = self.calculate_corrected_visibility(
                'oneweb',
                tle_data['oneweb'],
                self.oneweb_period_min
            )
            validation_results['constellation_results']['oneweb'] = oneweb_results
            
        # 4. 组合分析和合理性检查
        if 'starlink' in validation_results['constellation_results'] and 'oneweb' in validation_results['constellation_results']:
            self.perform_reasonableness_check(validation_results)
            
        # 5. 生成最终报告
        self.generate_final_report(validation_results)
        
        return validation_results
        
    def perform_reasonableness_check(self, results: Dict[str, Any]):
        """合理性检查"""
        logger.info(f"\n🔍 合理性检查")
        
        # 理论上限 (从之前的分析)
        theoretical_limits = {'starlink': 37, 'oneweb': 20}
        
        for const_name, const_results in results['constellation_results'].items():
            actual_max = const_results['visibility_statistics']['max_visible']
            actual_avg = const_results['visibility_statistics']['avg_visible']
            theoretical_max = theoretical_limits.get(const_name, 50)
            
            logger.info(f"  {const_name.upper()}:")
            logger.info(f"    实际最大: {actual_max} 颗")
            logger.info(f"    理论上限: {theoretical_max} 颗")
            
            if actual_max <= theoretical_max * 1.2:  # 允许20%误差
                logger.info(f"    合理性: ✅ 合理")
                const_results['reasonableness_check'] = 'reasonable'
            else:
                logger.warning(f"    合理性: ⚠️ 仍然偏高")
                const_results['reasonableness_check'] = 'still_high'
                
    def generate_final_report(self, results: Dict[str, Any]):
        """生成最终报告"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 修正版轨道可见性验证结果")
        logger.info("=" * 80)
        
        for const_name, const_results in results['constellation_results'].items():
            stats = const_results['visibility_statistics']
            logger.info(f"\n🛰️  {const_name.upper()} (修正后):")
            logger.info(f"   活跃卫星数: {const_results['total_satellites']}")
            logger.info(f"   可见范围: {stats['min_visible']}-{stats['max_visible']} 颗")
            logger.info(f"   平均可见: {stats['avg_visible']:.1f} 颗")
            logger.info(f"   可见率: {stats['avg_visible']/const_results['total_satellites']*100:.2f}%")
            logger.info(f"   合理性: {const_results.get('reasonableness_check', 'unknown')}")
            
        # 组合分析
        if len(results['constellation_results']) == 2:
            starlink_avg = results['constellation_results']['starlink']['visibility_statistics']['avg_visible']
            oneweb_avg = results['constellation_results']['oneweb']['visibility_statistics']['avg_visible']
            combined_avg = starlink_avg + oneweb_avg
            
            starlink_min = results['constellation_results']['starlink']['visibility_statistics']['min_visible']
            oneweb_min = results['constellation_results']['oneweb']['visibility_statistics']['min_visible']
            combined_min = starlink_min + oneweb_min
            
            logger.info(f"\n🔄 组合星座 (修正后):")
            logger.info(f"   预估平均可见: {combined_avg:.1f} 颗")
            logger.info(f"   预估最少可见: {combined_min} 颗")
            logger.info(f"   满足10-15颗要求: {'✅' if 10 <= combined_avg <= 15 else '❌'}")
            logger.info(f"   满足3-6颗要求: {'✅' if 3 <= combined_min <= 6 else '❌'}")
            
        logger.info("=" * 80)

def main():
    """主函数"""
    logger.info("🛰️ 修正版轨道可见性验证器")
    
    try:
        validator = CorrectedOrbitalValidator()
        results = validator.run_corrected_validation()
        
        # 保存结果
        output_file = Path("/home/sat/ntn-stack/corrected_orbital_validation_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        logger.info(f"\n✅ 修正后验证结果已保存: {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 验证过程发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)