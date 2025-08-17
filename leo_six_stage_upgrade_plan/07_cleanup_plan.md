# 🧹 Phase 5: 四階段檔案清理計劃

**風險等級**: 🟢 低風險  
**預估時間**: 30分鐘  
**必要性**: ✅ 整理清潔 - 清理四階段開發期間產生的檔案，恢復系統整潔

## 🎯 目標

安全清理**四階段開發檔案**(F1/F2/F3/A1相關)，保留並強化六階段系統，在技術資產整合完成後執行清理。

## 📋 待清理檔案清單 

### 四階段系統檔案 (需要清理)
```bash
# F1/F2/F3/A1 四階段系統 (整合完成後清理)
/netstack/src/leo_core/core_system/          # 整個四階段目錄
/netstack/src/leo_core.backup.20250816_*/    # 四階段備份目錄

# 四階段主控制器
/netstack/src/leo_core/core_system/main_pipeline.py
```

### 六階段系統檔案 (⭐ 保留並強化)
```bash
# 六階段處理器 (保留)
/netstack/src/stages/stage1_tle_processor.py
/netstack/src/stages/stage2_filter_processor.py  
/netstack/src/stages/stage3_signal_processor.py
/netstack/src/stages/stage4_timeseries_processor.py
/netstack/src/stages/stage5_integration_processor.py
/netstack/src/stages/stage6_dynamic_pool_planner.py

# 六階段核心組件 (保留)
/netstack/src/services/satellite/intelligent_filtering/unified_intelligent_filter.py  # 93.6%篩選率
/netstack/src/services/satellite/intelligent_filtering/                              # 智能篩選系統
/netstack/src/services/satellite/preprocessing/                                      # 預處理系統
```

### 六階段文檔系統 (⭐ 保留)
```bash
# 六階段文檔 (保留並更新)
/docs/overviews/data-processing-flow.md      # 六階段概述
/docs/stages/stage1-6*.md                    # 階段文檔
/docs/satellite_handover_standards.md        # 重要標準文檔
```

### 清理統計
- **清理對象**: 四階段檔案 (F1/F2/F3/A1)
- **保留對象**: 六階段檔案 + 技術資產整合
- **升級策略**: 六階段 + leo_restructure技術

## 🔧 清理執行計劃

### Step 1: 生成詳細檔案清單
```bash
# 掃描所有四階段相關檔案
find /home/sat/ntn-stack -name "*F1*" -o -name "*F2*" -o -name "*F3*" -o -name "*A1*" \
     -o -path "*/leo_core/core_system/*" > four_stage_cleanup_list.txt

echo "待清理檔案數量: $(wc -l < four_stage_cleanup_list.txt)"
```

### Step 2: 創建安全清理腳本
```bash
cat > safe_cleanup_four_stage.sh << 'EOF'
#!/bin/bash
# 四階段安全清理腳本

# 最終確認
echo "⚠️ 即將清理四階段檔案，請確認六階段系統已穩定運行"
read -p "繼續清理? (yes/no): " confirmation
if [ "$confirmation" != "yes" ]; then
  echo "清理已取消"
  exit 0
fi

# 執行清理
rm -rf /home/sat/ntn-stack/netstack/src/leo_core/core_system/
rm -rf /home/sat/ntn-stack/netstack/src/leo_core.backup.*/

echo "✅ 四階段檔案清理完成"
EOF
```

## ✅ 清理檢查清單

- [ ] 六階段系統已穩定運行3天以上
- [ ] 前端立體圖正常渲染
- [ ] API響應正常，篩選效率達93.6%  
- [ ] 詳細檔案清單已生成
- [ ] 用戶已確認可以清理

---
**重要**: 只有在六階段系統完全穩定後才執行清理！
