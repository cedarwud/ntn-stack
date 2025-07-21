#!/usr/bin/env node

/**
 * D2圖表靜態數據測試腳本
 * 驗證交叉變化模式是否正確顯示
 */

// 模擬D2圖表的靜態測試數據
const staticTestData = [
    // 第1段：綠色上升，橙色下降
    { timestamp: '2023-01-01T00:00:00Z', satellite_distance: 550, ground_distance: 8.0, trigger_condition_met: false, reference_satellite: 'gps_24876' },
    { timestamp: '2023-01-01T00:00:02Z', satellite_distance: 551, ground_distance: 7.5, trigger_condition_met: false, reference_satellite: 'gps_24877' },
    { timestamp: '2023-01-01T00:00:04Z', satellite_distance: 552, ground_distance: 7.0, trigger_condition_met: false, reference_satellite: 'gps_24878' },
    { timestamp: '2023-01-01T00:00:06Z', satellite_distance: 553, ground_distance: 6.5, trigger_condition_met: false, reference_satellite: 'gps_24879' },
    { timestamp: '2023-01-01T00:00:08Z', satellite_distance: 554, ground_distance: 6.0, trigger_condition_met: false, reference_satellite: 'gps_24880' },
    
    // 第2段：兩線接近交叉點
    { timestamp: '2023-01-01T00:00:10Z', satellite_distance: 555, ground_distance: 5.5, trigger_condition_met: true, reference_satellite: 'gps_24881' },
    { timestamp: '2023-01-01T00:00:12Z', satellite_distance: 555, ground_distance: 5.0, trigger_condition_met: true, reference_satellite: 'gps_24882' },
    { timestamp: '2023-01-01T00:00:14Z', satellite_distance: 554, ground_distance: 4.5, trigger_condition_met: true, reference_satellite: 'gps_24883' },
    { timestamp: '2023-01-01T00:00:16Z', satellite_distance: 553, ground_distance: 4.0, trigger_condition_met: true, reference_satellite: 'gps_24884' },
    { timestamp: '2023-01-01T00:00:18Z', satellite_distance: 552, ground_distance: 3.8, trigger_condition_met: true, reference_satellite: 'gps_24885' },
    
    // 第3段：交叉後分離
    { timestamp: '2023-01-01T00:00:20Z', satellite_distance: 551, ground_distance: 4.0, trigger_condition_met: false, reference_satellite: 'gps_24886' },
    { timestamp: '2023-01-01T00:00:22Z', satellite_distance: 550, ground_distance: 4.5, trigger_condition_met: false, reference_satellite: 'gps_24887' },
    { timestamp: '2023-01-01T00:00:24Z', satellite_distance: 549, ground_distance: 5.0, trigger_condition_met: false, reference_satellite: 'gps_24888' },
    { timestamp: '2023-01-01T00:00:26Z', satellite_distance: 548, ground_distance: 5.5, trigger_condition_met: false, reference_satellite: 'gps_24889' },
    { timestamp: '2023-01-01T00:00:28Z', satellite_distance: 547, ground_distance: 6.0, trigger_condition_met: false, reference_satellite: 'gps_24890' },
    
    // 第4段：繼續分離
    { timestamp: '2023-01-01T00:00:30Z', satellite_distance: 546, ground_distance: 6.5, trigger_condition_met: false, reference_satellite: 'gps_24891' },
    { timestamp: '2023-01-01T00:00:32Z', satellite_distance: 545, ground_distance: 7.0, trigger_condition_met: false, reference_satellite: 'gps_24892' },
    { timestamp: '2023-01-01T00:00:34Z', satellite_distance: 545, ground_distance: 7.5, trigger_condition_met: false, reference_satellite: 'gps_24893' },
    { timestamp: '2023-01-01T00:00:36Z', satellite_distance: 546, ground_distance: 8.0, trigger_condition_met: false, reference_satellite: 'gps_24894' },
    { timestamp: '2023-01-01T00:00:38Z', satellite_distance: 547, ground_distance: 8.0, trigger_condition_met: false, reference_satellite: 'gps_24895' }
]

console.log('🎯 D2靜態數據測試')
console.log('==================')

// 分析數據模式
const satelliteDistances = staticTestData.map(d => d.satellite_distance)
const groundDistances = staticTestData.map(d => d.ground_distance)

console.log('\n📊 數據概要:')
console.log(`數據點數量: ${staticTestData.length}`)
console.log(`綠色曲線範圍: ${Math.min(...satelliteDistances)} - ${Math.max(...satelliteDistances)} km`)
console.log(`橙色曲線範圍: ${Math.min(...groundDistances)} - ${Math.max(...groundDistances)} km`)

// 檢查交叉變化模式
console.log('\n🔄 交叉變化分析:')
console.log('時間點 | 衛星距離 | 地面距離 | 觸發狀態')
console.log('------|--------|--------|--------')

staticTestData.forEach((point, index) => {
    const time = index * 2
    const trigger = point.trigger_condition_met ? '✅ 觸發' : '⏸️ 待機'
    console.log(`  ${time}s  |  ${point.satellite_distance}km  |   ${point.ground_distance}km   | ${trigger}`)
})

// 驗證交叉模式
const firstSat = satelliteDistances[0]
const lastSat = satelliteDistances[satelliteDistances.length - 1]
const maxSat = Math.max(...satelliteDistances)

const firstGround = groundDistances[0]
const lastGround = groundDistances[groundDistances.length - 1]
const minGround = Math.min(...groundDistances)

console.log('\n✅ 模式驗證:')
console.log(`綠色曲線: ${firstSat}km → ${maxSat}km → ${lastSat}km (倒U型) ${firstSat < maxSat && lastSat < maxSat ? '✅' : '❌'}`)
console.log(`橙色曲線: ${firstGround}km → ${minGround}km → ${lastGround}km (U型) ${firstGround > minGround && lastGround > minGround ? '✅' : '❌'}`)

// 觸發事件檢查
const triggerEvents = staticTestData.filter(d => d.trigger_condition_met)
console.log(`觸發事件: ${triggerEvents.length}個 (${triggerEvents[0]?.timestamp} - ${triggerEvents[triggerEvents.length-1]?.timestamp})`)

console.log('\n🎯 預期圖表效果:')
console.log('- 綠色曲線應該呈現倒U型 (先上升後下降)')
console.log('- 橙色曲線應該呈現U型 (先下降後上升)')
console.log('- 兩條曲線在中間區域交叉')
console.log('- 交叉區域應該有觸發事件標記')