"""
多節點協調器 - Phase 4 核心組件

負責管理分佈式訓練環境中的多個計算節點：
- 節點註冊和發現
- 節點健康監控
- 任務分配和同步
- 節點間通信協調

Features:
- 支援動態節點加入/離開
- 自動故障檢測
- 負載平衡任務分配
- 實時節點狀態監控
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import socket
import aiohttp
import websockets

logger = logging.getLogger(__name__)


class NodeStatus(Enum):
    """節點狀態"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class NodeType(Enum):
    """節點類型"""
    WORKER = "worker"          # 訓練工作節點
    COORDINATOR = "coordinator"  # 協調節點
    STORAGE = "storage"        # 存儲節點
    EVALUATOR = "evaluator"    # 評估節點


@dataclass
class NodeInfo:
    """節點信息"""
    node_id: str
    node_type: NodeType
    host: str
    port: int
    status: NodeStatus
    capabilities: Dict[str, Any]
    last_heartbeat: datetime
    current_load: float = 0.0
    max_load: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "node_id": self.node_id,
            "node_type": self.node_type.value,
            "host": self.host,
            "port": self.port,
            "status": self.status.value,
            "capabilities": self.capabilities,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "current_load": self.current_load,
            "max_load": self.max_load,
            "metadata": self.metadata
        }


@dataclass
class TrainingTask:
    """訓練任務"""
    task_id: str
    algorithm: str
    assigned_node: Optional[str]
    status: str
    created_at: datetime
    parameters: Dict[str, Any]
    estimated_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "task_id": self.task_id,
            "algorithm": self.algorithm,
            "assigned_node": self.assigned_node,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "parameters": self.parameters,
            "estimated_duration": self.estimated_duration,
            "actual_duration": self.actual_duration
        }


