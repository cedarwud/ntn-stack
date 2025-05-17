import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

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

    // 所有其他警告正常顯示
    originalWarn.apply(console, args)
}

createRoot(document.getElementById('root')!).render(
    <StrictMode>
        <App />
    </StrictMode>
)
