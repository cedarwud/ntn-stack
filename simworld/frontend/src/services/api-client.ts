/* eslint-disable @typescript-eslint/no-explicit-any */
import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { getApiConfig } from '../config/api-config'

const API_CONFIG = getApiConfig()

class NetStackApiClient {
    private client: AxiosInstance

    constructor() {
        this.client = axios.create({
            baseURL: API_CONFIG.netstack.baseUrl,
            timeout: 10000,
            headers: {
                'Content-Type': 'application/json',
            },
        })
    }

    private async request<T>(
        method: 'get' | 'post' | 'put' | 'delete',
        url: string,
        data: any = null
    ): Promise<T> {
        try {
            const response: AxiosResponse<T> = await this.client[method](
                url,
                data
            )
            return response.data
        } catch (error) {
            console.error(`API Error on ${method.toUpperCase()} ${url}:`, error)
            throw error
        }
    }

    get<T>(url: string): Promise<T> {
        return this.request<T>('get', url)
    }

    post<T>(url: string, data: any): Promise<T> {
        return this.request<T>('post', url, data)
    }

    /**
     * 獲取 AI 決策引擎的健康狀態。
     */
    getAIDecisionEngineHealth() {
        // 新的 v2 協調器端點
        return this.get<any>('/api/v2/decision/health')
    }

    /**
     * 獲取 AI 決策引擎的狀態。
     */
    getAIDecisionEngineStatus() {
        return this.get<any>('/api/v2/decision/status')
    }

    /**
     * 獲取 RL 訓練會話狀態（真實數據）
     */
    getRLTrainingSessions() {
        return this.get<any>('/api/v1/rl/training/sessions')
    }

    /**
     * 控制 AI 決策引擎的訓練過程。
     * @param action 'start' 或 'stop'
     * @param algorithm 如果 action 是 'start'，則需要指定算法
     */
    controlTraining(action: 'start' | 'stop', algorithm?: string) {
        return this.post<any>('/api/v2/decision/training-simple', {
            action,
            algorithm,
        })
    }

    /**
     * 獲取訓練狀態摘要，用於前端狀態同步
     */
    getTrainingStatusSummary() {
        return this.get<any>('/api/v1/rl/training/status-summary')
    }

    /**
     * 停止所有活躍的訓練會話
     */
    stopAllTraining() {
        return this.post<any>('/api/v1/rl/training/stop-all', {})
    }

    /**
     * 根據會話 ID 停止特定訓練會話
     */
    stopTrainingSession(sessionId: string) {
        return this.post<any>(`/api/v1/rl/training/stop/${sessionId}`, {})
    }

    /**
     * 獲取系統資源監控數據
     */
    getSystemResources() {
        return this.get<any>('/api/v2/decision/status')
    }

    /**
     * 獲取訓練性能指標
     */
    getTrainingPerformanceMetrics() {
        return this.get<any>('/api/v1/rl/training/performance-metrics')
    }
}

export const apiClient = new NetStackApiClient() 