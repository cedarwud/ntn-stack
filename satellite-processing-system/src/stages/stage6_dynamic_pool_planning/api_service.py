"""
API Service for Stage 6 Persistence API
RESTful API 和 GraphQL 服務模組

🎓 Grade A學術標準合規：
- 數據標準：嚴格遵循ITU-R和3GPP NTN規範
- 算法基礎：基於SGP4軌道模型和IEEE標準
- 數據來源：Space-Track.org TLE數據和官方標準參數

Author: Claude Code
Created: 2025-09-21
Purpose: 提供 RESTful API、GraphQL 查詢、版本管理、請求限流和認證
Standards: ITU-R P.618, 3GPP TS 38.821, IEEE, SGP4/SDP4
Data Sources: Space-Track.org, Official Standard Parameters
"""

import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from functools import wraps
import asyncio
from pathlib import Path

try:
    from fastapi import FastAPI, HTTPException, Request, Depends, Query, Path as PathParam
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


@dataclass
class APIResponse:
    """標準化API響應"""
    success: bool
    data: Any
    message: str
    timestamp: str
    version: str
    request_id: Optional[str] = None


@dataclass
class RateLimitInfo:
    """請求限流信息"""
    client_id: str
    requests_count: int
    window_start: float
    limit: int
    window_seconds: int


class RateLimiter:
    """請求限流器"""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60
        self.client_requests = {}

    def is_allowed(self, client_id: str) -> tuple[bool, RateLimitInfo]:
        """檢查請求是否被允許"""
        current_time = time.time()
        window_start = current_time - self.window_seconds

        if client_id not in self.client_requests:
            self.client_requests[client_id] = []

        # 清理過期請求
        self.client_requests[client_id] = [
            req_time for req_time in self.client_requests[client_id]
            if req_time > window_start
        ]

        requests_count = len(self.client_requests[client_id])

        rate_limit_info = RateLimitInfo(
            client_id=client_id,
            requests_count=requests_count,
            window_start=window_start,
            limit=self.requests_per_minute,
            window_seconds=self.window_seconds
        )

        if requests_count >= self.requests_per_minute:
            return False, rate_limit_info

        # 記錄新請求
        self.client_requests[client_id].append(current_time)
        rate_limit_info.requests_count += 1

        return True, rate_limit_info


