#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
UERANSIM 動態配置生成器

此腳本用於根據網絡模式和衛星/UE位置動態生成UERANSIM配置文件。
支持不同的網絡模式（地面、LEO、MEO、GEO）並可根據衛星軌道參數調整配置。

用法:
    python3 config_generator.py --mode leo --output-dir /path/to/config
    python3 config_generator.py --mode leo --sat-lat 23.5 --sat-lon 120.3 --sat-alt 1200
"""

import os
import sys
import argparse
import yaml
import math
import logging
import shutil
from datetime import datetime

# 設置日誌記錄
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("config_generator.log"), logging.StreamHandler()],
)
logger = logging.getLogger("config_generator")

# 配置模板路徑
CONFIG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config"
)
TEMPLATE_DIR = os.path.join(CONFIG_DIR, "ueransim")
OUTPUT_DIR = os.path.join(CONFIG_DIR, "generated")

# 支持的網絡模式
NETWORK_MODES = ["ground", "leo", "meo", "geo"]

# 不同網絡模式的默認參數
DEFAULT_PARAMS = {
    "ground": {
        "linkLatency": 50,
        "linkJitter": 5,
        "linkLossRate": 0.01,
        "rrcTimeout": 1000,
        "ngapTimeout": 1500,
        "coverageRadius": 30,
    },
    "leo": {
        "linkLatency": 250,
        "linkJitter": 20,
        "linkLossRate": 0.02,
        "rrcTimeout": 2500,
        "ngapTimeout": 3000,
        "coverageRadius": 800,
        "orbitHeight": 1200,
    },
    "meo": {
        "linkLatency": 500,
        "linkJitter": 35,
        "linkLossRate": 0.03,
        "rrcTimeout": 4500,
        "ngapTimeout": 5000,
        "coverageRadius": 2500,
        "orbitHeight": 8000,
    },
    "geo": {
        "linkLatency": 750,
        "linkJitter": 50,
        "linkLossRate": 0.05,
        "rrcTimeout": 6500,
        "ngapTimeout": 7000,
        "coverageRadius": 5000,
        "orbitHeight": 35786,
    },
}


def parse_arguments():
    """解析命令行參數"""
    parser = argparse.ArgumentParser(description="UERANSIM 動態配置生成器")
    parser.add_argument(
        "--mode",
        "-m",
        type=str,
        choices=NETWORK_MODES,
        default="leo",
        help="網絡模式: ground, leo, meo, geo",
    )
    parser.add_argument("--ue-id", "-u", type=str, default="ue1", help="要配置的UE ID")
    parser.add_argument(
        "--gnb-id", "-g", type=str, default="gnb1", help="要配置的gNB ID"
    )
    parser.add_argument("--sat-lat", type=float, help="衛星緯度")
    parser.add_argument("--sat-lon", type=float, help="衛星經度")
    parser.add_argument("--sat-alt", type=float, help="衛星高度(千米)")
    parser.add_argument(
        "--output-dir", "-o", type=str, default=OUTPUT_DIR, help="輸出配置文件的目錄"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細輸出模式")

    return parser.parse_args()


def load_template(mode, device_type):
    """載入指定模式和設備類型的配置模板"""
    template_file = os.path.join(TEMPLATE_DIR, f"{device_type}_{mode}.yaml")

    # 檢查模板文件是否存在
    if not os.path.exists(template_file):
        logger.error(f"模板文件不存在: {template_file}")
        raise FileNotFoundError(f"模板文件不存在: {template_file}")

    try:
        with open(template_file, "r") as file:
            template = yaml.safe_load(file) or {}
            logger.debug(f"已載入模板文件: {template_file}")
            return template
    except Exception as e:
        logger.error(f"載入模板失敗: {str(e)}")
        raise


def calculate_satellite_params(lat, lon, alt, mode):
    """根據衛星位置計算配置參數"""
    # 如果未提供位置參數，則使用默認值
    if lat is None or lon is None or alt is None:
        logger.info(f"使用{mode}模式的默認參數")
        return DEFAULT_PARAMS[mode]

    # 計算衛星參數
    params = DEFAULT_PARAMS[mode].copy()

    # 根據衛星高度調整延遲參數
    if mode != "ground":
        # 根據衛星高度計算傳播延遲(光速約300,000 km/s)
        propagation_delay = (alt * 1000 * 2) / 300000  # 毫秒，往返延遲
        params["linkLatency"] = int(
            propagation_delay + params["linkLatency"] * 0.3
        )  # 加上處理延遲

        # 調整其他參數
        params["beamAzimuth"] = calculate_azimuth(lat, lon)
        params["beamElevation"] = calculate_elevation(lat, lon, alt)

        # 根據距離調整覆蓋範圍
        params["coverageRadius"] = min(
            calculate_coverage_radius(alt), params["coverageRadius"] * 1.5
        )

    logger.debug(f"計算衛星參數: {params}")
    return params


def calculate_azimuth(lat, lon):
    """計算方位角"""
    # 簡化計算，實際應用中需要考慮觀測點位置
    return (lon + 180) % 360


def calculate_elevation(lat, lon, alt):
    """計算仰角"""
    # 簡化計算，實際應用中需要根據觀測點位置計算
    # 對於GEO衛星，通常固定在某個位置，仰角較為穩定
    if alt > 20000:  # GEO
        return 45
    elif alt > 5000:  # MEO
        return 60
    else:  # LEO
        return 75


def calculate_coverage_radius(alt):
    """根據衛星高度計算覆蓋半徑"""
    # 簡化計算，地球半徑約6371千米
    earth_radius = 6371
    # 衛星視界的覆蓋半徑
    coverage = math.sqrt((earth_radius + alt) ** 2 - earth_radius**2)
    return coverage


def update_config_with_params(config, params, device_type):
    """根據計算的參數更新配置"""
    updated_config = config.copy()

    # 更新通用參數
    if "linkLatency" in params:
        updated_config["linkLatency"] = params["linkLatency"]
    if "linkJitter" in params:
        updated_config["linkJitter"] = params["linkJitter"]
    if "linkLossRate" in params:
        updated_config["linkLossRate"] = params["linkLossRate"]

    # 根據設備類型更新特定參數
    if device_type == "gnb":
        if "rrcTimeout" in params:
            updated_config["rrcSetupTimeout"] = params["rrcTimeout"]
        if "ngapTimeout" in params:
            updated_config["ngapSetupTimeout"] = params["ngapTimeout"]
        if "coverageRadius" in params:
            updated_config["coverageRadius"] = params["coverageRadius"]
        if "beamAzimuth" in params:
            updated_config["beamAzimuth"] = params["beamAzimuth"]
        if "beamElevation" in params:
            updated_config["beamElevation"] = params["beamElevation"]
    elif device_type == "ue":
        # UE特定參數更新
        if "rrcTimeout" in params:
            updated_config["rrcEstablishmentTimeout"] = params["rrcTimeout"]
        # 根據延遲調整連接重試時間
        if "linkLatency" in params:
            latency_factor = params["linkLatency"] / 100
            updated_config["minConnRetryTimer"] = max(2, int(2 * latency_factor))
            updated_config["maxConnRetryTimer"] = max(15, int(15 * latency_factor))
            updated_config["pduSessionTimeout"] = max(
                1000, int(params["linkLatency"] * 3)
            )

    return updated_config


def save_config(config, filename, output_dir):
    """將配置保存到文件"""
    # 確保輸出目錄存在
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, filename)

    try:
        with open(output_file, "w") as file:
            yaml.dump(config, file, default_flow_style=False)
        logger.info(f"配置已保存到: {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"保存配置失敗: {str(e)}")
        raise


def generate_config(args):
    """生成配置文件"""
    mode = args.mode
    logger.info(f"正在為{mode}模式生成配置")

    # 載入模板
    gnb_template = load_template(mode, "gnb")
    ue_template = load_template(mode, "ue")

    # 計算參數
    sat_params = calculate_satellite_params(
        args.sat_lat, args.sat_lon, args.sat_alt, mode
    )

    # 更新配置
    gnb_config = update_config_with_params(gnb_template, sat_params, "gnb")
    ue_config = update_config_with_params(ue_template, sat_params, "ue")

    # 生成時間戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 保存配置
    gnb_file = save_config(
        gnb_config, f"gnb_{args.gnb_id}_{mode}_{timestamp}.yaml", args.output_dir
    )
    ue_file = save_config(
        ue_config, f"ue_{args.ue_id}_{mode}_{timestamp}.yaml", args.output_dir
    )

    # 創建最新配置的軟連接
    create_symlinks(gnb_file, ue_file, args.gnb_id, args.ue_id, args.output_dir)

    return gnb_file, ue_file


def create_symlinks(gnb_file, ue_file, gnb_id, ue_id, output_dir):
    """創建最新配置的軟連接"""
    gnb_link = os.path.join(output_dir, f"gnb_{gnb_id}_latest.yaml")
    ue_link = os.path.join(output_dir, f"ue_{ue_id}_latest.yaml")

    # 刪除現有軟連接
    if os.path.exists(gnb_link):
        os.remove(gnb_link)
    if os.path.exists(ue_link):
        os.remove(ue_link)

    # 創建指向最新配置的軟連接
    os.symlink(os.path.basename(gnb_file), gnb_link)
    os.symlink(os.path.basename(ue_file), ue_link)

    logger.info(f"創建軟連接: {gnb_link}")
    logger.info(f"創建軟連接: {ue_link}")


def main():
    """主函數"""
    args = parse_arguments()

    # 設置日誌級別
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        # 生成配置
        gnb_file, ue_file = generate_config(args)
        logger.info(f"配置生成成功: {gnb_file}, {ue_file}")
        print(f"配置生成成功: {gnb_file}, {ue_file}")

        # 成功退出
        return 0
    except Exception as e:
        logger.error(f"配置生成失敗: {str(e)}")
        print(f"錯誤: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
