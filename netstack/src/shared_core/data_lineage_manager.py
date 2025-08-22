"""
數據血統追蹤管理器 - v3.1
統一管理六階段處理的數據血統信息，確保數據來源可追蹤性
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
import json
import logging

logger = logging.getLogger(__name__)

@dataclass
class DataSource:
    """數據來源描述"""
    source_type: str  # 'tle_file', 'computed', 'cached', 'external_api'
    source_path: str
    source_date: str  # 實際數據日期 (YYYYMMDD格式)
    file_size_bytes: Optional[int] = None
    modification_time: Optional[str] = None
    checksum: Optional[str] = None

@dataclass
class ProcessingRecord:
    """處理記錄"""
    stage_name: str
    processing_timestamp: str
    processing_duration_seconds: float
    input_data_sources: List[DataSource]
    output_path: Optional[str] = None
    processor_version: str = "3.1"
    configuration: Optional[Dict[str, Any]] = None

@dataclass
class DataLineage:
    """完整數據血統記錄"""
    lineage_id: str
    creation_timestamp: str
    project_name: str = "ntn-stack"
    data_category: str = "satellite_orbital_data"
    processing_chain: List[ProcessingRecord] = None
    
    def __post_init__(self):
        if self.processing_chain is None:
            self.processing_chain = []

class DataLineageManager:
    """數據血統追蹤管理器"""
    
    def __init__(self, project_name: str = "ntn-stack", lineage_storage_dir: str = "/app/data/.lineage"):
        self.project_name = project_name
        self.lineage_storage_dir = Path(lineage_storage_dir)
        self.lineage_storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 當前數據血統記錄
        self.current_lineage: Optional[DataLineage] = None
        
        logger.info(f"✅ 數據血統管理器初始化完成: {self.lineage_storage_dir}")
    
    def start_new_lineage(self, data_category: str = "satellite_orbital_data") -> str:
        """開始新的數據血統追蹤"""
        lineage_id = f"{self.project_name}_{data_category}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        
        self.current_lineage = DataLineage(
            lineage_id=lineage_id,
            creation_timestamp=datetime.now(timezone.utc).isoformat(),
            project_name=self.project_name,
            data_category=data_category,
            processing_chain=[]
        )
        
        logger.info(f"🎯 開始新的數據血統追蹤: {lineage_id}")
        return lineage_id
    
    def create_data_source(
        self, 
        source_type: str, 
        source_path: str, 
        source_date: str,
        file_size_bytes: Optional[int] = None
    ) -> DataSource:
        """創建數據來源記錄"""
        
        # 獲取文件修改時間（如果是文件路徑）
        modification_time = None
        if Path(source_path).exists():
            modification_time = datetime.fromtimestamp(
                Path(source_path).stat().st_mtime, 
                timezone.utc
            ).isoformat()
            
            if file_size_bytes is None:
                file_size_bytes = Path(source_path).stat().st_size
        
        return DataSource(
            source_type=source_type,
            source_path=source_path,
            source_date=source_date,
            file_size_bytes=file_size_bytes,
            modification_time=modification_time
        )
    
    def record_processing_stage(
        self,
        stage_name: str,
        input_data_sources: List[DataSource],
        processing_start_time: datetime,
        output_path: Optional[str] = None,
        configuration: Optional[Dict[str, Any]] = None
    ) -> ProcessingRecord:
        """記錄處理階段信息"""
        
        if self.current_lineage is None:
            raise RuntimeError("必須先調用 start_new_lineage() 開始數據血統追蹤")
        
        processing_end_time = datetime.now(timezone.utc)
        processing_duration = (processing_end_time - processing_start_time).total_seconds()
        
        record = ProcessingRecord(
            stage_name=stage_name,
            processing_timestamp=processing_end_time.isoformat(),
            processing_duration_seconds=processing_duration,
            input_data_sources=input_data_sources,
            output_path=output_path,
            configuration=configuration
        )
        
        # 添加到當前血統記錄中
        self.current_lineage.processing_chain.append(record)
        
        logger.info(f"📊 記錄處理階段: {stage_name} (耗時: {processing_duration:.2f}秒)")
        
        return record
    
    def save_lineage(self, stage_name: Optional[str] = None) -> str:
        """保存數據血統記錄到文件"""
        
        if self.current_lineage is None:
            raise RuntimeError("沒有可保存的數據血統記錄")
        
        # 生成文件名
        if stage_name:
            filename = f"{self.current_lineage.lineage_id}_{stage_name}.json"
        else:
            filename = f"{self.current_lineage.lineage_id}_complete.json"
        
        lineage_file = self.lineage_storage_dir / filename
        
        # 轉換為字典並保存
        lineage_data = asdict(self.current_lineage)
        
        with open(lineage_file, 'w', encoding='utf-8') as f:
            json.dump(lineage_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 數據血統記錄已保存: {lineage_file}")
        
        return str(lineage_file)
    
    def load_lineage(self, lineage_id: str) -> Optional[DataLineage]:
        """載入指定的數據血統記錄"""
        
        # 搜索匹配的血統文件
        lineage_files = list(self.lineage_storage_dir.glob(f"{lineage_id}*.json"))
        
        if not lineage_files:
            logger.warning(f"未找到數據血統記錄: {lineage_id}")
            return None
        
        # 使用最新的文件
        lineage_file = max(lineage_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(lineage_file, 'r', encoding='utf-8') as f:
                lineage_data = json.load(f)
            
            # 重建對象結構
            processing_chain = []
            for record_data in lineage_data.get('processing_chain', []):
                input_sources = [DataSource(**src) for src in record_data['input_data_sources']]
                record_data['input_data_sources'] = input_sources
                processing_chain.append(ProcessingRecord(**record_data))
            
            lineage_data['processing_chain'] = processing_chain
            
            lineage = DataLineage(**lineage_data)
            
            logger.info(f"📖 載入數據血統記錄: {lineage_id} ({len(lineage.processing_chain)} 個階段)")
            
            return lineage
            
        except Exception as e:
            logger.error(f"載入數據血統記錄失敗: {e}")
            return None
    
    def get_lineage_summary(self) -> Dict[str, Any]:
        """獲取當前數據血統摘要"""
        
        if self.current_lineage is None:
            return {"status": "no_active_lineage"}
        
        # 計算總處理時間
        total_duration = sum(
            record.processing_duration_seconds 
            for record in self.current_lineage.processing_chain
        )
        
        # 統計數據來源
        all_sources = []
        for record in self.current_lineage.processing_chain:
            all_sources.extend(record.input_data_sources)
        
        source_summary = {}
        for source in all_sources:
            if source.source_date not in source_summary:
                source_summary[source.source_date] = []
            source_summary[source.source_date].append(source.source_type)
        
        return {
            "lineage_id": self.current_lineage.lineage_id,
            "creation_timestamp": self.current_lineage.creation_timestamp,
            "stages_completed": len(self.current_lineage.processing_chain),
            "total_processing_duration_seconds": total_duration,
            "data_sources_by_date": source_summary,
            "latest_stage": (
                self.current_lineage.processing_chain[-1].stage_name 
                if self.current_lineage.processing_chain 
                else None
            )
        }
    
    def validate_data_freshness(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """驗證數據新鮮度"""
        
        if self.current_lineage is None:
            return {"status": "no_active_lineage"}
        
        current_time = datetime.now(timezone.utc)
        creation_time = datetime.fromisoformat(self.current_lineage.creation_timestamp.replace('Z', '+00:00'))
        
        age_hours = (current_time - creation_time).total_seconds() / 3600
        
        is_fresh = age_hours <= max_age_hours
        
        # 檢查數據來源日期一致性
        source_dates = set()
        for record in self.current_lineage.processing_chain:
            for source in record.input_data_sources:
                source_dates.add(source.source_date)
        
        return {
            "is_fresh": is_fresh,
            "age_hours": age_hours,
            "max_age_hours": max_age_hours,
            "unique_source_dates": list(source_dates),
            "date_consistency": len(source_dates) <= 1  # 所有來源應該是同一天的數據
        }

# 全局實例
_lineage_manager = None

def get_lineage_manager() -> DataLineageManager:
    """獲取全局數據血統管理器實例"""
    global _lineage_manager
    if _lineage_manager is None:
        _lineage_manager = DataLineageManager()
    return _lineage_manager

def create_tle_data_source(tle_file_path: str, tle_date: str) -> DataSource:
    """便利函數：創建TLE數據來源記錄"""
    return get_lineage_manager().create_data_source(
        source_type="tle_file",
        source_path=tle_file_path,
        source_date=tle_date
    )

def record_stage_processing(
    stage_name: str, 
    input_sources: List[DataSource],
    start_time: datetime,
    output_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> ProcessingRecord:
    """便利函數：記錄階段處理"""
    return get_lineage_manager().record_processing_stage(
        stage_name=stage_name,
        input_data_sources=input_sources,
        processing_start_time=start_time,
        output_path=output_path,
        configuration=config
    )