# 驗證與測試計畫

**文件版本**: 1.0.0  
**最後更新**: 2025-08-01  
**測試覆蓋**: 單元測試、整合測試、端到端測試、性能測試

## 📋 測試策略概述

### 測試金字塔
```
         /\
        /  \  端到端測試 (10%)
       /----\
      /      \  整合測試 (30%)
     /--------\
    /          \  單元測試 (60%)
   /____________\
```

### 測試原則
- **自動化優先** - 95% 測試自動化
- **持續整合** - 每次提交觸發測試
- **快速反饋** - 10 分鐘內完成基礎測試
- **全面覆蓋** - 代碼覆蓋率 > 85%

## 🧪 單元測試計畫

### 第一階段：零容忍篩選器
```python
# test_rl_optimized_filter.py

class TestRLOptimizedFilter:
    def test_parameter_validation(self):
        """測試參數完整性驗證"""
        filter = RLOptimizedSatelliteFilter()
        
        # 缺少必要參數
        invalid_sat = {"INCLINATION": 53.0}
        valid, reason = filter._validate_parameters(invalid_sat)
        assert not valid
        assert "Missing required parameter" in reason
        
    def test_physics_validation(self):
        """測試物理合理性驗證"""
        # 測試異常離心率
        sat_data = {
            "ECCENTRICITY": 0.5,  # 太高
            "MEAN_MOTION": 15.0
        }
        valid, reason = filter._validate_physics(sat_data)
        assert not valid
        
    def test_oneweb_acceptance(self):
        """確保 OneWeb 衛星通過篩選"""
        oneweb_data = load_test_data("oneweb_sample.json")
        accepted, rejected = filter.filter_satellites(oneweb_data)
        assert len(accepted) == len(oneweb_data)
        assert len(rejected) == 0
```

### 第二階段：軌道多樣性篩選
```python
# test_orbital_diversity.py

class TestOrbitalDiversityFilter:
    def test_raan_grouping(self):
        """測試 RAAN 分群算法"""
        satellites = generate_test_satellites(1000)
        filter = OrbitalDiversityFilter()
        groups = filter._group_by_orbital_plane(satellites)
        
        # 應該有 36 個組（每 10 度一組）
        assert len(groups) <= 36
        
        # 每組內的 RAAN 差異應小於 10 度
        for group in groups.values():
            raans = [s['RA_OF_ASC_NODE'] for s in group]
            assert max(raans) - min(raans) < 10
            
    def test_temporal_coverage(self):
        """測試時間覆蓋無空窗"""
        selected = filter.select_diverse_satellites(satellites, 500)
        coverage_valid, msg = filter._analyze_temporal_coverage(selected)
        assert coverage_valid, f"Coverage gap found: {msg}"
```

### 換手事件檢測測試
```python
# test_handover_events.py

class TestHandoverEventDetection:
    def test_d2_event_detection(self):
        """測試 D2 事件檢測準確性"""
        detector = D2EventDetector()
        
        # 創建測試場景：MRL 距離交叉
        serving_mrl = [800, 900, 1100, 1200]  # 遞增
        target_mrl = [1200, 1000, 700, 600]   # 遞減
        
        events = detector.detect(serving_mrl, target_mrl, timestamps)
        assert len(events) == 1
        assert events[0]['timestamp'] == timestamps[2]  # 交叉點
        
    def test_t1_prediction_accuracy(self):
        """測試 T1 事件預測準確性"""
        detector = T1EventDetector()
        
        # 模擬衛星即將消失的軌跡
        positions = simulate_satellite_pass(elevation_end=5)
        events = detector.detect(positions, ue_position, timestamps)
        
        # 應該在衛星消失前 30 秒觸發
        assert len(events) > 0
        assert 25 <= events[0]['time_to_loss_seconds'] <= 35
```

## 🔗 整合測試計畫

