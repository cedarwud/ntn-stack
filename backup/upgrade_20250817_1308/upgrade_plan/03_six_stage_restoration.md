# 🔄 Phase 2: 六階段系統恢復計劃

**風險等級**: 🔴 高風險  
**預估時間**: 2小時  
**必要性**: ✅ 核心任務 - 恢復完整的六階段架構，修復93.6%篩選效率

## 🎯 目標

完整恢復原始六階段系統 (階段一→階段六)，修復關鍵的篩選引擎問題，同時保留四階段系統中有價值的技術成果。

## 📋 六階段系統架構回顧

### 原始六階段設計 (基於 docs/overviews/data-processing-flow.md)
```
階段一: TLE載入與SGP4計算     → 8,735顆衛星 (載入)
階段二: 智能衛星篩選         → 563顆衛星 (93.6%篩選率) ⭐ 關鍵修復點
階段三: 信號品質分析與3GPP事件 → 高品質衛星數據
階段四: 時間序列預處理       → 前端動畫數據 ⚠️ 四階段缺失
階段五: 數據整合與接口準備   → PostgreSQL+Volume混合 ⚠️ 四階段缺失  
階段六: 動態池規劃          → 最終衛星池 (可用模擬退火升級)
```

### 核心問題分析
1. **階段二篩選失效**: F2使用 `satellite_filter_engine_v2.py` 而非 `unified_intelligent_filter.py`
2. **階段四缺失**: 時間序列預處理完全缺失，影響前端動畫
3. **階段五缺失**: 數據整合機制缺失，影響PostgreSQL存儲
4. **Pure Cron架構**: 記憶體傳遞機制可能缺失

## 🔧 恢復執行計劃

### Step 1: 驗證原始六階段檔案
**目標**: 確認 `/netstack/src/stages/` 目錄的完整性

```bash
# 檢查六階段處理器是否存在
echo "=== 六階段處理器檢查 ===" > restoration_log.txt
ls -la /home/sat/ntn-stack/netstack/src/stages/ >> restoration_log.txt

# 預期檔案清單
expected_files=(
  "stage1_processor.py"      # TLE載入處理器
  "stage2_processor.py"      # 智能篩選處理器  
  "stage3_processor.py"      # 信號分析處理器
  "stage4_processor.py"      # 時間序列處理器
  "stage5_processor.py"      # 數據整合處理器
  "stage6_processor.py"      # 動態池規劃處理器
)

echo "" >> restoration_log.txt
echo "=== 檔案存在性檢查 ===" >> restoration_log.txt
for file in "${expected_files[@]}"; do
  if [ -f "/home/sat/ntn-stack/netstack/src/stages/$file" ]; then
    echo "✅ $file 存在" >> restoration_log.txt
  else
    echo "❌ $file 缺失" >> restoration_log.txt
  fi
done
```

### Step 2: 檢查備份目錄的原始檔案
**目標**: 從備份恢復缺失的六階段檔案

```bash
# 檢查現有備份
echo "" >> restoration_log.txt
echo "=== 備份目錄檢查 ===" >> restoration_log.txt
ls -la /home/sat/ntn-stack/netstack/src/leo_core.backup.*/ >> restoration_log.txt

# 確認哪個備份包含最原始的六階段系統
backup_dirs=(
  "/home/sat/ntn-stack/netstack/src/leo_core.backup.20250816_014835"
  "/home/sat/ntn-stack/netstack/src/leo_core.backup.20250816_014956"
)

for backup_dir in "${backup_dirs[@]}"; do
  if [ -d "$backup_dir" ]; then
    echo "檢查備份: $backup_dir" >> restoration_log.txt
    find "$backup_dir" -name "*.py" | grep -E "(stage|unified)" >> restoration_log.txt
  fi
done
```

### Step 3: 恢復關鍵的階段二篩選引擎
**目標**: 修復93.6%篩選效率問題

