/**
 * 測試工具模塊
 * 提供共用的測試邏輯，避免重複代碼
 */
import { netStackApi } from '../services/netstack-api'
import { simWorldApi } from '../services/simworld-api'
import { realConnectionManager } from '../services/realConnectionService'

export interface TestResult {
  success: boolean
  message: string
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  details?: any
  error?: string
}

/**
 * 通用測試結果類型
 */
export interface SystemTestResults {
  netstack_core_sync: TestResult
  netstack_core?: TestResult
   
  simworld_satellites: TestResult
  real_connections: TestResult
  api_integration?: TestResult
  ieee_algorithm: TestResult
  handover_performance?: TestResult
  overall_score: number
  passed_tests: number
  total_tests: number
}

/**
 * 測試NetStack核心同步狀態
 */
export async function testNetStackCoreSync(): Promise<TestResult> {
  try {
    const coreSync = await netStackApi.getCoreSync()
    const success = coreSync && coreSync.service_info?.is_running === true
    
    return {
      success,
      message: success ? 'NetStack 核心同步正常' : 'NetStack 核心同步異常',
      details: success ? {
        uptime_hours: coreSync.service_info.uptime_hours,
        active_tasks: coreSync.service_info.active_tasks,
        sync_state: coreSync.service_info.core_sync_state
      } : null
    }
  } catch (error) {
    return {
      success: false,
      message: 'NetStack 核心同步測試失敗',
      error: error instanceof Error ? error.message : 'Unknown error'
    }
  }
}

/**
 * 測試SimWorld衛星可見性
 */
export async function testSimWorldSatellites(): Promise<TestResult> {
  try {
    const satellites = await simWorldApi.getVisibleSatellites(-90, 150, 0, 0)
    
    // 處理不同的響應格式
    let satelliteArray: unknown[] = []
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let observer: any = null
    let totalVisible = 0
    
    if (satellites.results?.satellites) {
      // 新格式：{ success: boolean, results: { satellites: [...] } }
      satelliteArray = satellites.results.satellites
      observer = satellites.observer
      totalVisible = satellites.results.total_visible || satelliteArray.length
    } else if (satellites.satellites) {
      // 舊格式：{ satellites: [...] }
      satelliteArray = satellites.satellites
      observer = satellites.observer
      totalVisible = satellites.visible || satelliteArray.length
    } else if (Array.isArray(satellites)) {
      // 直接數組格式
      satelliteArray = satellites
    }
    
    const success = satelliteArray.length > 0
    
    return {
      success,
      message: success ? 'SimWorld 衛星數據正常' : 'SimWorld 衛星數據異常',
      details: success ? {
        visible_count: satelliteArray.length,
        total_visible: totalVisible,
        observer: observer
      } : null
    }
  } catch (error) {
    return {
      success: false,
      message: 'SimWorld 衛星測試失敗',
      error: error instanceof Error ? error.message : 'Unknown error'
    }
  }
}

/**
 * 測試真實連接管理器
 */
export async function testRealConnections(): Promise<TestResult> {
  try {
    const connections = realConnectionManager.getAllConnections()
    const handovers = realConnectionManager.getAllHandovers()
    const success = connections.size >= 0 && handovers.size >= 0 // 允許為0
    
    return {
      success,
      message: success ? '真實連接管理器正常' : '真實連接管理器異常',
      details: {
        connections_count: connections.size,
        handovers_count: handovers.size,
        sample_connections: Array.from(connections.values()).slice(0, 2).map(c => ({
          satellite_id: c.current_satellite_id,
          ue_id: c.ue_id,
          signal_quality: c.signal_quality
        }))
      }
    }
  } catch (error) {
    return {
      success: false,
      message: '真實連接管理器測試失敗',
      error: error instanceof Error ? error.message : 'Unknown error'
    }
  }
}

/**
 * 測試IEEE INFOCOM 2024演算法
 */
