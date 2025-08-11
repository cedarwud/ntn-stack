# SimWorld Backend 重構實施計劃

## 🎯 執行準則

### 核心原則
1. **安全第一**: 每個變更都要有回滾方案
2. **漸進式改進**: 小步快跑，頻繁驗證  
3. **功能完整性**: 絕不破壞核心研究功能
4. **測試驅動**: 變更前後都要有充分測試

### 執行標準
- 每個階段完成後必須通過完整測試
- 每次變更都要有詳細的變更日誌
- 重要變更需要 Code Review
- 保持與前端團隊的密切溝通

## 📋 詳細實施步驟

### Phase 1: 環境準備與風險評估

#### 1.1 建立重構環境
```bash
# 建立重構分支
git checkout -b refactor/simworld-backend-cleanup
git push -u origin refactor/simworld-backend-cleanup

# 標記重構前版本
git tag v-before-refactor
git push origin v-before-refactor

# 建立備份目錄
mkdir -p backup/simworld-backend-$(date +%Y%m%d)
cp -r simworld/backend backup/simworld-backend-$(date +%Y%m%d)/
```

#### 1.2 相依性分析工具執行
```bash
# 安裝分析工具
pip install pydeps vulture pipdeptree

# 分析模組依賴  
pydeps simworld/backend/app --show-deps --max-bacon 3

# 找出未使用的程式碼
vulture simworld/backend/app

# 分析套件依賴
pipdeptree --packages simworld-backend
```

#### 1.3 建立測試基準
```bash
# 執行現有測試套件
cd simworld/backend
python -m pytest tests/ --cov=app --cov-report=html --cov-report=term

# 建立效能基準測試
python -m pytest tests/performance/ --benchmark-only --benchmark-json=baseline.json

# API 健康檢查
curl -s http://localhost:8888/health | jq .
curl -s http://localhost:8888/api/satellite/health | jq .
```

### Phase 2: 低風險組件移除

#### 2.1 移除 UAV 追踪模組
```bash
# 備份將要移除的檔案
mkdir -p backup/removed-components/uav
cp simworld/backend/app/api/routes/uav.py backup/removed-components/uav/

# 移除 UAV 相關檔案
rm simworld/backend/app/api/routes/uav.py

# 更新路由註冊
# 編輯 simworld/backend/app/main.py
# 移除: from app.api.routes import uav
# 移除: app.include_router(uav.router, prefix="/api/v1", tags=["UAV"])
```

修改 `main.py`:
```python
# 移除這些行
- from app.api.routes import uav
- app.include_router(uav.router, prefix="/api/v1", tags=["UAV"])
```

#### 2.2 移除開發期工具
```bash
# 備份開發工具
mkdir -p backup/removed-components/dev-tools
cp simworld/backend/app/services/precision_validator.py backup/removed-components/dev-tools/
cp simworld/backend/app/services/distance_validator.py backup/removed-components/dev-tools/
cp simworld/backend/app/api/v1/distance_validation.py backup/removed-components/dev-tools/

# 移除開發工具檔案
rm simworld/backend/app/services/precision_validator.py
rm simworld/backend/app/services/distance_validator.py  
rm simworld/backend/app/api/v1/distance_validation.py
```

#### 2.3 移除過時遷移代碼
```bash
# 備份遷移代碼
mkdir -p backup/removed-components/migration
cp simworld/backend/app/services/skyfield_migration.py backup/removed-components/migration/

# 移除遷移代碼
rm simworld/backend/app/services/skyfield_migration.py

# 檢查並移除相關 import 
grep -r "skyfield_migration" simworld/backend/app/
# 根據搜尋結果移除相關引用
```

#### 2.4 Phase 2 驗證
```bash
# 重新啟動服務
make simworld-restart

# 執行測試套件
cd simworld/backend
python -m pytest tests/ -v

# 檢查 API 健康狀態
curl -s http://localhost:8888/health
curl -s http://localhost:8888/api/satellite/visible_satellites?lat=24.9&lon=121.4

# 驗證前端載入
curl -s http://localhost:5173/api/models/sat.glb -I
```

### Phase 3: 系統監控域移除

#### 3.1 移除系統監控域
```bash
# 備份系統監控域
mkdir -p backup/removed-components/system-domain
cp -r simworld/backend/app/domains/system backup/removed-components/system-domain/

# 移除系統監控域
rm -rf simworld/backend/app/domains/system
```

