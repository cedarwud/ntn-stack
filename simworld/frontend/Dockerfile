# frontend/Dockerfile

# 1. 使用官方 Node.js 鏡像 (例如 LTS 版本 20)
FROM node:20-alpine

# 2. 設定工作目錄
WORKDIR /app

# 3. 複製 package.json 和 lock 文件 (利用緩存)
COPY package.json yarn.lock* package-lock.json* ./
# 如果只用 npm，可以只複製 package.json 和 package-lock.json

# 4. 安裝依賴
# 如果用 yarn:
# RUN yarn install --frozen-lockfile
# 如果用 npm:
RUN npm install

# 5. 複製所有前端程式碼
# COPY . .

# 6. 暴露 Vite 開發伺服器端口
EXPOSE 5173

# 7. 容器啟動時運行的命令 (啟動 Vite 開發伺服器並監聽所有地址)
CMD ["npm", "run", "dev", "--", "--host"]