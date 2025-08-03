/**
 * ImprovedD2DataService - 改進版 D2 數據處理服務
 * 
 * 職責：
 * 1. 將原始SGP4數據轉換為改進版圖表格式
 * 2. 應用數據平滑化算法
 * 3. 計算D2觸發條件和換手時機
 * 4. 支援與立體圖的時間同步
 */

// ImprovedD2Chart removed - defining interface locally
interface ImprovedD2DataPoint {
    timestamp: number
    satellite_distance: number
    ground_distance: number
    is_triggered: boolean
    trigger_intensity?: number
    smoothed_satellite_distance?: number
    smoothed_ground_distance?: number
}

// 原始數據接口（從現有API獲取）
export interface RawSatelliteData {
    timestamp: string
    satellite_distance: number // 米
    ground_distance: number // 米
    satellite_info: {
        norad_id: number
        name: string
        latitude: number
        longitude: number
        altitude: number
    }
    trigger_condition_met?: boolean
}

// D2 觸發配置
export interface D2TriggerConfig {
    thresh1: number // 衛星距離閾值（米）
    thresh2: number // 地面距離閾值（米）
    hysteresis: number // 遲滯值（米）
    sampleIntervalSeconds: number // 採樣間隔（秒）
}

// 平滑化配置
export interface SmoothingConfig {
    movingAverageWindow: number // 移動平均窗口大小
    exponentialAlpha: number // 指數平滑參數
    enableAdaptiveSmoothing: boolean // 是否啟用自適應平滑
}

// 數據品質評估
export interface DataQualityMetrics {
    totalPoints: number
    highFrequencyNoiseLevel: number // 0-1, 高頻噪聲水平
    signalToNoiseRatio: number // 信噪比
    smoothingEffectiveness: number // 0-1, 平滑化效果
    triggerAccuracy: number // 0-1, 觸發檢測準確度
}

export class ImprovedD2DataService {
    private static instance: ImprovedD2DataService
    
    public static getInstance(): ImprovedD2DataService {
        if (!ImprovedD2DataService.instance) {
            ImprovedD2DataService.instance = new ImprovedD2DataService()
        }
        return ImprovedD2DataService.instance
    }

    /**
     * 轉換原始數據為改進版格式
     */
    public convertRawData(
        rawData: RawSatelliteData[],
        triggerConfig: D2TriggerConfig,
        smoothingConfig: SmoothingConfig
    ): {
        processedData: ImprovedD2DataPoint[]
        qualityMetrics: DataQualityMetrics
        processingTime: number
    } {
        const startTime = performance.now()

        // 提取基礎數據
        const satelliteDistances = rawData.map(d => d.satellite_distance)
        const groundDistances = rawData.map(d => d.ground_distance)

        // 評估原始數據品質
        const rawQuality = this.assessDataQuality(satelliteDistances, groundDistances)

        // 應用平滑化算法
        const smoothedSatelliteDistances = this.applySmoothingAlgorithm(
            satelliteDistances, 
            smoothingConfig
        )
        const smoothedGroundDistances = this.applySmoothingAlgorithm(
            groundDistances, 
            smoothingConfig
        )

        // 計算D2觸發條件
        const triggerResults = this.calculateD2TriggerConditions(
            smoothedSatelliteDistances,
            smoothedGroundDistances,
            triggerConfig
        )

        // 構建處理後的數據點
        const processedData: ImprovedD2DataPoint[] = rawData.map((rawPoint, index) => ({
            timestamp: rawPoint.timestamp,
            satelliteDistance: rawPoint.satellite_distance,
            groundDistance: rawPoint.ground_distance,
            smoothedSatelliteDistance: smoothedSatelliteDistances[index],
            smoothedGroundDistance: smoothedGroundDistances[index],
            triggerConditionMet: triggerResults.triggerStates[index],
            d2EventDetails: {
                thresh1: triggerConfig.thresh1,
                thresh2: triggerConfig.thresh2,
                hysteresis: triggerConfig.hysteresis,
                enteringCondition: triggerResults.enteringConditions[index],
                leavingCondition: triggerResults.leavingConditions[index],
                triggerProbability: triggerResults.triggerProbabilities[index],
            },
            satelliteInfo: {
                noradId: rawPoint.satellite_info.norad_id,
                name: rawPoint.satellite_info.name,
                latitude: rawPoint.satellite_info.latitude,
                longitude: rawPoint.satellite_info.longitude,
                altitude: rawPoint.satellite_info.altitude,
            },
        }))

        // 評估處理後數據品質
        const processedQuality = this.assessDataQuality(
            smoothedSatelliteDistances,
            smoothedGroundDistances
        )

        const qualityMetrics: DataQualityMetrics = {
            totalPoints: rawData.length,
            highFrequencyNoiseLevel: rawQuality.noiseLevel,
            signalToNoiseRatio: processedQuality.signalToNoiseRatio,
            smoothingEffectiveness: this.calculateSmoothingEffectiveness(
                satelliteDistances,
                smoothedSatelliteDistances
            ),
            triggerAccuracy: this.evaluateTriggerAccuracy(triggerResults),
        }

        const processingTime = performance.now() - startTime

        return {
            processedData,
            qualityMetrics,
            processingTime,
        }
    }

