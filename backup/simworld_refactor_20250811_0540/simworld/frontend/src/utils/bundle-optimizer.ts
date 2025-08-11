/**
 * 前端打包優化工具
 * 提供代碼分割、懶加載、Tree Shaking等優化功能
 */

/**
 * 懶加載組件
 */
export function lazyLoadComponent<T extends React.ComponentType<Record<string, unknown>>>(
  importFunc: () => Promise<{ default: T }>,
  fallback?: React.ComponentType
) {
  const LazyComponent = React.lazy(importFunc)
  
  return (props: React.ComponentProps<T>) => 
    React.createElement(
      React.Suspense,
      { fallback: fallback ? React.createElement(fallback) : React.createElement('div', null, 'Loading...') },
      React.createElement(LazyComponent, props)
    )
}

/**
 * 懶加載工具函數
 */
export async function lazyLoadUtility<T>(importFunc: () => Promise<{ default: T }>): Promise<T> {
  const module = await importFunc()
  return module.default
}

/**
 * 預加載模塊
 */
export function preloadModule(importFunc: () => Promise<unknown>) {
  // 在空閒時間預加載
  if ('requestIdleCallback' in window) {
    requestIdleCallback(() => {
      importFunc()
    })
  } else {
    setTimeout(() => {
      importFunc()
    }, 1)
  }
}

/**
 * 資源優化工具
 */
export const resourceOptimizer = {
  /**
   * 圖片懶加載
   */
  lazyImage: (src: string, options: {
    placeholder?: string
    threshold?: number
    className?: string
  } = {}) => {
    const { placeholder = '', threshold = 0.1, className = '' } = options
    
    return function LazyImage(props: React.ImgHTMLAttributes<HTMLImageElement>) {
      const [imageSrc, setImageSrc] = React.useState(placeholder)
      const [isLoaded, setIsLoaded] = React.useState(false)
      const imgRef = React.useRef<HTMLImageElement>(null)

      React.useEffect(() => {
        const observer = new IntersectionObserver(
          ([entry]) => {
            if (entry.isIntersecting) {
              setImageSrc(src)
              observer.disconnect()
            }
          },
          { threshold }
        )

        if (imgRef.current) {
          observer.observe(imgRef.current)
        }

        return () => observer.disconnect()
      }, [])

      return React.createElement('img', {
        ...props,
        ref: imgRef,
        src: imageSrc,
        className: `${className} ${isLoaded ? 'loaded' : 'loading'}`,
        onLoad: () => setIsLoaded(true),
        loading: "lazy"
      })
    }
  },

  /**
   * 字體優化
   */
  optimizeFont: (fontFamily: string, options: {
    display?: 'auto' | 'block' | 'swap' | 'fallback' | 'optional'
    preload?: boolean
  } = {}) => {
    const { display = 'swap', preload = true } = options
    
    // 添加字體預加載
    if (preload && typeof document !== 'undefined') {
      const link = document.createElement('link')
      link.rel = 'preload'
      link.as = 'font'
      link.href = fontFamily
      link.crossOrigin = 'anonymous'
      document.head.appendChild(link)
    }
    
    // 返回優化的字體樣式
    return {
      fontFamily,
      fontDisplay: display
    }
  }
}

/**
 * 代碼分割配置
 */
export const codeSpittingConfig = {
  /**
   * 路由級別分割
   */
  routes: {
    // 主要頁面
    
    // 可視化組件
    fourWayComparison: () => import('../components/viewers/FourWayHandoverComparisonViewer'),
    
    // 測試組件
    stage3Tests: () => import('../test/stage3-comprehensive-test'),
    
    // 工具組件
    sidebar: () => import('../components/layout/Sidebar')
  },

  /**
   * 功能模塊分割
   */
  features: {
    // 性能監控
    performanceMonitoring: () => import('./performance-optimizer'),
    
    // API 服務
    netstackApi: () => import('../services/netstack-api'),
    simworldApi: () => import('../services/simworld-api'),
    
    // 圖表庫 (分離大型依賴)
    charts: () => import('recharts'),
    threeJS: () => import('three'),
    
    // 測試工具
    testUtils: () => import('../test/test-utils')
  },

  /**
   * 第三方庫分割
   */
  vendors: {
    ui: ['react', 'react-dom'],
    visualization: ['three', 'recharts'],
    testing: ['vitest', '@testing-library/react'],
    utils: ['lodash', 'moment']
  }
}

/**
 * Bundle 分析工具
 */
export const bundleAnalyzer = {
  /**
   * 估算模塊大小
   */
  estimateModuleSize: (moduleName: string): Promise<number> => {
    return new Promise((resolve) => {
      const startTime = performance.now()
      
      import(moduleName)
        .then(() => {
          const endTime = performance.now()
          const estimatedSize = (endTime - startTime) * 1000 // 粗略估算
          resolve(estimatedSize)
        })
        .catch(() => resolve(0))
    })
  },

  /**
   * 分析當前頁面使用的模塊
   */
  analyzeCurrentPage: () => {
    const modules = Array.from(document.querySelectorAll('script[src]'))
      .map(script => (script as HTMLScriptElement).src)
      .filter(src => src.includes('chunk') || src.includes('vendor'))
    
    return {
      totalModules: modules.length,
      modules,
      estimatedSize: modules.length * 50 // KB
    }
  },

  /**
   * 性能建議
   */
  getOptimizationSuggestions: () => {
    const suggestions = []
    
    // 檢查是否有未使用的大型依賴
    if (typeof window !== 'undefined') {
      const scripts = document.querySelectorAll('script[src]')
      if (scripts.length > 10) {
        suggestions.push('考慮進一步代碼分割以減少初始加載時間')
      }
      
      // 檢查字體加載
      const fonts = document.querySelectorAll('link[rel="stylesheet"]')
      if (fonts.length > 3) {
        suggestions.push('考慮字體子集化以減少字體文件大小')
      }
    }
    
    return suggestions
  }
}

/**
 * 樹搖優化工具
 */
export const treeShakingOptimizer = {
  /**
   * 標記未使用的導出
   */
  markUnusedExports: (modulePath: string) => {
    // 這個功能在構建時使用，運行時只返回標記
    return `/* @tree-shake-unused: ${modulePath} */`
  },

  /**
   * 建議的 Tree Shaking 配置
   */
  config: {
    // Webpack 配置建議
    webpack: {
      mode: 'production',
      optimization: {
        usedExports: true,
        sideEffects: false,
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            vendor: {
              test: /[\\/]node_modules[\\/]/,
              name: 'vendors',
              chunks: 'all',
            },
            common: {
              minChunks: 2,
              priority: -10,
              reuseExistingChunk: true,
            },
          },
        },
      },
    },
    
    // Vite 配置建議
    vite: {
      build: {
        rollupOptions: {
          output: {
            manualChunks: {
              vendor: ['react', 'react-dom'],
              charts: ['recharts'],
              three: ['three']
            }
          }
        }
      }
    }
  }
}

// React import for lazy loading
import React from 'react'