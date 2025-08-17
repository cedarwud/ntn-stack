# 🛡️ LEO系統升級備份報告

**備份時間**: 2025-08-17 13:09  
**備份目錄**: /home/sat/ntn-stack/backup/upgrade_20250817_1308

## 📂 備份內容清單

### 六階段系統檔案
- `stages/`: Python檔案已備份
- `services/satellite/`: 服務檔案已備份

### 四階段系統檔案  
- `leo_core/`: 四階段系統已備份

### leo_restructure資產
- 技術資產目錄已完整備份

### 升級計劃
- 完整升級計劃檔案已備份

## 🔄 回滾指令

如需回滾整個升級：
```bash
# 停止服務
make down

# 回滾檔案
backup_dir="/home/sat/ntn-stack/backup/upgrade_20250817_1308"
cp -r "$backup_dir/six_stage_system/stages/" /home/sat/ntn-stack/netstack/src/ 2>/dev/null
cp -r "$backup_dir/six_stage_system/satellite/" /home/sat/ntn-stack/netstack/src/services/ 2>/dev/null
cp -r "$backup_dir/four_stage_system/leo_core/" /home/sat/ntn-stack/netstack/src/ 2>/dev/null

# 重啟服務
make up
```

**✅ 備份狀態**: 完成