#### 3.1 檢查unified_intelligent_filter的位置
```bash
# 搜索unified_intelligent_filter.py
echo "" >> restoration_log.txt
echo "=== 搜索unified_intelligent_filter ===" >> restoration_log.txt
find /home/sat/ntn-stack -name "*unified_intelligent_filter*" -type f >> restoration_log.txt

# 搜索相關的智能篩選檔案
find /home/sat/ntn-stack -path "*/services/satellite/*" -name "*filter*" -type f >> restoration_log.txt
```

#### 3.2 修復階段二篩選引擎
```bash
# 備份當前錯誤的篩選引擎
backup_timestamp=$(date +%Y%m%d_%H%M%S)
mkdir -p "/home/sat/ntn-stack/backup/stage2_fix_$backup_timestamp"

# 備份F2篩選引擎
cp -r /home/sat/ntn-stack/netstack/src/leo_core/core_system/satellite_filter_engine/ \
   "/home/sat/ntn-stack/backup/stage2_fix_$backup_timestamp/"

# 如果找到unified_intelligent_filter，恢復使用
if [ -f "/home/sat/ntn-stack/netstack/src/services/satellite/intelligent_filtering/unified_intelligent_filter.py" ]; then
  echo "✅ 找到unified_intelligent_filter.py" >> restoration_log.txt
  
  # 修改階段二處理器使用正確的篩選引擎
  # TODO: 具體的修改邏輯需要基於實際檔案結構
else
  echo "❌ 未找到unified_intelligent_filter.py，需要從文檔重建" >> restoration_log.txt
fi
```

### Step 4: 恢復缺失的階段四和五
**目標**: 重建時間序列預處理和數據整合功能

#### 4.1 階段四：時間序列預處理器
```bash
# 檢查是否有階段四的實現
if [ ! -f "/home/sat/ntn-stack/netstack/src/stages/stage4_processor.py" ]; then
  echo "重建階段四：時間序列預處理器" >> restoration_log.txt
  
  # 創建階段四處理器模板
  cat > /home/sat/ntn-stack/netstack/src/stages/stage4_processor.py << 'EOF'
"""
階段四：時間序列預處理器
功能：為前端動畫準備30秒間隔的時間序列數據
"""
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

class Stage4TimeseriesProcessor:
    """時間序列預處理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process(self, stage3_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理階段三輸出，生成時間序列數據
        
        Args:
            stage3_output: 階段三信號分析結果
            
        Returns:
            時間序列預處理結果
        """
        self.logger.info("開始階段四：時間序列預處理")
        
        # TODO: 實現時間序列預處理邏輯
        # 1. 提取衛星軌跡數據
        # 2. 生成30秒間隔的位置點
        # 3. 計算動畫所需的插值數據
        # 4. 準備前端數據格式
        
        result = {
            "stage": 4,
            "description": "時間序列預處理",
            "timeseries_data": {},  # 時間序列數據
            "animation_waypoints": [],  # 動畫關鍵點
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info("階段四處理完成")
        return result

def create_stage4_processor():
    """創建階段四處理器實例"""
    return Stage4TimeseriesProcessor()
EOF
fi
```

#### 4.2 階段五：數據整合處理器
```bash
# 檢查是否有階段五的實現
if [ ! -f "/home/sat/ntn-stack/netstack/src/stages/stage5_processor.py" ]; then
  echo "重建階段五：數據整合處理器" >> restoration_log.txt
  
  # 創建階段五處理器模板
  cat > /home/sat/ntn-stack/netstack/src/stages/stage5_processor.py << 'EOF'
"""
階段五：數據整合與接口準備處理器
功能：整合數據並準備PostgreSQL和Volume存儲
"""
import logging
import json
from typing import Dict, List, Any
from datetime import datetime

class Stage5DataIntegrationProcessor:
    """數據整合處理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process(self, stage4_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        處理階段四輸出，進行數據整合
        
        Args:
            stage4_output: 階段四時間序列結果
            
        Returns:
            數據整合結果
        """
        self.logger.info("開始階段五：數據整合與接口準備")
        
        # TODO: 實現數據整合邏輯
        # 1. 準備PostgreSQL存儲格式
        # 2. 準備Volume JSON數據格式
        # 3. 生成API接口數據
        # 4. 進行數據驗證和完整性檢查
        
        result = {
            "stage": 5,
            "description": "數據整合與接口準備",
            "postgresql_data": {},  # PostgreSQL數據
            "volume_data": {},  # Volume JSON數據
            "api_endpoints": [],  # API端點數據
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info("階段五處理完成")
        return result

def create_stage5_processor():
    """創建階段五處理器實例"""
    return Stage5DataIntegrationProcessor()
EOF
fi
```

