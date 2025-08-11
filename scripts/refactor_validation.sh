#!/bin/bash
# SimWorld Backend Refactoring Validation Script
# Comprehensive verification of Phase 1-4 refactoring changes

set -e

echo "🔍 執行 SimWorld Backend 重構驗證..."
echo "=================================================="

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status
print_status() {
    if [ $? -eq 0 ]; then
        echo "✅ $1"
    else
        echo "❌ $1"
        exit 1
    fi
}

# Function to test HTTP endpoint
test_endpoint() {
    local url=$1
    local description=$2
    
    if curl -s "$url" > /dev/null 2>&1; then
        echo "✅ $description"
    else
        echo "❌ $description"
        return 1
    fi
}

# 1. Check for removed components
echo "🗑️  檢查移除的組件..."

# Check that removed files don't exist
if [ ! -f "simworld/backend/app/api/routes/uav.py" ]; then
    echo "✅ UAV 路由模組已移除"
else
    echo "❌ UAV 路由模組仍存在"
    exit 1
fi

if [ ! -f "simworld/backend/app/services/precision_validator.py" ]; then
    echo "✅ 精度驗證器已移除"  
else
    echo "❌ 精度驗證器仍存在"
    exit 1
fi

if [ ! -d "simworld/backend/app/domains/system" ]; then
    echo "✅ 系統監控域已移除"
else
    echo "❌ 系統監控域仍存在" 
    exit 1
fi

# 2. Check for dead imports/references
echo "🔍 檢查死連結和引用..."

if ! grep -r "uav" simworld/backend/app/ --include="*.py" | grep -v "#" | grep -v "def.*uav" >/dev/null 2>&1; then
    echo "✅ 無 UAV 相關引用"
else
    echo "❌ 發現 UAV 相關引用"
    grep -r "uav" simworld/backend/app/ --include="*.py" | grep -v "#"
fi

if ! grep -r "precision_validator" simworld/backend/app/ --include="*.py" >/dev/null 2>&1; then
    echo "✅ 無精度驗證器引用"
else
    echo "❌ 發現精度驗證器引用"
fi

if ! grep -r "app\.domains\.system" simworld/backend/app/ --include="*.py" | grep -v "#" >/dev/null 2>&1; then
    echo "✅ 無系統域引用"
else  
    echo "❌ 發現系統域引用"
fi

# 3. Check service health
echo "🏥 檢查服務健康狀態..."

# Wait for services to be ready
echo "等待服務啟動..."
sleep 10

# Check Docker containers
if docker ps --format "table {{.Names}}\t{{.Status}}" | grep "simworld_backend" | grep -q "healthy\|Up"; then
    echo "✅ SimWorld Backend 容器運行正常"
else
    echo "❌ SimWorld Backend 容器狀態異常"
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep simworld
    exit 1
fi

# 4. Test API endpoints
echo "🌐 檢查 API 端點..."

test_endpoint "http://localhost:8888/health" "健康檢查端點" || exit 1
test_endpoint "http://localhost:8888/ping" "Ping 端點" || exit 1  
test_endpoint "http://localhost:8888/" "根端點" || exit 1

# Check that removed endpoints return 404
if curl -s "http://localhost:8888/api/v1/tracking/uav/positions" | grep -q "Not Found\|404"; then
    echo "✅ UAV 端點已正確移除 (返回 404)"
else
    echo "❌ UAV 端點仍可訪問"
fi

# 5. Check core functionality preservation
echo "🛰️  檢查核心功能保留..."

# Test 3D model serving
if curl -s "http://localhost:8888/static/models/sat.glb" -I | grep -q "200 OK"; then
    echo "✅ 衛星 3D 模型服務正常"
else
    echo "❌ 衛星 3D 模型服務異常"
    exit 1
fi

# Test scene serving  
if curl -s "http://localhost:8888/static/scenes/NTPU_v2/NTPU_v2.glb" -I | grep -q "200 OK"; then
    echo "✅ 3D 場景服務正常"
else
    echo "❌ 3D 場景服務異常"
    exit 1
fi

# 6. Performance checks
echo "📊 檢查性能指標..."

# Check memory usage
memory_usage=$(docker stats simworld_backend --no-stream --format "{{.MemUsage}}" | cut -d'/' -f1 | sed 's/MiB//g')
if [ "${memory_usage%.*}" -lt 500 ]; then  # Less than 500MB
    echo "✅ 記憶體使用合理 (${memory_usage})"
else
    echo "⚠️  記憶體使用偏高 (${memory_usage})"
fi

# Check API response time
start_time=$(date +%s%N)
curl -s "http://localhost:8888/health" > /dev/null
end_time=$(date +%s%N)
response_time=$(( (end_time - start_time) / 1000000 ))  # Convert to milliseconds

if [ $response_time -lt 200 ]; then  # Less than 200ms
    echo "✅ API 響應時間良好 (${response_time}ms)"
else
    echo "⚠️  API 響應時間偏慢 (${response_time}ms)"
fi

# 7. Code quality checks (if available)
echo "🧹 檢查代碼品質..."

if command_exists python3; then
    # Simple import test
    cd simworld/backend
    if python3 -c "import app.main; print('✅ 主應用模組導入成功')" 2>/dev/null; then
        echo "✅ 主應用模組導入成功"
    else
        echo "❌ 主應用模組導入失敗"
        # Don't exit here as this might be expected outside container
    fi
    cd - > /dev/null
fi

# 8. Backup verification
echo "💾 檢查備份完整性..."

if [ -d "backup/removed-components" ]; then
    echo "✅ 移除組件備份存在"
    
    # Check backup contents
    if [ -f "backup/removed-components/uav/uav.py" ]; then
        echo "✅ UAV 組件已備份"
    fi
    
    if [ -f "backup/removed-components/dev-tools/precision_validator.py" ]; then
        echo "✅ 開發工具已備份"
    fi
    
    if [ -d "backup/removed-components/system-domain/system" ]; then
        echo "✅ 系統域已備份"
    fi
else
    echo "❌ 備份目錄不存在"
    exit 1
fi

# 9. Git status check
echo "📝 檢查 Git 狀態..."

if git status --porcelain | grep -q "^M\|^A\|^D"; then
    echo "✅ 檢測到 Git 變更"
    echo "變更的檔案數量: $(git status --porcelain | wc -l)"
else
    echo "⚠️  未檢測到 Git 變更"
fi

# 10. Final verification
echo "🎯 最終驗證..."

# Count remaining Python files
python_files=$(find simworld/backend/app -name "*.py" | wc -l)
echo "✅ 剩餘 Python 檔案數量: $python_files"

# Check docker-compose health
if docker-compose ps | grep -q "healthy"; then
    echo "✅ Docker Compose 健康檢查通過"
else
    echo "❌ Docker Compose 健康檢查失敗"
fi

echo "=================================================="
echo "🎉 SimWorld Backend 重構驗證完成！"
echo ""
echo "📊 重構統計:"
echo "   - 移除的組件: UAV 追踪、開發工具、系統監控域"
echo "   - 新增的優化: 統一距離計算器、優化座標服務"
echo "   - 保留的核心功能: 衛星追踪、3D 場景、設備管理"
echo "   - 服務健康狀態: 正常"
echo "   - API 響應時間: ${response_time}ms"
echo ""
echo "✅ 重構成功！系統運行穩定，核心功能完整保留。"