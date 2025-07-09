"""
3D 換手協調器
=============

協調與 HandoverAnimation3D 的整合，提供 3D 視覺化功能。
"""

import asyncio
import uuid
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict

from ..interfaces.visualization_coordinator import (
    VisualizationCoordinatorInterface,
    VisualizationEvent,
    AnimationType,
    AnimationState,
    AnimationNotFoundError,
)
from .realtime_event_streamer import RealtimeEventStreamer

logger = logging.getLogger(__name__)


class Handover3DCoordinator(VisualizationCoordinatorInterface):
    """
    3D 換手協調器實現
    
    負責協調與 HandoverAnimation3D 組件的整合：
    - 3D 動畫觸發
    - 前端狀態同步
    - 即時事件推送
    - 動畫狀態管理
    """

    def __init__(self, event_streamer: RealtimeEventStreamer,
                 config: Optional[Dict[str, Any]] = None):
        """
        初始化 3D 換手協調器
        
        Args:
            event_streamer: 即時事件推送器
            config: 配置參數
        """
        self.event_streamer = event_streamer
        self.config = config or {}
        self.logger = logger.bind(component="handover_3d_coordinator")
        
        # 動畫狀態管理
        self.animations: Dict[str, AnimationState] = {}
        self.animation_queue: List[VisualizationEvent] = []
        self.active_handovers: Dict[str, Dict[str, Any]] = {}
        
        # 衛星位置快取
        self.satellite_positions: Dict[str, Dict[str, Any]] = {}
        self.last_position_update = 0.0
        
        # 配置參數
        self.default_animation_duration = self.config.get("default_duration", 3000)
        self.max_concurrent_animations = self.config.get("max_concurrent", 5)
        self.position_update_interval = self.config.get("position_update_interval", 1.0)
        
        # 動畫預設參數
        self.animation_defaults = {
            "handover_started": {
                "highlight_source": True,
                "show_signal_lines": True,
                "camera_follow": False,
                "duration": 2000,
            },
            "candidate_selection": {
                "highlight_candidates": True,
                "show_scoring_indicators": True,
                "fade_non_candidates": True,
                "duration": 1500,
            },
            "decision_made": {
                "highlight_selected": True,
                "show_handover_path": True,
                "camera_follow": True,
                "duration": 3000,
            },
            "execution_complete": {
                "show_success_indicator": True,
                "update_connections": True,
                "cleanup_indicators": True,
                "duration": 1000,
            },
        }
        
        self.logger.info("3D 換手協調器初始化完成")

    async def trigger_3d_animation(self, event: VisualizationEvent) -> str:
        """
        觸發 3D 動畫更新
        
        Args:
            event: 視覺化事件
            
        Returns:
            str: 動畫ID
        """
        animation_id = str(uuid.uuid4())
        
        try:
            # 檢查並發限制
            if len(self.get_active_animations()) >= self.max_concurrent_animations:
                self.logger.warning("達到最大並發動畫數限制，將事件加入隊列")
                self.animation_queue.append(event)
                return animation_id
            
            # 創建動畫狀態
            animation_state = AnimationState(
                animation_id=animation_id,
                status="active",
                progress=0.0,
                start_time=event.timestamp,
                duration=event.duration_ms / 1000.0,
                parameters=event.animation_params,
            )
            
            self.animations[animation_id] = animation_state
            
            # 構建動畫指令
            animation_command = await self._build_animation_command(event, animation_id)
            
            # 推送到前端
            await self.event_streamer.broadcast_event(animation_command)
            
            # 更新活躍換手記錄
            if event.event_type == AnimationType.HANDOVER_STARTED:
                await self._track_handover_start(event, animation_id)
            elif event.event_type == AnimationType.EXECUTION_COMPLETE:
                await self._track_handover_complete(event, animation_id)
            
            # 啟動動畫進度追蹤
            asyncio.create_task(self._track_animation_progress(animation_id))
            
            self.logger.info(
                "3D 動畫觸發成功",
                animation_id=animation_id,
                event_type=event.event_type.value,
                duration=event.duration_ms,
            )
            
            return animation_id
            
        except Exception as e:
            self.logger.error("3D 動畫觸發失敗", animation_id=animation_id, error=str(e))
            if animation_id in self.animations:
                self.animations[animation_id].status = "failed"
            raise

    async def sync_with_frontend(self, state: Dict[str, Any]) -> None:
        """
        與前端同步狀態
        
        Args:
            state: 要同步的狀態數據
        """
        try:
            sync_command = {
                "type": "state_sync",
                "timestamp": datetime.now().timestamp(),
                "handover_state": state,
                "animation_state": {
                    "active_animations": len(self.get_active_animations()),
                    "queued_animations": len(self.animation_queue),
                    "active_handovers": len(self.active_handovers),
                },
                "satellite_positions": self.satellite_positions,
            }
            
            await self.event_streamer.broadcast_event(sync_command)
            
            self.logger.debug("前端狀態同步完成", state_keys=list(state.keys()))
            
        except Exception as e:
            self.logger.error("前端狀態同步失敗", error=str(e))

    async def stream_realtime_updates(self, decision_flow: Dict[str, Any]) -> None:
        """
        推送即時決策流程更新
        
        Args:
            decision_flow: 決策流程數據
        """
        try:
            update_command = {
                "type": "realtime_update",
                "timestamp": datetime.now().timestamp(),
                "decision_flow": decision_flow,
                "flow_stage": decision_flow.get("current_stage", "unknown"),
                "progress": decision_flow.get("progress", 0.0),
            }
            
            await self.event_streamer.broadcast_event(update_command)
            
            self.logger.debug("即時更新推送完成", stage=decision_flow.get("current_stage"))
            
        except Exception as e:
            self.logger.error("即時更新推送失敗", error=str(e))

    async def update_satellite_positions(self, satellite_positions: List[Dict[str, Any]]) -> None:
        """
        更新衛星位置
        
        Args:
            satellite_positions: 衛星位置列表
        """
        try:
            current_time = datetime.now().timestamp()
            
            # 更新位置快取
            for sat_pos in satellite_positions:
                sat_id = sat_pos.get("satellite_id")
                if sat_id:
                    self.satellite_positions[sat_id] = {
                        **sat_pos,
                        "last_update": current_time,
                    }
            
            # 檢查是否需要推送更新
            if current_time - self.last_position_update > self.position_update_interval:
                position_update = {
                    "type": "satellite_position_update",
                    "timestamp": current_time,
                    "positions": satellite_positions,
                    "update_count": len(satellite_positions),
                }
                
                await self.event_streamer.broadcast_event(position_update)
                self.last_position_update = current_time
                
                self.logger.debug(
                    "衛星位置更新完成",
                    satellite_count=len(satellite_positions),
                )
            
        except Exception as e:
            self.logger.error("衛星位置更新失敗", error=str(e))

    async def highlight_selected_satellite(self, satellite_id: str, 
                                         highlight_params: Dict[str, Any]) -> None:
        """
        高亮顯示選中的衛星
        
        Args:
            satellite_id: 衛星ID
            highlight_params: 高亮參數
        """
        try:
            highlight_command = {
                "type": "satellite_highlight",
                "timestamp": datetime.now().timestamp(),
                "satellite_id": satellite_id,
                "highlight_params": {
                    "color": highlight_params.get("color", "#00ff00"),
                    "intensity": highlight_params.get("intensity", 1.0),
                    "duration": highlight_params.get("duration", 2000),
                    "pulse_effect": highlight_params.get("pulse_effect", True),
                    **highlight_params,
                },
            }
            
            await self.event_streamer.broadcast_event(highlight_command)
            
            self.logger.debug("衛星高亮完成", satellite_id=satellite_id)
            
        except Exception as e:
            self.logger.error("衛星高亮失敗", satellite_id=satellite_id, error=str(e))

    async def show_handover_path(self, source_id: str, target_id: str,
                               path_params: Dict[str, Any]) -> str:
        """
        顯示換手路徑動畫
        
        Args:
            source_id: 源衛星ID
            target_id: 目標衛星ID
            path_params: 路徑參數
            
        Returns:
            str: 動畫ID
        """
        animation_id = str(uuid.uuid4())
        
        try:
            path_command = {
                "type": "handover_path_animation",
                "animation_id": animation_id,
                "timestamp": datetime.now().timestamp(),
                "source_satellite": source_id,
                "target_satellite": target_id,
                "path_params": {
                    "path_type": path_params.get("path_type", "arc"),
                    "color": path_params.get("color", "#ffff00"),
                    "width": path_params.get("width", 2.0),
                    "duration": path_params.get("duration", 3000),
                    "show_direction": path_params.get("show_direction", True),
                    "animate_flow": path_params.get("animate_flow", True),
                    **path_params,
                },
            }
            
            # 創建動畫狀態
            animation_state = AnimationState(
                animation_id=animation_id,
                status="active",
                progress=0.0,
                start_time=datetime.now().timestamp(),
                duration=path_params.get("duration", 3000) / 1000.0,
                parameters=path_params,
            )
            
            self.animations[animation_id] = animation_state
            
            # 推送路徑動畫
            await self.event_streamer.broadcast_event(path_command)
            
            # 啟動進度追蹤
            asyncio.create_task(self._track_animation_progress(animation_id))
            
            self.logger.info(
                "換手路徑動畫啟動",
                animation_id=animation_id,
                source=source_id,
                target=target_id,
            )
            
            return animation_id
            
        except Exception as e:
            self.logger.error(
                "換手路徑動畫失敗",
                animation_id=animation_id,
                source=source_id,
                target=target_id,
                error=str(e),
            )
            if animation_id in self.animations:
                self.animations[animation_id].status = "failed"
            raise

    async def update_network_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        更新網路指標顯示
        
        Args:
            metrics: 網路指標數據
        """
        try:
            metrics_command = {
                "type": "network_metrics_update",
                "timestamp": datetime.now().timestamp(),
                "metrics": metrics,
                "display_config": {
                    "show_latency": metrics.get("show_latency", True),
                    "show_throughput": metrics.get("show_throughput", True),
                    "show_packet_loss": metrics.get("show_packet_loss", True),
                    "update_interval": metrics.get("update_interval", 1000),
                },
            }
            
            await self.event_streamer.broadcast_event(metrics_command)
            
            self.logger.debug("網路指標更新完成", metrics_count=len(metrics))
            
        except Exception as e:
            self.logger.error("網路指標更新失敗", error=str(e))

    def get_animation_state(self, animation_id: str) -> Optional[AnimationState]:
        """
        獲取動畫狀態
        
        Args:
            animation_id: 動畫ID
            
        Returns:
            Optional[AnimationState]: 動畫狀態
        """
        return self.animations.get(animation_id)

    def get_active_animations(self) -> List[AnimationState]:
        """
        獲取所有活躍動畫
        
        Returns:
            List[AnimationState]: 活躍動畫列表
        """
        return [
            anim for anim in self.animations.values()
            if anim.status == "active"
        ]

    async def pause_animation(self, animation_id: str) -> bool:
        """
        暫停動畫
        
        Args:
            animation_id: 動畫ID
            
        Returns:
            bool: 是否成功暫停
        """
        try:
            if animation_id not in self.animations:
                raise AnimationNotFoundError(f"動畫未找到: {animation_id}")
            
            animation = self.animations[animation_id]
            if animation.status != "active":
                return False
            
            animation.status = "paused"
            
            # 推送暫停指令
            pause_command = {
                "type": "animation_control",
                "action": "pause",
                "animation_id": animation_id,
                "timestamp": datetime.now().timestamp(),
            }
            
            await self.event_streamer.broadcast_event(pause_command)
            
            self.logger.debug("動畫暫停成功", animation_id=animation_id)
            return True
            
        except Exception as e:
            self.logger.error("動畫暫停失敗", animation_id=animation_id, error=str(e))
            return False

    async def resume_animation(self, animation_id: str) -> bool:
        """
        恢復動畫
        
        Args:
            animation_id: 動畫ID
            
        Returns:
            bool: 是否成功恢復
        """
        try:
            if animation_id not in self.animations:
                raise AnimationNotFoundError(f"動畫未找到: {animation_id}")
            
            animation = self.animations[animation_id]
            if animation.status != "paused":
                return False
            
            animation.status = "active"
            
            # 推送恢復指令
            resume_command = {
                "type": "animation_control",
                "action": "resume",
                "animation_id": animation_id,
                "timestamp": datetime.now().timestamp(),
            }
            
            await self.event_streamer.broadcast_event(resume_command)
            
            self.logger.debug("動畫恢復成功", animation_id=animation_id)
            return True
            
        except Exception as e:
            self.logger.error("動畫恢復失敗", animation_id=animation_id, error=str(e))
            return False

    async def cancel_animation(self, animation_id: str) -> bool:
        """
        取消動畫
        
        Args:
            animation_id: 動畫ID
            
        Returns:
            bool: 是否成功取消
        """
        try:
            if animation_id not in self.animations:
                raise AnimationNotFoundError(f"動畫未找到: {animation_id}")
            
            animation = self.animations[animation_id]
            animation.status = "cancelled"
            
            # 推送取消指令
            cancel_command = {
                "type": "animation_control",
                "action": "cancel",
                "animation_id": animation_id,
                "timestamp": datetime.now().timestamp(),
            }
            
            await self.event_streamer.broadcast_event(cancel_command)
            
            self.logger.debug("動畫取消成功", animation_id=animation_id)
            return True
            
        except Exception as e:
            self.logger.error("動畫取消失敗", animation_id=animation_id, error=str(e))
            return False

    # 私有方法
    async def _build_animation_command(self, event: VisualizationEvent, animation_id: str) -> Dict[str, Any]:
        """構建動畫指令"""
        # 獲取默認參數
        default_params = self.animation_defaults.get(event.event_type.value, {})
        
        # 合併參數
        animation_params = {**default_params, **event.animation_params}
        
        command = {
            "type": "animation_trigger",
            "animation_id": animation_id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp,
            "satellite_data": event.satellite_data,
            "animation_params": animation_params,
            "duration_ms": event.duration_ms,
            "priority": event.priority,
        }
        
        return command

    async def _track_animation_progress(self, animation_id: str):
        """追蹤動畫進度"""
        if animation_id not in self.animations:
            return
            
        animation = self.animations[animation_id]
        start_time = animation.start_time
        duration = animation.duration
        
        try:
            while animation.status == "active":
                current_time = datetime.now().timestamp()
                elapsed = current_time - start_time
                progress = min(elapsed / duration, 1.0)
                
                animation.progress = progress
                
                # 動畫完成
                if progress >= 1.0:
                    animation.status = "completed"
                    
                    # 推送完成事件
                    complete_command = {
                        "type": "animation_complete",
                        "animation_id": animation_id,
                        "timestamp": current_time,
                    }
                    
                    await self.event_streamer.broadcast_event(complete_command)
                    
                    # 處理隊列中的動畫
                    await self._process_animation_queue()
                    
                    break
                
                # 等待 100ms 後再檢查
                await asyncio.sleep(0.1)
                
        except Exception as e:
            self.logger.error("動畫進度追蹤失敗", animation_id=animation_id, error=str(e))
            animation.status = "failed"

    async def _process_animation_queue(self):
        """處理動畫隊列"""
        if not self.animation_queue:
            return
            
        active_count = len(self.get_active_animations())
        available_slots = self.max_concurrent_animations - active_count
        
        for _ in range(min(available_slots, len(self.animation_queue))):
            if self.animation_queue:
                queued_event = self.animation_queue.pop(0)
                await self.trigger_3d_animation(queued_event)

    async def _track_handover_start(self, event: VisualizationEvent, animation_id: str):
        """追蹤換手開始"""
        handover_id = event.satellite_data.get("handover_id", animation_id)
        
        self.active_handovers[handover_id] = {
            "animation_id": animation_id,
            "start_time": event.timestamp,
            "source_satellite": event.satellite_data.get("source_satellite"),
            "target_satellite": event.satellite_data.get("target_satellite"),
            "status": "in_progress",
        }

    async def _track_handover_complete(self, event: VisualizationEvent, animation_id: str):
        """追蹤換手完成"""
        handover_id = event.satellite_data.get("handover_id", animation_id)
        
        if handover_id in self.active_handovers:
            self.active_handovers[handover_id].update({
                "completion_time": event.timestamp,
                "status": "completed",
                "success": event.satellite_data.get("success", True),
            })
            
            # 清理完成的換手記錄
            if event.satellite_data.get("cleanup", True):
                del self.active_handovers[handover_id]

    def get_current_satellite_positions(self) -> Dict[str, Dict[str, Any]]:
        """獲取當前衛星位置"""
        return self.satellite_positions.copy()

    def get_active_handovers(self) -> Dict[str, Dict[str, Any]]:
        """獲取活躍換手記錄"""
        return self.active_handovers.copy()