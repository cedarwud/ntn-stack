# Phase 1 整合指南

**版本**: v1.0.0  
**建立日期**: 2025-08-12  
**目標**: 完整的 Phase 1 → Phase 2 系統整合指南  

## 🎯 整合概述

本指南詳細說明如何將 Phase 1 重構系統整合到現有的 NTN Stack 架構中，確保：
- **無縫替換**原有的 phase0/simple_satellite 系統
- **標準化接口**供 Phase 2 使用
- **向下兼容**現有的 API 調用
- **性能提升**和穩定性改善

## 📁 系統架構整合

### 原有架構 vs 新架構

#### 原有架構 (Before)
```
netstack/
├── netstack_api/
│   ├── routers/
│   │   ├── simple_satellite_router.py    ❌ 將被替換
│   │   └── coordinate_orbit_endpoints.py ❌ 部分功能重疊
│   └── services/
│       └── satellite/                    ❌ 分散的實現
└── generate_precomputed_satellite_data.py ❌ 建構時混亂
```

#### 新架構 (After)
```
netstack/
├── phase1_refactor/                     ✅ 新的標準化實現
│   ├── 01_data_source/                 ✅ 統一 TLE 管理
│   ├── 02_orbit_calculation/           ✅ 純 SGP4 引擎
│   ├── 03_processing_pipeline/         ✅ 標準化處理
│   ├── 04_output_interface/            ✅ 標準化 API
│   └── 05_integration/                 ✅ 測試驗證
└── netstack_api/
    └── routers/
        └── phase1_router.py             ✅ 整合的標準路由
```

### 整合映射關係

| 原有組件 | 新組件 | 整合方式 |
|---------|-------|---------|
| `simple_satellite_router.py` | `phase1_api_enhanced.py` | 直接替換 + 兼容接口 |
| `coordinate_orbit_endpoints.py` | `phase2_interface.py` | 標準化重構 |
| `generate_precomputed_satellite_data.py` | `phase1_coordinator.py` | 職責分離重構 |
| 分散的衛星服務 | `sgp4_engine.py` + `tle_loader.py` | 統一整合 |

## 🔧 逐步整合流程

### Step 1: 準備階段

#### 1.1 備份現有系統
```bash
# 創建備份目錄
mkdir -p /home/sat/ntn-stack/backup/pre-phase1-integration/

# 備份關鍵文件
cp netstack/netstack_api/routers/simple_satellite_router.py backup/pre-phase1-integration/
cp netstack/netstack_api/routers/coordinate_orbit_endpoints.py backup/pre-phase1-integration/
cp netstack/generate_precomputed_satellite_data.py backup/pre-phase1-integration/

# 備份配置文件
cp -r netstack/netstack_api/services/satellite/ backup/pre-phase1-integration/satellite_services/
```

#### 1.2 驗證 Phase 1 系統
```bash
# 切換到 Phase 1 目錄
cd /home/sat/ntn-stack/phase1_refactor/

# 執行完整驗證
python validate_phase1_refactor.py

# 確認所有組件正常
python demo_phase1_refactor.py
```

### Step 2: 路由整合

#### 2.1 創建新的統一路由文件
```python
# netstack/netstack_api/routers/phase1_router.py

from fastapi import APIRouter, HTTPException
import sys
from pathlib import Path

# 添加 Phase 1 路徑
PHASE1_ROOT = Path(__file__).parent.parent.parent / "phase1_refactor"
sys.path.insert(0, str(PHASE1_ROOT / "04_output_interface"))

# 導入 Phase 1 增強 API
from phase1_api_enhanced import app as phase1_app

# 創建 Phase 1 路由器
router = APIRouter(prefix="/api/v1", tags=["Phase 1 Integrated"])

# 掛載整個 Phase 1 應用作為子路由
router.mount("/phase1", phase1_app)

# 提供直接兼容的端點
@router.get("/satellite_orbits")
async def get_satellite_orbits_direct(
    constellation: str,
    count: int = 200
):
    """直接兼容原有 simple_satellite_router 的端點"""
    # 重定向到新的 Phase 1 API
    from phase1_api_enhanced import get_satellite_orbits_legacy
    return await get_satellite_orbits_legacy(constellation, count)
```

#### 2.2 更新主應用路由
```python
# netstack/netstack_api/main.py (或相應的主應用文件)

from fastapi import FastAPI
from routers import phase1_router  # 新的整合路由

app = FastAPI(title="NetStack API Enhanced")

# 替換原有路由
# app.include_router(simple_satellite_router.router)  # 移除
app.include_router(phase1_router.router)              # 添加

# 其他路由保持不變...
```

