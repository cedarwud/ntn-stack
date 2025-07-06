# NetStack API 部署和遷移指南

## 🚀 部署方案選擇

### 選項 1: 直接替換 (推薦)
```bash
# 備份原文件
cp main.py main.py.backup.20250705_194003

# 部署新版本
cp main_v3.py main.py

# 重啟服務
make down && make up
```

### 選項 2: 漸進式遷移
```bash
# Week 1: 並行部署
cp main_v3.py main_production.py

# Week 2: 測試和驗證  
python main_production.py  # 測試端口 8081

# Week 3: 完整切換
mv main.py main.py.legacy
mv main_production.py main.py
```

### 選項 3: 藍綠部署
```bash
# 藍環境: 當前 main.py
# 綠環境: 新的 main_v3.py
# 使用負載均衡器切換流量
```

## 🏗️ 架構檔案清單

### 必要文件
- main_v3.py (247行) - 主應用程式
- app/core/config_manager.py (163行) - 統一配置  
- app/core/manager_factory.py (230行) - 管理器工廠
- app/core/adapter_manager.py (336行) - 適配器管理
- app/core/service_manager.py (204行) - 服務管理
- app/core/router_manager.py (282行) - 路由器管理
- app/core/middleware_manager.py (356行) - 中間件管理
- app/core/exception_manager.py (312行) - 異常管理

### 環境變數配置
```bash
# 生產環境
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info

# 資料庫
DATABASE_URL=mongodb://mongo:27017/open5gs
REDIS_URL=redis://redis:6379

# 安全設定
CORS_ORIGINS=https://yourdomain.com
MAX_REQUEST_SIZE=16777216
SECURITY_HEADERS=true
```

## 📋 部署檢查清單

### 部署前檢查
- [ ] 語法驗證 100% 通過
- [ ] 環境變數已配置
- [ ] 資料庫連接測試
- [ ] Redis 連接測試
- [ ] 備份策略已準備

### 部署中監控
- [ ] 啟動時間 < 5秒
- [ ] 記憶體使用正常
- [ ] 所有路由器載入成功
- [ ] 健康檢查端點回應正常

### 部署後驗證
- [ ] /health 端點正常
- [ ] /system/status 顯示完整狀態
- [ ] 所有 API 端點正常工作
- [ ] 日誌無錯誤訊息

## 🔄 回滾計劃

### 快速回滾
```bash
# 1分鐘內回滾
cp main.py.backup.* main.py
make down && make up
```

### 問題診斷
```bash
# 檢查啟動錯誤
make logs  < /dev/null |  grep -i error

# 檢查系統狀態
curl http://localhost:8080/system/health

# 檢查配置
curl http://localhost:8080/system/config
```

## 🛰️ LEO 衛星系統專用部署注意事項

### 毫秒級延遲要求
- 確保啟動時間 < 5秒
- 監控 API 回應時間 < 100ms
- 記憶體使用優化

### 高可用性部署
- 使用多實例部署
- 健康檢查頻率 30秒
- 自動故障轉移

### 監控和告警
- Prometheus 指標收集
- 系統狀態監控
- 自動告警設置

---
**NetStack API v2.0 - 世界級 LEO 衛星核心網管理系統**

