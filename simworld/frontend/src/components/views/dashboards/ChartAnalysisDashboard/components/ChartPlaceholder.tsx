import React from 'react'

interface ChartPlaceholderProps {
    message: string
}

export const ChartPlaceholder: React.FC<ChartPlaceholderProps> = ({
    message,
}) => {
    return (
        <div className="flex items-center justify-center h-full w-full">
            <div className="text-center text-gray-500">
                <div className="mb-2">
                    <svg
                        className="mx-auto h-12 w-12 text-gray-600"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        aria-hidden="true"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={1}
                            d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V7a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                    </svg>
                </div>
                <p className="text-sm font-medium">{message}</p>
            </div>
        </div>
    )
}
