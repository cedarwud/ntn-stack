"""
統一Sionna整合服務 (Unified Sionna Integration)

整合了以下三個服務的功能：
1. sionna_integration_service.py - 基礎Sionna通道模型整合與UERANSIM配置
2. sionna_interference_integration.py - Sionna與干擾控制服務整合，AI-RAN抗干擾
3. sionna_ueransim_integration_service.py - Sionna無線通道模型與UERANSIM深度整合

提供統一的Sionna整合接口，支持：
- 完整的無線通道模型模擬
- 實時干擾檢測與抗干擾算法
- UERANSIM配置自動生成與更新
- AI-RAN智能決策整合
- 性能監控與優化
- 多場景適應性配置
"""

import asyncio
import aiohttp
import json
import yaml
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import structlog

try:
    from ..models.sionna_models import (
        SionnaChannelRequest,
        SionnaChannelResponse,
        ChannelCharacteristics,
        PathLossParams,
        SINRParameters,
    )
except ImportError:
    # Fallback to simple dataclasses if models not available
    @dataclass
    class SionnaChannelRequest:
        ue_id: str
        gnb_id: str
        scenario: str = "urban"
    
    @dataclass
    class SionnaChannelResponse:
        sinr_db: float
        rsrp_dbm: float
        throughput_mbps: float

try:
    from ..adapters.redis_adapter import RedisAdapter
except ImportError:
    RedisAdapter = None

logger = structlog.get_logger(__name__)


class IntegrationMode(Enum):
    """整合模式"""
    BASIC = "basic"                    # 基礎整合
    INTERFERENCE_AWARE = "interference_aware"  # 干擾感知
    AI_ENHANCED = "ai_enhanced"        # AI增強
    FULL_INTEGRATION = "full_integration"  # 完整整合


class ChannelModelType(Enum):
    """通道模型類型"""
    URBAN_MACRO = "urban_macro"
    URBAN_MICRO = "urban_micro"
    RURAL_MACRO = "rural_macro"
    INDOOR = "indoor"
    SATELLITE = "satellite"
    NTN = "ntn"  # Non-Terrestrial Network


class InterferenceType(Enum):
    """干擾類型"""
    CO_CHANNEL = "co_channel"
    ADJACENT_CHANNEL = "adjacent_channel"
    INTER_SYSTEM = "inter_system"
    ATMOSPHERIC = "atmospheric"
    HARDWARE = "hardware"


class AIDecisionType(Enum):
    """AI決策類型"""
    POWER_CONTROL = "power_control"
    BEAMFORMING = "beamforming"
    RESOURCE_ALLOCATION = "resource_allocation"
    HANDOVER = "handover"
    INTERFERENCE_MITIGATION = "interference_mitigation"


@dataclass
class ChannelModelUpdate:
    """通道模型更新"""
    ue_id: str
    gnb_id: str
    sinr_db: float
    rsrp_dbm: float
    rsrq_db: float
    cqi: int
    throughput_mbps: float
    latency_ms: float
    error_rate: float
    timestamp: datetime
    valid_until: datetime
    
    # 增強字段
    channel_model_type: ChannelModelType = ChannelModelType.URBAN_MACRO
    interference_level: float = 0.0
    interference_sources: List[str] = field(default_factory=list)
    ai_recommendations: Dict[str, Any] = field(default_factory=dict)
    path_loss_db: float = 0.0
    shadowing_db: float = 0.0
    fast_fading_db: float = 0.0


@dataclass
class InterferenceDetection:
    """干擾檢測結果"""
    detection_id: str
    ue_id: str
    gnb_id: str
    interference_type: InterferenceType
    interference_level_db: float
    interference_sources: List[str]
    detection_confidence: float
    mitigation_recommendations: List[str]
    timestamp: datetime
    
    # AI分析結果
    ai_analysis: Dict[str, Any] = field(default_factory=dict)
    predicted_impact: float = 0.0
    mitigation_urgency: str = "low"  # low, medium, high, critical


@dataclass
class AIDecision:
    """AI決策結果"""
    decision_id: str
    decision_type: AIDecisionType
    ue_id: str
    gnb_id: str
    current_parameters: Dict[str, Any]
    recommended_parameters: Dict[str, Any]
    expected_improvement: float
    confidence_score: float
    decision_rationale: str
    timestamp: datetime
    
    # 實施狀態
    implemented: bool = False
    implementation_result: Optional[Dict[str, Any]] = None


