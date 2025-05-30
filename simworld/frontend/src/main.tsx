import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom'
import './styles/index.scss'
import App from './App.tsx'
import axios from 'axios'

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

// 攔截控制台警告以忽略特定的 Three.js 警告
const originalWarn = console.warn
console.warn = function (...args) {
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

// 使用 v7 的數據路由 API 創建路由
const router = createBrowserRouter(
    [
        {
            // 首頁重定向到 /nycu/stereogram
            path: '/',
            element: <Navigate to="/nycu/stereogram" replace />,
        },
        {
            // /nycu 重定向到 /nycu/stereogram
            path: '/nycu',
            element: <Navigate to="/nycu/stereogram" replace />,
        },
        {
            // 場景路由 - stereogram
            path: '/:scenes/stereogram',
            element: <App activeView="stereogram" />,
        },
        {
            // 場景路由 - floor-plan
            path: '/:scenes/floor-plan',
            element: <App activeView="floor-plan" />,
        },
        {
            // 404 重定向到預設場景
            path: '*',
            element: <Navigate to="/nycu/stereogram" replace />,
        },
    ],
    {
        future: {
            // @ts-ignore - React Router v7 新特性
            v7_startTransition: true,
        },
    }
)

createRoot(document.getElementById('root')!).render(
    <StrictMode>
        <RouterProvider router={router} />
    </StrictMode>
)
