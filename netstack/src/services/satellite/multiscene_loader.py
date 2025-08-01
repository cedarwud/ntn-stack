"""
多場景資料載入器
支援動態載入不同地理位置的衛星資料和配置
"""
import csv
import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass
import pandas as pd

logger = logging.getLogger(__name__)

@dataclass
class SceneConfig:
    """場景配置資料結構"""
    scene_id: str
    scene_name: str
    latitude: float
    longitude: float
    altitude: float
    scene_type: str
    pre_handover_threshold: float
    execution_threshold: float
    critical_threshold: float
    environment_factor: float

class MultiSceneLoader:
    """多場景資料載入器"""
    
    def __init__(self, data_dir: str = "/app/data"):
        self.data_dir = Path(data_dir)
        self.scenes_file = self.data_dir / "scenes.csv"
        self.scenes_data_dir = self.data_dir / "scenes"
        self._scenes_cache: Dict[str, SceneConfig] = {}
        self._active_scene: Optional[str] = None
        self._load_scenes_config()
        
    def _load_scenes_config(self):
        """載入場景配置表"""
        if not self.scenes_file.exists():
            logger.warning(f"場景配置文件不存在: {self.scenes_file}")
            return
            
        try:
            with open(self.scenes_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    scene = SceneConfig(
                        scene_id=row['scene_id'],
                        scene_name=row['scene_name'],
                        latitude=float(row['latitude']),
                        longitude=float(row['longitude']),
                        altitude=float(row['altitude']),
                        scene_type=row['scene_type'],
                        pre_handover_threshold=float(row['pre_handover_threshold']),
                        execution_threshold=float(row['execution_threshold']),
                        critical_threshold=float(row['critical_threshold']),
                        environment_factor=float(row['environment_factor'])
                    )
                    self._scenes_cache[scene.scene_id] = scene
                    
            logger.info(f"載入 {len(self._scenes_cache)} 個場景配置")
            
        except Exception as e:
            logger.error(f"載入場景配置失敗: {e}")
            
    def get_available_scenes(self) -> Dict[str, SceneConfig]:
        """獲取所有可用場景"""
        return self._scenes_cache.copy()
        
    def get_scene_config(self, scene_id: str) -> Optional[SceneConfig]:
        """獲取特定場景配置"""
        return self._scenes_cache.get(scene_id)
        
    def load_scene_data(self, scene_id: str) -> Dict[str, Any]:
        """載入場景特定資料"""
        if scene_id not in self._scenes_cache:
            raise ValueError(f"未知的場景 ID: {scene_id}")
            
        scene_dir = self.scenes_data_dir / scene_id
        
        # 檢查場景資料目錄是否存在
        if not scene_dir.exists():
            logger.warning(f"場景資料目錄不存在: {scene_dir}")
            # 返回基本配置，等待資料生成
            return {
                "config": self._scenes_cache[scene_id],
                "visibility_data": None,
                "handover_events": None,
                "status": "pending_generation"
            }
            
        result = {
            "config": self._scenes_cache[scene_id],
            "status": "loaded"
        }
        
        # 載入可見性索引
        visibility_file = scene_dir / "visibility_index.parquet"
        if visibility_file.exists():
            try:
                result["visibility_data"] = pd.read_parquet(visibility_file)
            except Exception as e:
                logger.error(f"載入可見性資料失敗: {e}")
                result["visibility_data"] = None
                
        # 載入換手事件
        handover_file = scene_dir / "handover_events.parquet"
        if handover_file.exists():
            try:
                result["handover_events"] = pd.read_parquet(handover_file)
            except Exception as e:
                logger.error(f"載入換手事件資料失敗: {e}")
                result["handover_events"] = None
                
        # 載入仰角配置
        elevation_file = scene_dir / "elevation_config.json"
        if elevation_file.exists():
            try:
                with open(elevation_file, 'r') as f:
                    result["elevation_config"] = json.load(f)
            except Exception as e:
                logger.error(f"載入仰角配置失敗: {e}")
                
        self._active_scene = scene_id
        logger.info(f"成功載入場景: {scene_id}")
        
        return result
        
    def get_active_scene(self) -> Optional[str]:
        """獲取當前活動場景"""
        return self._active_scene
        
    def switch_scene(self, scene_id: str) -> Dict[str, Any]:
        """切換到新場景"""
        logger.info(f"切換場景: {self._active_scene} -> {scene_id}")
        return self.load_scene_data(scene_id)
        
    def get_observer_location(self, scene_id: Optional[str] = None) -> Dict[str, float]:
        """獲取觀測點位置"""
        if scene_id is None:
            scene_id = self._active_scene
            
        if scene_id is None:
            raise ValueError("未指定場景且無活動場景")
            
        scene = self._scenes_cache.get(scene_id)
        if not scene:
            raise ValueError(f"未知的場景 ID: {scene_id}")
            
        return {
            "lat": scene.latitude,
            "lon": scene.longitude,
            "alt": scene.altitude
        }
        
    def get_elevation_thresholds(self, scene_id: Optional[str] = None) -> Dict[str, float]:
        """獲取場景的仰角門檻"""
        if scene_id is None:
            scene_id = self._active_scene
            
        if scene_id is None:
            raise ValueError("未指定場景且無活動場景")
            
        scene = self._scenes_cache.get(scene_id)
        if not scene:
            raise ValueError(f"未知的場景 ID: {scene_id}")
            
        return {
            "pre_handover": scene.pre_handover_threshold,
            "execution": scene.execution_threshold,
            "critical": scene.critical_threshold
        }

# 全域實例
multi_scene_loader = MultiSceneLoader()

# 匯出便利函式
def load_scene(scene_id: str) -> Dict[str, Any]:
    """載入場景的便利函式"""
    return multi_scene_loader.load_scene_data(scene_id)

def get_scenes() -> Dict[str, SceneConfig]:
    """獲取所有場景的便利函式"""
    return multi_scene_loader.get_available_scenes()