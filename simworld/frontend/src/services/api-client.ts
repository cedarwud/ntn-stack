/* eslint-disable @typescript-eslint/no-explicit-any */
import { netstackFetch } from '../config/api-config'

class NetStackApiClient {
    private async request<T>(
        method: 'GET' | 'POST' | 'PUT' | 'DELETE',
        url: string,
        data: any = null
    ): Promise<T> {
        try {
            const options: RequestInit = {
                method,
                headers: {
                    'Content-Type': 'application/json',
                },
            }

            if (data && (method === 'POST' || method === 'PUT')) {
                options.body = JSON.stringify(data)
            }

            const response = await netstackFetch(url, options)
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`)
            }

            return await response.json()
        } catch (error) {
            console.error(`API Error on ${method} ${url}:`, error)
            throw error
        }
    }

    get<T>(url: string): Promise<T> {
        return this.request<T>('GET', url)
    }

    post<T>(url: string, data: any): Promise<T> {
        return this.request<T>('POST', url, data)
    }

    /**
     * 獲取 AI 決策引擎的健康狀態。
     */
    getAIDecisionEngineHealth() {
        // 新的 v2 協調器端點 - 這是 SimWorld 後端的端點
        return this.get<any>('/api/v2/decision/health')
    }

    /**
     * 獲取 AI 決策引擎的狀態。
     */
    getAIDecisionEngineStatus() {
        return this.get<any>('/api/v2/decision/status')
    }


    /**
     * 獲取系統資源監控數據
     */
    getSystemResources() {
        return this.get<any>('/api/v2/decision/status')
    }


    /**
     * 獲取AI推薦數據
     */
    getAIRecommendations() {
        return this.get<any>('/api/v2/decision/recommendations')
    }

    /**
     * 獲取AI分析上下文
     */
    getAIAnalysisContext() {
        return this.get<any>('/api/v2/decision/analysis-context')
    }

    /**
     * 獲取AI分析結果
     */
    getAIAnalysis() {
        return this.get<any>('/api/v2/decision/analysis')
    }
}

export const apiClient = new NetStackApiClient()