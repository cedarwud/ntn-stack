/**
 * IntelligentDataProcessor - 智能數據處理服務
 * 
 * 核心理念：不丟棄真實性，而是智能提取可視化友好的特徵
 * 專門處理SGP4真實軌道數據的高頻振蕩問題
 */

// 數據處理配置
export interface ProcessingConfig {
    // 降噪策略
    noisReductionStrategy: 'conservative' | 'balanced' | 'aggressive' | 'adaptive'
    
    // 特徵提取選項
    preservePhysicalMeaning: boolean // 是否保留物理意義
    enhanceTriggerPatterns: boolean  // 是否強化觸發模式
    maintainTemporalAccuracy: boolean // 是否保持時間精度
    
    // 平滑化參數
    movingAverageWindow: number
    exponentialSmoothingAlpha: number
    
    // 高級選項
    adaptiveThreshold: number // 自適應閾值
    signalToNoiseThreshold: number // 信噪比閾值
    preserveExtremeEvents: boolean // 是否保留極端事件
}

// 數據處理結果
export interface ProcessingResult {
    processedData: any[]
    originalData: any[]
    processingMetrics: {
        noiseReductionRate: number // 噪聲減少率
        signalEnhancementRatio: number // 信號增強比
        physicalAccuracyScore: number // 物理準確度分數
        visualClarityScore: number // 視覺清晰度分數
        processingTime: number // 處理時間
    }
    recommendations: string[] // 處理建議
}

// 頻譜分析結果
interface FrequencyAnalysis {
    dominantFrequencies: number[]
    noiseFrequencies: number[]
    signalFrequencies: number[]
    separationQuality: number
}

export class IntelligentDataProcessor {
    private static instance: IntelligentDataProcessor
    
    public static getInstance(): IntelligentDataProcessor {
        if (!IntelligentDataProcessor.instance) {
            IntelligentDataProcessor.instance = new IntelligentDataProcessor()
        }
        return IntelligentDataProcessor.instance
    }

    /**
     * 主要數據處理入口
     */
    public processRealSatelliteData(
        rawData: any[],
        config: ProcessingConfig
    ): ProcessingResult {
        const startTime = performance.now()
        
        // 1. 數據品質分析
        const qualityAnalysis = this.analyzeDataQuality(rawData)
        // console.log('🔍 數據品質分析:', qualityAnalysis)
        
        // 2. 頻譜分析 - 識別噪聲和信號頻率
        const frequencyAnalysis = this.performFrequencyAnalysis(rawData)
        // console.log('📊 頻譜分析結果:', frequencyAnalysis)
        
        // 3. 根據分析結果選擇最佳處理策略
        const optimalStrategy = this.determineOptimalStrategy(qualityAnalysis, frequencyAnalysis, config)
        // console.log('🎯 選定處理策略:', optimalStrategy)
        
        // 4. 應用智能數據處理
        const processedData = this.applyIntelligentProcessing(rawData, optimalStrategy)
        
        // 5. 驗證處理效果
        const processingMetrics = this.evaluateProcessingResults(rawData, processedData)
        
        // 6. 生成處理建議
        const recommendations = this.generateRecommendations(processingMetrics, qualityAnalysis)
        
        const processingTime = performance.now() - startTime
        
        return {
            processedData,
            originalData: rawData,
            processingMetrics: {
                ...processingMetrics,
                processingTime,
            },
            recommendations,
        }
    }

