/**
 * TLE 數據 API 路由
 * 
 * 提供 TLE 數據的 REST API 端點：
 * 1. GET /api/tle/constellations - 獲取支持的星座列表
 * 2. GET /api/tle/{constellation}/latest - 獲取最新 TLE 數據
 * 3. GET /api/tle/{constellation}/stats - 獲取星座統計信息
 * 4. GET /api/tle/historical/{timestamp} - 獲取歷史 TLE 數據
 * 5. POST /api/tle/cache/preload - 預載推薦時段數據
 */

import { Router, Request, Response } from 'express'
import { TLEDataService } from '../services/TLEDataService'
import { HistoricalDataCache } from '../services/HistoricalDataCache'
import { createLogger } from '../utils/logger'

const router = Router()
const logger = createLogger('TLERouter')

// 服務實例
const tleService = new TLEDataService()
const historicalCache = new HistoricalDataCache(tleService)

/**
 * 獲取支持的星座列表
 */
router.get('/constellations', async (req: Request, res: Response) => {
  try {
    const constellations = tleService.getSupportedConstellations()
    
    res.json({
      success: true,
      data: constellations,
      timestamp: new Date().toISOString()
    })
  } catch (error) {
    logger.error('獲取星座列表失敗', { error })
    res.status(500).json({
      success: false,
      error: '獲取星座列表失敗',
      message: error instanceof Error ? error.message : '未知錯誤'
    })
  }
})

/**
 * 獲取指定星座的最新 TLE 數據
 */
router.get('/:constellation/latest', async (req: Request, res: Response) => {
  try {
    const { constellation } = req.params
    const limit = parseInt(req.query.limit as string) || 100
    
    logger.info('獲取最新 TLE 數據', { constellation, limit })
    
    const tleData = await tleService.fetchTLEFromSource(constellation)
    
    // 限制返回數量
    const limitedData = tleData.slice(0, limit)
    
    res.json({
      success: true,
      data: {
        constellation,
        satelliteCount: tleData.length,
        returnedCount: limitedData.length,
        satellites: limitedData,
        lastUpdated: limitedData[0]?.lastUpdated || null
      },
      timestamp: new Date().toISOString()
    })
  } catch (error) {
    logger.error('獲取最新 TLE 數據失敗', { error, constellation: req.params.constellation })
    res.status(500).json({
      success: false,
      error: '獲取 TLE 數據失敗',
      message: error instanceof Error ? error.message : '未知錯誤'
    })
  }
})

/**
 * 獲取星座統計信息
 */
router.get('/:constellation/stats', async (req: Request, res: Response) => {
  try {
    const { constellation } = req.params
    
    logger.info('獲取星座統計信息', { constellation })
    
    const stats = await tleService.getConstellationStats(constellation)
    
    res.json({
      success: true,
      data: {
        constellation,
        ...stats
      },
      timestamp: new Date().toISOString()
    })
  } catch (error) {
    logger.error('獲取星座統計信息失敗', { error, constellation: req.params.constellation })
    res.status(500).json({
      success: false,
      error: '獲取星座統計信息失敗',
      message: error instanceof Error ? error.message : '未知錯誤'
    })
  }
})

/**
 * 獲取歷史 TLE 數據
 */
router.get('/historical/:timestamp', async (req: Request, res: Response) => {
  try {
    const { timestamp } = req.params
    const constellation = req.query.constellation as string || 'starlink'
    
    const targetTime = new Date(timestamp)
    if (isNaN(targetTime.getTime())) {
      return res.status(400).json({
        success: false,
        error: '無效的時間格式',
        message: '請使用 ISO 8601 格式，例如: 2024-01-01T00:00:00Z'
      })
    }
    
    logger.info('獲取歷史 TLE 數據', { constellation, timestamp: targetTime })
    
    const historicalData = await historicalCache.getHistoricalTLE(constellation, targetTime)
    
    if (!historicalData) {
      return res.status(404).json({
        success: false,
        error: '未找到歷史數據',
        message: `未找到 ${constellation} 在 ${targetTime.toISOString()} 的歷史數據`
      })
    }
    
    res.json({
      success: true,
      data: {
        constellation,
        requestedTime: targetTime.toISOString(),
        actualTime: historicalData.timestamp.toISOString(),
        satelliteCount: historicalData.satellites.length,
        dataSource: historicalData.dataSource,
        quality: historicalData.quality,
        satellites: historicalData.satellites.slice(0, 50) // 限制返回數量
      },
      timestamp: new Date().toISOString()
    })
  } catch (error) {
    logger.error('獲取歷史 TLE 數據失敗', { error, timestamp: req.params.timestamp })
    res.status(500).json({
      success: false,
      error: '獲取歷史數據失敗',
      message: error instanceof Error ? error.message : '未知錯誤'
    })
  }
})