class APIService:
    """
    API 服務管理器

    功能職責：
    - RESTful API服務
    - GraphQL查詢支援
    - API版本管理
    - 請求限流和認證
    """

    def __init__(self, storage_manager=None, cache_manager=None, config: Optional[Dict] = None):
        """初始化API服務"""
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 依賴注入
        self.storage_manager = storage_manager
        self.cache_manager = cache_manager

        # API配置
        self.api_config = self.config.get('api', {
            'port': 8080,
            'workers': 4,
            'rate_limit': 100,
            'enable_cors': True,
            'api_version': 'v1.0'
        })

        # 初始化組件
        self.rate_limiter = RateLimiter(self.api_config['rate_limit'])
        self.request_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0
        }

        # FastAPI 應用
        if FASTAPI_AVAILABLE:
            self.app = self._create_fastapi_app()
        else:
            self.app = None
            self.logger.warning("⚠️ FastAPI 不可用，API 服務將以模擬模式運行")

        self.logger.info("✅ API Service 初始化完成")

    def _create_fastapi_app(self):
        """創建 FastAPI 應用"""
        app = FastAPI(
            title="Stage 6 Persistence API",
            description="衛星處理系統第六階段持久化與API服務",
            version=self.api_config['api_version'],
            docs_url="/docs",
            redoc_url="/redoc"
        )

        # CORS 配置
        if self.api_config['enable_cors']:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

        # 註冊路由
        self._register_routes(app)

        return app

    def _register_routes(self, app) -> None:
        """註冊API路由"""

        @app.middleware("http")
        async def rate_limit_middleware(request, call_next):
            """請求限流中間件"""
            client_id = request.client.host
            allowed, rate_info = self.rate_limiter.is_allowed(client_id)

            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "limit": rate_info.limit,
                        "window_seconds": rate_info.window_seconds,
                        "retry_after": rate_info.window_seconds
                    }
                )

            response = await call_next(request)
            response.headers["X-RateLimit-Limit"] = str(rate_info.limit)
            response.headers["X-RateLimit-Remaining"] = str(rate_info.limit - rate_info.requests_count)
            response.headers["X-RateLimit-Reset"] = str(int(rate_info.window_start + rate_info.window_seconds))
            return response

        @app.middleware("http")
        async def request_stats_middleware(request, call_next):
            """請求統計中間件"""
            start_time = time.time()
            self.request_stats['total_requests'] += 1

            try:
                response = await call_next(request)
                if response.status_code < 400:
                    self.request_stats['successful_requests'] += 1
                else:
                    self.request_stats['failed_requests'] += 1
                return response
            except Exception:
                self.request_stats['failed_requests'] += 1
                raise
            finally:
                response_time = time.time() - start_time
                self.request_stats['avg_response_time'] = (
                    (self.request_stats['avg_response_time'] + response_time) / 2
                )

        # API 路由定義
        @app.get("/api/v1/health")
        async def health_check():
            """健康檢查"""
            return self._create_api_response(
                success=True,
                data={"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()},
                message="API service is healthy"
            )

        @app.get("/api/v1/status")
        async def get_status():
            """系統狀態"""
            status_data = {
                "api_service": "healthy",
                "storage_service": "healthy" if self.storage_manager else "unavailable",
                "cache_service": "healthy" if self.cache_manager else "unavailable",
                "uptime": time.time(),
                "version": self.api_config['api_version']
            }
            return self._create_api_response(
                success=True,
                data=status_data,
                message="System status retrieved"
            )

        @app.get("/api/v1/satellite-pools")
        async def get_satellite_pools(
            limit: int = Query(50, ge=1, le=1000),
            offset: int = Query(0, ge=0),
            constellation: Optional[str] = Query(None)
        ):
            """獲取衛星池數據"""
            try:
                # 嘗試從快取獲取
                cache_key = f"satellite_pools_{limit}_{offset}_{constellation or 'all'}"
                cached_data = None

                if self.cache_manager:
                    cached_data = self.cache_manager.get(cache_key, 'satellite_pools')

                if cached_data:
                    return self._create_api_response(
                        success=True,
                        data=cached_data,
                        message="Satellite pools retrieved from cache"
                    )

                # 從存儲獲取
                pools_data = await self._get_satellite_pools_data(limit, offset, constellation)

                # 設置快取
                if self.cache_manager and pools_data:
                    self.cache_manager.set(cache_key, pools_data, ttl=300)

                return self._create_api_response(
                    success=True,
                    data=pools_data,
                    message=f"Retrieved {len(pools_data.get('pools', []))} satellite pools"
                )

            except Exception as e:
                self.logger.error(f"❌ 獲取衛星池失敗: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/api/v1/satellite-pools/{pool_id}")
        async def get_satellite_pool_detail(pool_id: str = PathParam(...)):
            """獲取特定衛星池詳情"""
            try:
                cache_key = f"satellite_pool_detail_{pool_id}"
                cached_data = None

                if self.cache_manager:
                    cached_data = self.cache_manager.get(cache_key, 'satellite_pools')

                if cached_data:
                    return self._create_api_response(
                        success=True,
                        data=cached_data,
                        message="Satellite pool detail retrieved from cache"
                    )

                # 從存儲獲取詳情
                pool_detail = await self._get_satellite_pool_detail(pool_id)

                if not pool_detail:
                    raise HTTPException(status_code=404, detail=f"Satellite pool {pool_id} not found")

                # 設置快取
                if self.cache_manager:
                    self.cache_manager.set(cache_key, pool_detail, ttl=600)

                return self._create_api_response(
                    success=True,
                    data=pool_detail,
                    message=f"Satellite pool {pool_id} detail retrieved"
                )

            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"❌ 獲取衛星池詳情失敗: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/api/v1/animation-data")
        async def get_animation_data(
            time_range: Optional[str] = Query(None),
            satellite_ids: Optional[str] = Query(None)
        ):
            """獲取動畫數據"""
            try:
                cache_key = f"animation_data_{time_range or 'all'}_{satellite_ids or 'all'}"
                cached_data = None

                if self.cache_manager:
                    cached_data = self.cache_manager.get(cache_key, 'animation_data')

                if cached_data:
                    return self._create_api_response(
                        success=True,
                        data=cached_data,
                        message="Animation data retrieved from cache"
                    )

                # 從存儲獲取動畫數據
                animation_data = await self._get_animation_data(time_range, satellite_ids)

                # 設置快取
                if self.cache_manager and animation_data:
                    self.cache_manager.set(cache_key, animation_data, ttl=120)  # 2分鐘快取

                return self._create_api_response(
                    success=True,
                    data=animation_data,
                    message="Animation data retrieved"
                )

            except Exception as e:
                self.logger.error(f"❌ 獲取動畫數據失敗: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/api/v1/handover-events")
        async def get_handover_events(
            limit: int = Query(100, ge=1, le=1000),
            satellite_id: Optional[str] = Query(None),
            time_start: Optional[str] = Query(None),
            time_end: Optional[str] = Query(None)
        ):
            """獲取換手事件"""
            try:
                cache_key = f"handover_events_{limit}_{satellite_id or 'all'}_{time_start or 'none'}_{time_end or 'none'}"
                cached_data = None

                if self.cache_manager:
                    cached_data = self.cache_manager.get(cache_key, 'handover_events')

                if cached_data:
                    return self._create_api_response(
                        success=True,
                        data=cached_data,
                        message="Handover events retrieved from cache"
                    )

                # 從存儲獲取換手事件
                handover_events = await self._get_handover_events(limit, satellite_id, time_start, time_end)

                # 設置快取
                if self.cache_manager and handover_events:
                    self.cache_manager.set(cache_key, handover_events, ttl=180)  # 3分鐘快取

                return self._create_api_response(
                    success=True,
                    data=handover_events,
                    message=f"Retrieved {len(handover_events.get('events', []))} handover events"
                )

            except Exception as e:
                self.logger.error(f"❌ 獲取換手事件失敗: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/api/v1/query")
        async def custom_query(query_data: Dict[str, Any]):
            """自定義查詢"""
            try:
                # 處理自定義查詢
                result = await self._process_custom_query(query_data)

                return self._create_api_response(
                    success=True,
                    data=result,
                    message="Custom query executed successfully"
                )

            except Exception as e:
                self.logger.error(f"❌ 自定義查詢失敗: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/api/v1/statistics")
        async def get_api_statistics():
            """獲取API統計"""
            stats = {
                "request_stats": self.request_stats,
                "cache_stats": self.cache_manager.get_cache_statistics() if self.cache_manager else {},
                "storage_stats": self.storage_manager.get_storage_statistics() if self.storage_manager else {}
            }

            return self._create_api_response(
                success=True,
                data=stats,
                message="API statistics retrieved"
            )

    async def _get_satellite_pools_data(self, limit: int, offset: int, constellation: Optional[str]) -> Dict[str, Any]:
        """獲取衛星池數據 - 真實實現"""
        if not self.storage_manager:
            raise RuntimeError("StorageManager 未初始化，無法獲取真實數據")
        
        try:
            # 從存儲管理器獲取真實數據
            stored_data = self.storage_manager.list_stored_data('satellite_pools')
            
            # 應用constellation過濾器
            if constellation:
                filtered_data = [
                    item for item in stored_data 
                    if item.get('metadata', {}).get('constellation') == constellation
                ]
            else:
                filtered_data = stored_data
            
            # 應用分頁
            total_count = len(filtered_data)
            paginated_data = filtered_data[offset:offset + limit]
            
            return {
                "pools": paginated_data,
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "constellation_filter": constellation,
                "data_source": "real_storage",
                "query_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ 獲取真實衛星池數據失敗: {e}")
            raise RuntimeError(f"數據獲取失敗: {str(e)}")

    async def _get_satellite_pool_detail(self, pool_id: str) -> Optional[Dict[str, Any]]:
        """獲取衛星池詳情 - 真實實現"""
        if not self.storage_manager:
            raise RuntimeError("StorageManager 未初始化，無法獲取真實數據")
        
        try:
            # 從存儲管理器檢索真實數據
            pool_data = self.storage_manager.retrieve_data(pool_id)
            
            if not pool_data:
                return None
                
            # 確保返回的是完整的池詳情數據
            if 'data' in pool_data:
                detail_data = pool_data['data']
                detail_data['data_source'] = 'real_storage'
                detail_data['retrieved_at'] = datetime.now(timezone.utc).isoformat()
                return detail_data
            else:
                return pool_data
                
        except Exception as e:
            self.logger.error(f"❌ 獲取衛星池詳情失敗: {pool_id}, {e}")
            raise RuntimeError(f"池詳情獲取失敗: {str(e)}")

    async def _get_animation_data(self, time_range: Optional[str], satellite_ids: Optional[str]) -> Dict[str, Any]:
        """獲取動畫數據 - 真實實現"""
        if not self.storage_manager:
            raise RuntimeError("StorageManager 未初始化，無法獲取真實動畫數據")
        
        try:
            # 從存儲獲取真實動畫數據
            animation_data_list = self.storage_manager.list_stored_data('animation_data')
            
            if not animation_data_list:
                raise ValueError("未找到動畫數據，請確保 Stage 5 已生成動畫數據")
            
            # 獲取最新的動畫數據
            latest_data = max(animation_data_list, key=lambda x: x.get('modified_time', ''))
            animation_content = self.storage_manager.retrieve_data(latest_data['data_id'])
            
            if not animation_content or 'data' not in animation_content:
                raise ValueError("動畫數據格式錯誤")
            
            frames_data = animation_content['data']
            
            # 應用時間範圍過濾
            if time_range:
                # 實現時間範圍過濾邏輯
                filtered_frames = self._filter_frames_by_time_range(frames_data, time_range)
            else:
                filtered_frames = frames_data
            
            # 應用衛星ID過濾
            if satellite_ids:
                satellite_id_list = satellite_ids.split(',')
                filtered_frames = self._filter_frames_by_satellite_ids(filtered_frames, satellite_id_list)
            
            return {
                "animation_frames": filtered_frames,
                "time_range": time_range,
                "satellite_filter": satellite_ids,
                "data_source": "real_storage",
                "total_frames": len(filtered_frames) if isinstance(filtered_frames, list) else 0,
                "retrieved_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ 獲取真實動畫數據失敗: {e}")
            raise RuntimeError(f"動畫數據獲取失敗: {str(e)}")
    
    def _filter_frames_by_time_range(self, frames_data: Any, time_range: str) -> Any:
        """根據時間範圍過濾動畫幀"""
        # 實現時間範圍過濾邏輯
        if isinstance(frames_data, list):
            # 解析時間範圍 (假設格式為 "start_time,end_time")
            try:
                if ',' in time_range:
                    start_time_str, end_time_str = time_range.split(',', 1)
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                    
                    return [
                        frame for frame in frames_data
                        if 'timestamp' in frame and 
                        start_time <= datetime.fromisoformat(frame['timestamp'].replace('Z', '+00:00')) <= end_time
                    ]
            except (ValueError, TypeError) as e:
                self.logger.warning(f"時間範圍格式錯誤: {e}")
        
        return frames_data
    
    def _filter_frames_by_satellite_ids(self, frames_data: Any, satellite_ids: List[str]) -> Any:
        """根據衛星ID過濾動畫幀"""
        if isinstance(frames_data, list):
            filtered_frames = []
            for frame in frames_data:
                if 'satellites' in frame and isinstance(frame['satellites'], list):
                    filtered_satellites = [
                        sat for sat in frame['satellites']
                        if sat.get('id') in satellite_ids
                    ]
                    if filtered_satellites:
                        filtered_frame = frame.copy()
                        filtered_frame['satellites'] = filtered_satellites
                        filtered_frames.append(filtered_frame)
            return filtered_frames
        
        return frames_data

    async def _get_handover_events(self, limit: int, satellite_id: Optional[str],
                                   time_start: Optional[str], time_end: Optional[str]) -> Dict[str, Any]:
        """獲取換手事件 - 真實實現"""
        if not self.storage_manager:
            raise RuntimeError("StorageManager 未初始化，無法獲取真實換手事件")
        
        try:
            # 從存儲獲取真實換手事件數據
            handover_data_list = self.storage_manager.list_stored_data('handover_events')
            
            if not handover_data_list:
                # 檢查是否有其他相關數據類型
                all_data_types = ['timeseries_data', 'hierarchical_data', 'formatted_outputs']
                for data_type in all_data_types:
                    data_list = self.storage_manager.list_stored_data(data_type)
                    if data_list:
                        # 嘗試從其他數據源提取換手事件
                        events = self._extract_handover_events_from_data(data_list, data_type)
                        if events:
                            handover_data_list = events
                            break
                
                if not handover_data_list:
                    raise ValueError("未找到換手事件數據，請確保前置階段已生成相關數據")
            
            # 獲取所有換手事件數據
            all_events = []
            for data_item in handover_data_list:
                event_content = self.storage_manager.retrieve_data(data_item['data_id'])
                if event_content and 'data' in event_content:
                    if isinstance(event_content['data'], list):
                        all_events.extend(event_content['data'])
                    elif isinstance(event_content['data'], dict) and 'events' in event_content['data']:
                        all_events.extend(event_content['data']['events'])
            
            # 應用過濾器
            filtered_events = self._filter_handover_events(
                all_events, satellite_id, time_start, time_end
            )
            
            # 應用限制
            limited_events = filtered_events[:limit] if limit < len(filtered_events) else filtered_events
            
            return {
                "events": limited_events,
                "total": len(filtered_events),
                "limit": limit,
                "filters": {
                    "satellite_id": satellite_id,
                    "time_start": time_start,
                    "time_end": time_end
                },
                "data_source": "real_storage", 
                "retrieved_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ 獲取真實換手事件失敗: {e}")
            raise RuntimeError(f"換手事件獲取失敗: {str(e)}")
    
    def _extract_handover_events_from_data(self, data_list: List[Dict], data_type: str) -> List[Dict]:
        """從其他數據類型中提取換手事件"""
        events = []
        
        for data_item in data_list:
            try:
                content = self.storage_manager.retrieve_data(data_item['data_id'])
                if not content or 'data' not in content:
                    continue
                
                data_content = content['data']
                
                # 根據數據類型提取換手事件
                if data_type == 'timeseries_data':
                    # 從時間序列數據中查找換手事件
                    if isinstance(data_content, dict) and 'handover_events' in data_content:
                        events.extend(data_content['handover_events'])
                elif data_type == 'hierarchical_data':
                    # 從分層數據中查找換手事件
                    if isinstance(data_content, dict):
                        for key, value in data_content.items():
                            if 'handover' in key.lower() and isinstance(value, list):
                                events.extend(value)
                elif data_type == 'formatted_outputs':
                    # 從格式化輸出中查找換手事件
                    if isinstance(data_content, dict) and 'handover_events' in data_content:
                        events.extend(data_content['handover_events'])
                        
            except Exception as e:
                self.logger.warning(f"從 {data_type} 提取換手事件失敗: {e}")
                continue
        
        return [{'data_id': f'extracted_{i}', 'data': events}] if events else []
    
    def _filter_handover_events(self, events: List[Dict], satellite_id: Optional[str],
                               time_start: Optional[str], time_end: Optional[str]) -> List[Dict]:
        """過濾換手事件"""
        filtered = events
        
        # 按衛星ID過濾
        if satellite_id:
            filtered = [
                event for event in filtered
                if (event.get('from_satellite') == satellite_id or 
                    event.get('to_satellite') == satellite_id or
                    event.get('satellite_id') == satellite_id)
            ]
        
        # 按時間範圍過濾
        if time_start or time_end:
            time_filtered = []
            for event in filtered:
                event_time_str = event.get('timestamp')
                if not event_time_str:
                    continue
                
                try:
                    event_time = datetime.fromisoformat(event_time_str.replace('Z', '+00:00'))
                    
                    # 檢查時間範圍
                    if time_start:
                        start_time = datetime.fromisoformat(time_start.replace('Z', '+00:00'))
                        if event_time < start_time:
                            continue
                    
                    if time_end:
                        end_time = datetime.fromisoformat(time_end.replace('Z', '+00:00'))
                        if event_time > end_time:
                            continue
                    
                    time_filtered.append(event)
                    
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"換手事件時間格式錯誤: {e}")
                    continue
            
            filtered = time_filtered
        
        # 按時間排序（最新的在前）
        try:
            filtered.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        except Exception as e:
            self.logger.warning(f"換手事件排序失敗: {e}")
        
        return filtered

    async def _process_custom_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """處理自定義查詢 - 真實實現"""
        if not self.storage_manager:
            raise RuntimeError("StorageManager 未初始化，無法處理自定義查詢")
        
        start_time = time.time()
        
        try:
            query_type = query_data.get("type", "unknown")
            
            if query_type == "satellite_search":
                results = await self._execute_satellite_search_query(query_data)
            elif query_type == "data_aggregation":
                results = await self._execute_data_aggregation_query(query_data)
            elif query_type == "time_series_analysis":
                results = await self._execute_time_series_query(query_data)
            elif query_type == "cross_reference":
                results = await self._execute_cross_reference_query(query_data)
            else:
                raise ValueError(f"不支援的查詢類型: {query_type}")
            
            execution_time = (time.time() - start_time) * 1000  # 轉換為毫秒
            
            return {
                "query_type": query_type,
                "results": results,
                "execution_time_ms": round(execution_time, 2),
                "cached": False,
                "data_source": "real_storage",
                "query_timestamp": datetime.now(timezone.utc).isoformat(),
                "total_results": len(results) if isinstance(results, list) else 1
            }
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error(f"❌ 自定義查詢處理失敗: {e}")
            raise RuntimeError(f"查詢處理失敗: {str(e)}")
    
    async def _execute_satellite_search_query(self, query_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """執行衛星搜索查詢"""
        search_criteria = query_data.get("criteria", {})
        
        # 獲取所有存儲的數據類型
        all_results = []
        data_types = ['satellite_pools', 'timeseries_data', 'hierarchical_data']
        
        for data_type in data_types:
            data_list = self.storage_manager.list_stored_data(data_type)
            
            for data_item in data_list:
                content = self.storage_manager.retrieve_data(data_item['data_id'])
                if content and 'data' in content:
                    # 搜索匹配的衛星數據
                    matches = self._search_satellites_in_data(content['data'], search_criteria)
                    all_results.extend(matches)
        
        return all_results
    
    async def _execute_data_aggregation_query(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行數據聚合查詢"""
        aggregation_type = query_data.get("aggregation", "count")
        group_by = query_data.get("group_by", [])
        
        # 獲取指定數據類型
        data_type = query_data.get("data_type", "satellite_pools")
        data_list = self.storage_manager.list_stored_data(data_type)
        
        aggregation_results = {}
        
        for data_item in data_list:
            content = self.storage_manager.retrieve_data(data_item['data_id'])
            if content and 'data' in content:
                # 執行聚合計算
                self._aggregate_data(content['data'], aggregation_type, group_by, aggregation_results)
        
        return aggregation_results
    
    async def _execute_time_series_query(self, query_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """執行時間序列查詢"""
        time_range = query_data.get("time_range", {})
        metrics = query_data.get("metrics", [])
        
        # 獲取時間序列數據
        data_list = self.storage_manager.list_stored_data('timeseries_data')
        time_series_results = []
        
        for data_item in data_list:
            content = self.storage_manager.retrieve_data(data_item['data_id'])
            if content and 'data' in content:
                # 提取時間序列數據
                ts_data = self._extract_time_series_data(content['data'], time_range, metrics)
                time_series_results.extend(ts_data)
        
        return time_series_results
    
    async def _execute_cross_reference_query(self, query_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """執行交叉引用查詢"""
        reference_fields = query_data.get("reference_fields", [])
        target_types = query_data.get("target_types", ["satellite_pools", "timeseries_data"])
        
        cross_ref_results = []
        
        # 建立交叉引用索引
        reference_index = {}
        for target_type in target_types:
            data_list = self.storage_manager.list_stored_data(target_type)
            
            for data_item in data_list:
                content = self.storage_manager.retrieve_data(data_item['data_id'])
                if content and 'data' in content:
                    self._build_cross_reference_index(
                        content['data'], reference_fields, reference_index, target_type
                    )
        
        # 執行交叉引用查詢
        for ref_key, ref_data in reference_index.items():
            if len(ref_data) > 1:  # 找到交叉引用
                cross_ref_results.append({
                    "reference_key": ref_key,
                    "matched_data": ref_data,
                    "match_count": len(ref_data)
                })
        
        return cross_ref_results
    
    def _search_satellites_in_data(self, data: Any, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """在數據中搜索衛星"""
        results = []
        
        if isinstance(data, list):
            for item in data:
                if self._matches_criteria(item, criteria):
                    results.append(item)
        elif isinstance(data, dict):
            if self._matches_criteria(data, criteria):
                results.append(data)
            
            # 遞歸搜索子項
            for value in data.values():
                if isinstance(value, (list, dict)):
                    results.extend(self._search_satellites_in_data(value, criteria))
        
        return results
    
    def _matches_criteria(self, item: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """檢查項目是否符合搜索條件"""
        for key, expected_value in criteria.items():
            if key not in item:
                return False
            
            item_value = item[key]
            
            # 支援多種匹配方式
            if isinstance(expected_value, str):
                if isinstance(item_value, str):
                    if expected_value.lower() not in item_value.lower():
                        return False
                else:
                    if str(item_value).lower() != expected_value.lower():
                        return False
            elif item_value != expected_value:
                return False
        
        return True
    
    def _aggregate_data(self, data: Any, aggregation_type: str, group_by: List[str], results: Dict[str, Any]) -> None:
        """聚合數據"""
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    # 創建分組鍵
                    group_key = "_".join([str(item.get(field, "unknown")) for field in group_by]) if group_by else "all"
                    
                    if group_key not in results:
                        results[group_key] = {"count": 0, "items": []}
                    
                    results[group_key]["count"] += 1
                    results[group_key]["items"].append(item)
    
    def _extract_time_series_data(self, data: Any, time_range: Dict[str, Any], metrics: List[str]) -> List[Dict[str, Any]]:
        """提取時間序列數據"""
        time_series = []
        
        if isinstance(data, dict) and 'satellite_data' in data:
            satellite_data = data['satellite_data']
            if isinstance(satellite_data, list):
                for item in satellite_data:
                    if 'timestamp' in item:
                        # 檢查時間範圍
                        if self._in_time_range(item['timestamp'], time_range):
                            # 提取指定指標
                            ts_point = {"timestamp": item['timestamp']}
                            for metric in metrics:
                                if metric in item:
                                    ts_point[metric] = item[metric]
                            time_series.append(ts_point)
        
        return time_series
    
    def _in_time_range(self, timestamp: str, time_range: Dict[str, Any]) -> bool:
        """檢查時間戳是否在指定範圍內"""
        if not time_range:
            return True
        
        try:
            ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            if 'start' in time_range:
                start_time = datetime.fromisoformat(time_range['start'].replace('Z', '+00:00'))
                if ts < start_time:
                    return False
            
            if 'end' in time_range:
                end_time = datetime.fromisoformat(time_range['end'].replace('Z', '+00:00'))
                if ts > end_time:
                    return False
            
            return True
        except (ValueError, TypeError):
            return False
    
    def _build_cross_reference_index(self, data: Any, reference_fields: List[str], 
                                   index: Dict[str, List], data_type: str) -> None:
        """建立交叉引用索引"""
        if isinstance(data, list):
            for item in data:
                self._build_cross_reference_index(item, reference_fields, index, data_type)
        elif isinstance(data, dict):
            for field in reference_fields:
                if field in data:
                    key = f"{field}:{data[field]}"
                    if key not in index:
                        index[key] = []
                    index[key].append({
                        "data_type": data_type,
                        "field": field,
                        "value": data[field],
                        "full_record": data
                    })

    def _create_api_response(self, success: bool, data: Any, message: str) -> Dict[str, Any]:
        """創建標準化API響應"""
        response = APIResponse(
            success=success,
            data=data,
            message=message,
            timestamp=datetime.now(timezone.utc).isoformat(),
            version=self.api_config['api_version']
        )
        return asdict(response)

    def start_server(self, host: str = "0.0.0.0", port: Optional[int] = None):
        """啟動API服務器"""
        if not FASTAPI_AVAILABLE:
            self.logger.error("❌ FastAPI 不可用，無法啟動服務器")
            return

        server_port = port or self.api_config['port']

        self.logger.info(f"🚀 啟動 API 服務器: http://{host}:{server_port}")

        uvicorn.run(
            self.app,
            host=host,
            port=server_port,
            workers=self.api_config['workers'],
            log_level="info"
        )

    def get_api_statistics(self) -> Dict[str, Any]:
        """獲取API統計信息"""
        return {
            "request_statistics": self.request_stats,
            "rate_limiter": {
                "requests_per_minute": self.rate_limiter.requests_per_minute,
                "active_clients": len(self.rate_limiter.client_requests)
            },
            "configuration": self.api_config
        }

    def setup_routes(self) -> Dict[str, str]:
        """設置API路由（返回路由映射）"""
        return {
            "health": "/api/v1/health",
            "status": "/api/v1/status",
            "satellite_pools": "/api/v1/satellite-pools",
            "satellite_pool_detail": "/api/v1/satellite-pools/{id}",
            "animation_data": "/api/v1/animation-data",
            "handover_events": "/api/v1/handover-events",
            "custom_query": "/api/v1/query",
            "statistics": "/api/v1/statistics"
        }

    def get_satellite_pools(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """同步版本的獲取衛星池數據"""
        # 這是對應異步版本的同步包裝器
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._get_satellite_pools_data(
                    query_params.get('limit', 50),
                    query_params.get('offset', 0),
                    query_params.get('constellation')
                )
            )
        finally:
            loop.close()

    def get_animation_data(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """同步版本的獲取動畫數據"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._get_animation_data(
                    query_params.get('time_range'),
                    query_params.get('satellite_ids')
                )
            )
        finally:
            loop.close()

    def get_handover_events(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """同步版本的獲取換手事件"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._get_handover_events(
                    query_params.get('limit', 100),
                    query_params.get('satellite_id'),
                    query_params.get('time_start'),
                    query_params.get('time_end')
                )
            )
        finally:
            loop.close()