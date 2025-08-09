# 代碼清理步驟執行計劃

## 🎯 執行順序與時程

### Step 1: 註釋代碼清理 (Priority 1)
**時間:** 4 小時  
**風險:** 低  
**影響:** 高

#### 1.1 清理 main.py 註釋代碼塊
```python
# 移除文件: /netstack_api/main.py

# 移除導入 (line 42)
- # from netstack_api.routers import ai_decision_router

# 移除AI服務初始化 (line 151)  
- # await ai_service.initialize()

# 移除RL訓練引擎 (line 153-158)
- # rl_engine = RLTrainingEngine(
- #     model_config=rl_config,
- #     reward_calculator=reward_calc
- # )
- # await rl_engine.start()
- # logger.info("RL Training Engine started successfully")

# 移除數據庫初始化 (line 160-169)
- # database_manager = DatabaseManager(
- #     mongo_client=mongo_client,
- #     postgres_pool=postgres_pool
- # )
- # await database_manager.initialize_collections()
- # logger.info("Database collections initialized")

# 移除AI服務關閉 (line 191)
- # await ai_service.shutdown()
```

#### 1.2 移除未使用的導入
```python
# 掃描並移除未使用的導入
import ast
import sys

def find_unused_imports(filename):
    with open(filename, 'r') as f:
        content = f.read()
    
    tree = ast.parse(content)
    # 分析未使用的導入...
```

#### 1.3 驗證清理結果
```bash
# 語法檢查
python -m py_compile netstack_api/main.py

# 功能測試
python -c "from netstack_api.main import app; print('Import successful')"
```

---

### Step 2: Dependencies 依賴清理 (Priority 1)
**時間:** 6 小時  
**風險:** 中等  
**影響:** 中等

#### 2.1 創建開發依賴分離
```bash
# 創建 requirements-dev.txt
echo "# Development Dependencies" > requirements-dev.txt
cat >> requirements-dev.txt << 'EOF'
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-html>=3.2.0
pytest-cov>=4.1.0
black>=23.9.0
flake8>=6.1.0
mypy>=1.6.0
sphinx>=7.2.0
sphinx-rtd-theme>=1.3.0
EOF
```

#### 2.2 清理生產依賴
```python
# 修改 requirements.txt - 移除開發工具
- pytest>=7.4.0
- pytest-asyncio>=0.21.0
- pytest-html>=3.2.0
- pytest-cov>=4.1.0
- black>=23.9.0
- flake8>=6.1.0
- mypy>=1.6.0
- sphinx>=7.2.0
- sphinx-rtd-theme>=1.3.0

# 移除重複依賴
- pymongo>=4.6.0  # 保留motor作為主要MongoDB驅動

# 移除未使用依賴
- asyncio-mqtt>=0.13.0  # MQTT客戶端未找到使用處
- sentry-sdk>=1.38.0    # 錯誤追蹤服務未配置

# 評估並移除可選依賴
- validators>=0.22.0    # 驗證工具 - 檢查實際使用
- cerberus>=1.3.0      # 數據驗證 - 檢查實際使用
- tqdm>=4.66.0         # 進度條 - 檢查實際使用
- rich>=13.6.0         # 終端美化 - 檢查實際使用
```

#### 2.3 依賴使用驗證
```bash
# 創建依賴檢查腳本
cat > scripts/check-dependencies.sh << 'EOF'
#!/bin/bash
echo "檢查依賴使用情況..."

# 檢查每個依賴是否被實際使用
for dep in $(pip list --format=freeze | cut -d'=' -f1); do
    echo "檢查 $dep..."
    if ! grep -r "import $dep" netstack/ > /dev/null 2>&1; then
        echo "⚠️ $dep 可能未被使用"
    fi
done
EOF

chmod +x scripts/check-dependencies.sh
./scripts/check-dependencies.sh
```

#### 2.4 Docker 建置測試
```bash
# 測試新的依賴配置
cd /home/sat/ntn-stack/netstack
docker build -t netstack-api:cleanup-test .

# 驗證容器功能
docker run --rm netstack-api:cleanup-test python -c "
import fastapi
import motor  
import redis
import skyfield
import sgp4
print('✅ 核心依賴導入成功')
"
```

---

### Step 3: 代碼結構簡化 (Priority 2)
**時間:** 8 小時  
**風險:** 中等  
**影響:** 中等

#### 3.1 Manager 類簡化
```python
# 文件: app/core/service_manager.py

class ServiceManager:
    """簡化的服務管理器 - 移除冗余功能"""
    
    def __init__(self):
        self.services = {}
        self.health_status = {}
    
    async def register_service(self, name: str, service):
        """註冊服務 - 保留核心功能"""
        self.services[name] = service
        
    async def start_all(self):
        """啟動所有服務 - 簡化邏輯"""
        for name, service in self.services.items():
            try:
                await service.start()
                self.health_status[name] = "healthy"
            except Exception as e:
                self.health_status[name] = f"error: {e}"
                
    # 移除複雜的依賴管理邏輯
    # 移除未使用的配置載入功能
    # 移除過度抽象的介面
```

#### 3.2 路由管理簡化
```python
# 文件: app/core/router_manager.py

class RouterManager:
    """簡化的路由管理器"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.routers = []
    
    def include_router(self, router, **kwargs):
        """包含路由 - 移除複雜的中介邏輯"""
        self.app.include_router(router, **kwargs)
        self.routers.append(router)
    
    # 移除動態路由載入
    # 移除複雜的權限管理
    # 移除未使用的路由分析功能
```

