import { useState, useCallback } from 'react'

export type ManualDirection =
    | 'up'
    | 'down'
    | 'left'
    | 'right'
    | 'ascend'
    | 'descend'
    | 'left-up'
    | 'right-up'
    | 'left-down'
    | 'right-down'
    | 'rotate-left'
    | 'rotate-right'
    | null

export function useManualControl() {
    const [manualDirection, setManualDirection] = useState<ManualDirection>(null)

    const handleManualControl = useCallback((direction: ManualDirection) => {
        setManualDirection(direction)
    }, [])

    const resetManualControl = useCallback(() => {
        setManualDirection(null)
    }, [])

    return {
        manualDirection,
        setManualDirection,
        handleManualControl,
        resetManualControl,
    }
} 