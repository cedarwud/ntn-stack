// 通用類型定義
export interface DataPoint {
  x: number | string | Date
  y: number
  label?: string
}

export interface ChartDataset {
  label: string
  data: DataPoint[]
  backgroundColor?: string
  borderColor?: string
  borderWidth?: number
  fill?: boolean
}

export interface ChartData {
  labels: string[]
  datasets: ChartDataset[]
}

export interface ChartOptions {
  responsive?: boolean
  maintainAspectRatio?: boolean
  plugins?: {
    legend?: {
      display?: boolean
      position?: 'top' | 'bottom' | 'left' | 'right'
    }
    tooltip?: {
      enabled?: boolean
      callbacks?: Record<string, unknown>
    }
  }
  scales?: {
    x?: {
      display?: boolean
      title?: {
        display?: boolean
        text?: string
      }
    }
    y?: {
      display?: boolean
      title?: {
        display?: boolean
        text?: string
      }
    }
  }
}

// React Three Fiber 相關類型
export interface Vector3 {
  x: number
  y: number
  z: number
}

export interface ThreeJSMesh {
  position: Vector3
  rotation: Vector3
  scale: Vector3
}

// 事件處理器類型
export type EventHandler<T = unknown> = (event: T) => void
export type ClickHandler = EventHandler<React.MouseEvent>
export type ChangeHandler<T = string> = EventHandler<React.ChangeEvent<HTMLInputElement>> | ((value: T) => void)

// API 相關類型
export interface ApiResponse<T = unknown> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface ApiError {
  message: string
  code?: number
  details?: string
}

// 通用組件 Props
export interface BaseComponentProps {
  className?: string
  style?: React.CSSProperties
  children?: React.ReactNode
}

// 可選的泛型類型
export type Optional<T> = T | undefined
export type Nullable<T> = T | null
export type AnyObject = Record<string, unknown>
