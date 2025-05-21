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
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("metrics-exporter")

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

# 全局變量
METRICS = {}
CONTAINERS = {}
SIMULATION_MODE = False


def setup_metrics():
    """設置和初始化所有指標"""
    global METRICS

    # UE 連接狀態指標
    METRICS["ue_connected"] = Gauge("ntn_ue_connected", "UE連接數量", ["gnb_id"])
    METRICS["ue_registered"] = Gauge("ntn_ue_registered", "UE註冊數量", ["gnb_id"])

    # 無線性能指標
    METRICS["ue_rsrp"] = Gauge("ntn_ue_rsrp", "UE RSRP (dBm)", ["ue_id", "gnb_id"])
    METRICS["ue_rsrq"] = Gauge("ntn_ue_rsrq", "UE RSRQ (dB)", ["ue_id", "gnb_id"])
    METRICS["ue_sinr"] = Gauge("ntn_ue_sinr", "UE SINR (dB)", ["ue_id", "gnb_id"])
    METRICS["ue_cqi"] = Gauge("ntn_ue_cqi", "UE CQI", ["ue_id", "gnb_id"])

    # 網絡性能指標
    METRICS["pdu_session_setup_time"] = Histogram(
        "ntn_pdu_session_setup_time", "PDU會話建立時間 (ms)", ["ue_id"]
    )
    METRICS["ue_registration_time"] = Histogram(
        "ntn_ue_registration_time", "UE註冊時間 (ms)", ["ue_id"]
    )
    METRICS["ping_latency"] = Histogram(
        "ntn_ping_latency", "Ping延遲 (ms)", ["ue_id", "destination"]
    )

    # 吞吐量指標
    METRICS["ue_uplink_throughput"] = Gauge(
        "ntn_ue_uplink_throughput", "UE上行吞吐量 (bps)", ["ue_id"]
    )
    METRICS["ue_downlink_throughput"] = Gauge(
        "ntn_ue_downlink_throughput", "UE下行吞吐量 (bps)", ["ue_id"]
    )

    # 故障指標
    METRICS["ue_connection_failures"] = Counter(
        "ntn_ue_connection_failures", "UE連接失敗次數", ["ue_id", "failure_type"]
    )
    METRICS["gnb_connection_failures"] = Counter(
        "ntn_gnb_connection_failures", "gNodeB連接失敗次數", ["gnb_id", "failure_type"]
    )

    # 恢復指標
    METRICS["ue_recovery_time"] = Histogram(
        "ntn_ue_recovery_time", "UE恢復時間 (ms)", ["ue_id", "failure_type"]
    )
    METRICS["gnb_recovery_time"] = Histogram(
        "ntn_gnb_recovery_time", "gNodeB恢復時間 (ms)", ["gnb_id", "failure_type"]
    )

    # 衛星特有指標
    METRICS["satellite_link_quality"] = Gauge(
        "ntn_satellite_link_quality", "衛星鏈路質量", ["satellite_id"]
    )
    METRICS["satellite_link_delay"] = Gauge(
        "ntn_satellite_link_delay", "衛星鏈路延遲 (ms)", ["satellite_id"]
    )
    METRICS["doppler_shift"] = Gauge(
        "ntn_doppler_shift", "多普勒頻移 (Hz)", ["satellite_id"]
    )

    # 系統資源指標
    METRICS["cpu_usage"] = Gauge("ntn_cpu_usage", "CPU使用率 (%)", ["container_id"])
    METRICS["memory_usage"] = Gauge(
        "ntn_memory_usage", "Memory使用率 (%)", ["container_id"]
    )
    METRICS["disk_usage"] = Gauge("ntn_disk_usage", "Disk使用率 (%)", ["container_id"])

    logger.info("所有指標已初始化")


