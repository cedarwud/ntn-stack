import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './styles/index.scss'
import App from './App.tsx'
import DataVisualizationDashboard from './components/dashboard/DataVisualizationDashboard'
import './styles/Dashboard.scss'
import axios from 'axios'

// 導入性能監控器（自動啟動）
import './utils/performanceMonitor'

// 設定 axios 默認配置，忽略設置 baseURL
// 讓所有請求都使用相對路徑，由 Vite 代理處理

// 攔截 axios 請求，確保使用相對路徑
axios.interceptors.request.use((config) => {
    // 檢查 URL 是否已經是相對路徑
    if (config.url && config.url.startsWith('/api')) {
        // 已經是相對路徑，不需要修改
        return config
    }

    // 對於其他可能的絕對路徑，返回配置時不做修改
    return config
})

// 攔截控制台警告和錯誤以忽略特定內容
const originalWarn = console.warn
const originalError = console.error

// 檢查是否為瀏覽器擴展相關的錯誤
function isExtensionRelated(message: string): boolean {
    const extensionKeywords = [
        'chrome-extension://',
        'moz-extension://',
        'CacheStore.js',
        'GenAIWebpageEligibilityService',
        'ActionableCoachmark',
        'ShowOneChild',
        'ch-content-script',
        'content-script-utils',
        'jquery-3.1.1.min.js',
        'Cache get failed',
        'Cache set failed',
        'caches is not defined',
    ]

    return extensionKeywords.some((keyword) => message.includes(keyword))
}

console.warn = function (...args) {
    const message = args[0]

    // 過濾瀏覽器擴展相關的警告
    if (message && typeof message === 'string' && isExtensionRelated(message)) {
        return
    }

    // 忽略 KHR_materials_pbrSpecularGlossiness 擴展警告
    if (
        args[0] &&
        typeof args[0] === 'string' &&
        args[0].includes(
            'Unknown extension "KHR_materials_pbrSpecularGlossiness"'
        )
    ) {
        return
    }

    // 忽略缺失的動畫節點警告
    if (
        args[0] &&
        typeof args[0] === 'string' &&
        args[0].includes(
            'THREE.PropertyBinding: No target node found for track:'
        )
    ) {
        return
    }

    // 忽略 React Router 關於 startTransition 的警告
    if (
        args[0] &&
        typeof args[0] === 'string' &&
        args[0].includes('React Router Future Flag Warning') &&
        args[0].includes('v7_startTransition')
    ) {
        return
    }

    // 所有其他警告正常顯示
    originalWarn.apply(console, args)
}

console.error = function (...args) {
    const message = args[0]

    // 過濾瀏覽器擴展相關的錯誤
    if (message && typeof message === 'string' && isExtensionRelated(message)) {
        return
    }

    // 過濾已知的無害錯誤
    if (message && typeof message === 'string') {
        const harmlessErrors = [
            'ResizeObserver loop limit exceeded',
            'Non-Error promise rejection captured',
        ]

        if (harmlessErrors.some((pattern) => message.includes(pattern))) {
            return
        }
    }

    // 所有其他錯誤正常顯示
    originalError.apply(console, args)
}

createRoot(document.getElementById('root')!).render(
    <StrictMode>
        <BrowserRouter>
            <Routes>
                {/* 首頁重定向到 /nycu/stereogram */}
                <Route
                    path="/"
                    element={<Navigate to="/nycu/stereogram" replace />}
                />

                {/* /nycu 重定向到 /nycu/stereogram */}
                <Route
                    path="/nycu"
                    element={<Navigate to="/nycu/stereogram" replace />}
                />

                {/* 數據可視化儀表盤 */}
                <Route
                    path="/dashboard"
                    element={<DataVisualizationDashboard />}
                />

                {/* 場景路由 - stereogram */}
                <Route
                    path="/:scenes/stereogram"
                    element={<App activeView="stereogram" />}
                />

                {/* 場景路由 - floor-plan */}
                <Route
                    path="/:scenes/floor-plan"
                    element={<App activeView="floor-plan" />}
                />

                {/* 404 重定向到預設場景 */}
                <Route
                    path="*"
                    element={<Navigate to="/nycu/stereogram" replace />}
                />
            </Routes>
        </BrowserRouter>
    </StrictMode>
)