    /**
     * 應用智能平滑化算法
     */
    private applySmoothingAlgorithm(
        data: number[], 
        config: SmoothingConfig
    ): number[] {
        if (data.length === 0) return data

        // 第一階段：移動平均
        let smoothed = this.movingAverage(data, config.movingAverageWindow)

        // 第二階段：指數平滑
        smoothed = this.exponentialSmoothing(smoothed, config.exponentialAlpha)

        // 第三階段：自適應平滑（可選）
        if (config.enableAdaptiveSmoothing) {
            smoothed = this.adaptiveSmoothing(data, smoothed)
        }

        return smoothed
    }

    /**
     * 移動平均平滑化
     */
    private movingAverage(data: number[], windowSize: number): number[] {
        if (data.length < windowSize) return [...data]
        
        const smoothed = []
        for (let i = 0; i < data.length; i++) {
            const start = Math.max(0, i - Math.floor(windowSize / 2))
            const end = Math.min(data.length, start + windowSize)
            const window = data.slice(start, end)
            const average = window.reduce((sum, val) => sum + val, 0) / window.length
            smoothed.push(average)
        }
        return smoothed
    }

    /**
     * 指數平滑
     */
    private exponentialSmoothing(data: number[], alpha: number): number[] {
        if (data.length === 0) return data
        
        const smoothed = [data[0]]
        for (let i = 1; i < data.length; i++) {
            const smoothedValue = alpha * data[i] + (1 - alpha) * smoothed[i - 1]
            smoothed.push(smoothedValue)
        }
        return smoothed
    }

    /**
     * 自適應平滑（基於局部變異度調整）
     */
    private adaptiveSmoothing(original: number[], smoothed: number[]): number[] {
        const adaptive = [...smoothed]
        const adaptationStrength = 0.3

        for (let i = 1; i < adaptive.length - 1; i++) {
            // 計算局部變異度
            const localVariation = Math.abs(original[i] - original[i - 1]) + 
                                   Math.abs(original[i + 1] - original[i])
            
            // 正規化變異度 (0-1)
            const normalizedVariation = Math.min(1, localVariation / (original[i] * 0.1))
            
            // 高變異區域減少平滑，低變異區域增加平滑
            const adaptiveFactor = 1 - normalizedVariation * adaptationStrength
            adaptive[i] = adaptiveFactor * smoothed[i] + (1 - adaptiveFactor) * original[i]
        }

        return adaptive
    }