#### 3.2 更新主配置
編輯 `simworld/backend/app/main.py`:
```python
# 移除這些行  
- from app.domains.system.api import system_api
- app.include_router(system_api.router, prefix="/api/v1", tags=["System"])
```

編輯 `simworld/backend/app/api/dependencies.py`:
```python
# 移除系統監控相關依賴注入
- from app.domains.system.services import system_resource_service
```

#### 3.3 更新 context_maps.py
編輯 `simworld/backend/app/domains/context_maps.py`:
```python
# 移除系統域的映射
- "system": "app.domains.system",
```

### Phase 4: 程式碼重構與優化

#### 4.1 距離計算邏輯合併
```bash
# 分析現有距離計算邏輯
grep -r "distance" simworld/backend/app/services/ --include="*.py"
grep -r "calculate.*distance" simworld/backend/app/domains/ --include="*.py"
```

重構 `services/distance_calculator.py`:
```python
class UnifiedDistanceCalculator:
    """統一的距離計算服務"""
    
    def calculate_satellite_distance(self, sat_pos, ground_pos):
        """計算衛星到地面點距離"""
        pass
        
    def calculate_great_circle_distance(self, pos1, pos2):  
        """計算球面大圓距離"""
        pass
        
    def calculate_elevation_angle(self, sat_pos, observer_pos):
        """計算仰角"""
        pass
```

#### 4.2 座標轉換優化  
重構 `domains/coordinates/services/coordinate_service.py`:
```python  
class OptimizedCoordinateService:
    """優化的座標轉換服務"""
    
    def __init__(self):
        # 預計算轉換矩陣，提升效能
        self._transformation_cache = {}
    
    def convert_geodetic_to_ecef(self, lat, lon, alt):
        """地理座標轉 ECEF"""
        pass
        
    def convert_ecef_to_enu(self, ecef_pos, ref_pos):
        """ECEF 轉 ENU 局部座標"""
        pass
```

#### 4.3 API 路由重組
重新組織 `api/routes/` 結構:
```
api/routes/
├── core.py           # 基礎健康檢查、模型服務
├── satellite/        # 衛星相關 API  
│   ├── __init__.py
│   ├── orbit.py      # 軌道計算 API
│   ├── visibility.py # 可見性 API
│   └── handover.py   # 切換相關 API
├── simulation/       # 模擬相關 API
│   ├── __init__.py  
│   ├── rendering.py  # 3D 渲染 API
│   └── scenes.py     # 場景管理 API
└── devices/          # 設備相關 API
    ├── __init__.py
    └── management.py # 設備管理 API
```

### Phase 5: 測試完善與文檔更新

#### 5.1 單元測試完善
```bash
# 建立測試目錄結構
mkdir -p simworld/backend/tests/unit/{satellite,coordinates,simulation}
mkdir -p simworld/backend/tests/integration/api
mkdir -p simworld/backend/tests/performance
```

新增核心功能測試:
```python
# tests/unit/satellite/test_orbit_service.py
class TestOrbitService:
    def test_calculate_satellite_position(self):
        """測試衛星位置計算"""
        pass
        
    def test_predict_visibility_window(self):
        """測試可見性時間窗計算"""
        pass

# tests/unit/coordinates/test_coordinate_service.py  
class TestCoordinateService:
    def test_geodetic_to_ecef_conversion(self):
        """測試地理座標轉換"""
        pass
        
    def test_elevation_angle_calculation(self):
        """測試仰角計算"""
        pass
```

#### 5.2 整合測試更新
```python
# tests/integration/api/test_satellite_api.py
class TestSatelliteAPI:
    def test_get_visible_satellites(self):
        """測試可見衛星 API"""
        response = client.get("/api/satellite/visible?lat=24.9&lon=121.4")
        assert response.status_code == 200
        
    def test_get_handover_candidates(self):
        """測試切換候選 API"""
        pass
```

#### 5.3 效能測試
```python
# tests/performance/test_orbit_calculation.py
def test_batch_orbit_calculation_performance():
    """測試批量軌道計算效能"""
    import time
    start_time = time.time()
    
    # 執行批量計算
    result = orbit_service.calculate_batch_positions(satellites, timestamps)
    
    execution_time = time.time() - start_time
    assert execution_time < 1.0  # 1秒內完成
    assert len(result) == len(satellites) * len(timestamps)
```

### Phase 6: 部署與驗證

