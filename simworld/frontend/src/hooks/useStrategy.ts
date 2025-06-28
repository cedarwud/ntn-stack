import { useContext } from 'react'
import { StrategyContext } from '../contexts/StrategyContext'

export const useStrategy = () => {
    const context = useContext(StrategyContext)
    if (context === undefined) {
        throw new Error('useStrategy must be used within a StrategyProvider')
    }
    return context
}