#### 3.3 算法複雜度評估
```python
# 文件: src/services/satellite/preprocessing/satellite_selector.py

# 評估ITU-R P.618鏈路預算計算複雜度
def evaluate_link_budget_complexity():
    """評估是否需要完整的ITU-R P.618計算"""
    # 分析：
    # 1. 是否所有參數都被使用？
    # 2. 計算結果是否影響核心邏輯？
    # 3. 能否簡化為關鍵參數？
    
    # 建議：保留核心的路徑損耗計算，簡化環境修正
    pass

# 評估環境補正係數
def evaluate_environment_correction():
    """評估環境補正係數的必要性"""
    # 當前：複雜的地形、氣候修正
    # 建議：簡化為3個級別：都市/郊區/開闊地
    pass
```

---

### Step 4: 測試與驗證 (Priority 1)
**時間:** 4 小時  
**風險:** 低  
**影響:** 高

#### 4.1 功能完整性測試
```bash
#!/bin/bash
# 文件: scripts/cleanup-validation.sh

echo "🧪 開始清理後功能驗證..."

# API健康檢查
echo "1. API健康檢查..."
response=$(curl -s -w "%{http_code}" http://localhost:8080/health -o /dev/null)
if [ "$response" -eq 200 ]; then
    echo "✅ API健康檢查通過"
else
    echo "❌ API健康檢查失敗 (HTTP: $response)"
    exit 1
fi

# 衛星數據端點測試
echo "2. 衛星數據端點測試..."
response=$(curl -s -w "%{http_code}" "http://localhost:8080/api/v1/satellites/positions" -o /dev/null)
if [ "$response" -eq 200 ]; then
    echo "✅ 衛星數據端點正常"
else
    echo "❌ 衛星數據端點異常 (HTTP: $response)"
    exit 1
fi

# 數據庫連接測試
echo "3. 數據庫連接測試..."
docker exec netstack-api python -c "
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import redis
import asyncpg

async def test_connections():
    # MongoDB
    mongo = AsyncIOMotorClient('mongodb://mongo:27017')
    await mongo.admin.command('ping')
    print('MongoDB: ✅')
    
    # Redis  
    r = redis.Redis(host='redis', port=6379)
    r.ping()
    print('Redis: ✅')
    
    # PostgreSQL
    conn = await asyncpg.connect(
        'postgresql://netstack_user:netstack_password@postgres:5432/netstack_db'
    )
    await conn.close()
    print('PostgreSQL: ✅')

asyncio.run(test_connections())
" || exit 1

echo "✅ 所有功能驗證通過"
```

#### 4.2 性能基準測試
```bash
#!/bin/bash
# 性能對比測試

echo "📊 性能基準測試..."

# 記錄清理前狀態（如果有備份）
if [ -d "netstack_backup_$(date +%Y%m%d)" ]; then
    echo "對比清理前後性能..."
fi

# 容器啟動時間測試
echo "測試容器啟動時間..."
start_time=$(date +%s)
docker-compose restart netstack-api
# 等待健康檢查通過
while ! curl -s http://localhost:8080/health > /dev/null; do
    sleep 1
done
end_time=$(date +%s)
startup_time=$((end_time - start_time))
echo "容器啟動時間: ${startup_time}秒"

# 記憶體使用測試
echo "檢查記憶體使用..."
docker stats netstack-api --no-stream --format "table {{.Container}}\t{{.MemUsage}}"

# API響應時間測試
echo "測試API響應時間..."
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8080/api/v1/satellites/positions

echo "✅ 性能測試完成"
```

#### 4.3 代碼品質檢查
```bash
# 代碼品質自動檢查
echo "🔍 代碼品質檢查..."

# 檢查註釋代碼殘留
echo "檢查註釋代碼殘留..."
if grep -r "# await\|# import\|# from" netstack_api/ | grep -v ".pyc"; then
    echo "❌ 發現註釋代碼殘留"
    exit 1
else
    echo "✅ 無註釋代碼殘留"
fi

# 檢查未使用導入
echo "檢查未使用導入..."
flake8 netstack_api/ --select=F401 | head -10

# 檢查語法錯誤
echo "檢查語法錯誤..."
python -m py_compile netstack_api/main.py
echo "✅ 語法檢查通過"
```

---

## 🚨 風險管理

### 清理前檢查清單
- [ ] 創建完整的代碼備份
- [ ] 確保有功能測試腳本
- [ ] 準備快速回滾方案
- [ ] 通知團隊成員清理計劃

### 清理中監控
- [ ] 每個步驟後運行驗證腳本
- [ ] 持續監控容器健康狀態
- [ ] 記錄性能變化數據
- [ ] 保持git commit的細粒度

### 清理後驗證
- [ ] 運行完整的功能測試套件
- [ ] 確認所有API端點正常
- [ ] 驗證性能改善指標
- [ ] 更新相關文檔

---

## 📈 預期成果

### 量化指標
- **代碼行數**: 減少 30-40%
- **啟動時間**: 從 >5分鐘 → <1分鐘  
- **記憶體使用**: 減少 20%
- **Docker映像**: 減少 15%

### 質化改善
- **可維護性**: 消除註釋代碼困惑
- **可讀性**: 簡化複雜的Manager架構
- **穩定性**: 移除潛在的依賴衝突
- **開發效率**: 更快的建置和部署

---

*執行計劃版本: v1.0*  
*預計總時間: 22 小時*  
*建議執行期: 2-3 工作天*