"""
Sionna 與干擾控制服務整合模組
實現階段四：Sionna 無線通道與 AI-RAN 抗干擾整合
"""

import asyncio
import json
import time
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import aiohttp
import structlog

logger = structlog.get_logger(__name__)


class SionnaInterferenceIntegration:
    """Sionna 與干擾控制整合服務"""

    def __init__(
        self,
        simworld_api_url: str = "http://simworld-backend:8000",
        netstack_api_url: str = "http://netstack-api:8080",
        update_interval_ms: float = 100,  # 100ms 更新間隔
    ):
        self.simworld_api_url = simworld_api_url
        self.netstack_api_url = netstack_api_url
        self.update_interval_ms = update_interval_ms
        
        self.logger = logger.bind(service="sionna_interference_integration")
        
        # 狀態管理
        self.active_integrations: Dict[str, Dict] = {}
        self.channel_cache: Dict[str, Dict] = {}
        self.last_sionna_update: Optional[datetime] = None
        
        # 性能統計
        self.integration_stats = {
            "total_integrations": 0,
            "successful_integrations": 0,
            "failed_integrations": 0,
            "avg_response_time_ms": 0.0,
            "sionna_updates": 0,
            "ai_decisions": 0,
        }
        
        # HTTP 客戶端
        self.http_session: Optional[aiohttp.ClientSession] = None

    async def start(self):
        """啟動整合服務"""
        try:
            self.logger.info("🚀 啟動 Sionna-干擾控制整合服務...")
            
            # 創建 HTTP 客戶端
            self.http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            self.logger.info("✅ Sionna-干擾控制整合服務已啟動")
            
        except Exception as e:
            self.logger.error("❌ 整合服務啟動失敗", error=str(e))
            raise

    async def stop(self):
        """停止整合服務"""
        try:
            self.logger.info("🛑 停止 Sionna-干擾控制整合服務...")
            
            # 關閉 HTTP 客戶端
            if self.http_session:
                await self.http_session.close()
                
            self.logger.info("✅ Sionna-干擾控制整合服務已停止")
            
        except Exception as e:
            self.logger.error("❌ 停止整合服務失敗", error=str(e))

    async def integrated_interference_detection_and_mitigation(
        self,
        scenario_id: str,
        ue_positions: List[Dict[str, float]],
        gnb_positions: List[Dict[str, float]],
        interference_sources: Optional[List[Dict]] = None,
        frequency_mhz: float = 2150.0,
        bandwidth_mhz: float = 20.0,
    ) -> Dict[str, Any]:
        """整合的干擾檢測和緩解"""
        
        integration_start_time = time.time()
        integration_id = f"int_{scenario_id}_{int(time.time() * 1000)}"
        
        try:
            self.logger.info(
                "開始整合檢測和緩解", 
                integration_id=integration_id,
                scenario_id=scenario_id
            )

            # 階段 1：並行請求 Sionna 通道模擬和干擾檢測
            sionna_task = asyncio.create_task(
                self._request_sionna_channel_simulation(
                    ue_positions, gnb_positions, interference_sources, frequency_mhz, bandwidth_mhz
                )
            )
            
            interference_task = asyncio.create_task(
                self._request_interference_detection(
                    ue_positions, interference_sources, frequency_mhz, bandwidth_mhz
                )
            )

            # 等待兩個任務完成
            sionna_data, interference_data = await asyncio.gather(
                sionna_task, interference_task, return_exceptions=True
            )

            # 處理異常
            if isinstance(sionna_data, Exception):
                self.logger.error(f"Sionna 通道模擬失敗: {sionna_data}")
                sionna_data = None
                
            if isinstance(interference_data, Exception):
                self.logger.error(f"干擾檢測失敗: {interference_data}")
                interference_data = None

            # 階段 2：融合數據並分析
            integrated_analysis = await self._fuse_sionna_and_interference_data(
                sionna_data, interference_data, scenario_id
            )

            # 階段 3：AI-RAN 決策
            ai_decision = await self._request_enhanced_ai_decision(
                integrated_analysis, ue_positions, gnb_positions
            )

            # 階段 4：應用緩解措施到 UERANSIM
            mitigation_result = await self._apply_integrated_mitigation(
                ai_decision, integrated_analysis, scenario_id
            )

            # 階段 5：生成詳細結果
            integration_time_ms = (time.time() - integration_start_time) * 1000
            
            result = {
                "integration_id": integration_id,
                "scenario_id": scenario_id,
                "success": True,
                "integration_time_ms": integration_time_ms,
                "timestamp": datetime.utcnow().isoformat(),
                
                # 原始數據
                "sionna_data": sionna_data,
                "interference_data": interference_data,
                
                # 融合分析
                "integrated_analysis": integrated_analysis,
                
                # AI 決策
                "ai_decision": ai_decision,
                
                # 緩解結果
                "mitigation_result": mitigation_result,
                
                # 性能指標
                "performance_metrics": {
                    "channel_quality_improvement": self._calculate_channel_improvement(
                        integrated_analysis, mitigation_result
                    ),
                    "interference_reduction_db": self._calculate_interference_reduction(
                        integrated_analysis, mitigation_result
                    ),
                    "estimated_throughput_improvement": self._estimate_throughput_improvement(
                        integrated_analysis, ai_decision
                    ),
                },
                
                # 系統狀態
                "system_status": {
                    "sionna_available": sionna_data is not None,
                    "interference_detector_available": interference_data is not None,
                    "ai_decision_confidence": ai_decision.get("confidence", 0.0) if ai_decision else 0.0,
                    "mitigation_applied": mitigation_result.get("success", False) if mitigation_result else False,
                }
            }

            # 更新統計
            self.integration_stats["total_integrations"] += 1
            self.integration_stats["successful_integrations"] += 1
            self._update_avg_response_time(integration_time_ms)

            # 緩存結果
            self.active_integrations[integration_id] = result

            return result

        except Exception as e:
            self.logger.error("整合檢測和緩解失敗", error=str(e))
            
            self.integration_stats["total_integrations"] += 1
            self.integration_stats["failed_integrations"] += 1
            
            return {
                "integration_id": integration_id,
                "scenario_id": scenario_id,
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _request_sionna_channel_simulation(
        self, 
        ue_positions: List[Dict], 
        gnb_positions: List[Dict],
        interference_sources: Optional[List[Dict]],
        frequency_mhz: float,
        bandwidth_mhz: float
    ) -> Optional[Dict]:
        """請求 Sionna 通道模擬"""
        
        try:
            simulation_request = {
                "simulation_type": "real_time_channel_with_interference",
                "ue_positions": ue_positions,
                "gnb_positions": gnb_positions,
                "interference_sources": interference_sources or [],
                "carrier_frequency_hz": frequency_mhz * 1e6,
                "bandwidth_hz": bandwidth_mhz * 1e6,
                "simulation_params": {
                    "enable_fast_fading": True,
                    "enable_shadowing": True,
                    "enable_path_loss": True,
                    "doppler_enabled": True,
                    "enable_interference_modeling": len(interference_sources or []) > 0,
                    "output_detailed_metrics": True,
                    "real_time_mode": True,
                },
                "analysis_params": {
                    "calculate_sinr": True,
                    "calculate_capacity": True,
                    "analyze_interference_impact": True,
                    "generate_channel_predictions": True,
                }
            }

            async with self.http_session.post(
                f"{self.simworld_api_url}/api/v1/wireless/sionna-integrated-simulation",
                json=simulation_request,
                timeout=aiohttp.ClientTimeout(total=2.0),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.integration_stats["sionna_updates"] += 1
                    self.last_sionna_update = datetime.utcnow()
                    return data
                else:
                    self.logger.warning(f"Sionna API 響應異常: {response.status}")
                    return None

        except Exception as e:
            self.logger.error(f"Sionna 通道模擬請求失敗: {e}")
            return None

    async def _request_interference_detection(
        self, 
        victim_positions: List[Dict],
        interference_sources: Optional[List[Dict]],
        frequency_mhz: float,
        bandwidth_mhz: float
    ) -> Optional[Dict]:
        """請求干擾檢測"""
        
        try:
            detection_request = {
                "victim_positions": victim_positions,
                "interference_sources": interference_sources or [],
                "frequency_mhz": frequency_mhz,
                "bandwidth_mhz": bandwidth_mhz,
                "detection_params": {
                    "enable_spectral_analysis": True,
                    "enable_pattern_recognition": True,
                    "enable_ml_classification": True,
                    "real_time_mode": True,
                },
                "analysis_depth": "comprehensive",
            }

            async with self.http_session.post(
                f"{self.simworld_api_url}/api/v1/interference/enhanced-detect",
                json=detection_request,
                timeout=aiohttp.ClientTimeout(total=1.5),
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.warning(f"干擾檢測 API 響應異常: {response.status}")
                    return None

        except Exception as e:
            self.logger.error(f"干擾檢測請求失敗: {e}")
            return None

    async def _fuse_sionna_and_interference_data(
        self, 
        sionna_data: Optional[Dict], 
        interference_data: Optional[Dict],
        scenario_id: str
    ) -> Dict[str, Any]:
        """融合 Sionna 和干擾檢測數據"""
        
        try:
            fused_analysis = {
                "scenario_id": scenario_id,
                "fusion_timestamp": datetime.utcnow().isoformat(),
                "data_sources": [],
                "channel_metrics": {},
                "interference_metrics": {},
                "integrated_assessment": {},
                "recommendations": [],
            }

            # 處理 Sionna 數據
            if sionna_data:
                fused_analysis["data_sources"].append("sionna_channel_model")
                
                channel_metrics = sionna_data.get("channel_metrics", {})
                fused_analysis["channel_metrics"] = {
                    "average_sinr_db": channel_metrics.get("average_sinr_db", 0),
                    "average_rsrp_dbm": channel_metrics.get("average_rsrp_dbm", -100),
                    "channel_capacity_bps": channel_metrics.get("channel_capacity_bps", 0),
                    "path_loss_db": channel_metrics.get("path_loss_db", 0),
                    "doppler_shift_hz": channel_metrics.get("doppler_shift_hz", 0),
                    "delay_spread_ns": channel_metrics.get("delay_spread_ns", 0),
                    "coherence_bandwidth_hz": channel_metrics.get("coherence_bandwidth_hz", 0),
                    "fading_variance": channel_metrics.get("fading_variance", 0),
                }

            # 處理干擾檢測數據
            if interference_data:
                fused_analysis["data_sources"].append("interference_detector")
                
                fused_analysis["interference_metrics"] = {
                    "interference_detected": interference_data.get("interference_detected", False),
                    "interference_level_db": interference_data.get("interference_level_db", -120),
                    "interference_type": interference_data.get("interference_type", "unknown"),
                    "affected_bandwidth_hz": interference_data.get("affected_bandwidth_hz", 0),
                    "interference_sources_count": len(interference_data.get("interference_sources", [])),
                    "confidence_score": interference_data.get("confidence_score", 0.0),
                    "spectral_efficiency_impact": interference_data.get("spectral_efficiency_impact", 0.0),
                }

            # 進行融合分析
            fused_analysis["integrated_assessment"] = self._perform_integrated_analysis(
                fused_analysis["channel_metrics"], 
                fused_analysis["interference_metrics"]
            )

            # 生成建議
            fused_analysis["recommendations"] = self._generate_fusion_recommendations(
                fused_analysis["integrated_assessment"]
            )

            return fused_analysis

        except Exception as e:
            self.logger.error(f"數據融合失敗: {e}")
            return {
                "scenario_id": scenario_id,
                "fusion_timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "data_sources": [],
            }

    def _perform_integrated_analysis(
        self, channel_metrics: Dict, interference_metrics: Dict
    ) -> Dict[str, Any]:
        """執行綜合分析"""
        
        try:
            # 計算綜合 SINR
            channel_sinr = channel_metrics.get("average_sinr_db", 0)
            interference_level = interference_metrics.get("interference_level_db", -120)
            
            # 干擾對 SINR 的影響
            sinr_degradation = max(0, 15 - channel_sinr) if interference_metrics.get("interference_detected") else 0
            
            # 綜合質量評分 (0-100)
            quality_score = self._calculate_quality_score(channel_metrics, interference_metrics)
            
            # 性能預測
            predicted_throughput = self._predict_throughput(channel_metrics, interference_metrics)
            
            # 緊急程度評估
            urgency_level = self._assess_urgency_level(channel_metrics, interference_metrics)
            
            return {
                "overall_sinr_db": channel_sinr - sinr_degradation,
                "sinr_degradation_db": sinr_degradation,
                "quality_score": quality_score,
                "predicted_throughput_mbps": predicted_throughput,
                "urgency_level": urgency_level,
                "interference_severity": self._classify_interference_severity(interference_metrics),
                "channel_conditions": self._classify_channel_conditions(channel_metrics),
                "mitigation_priority": self._determine_mitigation_priority(quality_score, urgency_level),
                "estimated_user_impact": self._estimate_user_impact(quality_score, predicted_throughput),
            }
            
        except Exception as e:
            self.logger.error(f"綜合分析失敗: {e}")
            return {"error": str(e)}

    def _calculate_quality_score(self, channel_metrics: Dict, interference_metrics: Dict) -> float:
        """計算綜合質量評分"""
        try:
            sinr_score = min(100, max(0, (channel_metrics.get("average_sinr_db", 0) + 10) * 3))
            capacity_score = min(100, channel_metrics.get("channel_capacity_bps", 0) / 1e8 * 100)
            
            interference_penalty = 0
            if interference_metrics.get("interference_detected"):
                interference_level = interference_metrics.get("interference_level_db", -120)
                interference_penalty = max(0, (interference_level + 100) * 2)
            
            quality_score = (sinr_score * 0.4 + capacity_score * 0.4 - interference_penalty * 0.2)
            return max(0, min(100, quality_score))
        except:
            return 50.0  # 默認中等質量

    def _predict_throughput(self, channel_metrics: Dict, interference_metrics: Dict) -> float:
        """預測吞吐量"""
        try:
            # Shannon 定理：C = B * log2(1 + SINR)
            bandwidth_hz = channel_metrics.get("coherence_bandwidth_hz", 20e6)
            sinr_db = channel_metrics.get("average_sinr_db", 10)
            sinr_linear = 10 ** (sinr_db / 10)
            
            # 考慮干擾影響
            if interference_metrics.get("interference_detected"):
                sinr_linear *= (1 - interference_metrics.get("spectral_efficiency_impact", 0.1))
            
            capacity_bps = bandwidth_hz * np.log2(1 + sinr_linear)
            return float(capacity_bps / 1e6)  # Mbps
        except:
            return 0.0

    def _assess_urgency_level(self, channel_metrics: Dict, interference_metrics: Dict) -> str:
        """評估緊急程度"""
        try:
            sinr_db = channel_metrics.get("average_sinr_db", 0)
            interference_detected = interference_metrics.get("interference_detected", False)
            interference_level = interference_metrics.get("interference_level_db", -120)
            
            if interference_detected and interference_level > -70:
                return "critical"
            elif sinr_db < 0 or (interference_detected and interference_level > -85):
                return "high"
            elif sinr_db < 10 or (interference_detected and interference_level > -100):
                return "medium"
            else:
                return "low"
        except:
            return "unknown"

    def _classify_interference_severity(self, interference_metrics: Dict) -> str:
        """分類干擾嚴重程度"""
        try:
            if not interference_metrics.get("interference_detected"):
                return "none"
            
            level_db = interference_metrics.get("interference_level_db", -120)
            if level_db > -70:
                return "severe"
            elif level_db > -85:
                return "moderate"
            else:
                return "mild"
        except:
            return "unknown"

    def _classify_channel_conditions(self, channel_metrics: Dict) -> str:
        """分類通道條件"""
        try:
            sinr_db = channel_metrics.get("average_sinr_db", 0)
            if sinr_db > 20:
                return "excellent"
            elif sinr_db > 10:
                return "good"
            elif sinr_db > 0:
                return "fair"
            else:
                return "poor"
        except:
            return "unknown"

    def _determine_mitigation_priority(self, quality_score: float, urgency_level: str) -> int:
        """確定緩解優先級 (1-10)"""
        urgency_scores = {"critical": 10, "high": 8, "medium": 5, "low": 2, "unknown": 3}
        urgency_score = urgency_scores.get(urgency_level, 3)
        
        quality_factor = 1.0 - (quality_score / 100.0)
        return min(10, max(1, int(urgency_score * (1 + quality_factor))))

    def _estimate_user_impact(self, quality_score: float, predicted_throughput: float) -> str:
        """估計用戶影響"""
        try:
            if quality_score > 80 and predicted_throughput > 50:
                return "minimal"
            elif quality_score > 60 and predicted_throughput > 20:
                return "moderate"
            elif quality_score > 40 and predicted_throughput > 5:
                return "significant"
            else:
                return "severe"
        except:
            return "unknown"

    def _generate_fusion_recommendations(self, integrated_assessment: Dict) -> List[str]:
        """生成融合建議"""
        recommendations = []
        
        try:
            urgency = integrated_assessment.get("urgency_level", "low")
            quality_score = integrated_assessment.get("quality_score", 50)
            interference_severity = integrated_assessment.get("interference_severity", "none")
            
            if urgency in ["critical", "high"]:
                recommendations.append("立即啟動 AI-RAN 抗干擾機制")
                
            if quality_score < 30:
                recommendations.append("考慮切換到不同頻段")
                
            if interference_severity in ["severe", "moderate"]:
                recommendations.append("啟用頻率跳變和功率控制")
                
            if integrated_assessment.get("predicted_throughput_mbps", 0) < 5:
                recommendations.append("優化波束賦形和自適應編碼")
                
            if not recommendations:
                recommendations.append("維持當前配置，持續監控")
                
        except Exception as e:
            self.logger.error(f"生成建議失敗: {e}")
            recommendations.append("無法生成建議，請手動檢查")
            
        return recommendations

    async def _request_enhanced_ai_decision(
        self, integrated_analysis: Dict, ue_positions: List[Dict], gnb_positions: List[Dict]
    ) -> Optional[Dict]:
        """請求增強的 AI 決策"""
        
        try:
            decision_request = {
                "integrated_analysis": integrated_analysis,
                "ue_positions": ue_positions,
                "gnb_positions": gnb_positions,
                "decision_params": {
                    "enable_sionna_integration": True,
                    "enable_predictive_analysis": True,
                    "optimization_objectives": ["throughput", "latency", "interference_mitigation"],
                    "time_horizon_ms": 1000,
                    "enable_multi_objective_optimization": True,
                },
                "constraints": {
                    "max_power_dbm": 30,
                    "available_frequencies": [2100, 2150, 2200, 2300, 2400, 2500],
                    "max_decision_time_ms": 500,
                }
            }

            async with self.http_session.post(
                f"{self.netstack_api_url}/api/v1/ai-ran/enhanced-decision",
                json=decision_request,
                timeout=aiohttp.ClientTimeout(total=2.0),
            ) as response:
                if response.status == 200:
                    decision = await response.json()
                    self.integration_stats["ai_decisions"] += 1
                    return decision
                else:
                    self.logger.warning(f"AI 決策 API 響應異常: {response.status}")
                    return None

        except Exception as e:
            self.logger.error(f"AI 決策請求失敗: {e}")
            return None

    async def _apply_integrated_mitigation(
        self, ai_decision: Optional[Dict], integrated_analysis: Dict, scenario_id: str
    ) -> Optional[Dict]:
        """應用整合的緩解措施"""
        
        try:
            if not ai_decision or not ai_decision.get("success"):
                return {"success": False, "error": "無有效 AI 決策"}

            mitigation_request = {
                "scenario_id": scenario_id,
                "ai_decision": ai_decision,
                "integrated_analysis": integrated_analysis,
                "mitigation_params": {
                    "apply_immediately": True,
                    "enable_verification": True,
                    "enable_rollback": True,
                    "update_ueransim": True,
                    "update_sionna_params": True,
                }
            }

            async with self.http_session.post(
                f"{self.netstack_api_url}/api/v1/interference/apply-integrated-mitigation",
                json=mitigation_request,
                timeout=aiohttp.ClientTimeout(total=3.0),
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.warning(f"緩解措施應用 API 響應異常: {response.status}")
                    return {"success": False, "error": f"API 響應異常: {response.status}"}

        except Exception as e:
            self.logger.error(f"緩解措施應用失敗: {e}")
            return {"success": False, "error": str(e)}

    def _calculate_channel_improvement(self, integrated_analysis: Dict, mitigation_result: Optional[Dict]) -> float:
        """計算通道質量改善"""
        try:
            if not mitigation_result or not mitigation_result.get("success"):
                return 0.0
            
            before_quality = integrated_analysis.get("integrated_assessment", {}).get("quality_score", 50)
            after_quality = mitigation_result.get("post_mitigation_metrics", {}).get("quality_score", before_quality)
            
            return float(after_quality - before_quality)
        except:
            return 0.0

    def _calculate_interference_reduction(self, integrated_analysis: Dict, mitigation_result: Optional[Dict]) -> float:
        """計算干擾減少量"""
        try:
            if not mitigation_result or not mitigation_result.get("success"):
                return 0.0
                
            before_level = integrated_analysis.get("interference_metrics", {}).get("interference_level_db", -120)
            after_level = mitigation_result.get("post_mitigation_metrics", {}).get("interference_level_db", before_level)
            
            return float(before_level - after_level)  # 正值表示干擾減少
        except:
            return 0.0

    def _estimate_throughput_improvement(self, integrated_analysis: Dict, ai_decision: Optional[Dict]) -> float:
        """估計吞吐量改善"""
        try:
            if not ai_decision or not ai_decision.get("success"):
                return 0.0
                
            current_throughput = integrated_analysis.get("integrated_assessment", {}).get("predicted_throughput_mbps", 0)
            estimated_improvement_factor = ai_decision.get("estimated_improvement_factor", 1.0)
            
            return float(current_throughput * (estimated_improvement_factor - 1.0))
        except:
            return 0.0

    def _update_avg_response_time(self, response_time_ms: float):
        """更新平均響應時間"""
        try:
            current_avg = self.integration_stats["avg_response_time_ms"]
            count = self.integration_stats["total_integrations"]
            
            if count <= 1:
                self.integration_stats["avg_response_time_ms"] = response_time_ms
            else:
                # 移動平均
                self.integration_stats["avg_response_time_ms"] = (
                    current_avg * (count - 1) + response_time_ms
                ) / count
        except Exception as e:
            self.logger.error(f"更新響應時間統計失敗: {e}")

    async def get_integration_status(self) -> Dict[str, Any]:
        """獲取整合狀態"""
        return {
            "service_name": "Sionna 干擾控制整合服務",
            "status": "running" if self.http_session and not self.http_session.closed else "stopped",
            "update_interval_ms": self.update_interval_ms,
            "active_integrations_count": len(self.active_integrations),
            "last_sionna_update": self.last_sionna_update.isoformat() if self.last_sionna_update else None,
            "integration_stats": self.integration_stats,
            "cache_size": len(self.channel_cache),
            "simworld_api_url": self.simworld_api_url,
            "netstack_api_url": self.netstack_api_url,
        }

    async def get_active_integrations(self) -> Dict[str, Dict]:
        """獲取活躍的整合"""
        return self.active_integrations.copy()

    async def clear_integration_cache(self) -> bool:
        """清除整合緩存"""
        try:
            self.active_integrations.clear()
            self.channel_cache.clear()
            self.logger.info("整合緩存已清除")
            return True
        except Exception as e:
            self.logger.error(f"清除緩存失敗: {e}")
            return False