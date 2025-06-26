import React, { useState, useEffect } from 'react'
import { Text } from '@react-three/drei'

interface Device {
    id: string
    name: string
    type: string
    status: string
}

interface TestResultsVisualizationProps {
    devices: Device[]
    enabled: boolean
}

interface TestSuite {
    id: string
    name: string
    category: 'unit' | 'integration' | 'e2e' | 'performance'
    status: 'pass' | 'fail' | 'running' | 'pending'
    progress: number
    testCount: number
    passCount: number
    failCount: number
    duration: number
    lastRun: number
    coverage: number
    criticalPath: boolean
}

interface TestCase {
    id: string
    suiteId: string
    name: string
    status: 'pass' | 'fail' | 'running' | 'pending'
    duration: number
    errorMessage?: string
    assertions: number
    timestamp: number
}

interface TestMetrics {
    totalSuites: number
    passingSuites: number
    failingSuites: number
    totalTests: number
    passingTests: number
    failingTests: number
    overallCoverage: number
    averageDuration: number
    successRate: number
}

const TestResultsVisualization: React.FC<TestResultsVisualizationProps> = ({
    enabled,
}) => {
    const [testSuites, setTestSuites] = useState<TestSuite[]>([])
    const [testCases, setTestCases] = useState<TestCase[]>([])
    const [metrics, setMetrics] = useState<TestMetrics>({
        totalSuites: 0,
        passingSuites: 0,
        failingSuites: 0,
        totalTests: 0,
        passingTests: 0,
        failingTests: 0,
        overallCoverage: 0,
        averageDuration: 0,
        successRate: 0,
    })

    // 模擬測試數據
    useEffect(() => {
        if (!enabled) {
            setTestSuites([])
            setTestCases([])
            return
        }

        const generateTestData = () => {
            const suiteNames = [
                'NetStack API 單元測試',
                'SimWorld 後端測試',
                'UAV 連接整合測試',
                '衛星軌道計算測試',
                'Mesh 網路故障轉移測試',
                'AI-RAN 抗干擾測試',
                '端到端性能測試',
                '負載壓力測試',
                '安全性測試',
                'UI 組件測試',
            ]

            const categories: (
                | 'unit'
                | 'integration'
                | 'e2e'
                | 'performance'
            )[] = [
                'unit',
                'unit',
                'integration',
                'unit',
                'integration',
                'integration',
                'e2e',
                'performance',
                'integration',
                'unit',
            ]

            const newSuites: TestSuite[] = suiteNames.map((name, index) => {
                const testCount = 5 + Math.floor(Math.random() * 20)
                const passCount = Math.floor(
                    testCount * (0.7 + Math.random() * 0.3)
                )
                const failCount = testCount - passCount
                const status = failCount > 0 ? 'fail' : 'pass'

                return {
                    id: `suite_${index}`,
                    name,
                    category: categories[index],
                    status: Math.random() < 0.05 ? 'running' : status,
                    progress:
                        Math.random() < 0.95
                            ? 100
                            : Math.floor(Math.random() * 100),
                    testCount,
                    passCount,
                    failCount,
                    duration: 1000 + Math.random() * 5000,
                    lastRun: Date.now() - Math.floor(Math.random() * 3600000),
                    coverage: 60 + Math.random() * 40,
                    criticalPath: Math.random() < 0.3,
                }
            })

            const newCases: TestCase[] = []
            newSuites.forEach((suite) => {
                for (let i = 0; i < Math.min(suite.testCount, 5); i++) {
                    newCases.push({
                        id: `case_${suite.id}_${i}`,
                        suiteId: suite.id,
                        name: `測試案例 ${i + 1}`,
                        status: i < suite.passCount ? 'pass' : 'fail',
                        duration: 100 + Math.random() * 500,
                        errorMessage:
                            i >= suite.passCount ? getRandomError() : undefined,
                        assertions: 1 + Math.floor(Math.random() * 10),
                        timestamp:
                            Date.now() - Math.floor(Math.random() * 1800000),
                    })
                }
            })

            setTestSuites(newSuites)
            setTestCases(newCases)

            // 計算指標
            const totalSuites = newSuites.length
            const passingSuites = newSuites.filter(
                (s) => s.status === 'pass'
            ).length
            const failingSuites = newSuites.filter(
                (s) => s.status === 'fail'
            ).length
            const totalTests = newSuites.reduce(
                (sum, s) => sum + s.testCount,
                0
            )
            const passingTests = newSuites.reduce(
                (sum, s) => sum + s.passCount,
                0
            )
            const failingTests = newSuites.reduce(
                (sum, s) => sum + s.failCount,
                0
            )
            const overallCoverage =
                newSuites.reduce((sum, s) => sum + s.coverage, 0) / totalSuites
            const averageDuration =
                newSuites.reduce((sum, s) => sum + s.duration, 0) / totalSuites
            const successRate = (passingTests / totalTests) * 100

            setMetrics({
                totalSuites,
                passingSuites,
                failingSuites,
                totalTests,
                passingTests,
                failingTests,
                overallCoverage,
                averageDuration,
                successRate,
            })
        }

        const getRandomError = (): string => {
            const errors = [
                'AssertionError: Expected 200, got 404',
                'TimeoutError: Request timeout after 5000ms',
                'ValidationError: Invalid input parameters',
                'ConnectionError: Unable to connect to database',
                'TypeError: Cannot read property of undefined',
                'NetworkError: API endpoint not responding',
            ]
            return errors[Math.floor(Math.random() * errors.length)]
        }

        generateTestData()
        const interval = setInterval(generateTestData, 10000) // 10秒更新

        return () => clearInterval(interval)
    }, [enabled])

    if (!enabled) return null

    const getStatusColor = (status: string): string => {
        switch (status) {
            case 'pass':
                return '#2ed573'
            case 'fail':
                return '#ff4757'
            case 'running':
                return '#3742fa'
            case 'pending':
                return '#ffa502'
            default:
                return '#747d8c'
        }
    }

    const getCategoryColor = (category: string): string => {
        switch (category) {
            case 'unit':
                return '#3742fa'
            case 'integration':
                return '#ffa502'
            case 'e2e':
                return '#2ed573'
            case 'performance':
                return '#ff4757'
            default:
                return '#747d8c'
        }
    }

    return (
        <>
            {/* 測試套件總覽 */}
            <group position={[-150, 120, 0]}>
                <Text
                    position={[0, 30, 0]}
                    fontSize={8}
                    color="#ffd700"
                    anchorX="center"
                    anchorY="middle"
                >
                    🧪 測試套件總覽
                </Text>

                <Text
                    position={[0, 22, 0]}
                    fontSize={5}
                    color="#ffffff"
                    anchorX="center"
                    anchorY="middle"
                >
                    總成功率: {metrics.successRate.toFixed(1)}%
                </Text>

                <Text
                    position={[0, 18, 0]}
                    fontSize={4}
                    color="#cccccc"
                    anchorX="center"
                    anchorY="middle"
                >
                    測試套件: {metrics.passingSuites}/{metrics.totalSuites}
                </Text>

                <Text
                    position={[0, 14, 0]}
                    fontSize={4}
                    color="#cccccc"
                    anchorX="center"
                    anchorY="middle"
                >
                    測試案例: {metrics.passingTests}/{metrics.totalTests}
                </Text>

                <Text
                    position={[0, 10, 0]}
                    fontSize={4}
                    color="#cccccc"
                    anchorX="center"
                    anchorY="middle"
                >
                    覆蓋率: {metrics.overallCoverage.toFixed(1)}%
                </Text>

                <Text
                    position={[0, 6, 0]}
                    fontSize={4}
                    color="#cccccc"
                    anchorX="center"
                    anchorY="middle"
                >
                    平均時間: {(metrics.averageDuration / 1000).toFixed(1)}s
                </Text>
            </group>

            {/* 測試套件狀態可視化 */}
            <group position={[0, 80, 0]}>
                <Text
                    position={[0, 25, 0]}
                    fontSize={6}
                    color="#00d4ff"
                    anchorX="center"
                    anchorY="middle"
                >
                    📊 測試套件狀態
                </Text>

                {testSuites.map((suite, index) => {
                    const angle = (index / testSuites.length) * Math.PI * 2
                    const radius = 40
                    const x = Math.cos(angle) * radius
                    const z = Math.sin(angle) * radius
                    const y = 0

                    return (
                        <group key={suite.id} position={[x, y, z]}>
                            {/* 測試套件狀態球 */}
                            <mesh>
                                <sphereGeometry args={[3, 16, 16]} />
                                <meshStandardMaterial
                                    color={getStatusColor(suite.status)}
                                    emissive={getStatusColor(suite.status)}
                                    emissiveIntensity={0.3}
                                />
                            </mesh>

                            {/* 關鍵路徑標示 */}
                            {suite.criticalPath && (
                                <mesh position={[0, 6, 0]}>
                                    <ringGeometry args={[4, 5, 8]} />
                                    <meshStandardMaterial
                                        color="#ff6b6b"
                                        emissive="#ff6b6b"
                                        emissiveIntensity={0.5}
                                    />
                                </mesh>
                            )}

                            {/* 類別標示 */}
                            <mesh position={[0, -6, 0]}>
                                <boxGeometry args={[2, 1, 2]} />
                                <meshStandardMaterial
                                    color={getCategoryColor(suite.category)}
                                    emissive={getCategoryColor(suite.category)}
                                    emissiveIntensity={0.2}
                                />
                            </mesh>

                            {/* 套件名稱 */}
                            <Text
                                position={[0, 10, 0]}
                                fontSize={2}
                                color="#ffffff"
                                anchorX="center"
                                anchorY="middle"
                                maxWidth={20}
                            >
                                {suite.name}
                            </Text>

                            {/* 測試結果 */}
                            <Text
                                position={[0, -10, 0]}
                                fontSize={1.5}
                                color={getStatusColor(suite.status)}
                                anchorX="center"
                                anchorY="middle"
                            >
                                {suite.passCount}/{suite.testCount}
                            </Text>

                            {/* 執行中的進度條 */}
                            {suite.status === 'running' && (
                                <group position={[0, -13, 0]}>
                                    <mesh>
                                        <boxGeometry args={[8, 0.5, 0.5]} />
                                        <meshStandardMaterial color="#333333" />
                                    </mesh>
                                    <mesh
                                        position={[
                                            (-8 + (8 * suite.progress) / 100) /
                                                2,
                                            0,
                                            0.1,
                                        ]}
                                    >
                                        <boxGeometry
                                            args={[
                                                (8 * suite.progress) / 100,
                                                0.5,
                                                0.5,
                                            ]}
                                        />
                                        <meshStandardMaterial
                                            color="#3742fa"
                                            emissive="#3742fa"
                                            emissiveIntensity={0.3}
                                        />
                                    </mesh>
                                    <Text
                                        position={[0, -2, 0]}
                                        fontSize={1}
                                        color="#3742fa"
                                        anchorX="center"
                                        anchorY="middle"
                                    >
                                        {suite.progress}%
                                    </Text>
                                </group>
                            )}
                        </group>
                    )
                })}
            </group>

            {/* 測試類別統計 */}
            <group position={[150, 120, 0]}>
                <Text
                    position={[0, 30, 0]}
                    fontSize={6}
                    color="#ff8800"
                    anchorX="center"
                    anchorY="middle"
                >
                    📈 類別統計
                </Text>

                {['unit', 'integration', 'e2e', 'performance'].map(
                    (category, index) => {
                        const suitesOfCategory = testSuites.filter(
                            (s) => s.category === category
                        )
                        const totalTests = suitesOfCategory.reduce(
                            (sum, s) => sum + s.testCount,
                            0
                        )
                        const passingTests = suitesOfCategory.reduce(
                            (sum, s) => sum + s.passCount,
                            0
                        )
                        const successRate =
                            totalTests > 0
                                ? (passingTests / totalTests) * 100
                                : 0

                        return (
                            <group
                                key={category}
                                position={[0, 22 - index * 6, 0]}
                            >
                                <mesh position={[-15, 0, 0]}>
                                    <boxGeometry args={[2, 2, 2]} />
                                    <meshStandardMaterial
                                        color={getCategoryColor(category)}
                                        emissive={getCategoryColor(category)}
                                        emissiveIntensity={0.3}
                                    />
                                </mesh>

                                <Text
                                    position={[-8, 0, 0]}
                                    fontSize={3}
                                    color="#ffffff"
                                    anchorX="left"
                                    anchorY="middle"
                                >
                                    {category}
                                </Text>

                                <Text
                                    position={[15, 0, 0]}
                                    fontSize={3}
                                    color={
                                        successRate >= 90
                                            ? '#2ed573'
                                            : successRate >= 70
                                            ? '#ffa502'
                                            : '#ff4757'
                                    }
                                    anchorX="right"
                                    anchorY="middle"
                                >
                                    {successRate.toFixed(0)}%
                                </Text>
                            </group>
                        )
                    }
                )}
            </group>

            {/* 最近失敗的測試 */}
            <group position={[0, -50, 0]}>
                <Text
                    position={[0, 20, 0]}
                    fontSize={6}
                    color="#ff4757"
                    anchorX="center"
                    anchorY="middle"
                >
                    ❌ 最近失敗的測試
                </Text>

                {testCases
                    .filter((tc) => tc.status === 'fail')
                    .slice(0, 5)
                    .map((testCase, index) => {
                        const suite = testSuites.find(
                            (s) => s.id === testCase.suiteId
                        )
                        return (
                            <group
                                key={testCase.id}
                                position={[0, 12 - index * 4, 0]}
                            >
                                <Text
                                    position={[-30, 0, 0]}
                                    fontSize={2.5}
                                    color="#ffffff"
                                    anchorX="left"
                                    anchorY="middle"
                                    maxWidth={25}
                                >
                                    {suite?.name || '未知套件'}
                                </Text>

                                <Text
                                    position={[0, 0, 0]}
                                    fontSize={2}
                                    color="#cccccc"
                                    anchorX="center"
                                    anchorY="middle"
                                    maxWidth={20}
                                >
                                    {testCase.name}
                                </Text>

                                <Text
                                    position={[35, 0, 0]}
                                    fontSize={1.8}
                                    color="#ff4757"
                                    anchorX="right"
                                    anchorY="middle"
                                    maxWidth={25}
                                >
                                    {testCase.errorMessage}
                                </Text>
                            </group>
                        )
                    })}
            </group>

            {/* 測試執行時間趨勢 */}
            <group position={[-100, -80, 0]}>
                <Text
                    position={[0, 20, 0]}
                    fontSize={5}
                    color="#3742fa"
                    anchorX="center"
                    anchorY="middle"
                >
                    ⏱️ 執行時間趨勢
                </Text>

                {testSuites.slice(0, 8).map((suite, index) => {
                    const barHeight = (suite.duration / 6000) * 15 // 正規化到15單位高度
                    return (
                        <group
                            key={`time_${suite.id}`}
                            position={[index * 4 - 14, 0, 0]}
                        >
                            <mesh position={[0, barHeight / 2, 0]}>
                                <boxGeometry args={[2, barHeight, 2]} />
                                <meshStandardMaterial
                                    color={
                                        barHeight > 10
                                            ? '#ff4757'
                                            : barHeight > 7
                                            ? '#ffa502'
                                            : '#2ed573'
                                    }
                                    emissive={
                                        barHeight > 10
                                            ? '#ff4757'
                                            : barHeight > 7
                                            ? '#ffa502'
                                            : '#2ed573'
                                    }
                                    emissiveIntensity={0.2}
                                />
                            </mesh>

                            <Text
                                position={[0, -3, 0]}
                                fontSize={1.5}
                                color="#ffffff"
                                anchorX="center"
                                anchorY="middle"
                                rotation={[0, 0, Math.PI / 4]}
                            >
                                {(suite.duration / 1000).toFixed(1)}s
                            </Text>
                        </group>
                    )
                })}
            </group>

            {/* 覆蓋率可視化 */}
            <group position={[100, -80, 0]}>
                <Text
                    position={[0, 20, 0]}
                    fontSize={5}
                    color="#2ed573"
                    anchorX="center"
                    anchorY="middle"
                >
                    📋 代碼覆蓋率
                </Text>

                {testSuites.slice(0, 8).map((suite, index) => {
                    const angle = (index / 8) * Math.PI * 2
                    const radius = 12
                    const x = Math.cos(angle) * radius
                    const z = Math.sin(angle) * radius
                    const coverageHeight = (suite.coverage / 100) * 8

                    return (
                        <group
                            key={`coverage_${suite.id}`}
                            position={[x, 0, z]}
                        >
                            <mesh position={[0, coverageHeight / 2, 0]}>
                                <cylinderGeometry
                                    args={[1, 1, coverageHeight, 8]}
                                />
                                <meshStandardMaterial
                                    color={
                                        suite.coverage >= 90
                                            ? '#2ed573'
                                            : suite.coverage >= 70
                                            ? '#ffa502'
                                            : '#ff4757'
                                    }
                                    emissive={
                                        suite.coverage >= 90
                                            ? '#2ed573'
                                            : suite.coverage >= 70
                                            ? '#ffa502'
                                            : '#ff4757'
                                    }
                                    emissiveIntensity={0.2}
                                />
                            </mesh>

                            <Text
                                position={[0, coverageHeight + 2, 0]}
                                fontSize={1.5}
                                color="#ffffff"
                                anchorX="center"
                                anchorY="middle"
                            >
                                {suite.coverage.toFixed(0)}%
                            </Text>
                        </group>
                    )
                })}
            </group>
        </>
    )
}

export default TestResultsVisualization
