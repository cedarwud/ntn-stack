#include "sync_algorithm_interface.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

int main() {
    printf("=== UPF 同步演算法測試程式 ===\n");
    
    sync_result_t result = sync_algorithm_init();
    if (result != SYNC_SUCCESS) {
        printf("初始化失敗: %d\n", result);
        return 1;
    }
    printf("✅ 模組初始化成功\n");
    
    ue_context_t ue_context = {0};
    strcpy(ue_context.ue_id, "test_ue_001");
    strcpy(ue_context.current_satellite_id, "starlink_1001");
    ue_context.access_strategy = 0;
    
    result = sync_algorithm_register_ue(&ue_context);
    if (result == SYNC_SUCCESS) {
        printf("✅ UE 註冊成功\n");
    }
    
    result = sync_algorithm_start_periodic_update();
    if (result == SYNC_SUCCESS) {
        printf("✅ 演算法啟動成功\n");
    }
    
    result = sync_algorithm_trigger_handover("test_ue_001", "starlink_1002", time(NULL) + 5);
    if (result == SYNC_SUCCESS) {
        printf("✅ 切換觸發成功\n");
    }
    
    sync_algorithm_status_t status;
    result = sync_algorithm_get_status(&status);
    if (result == SYNC_SUCCESS) {
        printf("✅ 狀態查詢成功\n");
        printf("   - 演算法運行中: %s\n", status.algorithm_running ? "是" : "否");
        printf("   - 總 UE 數量: %u\n", status.total_ue_count);
        printf("   - 總切換次數: %lu\n", status.total_handover_count);
    }
    
    sync_algorithm_cleanup();
    printf("✅ 模組清理完成\n");
    printf("\n=== 測試完成 ===\n");
    return 0;
}