    /**
     * 數據品質分析
     */
    private analyzeDataQuality(data: any[]): {
        noiseLevel: number
        signalStrength: number
        temporalConsistency: number
        extremeValueRatio: number
        overallQuality: 'excellent' | 'good' | 'fair' | 'poor'
    } {
        if (data.length < 10) {
            return {
                noiseLevel: 0,
                signalStrength: 0,
                temporalConsistency: 0,
                extremeValueRatio: 0,
                overallQuality: 'poor'
            }
        }

        const satelliteDistances = data.map(d => d.satelliteDistance || d.satellite_distance || 0)
        
        // 計算噪聲水平（基於相鄰點差異）
        const differences = []
        for (let i = 1; i < satelliteDistances.length; i++) {
            differences.push(Math.abs(satelliteDistances[i] - satelliteDistances[i - 1]))
        }
        
        const avgDifference = differences.reduce((sum, diff) => sum + diff, 0) / differences.length
        const avgValue = satelliteDistances.reduce((sum, val) => sum + val, 0) / satelliteDistances.length
        const noiseLevel = avgDifference / avgValue
        
        // 計算信號強度（基於整體變化範圍）
        const min = Math.min(...satelliteDistances)
        const max = Math.max(...satelliteDistances)
        const signalStrength = (max - min) / avgValue
        
        // 計算時間一致性（趨勢穩定性）
        let trendChanges = 0
        for (let i = 2; i < satelliteDistances.length; i++) {
            const trend1 = satelliteDistances[i - 1] - satelliteDistances[i - 2]
            const trend2 = satelliteDistances[i] - satelliteDistances[i - 1]
            if ((trend1 > 0 && trend2 < 0) || (trend1 < 0 && trend2 > 0)) {
                trendChanges++
            }
        }
        const temporalConsistency = 1 - (trendChanges / (satelliteDistances.length - 2))
        
        // 計算極端值比例
        const q1 = this.calculatePercentile(satelliteDistances, 25)
        const q3 = this.calculatePercentile(satelliteDistances, 75)
        const iqr = q3 - q1
        const extremeThreshold = 1.5 * iqr
        const extremeValues = satelliteDistances.filter(val => 
            val < (q1 - extremeThreshold) || val > (q3 + extremeThreshold)
        ).length
        const extremeValueRatio = extremeValues / satelliteDistances.length
        
        // 整體品質評估
        const qualityScore = (
            (1 - Math.min(noiseLevel, 1)) * 0.4 +
            Math.min(signalStrength, 1) * 0.3 +
            temporalConsistency * 0.2 +
            (1 - extremeValueRatio) * 0.1
        )
        
        const overallQuality = 
            qualityScore >= 0.8 ? 'excellent' :
            qualityScore >= 0.6 ? 'good' :
            qualityScore >= 0.4 ? 'fair' : 'poor'
        
        return {
            noiseLevel,
            signalStrength,
            temporalConsistency,
            extremeValueRatio,
            overallQuality
        }
    }

    /**
     * 頻譜分析 - 簡化版本，識別主要頻率成分
     */
    private performFrequencyAnalysis(data: any[]): FrequencyAnalysis {
        const satelliteDistances = data.map(d => d.satelliteDistance || d.satellite_distance || 0)
        
        if (satelliteDistances.length < 20) {
            return {
                dominantFrequencies: [],
                noiseFrequencies: [],
                signalFrequencies: [],
                separationQuality: 0
            }
        }

        // 簡化的頻率分析：計算不同窗口大小的變化模式
        const frequencyComponents = []
        
        // 短期變化（高頻，可能是噪聲）
        const shortTermVariations = this.calculateVariationAtScale(satelliteDistances, 2)
        frequencyComponents.push({ scale: 2, variation: shortTermVariations, type: 'high_freq' })
        
        // 中期變化（中頻，可能是軌道特徵）
        const mediumTermVariations = this.calculateVariationAtScale(satelliteDistances, 10)
        frequencyComponents.push({ scale: 10, variation: mediumTermVariations, type: 'medium_freq' })
        
        // 長期變化（低頻，主要軌道趨勢）
        const longTermVariations = this.calculateVariationAtScale(satelliteDistances, 30)
        frequencyComponents.push({ scale: 30, variation: longTermVariations, type: 'low_freq' })
        
        // 分類頻率成分
        const totalVariation = frequencyComponents.reduce((sum, comp) => sum + comp.variation, 0)
        const highFreqRatio = shortTermVariations / totalVariation
        const mediumFreqRatio = mediumTermVariations / totalVariation
        const lowFreqRatio = longTermVariations / totalVariation
        
        const dominantFrequencies = []
        const noiseFrequencies = []
        const signalFrequencies = []
        
        if (highFreqRatio > 0.4) noiseFrequencies.push(2) // 高頻噪聲
        if (mediumFreqRatio > 0.3) signalFrequencies.push(10) // 中頻信號
        if (lowFreqRatio > 0.2) signalFrequencies.push(30) // 低頻信號
        
        // 最大的成分是主導頻率
        const maxComponent = frequencyComponents.reduce((max, comp) => 
            comp.variation > max.variation ? comp : max
        )
        dominantFrequencies.push(maxComponent.scale)
        
        // 分離品質：信號和噪聲的分離程度
        const separationQuality = Math.abs(mediumFreqRatio + lowFreqRatio - highFreqRatio)
        
        return {
            dominantFrequencies,
            noiseFrequencies,
            signalFrequencies,
            separationQuality
        }
    }

