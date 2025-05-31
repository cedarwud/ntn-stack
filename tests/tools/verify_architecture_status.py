#!/usr/bin/env python3
"""
三個重構目標驗證腳本

驗證以下目標的達成情況：
1. NetStack 事件驅動架構（干擾檢測異步化）
2. SimWorld CQRS 模式（衛星位置讀寫分離）
3. 全面異步微服務架構
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any
import importlib.util


def check_file_exists(file_path: str) -> bool:
    """檢查檔案是否存在"""
    return Path(file_path).exists()


def check_service_implementation(
    service_path: str, required_classes: List[str]
) -> Dict[str, bool]:
    """檢查服務實現是否包含必要的類別"""
    results = {}

    if not check_file_exists(service_path):
        return {cls: False for cls in required_classes}

    try:
        with open(service_path, "r", encoding="utf-8") as f:
            content = f.read()

        for cls in required_classes:
            results[cls] = f"class {cls}" in content

    except Exception as e:
        print(f"❌ 檢查 {service_path} 失敗: {e}")
        results = {cls: False for cls in required_classes}

    return results


def check_api_integration(
    api_path: str, required_endpoints: List[str]
) -> Dict[str, bool]:
    """檢查 API 整合情況"""
    results = {}

    if not check_file_exists(api_path):
        return {endpoint: False for endpoint in required_endpoints}

    try:
        with open(api_path, "r", encoding="utf-8") as f:
            content = f.read()

        for endpoint in required_endpoints:
            results[endpoint] = endpoint in content

    except Exception as e:
        print(f"❌ 檢查 {api_path} 失敗: {e}")
        results = {endpoint: False for endpoint in required_endpoints}

    return results


def main():
    """主函數"""
    print("🔍 三個重構目標驗證開始...")
    print("=" * 60)

    # 檢查目標 1: NetStack 事件驅動架構
    print("\n✅ 目標 1: NetStack 事件驅動架構（干擾檢測異步化）")
    print("-" * 50)

    # 檢查事件總線服務
    event_bus_path = "netstack/netstack_api/services/event_bus_service.py"
    event_bus_classes = ["EventBusService", "Event", "EventStore", "EventPriority"]
    event_bus_results = check_service_implementation(event_bus_path, event_bus_classes)

    print(f"📋 事件總線服務檔案: {'✅' if check_file_exists(event_bus_path) else '❌'}")
    for cls, exists in event_bus_results.items():
        print(f"   - {cls}: {'✅' if exists else '❌'}")

    # 檢查干擾控制服務
    interference_path = "netstack/netstack_api/services/interference_control_service.py"
    interference_classes = ["InterferenceControlService", "InterferenceEventTypes"]
    interference_results = check_service_implementation(
        interference_path, interference_classes
    )

    print(
        f"📋 干擾控制服務檔案: {'✅' if check_file_exists(interference_path) else '❌'}"
    )
    for cls, exists in interference_results.items():
        print(f"   - {cls}: {'✅' if exists else '❌'}")

    # 檢查主程序整合
    main_py_path = "netstack/netstack_api/main.py"
    main_integrations = [
        "get_event_bus",
        "InterferenceControlService",
        "event_bus=event_bus",
    ]
    main_results = check_api_integration(main_py_path, main_integrations)

    print(f"📋 NetStack 主程序整合:")
    for integration, exists in main_results.items():
        print(f"   - {integration}: {'✅' if exists else '❌'}")

    # 檢查目標 2: SimWorld CQRS 模式
    print("\n✅ 目標 2: SimWorld CQRS 模式（衛星位置讀寫分離）")
    print("-" * 50)

    # 檢查 CQRS 衛星服務
    cqrs_path = (
        "simworld/backend/app/domains/satellite/services/cqrs_satellite_service.py"
    )
    cqrs_classes = [
        "CQRSSatelliteService",
        "SatelliteCommandService",
        "SatelliteQueryService",
        "SatelliteEventStore",
    ]
    cqrs_results = check_service_implementation(cqrs_path, cqrs_classes)

    print(f"📋 CQRS 衛星服務檔案: {'✅' if check_file_exists(cqrs_path) else '❌'}")
    for cls, exists in cqrs_results.items():
        print(f"   - {cls}: {'✅' if exists else '❌'}")

    # 檢查 API 路由器整合
    router_path = "simworld/backend/app/api/v1/router.py"
    router_endpoints = [
        "position-cqrs",
        "batch-positions-cqrs",
        "force-update-cqrs",
        "cqrs/satellite-service/stats",
    ]
    router_results = check_api_integration(router_path, router_endpoints)

    print(f"📋 SimWorld API 路由器整合:")
    for endpoint, exists in router_results.items():
        print(f"   - {endpoint}: {'✅' if exists else '❌'}")

    # 檢查 SimWorld 主程序
    simworld_main_path = "simworld/backend/app/main.py"
    simworld_integrations = ["CQRSSatelliteService", "cqrs_satellite_service"]
    simworld_results = check_api_integration(simworld_main_path, simworld_integrations)

    print(f"📋 SimWorld 主程序整合:")
    for integration, exists in simworld_results.items():
        print(f"   - {integration}: {'✅' if exists else '❌'}")

    # 檢查目標 3: 全面異步微服務架構
    print("\n✅ 目標 3: 全面異步微服務架構")
    print("-" * 50)

    # 檢查統一 API 路由器
    unified_router_path = "netstack/netstack_api/routers/unified_api_router.py"
    unified_features = [
        "event-driven/system-overview",
        "websocket",
        "ServiceDiscoveryResponse",
        "cross_service_events",
    ]
    unified_results = check_api_integration(unified_router_path, unified_features)

    print(
        f"📋 統一 API 路由器檔案: {'✅' if check_file_exists(unified_router_path) else '❌'}"
    )
    for feature, exists in unified_results.items():
        print(f"   - {feature}: {'✅' if exists else '❌'}")

    # 檢查依賴配置
    requirements_path = "requirements.txt"
    required_deps = ["aiohttp", "structlog", "pytest-asyncio", "httpx"]

    print(f"📋 依賴配置檢查:")
    if check_file_exists(requirements_path):
        with open(requirements_path, "r") as f:
            requirements_content = f.read()

        for dep in required_deps:
            exists = dep in requirements_content
            print(f"   - {dep}: {'✅' if exists else '❌'}")
    else:
        print("   - requirements.txt: ❌ 檔案不存在")

    # 檢查 Makefile 新架構命令
    makefile_path = "Makefile"
    makefile_commands = [
        "test-event-driven",
        "test-cqrs",
        "verify-architecture",
        "test-new-architecture",
    ]
    makefile_results = check_api_integration(makefile_path, makefile_commands)

    print(f"📋 Makefile 新架構命令:")
    for cmd, exists in makefile_results.items():
        print(f"   - {cmd}: {'✅' if exists else '❌'}")

    # 總結
    print("\n🎯 重構目標達成總結")
    print("=" * 60)

    total_checks = 0
    passed_checks = 0

    all_results = [
        event_bus_results,
        interference_results,
        main_results,
        cqrs_results,
        router_results,
        simworld_results,
        unified_results,
        makefile_results,
    ]

    for result_dict in all_results:
        for exists in result_dict.values():
            total_checks += 1
            if exists:
                passed_checks += 1

    # 額外檢查依賴
    if check_file_exists(requirements_path):
        with open(requirements_path, "r") as f:
            requirements_content = f.read()
        for dep in required_deps:
            total_checks += 1
            if dep in requirements_content:
                passed_checks += 1

    success_rate = (passed_checks / total_checks) * 100 if total_checks > 0 else 0

    print(f"📊 總體完成度: {passed_checks}/{total_checks} ({success_rate:.1f}%)")

    if success_rate >= 90:
        print("🎉 恭喜！三個重構目標已基本完成！")
        status = "✅ 已完成"
    elif success_rate >= 75:
        print("👍 很好！大部分重構已完成，還有一些細節需要完善。")
        status = "🔄 接近完成"
    elif success_rate >= 50:
        print("📝 重構已有重要進展，但還需要更多工作。")
        status = "🚧 進行中"
    else:
        print("⚠️  重構還需要大量工作。")
        status = "🔴 需要更多工作"

    print(f"\n📋 目標 1 (事件驅動): {status}")
    print(f"📋 目標 2 (CQRS): {status}")
    print(f"📋 目標 3 (異步微服務): {status}")

    print("\n💡 建議下一步:")
    print("1. 執行 `make verify-architecture` 進行實時驗證")
    print("2. 執行 `make test-new-architecture` 測試新架構")
    print("3. 執行 `make demo-new-architecture` 查看功能演示")

    return success_rate >= 75


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
