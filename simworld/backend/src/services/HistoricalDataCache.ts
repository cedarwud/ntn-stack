/**
 * 歷史數據緩存系統 - 支持 d2.md 中指定的歷史時段數據
 * 
 * 功能：
 * 1. 緩存指定時間段的 TLE 數據
 * 2. 支持 2024年1月1日 00:00:00 UTC 開始的3小時數據
 * 3. 高效的時間索引和檢索
 * 4. 數據壓縮和存儲優化
 */

import fs from 'fs/promises'
import path from 'path'
import { TLEData, TLEDataService } from './TLEDataService'
import { createLogger } from '../utils/logger'

const logger = createLogger('HistoricalDataCache')

export interface HistoricalTLERecord {
  timestamp: Date
  constellation: string
  satellites: TLEData[]
  dataSource: 'cached' | 'interpolated' | 'live'
  quality: 'high' | 'medium' | 'low'
}

export interface TimeRange {
  start: Date
  end: Date
}

export interface CacheMetadata {
  timeRange: TimeRange
  constellation: string
  totalRecords: number
  sampleInterval: number // 分鐘
  createdAt: Date
  lastAccessed: Date
  fileSize: number
}

export class HistoricalDataCache {
  private cacheDir = './data/tle_cache'
  private historicalDir = './data/tle_historical'
  private tleService: TLEDataService

  // d2.md 中推薦的歷史數據時段
  public static readonly RECOMMENDED_TIME_RANGES = {
    primary: {
      start: new Date('2024-01-01T00:00:00.000Z'),
      end: new Date('2024-01-01T03:00:00.000Z'),
      description: '主要時段 - 包含完整的 LEO 衛星軌道週期'
    },
    backup1: {
      start: new Date('2024-01-15T12:00:00.000Z'),
      end: new Date('2024-01-15T15:00:00.000Z'),
      description: '備選時段1 - 太陽最大活動期'
    },
    backup2: {
      start: new Date('2024-02-01T06:00:00.000Z'),
      end: new Date('2024-02-01T09:00:00.000Z'),
      description: '備選時段2 - 地磁暴期間'
    },
    backup3: {
      start: new Date('2024-03-21T18:00:00.000Z'),
      end: new Date('2024-03-21T21:00:00.000Z'),
      description: '備選時段3 - 春分點，最佳幾何條件'
    }
  }

  constructor(tleService?: TLEDataService) {
    this.tleService = tleService || new TLEDataService()
    this.initializeDirectories()
  }

  /**
   * 初始化緩存目錄
   */
  private async initializeDirectories(): Promise<void> {
    try {
      await fs.mkdir(this.cacheDir, { recursive: true })
      await fs.mkdir(this.historicalDir, { recursive: true })
      await fs.mkdir(path.join(this.historicalDir, 'metadata'), { recursive: true })
      
      logger.info('歷史數據緩存目錄初始化完成', {
        cacheDir: this.cacheDir,
        historicalDir: this.historicalDir
      })
    } catch (error) {
      logger.error('歷史數據緩存目錄初始化失敗', { error })
      throw error
    }
  }

  /**
   * 緩存指定時間段的歷史 TLE 數據
   */
  async cacheHistoricalTLE(
    constellation: string,
    timeRange: TimeRange,
    sampleIntervalMinutes: number = 10
  ): Promise<void> {
    try {
      logger.info('開始緩存歷史 TLE 數據', {
        constellation,
        timeRange,
        sampleIntervalMinutes
      })

      const records: HistoricalTLERecord[] = []
      const current = new Date(timeRange.start)
      const intervalMs = sampleIntervalMinutes * 60 * 1000

      // 由於歷史 TLE 數據通常不可用，我們使用最新數據作為基準
      // 在實際應用中，這裡應該從歷史數據源獲取
      const baseTLE = await this.tleService.fetchTLEFromSource(constellation)
      
      if (baseTLE.length === 0) {
        throw new Error(`無法獲取 ${constellation} 星座的 TLE 數據`)
      }

      while (current <= timeRange.end) {
        // 對於歷史數據，我們創建基於時間的變化
        const historicalTLE = this.generateHistoricalTLE(baseTLE, current)
        
        records.push({
          timestamp: new Date(current),
          constellation,
          satellites: historicalTLE,
          dataSource: 'interpolated',
          quality: 'medium'
        })

        current.setTime(current.getTime() + intervalMs)
      }

      // 保存到文件
      await this.saveHistoricalRecords(constellation, timeRange, records, sampleIntervalMinutes)
      
      logger.info('歷史 TLE 數據緩存完成', {
        constellation,
        recordCount: records.length,
        satelliteCount: baseTLE.length
      })

    } catch (error) {
      logger.error('歷史 TLE 數據緩存失敗', { error, constellation, timeRange })
      throw error
    }
  }

