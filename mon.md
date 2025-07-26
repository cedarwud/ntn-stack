# Monitoring 系統安全移除計畫

## 🔍 現狀分析

### 已確認狀態
經過完整檢查，確認 Monitoring 系統目前處於完全未使用狀態：

#### ✅ 未運行的服務
- **Prometheus**: 未運行 (端口 9090)
- **Grafana**: 未運行 (端口 3000)  
- **AlertManager**: 未運行 (端口 9093)
- **Node Exporter**: 未運行 (端口 9100)

#### ✅ 主 Makefile 中的註釋狀態
- `# MONITORING_DIR := monitoring  # 暫時不使用 monitoring`
- `# MONITORING_COMPOSE := $(MONITORING_DIR)/docker-compose.simple.yml  # 暫時不使用`
- 所有 `monitoring-*` 指令均已註釋掉
- help 指令中標註為「暫時禁用」

#### ✅ Docker 容器狀態檢查
執行 `docker ps` 確認無任何 monitoring 相關容器運行

## 📂 待移除的文件和目錄

### 🗂️ 獨立 monitoring 目錄
```
/monitoring/
├── docker-compose.monitoring.yml    # 完整監控堆疊
├── docker-compose.simple.yml        # 簡化監控堆疊
├── Dockerfile.operations            # 運營面板
├── operations_dashboard.py          # Python 運營面板
├── alertmanager/                    # AlertManager 配置
│   ├── alertmanager.yml
│   └── alertmanager-minimal.yml
├── grafana/                         # Grafana 配置
│   ├── dashboards/                  # 儀表板 JSON
│   └── provisioning/                # 自動配置
├── prometheus/                      # Prometheus 配置
│   ├── prometheus.yml
│   ├── prometheus-minimal.yml
│   └── alerts/                      # 告警規則
├── security/                       # 安全配置
├── docs/                           # 文檔
└── tests/                         # 測試文件
```

### 🗂️ NetStack 內部 monitoring 目錄
```
/netstack/monitoring/
├── README.md
├── configs/
├── deploy_observability.py
├── docs/
├── metrics/
├── operations/
├── standards/
├── templates/
├── tools/
└── web/
```

### 🗂️ 前端 monitoring 組件
```
/simworld/frontend/src/components/
├── rl-monitoring/                   # RL 監控組件
├── unified-monitoring/              # 統一監控中心
├── monitoring/                      # 系統監控組件
└── layout/                         
    ├── MonitoringDashboardModal.*   # 監控儀表板彈窗
    └── RLMonitoringModal*           # RL 監控彈窗
```

### 🗂️ 配置文件中的 monitoring 引用
- `/simworld/frontend/src/config/api-config.ts` - monitoring URL 配置
- `/simworld/backend/app/core/config.py` - PROMETHEUS_URL, ALERTMANAGER_URL
- `/netstack/config/prometheus.yml` - Prometheus 配置
- 多個 YAML 配置文件中的 monitoring 配置段落

## 🚨 風險評估

### ⚠️ 高風險區域
1. **前端 RL 監控組件**
   - 風險：可能與實際 RL 功能有依賴關係
   - 建議：先檢查是否為純顯示組件還是有業務邏輯

2. **NetStack 內部監控模組**
   - 風險：可能與核心網功能集成
   - 建議：檢查是否有 API 端點依賴

3. **配置文件中的 monitoring URL**
   - 風險：可能有硬編碼引用
   - 建議：確認無活動連接再移除

### ✅ 低風險區域
1. **獨立 monitoring 目錄**
   - 完全獨立的 Docker 服務
   - 無其他模組依賴
   - 可以安全刪除

2. **Makefile 中的註釋代碼**
   - 已經註釋，無功能影響
   - 可以安全清理

## 📋 安全移除步驟

### Phase 1: 準備階段 (5-10分鐘)
#### 1.1 系統狀態確認
```bash
# 確認系統正常運行
make status

# 確認無 monitoring 容器
docker ps | grep -E "(prometheus|grafana|alertmanager)"

# 備份當前配置
tar -czf monitoring-backup-$(date +%Y%m%d_%H%M%S).tar.gz monitoring/ netstack/monitoring/
```

#### 1.2 功能測試基準
```bash
# 執行基礎功能測試
cd tests && make test-smoke

# 檢查關鍵 API 端點
curl -s http://localhost:8080/health
curl -s http://localhost:8888/
```

### Phase 2: 清理 Makefile (5分鐘)
#### 2.1 清理根目錄 Makefile
```bash
# 移除被註釋的 monitoring 相關變數和指令
# 要清理的行：22, 40, 45-47, 62, 77-81, 127-131, 152-156, 177-181, 
# 188-193, 218-223, 244-248, 268-272, 297-301, 337-341, 397-400, 405-409, 
# 477-485
```

#### 2.2 清理相關註釋和說明
移除所有包含 "monitoring" 的註釋行和說明文字

### Phase 3: 移除獨立 monitoring 目錄 (2分鐘)
#### 3.1 完全移除
```bash
# 安全移除整個 monitoring 目錄
rm -rf /home/u24/ntn-stack/monitoring/
```

