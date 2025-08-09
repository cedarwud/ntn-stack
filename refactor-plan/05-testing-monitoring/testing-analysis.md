# 測試與監控系統建立分析報告

## 🎯 當前測試監控問題分析

### 嚴重問題: 測試覆蓋不足
**影響級別:** 🔴 嚴重 - 系統穩定性無法保證，部署風險高

#### 核心問題表現
1. **缺乏系統性測試架構**
   - 無單元測試覆蓋關鍵演算法
   - 無整合測試驗證API端點
   - 無端對端測試確保功能完整

2. **監控系統缺失**
   - 無實時性能監控
   - 無錯誤追蹤和報告
   - 無系統健康指標收集

3. **部署驗證不足**
   - 無自動化回歸測試
   - 無配置驗證機制
   - 無性能基準比較

## 📊 測試覆蓋現狀分析

### 1. 當前測試狀況評估

**代碼覆蓋率分析:**
```
netstack_api/
├── 🔴 main.py                    (0% 測試覆蓋)
├── 🔴 routers/                   (10% 測試覆蓋)
│   ├── satellite_router.py       (無測試)
│   └── simple_satellite_router.py (基本測試)
├── 🔴 services/                  (5% 測試覆蓋)
│   ├── satellite/                (演算法無測試)
│   └── preprocessing/            (關鍵邏輯無測試)
└── 🔴 algorithms/                (0% 測試覆蓋)
    ├── handover/                 (切換決策無驗證)
    └── prediction/               (軌道預測無測試)
```

**關鍵風險點:**
- **衛星選擇演算法** 無單元測試 (150/50配置變更風險)
- **SGP4軌道計算** 無精度驗證 (計算錯誤風險)
- **數據庫連接管理** 無連接池測試 (連接洩漏風險)
- **API端點** 無錯誤場景測試 (500錯誤風險)

### 2. 監控系統缺失分析

**缺失的監控指標:**
```yaml
系統監控:
  ❌ CPU/Memory使用率追蹤
  ❌ 磁碟I/O監控
  ❌ 網路流量分析
  ❌ 容器健康狀態

應用監控:
  ❌ API響應時間統計
  ❌ 衛星計算性能指標
  ❌ 數據庫查詢效能
  ❌ 錯誤率和異常追蹤

業務監控:
  ❌ 衛星可見數量趨勢
  ❌ 切換決策準確度
  ❌ 數據更新成功率
  ❌ 用戶行為分析
```

## 🛠️ 測試監控架構解決方案

### 方案概述: 五層測試監控體系
```
📁 測試監控架構
├── 🧪 Unit Testing Layer         # 單元測試
├── 🔗 Integration Testing Layer  # 整合測試  
├── 🌐 E2E Testing Layer          # 端對端測試
├── 📊 Monitoring Layer           # 監控系統
└── 🚨 Alerting Layer             # 告警系統
```

### 1. 單元測試架構設計