    /**
     * 計算特定尺度的變化量
     */
    private calculateVariationAtScale(data: number[], scale: number): number {
        if (data.length < scale * 2) return 0
        
        let totalVariation = 0
        let count = 0
        
        for (let i = scale; i < data.length - scale; i += scale) {
            const before = data.slice(i - scale, i).reduce((sum, val) => sum + val, 0) / scale
            const after = data.slice(i, i + scale).reduce((sum, val) => sum + val, 0) / scale
            totalVariation += Math.abs(after - before)
            count++
        }
        
        return count > 0 ? totalVariation / count : 0
    }

    /**
     * 確定最佳處理策略
     */
    private determineOptimalStrategy(
        qualityAnalysis: any,
        frequencyAnalysis: FrequencyAnalysis,
        config: ProcessingConfig
    ): {
        strategy: string
        parameters: any
        reasoning: string[]
    } {
        const reasoning = []
        const parameters = {
            movingAverageWindow: config.movingAverageWindow || 5,
            exponentialAlpha: config.exponentialSmoothingAlpha || 0.3,
            preserveExtremes: config.preserveExtremeEvents,
        }

        // 根據數據品質調整策略
        if (qualityAnalysis.noiseLevel > 0.15) {
            // 高噪聲：需要強力處理
            parameters.movingAverageWindow = Math.max(parameters.movingAverageWindow, 7)
            parameters.exponentialAlpha = Math.min(parameters.exponentialAlpha, 0.25)
            reasoning.push('檢測到高噪聲水平，採用強力平滑策略')
        } else if (qualityAnalysis.noiseLevel < 0.05) {
            // 低噪聲：輕度處理即可
            parameters.movingAverageWindow = Math.min(parameters.movingAverageWindow, 3)
            parameters.exponentialAlpha = Math.max(parameters.exponentialAlpha, 0.4)
            reasoning.push('數據品質良好，採用輕度處理策略')
        }

        // 根據頻譜分析調整
        if (frequencyAnalysis.noiseFrequencies.length > 0) {
            // 有明顯噪聲頻率
            parameters.targetNoiseFrequencies = frequencyAnalysis.noiseFrequencies
            reasoning.push('識別到特定噪聲頻率，將進行針對性濾波')
        }

        // 根據用戶配置微調
        if (config.noisReductionStrategy === 'aggressive') {
            parameters.movingAverageWindow += 2
            parameters.exponentialAlpha *= 0.8
            reasoning.push('用戶選擇激進策略，增強降噪力度')
        } else if (config.noisReductionStrategy === 'conservative') {
            parameters.movingAverageWindow = Math.max(1, parameters.movingAverageWindow - 2)
            parameters.exponentialAlpha = Math.min(1, parameters.exponentialAlpha * 1.2)
            reasoning.push('用戶選擇保守策略，保持更多原始特徵')
        }

        return {
            strategy: config.noisReductionStrategy === 'adaptive' ? 'intelligent_adaptive' : config.noisReductionStrategy,
            parameters,
            reasoning
        }
    }

    /**
     * 應用智能數據處理
     */
    private applyIntelligentProcessing(data: any[], strategy: any): any[] {
        // console.log(`🔧 應用處理策略: ${strategy.strategy}`, strategy.parameters)
        
        // 提取數據
        const satelliteDistances = data.map(d => d.satelliteDistance || d.satellite_distance || 0)
        const groundDistances = data.map(d => d.groundDistance || d.ground_distance || 0)
        
        // 階段1：基礎平滑
        let smoothedSatDistances = this.movingAverage(satelliteDistances, strategy.parameters.movingAverageWindow)
        let smoothedGroundDistances = this.movingAverage(groundDistances, Math.max(3, strategy.parameters.movingAverageWindow - 2))
        
        // 階段2：指數平滑
        smoothedSatDistances = this.exponentialSmoothing(smoothedSatDistances, strategy.parameters.exponentialAlpha)
        smoothedGroundDistances = this.exponentialSmoothing(smoothedGroundDistances, strategy.parameters.exponentialAlpha)
        
        // 階段3：邊緣保護（可選）
        if (strategy.parameters.preserveExtremes) {
            smoothedSatDistances = this.preserveExtremeValues(satelliteDistances, smoothedSatDistances)
            smoothedGroundDistances = this.preserveExtremeValues(groundDistances, smoothedGroundDistances)
        }
        
        // 階段4：物理約束校正
        smoothedSatDistances = this.applyPhysicalConstraints(smoothedSatDistances)
        smoothedGroundDistances = this.applyPhysicalConstraints(smoothedGroundDistances)
        
        // 構建處理後的數據
        return data.map((originalPoint, index) => ({
            ...originalPoint,
            // 保留原始數據
            originalSatelliteDistance: originalPoint.satelliteDistance || originalPoint.satellite_distance,
            originalGroundDistance: originalPoint.groundDistance || originalPoint.ground_distance,
            // 添加處理後的數據
            satelliteDistance: smoothedSatDistances[index],
            groundDistance: smoothedGroundDistances[index],
            satellite_distance: smoothedSatDistances[index], // 兼容性
            ground_distance: smoothedGroundDistances[index], // 兼容性
            // 元數據
            processingApplied: true,
            processingStrategy: strategy.strategy,
            confidenceScore: this.calculatePointConfidence(
                originalPoint.satelliteDistance || originalPoint.satellite_distance,
                smoothedSatDistances[index],
                strategy.parameters
            )
        }))
    }

