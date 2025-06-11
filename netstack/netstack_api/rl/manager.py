"""
統一 AI 服務管理器

提供統一的服務接口，支持：
- 動態引擎切換
- 配置驅動管理
- 優雅降級
- A/B 測試
"""

import os
import asyncio
from typing import Dict, Any, Optional, List, Type
import structlog
from datetime import datetime

from .engine import RLEngine, GymnasiumEngine, LegacyEngine, NullEngine
from .config import RLConfig

logger = structlog.get_logger(__name__)

class UnifiedAIService:
    """統一 AI 服務類"""
    
    def __init__(self, 
                 service_name: str,
                 engine: Optional[RLEngine] = None, 
                 config: Optional[Dict] = None):
        
        self.service_name = service_name
        self.config = RLConfig(config or {})
        self.engine = engine or self._create_default_engine()
        
        # 性能監控
        self.request_count = 0
        self.error_count = 0
        self.last_error = None
        self.response_times = []
        
        # 健康檢查
        self.health_status = "healthy"
        self.last_health_check = datetime.now()
        
        logger.info("統一 AI 服務初始化", 
                   service_name=service_name, 
                   engine_type=self.engine.engine_type)
    
    def _create_default_engine(self) -> RLEngine:
        """創建默認引擎"""
        engine_type = self.config.get_engine_type(self.service_name)
        
        if engine_type == "gymnasium":
            return self._create_gymnasium_engine()
        elif engine_type == "legacy":
            return self._create_legacy_engine()
        elif engine_type == "disabled":
            return NullEngine()
        else:
            logger.warning("未知引擎類型，使用 Null 引擎", 
                         engine_type=engine_type,
                         service_name=self.service_name)
            return NullEngine()
    
    def _create_gymnasium_engine(self) -> GymnasiumEngine:
        """創建 Gymnasium 引擎"""
        try:
            env_mapping = {
                "interference": "netstack/InterferenceMitigation-v0",
                "optimization": "netstack/NetworkOptimization-v0", 
                "uav": "netstack/UAVFormation-v0"
            }
            
            # 根據服務名稱選擇環境
            env_name = None
            for key, env in env_mapping.items():
                if key in self.service_name.lower():
                    env_name = env
                    break
            
            if env_name is None:
                env_name = env_mapping["optimization"]  # 默認
                
            algorithm = self.config.get_algorithm(self.service_name)
            config = self.config.get_engine_config(self.service_name)
            
            return GymnasiumEngine(env_name, algorithm, config)
            
        except Exception as e:
            logger.error("創建 Gymnasium 引擎失敗", error=str(e))
            return NullEngine()
    
    def _create_legacy_engine(self) -> LegacyEngine:
        """創建傳統引擎"""
        try:
            # 這裡需要根據服務名稱載入對應的傳統服務
            # 暫時返回空引擎
            logger.info("傳統引擎創建（待實現具體服務載入）")
            return NullEngine()
            
        except Exception as e:
            logger.error("創建傳統引擎失敗", error=str(e))
            return NullEngine()
    
    async def make_decision(self, 
                          input_data: Dict[str, Any],
                          context: Optional[Dict] = None) -> Dict[str, Any]:
        """統一決策接口"""
        
        start_time = asyncio.get_event_loop().time()
        self.request_count += 1
        
        try:
            # 預處理輸入數據
            processed_state = self._preprocess_input(input_data, context)
            
            # 健康檢查
            if not await self._health_check():
                return await self._fallback_decision(input_data)
            
            # 獲取決策
            action = await self.engine.get_action(processed_state)
            
            # 後處理結果
            result = self._postprocess_output(action, input_data)
            
            # 記錄響應時間
            response_time = asyncio.get_event_loop().time() - start_time
            self.response_times.append(response_time)
            if len(self.response_times) > 100:
                self.response_times = self.response_times[-50:]
            
            # 記錄成功
            logger.debug("決策成功", 
                        service_name=self.service_name,
                        response_time=response_time,
                        engine_type=self.engine.engine_type)
            
            return {
                "status": "success",
                "action": result,
                "metadata": {
                    "service_name": self.service_name,
                    "engine_type": self.engine.engine_type,
                    "response_time": response_time,
                    "request_id": self.request_count
                }
            }
            
        except Exception as e:
            self.error_count += 1
            self.last_error = str(e)
            
            logger.error("決策失敗", 
                        error=str(e),
                        service_name=self.service_name,
                        engine_type=self.engine.engine_type)
            
            # 嘗試降級處理
            try:
                fallback_result = await self._fallback_decision(input_data)
                return {
                    "status": "fallback",
                    "action": fallback_result,
                    "error": str(e),
                    "metadata": {
                        "service_name": self.service_name,
                        "engine_type": "fallback"
                    }
                }
            except Exception as fallback_error:
                return {
                    "status": "error",
                    "error": str(e),
                    "fallback_error": str(fallback_error),
                    "metadata": {
                        "service_name": self.service_name
                    }
                }
    
    async def learn(self, experience: Dict[str, Any]) -> Dict[str, Any]:
        """學習接口"""
        try:
            result = await self.engine.update(experience)
            
            logger.debug("學習完成",
                        service_name=self.service_name,
                        result=result)
            
            return result
            
        except Exception as e:
            logger.error("學習失敗", error=str(e))
            return {"status": "error", "message": str(e)}
    
    async def train(self, episodes: int = 1000) -> Dict[str, Any]:
        """訓練接口"""
        try:
            logger.info("開始訓練",
                       service_name=self.service_name,
                       episodes=episodes)
            
            result = await self.engine.train(episodes)
            
            logger.info("訓練完成",
                       service_name=self.service_name,
                       result=result)
            
            return result
            
        except Exception as e:
            logger.error("訓練失敗", error=str(e))
            return {"status": "error", "message": str(e)}
    
    def switch_engine(self, new_engine: RLEngine):
        """動態切換引擎"""
        old_engine_type = self.engine.engine_type
        self.engine = new_engine
        
        logger.info("引擎切換成功",
                   service_name=self.service_name,
                   old_engine=old_engine_type,
                   new_engine=new_engine.engine_type)
    
    async def _health_check(self) -> bool:
        """健康檢查"""
        try:
            # 檢查錯誤率
            if self.request_count > 10:
                error_rate = self.error_count / self.request_count
                if error_rate > 0.5:  # 錯誤率超過 50%
                    self.health_status = "unhealthy"
                    return False
            
            # 檢查響應時間
            if len(self.response_times) > 5:
                avg_response_time = sum(self.response_times[-5:]) / 5
                if avg_response_time > 10.0:  # 響應時間超過 10 秒
                    self.health_status = "slow"
                    return False
            
            # 檢查引擎狀態
            engine_status = await self.engine.get_status()
            if engine_status.get("status") == "error":
                self.health_status = "engine_error"
                return False
            
            self.health_status = "healthy"
            self.last_health_check = datetime.now()
            return True
            
        except Exception as e:
            logger.error("健康檢查失敗", error=str(e))
            self.health_status = "check_failed"
            return False
    
    def _preprocess_input(self, 
                         input_data: Dict[str, Any], 
                         context: Optional[Dict] = None) -> Dict[str, Any]:
        """預處理輸入數據"""
        
        processed = input_data.copy()
        
        # 添加上下文信息
        if context:
            processed.update(context)
        
        # 添加服務特定的預處理
        processed["service_name"] = self.service_name
        processed["timestamp"] = datetime.now().isoformat()
        
        # 數據驗證和清理
        if "sinr" in processed and processed["sinr"] is None:
            processed["sinr"] = 0.0
        
        if "position" in processed and not isinstance(processed["position"], (list, tuple)):
            processed["position"] = [0.0, 0.0, 0.0]
        
        return processed
    
    def _postprocess_output(self, 
                           action: Dict[str, Any], 
                           original_input: Dict[str, Any]) -> Dict[str, Any]:
        """後處理輸出結果"""
        
        result = action.copy()
        
        # 添加元數據
        result["generated_at"] = datetime.now().isoformat()
        result["service_name"] = self.service_name
        result["engine_type"] = self.engine.engine_type
        
        # 結果驗證
        if "error" in result:
            logger.warning("引擎返回錯誤", error=result["error"])
        
        return result
    
    async def _fallback_decision(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """降級決策"""
        
        # 簡單的啟發式決策
        if "interference" in self.service_name.lower():
            return {
                "power_control": 0.5,
                "frequency_selection": 0.0,
                "beam_direction": 0.0,
                "spread_factor": 0.5,
                "fallback": True
            }
        elif "optimization" in self.service_name.lower():
            return {
                "bandwidth_allocation": 0.6,
                "qos_priority": 0.7,
                "load_balancing": 0.5,
                "cache_policy": 0.4,
                "fallback": True
            }
        elif "uav" in self.service_name.lower():
            return {
                "action": "maintain_formation",
                "fallback": True
            }
        else:
            return {
                "action": "no_change",
                "fallback": True
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """獲取服務狀態"""
        return {
            "service_name": self.service_name,
            "health_status": self.health_status,
            "engine_type": self.engine.engine_type,
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(1, self.request_count),
            "avg_response_time": sum(self.response_times[-10:]) / max(1, len(self.response_times[-10:])),
            "last_error": self.last_error,
            "last_health_check": self.last_health_check.isoformat(),
            "engine_status": await self.engine.get_status()
        }

class ServiceContainer:
    """服務容器"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = RLConfig(config or {})
        self.services: Dict[str, UnifiedAIService] = {}
        self.service_configs: Dict[str, Dict] = {}
        
        logger.info("服務容器初始化")
    
    def register_service(self, 
                        service_name: str, 
                        service_config: Optional[Dict] = None,
                        engine: Optional[RLEngine] = None) -> UnifiedAIService:
        """註冊服務"""
        
        if service_name in self.services:
            logger.warning("服務已存在，將覆蓋", service_name=service_name)
        
        # 合併配置
        merged_config = self.config.config.copy()
        if service_config:
            merged_config.update(service_config)
        
        # 創建服務
        service = UnifiedAIService(
            service_name=service_name,
            engine=engine,
            config=merged_config
        )
        
        self.services[service_name] = service
        self.service_configs[service_name] = merged_config
        
        logger.info("服務註冊成功", service_name=service_name)
        return service
    
    def get_service(self, service_name: str) -> Optional[UnifiedAIService]:
        """獲取服務"""
        return self.services.get(service_name)
    
    def remove_service(self, service_name: str) -> bool:
        """移除服務"""
        if service_name in self.services:
            del self.services[service_name]
            if service_name in self.service_configs:
                del self.service_configs[service_name]
            
            logger.info("服務移除成功", service_name=service_name)
            return True
        
        logger.warning("服務不存在", service_name=service_name)
        return False
    
    def list_services(self) -> List[str]:
        """列出所有服務"""
        return list(self.services.keys())
    
    async def get_all_status(self) -> Dict[str, Dict]:
        """獲取所有服務狀態"""
        status = {}
        
        for service_name, service in self.services.items():
            try:
                status[service_name] = await service.get_status()
            except Exception as e:
                status[service_name] = {
                    "error": str(e),
                    "status": "failed_to_get_status"
                }
        
        return status
    
    def enable_service(self, service_name: str) -> bool:
        """啟用服務"""
        if service_name not in self.services:
            return False
        
        service = self.services[service_name]
        if isinstance(service.engine, NullEngine):
            # 重新創建引擎
            service.engine = service._create_default_engine()
            logger.info("服務已啟用", service_name=service_name)
        
        return True
    
    def disable_service(self, service_name: str) -> bool:
        """禁用服務"""
        if service_name not in self.services:
            return False
        
        service = self.services[service_name]
        service.switch_engine(NullEngine())
        
        logger.info("服務已禁用", service_name=service_name)
        return True
    
    async def health_check_all(self) -> Dict[str, bool]:
        """檢查所有服務健康狀態"""
        results = {}
        
        for service_name, service in self.services.items():
            try:
                status = await service.get_status()
                results[service_name] = status["health_status"] == "healthy"
            except Exception as e:
                logger.error("健康檢查失敗", service_name=service_name, error=str(e))
                results[service_name] = False
        
        return results

# 全局服務容器實例
_global_container: Optional[ServiceContainer] = None

def get_service_container() -> ServiceContainer:
    """獲取全局服務容器"""
    global _global_container
    if _global_container is None:
        _global_container = ServiceContainer()
    return _global_container

def initialize_container(config: Optional[Dict] = None) -> ServiceContainer:
    """初始化全局服務容器"""
    global _global_container
    _global_container = ServiceContainer(config)
    return _global_container