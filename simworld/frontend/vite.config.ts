// vite.config.ts
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

export default defineConfig(({ mode }) => {
    // 加載環境變量
    const env = loadEnv(mode, process.cwd(), '')
    
    return {
    plugins: [react()],
    
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },
        
        // 開發伺服器配置
    server: {
        host: '0.0.0.0', // 👈 必填，表示聽所有網卡
            port: parseInt(env.VITE_PORT) || 5173, // 使用 5173 端口
        strictPort: false, // 設為 false 以允許自動尋找可用端口
        hmr: false, // 在 Docker 環境中禁用 HMR 避免 WebSocket 問題
        origin: 'http://localhost:5173',
        proxy: {
            // 統一的 SimWorld API 代理
            '/api': {
                target: env.VITE_SIMWORLD_PROXY_TARGET || 'http://simworld_backend:8000',
                changeOrigin: true,
                secure: false,
                configure: (proxy) => {
                    proxy.on('error', (err) => {
                        console.log('🚨 SimWorld API 代理錯誤:', err)
                    })
                }
            },

            // SimWorld v1 API 代理（用於信號分析圖表）
            '/v1': {
                target: env.VITE_SIMWORLD_PROXY_TARGET || 'http://simworld_backend:8000',
                changeOrigin: true,
                secure: false,
                configure: (proxy) => {
                    proxy.on('error', (err) => {
                        console.log('🚨 SimWorld v1 API 代理錯誤:', err)
                    })
                }
            },
            
            // 統一的 NetStack API 代理  
            '/netstack': {
                target: env.VITE_NETSTACK_PROXY_TARGET || 'http://netstack-api:8080',
                changeOrigin: true,
                secure: false,
                rewrite: (path) => path.replace(/^\/netstack/, ''),
                configure: (proxy) => {
                    proxy.on('error', (err) => {
                        console.log('🚨 NetStack API 代理錯誤:', err)
                    })
                }
            },
            
            // WebSocket 和靜態資源代理
            '/socket.io': {
                target: env.VITE_SIMWORLD_PROXY_TARGET || 'http://simworld_backend:8000',
                changeOrigin: true,
                ws: true,
            },
            '/rendered_images': {
                target: env.VITE_SIMWORLD_PROXY_TARGET || 'http://simworld_backend:8000',
                changeOrigin: true,
                secure: false,
            },
            '/static': {
                target: env.VITE_SIMWORLD_PROXY_TARGET || 'http://simworld_backend:8000',
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
            chunkSizeWarningLimit: 1000, // 增加警告閾值到 1MB
            rollupOptions: {
                output: {
                    manualChunks(id) {
                        // 核心依賴
                        if (id.includes('node_modules')) {
                            if (id.includes('react') || id.includes('react-dom')) {
                                return 'vendor'
                            }
                            if (id.includes('react-router')) {
                                return 'router-vendor'
                            }
                            if (id.includes('chart') || id.includes('echarts') || id.includes('d3')) {
                                return 'charts'
                            }
                            if (id.includes('@react-three') || id.includes('three')) {
                                return 'visualization'
                            }
                            if (id.includes('axios') || id.includes('socket.io')) {
                                return 'network'
                            }
                            return 'vendor-misc'
                        }
                        
                        // 應用程式模組分割
                        if (id.includes('/handover/')) {
                            return 'handover-system'
                        }
                        if (id.includes('/services/')) {
                            return 'api-services'
                        }
                        if (id.includes('/device/')) {
                            return 'device-management'
                        }
                    }
                }
            }
        }
    }
})
