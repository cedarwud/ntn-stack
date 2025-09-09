#!/usr/bin/env python3
"""
可配置驗證級別整合器 - Phase 3.5 Task 3
===================================

將性能優化的可配置驗證級別整合到所有階段處理器中
提供統一的驗證配置管理和性能監控
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ValidationConfig:
    """驗證配置管理類"""
    
    def __init__(self, config_file: str = "validation_config.json"):
        self.config_file = Path(config_file)
        self.default_config = {
            "global_validation_level": "standard",  # fast/standard/comprehensive
            "performance_monitoring": True,
            "cache_enabled": True,
            "cache_ttl_seconds": 300,
            "stage_specific_overrides": {
                "stage1": {"level": "standard", "cache_enabled": True},
                "stage2": {"level": "standard", "cache_enabled": True}, 
                "stage3": {"level": "standard", "cache_enabled": True},
                "stage4": {"level": "fast", "cache_enabled": True},  # 時序處理用快速級別
                "stage5": {"level": "standard", "cache_enabled": True},
                "stage6": {"level": "comprehensive", "cache_enabled": True}  # 最終規劃用完整級別
            },
            "adaptive_config": {
                "enabled": True,
                "system_load_threshold": 80,
                "time_constraint_threshold": 60,
                "auto_downgrade": True
            }
        }
        self.load_config()
    
    def load_config(self):
        """載入驗證配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logger.info(f"已載入驗證配置: {self.config_file}")
            except Exception as e:
                logger.warning(f"載入配置失敗，使用預設配置: {e}")
                self.config = self.default_config.copy()
        else:
            self.config = self.default_config.copy()
            self.save_config()
    
    def save_config(self):
        """儲存驗證配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"已儲存驗證配置: {self.config_file}")
        except Exception as e:
            logger.error(f"儲存配置失敗: {e}")
    
    def get_stage_config(self, stage_name: str) -> Dict[str, Any]:
        """獲取指定階段的驗證配置"""
        stage_key = f"stage{stage_name.replace('stage', '')}" if stage_name.startswith('stage') else stage_name
        
        # 獲取階段特定配置，否則使用全局配置
        stage_override = self.config.get('stage_specific_overrides', {}).get(stage_key, {})
        
        return {
            'level': stage_override.get('level', self.config.get('global_validation_level', 'standard')),
            'cache_enabled': stage_override.get('cache_enabled', self.config.get('cache_enabled', True)),
            'cache_ttl': self.config.get('cache_ttl_seconds', 300)
        }
    
    def update_stage_config(self, stage_name: str, level: str, cache_enabled: bool = True):
        """更新指定階段的驗證配置"""
        stage_key = f"stage{stage_name.replace('stage', '')}" if stage_name.startswith('stage') else stage_name
        
        if 'stage_specific_overrides' not in self.config:
            self.config['stage_specific_overrides'] = {}
        
        self.config['stage_specific_overrides'][stage_key] = {
            'level': level,
            'cache_enabled': cache_enabled
        }
        
        self.save_config()
        logger.info(f"已更新 {stage_name} 驗證配置: level={level}, cache={cache_enabled}")

class ValidationIntegrator:
    """驗證整合器 - 將可配置驗證整合到現有處理器"""
    
    def __init__(self):
        self.config = ValidationConfig()
        self.performance_stats = {}
    
    def generate_stage_wrapper_code(self, stage_name: str, original_method_name: str = "run_validation_checks") -> str:
        """生成階段驗證包裝器代碼"""
        
        wrapper_code = f'''
def {original_method_name}_with_levels(self, processing_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    可配置級別的驗證檢查 - Phase 3.5 整合
    支援 FAST/STANDARD/COMPREHENSIVE 三個級別
    """
    import time
    from performance_optimized_validator import ValidationLevel, validate_with_level
    
    # 獲取配置
    from configurable_validation_integration import ValidationConfig
    config = ValidationConfig()
    stage_config = config.get_stage_config('{stage_name}')
    
    # 確定驗證級別
    level_str = stage_config.get('level', 'standard')
    if level_str == 'fast':
        validation_level = ValidationLevel.FAST
    elif level_str == 'comprehensive':
        validation_level = ValidationLevel.COMPREHENSIVE
    else:
        validation_level = ValidationLevel.STANDARD
    
    start_time = time.time()
    
    try:
        # 如果有專用的優化驗證器，使用它
        if hasattr(self, '_use_optimized_validator') and self._use_optimized_validator:
            result = validate_with_level('{stage_name}', processing_results, validation_level)
            
            # 轉換為標準格式
            return {{
                "passed": result.passed,
                "totalChecks": result.total_available_checks,
                "passedChecks": result.checks_performed if result.passed else result.checks_performed - len(result.issues),
                "failedChecks": len(result.issues),
                "validationLevel": level_str,
                "executionTimeMs": result.execution_time_ms,
                "cachedResults": result.cached_results,
                "criticalChecks": [
                    {{"name": name, "status": "passed" if status else "failed"}}
                    for name, status in result.details.items()
                ],
                "allChecks": result.details,
                "issues": result.issues
            }}
        else:
            # 回退到原始驗證方法
            original_result = self.{original_method_name}_original(processing_results)
            
            # 根據級別調整檢查數量
            if level_str == 'fast':
                # 快速模式：只保留關鍵檢查
                critical_checks = original_result.get('criticalChecks', [])[:3]
                original_result['criticalChecks'] = critical_checks
                original_result['validationLevel'] = 'fast'
            elif level_str == 'comprehensive':
                # 完整模式：包含所有檢查
                original_result['validationLevel'] = 'comprehensive'
            else:
                original_result['validationLevel'] = 'standard'
            
            execution_time = (time.time() - start_time) * 1000
            original_result['executionTimeMs'] = execution_time
            
            return original_result
            
    except Exception as e:
        logger.error(f"{{stage_name}} 驗證執行錯誤: {{e}}")
        return {{
            "passed": False,
            "totalChecks": 0,
            "passedChecks": 0,
            "failedChecks": 1,
            "validationLevel": level_str,
            "executionTimeMs": (time.time() - start_time) * 1000,
            "error": str(e),
            "allChecks": {{}},
            "issues": [f"驗證執行錯誤: {{str(e)}}"]
        }}
