/**
 * 優化的數據獲取Hook
 * 提供緩存、去重、錯誤重試等功能
 */
import { useState, useEffect, useRef, useCallback } from 'react'
import { performanceOptimizer } from '../utils/performance-optimizer'

interface FetchOptions {
  cacheTime?: number // 緩存時間(ms)
  retryCount?: number // 重試次數
  retryDelay?: number // 重試延遲(ms)
  enabled?: boolean // 是否啟用自動請求
  refreshInterval?: number // 自動刷新間隔(ms)
  dedupe?: boolean // 是否去重
}

interface FetchState<T> {
  data: T | null
  loading: boolean
  error: Error | null
  lastFetched: number
}

// 全局請求緩存
const requestCache = new Map<string, {
  data: any
  timestamp: number
  promise?: Promise<any>
}>()

// 全局請求去重
const pendingRequests = new Map<string, Promise<any>>()

export function useOptimizedFetch<T>(
  fetcher: () => Promise<T>,
  deps: any[] = [],
  options: FetchOptions = {}
) {
  const {
    cacheTime = 30000, // 30秒默認緩存
    retryCount = 3,
    retryDelay = 1000,
    enabled = true,
    refreshInterval,
    dedupe = true
  } = options

  const [state, setState] = useState<FetchState<T>>({
    data: null,
    loading: false,
    error: null,
    lastFetched: 0
  })

  const abortControllerRef = useRef<AbortController>()
  const refreshIntervalRef = useRef<NodeJS.Timeout>()
  const fetcherRef = useRef(fetcher)
  
  // 更新fetcher引用
  useEffect(() => {
    fetcherRef.current = fetcher
  }, [fetcher])

  // 生成緩存鍵
  const getCacheKey = useCallback(() => {
    return `${fetcherRef.current.toString()}_${JSON.stringify(deps)}`
  }, [deps])

  // 檢查緩存
  const checkCache = useCallback((key: string) => {
    const cached = requestCache.get(key)
    if (cached && Date.now() - cached.timestamp < cacheTime) {
      return cached.data
    }
    return null
  }, [cacheTime])

  // 設置緩存
  const setCache = useCallback((key: string, data: T) => {
    requestCache.set(key, {
      data,
      timestamp: Date.now()
    })
  }, [])

  // 執行請求with性能監控
  const executeRequest = useCallback(async (attempt = 1): Promise<T> => {
    const cacheKey = getCacheKey()
    
    // 檢查緩存
    const cachedData = checkCache(cacheKey)
    if (cachedData) {
      return cachedData
    }

    // 檢查去重
    if (dedupe && pendingRequests.has(cacheKey)) {
      return pendingRequests.get(cacheKey)!
    }

    const endAPICall = performanceOptimizer.startAPICall(cacheKey)

    const requestPromise = (async () => {
      try {
        const data = await fetcherRef.current()
        
        // 設置緩存
        setCache(cacheKey, data)
        
        endAPICall(false)
        return data
      } catch (error) {
        endAPICall(true)
        
        // 重試邏輯
        if (attempt < retryCount) {
          await new Promise(resolve => setTimeout(resolve, retryDelay * attempt))
          return executeRequest(attempt + 1)
        }
        
        throw error
      } finally {
        if (dedupe) {
          pendingRequests.delete(cacheKey)
        }
      }
    })()

    if (dedupe) {
      pendingRequests.set(cacheKey, requestPromise)
    }

    return requestPromise
  }, [getCacheKey, checkCache, setCache, dedupe, retryCount, retryDelay])

  // 主要的fetch函數
  const fetchData = useCallback(async () => {
    if (!enabled) return

    // 取消之前的請求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    abortControllerRef.current = new AbortController()

    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const data = await executeRequest()
      
      setState({
        data,
        loading: false,
        error: null,
        lastFetched: Date.now()
      })
    } catch (error) {
      if (!(error as Error).name === 'AbortError') {
        setState(prev => ({
          ...prev,
          loading: false,
          error: error as Error
        }))
      }
    }
  }, [enabled, executeRequest])

  // 手動刷新函數
  const refetch = useCallback(() => {
    const cacheKey = getCacheKey()
    requestCache.delete(cacheKey) // 清除緩存強制重新獲取
    return fetchData()
  }, [getCacheKey, fetchData])

  // 清除緩存
  const clearCache = useCallback(() => {
    const cacheKey = getCacheKey()
    requestCache.delete(cacheKey)
  }, [getCacheKey])

  // 初始請求和依賴變化時重新請求
  useEffect(() => {
    fetchData()
  }, [fetchData, ...deps])

  // 設置自動刷新
  useEffect(() => {
    if (refreshInterval && refreshInterval > 0) {
      refreshIntervalRef.current = setInterval(fetchData, refreshInterval)
      
      return () => {
        if (refreshIntervalRef.current) {
          clearInterval(refreshIntervalRef.current)
        }
      }
    }
  }, [refreshInterval, fetchData])

  // 清理函數
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current)
      }
    }
  }, [])

  return {
    ...state,
    refetch,
    clearCache,
    isCached: !!checkCache(getCacheKey())
  }
}

/**
 * 簡化的數據獲取Hook，適用於簡單場景
 */
export function useFetch<T>(
  url: string,
  options: RequestInit & { enabled?: boolean; refreshInterval?: number } = {}
) {
  const { enabled = true, refreshInterval, ...fetchOptions } = options

  const fetcher = useCallback(async (): Promise<T> => {
    const response = await fetch(url, fetchOptions)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    return response.json()
  }, [url, fetchOptions])

  return useOptimizedFetch(fetcher, [url], {
    enabled,
    refreshInterval
  })
}

/**
 * 批量數據獲取Hook
 */
export function useBatchFetch<T>(
  requests: Array<() => Promise<T>>,
  options: FetchOptions = {}
) {
  const [state, setState] = useState<{
    data: (T | null)[]
    loading: boolean
    errors: (Error | null)[]
  }>({
    data: new Array(requests.length).fill(null),
    loading: false,
    errors: new Array(requests.length).fill(null)
  })

  const fetchAll = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true }))

    try {
      const results = await Promise.allSettled(
        requests.map(request => request())
      )

      const data: (T | null)[] = []
      const errors: (Error | null)[] = []

      results.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          data[index] = result.value
          errors[index] = null
        } else {
          data[index] = null
          errors[index] = result.reason
        }
      })

      setState({
        data,
        loading: false,
        errors
      })
    } catch (error) {
      setState(prev => ({
        ...prev,
        loading: false,
        errors: new Array(requests.length).fill(error)
      }))
    }
  }, [requests])

  useEffect(() => {
    if (options.enabled !== false) {
      fetchAll()
    }
  }, [fetchAll, options.enabled])

  return {
    ...state,
    refetch: fetchAll
  }
}

/**
 * 清理全局緩存
 */
export function clearAllCache() {
  requestCache.clear()
  pendingRequests.clear()
}