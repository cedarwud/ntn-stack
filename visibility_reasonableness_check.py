#!/usr/bin/env python3
"""
🔍 卫星可见性合理性检查
================================

验证LEO卫星可见性计算的合理性：
1. 检查地面观测点的理论可见卫星数量上限
2. 分析轨道几何约束
3. 验证计算逻辑的正确性
"""

import sys
import math
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VisibilityReasonablenessChecker:
    """可见性合理性检查器"""
    
    def __init__(self):
        # NTPU坐标
        self.ntpu_lat = 24.943464  # 度
        self.ntpu_lon = 121.367699  # 度
        
        # 轨道参数
        self.earth_radius_km = 6371.0
        self.starlink_altitude_km = 550.0  # 平均高度
        self.oneweb_altitude_km = 1200.0   # 平均高度
        
        # 仰角门槛
        self.min_elevation_deg = 10.0
        
        logger.info("🔍 可见性合理性检查器初始化完成")
        
    def calculate_theoretical_visibility_limits(self):
        """计算理论可见性限制"""
        logger.info("📐 计算理论可见性限制...")
        
        results = {}
        
        for constellation, altitude_km in [("Starlink", self.starlink_altitude_km), 
                                          ("OneWeb", self.oneweb_altitude_km)]:
            logger.info(f"\n🛰️ {constellation} (高度: {altitude_km} km)")
            
            # 1. 计算地平线距离 (0度仰角)
            horizon_distance_km = math.sqrt(2 * self.earth_radius_km * altitude_km + altitude_km**2)
            logger.info(f"  地平线距离: {horizon_distance_km:.1f} km")
            
            # 2. 计算10度仰角对应的距离
            elevation_rad = math.radians(self.min_elevation_deg)
            
            # 使用球面几何计算最大范围
            # 地心角计算
            satellite_distance = self.earth_radius_km + altitude_km
            
            # 从观测点到卫星的角度计算
            sin_range_angle = math.cos(elevation_rad) * self.earth_radius_km / satellite_distance
            if sin_range_angle > 1.0:
                sin_range_angle = 1.0
            range_angle_rad = math.asin(sin_range_angle)
            
            max_range_km = self.earth_radius_km * range_angle_rad
            logger.info(f"  10度仰角最大范围: {max_range_km:.1f} km")
            
            # 3. 计算可见天空面积
            # 球冠面积计算
            earth_angular_radius = math.acos(self.earth_radius_km / satellite_distance)
            visible_solid_angle = 2 * math.pi * (1 - math.cos(earth_angular_radius))
            visible_sky_fraction = visible_solid_angle / (4 * math.pi)
            logger.info(f"  可见天空比例: {visible_sky_fraction:.1%}")
            
            # 4. 理论最大可见卫星数估算
            # 基于卫星密度和可见区域
            orbital_circumference = 2 * math.pi * satellite_distance
            if constellation == "Starlink":
                # Starlink约有72个轨道平面，每个平面约22颗卫星
                satellites_per_plane = 22
                num_orbital_planes = 72
                total_satellites_theoretical = satellites_per_plane * num_orbital_planes
            else:  # OneWeb
                # OneWeb约有49个轨道平面，每个平面约36颗卫星  
                satellites_per_plane = 36
                num_orbital_planes = 12  # 实际运营的平面数
                total_satellites_theoretical = satellites_per_plane * num_orbital_planes
                
            # 估算任何时刻可见的卫星数
            # 考虑轨道分布和可见区域重叠
            estimated_visible = total_satellites_theoretical * visible_sky_fraction
            
            # 考虑轨道倾角分布，减少重叠区域的影响
            inclination_factor = 0.6  # 经验系数，考虑轨道倾角分布
            reasonable_max_visible = int(estimated_visible * inclination_factor)
            
            logger.info(f"  理论总卫星数: {total_satellites_theoretical}")
            logger.info(f"  估算最大可见: {reasonable_max_visible} 颗")
            
            results[constellation.lower()] = {
                'altitude_km': altitude_km,
                'horizon_distance_km': horizon_distance_km,
                'max_range_10deg_km': max_range_km,
                'visible_sky_fraction': visible_sky_fraction,
                'theoretical_total': total_satellites_theoretical,
                'estimated_max_visible': reasonable_max_visible,
                'reasonable_range': f"5-{reasonable_max_visible}"
            }
            
        return results
        
    def analyze_actual_vs_theoretical(self, theoretical_limits):
        """分析实际结果与理论限制的对比"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 实际结果 vs 理论限制对比分析")
        logger.info("=" * 80)
        
        # 从验证结果文件读取实际数据
        results_file = Path("/home/sat/ntn-stack/orbital_coverage_validation_results.json")
        if results_file.exists():
            import json
            with open(results_file, 'r', encoding='utf-8') as f:
                actual_results = json.load(f)
                
            logger.info("🔍 对比分析:")
            
            for constellation in ['starlink', 'oneweb']:
                if constellation in actual_results['constellation_results']:
                    actual = actual_results['constellation_results'][constellation]
                    theoretical = theoretical_limits[constellation]
                    
                    actual_min = actual['visibility_statistics']['min_visible']
                    actual_max = actual['visibility_statistics']['max_visible']
                    actual_avg = actual['visibility_statistics']['avg_visible']
                    
                    theoretical_max = theoretical['estimated_max_visible']
                    
                    logger.info(f"\n🛰️ {constellation.upper()}:")
                    logger.info(f"  实际范围: {actual_min}-{actual_max} 颗 (平均 {actual_avg:.1f})")
                    logger.info(f"  理论上限: ~{theoretical_max} 颗")
                    logger.info(f"  合理性: {'❌ 异常高' if actual_min > theoretical_max else '⚠️ 需检查' if actual_avg > theoretical_max else '✅ 合理'}")
                    
                    # 详细分析
                    if actual_min > theoretical_max:
                        logger.warning(f"    ⚠️ 最小值 {actual_min} 超过理论上限 {theoretical_max}")
                        logger.warning(f"    可能原因: 计算错误、TLE数据异常、或理论模型不准确")
                        
                    # 计算可见率
                    total_sats = actual['total_satellites']
                    visibility_rate = (actual_avg / total_sats) * 100
                    logger.info(f"  可见率: {visibility_rate:.2f}% ({actual_avg:.1f}/{total_sats})")
                    
        else:
            logger.warning("未找到验证结果文件，无法进行对比分析")
            
    def check_calculation_logic(self):
        """检查计算逻辑的可能问题"""
        logger.info("\n" + "=" * 80) 
        logger.info("🔧 计算逻辑检查")
        logger.info("=" * 80)
        
        potential_issues = [
            "1. TLE数据可能包含非活跃卫星或测试卫星",
            "2. 未正确处理地球遮挡效应", 
            "3. 仰角计算可能存在坐标系转换错误",
            "4. 时间同步问题 - 不同卫星的轨道时期不一致",
            "5. Skyfield库的默认设置可能不适合大规模计算",
            "6. 卫星轨道衰减或维护状态未考虑"
        ]
        
        logger.info("🔍 可能的问题来源:")
        for issue in potential_issues:
            logger.info(f"  {issue}")
            
        logger.info("\n💡 建议的验证方法:")
        suggestions = [
            "1. 使用小样本卫星 (10-20颗) 手动验证计算",
            "2. 对比其他卫星跟踪工具 (如 N2YO, Heavens Above)",
            "3. 检查TLE数据的卫星状态和分类",
            "4. 验证坐标转换和时区处理",
            "5. 分析轨道平面分布的合理性"
        ]
        
        for suggestion in suggestions:
            logger.info(f"  {suggestion}")
            
    def run_comprehensive_check(self):
        """运行综合合理性检查"""
        logger.info("🔍 开始卫星可见性合理性检查")
        logger.info("=" * 80)
        
        # 1. 计算理论限制
        theoretical_limits = self.calculate_theoretical_visibility_limits()
        
        # 2. 对比实际与理论
        self.analyze_actual_vs_theoretical(theoretical_limits)
        
        # 3. 检查计算逻辑
        self.check_calculation_logic()
        
        logger.info("\n" + "=" * 80)
        logger.info("📋 合理性检查总结")
        logger.info("=" * 80)
        
        logger.info("🎯 关键发现:")
        logger.info("  1. 如果实际可见数量远超理论上限，说明计算存在问题")
        logger.info("  2. LEO卫星可见性应该受到严格的几何约束")
        logger.info("  3. 需要重新验证TLE数据和计算逻辑的正确性")
        
        return theoretical_limits

def main():
    """主函数"""
    logger.info("🔍 卫星可见性合理性检查工具")
    
    try:
        checker = VisibilityReasonablenessChecker()
        results = checker.run_comprehensive_check()
        
        logger.info("\n✅ 合理性检查完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 检查过程发生错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)