### Step 5: 恢復六階段主控制器
**目標**: 修復Pure Cron架構和記憶體傳遞機制

#### 5.1 檢查現有主控制器
```bash
# 檢查現有的主控制器
echo "" >> restoration_log.txt
echo "=== 主控制器檢查 ===" >> restoration_log.txt

# 搜索可能的主控制器檔案
find /home/sat/ntn-stack/netstack/src -name "*pipeline*" -o -name "*main*" -o -name "*controller*" >> restoration_log.txt
```

#### 5.2 創建六階段主控制器
```bash
# 創建六階段主控制器
cat > /home/sat/ntn-stack/netstack/src/stages/six_stage_main_controller.py << 'EOF'
"""
六階段LEO衛星系統主控制器
Pure Cron架構：記憶體傳遞，無文件IO
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
from pathlib import Path

# 導入六階段處理器
from .stage1_processor import create_stage1_processor
from .stage2_processor import create_stage2_processor  
from .stage3_processor import create_stage3_processor
from .stage4_processor import create_stage4_processor
from .stage5_processor import create_stage5_processor
from .stage6_processor import create_stage6_processor

class SixStageMainController:
    """六階段主控制器"""
    
    def __init__(self, output_dir: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.output_dir = Path(output_dir) if output_dir else Path("/tmp/leo_outputs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化各階段處理器
        self.stage1 = create_stage1_processor()
        self.stage2 = create_stage2_processor()
        self.stage3 = create_stage3_processor()
        self.stage4 = create_stage4_processor()
        self.stage5 = create_stage5_processor()
        self.stage6 = create_stage6_processor()
    
    async def execute_full_pipeline(self) -> Dict[str, Any]:
        """
        執行完整的六階段流水線
        Pure Cron架構：記憶體傳遞
        """
        self.logger.info("🚀 開始六階段LEO衛星系統處理")
        
        try:
            # 階段一：TLE載入與SGP4計算
            stage1_result = await self._execute_stage1()
            
            # 階段二：智能衛星篩選 (93.6%篩選率)
            stage2_result = await self._execute_stage2(stage1_result)
            
            # 階段三：信號品質分析與3GPP事件
            stage3_result = await self._execute_stage3(stage2_result)
            
            # 階段四：時間序列預處理
            stage4_result = await self._execute_stage4(stage3_result)
            
            # 階段五：數據整合與接口準備
            stage5_result = await self._execute_stage5(stage4_result)
            
            # 階段六：動態池規劃
            stage6_result = await self._execute_stage6(stage5_result)
            
            # 保存最終結果
            final_result = {
                "pipeline": "six_stage_complete",
                "timestamp": datetime.now().isoformat(),
                "stage1_output": stage1_result,
                "stage2_output": stage2_result,
                "stage3_output": stage3_result,
                "stage4_output": stage4_result,
                "stage5_output": stage5_result,
                "stage6_output": stage6_result
            }
            
            self._save_final_result(final_result)
            
            self.logger.info("✅ 六階段處理完成")
            return final_result
            
        except Exception as e:
            self.logger.error(f"❌ 六階段處理失敗: {e}")
            raise
    
    async def _execute_stage1(self) -> Dict[str, Any]:
        """執行階段一：TLE載入"""
        self.logger.info("執行階段一：TLE載入與SGP4計算")
        return self.stage1.process()
    
    async def _execute_stage2(self, stage1_output: Dict[str, Any]) -> Dict[str, Any]:
        """執行階段二：智能篩選"""
        self.logger.info("執行階段二：智能衛星篩選")
        return self.stage2.process(stage1_output)
    
    async def _execute_stage3(self, stage2_output: Dict[str, Any]) -> Dict[str, Any]:
        """執行階段三：信號分析"""
        self.logger.info("執行階段三：信號品質分析")
        return self.stage3.process(stage2_output)
    
    async def _execute_stage4(self, stage3_output: Dict[str, Any]) -> Dict[str, Any]:
        """執行階段四：時間序列"""
        self.logger.info("執行階段四：時間序列預處理")
        return self.stage4.process(stage3_output)
    
    async def _execute_stage5(self, stage4_output: Dict[str, Any]) -> Dict[str, Any]:
        """執行階段五：數據整合"""
        self.logger.info("執行階段五：數據整合")
        return self.stage5.process(stage4_output)
    
    async def _execute_stage6(self, stage5_output: Dict[str, Any]) -> Dict[str, Any]:
        """執行階段六：動態池規劃"""
        self.logger.info("執行階段六：動態池規劃")
        return self.stage6.process(stage5_output)
    
    def _save_final_result(self, result: Dict[str, Any]) -> None:
        """保存最終結果"""
        output_file = self.output_dir / "six_stage_final_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        self.logger.info(f"結果已保存到: {output_file}")

async def main():
    """主執行函數"""
    controller = SixStageMainController()
    result = await controller.execute_full_pipeline()
    return result

if __name__ == "__main__":
    asyncio.run(main())
EOF
```

