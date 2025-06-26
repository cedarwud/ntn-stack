/**
 * Strategy 相關的 Hook 函數
 * 分離出來以避免 Fast Refresh 警告
 */
import { useContext } from 'react'
import StrategyContext from '../contexts/StrategyContext'

export const useStrategy = () => {
    const context = useContext(StrategyContext)
    if (context === undefined) {
        throw new Error('useStrategy must be used within a StrategyProvider')
    }
    return context
}
