/**
 * Event D2 測試腳本
 * 驗證移動參考位置距離事件的功能
 */

// 測試衛星軌道計算
function testSatelliteOrbitCalculation() {
    console.log('=== Event D2 衛星軌道計算測試 ===')
    
    // 模擬計算函數
    function calculateAdvancedSatellitePosition(timeSeconds: number) {
        const centerLat = 25.0478
        const centerLon = 121.5319
        const orbitRadius = 0.01
        const orbitPeriod = 120
        const orbitAltitude = 550000
        
        const orbitalAngle = (timeSeconds / orbitPeriod) * 2 * Math.PI
        const earthRotationAngle = (timeSeconds / 86400) * 2 * Math.PI
        
        const satLat = centerLat + orbitRadius * Math.cos(orbitalAngle)
        const satLon = centerLon + orbitRadius * Math.sin(orbitalAngle) - earthRotationAngle * (180 / Math.PI)
        const orbitalVelocity = (2 * Math.PI * (6371 + 550)) / (orbitPeriod / 60)
        
        return {
            lat: satLat,
            lon: satLon,
            altitude: orbitAltitude,
            velocity: orbitalVelocity
        }
    }
    
    // 測試不同時間點的衛星位置
    const testTimes = [0, 30, 60, 90, 120]
    testTimes.forEach(time => {
        const pos = calculateAdvancedSatellitePosition(time)
        console.log(`時間 ${time}s: 緯度=${pos.lat.toFixed(4)}, 經度=${pos.lon.toFixed(4)}, 高度=${pos.altitude}m, 速度=${pos.velocity.toFixed(2)}km/s`)
    })
}

// 測試 Event D2 條件邏輯
function testEventD2Conditions() {
    console.log('\n=== Event D2 條件邏輯測試 ===')
    
    const testCases = [
        { distance1: 450, distance2: 7500, thresh1: 400, thresh2: 8000, hys: 20, expected: true },
        { distance1: 350, distance2: 8500, thresh1: 400, thresh2: 8000, hys: 20, expected: false },
        { distance1: 500, distance2: 7000, thresh1: 400, thresh2: 8000, hys: 20, expected: true },
        { distance1: 380, distance2: 7800, thresh1: 400, thresh2: 8000, hys: 20, expected: false },
    ]
    
    testCases.forEach((testCase, index) => {
        const { distance1, distance2, thresh1, thresh2, hys } = testCase
        
        // D2-1 進入條件: Ml1 - Hys > Thresh1
        const condition1 = distance1 - hys > thresh1
        // D2-2 進入條件: Ml2 + Hys < Thresh2
        const condition2 = distance2 + hys < thresh2
        // 事件觸發需要兩個條件同時滿足
        const eventTriggered = condition1 && condition2
        
        console.log(`測試案例 ${index + 1}:`)
        console.log(`  距離1=${distance1}m, 距離2=${distance2}m`)
        console.log(`  條件1 (${distance1} - ${hys} > ${thresh1}): ${condition1}`)
        console.log(`  條件2 (${distance2} + ${hys} < ${thresh2}): ${condition2}`)
        console.log(`  事件觸發: ${eventTriggered} (預期: ${testCase.expected})`)
        console.log(`  結果: ${eventTriggered === testCase.expected ? '✅ 通過' : '❌ 失敗'}`)
        console.log('')
    })
}

// 測試 3D 距離計算
function test3DDistanceCalculation() {
    console.log('=== 3D 距離計算測試 ===')
    
    function calculate3DDistance(lat1: number, lon1: number, alt1: number, lat2: number, lon2: number, alt2: number): number {
        // 計算表面距離 (Haversine formula)
        const R = 6371000
        const dLat = ((lat2 - lat1) * Math.PI) / 180
        const dLon = ((lon2 - lon1) * Math.PI) / 180
        const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                  Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) *
                  Math.sin(dLon / 2) * Math.sin(dLon / 2)
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
        const surfaceDistance = R * c
        
        // 計算高度差
        const altitudeDiff = Math.abs(alt1 - alt2)
        
        // 計算 3D 距離
        return Math.sqrt(surfaceDistance * surfaceDistance + altitudeDiff * altitudeDiff)
    }
    
    // 測試案例：UE 在地面，衛星在高空
    const uePos = { lat: 25.048, lon: 121.528, alt: 0 }
    const satPos = { lat: 25.0478, lon: 121.5319, alt: 550000 }
    
    const distance3D = calculate3DDistance(uePos.lat, uePos.lon, uePos.alt, satPos.lat, satPos.lon, satPos.alt)
    console.log(`UE 到衛星的 3D 距離: ${distance3D.toFixed(0)}m (約 ${(distance3D/1000).toFixed(1)}km)`)
    
    // 理論最小距離應該接近衛星高度
    console.log(`衛星高度: ${satPos.alt}m (${satPos.alt/1000}km)`)
    console.log(`距離是否合理: ${distance3D >= satPos.alt ? '✅ 是' : '❌ 否'}`)
}

// 執行所有測試
export function runEventD2Tests() {
    console.log('🚀 開始 Event D2 功能測試\n')
    
    testSatelliteOrbitCalculation()
    testEventD2Conditions()
    test3DDistanceCalculation()
    
    console.log('✅ Event D2 測試完成!')
}

// 如果是 Node.js 環境，直接執行測試
if (typeof module !== 'undefined' && module.exports) {
    runEventD2Tests()
}
