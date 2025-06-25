import React, { useState, useEffect } from 'react'
import * as THREE from 'three'
import { Text } from '@react-three/drei'

interface AutomatedReportGeneratorProps {
    devices: any[]
    enabled: boolean
}

interface ReportSection {
    id: string
    title: string
    status: 'complete' | 'generating' | 'pending' | 'error'
    progress: number
    data: any
    lastGenerated: number
    timeToGenerate: number
}

interface SystemReport {
    id: string
    title: string
    type: 'daily' | 'weekly' | 'monthly' | 'incident' | 'performance'
    status: 'completed' | 'generating' | 'scheduled' | 'failed'
    scheduledTime: number
    completedTime?: number
    sections: ReportSection[]
    priority: 'high' | 'medium' | 'low'
    recipients: string[]
    fileSize: number
    summary: string
}

interface ReportMetrics {
    totalReports: number
    completedReports: number
    failedReports: number
    avgGenerationTime: number
    totalFileSize: number
    automationRate: number
}

const AutomatedReportGenerator: React.FC<AutomatedReportGeneratorProps> = ({ devices, enabled }) => {
    const [reports, setReports] = useState<SystemReport[]>([])
    const [metrics, setMetrics] = useState<ReportMetrics>({
        totalReports: 0,
        completedReports: 0,
        failedReports: 0,
        avgGenerationTime: 0,
        totalFileSize: 0,
        automationRate: 0
    })
    const [activeGenerations, setActiveGenerations] = useState<string[]>([])

    // 模擬報告生成系統
    useEffect(() => {
        if (!enabled) {
            setReports([])
            setActiveGenerations([])
            return
        }

        const generateReportsData = () => {
            const reportTypes = [
                {
                    title: '每日系統性能報告',
                    type: 'daily' as const,
                    priority: 'high' as const,
                    sections: [
                        '系統概覽', '性能指標', 'API 響應時間', '錯誤分析', 
                        '資源使用率', 'UAV 連接狀態', '衛星追蹤精度'
                    ]
                },
                {
                    title: '週度測試執行報告',
                    type: 'weekly' as const,
                    priority: 'medium' as const,
                    sections: [
                        '測試覆蓋率', '通過率統計', '性能回歸測試', 
                        '整合測試結果', '安全性測試', 'E2E 測試摘要'
                    ]
                },
                {
                    title: '月度架構健康報告',
                    type: 'monthly' as const,
                    priority: 'medium' as const,
                    sections: [
                        '系統穩定性', '容量規劃', '技術債務分析', 
                        '性能趨勢', '最佳化建議', '升級計畫'
                    ]
                },
                {
                    title: '事件分析報告',
                    type: 'incident' as const,
                    priority: 'high' as const,
                    sections: [
                        '事件時間軸', '根本原因分析', '影響評估', 
                        '恢復行動', '預防措施', '經驗教訓'
                    ]
                },
                {
                    title: '性能最佳化報告',
                    type: 'performance' as const,
                    priority: 'low' as const,
                    sections: [
                        '瓶頸分析', '最佳化機會', '成本效益分析', 
                        '實施建議', 'ROI 預測', '風險評估'
                    ]
                }
            ]

            const newReports: SystemReport[] = reportTypes.map((reportType, index) => {
                const sections: ReportSection[] = reportType.sections.map((sectionTitle, sIndex) => ({
                    id: `section_${index}_${sIndex}`,
                    title: sectionTitle,
                    status: Math.random() > 0.8 ? 'generating' : Math.random() > 0.1 ? 'complete' : 'error',
                    progress: Math.random() > 0.8 ? Math.floor(Math.random() * 100) : 100,
                    data: generateSectionData(sectionTitle),
                    lastGenerated: Date.now() - Math.floor(Math.random() * 86400000),
                    timeToGenerate: 30 + Math.random() * 120
                }))

                const allComplete = sections.every(s => s.status === 'complete')
                const hasError = sections.some(s => s.status === 'error')
                const isGenerating = sections.some(s => s.status === 'generating')

                let status: 'completed' | 'generating' | 'scheduled' | 'failed'
                if (hasError) status = 'failed'
                else if (isGenerating) status = 'generating'
                else if (allComplete) status = 'completed'
                else status = 'scheduled'

                return {
                    id: `report_${index}`,
                    title: reportType.title,
                    type: reportType.type,
                    status,
                    scheduledTime: Date.now() + Math.floor(Math.random() * 3600000),
                    completedTime: allComplete ? Date.now() - Math.floor(Math.random() * 1800000) : undefined,
                    sections,
                    priority: reportType.priority,
                    recipients: generateRecipients(),
                    fileSize: 0.5 + Math.random() * 2, // MB
                    summary: generateReportSummary(reportType.title)
                }
            })

            setReports(newReports)

            // 計算指標
            const totalReports = newReports.length
            const completedReports = newReports.filter(r => r.status === 'completed').length
            const failedReports = newReports.filter(r => r.status === 'failed').length
            const avgGenerationTime = newReports
                .filter(r => r.completedTime)
                .reduce((sum, r) => sum + (r.completedTime! - r.scheduledTime), 0) / 
                (completedReports || 1)
            const totalFileSize = newReports.reduce((sum, r) => sum + r.fileSize, 0)
            const automationRate = (completedReports / totalReports) * 100

            setMetrics({
                totalReports,
                completedReports,
                failedReports,
                avgGenerationTime: avgGenerationTime / 1000, // 轉為秒
                totalFileSize,
                automationRate
            })

            // 更新正在生成的報告
            setActiveGenerations(newReports
                .filter(r => r.status === 'generating')
                .map(r => r.id)
            )
        }

        const generateSectionData = (sectionTitle: string): any => {
            switch (sectionTitle) {
                case '系統概覽':
                    return {
                        uptime: '99.95%',
                        services: 25,
                        errors: 3,
                        warnings: 12
                    }
                case '性能指標':
                    return {
                        avgLatency: '28ms',
                        throughput: '1,250 req/s',
                        cpuUsage: '65%',
                        memoryUsage: '58%'
                    }
                case '測試覆蓋率':
                    return {
                        unitTests: '94%',
                        integrationTests: '87%',
                        e2eTests: '92%',
                        overallCoverage: '91%'
                    }
                default:
                    return {
                        status: 'complete',
                        dataPoints: Math.floor(Math.random() * 1000),
                        insights: Math.floor(Math.random() * 20)
                    }
            }
        }

        const generateRecipients = (): string[] => {
            const recipients = [
                'dev-team@company.com',
                'ops-team@company.com', 
                'qa-team@company.com',
                'management@company.com',
                'architects@company.com'
            ]
            return recipients.slice(0, 1 + Math.floor(Math.random() * 4))
        }

        const generateReportSummary = (title: string): string => {
            const summaries: { [key: string]: string } = {
                '每日系統性能報告': '系統運行穩定，性能指標正常，無重大問題發現',
                '週度測試執行報告': '測試覆蓋率達標，通過率良好，發現2個非關鍵性問題',
                '月度架構健康報告': '架構健康狀況良好，建議進行部分組件升級',
                '事件分析報告': '事件已解決，實施預防措施，系統穩定性提升',
                '性能最佳化報告': '識別3個最佳化機會，預期性能提升15-20%'
            }
            return summaries[title] || '報告生成完成，數據分析正常'
        }

        generateReportsData()
        const interval = setInterval(generateReportsData, 15000) // 15秒更新

        return () => clearInterval(interval)
    }, [enabled])

    if (!enabled) return null

    const getStatusColor = (status: string): string => {
        switch (status) {
            case 'completed': return '#2ed573'
            case 'generating': return '#3742fa'
            case 'scheduled': return '#ffa502'
            case 'failed': return '#ff4757'
            default: return '#747d8c'
        }
    }

    const getPriorityColor = (priority: string): string => {
        switch (priority) {
            case 'high': return '#ff4757'
            case 'medium': return '#ffa502'
            case 'low': return '#2ed573'
            default: return '#747d8c'
        }
    }

    const getTypeIcon = (type: string): string => {
        switch (type) {
            case 'daily': return '📅'
            case 'weekly': return '📊'
            case 'monthly': return '📈'
            case 'incident': return '🚨'
            case 'performance': return '⚡'
            default: return '📄'
        }
    }

    return (
        <>
            {/* 報告生成總覽 */}
            <group position={[-120, 120, 0]}>
                <Text
                    position={[0, 30, 0]}
                    fontSize={8}
                    color="#ffd700"
                    anchorX="center"
                    anchorY="middle"
                >
                    📋 自動化報告生成
                </Text>

                <Text
                    position={[0, 23, 0]}
                    fontSize={4}
                    color="#ffffff"
                    anchorX="center"
                    anchorY="middle"
                >
                    自動化率: {metrics.automationRate.toFixed(1)}%
                </Text>

                <Text
                    position={[0, 19, 0]}
                    fontSize={4}
                    color="#cccccc"
                    anchorX="center"
                    anchorY="middle"
                >
                    完成報告: {metrics.completedReports}/{metrics.totalReports}
                </Text>

                <Text
                    position={[0, 15, 0]}
                    fontSize={4}
                    color="#cccccc"
                    anchorX="center"
                    anchorY="middle"
                >
                    平均時間: {(metrics.avgGenerationTime / 60).toFixed(1)}分鐘
                </Text>

                <Text
                    position={[0, 11, 0]}
                    fontSize={4}
                    color="#cccccc"
                    anchorX="center"
                    anchorY="middle"
                >
                    總檔案大小: {metrics.totalFileSize.toFixed(1)}MB
                </Text>

                <Text
                    position={[0, 7, 0]}
                    fontSize={4}
                    color={metrics.failedReports > 0 ? '#ff4757' : '#2ed573'}
                    anchorX="center"
                    anchorY="middle"
                >
                    失敗報告: {metrics.failedReports}
                </Text>
            </group>

            {/* 報告狀態可視化 */}
            <group position={[0, 80, 0]}>
                <Text
                    position={[0, 25, 0]}
                    fontSize={6}
                    color="#00d4ff"
                    anchorX="center"
                    anchorY="middle"
                >
                    📊 報告狀態概覽
                </Text>

                {reports.map((report, index) => {
                    const angle = (index / reports.length) * Math.PI * 2
                    const radius = 35
                    const x = Math.cos(angle) * radius
                    const z = Math.sin(angle) * radius

                    return (
                        <group key={report.id} position={[x, 0, z]}>
                            {/* 報告狀態指示器 */}
                            <mesh>
                                <cylinderGeometry args={[3, 3, 2, 8]} />
                                <meshStandardMaterial
                                    color={getStatusColor(report.status)}
                                    emissive={getStatusColor(report.status)}
                                    emissiveIntensity={0.3}
                                />
                            </mesh>

                            {/* 優先級標示 */}
                            <mesh position={[0, 4, 0]}>
                                <boxGeometry args={[1.5, 1.5, 1.5]} />
                                <meshStandardMaterial
                                    color={getPriorityColor(report.priority)}
                                    emissive={getPriorityColor(report.priority)}
                                    emissiveIntensity={0.4}
                                />
                            </mesh>

                            {/* 報告類型圖標 */}
                            <Text
                                position={[0, 8, 0]}
                                fontSize={3}
                                color="#ffffff"
                                anchorX="center"
                                anchorY="middle"
                            >
                                {getTypeIcon(report.type)}
                            </Text>

                            {/* 報告標題 */}
                            <Text
                                position={[0, 12, 0]}
                                fontSize={2}
                                color="#ffffff"
                                anchorX="center"
                                anchorY="middle"
                                maxWidth={20}
                            >
                                {report.title}
                            </Text>

                            {/* 狀態文字 */}
                            <Text
                                position={[0, -6, 0]}
                                fontSize={2}
                                color={getStatusColor(report.status)}
                                anchorX="center"
                                anchorY="middle"
                            >
                                {report.status}
                            </Text>

                            {/* 生成進度 */}
                            {report.status === 'generating' && (
                                <group position={[0, -10, 0]}>
                                    <mesh>
                                        <boxGeometry args={[8, 1, 1]} />
                                        <meshStandardMaterial color="#333333" />
                                    </mesh>
                                    <mesh position={[(-8 + (8 * getReportProgress(report))) / 2, 0, 0.1]}>
                                        <boxGeometry args={[8 * getReportProgress(report), 1, 1]} />
                                        <meshStandardMaterial
                                            color="#3742fa"
                                            emissive="#3742fa"
                                            emissiveIntensity={0.3}
                                        />
                                    </mesh>
                                    <Text
                                        position={[0, -3, 0]}
                                        fontSize={1.5}
                                        color="#3742fa"
                                        anchorX="center"
                                        anchorY="middle"
                                    >
                                        {(getReportProgress(report) * 100).toFixed(0)}%
                                    </Text>
                                </group>
                            )}
                        </group>
                    )
                })}
            </group>

            {/* 報告段落詳情 */}
            <group position={[120, 80, 0]}>
                <Text
                    position={[0, 25, 0]}
                    fontSize={6}
                    color="#ff8800"
                    anchorX="center"
                    anchorY="middle"
                >
                    📝 段落生成狀態
                </Text>

                {reports
                    .filter(r => r.status === 'generating')
                    .slice(0, 3)
                    .map((report, reportIndex) => (
                        <group key={`details_${report.id}`} position={[0, 15 - reportIndex * 20, 0]}>
                            <Text
                                position={[0, 5, 0]}
                                fontSize={3}
                                color="#ffffff"
                                anchorX="center"
                                anchorY="middle"
                            >
                                {report.title}
                            </Text>

                            {report.sections.slice(0, 4).map((section, sectionIndex) => (
                                <group key={section.id} position={[0, 0 - sectionIndex * 4, 0]}>
                                    <mesh position={[-15, 0, 0]}>
                                        <sphereGeometry args={[0.8, 8, 8]} />
                                        <meshStandardMaterial
                                            color={getStatusColor(section.status)}
                                            emissive={getStatusColor(section.status)}
                                            emissiveIntensity={0.4}
                                        />
                                    </mesh>

                                    <Text
                                        position={[-10, 0, 0]}
                                        fontSize={2}
                                        color="#ffffff"
                                        anchorX="left"
                                        anchorY="middle"
                                    >
                                        {section.title}
                                    </Text>

                                    <Text
                                        position={[15, 0, 0]}
                                        fontSize={1.8}
                                        color={getStatusColor(section.status)}
                                        anchorX="right"
                                        anchorY="middle"
                                    >
                                        {section.status === 'generating' 
                                            ? `${section.progress}%` 
                                            : section.status
                                        }
                                    </Text>
                                </group>
                            ))}
                        </group>
                    ))
                }

                {reports.filter(r => r.status === 'generating').length === 0 && (
                    <Text
                        position={[0, 10, 0]}
                        fontSize={4}
                        color="#2ed573"
                        anchorX="center"
                        anchorY="middle"
                    >
                        ✅ 目前沒有報告在生成中
                    </Text>
                )}
            </group>

            {/* 報告類型統計 */}
            <group position={[-120, -20, 0]}>
                <Text
                    position={[0, 20, 0]}
                    fontSize={6}
                    color="#3742fa"
                    anchorX="center"
                    anchorY="middle"
                >
                    📈 報告類型統計
                </Text>

                {['daily', 'weekly', 'monthly', 'incident', 'performance'].map((type, index) => {
                    const reportsOfType = reports.filter(r => r.type === type)
                    const completedOfType = reportsOfType.filter(r => r.status === 'completed').length
                    const completionRate = reportsOfType.length > 0 ? (completedOfType / reportsOfType.length) * 100 : 0

                    return (
                        <group key={type} position={[0, 12 - index * 6, 0]}>
                            <Text
                                position={[-15, 0, 0]}
                                fontSize={2.5}
                                color="#ffffff"
                                anchorX="left"
                                anchorY="middle"
                            >
                                {getTypeIcon(type)} {type}
                            </Text>

                            <mesh position={[0, 0, 0]}>
                                <boxGeometry args={[completionRate / 5, 2, 2]} />
                                <meshStandardMaterial
                                    color={completionRate >= 80 ? '#2ed573' : completionRate >= 60 ? '#ffa502' : '#ff4757'}
                                    emissive={completionRate >= 80 ? '#2ed573' : completionRate >= 60 ? '#ffa502' : '#ff4757'}
                                    emissiveIntensity={0.2}
                                />
                            </mesh>

                            <Text
                                position={[15, 0, 0]}
                                fontSize={2.5}
                                color={completionRate >= 80 ? '#2ed573' : completionRate >= 60 ? '#ffa502' : '#ff4757'}
                                anchorX="right"
                                anchorY="middle"
                            >
                                {completionRate.toFixed(0)}%
                            </Text>
                        </group>
                    )
                })}
            </group>

            {/* 最近完成的報告 */}
            <group position={[120, -20, 0]}>
                <Text
                    position={[0, 20, 0]}
                    fontSize={6}
                    color="#2ed573"
                    anchorX="center"
                    anchorY="middle"
                >
                    ✅ 最近完成的報告
                </Text>

                {reports
                    .filter(r => r.status === 'completed')
                    .sort((a, b) => (b.completedTime || 0) - (a.completedTime || 0))
                    .slice(0, 5)
                    .map((report, index) => (
                        <group key={`completed_${report.id}`} position={[0, 12 - index * 4, 0]}>
                            <Text
                                position={[-20, 1, 0]}
                                fontSize={2.5}
                                color="#ffffff"
                                anchorX="left"
                                anchorY="middle"
                                maxWidth={25}
                            >
                                {report.title}
                            </Text>

                            <Text
                                position={[20, 1, 0]}
                                fontSize={2}
                                color="#cccccc"
                                anchorX="right"
                                anchorY="middle"
                            >
                                {report.fileSize.toFixed(1)}MB
                            </Text>

                            <Text
                                position={[20, -1.5, 0]}
                                fontSize={1.5}
                                color="#999999"
                                anchorX="right"
                                anchorY="middle"
                            >
                                {report.completedTime ? 
                                    new Date(report.completedTime).toLocaleString() : 
                                    '未知時間'
                                }
                            </Text>
                        </group>
                    ))
                }
            </group>

            {/* 效能指標總結 */}
            <group position={[0, -80, 0]}>
                <Text
                    position={[0, 15, 0]}
                    fontSize={6}
                    color="#ffd700"
                    anchorX="center"
                    anchorY="middle"
                >
                    📊 報告生成效能總結
                </Text>

                <Text
                    position={[-30, 8, 0]}
                    fontSize={3}
                    color="#ffffff"
                    anchorX="center"
                    anchorY="middle"
                >
                    總報告數: {metrics.totalReports}
                </Text>

                <Text
                    position={[0, 8, 0]}
                    fontSize={3}
                    color="#ffffff"
                    anchorX="center"
                    anchorY="middle"
                >
                    成功率: {((metrics.completedReports / metrics.totalReports) * 100).toFixed(1)}%
                </Text>

                <Text
                    position={[30, 8, 0]}
                    fontSize={3}
                    color="#ffffff"
                    anchorX="center"
                    anchorY="middle"
                >
                    平均時間: {(metrics.avgGenerationTime / 60).toFixed(1)}分
                </Text>

                <Text
                    position={[0, 3, 0]}
                    fontSize={3}
                    color={metrics.automationRate >= 90 ? '#2ed573' : '#ffa502'}
                    anchorX="center"
                    anchorY="middle"
                >
                    自動化程度: {metrics.automationRate.toFixed(1)}%
                    {metrics.automationRate >= 90 ? ' 🎯 優秀' : ' 📈 良好'}
                </Text>
            </group>
        </>
    )

    // 輔助函數：計算報告總進度
    function getReportProgress(report: SystemReport): number {
        const totalSections = report.sections.length
        const completedWeight = report.sections.filter(s => s.status === 'complete').length
        const generatingWeight = report.sections
            .filter(s => s.status === 'generating')
            .reduce((sum, s) => sum + (s.progress / 100), 0)

        return (completedWeight + generatingWeight) / totalSections
    }
}

export default AutomatedReportGenerator