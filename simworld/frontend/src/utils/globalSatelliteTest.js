/**
 * 全球視野衛星測試腳本
 * 可以在瀏覽器控制台中執行，測試不同參數下的衛星API響應
 */

window.testGlobalSatelliteView = async function () {
    console.log('🌍 開始全球視野衛星測試...')

    const testCases = [
        {
            name: '極限全球視野測試',
            params: { count: 100, min_elevation_deg: 0, global_view: true },
        },
        {
            name: '標準全球視野測試',
            params: { count: 50, min_elevation_deg: 0, global_view: true },
        },
        {
            name: '傳統地域限制測試（對照組）',
            params: {
                count: 20,
                min_elevation_deg: 5,
                global_view: false,
                observer_lat: 25.033,
                observer_lon: 121.565,
            },
        },
    ]

    for (const testCase of testCases) {
        console.log(`\n🔍 執行測試: ${testCase.name}`)
        console.log(`參數:`, testCase.params)

        try {
            const queryString = new URLSearchParams(testCase.params).toString()
            const url = `/api/v1/satellite-ops/visible_satellites?${queryString}`

            const startTime = performance.now()
            const response = await fetch(url)
            const endTime = performance.now()

            console.log(`⏱️ 響應時間: ${(endTime - startTime).toFixed(2)}ms`)
            console.log(`📡 HTTP狀態: ${response.status}`)

            if (response.ok) {
                const data = await response.json()
                const satelliteCount = data.satellites?.length || 0

                console.log(`🛰️ 獲得衛星數量: ${satelliteCount}`)
                console.log(
                    `📊 後端處理統計: 處理 ${
                        data.processed || 'N/A'
                    } 顆，可見 ${data.visible || 'N/A'} 顆`
                )

                if (satelliteCount > 0) {
                    // 分析衛星分布
                    const elevations = data.satellites.map(
                        (sat) => sat.elevation_deg || 0
                    )
                    const avgElevation =
                        elevations.reduce((sum, el) => sum + el, 0) /
                        elevations.length
                    const minElevation = Math.min(...elevations)
                    const maxElevation = Math.max(...elevations)

                    console.log(
                        `📐 仰角分布: 平均 ${avgElevation.toFixed(
                            1
                        )}°, 範圍 ${minElevation.toFixed(
                            1
                        )}° ~ ${maxElevation.toFixed(1)}°`
                    )

                    // 檢查星座分布
                    const constellations = {}
                    data.satellites.forEach((sat) => {
                        const name = sat.name?.toUpperCase() || 'UNKNOWN'
                        if (name.includes('STARLINK'))
                            constellations.STARLINK =
                                (constellations.STARLINK || 0) + 1
                        else if (name.includes('KUIPER'))
                            constellations.KUIPER =
                                (constellations.KUIPER || 0) + 1
                        else if (name.includes('ONEWEB'))
                            constellations.ONEWEB =
                                (constellations.ONEWEB || 0) + 1
                        else
                            constellations.OTHER =
                                (constellations.OTHER || 0) + 1
                    })
                    console.log(`🛰️ 星座分布:`, constellations)

                    console.log(`✅ 測試成功`)
                } else {
                    console.log(`❌ 無衛星數據`)
                }
            } else {
                console.log(`❌ API請求失敗: ${response.status}`)
                const errorText = await response.text()
                console.log(`錯誤內容: ${errorText}`)
            }
        } catch (error) {
            console.error(`❌ 測試過程中發生錯誤:`, error)
        }

        console.log(`${'='.repeat(50)}`)
    }

    console.log('\n🌍 全球視野衛星測試完成')
    console.log(
        '💡 提示: 如果所有測試都只返回少量衛星，說明後端需要實現真正的全球視野模式'
    )
}

// 快速測試函數
window.quickSatelliteTest = async function () {
    console.log('🚀 快速衛星測試...')
    try {
        const response = await fetch(
            '/api/v1/satellite-ops/visible_satellites?count=100&min_elevation_deg=0&global_view=true'
        )
        if (response.ok) {
            const data = await response.json()
            console.log(`✅ 獲得 ${data.satellites?.length || 0} 顆衛星`)
            return data.satellites?.length || 0
        } else {
            console.log(`❌ API失敗: ${response.status}`)
            return 0
        }
    } catch (error) {
        console.error('❌ 錯誤:', error)
        return 0
    }
}

console.log('🌍 全球視野測試腳本已載入')
console.log('💡 執行 testGlobalSatelliteView() 進行完整測試')
console.log('💡 執行 quickSatelliteTest() 進行快速測試')
