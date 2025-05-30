/**
 * UAVMetricsChart 組件測試
 */
import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import UAVMetricsChart from '../UAVMetricsChart'
import * as netstackApi from '../../../../services/netstackApi'

// Mock NetStack API
vi.mock('../../../../services/netstackApi', () => ({
    getUAVList: vi.fn(),
}))

const mockUAVData = {
    uavs: [
        {
            uav_id: 'uav-001',
            name: 'UAV-Alpha',
            flight_status: 'flying',
            ue_connection_status: 'connected',
            current_position: {
                latitude: 25.033,
                longitude: 121.5654,
                altitude: 100.5,
                speed: 15.2,
                heading: 45.0,
                timestamp: '2024-01-01T10:00:00Z',
            },
            signal_quality: {
                rsrp_dbm: -85.5,
                rsrq_db: -12.3,
                sinr_db: 15.8,
                cqi: 12,
                throughput_mbps: 50.2,
                latency_ms: 12.5,
                packet_loss_rate: 0.001,
                jitter_ms: 2.1,
                link_budget_margin_db: 8.5,
                doppler_shift_hz: 125.0,
                beam_alignment_score: 0.95,
                interference_level_db: -95.2,
                timestamp: '2024-01-01T10:00:00Z',
                measurement_confidence: 0.98,
            },
            last_update: '2024-01-01T10:00:00Z',
        },
    ],
    total: 1,
}

describe('UAVMetricsChart', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        vi.spyOn(Date.prototype, 'toLocaleString').mockReturnValue(
            '1/1/2024, 10:00:00 AM'
        )
    })

    it('應該正確渲染載入狀態', () => {
        vi.mocked(netstackApi.getUAVList).mockImplementation(
            () => new Promise((resolve) => setTimeout(resolve, 1000))
        )

        render(<UAVMetricsChart />)

        expect(screen.getByText('載入 UAV 數據中...')).toBeInTheDocument()
    })

    it('應該正確渲染UAV數據', async () => {
        vi.mocked(netstackApi.getUAVList).mockResolvedValue(mockUAVData)

        render(<UAVMetricsChart />)

        await waitFor(() => {
            expect(screen.getByText('UAV 監控面板')).toBeInTheDocument()
        })

        // 檢查UAV選擇器
        expect(screen.getByText('UAV-Alpha (uav-001...)')).toBeInTheDocument()

        // 檢查基本狀態
        expect(screen.getByText('基本狀態')).toBeInTheDocument()
        expect(screen.getByText('flying')).toBeInTheDocument()
        expect(screen.getByText('connected')).toBeInTheDocument()

        // 檢查位置信息
        expect(screen.getByText('位置信息')).toBeInTheDocument()
        expect(screen.getByText('25.033000°')).toBeInTheDocument()
        expect(screen.getByText('121.565400°')).toBeInTheDocument()
        expect(screen.getByText('100.5m')).toBeInTheDocument()

        // 檢查信號質量
        expect(screen.getByText('信號質量')).toBeInTheDocument()
        expect(screen.getByText('-85.5 dBm')).toBeInTheDocument()
        expect(screen.getByText('50.20 Mbps')).toBeInTheDocument()
    })

    it('應該正確渲染錯誤狀態', async () => {
        vi.mocked(netstackApi.getUAVList).mockRejectedValue(
            new Error('Network error')
        )

        render(<UAVMetricsChart />)

        await waitFor(() => {
            expect(screen.getByText('無法載入 UAV 數據')).toBeInTheDocument()
        })

        expect(screen.getByText('重試')).toBeInTheDocument()
    })

    it('應該正確處理無UAV數據', async () => {
        vi.mocked(netstackApi.getUAVList).mockResolvedValue({
            uavs: [],
            total: 0,
        })

        render(<UAVMetricsChart />)

        await waitFor(() => {
            expect(screen.getByText('無 UAV 數據')).toBeInTheDocument()
        })
    })

    it('應該支持自動刷新', async () => {
        vi.mocked(netstackApi.getUAVList).mockResolvedValue(mockUAVData)

        render(<UAVMetricsChart refreshInterval={100} />)

        await waitFor(() => {
            expect(netstackApi.getUAVList).toHaveBeenCalledTimes(1)
        })

        // 等待自動刷新
        await waitFor(
            () => {
                expect(netstackApi.getUAVList).toHaveBeenCalledTimes(2)
            },
            { timeout: 200 }
        )
    })
})
