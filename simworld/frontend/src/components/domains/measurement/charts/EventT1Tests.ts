/**
 * Event T1 Tests
 * 驗證 3GPP TS 38.331 Event T1 功能實現
 */

import { EventT1Params } from '../types'

interface T1TestCase {
    name: string
    params: EventT1Params
    expectedBehavior: string
    testDescription: string
}

export const t1TestCases: T1TestCase[] = [
    {
        name: 'T1-Test-1: 基本時間窗口觸發',
        params: {
            Thresh1: 5000, // 5 seconds
            Duration: 10000, // 10 seconds
            Hys: 0,
            timeToTrigger: 0,
            reportAmount: 1,
            reportInterval: 0,
            reportOnLeave: true,
        },
        expectedBehavior: '當時間測量值 Mt 超過 5000ms 並持續 10000ms 時觸發',
        testDescription: '驗證基本的 T1 事件觸發邏輯',
    },
    {
        name: 'T1-Test-2: 短時間窗口',
        params: {
            Thresh1: 3000, // 3 seconds
            Duration: 5000, // 5 seconds
            Hys: 0,
            timeToTrigger: 0,
            reportAmount: 2,
            reportInterval: 1000,
            reportOnLeave: false,
        },
        expectedBehavior: '較短的時間窗口，更快觸發條件',
        testDescription: '測試較短持續時間的 T1 事件行為',
    },
    {
        name: 'T1-Test-3: 長時間窗口',
        params: {
            Thresh1: 8000, // 8 seconds
            Duration: 20000, // 20 seconds
            Hys: 0,
            timeToTrigger: 0,
            reportAmount: 4,
            reportInterval: 2000,
            reportOnLeave: true,
        },
        expectedBehavior: '較長的時間窗口，需要更長時間才觸發',
        testDescription: '測試長持續時間的 T1 事件穩定性',
    },
    {
        name: 'T1-Test-4: 高閾值測試',
        params: {
            Thresh1: 12000, // 12 seconds
            Duration: 15000, // 15 seconds
            Hys: 0,
            timeToTrigger: 0,
            reportAmount: 1,
            reportInterval: 0,
            reportOnLeave: true,
        },
        expectedBehavior: '高閾值條件，只有在長時間測量值很高時才觸發',
        testDescription: '驗證高閾值設置下的 T1 事件行為',
    },
]

export const validateT1Logic = (mt: number, thresh1: number, duration: number, timeInCondition: number): {
    enterCondition: boolean
    leaveCondition: boolean
    conditionMet: boolean
    status: string
} => {
    const enterCondition = mt > thresh1
    const conditionMet = enterCondition && timeInCondition >= duration
    const leaveCondition = mt > (thresh1 + duration * 0.1) // 簡化的離開條件
    
    let status = 'Not Triggered'
    if (enterCondition && !conditionMet) {
        status = 'Pending'
    } else if (conditionMet) {
        status = 'Triggered'
    }
    
    return {
        enterCondition,
        leaveCondition,
        conditionMet,
        status
    }
}

export const generateT1Report = (params: EventT1Params): string => {
    return `
3GPP TS 38.331 Event T1 Configuration Report
============================================

Event Type: T1 (Time Window Condition)
Specification: 3GPP TS 38.331 Section 5.5.4.16

Parameters:
- t1-Threshold: ${params.Thresh1}ms
- Duration: ${params.Duration}ms
- Report Amount: ${params.reportAmount}
- Report Interval: ${params.reportInterval}ms
- Report On Leave: ${params.reportOnLeave ? 'Enabled' : 'Disabled'}

Event Conditions:
- Enter: Mt > ${params.Thresh1}ms (持續 ${params.Duration}ms)
- Leave: Mt > ${params.Thresh1 + params.Duration * 0.1}ms (時間超出範圍)

Use Case:
Event T1 適用於需要監控時間測量值在特定閾值以上持續一定時間的場景，
常用於網路延遲監控、服務質量評估等應用。

Generated at: ${new Date().toISOString()}
    `.trim()
}

export const runT1Tests = (): void => {
    console.log('🧪 Running Event T1 Tests...\n')
    
    t1TestCases.forEach((testCase, index) => {
        console.log(`Test ${index + 1}: ${testCase.name}`)
        console.log(`Description: ${testCase.testDescription}`)
        console.log(`Expected: ${testCase.expectedBehavior}`)
        console.log(`Parameters:`, testCase.params)
        console.log(`Report:\n${generateT1Report(testCase.params)}\n`)
        console.log('---\n')
    })
    
    // 測試 T1 邏輯驗證
    console.log('🔬 Testing T1 Logic Validation...\n')
    
    const testScenarios = [
        { mt: 6000, thresh1: 5000, duration: 10000, timeInCondition: 5000 },
        { mt: 6000, thresh1: 5000, duration: 10000, timeInCondition: 12000 },
        { mt: 4000, thresh1: 5000, duration: 10000, timeInCondition: 15000 },
    ]
    
    testScenarios.forEach((scenario, index) => {
        const result = validateT1Logic(scenario.mt, scenario.thresh1, scenario.duration, scenario.timeInCondition)
        console.log(`Scenario ${index + 1}:`)
        console.log(`  Mt: ${scenario.mt}ms, Threshold: ${scenario.thresh1}ms, Duration: ${scenario.duration}ms`)
        console.log(`  Time in condition: ${scenario.timeInCondition}ms`)
        console.log(`  Result: ${result.status}`)
        console.log(`  Enter condition: ${result.enterCondition}`)
        console.log(`  Condition met: ${result.conditionMet}`)
        console.log()
    })
    
    console.log('✅ T1 Tests completed!')
}

// 如果直接運行此腳本
if (typeof window === 'undefined') {
    runT1Tests()
}