### API 整合測試
```python
# test_api_integration.py

class TestUnifiedAPI:
    @pytest.fixture
    def client(self):
        """測試客戶端"""
        return TestClient(app)
        
    def test_tier_filtering(self, client):
        """測試分層查詢功能"""
        # Tier 1 查詢
        response = client.get("/api/v1/satellites/unified/timeseries?tier=tier_1")
        assert response.status_code == 200
        data = response.json()
        assert len(data['satellites']) == 20
        
        # 驗證層級包含關係
        tier1_ids = {s['id'] for s in data['satellites']}
        
        # Tier 2 應包含所有 Tier 1
        response = client.get("/api/v1/satellites/unified/timeseries?tier=tier_2")
        tier2_data = response.json()
        tier2_ids = {s['id'] for s in tier2_data['satellites']}
        assert tier1_ids.issubset(tier2_ids)
        
    def test_backward_compatibility(self, client):
        """測試向後兼容性"""
        # 舊版 API 調用
        response = client.get("/api/v1/satellites/precomputed/ntpu")
        assert response.status_code == 200
        
        # 驗證舊格式字段存在
        data = response.json()
        assert 'positions' in data['satellites'][0]
```

### 數據管道整合測試
```python
# test_pipeline_integration.py

def test_full_pipeline():
    """測試完整的篩選和預處理管道"""
    # 1. 載入原始數據
    raw_satellites = load_raw_tle_data()
    
    # 2. 第一階段篩選
    rl_filter = RLOptimizedSatelliteFilter()
    stage1_output = rl_filter.filter_satellites(raw_satellites)
    assert len(stage1_output) < 2500
    
    # 3. 第二階段篩選
    diversity_filter = OrbitalDiversityFilter()
    stage2_output = diversity_filter.select_diverse_satellites(stage1_output, 500)
    assert 490 <= len(stage2_output) <= 510
    
    # 4. 統一預處理
    preprocessor = UnifiedSatellitePreprocessor()
    final_output = preprocessor.preprocess(stage2_output)
    
    # 驗證輸出格式
    assert 'metadata' in final_output
    assert 'satellites' in final_output
    assert all(event in final_output['satellites'][0]['handover_events'] 
              for event in ['d2', 'd1', 'a4', 't1'])
```

## 🚀 端到端測試

### 3D 渲染測試
```javascript
// test_3d_visualization.e2e.js

describe('3D Satellite Visualization', () => {
  it('should load only Tier 1 satellites', async () => {
    await page.goto('http://localhost:5173/3d-view');
    
    // 等待 3D 場景載入
    await page.waitForSelector('.cesium-viewer');
    
    // 檢查衛星數量
    const satelliteCount = await page.evaluate(() => {
      return window.cesiumViewer.entities.values.length;
    });
    
    expect(satelliteCount).toBeLessThanOrEqual(20);
  });
  
  it('should show smooth transitions without lag', async () => {
    const startTime = Date.now();
    
    // 模擬 60 秒動畫
    await page.evaluate(() => {
      window.cesiumViewer.clock.multiplier = 60;
    });
    
    await page.waitForTimeout(1000);
    
    // 檢查 FPS
    const fps = await page.evaluate(() => {
      return window.cesiumViewer.scene.frameState.fps;
    });
    
    expect(fps).toBeGreaterThan(30);
  });
});
```

### 換手事件圖表測試
```javascript
// test_handover_charts.e2e.js

describe('Handover Event Charts', () => {
  it('should display all event types', async () => {
    await page.goto('http://localhost:5173/handover/charts');
    
    // 檢查所有事件類型標籤
    const eventTypes = await page.$$eval('.event-legend-item', 
      items => items.map(item => item.textContent)
    );
    
    expect(eventTypes).toContain('D2 Event');
    expect(eventTypes).toContain('D1 Event');
    expect(eventTypes).toContain('A4 Event');
    expect(eventTypes).toContain('T1 Event');
  });
});
```

## 📊 性能測試

