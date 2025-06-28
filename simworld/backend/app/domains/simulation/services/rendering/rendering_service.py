"""
渲染引擎服務
負責 3D 場景渲染、圖像處理、GLB 載入等功能
"""

import logging
import os
import numpy as np
from typing import List, Optional
from PIL import Image

# 3D 渲染相關導入
import trimesh
import pyrender

from app.core.config import NYCU_GLB_PATH

logger = logging.getLogger(__name__)

# 場景背景顏色常數
SCENE_BACKGROUND_COLOR_RGB = [0.5, 0.5, 0.5]


class RenderingService:
    """
    渲染引擎服務
    提供 3D 場景渲染、圖像處理等功能
    """

    def __init__(self):
        pass

    def setup_pyrender_scene_from_glb(self) -> Optional[pyrender.Scene]:
        """
        從 GLB 檔案設置 pyrender 場景
        
        Returns:
            Optional[pyrender.Scene]: 設置好的場景，失敗時返回 None
        """
        logger.info(f"Setting up base pyrender scene from GLB: {NYCU_GLB_PATH}")
        
        try:
            # 1. 載入 GLB 檔案
            if not os.path.exists(NYCU_GLB_PATH) or os.path.getsize(NYCU_GLB_PATH) == 0:
                logger.error(f"GLB file not found or empty: {NYCU_GLB_PATH}")
                return None
                
            scene_tm = trimesh.load(NYCU_GLB_PATH, force="scenes")
            logger.info("GLB file loaded.")

            # 2. 創建 pyrender 場景，設置背景和環境光
            pr_scene = pyrender.Scene(
                bg_color=[*SCENE_BACKGROUND_COLOR_RGB, 1.0],
                ambient_light=[0.6, 0.6, 0.6],
            )

            # 3. 添加 GLB 幾何體
            logger.info("Adding GLB geometry...")
            self._add_glb_geometry_to_scene(scene_tm, pr_scene)
            logger.info("GLB geometry added.")

            # 4. 添加燈光
            self._add_lights_to_scene(pr_scene)
            logger.info("Lights added.")

            # 5. 添加相機
            self._add_camera_to_scene(pr_scene)
            logger.info("Camera added.")

            return pr_scene

        except Exception as e:
            logger.error(f"Error setting up pyrender scene from GLB: {e}", exc_info=True)
            return None

    def render_crop_and_save(
        self,
        pr_scene: pyrender.Scene,
        output_path: str,
        bg_color_float: List[float] = None,
        render_width: int = 1200,
        render_height: int = 858,
        padding_y: int = 0,
        padding_x: int = 0,
    ) -> bool:
        """
        渲染場景、裁剪並保存圖像
        
        Args:
            pr_scene: pyrender 場景
            output_path: 輸出路徑
            bg_color_float: 背景顏色
            render_width: 渲染寬度
            render_height: 渲染高度
            padding_y: 垂直邊距
            padding_x: 水平邊距
            
        Returns:
            bool: 渲染是否成功
        """
        if bg_color_float is None:
            bg_color_float = SCENE_BACKGROUND_COLOR_RGB
            
        logger.info("Starting offscreen rendering...")
        
        try:
            # 離屏渲染
            renderer = pyrender.OffscreenRenderer(render_width, render_height)
            color, _ = renderer.render(pr_scene)

            # 安全地釋放 renderer 資源
            try:
                renderer.delete()
            except Exception:
                # 這是已知的 EGL 問題，不影響渲染結果，可以忽略
                pass

            logger.info("Rendering complete.")
            
            # 裁剪圖像
            cropped_image = self._crop_image(
                color, bg_color_float, render_width, render_height, 
                padding_x, padding_y
            )
            
            # 保存圖像
            return self._save_image(cropped_image, output_path)

        except Exception as render_err:
            logger.error(f"Pyrender OffscreenRenderer failed: {render_err}", exc_info=True)
            return False

    def generate_empty_scene_image(self, output_path: str) -> bool:
        """
        生成空場景圖像
        
        Args:
            output_path: 輸出路徑
            
        Returns:
            bool: 生成是否成功
        """
        logger.info(f"Generating empty scene image at {output_path}")
        
        try:
            # 設置 pyrender 場景
            pr_scene = self.setup_pyrender_scene_from_glb()
            if not pr_scene:
                logger.error("無法設置 pyrender 場景")
                return False

            # 渲染並保存場景
            return self.render_crop_and_save(
                pr_scene,
                output_path,
                bg_color_float=SCENE_BACKGROUND_COLOR_RGB,
                render_width=1200,
                render_height=858,
                padding_y=20,
                padding_x=20,
            )

        except Exception as e:
            logger.error(f"生成空場景圖像失敗: {e}", exc_info=True)
            return False

    def _add_glb_geometry_to_scene(self, scene_tm, pr_scene: pyrender.Scene) -> None:
        """添加 GLB 幾何體到場景"""
        for name, geom in scene_tm.geometry.items():
            if geom.vertices is not None and len(geom.vertices) > 0:
                # 處理法線
                if (
                    not hasattr(geom, "vertex_normals")
                    or geom.vertex_normals is None
                    or len(geom.vertex_normals) != len(geom.vertices)
                ):
                    if (
                        hasattr(geom, "faces")
                        and geom.faces is not None
                        and len(geom.faces) > 0
                    ):
                        try:
                            geom.compute_vertex_normals()
                        except Exception as norm_err:
                            logger.error(
                                f"Failed compute normals for '{name}': {norm_err}",
                                exc_info=True,
                            )
                            continue
                    else:
                        logger.warning(f"Mesh '{name}' has no faces. Skipping.")
                        continue
                        
                # 處理材質
                if not hasattr(geom, "visual") or (
                    not hasattr(geom.visual, "vertex_colors")
                    and not hasattr(geom.visual, "material")
                ):
                    geom.visual = trimesh.visual.ColorVisuals(
                        mesh=geom, vertex_colors=[255, 255, 255, 255]
                    )
                    
                # 添加到場景
                try:
                    mesh = pyrender.Mesh.from_trimesh(geom, smooth=False)
                    pr_scene.add(mesh)
                except Exception as mesh_err:
                    logger.error(
                        f"Failed convert mesh '{name}': {mesh_err}", exc_info=True
                    )
            else:
                logger.warning(f"Skipping empty mesh '{name}'.")

    def _add_lights_to_scene(self, pr_scene: pyrender.Scene) -> None:
        """添加燈光到場景"""
        warm_white = np.array([1.0, 0.98, 0.9])
        main_light = pyrender.DirectionalLight(color=warm_white, intensity=3.0)
        pr_scene.add(main_light, pose=np.eye(4))

    def _add_camera_to_scene(self, pr_scene: pyrender.Scene) -> None:
        """添加相機到場景"""
        camera = pyrender.PerspectiveCamera(yfov=np.pi / 4.0, znear=0.1, zfar=10000.0)
        cam_pose = np.array(
            [
                [1.0, 0.0, 0.0, 17.0],
                [0.0, 0.0, 1.0, 940.0],
                [0.0, -1.0, 0.0, -19.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )
        pr_scene.add(camera, pose=cam_pose)

    def _crop_image(
        self, 
        color: np.ndarray, 
        bg_color_float: List[float], 
        render_width: int, 
        render_height: int,
        padding_x: int, 
        padding_y: int
    ) -> np.ndarray:
        """裁剪圖像"""
        logger.info("Calculating bounding box for cropping...")
        image_to_save = color  # 默認使用原始圖像
        
        try:
            bg_color_uint8 = (np.array(bg_color_float) * 255).astype(np.uint8)
            mask = ~np.all(color[:, :, :3] == bg_color_uint8, axis=2)
            rows, cols = np.where(mask)

            if rows.size > 0 and cols.size > 0:
                ymin, ymax = rows.min(), rows.max()
                xmin, xmax = cols.min(), cols.max()
                
                # 應用邊距
                ymin = max(0, ymin - padding_y)
                xmin = max(0, xmin - padding_x)
                ymax = min(render_height - 1, ymax + padding_y)
                xmax = min(render_width - 1, xmax + padding_x)

                if xmin < xmax and ymin < ymax:
                    cropped_color = color[ymin : ymax + 1, xmin : xmax + 1]
                    logger.info(
                        f"Cropping image to bounds: (xmin={xmin}, ymin={ymin}, xmax={xmax}, ymax={ymax})"
                    )
                    image_to_save = cropped_color
                else:
                    logger.warning(f"Invalid crop bounds (min>=max). Saving original.")
            else:
                logger.warning("No non-background pixels found. Saving original image.")

        except Exception as crop_err:
            logger.error(f"Error during image cropping: {crop_err}", exc_info=True)
            # 回退到原始圖像

        return image_to_save

    def _save_image(self, image_data: np.ndarray, output_path: str) -> bool:
        """保存圖像"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        logger.info(f"Saving final image to: {output_path}")
        
        try:
            img = Image.fromarray(image_data)
            img.save(output_path, format="PNG")
            
            # 最終檢查
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(
                    f"Successfully saved image to {output_path}, size: {os.path.getsize(output_path)} bytes"
                )
                return True
            else:
                logger.error(f"Failed to save image or image is empty: {output_path}")
                return False
                
        except Exception as save_err:
            logger.error(f"Failed to save rendered image: {save_err}", exc_info=True)
            return False