### Step 3: 配置整合

#### 3.1 環境變量設置
```bash
# 在 .env 或環境配置中添加
export PHASE1_TLE_DATA_PATH="/netstack/tle_data"
export PHASE1_OUTPUT_PATH="/app/data"
export PHASE1_LOG_LEVEL="INFO"
export PHASE1_CACHE_SIZE="1000"
export PHASE1_API_TIMEOUT="30"
```

#### 3.2 Docker 配置更新
```dockerfile
# 在 Dockerfile 中添加 Phase 1 支援

# 複製 Phase 1 代碼
COPY phase1_refactor/ /app/phase1_refactor/

# 安裝 Phase 1 依賴
RUN pip install -r phase1_refactor/requirements.txt

# 設置 Python 路徑
ENV PYTHONPATH="${PYTHONPATH}:/app/phase1_refactor"
```

#### 3.3 docker-compose 配置
```yaml
# docker-compose.yml 中的更新

services:
  netstack-api:
    build: .
    volumes:
      - ./phase1_refactor:/app/phase1_refactor  # 掛載 Phase 1 代碼
      - ./tle_data:/netstack/tle_data           # TLE 數據路徑
    environment:
      - PHASE1_TLE_DATA_PATH=/netstack/tle_data
      - PHASE1_OUTPUT_PATH=/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/v1/phase1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Step 4: 數據遷移

#### 4.1 TLE 數據遷移
```bash
#!/bin/bash
# migrate_tle_data.sh

echo "遷移 TLE 數據到 Phase 1 標準格式..."

# 確保目標目錄存在
mkdir -p /netstack/tle_data/starlink/tle/
mkdir -p /netstack/tle_data/oneweb/tle/

# 如果原有數據在不同位置，複製到標準位置
if [ -d "/app/old_tle_data/" ]; then
    echo "發現原有 TLE 數據，開始遷移..."
    cp /app/old_tle_data/starlink*.tle /netstack/tle_data/starlink/tle/
    cp /app/old_tle_data/oneweb*.tle /netstack/tle_data/oneweb/tle/
    echo "TLE 數據遷移完成"
fi

# 驗證數據完整性
python /app/phase1_refactor/01_data_source/tle_loader.py --validate
```

#### 4.2 預計算數據清理
```bash
#!/bin/bash
# cleanup_old_precomputed.sh

echo "清理舊的預計算數據..."

# 移除舊的預計算文件
rm -f /app/data/phase0_*.json
rm -f /app/data/simple_satellite_*.json
rm -f /app/data/precomputed_orbits.json

echo "舊預計算數據已清理"
```

### Step 5: 漸進式切換

#### 5.1 藍綠部署策略
```python
# config/feature_flags.py

import os

class FeatureFlags:
    """功能切換標識"""
    
    # Phase 1 相關標識
    USE_PHASE1_API = os.getenv("USE_PHASE1_API", "false").lower() == "true"
    USE_LEGACY_API = os.getenv("USE_LEGACY_API", "true").lower() == "true"
    
    # 混合模式：同時支援新舊 API
    HYBRID_MODE = os.getenv("HYBRID_MODE", "true").lower() == "true"
    
    @classmethod
    def should_use_phase1(cls, endpoint: str) -> bool:
        """判斷是否使用 Phase 1 API"""
        if cls.USE_PHASE1_API:
            return True
        
        # 漸進式切換規則
        phase1_endpoints = [
            "/satellite_orbits",
            "/constellations/info"
        ]
        
        return cls.HYBRID_MODE and any(ep in endpoint for ep in phase1_endpoints)
```

#### 5.2 智能路由切換
```python
# routers/adaptive_router.py

from fastapi import APIRouter, Request, HTTPException
from config.feature_flags import FeatureFlags
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")

