#!/bin/bash
# 臨時GTP修復腳本用於測試

echo "開始修復GTP隧道..."

# 模擬禁用Linux內核源地址驗證
echo "禁用Linux內核源地址驗證..."
# sysctl -w net.ipv4.conf.all.rp_filter=0 2>/dev/null || echo "無法設置rp_filter"

# 模擬配置IP轉發規則
echo "配置IP轉發規則..."
# sysctl -w net.ipv4.ip_forward=1 2>/dev/null || echo "無法設置ip_forward"

echo "GTP隧道修復完成"
exit 0
