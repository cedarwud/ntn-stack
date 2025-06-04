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
    children: ReactNode
    className?: string
}

export const Alert: FC<AlertProps> = ({
    type = 'info',
    children,
    className = '',
}) => {
    const typeStyles = {
        info: 'bg-blue-50 border-blue-200 text-blue-800',
        success: 'bg-green-50 border-green-200 text-green-800',
        warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
        error: 'bg-red-50 border-red-200 text-red-800',
    }

    return (
        <div
            className={`border rounded-md p-3 ${typeStyles[type]} ${className}`}
        >
            {children}
        </div>
    )
}

// Spin 組件
export interface SpinProps {
    className?: string
}

export const Spin: FC<SpinProps> = ({ className = '' }) => (
    <div
        className={`animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 ${className}`}
    ></div>
)

// Progress 組件
export interface ProgressProps {
    percent: number
    className?: string
    showInfo?: boolean
}

export const Progress: FC<ProgressProps> = ({
    percent,
    className = '',
    showInfo = true,
}) => (
    <div className={`w-full ${className}`}>
        <div className="bg-gray-200 rounded-full h-2">
            <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${Math.min(Math.max(percent, 0), 100)}%` }}
            />
        </div>
        {showInfo && (
            <span className="text-sm text-gray-600 mt-1">{percent}%</span>
        )}
    </div>
)

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
    count: number
    className?: string
}

export const Badge: FC<BadgeProps> = ({ count, className = '' }) => (
    <span
        className={`inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white bg-red-500 rounded-full ${className}`}
    >
        {count}
    </span>
)

// Statistic 組件
export interface StatisticProps {
    title: string
    value: string | number
    suffix?: string
    prefix?: string
    className?: string
}

export const Statistic: FC<StatisticProps> = ({
    title,
    value,
    suffix,
    prefix,
    className = '',
}) => (
    <div className={`text-center ${className}`}>
        <div className="text-2xl font-bold text-gray-900">
            {prefix}
            {value}
            {suffix}
        </div>
        <div className="text-sm text-gray-500">{title}</div>
    </div>
)
