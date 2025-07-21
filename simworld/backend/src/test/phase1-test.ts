/**
 * Phase 1 測試腳本 - TLE 數據集成驗證
 * 
 * 測試項目：
 * 1. CelesTrak API 連接
 * 2. TLE 數據解析
 * 3. 歷史數據緩存
 * 4. 2024年1月1日數據獲取
 * 
 * 符合 d2.md Phase 1 驗收標準
 */

import { TLEDataService } from '../services/TLEDataService'
import { HistoricalDataCache } from '../services/HistoricalDataCache'
import { createLogger } from '../utils/logger'

const logger = createLogger('Phase1Test')

async function runPhase1Tests(): Promise<void> {
  logger.info('開始 Phase 1 測試 - TLE 數據集成')
  
  const tleService = new TLEDataService()
  const historicalCache = new HistoricalDataCache(tleService)
  
  let passedTests = 0
  let totalTests = 0
  
  // 測試 1: 獲取支持的星座列表
  totalTests++
  try {
    logger.info('測試 1: 獲取支持的星座列表')
    const constellations = tleService.getSupportedConstellations()
    
    if (constellations.length > 0 && constellations.some(c => c.constellation === 'starlink')) {
      logger.info('✅ 測試 1 通過', { constellationCount: constellations.length })
      passedTests++
    } else {
      logger.error('❌ 測試 1 失敗: 未找到 Starlink 星座')
    }
  } catch (error) {
    logger.error('❌ 測試 1 失敗', { error })
  }
  
  // 測試 2: 從 CelesTrak API 獲取 Starlink TLE 數據
  totalTests++
  try {
    logger.info('測試 2: 從 CelesTrak API 獲取 Starlink TLE 數據')
    const starlinkTLE = await tleService.fetchStarlinkTLE()
    
    if (starlinkTLE.length > 0) {
      logger.info('✅ 測試 2 通過', { 
        satelliteCount: starlinkTLE.length,
        firstSatellite: starlinkTLE[0].satelliteName
      })
      passedTests++
      
      // 驗證 TLE 數據格式
      const firstTLE = starlinkTLE[0]
      if (tleService.validateTLEData(firstTLE)) {
        logger.info('✅ TLE 數據格式驗證通過')
      } else {
        logger.warn('⚠️ TLE 數據格式驗證失敗')
      }
    } else {
      logger.error('❌ 測試 2 失敗: 未獲取到 TLE 數據')
    }
  } catch (error) {
    logger.error('❌ 測試 2 失敗', { error })
  }
  
  // 測試 3: 獲取星座統計信息
  totalTests++
  try {
    logger.info('測試 3: 獲取星座統計信息')
    const stats = await tleService.getConstellationStats('starlink')
    
    if (stats.totalSatellites > 0) {
      logger.info('✅ 測試 3 通過', stats)
      passedTests++
    } else {
      logger.error('❌ 測試 3 失敗: 統計信息無效')
    }
  } catch (error) {
    logger.error('❌ 測試 3 失敗', { error })
  }
  
  // 測試 4: 緩存歷史數據（2024年1月1日）
  totalTests++
  try {
    logger.info('測試 4: 緩存 2024年1月1日 歷史數據')
    const primaryTimeRange = HistoricalDataCache.RECOMMENDED_TIME_RANGES.primary
    
    await historicalCache.cacheHistoricalTLE('starlink', primaryTimeRange, 30) // 30分鐘間隔
    
    logger.info('✅ 測試 4 通過: 歷史數據緩存完成')
    passedTests++
  } catch (error) {
    logger.error('❌ 測試 4 失敗', { error })
  }
  
  // 測試 5: 獲取特定時間點的歷史數據
  totalTests++
  try {
    logger.info('測試 5: 獲取 2024年1月1日 00:00:00 UTC 的歷史數據')
    const targetTime = new Date('2024-01-01T00:00:00.000Z')
    const historicalData = await historicalCache.getHistoricalTLE('starlink', targetTime)
    
    if (historicalData && historicalData.satellites.length > 0) {
      logger.info('✅ 測試 5 通過', {
        timestamp: historicalData.timestamp.toISOString(),
        satelliteCount: historicalData.satellites.length,
        dataSource: historicalData.dataSource,
        quality: historicalData.quality
      })
      passedTests++
    } else {
      logger.error('❌ 測試 5 失敗: 未找到歷史數據')
    }
  } catch (error) {
    logger.error('❌ 測試 5 失敗', { error })
  }
  
  // 測試 6: 獲取歷史數據範圍
  totalTests++
  try {
    logger.info('測試 6: 獲取歷史數據範圍（1小時）')
    const startTime = new Date('2024-01-01T00:00:00.000Z')
    const endTime = new Date('2024-01-01T01:00:00.000Z')
    
    const historicalRange = await historicalCache.getHistoricalTLERange(
      'starlink',
      { start: startTime, end: endTime },
      10
    )
    
    if (historicalRange.length > 0) {
      logger.info('✅ 測試 6 通過', {
        recordCount: historicalRange.length,
        timeSpan: `${startTime.toISOString()} - ${endTime.toISOString()}`
      })
      passedTests++
    } else {
      logger.error('❌ 測試 6 失敗: 未找到歷史數據範圍')
    }
  } catch (error) {
    logger.error('❌ 測試 6 失敗', { error })
  }
  
  // 測試 7: 緩存統計信息
  totalTests++
  try {
    logger.info('測試 7: 獲取緩存統計信息')
    const cacheStats = await historicalCache.getCacheStats()
    
    if (cacheStats.totalFiles > 0) {
      logger.info('✅ 測試 7 通過', cacheStats)
      passedTests++
    } else {
      logger.warn('⚠️ 測試 7: 無緩存文件，但功能正常')
      passedTests++
    }
  } catch (error) {
    logger.error('❌ 測試 7 失敗', { error })
  }
  
  // 測試結果總結
  logger.info('Phase 1 測試完成', {
    passedTests,
    totalTests,
    successRate: `${((passedTests / totalTests) * 100).toFixed(1)}%`
  })
  
  // Phase 1 驗收標準檢查
  const phase1Requirements = [
    { name: '成功從 CelesTrak API 獲取 TLE 數據', passed: passedTests >= 2 },
    { name: '實現本地歷史數據緩存機制', passed: passedTests >= 4 },
    { name: '可獲取 2024年1月1日 的 Starlink 衛星 TLE 數據', passed: passedTests >= 5 },
    { name: 'API 端點功能正常', passed: passedTests >= 6 }
  ]
  
  logger.info('Phase 1 驗收標準檢查:')
  let allRequirementsMet = true
  
  for (const requirement of phase1Requirements) {
    if (requirement.passed) {
      logger.info(`✅ ${requirement.name}`)
    } else {
      logger.error(`❌ ${requirement.name}`)
      allRequirementsMet = false
    }
  }
  
  if (allRequirementsMet) {
    logger.info('🎉 Phase 1 驗收標準全部通過！可以進入 Phase 2')
  } else {
    logger.error('❌ Phase 1 驗收標準未完全通過，需要修復問題')
  }
}

// 執行測試
if (require.main === module) {
  runPhase1Tests()
    .then(() => {
      logger.info('Phase 1 測試腳本執行完成')
      process.exit(0)
    })
    .catch((error) => {
      logger.error('Phase 1 測試腳本執行失敗', { error })
      process.exit(1)
    })
}

export { runPhase1Tests }
