import {
    createContext,
    useState,
    useCallback,
    ReactNode,
} from 'react'
import { netstackFetch } from '../config/api-config'

export type HandoverStrategy = 'flexible' | 'consistent'

interface StrategyContextType {
    currentStrategy: HandoverStrategy
    switchStrategy: (strategy: HandoverStrategy) => Promise<void>
    isLoading: boolean
    lastChanged: Date | null
}

const StrategyContext = createContext<StrategyContextType | undefined>(
    undefined
)

export { StrategyContext }

interface StrategyProviderProps {
    children: ReactNode
}

export const StrategyProvider = ({ children }: StrategyProviderProps) => {
    const [currentStrategy, setCurrentStrategy] =
        useState<HandoverStrategy>('flexible')
    const [isLoading, setIsLoading] = useState(false)
    const [lastChanged, setLastChanged] = useState<Date | null>(null)

    const switchStrategy = useCallback(
        async (strategy: HandoverStrategy) => {
            if (currentStrategy === strategy) return

            setIsLoading(true)
            console.log(`🔄 全域策略切換：${currentStrategy} → ${strategy}`)

            try {
                // 將前端策略名稱對應到後端期望的格式
                const backendStrategy =
                    strategy === 'flexible'
                        ? 'fast_handover'
                        : 'ai_optimized_handover'

                // 調用 NetStack API 進行策略切換 (使用統一配置)
                const response = await netstackFetch(
                    '/api/v1/handover/strategy/switch',
                    {
                        method: 'POST',
                        body: JSON.stringify({
                            strategy: backendStrategy,
                            parameters: {},
                            priority: 1,
                            force: false,
                        }),
                    }
                )

                if (response.ok) {
                    const result = await response.json()
                    console.log('✅ 全域策略切換成功:', result)
                } else {
                    const errorData = await response.json().catch(() => ({}))
                    console.warn(
                        '⚠️ NetStack API 調用失敗，使用本地策略切換:',
                        errorData
                    )
                }
            } catch (error) {
                console.warn('🔧 NetStack API 不可用，使用本地策略切換:', error)
            }

            // 無論 API 是否成功，都更新本地狀態
            setCurrentStrategy(strategy)
            setLastChanged(new Date())
            setIsLoading(false)

            // 廣播策略變更事件給其他組件
            window.dispatchEvent(
                new CustomEvent('strategyChanged', {
                    detail: { strategy, timestamp: new Date() },
                })
            )

            console.log(`🎯 全域策略已切換到: ${strategy}`)
        },
        [currentStrategy]
    )

    return (
        <StrategyContext.Provider
            value={{
                currentStrategy,
                switchStrategy,
                isLoading,
                lastChanged,
            }}
        >
            {children}
        </StrategyContext.Provider>
    )
}
