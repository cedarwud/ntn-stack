// ChartAnalysisDashboard Module Exports

// Main component
export { default as ChartAnalysisDashboard } from './ChartAnalysisDashboard';

// Refactored component (可選擇性使用)
export { default as ChartAnalysisDashboardRefactored } from './ChartAnalysisDashboard.refactored';

// Tab components
export { default as OverviewTabContent } from './components/OverviewTabContent';
export { default as AlgorithmTabContent } from './components/AlgorithmTabContent';
export { default as PerformanceTabContent } from './components/PerformanceTabContent';

// Services
export { ChartDataService } from './services/chartDataService';

// Hooks
export { useChartAnalysisData } from './hooks/useChartAnalysisData';

// Configuration
export { initializeChartSystem, commonChartOptions, chartColors } from './config/chartConfig';

// Types
export type * from './types/index';