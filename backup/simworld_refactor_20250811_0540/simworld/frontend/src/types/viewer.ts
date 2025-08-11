export interface ViewerProps {
    onReportLastUpdateToNavbar?: (time: string) => void; // For header last update
    reportRefreshHandlerToNavbar: (handler: () => void) => void;
    reportIsLoadingToNavbar: (isLoading: boolean) => void;
    currentScene: string; // 當前場景名稱
} 