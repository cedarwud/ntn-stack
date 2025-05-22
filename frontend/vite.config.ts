// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// 標記這是一個 Node.js 環境，所以 console 是有效的
/* eslint-disable */
// @ts-ignore
const nodeProcess = process;

export default defineConfig({
    plugins: [react()],
    server: {
        host: '0.0.0.0', // 👈 必填，表示聽所有網卡
        port: 5173, // 使用 5173 端口
        strictPort: false, // 設為 false 以允許自動尋找可用端口
        hmr: {
            host: '120.126.151.101', // 👈 請將這裡替換成您的伺服器可被瀏覽器訪問的實際 IP 或主機名
            port: 5173, // 保持與 server.port 一致
        },
        proxy: {
            // 將所有以 /api 開頭的請求都代理到後端
            '/api': {
                target: 'http://fastapi_app:8000', // 改回使用Docker網絡中的服務名稱
                changeOrigin: true, // 修改請求頭中的 Host 字段為目標 URL
                secure: false, // 關閉安全檢查，允許自簽證書
                rewrite: (path) => path, // 保持路徑不變
                configure: (proxy, options) => {
                    // 代理事件處理
                    proxy.on('error', (err, req, res) => {
                        nodeProcess.stdout.write(`代理錯誤: ${err}\n`);
                    });
                    proxy.on('proxyReq', (proxyReq, req, res) => {
                        nodeProcess.stdout.write(`代理請求: ${req.url}\n`);
                    });
                    proxy.on('proxyRes', (proxyRes, req, res) => {
                        nodeProcess.stdout.write(`代理響應: ${proxyRes.statusCode} ${req.url}\n`);
                    });
                },
            },
            // 增加對靜態文件的代理
            '/rendered_images': {
                target: 'http://fastapi_app:8000',
                changeOrigin: true,
                secure: false,
            },
            // 其他靜態資源路徑
            '/static': {
                target: 'http://fastapi_app:8000',
                changeOrigin: true,
                secure: false,
            }
        },
    },
})