#### 核心演算法測試
```python
# /tests/unit/algorithms/test_satellite_selector.py

import pytest
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from netstack_api.services.satellite.preprocessing.satellite_selector import (
    SatelliteSelector, 
    LayeredElevationThreshold,
    CoordinateSpecificOrbitEngine
)

class TestSatelliteSelector:
    """衛星選擇器單元測試"""
    
    @pytest.fixture
    def satellite_selector(self):
        """測試用衛星選擇器實例"""
        return SatelliteSelector()
    
    @pytest.fixture  
    def mock_tle_data(self):
        """模擬TLE數據"""
        return {
            "starlink": [
                {
                    "satellite_id": "STARLINK-123",
                    "line1": "1 47964U 21022AL  25219.50000000  .00001234  00000-0  12345-4 0  9991",
                    "line2": "2 47964  53.0538 123.4567 0001234  12.3456  78.9012 15.12345678123456",
                    "epoch": datetime.now(timezone.utc)
                }
                # ... 更多測試數據
            ]
        }
    
    def test_target_counts_configuration(self, satellite_selector):
        """測試目標衛星數量配置"""
        starlink_target, oneweb_target = satellite_selector.get_target_counts()
        
        # 驗證配置值正確性
        assert starlink_target == 150, f"Starlink目標數量應為150，實際為{starlink_target}"
        assert oneweb_target == 50, f"OneWeb目標數量應為50，實際為{oneweb_target}"
        
        # 驗證數量合理性
        assert 50 <= starlink_target <= 300, "Starlink目標數量應在合理範圍內"
        assert 20 <= oneweb_target <= 100, "OneWeb目標數量應在合理範圍內"
    
    def test_elevation_threshold_calculation(self, satellite_selector):
        """測試仰角門檻計算"""
        # 測試不同星座的仰角門檻
        starlink_threshold = satellite_selector.get_elevation_threshold("starlink")
        oneweb_threshold = satellite_selector.get_elevation_threshold("oneweb")
        
        assert starlink_threshold == 10.0, "Starlink仰角門檻應為10度"
        assert oneweb_threshold == 10.0, "OneWeb仰角門檻應為10度"
        
        # 測試無效星座
        default_threshold = satellite_selector.get_elevation_threshold("invalid")
        assert default_threshold == 10.0, "無效星座應返回預設門檻"
    
    def test_observer_location_accuracy(self, satellite_selector):
        """測試觀測點位置精度"""
        lat, lon, alt = satellite_selector.get_observer_location()
        
        # NTPU座標精度驗證
        assert abs(lat - 24.9441667) < 0.0001, f"緯度精度不足: {lat}"
        assert abs(lon - 121.3713889) < 0.0001, f"經度精度不足: {lon}"
        assert 0 <= alt <= 1000, f"海拔高度不合理: {alt}"
    
    @patch('netstack_api.services.satellite.tle_data_loader.load_tle_data')
    def test_satellite_filtering_accuracy(self, mock_load_tle, satellite_selector, mock_tle_data):
        """測試衛星過濾精度"""
        mock_load_tle.return_value = mock_tle_data
        
        # 執行衛星選擇
        selected_satellites = satellite_selector.select_satellites(
            constellation="starlink",
            target_count=10,
            timestamp=datetime.now(timezone.utc)
        )
        
        # 驗證選擇結果
        assert len(selected_satellites) <= 10, "選擇數量不應超過目標"
        assert all(sat["elevation_deg"] >= 10.0 for sat in selected_satellites), "所有衛星仰角應≥10度"
        
        # 驗證排序正確性 (按仰角降序)
        elevations = [sat["elevation_deg"] for sat in selected_satellites]
        assert elevations == sorted(elevations, reverse=True), "衛星應按仰角降序排列"

class TestLayeredElevationThreshold:
    """分層仰角門檻測試"""
    
    def test_threshold_layers(self):
        """測試分層門檻邏輯"""
        threshold = LayeredElevationThreshold()
        
        # 測試預備觸發 (15°)
        assert threshold.is_prepare_trigger(16.0) == True
        assert threshold.is_prepare_trigger(14.0) == False
        
        # 測試執行門檻 (10°)
        assert threshold.is_execute_threshold(11.0) == True
        assert threshold.is_execute_threshold(9.0) == False
        
        # 測試臨界門檻 (5°)
        assert threshold.is_critical_threshold(6.0) == True
        assert threshold.is_critical_threshold(4.0) == False

class TestCoordinateSpecificOrbitEngine:
    """座標特定軌道引擎測試"""
    
    @pytest.fixture
    def orbit_engine(self):
        """測試用軌道引擎"""
        return CoordinateSpecificOrbitEngine(
            observer_lat=24.9441667,
            observer_lon=121.3713889,
            observer_alt=50.0
        )
    
    def test_sgp4_calculation_accuracy(self, orbit_engine):
        """測試SGP4計算精度"""
        # 使用已知TLE數據計算位置
        test_tle = {
            "line1": "1 25544U 98067A   21001.00000000  .00001817  00000-0  41860-4 0  9990",
            "line2": "2 25544  51.6461 290.5094 0000597  91.8164 268.3516 15.48919103262509"
        }
        
        position, velocity = orbit_engine.calculate_satellite_position(
            test_tle, 
            datetime(2021, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        )
        
        # 驗證計算結果合理性
        position_magnitude = np.linalg.norm(position)
        velocity_magnitude = np.linalg.norm(velocity)
        
        assert 6500 <= position_magnitude <= 8000, f"軌道高度不合理: {position_magnitude} km"
        assert 5 <= velocity_magnitude <= 10, f"軌道速度不合理: {velocity_magnitude} km/s"
    
    def test_elevation_azimuth_calculation(self, orbit_engine):
        """測試仰角方位角計算"""
        # 模擬NTPU上方的衛星位置
        satellite_position = np.array([6500.0, 0.0, 2000.0])  # 粗略位置
        
        elevation, azimuth = orbit_engine.calculate_elevation_azimuth(satellite_position)
        
        # 驗證角度範圍
        assert -90 <= elevation <= 90, f"仰角超出範圍: {elevation}°"
        assert 0 <= azimuth <= 360, f"方位角超出範圍: {azimuth}°"
    
    def test_visibility_determination(self, orbit_engine):
        """測試可見性判斷"""
        # 測試可見衛星 (仰角15°)
        visible_result = orbit_engine.is_satellite_visible(
            satellite_position=np.array([6500.0, 0.0, 3000.0]),
            min_elevation=10.0
        )
        assert visible_result == True, "高仰角衛星應該可見"
        
        # 測試不可見衛星 (仰角5°)  
        invisible_result = orbit_engine.is_satellite_visible(
            satellite_position=np.array([6500.0, 0.0, 500.0]),
            min_elevation=10.0
        )
        assert invisible_result == False, "低仰角衛星應該不可見"
```