### Step 6: 重命名檔案為功能導向
**目標**: 按照CLAUDE.md規範重命名所有檔案

```bash
# 基於Phase 1B的掃描結果進行重命名
echo "" >> restoration_log.txt
echo "=== 檔案重命名 ===" >> restoration_log.txt

# 創建重命名腳本
cat > rename_six_stage_files.sh << 'EOF'
#!/bin/bash
# 六階段檔案重命名腳本

backup_dir="/home/sat/ntn-stack/backup/six_stage_renaming_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"

echo "開始檔案重命名..."

# 重命名六階段處理器
if [ -f "/home/sat/ntn-stack/netstack/src/stages/stage1_processor.py" ]; then
  cp "/home/sat/ntn-stack/netstack/src/stages/stage1_processor.py" "$backup_dir/"
  mv "/home/sat/ntn-stack/netstack/src/stages/stage1_processor.py" \
     "/home/sat/ntn-stack/netstack/src/stages/tle_processing_engine.py"
  echo "✅ stage1_processor.py → tle_processing_engine.py"
fi

if [ -f "/home/sat/ntn-stack/netstack/src/stages/stage2_processor.py" ]; then
  cp "/home/sat/ntn-stack/netstack/src/stages/stage2_processor.py" "$backup_dir/"
  mv "/home/sat/ntn-stack/netstack/src/stages/stage2_processor.py" \
     "/home/sat/ntn-stack/netstack/src/stages/intelligent_filtering_engine.py"
  echo "✅ stage2_processor.py → intelligent_filtering_engine.py"
fi

if [ -f "/home/sat/ntn-stack/netstack/src/stages/stage3_processor.py" ]; then
  cp "/home/sat/ntn-stack/netstack/src/stages/stage3_processor.py" "$backup_dir/"
  mv "/home/sat/ntn-stack/netstack/src/stages/stage3_processor.py" \
     "/home/sat/ntn-stack/netstack/src/stages/signal_analysis_engine.py"
  echo "✅ stage3_processor.py → signal_analysis_engine.py"
fi

if [ -f "/home/sat/ntn-stack/netstack/src/stages/stage4_processor.py" ]; then
  cp "/home/sat/ntn-stack/netstack/src/stages/stage4_processor.py" "$backup_dir/"
  mv "/home/sat/ntn-stack/netstack/src/stages/stage4_processor.py" \
     "/home/sat/ntn-stack/netstack/src/stages/timeseries_processing_engine.py"
  echo "✅ stage4_processor.py → timeseries_processing_engine.py"
fi

if [ -f "/home/sat/ntn-stack/netstack/src/stages/stage5_processor.py" ]; then
  cp "/home/sat/ntn-stack/netstack/src/stages/stage5_processor.py" "$backup_dir/"
  mv "/home/sat/ntn-stack/netstack/src/stages/stage5_processor.py" \
     "/home/sat/ntn-stack/netstack/src/stages/data_integration_engine.py"
  echo "✅ stage5_processor.py → data_integration_engine.py"
fi

if [ -f "/home/sat/ntn-stack/netstack/src/stages/stage6_processor.py" ]; then
  cp "/home/sat/ntn-stack/netstack/src/stages/stage6_processor.py" "$backup_dir/"
  mv "/home/sat/ntn-stack/netstack/src/stages/stage6_processor.py" \
     "/home/sat/ntn-stack/netstack/src/stages/dynamic_pool_planning_engine.py"
  echo "✅ stage6_processor.py → dynamic_pool_planning_engine.py"
fi

echo "檔案重命名完成，備份目錄: $backup_dir"
EOF

chmod +x rename_six_stage_files.sh
```

