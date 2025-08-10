#!/bin/bash
# IP 配置一致性驗證腳本

echo "🔍 檢查 Docker Compose IP 配置一致性..."
echo ""

# 檢查關鍵服務的 IP 配置
services=("postgres" "redis" "netstack-api")
declare -A expected_ips=(
    ["postgres"]="172.20.0.51"
    ["redis"]="172.20.0.50" 
    ["netstack-api"]="172.20.0.40"
)

compose_files=("core.yaml" "core-simple.yaml")

for service in "${services[@]}"; do
    echo "📋 檢查 $service 服務 IP 配置:"
    
    for file in "${compose_files[@]}"; do
        file_path="/home/sat/ntn-stack/netstack/compose/$file"
        
        if [[ -f "$file_path" ]]; then
            # 搜尋服務的 IP 配置
            if [[ "$service" == "netstack-api" ]]; then
                ip=$(grep -A50 "netstack-api:" "$file_path" | grep "ipv4_address:" | head -1 | awk '{print $2}')
            else
                ip=$(grep -A30 "^  $service:" "$file_path" | grep "ipv4_address:" | head -1 | awk '{print $2}')
            fi
            
            expected="${expected_ips[$service]}"
            
            if [[ "$ip" == "$expected" ]]; then
                echo "  ✅ $file: $ip (正確)"
            elif [[ -n "$ip" ]]; then
                echo "  ❌ $file: $ip (預期: $expected)"
            else
                echo "  ⚠️ $file: 未找到 IP 配置"
            fi
        else
            echo "  ❓ $file: 檔案不存在"
        fi
    done
    echo ""
done

echo "🎯 統一 IP 配置標準:"
echo "  📡 PostgreSQL: 172.20.0.51"
echo "  📊 Redis: 172.20.0.50"  
echo "  🚀 NetStack API: 172.20.0.40"
echo ""
echo "✅ IP 配置一致性檢查完成"