#### API端點測試
```python
# /tests/integration/api/test_satellite_api.py

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient

from netstack_api.main import app

class TestSatelliteAPI:
    """衛星API整合測試"""
    
    @pytest.fixture
    def client(self):
        """測試客戶端"""
        return TestClient(app)
    
    @pytest.fixture
    async def async_client(self):
        """異步測試客戶端"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    def test_health_endpoint(self, client):
        """測試健康檢查端點"""
        response = client.get("/health")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "ok", "running"]
        
        # 驗證回應時間 (<100ms)
        assert response.elapsed.total_seconds() < 0.1
    
    def test_constellation_info_endpoint(self, client):
        """測試星座資訊端點"""
        response = client.get("/api/v1/satellites/constellations/info")
        
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert "starlink" in data
        assert "oneweb" in data
        
        # 驗證Starlink資訊
        starlink_info = data["starlink"]
        assert "target_count" in starlink_info
        assert starlink_info["target_count"] == 150
        
        # 驗證OneWeb資訊
        oneweb_info = data["oneweb"]
        assert "target_count" in oneweb_info
        assert oneweb_info["target_count"] == 50
    
    @pytest.mark.asyncio
    async def test_satellite_positions_endpoint(self, async_client):
        """測試衛星位置查詢端點"""
        # 測試基本查詢
        response = await async_client.get(
            "/api/v1/satellites/positions",
            params={
                "constellation": "starlink",
                "limit": 10,
                "min_elevation": 10.0
            }
        )
        
        assert response.status_code == 200
        
        data = response.json()
        assert "satellites" in data
        assert "total_count" in data
        assert "query_params" in data
        
        satellites = data["satellites"]
        assert len(satellites) <= 10
        
        # 驗證衛星資料結構
        if satellites:
            first_satellite = satellites[0]
            required_fields = ["satellite_id", "elevation_deg", "azimuth_deg", "distance_km"]
            for field in required_fields:
                assert field in first_satellite, f"缺少必要欄位: {field}"
            
            # 驗證仰角門檻
            assert all(sat["elevation_deg"] >= 10.0 for sat in satellites)
    
    def test_api_error_handling(self, client):
        """測試API錯誤處理"""
        # 測試無效星座
        response = client.get(
            "/api/v1/satellites/positions",
            params={"constellation": "invalid_constellation"}
        )
        assert response.status_code == 400
        
        # 測試無效參數
        response = client.get(
            "/api/v1/satellites/positions", 
            params={"min_elevation": -10}  # 無效仰角
        )
        assert response.status_code == 400
        
        # 測試過大的limit
        response = client.get(
            "/api/v1/satellites/positions",
            params={"limit": 10000}  # 過大
        )
        assert response.status_code == 400
    
    def test_api_performance_requirements(self, client):
        """測試API性能需求"""
        import time
        
        # 測試響應時間 (應<100ms)
        start_time = time.time()
        response = client.get("/api/v1/satellites/constellations/info")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 0.1, f"響應時間過長: {response_time:.3f}s"
        
        # 測試並發處理
        import threading
        results = []
        
        def make_request():
            resp = client.get("/health")
            results.append(resp.status_code)
        
        # 同時發送10個請求
        threads = [threading.Thread(target=make_request) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # 所有請求都應該成功
        assert all(status == 200 for status in results), "並發請求處理失敗"
```

