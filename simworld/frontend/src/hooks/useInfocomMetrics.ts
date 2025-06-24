/**
 * Hook for fetching real INFOCOM 2024 algorithm metrics
 * 用於獲取實際的 INFOCOM 2024 算法性能指標
 */

import { useState, useEffect } from 'react';

interface InfocomMetrics {
    handoverLatency: number;      // 換手延遲 (ms)
    successRate: number;          // 成功率 (%)
    signalInterruption: number;   // 信號中斷時間 (ms)  
    energyEfficiency: number;     // 能耗效率
}

interface InfocomMetricsResponse {
    latency_ms: number;
    success_rate_percent: number;
    packet_loss_percent: number;
    throughput_mbps: number;
    latency_breakdown: {
        preparation: number;
        rrc_reconfig: number;
        random_access: number;
        ue_context: number;
        path_switch: number;
    };
    confidence_intervals: any;
    data_source: string;
}

const DEFAULT_METRICS: InfocomMetrics = {
    handoverLatency: 52.1,        // 原 hard code 值
    successRate: 91.2,            // 原 hard code 值
    signalInterruption: 22.4,     // 原 hard code 值
    energyEfficiency: 0.73        // 原 hard code 值
};

export const useInfocomMetrics = (enabled: boolean = true) => {
    const [metrics, setMetrics] = useState<InfocomMetrics>(DEFAULT_METRICS);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [dataSource, setDataSource] = useState<'calculated' | 'fallback'>('fallback');

    useEffect(() => {
        if (!enabled) return;

        const fetchMetrics = async () => {
            setIsLoading(true);
            setError(null);

            try {
                const response = await fetch('/api/algorithm-performance/infocom-2024-detailed');
                
                if (!response.ok) {
                    throw new Error(`API request failed: ${response.status}`);
                }

                const data: InfocomMetricsResponse = await response.json();
                
                // 轉換為前端需要的格式
                const calculatedMetrics: InfocomMetrics = {
                    handoverLatency: data.latency_ms,
                    successRate: data.success_rate_percent,
                    // 計算信號中斷時間：基於延遲分解中的關鍵階段
                    signalInterruption: data.latency_breakdown.rrc_reconfig + 
                                       data.latency_breakdown.random_access,
                    // 計算能耗效率：基於成功率和延遲的綜合指標
                    energyEfficiency: Math.min(1.0, 
                        (data.success_rate_percent / 100) * 
                        (1 - Math.min(0.5, data.latency_ms / 100))
                    )
                };

                setMetrics(calculatedMetrics);
                setDataSource('calculated');
                
                console.log('🚀 INFOCOM 2024 實際算法指標已更新:', {
                    source: data.data_source,
                    originalLatency: data.latency_ms,
                    calculatedMetrics
                });

            } catch (err) {
                console.warn('⚠️ INFOCOM 2024 算法指標獲取失敗，使用預設值:', err);
                setError(err instanceof Error ? err.message : 'Unknown error');
                setMetrics(DEFAULT_METRICS);
                setDataSource('fallback');
            } finally {
                setIsLoading(false);
            }
        };

        fetchMetrics();

        // 定期更新 (每30秒)
        const interval = setInterval(fetchMetrics, 30000);
        return () => clearInterval(interval);

    }, [enabled]);

    return {
        metrics,
        isLoading,
        error,
        dataSource,
        // 提供個別指標的便捷訪問
        handoverLatency: metrics.handoverLatency,
        successRate: metrics.successRate,
        signalInterruption: metrics.signalInterruption,
        energyEfficiency: metrics.energyEfficiency
    };
};