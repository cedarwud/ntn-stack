// Dashboard UI 組件
import type { FC, ReactNode } from 'react'

// Card 組件
export interface CardProps {
    children: ReactNode
    className?: string
    title?: string
}

export const Card: FC<CardProps> = ({ children, className = '', title }) => (
    <div className={`bg-white rounded-lg shadow-md p-4 ${className}`}>
        {title && <h3 className="text-lg font-semibold mb-3">{title}</h3>}
        {children}
    </div>
)

// Alert 組件
export interface AlertProps {
    type?: 'info' | 'success' | 'warning' | 'error'
    message?: string
    description?: string
    children?: ReactNode
    className?: string
    closable?: boolean
    onClose?: () => void
}

export const Alert: FC<AlertProps> = ({
    type = 'info',
    message,
    description,
    children,
    className = '',
    closable = false,
    onClose,
}) => {
    const typeStyles = {
        info: 'bg-blue-50 border-blue-200 text-blue-800',
        success: 'bg-green-50 border-green-200 text-green-800',
        warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
        error: 'bg-red-50 border-red-200 text-red-800',
    }

    return (
        <div
            className={`border rounded-md p-3 ${typeStyles[type]} ${className} ${closable ? 'relative pr-8' : ''}`}
        >
            {message && <div className="font-medium">{message}</div>}
            {description && <div className="text-sm mt-1">{description}</div>}
            {children}
            {closable && onClose && (
                <button
                    onClick={onClose}
                    className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
                >
                    ×
                </button>
            )}
        </div>
    )
}

// Spin 組件
export interface SpinProps {
    className?: string
    size?: 'small' | 'default' | 'large'
}

export const Spin: FC<SpinProps> = ({ className = '', size = 'default' }) => {
    const sizeStyles = {
        small: 'h-4 w-4',
        default: 'h-6 w-6',
        large: 'h-8 w-8',
    }

    return (
        <div
            className={`animate-spin rounded-full border-b-2 border-blue-500 ${sizeStyles[size]} ${className}`}
        ></div>
    )
}

// Progress 組件
export interface ProgressProps {
    percent: number
    className?: string
    showInfo?: boolean
    status?: 'success' | 'exception' | 'active' | 'normal'
    size?: 'small' | 'default' | 'large'
}

export const Progress: FC<ProgressProps> = ({
    percent,
    className = '',
    showInfo = true,
    status = 'normal',
    size = 'default',
}) => {
    const statusStyles = {
        success: 'bg-green-500',
        exception: 'bg-red-500',
        active: 'bg-blue-500',
        normal: 'bg-blue-500',
    }

    const sizeStyles = {
        small: 'h-1',
        default: 'h-2',
        large: 'h-3',
    }

    const progressColor = statusStyles[status]
    const progressHeight = sizeStyles[size]

    return (
        <div className={`w-full ${className}`}>
            <div className={`bg-gray-200 rounded-full ${progressHeight}`}>
                <div
                    className={`${progressColor} ${progressHeight} rounded-full transition-all duration-300`}
                    style={{ width: `${Math.min(Math.max(percent, 0), 100)}%` }}
                />
            </div>
            {showInfo && (
                <span className="text-sm text-gray-600 mt-1">{percent}%</span>
            )}
        </div>
    )
}

// Tag 組件
export interface TagProps {
    children: ReactNode
    color?: string
    className?: string
}

export const Tag: FC<TagProps> = ({
    children,
    color = 'blue',
    className = '',
}) => {
    const colorStyles = {
        blue: 'bg-blue-100 text-blue-800',
        green: 'bg-green-100 text-green-800',
        yellow: 'bg-yellow-100 text-yellow-800',
        red: 'bg-red-100 text-red-800',
        gray: 'bg-gray-100 text-gray-800',
    }

    return (
        <span
            className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                colorStyles[color as keyof typeof colorStyles] ||
                colorStyles.blue
            } ${className}`}
        >
            {children}
        </span>
    )
}

// Badge 組件
export interface BadgeProps {
    status?: 'success' | 'error' | 'warning' | 'info'
    text?: string
    count?: number
    className?: string
}

export const Badge: FC<BadgeProps> = ({ status, text, count, className = '' }) => {
    const statusStyles = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-blue-500',
    }

    const bgColor = status ? statusStyles[status] : 'bg-red-500'

    return (
        <span
            className={`inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white rounded-full ${bgColor} ${className}`}
        >
            {text || count}
        </span>
    )
}

// Statistic 組件
export interface StatisticProps {
    title: string
    value: string | number
    suffix?: string
    prefix?: string
    precision?: number
    valueStyle?: { color?: string }
    className?: string
}

export const Statistic: FC<StatisticProps> = ({
    title,
    value,
    suffix,
    prefix,
    precision,
    valueStyle,
    className = '',
}) => {
    const formattedValue = typeof value === 'number' && precision !== undefined
        ? value.toFixed(precision)
        : value

    return (
        <div className={`text-center ${className}`}>
            <div 
                className="text-2xl font-bold text-gray-900"
                style={valueStyle}
            >
                {prefix}
                {formattedValue}
                {suffix}
            </div>
            <div className="text-sm text-gray-500">{title}</div>
        </div>
    )
}