### 2. 系統監控架構設計

#### Prometheus + Grafana 監控堆疊
```yaml
# /docker/compose/docker-compose.monitoring.yaml

version: '3.8'

services:
  # Prometheus - 指標收集
  prometheus:
    image: prom/prometheus:v2.47.0
    container_name: netstack-prometheus
    hostname: prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
    volumes:
      - ../monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ../monitoring/alert_rules.yml:/etc/prometheus/alert_rules.yml:ro
      - prometheus_data:/prometheus
    networks:
      netstack-network:
        ipv4_address: 172.20.0.90
    ports:
      - "9090:9090"
    restart: unless-stopped
    
  # Grafana - 視覺化儀表板
  grafana:
    image: grafana/grafana:10.1.0
    container_name: netstack-grafana
    hostname: grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin123}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ../monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ../monitoring/grafana/datasources:/etc/grafana/provisioning/datasources:ro
    networks:
      netstack-network:
        ipv4_address: 172.20.0.91
    ports:
      - "3000:3000"
    restart: unless-stopped
    depends_on:
      - prometheus
    
  # Node Exporter - 系統指標收集
  node-exporter:
    image: prom/node-exporter:v1.6.1
    container_name: netstack-node-exporter
    hostname: node-exporter
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    networks:
      netstack-network:
        ipv4_address: 172.20.0.92
    ports:
      - "9100:9100"
    restart: unless-stopped
    
  # cAdvisor - 容器指標收集
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.47.0
    container_name: netstack-cadvisor
    hostname: cadvisor
    privileged: true
    devices:
      - /dev/kmsg:/dev/kmsg
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      netstack-network:
        ipv4_address: 172.20.0.93
    ports:
      - "8080:8080"  # 注意: 與API端口衝突，需要調整
    restart: unless-stopped

networks:
  netstack-network:
    external: true

volumes:
  prometheus_data:
    driver: local
  grafana_data:
    driver: local
```