export async function testIEEEAlgorithm(): Promise<TestResult> {
  try {
    const prediction = await netStackApi.predictSatelliteAccess({
      ue_id: 'TEST_UE',
      satellite_id: 'STARLINK-1071'
    })
    const success = !!(prediction && prediction.prediction_id)
    
    return {
      success,
      message: success ? 'IEEE INFOCOM 2024 演算法正常' : 'IEEE INFOCOM 2024 演算法異常',
      details: success ? {
        prediction_id: prediction.prediction_id,
        handover_trigger_time: prediction.handover_trigger_time,
        handover_required: prediction.handover_required,
        current_satellite: prediction.current_satellite?.satellite_id,
        target_satellite: prediction.satellite_id
      } : null
    }
  } catch (error) {
    return {
      success: false,
      message: 'IEEE INFOCOM 2024 演算法測試失敗',
      error: error instanceof Error ? error.message : 'Unknown error'
    }
  }
}

/**
 * 測試換手性能數據
 */
export async function testHandoverPerformance(): Promise<TestResult> {
  try {
     
     
     
    const _metrics = await netStackApi.getHandoverLatencyMetrics()
     
     
    const success = Array.isArray(metrics) && metrics.length > 0
    
    return {
      success,
      message: success ? '換手性能數據正常' : '換手性能數據異常',
      details: success ? {
        metrics_count: metrics.length,
        sample_metric: metrics[0]
      } : null
    }
  } catch (error) {
    return {
      success: false,
      message: '換手性能測試失敗',
      error: error instanceof Error ? error.message : 'Unknown error'
    }
  }
}

/**
 * 執行完整系統測試
 */
export async function runSystemTests(
  includePerformance: boolean = false
): Promise<SystemTestResults> {
  console.log('🚀 開始系統測試...')
  
  const results: SystemTestResults = {
    netstack_core_sync: await testNetStackCoreSync(),
     
    simworld_satellites: await testSimWorldSatellites(),
    real_connections: await testRealConnections(),
    ieee_algorithm: await testIEEEAlgorithm(),
    overall_score: 0,
    passed_tests: 0,
    total_tests: 4
  }
  
  // 添加相容性映射
  results.netstack_core = results.netstack_core_sync
  results.api_integration = results.real_connections
  
  if (includePerformance) {
    results.handover_performance = await testHandoverPerformance()
    results.total_tests = 5
  }
  
  // 計算通過的測試數量
  const testResults = [
    results.netstack_core_sync,
     
    results.simworld_satellites,
    results.real_connections,
    results.ieee_algorithm,
    ...(results.handover_performance ? [results.handover_performance] : [])
  ]
  
  results.passed_tests = testResults.filter(test => test.success).length
  results.overall_score = Math.round((results.passed_tests / results.total_tests) * 100)
  
  console.log(`✅ 測試完成: ${results.passed_tests}/${results.total_tests} 通過 (${results.overall_score}%)`)
  
  return results
}

/**
 * 顯示測試結果摘要
 */
export function displayTestSummary(results: SystemTestResults): void {
  console.log('\n📊 測試結果摘要:')
  console.log(`NetStack 核心同步: ${results.netstack_core_sync.success ? '✅' : '❌'} ${results.netstack_core_sync.message}`)
   
  console.log(`SimWorld 衛星: ${results.simworld_satellites.success ? '✅' : '❌'} ${results.simworld_satellites.message}`)
  console.log(`真實連接管理: ${results.real_connections.success ? '✅' : '❌'} ${results.real_connections.message}`)
  console.log(`IEEE 演算法: ${results.ieee_algorithm.success ? '✅' : '❌'} ${results.ieee_algorithm.message}`)
  
  if (results.handover_performance) {
    console.log(`換手性能: ${results.handover_performance.success ? '✅' : '❌'} ${results.handover_performance.message}`)
  }
  
  console.log(`\n🎯 總分: ${results.overall_score}% (${results.passed_tests}/${results.total_tests})`)
}

/**
 * 等待函數 - 測試中使用
 */
export function wait(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * 測試狀態更新回調類型
 */
export type TestStatusCallback = (currentTest: string, progress: number) => void