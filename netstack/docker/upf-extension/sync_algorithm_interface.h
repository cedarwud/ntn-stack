/**
 * UPF 同步演算法介面
 * 
 * 提供 Open5GS UPF 與論文同步演算法的整合介面
 * 支援快速衛星切換和路由表即時更新
 */

#ifndef SYNC_ALGORITHM_INTERFACE_H
#define SYNC_ALGORITHM_INTERFACE_H

#include <stdint.h>
#include <stdbool.h>
#include <time.h>

#ifdef __cplusplus
extern "C" {
#endif

// 錯誤碼定義
typedef enum {
    SYNC_SUCCESS = 0,
    SYNC_ERROR_INVALID_PARAM = -1,
    SYNC_ERROR_UE_NOT_FOUND = -2,
    SYNC_ERROR_SATELLITE_NOT_FOUND = -3,
    SYNC_ERROR_HANDOVER_IN_PROGRESS = -4,
    SYNC_ERROR_ROUTING_UPDATE_FAILED = -5,
    SYNC_ERROR_MEMORY_ALLOCATION = -6,
    SYNC_ERROR_TIMEOUT = -7
} sync_result_t;

// UE 資訊結構
typedef struct {
    char ue_id[64];                    // UE 識別碼
    char current_satellite_id[64];     // 目前接入衛星
    char target_satellite_id[64];      // 目標衛星
    uint32_t ipv4_addr;               // UE IPv4 地址
    double predicted_handover_time;    // 預測切換時間
    bool handover_in_progress;         // 切換進行中標記
    uint8_t access_strategy;           // 接入策略 (0=flexible, 1=consistent)
} ue_context_t;

// 衛星資訊結構
typedef struct {
    char satellite_id[64];             // 衛星識別碼
    uint32_t gnb_ip;                  // gNB IP 地址
    uint16_t gnb_port;                // gNB 埠號
    double latitude;                   // 緯度
    double longitude;                  // 經度
    double altitude;                   // 高度
    bool is_active;                    // 是否啟用
    uint32_t connected_ue_count;       // 連接的 UE 數量
} satellite_info_t;

// 切換事件結構
typedef struct {
    char ue_id[64];
    char source_satellite[64];
    char target_satellite[64];
    double trigger_time;
    double completion_time;
    sync_result_t result;
    char error_message[256];
} handover_event_t;

// 同步演算法狀態
typedef struct {
    bool algorithm_running;            // 演算法是否運行中
    uint32_t total_ue_count;          // 總 UE 數量
    uint32_t active_handover_count;    // 進行中的切換數量
    double last_update_time;           // 最後更新時間
    uint64_t total_handover_count;     // 總切換次數
    uint64_t successful_handover_count; // 成功切換次數
    double average_handover_latency;   // 平均切換延遲 (ms)
} sync_algorithm_status_t;

/**
 * 初始化同步演算法模組
 * 
 * @return sync_result_t 結果代碼
 */
sync_result_t sync_algorithm_init(void);

/**
 * 關閉同步演算法模組
 */
void sync_algorithm_cleanup(void);

/**
 * 註冊 UE 到同步演算法
 * 
 * @param ue_context UE 上下文資訊
 * @return sync_result_t 結果代碼
 */
sync_result_t sync_algorithm_register_ue(const ue_context_t *ue_context);

/**
 * 註銷 UE
 * 
 * @param ue_id UE 識別碼
 * @return sync_result_t 結果代碼
 */
sync_result_t sync_algorithm_unregister_ue(const char *ue_id);

/**
 * 更新 UE 位置資訊
 * 
 * @param ue_id UE 識別碼
 * @param latitude 緯度
 * @param longitude 經度
 * @param altitude 高度
 * @return sync_result_t 結果代碼
 */
sync_result_t sync_algorithm_update_ue_position(const char *ue_id,
                                               double latitude,
                                               double longitude,
                                               double altitude);

/**
 * 觸發 UE 切換
 * 
 * @param ue_id UE 識別碼
 * @param target_satellite_id 目標衛星識別碼
 * @param predicted_time 預測切換時間
 * @return sync_result_t 結果代碼
 */
sync_result_t sync_algorithm_trigger_handover(const char *ue_id,
                                             const char *target_satellite_id,
                                             double predicted_time);

/**
 * 獲取 UE 當前狀態
 * 
 * @param ue_id UE 識別碼
 * @param ue_context 輸出參數：UE 上下文
 * @return sync_result_t 結果代碼
 */
sync_result_t sync_algorithm_get_ue_context(const char *ue_id,
                                           ue_context_t *ue_context);

/**
 * 獲取衛星資訊
 * 
 * @param satellite_id 衛星識別碼
 * @param satellite_info 輸出參數：衛星資訊
 * @return sync_result_t 結果代碼
 */
sync_result_t sync_algorithm_get_satellite_info(const char *satellite_id,
                                               satellite_info_t *satellite_info);

/**
 * 更新路由表
 * 
 * @param ue_id UE 識別碼
 * @param new_gnb_ip 新的 gNB IP 地址
 * @param new_gnb_port 新的 gNB 埠號
 * @return sync_result_t 結果代碼
 */
sync_result_t sync_algorithm_update_routing_table(const char *ue_id,
                                                 uint32_t new_gnb_ip,
                                                 uint16_t new_gnb_port);

/**
 * 獲取演算法狀態
 * 
 * @param status 輸出參數：演算法狀態
 * @return sync_result_t 結果代碼
 */
sync_result_t sync_algorithm_get_status(sync_algorithm_status_t *status);

/**
 * 設置演算法參數
 * 
 * @param delta_t 更新週期 (秒)
 * @param binary_search_precision 二分搜尋精度 (秒)
 * @return sync_result_t 結果代碼
 */
sync_result_t sync_algorithm_set_parameters(double delta_t,
                                           double binary_search_precision);

/**
 * 獲取最近的切換事件
 * 
 * @param events 輸出參數：事件陣列
 * @param max_events 最大事件數量
 * @param actual_count 輸出參數：實際事件數量
 * @return sync_result_t 結果代碼
 */
sync_result_t sync_algorithm_get_recent_handover_events(handover_event_t *events,
                                                       uint32_t max_events,
                                                       uint32_t *actual_count);

/**
 * 啟動演算法週期性更新
 * 
 * @return sync_result_t 結果代碼
 */
sync_result_t sync_algorithm_start_periodic_update(void);

/**
 * 停止演算法週期性更新
 * 
 * @return sync_result_t 結果代碼
 */
sync_result_t sync_algorithm_stop_periodic_update(void);

#ifdef __cplusplus
}
#endif

#endif // SYNC_ALGORITHM_INTERFACE_H