@dataclass
class UERANSIMConfiguration:
    """UERANSIM配置"""
    config_id: str
    ue_id: str
    gnb_id: str
    
    # 基礎配置
    frequency_mhz: float
    bandwidth_mhz: float
    tx_power_dbm: float
    antenna_gain_db: float
    
    # 通道參數
    path_loss_model: str
    shadowing_std_db: float
    fast_fading_model: str
    
    # Sionna整合參數
    sionna_channel_params: Dict[str, Any] = field(default_factory=dict)
    interference_mitigation_params: Dict[str, Any] = field(default_factory=dict)
    ai_optimization_params: Dict[str, Any] = field(default_factory=dict)
    
    # 配置文件路徑
    config_file_path: Optional[str] = None
    last_updated: datetime = field(default_factory=datetime.utcnow)


class UnifiedSionnaIntegration:
    """
    統一Sionna整合服務
    
    提供完整的Sionna無線通道模型整合，包括干擾控制、
    AI決策、UERANSIM配置等功能。
    """

    def __init__(
        self,
        redis_adapter: Optional[RedisAdapter] = None,
        simworld_api_url: str = "http://simworld-backend:8000",
        netstack_api_url: str = "http://netstack-api:8080",
        ueransim_config_dir: str = "/tmp/ueransim_configs",
        integration_mode: IntegrationMode = IntegrationMode.FULL_INTEGRATION,
        update_interval_ms: float = 100,
        enable_ai_decisions: bool = True,
        enable_interference_detection: bool = True,
    ):
        self.redis_adapter = redis_adapter
        self.simworld_api_url = simworld_api_url
        self.netstack_api_url = netstack_api_url
        self.ueransim_config_dir = Path(ueransim_config_dir)
        self.integration_mode = integration_mode
        self.update_interval_ms = update_interval_ms
        self.enable_ai_decisions = enable_ai_decisions
        self.enable_interference_detection = enable_interference_detection
        
        # Ensure config directory exists
        self.ueransim_config_dir.mkdir(parents=True, exist_ok=True)
        
        # Service state
        self.active_integrations: Dict[str, Dict] = {}
        self.channel_cache: Dict[str, ChannelModelUpdate] = {}
        self.interference_detections: Dict[str, InterferenceDetection] = {}
        self.ai_decisions: Dict[str, AIDecision] = {}
        self.ueransim_configurations: Dict[str, UERANSIMConfiguration] = {}
        
        # Performance statistics
        self.integration_stats = {
            "total_integrations": 0,
            "successful_integrations": 0,
            "failed_integrations": 0,
            "avg_response_time_ms": 0.0,
            "sionna_updates": 0,
            "ai_decisions": 0,
            "interference_detections": 0,
            "ueransim_updates": 0,
        }
        
        # HTTP session
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        # Monitoring state
        self._monitoring_active = False
        self._integration_active = False
        
        self.logger = logger.bind(service="unified_sionna_integration")

    async def initialize(self):
        """初始化統一Sionna整合服務"""
        try:
            # Initialize HTTP session
            self.http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            
            # Load existing configurations
            await self._load_existing_configurations()
            
            # Initialize AI models if enabled
            if self.enable_ai_decisions:
                await self._initialize_ai_models()
            
            # Test connections
            await self._test_service_connections()
            
            self.logger.info("✅ 統一Sionna整合服務初始化完成")
            
        except Exception as e:
            self.logger.error(f"❌ 統一Sionna整合服務初始化失敗: {e}")
            raise

    async def _load_existing_configurations(self):
        """載入現有配置"""
        try:
            # Load UERANSIM configurations from disk
            config_files = list(self.ueransim_config_dir.glob("*.yaml"))
            for config_file in config_files:
                try:
                    with open(config_file, 'r') as f:
                        config_data = yaml.safe_load(f)
                    
                    # Parse configuration and store
                    if config_data:
                        await self._parse_and_store_config(config_file, config_data)
                        
                except Exception as e:
                    self.logger.warning(f"載入配置文件失敗 {config_file}: {e}")
            
            self.logger.info(f"載入了 {len(self.ueransim_configurations)} 個UERANSIM配置")
            
        except Exception as e:
            self.logger.error(f"載入現有配置失敗: {e}")

    async def _parse_and_store_config(self, config_file: Path, config_data: Dict):
        """解析並存儲配置"""
        try:
            # Extract relevant parameters from UERANSIM config
            ue_id = config_data.get("ue_id", f"ue_{config_file.stem}")
            gnb_id = config_data.get("gnb_id", "gnb_001")
            
            configuration = UERANSIMConfiguration(
                config_id=str(config_file.stem),
                ue_id=ue_id,
                gnb_id=gnb_id,
                frequency_mhz=config_data.get("frequency", 2400.0),
                bandwidth_mhz=config_data.get("bandwidth", 20.0),
                tx_power_dbm=config_data.get("tx_power", 23.0),
                antenna_gain_db=config_data.get("antenna_gain", 0.0),
                path_loss_model=config_data.get("path_loss_model", "friis"),
                shadowing_std_db=config_data.get("shadowing_std", 8.0),
                fast_fading_model=config_data.get("fast_fading_model", "rayleigh"),
                config_file_path=str(config_file),
            )
            
            self.ueransim_configurations[ue_id] = configuration
            
        except Exception as e:
            self.logger.error(f"解析配置失敗: {e}")

    async def _initialize_ai_models(self):
        """初始化AI模型"""
        try:
            # Initialize AI models for interference detection and mitigation
            self.ai_models = {
                "interference_detector": None,  # Would load trained model in production
                "power_control_optimizer": None,
                "beamforming_optimizer": None,
                "resource_allocator": None,
            }
            
            self.logger.info("✅ AI模型初始化完成")
            
        except Exception as e:
            self.logger.error(f"AI模型初始化失敗: {e}")

    async def _test_service_connections(self):
        """測試服務連接"""
        try:
            # Test SimWorld connection
            async with self.http_session.get(f"{self.simworld_api_url}/health") as response:
                if response.status == 200:
                    self.logger.info("✅ SimWorld 連接正常")
                else:
                    self.logger.warning(f"⚠️ SimWorld 連接異常: {response.status}")
        
        except Exception as e:
            self.logger.warning(f"⚠️ SimWorld 連接測試失敗: {e}")

    async def start_integration(self):
        """啟動整合服務"""
        if self._integration_active:
            self.logger.warning("整合服務已在運行中")
            return

        try:
            self._integration_active = True
            
            # Start integration tasks
            asyncio.create_task(self._channel_model_update_loop())
            
            if self.enable_interference_detection:
                asyncio.create_task(self._interference_detection_loop())
            
            if self.enable_ai_decisions:
                asyncio.create_task(self._ai_decision_loop())
            
            asyncio.create_task(self._ueransim_update_loop())
            
            self.logger.info("🚀 統一Sionna整合服務已啟動")
            
        except Exception as e:
            self._integration_active = False
            self.logger.error(f"整合服務啟動失敗: {e}")
            raise

    async def _channel_model_update_loop(self):
        """通道模型更新循環"""
        while self._integration_active:
            try:
                await self._update_channel_models()
                await asyncio.sleep(self.update_interval_ms / 1000)
                
            except Exception as e:
                self.logger.error(f"通道模型更新循環錯誤: {e}")
                await asyncio.sleep(1)

    async def _update_channel_models(self):
        """更新通道模型"""
        try:
            # Get channel updates from SimWorld
            channel_updates = await self._fetch_sionna_channel_data()
            
            for update_data in channel_updates:
                await self._process_channel_update(update_data)
            
            self.integration_stats["sionna_updates"] += len(channel_updates)
            
        except Exception as e:
            self.logger.error(f"通道模型更新失敗: {e}")

    async def _fetch_sionna_channel_data(self) -> List[Dict]:
        """從SimWorld獲取Sionna通道數據"""
        try:
            async with self.http_session.get(
                f"{self.simworld_api_url}/api/v1/interference/channel-models"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("channel_models", [])
                else:
                    self.logger.warning(f"獲取通道數據失敗: {response.status}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"獲取Sionna通道數據失敗: {e}")
            return []

    async def _process_channel_update(self, update_data: Dict):
        """處理通道更新"""
        try:
            ue_id = update_data.get("ue_id")
            gnb_id = update_data.get("gnb_id")
            
            if not ue_id or not gnb_id:
                return
            
            # Create channel model update
            channel_update = ChannelModelUpdate(
                ue_id=ue_id,
                gnb_id=gnb_id,
                sinr_db=update_data.get("sinr_db", 0.0),
                rsrp_dbm=update_data.get("rsrp_dbm", -100.0),
                rsrq_db=update_data.get("rsrq_db", -10.0),
                cqi=update_data.get("cqi", 7),
                throughput_mbps=update_data.get("throughput_mbps", 10.0),
                latency_ms=update_data.get("latency_ms", 20.0),
                error_rate=update_data.get("error_rate", 0.01),
                timestamp=datetime.utcnow(),
                valid_until=datetime.utcnow() + timedelta(seconds=30),
                channel_model_type=ChannelModelType(update_data.get("channel_type", "urban_macro")),
                interference_level=update_data.get("interference_level", 0.0),
                interference_sources=update_data.get("interference_sources", []),
                path_loss_db=update_data.get("path_loss_db", 120.0),
                shadowing_db=update_data.get("shadowing_db", 8.0),
                fast_fading_db=update_data.get("fast_fading_db", 0.0),
            )
            
            # Store in cache
            cache_key = f"{ue_id}_{gnb_id}"
            self.channel_cache[cache_key] = channel_update
            
            # Trigger interference detection if enabled
            if self.enable_interference_detection and channel_update.interference_level > 0.1:
                await self._trigger_interference_detection(channel_update)
            
            # Update UERANSIM configuration
            await self._update_ueransim_config(channel_update)
            
        except Exception as e:
            self.logger.error(f"處理通道更新失敗: {e}")

    async def _interference_detection_loop(self):
        """干擾檢測循環"""
        while self._integration_active:
            try:
                await self._run_interference_detection()
                await asyncio.sleep(0.5)  # 500ms間隔
                
            except Exception as e:
                self.logger.error(f"干擾檢測循環錯誤: {e}")
                await asyncio.sleep(2)

    async def _run_interference_detection(self):
        """運行干擾檢測"""
        try:
            # Analyze channel cache for interference patterns
            for cache_key, channel_update in self.channel_cache.items():
                if channel_update.interference_level > 0.2:  # Threshold for detection
                    await self._analyze_interference(channel_update)
            
        except Exception as e:
            self.logger.error(f"干擾檢測運行失敗: {e}")

    async def _trigger_interference_detection(self, channel_update: ChannelModelUpdate):
        """觸發干擾檢測"""
        try:
            interference_detection = await self._detect_interference(channel_update)
            if interference_detection:
                self.interference_detections[interference_detection.detection_id] = interference_detection
                
                # Trigger AI decision if high severity
                if interference_detection.mitigation_urgency in ["high", "critical"]:
                    await self._trigger_ai_decision(interference_detection)
                
        except Exception as e:
            self.logger.error(f"觸發干擾檢測失敗: {e}")

    async def _detect_interference(self, channel_update: ChannelModelUpdate) -> Optional[InterferenceDetection]:
        """檢測干擾"""
        try:
            # Analyze interference patterns
            interference_type = self._classify_interference(channel_update)
            confidence = self._calculate_detection_confidence(channel_update)
            
            if confidence > 0.7:  # High confidence threshold
                detection = InterferenceDetection(
                    detection_id=f"int_{int(time.time() * 1000)}",
                    ue_id=channel_update.ue_id,
                    gnb_id=channel_update.gnb_id,
                    interference_type=interference_type,
                    interference_level_db=10 * np.log10(channel_update.interference_level + 1e-12),
                    interference_sources=channel_update.interference_sources,
                    detection_confidence=confidence,
                    mitigation_recommendations=self._get_mitigation_recommendations(interference_type),
                    timestamp=datetime.utcnow(),
                    mitigation_urgency=self._assess_urgency(channel_update),
                )
                
                self.integration_stats["interference_detections"] += 1
                return detection
                
        except Exception as e:
            self.logger.error(f"干擾檢測失敗: {e}")
        
        return None

    def _classify_interference(self, channel_update: ChannelModelUpdate) -> InterferenceType:
        """分類干擾類型"""
        # Simplified interference classification
        if channel_update.interference_level > 0.8:
            return InterferenceType.CO_CHANNEL
        elif channel_update.interference_level > 0.5:
            return InterferenceType.ADJACENT_CHANNEL
        else:
            return InterferenceType.ATMOSPHERIC

    def _calculate_detection_confidence(self, channel_update: ChannelModelUpdate) -> float:
        """計算檢測信心度"""
        # Base confidence on signal quality and interference level
        base_confidence = 0.5
        
        # Higher interference level increases confidence
        if channel_update.interference_level > 0.5:
            base_confidence += 0.3
        
        # Lower SINR increases confidence of interference
        if channel_update.sinr_db < 10:
            base_confidence += 0.2
        
        return min(1.0, base_confidence)

    def _get_mitigation_recommendations(self, interference_type: InterferenceType) -> List[str]:
        """獲取緩解建議"""
        recommendations = {
            InterferenceType.CO_CHANNEL: ["power_control", "beamforming", "frequency_reuse"],
            InterferenceType.ADJACENT_CHANNEL: ["filtering", "power_control", "scheduling"],
            InterferenceType.INTER_SYSTEM: ["coordination", "spectrum_management", "isolation"],
            InterferenceType.ATMOSPHERIC: ["adaptive_modulation", "power_boost", "diversity"],
            InterferenceType.HARDWARE: ["calibration", "hardware_replacement", "compensation"],
        }
        
        return recommendations.get(interference_type, ["monitoring"])

    def _assess_urgency(self, channel_update: ChannelModelUpdate) -> str:
        """評估緩解緊急程度"""
        if channel_update.interference_level > 0.8 or channel_update.sinr_db < 0:
            return "critical"
        elif channel_update.interference_level > 0.5 or channel_update.sinr_db < 5:
            return "high"
        elif channel_update.interference_level > 0.2 or channel_update.sinr_db < 10:
            return "medium"
        else:
            return "low"

    async def _analyze_interference(self, channel_update: ChannelModelUpdate):
        """分析干擾模式"""
        try:
            # Perform deeper interference analysis
            cache_key = f"{channel_update.ue_id}_{channel_update.gnb_id}"
            
            # Check if already detected
            existing_detections = [
                d for d in self.interference_detections.values()
                if d.ue_id == channel_update.ue_id and d.gnb_id == channel_update.gnb_id
            ]
            
            # If no recent detection, trigger new detection
            if not existing_detections:
                await self._trigger_interference_detection(channel_update)
                
        except Exception as e:
            self.logger.error(f"干擾分析失敗: {e}")

    async def _ai_decision_loop(self):
        """AI決策循環"""
        while self._integration_active:
            try:
                await self._run_ai_decisions()
                await asyncio.sleep(1)  # 1秒間隔
                
            except Exception as e:
                self.logger.error(f"AI決策循環錯誤: {e}")
                await asyncio.sleep(3)

    async def _run_ai_decisions(self):
        """運行AI決策"""
        try:
            # Process pending interference detections
            for detection in self.interference_detections.values():
                if not detection.ai_analysis:
                    await self._generate_ai_decision(detection)
            
        except Exception as e:
            self.logger.error(f"AI決策運行失敗: {e}")

    async def _trigger_ai_decision(self, interference_detection: InterferenceDetection):
        """觸發AI決策"""
        try:
            ai_decision = await self._generate_ai_decision(interference_detection)
            if ai_decision:
                self.ai_decisions[ai_decision.decision_id] = ai_decision
                
                # Implement decision if confidence is high
                if ai_decision.confidence_score > 0.8:
                    await self._implement_ai_decision(ai_decision)
                
        except Exception as e:
            self.logger.error(f"觸發AI決策失敗: {e}")

    async def _generate_ai_decision(self, interference_detection: InterferenceDetection) -> Optional[AIDecision]:
        """生成AI決策"""
        try:
            # Determine best mitigation strategy
            decision_type = self._select_ai_decision_type(interference_detection)
            
            # Get current parameters
            current_params = await self._get_current_parameters(
                interference_detection.ue_id, 
                interference_detection.gnb_id
            )
            
            # Generate optimized parameters
            recommended_params = await self._optimize_parameters(
                decision_type, 
                current_params, 
                interference_detection
            )
            
            # Estimate improvement
            expected_improvement = self._estimate_improvement(
                current_params, 
                recommended_params, 
                interference_detection
            )
            
            decision = AIDecision(
                decision_id=f"ai_{int(time.time() * 1000)}",
                decision_type=decision_type,
                ue_id=interference_detection.ue_id,
                gnb_id=interference_detection.gnb_id,
                current_parameters=current_params,
                recommended_parameters=recommended_params,
                expected_improvement=expected_improvement,
                confidence_score=self._calculate_ai_confidence(interference_detection),
                decision_rationale=self._generate_rationale(decision_type, interference_detection),
                timestamp=datetime.utcnow(),
            )
            
            # Update interference detection with AI analysis
            interference_detection.ai_analysis = {
                "decision_id": decision.decision_id,
                "decision_type": decision_type.value,
                "expected_improvement": expected_improvement,
                "confidence": decision.confidence_score,
            }
            
            self.integration_stats["ai_decisions"] += 1
            return decision
            
        except Exception as e:
            self.logger.error(f"生成AI決策失敗: {e}")
        
        return None

    def _select_ai_decision_type(self, interference_detection: InterferenceDetection) -> AIDecisionType:
        """選擇AI決策類型"""
        if interference_detection.interference_type == InterferenceType.CO_CHANNEL:
            return AIDecisionType.POWER_CONTROL
        elif interference_detection.interference_level_db > -80:
            return AIDecisionType.BEAMFORMING
        else:
            return AIDecisionType.INTERFERENCE_MITIGATION

    async def _get_current_parameters(self, ue_id: str, gnb_id: str) -> Dict[str, Any]:
        """獲取當前參數"""
        config = self.ueransim_configurations.get(ue_id)
        if config:
            return {
                "tx_power_dbm": config.tx_power_dbm,
                "antenna_gain_db": config.antenna_gain_db,
                "frequency_mhz": config.frequency_mhz,
                "bandwidth_mhz": config.bandwidth_mhz,
            }
        
        # Default parameters
        return {
            "tx_power_dbm": 23.0,
            "antenna_gain_db": 0.0,
            "frequency_mhz": 2400.0,
            "bandwidth_mhz": 20.0,
        }

    async def _optimize_parameters(
        self, 
        decision_type: AIDecisionType, 
        current_params: Dict[str, Any], 
        interference_detection: InterferenceDetection
    ) -> Dict[str, Any]:
        """優化參數"""
        optimized_params = current_params.copy()
        
        if decision_type == AIDecisionType.POWER_CONTROL:
            # Reduce power if interference is high
            if interference_detection.interference_level_db > -70:
                optimized_params["tx_power_dbm"] = max(10.0, current_params["tx_power_dbm"] - 3.0)
        
        elif decision_type == AIDecisionType.BEAMFORMING:
            # Increase antenna gain for beamforming
            optimized_params["antenna_gain_db"] = min(20.0, current_params["antenna_gain_db"] + 3.0)
        
        elif decision_type == AIDecisionType.RESOURCE_ALLOCATION:
            # Adjust bandwidth allocation
            if interference_detection.interference_level_db > -80:
                optimized_params["bandwidth_mhz"] = max(5.0, current_params["bandwidth_mhz"] * 0.8)
        
        return optimized_params

    def _estimate_improvement(
        self, 
        current_params: Dict[str, Any], 
        recommended_params: Dict[str, Any], 
        interference_detection: InterferenceDetection
    ) -> float:
        """估計改善程度"""
        # Simplified improvement estimation
        power_improvement = abs(recommended_params["tx_power_dbm"] - current_params["tx_power_dbm"]) * 0.1
        gain_improvement = abs(recommended_params["antenna_gain_db"] - current_params["antenna_gain_db"]) * 0.05
        
        total_improvement = min(50.0, power_improvement + gain_improvement)
        return total_improvement

    def _calculate_ai_confidence(self, interference_detection: InterferenceDetection) -> float:
        """計算AI信心度"""
        base_confidence = 0.7
        
        # Higher detection confidence increases AI confidence
        base_confidence += interference_detection.detection_confidence * 0.2
        
        # Higher interference level increases AI confidence
        if interference_detection.interference_level_db > -70:
            base_confidence += 0.1
        
        return min(1.0, base_confidence)

    def _generate_rationale(self, decision_type: AIDecisionType, interference_detection: InterferenceDetection) -> str:
        """生成決策理由"""
        rationales = {
            AIDecisionType.POWER_CONTROL: f"高干擾水平 ({interference_detection.interference_level_db:.1f} dB) 需要功率控制",
            AIDecisionType.BEAMFORMING: f"定向波束成形可改善 {interference_detection.interference_type.value} 干擾",
            AIDecisionType.RESOURCE_ALLOCATION: "資源重新分配以避免干擾源",
            AIDecisionType.INTERFERENCE_MITIGATION: f"針對 {interference_detection.interference_type.value} 的專用緩解策略",
        }
        
        return rationales.get(decision_type, "AI建議的優化策略")

    async def _implement_ai_decision(self, ai_decision: AIDecision):
        """實施AI決策"""
        try:
            # Update UERANSIM configuration with new parameters
            await self._update_ueransim_parameters(
                ai_decision.ue_id,
                ai_decision.recommended_parameters
            )
            
            # Mark as implemented
            ai_decision.implemented = True
            ai_decision.implementation_result = {
                "status": "success",
                "timestamp": datetime.utcnow().isoformat(),
                "applied_parameters": ai_decision.recommended_parameters,
            }
            
            self.logger.info(f"✅ AI決策已實施: {ai_decision.decision_id}")
            
        except Exception as e:
            ai_decision.implementation_result = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.logger.error(f"AI決策實施失敗: {e}")

    async def _ueransim_update_loop(self):
        """UERANSIM更新循環"""
        while self._integration_active:
            try:
                await self._update_ueransim_configurations()
                await asyncio.sleep(5)  # 5秒間隔
                
            except Exception as e:
                self.logger.error(f"UERANSIM更新循環錯誤: {e}")
                await asyncio.sleep(10)

    async def _update_ueransim_configurations(self):
        """更新UERANSIM配置"""
        try:
            # Update configurations based on latest channel data
            for cache_key, channel_update in self.channel_cache.items():
                await self._update_ueransim_config(channel_update)
            
        except Exception as e:
            self.logger.error(f"UERANSIM配置更新失敗: {e}")

    async def _update_ueransim_config(self, channel_update: ChannelModelUpdate):
        """更新特定UE的UERANSIM配置"""
        try:
            config = self.ueransim_configurations.get(channel_update.ue_id)
            if not config:
                # Create new configuration
                config = UERANSIMConfiguration(
                    config_id=f"config_{channel_update.ue_id}",
                    ue_id=channel_update.ue_id,
                    gnb_id=channel_update.gnb_id,
                    frequency_mhz=2400.0,
                    bandwidth_mhz=20.0,
                    tx_power_dbm=23.0,
                    antenna_gain_db=0.0,
                    path_loss_model="friis",
                    shadowing_std_db=8.0,
                    fast_fading_model="rayleigh",
                )
                self.ueransim_configurations[channel_update.ue_id] = config
            
            # Update Sionna integration parameters
            config.sionna_channel_params = {
                "sinr_db": channel_update.sinr_db,
                "rsrp_dbm": channel_update.rsrp_dbm,
                "rsrq_db": channel_update.rsrq_db,
                "path_loss_db": channel_update.path_loss_db,
                "shadowing_db": channel_update.shadowing_db,
                "fast_fading_db": channel_update.fast_fading_db,
                "channel_model_type": channel_update.channel_model_type.value,
            }
            
            # Update interference parameters
            if channel_update.interference_level > 0:
                config.interference_mitigation_params = {
                    "interference_level": channel_update.interference_level,
                    "interference_sources": channel_update.interference_sources,
                    "mitigation_enabled": True,
                }
            
            # Generate configuration file
            await self._generate_ueransim_config_file(config)
            
            config.last_updated = datetime.utcnow()
            self.integration_stats["ueransim_updates"] += 1
            
        except Exception as e:
            self.logger.error(f"UERANSIM配置更新失敗: {e}")

    async def _update_ueransim_parameters(self, ue_id: str, new_parameters: Dict[str, Any]):
        """更新UERANSIM參數"""
        try:
            config = self.ueransim_configurations.get(ue_id)
            if not config:
                return
            
            # Update configuration parameters
            if "tx_power_dbm" in new_parameters:
                config.tx_power_dbm = new_parameters["tx_power_dbm"]
            if "antenna_gain_db" in new_parameters:
                config.antenna_gain_db = new_parameters["antenna_gain_db"]
            if "frequency_mhz" in new_parameters:
                config.frequency_mhz = new_parameters["frequency_mhz"]
            if "bandwidth_mhz" in new_parameters:
                config.bandwidth_mhz = new_parameters["bandwidth_mhz"]
            
            # Regenerate configuration file
            await self._generate_ueransim_config_file(config)
            
            self.logger.info(f"✅ UERANSIM參數已更新: {ue_id}")
            
        except Exception as e:
            self.logger.error(f"UERANSIM參數更新失敗: {e}")

    async def _generate_ueransim_config_file(self, config: UERANSIMConfiguration):
        """生成UERANSIM配置文件"""
        try:
            config_data = {
                "ue_id": config.ue_id,
                "gnb_id": config.gnb_id,
                "frequency": config.frequency_mhz,
                "bandwidth": config.bandwidth_mhz,
                "tx_power": config.tx_power_dbm,
                "antenna_gain": config.antenna_gain_db,
                "path_loss_model": config.path_loss_model,
                "shadowing_std": config.shadowing_std_db,
                "fast_fading_model": config.fast_fading_model,
                
                # Sionna integration
                "sionna_integration": {
                    "enabled": True,
                    "channel_params": config.sionna_channel_params,
                    "interference_mitigation": config.interference_mitigation_params,
                    "ai_optimization": config.ai_optimization_params,
                },
                
                # Metadata
                "last_updated": config.last_updated.isoformat(),
                "config_version": "2.0",
            }
            
            # Write to file
            config_file = self.ueransim_config_dir / f"{config.ue_id}.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
            
            config.config_file_path = str(config_file)
            
        except Exception as e:
            self.logger.error(f"生成UERANSIM配置文件失敗: {e}")

    async def get_channel_model_status(self, ue_id: str, gnb_id: str) -> Optional[Dict[str, Any]]:
        """獲取通道模型狀態"""
        cache_key = f"{ue_id}_{gnb_id}"
        channel_update = self.channel_cache.get(cache_key)
        
        if not channel_update:
            return None
        
        return {
            "ue_id": channel_update.ue_id,
            "gnb_id": channel_update.gnb_id,
            "sinr_db": channel_update.sinr_db,
            "rsrp_dbm": channel_update.rsrp_dbm,
            "throughput_mbps": channel_update.throughput_mbps,
            "latency_ms": channel_update.latency_ms,
            "channel_model_type": channel_update.channel_model_type.value,
            "interference_level": channel_update.interference_level,
            "interference_sources": channel_update.interference_sources,
            "last_updated": channel_update.timestamp.isoformat(),
            "valid_until": channel_update.valid_until.isoformat(),
        }

    async def get_interference_status(self, ue_id: str) -> List[Dict[str, Any]]:
        """獲取干擾狀態"""
        detections = [
            d for d in self.interference_detections.values()
            if d.ue_id == ue_id
        ]
        
        return [
            {
                "detection_id": d.detection_id,
                "interference_type": d.interference_type.value,
                "interference_level_db": d.interference_level_db,
                "detection_confidence": d.detection_confidence,
                "mitigation_urgency": d.mitigation_urgency,
                "mitigation_recommendations": d.mitigation_recommendations,
                "ai_analysis": d.ai_analysis,
                "timestamp": d.timestamp.isoformat(),
            }
            for d in detections
        ]

    async def get_ai_decisions(self, ue_id: str) -> List[Dict[str, Any]]:
        """獲取AI決策"""
        decisions = [
            d for d in self.ai_decisions.values()
            if d.ue_id == ue_id
        ]
        
        return [
            {
                "decision_id": d.decision_id,
                "decision_type": d.decision_type.value,
                "confidence_score": d.confidence_score,
                "expected_improvement": d.expected_improvement,
                "decision_rationale": d.decision_rationale,
                "implemented": d.implemented,
                "implementation_result": d.implementation_result,
                "timestamp": d.timestamp.isoformat(),
            }
            for d in decisions
        ]

    def get_integration_statistics(self) -> Dict[str, Any]:
        """獲取整合統計"""
        return {
            "integration_mode": self.integration_mode.value,
            "integration_active": self._integration_active,
            "statistics": self.integration_stats.copy(),
            "active_ues": len(self.ueransim_configurations),
            "active_channel_models": len(self.channel_cache),
            "active_interference_detections": len(self.interference_detections),
            "active_ai_decisions": len(self.ai_decisions),
            "features": {
                "ai_decisions_enabled": self.enable_ai_decisions,
                "interference_detection_enabled": self.enable_interference_detection,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def stop_integration(self):
        """停止整合服務"""
        try:
            self._integration_active = False
            
            # Close HTTP session
            if self.http_session:
                await self.http_session.close()
            
            self.logger.info("🛑 統一Sionna整合服務已停止")
            
        except Exception as e:
            self.logger.error(f"停止整合服務失敗: {e}")


# Global instance
unified_sionna_integration = UnifiedSionnaIntegration()