#!/bin/bash
# Phase 1 部署準備腳本

set -e

echo "🚀 Phase 1 部署準備開始..."

# 檢查 Docker 和 Docker Compose
echo "檢查 Docker 環境..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安裝"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安裝"
    exit 1
fi

echo "✅ Docker 環境檢查通過"

# 創建必要目錄
echo "創建必要目錄..."
mkdir -p ../../tle_data/starlink/tle
mkdir -p ../../tle_data/oneweb/tle
mkdir -p ../../data
mkdir -p ../../logs

echo "✅ 目錄創建完成"

# 檢查 TLE 數據
echo "檢查 TLE 數據..."
if [ ! -f "../../tle_data/starlink/tle/starlink_20250805.tle" ]; then
    echo "⚠️  未找到 Starlink TLE 數據，將從歷史數據生成..."
    python ../../phase1_refactor/01_data_source/generate_tle_from_historical.py
fi

if [ ! -f "../../tle_data/oneweb/tle/oneweb_20250805.tle" ]; then
    echo "⚠️  未找到 OneWeb TLE 數據，將從歷史數據生成..."
    python ../../phase1_refactor/01_data_source/generate_tle_from_historical.py --constellation oneweb
fi

echo "✅ TLE 數據檢查完成"

# 驗證 Phase 1 系統
echo "驗證 Phase 1 系統..."
cd ../../phase1_refactor
python validate_phase1_refactor.py

if [ $? -eq 0 ]; then
    echo "✅ Phase 1 系統驗證通過"
else
    echo "❌ Phase 1 系統驗證失敗"
    exit 1
fi

cd deployment

echo "🎯 Phase 1 部署準備完成"
