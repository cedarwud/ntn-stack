# NTN Stack RL 系統完全重建計畫

## 🎯 執行概要

**目標**：完全清除現有RL系統，建立符合CLAUDE.md原則的乾淨架構  
**策略**：按功能鏈路清理 + 全面檢查加強  
**預期時間**：2-3天完全清理 + 1-2週重建  

## 📊 現況分析

### 🔍 發現的問題規模
- **後端**：124+ Python檔案，約40,000行程式碼
- **前端**：66+ TypeScript/React檔案，RL相關組件
- **技術債務**：466行模擬程式碼，12.3%違反CLAUDE.md原則
- **架構複雜**：20+個後端子模組，分散且耦合

### 📁 影響範圍統計
```
後端影響：
├── netstack/netstack_api/services/rl_training/ (74個檔案)
├── netstack/netstack_api/services/ai_decision_integration/ (50個檔案)
├── netstack/netstack_api/services/ai_decision_engine.py
├── netstack/netstack_api/rl/ (配置檔案)
└── netstack/tests/*/rl_training/ (測試檔案)

前端影響：
├── simworld/frontend/src/components/rl-monitoring/ (50個檔案)
├── simworld/frontend/src/services/enhanced-rl-monitoring.ts
├── simworld/frontend/src/types/rl_types.ts
├── simworld/frontend/src/components/layout/RLMonitoring*.tsx
└── simworld/frontend/src/components/dashboard/GymnasiumRLMonitor.tsx
```

## 🚀 整合清理流程

### **階段1：功能鏈路清理** (按順序執行)

#### 🔗 鏈路1：RL即時監控功能清理
```bash
# 1.1 備份RL監控鏈路
mkdir -p backup/rl_monitoring_chain_$(date +%Y%m%d_%H%M)
cp -r simworld/frontend/src/components/rl-monitoring backup/rl_monitoring_chain_$(date +%Y%m%d_%H%M)/frontend_rl_monitoring
cp simworld/frontend/src/services/enhanced-rl-monitoring.ts backup/rl_monitoring_chain_$(date +%Y%m%d_%H%M)/
cp -r netstack/netstack_api/services/rl_training/api backup/rl_monitoring_chain_$(date +%Y%m%d_%H%M)/backend_rl_api

# 1.2 清除前端RL監控組件
rm -rf simworld/frontend/src/components/rl-monitoring
rm simworld/frontend/src/services/enhanced-rl-monitoring.ts
rm simworld/frontend/src/types/rl_types.ts
rm simworld/frontend/src/components/layout/RLMonitoringModal*.tsx
rm simworld/frontend/src/components/dashboard/GymnasiumRLMonitor.*

# 1.3 移除WebSocket API路由
# 編輯 netstack/netstack_api/services/rl_training/api/phase_3_api.py
# 移除 /api/v1/rl/phase-2-3/ws/monitoring 路由

# 1.4 清除RL監控後端服務
rm -rf netstack/netstack_api/services/rl_training/api/

# 1.5 驗證鏈路1清理完成
curl -s http://localhost:8080/api/v1/rl/phase-2-3/ws/monitoring
# 預期：404 Not Found
```

#### 🔗 鏈路2：AI決策功能清理
```bash
# 2.1 備份AI決策鏈路
mkdir -p backup/ai_decision_chain_$(date +%Y%m%d_%H%M)
cp -r netstack/netstack_api/services/ai_decision_integration backup/ai_decision_chain_$(date +%Y%m%d_%H%M)/
cp netstack/netstack_api/services/ai_decision_engine.py backup/ai_decision_chain_$(date +%Y%m%d_%H%M)/

# 2.2 清除AI決策前端組件
# 搜尋並移除所有包含 ai_decision 的前端檔案
find simworld/frontend/src -name "*.tsx" -o -name "*.ts" -exec grep -l "ai_decision" {} \; | xargs rm -f

# 2.3 移除AI決策API路由
# 編輯 netstack/netstack_api/app/core/router_manager.py
# 移除AI決策相關路由

# 2.4 清除AI決策後端服務
rm -rf netstack/netstack_api/services/ai_decision_integration
rm netstack/netstack_api/services/ai_decision_engine.py

# 2.5 驗證鏈路2清理完成
curl -s http://localhost:8080/api/v1/ai_decision/status
# 預期：404 Not Found
```

#### 🔗 鏈路3：RL訓練功能清理
```bash
# 3.1 備份RL訓練鏈路
mkdir -p backup/rl_training_chain_$(date +%Y%m%d_%H%M)
cp -r netstack/netstack_api/services/rl_training backup/rl_training_chain_$(date +%Y%m%d_%H%M)/
cp -r netstack/netstack_api/rl backup/rl_training_chain_$(date +%Y%m%d_%H%M)/

# 3.2 清除RL訓練前端組件
# 搜尋並移除所有剩餘的RL相關前端檔案
find simworld/frontend/src -name "*.tsx" -o -name "*.ts" -exec grep -l "rl_training\|RL.*training" {} \; | xargs rm -f

# 3.3 移除router_manager.py中RL路由註冊
# 編輯 netstack/netstack_api/app/core/router_manager.py
# 完全移除RL路由相關程式碼

# 3.4 清除RL訓練完整目錄
rm -rf netstack/netstack_api/services/rl_training
rm -rf netstack/netstack_api/rl

# 3.5 驗證鏈路3清理完成
curl -s http://localhost:8080/api/v1/rl/training/status
# 預期：404 Not Found
```

### **階段2：全面檢查加強** (確保清理徹底)

