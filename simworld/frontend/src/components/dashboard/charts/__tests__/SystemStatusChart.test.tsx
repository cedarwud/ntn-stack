/**
 * SystemStatusChart 組件測試
 */
import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import SystemStatusChart from '../SystemStatusChart'
import * as netstackApi from '../../../../services/netstackApi'

// Mock NetStack API
vi.mock('../../../../services/netstackApi', () => ({
    getSystemStatus: vi.fn(),
}))

const mockSystemStatus = {
    status: 'healthy',
    timestamp: '2024-01-01T10:00:00Z',
    components: {
        netstack: {
            name: 'NetStack',
            healthy: true,
            status: 'running',
            version: '1.0.0',
            last_health_check: '2024-01-01T10:00:00Z',
            metrics: {
                cpu_usage: 45.2,
                memory_usage: 512.8,
                active_connections: 24,
            },
            error: null,
        },
        simworld: {
            name: 'SimWorld',
            healthy: false,
            status: 'error',
            version: '0.1.0',
            last_health_check: '2024-01-01T10:00:00Z',
            metrics: null,
            error: 'Connection failed',
        },
    },
    summary: {
        total_services: 2,
        healthy_services: 1,
        degraded_services: 1,
        last_updated: '2024-01-01T10:00:00Z',
    },
}

describe('SystemStatusChart', () => {
    beforeEach(() => {
        vi.clearAllMocks()
        // Mock Date.prototype.toLocaleString to return consistent format
        vi.spyOn(Date.prototype, 'toLocaleString').mockReturnValue(
            '1/1/2024, 10:00:00 AM'
        )
    })

    it('應該正確渲染載入狀態', () => {
        vi.mocked(netstackApi.getSystemStatus).mockImplementation(
            () => new Promise((resolve) => setTimeout(resolve, 1000))
        )

        render(<SystemStatusChart />)

        expect(screen.getByText('載入系統狀態中...')).toBeInTheDocument()
        expect(screen.getByText('載入系統狀態中...')).toBeInTheDocument()
    })

    it('應該正確渲染系統狀態數據', async () => {
        vi.mocked(netstackApi.getSystemStatus).mockResolvedValue(
            mockSystemStatus
        )

        render(<SystemStatusChart />)

        await waitFor(() => {
            expect(screen.getByText('系統狀態監控')).toBeInTheDocument()
        })

        // 檢查狀態指示器
        expect(screen.getByText('HEALTHY')).toBeInTheDocument()

        // 檢查摘要數據 - 使用更具體的查詢
        expect(screen.getByText('總服務數')).toBeInTheDocument()
        expect(screen.getByText('2')).toBeInTheDocument()
        expect(screen.getByText('健康服務')).toBeInTheDocument()

        // 使用 getAllByText 處理重複的文字
        const healthyValues = screen.getAllByText('1')
        expect(healthyValues.length).toBeGreaterThanOrEqual(1)

        expect(screen.getByText('異常服務')).toBeInTheDocument()

        // 檢查組件列表
        expect(screen.getByText('NetStack')).toBeInTheDocument()
        expect(screen.getByText('SimWorld')).toBeInTheDocument()
        expect(screen.getByText('v1.0.0')).toBeInTheDocument()
        expect(screen.getByText('v0.1.0')).toBeInTheDocument()

        // 檢查指標
        expect(screen.getByText('CPU:')).toBeInTheDocument()
        expect(screen.getByText('45.2%')).toBeInTheDocument()
        expect(screen.getByText('記憶體:')).toBeInTheDocument()
        expect(screen.getByText('512.8MB')).toBeInTheDocument()
        expect(screen.getByText('連線數:')).toBeInTheDocument()
        expect(screen.getByText('24')).toBeInTheDocument()

        // 檢查錯誤信息
        expect(screen.getByText('Connection failed')).toBeInTheDocument()
    })

    it('應該正確渲染錯誤狀態', async () => {
        vi.mocked(netstackApi.getSystemStatus).mockRejectedValue(
            new Error('Network error')
        )

        render(<SystemStatusChart />)

        await waitFor(() => {
            expect(screen.getByText('無法載入系統狀態')).toBeInTheDocument()
        })

        expect(screen.getByText('重試')).toBeInTheDocument()
    })

    it('應該支持自動刷新', async () => {
        vi.mocked(netstackApi.getSystemStatus).mockResolvedValue(
            mockSystemStatus
        )

        render(<SystemStatusChart refreshInterval={100} />)

        await waitFor(() => {
            expect(netstackApi.getSystemStatus).toHaveBeenCalledTimes(1)
        })

        // 等待自動刷新
        await waitFor(
            () => {
                expect(netstackApi.getSystemStatus).toHaveBeenCalledTimes(2)
            },
            { timeout: 200 }
        )
    })

    it('應該正確處理空數據', async () => {
        vi.mocked(netstackApi.getSystemStatus).mockResolvedValue(null as any)

        render(<SystemStatusChart />)

        await waitFor(() => {
            expect(screen.getByText('無系統狀態數據')).toBeInTheDocument()
        })
    })

    it('應該應用自定義 className', () => {
        vi.mocked(netstackApi.getSystemStatus).mockResolvedValue(
            mockSystemStatus
        )

        const { container } = render(
            <SystemStatusChart className="custom-class" />
        )

        expect(container.firstChild).toHaveClass(
            'system-status-chart',
            'custom-class'
        )
    })

    it('應該正確顯示健康狀態圖標', async () => {
        vi.mocked(netstackApi.getSystemStatus).mockResolvedValue(
            mockSystemStatus
        )

        render(<SystemStatusChart />)

        await waitFor(() => {
            const healthyIcon = screen.getByText('✅')
            const unhealthyIcon = screen.getByText('❌')

            expect(healthyIcon).toBeInTheDocument()
            expect(unhealthyIcon).toBeInTheDocument()
        })
    })

    it('應該正確顯示時間格式', async () => {
        vi.mocked(netstackApi.getSystemStatus).mockResolvedValue(
            mockSystemStatus
        )

        render(<SystemStatusChart />)

        await waitFor(() => {
            // 使用 getAllByText 處理重複的時間文字
            const lastCheckTexts = screen.getAllByText(/最後檢查:/)
            expect(lastCheckTexts.length).toBeGreaterThanOrEqual(1)

            const timeTexts = screen.getAllByText(/1\/1\/2024, 10:00:00 AM/)
            expect(timeTexts.length).toBeGreaterThanOrEqual(1)

            expect(screen.getByText(/最後更新:/)).toBeInTheDocument()
        })
    })
})