    /**
     * 移動平均
     */
    private movingAverage(data: number[], window: number): number[] {
        if (window <= 1) return [...data]
        
        const result = []
        for (let i = 0; i < data.length; i++) {
            const start = Math.max(0, i - Math.floor(window / 2))
            const end = Math.min(data.length, start + window)
            const slice = data.slice(start, end)
            const avg = slice.reduce((sum, val) => sum + val, 0) / slice.length
            result.push(avg)
        }
        return result
    }

    /**
     * 指數平滑
     */
    private exponentialSmoothing(data: number[], alpha: number): number[] {
        if (data.length === 0 || alpha >= 1) return [...data]
        
        const result = [data[0]]
        for (let i = 1; i < data.length; i++) {
            result.push(alpha * data[i] + (1 - alpha) * result[i - 1])
        }
        return result
    }

    /**
     * 保護極端值
     */
    private preserveExtremeValues(original: number[], smoothed: number[]): number[] {
        const result = [...smoothed]
        const threshold = 2 // 標準差倍數
        
        const mean = original.reduce((sum, val) => sum + val, 0) / original.length
        const std = Math.sqrt(
            original.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / original.length
        )
        
        for (let i = 0; i < original.length; i++) {
            const isExtreme = Math.abs(original[i] - mean) > threshold * std
            if (isExtreme) {
                // 保留一定比例的極端值特徵
                result[i] = 0.7 * original[i] + 0.3 * smoothed[i]
            }
        }
        
        return result
    }

    /**
     * 應用物理約束
     */
    private applyPhysicalConstraints(data: number[]): number[] {
        return data.map(val => {
            // 衛星距離約束：200km - 2000km（合理的LEO範圍）
            return Math.max(200000, Math.min(2000000, val))
        })
    }

    /**
     * 計算點置信度
     */
    private calculatePointConfidence(original: number, processed: number, parameters: any): number {
        const difference = Math.abs(original - processed)
        const relativeDifference = difference / original
        
        // 差異越小，置信度越高
        return Math.max(0, 1 - relativeDifference * 2)
    }

    /**
     * 評估處理結果
     */
    private evaluateProcessingResults(original: any[], processed: any[]): {
        noiseReductionRate: number
        signalEnhancementRatio: number
        physicalAccuracyScore: number
        visualClarityScore: number
    } {
        const originalSatDistances = original.map(d => d.satelliteDistance || d.satellite_distance || 0)
        const processedSatDistances = processed.map(d => d.satelliteDistance || d.satellite_distance || 0)
        
        // 噪聲減少率
        const originalNoise = this.calculateNoise(originalSatDistances)
        const processedNoise = this.calculateNoise(processedSatDistances)
        const noiseReductionRate = Math.max(0, (originalNoise - processedNoise) / originalNoise)
        
        // 信號增強比
        const originalSignal = this.calculateSignalStrength(originalSatDistances)
        const processedSignal = this.calculateSignalStrength(processedSatDistances)
        const signalEnhancementRatio = processedSignal / originalSignal
        
        // 物理準確度（保持原始趨勢的程度）
        const physicalAccuracyScore = this.calculateTrendSimilarity(originalSatDistances, processedSatDistances)
        
        // 視覺清晰度（變化的平滑度）
        const visualClarityScore = this.calculateSmoothness(processedSatDistances)
        
        return {
            noiseReductionRate,
            signalEnhancementRatio,
            physicalAccuracyScore,
            visualClarityScore
        }
    }

