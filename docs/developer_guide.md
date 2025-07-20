# NTN-Stack 開發者指南

## 概述

歡迎來到 NTN-Stack 開發者指南！本文檔將幫助您了解系統架構、開發環境設置、編碼規範和貢獻流程。

## 系統架構

### 整體架構

NTN-Stack 採用前後端分離的微服務架構：

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Data Layer    │
│   (React/TS)    │◄──►│   (FastAPI)     │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│  Cache Layer    │◄─────────────┘
                        │  (Redis/Memory) │
                        └─────────────────┘
```

### 核心模組

1. **SIB19 統一平台** (`netstack_api/services/sib19_unified_platform.py`)
   - 統一的系統資訊廣播管理
   - 資訊統一 + 應用分化架構

2. **測量事件服務** (`netstack_api/services/measurement_event_service.py`)
   - A4/D1/D2/T1 事件處理
   - 實時數據收集和分析

3. **軌道計算引擎** (`netstack_api/services/orbit_calculation_engine.py`)
   - SGP4 軌道模型實現
   - 高精度衛星位置計算

4. **前端組件系統** (`simworld/frontend/src/components/`)
   - 統一基礎組件 + 事件專屬組件
   - 多層次視圖模式支援

## 開發環境設置

### 前置需求

- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Redis 6+
- Git

### 後端設置

```bash
# 克隆專案
git clone https://github.com/ntn-stack/ntn-stack.git
cd ntn-stack

# 創建虛擬環境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安裝依賴
pip install -r requirements.txt

# 設置環境變數
cp .env.example .env
# 編輯 .env 文件設置數據庫連接等

# 運行數據庫遷移
alembic upgrade head

# 啟動開發服務器
uvicorn netstack_api.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端設置

```bash
cd simworld/frontend

# 安裝依賴
npm install

# 啟動開發服務器
npm run dev

# 或使用 yarn
yarn install
yarn dev
```

### 數據庫設置

```sql
-- 創建數據庫
CREATE DATABASE ntn_stack;
CREATE USER ntn_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ntn_stack TO ntn_user;
```

## 編碼規範

### Python 後端

遵循 PEP 8 規範：

```python
# 好的示例
class MeasurementEventService:
    """測量事件服務類"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def process_event(self, event_data: EventData) -> ProcessResult:
        """處理測量事件"""
        try:
            result = await self._validate_and_process(event_data)
            self.logger.info(f"事件處理成功: {event_data.event_id}")
            return result
        except Exception as e:
            self.logger.error(f"事件處理失敗: {e}")
            raise
```

### TypeScript 前端

使用 ESLint 和 Prettier：

```typescript
// 好的示例
interface MeasurementConfig {
  eventType: 'A4' | 'D1' | 'D2' | 'T1'
  measurementInterval: number
  reportingInterval: number
  thresholds: {
    primary: number
    secondary?: number
  }
}

const useMeasurementEvent = (config: MeasurementConfig) => {
  const [isRunning, setIsRunning] = useState(false)
  const [data, setData] = useState<MeasurementData[]>([])
  
  const startMeasurement = useCallback(async () => {
    try {
      await api.startMeasurement(config)
      setIsRunning(true)
    } catch (error) {
      console.error('啟動測量失敗:', error)
    }
  }, [config])
  
  return { isRunning, data, startMeasurement }
}
```

### 命名規範

- **文件名**: 使用 kebab-case (`measurement-event-service.py`)
- **類名**: 使用 PascalCase (`MeasurementEventService`)
- **函數名**: 使用 snake_case (Python) 或 camelCase (TypeScript)
- **常數**: 使用 UPPER_SNAKE_CASE (`MAX_RETRY_COUNT`)

## 測試指南

### 後端測試

使用 pytest：

```python
# tests/test_measurement_events.py
import pytest
from netstack_api.services.measurement_event_service import MeasurementEventService

@pytest.fixture
def measurement_service():
    return MeasurementEventService(config={})

async def test_a4_event_processing(measurement_service):
    """測試 A4 事件處理"""
    event_data = {
        'event_type': 'A4',
        'measurement_value': 45.2,
        'timestamp': '2025-07-20T10:30:00Z'
    }
    
    result = await measurement_service.process_a4_event(event_data)
    
    assert result.success is True
    assert result.triggered is False  # 低於門檻值
```

運行測試：

```bash
# 運行所有測試
pytest

# 運行特定測試文件
pytest tests/test_measurement_events.py

# 運行覆蓋率測試
pytest --cov=netstack_api tests/
```