#### 3.2 驗證移除
```bash
# 確認目錄已移除
ls -la /home/u24/ntn-stack/ | grep monitoring
```

### Phase 4: 清理 NetStack monitoring (10-15分鐘)
#### 4.1 檢查依賴關係
```bash
# 搜索對 netstack/monitoring 的引用
grep -r "netstack/monitoring" /home/u24/ntn-stack/ --exclude-dir=monitoring
grep -r "monitoring" /home/u24/ntn-stack/netstack/netstack_api/ | grep -v ".pyc"
```

#### 4.2 安全移除
```bash
# 移除 netstack/monitoring 目錄
rm -rf /home/u24/ntn-stack/netstack/monitoring/
```

### Phase 5: 前端 monitoring 組件清理 (20-30分鐘)
#### 5.1 識別業務依賴
```bash
# 檢查 RL 監控組件的實際用途
grep -r "useRLMonitoring" /home/u24/ntn-stack/simworld/frontend/src/
grep -r "RLMonitoringPanel" /home/u24/ntn-stack/simworld/frontend/src/
```

#### 5.2 分階段移除
- **階段 5.2a**: 移除純顯示組件
- **階段 5.2b**: 檢查業務邏輯依賴
- **階段 5.2c**: 修改路由和導入語句

### Phase 6: 配置文件清理 (10-15分鐘)
#### 6.1 清理 API 配置
```bash
# 移除 monitoring URL 配置
# 文件: /simworld/frontend/src/config/api-config.ts
# 移除 monitoring 配置段落 (第 76-81 行)
```

#### 6.2 清理後端配置
```bash
# 文件: /simworld/backend/app/core/config.py
# 移除 PROMETHEUS_URL, ALERTMANAGER_URL, MONITORING_ENABLED (第 216-218 行)
```

#### 6.3 清理其他配置文件
- 移除 YAML 文件中的 monitoring 配置段落
- 清理 CORS 設定中的 monitoring 端口引用

### Phase 7: 最終驗證 (5-10分鐘)
#### 7.1 功能完整性測試
```bash
# 完整重啟驗證
make down && make up

# 等待服務啟動
sleep 30

# 執行完整測試
cd tests && make test-smoke

# 檢查服務狀態
make status
```

#### 7.2 搜索殘留引用
```bash
# 搜索可能的殘留引用
grep -r "monitoring" /home/u24/ntn-stack/ --exclude-dir=.git --exclude="*.md" | grep -v "mon.md"
grep -r ":9090" /home/u24/ntn-stack/ --exclude-dir=.git --exclude="*.md"
grep -r ":3000" /home/u24/ntn-stack/ --exclude-dir=.git --exclude="*.md"
grep -r ":9093" /home/u24/ntn-stack/ --exclude-dir=.git --exclude="*.md"
```

## ✅ 完成檢查清單

### 🔍 Phase 1 檢查清單
- [ ] 系統狀態正常 (`make status` 全綠)
- [ ] 無 monitoring 容器運行
- [ ] 配置備份已創建
- [ ] 基礎功能測試通過

### 🧹 Phase 2 檢查清單
- [ ] 根目錄 Makefile 清理完成
- [ ] 所有 monitoring 註釋已移除
- [ ] help 指令無 monitoring 引用

### 🗂️ Phase 3 檢查清單
- [ ] `/monitoring/` 目錄已完全移除
- [ ] 無殘留監控配置文件

### 🔧 Phase 4 檢查清單
- [ ] `/netstack/monitoring/` 目錄已移除
- [ ] NetStack API 無 monitoring 依賴

### 🎨 Phase 5 檢查清單
- [ ] 前端監控組件已評估
- [ ] 純顯示組件已移除
- [ ] 業務邏輯組件已妥善處理
- [ ] 路由和導入已更新

### ⚙️ Phase 6 檢查清單
- [ ] API 配置文件已清理
- [ ] 後端配置變數已移除
- [ ] YAML 配置已清理
- [ ] CORS 設定已更新

### ✅ Phase 7 檢查清單
- [ ] 系統重啟測試通過
- [ ] 完整功能測試通過
- [ ] 無殘留 monitoring 引用
- [ ] 監控端口檢查通過

## 🚨 回滾計畫

如果移除過程中發現問題，可以按以下步驟回滾：

### 緊急回滾步驟
```bash
# 1. 恢復備份
cd /home/u24/ntn-stack/
tar -xzf monitoring-backup-*.tar.gz

# 2. 恢復 Makefile
git checkout Makefile  # 如果在 git 管理下

# 3. 重新啟動系統
make down && make up

# 4. 驗證功能
make status
cd tests && make test-smoke
```

## 📊 預期效果

移除完成後：
- **磁盤空間釋放**: 約 50-100MB
- **代碼複雜度降低**: 移除約 2000+ 行代碼和配置
- **維護負擔減輕**: 無需維護未使用的監控系統
- **啟動時間可能微幅提升**: 減少不必要的配置加載

## 📝 完成報告模板

移除完成後請填寫：

- **執行日期**: _____________
- **執行人員**: _____________
- **總耗時**: _____________
- **遇到問題**: _____________
- **最終狀態**: [ ] 成功 [ ] 部分成功 [ ] 需要回滾
- **備註**: _____________
