/**
 * TLE 數據服務 - 真實衛星軌道數據集成
 * 
 * 功能：
 * 1. 從 CelesTrak API 獲取真實 TLE 數據
 * 2. 支持 Starlink 星座數據
 * 3. 歷史數據緩存和管理
 * 4. 數據驗證和清理
 * 
 * 符合 d2.md 中 Phase 1 的要求
 */

import axios from 'axios'
import fs from 'fs/promises'
import path from 'path'
import { createLogger } from '../utils/logger'

const logger = createLogger('TLEDataService')

export interface TLEData {
  satelliteName: string
  catalogNumber: number
  epochYear: number
  epochDay: number
  firstDerivative: number
  secondDerivative: number
  dragTerm: number
  inclination: number
  rightAscension: number
  eccentricity: number
  argumentOfPerigee: number
  meanAnomaly: number
  meanMotion: number
  revolutionNumber: number
  line1: string  // 原始 TLE 第一行
  line2: string  // 原始 TLE 第二行
  lastUpdated: Date
}

export interface TLESource {
  name: string
  url: string
  constellation: string
  description: string
}

export class TLEDataService {
  private readonly CELESTRAK_BASE_URL = 'https://celestrak.org/NORAD/elements/gp.php'
  private readonly CACHE_DIR = './data/tle_cache'
  private readonly HISTORICAL_DIR = './data/tle_historical'
  
  // 支持的 TLE 數據源
  private readonly TLE_SOURCES: Record<string, TLESource> = {
    starlink: {
      name: 'Starlink',
      url: `${this.CELESTRAK_BASE_URL}?GROUP=starlink&FORMAT=tle`,
      constellation: 'starlink',
      description: 'SpaceX Starlink constellation'
    },
    oneweb: {
      name: 'OneWeb',
      url: `${this.CELESTRAK_BASE_URL}?GROUP=oneweb&FORMAT=tle`,
      constellation: 'oneweb',
      description: 'OneWeb constellation'
    },
    gps: {
      name: 'GPS',
      url: `${this.CELESTRAK_BASE_URL}?GROUP=gps-ops&FORMAT=tle`,
      constellation: 'gps',
      description: 'GPS operational satellites'
    }
  }

  constructor() {
    this.initializeDirectories()
  }

  /**
   * 初始化緩存目錄
   */
  private async initializeDirectories(): Promise<void> {
    try {
      await fs.mkdir(this.CACHE_DIR, { recursive: true })
      await fs.mkdir(this.HISTORICAL_DIR, { recursive: true })
      logger.info('TLE 緩存目錄初始化完成', {
        cacheDir: this.CACHE_DIR,
        historicalDir: this.HISTORICAL_DIR
      })
    } catch (error) {
      logger.error('TLE 緩存目錄初始化失敗', { error })
      throw error
    }
  }

  /**
   * 獲取 Starlink 星座 TLE 數據
   */
  async fetchStarlinkTLE(): Promise<TLEData[]> {
    return this.fetchTLEFromSource('starlink')
  }

  /**
   * 獲取指定星座的 TLE 數據
   */
  async fetchTLEFromSource(constellation: string): Promise<TLEData[]> {
    const source = this.TLE_SOURCES[constellation]
    if (!source) {
      throw new Error(`不支援的星座: ${constellation}`)
    }

    try {
      logger.info(`開始獲取 ${source.name} TLE 數據`, { url: source.url })
      
      const response = await axios.get(source.url, {
        timeout: 30000,
        headers: {
          'User-Agent': 'NTN-Stack-Research/1.0'
        }
      })

      if (response.status !== 200) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const tleText = response.data
      const tleData = this.parseTLEText(tleText, constellation)
      
      // 緩存數據
      await this.cacheTLEData(constellation, tleData)
      
      logger.info(`成功獲取 ${source.name} TLE 數據`, {
        satelliteCount: tleData.length,
        constellation
      })

      return tleData
    } catch (error) {
      logger.error(`獲取 ${source.name} TLE 數據失敗`, { error, constellation })
      
      // 嘗試從緩存讀取
      const cachedData = await this.getCachedTLEData(constellation)
      if (cachedData.length > 0) {
        logger.warn(`使用緩存的 ${source.name} TLE 數據`, {
          satelliteCount: cachedData.length
        })
        return cachedData
      }
      
      throw error
    }
  }

