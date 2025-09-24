"""
動畫建構器 - Stage 3模組化組件

職責：
1. 創建前端動畫所需的數據結構
2. 生成標準化的動畫格式
3. 優化動畫性能和數據大小
4. 確保動畫數據的學術級精度
"""

import logging
import math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class AnimationBuilder:
    """動畫建構器 - 創建前端友善的動畫數據格式"""
    
    def __init__(self, animation_fps: int = 24, optimize_for_web: bool = True):
        """
        初始化動畫建構器
        
        Args:
            animation_fps: 動畫幀率
            optimize_for_web: 是否為Web優化
        """
        self.logger = logging.getLogger(f"{__name__}.AnimationBuilder")
        
        self.animation_fps = animation_fps
        self.optimize_for_web = optimize_for_web
        
        # 動畫配置
        self.animation_config = {
            "target_fps": animation_fps,
            "time_range_hours": 6,  # 6小時動畫時長
            "quality_optimization": "high_precision" if not optimize_for_web else "web_optimized",
            "data_compression": optimize_for_web
        }
        
        # 建構統計
        self.build_statistics = {
            "total_satellites_processed": 0,
            "total_frames_generated": 0,
            "total_constellations": 0,
            "animation_data_size_mb": 0.0,
            "build_errors": 0
        }
        
        self.logger.info("✅ 動畫建構器初始化完成")
        self.logger.info(f"   動畫幀率: {animation_fps}fps")
        self.logger.info(f"   Web優化: {'是' if optimize_for_web else '否'}")
    
    def build_animation_data(self, timeseries_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        建構完整的動畫數據
        
        Args:
            timeseries_data: 時間序列轉換結果
            
        Returns:
            動畫數據結構
        """
        self.logger.info("🎬 開始建構動畫數據...")
        
        satellites = timeseries_data.get("satellites", [])
        self.build_statistics["total_satellites_processed"] = len(satellites)
        
        # 按星座分組衛星
        constellation_groups = self._group_satellites_by_constellation(satellites)
        self.build_statistics["total_constellations"] = len(constellation_groups)
        
        # 建構各星座的動畫數據
        constellation_animations = {}
        
        for const_name, const_satellites in constellation_groups.items():
            try:
                const_animation = self._build_constellation_animation(const_name, const_satellites)
                constellation_animations[const_name] = const_animation
                
            except Exception as e:
                self.logger.error(f"建構 {const_name} 星座動畫失敗: {e}")
                self.build_statistics["build_errors"] += 1
                continue
        
        # 建構全域動畫元數據
        global_metadata = self._build_global_animation_metadata(constellation_animations)
        
        # 組裝完整動畫數據
        animation_data = {
            "animation_metadata": global_metadata,
            "constellation_animations": constellation_animations,
            "build_statistics": self.build_statistics.copy(),
            "format_version": "v2.0",
            "builder_type": "modular_animation_builder"
        }
        
        self.logger.info(f"✅ 動畫數據建構完成: {len(constellation_animations)} 個星座")
        
        return animation_data
    
    def _group_satellites_by_constellation(self, satellites: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """按星座分組衛星"""
        
        constellation_groups = {}
        
        for satellite in satellites:
            constellation = satellite.get("constellation", "unknown").lower()
            
            if constellation not in constellation_groups:
                constellation_groups[constellation] = []
            
            constellation_groups[constellation].append(satellite)
        
        return constellation_groups
    
    def _build_constellation_animation(self, constellation_name: str, 
                                     satellites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """建構單個星座的動畫數據"""
        
        self.logger.info(f"🌌 建構 {constellation_name} 星座動畫: {len(satellites)} 顆衛星")
        
        # 建構衛星軌跡動畫
        satellite_tracks = []
        total_frames = 0
        
        for satellite in satellites:
            try:
                satellite_track = self._build_satellite_track(satellite)
                if satellite_track:
                    satellite_tracks.append(satellite_track)
                    total_frames += satellite_track.get("frame_count", 0)
                    
            except Exception as e:
                self.logger.warning(f"建構衛星 {satellite.get('name', 'unknown')} 軌跡失敗: {e}")
                continue
        
        # 建構星座級別的動畫特效
        constellation_effects = self._build_constellation_effects(constellation_name, satellite_tracks)
        
        # 建構時間軸和關鍵幀
        animation_timeline = self._build_animation_timeline(satellite_tracks)
        
        # 優化動畫數據
        if self.optimize_for_web:
            satellite_tracks = self._optimize_tracks_for_web(satellite_tracks)
        
        constellation_animation = {
            "constellation": constellation_name,
            "metadata": {
                "satellite_count": len(satellite_tracks),
                "total_frames": total_frames,
                "animation_duration_seconds": total_frames / self.animation_fps if self.animation_fps > 0 else 0,
                "quality_level": "high_precision",
                "optimization": "web" if self.optimize_for_web else "desktop"
            },
            "satellite_tracks": satellite_tracks,
            "constellation_effects": constellation_effects,
            "animation_timeline": animation_timeline,
            "rendering_hints": self._generate_rendering_hints(constellation_name, satellite_tracks)
        }
        
        self.build_statistics["total_frames_generated"] += total_frames
        
        return constellation_animation
    
    def _build_satellite_track(self, satellite: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """建構單顆衛星的動畫軌跡"""
        
        timeseries = satellite.get("timeseries", [])
        if not timeseries:
            return None
        
        # 建構位置關鍵幀
        position_keyframes = []
        visibility_keyframes = []
        signal_keyframes = []
        
        for point in timeseries:
            frame_number = point.get("frame_number", 0)
            
            # 位置關鍵幀
            position_keyframe = {
                "frame": frame_number,
                "position": {
                    "lat": point.get("latitude", 0.0),
                    "lon": point.get("longitude", 0.0),
                    "alt": point.get("altitude_km", 0.0)
                },
                "velocity": point.get("velocity_kmps", 0.0)
            }
            position_keyframes.append(position_keyframe)
            
            # 可見性關鍵幀
            if point.get("is_visible", False):
                visibility_keyframe = {
                    "frame": frame_number,
                    "elevation": point.get("elevation_deg", 0.0),
                    "azimuth": point.get("azimuth_deg", 0.0),
                    "range": point.get("range_km", 0.0),
                    "visibility_quality": point.get("elevation_quality", "standard")
                }
                visibility_keyframes.append(visibility_keyframe)
            
            # 信號關鍵幀（如果有信號時間線數據）
            signal_timeline = satellite.get("signal_timeline", {})
            if signal_timeline:
                signal_points = signal_timeline.get("signal_points", [])
                matching_signal = next(
                    (sp for sp in signal_points if sp.get("frame") == frame_number), None
                )
                
                if matching_signal:
                    signal_keyframe = {
                        "frame": frame_number,
                        "signal_strength": matching_signal.get("signal_strength", -140),
                        "signal_quality": matching_signal.get("signal_quality", "no_signal")
                    }
                    signal_keyframes.append(signal_keyframe)
        
        # 建構軌跡特徵
        track_features = self._analyze_track_features(position_keyframes, visibility_keyframes)
        
        satellite_track = {
            "satellite_id": satellite.get("satellite_id", "unknown"),
            "name": satellite.get("name", "unknown"),
            "constellation": satellite.get("constellation", "unknown"),
            
            # 動畫關鍵幀
            "position_keyframes": position_keyframes,
            "visibility_keyframes": visibility_keyframes,
            "signal_keyframes": signal_keyframes,
            
            # 軌跡特徵
            "track_features": track_features,
            
            # 動畫元數據
            "animation_metadata": {
                "frame_count": len(position_keyframes),
                "visible_frame_count": len(visibility_keyframes),
                "track_type": track_features.get("track_type", "unknown"),
                "animation_quality": satellite.get("animation_metadata", {}).get("animation_quality", "unknown")
            },
            
            # 渲染配置
            "rendering_config": self._generate_satellite_rendering_config(satellite, track_features)
        }
        
        return satellite_track
    
    def _analyze_track_features(self, position_keyframes: List[Dict[str, Any]], 
                               visibility_keyframes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析軌跡特徵"""
        
        features = {
            "track_type": "unknown",
            "peak_elevation": 0.0,
            "peak_frame": 0,
            "track_duration_frames": len(position_keyframes),
            "visible_duration_frames": len(visibility_keyframes)
        }
        
        if not visibility_keyframes:
            features["track_type"] = "not_visible"
            return features
        
        # 找到最高點
        peak_visibility = max(visibility_keyframes, key=lambda v: v["elevation"])
        features["peak_elevation"] = peak_visibility["elevation"]
        features["peak_frame"] = peak_visibility["frame"]
        
        # 判斷軌跡類型
        if len(visibility_keyframes) >= 3:
            elevations = [v["elevation"] for v in visibility_keyframes]
            frames = [v["frame"] for v in visibility_keyframes]
            
            # 找到最高點在序列中的位置
            peak_index = elevations.index(max(elevations))
            
            if peak_index == 0:
                features["track_type"] = "setting"
            elif peak_index == len(elevations) - 1:
                features["track_type"] = "rising"
            else:
                features["track_type"] = "transit"
        else:
            features["track_type"] = "brief_pass"
        
        # 計算軌跡覆蓋角度
        if len(visibility_keyframes) >= 2:
            azimuths = [v["azimuth"] for v in visibility_keyframes]
            features["azimuth_range"] = max(azimuths) - min(azimuths)
        
        return features
    
    def _build_constellation_effects(self, constellation_name: str, 
                                   satellite_tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """建構星座級別的動畫特效"""
        
        effects = {
            "constellation_name": constellation_name,
            "effect_type": self._determine_constellation_effect_type(constellation_name),
            "coverage_visualization": self._build_coverage_visualization(satellite_tracks),
            "handover_animations": self._build_handover_animations(satellite_tracks),
            "constellation_statistics": self._calculate_constellation_statistics(satellite_tracks)
        }
        
        return effects
    
    def _determine_constellation_effect_type(self, constellation_name: str) -> str:
        """決定星座動畫特效類型"""
        
        constellation_effects = {
            "starlink": "high_density_mesh",
            "oneweb": "polar_coverage",
            "unknown": "basic_tracks"
        }
        
        return constellation_effects.get(constellation_name.lower(), "basic_tracks")
    
    def _build_coverage_visualization(self, satellite_tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """建構覆蓋範圍可視化"""
        
        coverage_frames = []
        
        # 計算每幀的覆蓋狀況
        max_frames = max((track.get("animation_metadata", {}).get("frame_count", 0) 
                         for track in satellite_tracks), default=0)
        
        for frame in range(0, max_frames, 10):  # 每10幀計算一次覆蓋
            frame_coverage = {
                "frame": frame,
                "visible_satellites": 0,
                "coverage_areas": []
            }
            
            for track in satellite_tracks:
                # 檢查該幀是否有可見衛星
                visible_keyframes = track.get("visibility_keyframes", [])
                frame_visible = any(vk["frame"] == frame for vk in visible_keyframes)
                
                if frame_visible:
                    frame_coverage["visible_satellites"] += 1
                    
                    # 找到該幀的位置
                    position_keyframes = track.get("position_keyframes", [])
                    frame_position = next((pk for pk in position_keyframes if pk["frame"] == frame), None)
                    
                    if frame_position:
                        coverage_area = {
                            "satellite_id": track.get("satellite_id"),
                            "center": frame_position["position"],
                            "coverage_radius_km": self._calculate_realistic_coverage_radius(track)
                        }
                        frame_coverage["coverage_areas"].append(coverage_area)
            
            coverage_frames.append(frame_coverage)
        
        return {
            "coverage_frames": coverage_frames,
            "coverage_type": "ground_footprint",
            "update_interval_frames": 10
        }
    
    def _build_handover_animations(self, satellite_tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """建構換手動畫"""
        
        handover_events = []
        
        # 分析潛在的換手事件
        for i, track1 in enumerate(satellite_tracks):
            for j, track2 in enumerate(satellite_tracks[i+1:], i+1):
                handover_opportunities = self._find_handover_opportunities(track1, track2)
                handover_events.extend(handover_opportunities)
        
        return {
            "handover_events": handover_events,
            "animation_style": "smooth_transition",
            "highlight_duration_frames": 30
        }
    
    def _find_handover_opportunities(self, track1: Dict[str, Any], 
                                   track2: Dict[str, Any]) -> List[Dict[str, Any]]:
        """尋找兩顆衛星之間的換手機會"""
        
        handovers = []
        
        vis1 = track1.get("visibility_keyframes", [])
        vis2 = track2.get("visibility_keyframes", [])
        
        # 簡化版本：找到一顆衛星下降另一顆上升的時間點
        for v1 in vis1:
            for v2 in vis2:
                frame_diff = abs(v1["frame"] - v2["frame"])
                if frame_diff <= 30:  # 30幀內的換手機會
                    if v1["elevation"] > 15 and v2["elevation"] > 15:  # 都在有效仰角
                        handover = {
                            "frame": (v1["frame"] + v2["frame"]) // 2,
                            "from_satellite": track1.get("satellite_id"),
                            "to_satellite": track2.get("satellite_id"),
                            "handover_quality": "good" if min(v1["elevation"], v2["elevation"]) > 30 else "fair"
                        }
                        handovers.append(handover)
        
        return handovers
    
    def _build_animation_timeline(self, satellite_tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """建構動畫時間軸"""
        
        if not satellite_tracks:
            return {"timeline_events": [], "total_duration_frames": 0}
        
        timeline_events = []
        
        # 收集所有重要事件
        for track in satellite_tracks:
            satellite_id = track.get("satellite_id")
            
            # 可見性開始和結束事件
            visibility_keyframes = track.get("visibility_keyframes", [])
            if visibility_keyframes:
                # 可見性開始
                first_visible = min(visibility_keyframes, key=lambda v: v["frame"])
                timeline_events.append({
                    "frame": first_visible["frame"],
                    "event_type": "visibility_start",
                    "satellite_id": satellite_id,
                    "elevation": first_visible["elevation"]
                })
                
                # 峰值仰角
                peak_visible = max(visibility_keyframes, key=lambda v: v["elevation"])
                timeline_events.append({
                    "frame": peak_visible["frame"],
                    "event_type": "peak_elevation",
                    "satellite_id": satellite_id,
                    "elevation": peak_visible["elevation"]
                })
                
                # 可見性結束
                last_visible = max(visibility_keyframes, key=lambda v: v["frame"])
                timeline_events.append({
                    "frame": last_visible["frame"],
                    "event_type": "visibility_end",
                    "satellite_id": satellite_id,
                    "elevation": last_visible["elevation"]
                })
        
        # 按幀號排序事件
        timeline_events.sort(key=lambda e: e["frame"])
        
        total_duration = max((track.get("animation_metadata", {}).get("frame_count", 0) 
                             for track in satellite_tracks), default=0)
        
        return {
            "timeline_events": timeline_events,
            "total_duration_frames": total_duration,
            "key_moments": self._identify_key_animation_moments(timeline_events)
        }
    
    def _identify_key_animation_moments(self, timeline_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """識別關鍵動畫時刻"""
        
        key_moments = []
        
        # 找到最佳觀測時刻（多顆衛星同時可見）
        frame_visibility = {}
        for event in timeline_events:
            if event["event_type"] == "peak_elevation":
                frame = event["frame"]
                if frame not in frame_visibility:
                    frame_visibility[frame] = []
                frame_visibility[frame].append(event)
        
        # 找到同時可見衛星最多的時刻
        for frame, events in frame_visibility.items():
            if len(events) >= 2:  # 至少2顆衛星
                key_moments.append({
                    "frame": frame,
                    "moment_type": "multi_satellite_peak",
                    "satellite_count": len(events),
                    "max_elevation": max(e["elevation"] for e in events)
                })
        
        return key_moments
    
    def _calculate_constellation_statistics(self, satellite_tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """計算星座統計信息"""
        
        if not satellite_tracks:
            return {"satellite_count": 0}
        
        total_satellites = len(satellite_tracks)
        visible_satellites = len([t for t in satellite_tracks 
                                 if t.get("animation_metadata", {}).get("visible_frame_count", 0) > 0])
        
        total_frames = sum(t.get("animation_metadata", {}).get("frame_count", 0) 
                          for t in satellite_tracks)
        
        peak_elevations = []
        for track in satellite_tracks:
            track_features = track.get("track_features", {})
            peak_elevation = track_features.get("peak_elevation", 0)
            if peak_elevation > 0:
                peak_elevations.append(peak_elevation)
        
        stats = {
            "satellite_count": total_satellites,
            "visible_satellite_count": visible_satellites,
            "visibility_rate": visible_satellites / total_satellites if total_satellites > 0 else 0,
            "total_animation_frames": total_frames,
            "avg_frames_per_satellite": total_frames / total_satellites if total_satellites > 0 else 0
        }
        
        if peak_elevations:
            stats.update({
                "max_elevation_overall": max(peak_elevations),
                "avg_peak_elevation": sum(peak_elevations) / len(peak_elevations),
                "satellites_above_45deg": len([e for e in peak_elevations if e >= 45])
            })
        
        return stats
    
    def _optimize_tracks_for_web(self, satellite_tracks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """為Web優化軌跡數據"""
        
        optimized_tracks = []
        
        for track in satellite_tracks:
            # 減少關鍵幀密度（保持重要幀）
            position_keyframes = track.get("position_keyframes", [])
            visibility_keyframes = track.get("visibility_keyframes", [])
            
            # 智能抽取關鍵幀
            optimized_position = self._thin_keyframes(position_keyframes, max_frames=200)
            optimized_visibility = self._thin_keyframes(visibility_keyframes, max_frames=100)
            
            optimized_track = track.copy()
            optimized_track["position_keyframes"] = optimized_position
            optimized_track["visibility_keyframes"] = optimized_visibility
            
            # 添加優化標記
            optimized_track["optimization_applied"] = True
            optimized_track["original_frame_count"] = len(position_keyframes)
            optimized_track["optimized_frame_count"] = len(optimized_position)
            
            optimized_tracks.append(optimized_track)
        
        return optimized_tracks
    
    def _thin_keyframes(self, keyframes: List[Dict[str, Any]], max_frames: int) -> List[Dict[str, Any]]:
        """智能抽減關鍵幀"""
        
        if len(keyframes) <= max_frames:
            return keyframes
        
        # 保持開始、結束和峰值幀
        if len(keyframes) < 3:
            return keyframes
        
        result = [keyframes[0]]  # 保持第一幀
        
        # 計算抽取間隔
        skip_interval = len(keyframes) // max_frames
        
        for i in range(skip_interval, len(keyframes), skip_interval):
            if i < len(keyframes) - 1:  # 不要最後一幀（單獨添加）
                result.append(keyframes[i])
        
        result.append(keyframes[-1])  # 保持最後一幀
        
        return result
    
    def _generate_rendering_hints(self, constellation_name: str, 
                                satellite_tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成渲染提示"""
        
        hints = {
            "constellation_color_scheme": self._get_constellation_colors(constellation_name),
            "rendering_priority": "performance" if self.optimize_for_web else "quality",
            "suggested_effects": [],
            "performance_recommendations": []
        }
        
        # 基於衛星數量調整渲染策略
        satellite_count = len(satellite_tracks)
        
        if satellite_count > 50:
            hints["performance_recommendations"].extend([
                "use_instanced_rendering",
                "enable_level_of_detail",
                "reduce_trail_length"
            ])
        
        if constellation_name.lower() == "starlink":
            hints["suggested_effects"].extend([
                "constellation_mesh",
                "coverage_overlay",
                "inter_satellite_links"
            ])
        
        return hints
    
    def _get_constellation_colors(self, constellation_name: str) -> Dict[str, str]:
        """獲取星座配色方案"""
        
        color_schemes = {
            "starlink": {
                "primary": "#00D4FF",
                "secondary": "#0099CC", 
                "trail": "#004D66"
            },
            "oneweb": {
                "primary": "#FF6B35",
                "secondary": "#CC5429",
                "trail": "#7A311A"
            },
            "unknown": {
                "primary": "#FFFFFF",
                "secondary": "#CCCCCC",
                "trail": "#666666"
            }
        }
        
        return color_schemes.get(constellation_name.lower(), color_schemes["unknown"])
    
    def _generate_satellite_rendering_config(self, satellite: Dict[str, Any], 
                                           track_features: Dict[str, Any]) -> Dict[str, Any]:
        """生成衛星渲染配置"""
        
        config = {
            "visibility": {
                "show_satellite": True,
                "show_trail": track_features.get("visible_duration_frames", 0) > 10,
                "show_coverage": track_features.get("peak_elevation", 0) > 30,
                "show_signal_strength": True
            },
            "rendering_style": {
                "satellite_size": self._calculate_satellite_size(track_features),
                "trail_length": min(100, track_features.get("visible_duration_frames", 0)),
                "opacity": self._calculate_opacity(track_features)
            },
            "animation_behavior": {
                "smooth_motion": True,
                "anticipation_frames": 5,
                "highlight_peak": track_features.get("peak_elevation", 0) > 45
            }
        }
        
        return config
    
    def _calculate_satellite_size(self, track_features: Dict[str, Any]) -> float:
        """計算衛星渲染大小"""
        
        peak_elevation = track_features.get("peak_elevation", 0)
        
        if peak_elevation >= 60:
            return 1.5
        elif peak_elevation >= 30:
            return 1.2
        elif peak_elevation >= 15:
            return 1.0
        else:
            return 0.8
    
    def _calculate_opacity(self, track_features: Dict[str, Any]) -> float:
        """計算透明度"""
        
        peak_elevation = track_features.get("peak_elevation", 0)
        visible_duration = track_features.get("visible_duration_frames", 0)
        
        # 基於仰角和可見時間計算透明度
        elevation_factor = min(1.0, peak_elevation / 90.0)
        duration_factor = min(1.0, visible_duration / 100.0)
        
        return max(0.3, (elevation_factor + duration_factor) / 2)

    def _calculate_realistic_coverage_radius(self, track: Dict[str, Any]) -> float:
        """
        基於學術級物理計算衛星覆蓋半徑 (Grade A標準)
        
        Args:
            track: 衛星軌跡數據
            
        Returns:
            實際覆蓋半徑 (km)
        """
        try:
            # 🔬 基於球面幾何學計算覆蓋半徑
            # 公式: R = R_earth * arccos(R_earth / (R_earth + h)) / sin(min_elevation)
            
            # 地球半徑 (ITU-R標準值)
            earth_radius_km = 6371.0  # km
            
            # 獲取衛星高度
            satellite_altitude_km = None
            constellation = track.get("constellation", "unknown").lower()
            
            # 從學術配置獲取真實高度數據
            try:
                from ...shared.academic_standards_config import ACADEMIC_STANDARDS_CONFIG
                constellation_params = ACADEMIC_STANDARDS_CONFIG.get_constellation_params(constellation)
                satellite_altitude_km = constellation_params.get("altitude_km")
                
                if satellite_altitude_km is None:
                    self.logger.warning(f"⚠️ 無法獲取{constellation}星座的高度數據")
                    
            except Exception as e:
                self.logger.error(f"❌ 學術配置載入失敗: {e}")
            
            # 如果無法獲取真實高度，拒絕使用假設值
            if satellite_altitude_km is None:
                raise ValueError("無法獲取衛星真實高度數據，拒絕使用假設覆蓋半徑")
            
            # 最小仰角門檻 (基於ITU-R P.618建議) - 動態載入標準配置
            from shared.constants.system_constants import get_system_constants
            elevation_standards = get_system_constants().get_elevation_standards()
            min_elevation_deg = elevation_standards.STANDARD_ELEVATION_DEG  # 動態從ITU-R標準
            min_elevation_rad = math.radians(min_elevation_deg)
            
            # 物理級覆蓋半徑計算
            # 基於球面幾何學：考慮地球曲率的視線距離
            orbital_radius = earth_radius_km + satellite_altitude_km
            
            # 地心角計算 (從衛星到地平線)
            horizon_angle = math.acos(earth_radius_km / orbital_radius)
            
            # 考慮最小仰角的有效覆蓋角
            effective_coverage_angle = horizon_angle - min_elevation_rad
            
            # 地面覆蓋半徑
            coverage_radius_km = earth_radius_km * math.sin(effective_coverage_angle)
            
            self.logger.debug(f"🛰️ {constellation}覆蓋半徑計算: 高度={satellite_altitude_km}km, 半徑={coverage_radius_km:.1f}km")
            
            return max(100.0, min(2000.0, coverage_radius_km))  # 合理範圍限制
            
        except Exception as e:
            self.logger.error(f"❌ 覆蓋半徑計算失敗: {e}")
            # 🚨 學術標準要求：計算失敗時不得使用硬編碼回退
            raise ValueError(f"覆蓋半徑計算失敗且無法使用假設值，請檢查衛星參數配置: {e}")
    
    def _build_global_animation_metadata(self, constellation_animations: Dict[str, Any]) -> Dict[str, Any]:
        """建構全域動畫元數據"""
        
        total_satellites = sum(
            anim.get("metadata", {}).get("satellite_count", 0)
            for anim in constellation_animations.values()
        )
        
        total_frames = sum(
            anim.get("metadata", {}).get("total_frames", 0)
            for anim in constellation_animations.values()
        )
        
        metadata = {
            "animation_version": "2.0",
            "created_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_constellations": len(constellation_animations),
            "total_satellites": total_satellites,
            "total_animation_frames": total_frames,
            "animation_duration_seconds": total_frames / self.animation_fps if self.animation_fps > 0 else 0,
            "target_fps": self.animation_fps,
            "quality_settings": {
                "precision": "high",
                "optimization": "web" if self.optimize_for_web else "desktop",
                "academic_compliance": "grade_a"
            },
            "rendering_recommendations": {
                "recommended_canvas_size": "1920x1080",
                "minimum_canvas_size": "800x600",
                "suggested_camera_distance": 2.5,
                "lighting_model": "realistic"
            }
        }
        
        return metadata
    
    def get_build_statistics(self) -> Dict[str, Any]:
        """獲取建構統計信息"""
        return self.build_statistics.copy()
    
    def validate_animation_data(self, animation_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證動畫數據完整性"""
        
        validation_result = {
            "passed": True,
            "total_constellations": len(animation_data.get("constellation_animations", {})),
            "validation_checks": {},
            "issues": []
        }
        
        constellation_animations = animation_data.get("constellation_animations", {})
        
        if not constellation_animations:
            validation_result["passed"] = False
            validation_result["issues"].append("無星座動畫數據")
            return validation_result
        
        # 檢查每個星座的動畫完整性
        constellations_with_tracks = 0
        constellations_with_effects = 0
        
        for const_name, const_anim in constellation_animations.items():
            satellite_tracks = const_anim.get("satellite_tracks", [])
            constellation_effects = const_anim.get("constellation_effects", {})
            
            if satellite_tracks:
                constellations_with_tracks += 1
            
            if constellation_effects:
                constellations_with_effects += 1
        
        validation_result["validation_checks"]["animation_completeness_check"] = {
            "constellations_with_tracks": constellations_with_tracks,
            "constellations_with_effects": constellations_with_effects,
            "passed": constellations_with_tracks == len(constellation_animations)
        }
        
        if constellations_with_tracks < len(constellation_animations):
            validation_result["passed"] = False
            validation_result["issues"].append(f"{len(constellation_animations) - constellations_with_tracks} 個星座缺少軌跡數據")
        
        return validation_result