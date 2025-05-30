import { useState, useEffect, useCallback } from 'react'

interface ApiDataHookReturn {
    data: any
    loading: boolean
    error: string | null
    refetch: () => Promise<void>
}

export const useApiData = (url: string, options?: RequestInit): ApiDataHookReturn => {
    const [data, setData] = useState<any>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const fetchData = useCallback(async () => {
        setLoading(true)
        setError(null)

        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options?.headers
                },
                ...options
            })

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`)
            }

            const result = await response.json()
            setData(result)
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
            setError(errorMessage)
            console.error('API fetch error:', errorMessage)
        } finally {
            setLoading(false)
        }
    }, [url, options])

    useEffect(() => {
        fetchData()
    }, [fetchData])

    return {
        data,
        loading,
        error,
        refetch: fetchData
    }
} 