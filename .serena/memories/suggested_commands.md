# NTN Stack 開發常用命令

## 項目啟動
```bash
# 啟動所有服務 (開發環境)
make dev

# 啟動完整系統
make all-start

# 檢查服務狀態
make status

# 查看日誌
make logs
```

## 前端開發
```bash
# 進入前端目錄
cd simworld/frontend

# 安裝依賴
npm install

# 開發模式
npm run dev

# 建置
npm run build

# 測試
npm run test

# 程式碼檢查
npm run lint
```

## 後端開發
```bash
# 進入後端目錄
cd netstack

# 啟動開發環境
make dev-up

# 查看 API 文檔
# http://localhost:8080/docs
```

## Docker 操作
```bash
# 重新建置並啟動
make fresh-up

# 停止所有服務
make down

# 清理資源
make clean

# 清理映像檔
make clean-i
```

## 測試相關
```bash
# 進入測試目錄
cd tests

# 快速煙霧測試
make test-smoke

# 完整測試套件
make test-all
```

## 系統工具 (Linux)
```bash
# 文件查找
find . -name "*.tsx" -type f

# 內容搜尋
grep -r "EventA4" simworld/frontend/src

# 查看進程
ps aux | grep node

# 查看端口
netstat -tlnp | grep :5173

# 文件權限
chmod +x script.sh

# 磁盤使用
df -h
du -sh *
```

## Git 操作
```bash
# 查看狀態
git status

# 添加變更
git add .

# 提交
git commit -m "feat: implement Event D1 chart"

# 推送
git push origin main

# 查看分支
git branch -a
```