def discover_containers():
    """發現並跟踪所有相關的容器"""
    global CONTAINERS

    try:
        cmd = ["docker", "ps", "--format", "{{.Names}}"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        container_names = result.stdout.strip().split("\n")

        for name in container_names:
            if not name:
                continue

            if "gnb" in name or "ue" in name or "open5gs" in name:
                CONTAINERS[name] = {"id": name}
                logger.info(f"發現容器: {name}")

    except subprocess.CalledProcessError as e:
        logger.error(f"發現容器時出錯: {e}")
    except Exception as e:
        logger.error(f"發現容器時發生未知錯誤: {e}")

    logger.info(f"共發現 {len(CONTAINERS)} 個相關容器")


def collect_ue_metrics():
    """收集UE相關指標"""
    if SIMULATION_MODE:
        simulate_ue_metrics()
        return

    try:
        # 查找所有UE容器
        ue_containers = [name for name in CONTAINERS.keys() if "ue" in name.lower()]

        for container in ue_containers:
            # 收集UE狀態
            cmd = [
                "docker",
                "exec",
                container,
                "nr-cli",
                "imsi-999700000000001",
                "-e",
                "status",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                # 分析輸出獲取狀態
                status_output = result.stdout

                # 例如: 檢測是否連接
                if "CM-STATE: CM-CONNECTED" in status_output:
                    METRICS["ue_connected"].labels(gnb_id="gnb1").set(1)
                else:
                    METRICS["ue_connected"].labels(gnb_id="gnb1").set(0)

                # 收集信號質量指標 (RSRP, RSRQ, 等)
                rsrp_value = extract_metric_from_output(status_output, "RSRP:")
                if rsrp_value:
                    METRICS["ue_rsrp"].labels(ue_id="ue1", gnb_id="gnb1").set(
                        float(rsrp_value)
                    )

                rsrq_value = extract_metric_from_output(status_output, "RSRQ:")
                if rsrq_value:
                    METRICS["ue_rsrq"].labels(ue_id="ue1", gnb_id="gnb1").set(
                        float(rsrq_value)
                    )

                # 檢查PDU會話
                cmd = [
                    "docker",
                    "exec",
                    container,
                    "nr-cli",
                    "imsi-999700000000001",
                    "-e",
                    "ps-list",
                ]
                ps_result = subprocess.run(cmd, capture_output=True, text=True)

                if ps_result.returncode == 0 and "PDU SESSION[" in ps_result.stdout:
                    METRICS["ue_registered"].labels(gnb_id="gnb1").set(1)
                else:
                    METRICS["ue_registered"].labels(gnb_id="gnb1").set(0)

                # 執行ping測試測量延遲
                cmd = [
                    "docker",
                    "exec",
                    container,
                    "ping",
                    "-I",
                    "uesimtun0",
                    "10.45.0.1",
                    "-c",
                    "1",
                ]
                ping_result = subprocess.run(cmd, capture_output=True, text=True)

                if ping_result.returncode == 0:
                    # 提取時間
                    latency = extract_ping_latency(ping_result.stdout)
                    if latency:
                        METRICS["ping_latency"].labels(
                            ue_id="ue1", destination="upf"
                        ).observe(latency)
            else:
                # 連接失敗
                logger.warning(f"無法從容器 {container} 獲取UE狀態: {result.stderr}")
                METRICS["ue_connection_failures"].labels(
                    ue_id="ue1", failure_type="status_check"
                ).inc()

    except Exception as e:
        logger.error(f"收集UE指標時出錯: {e}")


def collect_gnb_metrics():
    """收集gNodeB相關指標"""
    if SIMULATION_MODE:
        simulate_gnb_metrics()
        return

    try:
        # 查找所有gNodeB容器
        gnb_containers = [name for name in CONTAINERS.keys() if "gnb" in name.lower()]

        for container in gnb_containers:
            # 檢查gNodeB狀態
            cmd = ["docker", "exec", container, "cat", "/proc/net/dev"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                # 分析輸出以獲取網絡統計信息
                # 這裡僅為示例，實際生產環境中需要更精確的指標收集
                pass
            else:
                logger.warning(
                    f"無法從容器 {container} 獲取gNodeB狀態: {result.stderr}"
                )

    except Exception as e:
        logger.error(f"收集gNodeB指標時出錯: {e}")


def collect_system_metrics():
    """收集系統資源指標"""
    if SIMULATION_MODE:
        simulate_system_metrics()
        return

    try:
        for container_name, container_info in CONTAINERS.items():
            # 收集CPU使用率
            cmd = [
                "docker",
                "stats",
                container_name,
                "--no-stream",
                "--format",
                "{{.CPUPerc}}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                cpu_usage = result.stdout.strip().replace("%", "")
                try:
                    METRICS["cpu_usage"].labels(container_id=container_name).set(
                        float(cpu_usage)
                    )
                except ValueError:
                    logger.warning(f"無法解析CPU使用率: {cpu_usage}")

            # 收集內存使用率
            cmd = [
                "docker",
                "stats",
                container_name,
                "--no-stream",
                "--format",
                "{{.MemPerc}}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                mem_usage = result.stdout.strip().replace("%", "")
                try:
                    METRICS["memory_usage"].labels(container_id=container_name).set(
                        float(mem_usage)
                    )
                except ValueError:
                    logger.warning(f"無法解析內存使用率: {mem_usage}")

    except Exception as e:
        logger.error(f"收集系統指標時出錯: {e}")


def collect_satellite_metrics():
    """收集衛星特有的指標"""
    if SIMULATION_MODE:
        simulate_satellite_metrics()
        return

    # 在實際生產環境中，這裡應該從衛星系統或模擬器獲取實際數據
    # 這個示例暫時留空


# 模擬數據生成函數
def simulate_ue_metrics():
    """模擬UE指標數據"""
    # UE連接和註冊
    METRICS["ue_connected"].labels(gnb_id="gnb1").set(1)
    METRICS["ue_registered"].labels(gnb_id="gnb1").set(1)

    # 無線性能指標 - 使用更真實的值範圍
    rsrp = random.uniform(-110, -80)  # dBm
    rsrq = random.uniform(-15, -5)  # dB
    sinr = random.uniform(5, 25)  # dB
    cqi = random.randint(1, 15)

    METRICS["ue_rsrp"].labels(ue_id="ue1", gnb_id="gnb1").set(rsrp)
    METRICS["ue_rsrq"].labels(ue_id="ue1", gnb_id="gnb1").set(rsrq)
    METRICS["ue_sinr"].labels(ue_id="ue1", gnb_id="gnb1").set(sinr)
    METRICS["ue_cqi"].labels(ue_id="ue1", gnb_id="gnb1").set(cqi)

    # 隨機模擬一些故障
    if random.random() < 0.05:  # 5%的機率
        METRICS["ue_connection_failures"].labels(
            ue_id="ue1", failure_type="rrc_setup"
        ).inc()
        METRICS["ue_recovery_time"].labels(
            ue_id="ue1", failure_type="rrc_setup"
        ).observe(random.uniform(100, 500))

    # 網絡性能
    METRICS["pdu_session_setup_time"].labels(ue_id="ue1").observe(
        random.uniform(50, 200)
    )
    METRICS["ue_registration_time"].labels(ue_id="ue1").observe(
        random.uniform(100, 300)
    )
    METRICS["ping_latency"].labels(ue_id="ue1", destination="upf").observe(
        random.uniform(20, 50)
    )

    # 吞吐量
    uplink = random.uniform(1000000, 10000000)  # 1-10 Mbps
    downlink = random.uniform(5000000, 50000000)  # 5-50 Mbps
    METRICS["ue_uplink_throughput"].labels(ue_id="ue1").set(uplink)
    METRICS["ue_downlink_throughput"].labels(ue_id="ue1").set(downlink)


def simulate_gnb_metrics():
    """模擬gNodeB指標數據"""
    # gNodeB故障模擬
    if random.random() < 0.03:  # 3%的機率
        METRICS["gnb_connection_failures"].labels(
            gnb_id="gnb1", failure_type="amf_connection"
        ).inc()
        METRICS["gnb_recovery_time"].labels(
            gnb_id="gnb1", failure_type="amf_connection"
        ).observe(random.uniform(200, 800))


def simulate_system_metrics():
    """模擬系統資源指標數據"""
    # 為模擬的容器創建隨機但合理的資源使用數據
    containers = [
        "gnb1",
        "ntn-stack-ues1-1",
        "open5gs-amf",
        "open5gs-smf",
        "open5gs-upf",
    ]

    for container in containers:
        cpu = random.uniform(5, 30)  # 5-30% CPU使用率
        memory = random.uniform(10, 50)  # 10-50% 內存使用率
        disk = random.uniform(20, 60)  # 20-60% 磁盤使用率

        METRICS["cpu_usage"].labels(container_id=container).set(cpu)
        METRICS["memory_usage"].labels(container_id=container).set(memory)
        METRICS["disk_usage"].labels(container_id=container).set(disk)


def simulate_satellite_metrics():
    """模擬衛星特有的指標數據"""
    satellites = ["leo1", "meo1", "geo1"]
    link_qualities = {
        "leo1": (70, 90),
        "meo1": (60, 80),
        "geo1": (50, 70),
    }  # 鏈路質量範圍
    link_delays = {
        "leo1": (20, 60),
        "meo1": (100, 200),
        "geo1": (250, 350),
    }  # 延遲範圍(ms)
    doppler_shifts = {
        "leo1": (500, 1500),
        "meo1": (200, 800),
        "geo1": (50, 150),
    }  # 多普勒頻移範圍(Hz)

    for sat in satellites:
        quality_range = link_qualities[sat]
        delay_range = link_delays[sat]
        doppler_range = doppler_shifts[sat]

        quality = random.uniform(quality_range[0], quality_range[1])
        delay = random.uniform(delay_range[0], delay_range[1])
        doppler = random.uniform(doppler_range[0], doppler_range[1])

        METRICS["satellite_link_quality"].labels(satellite_id=sat).set(quality)
        METRICS["satellite_link_delay"].labels(satellite_id=sat).set(delay)
        METRICS["doppler_shift"].labels(satellite_id=sat).set(doppler)


# 工具函數
def extract_metric_from_output(output: str, metric_prefix: str) -> Optional[str]:
    """從輸出文本中提取指標值"""
    lines = output.split("\n")
    for line in lines:
        if metric_prefix in line:
            parts = line.split(metric_prefix)
            if len(parts) > 1:
                value = parts[1].strip().split()[0]
                return value
    return None


def extract_ping_latency(ping_output: str) -> Optional[float]:
    """從ping輸出中提取延遲值"""
    lines = ping_output.split("\n")
    for line in lines:
        if "time=" in line:
            parts = line.split("time=")
            if len(parts) > 1:
                time_part = parts[1].strip().split()[0]
                try:
                    return float(time_part.replace("ms", ""))
                except ValueError:
                    return None
    return None


def main():
    """主函數"""
    global SIMULATION_MODE

    parser = argparse.ArgumentParser(description="NTN 5G網絡指標導出器")
    parser.add_argument("--port", type=int, default=9091, help="HTTP服務器端口")
    parser.add_argument("--interval", type=int, default=15, help="指標收集間隔(秒)")
    parser.add_argument("--simulate", action="store_true", help="使用模擬數據")

    args = parser.parse_args()

    port = args.port
    interval = args.interval
    SIMULATION_MODE = args.simulate

    logger.info(
        f"啟動NTN 5G網絡指標導出器 (端口: {port}, 間隔: {interval}秒, 模擬模式: {SIMULATION_MODE})"
    )

    # 初始化指標
    setup_metrics()

    # 如果不是模擬模式，發現容器
    if not SIMULATION_MODE:
        discover_containers()

    # 啟動HTTP服務器
    start_http_server(port)
    logger.info(f"HTTP服務器已啟動在端口 {port}")

    # 循環收集指標
    while True:
        try:
            collect_ue_metrics()
            collect_gnb_metrics()
            collect_system_metrics()
            collect_satellite_metrics()

            time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("收到中斷信號，退出")
            break
        except Exception as e:
            logger.error(f"收集指標時發生錯誤: {e}")
            time.sleep(interval)


if __name__ == "__main__":
    main()
