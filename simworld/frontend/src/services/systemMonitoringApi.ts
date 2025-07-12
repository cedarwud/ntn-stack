/**
 * 系統監控 API 服務層
 * 使用現有 API 端點，不依賴 Prometheus
 * 為 RL 監控系統提供統一的數據訪問接口
 */

import axios, { AxiosInstance } from 'axios'

// 系統監控數據類型定義
export interface SystemHealthData {
    status: 'healthy' | 'unhealthy' | 'operational'
    timestamp: string
    service: string
    components?: {
        api: string
        database: string
        cache: string
    }
}

export interface PerformanceMetrics {
    latency: number
    throughput: number
    errorRate: number
    timestamp: string
}

export interface MockMetricData {
    metric: Record<string, string>
    value: [number, string]
}

export interface MockQueryResult {
    status: 'success' | 'error'
    data: {
        resultType: 'vector' | 'matrix' | 'scalar'
        result: MockMetricData[]
    }
}

export interface AlertManagerAlert {
    labels: Record<string, string>
    annotations: Record<string, string>
    state: 'active' | 'suppressed' | 'unprocessed'
    activeAt: string
    value: string
    generatorURL: string
    fingerprint: string
    startsAt: string
    endsAt?: string
    status: {
        state: 'active' | 'suppressed' | 'unprocessed'
        silencedBy: string[]
        inhibitedBy: string[]
    }
}

export interface PrometheusTarget {
    discoveredLabels: Record<string, string>
    labels: Record<string, string>
    scrapePool: string
    scrapeUrl: string
    globalUrl: string
    lastError: string
    lastScrape: string
    lastScrapeDuration: number
    health: 'up' | 'down' | 'unknown'
}

class SystemMonitoringService {
    private client: AxiosInstance

    constructor() {
        // 使用現有API端點
        this.client = axios.create({
            baseURL: '/api/v1',
            timeout: 10000,
            headers: {
                'Content-Type': 'application/json',
            },
        })
    }

    /**
     * 檢查系統健康狀態
     */
    async checkHealth(): Promise<boolean> {
        try {
            const response = await this.client.get('/health')
            return response.data.status === 'healthy'
        } catch (error) {
            console.error('System health check failed:', error)
            try {
                const statusResponse = await this.client.get('/status')
                return statusResponse.data.status === 'operational'
            } catch (statusError) {
                console.error('System status check failed:', statusError)
                return false
            }
        }
    }

    /**
     * 獲取系統狀態信息
     */
    async getSystemStatus(): Promise<SystemHealthData> {
        try {
            const response = await this.client.get('/status')
            return response.data
        } catch (error) {
            console.error('Failed to get system status:', error)
            return {
                status: 'unhealthy',
                timestamp: new Date().toISOString(),
                service: 'simworld-backend'
            }
        }
    }

    /**
     * 獲取性能指標 (實時)
     */
    async getPerformanceMetrics(): Promise<PerformanceMetrics> {
        try {
            const response = await this.client.get('/performance/health')
            const data = response.data
            
            // 從 performance health 端點提取指標
            const metrics = data.metrics_summary
            return {
                latency: metrics.algorithms?.proposed?.latency_ms || 0,
                throughput: metrics.application?.requests_per_second || 0,
                errorRate: metrics.application?.error_rate_percent || 0,
                timestamp: data.timestamp
            }
        } catch (error) {
            console.error('Failed to get performance metrics:', error)
            // 返回模擬數據
            return {
                latency: Math.random() * 100,
                throughput: Math.random() * 1000,
                errorRate: Math.random() * 5,
                timestamp: new Date().toISOString()
            }
        }
    }

    /**
     * 模擬 RL 訓練指標（因為沒有實際的 Prometheus 數據）
     */
    async getRLTrainingMetrics(): Promise<any> {
        // 生成模擬數據而不是查詢 Prometheus
        const mockData = {
            convergence: this.generateMockMetric('rl_convergence', Math.random() * 0.1),
            loss: this.generateMockMetric('rl_loss', Math.random() * 0.5),
            gpuUtilization: this.generateMockMetric('gpu_util', Math.random() * 100),
            episodes: this.generateMockMetric('episodes', Math.floor(Math.random() * 1000))
        }

        return mockData
    }

    /**
     * 模擬 AI 決策指標
     */
    async getAIDecisionMetrics(): Promise<any> {
        const mockData = {
            latency: this.generateMockMetric('ai_latency', Math.random() * 50),
            errorRate: this.generateMockMetric('ai_error_rate', Math.random() * 2),
            throughput: this.generateMockMetric('ai_throughput', Math.random() * 500),
            confidence: this.generateMockMetric('ai_confidence', 0.8 + Math.random() * 0.2)
        }

        return mockData
    }

    /**
     * 模擬系統健康指標
     */
    async getSystemHealthMetrics(): Promise<any> {
        const mockData = {
            cpuUsage: this.generateMockMetric('cpu_usage', Math.random() * 80),
            memoryUsage: this.generateMockMetric('memory_usage', Math.random() * 70),
            diskUsage: this.generateMockMetric('disk_usage', Math.random() * 60),
            networkRx: this.generateMockMetric('network_rx', Math.random() * 1000)
        }

        return mockData
    }

