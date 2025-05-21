#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NTN (Non-Terrestrial Network) 指標導出器

此腳本提供NTN網絡特有指標的收集和導出功能，包括：
- 衛星鏈路延遲指標
- 衛星切換性能指標
- UE連接統計指標
- 吞吐量和丟包率指標

用法：
    python3 metrics_exporter.py --port 9091 --interval 5
"""

import argparse
import logging
import os
import subprocess
import socket
import sys
import time
import json
from threading import Thread
from typing import Dict, List, Optional, Union
import re
import random

try:
    from prometheus_client import start_http_server, Gauge, Counter, Histogram, Summary
except ImportError:
    print("請安裝prometheus_client: pip install prometheus_client")
    sys.exit(1)

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/var/log/ntn/metrics_exporter.log"),
    ],
)
logger = logging.getLogger("ntn_metrics")

# 定義Prometheus指標
NTN_LINK_LATENCY = Gauge(
    "ntn_link_latency_ms", "NTN衛星鏈路延遲(ms)", ["link_id", "link_type"]
)

NTN_LINK_JITTER = Gauge(
    "ntn_link_jitter_ms", "NTN衛星鏈路抖動(ms)", ["link_id", "link_type"]
)

NTN_PACKETS_TOTAL = Counter(
    "ntn_packets_total", "NTN傳輸封包總數", ["direction", "link_id"]
)

NTN_PACKETS_LOST = Counter(
    "ntn_packets_lost", "NTN丟失封包數量", ["direction", "link_id"]
)

NTN_BYTES_RECEIVED = Counter(
    "ntn_bytes_received", "NTN接收位元組數", ["interface", "link_id"]
)

NTN_BYTES_TRANSMITTED = Counter(
    "ntn_bytes_transmitted", "NTN發送位元組數", ["interface", "link_id"]
)

UE_CONNECTION_SUCCESSFUL = Counter(
    "ue_connection_successful_total", "UE成功連接次數", ["ue_id", "gnb_id"]
)

UE_CONNECTION_FAILURES = Counter(
    "ue_connection_failures_total",
    "UE連接失敗次數",
    ["ue_id", "gnb_id", "failure_reason"],
)

PDU_SESSION_SETUP_TIME = Histogram(
    "pdu_session_setup_time_seconds",
    "PDU會話建立時間(秒)",
    ["ue_id", "session_type"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0),
)

SATELLITE_VISIBILITY_DURATION = Gauge(
    "satellite_visibility_duration_seconds",
    "衛星可見時間(秒)",
    ["satellite_id", "satellite_type"],
)

SATELLITE_HANDOVER_TIME = Histogram(
    "satellite_handover_time_seconds",
    "衛星切換時間(秒)",
    ["source_id", "target_id"],
    buckets=(0.1, 0.5, 1.0, 3.0, 5.0, 10.0, 20.0),
)

SATELLITE_HANDOVER_FAILURES = Counter(
    "satellite_handover_failures_total",
    "衛星切換失敗次數",
    ["source_id", "target_id", "failure_reason"],
)

LINK_SIGNAL_STRENGTH = Gauge(
    "link_signal_strength_dbm", "鏈路信號強度(dBm)", ["link_id", "link_type"]
)

LINK_SIGNAL_QUALITY = Gauge(
    "link_signal_quality_percent", "鏈路信號質量(%)", ["link_id", "link_type"]
)


def parse_arguments():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description="NTN網絡指標導出器")
    parser.add_argument(
        "--port", type=int, default=9091, help="HTTP服務器端口 (默認: 9091)"
    )
    parser.add_argument(
        "--interval", type=int, default=5, help="指標收集間隔(秒) (默認: 5)"
    )
    parser.add_argument(
        "--simulate", action="store_true", help="使用模擬數據 (默認: 根據環境自動決定)"
    )
    return parser.parse_args()


def check_docker_environment() -> bool:
    """檢查是否在Docker環境中運行"""
    return os.path.exists("/.dockerenv")


def check_network_mode() -> str:
    """檢測當前運行的網絡模式 (ground, leo, meo, geo)"""
    try:
        # 嘗試從TC命令獲取延遲信息
        result = subprocess.run(
            ["tc", "qdisc", "show", "dev", "eth0"],
            capture_output=True,
            text=True,
            check=False,
        )

        # 解析延遲值
        match = re.search(r"delay\s+(\d+\.?\d*)ms", result.stdout)
        if match:
            delay = float(match.group(1))

            # 根據延遲判斷模式
            if delay < 100:
                return "ground"
            elif delay < 400:
                return "leo"
            elif delay < 600:
                return "meo"
            else:
                return "geo"
    except Exception as e:
        logger.warning(f"檢測網絡模式時出錯: {str(e)}")

    # 默認返回leo模式
    return "leo"


def get_ping_stats(target: str = "8.8.8.8", count: int = 5) -> Dict[str, float]:
    """獲取ping統計數據"""
    stats = {"latency": 0.0, "jitter": 0.0, "packet_loss": 0.0}

    try:
        result = subprocess.run(
            ["ping", "-c", str(count), target],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # 解析延遲
        latency_match = re.search(
            r"rtt min/avg/max/mdev = (\d+\.?\d*)/(\d+\.?\d*)/(\d+\.?\d*)/(\d+\.?\d*)",
            result.stdout,
        )
        if latency_match:
            stats["latency"] = float(latency_match.group(2))  # 平均延遲
            stats["jitter"] = float(latency_match.group(4))  # mdev 作為抖動

        # 解析丟包率
        loss_match = re.search(r"(\d+\.?\d*)% packet loss", result.stdout)
        if loss_match:
            stats["packet_loss"] = float(loss_match.group(1))
    except Exception as e:
        logger.error(f"獲取ping統計失敗: {str(e)}")

    return stats


def get_interface_stats(interface: str = "uesimtun0") -> Dict[str, int]:
    """獲取網絡介面的統計數據"""
    stats = {
        "rx_bytes": 0,
        "tx_bytes": 0,
        "rx_packets": 0,
        "tx_packets": 0,
        "rx_errors": 0,
        "tx_errors": 0,
    }

    try:
        with open(f"/proc/net/dev", "r") as f:
            lines = f.readlines()

        for line in lines:
            if interface in line:
                fields = line.split(":")
                if len(fields) >= 2:
                    values = fields[1].strip().split()
                    stats["rx_bytes"] = int(values[0])
                    stats["rx_packets"] = int(values[1])
                    stats["rx_errors"] = int(values[2])
                    stats["tx_bytes"] = int(values[8])
                    stats["tx_packets"] = int(values[9])
                    stats["tx_errors"] = int(values[10])
    except Exception as e:
        logger.error(f"獲取介面統計失敗: {str(e)}")

    return stats


def get_satellite_stats(mode: str = "leo") -> Dict[str, any]:
    """獲取衛星相關統計數據 (模擬)"""
    sat_types = {
        "leo": {
            "alt": 1200,
            "visibility": 900,
            "handover_time": 0.8,
            "signal_strength": -90,
        },
        "meo": {
            "alt": 8000,
            "visibility": 3600,
            "handover_time": 1.5,
            "signal_strength": -100,
        },
        "geo": {
            "alt": 35786,
            "visibility": 86400,
            "handover_time": 3.0,
            "signal_strength": -110,
        },
    }

    sat_type = sat_types.get(mode, sat_types["leo"])
    visibility = sat_type["visibility"] * (0.9 + 0.2 * random.random())
    handover_time = sat_type["handover_time"] * (0.8 + 0.4 * random.random())
    signal_strength = sat_type["signal_strength"] * (0.9 + 0.2 * random.random())
    signal_quality = (
        random.uniform(70, 100)
        if mode == "ground"
        else (
            random.uniform(60, 95)
            if mode == "leo"
            else random.uniform(50, 90) if mode == "meo" else random.uniform(40, 85)
        )
    )

    return {
        "visibility": visibility,
        "handover_time": handover_time,
        "signal_strength": signal_strength,
        "signal_quality": signal_quality,
    }


def collect_ntn_metrics(mode: str, simulate: bool = False):
    """收集NTN特有的指標"""
    # 根據模式設置基本參數
    link_id = f"ntn-{mode}-link-1"
    link_type = mode
    ue_id = "imsi-999700000000001"
    gnb_id = "gnb1"

    if simulate:
        # 模擬數據
        latency_base = (
            50
            if mode == "ground"
            else 250 if mode == "leo" else 500 if mode == "meo" else 750
        )
        latency = latency_base * (0.9 + 0.2 * random.random())
        jitter = latency * 0.1 * random.random()
        packet_loss = (
            0.01
            if mode == "ground"
            else 0.02 if mode == "leo" else 0.03 if mode == "meo" else 0.05
        ) * (0.8 + 0.4 * random.random())
        rx_bytes = int(random.uniform(1000, 10000))
        tx_bytes = int(random.uniform(1000, 5000))
        packets_total = int(random.uniform(100, 1000))
        packets_lost = int(packets_total * packet_loss)

        # UE連接相關
        if random.random() > 0.95:  # 5% 機率記錄一次連接事件
            if random.random() > 0.2:  # 80% 機率連接成功
                UE_CONNECTION_SUCCESSFUL.labels(ue_id=ue_id, gnb_id=gnb_id).inc()
            else:
                failure_reasons = [
                    "timeout",
                    "authentication_failure",
                    "handover_failure",
                    "congestion",
                ]
                failure_reason = random.choice(failure_reasons)
                UE_CONNECTION_FAILURES.labels(
                    ue_id=ue_id, gnb_id=gnb_id, failure_reason=failure_reason
                ).inc()

        # PDU會話時間
        if random.random() > 0.9:  # 10% 機率記錄PDU會話時間
            session_time = (latency / 1000) * (
                2 + random.random() * 8
            )  # 根據延遲計算會話時間
            PDU_SESSION_SETUP_TIME.labels(ue_id=ue_id, session_type="ipv4").observe(
                session_time
            )

        # 衛星指標
        sat_stats = get_satellite_stats(mode)
        sat_id = f"sat-{mode}-1"
        SATELLITE_VISIBILITY_DURATION.labels(
            satellite_id=sat_id, satellite_type=mode
        ).set(sat_stats["visibility"])

        # 衛星切換
        if random.random() > 0.98:  # 2% 機率記錄衛星切換
            source_id = f"sat-{mode}-1"
            target_id = f"sat-{mode}-2"
            if random.random() > 0.1:  # 90% 機率切換成功
                SATELLITE_HANDOVER_TIME.labels(
                    source_id=source_id, target_id=target_id
                ).observe(sat_stats["handover_time"])
            else:
                failure_reasons = [
                    "visibility_lost",
                    "link_failure",
                    "synchronization_error",
                ]
                failure_reason = random.choice(failure_reasons)
                SATELLITE_HANDOVER_FAILURES.labels(
                    source_id=source_id,
                    target_id=target_id,
                    failure_reason=failure_reason,
                ).inc()
    else:
        # 實際數據收集
        try:
            # 從ping獲取延遲和丟包
            target = "10.45.0.1"  # UPF地址
            ping_stats = get_ping_stats(target)
            latency = ping_stats["latency"]
            jitter = ping_stats["jitter"]
            packet_loss = ping_stats["packet_loss"] / 100.0

            # 獲取介面統計
            interface = "uesimtun0"
            if_stats = get_interface_stats(interface)
            rx_bytes = if_stats["rx_bytes"]
            tx_bytes = if_stats["tx_bytes"]
            packets_total = if_stats["rx_packets"] + if_stats["tx_packets"]
            packets_lost = if_stats["rx_errors"] + if_stats["tx_errors"]

            # 嘗試從NTN特有日誌或API中獲取數據
            # ...實際部署時實現

            # 衛星相關指標使用模擬數據
            sat_stats = get_satellite_stats(mode)
        except Exception as e:
            logger.error(f"實際數據收集出錯: {str(e)}，使用模擬數據")
            # 執行故障回退到模擬數據
            return collect_ntn_metrics(mode, simulate=True)

    # 更新指標
    NTN_LINK_LATENCY.labels(link_id=link_id, link_type=link_type).set(latency)
    NTN_LINK_JITTER.labels(link_id=link_id, link_type=link_type).set(jitter)

    # 更新計數器增量
    NTN_PACKETS_TOTAL.labels(direction="downlink", link_id=link_id).inc(packets_total)
    NTN_PACKETS_LOST.labels(direction="downlink", link_id=link_id).inc(packets_lost)

    NTN_BYTES_RECEIVED.labels(interface="uesimtun0", link_id=link_id).inc(rx_bytes)
    NTN_BYTES_TRANSMITTED.labels(interface="uesimtun0", link_id=link_id).inc(tx_bytes)

    # 信號強度和質量
    LINK_SIGNAL_STRENGTH.labels(link_id=link_id, link_type=link_type).set(
        sat_stats["signal_strength"]
    )
    LINK_SIGNAL_QUALITY.labels(link_id=link_id, link_type=link_type).set(
        sat_stats["signal_quality"]
    )

    logger.debug(
        f"已更新NTN指標: mode={mode}, latency={latency:.2f}ms, jitter={jitter:.2f}ms, packet_loss={packet_loss:.2%}"
    )


def main():
    """主函數"""
    args = parse_arguments()

    # 創建日誌目錄
    os.makedirs("/var/log/ntn", exist_ok=True)

    # 檢測環境和網絡模式
    is_docker = check_docker_environment()
    network_mode = check_network_mode()
    logger.info(
        f"NTN指標導出器啟動: 運行於{'Docker環境' if is_docker else '非Docker環境'}, 網絡模式: {network_mode}"
    )

    # 決定是否使用模擬數據
    use_simulation = args.simulate
    if not args.simulate:
        # 如果不是Docker環境，默認使用模擬數據
        use_simulation = not is_docker

    logger.info(f"使用{'模擬' if use_simulation else '實際'}數據")

    # 啟動HTTP服務器
    start_http_server(args.port)
    logger.info(f"HTTP服務器啟動在端口 {args.port}")

    # 初始化一些全局指標
    sat_id = f"sat-{network_mode}-1"
    sat_stats = get_satellite_stats(network_mode)
    SATELLITE_VISIBILITY_DURATION.labels(
        satellite_id=sat_id, satellite_type=network_mode
    ).set(sat_stats["visibility"])

    try:
        # 主循環
        while True:
            collect_ntn_metrics(network_mode, use_simulation)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("收到中斷信號，關閉服務")
    except Exception as e:
        logger.error(f"運行時錯誤: {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
