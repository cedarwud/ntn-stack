# Phase 1: 測試驗證指南

**測試範圍**: 立即修復項目的全面驗證
**測試環境**: 本地開發 + Docker 容器
**執行時間**: 每日測試 + 最終整合測試

## 🧪 測試策略概覽

### 測試金字塔
```
        🔺 E2E 測試 (10%)
       🔺🔺 整合測試 (30%) 
      🔺🔺🔺 單元測試 (60%)
```

### 測試階段
1. **單元測試** - 每個修改完成後立即執行
2. **整合測試** - 模組間交互驗證
3. **系統測試** - 完整流程驗證
4. **性能測試** - 確保性能基準達標

## 📋 詳細測試計畫

### 1. 配置系統測試

#### 1.1 單元測試
```bash
# 測試配置驗證
python -m pytest tests/test_satellite_config.py::test_config_validation -v

# 測試配置載入
python -m pytest tests/test_satellite_config.py::test_config_loading -v

# 測試錯誤處理
python -m pytest tests/test_satellite_config.py::test_invalid_config -v
```

#### 1.2 整合測試
```bash
# 驗證所有模組正確使用配置
python scripts/validate_config.py

# 檢查配置一致性
python -c "
from config.satellite_config import SATELLITE_CONFIG
from netstack.netstack_api.services.sib19_unified_platform import SIB19UnifiedPlatform

platform = SIB19UnifiedPlatform()
assert platform.max_tracked_satellites == SATELLITE_CONFIG.MAX_CANDIDATE_SATELLITES
print('✅ 配置一致性驗證通過')
"
```

### 2. 預處理系統測試

#### 2.1 數據一致性測試
```bash
# 測試預處理數據結構
python -m pytest tests/test_data_consistency.py::test_preprocessing_consistency -v

# 測試 SGP4 計算精度
python -m pytest tests/test_data_consistency.py::test_sgp4_calculation_accuracy -v

# 測試簡化模型回退
python tests/test_preprocessing_fallback.py
```

#### 2.2 性能基準測試
```bash
# 測試建置時間
python -m pytest tests/test_data_consistency.py::test_build_time_performance -v

# 測試記憶體使用
python tests/test_memory_usage.py

# 測試 API 響應時間
curl -w "@curl-format.txt" -s -o /dev/null http://localhost:8080/api/v1/satellites/unified/health
```

### 3. SIB19 平台測試

#### 3.1 候選衛星管理測試
```bash
# 測試候選數量限制
python -c "
from netstack.netstack_api.services.sib19_unified_platform import SIB19UnifiedPlatform

platform = SIB19UnifiedPlatform()
# 測試正常情況
assert platform.validate_candidate_count(5) == 5
# 測試超出限制
assert platform.validate_candidate_count(10) == 8
print('✅ 候選衛星數量驗證通過')
"

# 測試候選衛星選擇邏輯
python tests/test_sib19_candidate_selection.py
```

#### 3.2 鄰居細胞配置測試
```bash
# 測試 SIB19 數據解析
python tests/test_sib19_parsing.py

# 測試星曆數據處理
python tests/test_ephemeris_processing.py
```

### 4. 批次預計算測試

#### 4.1 功能測試
```bash
# 測試小範圍批次計算
python -c "
import asyncio
from netstack.scripts.batch_precompute_taiwan import TaiwanBatchPrecomputer

async def test_batch():
    computer = TaiwanBatchPrecomputer()
    # 測試使用統一配置
    assert computer.max_satellites <= 50
    print('✅ 批次預計算配置正確')

asyncio.run(test_batch())
"

# 測試數據格式輸出
python tests/test_batch_output_format.py
```

## 🔄 自動化測試腳本

### 每日檢查腳本
```bash
#!/bin/bash
# daily_check.sh - 每日自動化檢查

echo "🚀 開始每日測試檢查..."

# 1. 配置驗證
echo "📋 檢查配置一致性..."
python scripts/validate_config.py
if [ $? -ne 0 ]; then
    echo "❌ 配置驗證失敗"
    exit 1
fi

# 2. 單元測試
echo "🧪 執行單元測試..."
python -m pytest tests/test_satellite_config.py -v
python -m pytest tests/test_data_consistency.py -v
if [ $? -ne 0 ]; then
    echo "❌ 單元測試失敗"
    exit 1
fi

# 3. 系統健康檢查
echo "🏥 系統健康檢查..."
curl -f http://localhost:8080/health > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ 系統健康檢查失敗"
    exit 1
fi

# 4. 數據檔案檢查
echo "📁 檢查數據檔案..."
if [ ! -f "/app/data/starlink_120min_timeseries.json" ]; then
    echo "⚠️ Starlink 預處理數據不存在"
fi

if [ ! -f "/app/data/oneweb_120min_timeseries.json" ]; then
    echo "⚠️ OneWeb 預處理數據不存在"
fi

echo "✅ 每日檢查完成"
```