@router.get("/satellite_orbits")
async def adaptive_satellite_orbits(request: Request, constellation: str, count: int = 200):
    """自適應衛星軌道數據端點"""
    
    endpoint_path = str(request.url.path)
    
    try:
        if FeatureFlags.should_use_phase1(endpoint_path):
            # 使用 Phase 1 新 API
            logger.info(f"使用 Phase 1 API 處理請求: {endpoint_path}")
            from phase1_api_enhanced import get_satellite_orbits_legacy
            return await get_satellite_orbits_legacy(constellation, count)
        
        elif FeatureFlags.USE_LEGACY_API:
            # 使用舊 API
            logger.info(f"使用舊 API 處理請求: {endpoint_path}")
            from simple_satellite_router import get_phase0_satellite_data
            return get_phase0_satellite_data(constellation, count)
        
        else:
            raise HTTPException(status_code=503, detail="服務暫不可用")
            
    except Exception as e:
        logger.error(f"自適應路由失敗 {endpoint_path}: {e}")
        # 降級到可用的 API
        if FeatureFlags.USE_LEGACY_API and not FeatureFlags.should_use_phase1(endpoint_path):
            try:
                from simple_satellite_router import get_phase0_satellite_data
                return get_phase0_satellite_data(constellation, count)
            except Exception as fallback_error:
                logger.error(f"降級處理也失敗: {fallback_error}")
        
        raise HTTPException(status_code=500, detail="所有 API 都不可用")
```

### Step 6: 監控與驗證

#### 6.1 整合測試腳本
```python
#!/usr/bin/env python3
# integration_test.py

