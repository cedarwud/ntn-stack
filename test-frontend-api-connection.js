#!/usr/bin/env node

/**
 * 測試前端 API 連接
 * 模擬瀏覽器環境中的 fetch 請求
 */

const test_url = 'http://localhost:5173/netstack/api/v1/satellite-simple/visible_satellites?count=3&min_elevation_deg=5&observer_lat=24.9441667&observer_lon=121.3713889&utc_timestamp=2025-08-18T12:00:00.000Z&global_view=false'

console.log('🧪 測試前端 API 連接...')
console.log('URL:', test_url)

async function testConnection() {
    try {
        const response = await fetch(test_url, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            timeout: 30000
        })
        
        if (!response.ok) {
            console.error('❌ HTTP 錯誤:', response.status, response.statusText)
            return false
        }
        
        const data = await response.json()
        console.log('✅ API 連接成功')
        console.log('📊 返回衛星數量:', data.total_count)
        console.log('🛰️ 第一顆衛星:', data.satellites?.[0]?.name || '無')
        
        return true
    } catch (error) {
        console.error('❌ 連接失敗:', error.message)
        if (error.name === 'AbortError') {
            console.error('⏰ 請求超時')
        } else if (error.message.includes('Failed to fetch')) {
            console.error('🌐 網路連接失敗，可能原因:')
            console.error('  - Vite 代理配置問題')
            console.error('  - 後端服務不可達')
            console.error('  - 防火牆阻擋')
        }
        return false
    }
}

testConnection().then(success => {
    process.exit(success ? 0 : 1)
})