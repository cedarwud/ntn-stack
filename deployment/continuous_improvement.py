"""
Phase 3 Stage 9: 持續監控和改進機制
建立持續監控、自動化改進和智能優化系統
"""
import asyncio
import json
import logging
import time
import statistics
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Tuple
from pathlib import Path
import yaml
import math

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovementType(Enum):
    """改進類型"""
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    RESOURCE_EFFICIENCY = "resource_efficiency"
    SLA_ENHANCEMENT = "sla_enhancement"
    COST_REDUCTION = "cost_reduction"
    RELIABILITY_IMPROVEMENT = "reliability_improvement"
    SECURITY_ENHANCEMENT = "security_enhancement"

class ImprovementPriority(Enum):
    """改進優先級"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ImprovementStatus(Enum):
    """改進狀態"""
    IDENTIFIED = "identified"
    PLANNED = "planned"
    IMPLEMENTING = "implementing"
    TESTING = "testing"
    DEPLOYED = "deployed"
    VERIFIED = "verified"
    FAILED = "failed"

@dataclass
class ImprovementOpportunity:
    """改進機會"""
    id: str
    type: ImprovementType
    priority: ImprovementPriority
    status: ImprovementStatus
    title: str
    description: str
    impact_score: float
    effort_score: float
    roi_score: float
    identified_at: datetime
    target_metrics: Dict[str, float]
    current_metrics: Dict[str, float]
    implementation_plan: List[str] = field(default_factory=list)
    estimated_duration_days: int = 7
    dependencies: List[str] = field(default_factory=list)
    
@dataclass
class KPI:
    """關鍵性能指標"""
    name: str
    current_value: float
    target_value: float
    trend: str  # improving, degrading, stable
    last_updated: datetime
    history: List[Tuple[datetime, float]] = field(default_factory=list)
    
@dataclass
class ImprovementMetrics:
    """改進指標"""
    timestamp: datetime
    improvements_identified: int
    improvements_implemented: int
    average_implementation_time_days: float
    total_cost_savings: float
    performance_improvement_percentage: float
    sla_compliance_improvement: float
    customer_satisfaction_score: float

class ContinuousImprovementEngine:
    """持續改進引擎"""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.improvement_opportunities: Dict[str, ImprovementOpportunity] = {}
        self.kpis: Dict[str, KPI] = {}
        self.improvement_history: List[ImprovementMetrics] = []
        self.is_running = False
        
        # 智能分析組件
        self.pattern_analyzer = PatternAnalyzer()
        self.anomaly_detector = AnomalyDetector()
        self.recommendation_engine = RecommendationEngine()
        
        # 初始化 KPI
        self._initialize_kpis()
        
    def _load_config(self) -> Dict[str, Any]:
        """載入配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"載入配置失敗: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """獲取預設配置"""
        return {
            "continuous_improvement": {
                "analysis_interval_hours": 6,
                "implementation_check_interval_hours": 24,
                "min_roi_threshold": 1.5,
                "max_concurrent_improvements": 3,
                "auto_implement_low_risk": False
            },
            "kpi_targets": {
                "system_availability": 0.9995,  # 99.95%
                "error_rate": 0.0005,          # 0.05%
                "handover_latency_ms": 45.0,    # 45ms
                "handover_success_rate": 0.997, # 99.7%
                "cost_per_transaction": 0.10,   # $0.10
                "customer_satisfaction": 4.5     # 1-5 scale
            },
            "improvement_thresholds": {
                "performance_degradation_threshold": 0.05,  # 5%
                "cost_increase_threshold": 0.10,           # 10%
                "sla_violation_threshold": 0.02            # 2%
            }
        }
    
    def _initialize_kpis(self):
        """初始化關鍵性能指標"""
        kpi_targets = self.config.get("kpi_targets", {})
        
        for kpi_name, target_value in kpi_targets.items():
            # 模擬當前值（略低於目標值）
            current_value = target_value * (0.95 + 0.04 * hash(kpi_name) % 10 / 10)
            
            self.kpis[kpi_name] = KPI(
                name=kpi_name,
                current_value=current_value,
                target_value=target_value,
                trend="stable",
                last_updated=datetime.now()
            )
        
        logger.info(f"初始化 {len(self.kpis)} 個 KPI 指標")
    
    async def start_continuous_improvement(self):
        """啟動持續改進"""
        if self.is_running:
            logger.warning("持續改進已在運行")
            return
        
        self.is_running = True
        logger.info("🚀 啟動持續監控和改進機制")
        
        # 啟動持續改進任務
        tasks = [
            asyncio.create_task(self._monitoring_loop()),
            asyncio.create_task(self._analysis_loop()),
            asyncio.create_task(self._implementation_loop()),
            asyncio.create_task(self._reporting_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("持續改進已停止")
        finally:
            self.is_running = False
    
    async def stop_continuous_improvement(self):
        """停止持續改進"""
        logger.info("🛑 停止持續監控和改進")
        self.is_running = False
    
    async def _monitoring_loop(self):
        """監控循環"""
        while self.is_running:
            try:
                # 更新 KPI 指標
                await self._update_kpis()
                
                # 檢測性能趨勢
                await self._detect_performance_trends()
                
                # 監控 SLA 合規性
                await self._monitor_sla_compliance()
                
                # 每小時監控一次
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"監控循環失敗: {e}")
                await asyncio.sleep(3600)
    
    async def _analysis_loop(self):
        """分析循環"""
        analysis_interval = self.config.get("continuous_improvement", {}).get("analysis_interval_hours", 6)
        
        while self.is_running:
            try:
                # 識別改進機會
                await self._identify_improvement_opportunities()
                
                # 分析系統模式
                await self._analyze_system_patterns()
                
                # 生成改進建議
                await self._generate_improvement_recommendations()
                
                # 每6小時分析一次
                await asyncio.sleep(analysis_interval * 3600)
                
            except Exception as e:
                logger.error(f"分析循環失敗: {e}")
                await asyncio.sleep(analysis_interval * 3600)
    
    async def _implementation_loop(self):
        """實施循環"""
        check_interval = self.config.get("continuous_improvement", {}).get("implementation_check_interval_hours", 24)
        
        while self.is_running:
            try:
                # 檢查待實施的改進
                await self._check_pending_improvements()
                
                # 自動實施低風險改進
                await self._auto_implement_low_risk_improvements()
                
                # 驗證已實施改進的效果
                await self._verify_improvement_effects()
                
                # 每日檢查一次
                await asyncio.sleep(check_interval * 3600)
                
            except Exception as e:
                logger.error(f"實施循環失敗: {e}")
                await asyncio.sleep(check_interval * 3600)
    
    async def _reporting_loop(self):
        """報告循環"""
        while self.is_running:
            try:
                # 生成改進報告
                await self._generate_improvement_report()
                
                # 更新改進指標
                await self._update_improvement_metrics()
                
                # 每日報告一次
                await asyncio.sleep(86400)
                
            except Exception as e:
                logger.error(f"報告循環失敗: {e}")
                await asyncio.sleep(86400)
    
    async def _update_kpis(self):
        """更新 KPI 指標"""
        for kpi_name, kpi in self.kpis.items():
            # 模擬指標更新
            new_value = await self._collect_kpi_value(kpi_name)
            
            # 更新歷史
            kpi.history.append((datetime.now(), new_value))
            
            # 保留最近 30 天的數據
            cutoff_time = datetime.now() - timedelta(days=30)
            kpi.history = [(ts, val) for ts, val in kpi.history if ts > cutoff_time]
            
            # 計算趨勢
            if len(kpi.history) >= 5:
                recent_values = [val for _, val in kpi.history[-5:]]
                if recent_values[-1] > recent_values[0] * 1.02:
                    kpi.trend = "improving"
                elif recent_values[-1] < recent_values[0] * 0.98:
                    kpi.trend = "degrading"
                else:
                    kpi.trend = "stable"
            
            kpi.current_value = new_value
            kpi.last_updated = datetime.now()
    
    async def _collect_kpi_value(self, kpi_name: str) -> float:
        """收集 KPI 值"""
        # 模擬 KPI 數據收集
        import random
        
        target_value = self.kpis[kpi_name].target_value
        current_value = self.kpis[kpi_name].current_value
        
        # 添加隨機變動
        variation = random.uniform(-0.02, 0.02)  # ±2% 變動
        new_value = current_value * (1 + variation)
        
        # 模擬逐漸向目標值改進的趨勢
        improvement_factor = 0.001  # 每次 0.1% 的改進
        if current_value < target_value:
            new_value += target_value * improvement_factor
        
        return min(new_value, target_value * 1.05)  # 不超過目標值的 105%
    
    async def _detect_performance_trends(self):
        """檢測性能趨勢"""
        performance_kpis = [
            "system_availability", "error_rate", "handover_latency_ms", "handover_success_rate"
        ]
        
        for kpi_name in performance_kpis:
            if kpi_name not in self.kpis:
                continue
                
            kpi = self.kpis[kpi_name]
            
            if kpi.trend == "degrading":
                degradation_threshold = self.config.get("improvement_thresholds", {}).get("performance_degradation_threshold", 0.05)
                
                degradation_rate = (kpi.target_value - kpi.current_value) / kpi.target_value
                
                if degradation_rate > degradation_threshold:
                    await self._create_improvement_opportunity(
                        type=ImprovementType.PERFORMANCE_OPTIMIZATION,
                        priority=ImprovementPriority.HIGH,
                        title=f"{kpi_name} 性能下降",
                        description=f"{kpi_name} 當前值 {kpi.current_value:.4f} 低於目標值 {kpi.target_value:.4f}",
                        target_metrics={kpi_name: kpi.target_value}
                    )
    
    async def _identify_improvement_opportunities(self):
        """識別改進機會"""
        logger.info("🔍 識別改進機會...")
        
        # 分析成本效益
        await self._analyze_cost_efficiency()
        
        # 分析資源利用率
        await self._analyze_resource_utilization()
        
        # 分析客戶體驗
        await self._analyze_customer_experience()
        
        # 分析安全風險
        await self._analyze_security_risks()
        
        logger.info(f"識別到 {len([opp for opp in self.improvement_opportunities.values() if opp.status == ImprovementStatus.IDENTIFIED])} 個新改進機會")
    
    async def _analyze_cost_efficiency(self):
        """分析成本效益"""
        # 模擬成本分析
        cost_increase_threshold = self.config.get("improvement_thresholds", {}).get("cost_increase_threshold", 0.10)
        
        # 檢查成本 KPI
        if "cost_per_transaction" in self.kpis:
            cost_kpi = self.kpis["cost_per_transaction"]
            
            if cost_kpi.current_value > cost_kpi.target_value * (1 + cost_increase_threshold):
                await self._create_improvement_opportunity(
                    type=ImprovementType.COST_REDUCTION,
                    priority=ImprovementPriority.MEDIUM,
                    title="交易成本過高",
                    description=f"每筆交易成本 ${cost_kpi.current_value:.3f} 超過目標 ${cost_kpi.target_value:.3f}",
                    target_metrics={"cost_per_transaction": cost_kpi.target_value}
                )
    
    async def _analyze_resource_utilization(self):
        """分析資源利用率"""
        # 模擬資源利用率分析
        import random
        
        cpu_utilization = random.uniform(0.4, 0.8)
        memory_utilization = random.uniform(0.5, 0.9)
        
        # 如果資源利用率過低，建議優化
        if cpu_utilization < 0.5 or memory_utilization < 0.6:
            await self._create_improvement_opportunity(
                type=ImprovementType.RESOURCE_EFFICIENCY,
                priority=ImprovementPriority.MEDIUM,
                title="資源利用率偏低",
                description=f"CPU 利用率 {cpu_utilization:.1%}, 記憶體利用率 {memory_utilization:.1%}，存在優化空間",
                target_metrics={"cpu_utilization": 0.7, "memory_utilization": 0.75}
            )
    
    async def _analyze_customer_experience(self):
        """分析客戶體驗"""
        if "customer_satisfaction" in self.kpis:
            satisfaction_kpi = self.kpis["customer_satisfaction"]
            
            if satisfaction_kpi.current_value < satisfaction_kpi.target_value * 0.9:
                await self._create_improvement_opportunity(
                    type=ImprovementType.SLA_ENHANCEMENT,
                    priority=ImprovementPriority.HIGH,
                    title="客戶滿意度下降",
                    description=f"客戶滿意度 {satisfaction_kpi.current_value:.2f} 低於目標 {satisfaction_kpi.target_value:.2f}",
                    target_metrics={"customer_satisfaction": satisfaction_kpi.target_value}
                )
    
    async def _analyze_security_risks(self):
        """分析安全風險"""
        # 模擬安全風險分析
        import random
        
        if random.random() < 0.1:  # 10% 機率發現安全改進機會
            await self._create_improvement_opportunity(
                type=ImprovementType.SECURITY_ENHANCEMENT,
                priority=ImprovementPriority.HIGH,
                title="安全配置優化",
                description="檢測到潛在的安全配置改進機會",
                target_metrics={"security_score": 95.0}
            )
    
    async def _create_improvement_opportunity(self, type: ImprovementType, priority: ImprovementPriority,
                                           title: str, description: str, target_metrics: Dict[str, float]):
        """創建改進機會"""
        # 生成唯一 ID
        opportunity_id = hashlib.md5(f"{title}_{datetime.now().isoformat()}".encode()).hexdigest()[:8]
        
        # 檢查是否已存在類似的改進機會
        existing_similar = [
            opp for opp in self.improvement_opportunities.values()
            if opp.title == title and opp.status in [ImprovementStatus.IDENTIFIED, ImprovementStatus.PLANNED, ImprovementStatus.IMPLEMENTING]
        ]
        
        if existing_similar:
            logger.debug(f"類似改進機會已存在: {title}")
            return
        
        # 計算影響評分
        impact_score = await self._calculate_impact_score(target_metrics)
        
        # 計算工作量評分
        effort_score = await self._calculate_effort_score(type, target_metrics)
        
        # 計算 ROI 評分
        roi_score = impact_score / effort_score if effort_score > 0 else 0
        
        # 檢查 ROI 閾值
        min_roi_threshold = self.config.get("continuous_improvement", {}).get("min_roi_threshold", 1.5)
        if roi_score < min_roi_threshold:
            logger.debug(f"改進機會 ROI {roi_score:.2f} 低於閾值 {min_roi_threshold}")
            return
        
        opportunity = ImprovementOpportunity(
            id=opportunity_id,
            type=type,
            priority=priority,
            status=ImprovementStatus.IDENTIFIED,
            title=title,
            description=description,
            impact_score=impact_score,
            effort_score=effort_score,
            roi_score=roi_score,
            identified_at=datetime.now(),
            target_metrics=target_metrics,
            current_metrics={k: self.kpis.get(k, KPI("", 0, 0, "", datetime.now())).current_value for k in target_metrics.keys()}
        )
        
        self.improvement_opportunities[opportunity_id] = opportunity
        
        logger.info(f"💡 識別新改進機會: {title} (ROI: {roi_score:.2f})")
    
    async def _calculate_impact_score(self, target_metrics: Dict[str, float]) -> float:
        """計算影響評分"""
        total_impact = 0
        
        for metric_name, target_value in target_metrics.items():
            if metric_name in self.kpis:
                current_value = self.kpis[metric_name].current_value
                
                # 計算改進百分比
                if "rate" in metric_name or "satisfaction" in metric_name:
                    improvement = (target_value - current_value) / current_value
                else:  # 對於延遲、錯誤率等，值越低越好
                    improvement = (current_value - target_value) / current_value
                
                total_impact += max(0, improvement) * 10  # 0-10 分
        
        return min(total_impact, 10)  # 最高 10 分
    
    async def _calculate_effort_score(self, improvement_type: ImprovementType, target_metrics: Dict[str, float]) -> float:
        """計算工作量評分"""
        # 根據改進類型估算工作量
        base_effort = {
            ImprovementType.PERFORMANCE_OPTIMIZATION: 5,
            ImprovementType.RESOURCE_EFFICIENCY: 3,
            ImprovementType.SLA_ENHANCEMENT: 6,
            ImprovementType.COST_REDUCTION: 4,
            ImprovementType.RELIABILITY_IMPROVEMENT: 7,
            ImprovementType.SECURITY_ENHANCEMENT: 8
        }
        
        effort = base_effort.get(improvement_type, 5)
        
        # 根據影響範圍調整工作量
        if len(target_metrics) > 2:
            effort += 2  # 影響多個指標需要更多工作
        
        return effort
    
    async def _auto_implement_low_risk_improvements(self):
        """自動實施低風險改進"""
        auto_implement = self.config.get("continuous_improvement", {}).get("auto_implement_low_risk", False)
        
        if not auto_implement:
            return
        
        max_concurrent = self.config.get("continuous_improvement", {}).get("max_concurrent_improvements", 3)
        
        # 統計當前實施中的改進
        implementing_count = len([
            opp for opp in self.improvement_opportunities.values()
            if opp.status == ImprovementStatus.IMPLEMENTING
        ])
        
        if implementing_count >= max_concurrent:
            logger.debug(f"已達到最大並發改進數量 {max_concurrent}")
            return
        
        # 查找低風險改進機會
        low_risk_opportunities = [
            opp for opp in self.improvement_opportunities.values()
            if (opp.status == ImprovementStatus.IDENTIFIED and
                opp.effort_score <= 3 and
                opp.roi_score >= 3 and
                opp.type in [ImprovementType.RESOURCE_EFFICIENCY, ImprovementType.PERFORMANCE_OPTIMIZATION])
        ]
        
        # 按 ROI 排序
        low_risk_opportunities.sort(key=lambda x: x.roi_score, reverse=True)
        
        # 自動實施前幾個低風險改進
        for opportunity in low_risk_opportunities[:max_concurrent - implementing_count]:
            await self._implement_improvement(opportunity)
    
    async def _implement_improvement(self, opportunity: ImprovementOpportunity):
        """實施改進"""
        logger.info(f"🔧 開始實施改進: {opportunity.title}")
        
        opportunity.status = ImprovementStatus.IMPLEMENTING
        
        try:
            # 根據改進類型執行相應的實施步驟
            if opportunity.type == ImprovementType.PERFORMANCE_OPTIMIZATION:
                await self._implement_performance_optimization(opportunity)
            elif opportunity.type == ImprovementType.RESOURCE_EFFICIENCY:
                await self._implement_resource_optimization(opportunity)
            elif opportunity.type == ImprovementType.COST_REDUCTION:
                await self._implement_cost_optimization(opportunity)
            else:
                await self._implement_generic_improvement(opportunity)
            
            opportunity.status = ImprovementStatus.TESTING
            logger.info(f"✅ 改進實施完成，進入測試階段: {opportunity.title}")
            
        except Exception as e:
            opportunity.status = ImprovementStatus.FAILED
            logger.error(f"❌ 改進實施失敗: {opportunity.title} - {e}")
    
    async def _verify_improvement_effects(self):
        """驗證改進效果"""
        testing_improvements = [
            opp for opp in self.improvement_opportunities.values()
            if opp.status == ImprovementStatus.TESTING
        ]
        
        for opportunity in testing_improvements:
            # 檢查改進是否已測試足夠時間
            days_since_implementation = (datetime.now() - opportunity.identified_at).days
            
            if days_since_implementation >= 3:  # 至少測試 3 天
                success = await self._measure_improvement_success(opportunity)
                
                if success:
                    opportunity.status = ImprovementStatus.VERIFIED
                    logger.info(f"✅ 改進效果驗證成功: {opportunity.title}")
                else:
                    opportunity.status = ImprovementStatus.FAILED
                    logger.warning(f"⚠️ 改進效果未達預期: {opportunity.title}")
    
    async def _measure_improvement_success(self, opportunity: ImprovementOpportunity) -> bool:
        """測量改進成功率"""
        success_count = 0
        total_metrics = len(opportunity.target_metrics)
        
        for metric_name, target_value in opportunity.target_metrics.items():
            if metric_name in self.kpis:
                current_value = self.kpis[metric_name].current_value
                original_value = opportunity.current_metrics.get(metric_name, current_value)
                
                # 檢查是否達到改進目標
                if "rate" in metric_name or "satisfaction" in metric_name:
                    # 值越高越好的指標
                    if current_value > original_value:
                        success_count += 1
                else:
                    # 值越低越好的指標
                    if current_value < original_value:
                        success_count += 1
        
        success_rate = success_count / total_metrics if total_metrics > 0 else 0
        return success_rate >= 0.7  # 70% 的指標改善算成功
    
    # 實施方法（模擬實現）
    async def _implement_performance_optimization(self, opportunity: ImprovementOpportunity):
        """實施性能優化"""
        await asyncio.sleep(2)  # 模擬實施時間
    
    async def _implement_resource_optimization(self, opportunity: ImprovementOpportunity):
        """實施資源優化"""
        await asyncio.sleep(1)
    
    async def _implement_cost_optimization(self, opportunity: ImprovementOpportunity):
        """實施成本優化"""
        await asyncio.sleep(3)
    
    async def _implement_generic_improvement(self, opportunity: ImprovementOpportunity):
        """實施通用改進"""
        await asyncio.sleep(2)
    
    async def _generate_improvement_report(self):
        """生成改進報告"""
        logger.info("📊 生成持續改進報告")
        
        # 統計改進狀態
        status_counts = {}
        for status in ImprovementStatus:
            status_counts[status.value] = len([
                opp for opp in self.improvement_opportunities.values()
                if opp.status == status
            ])
        
        # 計算總體改進指標
        verified_improvements = [
            opp for opp in self.improvement_opportunities.values()
            if opp.status == ImprovementStatus.VERIFIED
        ]
        
        if verified_improvements:
            avg_roi = statistics.mean([opp.roi_score for opp in verified_improvements])
            total_impact = sum([opp.impact_score for opp in verified_improvements])
        else:
            avg_roi = 0
            total_impact = 0
        
        report = {
            "report_date": datetime.now().isoformat(),
            "improvement_status_summary": status_counts,
            "total_opportunities": len(self.improvement_opportunities),
            "verified_improvements": len(verified_improvements),
            "average_roi": avg_roi,
            "total_impact_score": total_impact,
            "kpi_status": {
                name: {
                    "current": kpi.current_value,
                    "target": kpi.target_value,
                    "trend": kpi.trend,
                    "achievement_rate": (kpi.current_value / kpi.target_value) * 100
                }
                for name, kpi in self.kpis.items()
            }
        }
        
        # 保存報告
        report_path = f"improvement_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📋 改進報告已保存: {report_path}")
    
    async def _update_improvement_metrics(self):
        """更新改進指標"""
        current_time = datetime.now()
        
        # 計算改進指標
        identified_count = len([opp for opp in self.improvement_opportunities.values() if opp.status == ImprovementStatus.IDENTIFIED])
        implemented_count = len([opp for opp in self.improvement_opportunities.values() if opp.status in [ImprovementStatus.DEPLOYED, ImprovementStatus.VERIFIED]])
        
        # 計算平均實施時間
        completed_improvements = [
            opp for opp in self.improvement_opportunities.values()
            if opp.status in [ImprovementStatus.DEPLOYED, ImprovementStatus.VERIFIED]
        ]
        
        if completed_improvements:
            avg_implementation_time = statistics.mean([
                (current_time - opp.identified_at).days
                for opp in completed_improvements
            ])
        else:
            avg_implementation_time = 0
        
        metrics = ImprovementMetrics(
            timestamp=current_time,
            improvements_identified=identified_count,
            improvements_implemented=implemented_count,
            average_implementation_time_days=avg_implementation_time,
            total_cost_savings=sum([opp.impact_score * 1000 for opp in completed_improvements]),  # 模擬成本節省
            performance_improvement_percentage=5.0,  # 模擬性能改善
            sla_compliance_improvement=2.0,  # 模擬 SLA 改善
            customer_satisfaction_score=self.kpis.get("customer_satisfaction", KPI("", 4.0, 4.5, "", current_time)).current_value
        )
        
        self.improvement_history.append(metrics)
    
    # 其他輔助方法
    async def _monitor_sla_compliance(self):
        """監控 SLA 合規性"""
        sla_violation_threshold = self.config.get("improvement_thresholds", {}).get("sla_violation_threshold", 0.02)
        
        sla_kpis = ["system_availability", "error_rate", "handover_latency_ms", "handover_success_rate"]
        
        for kpi_name in sla_kpis:
            if kpi_name not in self.kpis:
                continue
            
            kpi = self.kpis[kpi_name]
            
            # 計算 SLA 違規程度
            if "rate" in kpi_name or "availability" in kpi_name:
                violation_rate = max(0, (kpi.target_value - kpi.current_value) / kpi.target_value)
            else:
                violation_rate = max(0, (kpi.current_value - kpi.target_value) / kpi.target_value)
            
            if violation_rate > sla_violation_threshold:
                await self._create_improvement_opportunity(
                    type=ImprovementType.SLA_ENHANCEMENT,
                    priority=ImprovementPriority.CRITICAL,
                    title=f"{kpi_name} SLA 違規",
                    description=f"{kpi_name} 違規率 {violation_rate:.2%}，需要立即改進",
                    target_metrics={kpi_name: kpi.target_value}
                )
    
    async def _check_pending_improvements(self):
        """檢查待實施改進"""
        pending_improvements = [
            opp for opp in self.improvement_opportunities.values()
            if opp.status == ImprovementStatus.IDENTIFIED
        ]
        
        # 按優先級和 ROI 排序
        pending_improvements.sort(key=lambda x: (x.priority.value, -x.roi_score))
        
        logger.info(f"當前有 {len(pending_improvements)} 個待實施的改進機會")
    
    def get_improvement_status(self) -> Dict[str, Any]:
        """獲取改進狀態"""
        return {
            "is_running": self.is_running,
            "total_opportunities": len(self.improvement_opportunities),
            "opportunities_by_status": {
                status.value: len([opp for opp in self.improvement_opportunities.values() if opp.status == status])
                for status in ImprovementStatus
            },
            "kpi_summary": {
                name: {
                    "current": kpi.current_value,
                    "target": kpi.target_value,
                    "trend": kpi.trend
                }
                for name, kpi in self.kpis.items()
            },
            "last_updated": datetime.now().isoformat()
        }

# 輔助類
class PatternAnalyzer:
    """模式分析器"""
    
    def analyze_patterns(self, data: List[Any]) -> Dict[str, Any]:
        return {"patterns_found": 0}

class AnomalyDetector:
    """異常檢測器"""
    
    def detect_anomalies(self, data: List[Any]) -> List[Any]:
        return []

class RecommendationEngine:
    """推薦引擎"""
    
    def generate_recommendations(self, context: Dict[str, Any]) -> List[str]:
        return []

# 使用示例
async def main():
    """持續改進示例"""
    
    # 創建配置
    config = {
        "continuous_improvement": {
            "analysis_interval_hours": 1,  # 縮短為示例
            "implementation_check_interval_hours": 2,
            "min_roi_threshold": 1.5,
            "max_concurrent_improvements": 3,
            "auto_implement_low_risk": True
        },
        "kpi_targets": {
            "system_availability": 0.9995,
            "error_rate": 0.0005,
            "handover_latency_ms": 45.0,
            "handover_success_rate": 0.997,
            "customer_satisfaction": 4.5
        }
    }
    
    config_path = "/tmp/continuous_improvement_config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    # 初始化持續改進引擎
    improvement_engine = ContinuousImprovementEngine(config_path)
    
    # 啟動持續改進
    try:
        print("🚀 啟動持續監控和改進機制...")
        
        # 運行一段時間
        improvement_task = asyncio.create_task(improvement_engine.start_continuous_improvement())
        
        # 等待並查看狀態
        await asyncio.sleep(30)
        
        status = improvement_engine.get_improvement_status()
        print(f"改進狀態: {json.dumps(status, ensure_ascii=False, indent=2)}")
        
        # 停止改進引擎
        await improvement_engine.stop_continuous_improvement()
        improvement_task.cancel()
        
        print("\n" + "="*60)
        print("🎉 持續監控和改進機制運行成功！")
        print("="*60)
        
    except KeyboardInterrupt:
        print("停止持續改進系統")
        await improvement_engine.stop_continuous_improvement()

if __name__ == "__main__":
    asyncio.run(main())