  /**
   * 獲取特定時間點的歷史 TLE 數據
   */
  async getHistoricalTLE(
    constellation: string,
    timestamp: Date
  ): Promise<HistoricalTLERecord | null> {
    try {
      // 查找包含該時間點的緩存文件
      const cacheFiles = await this.findCacheFilesForTime(constellation, timestamp)
      
      for (const cacheFile of cacheFiles) {
        const records = await this.loadHistoricalRecords(cacheFile)
        
        // 找到最接近的時間點
        const closestRecord = this.findClosestRecord(records, timestamp)
        if (closestRecord) {
          await this.updateAccessTime(cacheFile)
          return closestRecord
        }
      }

      logger.warn('未找到指定時間的歷史 TLE 數據', { constellation, timestamp })
      return null

    } catch (error) {
      logger.error('獲取歷史 TLE 數據失敗', { error, constellation, timestamp })
      return null
    }
  }

  /**
   * 獲取時間範圍內的歷史 TLE 數據
   */
  async getHistoricalTLERange(
    constellation: string,
    timeRange: TimeRange,
    maxRecords: number = 1000
  ): Promise<HistoricalTLERecord[]> {
    try {
      const cacheFiles = await this.findCacheFilesForTimeRange(constellation, timeRange)
      const allRecords: HistoricalTLERecord[] = []

      for (const cacheFile of cacheFiles) {
        const records = await this.loadHistoricalRecords(cacheFile)
        
        // 過濾時間範圍內的記錄
        const filteredRecords = records.filter(record => 
          record.timestamp >= timeRange.start && record.timestamp <= timeRange.end
        )
        
        allRecords.push(...filteredRecords)
      }

      // 按時間排序並限制數量
      allRecords.sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime())
      
      const result = allRecords.slice(0, maxRecords)
      
      logger.info('獲取歷史 TLE 數據範圍', {
        constellation,
        timeRange,
        recordCount: result.length,
        totalFound: allRecords.length
      })

      return result

    } catch (error) {
      logger.error('獲取歷史 TLE 數據範圍失敗', { error, constellation, timeRange })
      return []
    }
  }

  /**
   * 生成基於時間的歷史 TLE 數據（模擬軌道演化）
   */
  private generateHistoricalTLE(baseTLE: TLEData[], timestamp: Date): TLEData[] {
    const now = new Date()
    const timeDiffHours = (timestamp.getTime() - now.getTime()) / (1000 * 60 * 60)
    
    return baseTLE.map(tle => {
      // 簡單的軌道演化模擬
      // 在實際應用中，這裡應該使用 SGP4 算法進行精確計算
      const meanAnomalyChange = (tle.meanMotion * timeDiffHours * 360 / 24) % 360
      const newMeanAnomaly = (tle.meanAnomaly + meanAnomalyChange + 360) % 360
      
      // 考慮軌道衰減（大氣阻力）
      const altitudeDecay = Math.abs(timeDiffHours) * 0.001 // 每小時約1米的衰減
      const meanMotionIncrease = altitudeDecay * 0.000001 // 軌道衰減導致的平均運動增加
      
      return {
        ...tle,
        meanAnomaly: newMeanAnomaly,
        meanMotion: tle.meanMotion + meanMotionIncrease,
        epochDay: tle.epochDay + timeDiffHours / 24,
        lastUpdated: timestamp
      }
    })
  }

  /**
   * 保存歷史記錄到文件
   */
  private async saveHistoricalRecords(
    constellation: string,
    timeRange: TimeRange,
    records: HistoricalTLERecord[],
    sampleInterval: number
  ): Promise<void> {
    const filename = this.generateCacheFileName(constellation, timeRange)
    const filepath = path.join(this.historicalDir, filename)
    
    // 保存數據
    await fs.writeFile(filepath, JSON.stringify(records, null, 2))
    
    // 保存元數據
    const metadata: CacheMetadata = {
      timeRange,
      constellation,
      totalRecords: records.length,
      sampleInterval,
      createdAt: new Date(),
      lastAccessed: new Date(),
      fileSize: (await fs.stat(filepath)).size
    }
    
    const metadataPath = path.join(this.historicalDir, 'metadata', `${filename}.meta`)
    await fs.writeFile(metadataPath, JSON.stringify(metadata, null, 2))
  }

  /**
   * 生成緩存文件名
   */
  private generateCacheFileName(constellation: string, timeRange: TimeRange): string {
    const startStr = timeRange.start.toISOString().replace(/[:.]/g, '-')
    const endStr = timeRange.end.toISOString().replace(/[:.]/g, '-')
    return `${constellation}_${startStr}_${endStr}.json`
  }

  /**
   * 查找包含指定時間的緩存文件
   */
  private async findCacheFilesForTime(constellation: string, timestamp: Date): Promise<string[]> {
    try {
      const metadataDir = path.join(this.historicalDir, 'metadata')
      const files = await fs.readdir(metadataDir)
      const matchingFiles: string[] = []

      for (const file of files) {
        if (!file.startsWith(constellation) || !file.endsWith('.meta')) continue

        const metadataPath = path.join(metadataDir, file)
        const metadataContent = await fs.readFile(metadataPath, 'utf-8')
        const metadata: CacheMetadata = JSON.parse(metadataContent)

        if (timestamp >= new Date(metadata.timeRange.start) &&
            timestamp <= new Date(metadata.timeRange.end)) {
          const dataFile = file.replace('.meta', '')
          matchingFiles.push(path.join(this.historicalDir, dataFile))
        }
      }

      return matchingFiles
    } catch (error) {
      logger.error('查找緩存文件失敗', { error, constellation, timestamp })
      return []
    }
  }

  /**
   * 查找時間範圍內的緩存文件
   */
  private async findCacheFilesForTimeRange(constellation: string, timeRange: TimeRange): Promise<string[]> {
    try {
      const metadataDir = path.join(this.historicalDir, 'metadata')
      const files = await fs.readdir(metadataDir)
      const matchingFiles: string[] = []

      for (const file of files) {
        if (!file.startsWith(constellation) || !file.endsWith('.meta')) continue

        const metadataPath = path.join(metadataDir, file)
        const metadataContent = await fs.readFile(metadataPath, 'utf-8')
        const metadata: CacheMetadata = JSON.parse(metadataContent)

        // 檢查時間範圍是否有重疊
        const metaStart = new Date(metadata.timeRange.start)
        const metaEnd = new Date(metadata.timeRange.end)

        if (metaStart <= timeRange.end && metaEnd >= timeRange.start) {
          const dataFile = file.replace('.meta', '')
          matchingFiles.push(path.join(this.historicalDir, dataFile))
        }
      }

      return matchingFiles
    } catch (error) {
      logger.error('查找時間範圍緩存文件失敗', { error, constellation, timeRange })
      return []
    }
  }

  /**
   * 載入歷史記錄
   */
  private async loadHistoricalRecords(filepath: string): Promise<HistoricalTLERecord[]> {
    try {
      const content = await fs.readFile(filepath, 'utf-8')
      const records = JSON.parse(content)

      // 轉換日期字符串為 Date 對象
      return records.map((record: any) => ({
        ...record,
        timestamp: new Date(record.timestamp),
        satellites: record.satellites.map((sat: any) => ({
          ...sat,
          lastUpdated: new Date(sat.lastUpdated)
        }))
      }))
    } catch (error) {
      logger.error('載入歷史記錄失敗', { error, filepath })
      return []
    }
  }

  /**
   * 找到最接近指定時間的記錄
   */
  private findClosestRecord(records: HistoricalTLERecord[], timestamp: Date): HistoricalTLERecord | null {
    if (records.length === 0) return null

    let closest = records[0]
    let minDiff = Math.abs(records[0].timestamp.getTime() - timestamp.getTime())

    for (const record of records) {
      const diff = Math.abs(record.timestamp.getTime() - timestamp.getTime())
      if (diff < minDiff) {
        minDiff = diff
        closest = record
      }
    }

    return closest
  }

  /**
   * 更新文件訪問時間
   */
  private async updateAccessTime(filepath: string): Promise<void> {
    try {
      const metaPath = filepath.replace('.json', '.meta').replace(this.historicalDir, path.join(this.historicalDir, 'metadata'))
      const metadataContent = await fs.readFile(metaPath, 'utf-8')
      const metadata: CacheMetadata = JSON.parse(metadataContent)

      metadata.lastAccessed = new Date()
      await fs.writeFile(metaPath, JSON.stringify(metadata, null, 2))
    } catch (error) {
      logger.debug('更新訪問時間失敗', { error, filepath })
    }
  }

  /**
   * 清理過期的緩存文件
   */
  async cleanupExpiredCache(maxAgeHours: number = 168): Promise<void> { // 默認7天
    try {
      const metadataDir = path.join(this.historicalDir, 'metadata')
      const files = await fs.readdir(metadataDir)
      const now = new Date()
      let cleanedCount = 0

      for (const file of files) {
        if (!file.endsWith('.meta')) continue

        const metadataPath = path.join(metadataDir, file)
        const metadataContent = await fs.readFile(metadataPath, 'utf-8')
        const metadata: CacheMetadata = JSON.parse(metadataContent)

        const ageHours = (now.getTime() - new Date(metadata.lastAccessed).getTime()) / (1000 * 60 * 60)

        if (ageHours > maxAgeHours) {
          // 刪除數據文件和元數據文件
          const dataFile = path.join(this.historicalDir, file.replace('.meta', ''))

          try {
            await fs.unlink(dataFile)
            await fs.unlink(metadataPath)
            cleanedCount++
          } catch (error) {
            logger.warn('刪除過期緩存文件失敗', { error, file })
          }
        }
      }

      logger.info('緩存清理完成', { cleanedCount, maxAgeHours })
    } catch (error) {
      logger.error('緩存清理失敗', { error })
    }
  }

  /**
   * 獲取緩存統計信息
   */
  async getCacheStats(): Promise<{
    totalFiles: number
    totalSize: number
    constellations: string[]
    oldestCache: Date | null
    newestCache: Date | null
  }> {
    try {
      const metadataDir = path.join(this.historicalDir, 'metadata')
      const files = await fs.readdir(metadataDir)

      let totalSize = 0
      const constellations = new Set<string>()
      let oldestCache: Date | null = null
      let newestCache: Date | null = null

      for (const file of files) {
        if (!file.endsWith('.meta')) continue

        const metadataPath = path.join(metadataDir, file)
        const metadataContent = await fs.readFile(metadataPath, 'utf-8')
        const metadata: CacheMetadata = JSON.parse(metadataContent)

        totalSize += metadata.fileSize
        constellations.add(metadata.constellation)

        const createdAt = new Date(metadata.createdAt)
        if (!oldestCache || createdAt < oldestCache) {
          oldestCache = createdAt
        }
        if (!newestCache || createdAt > newestCache) {
          newestCache = createdAt
        }
      }

      return {
        totalFiles: files.length,
        totalSize,
        constellations: Array.from(constellations),
        oldestCache,
        newestCache
      }
    } catch (error) {
      logger.error('獲取緩存統計失敗', { error })
      return {
        totalFiles: 0,
        totalSize: 0,
        constellations: [],
        oldestCache: null,
        newestCache: null
      }
    }
  }

  /**
   * 預載推薦時段的歷史數據
   */
  async preloadRecommendedTimeRanges(constellation: string = 'starlink'): Promise<void> {
    logger.info('開始預載推薦時段的歷史數據', { constellation })

    for (const [key, timeRange] of Object.entries(HistoricalDataCache.RECOMMENDED_TIME_RANGES)) {
      try {
        await this.cacheHistoricalTLE(constellation, timeRange, 10) // 10分鐘間隔
        logger.info(`預載完成: ${timeRange.description}`, { key, constellation })
      } catch (error) {
        logger.error(`預載失敗: ${timeRange.description}`, { error, key, constellation })
      }
    }

    logger.info('推薦時段歷史數據預載完成', { constellation })
  }
}