    /**
     * 計算噪聲水平
     */
    private calculateNoise(data: number[]): number {
        if (data.length < 3) return 0
        
        const secondDerivatives = []
        for (let i = 1; i < data.length - 1; i++) {
            const secondDerivative = data[i + 1] - 2 * data[i] + data[i - 1]
            secondDerivatives.push(Math.abs(secondDerivative))
        }
        
        return secondDerivatives.reduce((sum, val) => sum + val, 0) / secondDerivatives.length
    }

    /**
     * 計算信號強度
     */
    private calculateSignalStrength(data: number[]): number {
        const min = Math.min(...data)
        const max = Math.max(...data)
        const mean = data.reduce((sum, val) => sum + val, 0) / data.length
        return (max - min) / mean
    }

    /**
     * 計算趨勢相似度
     */
    private calculateTrendSimilarity(original: number[], processed: number[]): number {
        if (original.length !== processed.length || original.length < 3) return 1
        
        let matchingTrends = 0
        for (let i = 1; i < original.length - 1; i++) {
            const originalTrend = original[i + 1] - original[i - 1]
            const processedTrend = processed[i + 1] - processed[i - 1]
            
            if ((originalTrend > 0 && processedTrend > 0) || 
                (originalTrend < 0 && processedTrend < 0) ||
                (Math.abs(originalTrend) < 1000 && Math.abs(processedTrend) < 1000)) {
                matchingTrends++
            }
        }
        
        return matchingTrends / (original.length - 2)
    }

    /**
     * 計算平滑度
     */
    private calculateSmoothness(data: number[]): number {
        if (data.length < 3) return 1
        
        const variations = []
        for (let i = 1; i < data.length - 1; i++) {
            const variation = Math.abs(data[i + 1] - 2 * data[i] + data[i - 1])
            variations.push(variation)
        }
        
        const avgVariation = variations.reduce((sum, val) => sum + val, 0) / variations.length
        const avgValue = data.reduce((sum, val) => sum + val, 0) / data.length
        
        // 正規化平滑度分數
        return Math.max(0, 1 - (avgVariation / (avgValue * 0.01)))
    }

    /**
     * 生成處理建議
     */
    private generateRecommendations(metrics: any, qualityAnalysis: any): string[] {
        const recommendations = []
        
        if (metrics.noiseReductionRate > 0.6) {
            recommendations.push('✅ 降噪效果優秀，建議保持當前設定')
        } else if (metrics.noiseReductionRate < 0.3) {
            recommendations.push('⚠️ 降噪效果不佳，建議增加平滑窗口大小')
        }
        
        if (metrics.physicalAccuracyScore < 0.7) {
            recommendations.push('⚠️ 物理準確度較低，建議減少處理強度')
        }
        
        if (metrics.visualClarityScore < 0.8) {
            recommendations.push('💡 可進一步提升視覺清晰度，建議調整指數平滑參數')
        }
        
        if (qualityAnalysis.overallQuality === 'excellent' && metrics.noiseReductionRate > 0.8) {
            recommendations.push('🎯 處理效果優異，適合用於研究和展示')
        }
        
        return recommendations
    }

    /**
     * 計算百分位數
     */
    private calculatePercentile(data: number[], percentile: number): number {
        const sorted = [...data].sort((a, b) => a - b)
        const index = (percentile / 100) * (sorted.length - 1)
        const lower = Math.floor(index)
        const upper = Math.ceil(index)
        const weight = index - lower
        
        return sorted[lower] * (1 - weight) + sorted[upper] * weight
    }
}

// 預設配置
export const DEFAULT_PROCESSING_CONFIG: ProcessingConfig = {
    noisReductionStrategy: 'adaptive',
    preservePhysicalMeaning: true,
    enhanceTriggerPatterns: true,
    maintainTemporalAccuracy: true,
    movingAverageWindow: 5,
    exponentialSmoothingAlpha: 0.3,
    adaptiveThreshold: 0.15,
    signalToNoiseThreshold: 2.0,
    preserveExtremeEvents: true,
}

// 導出服務實例
export const intelligentDataProcessor = IntelligentDataProcessor.getInstance()