    /**
     * 計算D2觸發條件
     */
    private calculateD2TriggerConditions(
        satelliteDistances: number[],
        groundDistances: number[],
        config: D2TriggerConfig
    ): {
        triggerStates: boolean[]
        enteringConditions: boolean[]
        leavingConditions: boolean[]
        triggerProbabilities: number[]
    } {
        const results = {
            triggerStates: [] as boolean[],
            enteringConditions: [] as boolean[],
            leavingConditions: [] as boolean[],
            triggerProbabilities: [] as number[],
        }

        let previousTriggerState = false

        for (let i = 0; i < satelliteDistances.length; i++) {
            const satDist = satelliteDistances[i]
            const groundDist = groundDistances[i]

            // D2 進入條件
            // Condition 1: Ml1 - Hys > Thresh1 (服務衛星距離 > 閾值1)
            // Condition 2: Ml2 + Hys < Thresh2 (目標衛星距離 < 閾值2)
            const enteringCond1 = (satDist - config.hysteresis) > config.thresh1
            const enteringCond2 = (groundDist + config.hysteresis) < config.thresh2
            const enteringCondition = enteringCond1 && enteringCond2

            // D2 離開條件
            // Condition 1: Ml1 + Hys < Thresh1
            // Condition 2: Ml2 - Hys > Thresh2
            const leavingCond1 = (satDist + config.hysteresis) < config.thresh1
            const leavingCond2 = (groundDist - config.hysteresis) > config.thresh2
            const leavingCondition = leavingCond1 || leavingCond2

            // 狀態轉換邏輯
            let currentTriggerState = previousTriggerState
            if (!previousTriggerState && enteringCondition) {
                currentTriggerState = true
            } else if (previousTriggerState && leavingCondition) {
                currentTriggerState = false
            }

            // 計算觸發可能性 (0-1)
            const cond1Strength = enteringCond1 ? 
                Math.min(1, (satDist - config.thresh1) / (config.thresh1 * 0.1)) : 0
            const cond2Strength = enteringCond2 ? 
                Math.min(1, (config.thresh2 - groundDist) / (config.thresh2 * 0.1)) : 0
            const triggerProbability = Math.min(cond1Strength, cond2Strength)

            results.triggerStates.push(currentTriggerState)
            results.enteringConditions.push(enteringCondition)
            results.leavingConditions.push(leavingCondition)
            results.triggerProbabilities.push(triggerProbability)

            previousTriggerState = currentTriggerState
        }

        return results
    }

    /**
     * 評估數據品質
     */
    private assessDataQuality(
        satelliteDistances: number[],
        groundDistances: number[]
    ): {
        noiseLevel: number
        signalToNoiseRatio: number
        stability: number
    } {
        // 計算噪聲水平（基於相鄰點差異）
        const satDiffs = satelliteDistances.slice(1).map((val, i) => 
            Math.abs(val - satelliteDistances[i])
        )
        const avgSatDiff = satDiffs.reduce((sum, diff) => sum + diff, 0) / satDiffs.length
        const avgSatValue = satelliteDistances.reduce((sum, val) => sum + val, 0) / satelliteDistances.length
        
        const noiseLevel = avgSatDiff / avgSatValue // 正規化噪聲水平
        const signalToNoiseRatio = avgSatValue / avgSatDiff
        
        // 計算穩定性（變異係數）
        const satVariance = satelliteDistances.reduce((sum, val) => 
            sum + Math.pow(val - avgSatValue, 2), 0
        ) / satelliteDistances.length
        const stability = 1 - (Math.sqrt(satVariance) / avgSatValue)

        return { noiseLevel, signalToNoiseRatio, stability }
    }

    /**
     * 計算平滑化效果
     */
    private calculateSmoothingEffectiveness(
        original: number[],
        smoothed: number[]
    ): number {
        if (original.length !== smoothed.length || original.length < 2) return 0

        // 計算原始數據的變異度
        const originalVariations = original.slice(1).map((val, i) => 
            Math.abs(val - original[i])
        )
        const avgOriginalVariation = originalVariations.reduce((sum, v) => sum + v, 0) / originalVariations.length

        // 計算平滑後數據的變異度
        const smoothedVariations = smoothed.slice(1).map((val, i) => 
            Math.abs(val - smoothed[i])
        )
        const avgSmoothedVariation = smoothedVariations.reduce((sum, v) => sum + v, 0) / smoothedVariations.length

        // 平滑化效果 = 變異度減少程度
        const effectiveness = (avgOriginalVariation - avgSmoothedVariation) / avgOriginalVariation
        return Math.max(0, Math.min(1, effectiveness))
    }