#### 🔍 檢查1：檔案系統殘留
```bash
# 搜尋所有可能的RL相關檔案
find /home/sat/ntn-stack -name "*rl*" -o -name "*RL*" -o -name "*reinforcement*" -o -name "*ai_decision*" 2>/dev/null | grep -v backup | grep -v __pycache__ | grep -v node_modules

# 搜尋程式碼中的RL引用
grep -r "rl_training\|ai_decision\|reinforcement" /home/sat/ntn-stack/netstack --include="*.py" | grep -v backup
grep -r "rl.*monitoring\|RL.*Monitor" /home/sat/ntn-stack/simworld/frontend/src --include="*.ts" --include="*.tsx" | grep -v backup
```

#### 🔍 檢查2：導入引用清理
```bash
# 檢查Python導入
python3 -c "
import sys
sys.path.append('/home/sat/ntn-stack/netstack')
try:
    from netstack_api.services.rl_training import *
    print('❌ RL導入仍存在')
except ImportError:
    print('✅ RL導入已清理')
"

# 檢查Docker日誌錯誤
docker logs netstack-api --tail 20 | grep -i "error\|exception"
```

#### 🔍 檢查3：資料庫殘留
```bash
# 檢查PostgreSQL中的RL相關表
docker exec netstack-rl-postgres psql -U rl_user -d rl_research -c "
SELECT table_name FROM information_schema.tables 
WHERE table_name LIKE '%rl%' OR table_name LIKE '%ai_decision%';
"

# 清理RL相關資料表 (如需要)
# docker exec netstack-rl-postgres psql -U rl_user -d rl_research -c "DROP TABLE IF EXISTS rl_training_sessions CASCADE;"
```

#### 🔍 檢查4：API路由清理
```bash
# 測試所有可能的RL API端點
endpoints=(
    "/api/v1/rl/training"
    "/api/v1/rl/monitoring" 
    "/api/v1/rl/phase-2-3"
    "/api/v1/ai_decision"
    "/api/v1/ai_decision/engine"
)

for endpoint in "${endpoints[@]}"; do
    response=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost:8080$endpoint")
    if [ "$response" \!= "404" ]; then
        echo "❌ 端點仍存在: $endpoint (HTTP $response)"
    else
        echo "✅ 端點已清理: $endpoint"
    fi
done
```

### **階段3：系統穩定性驗證**

#### ✅ 驗證步驟
```bash
# 1. 容器健康檢查
make status
# 預期：所有容器 healthy，無RL相關容器

# 2. API健康檢查  
curl -s http://localhost:8080/health | jq
# 預期：overall_status: "healthy"

# 3. 前端載入測試
curl -s http://localhost:5173
# 預期：頁面正常載入，無RL組件錯誤

# 4. 系統日誌檢查
docker logs netstack-api --tail 50 | grep -i "error\|exception\|rl\|ai_decision"
# 預期：無RL相關錯誤

# 5. 前端控制台檢查
# 開啟瀏覽器 http://localhost:5173，檢查控制台
# 預期：無RL相關API調用錯誤
```

## 🏗️ 重建階段規劃

### **Phase A：架構設計** (1-2天)
```
目標：設計符合CLAUDE.md原則的乾淨RL架構

netstack/netstack_api/services/rl_unified/
├── core/
│   ├── algorithm.py          # 單一真實DQN實現
│   ├── environment.py        # LEO衛星環境  
│   └── trainer.py            # 訓練管理器
├── data/
│   ├── repository.py         # PostgreSQL數據層
│   └── models.py             # Pydantic模型
├── api/
│   └── routes.py             # FastAPI路由
└── config/
    └── settings.py           # 配置管理
```

### **Phase B：核心實現** (1-2週)
- 基於 Stable-Baselines3 的真實DQN算法
- 真實PostgreSQL數據存儲
- 與LEO衛星環境的真實整合
- 簡潔的FastAPI接口

### **Phase C：整合測試** (3-5天)
- 單元測試覆蓋
- 整合測試驗證
- 性能基準測試
- 文檔完善

## 📋 執行檢查清單

### ✅ 完全清理確認
- [ ] 鏈路1：RL監控功能完全移除
- [ ] 鏈路2：AI決策功能完全移除  
- [ ] 鏈路3：RL訓練功能完全移除
- [ ] 檔案系統無RL相關殘留
- [ ] 程式碼無RL導入引用
- [ ] 資料庫無RL相關表格
- [ ] API路由無RL端點回應
- [ ] 系統運行完全穩定
- [ ] 前端載入無RL錯誤
- [ ] 日誌無RL相關異常

### 🎯 重建準備確認
- [ ] 技術棧選擇：FastAPI + SQLAlchemy + Stable-Baselines3
- [ ] 架構設計：符合CLAUDE.md原則
- [ ] 開發環境：PostgreSQL + Docker
- [ ] 測試框架：pytest + 整合測試
- [ ] 文檔標準：完整API文檔

## 💡 關鍵成功因素

1. **按鏈路清理** - 保持功能完整性，降低風險
2. **全面檢查** - 確保無殘留，避免後續問題  
3. **系統驗證** - 每步都要確認系統穩定
4. **備份策略** - 完整備份，可回滾操作
5. **漸進執行** - 逐步清理，立即測試

---

**執行原則**：寧可多花時間徹底清理，也不要留下技術債務！

**預期成果**：建立一個符合學術研究標準的真實LEO衛星RL平台 🚀

---

*最後更新：2025-08-02*  
*文檔版本：v2.0*  
*負責人：NTN Stack 開發團隊*

