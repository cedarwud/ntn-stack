export interface ViewerProps {
    onReportLastUpdateToNavbar?: (time: string) => void; // For header last update
    reportRefreshHandlerToNavbar: (handler: () => void) => void;
    reportIsLoadingToNavbar: (isLoading: boolean) => void;
} 