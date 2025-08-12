#!/bin/bash
# Phase 1 回滾腳本

set -e

echo "🔄 Phase 1 回滾開始..."

# 停止當前服務
echo "停止當前服務..."
docker-compose -f docker-compose.phase1.yml down

# 備份當前數據
echo "備份當前數據..."
backup_dir="../../backup/rollback_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"
cp -r ../../data "$backup_dir/"
cp -r ../../logs "$backup_dir/"

# 恢復到原有配置
echo "恢復到原有配置..."
if [ -d "../../backup/pre-phase1-integration/" ]; then
    cp -r ../../backup/pre-phase1-integration/* ../../
    echo "✅ 原有配置已恢復"
else
    echo "❌ 未找到原有配置備份"
    exit 1
fi

# 重啟原有服務
echo "重啟原有服務..."
cd ../..
make up

echo "✅ Phase 1 回滾完成"
