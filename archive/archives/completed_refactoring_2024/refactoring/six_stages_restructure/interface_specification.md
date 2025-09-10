# 統一階段接口規範

## 🎯 接口設計原則

### 核心原則
1. **統一性**: 所有階段使用相同的基礎接口
2. **可擴展性**: 支援階段特定的自訂方法
3. **可測試性**: 每個方法都可獨立測試
4. **可觀測性**: 統一的日誌、指標和追蹤
5. **容錯性**: 清晰的錯誤處理和回退機制

## 📋 基礎抽象類

### BaseStageProcessor
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timezone
import logging

class BaseStageProcessor(ABC):
    """所有階段處理器的基礎抽象類"""
    
    def __init__(self, stage_number: int, stage_name: str, config: Optional[Dict] = None):
        """
        初始化基礎處理器
        
        Args:
            stage_number: 階段編號 (1-6)
            stage_name: 階段名稱
            config: 配置參數
        """
        self.stage_number = stage_number
        self.stage_name = stage_name
        self.config = config or {}
        
        # 處理時間追蹤
        self.processing_start_time: Optional[datetime] = None
        self.processing_end_time: Optional[datetime] = None
        self.processing_duration: float = 0.0
        
        # 統一日誌
        self.logger = logging.getLogger(f"stage{stage_number}_{stage_name}")
        
        # 輸出目錄
        self.output_dir = Path(f"/app/data/stage{stage_number}_outputs")
        self.validation_dir = Path("/app/data/validation_snapshots")
        
        self._initialize_directories()
        self._load_configuration()
    
    def _initialize_directories(self) -> None:
        """初始化輸出目錄"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.validation_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_configuration(self) -> None:
        """載入配置參數"""
        # 從配置文件或環境變量載入參數
        pass
    
    # ===== 核心處理流程方法 =====
    
    @abstractmethod
    def validate_input(self, input_data: Any) -> bool:
        """
        驗證輸入數據的有效性
        
        Args:
            input_data: 輸入數據
            
        Returns:
            bool: 驗證是否通過
            
        Raises:
            ValidationError: 輸入數據無效
        """
        pass
    
    @abstractmethod
    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        執行階段的核心處理邏輯
        
        Args:
            input_data: 輸入數據
            
        Returns:
            Dict[str, Any]: 處理結果，包含 data 和 metadata
            
        Raises:
            ProcessingError: 處理過程中發生錯誤
        """
        pass
    
    @abstractmethod
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """
        驗證輸出數據的有效性
        
        Args:
            output_data: 輸出數據
            
        Returns:
            bool: 驗證是否通過
            
        Raises:
            ValidationError: 輸出數據無效
        """
        pass
    
    @abstractmethod
    def save_results(self, results: Dict[str, Any]) -> str:
        """
        保存處理結果到文件
        
        Args:
            results: 處理結果
            
        Returns:
            str: 保存的文件路徑
            
        Raises:
            IOError: 文件保存失敗
        """
        pass
    
    # ===== 統一的執行流程 =====
    
    def execute(self, input_data: Any = None) -> Dict[str, Any]:
        """
        執行完整的階段處理流程
        
        Args:
            input_data: 輸入數據
            
        Returns:
            Dict[str, Any]: 處理結果
        """
        self.logger.info(f"開始執行 Stage {self.stage_number}: {self.stage_name}")
        
        try:
            # 1. 開始計時
            self.start_processing_timer()
            
            # 2. 載入輸入數據（如果未提供）
            if input_data is None:
                input_data = self.load_input_data()
            
            # 3. 驗證輸入
            if not self.validate_input(input_data):
                raise ValueError("輸入數據驗證失敗")
            
            # 4. 執行處理
            results = self.process(input_data)
            
            # 5. 驗證輸出
            if not self.validate_output(results):
                raise ValueError("輸出數據驗證失敗")
            
            # 6. 保存結果
            output_path = self.save_results(results)
            results['metadata']['output_file'] = output_path
            
            # 7. 結束計時
            self.end_processing_timer()
            results['metadata']['processing_duration'] = self.processing_duration
            
            # 8. 保存驗證快照
            self.save_validation_snapshot(results)
            
            self.logger.info(f"Stage {self.stage_number} 執行完成，耗時 {self.processing_duration:.2f}秒")
            return results
            
        except Exception as e:
            self.logger.error(f"Stage {self.stage_number} 執行失敗: {e}")
            self.end_processing_timer()
            raise
    
    # ===== 時間管理 =====
    
    def start_processing_timer(self) -> None:
        """開始處理計時"""
        self.processing_start_time = datetime.now(timezone.utc)
    
    def end_processing_timer(self) -> None:
        """結束處理計時"""
        self.processing_end_time = datetime.now(timezone.utc)
        if self.processing_start_time:
            self.processing_duration = (
                self.processing_end_time - self.processing_start_time
            ).total_seconds()
    
    # ===== 數據載入和保存 =====
    
    def load_input_data(self) -> Any:
        """
        載入輸入數據（從前一階段的輸出）
        
        Returns:
            Any: 輸入數據
        """
        if self.stage_number == 1:
            # Stage 1 沒有前置依賴，直接載入原始數據
            return None
        
        # 其他階段從前一階段載入數據
        prev_stage_output = self.output_dir.parent / f"stage{self.stage_number-1}_outputs"
        # 實施載入邏輯
        pass
    
    def save_validation_snapshot(self, results: Dict[str, Any]) -> bool:
        """
        保存驗證快照
        
        Args:
            results: 處理結果
            
        Returns:
            bool: 保存是否成功
        """
        try:
            snapshot = {
                "stage": self.stage_number,
                "stageName": self.stage_name,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "completed",
                "duration_seconds": round(self.processing_duration, 2),
                "keyMetrics": self.extract_key_metrics(results),
                "validation": self.run_validation_checks(results),
                "systemInfo": {
                    "processor_version": "2.0.0",
                    "validation_framework": "unified_pipeline_v2"
                }
            }
            
            snapshot_file = self.validation_dir / f"stage{self.stage_number}_validation.json"
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(snapshot, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"驗證快照已保存: {snapshot_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存驗證快照失敗: {e}")
            return False
    
    # ===== 抽象方法 - 子類必須實施 =====
    
    @abstractmethod
    def extract_key_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取關鍵指標
        
        Args:
            results: 處理結果
            
        Returns:
            Dict[str, Any]: 關鍵指標
        """
        pass
    
    @abstractmethod
    def run_validation_checks(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        執行驗證檢查
        
        Args:
            results: 處理結果
            
        Returns:
            Dict[str, Any]: 驗證結果
        """
        pass
    
    # ===== 可選覆寫方法 =====
    
    def cleanup_previous_output(self) -> None:
        """清理之前的輸出文件"""
        if self.output_dir.exists():
            for file in self.output_dir.glob("*"):
                if file.is_file():
                    file.unlink()
                    self.logger.info(f"已清理舊文件: {file}")
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        獲取處理統計信息
        
        Returns:
            Dict[str, Any]: 統計信息
        """
        return {
            "stage_number": self.stage_number,
            "stage_name": self.stage_name,
            "processing_duration": self.processing_duration,
            "start_time": self.processing_start_time.isoformat() if self.processing_start_time else None,
            "end_time": self.processing_end_time.isoformat() if self.processing_end_time else None,
        }
```

## 📊 標準化數據格式

### 輸入數據格式
```python
StandardInputFormat = {
    "data": Any,  # 實際數據內容
    "metadata": {
        "source_stage": int,
        "processing_timestamp": str,
        "data_format_version": str,
        "total_records": int,
        "data_lineage": Dict[str, Any]
    }
}
```

### 輸出數據格式
```python
StandardOutputFormat = {
    "data": Any,  # 處理後的數據
    "metadata": {
        "stage_number": int,
        "stage_name": str,
        "processing_timestamp": str,
        "processing_duration": float,
        "data_format_version": str,
        "total_records": int,
        "output_file": str,
        "data_lineage": Dict[str, Any],
        "academic_compliance": Dict[str, Any]
    }
}
```

### 驗證結果格式
```python
ValidationResultFormat = {
    "passed": bool,
    "totalChecks": int,
    "passedChecks": int,
    "failedChecks": int,
    "criticalChecks": List[Dict[str, str]],
    "allChecks": Dict[str, bool],
    "validation_level_info": Dict[str, Any]
}
```

## 🛠️ 階段特定接口

### Stage1Interface (軌道計算)
```python
class Stage1Interface(BaseStageProcessor):
    """Stage 1 特定接口"""
    
    @abstractmethod
    def scan_tle_data(self) -> Dict[str, Any]:
        """掃描 TLE 數據文件"""
        pass
    
    @abstractmethod
    def load_satellite_data(self, scan_result: Dict) -> List[Dict]:
        """載入衛星數據"""
        pass
    
    @abstractmethod
    def calculate_orbits(self, satellite_data: List) -> Dict[str, Any]:
        """計算軌道"""
        pass
```

### Stage2Interface (可見性過濾)
```python
class Stage2Interface(BaseStageProcessor):
    """Stage 2 特定接口"""
    
    @abstractmethod
    def apply_elevation_filter(self, orbital_data: Dict) -> Dict[str, Any]:
        """應用仰角過濾"""
        pass
    
    @abstractmethod
    def calculate_visibility_windows(self, filtered_data: Dict) -> Dict[str, Any]:
        """計算可見性時間窗口"""
        pass
```

## 📝 使用範例

### 實施 Stage 1 處理器
```python
from pipeline.shared.base_processor import BaseStageProcessor
from pipeline.stages.stage1_orbital_calculation.tle_data_loader import TLEDataLoader
from pipeline.stages.stage1_orbital_calculation.orbital_calculator import OrbitalCalculator

class Stage1Processor(BaseStageProcessor):
    """階段一：軌道計算處理器"""
    
    def __init__(self):
        super().__init__(stage_number=1, stage_name="orbital_calculation")
        self.tle_loader = TLEDataLoader()
        self.orbital_calculator = OrbitalCalculator()
    
    def validate_input(self, input_data: Any) -> bool:
        # TLE 數據驗證邏輯
        return True
    
    def process(self, input_data: Any) -> Dict[str, Any]:
        # 1. 掃描 TLE 數據
        scan_result = self.tle_loader.scan_tle_data()
        
        # 2. 載入衛星數據
        satellite_data = self.tle_loader.load_satellite_data(scan_result)
        
        # 3. 計算軌道
        orbital_data = self.orbital_calculator.calculate_orbits(satellite_data)
        
        return {
            "data": orbital_data,
            "metadata": {
                "stage_number": 1,
                "stage_name": "orbital_calculation",
                "total_satellites": len(satellite_data),
                "processing_timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        # 輸出驗證邏輯
        return True
    
    def save_results(self, results: Dict[str, Any]) -> str:
        output_file = self.output_dir / "orbital_calculation_output.json"
        with open(output_file, 'w') as f:
            json.dump(results, f)
        return str(output_file)
    
    def extract_key_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "total_satellites": results["metadata"]["total_satellites"],
            "processing_time": self.processing_duration
        }
    
    def run_validation_checks(self, results: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "passed": True,
            "totalChecks": 5,
            "passedChecks": 5,
            "failedChecks": 0
        }

# 使用範例
processor = Stage1Processor()
results = processor.execute()
```

## 🔧 配置管理

### 階段配置文件範例 (config.py)
```python
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Stage1Config:
    """Stage 1 配置參數"""
    
    # TLE 數據配置
    tle_data_path: str = "/app/tle_data"
    sample_mode: bool = False
    sample_size: int = 100
    
    # SGP4 計算配置
    time_points_per_orbit: int = 192
    calculation_precision: float = 1e-10
    
    # 輸出配置
    output_format: str = "unified_v1.2"
    compress_output: bool = False
    
    # 驗證配置
    validation_level: str = "STANDARD"  # FAST, STANDARD, COMPREHENSIVE
    enable_academic_compliance: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "tle_data_path": self.tle_data_path,
            "sample_mode": self.sample_mode,
            "sample_size": self.sample_size,
            "time_points_per_orbit": self.time_points_per_orbit,
            "calculation_precision": self.calculation_precision,
            "output_format": self.output_format,
            "compress_output": self.compress_output,
            "validation_level": self.validation_level,
            "enable_academic_compliance": self.enable_academic_compliance
        }
```

## 📋 接口實施檢查清單

### 基礎要求 ✅
- [ ] 繼承 `BaseStageProcessor`
- [ ] 實施所有抽象方法
- [ ] 使用標準化數據格式
- [ ] 統一的錯誤處理
- [ ] 完整的日誌記錄

### 進階要求 ✅
- [ ] 配置文件支援
- [ ] 單元測試覆蓋率 >90%
- [ ] 性能基準測試
- [ ] 文檔完整
- [ ] 型別提示完整

### 品質要求 ✅
- [ ] 代碼風格一致
- [ ] 無安全漏洞
- [ ] 記憶體使用合理
- [ ] 並發安全（如適用）
- [ ] 向後兼容

---

**重要**: 這個接口規範是整個重構項目的核心，所有階段處理器都必須遵循這個標準。