### 負載測試
```yaml
# k6_load_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },   // 漸增到 100 用戶
    { duration: '5m', target: 100 },   // 維持 100 用戶
    { duration: '2m', target: 200 },   // 增加到 200 用戶
    { duration: '5m', target: 200 },   // 維持 200 用戶
    { duration: '2m', target: 0 },     // 降到 0
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% 請求 < 500ms
    http_req_failed: ['rate<0.01'],   // 錯誤率 < 1%
  },
};

export default function() {
  // 測試不同 tier 的查詢
  const tier = ['tier_1', 'tier_2', 'tier_3'][Math.floor(Math.random() * 3)];
  const res = http.get(`http://localhost:8080/api/v1/satellites/unified/timeseries?tier=${tier}`);
  
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  
  sleep(1);
}
```

### 記憶體壓力測試
```python
# memory_stress_test.py

def test_memory_usage():
    """測試處理 500 顆衛星的記憶體使用"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # 執行完整預處理
    preprocessor = UnifiedSatellitePreprocessor()
    satellites = load_test_satellites(500)
    
    for _ in range(10):  # 重複 10 次
        result = preprocessor.preprocess(satellites)
        
    final_memory = process.memory_info().rss / 1024 / 1024
    memory_increase = final_memory - initial_memory
    
    assert memory_increase < 4000, f"Memory usage too high: {memory_increase}MB"
```

## 🛡️ 安全測試

### API 安全測試
```python
# test_security.py

def test_sql_injection_protection():
    """測試 SQL 注入防護"""
    malicious_params = [
        "'; DROP TABLE satellites; --",
        "1' OR '1'='1",
        "<script>alert('xss')</script>"
    ]
    
    for param in malicious_params:
        response = client.get(f"/api/v1/satellites/search?name={param}")
        assert response.status_code in [400, 422]  # Bad request
        assert "error" in response.json()

def test_rate_limiting():
    """測試速率限制"""
    # 快速發送 100 個請求
    responses = []
    for _ in range(100):
        r = client.get("/api/v1/satellites/unified/timeseries")
        responses.append(r.status_code)
    
    # 應該有一些請求被限流
    assert 429 in responses  # Too Many Requests
```

## 📈 測試指標與報告

### 測試覆蓋率目標
| 模組 | 目標覆蓋率 | 當前覆蓋率 |
|------|------------|------------|
| 零容忍篩選器 | 90% | - |
| 軌道多樣性篩選 | 85% | - |
| 換手事件檢測 | 90% | - |
| API 端點 | 95% | - |
| 前端組件 | 80% | - |

### 自動化測試報告
```bash
#!/bin/bash
# generate_test_report.sh

# 執行所有測試並生成報告
pytest --cov=. --cov-report=html --html=report.html
npm run test:coverage
k6 run k6_load_test.js --out json=load_test_results.json

# 整合報告
python consolidate_reports.py

# 發送到監控系統
curl -X POST http://monitoring.internal/api/test-results \
  -H "Content-Type: application/json" \
  -d @consolidated_report.json
```

## 🔄 持續整合配置

### GitHub Actions
```yaml
# .github/workflows/test.yml
name: Test Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Run Unit Tests
      run: |
        python -m pytest tests/unit -v
        
    - name: Run Integration Tests
      run: |
        docker-compose up -d
        python -m pytest tests/integration -v
        
    - name: Run E2E Tests
      run: |
        npm run test:e2e
        
    - name: Performance Tests
      if: github.ref == 'refs/heads/main'
      run: |
        k6 run tests/performance/load_test.js
```

## ✅ 測試完成標準

### 發布前必須通過
- [ ] 所有單元測試通過
- [ ] 整合測試無失敗
- [ ] E2E 測試全部綠燈
- [ ] 性能測試達標
- [ ] 安全掃描無高危漏洞
- [ ] 代碼覆蓋率 > 85%

### 測試報告要求
- [ ] 自動生成測試報告
- [ ] 包含失敗案例分析
- [ ] 性能基準對比
- [ ] 改進建議

## 📚 測試資源

- 測試數據集：`/tests/fixtures/`
- 測試工具：pytest, jest, k6, cypress
- CI/CD 平台：GitHub Actions
- 監控平台：Grafana + Prometheus
