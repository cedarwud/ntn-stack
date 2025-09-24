"""
存儲平衡分析器 - Stage 5模組化組件

職責：
1. 分析和優化混合存儲策略
2. 計算PostgreSQL和Volume存儲需求
3. 評估存儲平衡最優性
4. 提供存儲優化建議
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class StorageBalanceAnalyzer:
    """存儲平衡分析器 - 分析和優化混合存儲架構平衡"""
    
    def __init__(self):
        """初始化存儲平衡分析器"""
        self.logger = logging.getLogger(f"{__name__}.StorageBalanceAnalyzer")
        
        # 分析統計
        self.analysis_statistics = {
            "balance_analyses_performed": 0,
            "storage_calculations_completed": 0,
            "optimization_recommendations_generated": 0,
            "performance_assessments": 0
        }
        
        # 存儲類型特性配置
        self.storage_characteristics = {
            "postgresql": {
                "optimal_data_types": ["structured_metadata", "indexed_queries", "relational_data"],
                "performance_profile": {
                    "query_speed": "high",
                    "storage_efficiency": "medium",
                    "scalability": "high",
                    "maintenance_overhead": "medium"
                },
                "cost_factors": {
                    "storage_cost_per_gb": 0.10,  # USD
                    "query_cost_per_1000": 0.005,
                    "maintenance_cost_factor": 1.2
                }
            },
            "volume_storage": {
                "optimal_data_types": ["large_json_files", "timeseries_data", "bulk_data"],
                "performance_profile": {
                    "query_speed": "medium",
                    "storage_efficiency": "high", 
                    "scalability": "very_high",
                    "maintenance_overhead": "low"
                },
                "cost_factors": {
                    "storage_cost_per_gb": 0.023,  # USD
                    "access_cost_per_1000": 0.0004,
                    "maintenance_cost_factor": 0.3
                }
            }
        }
        
        self.logger.info("✅ 存儲平衡分析器初始化完成")
        self.logger.info("   支持PostgreSQL和Volume混合存儲分析")
    
    def analyze_storage_balance(self, 
                              integrated_satellites: List[Dict[str, Any]],
                              postgresql_data: Dict[str, Any],
                              volume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析存儲平衡
        
        Args:
            integrated_satellites: 整合的衛星數據
            postgresql_data: PostgreSQL存儲數據
            volume_data: Volume存儲數據
            
        Returns:
            存儲平衡分析結果
        """
        self.logger.info(f"⚖️ 開始存儲平衡分析 ({len(integrated_satellites)} 衛星)...")
        
        balance_analysis = {
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "total_satellites": len(integrated_satellites),
            "storage_requirements": {},
            "performance_analysis": {},
            "balance_assessment": {},
            "optimization_recommendations": [],
            "cost_analysis": {}
        }
        
        # 1. 計算存儲需求
        storage_requirements = self._calculate_storage_requirements(
            integrated_satellites, postgresql_data, volume_data
        )
        balance_analysis["storage_requirements"] = storage_requirements
        
        # 2. 分析查詢性能
        performance_analysis = self._analyze_query_performance(
            integrated_satellites, postgresql_data, volume_data
        )
        balance_analysis["performance_analysis"] = performance_analysis
        
        # 3. 評估存儲平衡最優性
        balance_assessment = self._assess_storage_optimality(
            storage_requirements, performance_analysis
        )
        balance_analysis["balance_assessment"] = balance_assessment
        
        # 4. 生成優化建議
        optimization_recommendations = self._generate_optimization_recommendations(
            balance_assessment, storage_requirements
        )
        balance_analysis["optimization_recommendations"] = optimization_recommendations
        
        # 5. 計算成本分析
        cost_analysis = self._calculate_cost_analysis(
            storage_requirements, performance_analysis
        )
        balance_analysis["cost_analysis"] = cost_analysis
        
        # 更新統計
        self.analysis_statistics["balance_analyses_performed"] += 1
        self.analysis_statistics["storage_calculations_completed"] += 1
        self.analysis_statistics["optimization_recommendations_generated"] += len(optimization_recommendations)
        self.analysis_statistics["performance_assessments"] += 1
        
        self.logger.info(f"✅ 存儲平衡分析完成 (平衡分數: {balance_assessment.get('overall_balance_score', 'N/A')})")
        
        return balance_analysis
    
    def _calculate_storage_requirements(self, 
                                      integrated_satellites: List[Dict[str, Any]],
                                      postgresql_data: Dict[str, Any],
                                      volume_data: Dict[str, Any]) -> Dict[str, Any]:
        """計算存儲需求"""
        self.logger.info("📊 計算存儲需求...")
        
        requirements = {
            "postgresql_requirements": self._calculate_postgresql_requirements(integrated_satellites, postgresql_data),
            "volume_requirements": self._calculate_volume_requirements(integrated_satellites, volume_data),
            "total_requirements": {},
            "storage_distribution": {}
        }
        
        # 計算總需求
        pg_size = requirements["postgresql_requirements"]["estimated_size_gb"]
        volume_size = requirements["volume_requirements"]["estimated_size_gb"]
        total_size = pg_size + volume_size
        
        requirements["total_requirements"] = {
            "total_storage_gb": total_size,
            "postgresql_percentage": (pg_size / total_size * 100) if total_size > 0 else 0,
            "volume_percentage": (volume_size / total_size * 100) if total_size > 0 else 0
        }
        
        # 存儲分布分析
        requirements["storage_distribution"] = {
            "structured_data_gb": pg_size,
            "unstructured_data_gb": volume_size,
            "distribution_balance": "optimal" if 20 <= (pg_size / total_size * 100) <= 40 else "suboptimal" if total_size > 0 else "unknown"
        }
        
        return requirements
    
    def _calculate_postgresql_requirements(self, 
                                         integrated_satellites: List[Dict[str, Any]], 
                                         postgresql_data: Dict[str, Any]) -> Dict[str, Any]:
        """計算PostgreSQL存儲需求"""
        satellites_count = len(integrated_satellites)
        
        # 估算表大小 (bytes per row)
        table_estimates = {
            "satellite_metadata": 500,      # 每行500字節
            "signal_statistics": 200,       # 每行200字節  
            "handover_events": 300,         # 每行300字節
            "processing_summary": 1000      # 每行1000字節
        }
        
        # 計算數據量
        estimated_rows = {
            "satellite_metadata": satellites_count,
            "signal_statistics": satellites_count,
            "handover_events": satellites_count * 5,  # 每衛星5個事件
            "processing_summary": max(1, satellites_count // 1000)  # 每1000衛星1個摘要
        }
        
        total_bytes = 0
        table_sizes = {}
        
        for table, bytes_per_row in table_estimates.items():
            rows = estimated_rows.get(table, 0)
            size_bytes = rows * bytes_per_row
            size_mb = size_bytes / (1024 * 1024)
            
            table_sizes[table] = {
                "estimated_rows": rows,
                "size_bytes": size_bytes,
                "size_mb": size_mb
            }
            
            total_bytes += size_bytes
        
        # 添加索引開銷 (約30%)
        index_overhead = total_bytes * 0.3
        total_with_indexes = total_bytes + index_overhead
        
        return {
            "estimated_size_bytes": int(total_with_indexes),
            "estimated_size_gb": total_with_indexes / (1024 ** 3),
            "table_breakdown": table_sizes,
            "index_overhead_bytes": int(index_overhead),
            "optimization_potential": {
                "compression_savings": "15-25%",
                "partition_benefits": "high" if satellites_count > 10000 else "medium"
            }
        }
    
    def _calculate_volume_requirements(self, 
                                     integrated_satellites: List[Dict[str, Any]], 
                                     volume_data: Dict[str, Any]) -> Dict[str, Any]:
        """計算Volume存儲需求"""
        satellites_count = len(integrated_satellites)
        
        # 估算每衛星的JSON數據大小
        data_size_estimates = {
            "stage1_orbital": 2048,         # 2KB per satellite
            "stage2_visibility": 5120,      # 5KB per satellite  
            "stage3_timeseries": 20480,     # 20KB per satellite
            "stage4_signal_analysis": 8192, # 8KB per satellite
            "layered_data": 4096,           # 4KB per satellite
            "handover_scenarios": 6144      # 6KB per satellite
        }
        
        total_bytes = 0
        file_breakdown = {}
        
        for data_type, bytes_per_satellite in data_size_estimates.items():
            total_size = satellites_count * bytes_per_satellite
            size_mb = total_size / (1024 * 1024)
            
            file_breakdown[data_type] = {
                "satellites": satellites_count,
                "size_bytes": total_size,
                "size_mb": size_mb
            }
            
            total_bytes += total_size
        
        return {
            "estimated_size_bytes": total_bytes,
            "estimated_size_gb": total_bytes / (1024 ** 3),
            "file_breakdown": file_breakdown,
            "compression_potential": {
                "json_compression_ratio": "3:1",
                "gzip_savings": "60-70%",
                "estimated_compressed_gb": (total_bytes / (1024 ** 3)) * 0.35
            }
        }
    
    def _analyze_query_performance(self, 
                                 integrated_satellites: List[Dict[str, Any]],
                                 postgresql_data: Dict[str, Any],
                                 volume_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析查詢性能"""
        self.logger.info("⚡ 分析查詢性能...")
        
        satellites_count = len(integrated_satellites)
        
        performance_analysis = {
            "postgresql_performance": self._assess_postgresql_performance(satellites_count),
            "volume_performance": self._assess_volume_performance(satellites_count),
            "comparative_analysis": {},
            "bottleneck_identification": []
        }
        
        # 比較分析
        pg_perf = performance_analysis["postgresql_performance"]
        vol_perf = performance_analysis["volume_performance"]
        
        performance_analysis["comparative_analysis"] = {
            "structured_queries": {
                "postgresql_advantage": pg_perf["structured_query_ms"] < vol_perf["structured_query_ms"],
                "performance_ratio": vol_perf["structured_query_ms"] / pg_perf["structured_query_ms"]
            },
            "bulk_data_access": {
                "volume_advantage": vol_perf["bulk_access_ms"] < pg_perf["bulk_access_ms"],
                "performance_ratio": pg_perf["bulk_access_ms"] / vol_perf["bulk_access_ms"]
            },
            "scalability": {
                "postgresql_scalability_score": pg_perf["scalability_score"],
                "volume_scalability_score": vol_perf["scalability_score"],
                "better_scalability": "volume" if vol_perf["scalability_score"] > pg_perf["scalability_score"] else "postgresql"
            }
        }
        
        # 瓶頸識別
        bottlenecks = []
        if pg_perf["structured_query_ms"] > 1000:
            bottlenecks.append("PostgreSQL索引優化需求")
        
        if vol_perf["bulk_access_ms"] > 5000:
            bottlenecks.append("Volume存儲I/O優化需求")
        
        if satellites_count > 50000:
            bottlenecks.append("大規模數據分區策略")
        
        performance_analysis["bottleneck_identification"] = bottlenecks
        
        return performance_analysis
    
    def _assess_postgresql_performance(self, satellites_count: int) -> Dict[str, Any]:
        """評估PostgreSQL性能"""
        # 基於數據量的性能模型
        base_query_time = 50  # ms
        scaling_factor = max(1, satellites_count / 10000)
        
        return {
            "structured_query_ms": base_query_time * scaling_factor,
            "index_query_ms": 25 * scaling_factor,
            "bulk_access_ms": 200 * scaling_factor,
            "concurrent_connections": min(100, satellites_count // 100),
            "scalability_score": max(50, 100 - (scaling_factor - 1) * 20),
            "memory_efficiency": "high" if satellites_count < 100000 else "medium",
            "query_optimization_potential": "high"
        }
    
    def _assess_volume_performance(self, satellites_count: int) -> Dict[str, Any]:
        """評估Volume存儲性能"""
        base_access_time = 100  # ms
        scaling_factor = max(1, satellites_count / 100000)  # Volume擴展性更好
        
        return {
            "structured_query_ms": 500 * scaling_factor,  # 結構化查詢較慢
            "bulk_access_ms": base_access_time * scaling_factor,
            "file_streaming_ms": 50 * scaling_factor,
            "concurrent_access": min(1000, satellites_count // 10),
            "scalability_score": min(100, 80 + (100000 / max(satellites_count, 1000)) * 0.2),
            "storage_efficiency": "very_high",
            "compression_benefit": "high"
        }
    
    def _assess_storage_optimality(self, 
                                 storage_requirements: Dict[str, Any], 
                                 performance_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """評估存儲平衡最優性"""
        self.logger.info("🎯 評估存儲最優性...")
        
        total_req = storage_requirements["total_requirements"]
        pg_percentage = total_req["postgresql_percentage"]
        volume_percentage = total_req["volume_percentage"]
        
        # 平衡分數計算 (0-100)
        balance_factors = []
        
        # 1. 存儲分布平衡 (30% 權重)
        if 20 <= pg_percentage <= 40:
            distribution_score = 100
        elif 15 <= pg_percentage <= 45:
            distribution_score = 80
        elif 10 <= pg_percentage <= 50:
            distribution_score = 60
        else:
            distribution_score = 40
        
        balance_factors.append(("storage_distribution", distribution_score, 0.3))
        
        # 2. 性能匹配 (25% 權重)
        comp_analysis = performance_analysis["comparative_analysis"]
        performance_score = 0
        
        if comp_analysis["structured_queries"]["postgresql_advantage"]:
            performance_score += 50
        
        if comp_analysis["bulk_data_access"]["volume_advantage"]:
            performance_score += 50
        
        balance_factors.append(("performance_matching", performance_score, 0.25))
        
        # 3. 可擴展性 (20% 權重)
        pg_scalability = performance_analysis["postgresql_performance"]["scalability_score"]
        vol_scalability = performance_analysis["volume_performance"]["scalability_score"]
        avg_scalability = (pg_scalability + vol_scalability) / 2
        
        balance_factors.append(("scalability", avg_scalability, 0.20))
        
        # 4. 成本效益 (15% 權重)
        cost_efficiency_score = self._estimate_cost_efficiency(storage_requirements)
        balance_factors.append(("cost_efficiency", cost_efficiency_score, 0.15))
        
        # 5. 維護複雜度 (10% 權重)
        maintenance_score = self._assess_maintenance_complexity(storage_requirements)
        balance_factors.append(("maintenance_complexity", maintenance_score, 0.10))
        
        # 計算整體平衡分數
        overall_score = sum(score * weight for _, score, weight in balance_factors)
        
        # 分級評估
        if overall_score >= 85:
            balance_grade = "Excellent"
            recommendation = "當前存儲配置已達到最優平衡"
        elif overall_score >= 75:
            balance_grade = "Good"
            recommendation = "存儲配置良好，有少量優化空間"
        elif overall_score >= 65:
            balance_grade = "Fair"
            recommendation = "存儲配置可接受，建議進行優化"
        else:
            balance_grade = "Poor"
            recommendation = "存儲配置需要重大調整"
        
        return {
            "overall_balance_score": round(overall_score, 2),
            "balance_grade": balance_grade,
            "recommendation": recommendation,
            "balance_factors": {name: score for name, score, _ in balance_factors},
            "optimization_priority": self._identify_optimization_priorities(balance_factors)
        }
    
    def _estimate_cost_efficiency(self, storage_requirements: Dict[str, Any]) -> float:
        """估算成本效益"""
        pg_req = storage_requirements["postgresql_requirements"]
        vol_req = storage_requirements["volume_requirements"]
        
        # 計算月度成本
        pg_cost = (pg_req["estimated_size_gb"] * 
                  self.storage_characteristics["postgresql"]["cost_factors"]["storage_cost_per_gb"])
        
        vol_cost = (vol_req["estimated_size_gb"] * 
                   self.storage_characteristics["volume_storage"]["cost_factors"]["storage_cost_per_gb"])
        
        total_cost = pg_cost + vol_cost
        total_storage = pg_req["estimated_size_gb"] + vol_req["estimated_size_gb"]
        
        # 成本效益分數 (基於每GB成本)
        if total_storage > 0:
            cost_per_gb = total_cost / total_storage
            
            # 評分標準 (USD per GB per month)
            if cost_per_gb <= 0.05:
                return 100
            elif cost_per_gb <= 0.08:
                return 80
            elif cost_per_gb <= 0.12:
                return 60
            else:
                return 40
        
        return 70  # 預設分數
    
    def _assess_maintenance_complexity(self, storage_requirements: Dict[str, Any]) -> float:
        """評估維護複雜度"""
        # 簡化的維護複雜度評估
        pg_tables = len(storage_requirements["postgresql_requirements"]["table_breakdown"])
        total_storage = storage_requirements["total_requirements"]["total_storage_gb"]
        
        # 基於表數量和存儲大小的複雜度
        complexity_factors = []
        
        # 表數量因子
        if pg_tables <= 5:
            table_score = 100
        elif pg_tables <= 10:
            table_score = 80
        else:
            table_score = 60
        
        complexity_factors.append(table_score * 0.4)
        
        # 存儲大小因子
        if total_storage <= 10:
            size_score = 100
        elif total_storage <= 100:
            size_score = 85
        elif total_storage <= 1000:
            size_score = 70
        else:
            size_score = 55
        
        complexity_factors.append(size_score * 0.6)
        
        return sum(complexity_factors)
    
    def _identify_optimization_priorities(self, balance_factors: List[Tuple[str, float, float]]) -> List[str]:
        """識別優化優先級"""
        priorities = []
        
        for name, score, weight in balance_factors:
            if score < 70:  # 需要改善的因子
                importance = weight * (70 - score)  # 權重 × 改善空間
                priorities.append((name, importance))
        
        # 按重要性排序
        priorities.sort(key=lambda x: x[1], reverse=True)
        
        return [name for name, _ in priorities[:3]]  # 返回前3個優先級
    
    def _generate_optimization_recommendations(self, 
                                             balance_assessment: Dict[str, Any], 
                                             storage_requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成優化建議"""
        self.logger.info("💡 生成存儲優化建議...")
        
        recommendations = []
        balance_score = balance_assessment["overall_balance_score"]
        priorities = balance_assessment["optimization_priority"]
        
        # 基於優先級生成具體建議
        for priority in priorities:
            if priority == "storage_distribution":
                recommendations.append({
                    "category": "存儲分布優化",
                    "priority": "high",
                    "recommendation": "調整PostgreSQL和Volume存儲的數據分布比例",
                    "specific_actions": [
                        "將時間序列數據遷移至Volume存儲",
                        "保留索引查詢數據在PostgreSQL",
                        "實施智能數據分層策略"
                    ],
                    "expected_improvement": "15-25%"
                })
            
            elif priority == "performance_matching":
                recommendations.append({
                    "category": "性能匹配優化", 
                    "priority": "medium",
                    "recommendation": "優化查詢路由以匹配存儲特性",
                    "specific_actions": [
                        "結構化查詢導向PostgreSQL",
                        "批量數據訪問導向Volume存儲",
                        "實施智能查詢路由器"
                    ],
                    "expected_improvement": "20-30%"
                })
            
            elif priority == "scalability":
                recommendations.append({
                    "category": "可擴展性優化",
                    "priority": "medium",
                    "recommendation": "實施分區和分片策略",
                    "specific_actions": [
                        "PostgreSQL表分區(按星座或時間)",
                        "Volume存儲階層化組織",
                        "實施自動擴展機制"
                    ],
                    "expected_improvement": "40-60%"
                })
        
        # 通用優化建議
        if balance_score < 75:
            recommendations.append({
                "category": "通用優化",
                "priority": "low",
                "recommendation": "實施存儲監控和自動化管理",
                "specific_actions": [
                    "部署存儲使用監控",
                    "設置自動備份策略",
                    "實施成本優化警報"
                ],
                "expected_improvement": "10-20%"
            })
        
        return recommendations
    
    def _calculate_cost_analysis(self, 
                               storage_requirements: Dict[str, Any], 
                               performance_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """計算成本分析"""
        self.logger.info("💰 計算成本分析...")
        
        pg_req = storage_requirements["postgresql_requirements"]
        vol_req = storage_requirements["volume_requirements"]
        
        # PostgreSQL成本
        pg_storage_cost = (pg_req["estimated_size_gb"] * 
                          self.storage_characteristics["postgresql"]["cost_factors"]["storage_cost_per_gb"])
        
        pg_query_cost = (1000 * 
                        self.storage_characteristics["postgresql"]["cost_factors"]["query_cost_per_1000"])
        
        pg_maintenance_cost = (pg_storage_cost * 
                              self.storage_characteristics["postgresql"]["cost_factors"]["maintenance_cost_factor"])
        
        pg_total_cost = pg_storage_cost + pg_query_cost + pg_maintenance_cost
        
        # Volume存儲成本
        vol_storage_cost = (vol_req["estimated_size_gb"] * 
                           self.storage_characteristics["volume_storage"]["cost_factors"]["storage_cost_per_gb"])
        
        vol_access_cost = (1000 * 
                          self.storage_characteristics["volume_storage"]["cost_factors"]["access_cost_per_1000"])
        
        vol_maintenance_cost = (vol_storage_cost * 
                               self.storage_characteristics["volume_storage"]["cost_factors"]["maintenance_cost_factor"])
        
        vol_total_cost = vol_storage_cost + vol_access_cost + vol_maintenance_cost
        
        total_monthly_cost = pg_total_cost + vol_total_cost
        
        return {
            "monthly_costs": {
                "postgresql": {
                    "storage_cost": round(pg_storage_cost, 2),
                    "query_cost": round(pg_query_cost, 2), 
                    "maintenance_cost": round(pg_maintenance_cost, 2),
                    "total_cost": round(pg_total_cost, 2)
                },
                "volume_storage": {
                    "storage_cost": round(vol_storage_cost, 2),
                    "access_cost": round(vol_access_cost, 2),
                    "maintenance_cost": round(vol_maintenance_cost, 2),
                    "total_cost": round(vol_total_cost, 2)
                },
                "total_monthly_cost": round(total_monthly_cost, 2)
            },
            "cost_efficiency": {
                "cost_per_satellite": round(total_monthly_cost / max(storage_requirements.get("total_satellites", 1), 1), 4),
                "cost_per_gb": round(total_monthly_cost / max(storage_requirements["total_requirements"]["total_storage_gb"], 1), 2),
                "postgresql_percentage": round((pg_total_cost / total_monthly_cost * 100), 1) if total_monthly_cost > 0 else 0,
                "volume_percentage": round((vol_total_cost / total_monthly_cost * 100), 1) if total_monthly_cost > 0 else 0
            },
            "cost_optimization_potential": {
                "compression_savings": round(vol_storage_cost * 0.65, 2),
                "query_optimization_savings": round(pg_query_cost * 0.3, 2),
                "total_potential_savings": round((vol_storage_cost * 0.65) + (pg_query_cost * 0.3), 2)
            }
        }
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """獲取分析統計信息"""
        return self.analysis_statistics.copy()