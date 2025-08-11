import React from 'react'
import { FeatureToggleManagerProps } from '../types/sidebar.types'

const FeatureToggleManager: React.FC<FeatureToggleManagerProps> = ({
    activeCategory,
    featureToggles,
}) => {
    // 過濾當前分頁的功能開關
    const currentToggles = featureToggles.filter(
        (toggle) => toggle.category === activeCategory && !toggle.hidden
    )

    return (
        <div className="feature-toggles-container">
            {currentToggles.map((toggle) => (
                <div
                    key={toggle.id}
                    className={`feature-toggle ${
                        toggle.enabled ? 'enabled' : 'disabled'
                    }`}
                    onClick={() => toggle.onToggle(!toggle.enabled)}
                    title={toggle.description}
                >
                    <div className="toggle-content">
                        <span className="toggle-icon">{toggle.icon}</span>
                        <span className="toggle-label">{toggle.label}</span>
                    </div>
                    <div
                        className={`toggle-switch ${
                            toggle.enabled ? 'on' : 'off'
                        }`}
                    >
                        <div className="toggle-slider"></div>
                    </div>
                </div>
            ))}
        </div>
    )
}

export default FeatureToggleManager