/**
 * 獲取歷史數據範圍
 */
router.get('/historical-range/:constellation', async (req: Request, res: Response) => {
  try {
    const { constellation } = req.params
    const { start, end, limit } = req.query
    
    if (!start || !end) {
      return res.status(400).json({
        success: false,
        error: '缺少必要參數',
        message: '請提供 start 和 end 時間參數'
      })
    }
    
    const startTime = new Date(start as string)
    const endTime = new Date(end as string)
    const maxRecords = parseInt(limit as string) || 100
    
    if (isNaN(startTime.getTime()) || isNaN(endTime.getTime())) {
      return res.status(400).json({
        success: false,
        error: '無效的時間格式',
        message: '請使用 ISO 8601 格式'
      })
    }
    
    logger.info('獲取歷史數據範圍', { constellation, startTime, endTime, maxRecords })
    
    const historicalData = await historicalCache.getHistoricalTLERange(
      constellation,
      { start: startTime, end: endTime },
      maxRecords
    )
    
    res.json({
      success: true,
      data: {
        constellation,
        timeRange: {
          start: startTime.toISOString(),
          end: endTime.toISOString()
        },
        recordCount: historicalData.length,
        records: historicalData.map(record => ({
          timestamp: record.timestamp.toISOString(),
          satelliteCount: record.satellites.length,
          dataSource: record.dataSource,
          quality: record.quality
        }))
      },
      timestamp: new Date().toISOString()
    })
  } catch (error) {
    logger.error('獲取歷史數據範圍失敗', { error })
    res.status(500).json({
      success: false,
      error: '獲取歷史數據範圍失敗',
      message: error instanceof Error ? error.message : '未知錯誤'
    })
  }
})

/**
 * 預載推薦時段數據
 */
router.post('/cache/preload', async (req: Request, res: Response) => {
  try {
    const { constellation } = req.body
    const targetConstellation = constellation || 'starlink'
    
    logger.info('開始預載推薦時段數據', { constellation: targetConstellation })
    
    // 異步執行預載，不阻塞響應
    historicalCache.preloadRecommendedTimeRanges(targetConstellation)
      .then(() => {
        logger.info('推薦時段數據預載完成', { constellation: targetConstellation })
      })
      .catch((error) => {
        logger.error('推薦時段數據預載失敗', { error, constellation: targetConstellation })
      })
    
    res.json({
      success: true,
      message: '預載任務已啟動',
      data: {
        constellation: targetConstellation,
        timeRanges: Object.keys(HistoricalDataCache.RECOMMENDED_TIME_RANGES)
      },
      timestamp: new Date().toISOString()
    })
  } catch (error) {
    logger.error('啟動預載任務失敗', { error })
    res.status(500).json({
      success: false,
      error: '啟動預載任務失敗',
      message: error instanceof Error ? error.message : '未知錯誤'
    })
  }
})

/**
 * 獲取緩存統計信息
 */
router.get('/cache/stats', async (req: Request, res: Response) => {
  try {
    const stats = await historicalCache.getCacheStats()
    
    res.json({
      success: true,
      data: stats,
      timestamp: new Date().toISOString()
    })
  } catch (error) {
    logger.error('獲取緩存統計失敗', { error })
    res.status(500).json({
      success: false,
      error: '獲取緩存統計失敗',
      message: error instanceof Error ? error.message : '未知錯誤'
    })
  }
})

export default router
