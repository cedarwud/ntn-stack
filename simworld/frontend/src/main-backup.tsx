// Backup of the modified main.tsx
// StrictMode 已被暫時禁用 - 如需重新啟用請取消註釋 StrictMode 相關代碼
import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
// import './styles/index.scss'
// import App from './App.tsx'
// import DecisionControlCenterSimple from './components/unified-decision-center/DecisionControlCenterSimple'
// import D2DataProcessingDemo from './pages/D2DataProcessingDemo'
// import axios from 'axios'

// (rest of the commented out file content would be here...)

try {
    console.log('Starting React app...')
    createRoot(document.getElementById('root')!).render(
        <div>
            <h1>Debug: React app is working</h1>
            <p>This is a minimal test to verify React mounting</p>
        </div>
    )
    console.log('React app started successfully')
} catch (error) {
    console.error('Error starting React app:', error)
}