#### 6.1 容器重建與部署
```bash
# 重建 SimWorld Backend 容器
cd simworld
docker build -t simworld-backend:refactored .

# 更新 docker-compose 
docker-compose down simworld_backend
docker-compose up -d simworld_backend

# 檢查服務狀態
docker logs simworld_backend
curl -s http://localhost:8888/health | jq .
```

#### 6.2 完整系統驗證
```bash
# 執行完整測試套件
cd simworld/backend
python -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# 驗證 API 功能
bash scripts/api_integration_test.sh

# 驗證前端整合
curl -s http://localhost:5173 -I
curl -s http://localhost:5173/api/models/sat.glb -I
```

## 🔧 工具與腳本

### 自動化檢查腳本
```bash
#\!/bin/bash
# scripts/refactor_validation.sh

echo "🔍 執行重構驗證檢查..."

# 檢查移除的檔案是否仍有引用
echo "檢查死連結..."
grep -r "uav" simworld/backend/app/ --include="*.py" | grep -v "def.*uav" || echo "✅ 無 UAV 相關引用"
grep -r "precision_validator" simworld/backend/app/ --include="*.py" || echo "✅ 無精度驗證器引用"
grep -r "system_resource" simworld/backend/app/ --include="*.py" || echo "✅ 無系統資源監控引用"

# 檢查 API 端點
echo "檢查 API 端點..."
curl -s http://localhost:8888/health > /dev/null && echo "✅ 健康檢查正常" || echo "❌ 健康檢查失敗"
curl -s http://localhost:8888/api/satellite/visible_satellites?lat=24.9&lon=121.4 > /dev/null && echo "✅ 衛星 API 正常" || echo "❌ 衛星 API 失敗"

# 檢查模型檔案服務  
curl -s http://localhost:8888/sionna/models/sat.glb -I | grep "200 OK" > /dev/null && echo "✅ 模型服務正常" || echo "❌ 模型服務失敗"

echo "🎯 驗證完成"
```

### 程式碼品質檢查
```bash
#\!/bin/bash
# scripts/code_quality_check.sh

echo "🧹 執行程式碼品質檢查..."

cd simworld/backend

# 格式化程式碼
black app/
isort app/

# 程式碼品質檢查  
flake8 app/ --max-line-length=88 --ignore=E203,W503
pylint app/ --fail-under=8.0

# 型別檢查
mypy app/ --ignore-missing-imports

# 安全檢查
bandit -r app/

echo "✨ 程式碼品質檢查完成"
```

### 效能基準測試
```bash
#\!/bin/bash
# scripts/performance_benchmark.sh

echo "📊 執行效能基準測試..."

cd simworld/backend

# API 響應時間測試
echo "測試 API 響應時間..."
for i in {1..10}; do
  curl -w "%{time_total}\n" -o /dev/null -s http://localhost:8888/api/satellite/visible_satellites?lat=24.9&lon=121.4
done | awk '{sum+=$1; count++} END {print "平均響應時間: " sum/count " 秒"}'

# 記憶體使用測試  
echo "檢查記憶體使用..."
docker stats simworld_backend --no-stream --format "記憶體使用: {{.MemUsage}}"

# 軌道計算效能測試
echo "執行軌道計算效能測試..."
python -m pytest tests/performance/test_orbit_calculation.py --benchmark-only

echo "📈 效能基準測試完成"
```

## 📊 變更追蹤

### 變更日誌範本
```markdown
## [Unreleased] - Phase X 

### 移除 (Removed)
- 移除 UAV 追踪模組 (api/routes/uav.py)
- 移除系統資源監控域 (domains/system/)
- 移除開發期驗證工具

### 重構 (Refactored)  
- 統一距離計算邏輯
- 優化座標轉換服務
- 重組 API 路由結構

### 修正 (Fixed)
- 修正循環依賴問題
- 改善錯誤處理機制

### 效能改善 (Performance)
- 軌道計算效能提升 15%
- API 響應時間減少 20%  
- 記憶體使用降低 25%
```

### 測試覆蓋率追蹤
每個階段記錄測試覆蓋率變化:
```bash
# 生成測試報告
python -m pytest --cov=app --cov-report=json
python -c "
import json
with open('coverage.json') as f:
    data = json.load(f)
    print(f'總覆蓋率: {data[\"totals\"][\"percent_covered\"]:.1f}%')
"
```

---

**執行準則**: 嚴格按照階段執行，每階段完成後必須通過所有驗證檢查，確保系統穩定性和功能完整性。
EOF < /dev/null