### 整合測試腳本
```bash
#!/bin/bash
# integration_test.sh - 完整整合測試

echo "🔄 開始整合測試..."

# 1. 清理環境
echo "🧹 清理測試環境..."
docker-compose down
docker system prune -f

# 2. 重新建置
echo "🏗️ 重新建置系統..."
make build
if [ $? -ne 0 ]; then
    echo "❌ 建置失敗"
    exit 1
fi

# 3. 啟動服務
echo "🚀 啟動服務..."
make up
sleep 30  # 等待服務啟動

# 4. 健康檢查
echo "🏥 服務健康檢查..."
curl -f http://localhost:8080/health
curl -f http://localhost:8888/health
curl -f http://localhost:5173

# 5. 功能測試
echo "⚙️ 功能測試..."
python tests/integration/test_complete_workflow.py

# 6. 性能測試
echo "📊 性能測試..."
python tests/performance/test_api_response_time.py
python tests/performance/test_memory_usage.py

echo "✅ 整合測試完成"
```

## 📊 測試覆蓋率目標

### 目標覆蓋率
| 測試類型 | 目標覆蓋率 | 測量工具 |
|----------|------------|----------|
| 單元測試 | 85% | pytest-cov |
| 整合測試 | 70% | 自定義指標 |
| API 測試 | 100% | 端點檢查 |
| 配置測試 | 100% | 驗證腳本 |

### 覆蓋率測量
```bash
# 生成覆蓋率報告
python -m pytest --cov=config --cov=netstack --cov=simworld \
  --cov-report=html --cov-report=term-missing

# 查看覆蓋率報告
open htmlcov/index.html
```

## 🚨 測試失敗處理

### 常見問題排除

#### 1. 配置載入失敗
```bash
# 檢查配置檔案路徑
python -c "
import sys
from pathlib import Path
config_path = Path('./config/satellite_config.py')
print(f'配置檔案存在: {config_path.exists()}')
print(f'Python 路徑: {sys.path}')
"

# 檢查權限
ls -la config/satellite_config.py
```

#### 2. 模組導入錯誤
```bash
# 檢查 Python 路徑
python -c "
import sys
print('Python 路徑:')
for path in sys.path:
    print(f'  {path}')
"

# 檢查模組存在
find . -name "sib19_unified_platform.py"
find . -name "preprocess_120min_timeseries.py"
```

#### 3. Docker 容器問題
```bash
# 檢查容器狀態
docker-compose ps

# 檢查容器日誌
docker logs netstack-api --tail 50
docker logs simworld-backend --tail 50

# 重新啟動有問題的容器
docker-compose restart netstack-api
```

#### 4. 性能測試失敗
```bash
# 檢查系統資源
free -h
df -h
top -bn1 | head -10

# 調整性能測試參數
export PERFORMANCE_TEST_TIMEOUT=300
export MAX_ACCEPTABLE_MEMORY_MB=512
```

## ✅ 測試檢查清單

### 每個修改完成後
- [ ] 相關單元測試通過
- [ ] 配置驗證腳本通過
- [ ] 基本功能測試通過
- [ ] 沒有明顯性能回歸

### 每日檢查
- [ ] 所有自動化測試通過
- [ ] 系統健康檢查正常
- [ ] 數據檔案完整
- [ ] 測試覆蓋率達標

### Phase 1 完成前
- [ ] 完整整合測試通過
- [ ] 性能基準測試達標
- [ ] 所有配置驗證通過
- [ ] 文檔測試步驟驗證
- [ ] 回歸測試全部通過

## 📈 測試報告範本

### 每日測試報告
```
日期: 2025-08-XX
測試人員: [姓名]
測試環境: [環境描述]

🧪 測試結果:
- 單元測試: ✅ 25/25 通過
- 整合測試: ✅ 8/8 通過  
- 性能測試: ✅ API < 100ms
- 覆蓋率: 87% (目標 85%)

⚠️ 發現問題:
- [問題描述]
- [修復狀態]

📋 建議:
- [改進建議]
```

---

**重要提醒**: 測試失敗時應立即停止部署，修復問題後重新測試。