### 前端測試

使用 Jest 和 React Testing Library：

```typescript
// __tests__/MeasurementChart.test.tsx
import { render, screen } from '@testing-library/react'
import { MeasurementChart } from '../components/MeasurementChart'

describe('MeasurementChart', () => {
  it('應該顯示測量數據', () => {
    const mockData = [
      { timestamp: '2025-07-20T10:30:00Z', value: 45.2 }
    ]
    
    render(<MeasurementChart data={mockData} />)
    
    expect(screen.getByText('測量圖表')).toBeInTheDocument()
  })
})
```

## API 開發

### 新增 API 端點

1. 在 `netstack_api/routers/` 中創建或修改路由器
2. 在 `netstack_api/services/` 中實現業務邏輯
3. 在 `netstack_api/models/` 中定義數據模型
4. 添加相應的測試

示例：

```python
# netstack_api/routers/new_feature_router.py
from fastapi import APIRouter, Depends
from netstack_api.services.new_feature_service import NewFeatureService

router = APIRouter(prefix="/api/new-feature", tags=["new-feature"])

@router.post("/process")
async def process_new_feature(
    data: NewFeatureRequest,
    service: NewFeatureService = Depends()
):
    """處理新功能請求"""
    result = await service.process(data)
    return {"status": "success", "result": result}
```

### API 文檔

使用 FastAPI 自動生成的文檔：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 前端組件開發

### 組件結構

```
src/components/
├── common/           # 通用組件
├── domains/          # 領域特定組件
│   └── measurement/
│       ├── charts/   # 圖表組件
│       ├── viewers/  # 查看器組件
│       └── shared/   # 共享組件
└── ui/              # 基礎 UI 組件
```

### 新增測量事件組件

1. 在 `shared/components/` 中創建事件專屬組件
2. 在 `viewers/` 中創建增強查看器
3. 在 `charts/` 中創建傳統圖表組件
4. 更新 `SIB19UnifiedDataManager` 添加數據萃取方法

## 部署指南

### Docker 部署

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "netstack_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/ntn_stack
    depends_on:
      - db
      - redis
  
  frontend:
    build: ./simworld/frontend
    ports:
      - "3000:3000"
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: ntn_stack
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
  
  redis:
    image: redis:6-alpine
```

### 生產部署

1. 使用 Nginx 作為反向代理
2. 配置 SSL 證書
3. 設置監控和日誌
4. 配置自動備份

## 貢獻流程

### Git 工作流

1. Fork 專案到您的 GitHub 帳戶
2. 創建功能分支：`git checkout -b feature/new-feature`
3. 提交變更：`git commit -m "feat: 添加新功能"`
4. 推送分支：`git push origin feature/new-feature`
5. 創建 Pull Request

### 提交訊息規範

使用 Conventional Commits：

```
feat: 添加 A5 測量事件支援
fix: 修復軌道計算精度問題
docs: 更新 API 文檔
test: 添加單元測試
refactor: 重構 SIB19 數據管理器
```

### Code Review 檢查清單

- [ ] 代碼符合編碼規範
- [ ] 添加了適當的測試
- [ ] 更新了相關文檔
- [ ] 通過了所有 CI 檢查
- [ ] 沒有引入安全漏洞

## 常見問題

### Q: 如何添加新的測量事件類型？

A: 
1. 在 `measurement_event_service.py` 中添加處理邏輯
2. 創建對應的前端組件
3. 更新 SIB19 數據管理器
4. 添加測試和文檔

### Q: 如何優化軌道計算性能？

A: 
1. 使用軌道緩存服務
2. 實施批量計算
3. 考慮使用 C++ 擴展
4. 優化 TLE 數據管理

### Q: 如何調試前端組件？

A: 
1. 使用 React DevTools
2. 檢查瀏覽器控制台
3. 使用 Redux DevTools (如果使用)
4. 添加 console.log 調試

## 資源連結

- [專案 GitHub](https://github.com/ntn-stack/ntn-stack)
- [API 文檔](./api_documentation.md)
- [用戶手冊](./user_manual.md)
- [故障排除](./troubleshooting.md)
- [3GPP TS 38.331 標準](https://www.3gpp.org/DynaReport/38331.htm)

## 聯繫方式

- 技術討論: dev@ntn-stack.com
- Bug 報告: GitHub Issues
- 功能請求: GitHub Discussions
