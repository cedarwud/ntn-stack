# NetStack API 重構計劃 - Phase 2

## 🎯 重構現況分析

### 當前狀態
- **main.py (428行)**: 當前生產版本，功能完整但仍需重構
- **main_refactored.py (298行)**: 未完成的重構版本，缺少30%功能
- **app/api/ 模組**: 已完成高品質重構，包含 health、ue、handover 路由器
- **routers/ 生態系統**: 9個專業路由器，96個端點，功能豐富

### 核心問題
1. **兩個版本共存** - 造成維護困惑和重複工作
2. **main_refactored.py 不完整** - 缺少 UAV、Mesh 服務和 4 個條件性路由器
3. **main.py 仍然臃腫** - 428行包含太多職責，需進一步模組化
4. **服務初始化混亂** - 60行的服務初始化代碼需要獨立管理

## 🚀 分階段重構策略

### Phase 2A: 修復和統一 (Priority: 🔥 High)

#### 目標: 修復 main_refactored.py 使其功能對等

**步驟 1: 補全缺失功能**
```python
# 1. 添加缺失的模型導入
from .models.uav_models import (
    TrajectoryCreateRequest, UAVCreateRequest, UAVStatusResponse,
    # ... 所有 UAV 相關模型
)
from .models.mesh_models import (
    MeshNodeCreateRequest, BridgeGatewayCreateRequest,
    # ... 所有 Mesh 相關模型  
)

# 2. 完善服務初始化
app.state.slice_service = SliceService(mongo_adapter, open5gs_adapter, redis_adapter)
app.state.mesh_service = MeshBridgeService(mongo_adapter, redis_adapter, open5gs_adapter)
app.state.uav_failover_service = UAVMeshFailoverService(
    mongo_adapter, redis_adapter, 
    app.state.connection_service, app.state.mesh_service
)

# 3. 添加缺失的路由器
app.include_router(handover_router)  # 目前被遺漏

# 4. 修復條件性路由器註冊
if performance_router:
    app.include_router(performance_router, tags=["性能監控"])
if rl_monitoring_router:
    app.include_router(rl_monitoring_router, tags=["RL 訓練監控"])
if satellite_tle_router:
    app.include_router(satellite_tle_router, tags=["衛星 TLE 橋接"])
if scenario_test_router:
    app.include_router(scenario_test_router, tags=["場景測試驗證"])
```

**步驟 2: 環境配置統一**
```python
# 使用與 main.py 相同的環境變數配置
mongo_url = os.getenv("DATABASE_URL", "mongodb://mongo:27017/open5gs")
redis_url = os.getenv("REDIS_URL", "redis://redis:6379") 
mongo_host = os.getenv("MONGO_HOST", "mongo")

mongo_adapter = MongoAdapter(mongo_url)
redis_adapter = RedisAdapter(redis_url)
open5gs_adapter = Open5GSAdapter(mongo_host=mongo_host, mongo_port=27017)
```

### Phase 2B: 深度模組化 (Priority: 🟡 Medium)

#### 目標: 進一步拆分 main.py 為微服務架構

**1. 服務初始化管理器**
```python
# 新建 app/core/service_manager.py
class ServiceManager:
    def __init__(self, mongo_adapter, redis_adapter, open5gs_adapter):
        self.mongo_adapter = mongo_adapter
        self.redis_adapter = redis_adapter  
        self.open5gs_adapter = open5gs_adapter
        
    async def initialize_services(self, app: FastAPI):
        """統一初始化所有服務"""
        # 基礎服務
        app.state.ue_service = UEService(self.mongo_adapter, self.open5gs_adapter)
        app.state.slice_service = SliceService(
            self.mongo_adapter, self.open5gs_adapter, self.redis_adapter
        )
        
        # 進階服務 (依賴基礎服務)
        app.state.connection_service = ConnectionQualityService(self.mongo_adapter)
        app.state.mesh_service = MeshBridgeService(
            self.mongo_adapter, self.redis_adapter, self.open5gs_adapter
        )
        
        # 複合服務 (依賴多個服務)
        app.state.uav_failover_service = UAVMeshFailoverService(
            self.mongo_adapter, self.redis_adapter,
            app.state.connection_service, app.state.mesh_service
        )
```

**2. 路由器註冊管理器**
```python
# 新建 app/core/router_manager.py
class RouterManager:
    def __init__(self, app: FastAPI):
        self.app = app
        
    def register_core_routers(self):
        """註冊核心路由器"""
        # 新模組化路由器 (優先級最高)
        self.app.include_router(health_router, tags=["健康檢查"])
        self.app.include_router(ue_router, tags=["UE 管理"])
        self.app.include_router(handover_router, tags=["切換管理"])
        
        # 現有統一路由器
        self.app.include_router(unified_router, tags=["統一 API"])
        self.app.include_router(ai_decision_router, tags=["AI 智慧決策"])
        self.app.include_router(core_sync_router, tags=["核心同步"])
        self.app.include_router(intelligent_fallback_router, tags=["智能回退"])
        
    def register_optional_routers(self):
        """註冊可選路由器 (有條件註冊)"""
        optional_routers = [
            (performance_router, "性能監控"),
            (rl_monitoring_router, "RL 訓練監控"),
            (satellite_tle_router, "衛星 TLE 橋接"),
            (scenario_test_router, "場景測試驗證")
        ]
        
        for router, tag in optional_routers:
            if router:
                self.app.include_router(router, tags=[tag])
                logger.info(f"✅ 成功註冊 {tag} 路由器")
            else:
                logger.warning(f"⚠️ {tag} 路由器導入失敗，跳過註冊")
```

