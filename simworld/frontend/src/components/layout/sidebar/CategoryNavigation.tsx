import React from 'react'
import { CategoryNavigationProps } from '../types/sidebar.types'

const CategoryNavigation: React.FC<CategoryNavigationProps> = ({
    categories,
    activeCategory,
    onCategoryChange,
}) => {
    return (
        <div className="category-tabs">
            {categories.map((category) => (
                <button
                    key={category.id}
                    className={`category-tab ${
                        activeCategory === category.id ? 'active' : ''
                    }`}
                    onClick={() => onCategoryChange(category.id)}
                    title={category.label}
                >
                    <span className="tab-icon">{category.icon}</span>
                    <span className="tab-label">{category.label}</span>
                </button>
            ))}
        </div>
    )
}

export default CategoryNavigation