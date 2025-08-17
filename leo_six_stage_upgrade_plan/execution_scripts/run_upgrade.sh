#!/bin/bash
# LEO 六階段升級計劃 - 主執行腳本

echo "🔄 LEO衛星系統六階段升級開始"
echo "版本: v1.0"
echo "日期: $(date)"
echo ""

# 執行Phase 0: 系統備份
echo "Phase 0: 執行系統備份..."
./00_backup_system.sh
if [ $? -ne 0 ]; then
  echo "❌ Phase 0 失敗，中止升級"
  exit 1
fi

# 執行Phase 1: 系統分析
echo "Phase 1: 執行系統分析..."
./01_analyze_system.sh
./02_inventory_files.sh

# 執行Phase 2: 六階段恢復 (高風險階段)
echo "⚠️ Phase 2: 六階段恢復 (高風險階段)"
read -p "確認繼續? (yes/no): " continue_phase2
if [ "$continue_phase2" != "yes" ]; then
  echo "升級已暫停"
  exit 0
fi
./03_restore_six_stages.sh

# 執行Phase 3: 資產整合
echo "Phase 3: 執行資產整合..."
./04_integrate_assets.sh

# 執行Phase 4: 技術優化
echo "Phase 4: 執行技術優化..."
./05_fix_cross_platform.sh
./06_validate_data_sources.sh

echo ""
echo "✅ LEO六階段升級完成！"
echo "📋 Phase 5清理計劃已準備，等待系統穩定後執行"
echo "🔗 請參考README.md進行驗證測試"