#### 應用程式監控整合
```python
# /netstack_api/app/core/monitoring.py

from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
import functools
import logging
from typing import Optional, Dict, Any

# 定義Prometheus指標
REQUEST_COUNT = Counter(
    'netstack_api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'netstack_api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint']
)

SATELLITE_CALCULATION_DURATION = Histogram(
    'netstack_satellite_calculation_duration_seconds',
    'Satellite calculation duration in seconds',
    ['constellation', 'calculation_type']
)

ACTIVE_SATELLITES = Gauge(
    'netstack_active_satellites_total',
    'Number of active satellites',
    ['constellation']
)

DATABASE_CONNECTIONS = Gauge(
    'netstack_database_connections_active',
    'Number of active database connections',
    ['database_type']
)

SYSTEM_HEALTH_SCORE = Gauge(
    'netstack_system_health_score',
    'Overall system health score (0-100)'
)

logger = logging.getLogger(__name__)

class MetricsCollector:
    """NetStack 指標收集器"""
    
    def __init__(self):
        self.start_time = time.time()
        
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """記錄API請求指標"""
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint, 
            status_code=str(status_code)
        ).inc()
        
        REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_satellite_calculation(self, constellation: str, calculation_type: str, duration: float):
        """記錄衛星計算指標"""
        SATELLITE_CALCULATION_DURATION.labels(
            constellation=constellation,
            calculation_type=calculation_type
        ).observe(duration)
    
    def update_satellite_count(self, constellation: str, count: int):
        """更新活躍衛星數量"""
        ACTIVE_SATELLITES.labels(constellation=constellation).set(count)
    
    def update_database_connections(self, db_type: str, count: int):
        """更新數據庫連接數"""
        DATABASE_CONNECTIONS.labels(database_type=db_type).set(count)
    
    def update_system_health(self, health_score: float):
        """更新系統健康分數"""
        SYSTEM_HEALTH_SCORE.set(health_score)
    
    def calculate_system_health(self) -> float:
        """計算系統健康分數"""
        try:
            # 基礎健康分數
            health_score = 100.0
            
            # 檢查關鍵組件狀態
            components_health = self._check_components_health()
            
            for component, status in components_health.items():
                if not status['healthy']:
                    penalty = status.get('penalty', 20)
                    health_score -= penalty
                    logger.warning(f"組件 {component} 不健康，扣除 {penalty} 分")
            
            # 確保健康分數在0-100範圍內
            health_score = max(0.0, min(100.0, health_score))
            
            return health_score
            
        except Exception as e:
            logger.error(f"計算系統健康分數失敗: {e}")
            return 50.0  # 返回中等健康分數
    
    def _check_components_health(self) -> Dict[str, Dict[str, Any]]:
        """檢查組件健康狀態"""
        components = {
            'database': {'healthy': True, 'penalty': 30},
            'satellite_calculation': {'healthy': True, 'penalty': 20}, 
            'api_response': {'healthy': True, 'penalty': 15},
            'memory_usage': {'healthy': True, 'penalty': 10}
        }
        
        try:
            # 檢查數據庫連接
            # TODO: 實際的數據庫健康檢查邏輯
            
            # 檢查API響應時間
            # TODO: 實際的響應時間檢查邏輯
            
            # 檢查記憶體使用率
            # TODO: 實際的記憶體使用率檢查邏輯
            
        except Exception as e:
            logger.error(f"組件健康檢查失敗: {e}")
        
        return components

# 全域指標收集器實例
metrics_collector = MetricsCollector()

def monitor_api_request(func):
    """API請求監控裝飾器"""
    @functools.wraps(func)
    async def wrapper(request, *args, **kwargs):
        start_time = time.time()
        method = request.method
        endpoint = str(request.url.path)
        status_code = 200
        
        try:
            response = await func(request, *args, **kwargs)
            if hasattr(response, 'status_code'):
                status_code = response.status_code
            return response
        except Exception as e:
            status_code = 500
            logger.error(f"API請求失敗 {method} {endpoint}: {e}")
            raise
        finally:
            duration = time.time() - start_time
            metrics_collector.record_request(method, endpoint, status_code, duration)
    
    return wrapper

def monitor_satellite_calculation(constellation: str, calculation_type: str):
    """衛星計算監控裝飾器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metrics_collector.record_satellite_calculation(constellation, calculation_type, duration)
        return wrapper
    return decorator
```

## 📊 監控儀表板設計

