# 🕒 Cron調度頻率優化說明

**基於用戶反饋**: TLE每6小時才下載一次，每2小時自動檢查沒有意義，且TLE數據可以用好幾天

## ❌ 原設計問題

### 過於頻繁的檢查
```bash
# 問題：每2小時檢查增量更新
0 */2 * * * intelligent_cron_update.sh  # 一天12次！

# 問題：與TLE下載頻率不匹配  
0 2,8,14,20 * * * daily_tle_download.sh  # 一天4次
```

### 邏輯問題分析
1. **TLE數據精度**：可用3-7天，不需頻繁更新
2. **資源浪費**：大部分檢查都是無效的
3. **頻率不匹配**：檢查頻率 > 數據更新頻率

---

## ✅ 修正後的調度策略 (保護 RL 訓練數據)

### **生產環境推薦**
```bash
# 🛰️ TLE數據下載 (恢復每6小時4次，供RL訓練使用)
0 2,8,14,20 * * * /home/sat/ntn-stack/scripts/daily_tle_download_enhanced.sh

# 🧠 智能增量更新 (每天1次，檢查非RL數據變更)
0 5 * * * /home/sat/ntn-stack/leo_restructure/intelligent_cron_update.sh

# 🔄 完整系統重建 (每週日凌晨，確保系統健康)
0 3 * * 0 cd /home/sat/ntn-stack && make down-v && make build-n && make up

# 🧹 安全清理過期檔案 (保護 RL 訓練數據)
0 1 * * * cd /home/sat/ntn-stack/leo_restructure && python -c "
from shared_core.auto_cleanup_manager import AutoCleanupManager
# 使用受保護的清理管理器，絕不刪除 /netstack/tle_data/
manager = AutoCleanupManager()
manager.cleanup_by_age(72, mode='temp_cache')  # 僅清理臨時緩存
"
```

### **開發環境使用**
```bash
# 主要使用手動觸發
leo-inc      # 代碼變更後增量更新
leo-check    # 檢查是否需要更新
leo-clean    # 清理舊數據
```

---

## 📊 效率對比

| 項目 | 原設計 | 修正後 | 改善 |
|------|--------|--------|------|
| **檢查頻率** | 每2小時 (12次/天) | 每天1次 | **減少92%** |
| **TLE下載** | 每6小時 (4次/天) | **維持 4次/天** | **RL訓練需求** |
| **資源使用** | 高 (頻繁檢查) | 低 (智能清理) | **大幅減少** |
| **數據保護** | 無 | **RL數據受保護** | **新增安全機制** |

---

## 🎯 智能檢查邏輯

### **增量更新觸發條件**
```python
def should_run_incremental():
    # 1. 檢查TLE是否在過去12小時內更新
    if tle_updated_recently(12 * 3600):
        return True, "tle_incremental"
    
    # 2. 檢查代碼是否在過去24小時內變更
    if code_changed_recently(24 * 3600):
        return True, "code_incremental"
    
    # 3. 檢查輸出數據是否超過3天
    if output_age() > 3 * 24 * 3600:
        return True, "output_refresh"
    
    # 4. 檢查是否超過1週未完整重建
    if last_full_rebuild() > 7 * 24 * 3600:
        return True, "full_rebuild"
    
    return False, "no_update_needed"
```

### **實際運行示例**
```bash
🕒 2025-08-15 05:00:00 - 開始智能增量更新檢查...
🔍 檢測系統變更...
📡 檢查TLE更新: 最後下載 2025-08-15 02:00:00 (3小時前)
💻 檢查代碡變更: 無變更 (檢查24小時內)
📊 檢查輸出新鮮度: 1天前 (良好)
💡 建議策略: tle_incremental

📡 執行TLE增量更新...
✅ TLE增量更新完成 (156秒)
📝 下次檢查時間: 2025-08-16 05:00:00
```

---

## 🎯 關鍵修正原則

1. **RL 訓練數據保護**：絕對禁止清理 `/netstack/tle_data/` 
2. **維持 TLE 下載頻率**：每 6 小時 4 次，供 RL 訓練使用
3. **智能清理策略**：僅清理臨時緩存，保護核心數據
4. **按需更新**：只在真正需要時執行增量處理
5. **錯開時間**：避免同時競爭系統資源

---

## 📋 使用建議

### **生產環境**
- 使用優化後的Cron調度
- 監控 `/tmp/intelligent_update.log` 了解更新狀況
- 每週檢查系統健康狀況

### **開發環境**  
- 主要使用手動觸發 (`leo-inc`)
- 代碼變更後立即測試
- 定期執行 `leo-clean` 清理舊數據

### **緊急情況**
- 使用 `leo-build` 完整重建
- 使用 `leo-check` 診斷問題
- 檢查 `/tmp/intelligent_update.log` 錯誤日誌

---

**總結**: 優化後的調度策略更符合實際需求，大幅減少無意義檢查，提升系統效率和穩定性。