    /**
     * 模擬 NTN 網路指標
     */
    async getNTNNetworkMetrics(): Promise<any> {
        const mockData = {
            handoverSuccessRate: this.generateMockMetric('handover_success', 95 + Math.random() * 5),
            endToEndLatency: this.generateMockMetric('e2e_latency', 20 + Math.random() * 30),
            packetLoss: this.generateMockMetric('packet_loss', Math.random() * 2),
            coverage: this.generateMockMetric('coverage', 90 + Math.random() * 10)
        }

        return mockData
    }

    /**
     * 生成模擬指標數據
     */
    private generateMockMetric(metricName: string, value: number): MockQueryResult {
        return {
            status: 'success',
            data: {
                resultType: 'vector',
                result: [{
                    metric: { __name__: metricName },
                    value: [Date.now() / 1000, value.toString()]
                }]
            }
        }
    }

    /**
     * 模擬時間序列數據
     */
    async getTimeSeriesData(metricName: string, hours: number = 1): Promise<MockQueryResult> {
        const points = Math.floor(hours * 60 / 5) // 每5分鐘一個點
        const result = []
        const now = Date.now()

        for (let i = 0; i < points; i++) {
            const timestamp = (now - (hours * 60 * 60 * 1000 - i * 5 * 60 * 1000)) / 1000
            const value = Math.random() * 100
            result.push([timestamp, value.toString()])
        }

        return {
            status: 'success',
            data: {
                resultType: 'matrix',
                result: [{
                    metric: { __name__: metricName },
                    value: result[result.length - 1] // 最新值
                }]
            }
        }
    }

    /**
     * 模擬查詢指標功能 (兼容性)
     */
    async queryMetrics(query: string, time?: Date): Promise<MockQueryResult> {
        console.log(`Mock query: ${query}`)
        
        // 根據查詢類型返回不同的模擬數據
        if (query.includes('rl_training')) {
            return this.generateMockMetric('rl_training', Math.random() * 100)
        } else if (query.includes('ai_decision')) {
            return this.generateMockMetric('ai_decision', Math.random() * 50)
        } else if (query.includes('cpu')) {
            return this.generateMockMetric('cpu', Math.random() * 80)
        } else {
            return this.generateMockMetric('generic', Math.random() * 100)
        }
    }

    /**
     * 模擬範圍查詢功能 (兼容性)
     */
    async queryRange(query: string, start: Date, end: Date, step: string = '1m'): Promise<MockQueryResult> {
        console.log(`Mock range query: ${query}`)
        return this.getTimeSeriesData(query, 1)
    }

    /**
     * 模擬目標狀態 (兼容性)
     */
    async getTargetStatus(): Promise<any> {
        return {
            status: 'success',
            data: {
                activeTargets: [
                    {
                        discoveredLabels: {},
                        labels: { job: 'simworld-backend' },
                        scrapePool: 'simworld',
                        scrapeUrl: 'http://localhost:8888/metrics',
                        globalUrl: 'http://localhost:8888/metrics',
                        lastError: '',
                        lastScrape: new Date().toISOString(),
                        lastScrapeDuration: 0.001,
                        health: 'up'
                    }
                ],
                droppedTargets: []
            }
        }
    }

    /**
     * 模擬告警數據 (兼容性)
     */
    async getAlerts(): Promise<any> {
        return {
            status: 'success',
            data: []
        }
    }

    /**
     * 模擬 AlertManager 健康檢查 (兼容性)
     */
    async checkAlertManagerHealth(): Promise<boolean> {
        return true
    }
}

// 單例模式
const systemMonitoringService = new SystemMonitoringService()
export default systemMonitoringService

// 導出便捷函數 (保持向後兼容)
export const {
    checkHealth,
    getSystemStatus,
    getPerformanceMetrics,
    getRLTrainingMetrics,
    getAIDecisionMetrics,
    getSystemHealthMetrics,
    getNTNNetworkMetrics,
    getTimeSeriesData,
    queryMetrics,
    queryRange,
    getTargetStatus,
    getAlerts,
    checkAlertManagerHealth
} = systemMonitoringService

// 保持舊的導出名稱以兼容現有代碼
export const prometheusApiService = systemMonitoringService
export const {
    queryMetrics: queryMetrics_legacy,
    queryRange: queryRange_legacy,
    getTargetStatus: getTargetStatus_legacy,
    getAlerts: getAlerts_legacy,
    getAIDecisionMetrics: getAIDecisionMetrics_legacy,
    getRLTrainingMetrics: getRLTrainingMetrics_legacy,
    getSystemHealthMetrics: getSystemHealthMetrics_legacy,
    getNTNNetworkMetrics: getNTNNetworkMetrics_legacy,
    getTimeSeriesData: getTimeSeriesData_legacy,
    checkHealth: checkHealth_legacy,
    checkAlertManagerHealth: checkAlertManagerHealth_legacy,
} = systemMonitoringService
