#!/usr/bin/env python3
"""
測試優先級配置
定義測試程式的優先級分級和執行策略
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class Priority(Enum):
    """測試優先級等級"""

    CRITICAL = 1  # 關鍵測試 - 核心功能
    HIGH = 2  # 高優先級 - 重要功能
    MEDIUM = 3  # 中優先級 - 一般功能
    LOW = 4  # 低優先級 - 輔助功能


@dataclass
class TestCase:
    """測試案例配置"""

    path: str
    priority: Priority
    description: str
    dependencies: List[str] = None
    timeout: int = 30
    retry_count: int = 1


class TestPriorityConfig:
    """測試優先級配置管理器"""

    def __init__(self):
        self.test_cases = self._define_test_priorities()

    def _define_test_priorities(self) -> Dict[str, TestCase]:
        """定義所有測試的優先級"""
        return {
            # ============= 關鍵測試 (CRITICAL) =============
            # 核心系統健康檢查 - 必須最先通過
            "health_check": TestCase(
                path="unit/simworld/test_health_check.py",
                priority=Priority.CRITICAL,
                description="SimWorld 健康檢查 - 系統核心運行狀態",
                timeout=10,
            ),
            "netstack_health": TestCase(
                path="unit/netstack/test_api_health.py",
                priority=Priority.CRITICAL,
                description="NetStack API 健康檢查 - 網路堆疊核心",
                timeout=15,
            ),
            # 基礎 API 功能
            "simworld_api": TestCase(
                path="unit/simworld/test_api_functions.py",
                priority=Priority.CRITICAL,
                description="SimWorld API 基礎功能測試",
                dependencies=["health_check"],
                timeout=20,
            ),
            # ============= 高優先級測試 (HIGH) =============
            # 核心模組功能
            "simworld_scene": TestCase(
                path="unit/simworld/test_scene.py",
                priority=Priority.HIGH,
                description="SimWorld 場景管理功能",
                dependencies=["health_check", "simworld_api"],
                timeout=25,
            ),
            "deployment_basic": TestCase(
                path="unit/deployment/test_basic_functionality.py",
                priority=Priority.HIGH,
                description="部署模組基礎功能測試",
                timeout=30,
            ),
            # ============= 中優先級測試 (MEDIUM) =============
            # 系統整合測試
            "satellite_gnb_mapping": TestCase(
                path="integration/test_satellite_gnb_mapping.py",
                priority=Priority.MEDIUM,
                description="衛星-基站映射整合測試",
                dependencies=["health_check", "netstack_health"],
                timeout=45,
            ),
            "interference_control": TestCase(
                path="integration/test_interference_control.py",
                priority=Priority.MEDIUM,
                description="干擾控制整合測試",
                dependencies=["satellite_gnb_mapping"],
                timeout=60,
            ),
            "sionna_integration": TestCase(
                path="integration/test_sionna_integration.py",
                priority=Priority.MEDIUM,
                description="Sionna 整合測試",
                dependencies=["health_check"],
                timeout=90,
            ),
            # API 系統測試
            "api_comprehensive": TestCase(
                path="api/api_tests.py",
                priority=Priority.MEDIUM,
                description="綜合 API 測試",
                dependencies=["simworld_api", "netstack_health"],
                timeout=120,
            ),
            # ============= 低優先級測試 (LOW) =============
            # 特定情境測試
            "connectivity_tests": TestCase(
                path="integration/connectivity_tests.py",
                priority=Priority.LOW,
                description="連接性測試",
                dependencies=["satellite_gnb_mapping"],
                timeout=180,
            ),
            "interference_tests": TestCase(
                path="integration/interference_tests.py",
                priority=Priority.LOW,
                description="干擾測試",
                dependencies=["interference_control"],
                timeout=120,
            ),
            "failover_tests": TestCase(
                path="integration/failover_tests.py",
                priority=Priority.LOW,
                description="故障轉移測試",
                dependencies=["connectivity_tests"],
                timeout=300,
            ),
            # E2E 測試 - 最後執行
            "e2e_quick": TestCase(
                path="e2e/run_quick_test.py",
                priority=Priority.LOW,
                description="端到端快速測試",
                dependencies=["api_comprehensive"],
                timeout=600,
            ),
        }

    def get_tests_by_priority(self, priority: Priority) -> List[TestCase]:
        """取得指定優先級的測試"""
        return [test for test in self.test_cases.values() if test.priority == priority]

    def get_ordered_tests(self) -> List[TestCase]:
        """取得按優先級排序的測試列表"""
        ordered = []
        for priority in Priority:
            priority_tests = self.get_tests_by_priority(priority)
            # 按依賴關係排序
            priority_tests.sort(
                key=lambda x: len(x.dependencies) if x.dependencies else 0
            )
            ordered.extend(priority_tests)
        return ordered

    def get_test_by_name(self, name: str) -> TestCase:
        """根據名稱取得測試配置"""
        return self.test_cases.get(name)

    def validate_dependencies(self) -> List[str]:
        """驗證測試依賴關係"""
        errors = []
        for name, test in self.test_cases.items():
            if test.dependencies:
                for dep in test.dependencies:
                    if dep not in self.test_cases:
                        errors.append(f"測試 '{name}' 依賴不存在的測試 '{dep}'")
        return errors

    def get_critical_tests(self) -> List[TestCase]:
        """取得關鍵測試列表"""
        return self.get_tests_by_priority(Priority.CRITICAL)

    def get_high_priority_tests(self) -> List[TestCase]:
        """取得高優先級測試列表"""
        return self.get_tests_by_priority(Priority.HIGH)


# 全域配置實例
TEST_PRIORITY_CONFIG = TestPriorityConfig()
