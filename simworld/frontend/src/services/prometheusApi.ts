/**
 * Prometheus API 服務層
 * 階段8：監控系統前端整合
 * 提供對 Prometheus 監控數據的統一訪問接口
 */

import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { getApiConfig } from '../config/api-config'

// Prometheus 查詢結果類型定義
export interface PrometheusMetric {
    metric: Record<string, string>
    value: [number, string]
}

export interface PrometheusRangeMetric {
    metric: Record<string, string>
    values: Array<[number, string]>
}

export interface PrometheusQueryResult {
    status: 'success' | 'error'
    data: {
        resultType: 'matrix' | 'vector' | 'scalar' | 'string'
        result: PrometheusMetric[]
    }
    errorType?: string
    error?: string
}

export interface PrometheusRangeResult {
    status: 'success' | 'error'
    data: {
        resultType: 'matrix' | 'vector'
        result: PrometheusRangeMetric[]
    }
    errorType?: string
    error?: string
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

export interface PrometheusTargetsResult {
    status: 'success' | 'error'
    data: {
        activeTargets: PrometheusTarget[]
        droppedTargets: PrometheusTarget[]
    }
}

export interface AlertManagerAlert {
    annotations: Record<string, string>
    endsAt: string
    fingerprint: string
    receivers: Array<{ name: string }>
    startsAt: string
    status: {
        inhibitedBy: string[]
        silencedBy: string[]
        state: 'active' | 'suppressed' | 'unprocessed'
    }
    updatedAt: string
    generatorURL: string
    labels: Record<string, string>
}

export interface AlertManagerAlertsResult {
    status: 'success' | 'error'
    data: AlertManagerAlert[]
}

class PrometheusApiService {
    private client: AxiosInstance
    private alertManagerClient: AxiosInstance
    private readonly prometheusUrl: string
    private readonly alertManagerUrl: string

    constructor() {
        // 從環境變數或配置獲取監控服務地址
        this.prometheusUrl = import.meta.env.VITE_PROMETHEUS_URL || 'http://localhost:9090'
        this.alertManagerUrl = import.meta.env.VITE_ALERTMANAGER_URL || 'http://localhost:9093'

        // Prometheus 客戶端
        this.client = axios.create({
            baseURL: this.prometheusUrl,
            timeout: 10000,
            headers: {
                'Content-Type': 'application/json',
            },
        })

        // AlertManager 客戶端
        this.alertManagerClient = axios.create({
            baseURL: this.alertManagerUrl,
            timeout: 10000,
            headers: {
                'Content-Type': 'application/json',
            },
        })
    }

    /**
     * 執行 Prometheus 即時查詢
     * @param query PromQL 查詢語句
     * @param time 可選的查詢時間戳
     */
    async queryMetrics(query: string, time?: Date): Promise<PrometheusQueryResult> {
        try {
            const params: Record<string, string> = { query }
            if (time) {
                params.time = (time.getTime() / 1000).toString()
            }

            const response: AxiosResponse<PrometheusQueryResult> = await this.client.get(
                '/api/v1/query',
                { params }
            )
            return response.data
        } catch (error) {
            console.error('Prometheus query error:', error)
            throw new Error(`Prometheus 查詢失敗: ${error}`)
        }
    }

    /**
     * 執行 Prometheus 範圍查詢
     * @param query PromQL 查詢語句
     * @param start 開始時間
     * @param end 結束時間
     * @param step 查詢步長 (例如: "15s", "1m", "5m")
     */
    async queryRange(
        query: string,
        start: Date,
        end: Date,
        step: string = '15s'
    ): Promise<PrometheusRangeResult> {
        try {
            const params = {
                query,
                start: (start.getTime() / 1000).toString(),
                end: (end.getTime() / 1000).toString(),
                step,
            }

            const response: AxiosResponse<PrometheusRangeResult> = await this.client.get(
                '/api/v1/query_range',
                { params }
            )
            return response.data
        } catch (error) {
            console.error('Prometheus range query error:', error)
            throw new Error(`Prometheus 範圍查詢失敗: ${error}`)
        }
    }

    /**
     * 獲取 Prometheus 監控目標狀態
     */
    async getTargetStatus(): Promise<PrometheusTargetsResult> {
        try {
            const response: AxiosResponse<PrometheusTargetsResult> = await this.client.get(
                '/api/v1/targets'
            )
            return response.data
        } catch (error) {
            console.error('Prometheus targets error:', error)
            throw new Error(`Prometheus 目標狀態查詢失敗: ${error}`)
        }
    }

    /**
     * 獲取 AlertManager 告警列表
     */
    async getAlerts(): Promise<AlertManagerAlertsResult> {
        try {
            const response: AxiosResponse<AlertManagerAlert[]> = await this.alertManagerClient.get(
                '/api/v1/alerts'
            )
            return {
                status: 'success',
                data: response.data
            }
        } catch (error) {
            console.error('AlertManager alerts error:', error)
            throw new Error(`AlertManager 告警查詢失敗: ${error}`)
        }
    }

