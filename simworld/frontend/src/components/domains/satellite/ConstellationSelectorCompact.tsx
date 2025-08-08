import React from 'react'

interface Props {
    value: 'starlink' | 'oneweb'
    onChange: (constellation: 'starlink' | 'oneweb') => void
    disabled?: boolean
}

const CONSTELLATION_CONFIGS = {
    starlink: {
        icon: '🛰️',
        name: 'Starlink',
        color: '#1890ff',
    },
    oneweb: {
        icon: '🌐', 
        name: 'OneWeb',
        color: '#52c41a',
    },
}

export const ConstellationSelectorCompact: React.FC<Props> = ({
    value,
    onChange,
    disabled = false,
}) => {
    return (
        <div className="constellation-selector">
            <div className="constellation-options-compact">
                {Object.entries(CONSTELLATION_CONFIGS).map(([key, config]) => (
                    <button
                        key={key}
                        className={`constellation-btn-compact ${
                            value === key ? 'active' : ''
                        }`}
                        onClick={() => onChange(key as 'starlink' | 'oneweb')}
                        disabled={disabled}
                    >
                        {config.icon} {config.name}
                    </button>
                ))}
            </div>
        </div>
    )
}

export default ConstellationSelectorCompact