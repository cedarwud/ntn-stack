/**
 * NetworkTopologyChart 組件測試
 */
import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import NetworkTopologyChart from '../NetworkTopologyChart'
import * as netstackApi from '../../../../services/netstackApi'

// Mock NetStack API
vi.mock('../../../../services/netstackApi', () => ({
    getMeshTopology: vi.fn(),
    getMeshNodes: vi.fn(),
}))

const mockTopologyData = {
    links: [
        {
            source: 'node1',
            target: 'node2',
            type: 'mesh',
            status: 'active',
        },
    ],
}

const mockNodesData = {
    nodes: [
        {
            id: 'node1',
            name: '節點1',
            type: 'mesh',
            status: 'active',
        },
        {
            id: 'node2',
            name: '節點2',
            type: 'uav',
            status: 'active',
        },
    ],
}

describe('NetworkTopologyChart', () => {
    beforeEach(() => {
        vi.clearAllMocks()
    })

    it('應該正確渲染載入狀態', () => {
        vi.mocked(netstackApi.getMeshTopology).mockImplementation(
            () => new Promise((resolve) => setTimeout(resolve, 1000))
        )
        vi.mocked(netstackApi.getMeshNodes).mockImplementation(
            () => new Promise((resolve) => setTimeout(resolve, 1000))
        )

        render(<NetworkTopologyChart />)

        expect(screen.getByText('載入網路拓撲中...')).toBeInTheDocument()
    })

    it('應該正確渲染網路拓撲數據', async () => {
        vi.mocked(netstackApi.getMeshTopology).mockResolvedValue(
            mockTopologyData
        )
        vi.mocked(netstackApi.getMeshNodes).mockResolvedValue(mockNodesData)

        render(<NetworkTopologyChart />)

        await waitFor(() => {
            expect(screen.getByText('網路拓撲圖')).toBeInTheDocument()
        })

        // 檢查圖例
        expect(screen.getByText('網關')).toBeInTheDocument()
        expect(screen.getByText('Mesh 節點')).toBeInTheDocument()
        expect(screen.getByText('UAV')).toBeInTheDocument()

        // 檢查底部統計
        expect(screen.getByText('節點數: 2')).toBeInTheDocument()
        expect(screen.getByText('連接數: 1')).toBeInTheDocument()
    })

    it('應該正確處理API錯誤並顯示模擬數據', async () => {
        vi.mocked(netstackApi.getMeshTopology).mockRejectedValue(
            new Error('Network error')
        )
        vi.mocked(netstackApi.getMeshNodes).mockRejectedValue(
            new Error('Network error')
        )

        render(<NetworkTopologyChart />)

        await waitFor(() => {
            expect(screen.getByText('網路拓撲圖')).toBeInTheDocument()
        })

        // 應該顯示錯誤通知
        expect(
            screen.getByText(/無法載入網路拓撲數據 \(顯示模擬數據\)/)
        ).toBeInTheDocument()
        expect(screen.getByText('重試')).toBeInTheDocument()

        // 仍應顯示模擬數據
        expect(screen.getByText('節點數: 6')).toBeInTheDocument()
        expect(screen.getByText('連接數: 5')).toBeInTheDocument()
    })

    it('應該支持自動刷新', async () => {
        vi.mocked(netstackApi.getMeshTopology).mockResolvedValue(
            mockTopologyData
        )
        vi.mocked(netstackApi.getMeshNodes).mockResolvedValue(mockNodesData)

        render(<NetworkTopologyChart refreshInterval={100} />)

        await waitFor(() => {
            expect(netstackApi.getMeshTopology).toHaveBeenCalledTimes(1)
            expect(netstackApi.getMeshNodes).toHaveBeenCalledTimes(1)
        })

        // 等待自動刷新
        await waitFor(
            () => {
                expect(netstackApi.getMeshTopology).toHaveBeenCalledTimes(2)
                expect(netstackApi.getMeshNodes).toHaveBeenCalledTimes(2)
            },
            { timeout: 200 }
        )
    })

    it('應該正確應用自定義屬性', () => {
        vi.mocked(netstackApi.getMeshTopology).mockResolvedValue(
            mockTopologyData
        )
        vi.mocked(netstackApi.getMeshNodes).mockResolvedValue(mockNodesData)

        const { container } = render(
            <NetworkTopologyChart
                className="custom-class"
                width={600}
                height={400}
            />
        )

        expect(container.firstChild).toHaveClass(
            'network-topology-chart',
            'custom-class'
        )
    })
})
