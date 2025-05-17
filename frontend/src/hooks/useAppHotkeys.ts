import { useEffect } from 'react'

export type HotkeyMap = {
    [key: string]: (e: KeyboardEvent) => void
}

export function useAppHotkeys(hotkeyMap: HotkeyMap) {
    useEffect(() => {
        function handleKeyDown(e: KeyboardEvent) {
            const key = e.key.toLowerCase()
            if (hotkeyMap[key]) {
                hotkeyMap[key](e)
            }
        }
        window.addEventListener('keydown', handleKeyDown)
        return () => {
            window.removeEventListener('keydown', handleKeyDown)
        }
    }, [hotkeyMap])
} 