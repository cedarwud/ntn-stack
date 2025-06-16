#include "sync_algorithm_interface.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <time.h>

typedef struct routing_entry {
    char ue_id[64];
    uint32_t gnb_ip;
    uint16_t gnb_port;
    time_t last_update;
    struct routing_entry *next;
} routing_entry_t;

static routing_entry_t *g_routing_table = NULL;
static pthread_mutex_t g_routing_mutex = PTHREAD_MUTEX_INITIALIZER;

sync_result_t update_routing_entry(const char *ue_id, uint32_t gnb_ip, uint16_t gnb_port) {
    if (!ue_id) {
        return SYNC_ERROR_INVALID_PARAM;
    }
    
    pthread_mutex_lock(&g_routing_mutex);
    
    routing_entry_t *entry = g_routing_table;
    while (entry) {
        if (strcmp(entry->ue_id, ue_id) == 0) {
            entry->gnb_ip = gnb_ip;
            entry->gnb_port = gnb_port;
            entry->last_update = time(NULL);
            pthread_mutex_unlock(&g_routing_mutex);
            printf("路由表更新: UE=%s\n", ue_id);
            return SYNC_SUCCESS;
        }
        entry = entry->next;
    }
    
    entry = malloc(sizeof(routing_entry_t));
    if (!entry) {
        pthread_mutex_unlock(&g_routing_mutex);
        return SYNC_ERROR_MEMORY_ALLOCATION;
    }
    
    strncpy(entry->ue_id, ue_id, sizeof(entry->ue_id) - 1);
    entry->ue_id[sizeof(entry->ue_id) - 1] = '\0';
    entry->gnb_ip = gnb_ip;
    entry->gnb_port = gnb_port;
    entry->last_update = time(NULL);
    entry->next = g_routing_table;
    g_routing_table = entry;
    
    pthread_mutex_unlock(&g_routing_mutex);
    printf("路由表新增: UE=%s\n", ue_id);
    return SYNC_SUCCESS;
}

void cleanup_routing_table(void) {
    pthread_mutex_lock(&g_routing_mutex);
    routing_entry_t *entry = g_routing_table;
    while (entry) {
        routing_entry_t *next = entry->next;
        free(entry);
        entry = next;
    }
    g_routing_table = NULL;
    pthread_mutex_unlock(&g_routing_mutex);
    printf("路由表已清理\n");
}