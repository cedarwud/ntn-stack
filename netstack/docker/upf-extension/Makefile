# UPF 擴展模組 Makefile
# 編譯同步演算法 C 實作和 Python 橋接

CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -fPIC -O2 -g
LDFLAGS = -shared
PYTHON = python3

# 目標文件
TARGET_LIB = libsync_algorithm.so
TARGET_BRIDGE = sync_algorithm_bridge.o
TARGET_ROUTING = routing_table_manager.o

# 源文件
SOURCES = sync_algorithm_bridge.c routing_table_manager.c
HEADERS = sync_algorithm_interface.h gtp_extension.h

# 包含路徑
INCLUDES = -I.

# 函式庫連結
LIBS = -lpthread -lm

# 預設目標
all: $(TARGET_LIB) test_bridge

# 編譯共享函式庫
$(TARGET_LIB): $(TARGET_BRIDGE) $(TARGET_ROUTING)
	@echo "正在連結共享函式庫..."
	$(CC) $(LDFLAGS) -o $@ $^ $(LIBS)
	@echo "共享函式庫編譯完成: $(TARGET_LIB)"
	@echo "複製函式庫到測試目錄..."
	@cp $(TARGET_LIB) ../../paper/1.4_upf_integration/ 2>/dev/null || echo "測試目錄不存在，跳過複製"

# 編譯橋接模組
$(TARGET_BRIDGE): sync_algorithm_bridge.c $(HEADERS)
	@echo "正在編譯同步演算法橋接模組..."
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

# 編譯路由表管理模組
$(TARGET_ROUTING): routing_table_manager.c $(HEADERS)
	@echo "正在編譯路由表管理模組..."
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

# 編譯測試程式
test_bridge: test_sync_bridge.c $(TARGET_LIB)
	@echo "正在編譯測試程式..."
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ $< -L. -lsync_algorithm $(LIBS)

clean:
	@echo "清理編譯文件..."
	rm -f *.o *.so test_bridge

help:
	@echo "UPF 擴展模組 Makefile"
	@echo "可用目標: all, clean, help"

.PHONY: all clean help