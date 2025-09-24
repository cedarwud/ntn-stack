"""
Stage 4 Optimization Configuration Manager

This module handles loading, validation, and management of configuration
for the Stage 4 optimization decision layer.

Features:
- YAML configuration loading
- Configuration validation and defaults
- Runtime configuration updates
- Environment-specific overrides
- Configuration backup and versioning
"""

import logging
import os
import yaml
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pathlib import Path
import json
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class OptimizationObjectives:
    """優化目標配置"""
    signal_quality_weight: float = 0.4
    coverage_weight: float = 0.3
    handover_cost_weight: float = 0.2
    energy_efficiency_weight: float = 0.1


@dataclass
class Constraints:
    """約束條件配置"""
    min_satellites_per_pool: int = 5
    max_handover_frequency: int = 10
    min_signal_quality: float = -100.0
    max_latency_ms: int = 50


@dataclass
class PerformanceTargets:
    """性能目標配置"""
    processing_time_max_seconds: float = 10.0
    memory_usage_max_mb: int = 300
    decision_quality_min_score: float = 0.8
    constraint_satisfaction_min_rate: float = 0.95


@dataclass
class RLConfiguration:
    """RL擴展配置"""
    rl_enabled: bool = False
    hybrid_mode: bool = True
    rl_confidence_threshold: float = 0.7
    state_dimensions: int = 128
    action_space_size: int = 64


