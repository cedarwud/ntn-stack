"""
場景管理服務
負責場景健康度檢查、XML 路徑獲取、檔案準備等功能
"""

import logging
import os
from typing import Optional

from app.core.config import get_scene_xml_path

logger = logging.getLogger(__name__)


class SceneManagementService:
    """
    場景管理服務
    提供場景健康度檢查、檔案管理等功能
    """

    def __init__(self):
        pass

    def check_scene_health(self, scene_name: str, xml_path: str) -> bool:
        """
        檢查場景的健康度，包括 XML 格式和幾何數據完整性
        返回 True 表示健康，False 表示需要回退
        
        Args:
            scene_name: 場景名稱
            xml_path: XML 檔案路徑
            
        Returns:
            bool: 場景是否健康
        """
        try:
            # 檢查 1: XML 文件是否存在
            if not os.path.exists(xml_path):
                logger.warning(f"場景 {scene_name} 的 XML 文件不存在: {xml_path}")
                return False

            # 檢查 2: XML 格式問題 - NTPU 和 Nanliao 有已知問題
            problematic_scenes = ["NTPU", "Nanliao", "NTPU"]
            
            if scene_name in problematic_scenes:
                if scene_name in ["NTPU", "NTPU"]:
                    logger.warning(
                        f"⚠️  注意：{scene_name} 場景的 XML 文件不相容於 Sionna "
                        f"（HolderMaterial 配置錯誤：只允許一個嵌套radio material），"
                        f"自動回退到 NYCU 場景。"
                    )
                else:  # Nanliao
                    logger.warning(
                        f"⚠️  注意：{scene_name} 場景的 XML 文件格式不相容於 Sionna "
                        f"（shape 元素缺少 id 屬性），自動回退到 NYCU 場景。"
                    )
                return False

            # 檢查 3: 幾何數據完整性 - 檢查 PLY 文件大小
            if scene_name == "Lotus":
                scene_dir = os.path.dirname(xml_path)
                meshes_dir = os.path.join(scene_dir, "meshes")

                if os.path.exists(meshes_dir):
                    ply_files = [f for f in os.listdir(meshes_dir) if f.endswith(".ply")]
                    total_size = 0
                    small_files = 0

                    for ply_file in ply_files:
                        ply_path = os.path.join(meshes_dir, ply_file)
                        if os.path.exists(ply_path):
                            size = os.path.getsize(ply_path)
                            total_size += size
                            if size < 2000:  # 小於 2KB 的文件視為不完整
                                small_files += 1

                    # 如果總大小太小或太多小文件，視為不健康
                    if total_size < 30000 or small_files > len(ply_files) * 0.8:
                        logger.warning(
                            f"⚠️  注意：{scene_name} 場景的 PLY 幾何數據不完整 "
                            f"（總大小: {total_size} bytes, 小文件數: {small_files}/{len(ply_files)}），"
                            f"自動回退到 NYCU 場景。"
                        )
                        return False

            logger.info(f"✅ 場景 {scene_name} 健康度檢查通過")
            return True

        except Exception as e:
            logger.error(f"檢查場景 {scene_name} 健康度時發生錯誤: {e}")
            return False

    def get_scene_xml_file_path(self, scene_name: str = "nycu") -> str:
        """
        獲取場景 XML 檔案路徑，包含健康度檢查和回退機制
        
        Args:
            scene_name: 場景名稱
            
        Returns:
            str: XML 檔案路徑
        """
        logger.info(f"獲取場景 '{scene_name}' 的 XML 檔案路徑")

        try:
            # 先嘗試獲取指定場景的路徑
            xml_path = get_scene_xml_path(scene_name)

            # 從路徑中提取實際的場景目錄名稱進行健康檢查
            import os
            actual_scene_name = os.path.basename(os.path.dirname(xml_path))
            
            # 檢查場景健康度
            if self.check_scene_health(actual_scene_name, xml_path):
                logger.info(f"✅ 使用場景: {scene_name}, 路徑: {xml_path}")
                return xml_path
            else:
                # 回退到默認的 NYCU 場景
                fallback_scene = "nycu"
                logger.warning(f"⚠️  回退到默認場景: {fallback_scene}")
                fallback_xml_path = get_scene_xml_path(fallback_scene)

                # 再次檢查回退場景的健康度
                fallback_actual_scene_name = os.path.basename(os.path.dirname(fallback_xml_path))
                if self.check_scene_health(fallback_actual_scene_name, fallback_xml_path):
                    logger.info(f"✅ 使用回退場景: {fallback_scene}, 路徑: {fallback_xml_path}")
                    return fallback_xml_path
                else:
                    # 如果回退場景也不健康，發出警告但仍返回路徑
                    logger.error(
                        f"❌ 連回退場景 {fallback_scene} 也不健康，但仍嘗試使用"
                    )
                    return fallback_xml_path

        except Exception as e:
            logger.error(f"獲取場景 XML 檔案路徑時發生錯誤: {e}")
            # 發生錯誤時，嘗試回退到 NYCU
            try:
                fallback_xml_path = get_scene_xml_path("nycu")
                logger.warning(f"⚠️  錯誤回退到 NYCU 場景: {fallback_xml_path}")
                return fallback_xml_path
            except Exception as fallback_error:
                logger.error(f"❌ 連回退操作都失敗: {fallback_error}")
                raise

    def prepare_output_file(self, output_path: str, file_desc: str = "檔案") -> bool:
        """
        清理舊文件並準備目錄結構
        
        Args:
            output_path: 輸出檔案路徑
            file_desc: 檔案描述
            
        Returns:
            bool: 準備是否成功
        """
        try:
            # 清理舊文件
            self._clean_output_file(output_path, file_desc)
            
            # 確保輸出目錄存在
            self._ensure_output_dir(output_path)
            
            return True
            
        except Exception as e:
            logger.error(f"準備輸出檔案失敗 {output_path}: {e}")
            return False

    def verify_output_file(self, output_path: str, min_size: int = 1000) -> bool:
        """
        驗證輸出檔案是否成功生成
        
        Args:
            output_path: 輸出檔案路徑
            min_size: 最小檔案大小（bytes）
            
        Returns:
            bool: 檔案是否有效
        """
        try:
            if not os.path.exists(output_path):
                logger.error(f"輸出檔案不存在: {output_path}")
                return False

            file_size = os.path.getsize(output_path)
            if file_size < min_size:
                logger.error(f"輸出檔案太小: {output_path} ({file_size} bytes)")
                return False

            logger.info(f"✅ 輸出檔案驗證成功: {output_path} ({file_size} bytes)")
            return True

        except Exception as e:
            logger.error(f"驗證輸出檔案失敗 {output_path}: {e}")
            return False

    def _clean_output_file(self, output_path: str, file_desc: str) -> None:
        """清理舊的輸出檔案"""
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
                logger.info(f"已清理舊的{file_desc}: {output_path}")
        except Exception as e:
            logger.warning(f"清理舊{file_desc}失敗: {e}")

    def _ensure_output_dir(self, output_path: str) -> None:
        """確保輸出目錄存在"""
        try:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"已創建輸出目錄: {output_dir}")
        except Exception as e:
            logger.error(f"創建輸出目錄失敗: {e}")
            raise