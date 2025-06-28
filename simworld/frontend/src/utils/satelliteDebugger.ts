/**
 * 衛星數據調試工具
 * 用於分析為什麼衛星數據少於預期數量的問題
 */

interface SatelliteDebugInfo {
  apiUrl: string
  params: Record<string, any>
  responseStatus: number
  responseData: any
  satelliteCount: number
  analysisResult: {
    issue: string
    possibleCauses: string[]
    recommendations: string[]
  }
}

export class SatelliteDebugger {
  /**
   * 全面測試衛星API並分析數據源
   */
  static async debugSatelliteAPI(): Promise<SatelliteDebugInfo> {
    const debugInfo: Partial<SatelliteDebugInfo> = {}
    
    // 🌍 設置全球視野測試參數 - 移除地域限制
    const params = {
      count: 100,  // 🚀 大幅增加請求數量
      min_elevation_deg: 0,  // 🌍 使用標準仰角（地平線以上）
      global_view: true,  // 強制全球視野
      // 🌍 不指定觀測點，讓後端返回全球範圍的衛星
    }
    
    const queryString = new URLSearchParams(params as any).toString()
    const apiUrl = `/api/v1/satellite-ops/visible_satellites?${queryString}`
    
    debugInfo.apiUrl = apiUrl
    debugInfo.params = params
    
    console.log(`🔍 SatelliteDebugger: 開始全球視野衛星API調試`)
    console.log(`🌍 API URL: ${apiUrl}`)
    console.log(`🌍 全球視野參數:`, params)
    console.log(`🌍 目標: 獲取全球範圍內所有可用衛星，不受地域限制`)
    
    try {
      // 發送API請求
      const startTime = performance.now()
      const response = await fetch(apiUrl, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      const endTime = performance.now()
      
      debugInfo.responseStatus = response.status
      console.log(`🔍 API響應狀態: ${response.status} (耗時: ${(endTime - startTime).toFixed(2)}ms)`)
      
      if (!response.ok) {
        const errorText = await response.text()
        console.error(`🔍 API請求失敗: ${response.status} - ${errorText}`)
        debugInfo.responseData = { error: errorText }
        debugInfo.satelliteCount = 0
        debugInfo.analysisResult = {
          issue: 'API請求失敗',
          possibleCauses: [
            '後端服務未運行',
            'API端點不存在',
            '網路連接問題',
            '後端內部錯誤'
          ],
          recommendations: [
            '檢查Docker容器狀態',
            '檢查後端日誌',
            '驗證API路由配置',
            '檢查網路連接'
          ]
        }
        return debugInfo as SatelliteDebugInfo
      }
      
      // 解析響應數據
      const responseData = await response.json()
      debugInfo.responseData = responseData
      
      console.log(`🔍 API響應數據:`, responseData)
      console.log(`🔍 響應結構分析:`, {
        hasData: !!responseData,
        responseKeys: responseData ? Object.keys(responseData) : [],
        hasSatellites: !!responseData.satellites,
        satellitesType: typeof responseData.satellites,
        satellitesLength: responseData.satellites?.length,
        isArray: Array.isArray(responseData.satellites),
        status: responseData.status,
        processed: responseData.processed,
        visible: responseData.visible,
        error: responseData.error
      })
      
      // 分析衛星數據
      const satelliteCount = responseData.satellites?.length || 0
      debugInfo.satelliteCount = satelliteCount
      
      console.log(`🔍 全球視野模式獲得衛星數量: ${satelliteCount}`)
      
      if (responseData.satellites && responseData.satellites.length > 0) {
        console.log(`🔍 前5顆衛星詳細信息:`)
        responseData.satellites.slice(0, 5).forEach((sat: any, index: number) => {
          console.log(`  ${index + 1}. ${sat.name} (ID: ${sat.norad_id})`)
          console.log(`     - 仰角: ${sat.elevation_deg}°`)
          console.log(`     - 方位角: ${sat.azimuth_deg}°`)
          console.log(`     - 距離: ${sat.distance_km}km`)
          console.log(`     - 軌道高度: ${sat.orbit_altitude_km}km`)
        })
        
        // 🌍 分析衛星分布以確認是否為全球視野
        const elevations = responseData.satellites.map((sat: any) => sat.elevation_deg || 0)
        const avgElevation = elevations.reduce((sum: number, el: number) => sum + el, 0) / elevations.length
        const minElevation = Math.min(...elevations)
        const maxElevation = Math.max(...elevations)
        
        console.log(`🌍 衛星仰角分布分析:`)
        console.log(`   - 平均仰角: ${avgElevation.toFixed(2)}°`)
        console.log(`   - 最低仰角: ${minElevation.toFixed(2)}°`)
        console.log(`   - 最高仰角: ${maxElevation.toFixed(2)}°`)
        console.log(`   - 仰角範圍: ${(maxElevation - minElevation).toFixed(2)}°`)
        
        if (minElevation > 10) {
          console.warn(`🌍 最低仰角 ${minElevation.toFixed(2)}° 較高，可能仍有較嚴格的仰角限制`)
        }
      }
      
      // 🌍 更新問題分析邏輯，考慮全球視野
      let issue = ''
      let possibleCauses: string[] = []
      let recommendations: string[] = []
      
      if (satelliteCount === 0) {
        issue = '全球視野模式無衛星數據'
        possibleCauses = [
          '後端TLE資料庫完全為空',
          'Skyfield初始化完全失敗', 
          '後端未正確實現全球視野模式',
          'API路由配置錯誤',
          '資料庫連接問題'
        ]
        recommendations = [
          '檢查後端衛星數據初始化日誌',
          '驗證TLE數據源和載入過程',
          '確認後端實現了真正的全球視野算法',
          '檢查資料庫連接和衛星數據表',
          '測試後端Skyfield庫配置'
        ]
        
        // 檢查後端處理統計
        if (responseData.processed !== undefined && responseData.visible !== undefined) {
          console.log(`🔍 後端處理統計: 處理了${responseData.processed}顆衛星，${responseData.visible}顆可見`)
          if (responseData.processed > 0 && responseData.visible === 0) {
            possibleCauses.unshift('後端算法將所有衛星都標記為不可見')
            recommendations.unshift('檢查後端可見性判斷邏輯，確保全球視野模式')
          } else if (responseData.processed === 0) {
            possibleCauses.unshift('後端衛星數據庫為空或未正確載入')
            recommendations.unshift('重新初始化後端衛星數據庫')
          }
        }
        
      } else if (satelliteCount < 2) {
        issue = '全球視野模式衛星數量異常偏少'
        possibleCauses = [
          '後端仍在使用地域限制邏輯',
          'TLE數據庫衛星數量本身就很少',
          '後端global_view參數未生效',
          '仰角限制仍然過於嚴格',
          '後端只載入了部分衛星星座'
        ]
        recommendations = [
          '檢查後端是否真正實現了全球視野',
          '確認後端忽略觀測點座標限制',
          '檢查TLE數據庫的衛星總數',
          '驗證後端Starlink/Kuiper數據載入',
          '測試極低仰角(-45度)參數'
        ]
      } else {
        // 2顆以上衛星屬於正常範圍，根據真實軌道位置和時間變化
        issue = '衛星數據正常'
        possibleCauses = [
          '當前時間和觀測位置的真實衛星分布',
          '衛星軌道運動導致的自然變化',
          '基於實際TLE數據的準確計算'
        ]
        recommendations = [
          '數據充足，可以正常使用',
          '衛星數量會隨時間自然變化',
          '如需更多衛星可調整仰角或時間'
        ]
      }
      
      debugInfo.analysisResult = {
        issue,
        possibleCauses,
        recommendations
      }
      
      // 只在真正有問題時輸出分析結果
      if (satelliteCount < 2) {
        console.log(`🔍 全球視野模式問題分析結果:`)
        console.log(`   問題: ${issue}`)
        console.log(`   可能原因:`, possibleCauses)
        console.log(`   建議解決方案:`, recommendations)
      } else {
        console.log(`✅ 衛星數據正常: ${satelliteCount} 顆衛星可用`)
      }
      
      return debugInfo as SatelliteDebugInfo
      
    } catch (error) {
      console.error(`🔍 全球視野調試過程中發生錯誤:`, error)
      debugInfo.responseStatus = 0
      debugInfo.responseData = { error: error.message }
      debugInfo.satelliteCount = 0
      debugInfo.analysisResult = {
        issue: '全球視野調試過程異常',
        possibleCauses: [
          '網路連接失敗',
          'JavaScript執行錯誤',
          '瀏覽器安全限制',
          'API代理配置問題',
          '後端全球視野模式實現錯誤'
        ],
        recommendations: [
          '檢查瀏覽器開發者工具Network標籤',
          '確認Vite代理配置',
          '檢查CORS設置',
          '重新啟動前端開發服務器',
          '驗證後端全球視野模式實現'
        ]
      }
      return debugInfo as SatelliteDebugInfo
    }
  }
  
  /**
   * 快速檢測API連通性
   */
  static async quickHealthCheck(): Promise<boolean> {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 3000)
      
      const response = await fetch('/api/v1/satellite-ops/visible_satellites?count=1&global_view=true', {
        method: 'GET',
        signal: controller.signal
      })
      
      clearTimeout(timeoutId)
      return response.ok
    } catch {
      return false
    }
  }
  
  /**
   * 生成調試報告
   */
  static generateDebugReport(debugInfo: SatelliteDebugInfo): string {
    return `
=== 衛星API調試報告 ===
時間: ${new Date().toISOString()}

API測試:
- URL: ${debugInfo.apiUrl}
- 參數: ${JSON.stringify(debugInfo.params, null, 2)}
- 響應狀態: ${debugInfo.responseStatus}
- 衛星數量: ${debugInfo.satelliteCount}

問題分析:
- 主要問題: ${debugInfo.analysisResult.issue}
- 可能原因: ${debugInfo.analysisResult.possibleCauses.join(', ')}
- 解決建議: ${debugInfo.analysisResult.recommendations.join(', ')}

響應數據:
${JSON.stringify(debugInfo.responseData, null, 2)}

========================
    `.trim()
  }
}

// 導出給控制台使用的全局函數
if (typeof window !== 'undefined') {
  (window as any).debugSatelliteAPI = SatelliteDebugger.debugSatelliteAPI.bind(SatelliteDebugger)
  (window as any).satelliteHealthCheck = SatelliteDebugger.quickHealthCheck.bind(SatelliteDebugger)
}
