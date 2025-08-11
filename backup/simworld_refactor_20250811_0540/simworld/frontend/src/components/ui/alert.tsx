import React from 'react'

interface AlertProps {
  variant?: 'default' | 'destructive'
  className?: string
  children: React.ReactNode
}

export const Alert: React.FC<AlertProps> = ({ 
  variant = 'default', 
  className = '', 
  children 
}) => {
  const baseClasses = 'relative w-full rounded-lg border p-4'
  
  const variants = {
    default: 'border-gray-300 bg-white text-gray-900',
    destructive: 'border-red-300 bg-red-50 text-red-900'
  }
  
  return (
    <div className={`${baseClasses} ${variants[variant]} ${className}`}>
      {children}
    </div>
  )
}

interface AlertDescriptionProps {
  className?: string
  children: React.ReactNode
}

export const AlertDescription: React.FC<AlertDescriptionProps> = ({ 
  className = '', 
  children 
}) => {
  return (
    <div className={`text-sm ${className}`}>
      {children}
    </div>
  )
}

export default Alert