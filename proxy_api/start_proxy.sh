#!/bin/bash
set -e

PROXY_IMAGE="ntn-proxy-api"
PROXY_CONTAINER="ntn-proxy"
BACKEND_NETWORK=$(docker inspect -f '{{range $net, $conf := .NetworkSettings.Networks}}{{$net}}{{end}}' fastapi_app)

# 構建代理API映像
echo "構建代理API映像..."
docker build -t $PROXY_IMAGE .

# 移除現有容器（如果存在）
docker rm -f $PROXY_CONTAINER 2>/dev/null || true

# 啟動代理API容器
echo "啟動代理API容器..."
docker run -d --name $PROXY_CONTAINER \
    --network $BACKEND_NETWORK \
    -p 8888:8888 \
    $PROXY_IMAGE

echo "代理API已啟動!"
echo "可通過以下URL訪問: http://localhost:8888/api/status"