class NodeCoordinator:
    """
    多節點協調器
    
    管理分佈式訓練環境中的所有計算節點，
    提供節點發現、健康監控、任務分配等功能。
    """
    
    def __init__(self, 
                 coordinator_host: str = "localhost",
                 coordinator_port: int = 8765,
                 heartbeat_interval: int = 30,
                 heartbeat_timeout: int = 90):
        """
        初始化節點協調器
        
        Args:
            coordinator_host: 協調器主機地址
            coordinator_port: 協調器端口
            heartbeat_interval: 心跳間隔（秒）
            heartbeat_timeout: 心跳超時（秒）
        """
        self.coordinator_host = coordinator_host
        self.coordinator_port = coordinator_port
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_timeout
        
        # 節點管理
        self.nodes: Dict[str, NodeInfo] = {}
        self.tasks: Dict[str, TrainingTask] = {}
        
        # 運行狀態
        self.is_running = False
        self.websocket_server = None
        self.heartbeat_task = None
        
        # 統計信息
        self.stats = {
            "total_nodes": 0,
            "active_nodes": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "start_time": datetime.now()
        }
        
        self.logger = logger
        
    async def start(self):
        """啟動協調器"""
        try:
            self.logger.info(f"🚀 啟動節點協調器 {self.coordinator_host}:{self.coordinator_port}")
            
            # 啟動 WebSocket 服務器
            self.websocket_server = await websockets.serve(
                self._handle_websocket_connection,
                self.coordinator_host,
                self.coordinator_port
            )
            
            # 啟動心跳監控
            self.heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
            
            self.is_running = True
            self.stats["start_time"] = datetime.now()
            
            self.logger.info("✅ 節點協調器啟動成功")
            
        except Exception as e:
            self.logger.error(f"❌ 節點協調器啟動失敗: {e}")
            raise
    
    async def stop(self):
        """停止協調器"""
        try:
            self.logger.info("🛑 停止節點協調器...")
            
            self.is_running = False
            
            # 停止心跳監控
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            # 停止 WebSocket 服務器
            if self.websocket_server:
                self.websocket_server.close()
                await self.websocket_server.wait_closed()
            
            self.logger.info("✅ 節點協調器已停止")
            
        except Exception as e:
            self.logger.error(f"❌ 停止節點協調器失敗: {e}")
    
    async def _handle_websocket_connection(self, websocket, path):
        """處理 WebSocket 連接"""
        try:
            self.logger.info(f"📡 新的 WebSocket 連接: {websocket.remote_address}")
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    response = await self._handle_message(data)
                    
                    if response:
                        await websocket.send(json.dumps(response))
                        
                except json.JSONDecodeError as e:
                    self.logger.error(f"❌ JSON 解析錯誤: {e}")
                    error_response = {
                        "type": "error",
                        "message": "Invalid JSON format"
                    }
                    await websocket.send(json.dumps(error_response))
                    
                except Exception as e:
                    self.logger.error(f"❌ 處理消息錯誤: {e}")
                    error_response = {
                        "type": "error", 
                        "message": str(e)
                    }
                    await websocket.send(json.dumps(error_response))
                    
        except websockets.exceptions.ConnectionClosed:
            self.logger.info("📡 WebSocket 連接已關閉")
        except Exception as e:
            self.logger.error(f"❌ WebSocket 連接錯誤: {e}")
    
    async def _handle_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理收到的消息"""
        message_type = data.get("type")
        
        if message_type == "register_node":
            return await self._handle_register_node(data)
        elif message_type == "heartbeat":
            return await self._handle_heartbeat(data)
        elif message_type == "task_result":
            return await self._handle_task_result(data)
        elif message_type == "get_nodes":
            return await self._handle_get_nodes(data)
        elif message_type == "get_tasks":
            return await self._handle_get_tasks(data)
        elif message_type == "assign_task":
            return await self._handle_assign_task(data)
        else:
            return {
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            }
    
    async def _handle_register_node(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理節點註冊"""
        try:
            node_id = data.get("node_id", str(uuid.uuid4()))
            node_type = NodeType(data.get("node_type", "worker"))
            host = data.get("host", "localhost")
            port = data.get("port", 8000)
            capabilities = data.get("capabilities", {})
            
            # 創建節點信息
            node_info = NodeInfo(
                node_id=node_id,
                node_type=node_type,
                host=host,
                port=port,
                status=NodeStatus.READY,
                capabilities=capabilities,
                last_heartbeat=datetime.now()
            )
            
            # 註冊節點
            self.nodes[node_id] = node_info
            self.stats["total_nodes"] = len(self.nodes)
            self.stats["active_nodes"] = len([n for n in self.nodes.values() 
                                            if n.status in [NodeStatus.READY, NodeStatus.BUSY]])
            
            self.logger.info(f"✅ 節點註冊成功: {node_id} ({node_type.value})")
            
            return {
                "type": "register_response",
                "status": "success",
                "node_id": node_id,
                "message": "Node registered successfully"
            }
            
        except Exception as e:
            self.logger.error(f"❌ 節點註冊失敗: {e}")
            return {
                "type": "register_response",
                "status": "error",
                "message": str(e)
            }
    
    async def _handle_heartbeat(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理心跳"""
        try:
            node_id = data.get("node_id")
            if not node_id or node_id not in self.nodes:
                return {
                    "type": "heartbeat_response",
                    "status": "error",
                    "message": "Node not found"
                }
            
            # 更新節點狀態
            node = self.nodes[node_id]
            node.last_heartbeat = datetime.now()
            node.current_load = data.get("current_load", 0.0)
            node.status = NodeStatus(data.get("status", "ready"))
            
            return {
                "type": "heartbeat_response",
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ 心跳處理失敗: {e}")
            return {
                "type": "heartbeat_response",
                "status": "error",
                "message": str(e)
            }
    
    async def _handle_task_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理任務結果"""
        try:
            task_id = data.get("task_id")
            if not task_id or task_id not in self.tasks:
                return {
                    "type": "task_result_response",
                    "status": "error",
                    "message": "Task not found"
                }
            
            # 更新任務狀態
            task = self.tasks[task_id]
            task.status = data.get("status", "completed")
            task.actual_duration = data.get("duration")
            
            # 更新統計
            if task.status == "completed":
                self.stats["completed_tasks"] += 1
            elif task.status == "failed":
                self.stats["failed_tasks"] += 1
            
            # 釋放節點
            if task.assigned_node and task.assigned_node in self.nodes:
                self.nodes[task.assigned_node].status = NodeStatus.READY
                self.nodes[task.assigned_node].current_load = 0.0
            
            self.logger.info(f"✅ 任務完成: {task_id} ({task.status})")
            
            return {
                "type": "task_result_response",
                "status": "success",
                "message": "Task result processed"
            }
            
        except Exception as e:
            self.logger.error(f"❌ 任務結果處理失敗: {e}")
            return {
                "type": "task_result_response",
                "status": "error",
                "message": str(e)
            }
    
    async def _handle_get_nodes(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """獲取節點列表"""
        try:
            nodes_data = [node.to_dict() for node in self.nodes.values()]
            
            return {
                "type": "nodes_response",
                "status": "success",
                "nodes": nodes_data,
                "total_nodes": len(nodes_data)
            }
            
        except Exception as e:
            self.logger.error(f"❌ 獲取節點列表失敗: {e}")
            return {
                "type": "nodes_response",
                "status": "error",
                "message": str(e)
            }
    
    async def _handle_get_tasks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """獲取任務列表"""
        try:
            tasks_data = [task.to_dict() for task in self.tasks.values()]
            
            return {
                "type": "tasks_response",
                "status": "success",
                "tasks": tasks_data,
                "total_tasks": len(tasks_data)
            }
            
        except Exception as e:
            self.logger.error(f"❌ 獲取任務列表失敗: {e}")
            return {
                "type": "tasks_response",
                "status": "error",
                "message": str(e)
            }
    
    async def _handle_assign_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分配任務"""
        try:
            task_id = data.get("task_id", str(uuid.uuid4()))
            algorithm = data.get("algorithm", "dqn")
            parameters = data.get("parameters", {})
            
            # 選擇最適合的節點
            best_node = self._select_best_node(algorithm)
            if not best_node:
                return {
                    "type": "assign_task_response",
                    "status": "error",
                    "message": "No available nodes"
                }
            
            # 創建任務
            task = TrainingTask(
                task_id=task_id,
                algorithm=algorithm,
                assigned_node=best_node.node_id,
                status="assigned",
                created_at=datetime.now(),
                parameters=parameters
            )
            
            # 分配任務
            self.tasks[task_id] = task
            best_node.status = NodeStatus.BUSY
            best_node.current_load = 1.0
            
            self.stats["total_tasks"] += 1
            
            self.logger.info(f"✅ 任務分配成功: {task_id} -> {best_node.node_id}")
            
            return {
                "type": "assign_task_response",
                "status": "success",
                "task_id": task_id,
                "assigned_node": best_node.node_id,
                "message": "Task assigned successfully"
            }
            
        except Exception as e:
            self.logger.error(f"❌ 任務分配失敗: {e}")
            return {
                "type": "assign_task_response",
                "status": "error",
                "message": str(e)
            }
    
    def _select_best_node(self, algorithm: str) -> Optional[NodeInfo]:
        """選擇最適合的節點"""
        available_nodes = [
            node for node in self.nodes.values()
            if node.status == NodeStatus.READY and 
               node.node_type == NodeType.WORKER and
               algorithm in node.capabilities.get("algorithms", [algorithm])
        ]
        
        if not available_nodes:
            return None
        
        # 按負載排序，選擇負載最低的節點
        return min(available_nodes, key=lambda n: n.current_load)
    
    async def _heartbeat_monitor(self):
        """心跳監控任務"""
        while self.is_running:
            try:
                current_time = datetime.now()
                timeout_threshold = current_time - timedelta(seconds=self.heartbeat_timeout)
                
                # 檢查超時的節點
                for node_id, node in self.nodes.items():
                    if node.last_heartbeat < timeout_threshold:
                        if node.status != NodeStatus.DISCONNECTED:
                            self.logger.warning(f"⚠️ 節點心跳超時: {node_id}")
                            node.status = NodeStatus.DISCONNECTED
                            
                            # 重新分配該節點的任務
                            await self._reassign_node_tasks(node_id)
                
                # 更新統計
                self.stats["active_nodes"] = len([n for n in self.nodes.values() 
                                                if n.status in [NodeStatus.READY, NodeStatus.BUSY]])
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                self.logger.error(f"❌ 心跳監控錯誤: {e}")
                await asyncio.sleep(5)
    
    async def _reassign_node_tasks(self, failed_node_id: str):
        """重新分配失敗節點的任務"""
        try:
            # 找到該節點的未完成任務
            node_tasks = [
                task for task in self.tasks.values()
                if task.assigned_node == failed_node_id and task.status in ["assigned", "running"]
            ]
            
            for task in node_tasks:
                # 選擇新節點
                new_node = self._select_best_node(task.algorithm)
                if new_node:
                    task.assigned_node = new_node.node_id
                    task.status = "reassigned"
                    new_node.status = NodeStatus.BUSY
                    
                    self.logger.info(f"✅ 任務重新分配: {task.task_id} -> {new_node.node_id}")
                else:
                    task.status = "failed"
                    self.stats["failed_tasks"] += 1
                    
                    self.logger.warning(f"⚠️ 任務無法重新分配: {task.task_id}")
            
        except Exception as e:
            self.logger.error(f"❌ 重新分配任務失敗: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        uptime = datetime.now() - self.stats["start_time"]
        
        return {
            **self.stats,
            "uptime_seconds": uptime.total_seconds(),
            "nodes_by_status": {
                status.value: len([n for n in self.nodes.values() if n.status == status])
                for status in NodeStatus
            },
            "tasks_by_status": {
                status: len([t for t in self.tasks.values() if t.status == status])
                for status in ["assigned", "running", "completed", "failed", "reassigned"]
            }
        }
    
    def get_node_info(self, node_id: str) -> Optional[NodeInfo]:
        """獲取節點信息"""
        return self.nodes.get(node_id)
    
    def get_task_info(self, task_id: str) -> Optional[TrainingTask]:
        """獲取任務信息"""
        return self.tasks.get(task_id)
    
    async def create_training_task(self, 
                                 algorithm: str,
                                 parameters: Dict[str, Any],
                                 estimated_duration: Optional[int] = None) -> str:
        """創建訓練任務"""
        task_id = str(uuid.uuid4())
        
        # 選擇節點
        best_node = self._select_best_node(algorithm)
        if not best_node:
            raise RuntimeError("No available nodes for task assignment")
        
        # 創建任務
        task = TrainingTask(
            task_id=task_id,
            algorithm=algorithm,
            assigned_node=best_node.node_id,
            status="assigned",
            created_at=datetime.now(),
            parameters=parameters,
            estimated_duration=estimated_duration
        )
        
        # 分配任務
        self.tasks[task_id] = task
        best_node.status = NodeStatus.BUSY
        best_node.current_load = 1.0
        
        self.stats["total_tasks"] += 1
        
        self.logger.info(f"✅ 訓練任務創建成功: {task_id} -> {best_node.node_id}")
        
        return task_id