import requests
import json
import time
import logging
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationTester:
    """Phase 1 整合測試器"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.test_results = []
    
    def test_health_endpoints(self):
        """測試健康檢查端點"""
        endpoints = [
            "/api/v1/phase1/health",
            "/health",
            "/api/v1/health"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                success = response.status_code == 200
                
                self.test_results.append({
                    "test": f"Health Check - {endpoint}",
                    "success": success,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                })
                
                logger.info(f"{'✅' if success else '❌'} {endpoint}: {response.status_code}")
                
            except Exception as e:
                self.test_results.append({
                    "test": f"Health Check - {endpoint}",
                    "success": False,
                    "error": str(e)
                })
                logger.error(f"❌ {endpoint}: {e}")
    
    def test_data_endpoints(self):
        """測試數據查詢端點"""
        tests = [
            {
                "endpoint": "/api/v1/phase1/satellite_orbits",
                "params": {"constellation": "starlink", "count": 10}
            },
            {
                "endpoint": "/api/v1/phase1/constellations/info",
                "params": {}
            },
            {
                "endpoint": "/satellites",
                "params": {"constellation": "starlink", "limit": 10}
            }
        ]
        
        for test in tests:
            try:
                response = requests.get(
                    f"{self.base_url}{test['endpoint']}",
                    params=test['params'],
                    timeout=30
                )
                
                success = response.status_code == 200
                data = response.json() if success else None
                
                self.test_results.append({
                    "test": f"Data Query - {test['endpoint']}",
                    "success": success,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                    "data_size": len(json.dumps(data)) if data else 0
                })
                
                logger.info(f"{'✅' if success else '❌'} {test['endpoint']}: {response.status_code}")
                
            except Exception as e:
                self.test_results.append({
                    "test": f"Data Query - {test['endpoint']}",
                    "success": False,
                    "error": str(e)
                })
                logger.error(f"❌ {test['endpoint']}: {e}")
    
    def test_performance_benchmarks(self):
        """測試性能基準"""
        # 測試響應時間
        start_time = time.time()
        
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/phase1/satellite_orbits",
                params={"constellation": "starlink", "count": 100},
                timeout=30
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # 性能要求：< 500ms for 100 records
            performance_ok = response_time < 0.5
            
            self.test_results.append({
                "test": "Performance Benchmark - 100 Records",
                "success": performance_ok,
                "response_time": response_time,
                "target_time": 0.5,
                "status_code": response.status_code
            })
            
            logger.info(f"{'✅' if performance_ok else '❌'} Performance: {response_time:.3f}s")
            
        except Exception as e:
            self.test_results.append({
                "test": "Performance Benchmark",
                "success": False,
                "error": str(e)
            })
            logger.error(f"❌ Performance test failed: {e}")
    
    def run_all_tests(self) -> Dict:
        """執行所有整合測試"""
        logger.info("開始 Phase 1 整合測試...")
        
        self.test_health_endpoints()
        self.test_data_endpoints()
        self.test_performance_benchmarks()
        
        # 統計結果
        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result["success"])
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        summary = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": success_rate,
            "test_results": self.test_results
        }
        
        logger.info(f"整合測試完成: {successful_tests}/{total_tests} 通過 ({success_rate:.1f}%)")
        
        return summary

def main():
    """主函數"""
    tester = IntegrationTester()
    results = tester.run_all_tests()
    
    # 保存測試結果
    with open("/tmp/phase1_integration_test_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # 返回適當的退出碼
    return 0 if results["success_rate"] >= 90.0 else 1

if __name__ == "__main__":
    exit(main())
```

#### 6.2 監控腳本
```bash
#!/bin/bash
# monitor_phase1_integration.sh

echo "🔍 Phase 1 整合狀態監控"
echo "=========================="

# 檢查服務狀態
echo "1. 服務健康狀態："
curl -s http://localhost:8080/api/v1/phase1/health | jq '.service'

# 檢查數據可用性
echo "2. 數據可用性："
curl -s http://localhost:8080/api/v1/phase1/constellations/info | jq '.total_satellites'

# 檢查響應時間
echo "3. API 響應時間："
time curl -s http://localhost:8080/api/v1/phase1/satellite_orbits?constellation=starlink&count=10 > /dev/null

# 檢查日誌錯誤
echo "4. 最近錯誤日誌："
docker logs netstack-api --tail=20 | grep -i error | tail -5

# 檢查內存使用
echo "5. 內存使用情況："
docker stats netstack-api --no-stream --format "table {{.MemUsage}}"

echo "=========================="
echo "監控完成"
```

## 🚀 部署檢查清單

### Pre-deployment 檢查

- [ ] **備份完成**: 原有系統已備份
- [ ] **依賴安裝**: Phase 1 所需依賴已安裝
- [ ] **配置正確**: 環境變量和配置文件已設置
- [ ] **測試通過**: 所有 Phase 1 驗證測試通過
- [ ] **數據遷移**: TLE 數據已遷移到標準位置

### Deployment 步驟

- [ ] **停止舊服務**: 優雅停止當前運行的服務
- [ ] **部署新代碼**: 部署 Phase 1 整合版本
- [ ] **啟動服務**: 啟動整合後的服務
- [ ] **整合測試**: 執行完整的整合測試
- [ ] **性能驗證**: 確認性能指標符合要求

### Post-deployment 驗證

- [ ] **功能測試**: 所有 API 端點正常工作
- [ ] **兼容性測試**: 原有客戶端仍能正常使用
- [ ] **監控設置**: 監控和告警系統正常運行
- [ ] **文檔更新**: API 文檔和使用指南已更新
- [ ] **團隊培訓**: 相關團隊已了解新系統

## 📞 問題排除

### 常見問題及解決方案

#### 問題 1: Phase 1 API 初始化失敗

**症狀**:
```
ERROR: 標準接口初始化失敗: SGP4 庫不可用
```

**解決方案**:
```bash
# 安裝 SGP4 依賴
pip install sgp4

# 驗證安裝
python -c "from sgp4.api import Satrec; print('SGP4 OK')"
```

#### 問題 2: TLE 數據載入失敗

**症狀**:
```
WARNING: 未找到任何 TLE 數據
```

**解決方案**:
```bash
# 檢查 TLE 數據目錄
ls -la /netstack/tle_data/

# 檢查文件權限
chmod -R 644 /netstack/tle_data/

# 重新下載 TLE 數據（如果需要）
./scripts/download_tle_data.sh
```

#### 問題 3: API 響應時間過慢

**症狀**: API 響應時間 > 1 秒

**解決方案**:
```python
# 檢查 SGP4 引擎緩存
curl http://localhost:8080/api/v1/phase1/statistics | jq '.performance_statistics'

# 調整緩存大小
export PHASE1_CACHE_SIZE="2000"
```

#### 問題 4: 兼容性問題

**症狀**: 原有客戶端調用失敗

**解決方案**:
```bash
# 啟用混合模式
export HYBRID_MODE="true"
export USE_LEGACY_API="true"

# 重啟服務
docker restart netstack-api
```

## 📚 相關文檔

- **[API 規範](./api_specification.md)**: 完整的 API 端點規範
- **[架構設計](./architecture.md)**: 系統架構設計文檔
- **[數據流向](./data_flow.md)**: 數據處理流程說明
- **[算法規格](./algorithm_specification.md)**: SGP4 算法實現規格

## 📞 支援與聯絡

**整合支援**: Phase 1 重構專案團隊  
**技術問題**: 參考本目錄下的技術文檔  
**問題報告**: 請在相關 GitHub Issue 中提出

---

**文檔版本**: v1.0.0  
**最後更新**: 2025-08-12  
**維護團隊**: Phase 1 重構專案團隊