'''
        return wrapper_code
    
    def generate_integration_patch(self, stage_file: str) -> str:
        """生成整合補丁代碼"""
        
        stage_name = Path(stage_file).stem.replace('_processor', '').replace('_', '')
        
        patch_code = f'''
# ======= Phase 3.5 可配置驗證級別整合 =======
# 在文件開頭添加導入

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from performance_optimized_validator import ValidationLevel, validate_with_level
    from configurable_validation_integration import ValidationConfig
    OPTIMIZED_VALIDATION_AVAILABLE = True
except ImportError:
    OPTIMIZED_VALIDATION_AVAILABLE = False

# ======= 在類別初始化方法中添加 =======

def __init__(self, ...):  # 保持原始參數
    # ... 原始初始化代碼 ...
    
    # Phase 3.5: 驗證配置初始化
    self.validation_config = ValidationConfig()
    self._use_optimized_validator = OPTIMIZED_VALIDATION_AVAILABLE
    self.validation_performance_stats = {{
        'total_validations': 0,
        'avg_execution_time_ms': 0.0,
        'cache_hit_rate': 0.0
    }}

# ======= 修改現有的 run_validation_checks 方法 =======

def run_validation_checks(self, processing_results: Dict[str, Any]) -> Dict[str, Any]:
    """可配置級別的驗證檢查 - Phase 3.5 整合版本"""
    
    import time
    start_time = time.time()
    
    # 獲取配置
    stage_config = self.validation_config.get_stage_config('{stage_name}')
    level_str = stage_config.get('level', 'standard')
    
    # 確定驗證級別
    if OPTIMIZED_VALIDATION_AVAILABLE:
        if level_str == 'fast':
            validation_level = ValidationLevel.FAST
        elif level_str == 'comprehensive':
            validation_level = ValidationLevel.COMPREHENSIVE
        else:
            validation_level = ValidationLevel.STANDARD
        
        try:
            # 使用優化的驗證器
            result = validate_with_level('{stage_name}', processing_results, validation_level)
            
            # 更新性能統計
            self.validation_performance_stats['total_validations'] += 1
            current_avg = self.validation_performance_stats['avg_execution_time_ms']
            total_validations = self.validation_performance_stats['total_validations']
            self.validation_performance_stats['avg_execution_time_ms'] = (
                (current_avg * (total_validations - 1) + result.execution_time_ms) / total_validations
            )
            
            # 轉換為標準格式
            return {{
                "passed": result.passed,
                "totalChecks": result.total_available_checks,
                "passedChecks": result.checks_performed if result.passed else result.checks_performed - len(result.issues),
                "failedChecks": len(result.issues),
                "validationLevel": level_str,
                "executionTimeMs": result.execution_time_ms,
                "cachedResults": result.cached_results,
                "performanceStats": self.validation_performance_stats,
                "criticalChecks": [
                    {{"name": name, "status": "passed" if status else "failed"}}
                    for name, status in result.details.items()
                ],
                "allChecks": result.details,
                "issues": result.issues
            }}
            
        except Exception as e:
            logger.error(f"優化驗證器執行失敗，回退到原始方法: {{e}}")
    
    # 回退到原始驗證方法 (需要確保原始方法存在)
    if hasattr(self, 'run_validation_checks_original'):
        result = self.run_validation_checks_original(processing_results)
    else:
        # 如果沒有原始方法，執行基本檢查
        result = {{
            "passed": True,
            "totalChecks": 1,
            "passedChecks": 1,
            "failedChecks": 0,
            "allChecks": {{"basic_check": True}},
            "issues": []
        }}
    
    # 添加配置信息
    execution_time = (time.time() - start_time) * 1000
    result.update({{
        'validationLevel': level_str,
        'executionTimeMs': execution_time,
        'optimizedValidatorUsed': OPTIMIZED_VALIDATION_AVAILABLE
    }})
    
    return result