  /**
   * 獲取特定衛星的 TLE 數據
   */
  async fetchSpecificSatellite(noradId: number): Promise<TLEData | null> {
    try {
      const url = `${this.CELESTRAK_BASE_URL}?CATNR=${noradId}&FORMAT=tle`
      
      logger.info('獲取特定衛星 TLE 數據', { noradId, url })
      
      const response = await axios.get(url, {
        timeout: 10000,
        headers: {
          'User-Agent': 'NTN-Stack-Research/1.0'
        }
      })

      if (response.status !== 200) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const tleText = response.data.trim()
      if (!tleText) {
        logger.warn('未找到指定衛星的 TLE 數據', { noradId })
        return null
      }

      const tleData = this.parseTLEText(tleText, 'individual')
      return tleData.length > 0 ? tleData[0] : null
      
    } catch (error) {
      logger.error('獲取特定衛星 TLE 數據失敗', { error, noradId })
      return null
    }
  }

  /**
   * 解析 TLE 文本數據
   */
  private parseTLEText(tleText: string, constellation: string): TLEData[] {
    const lines = tleText.trim().split('\n').map(line => line.trim()).filter(line => line.length > 0)
    const tleData: TLEData[] = []
    
    // TLE 格式：每3行為一組（衛星名稱 + 兩行軌道數據）
    for (let i = 0; i < lines.length; i += 3) {
      if (i + 2 >= lines.length) break
      
      const satelliteName = lines[i]
      const line1 = lines[i + 1]
      const line2 = lines[i + 2]
      
      // 驗證 TLE 格式
      if (!line1.startsWith('1 ') || !line2.startsWith('2 ')) {
        logger.warn('無效的 TLE 格式', { satelliteName, line1: line1.substring(0, 20) })
        continue
      }
      
      try {
        const tle = this.parseTLELines(satelliteName, line1, line2)
        tleData.push(tle)
      } catch (error) {
        logger.warn('TLE 解析失敗', { satelliteName, error })
      }
    }
    
    return tleData
  }

  /**
   * 解析單個 TLE 記錄
   */
  private parseTLELines(satelliteName: string, line1: string, line2: string): TLEData {
    // 解析第一行
    const catalogNumber = parseInt(line1.substring(2, 7))
    const epochYear = parseInt(line1.substring(18, 20))
    const epochDay = parseFloat(line1.substring(20, 32))
    const firstDerivative = parseFloat(line1.substring(33, 43))
    const secondDerivative = this.parseScientificNotation(line1.substring(44, 52))
    const dragTerm = this.parseScientificNotation(line1.substring(53, 61))
    
    // 解析第二行
    const inclination = parseFloat(line2.substring(8, 16))
    const rightAscension = parseFloat(line2.substring(17, 25))
    const eccentricity = parseFloat('0.' + line2.substring(26, 33))
    const argumentOfPerigee = parseFloat(line2.substring(34, 42))
    const meanAnomaly = parseFloat(line2.substring(43, 51))
    const meanMotion = parseFloat(line2.substring(52, 63))
    const revolutionNumber = parseInt(line2.substring(63, 68))
    
    return {
      satelliteName: satelliteName.trim(),
      catalogNumber,
      epochYear: epochYear < 57 ? 2000 + epochYear : 1900 + epochYear,
      epochDay,
      firstDerivative,
      secondDerivative,
      dragTerm,
      inclination,
      rightAscension,
      eccentricity,
      argumentOfPerigee,
      meanAnomaly,
      meanMotion,
      revolutionNumber,
      line1,
      line2,
      lastUpdated: new Date()
    }
  }

  /**
   * 解析科學記數法格式（TLE 特殊格式）
   */
  private parseScientificNotation(str: string): number {
    if (!str || str.trim().length === 0) return 0

    const trimmed = str.trim()
    if (trimmed === '00000-0' || trimmed === '00000+0') return 0

    // TLE 格式：±.12345-6 表示 ±0.12345e-6
    const sign = trimmed[0] === '-' ? -1 : 1
    const mantissa = parseFloat('0.' + trimmed.substring(1, 6))
    const exponent = parseInt(trimmed.substring(6, 8))

    return sign * mantissa * Math.pow(10, exponent)
  }

