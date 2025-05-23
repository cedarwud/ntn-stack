#!/bin/bash
# 臨時 NTN 模擬器腳本
MODE="${1:-ground}"
echo "臨時模擬器: 接收到模式 $MODE"
case "$MODE" in
    leo|meo|geo|ground|default)
        echo "臨時模擬器: 正在模擬 $MODE 模式的網絡條件..."
        # Try to add a qdisc to loopback, which should generally be safe and available
        # Clean up existing qdisc on lo first to avoid errors if it already exists
        tc qdisc del dev lo root 2>/dev/null
        if tc qdisc add dev lo root netem delay 10ms loss 0.1% rate 100mbit; then
            echo "臨時模擬器: tc rule applied to lo for $MODE."
        else
            echo "臨時模擬器: tc 命令模擬失敗 (lo) for $MODE."
        fi
        echo "臨時模擬器: $MODE 模式模擬完成。"
        exit 0
        ;;
    *)
        echo "臨時模擬器: 未知模式: $MODE. 有效模式: leo, meo, geo, ground, default."
        exit 1
        ;;
esac