## ⚠️ 風險控制措施

### 高風險操作識別
1. **篩選引擎替換**: 可能影響整個系統的數據流
2. **主控制器修改**: 可能破壞現有的四階段執行流程
3. **檔案重命名**: 可能造成import錯誤
4. **Pure Cron架構**: 記憶體傳遞機制需要仔細設計

### 安全恢復策略
```bash
# 每個步驟前的安全檢查
safety_check() {
  echo "執行安全檢查..."
  
  # 1. 確認備份完整
  if [ ! -d "/home/sat/ntn-stack/backup" ]; then
    echo "❌ 備份目錄不存在，中止操作"
    exit 1
  fi
  
  # 2. 確認Docker狀態
  if ! make status > /dev/null 2>&1; then
    echo "⚠️ Docker服務異常，建議修復後再繼續"
  fi
  
  # 3. 確認關鍵檔案存在
  if [ ! -f "/home/sat/ntn-stack/netstack/src/leo_core/core_system/main_pipeline.py" ]; then
    echo "❌ 關鍵檔案缺失，中止操作"
    exit 1
  fi
  
  echo "✅ 安全檢查通過"
}
```

## ✅ 恢復驗證檢查清單

### 系統完整性驗證
- [ ] 所有六階段處理器檔案存在
- [ ] unified_intelligent_filter已恢復並正確配置
- [ ] 階段四和五處理器已重建
- [ ] 六階段主控制器已創建
- [ ] 檔案已按功能命名重命名

### 功能驗證
- [ ] 六階段流水線可以完整執行
- [ ] 階段二篩選效率恢復到93.6%
- [ ] 記憶體傳遞機制運作正常
- [ ] 時間序列數據正確生成
- [ ] 數據整合功能正常

### 性能驗證
- [ ] 系統響應時間 < 100ms
- [ ] 篩選從8,735→563顆衛星
- [ ] 前端動畫數據正確生成
- [ ] PostgreSQL存儲正常運作

## 📊 恢復結果記錄

執行完成後記錄：

### 恢復統計
- 恢復的處理器數量: `_______`
- 重建的處理器數量: `_______`
- 重命名的檔案數量: `_______`
- 修復的引用關係: `_______`

### 性能改善
- 篩選效率改善: `從 ___% 到 93.6%`
- 響應時間改善: `從 ___ms 到 ___ms`
- 數據完整性: `___% 完整`

## 🔗 下一步行動

六階段恢復完成並驗證成功後，繼續執行：
→ `04_leo_restructure_integration.md`

---
**🚨 重要警告**: 此階段風險最高，必須確保Phase 0備份完整，且每個步驟都要增量驗證。如出現問題立即停止並回滾！