### Grafana 儀表板配置
```json
{
  "dashboard": {
    "title": "NetStack LEO 衛星系統監控",
    "panels": [
      {
        "title": "系統健康總覽",
        "type": "stat",
        "targets": [
          {
            "expr": "netstack_system_health_score",
            "legendFormat": "健康分數"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                {"color": "red", "value": 0},
                {"color": "yellow", "value": 60},
                {"color": "green", "value": 80}
              ]
            }
          }
        }
      },
      {
        "title": "API請求量",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(netstack_api_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "API響應時間",
        "type": "graph", 
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(netstack_api_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(netstack_api_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "title": "活躍衛星數量",
        "type": "graph",
        "targets": [
          {
            "expr": "netstack_active_satellites_total",
            "legendFormat": "{{constellation}}"
          }
        ]
      },
      {
        "title": "衛星計算性能",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(netstack_satellite_calculation_duration_seconds_sum[5m]) / rate(netstack_satellite_calculation_duration_seconds_count[5m])",
            "legendFormat": "{{constellation}} - {{calculation_type}}"
          }
        ]
      },
      {
        "title": "數據庫連接數",
        "type": "graph",
        "targets": [
          {
            "expr": "netstack_database_connections_active",
            "legendFormat": "{{database_type}}"
          }
        ]
      },
      {
        "title": "容器資源使用",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(container_cpu_usage_seconds_total{name=\"netstack-api\"}[5m]) * 100",
            "legendFormat": "CPU 使用率 %"
          },
          {
            "expr": "container_memory_usage_bytes{name=\"netstack-api\"} / container_spec_memory_limit_bytes{name=\"netstack-api\"} * 100",
            "legendFormat": "記憶體使用率 %"
          }
        ]
      }
    ]
  }
}
```

## 🚨 告警系統設計

### Prometheus 告警規則
```yaml
# /docker/monitoring/alert_rules.yml

groups:
  - name: netstack_critical_alerts
    rules:
      - alert: SystemHealthCritical
        expr: netstack_system_health_score < 50
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "NetStack系統健康狀況嚴重"
          description: "系統健康分數 {{ $value }} 低於50，需要立即處理"
      
      - alert: APIResponseTimeHigh
        expr: histogram_quantile(0.95, rate(netstack_api_request_duration_seconds_bucket[5m])) > 1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "API響應時間過長"
          description: "95th percentile 響應時間 {{ $value }}s 超過 1 秒"
      
      - alert: SatelliteCalculationSlow
        expr: rate(netstack_satellite_calculation_duration_seconds_sum[5m]) / rate(netstack_satellite_calculation_duration_seconds_count[5m]) > 5
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "衛星計算速度過慢"
          description: "衛星計算平均時間 {{ $value }}s 超過 5 秒"
      
      - alert: DatabaseConnectionHigh
        expr: netstack_database_connections_active > 50
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "數據庫連接數過高"
          description: "{{ $labels.database_type }} 連接數 {{ $value }} 超過 50"
      
      - alert: ContainerMemoryHigh
        expr: container_memory_usage_bytes{name="netstack-api"} / container_spec_memory_limit_bytes{name="netstack-api"} > 0.9
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "容器記憶體使用率過高"
          description: "NetStack API 記憶體使用率 {{ $value | humanizePercentage }} 超過 90%"

  - name: netstack_business_alerts
    rules:
      - alert: SatelliteCountTooLow
        expr: netstack_active_satellites_total < 20
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "可見衛星數量過少"
          description: "{{ $labels.constellation }} 可見衛星數量 {{ $value }} 少於 20 顆"
      
      - alert: APIErrorRateHigh
        expr: rate(netstack_api_requests_total{status_code=~"5.."}[5m]) / rate(netstack_api_requests_total[5m]) > 0.1
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "API錯誤率過高"
          description: "API 5xx 錯誤率 {{ $value | humanizePercentage }} 超過 10%"
```

---

*測試監控建立分析報告*  
*版本: v1.0*  
*制定時間: 2025-08-09*