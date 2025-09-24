"""
輸出格式化器 - Stage 3模組化組件

職責：
1. 標準化Stage 3輸出格式
2. 生成前端動畫所需的文件格式
3. 確保與下游階段的兼容性
4. 優化輸出文件大小和結構
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class OutputFormatter:
    """輸出格式化器 - 標準化Stage 3輸出格式"""
    
    def __init__(self, output_format: str = "enhanced_animation", compress_output: bool = False):
        """
        初始化輸出格式化器
        
        Args:
            output_format: 輸出格式類型 (enhanced_animation/web_optimized/research_grade)
            compress_output: 是否壓縮輸出
        """
        self.logger = logging.getLogger(f"{__name__}.OutputFormatter")
        
        self.output_format = output_format.lower()
        self.compress_output = compress_output
        
        # 支援的輸出格式
        self.supported_formats = ["enhanced_animation", "web_optimized", "research_grade"]
        
        if self.output_format not in self.supported_formats:
            self.logger.warning(f"不支援的輸出格式 '{output_format}'，使用預設格式 'enhanced_animation'")
            self.output_format = "enhanced_animation"
        
        # 格式化統計
        self.formatting_statistics = {
            "files_generated": 0,
            "total_output_size_mb": 0.0,
            "constellations_processed": 0,
            "animation_frames_total": 0
        }
        
        self.logger.info(f"✅ 輸出格式化器初始化完成 (格式: {self.output_format})")
    
    def format_stage3_output(self, 
                           timeseries_data: Dict[str, Any],
                           animation_data: Dict[str, Any],
                           academic_validation: Dict[str, Any],
                           processing_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化Stage 3的完整輸出
        
        Args:
            timeseries_data: 時間序列轉換結果
            animation_data: 動畫建構結果
            academic_validation: 學術驗證結果
            processing_metadata: 處理元數據
            
        Returns:
            標準化的Stage 3輸出
        """
        self.logger.info(f"📋 格式化Stage 3輸出 (格式: {self.output_format})...")
        
        try:
            if self.output_format == "web_optimized":
                return self._format_web_optimized_output(
                    timeseries_data, animation_data, academic_validation, processing_metadata
                )
            elif self.output_format == "research_grade":
                return self._format_research_grade_output(
                    timeseries_data, animation_data, academic_validation, processing_metadata
                )
            else:  # enhanced_animation
                return self._format_enhanced_animation_output(
                    timeseries_data, animation_data, academic_validation, processing_metadata
                )
                
        except Exception as e:
            self.logger.error(f"格式化輸出時出錯: {e}")
            raise
    
    def _format_enhanced_animation_output(self,
                                        timeseries_data: Dict[str, Any],
                                        animation_data: Dict[str, Any],
                                        academic_validation: Dict[str, Any],
                                        processing_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """格式化增強動畫輸出"""
        
        constellation_animations = animation_data.get("constellation_animations", {})
        self.formatting_statistics["constellations_processed"] = len(constellation_animations)
        
        # 為每個星座創建標準化動畫格式
        formatted_constellations = {}
        
        for const_name, const_anim in constellation_animations.items():
            formatted_const = self._format_constellation_animation(const_name, const_anim)
            formatted_constellations[const_name] = formatted_const
            
            # 統計動畫幀數
            frames = formatted_const.get("metadata", {}).get("total_frames", 0)
            self.formatting_statistics["animation_frames_total"] += frames
        
        # 生成全域元數據
        global_metadata = self._generate_global_metadata(
            timeseries_data, animation_data, academic_validation, processing_metadata
        )
        
        # 生成動畫配置
        animation_config = self._generate_animation_config(constellation_animations)
        
        return {
            "format_version": "enhanced_animation_v2.0",
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            
            # 核心動畫數據
            "animation_data": {
                "constellations": formatted_constellations,
                "global_config": animation_config,
                "rendering_hints": self._generate_rendering_hints(constellation_animations)
            },
            
            # 元數據和統計
            "metadata": global_metadata,
            "processing_statistics": self._compile_processing_statistics(
                timeseries_data, animation_data, processing_metadata
            ),
            
            # 品質保證
            "quality_assurance": {
                "academic_validation": self._summarize_academic_validation(academic_validation),
                "data_integrity_checks": self._generate_integrity_summary(timeseries_data),
                "animation_quality_metrics": self._calculate_animation_quality_metrics(constellation_animations)
            }
        }
    
    def _format_web_optimized_output(self,
                                   timeseries_data: Dict[str, Any],
                                   animation_data: Dict[str, Any],
                                   academic_validation: Dict[str, Any],
                                   processing_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """格式化Web優化輸出（較小文件大小）"""
        
        constellation_animations = animation_data.get("constellation_animations", {})
        
        # 優化星座動畫數據
        optimized_constellations = {}
        
        for const_name, const_anim in constellation_animations.items():
            optimized_const = self._optimize_constellation_for_web(const_name, const_anim)
            optimized_constellations[const_name] = optimized_const
        
        # 精簡元數據
        compact_metadata = {
            "stage": 3,
            "stage_name": "timeseries_preprocessing",
            "format": "web_optimized",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_constellations": len(optimized_constellations),
            "optimization_applied": True
        }
        
        return {
            "format_version": "web_optimized_v1.0",
            "data": optimized_constellations,
            "metadata": compact_metadata,
            "validation_status": academic_validation.get("overall_compliance", "UNKNOWN")
        }
    
    def _format_research_grade_output(self,
                                    timeseries_data: Dict[str, Any],
                                    animation_data: Dict[str, Any],
                                    academic_validation: Dict[str, Any],
                                    processing_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """格式化研究級輸出（包含所有詳細信息）"""
        
        # 完整的數據保留
        research_output = {
            "format_version": "research_grade_v1.0",
            "academic_certification": academic_validation.get("academic_certification", {}),
            
            # 完整的原始數據
            "raw_data": {
                "timeseries_conversion_results": timeseries_data,
                "animation_build_results": animation_data,
                "academic_validation_report": academic_validation
            },
            
            # 研究用途的增強數據
            "research_data": {
                "constellation_analyses": self._generate_research_analyses(animation_data),
                "statistical_summaries": self._generate_statistical_summaries(timeseries_data),
                "methodology_documentation": self._generate_methodology_docs(processing_metadata)
            },
            
            # 完整元數據
            "comprehensive_metadata": {
                **processing_metadata,
                "research_compliance": {
                    "grade": academic_validation.get("overall_compliance", "UNKNOWN"),
                    "validation_level": academic_validation.get("validation_level", "UNKNOWN"),
                    "publication_ready": academic_validation.get("academic_certification", {}).get("publication_ready", False)
                },
                "data_provenance": self._generate_data_provenance(timeseries_data, processing_metadata)
            }
        }
        
        return research_output
    
    def _format_constellation_animation(self, const_name: str, const_anim: Dict[str, Any]) -> Dict[str, Any]:
        """格式化單個星座的動畫數據"""
        
        satellite_tracks = const_anim.get("satellite_tracks", [])
        
        # 格式化衛星軌跡
        formatted_satellites = []
        for track in satellite_tracks:
            formatted_satellite = {
                "id": track.get("satellite_id", "unknown"),
                "name": track.get("name", "unknown"),
                "constellation": track.get("constellation", const_name),
                
                # 動畫軌跡數據
                "trajectory": {
                    "keyframes": track.get("position_keyframes", []),
                    "total_frames": len(track.get("position_keyframes", [])),
                    "track_type": track.get("track_features", {}).get("track_type", "unknown")
                },
                
                # 可見性動畫
                "visibility": {
                    "keyframes": track.get("visibility_keyframes", []),
                    "peak_elevation": track.get("track_features", {}).get("peak_elevation", 0),
                    "peak_frame": track.get("track_features", {}).get("peak_frame", 0)
                },
                
                # 信號動畫（如果有）
                "signal": {
                    "keyframes": track.get("signal_keyframes", []),
                    "quality_profile": "unknown"
                },
                
                # 渲染配置
                "rendering": track.get("rendering_config", {})
            }
            
            formatted_satellites.append(formatted_satellite)
        
        # 星座級別的動畫特效
        constellation_effects = const_anim.get("constellation_effects", {})
        
        # 動畫時間軸
        animation_timeline = const_anim.get("animation_timeline", {})
        
        return {
            "constellation": const_name,
            "metadata": {
                "satellite_count": len(formatted_satellites),
                "total_frames": sum(s["trajectory"]["total_frames"] for s in formatted_satellites),
                "animation_duration_seconds": const_anim.get("metadata", {}).get("animation_duration_seconds", 0),
                "quality_level": const_anim.get("metadata", {}).get("quality_level", "unknown")
            },
            "satellites": formatted_satellites,
            "effects": {
                "coverage_visualization": constellation_effects.get("coverage_visualization", {}),
                "handover_animations": constellation_effects.get("handover_animations", {}),
                "constellation_statistics": constellation_effects.get("constellation_statistics", {})
            },
            "timeline": {
                "events": animation_timeline.get("timeline_events", []),
                "key_moments": animation_timeline.get("key_moments", []),
                "duration_frames": animation_timeline.get("total_duration_frames", 0)
            }
        }
    
    def _optimize_constellation_for_web(self, const_name: str, const_anim: Dict[str, Any]) -> Dict[str, Any]:
        """為Web優化星座動畫數據"""
        
        satellite_tracks = const_anim.get("satellite_tracks", [])
        
        # 精簡衛星數據
        optimized_satellites = []
        for track in satellite_tracks:
            # 保留關鍵信息，移除冗餘數據
            optimized_satellite = {
                "id": track.get("satellite_id", "unknown"),
                "name": track.get("name", "unknown"),
                
                # 精簡的軌跡數據
                "positions": self._compress_keyframes(track.get("position_keyframes", []), max_frames=100),
                "visibility": self._compress_keyframes(track.get("visibility_keyframes", []), max_frames=50),
                
                # 基本統計
                "stats": {
                    "peak_elevation": track.get("track_features", {}).get("peak_elevation", 0),
                    "visible_frames": len(track.get("visibility_keyframes", [])),
                    "track_type": track.get("track_features", {}).get("track_type", "unknown")
                }
            }
            
            optimized_satellites.append(optimized_satellite)
        
        return {
            "constellation": const_name,
            "satellite_count": len(optimized_satellites),
            "satellites": optimized_satellites,
            "optimized": True
        }
    
    def _compress_keyframes(self, keyframes: List[Dict[str, Any]], max_frames: int) -> List[Dict[str, Any]]:
        """壓縮關鍵幀數據"""
        
        if len(keyframes) <= max_frames:
            return keyframes
        
        # 智能抽取關鍵幀
        if len(keyframes) < 3:
            return keyframes
        
        compressed = []
        step = len(keyframes) // max_frames
        
        # 保留第一幀
        compressed.append(keyframes[0])
        
        # 按步長抽取中間幀
        for i in range(step, len(keyframes) - 1, step):
            compressed.append(keyframes[i])
        
        # 保留最後一幀
        if len(keyframes) > 1:
            compressed.append(keyframes[-1])
        
        return compressed
    
    def _generate_global_metadata(self, 
                                timeseries_data: Dict[str, Any],
                                animation_data: Dict[str, Any],
                                academic_validation: Dict[str, Any],
                                processing_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """生成全域元數據"""
        
        satellites_count = len(timeseries_data.get("satellites", []))
        constellations_count = len(animation_data.get("constellation_animations", {}))
        
        return {
            "stage": 3,
            "stage_name": "timeseries_preprocessing",
            "processor_version": "modular_v1.0",
            "processing_timestamp": datetime.now(timezone.utc).isoformat(),
            
            # 數據統計
            "data_statistics": {
                "total_satellites": satellites_count,
                "total_constellations": constellations_count,
                "total_animation_frames": self.formatting_statistics["animation_frames_total"]
            },
            
            # 處理配置
            "processing_config": {
                "time_resolution_seconds": timeseries_data.get("conversion_metadata", {}).get("time_resolution_seconds", 30),
                "animation_fps": timeseries_data.get("conversion_metadata", {}).get("animation_fps", 24),
                "output_format": self.output_format
            },
            
            # 學術合規性
            "academic_compliance": {
                "validation_level": academic_validation.get("validation_level", "UNKNOWN"),
                "overall_grade": academic_validation.get("overall_compliance", "UNKNOWN"),
                "publication_ready": academic_validation.get("academic_certification", {}).get("publication_ready", False)
            }
        }
    
    def _generate_animation_config(self, constellation_animations: Dict[str, Any]) -> Dict[str, Any]:
        """生成動畫配置"""
        
        total_frames = 0
        total_duration = 0
        
        for const_anim in constellation_animations.values():
            const_frames = const_anim.get("metadata", {}).get("total_frames", 0)
            const_duration = const_anim.get("metadata", {}).get("animation_duration_seconds", 0)
            
            total_frames = max(total_frames, const_frames)
            total_duration = max(total_duration, const_duration)
        
        return {
            "animation_duration_seconds": total_duration,
            "total_frames": total_frames,
            "recommended_fps": 24,
            "time_scale": "real_time",
            "coordinate_system": "WGS84",
            "projection": "mercator"
        }
    
    def _generate_rendering_hints(self, constellation_animations: Dict[str, Any]) -> Dict[str, Any]:
        """生成渲染提示"""
        
        total_satellites = sum(
            len(const_anim.get("satellite_tracks", [])) 
            for const_anim in constellation_animations.values()
        )
        
        return {
            "performance_level": "high" if total_satellites <= 50 else "medium",
            "rendering_strategy": "instanced" if total_satellites > 100 else "individual",
            "suggested_effects": ["trails", "coverage_areas", "signal_strength"],
            "optimization_hints": {
                "use_level_of_detail": total_satellites > 50,
                "enable_frustum_culling": True,
                "batch_rendering": total_satellites > 20
            }
        }
    
    def _compile_processing_statistics(self,
                                     timeseries_data: Dict[str, Any],
                                     animation_data: Dict[str, Any],
                                     processing_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """編譯處理統計信息"""
        
        return {
            "timeseries_conversion": timeseries_data.get("conversion_statistics", {}),
            "animation_building": animation_data.get("build_statistics", {}),
            "output_formatting": self.formatting_statistics.copy(),
            "total_processing_time": processing_metadata.get("total_processing_duration", 0)
        }
    
    def _summarize_academic_validation(self, academic_validation: Dict[str, Any]) -> Dict[str, Any]:
        """總結學術驗證結果"""
        
        return {
            "overall_grade": academic_validation.get("overall_compliance", "UNKNOWN"),
            "validation_passed": academic_validation.get("overall_compliance") in ["GRADE_A", "GRADE_B"],
            "critical_issues": len(academic_validation.get("critical_violations", [])),
            "recommendations_count": len(academic_validation.get("recommendations", []))
        }
    
    def _generate_integrity_summary(self, timeseries_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成數據完整性摘要"""
        
        satellites = timeseries_data.get("satellites", [])
        
        satellites_with_data = len([s for s in satellites if s.get("timeseries")])
        satellites_with_visibility = len([s for s in satellites if s.get("animation_trajectory", {}).get("visible_frames", 0) > 0])
        
        return {
            "data_completeness": round((satellites_with_data / len(satellites) * 100) if satellites else 0, 1),
            "visibility_coverage": round((satellites_with_visibility / len(satellites) * 100) if satellites else 0, 1),
            "integrity_score": "high" if satellites_with_data == len(satellites) else "medium"
        }
    
    def _calculate_animation_quality_metrics(self, constellation_animations: Dict[str, Any]) -> Dict[str, Any]:
        """計算動畫品質指標"""
        
        total_tracks = 0
        high_quality_tracks = 0
        total_visible_frames = 0
        
        for const_anim in constellation_animations.values():
            satellite_tracks = const_anim.get("satellite_tracks", [])
            total_tracks += len(satellite_tracks)
            
            for track in satellite_tracks:
                animation_quality = track.get("animation_metadata", {}).get("animation_quality", "unknown")
                visible_frames = track.get("animation_metadata", {}).get("visible_frame_count", 0)
                
                if animation_quality in ["excellent", "good"]:
                    high_quality_tracks += 1
                
                total_visible_frames += visible_frames
        
        return {
            "total_animation_tracks": total_tracks,
            "high_quality_tracks": high_quality_tracks,
            "quality_ratio": round((high_quality_tracks / total_tracks * 100) if total_tracks > 0 else 0, 1),
            "average_visible_frames": round(total_visible_frames / total_tracks if total_tracks > 0 else 0, 1),
            "overall_animation_quality": "high" if (high_quality_tracks / total_tracks) >= 0.7 else "medium" if (high_quality_tracks / total_tracks) >= 0.4 else "low"
        }
    
    def _generate_research_analyses(self, animation_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成研究用途的分析數據"""
        
        constellation_animations = animation_data.get("constellation_animations", {})
        
        analyses = {}
        
        for const_name, const_anim in constellation_animations.items():
            constellation_stats = const_anim.get("constellation_effects", {}).get("constellation_statistics", {})
            
            analyses[const_name] = {
                "coverage_analysis": {
                    "satellite_count": constellation_stats.get("satellite_count", 0),
                    "visibility_rate": constellation_stats.get("visibility_rate", 0),
                    "peak_elevations": {
                        "max_overall": constellation_stats.get("max_elevation_overall", 0),
                        "average_peak": constellation_stats.get("avg_peak_elevation", 0),
                        "high_elevation_satellites": constellation_stats.get("satellites_above_45deg", 0)
                    }
                },
                "temporal_analysis": {
                    "total_animation_frames": constellation_stats.get("total_animation_frames", 0),
                    "avg_frames_per_satellite": constellation_stats.get("avg_frames_per_satellite", 0)
                }
            }
        
        return analyses
    
    def _generate_statistical_summaries(self, timeseries_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成統計摘要"""
        
        conversion_stats = timeseries_data.get("conversion_statistics", {})
        
        return {
            "conversion_performance": {
                "total_processed": conversion_stats.get("total_satellites_processed", 0),
                "successful_conversions": conversion_stats.get("successful_conversions", 0),
                "success_rate": round((conversion_stats.get("successful_conversions", 0) / 
                                     max(1, conversion_stats.get("total_satellites_processed", 1))) * 100, 2)
            },
            "data_volume": {
                "total_timeseries_points": conversion_stats.get("total_timeseries_points", 0),
                "total_animation_frames": conversion_stats.get("total_animation_frames", 0)
            }
        }
    
    def _generate_methodology_docs(self, processing_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """生成方法學文檔"""
        
        return {
            "processing_pipeline": "modular_stage3_processor",
            "time_resolution": processing_metadata.get("time_resolution_seconds", 30),
            "coordinate_system": "WGS84",
            "signal_model": "friis_propagation_with_atmosphere",
            "academic_standards": "grade_a_compliant",
            "validation_framework": "comprehensive_academic_validation"
        }
    
    def _generate_data_provenance(self, timeseries_data: Dict[str, Any], 
                                processing_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """生成數據來源信息"""
        
        return {
            "data_source": "stage2_visibility_filter_output",
            "processing_stage": 3,
            "transformation_applied": [
                "visibility_to_timeseries_conversion",
                "animation_data_building",
                "academic_validation"
            ],
            "data_lineage": {
                "stage1": "orbital_calculation",
                "stage2": "visibility_filtering",
                "stage3": "timeseries_preprocessing"
            },
            "quality_assurance": "academic_grade_validation_applied"
        }
    
    def export_formatted_results(self, formatted_results: Dict[str, Any], 
                                output_dir: Path, file_prefix: str = "stage3") -> Dict[str, str]:
        """
        匯出格式化結果到文件
        
        Args:
            formatted_results: 格式化的結果數據
            output_dir: 輸出目錄
            file_prefix: 文件前綴
            
        Returns:
            Dict[str, str]: 生成的文件路徑
        """
        self.logger.info(f"📁 匯出格式化結果到 {output_dir}...")
        
        output_files = {}
        
        try:
            # 確保輸出目錄存在
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if self.output_format == "enhanced_animation":
                # 主動畫文件
                main_file = output_dir / f"{file_prefix}_enhanced_animation.json"
                with open(main_file, 'w', encoding='utf-8') as f:
                    json.dump(formatted_results, f, indent=2, ensure_ascii=False)
                output_files["main_animation"] = str(main_file)
                
                # 按星座分別導出
                animation_data = formatted_results.get("animation_data", {}).get("constellations", {})
                for const_name, const_data in animation_data.items():
                    const_file = output_dir / f"{file_prefix}_{const_name}_animation.json"
                    with open(const_file, 'w', encoding='utf-8') as f:
                        json.dump(const_data, f, indent=2, ensure_ascii=False)
                    output_files[f"{const_name}_animation"] = str(const_file)
            
            elif self.output_format == "web_optimized":
                # Web優化文件
                web_file = output_dir / f"{file_prefix}_web_optimized.json"
                with open(web_file, 'w', encoding='utf-8') as f:
                    json.dump(formatted_results, f, separators=(',', ':'), ensure_ascii=False)
                output_files["web_optimized"] = str(web_file)
            
            elif self.output_format == "research_grade":
                # 研究級文件
                research_file = output_dir / f"{file_prefix}_research_grade.json"
                with open(research_file, 'w', encoding='utf-8') as f:
                    json.dump(formatted_results, f, indent=2, ensure_ascii=False)
                output_files["research_grade"] = str(research_file)
            
            # 計算輸出文件總大小
            total_size = 0
            for file_path in output_files.values():
                file_size = Path(file_path).stat().st_size
                total_size += file_size
            
            self.formatting_statistics["files_generated"] = len(output_files)
            self.formatting_statistics["total_output_size_mb"] = total_size / (1024 * 1024)
            
            self.logger.info(f"✅ 格式化結果匯出成功: {len(output_files)} 個文件，總大小 {self.formatting_statistics['total_output_size_mb']:.2f}MB")
            
            return output_files
            
        except Exception as e:
            self.logger.error(f"匯出格式化結果時出錯: {e}")
            raise
    
    def get_formatting_statistics(self) -> Dict[str, Any]:
        """獲取格式化統計信息"""
        return self.formatting_statistics.copy()