    /**
     * 評估觸發檢測準確度
     */
    private evaluateTriggerAccuracy(triggerResults: {
        triggerStates: boolean[]
        enteringConditions: boolean[]
        leavingConditions: boolean[]
        triggerProbabilities: number[]
    }): number {
        // 檢查觸發狀態的一致性和合理性
        let consistencyScore = 0
        const totalTransitions = triggerResults.triggerStates.length - 1

        for (let i = 1; i < triggerResults.triggerStates.length; i++) {
            const prevState = triggerResults.triggerStates[i - 1]
            const currentState = triggerResults.triggerStates[i]
            const entering = triggerResults.enteringConditions[i]
            const leaving = triggerResults.leavingConditions[i]

            // 檢查狀態轉換的邏輯一致性
            if (!prevState && currentState && entering) {
                consistencyScore += 1 // 正確的進入轉換
            } else if (prevState && !currentState && leaving) {
                consistencyScore += 1 // 正確的離開轉換
            } else if (prevState === currentState) {
                consistencyScore += 1 // 狀態保持
            }
        }

        return totalTransitions > 0 ? consistencyScore / totalTransitions : 1
    }

    /**
     * 生成測試數據（用於開發和測試）
     */
    public generateTestData(
        durationSeconds: number = 300,
        sampleInterval: number = 10
    ): RawSatelliteData[] {
        const testData: RawSatelliteData[] = []
        const totalPoints = Math.floor(durationSeconds / sampleInterval)

        for (let i = 0; i < totalPoints; i++) {
            const time = i * sampleInterval
            const timestamp = new Date(Date.now() + time * 1000).toISOString()

            // 模擬衛星軌道：拋物線軌跡 + 高頻振蕩（模擬SGP4效果）
            const baseSatDistance = 500000 + 300000 * Math.sin(time / 100) + 100000 * Math.cos(time / 50)
            const highFreqNoise = 5000 * Math.sin(time * 2) + 3000 * Math.cos(time * 3.7)
            const satelliteDistance = baseSatDistance + highFreqNoise

            // 模擬地面距離：較為穩定的參考距離
            const baseGroundDistance = 50000 + 20000 * Math.sin(time / 150)
            const groundNoise = 1000 * Math.sin(time * 1.5)
            const groundDistance = baseGroundDistance + groundNoise

            testData.push({
                timestamp,
                satellite_distance: satelliteDistance,
                ground_distance: groundDistance,
                satellite_info: {
                    norad_id: 12345 + (i % 3), // 模擬多顆衛星
                    name: `TestSat-${12345 + (i % 3)}`,
                    latitude: 25.0 + Math.sin(time / 100) * 10,
                    longitude: 121.0 + Math.cos(time / 100) * 5,
                    altitude: 550000 + Math.sin(time / 80) * 50000,
                },
            })
        }

        return testData
    }
}

// 導出服務實例
export const improvedD2DataService = ImprovedD2DataService.getInstance()

// 導出預設配置
export const DEFAULT_D2_TRIGGER_CONFIG: D2TriggerConfig = {
    thresh1: 600000, // 600km (衛星距離閾值)
    thresh2: 80000,  // 80km (地面距離閾值)
    hysteresis: 5000, // 5km (遲滯值)
    sampleIntervalSeconds: 10,
}

export const DEFAULT_SMOOTHING_CONFIG: SmoothingConfig = {
    movingAverageWindow: 5,
    exponentialAlpha: 0.3,
    enableAdaptiveSmoothing: true,
}

// 導出便利函數
export function createImprovedD2Data(
    rawData: RawSatelliteData[],
    triggerConfig: D2TriggerConfig = DEFAULT_D2_TRIGGER_CONFIG,
    smoothingConfig: SmoothingConfig = DEFAULT_SMOOTHING_CONFIG
) {
    return improvedD2DataService.convertRawData(rawData, triggerConfig, smoothingConfig)
}