    /**
     * AI 決策引擎監控專用查詢
     */
    async getAIDecisionMetrics() {
        const metrics = {
            // AI 決策延遲 (95分位)
            latency: await this.queryMetrics(
                'histogram_quantile(0.95, rate(ai_decision_latency_seconds_bucket[5m]))'
            ),
            // AI 決策錯誤率
            errorRate: await this.queryMetrics(
                'rate(ai_decision_errors_total[5m]) / rate(ai_decision_requests_total[5m]) * 100'
            ),
            // AI 決策吞吐量
            throughput: await this.queryMetrics(
                'rate(ai_decision_requests_total[5m])'
            ),
            // AI 決策置信度
            confidence: await this.queryMetrics(
                'avg_over_time(ai_decision_confidence_score[5m])'
            ),
        }
        return metrics
    }

    /**
     * RL 訓練監控專用查詢
     */
    async getRLTrainingMetrics() {
        const metrics = {
            // RL 訓練收斂狀態
            convergence: await this.queryMetrics(
                'avg_over_time(rl_training_reward_mean[10m]) - avg_over_time(rl_training_reward_mean[10m] offset 10m)'
            ),
            // RL 訓練損失
            loss: await this.queryMetrics(
                'avg_over_time(rl_training_loss[5m])'
            ),
            // GPU 利用率
            gpuUtilization: await this.queryMetrics(
                'avg_over_time(rl_training_gpu_utilization_percent[5m])'
            ),
            // Episodes 完成數
            episodes: await this.queryMetrics(
                'increase(rl_training_episodes_total[15m])'
            ),
        }
        return metrics
    }

    /**
     * 系統健康監控專用查詢
     */
    async getSystemHealthMetrics() {
        const metrics = {
            // CPU 使用率
            cpuUsage: await this.queryMetrics(
                '100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
            ),
            // 記憶體使用率
            memoryUsage: await this.queryMetrics(
                '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
            ),
            // 磁碟使用率
            diskUsage: await this.queryMetrics(
                '(1 - (node_filesystem_avail_bytes{fstype!="tmpfs"} / node_filesystem_size_bytes{fstype!="tmpfs"})) * 100'
            ),
            // 網路接收流量
            networkRx: await this.queryMetrics(
                'rate(node_network_receive_bytes_total[5m])'
            ),
        }
        return metrics
    }

    /**
     * NTN 網路性能監控專用查詢
     */
    async getNTNNetworkMetrics() {
        const metrics = {
            // 切換成功率
            handoverSuccessRate: await this.queryMetrics(
                'rate(handover_success_total[5m]) / (rate(handover_success_total[5m]) + rate(handover_failure_total[5m])) * 100'
            ),
            // 端到端延遲
            endToEndLatency: await this.queryMetrics(
                'histogram_quantile(0.95, rate(ntn_end_to_end_latency_seconds_bucket[5m]))'
            ),
            // 丟包率
            packetLoss: await this.queryMetrics(
                'rate(ntn_packets_dropped_total[5m]) / rate(ntn_packets_total[5m]) * 100'
            ),
            // 衛星覆蓋率
            coverage: await this.queryMetrics(
                'ntn_coverage_percentage'
            ),
        }
        return metrics
    }

    /**
     * 獲取時間序列數據 (用於圖表展示)
     * @param query PromQL 查詢
     * @param hours 過去幾小時的數據
     */
    async getTimeSeriesData(query: string, hours: number = 1) {
        const end = new Date()
        const start = new Date(end.getTime() - hours * 60 * 60 * 1000)
        return this.queryRange(query, start, end, '1m')
    }

    /**
     * 檢查 Prometheus 服務健康狀態
     */
    async checkHealth(): Promise<boolean> {
        try {
            const response = await this.client.get('/-/healthy')
            return response.status === 200
        } catch (error) {
            console.error('Prometheus health check failed:', error)
            return false
        }
    }

    /**
     * 檢查 AlertManager 服務健康狀態
     */
    async checkAlertManagerHealth(): Promise<boolean> {
        try {
            const response = await this.alertManagerClient.get('/-/healthy')
            return response.status === 200
        } catch (error) {
            console.error('AlertManager health check failed:', error)
            return false
        }
    }
}

// 單例模式
const prometheusApiService = new PrometheusApiService()
export default prometheusApiService

// 導出便捷函數
export const {
    queryMetrics,
    queryRange,
    getTargetStatus,
    getAlerts,
    getAIDecisionMetrics,
    getRLTrainingMetrics,
    getSystemHealthMetrics,
    getNTNNetworkMetrics,
    getTimeSeriesData,
    checkHealth,
    checkAlertManagerHealth,
} = prometheusApiService