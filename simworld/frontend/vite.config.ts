// vite.config.ts
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react-swc'

// 標記這是一個 Node.js 環境，所以 console 是有效的
/* eslint-disable */
// @ts-ignore
const nodeProcess = process;

export default defineConfig(({ command, mode }) => {
    // 加載環境變量
    const env = loadEnv(mode, process.cwd(), '')
    
    return {
    plugins: [react()],
        
        // 開發伺服器配置
    server: {
        host: '0.0.0.0', // 👈 必填，表示聽所有網卡
            port: parseInt(env.VITE_PORT) || 5173, // 使用 5173 端口
        strictPort: false, // 設為 false 以允許自動尋找可用端口
        hmr: {
            host: '120.126.151.101', // 👈 請將這裡替換成您的伺服器可被瀏覽器訪問的實際 IP 或主機名
            port: 5173, // 保持與 server.port 一致
        },
        proxy: {
                // 代理API請求到後端
            '/api': {
                    target: 'http://simworld_backend:8000',
                    changeOrigin: true,
                    secure: false,
                },
                // 代理 WebSocket 連接
                '/socket.io': {
                    target: 'http://simworld_backend:8000',
                    changeOrigin: true,
                    ws: true,
            },
            // 增加對靜態文件的代理
            '/rendered_images': {
                target: 'http://simworld_backend:8000',
                changeOrigin: true,
                secure: false,
            },
            // 其他靜態資源路徑
            '/static': {
                target: 'http://simworld_backend:8000',
                changeOrigin: true,
                secure: false,
            }
        },
    },
        
        // 測試配置
        test: {
            globals: true,
            environment: 'jsdom',
            setupFiles: './src/test/setup.ts',
            css: true,
            coverage: {
                provider: 'v8',
                reporter: ['text', 'json', 'html'],
                exclude: [
                    'node_modules/',
                    'src/test/',
                    '**/*.d.ts',
                    '**/*.config.*',
                    'dist/'
                ]
            }
        },
        
        // 預覽配置
        preview: {
            host: '0.0.0.0',
            port: parseInt(env.VITE_PORT) || 5173,
        },
        
        // 構建配置
        build: {
            outDir: 'dist',
            sourcemap: true,
            rollupOptions: {
                output: {
                    manualChunks: {
                        vendor: ['react', 'react-dom'],
                        charts: ['chart.js', 'echarts', 'react-chartjs-2', 'echarts-for-react'],
                        visualization: ['d3', '@react-three/fiber', '@react-three/drei']
                    }
                }
            }
        }
    }
})