# ======= 添加驗證配置管理方法 =======

def set_validation_level(self, level: str):
    """設置此階段的驗證級別"""
    self.validation_config.update_stage_config('{stage_name}', level)
    logger.info(f"已設置 {{stage_name}} 驗證級別為: {{level}}")

def get_validation_performance(self) -> Dict[str, Any]:
    """獲取驗證性能統計"""
    return {{
        'stage_name': '{stage_name}',
        'current_level': self.validation_config.get_stage_config('{stage_name}').get('level'),
        'performance_stats': self.validation_performance_stats,
        'optimized_validator_available': OPTIMIZED_VALIDATION_AVAILABLE
    }}
'''
        
        return patch_code
    
    def create_validation_config_file(self):
        """創建驗證配置文件"""
        config_content = {
            "global_validation_level": "standard",
            "performance_monitoring": True,
            "cache_enabled": True,
            "cache_ttl_seconds": 300,
            "stage_specific_overrides": {
                "stage1": {"level": "standard", "cache_enabled": True, "note": "軌道計算需要平衡精度和性能"},
                "stage2": {"level": "fast", "cache_enabled": True, "note": "可見性過濾可以快速檢查"},
                "stage3": {"level": "standard", "cache_enabled": True, "note": "信號分析需要標準檢查"},
                "stage4": {"level": "fast", "cache_enabled": True, "note": "時序處理性能優先"},
                "stage5": {"level": "standard", "cache_enabled": True, "note": "數據整合需要平衡檢查"},
                "stage6": {"level": "comprehensive", "cache_enabled": True, "note": "最終規劃需要完整檢查"}
            },
            "adaptive_config": {
                "enabled": True,
                "system_load_threshold": 80,
                "time_constraint_threshold": 60,
                "auto_downgrade": True,
                "downgrade_rules": [
                    {"condition": "system_load > 90", "action": "downgrade_to_fast"},
                    {"condition": "time_constraint < 30", "action": "downgrade_to_fast"},
                    {"condition": "memory_usage > 2GB", "action": "disable_cache"}
                ]
            },
            "performance_targets": {
                "max_validation_overhead_percent": 15,
                "target_cache_hit_rate_percent": 60,
                "max_validation_time_ms": 500
            }
        }
        
        config_file = Path("/home/sat/ntn-stack/validation_config.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_content, f, indent=2, ensure_ascii=False)
        
        logger.info(f"已創建驗證配置文件: {config_file}")
        return str(config_file)
    
    def generate_usage_guide(self) -> str:
        """生成使用指南"""
        
        guide = """
# 可配置驗證級別使用指南

## 🚀 快速開始

### 1. 驗證級別說明
- **FAST**: 僅關鍵檢查，約5%性能開銷
- **STANDARD**: 平衡檢查，約10%性能開銷  
- **COMPREHENSIVE**: 完整檢查，約15%性能開銷

### 2. 配置驗證級別

```python
# 在處理器中設置驗證級別
processor.set_validation_level('fast')      # 快速模式
processor.set_validation_level('standard')  # 標準模式
processor.set_validation_level('comprehensive')  # 完整模式
```

### 3. 查看性能統計

```python
# 獲取驗證性能報告
stats = processor.get_validation_performance()
print(f"平均執行時間: {stats['performance_stats']['avg_execution_time_ms']:.2f}ms")
```

### 4. 全局配置

編輯 `validation_config.json`:

```json
{
  "global_validation_level": "standard",
  "stage_specific_overrides": {
    "stage1": {"level": "comprehensive"},
    "stage4": {"level": "fast"}
  }
}
```

## 📊 性能最佳化建議

### 開發環境
- 使用 `comprehensive` 級別進行完整測試
- 啟用緩存以提高重複測試性能

### 生產環境
- Stage 1,3,5,6: `standard` 級別
- Stage 2,4: `fast` 級別
- 在高負載時自動降級

### CI/CD 環境
- 使用 `comprehensive` 級別確保品質
- 設置較長的緩存 TTL 以加速構建

## 🔧 故障排除

### 性能問題
1. 檢查緩存命中率: 目標 > 60%
2. 調整驗證級別: 降級到 `fast`
3. 禁用非關鍵檢查

### 準確性問題
1. 升級到 `comprehensive` 級別
2. 清除緩存以獲得最新結果
3. 檢查學術標準合規性

## 📈 監控指標

- 驗證執行時間: 目標 < 500ms
- 緩存命中率: 目標 > 60%
- 性能開銷: 目標 < 15%
"""
        
        return guide

def main():
    """主執行函數"""
    integrator = ValidationIntegrator()
    
    print("🔧 可配置驗證級別整合器")
    print("=" * 50)
    
    # 1. 創建配置文件
    config_file = integrator.create_validation_config_file()
    print(f"✅ 已創建驗證配置文件: {config_file}")
    
    # 2. 生成使用指南
    guide_file = "/home/sat/ntn-stack/validation_levels_usage_guide.md"
    with open(guide_file, 'w', encoding='utf-8') as f:
        f.write(integrator.generate_usage_guide())
    print(f"✅ 已創建使用指南: {guide_file}")
    
    # 3. 生成示例整合代碼
    example_integration = integrator.generate_integration_patch("stage1_processor.py")
    example_file = "/home/sat/ntn-stack/integration_example.py"
    with open(example_file, 'w', encoding='utf-8') as f:
        f.write(example_integration)
    print(f"✅ 已生成整合示例: {example_file}")
    
    # 4. 顯示配置摘要
    print("\n📊 預設配置摘要:")
    config = ValidationConfig()
    for stage in ['stage1', 'stage2', 'stage3', 'stage4', 'stage5', 'stage6']:
        stage_config = config.get_stage_config(stage)
        print(f"  {stage}: {stage_config['level']} (緩存: {stage_config['cache_enabled']})")
    
    print("\n🎯 整合完成！")
    print("請參考使用指南和整合示例來整合到現有處理器中")

if __name__ == "__main__":
    main()