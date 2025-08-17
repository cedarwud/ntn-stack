# 📦 Phase 0: 系統完整備份計劃

**風險等級**: 🟢 低風險  
**預估時間**: 10分鐘  
**必要性**: ✅ 絕對必要 - 所有後續修改的安全保障

## 🎯 目標

建立完整的系統備份，確保升級過程中任何失敗都可以完全回滾到原始狀態。

## 📋 備份清單

### 關鍵目錄完整備份
```bash
# 1. 整個 leo_core 目錄 (包含四階段系統)
/netstack/src/leo_core/ → backup/leo_core_$(date +%Y%m%d_%H%M%S)/

# 2. 六階段處理器目錄
/netstack/src/stages/ → backup/stages_original_$(date +%Y%m%d_%H%M%S)/

# 3. 前端相關檔案
/simworld/frontend/src/services/ → backup/frontend_services_$(date +%Y%m%d_%H%M%S)/
/simworld/frontend/src/config/ → backup/frontend_config_$(date +%Y%m%d_%H%M%S)/

# 4. 後端相關檔案  
/simworld/backend/app/api/routes/ → backup/backend_routes_$(date +%Y%m%d_%H%M%S)/

# 5. NetStack 配置檔案
/netstack/config/ → backup/netstack_config_$(date +%Y%m%d_%H%M%S)/
/netstack/netstack_api/routers/ → backup/netstack_routers_$(date +%Y%m%d_%H%M%S)/
```

### Git 狀態快照
```bash
# 當前 commit 狀態記錄
git rev-parse HEAD > backup/current_commit_$(date +%Y%m%d_%H%M%S).txt
git status --porcelain > backup/current_status_$(date +%Y%m%d_%H%M%S).txt
git diff > backup/current_diff_$(date +%Y%m%d_%H%M%S).patch
```

## 🔧 執行步驟

### Step 1: 建立備份根目錄
```bash
backup_timestamp=$(date +%Y%m%d_%H%M%S)
backup_root="/home/sat/ntn-stack/backup/upgrade_${backup_timestamp}"
mkdir -p "$backup_root"
echo "備份開始時間: $(date)" > "$backup_root/backup_info.txt"
```

### Step 2: 核心系統備份
```bash
# 備份 leo_core (四階段系統)
cp -r /home/sat/ntn-stack/netstack/src/leo_core "$backup_root/leo_core_original"

# 備份 stages (六階段處理器)
cp -r /home/sat/ntn-stack/netstack/src/stages "$backup_root/stages_original"

# 備份 NetStack 服務
cp -r /home/sat/ntn-stack/netstack/src/services "$backup_root/services_original"

# 備份 NetStack API 路由
cp -r /home/sat/ntn-stack/netstack/netstack_api/routers "$backup_root/routers_original"

# 備份配置檔案
cp -r /home/sat/ntn-stack/netstack/config "$backup_root/config_original"
```

### Step 3: 前端系統備份
```bash
# 前端服務檔案
cp -r /home/sat/ntn-stack/simworld/frontend/src/services "$backup_root/frontend_services_original"

# 前端配置檔案
cp -r /home/sat/ntn-stack/simworld/frontend/src/config "$backup_root/frontend_config_original"

# 關鍵組件
cp -r /home/sat/ntn-stack/simworld/frontend/src/components/domains "$backup_root/frontend_domains_original"
```

### Step 4: 後端系統備份
```bash
# 後端路由
cp -r /home/sat/ntn-stack/simworld/backend/app/api/routes "$backup_root/backend_routes_original"

# 後端服務
cp -r /home/sat/ntn-stack/simworld/backend/app/services "$backup_root/backend_services_original"
```

### Step 5: Git 狀態記錄
```bash
cd /home/sat/ntn-stack

# Git 狀態快照
git rev-parse HEAD > "$backup_root/current_commit.txt"
git status --porcelain > "$backup_root/current_status.txt"
git diff > "$backup_root/current_diff.patch"
git log --oneline -10 > "$backup_root/recent_commits.txt"

# 分支資訊
git branch -a > "$backup_root/all_branches.txt"
```

### Step 6: 系統資訊記錄
```bash
# 系統環境
uname -a > "$backup_root/system_info.txt"
python3 --version >> "$backup_root/system_info.txt"
node --version >> "$backup_root/system_info.txt"

# Docker 狀態
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" > "$backup_root/docker_status.txt"

# 檔案結構
find /home/sat/ntn-stack/netstack/src/leo_core -type f -name "*.py" | head -20 > "$backup_root/leo_core_files.txt"
find /home/sat/ntn-stack/netstack/src/stages -type f -name "*.py" | head -20 > "$backup_root/stages_files.txt"
```

### Step 7: 備份驗證
```bash
# 檔案數量檢查
echo "=== 備份驗證 ===" >> "$backup_root/backup_info.txt"
echo "leo_core 檔案數: $(find $backup_root/leo_core_original -type f | wc -l)" >> "$backup_root/backup_info.txt"
echo "stages 檔案數: $(find $backup_root/stages_original -type f | wc -l)" >> "$backup_root/backup_info.txt"
echo "前端服務檔案數: $(find $backup_root/frontend_services_original -type f | wc -l)" >> "$backup_root/backup_info.txt"
echo "後端路由檔案數: $(find $backup_root/backend_routes_original -type f | wc -l)" >> "$backup_root/backup_info.txt"

# 總大小計算
echo "備份總大小: $(du -sh $backup_root | cut -f1)" >> "$backup_root/backup_info.txt"
echo "備份完成時間: $(date)" >> "$backup_root/backup_info.txt"
```

## 🚨 回滾程序

### 完全回滾指令
```bash
# 1. 確認備份目錄
backup_dir="/home/sat/ntn-stack/backup/upgrade_XXXXXXXX_XXXXXX"  # 替換為實際時間戳

# 2. 停止所有服務
cd /home/sat/ntn-stack
make down

# 3. 恢復檔案
rm -rf /home/sat/ntn-stack/netstack/src/leo_core
cp -r "$backup_dir/leo_core_original" /home/sat/ntn-stack/netstack/src/leo_core

rm -rf /home/sat/ntn-stack/netstack/src/stages  
cp -r "$backup_dir/stages_original" /home/sat/ntn-stack/netstack/src/stages

rm -rf /home/sat/ntn-stack/netstack/config
cp -r "$backup_dir/config_original" /home/sat/ntn-stack/netstack/config

rm -rf /home/sat/ntn-stack/simworld/frontend/src/services
cp -r "$backup_dir/frontend_services_original" /home/sat/ntn-stack/simworld/frontend/src/services

# 4. Git 回滾 (如果需要)
git checkout $(cat "$backup_dir/current_commit.txt")

# 5. 重啟系統驗證
make up
```

## ✅ 成功標準

- [ ] 所有關鍵目錄已備份
- [ ] Git 狀態已記錄  
- [ ] 備份檔案完整性驗證通過
- [ ] 備份資訊檔案已生成
- [ ] 回滾程序已測試 (乾運行)

## 📊 執行結果記錄

執行完成後，請記錄：
- 備份目錄路徑: `_______________`
- 備份總大小: `_______________`
- 備份檔案數量: `_______________`
- 執行時間: `_______________`

## 🔗 下一步

備份完成並驗證成功後，繼續執行：
→ `01_current_system_analysis.md`

---
**⚠️ 重要**: 此階段必須100%成功才能繼續後續升級！