class ConfigurationManager:
    """配置管理器"""

    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(f"{__name__}.ConfigurationManager")

        # 配置路徑
        self.config_path = config_path or self._get_default_config_path()
        self.config_backup_dir = os.path.join(os.path.dirname(self.config_path), "backups")

        # 當前配置
        self.current_config: Dict[str, Any] = {}
        self.config_version = "1.0.0"
        self.last_updated = None

        # 默認配置
        self.default_config = self._get_default_configuration()

        # 配置更新歷史
        self.update_history: List[Dict[str, Any]] = []

        # 載入配置
        self._load_configuration()

        self.logger.info(f"✅ 配置管理器初始化完成: {self.config_path}")

    def _get_default_config_path(self) -> str:
        """獲取默認配置路徑"""
        # 嘗試多個可能的配置路徑
        possible_paths = [
            "config/stage4_optimization_config.yaml",
            "src/stages/stage4_optimization/default_config.yaml",
            "/orbit-engine/config/stage4_optimization_config.yaml"
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # 如果都不存在，返回第一個作為創建目標
        return possible_paths[0]

    def _get_default_configuration(self) -> Dict[str, Any]:
        """獲取默認配置"""
        return {
            "optimization_objectives": asdict(OptimizationObjectives()),
            "constraints": asdict(Constraints()),
            "performance_monitoring": {
                "enable_detailed_metrics": True,
                "benchmark_targets": asdict(PerformanceTargets())
            },
            "rl_extension": asdict(RLConfiguration()),
            "pool_planner": {
                "algorithm": "dynamic_clustering",
                "max_pools": 3,
                "min_pool_size": 5,
                "max_pool_size": 20
            },
            "handover_optimizer": {
                "algorithm": "predictive_optimization",
                "prediction_horizon_minutes": 15,
                "trigger_sensitivity": "medium"
            },
            "multi_objective_optimizer": {
                "algorithm": "nsga2",
                "population_size": 100,
                "max_generations": 50
            },
            "error_handling": {
                "max_retry_attempts": 3,
                "retry_delay_seconds": 1.0,
                "fallback_strategy": "simplified_optimization"
            },
            "logging": {
                "log_level": "INFO",
                "enable_performance_logs": True
            },
            "validation": {
                "enable_input_validation": True,
                "enable_output_validation": True
            }
        }

    def _load_configuration(self):
        """載入配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    loaded_config = yaml.safe_load(file)

                # 合併默認配置和載入的配置
                self.current_config = self._merge_configurations(
                    self.default_config, loaded_config
                )

                self.logger.info(f"✅ 配置文件載入成功: {self.config_path}")
            else:
                # 使用默認配置並創建配置文件
                self.current_config = self.default_config.copy()
                self._save_configuration()
                self.logger.warning(f"⚠️ 配置文件不存在，使用默認配置並創建: {self.config_path}")

            # 驗證配置
            self._validate_configuration()

            # 記錄更新
            self.last_updated = datetime.now(timezone.utc)

        except Exception as e:
            self.logger.error(f"❌ 配置載入失敗: {e}")
            self.current_config = self.default_config.copy()
            raise

    def _merge_configurations(self, default: Dict[str, Any],
                            loaded: Dict[str, Any]) -> Dict[str, Any]:
        """合併配置（深度合併）"""
        merged = default.copy()

        for key, value in loaded.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configurations(merged[key], value)
            else:
                merged[key] = value

        return merged

    def _validate_configuration(self):
        """驗證配置有效性"""
        try:
            # 驗證優化目標權重總和
            objectives = self.current_config.get("optimization_objectives", {})
            weight_sum = sum([
                objectives.get("signal_quality_weight", 0),
                objectives.get("coverage_weight", 0),
                objectives.get("handover_cost_weight", 0),
                objectives.get("energy_efficiency_weight", 0)
            ])

            if abs(weight_sum - 1.0) > 0.01:
                self.logger.warning(f"⚠️ 優化目標權重總和不為1.0: {weight_sum}")

            # 驗證約束條件
            constraints = self.current_config.get("constraints", {})
            if constraints.get("min_satellites_per_pool", 0) <= 0:
                raise ValueError("min_satellites_per_pool必須大於0")

            if constraints.get("max_handover_frequency", 0) <= 0:
                raise ValueError("max_handover_frequency必須大於0")

            # 驗證RL配置
            rl_config = self.current_config.get("rl_extension", {})
            threshold = rl_config.get("rl_confidence_threshold", 0.7)
            if not 0.0 <= threshold <= 1.0:
                raise ValueError("rl_confidence_threshold必須在0.0-1.0範圍內")

            self.logger.info("✅ 配置驗證通過")

        except Exception as e:
            self.logger.error(f"❌ 配置驗證失敗: {e}")
            raise

    def _save_configuration(self):
        """保存配置到文件"""
        try:
            # 確保目錄存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as file:
                yaml.dump(self.current_config, file,
                         default_flow_style=False, allow_unicode=True)

            self.logger.info(f"✅ 配置保存成功: {self.config_path}")

        except Exception as e:
            self.logger.error(f"❌ 配置保存失敗: {e}")
            raise

    def get_config(self, section: Optional[str] = None) -> Dict[str, Any]:
        """獲取配置"""
        if section:
            return self.current_config.get(section, {})
        return self.current_config.copy()

    def get_optimization_objectives(self) -> OptimizationObjectives:
        """獲取優化目標配置"""
        obj_dict = self.current_config.get("optimization_objectives", {})
        return OptimizationObjectives(**obj_dict)

    def get_constraints(self) -> Constraints:
        """獲取約束條件配置"""
        const_dict = self.current_config.get("constraints", {})
        return Constraints(**const_dict)

    def get_performance_targets(self) -> PerformanceTargets:
        """獲取性能目標配置"""
        perf_dict = self.current_config.get("performance_monitoring", {}).get("benchmark_targets", {})
        return PerformanceTargets(**perf_dict)

    def get_rl_configuration(self) -> RLConfiguration:
        """獲取RL配置"""
        rl_dict = self.current_config.get("rl_extension", {})
        return RLConfiguration(**rl_dict)

    def update_config(self, section: str, updates: Dict[str, Any],
                     save_immediately: bool = True):
        """更新配置"""
        try:
            # 備份當前配置
            self._backup_configuration()

            # 更新配置
            if section not in self.current_config:
                self.current_config[section] = {}

            self.current_config[section].update(updates)

            # 驗證更新後的配置
            self._validate_configuration()

            # 保存配置
            if save_immediately:
                self._save_configuration()

            # 記錄更新歷史
            self.update_history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "section": section,
                "updates": updates,
                "version": self.config_version
            })

            self.last_updated = datetime.now(timezone.utc)

            self.logger.info(f"✅ 配置更新成功: {section}")

        except Exception as e:
            self.logger.error(f"❌ 配置更新失敗: {e}")
            # 恢復備份
            self._restore_from_backup()
            raise

    def _backup_configuration(self):
        """備份當前配置"""
        try:
            os.makedirs(self.config_backup_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"config_backup_{timestamp}.yaml"
            backup_path = os.path.join(self.config_backup_dir, backup_filename)

            with open(backup_path, 'w', encoding='utf-8') as file:
                yaml.dump(self.current_config, file,
                         default_flow_style=False, allow_unicode=True)

            self.logger.debug(f"📦 配置備份創建: {backup_path}")

        except Exception as e:
            self.logger.error(f"❌ 配置備份失敗: {e}")

    def _restore_from_backup(self):
        """從備份恢復配置"""
        try:
            if not os.path.exists(self.config_backup_dir):
                return

            # 找到最新的備份文件
            backup_files = [f for f in os.listdir(self.config_backup_dir)
                          if f.startswith("config_backup_") and f.endswith(".yaml")]

            if not backup_files:
                return

            latest_backup = sorted(backup_files)[-1]
            backup_path = os.path.join(self.config_backup_dir, latest_backup)

            with open(backup_path, 'r', encoding='utf-8') as file:
                self.current_config = yaml.safe_load(file)

            self.logger.info(f"🔄 配置從備份恢復: {backup_path}")

        except Exception as e:
            self.logger.error(f"❌ 配置恢復失敗: {e}")

    def reset_to_defaults(self):
        """重置為默認配置"""
        self._backup_configuration()
        self.current_config = self.default_config.copy()
        self._save_configuration()

        self.update_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": "reset_to_defaults",
            "version": self.config_version
        })

        self.logger.info("🔄 配置已重置為默認值")

    def get_configuration_info(self) -> Dict[str, Any]:
        """獲取配置信息"""
        return {
            "config_path": self.config_path,
            "config_version": self.config_version,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "total_sections": len(self.current_config),
            "update_count": len(self.update_history),
            "has_backups": os.path.exists(self.config_backup_dir),
            "sections": list(self.current_config.keys())
        }

    def export_configuration(self, export_path: str, format: str = "yaml"):
        """導出配置"""
        try:
            os.makedirs(os.path.dirname(export_path), exist_ok=True)

            if format.lower() == "yaml":
                with open(export_path, 'w', encoding='utf-8') as file:
                    yaml.dump(self.current_config, file,
                             default_flow_style=False, allow_unicode=True)
            elif format.lower() == "json":
                with open(export_path, 'w', encoding='utf-8') as file:
                    json.dump(self.current_config, file, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"不支持的導出格式: {format}")

            self.logger.info(f"✅ 配置導出成功: {export_path}")

        except Exception as e:
            self.logger.error(f"❌ 配置導出失敗: {e}")
            raise

    def import_configuration(self, import_path: str, merge: bool = True):
        """導入配置"""
        try:
            if not os.path.exists(import_path):
                raise FileNotFoundError(f"配置文件不存在: {import_path}")

            # 備份當前配置
            self._backup_configuration()

            with open(import_path, 'r', encoding='utf-8') as file:
                if import_path.endswith('.yaml') or import_path.endswith('.yml'):
                    imported_config = yaml.safe_load(file)
                elif import_path.endswith('.json'):
                    imported_config = json.load(file)
                else:
                    raise ValueError("只支持YAML和JSON格式的配置文件")

            if merge:
                # 合併配置
                self.current_config = self._merge_configurations(
                    self.current_config, imported_config
                )
            else:
                # 替換配置
                self.current_config = imported_config

            # 驗證和保存
            self._validate_configuration()
            self._save_configuration()

            self.update_history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "import_configuration",
                "source": import_path,
                "merge": merge,
                "version": self.config_version
            })

            self.logger.info(f"✅ 配置導入成功: {import_path}")

        except Exception as e:
            self.logger.error(f"❌ 配置導入失敗: {e}")
            # 恢復備份
            self._restore_from_backup()
            raise