### Phase 2C: 最終重構 (Priority: 🟢 Low)

#### 目標: 極簡化的 main.py

**最終的 main.py 結構 (~150行)**
```python
"""
NetStack API - 極簡化主應用程式
所有功能模組化，主文件只負責應用配置和啟動
"""

from .app.core.service_manager import ServiceManager
from .app.core.router_manager import RouterManager  
from .app.core.middleware_manager import MiddlewareManager
from .app.core.exception_manager import ExceptionManager

# 生命週期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 NetStack API 正在啟動...")
    
    # 初始化適配器
    adapters = await AdapterManager.initialize()
    
    # 初始化服務
    service_manager = ServiceManager(*adapters)
    await service_manager.initialize_services(app)
    
    # 初始化 AI 服務
    await initialize_ai_services(adapters[1])  # redis_adapter
    
    logger.info("✅ NetStack API 啟動完成")
    yield
    
    # 清理資源
    await AdapterManager.cleanup(adapters)
    logger.info("✅ NetStack API 已關閉")

# 應用程式建立
app = FastAPI(
    title="NetStack API",
    description="Open5GS + UERANSIM 雙 Slice 核心網管理 API",
    version="2.0.0",  # 重構完成版本
    lifespan=lifespan
)

# 設定管理器
middleware_manager = MiddlewareManager(app)
router_manager = RouterManager(app)
exception_manager = ExceptionManager(app)

# 初始化應用程式
middleware_manager.setup_cors()
middleware_manager.setup_metrics_logging()
router_manager.register_core_routers()
router_manager.register_optional_routers()
exception_manager.setup_handlers()

# 根路徑
@app.get("/")
async def root():
    return {
        "name": "NetStack API",
        "version": "2.0.0",
        "status": "完全重構完成 - 極簡化架構",
        "architecture": "Hexagonal + Microservices",
        "timestamp": datetime.utcnow().isoformat()
    }
```

## 🧪 測試和驗證策略

### 自動化測試要求
```bash
# Phase 2A 完成後必須執行
./verify-refactor.sh --compare-versions  # 比較兩版本功能對等性

# Phase 2B 完成後必須執行  
./verify-refactor.sh --performance-test  # 性能回歸測試

# Phase 2C 完成後必須執行
./verify-refactor.sh --full-suite        # 完整測試套件
```

### 功能對等性檢查
```python
# 新建 tests/version_comparison_test.py
class VersionComparisonTest:
    def test_endpoint_coverage(self):
        """確保兩版本端點完全相同"""
        
    def test_service_initialization(self):
        """確保兩版本服務初始化相同"""
        
    def test_response_compatibility(self):
        """確保兩版本 API 回應相同"""
```

## 📋 實施時間線

### Week 1: Phase 2A - 修復統一
- **Day 1-2**: 修復 main_refactored.py 缺失功能
- **Day 3-4**: 環境配置統一和測試
- **Day 5**: 功能對等性驗證

### Week 2: Phase 2B - 深度模組化  
- **Day 1-2**: 建立管理器模組 (Service, Router, Middleware, Exception)
- **Day 3-4**: 重構 main.py 使用管理器
- **Day 5**: 效能和穩定性測試

### Week 3: Phase 2C - 最終極簡化
- **Day 1-2**: 建立 AdapterManager，極簡化 main.py
- **Day 3-4**: 完整測試和優化
- **Day 5**: 文檔更新和部署準備

## 🎯 成功指標

### 定量指標
- **代碼行數**: main.py 從 428行 減少到 ~150行 (65% 減少)
- **維護性**: 循環複雜度 < 5
- **效能**: API 回應時間無回歸 (< 5% 差異)
- **測試覆蓋率**: > 95%

### 定性指標  
- **單一職責**: 每個模組只負責一項核心功能
- **依賴注入**: 服務間依賴關係清晰可測試
- **擴展性**: 新增路由器和服務無需修改主文件
- **可讀性**: 新人能在 10 分鐘內理解架構

## 🚨 風險管控

### 高風險項目
1. **服務依賴關係**: UAV 和 Mesh 服務的複雜依賴
2. **路由器導入失敗**: 條件性路由器的錯誤處理
3. **生產環境相容性**: Docker 環境變數配置

### 緩解策略
1. **依賴圖映射**: 建立服務依賴關係圖，確保初始化順序
2. **優雅降級**: 路由器導入失敗不影響核心功能
3. **環境隔離測試**: 多環境驗證 (開發/測試/生產)

## 📚 最佳實踐

### 衛星通訊系統要求
- **延遲敏感**: 服務初始化時間 < 10秒
- **高可用性**: 單一路由器失敗不影響其他功能
- **可觀測性**: 完整的指標和日誌追蹤
- **擴展性**: 支援未來新增衛星星座和演算法

### 代碼品質標準
- **類型註解**: 100% 類型覆蓋
- **文檔字串**: 所有公開方法有詳細說明
- **錯誤處理**: 所有異常都有適當的錯誤碼和訊息
- **測試先行**: 每個新功能都有對應測試

---

**作者**: Claude (衛星通訊系統工程師 + AI 演算法專家)  
**建立時間**: 2025-01-05  
**重構目標**: 打造世界級的 LEO 衛星核心網管理系統
