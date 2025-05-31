/**
 * DataVisualizationDashboard 組件測試
 */
import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import DataVisualizationDashboard from '../DataVisualizationDashboard'

// Mock 子組件
vi.mock('../charts/SystemStatusChart', () => ({
    default: () => (
        <div data-testid="system-status-chart">System Status Chart</div>
    ),
}))

vi.mock('../charts/UAVMetricsChart', () => ({
    default: () => <div data-testid="uav-metrics-chart">UAV Metrics Chart</div>,
}))

vi.mock('../charts/NetworkTopologyChart', () => ({
    default: () => (
        <div data-testid="network-topology-chart">Network Topology Chart</div>
    ),
}))

// Mock useWebSocket hook
vi.mock('../../../hooks/useWebSocket', () => ({
    default: () => ({
        isConnected: true,
        reconnectCount: 0,
        sendMessage: vi.fn(),
        disconnect: vi.fn(),
        connect: vi.fn(),
    }),
}))

describe('DataVisualizationDashboard', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('應該正確渲染儀表盤標題和連接狀態', () => {
        render(<DataVisualizationDashboard />)

        expect(screen.getByText('數據可視化儀表盤')).toBeInTheDocument()
        expect(screen.getByText('實時連接')).toBeInTheDocument()
        expect(screen.getByText('實時更新')).toBeInTheDocument()
    })

    it('應該正確渲染所有標籤', () => {
        render(<DataVisualizationDashboard />)

        expect(screen.getByText('總覽')).toBeInTheDocument()
        expect(screen.getByText('系統狀態')).toBeInTheDocument()
        expect(screen.getByText('UAV 監控')).toBeInTheDocument()
        expect(screen.getByText('網路拓撲')).toBeInTheDocument()
    })

    it('應該默認顯示總覽頁面', () => {
        render(<DataVisualizationDashboard />)

        // 總覽頁面應該顯示所有三個圖表
        expect(screen.getByTestId('system-status-chart')).toBeInTheDocument()
        expect(screen.getByTestId('uav-metrics-chart')).toBeInTheDocument()
        expect(screen.getByTestId('network-topology-chart')).toBeInTheDocument()
    })

    it('應該能夠切換到系統狀態標籤', () => {
        render(<DataVisualizationDashboard />)

        const systemTab = screen.getByText('系統狀態')
        fireEvent.click(systemTab)

        // 應該只顯示系統狀態圖表
        expect(screen.getByTestId('system-status-chart')).toBeInTheDocument()
        expect(
            screen.queryByTestId('uav-metrics-chart')
        ).not.toBeInTheDocument()
        expect(
            screen.queryByTestId('network-topology-chart')
        ).not.toBeInTheDocument()
    })

    it('應該能夠切換到UAV監控標籤', () => {
        render(<DataVisualizationDashboard />)

        const uavTab = screen.getByText('UAV 監控')
        fireEvent.click(uavTab)

        // 應該只顯示UAV圖表
        expect(
            screen.queryByTestId('system-status-chart')
        ).not.toBeInTheDocument()
        expect(screen.getByTestId('uav-metrics-chart')).toBeInTheDocument()
        expect(
            screen.queryByTestId('network-topology-chart')
        ).not.toBeInTheDocument()
    })

    it('應該能夠切換到網路拓撲標籤', () => {
        render(<DataVisualizationDashboard />)

        const networkTab = screen.getByText('網路拓撲')
        fireEvent.click(networkTab)

        // 應該只顯示網路拓撲圖表
        expect(
            screen.queryByTestId('system-status-chart')
        ).not.toBeInTheDocument()
        expect(
            screen.queryByTestId('uav-metrics-chart')
        ).not.toBeInTheDocument()
        expect(screen.getByTestId('network-topology-chart')).toBeInTheDocument()
    })

    it('應該能夠切換實時更新選項', () => {
        render(<DataVisualizationDashboard />)

        const realtimeToggle = screen.getByRole('checkbox')
        expect(realtimeToggle).toBeChecked()

        fireEvent.click(realtimeToggle)
        expect(realtimeToggle).not.toBeChecked()
    })

    it('應該正確顯示底部信息', () => {
        render(<DataVisualizationDashboard />)

        expect(screen.getByText('NTN Stack 數據可視化平台')).toBeInTheDocument()
        expect(screen.getByText('當前頁面: 總覽')).toBeInTheDocument()
    })

    it('應該應用自定義className', () => {
        const { container } = render(
            <DataVisualizationDashboard className="custom-class" />
        )

        expect(container.firstChild).toHaveClass(
            'data-visualization-dashboard',
            'custom-class'
        )
    })
})
