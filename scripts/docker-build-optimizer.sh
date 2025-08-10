#!/bin/bash
# Docker 構建優化腳本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
NETSTACK_DIR="$PROJECT_DIR/netstack"

echo "🚀 Docker 構建優化工具"
echo "=============================="

# 檢查是否需要顯示幫助
if [[ "$1" == "--help" ]] || [[ "$1" == "help" ]] || [[ "$1" == "-h" ]]; then
    echo "用法: $0 [build_type] [use_multistage]"
    echo ""
    echo "參數："
    echo "  build_type     - 建置類型：development|production (預設: production)"
    echo "  use_multistage - 使用多階段建置：true|false (預設: false)"
    echo ""
    echo "範例："
    echo "  $0 production true   # 生產環境，多階段建置"
    echo "  $0 development       # 開發環境，單階段建置"
    echo "  $0                   # 預設設定 (production, 單階段)"
    exit 0
fi

# 檢查構建選項
BUILD_TYPE=${1:-production}
USE_MULTISTAGE=${2:-false}

echo "📊 構建配置："
echo "  構建類型: $BUILD_TYPE"
echo "  多階段構建: $USE_MULTISTAGE"
echo ""

# 選擇 Dockerfile
if [[ "$USE_MULTISTAGE" == "true" ]]; then
    DOCKERFILE="$NETSTACK_DIR/docker/Dockerfile.multistage"
    TARGET_STAGE=$BUILD_TYPE
    echo "📄 使用多階段 Dockerfile: $DOCKERFILE"
    echo "🎯 目標階段: $TARGET_STAGE"
else
    DOCKERFILE="$NETSTACK_DIR/docker/Dockerfile"
    TARGET_STAGE=""
    echo "📄 使用單階段 Dockerfile: $DOCKERFILE"
fi

# 檢查 Dockerfile 是否存在
if [[ ! -f "$DOCKERFILE" ]]; then
    echo "❌ Dockerfile 不存在: $DOCKERFILE"
    exit 1
fi

# 構建開始時間
BUILD_START=$(date +%s)

# 構建映像
echo ""
echo "🔨 開始構建 NetStack API 映像..."
echo ""

if [[ -n "$TARGET_STAGE" ]]; then
    # 多階段構建
    docker build \
        --file "$DOCKERFILE" \
        --target "$TARGET_STAGE" \
        --tag "netstack-api:${BUILD_TYPE}-multistage" \
        --build-arg BUILD_ENV="$BUILD_TYPE" \
        --build-arg INSTALL_DEV_TOOLS=$([ "$BUILD_TYPE" == "development" ] && echo "true" || echo "false") \
        "$NETSTACK_DIR"
    
    IMAGE_TAG="netstack-api:${BUILD_TYPE}-multistage"
else
    # 單階段構建
    docker build \
        --file "$DOCKERFILE" \
        --tag "netstack-api:${BUILD_TYPE}-single" \
        --build-arg BUILD_ENV="$BUILD_TYPE" \
        --build-arg INSTALL_DEV_TOOLS=$([ "$BUILD_TYPE" == "development" ] && echo "true" || echo "false") \
        "$NETSTACK_DIR"
    
    IMAGE_TAG="netstack-api:${BUILD_TYPE}-single"
fi

# 構建結束時間
BUILD_END=$(date +%s)
BUILD_TIME=$((BUILD_END - BUILD_START))

echo ""
echo "✅ 構建完成！"
echo ""

# 檢查映像資訊
echo "📊 映像資訊："
docker images "$IMAGE_TAG" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

echo ""
echo "⏱️ 構建時間: ${BUILD_TIME} 秒"

# 映像大小分析
IMAGE_SIZE=$(docker images "$IMAGE_TAG" --format "{{.Size}}")
echo "💾 映像大小: $IMAGE_SIZE"

# 構建層級分析
echo ""
echo "📋 構建層級分析："
docker history "$IMAGE_TAG" --format "table {{.CreatedBy}}\t{{.Size}}" | head -10

echo ""
echo "🎯 構建完成摘要："
echo "  ✅ 映像標籤: $IMAGE_TAG"
echo "  ✅ 構建時間: ${BUILD_TIME} 秒"
echo "  ✅ 映像大小: $IMAGE_SIZE"
echo ""

# 提供使用建議
echo "💡 使用建議："
if [[ "$USE_MULTISTAGE" == "true" ]]; then
    echo "  🚀 多階段構建完成，映像已優化"
    if [[ "$BUILD_TYPE" == "development" ]]; then
        echo "  📝 開發模式：包含開發工具和熱重載"
        echo "  🔧 運行命令: docker run -p 8080:8080 -v \$(pwd):/app $IMAGE_TAG"
    else
        echo "  🏭 生產模式：最小化映像，優化性能"  
        echo "  🔧 運行命令: docker run -p 8080:8080 $IMAGE_TAG"
    fi
else
    echo "  📦 單階段構建完成"
    echo "  🔧 運行命令: docker run -p 8080:8080 $IMAGE_TAG"
fi

echo ""
echo "✨ 構建優化完成！"