# Phase 1 部署包

**生成時間**: 2025-08-12T08:54:08.359517+00:00
**版本**: 1.0.0

## 📁 部署包內容

### 核心配置
- `Dockerfile.phase1`: Phase 1 增強 Docker 鏡像
- `docker-compose.phase1.yml`: Docker Compose 配置
- `production.yaml`: 生產環境配置

### 部署腳本
- `prepare_deployment.sh`: 部署準備腳本
- `deploy.sh`: 部署執行腳本
- `rollback.sh`: 回滾腳本

### CI/CD 配置
- `.github/workflows/phase1-deploy.yml`: GitHub Actions 工作流

### 監控配置
- `monitoring/`: 監控系統配置目錄
  - `docker-compose.monitoring.yml`: 監控服務
  - `prometheus.yml`: Prometheus 配置

## 🚀 部署步驟

1. **準備階段**:
   ```bash
   cd phase1_refactor/deployment
   ./prepare_deployment.sh
   ```

2. **執行部署**:
   ```bash
   ./deploy.sh
   ```

3. **驗證部署**:
   ```bash
   curl http://localhost:8080/health
   curl http://localhost:8001/health
   ```

4. **啟動監控** (可選):
   ```bash
   docker-compose -f monitoring/docker-compose.monitoring.yml up -d
   ```

## 📊 部署後檢查

### 服務狀態
- NetStack API: http://localhost:8080
- Phase 1 API: http://localhost:8001  
- 健康檢查: http://localhost:8080/health
- Prometheus: http://localhost:9090 (如啟用監控)
- Grafana: http://localhost:3000 (如啟用監控)

### 性能驗證
```bash
# 執行性能測試
cd ../05_integration
python performance_benchmark.py

# 查看服務狀態
docker-compose -f ../deployment/docker-compose.phase1.yml ps
```

## 🔧 故障排除

### 常見問題
1. **TLE 數據缺失**: 執行 `prepare_deployment.sh`
2. **服務啟動失敗**: 檢查 Docker logs
3. **性能不佳**: 調整 `production.yaml` 中的配置

### 回滾步驟
```bash
./rollback.sh
```

## 📞 支援資訊
- 技術文檔: `../docs/`
- 整合指南: `../docs/integration_guide.md`
- API 規範: `../docs/api_specification.md`
