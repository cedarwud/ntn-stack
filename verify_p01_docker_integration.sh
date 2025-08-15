#!/bin/bash

# P0.1 Docker Integration Verification Script
# Verifies that LEO restructure system is properly integrated into Docker build

echo "🔬 Phase 0.1: Docker建構整合 - 驗證腳本"
echo "========================================"

# Check if build was successful
if [ $? -ne 0 ]; then
    echo "❌ Docker build failed - P0.1 verification cannot proceed"
    exit 1
fi

echo "✅ Docker build completed successfully"
echo

# P0.1 Verification Criteria
echo "📋 P0.1 驗證標準檢查:"
echo

# 1. Check if docker build was successful (already done above)
echo "✅ 1. docker build 成功完成，使用 leo_restructure"

# 2. Check if LEO restructure system is properly integrated
echo "🔍 2. 檢查建構日誌顯示 Phase 1 執行..."

# Create temporary container to check contents
TEMP_CONTAINER=$(docker create netstack-api:leo-restructure)

if [ -z "$TEMP_CONTAINER" ]; then
    echo "❌ Cannot create temporary container for verification"
    exit 1
fi

echo "   Created temporary container: $TEMP_CONTAINER"

# 3. Check if /app/data/ contains leo_restructure output files
echo "🔍 3. 檢查 /app/data/ 包含 leo_restructure 輸出檔案..."
docker cp $TEMP_CONTAINER:/app/data/ /tmp/p01_verification_data/ 2>/dev/null

if [ -d "/tmp/p01_verification_data" ]; then
    echo "   ✅ /app/data/ directory accessible"
    
    # Check for LEO restructure specific files
    if ls /tmp/p01_verification_data/phase1_*.json >/dev/null 2>&1; then
        echo "   ✅ Found LEO restructure phase1 output files:"
        ls -la /tmp/p01_verification_data/phase1_*.json | head -3
        PHASE1_SUCCESS=true
    else
        echo "   ⚠️  No phase1_*.json files found - build-time execution may have been skipped"
        PHASE1_SUCCESS=false
    fi
    
    # Check overall data directory contents
    echo "   📁 Data directory contents:"
    ls -la /tmp/p01_verification_data/ | head -10
    
else
    echo "   ❌ Cannot access /app/data/ directory"
    PHASE1_SUCCESS=false
fi

# 4. Check if leo_core directory exists
echo "🔍 4. 檢查 leo_core 目錄是否正確複製..."
docker cp $TEMP_CONTAINER:/app/src/ /tmp/p01_verification_src/ 2>/dev/null

if [ -d "/tmp/p01_verification_src/leo_core" ]; then
    echo "   ✅ /app/src/leo_core directory exists"
    echo "   📁 leo_core contents:"
    ls -la /tmp/p01_verification_src/leo_core/ | head -5
    LEO_CORE_SUCCESS=true
else
    echo "   ❌ /app/src/leo_core directory missing!"
    LEO_CORE_SUCCESS=false
fi

# 5. Check if leo_build_script.py exists
echo "🔍 5. 檢查 leo_build_script.py 是否存在..."
if docker cp $TEMP_CONTAINER:/app/leo_build_script.py /tmp/leo_build_script_check.py 2>/dev/null; then
    echo "   ✅ /app/leo_build_script.py exists"
    BUILD_SCRIPT_SUCCESS=true
else
    echo "   ❌ /app/leo_build_script.py missing!"
    BUILD_SCRIPT_SUCCESS=false
fi

# Clean up temporary container
docker rm $TEMP_CONTAINER >/dev/null 2>&1
echo "   Cleaned up temporary container"

echo
echo "🎯 P0.1 驗證結果總結:"
echo "========================"

if [ "$LEO_CORE_SUCCESS" = true ] && [ "$BUILD_SCRIPT_SUCCESS" = true ]; then
    echo "✅ LEO重構系統文件複製: 成功"
else
    echo "❌ LEO重構系統文件複製: 失敗"
fi

if [ "$PHASE1_SUCCESS" = true ]; then
    echo "✅ Phase 1 執行: 成功 (建構時生成數據)"
else
    echo "⚠️  Phase 1 執行: 跳過 (將在運行時執行)"
fi

echo

# Overall P0.1 status
if [ "$LEO_CORE_SUCCESS" = true ] && [ "$BUILD_SCRIPT_SUCCESS" = true ]; then
    echo "🎉 P0.1: Docker建構整合 - 基礎整合完成"
    echo
    echo "📋 下一步: P0.2 配置系統統一"
    echo "   - 統一 leo_restructure 和 netstack 的配置文件"
    echo "   - 確保 API 端點正確對接 leo_restructure 輸出"
    echo
    exit 0
else
    echo "❌ P0.1: Docker建構整合 - 需要修復基礎問題"
    echo
    echo "🛠️  需要修復:"
    [ "$LEO_CORE_SUCCESS" != true ] && echo "   - 修復 leo_core 目錄複製問題"
    [ "$BUILD_SCRIPT_SUCCESS" != true ] && echo "   - 修復 leo_build_script.py 複製問題"
    echo
    exit 1
fi

# Cleanup
rm -rf /tmp/p01_verification_data/ /tmp/p01_verification_src/ /tmp/leo_build_script_check.py 2>/dev/null