  /**
   * 緩存 TLE 數據到本地
   */
  private async cacheTLEData(constellation: string, tleData: TLEData[]): Promise<void> {
    try {
      const cacheFile = path.join(this.CACHE_DIR, `${constellation}_latest.json`)
      const cacheData = {
        constellation,
        timestamp: new Date().toISOString(),
        satelliteCount: tleData.length,
        data: tleData
      }

      await fs.writeFile(cacheFile, JSON.stringify(cacheData, null, 2))
      logger.info('TLE 數據緩存完成', { constellation, satelliteCount: tleData.length })
    } catch (error) {
      logger.error('TLE 數據緩存失敗', { error, constellation })
    }
  }

  /**
   * 從緩存讀取 TLE 數據
   */
  private async getCachedTLEData(constellation: string): Promise<TLEData[]> {
    try {
      const cacheFile = path.join(this.CACHE_DIR, `${constellation}_latest.json`)
      const cacheContent = await fs.readFile(cacheFile, 'utf-8')
      const cacheData = JSON.parse(cacheContent)

      // 檢查緩存時效性（24小時）
      const cacheTime = new Date(cacheData.timestamp)
      const now = new Date()
      const hoursDiff = (now.getTime() - cacheTime.getTime()) / (1000 * 60 * 60)

      if (hoursDiff > 24) {
        logger.warn('緩存數據已過期', { constellation, hoursDiff })
        return []
      }

      logger.info('使用緩存的 TLE 數據', {
        constellation,
        satelliteCount: cacheData.satelliteCount,
        cacheAge: `${hoursDiff.toFixed(1)}小時`
      })

      return cacheData.data.map((item: any) => ({
        ...item,
        lastUpdated: new Date(item.lastUpdated)
      }))
    } catch (error) {
      logger.debug('無法讀取緩存數據', { error, constellation })
      return []
    }
  }

  /**
   * 獲取支持的星座列表
   */
  getSupportedConstellations(): TLESource[] {
    return Object.values(this.TLE_SOURCES)
  }

  /**
   * 驗證 TLE 數據的有效性
   */
  validateTLEData(tle: TLEData): boolean {
    // 基本範圍檢查
    if (tle.inclination < 0 || tle.inclination > 180) return false
    if (tle.eccentricity < 0 || tle.eccentricity >= 1) return false
    if (tle.meanMotion <= 0) return false
    if (tle.catalogNumber <= 0) return false

    // 檢查軌道週期是否合理（30分鐘到24小時）
    const orbitalPeriod = 1440 / tle.meanMotion // 分鐘
    if (orbitalPeriod < 30 || orbitalPeriod > 1440) return false

    return true
  }

  /**
   * 獲取星座統計信息
   */
  async getConstellationStats(constellation: string): Promise<{
    totalSatellites: number
    validSatellites: number
    lastUpdated: Date | null
    averageAltitude: number
    inclinationRange: { min: number, max: number }
  }> {
    const tleData = await this.getCachedTLEData(constellation)

    if (tleData.length === 0) {
      return {
        totalSatellites: 0,
        validSatellites: 0,
        lastUpdated: null,
        averageAltitude: 0,
        inclinationRange: { min: 0, max: 0 }
      }
    }

    const validSatellites = tleData.filter(tle => this.validateTLEData(tle))
    const inclinations = validSatellites.map(tle => tle.inclination)

    // 估算平均高度（基於平均運動）
    const avgMeanMotion = validSatellites.reduce((sum, tle) => sum + tle.meanMotion, 0) / validSatellites.length
    const avgOrbitalPeriod = 1440 / avgMeanMotion // 分鐘
    const avgAltitude = Math.pow((avgOrbitalPeriod * 60) ** 2 * 3.986004418e14 / (4 * Math.PI ** 2), 1/3) / 1000 - 6371 // km

    return {
      totalSatellites: tleData.length,
      validSatellites: validSatellites.length,
      lastUpdated: tleData[0]?.lastUpdated || null,
      averageAltitude: Math.round(avgAltitude),
      inclinationRange: {
        min: Math.min(...inclinations),
        max: Math.max(...inclinations)
      }
    }
  }
}
