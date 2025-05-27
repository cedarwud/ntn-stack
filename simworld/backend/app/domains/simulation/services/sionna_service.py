# backend/app/services/sionna_simulation.py
import logging
import os
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field as PydanticField  # Use Pydantic BaseModel
from sionna.rt import (
    load_scene,
    Transmitter as SionnaTransmitter,
    Receiver as SionnaReceiver,
    PlanarArray,
    PathSolver,
    subcarrier_frequencies,
    RadioMapSolver,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

# Import models and config from their new locations
from app.domains.device.models.device_model import Device, DeviceRole
from app.core.config import (
    NYCU_XML_PATH,
    CFR_PLOT_IMAGE_PATH,
    DOPPLER_IMAGE_PATH,
    CHANNEL_RESPONSE_IMAGE_PATH,
    SINR_MAP_IMAGE_PATH,
    get_scene_xml_path,
)

# 從設備領域中導入設備服務和儲存庫
from app.domains.device.services.device_service import DeviceService
from app.domains.device.adapters.sqlmodel_device_repository import (
    SQLModelDeviceRepository,
)

# Import interfaces and models
from app.domains.simulation.interfaces.simulation_service_interface import (
    SimulationServiceInterface,
)
from app.domains.simulation.models.simulation_model import SimulationParameters

# 新增導入 for GLB rendering
import trimesh
import pyrender
from PIL import Image
import io
import tensorflow as tf

# 從 config 導入
from app.core.config import NYCU_GLB_PATH, OUTPUT_DIR  # 確保導入 NYCU_GLB_PATH

logger = logging.getLogger(__name__)

# --- 新增：場景背景顏色常數 ---
SCENE_BACKGROUND_COLOR_RGB = [0.5, 0.5, 0.5]
# --- End Constant ---


# --- 輔助函數：XML 健康度檢查 ---
def check_scene_health(scene_name: str, xml_path: str) -> bool:
    """
    檢查場景的健康度，包括 XML 格式和幾何數據完整性
    返回 True 表示健康，False 表示需要回退
    """
    try:
        # 檢查 1: XML 文件是否存在
        if not os.path.exists(xml_path):
            logger.warning(f"場景 {scene_name} 的 XML 文件不存在: {xml_path}")
            return False

        # 檢查 2: XML 格式問題 - NTPU 和 Nanliao 有已知的 shape id 問題
        if scene_name in ["NTPU", "Nanliao"]:
            logger.warning(
                f"⚠️  注意：{scene_name} 場景的 XML 文件格式不相容於 Sionna"
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
                        f"⚠️  注意：{scene_name} 場景的幾何數據不完整"
                        f"（總大小: {total_size} bytes，{small_files}/{len(ply_files)} 個小文件），"
                        f"自動回退到 NYCU 場景以確保計算品質。"
                    )
                    return False

        return True

    except Exception as e:
        logger.warning(f"檢查場景 {scene_name} 健康度時出錯: {e}，回退到 NYCU")
        return False


# --- 輔助函數：獲取場景 XML 路徑 ---
def get_scene_xml_file_path(scene_name: str) -> str:
    """
    根據場景名稱獲取對應的 XML 文件路徑，包含智能健康度檢查和回退機制
    """
    try:
        # 將前端路由參數映射到後端場景名稱
        scene_mapping = {
            "nycu": "NYCU",
            "lotus": "Lotus",
            "ntpu": "NTPU",
            "nanliao": "Nanliao",
        }

        backend_scene_name = scene_mapping.get(scene_name.lower(), "NYCU")
        original_scene_name = backend_scene_name

        # 獲取 XML 路徑
        try:
            xml_path = get_scene_xml_path(backend_scene_name)
        except Exception as e:
            logger.warning(f"獲取場景檔案失敗: {e}，回退到 NYCU 場景")
            backend_scene_name = "NYCU"
            xml_path = get_scene_xml_path(backend_scene_name)

        # 健康度檢查
        if not check_scene_health(original_scene_name, xml_path):
            logger.info(f"場景 {original_scene_name} 健康度檢查失敗，回退到 NYCU 場景")
            backend_scene_name = "NYCU"
            xml_path = get_scene_xml_path(backend_scene_name)

        logger.info(f"場景 '{scene_name}' 映射到 XML 路徑: {xml_path}")
        return str(xml_path)

    except Exception as e:
        logger.error(f"獲取場景 XML 路徑失敗，使用預設 NYCU: {e}")
        return str(NYCU_XML_PATH)


# --- 通用函數：GPU 設置 ---
def _setup_gpu():
    """設置 GPU 環境，啟用記憶體增長"""
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
    gpus = tf.config.list_physical_devices("GPU")

    if gpus:
        try:
            tf.config.experimental.set_memory_growth(gpus[0], True)
            logger.info("GPU 記憶體成長已啟用")
        except Exception as e:
            logger.warning(f"無法啟用GPU記憶體增長: {e}")
    else:
        logger.info("未找到 GPU，使用 CPU")

    return gpus is not None


def _clean_output_file(output_path, file_desc="圖檔"):
    """清理舊的輸出文件"""
    if os.path.exists(output_path):
        logger.info(f"刪除舊的{file_desc}: {output_path}")
        os.remove(output_path)
        return True
    return False


def _ensure_output_dir(output_path):
    """確保輸出目錄存在"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    return True


def verify_output_file(output_path):
    """檢查輸出文件是否成功生成，可被外部調用"""
    exists = os.path.exists(output_path)
    size = os.path.getsize(output_path) if exists else -1
    is_file = os.path.isfile(output_path) if exists else False

    if exists and is_file and size > 0:
        logger.info(
            f"SUCCESS: File verified. Path: {output_path}, Size: {size} bytes, IsFile: {is_file}"
        )
        return True
    else:
        logger.error(
            f"FAILURE: File verification failed. Path: {output_path}, Exists: {exists}, Size: {size} bytes, IsFile: {is_file}"
        )
        return False


# 統一的文件準備函數
def prepare_output_file(output_path, file_desc="圖檔"):
    """清理舊文件並準備目錄結構"""
    _clean_output_file(output_path, file_desc)
    _ensure_output_dir(output_path)
    return True


# --- 定義新的資料容器 ---
class DeviceData(BaseModel):
    """用於傳遞設備模型和其處理後的位置列表"""

    device_model: Device = PydanticField(...)  # Store the original SQLModel object
    position_list: List[float] = None  # Store the position as a list [x, y, z]
    orientation_list: List[float] = None  # Store the orientation as a list [x, y, z]
    transmitter_role: Optional[DeviceRole] = (
        None  # Store transmitter type if applicable
    )

    class Config:
        arbitrary_types_allowed = True  # Allow complex types like SQLModel objects


# --- Helper Function for Pyrender Scene Setup ---
def _setup_pyrender_scene_from_glb() -> Optional[pyrender.Scene]:
    """Loads GLB, sets up pyrender scene, lights, camera. Returns Scene or None on error."""
    logger.info(f"Setting up base pyrender scene from GLB: {NYCU_GLB_PATH}")
    try:
        # 1. Load GLB
        if not os.path.exists(NYCU_GLB_PATH) or os.path.getsize(NYCU_GLB_PATH) == 0:
            logger.error(f"GLB file not found or empty: {NYCU_GLB_PATH}")
            return None
        scene_tm = trimesh.load(NYCU_GLB_PATH, force="scene")
        logger.info("GLB file loaded.")

        # 2. Create pyrender scene with background and ambient light
        pr_scene = pyrender.Scene(
            bg_color=[*SCENE_BACKGROUND_COLOR_RGB, 1.0],
            ambient_light=[0.6, 0.6, 0.6],
        )

        # 3. Add GLB geometry
        logger.info("Adding GLB geometry...")
        for name, geom in scene_tm.geometry.items():
            if geom.vertices is not None and len(geom.vertices) > 0:
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
                if not hasattr(geom, "visual") or (
                    not hasattr(geom.visual, "vertex_colors")
                    and not hasattr(geom.visual, "material")
                ):
                    geom.visual = trimesh.visual.ColorVisuals(
                        mesh=geom, vertex_colors=[255, 255, 255, 255]
                    )
                try:
                    mesh = pyrender.Mesh.from_trimesh(geom, smooth=False)
                    pr_scene.add(mesh)
                except Exception as mesh_err:
                    logger.error(
                        f"Failed convert mesh '{name}': {mesh_err}", exc_info=True
                    )
            else:
                logger.warning(f"Skipping empty mesh '{name}'.")
        logger.info("GLB geometry added.")

        # 4. Add lights
        warm_white = np.array([1.0, 0.98, 0.9])
        main_light = pyrender.DirectionalLight(color=warm_white, intensity=3.0)
        pr_scene.add(main_light, pose=np.eye(4))
        logger.info("Lights added.")

        # 5. Add camera
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
        logger.info("Camera added.")

        return pr_scene

    except Exception as e:
        logger.error(f"Error setting up pyrender scene from GLB: {e}", exc_info=True)
        return None


# --- NEW Helper Function for Rendering, Cropping, and Saving ---
def _render_crop_and_save(
    pr_scene: pyrender.Scene,
    output_path: str,
    bg_color_float: List[float] = SCENE_BACKGROUND_COLOR_RGB,
    render_width: int = 1200,
    render_height: int = 858,
    padding_y: int = 0,  # Default vertical padding
    padding_x: int = 0,  # Default horizontal padding
) -> bool:
    """Renders the scene, crops based on content, and saves the image."""
    logger.info("Starting offscreen rendering...")
    try:
        renderer = pyrender.OffscreenRenderer(render_width, render_height)
        color, _ = renderer.render(pr_scene)

        # 安全地釋放 renderer 資源，捕獲可能的 GLError
        try:
            renderer.delete()
        except Exception as delete_err:
            # 這是已知的 EGL 問題，不影響渲染結果，可以忽略
            pass

        logger.info("Rendering complete.")
    except Exception as render_err:
        logger.error(f"Pyrender OffscreenRenderer failed: {render_err}", exc_info=True)
        return False

    # --- Cropping Logic ---
    logger.info("Calculating bounding box for cropping...")
    image_to_save = color  # Default to original image
    try:
        bg_color_uint8 = (np.array(bg_color_float) * 255).astype(np.uint8)
        mask = ~np.all(color[:, :, :3] == bg_color_uint8, axis=2)
        rows, cols = np.where(mask)

        if rows.size > 0 and cols.size > 0:
            ymin, ymax = rows.min(), rows.max()
            xmin, xmax = cols.min(), cols.max()
            # Apply padding separately
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
        # Fallback to original image

    # --- Save the Image using PIL ---
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    logger.info(f"Saving final image to: {output_path}")
    try:
        img = Image.fromarray(image_to_save)
        img.save(output_path, format="PNG")
    except Exception as save_err:
        logger.error(f"Failed to save rendered image: {save_err}", exc_info=True)
        return False

    # Final check
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        logger.info(
            f"Successfully saved image to {output_path}, size: {os.path.getsize(output_path)} bytes"
        )
        return True
    else:
        logger.error(f"Failed to save image or image is empty: {output_path}")
        return False


# --- Refactor generate_empty_scene_image to use the helpers ---
def generate_empty_scene_image(output_path: str):
    """Generates a cropped scene image by rendering the GLB file (using helpers)."""
    logger.info(f"Entering generate_empty_scene_image function, calling helpers...")
    try:
        # 準備輸出檔案
        prepare_output_file(output_path, "空場景圖檔")

        # 1. Setup scene using helper
        pr_scene = _setup_pyrender_scene_from_glb()  # Helper uses this bg color
        if pr_scene is None:
            return False

        # 2. Render, Crop, and Save using helper
        success = _render_crop_and_save(
            pr_scene,
            output_path,
            bg_color_float=SCENE_BACKGROUND_COLOR_RGB,
            padding_x=5,  # Set horizontal padding to 5
            padding_y=20,  # Keep vertical padding at 20 (or adjust if needed)
        )
        return success

    except ImportError as ie:
        logger.error(f"Import error in generate_empty_scene_image: {ie}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"Error rendering empty scene via helpers: {e}", exc_info=True)
        return False


# 新增函數: generate_cfr_plot
async def generate_cfr_plot(
    session: AsyncSession,
    output_path: str = str(CFR_PLOT_IMAGE_PATH),
    scene_name: str = "nycu",
) -> bool:
    """
    生成 Channel Frequency Response (CFR) 圖，基於 Sionna 的模擬。
    這是從 cfr.py 整合的功能。

    從資料庫中獲取接收器 (receiver)、發射器 (desired) 和干擾器 (jammer) 參數。
    """
    logger.info("Entering generate_cfr_plot function...")

    try:
        # 準備輸出檔案
        prepare_output_file(output_path, "CFR 圖檔")

        # 創建設備服務和儲存庫
        device_repository = SQLModelDeviceRepository(session)
        device_service = DeviceService(device_repository)

        logger.info("Fetching active receivers from database...")
        active_receivers = await device_service.get_devices(
            skip=0, limit=100, role=DeviceRole.RECEIVER.value, active_only=True
        )

        if not active_receivers:
            logger.warning(
                "No active receivers found in database. Using default receiver parameters."
            )
            # 使用默認的接收器參數
            rx_name = "rx"
            rx_position = [0, 0, 20]
        else:
            # 使用第一個活動接收器的參數
            receiver = active_receivers[0]
            rx_name = receiver.name
            rx_position = [
                receiver.position_x,
                receiver.position_y,
                receiver.position_z,
            ]
            logger.info(f"Using receiver '{rx_name}' with position {rx_position}")

        # 從資料庫獲取活動的發射器 (desired)
        logger.info("Fetching active desired transmitters from database...")
        active_desired = await device_service.get_devices(
            skip=0, limit=100, role=DeviceRole.DESIRED.value, active_only=True
        )

        # 從資料庫獲取活動的干擾器 (jammer)
        logger.info("Fetching active jammers from database...")
        active_jammers = await device_service.get_devices(
            skip=0, limit=100, role=DeviceRole.JAMMER.value, active_only=True
        )

        # 構建 TX_LIST (發射器和干擾器列表)
        TX_LIST = []

        # 添加發射器
        if not active_desired:
            logger.warning(
                "No active desired transmitters found in database. Simulation might not be meaningful."
            )
            # 添加默認的發射器參數 # REMOVED
        else:
            # 添加從資料庫獲取的發射器
            for i, tx in enumerate(active_desired):
                tx_name = tx.name
                tx_position = [tx.position_x, tx.position_y, tx.position_z]
                tx_orientation = [tx.orientation_x, tx.orientation_y, tx.orientation_z]
                tx_power = tx.power_dbm

                TX_LIST.append(
                    (tx_name, tx_position, tx_orientation, "desired", tx_power)
                )
                logger.info(
                    f"Added desired transmitter: {tx_name}, position: {tx_position}, orientation: {tx_orientation}, power: {tx_power} dBm"
                )

        # 添加干擾器
        if not active_jammers:
            logger.warning(
                "No active jammers found in database. Interference simulation will not run."
            )
            # 添加默認的干擾器參數 # REMOVED
        else:
            # 添加從資料庫獲取的干擾器
            for i, jammer in enumerate(active_jammers):
                jammer_name = jammer.name
                jammer_position = [
                    jammer.position_x,
                    jammer.position_y,
                    jammer.position_z,
                ]
                jammer_orientation = [
                    jammer.orientation_x,
                    jammer.orientation_y,
                    jammer.orientation_z,
                ]
                jammer_power = jammer.power_dbm

                TX_LIST.append(
                    (
                        jammer_name,
                        jammer_position,
                        jammer_orientation,
                        "jammer",
                        jammer_power,
                    )
                )
                logger.info(
                    f"Added jammer: {jammer_name}, position: {jammer_position}, orientation: {jammer_orientation}, power: {jammer_power} dBm"
                )

        # 檢查是否有足夠的發射器和干擾器
        if not TX_LIST:
            logger.error(
                "No transmitters or jammers available for simulation. Cannot proceed."
            )
            return False

        # 參數設置
        SCENE_NAME = get_scene_xml_file_path(scene_name)
        logger.info(f"Loading scene from: {SCENE_NAME}")

        TX_ARRAY_CONFIG = {
            "num_rows": 1,
            "num_cols": 1,
            "vertical_spacing": 0.5,
            "horizontal_spacing": 0.5,
            "pattern": "iso",
            "polarization": "V",
        }
        RX_ARRAY_CONFIG = TX_ARRAY_CONFIG

        # 使用從資料庫獲取的接收器參數
        RX_CONFIG = (rx_name, rx_position)

        PATHSOLVER_ARGS = {
            "max_depth": 10,
            "los": True,
            "specular_reflection": True,
            "diffuse_reflection": False,
            "refraction": False,
            "synthetic_array": False,
            "seed": 41,
        }

        N_SYMBOLS = 1
        N_SUBCARRIERS = 1024
        SUBCARRIER_SPACING = 30e3
        EBN0_dB = 20.0

        # 場景設置
        logger.info("Setting up scene")
        scene = load_scene(SCENE_NAME)
        scene.tx_array = PlanarArray(**TX_ARRAY_CONFIG)
        scene.rx_array = PlanarArray(**RX_ARRAY_CONFIG)

        # 清除現有的發射器和接收器
        for name in list(scene.transmitters.keys()) + list(scene.receivers.keys()):
            scene.remove(name)

        # 添加發射器
        logger.info("Adding transmitters")

        def add_tx(scene, name, pos, ori, role, power_dbm):
            tx = SionnaTransmitter(
                name=name, position=pos, orientation=ori, power_dbm=power_dbm
            )
            tx.role = role
            scene.add(tx)
            return tx

        for name, pos, ori, role, p_dbm in TX_LIST:
            add_tx(scene, name, pos, ori, role, p_dbm)

        # 添加接收器
        logger.info(f"Adding receiver '{rx_name}' at position {rx_position}")
        rx_name, rx_pos = RX_CONFIG
        scene.add(SionnaReceiver(name=rx_name, position=rx_pos))

        # 分組發射器
        tx_names = list(scene.transmitters.keys())
        all_txs = [scene.get(n) for n in tx_names]
        idx_des = [i for i, tx in enumerate(all_txs) if tx.role == "desired"]
        idx_jam = [i for i, tx in enumerate(all_txs) if tx.role == "jammer"]

        # 檢查是否有發射器和干擾器
        if not idx_des:
            logger.warning(
                "No desired transmitters available in scene. CFR calculation may not be accurate."
            )
        if not idx_jam:
            logger.warning(
                "No jammers available in scene. Interference will not be present in plot."
            )

        # 計算 CFR
        logger.info("Computing CFR")
        freqs = subcarrier_frequencies(N_SUBCARRIERS, SUBCARRIER_SPACING)
        for name in tx_names:
            scene.get(name).velocity = [30, 0, 0]
        paths = PathSolver()(scene, **PATHSOLVER_ARGS)

        def dbm2w(dbm):
            return 10 ** (dbm / 10) / 1000

        tx_powers = [dbm2w(scene.get(n).power_dbm) for n in tx_names]
        ofdm_symbol_duration = 1 / SUBCARRIER_SPACING
        H_unit = paths.cfr(
            frequencies=freqs,
            sampling_frequency=1 / ofdm_symbol_duration,
            num_time_steps=N_SUBCARRIERS,
            normalize_delays=True,
            normalize=False,
            out_type="numpy",
        ).squeeze()  # shape: (num_tx, T, F)

        H_all = np.sqrt(np.array(tx_powers)[:, None, None]) * H_unit
        H = H_unit[:, 0, :]  # 取第一個時間步

        # 安全處理：確保有所需的發射器
        h_main = np.zeros(N_SUBCARRIERS, dtype=complex)
        if idx_des:
            h_main = sum(np.sqrt(tx_powers[i]) * H[i] for i in idx_des)

        h_intf = np.zeros(N_SUBCARRIERS, dtype=complex)
        if idx_jam:
            h_intf = sum(np.sqrt(tx_powers[i]) * H[i] for i in idx_jam)

        # 生成 QPSK+OFDM 符號
        logger.info("Generating QPSK+OFDM symbols")
        bits = np.random.randint(0, 2, (N_SYMBOLS, N_SUBCARRIERS, 2))
        bits_jam = np.random.randint(0, 2, (N_SYMBOLS, N_SUBCARRIERS, 2))
        X_sig = (1 - 2 * bits[..., 0] + 1j * (1 - 2 * bits[..., 1])) / np.sqrt(2)
        X_jam = (1 - 2 * bits_jam[..., 0] + 1j * (1 - 2 * bits_jam[..., 1])) / np.sqrt(
            2
        )

        Y_sig = X_sig * h_main[None, :]
        Y_int = X_jam * h_intf[None, :]
        p_sig = np.mean(np.abs(Y_sig) ** 2)
        N0 = p_sig / (10 ** (EBN0_dB / 10) * 2) if p_sig > 0 else 1e-10
        noise = np.sqrt(N0 / 2) * (
            np.random.randn(*Y_sig.shape) + 1j * np.random.randn(*Y_sig.shape)
        )
        Y_tot = Y_sig + Y_int + noise

        # 安全處理：避免除以零
        non_zero_mask = np.abs(h_main) > 1e-10
        y_eq_no_i = np.zeros_like(Y_sig)
        y_eq_with_i = np.zeros_like(Y_tot)

        if np.any(non_zero_mask):
            y_eq_no_i[:, non_zero_mask] = (Y_sig + noise)[:, non_zero_mask] / h_main[
                None, non_zero_mask
            ]
            y_eq_with_i[:, non_zero_mask] = (
                Y_tot[:, non_zero_mask] / h_main[None, non_zero_mask]
            )

        # 繪製星座圖和 CFR，然後保存到文件
        logger.info("Plotting constellation and CFR")
        fig, ax = plt.subplots(1, 3, figsize=(15, 4))
        ax[0].scatter(y_eq_no_i.real, y_eq_no_i.imag, s=4, alpha=0.25)
        ax[0].set(title="No interference", xlabel="Real", ylabel="Imag")
        ax[0].grid(True)

        ax[1].scatter(y_eq_with_i.real, y_eq_with_i.imag, s=4, alpha=0.25)
        ax[1].set(title="With interferer", xlabel="Real", ylabel="Imag")
        ax[1].grid(True)

        ax[2].plot(np.abs(h_main), label="|H_main|")
        ax[2].plot(np.abs(h_intf), label="|H_intf|")
        ax[2].set(title="CFR Magnitude", xlabel="Subcarrier Index")
        ax[2].legend()
        ax[2].grid(True)

        plt.tight_layout()

        # 保存圖片
        logger.info(f"Saving plot to {output_path}")
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

        # 檢查文件是否成功生成
        return verify_output_file(output_path)

    except Exception as e:
        logger.exception(f"Error in generate_cfr_plot: {e}")
        # 確保關閉所有打開的圖表
        plt.close("all")
        return False


# 新增 SINR Map 生成函數
async def generate_sinr_map(
    session: AsyncSession,
    output_path: str = str(SINR_MAP_IMAGE_PATH),
    scene_name: str = "nycu",
    sinr_vmin: float = -40,
    sinr_vmax: float = 0,
    cell_size: float = 1.0,
    samples_per_tx: int = 10**7,
) -> bool:
    """
    生成 SINR (Signal-to-Interference-plus-Noise Ratio) 地圖

    從數據庫獲取發射器和接收器設置，計算並生成 SINR 地圖
    """
    logger.info("開始生成 SINR 地圖...")

    try:
        # 準備輸出檔案
        prepare_output_file(output_path, "SINR 地圖圖檔")

        # GPU 設置
        gpus = _setup_gpu()

        # 創建設備服務和儲存庫
        device_repository = SQLModelDeviceRepository(session)
        device_service = DeviceService(device_repository)

        # 從數據庫獲取活動的發射器 (desired)
        logger.info("從數據庫獲取活動的發射器...")
        active_desired = await device_service.get_devices(
            skip=0, limit=100, role=DeviceRole.DESIRED.value, active_only=True
        )

        # 從數據庫獲取活動的干擾器 (jammer)
        logger.info("從數據庫獲取活動的干擾器...")
        active_jammers = await device_service.get_devices(
            skip=0, limit=100, role=DeviceRole.JAMMER.value, active_only=True
        )

        # 從數據庫獲取活動的接收器
        logger.info("從數據庫獲取活動的接收器...")
        active_receivers = await device_service.get_devices(
            skip=0, limit=100, role=DeviceRole.RECEIVER.value, active_only=True
        )

        # 檢查是否有足夠的設備
        if not active_desired and not active_jammers:
            logger.error("沒有活動的發射器或干擾器，無法生成 SINR 地圖")
            return False

        if not active_receivers:
            logger.warning("沒有活動的接收器，將使用預設接收器位置")
            rx_config = ("rx", [-30, 50, 20])
        else:
            # 使用第一個活動接收器
            receiver = active_receivers[0]
            rx_config = (
                receiver.name,
                [receiver.position_x, receiver.position_y, receiver.position_z],
            )

        # 構建 TX_LIST
        tx_list = []

        # 添加發射器
        for tx in active_desired:
            tx_name = tx.name
            tx_position = [tx.position_x, tx.position_y, tx.position_z]
            tx_orientation = [tx.orientation_x, tx.orientation_y, tx.orientation_z]
            tx_power = tx.power_dbm

            tx_list.append((tx_name, tx_position, tx_orientation, "desired", tx_power))
            logger.info(
                f"添加發射器: {tx_name}, 位置: {tx_position}, 方向: {tx_orientation}, 功率: {tx_power} dBm"
            )

        # 添加干擾器
        for jammer in active_jammers:
            jammer_name = jammer.name
            jammer_position = [jammer.position_x, jammer.position_y, jammer.position_z]
            jammer_orientation = [
                jammer.orientation_x,
                jammer.orientation_y,
                jammer.orientation_z,
            ]
            jammer_power = jammer.power_dbm

            tx_list.append(
                (
                    jammer_name,
                    jammer_position,
                    jammer_orientation,
                    "jammer",
                    jammer_power,
                )
            )
            logger.info(
                f"添加干擾器: {jammer_name}, 位置: {jammer_position}, 方向: {jammer_orientation}, 功率: {jammer_power} dBm"
            )

        # 如果沒有足夠的發射器，返回錯誤
        if not tx_list:
            logger.error("沒有可用的發射器或干擾器，無法生成 SINR 地圖")
            return False

        # 參數設置
        scene_xml_path = get_scene_xml_file_path(scene_name)
        logger.info(f"從 {scene_xml_path} 加載場景")

        tx_array_config = {
            "num_rows": 1,
            "num_cols": 1,
            "vertical_spacing": 0.5,
            "horizontal_spacing": 0.5,
            "pattern": "iso",
            "polarization": "V",
        }
        rx_array_config = tx_array_config

        rmsolver_args = {
            "max_depth": 10,
            "cell_size": (cell_size, cell_size),
            "samples_per_tx": samples_per_tx,
        }

        # 場景設置
        logger.info("設置場景")
        scene = load_scene(scene_xml_path)
        scene.tx_array = PlanarArray(**tx_array_config)
        scene.rx_array = PlanarArray(**rx_array_config)

        # 清除現有的發射器和接收器
        for name in list(scene.transmitters.keys()) + list(scene.receivers.keys()):
            scene.remove(name)

        # 添加發射器
        logger.info("添加發射器")

        def add_tx(scene, name, pos, ori, role, power_dbm):
            tx = SionnaTransmitter(
                name=name, position=pos, orientation=ori, power_dbm=power_dbm
            )
            tx.role = role
            scene.add(tx)
            return tx

        for name, pos, ori, role, p_dbm in tx_list:
            add_tx(scene, name, pos, ori, role, p_dbm)

        # 添加接收器
        rx_name, rx_pos = rx_config
        logger.info(f"添加接收器 '{rx_name}' 在位置 {rx_pos}")
        scene.add(SionnaReceiver(name=rx_name, position=rx_pos))

        # 按角色分組發射器
        all_txs = [scene.get(n) for n in scene.transmitters]
        idx_des = [
            i for i, tx in enumerate(all_txs) if getattr(tx, "role", None) == "desired"
        ]
        idx_jam = [
            i for i, tx in enumerate(all_txs) if getattr(tx, "role", None) == "jammer"
        ]

        if not idx_des and not idx_jam:
            logger.error("場景中沒有有效的發射器或干擾器")
            return False

        # 計算無線電地圖
        logger.info("計算無線電地圖")
        rm_solver = RadioMapSolver()
        rm = rm_solver(scene, **rmsolver_args)

        # 計算並繪製 SINR 地圖
        logger.info("計算 SINR 地圖")
        cc = rm.cell_centers.numpy()
        x_unique = cc[0, :, 0]
        y_unique = cc[:, 0, 1]
        rss_list = [rm.rss[i].numpy() for i in range(len(all_txs))]

        # 計算 SINR
        N0_map = 1e-12  # 噪聲功率

        # 檢查是否有目標發射器和干擾器
        if idx_des:
            rss_des = sum(rss_list[i] for i in idx_des)
        else:
            logger.warning("沒有目標發射器，將假設沒有信號")
            rss_des = (
                np.zeros_like(rss_list[0])
                if rss_list
                else np.zeros((len(y_unique), len(x_unique)))
            )

        if idx_jam:
            rss_jam = sum(rss_list[i] for i in idx_jam)
        else:
            logger.warning("沒有干擾器，將假設沒有干擾")
            rss_jam = (
                np.zeros_like(rss_list[0])
                if rss_list
                else np.zeros((len(y_unique), len(x_unique)))
            )

        # 計算 SINR (dB)，確保公式與原始 sinr.py 一致
        sinr_db = 10 * np.log10(
            np.clip(rss_des / (rss_des + rss_jam + N0_map), 1e-12, None)
        )

        # 繪製地圖
        logger.info("繪製 SINR 地圖")
        fig, ax = plt.subplots(figsize=(7, 5))
        X, Y = np.meshgrid(x_unique, y_unique)
        pcm = ax.pcolormesh(
            X, Y, sinr_db, shading="nearest", vmin=sinr_vmin + 10, vmax=sinr_vmax
        )
        fig.colorbar(pcm, ax=ax, label="SINR (dB)")

        # 繪製發射器和接收器
        ax.scatter(
            [t.position[0] for t in all_txs if getattr(t, "role", None) == "desired"],
            [t.position[1] for t in all_txs if getattr(t, "role", None) == "desired"],
            c="red",
            marker="^",
            s=100,
            label="Tx",
        )
        ax.scatter(
            [t.position[0] for t in all_txs if getattr(t, "role", None) == "jammer"],
            [t.position[1] for t in all_txs if getattr(t, "role", None) == "jammer"],
            c="red",
            marker="x",
            s=100,
            label="Jam",
        )

        # 獲取接收器
        rx_object = scene.get(rx_name)
        if rx_object:
            ax.scatter(
                rx_object.position[0],
                rx_object.position[1],
                c="green",
                marker="o",
                s=50,
                label="Rx",
            )

        ax.legend()
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
        ax.set_title("SINR Map")
        ax.invert_yaxis()
        plt.tight_layout()

        # 保存圖片
        logger.info(f"保存 SINR 地圖到 {output_path}")
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

        # 檢查文件是否生成成功
        return verify_output_file(output_path)

    except Exception as e:
        logger.exception(f"生成 SINR 地圖時發生錯誤: {e}")
        # 確保關閉所有打開的圖表
        plt.close("all")
        return False


# 新增 Doppler 圖生成函數
async def generate_doppler_plots(
    session: AsyncSession,
    output_path: str = str(DOPPLER_IMAGE_PATH),
    scene_name: str = "nycu",
) -> bool:
    """
    生成延遲多普勒圖 (Delay-Doppler)，基於 delay-doppler-v2.py 的功能

    從數據庫中獲取發射器、接收器和干擾器參數，生成統一的延遲多普勒圖
    """
    logger.info("開始生成延遲多普勒圖...")

    try:
        # 準備輸出檔案
        prepare_output_file(output_path, "延遲多普勒圖檔")

        # 設置 GPU
        _setup_gpu()

        # 創建設備服務和儲存庫
        device_repository = SQLModelDeviceRepository(session)
        device_service = DeviceService(device_repository)

        # 從資料庫獲取活動的發射器 (desired)
        logger.info("從數據庫獲取活動的發射器...")
        active_desired = await device_service.get_devices(
            skip=0, limit=100, role=DeviceRole.DESIRED.value, active_only=True
        )

        # 從資料庫獲取活動的干擾器 (jammer)
        logger.info("從數據庫獲取活動的干擾器...")
        active_jammers = await device_service.get_devices(
            skip=0, limit=100, role=DeviceRole.JAMMER.value, active_only=True
        )

        # 從資料庫獲取活動的接收器
        logger.info("從數據庫獲取活動的接收器...")
        active_receivers = await device_service.get_devices(
            skip=0, limit=100, role=DeviceRole.RECEIVER.value, active_only=True
        )

        # 構建 TX_LIST
        tx_list = []

        # 添加發射器
        for tx in active_desired:
            tx_name = tx.name
            tx_position = [tx.position_x, tx.position_y, tx.position_z]
            tx_orientation = [tx.orientation_x, tx.orientation_y, tx.orientation_z]
            tx_power = tx.power_dbm

            tx_list.append((tx_name, tx_position, tx_orientation, "desired", tx_power))
            logger.info(
                f"添加發射器: {tx_name}, 位置: {tx_position}, 方向: {tx_orientation}, 功率: {tx_power} dBm"
            )

        # 添加干擾器
        for jammer in active_jammers:
            jammer_name = jammer.name
            jammer_position = [jammer.position_x, jammer.position_y, jammer.position_z]
            jammer_orientation = [
                jammer.orientation_x,
                jammer.orientation_y,
                jammer.orientation_z,
            ]
            jammer_power = jammer.power_dbm

            tx_list.append(
                (
                    jammer_name,
                    jammer_position,
                    jammer_orientation,
                    "jammer",
                    jammer_power,
                )
            )
            logger.info(
                f"添加干擾器: {jammer_name}, 位置: {jammer_position}, 方向: {jammer_orientation}, 功率: {jammer_power} dBm"
            )

        # 設置接收器
        if not active_receivers:
            logger.warning("沒有找到活動的接收器，使用默認位置")
            rx_config = ("rx", [0, 0, 40])
        else:
            # 使用第一個活動接收器
            receiver = active_receivers[0]
            rx_config = (
                receiver.name,
                [receiver.position_x, receiver.position_y, receiver.position_z],
            )
            logger.info(f"使用接收器 '{rx_config[0]}' 在位置 {rx_config[1]}")

        # -------- 以下為參考 delay-doppler-v2.py 的邏輯 --------

        # 參數設定
        TX_ARRAY_CONFIG = dict(
            num_rows=1,
            num_cols=1,
            vertical_spacing=0.5,
            horizontal_spacing=0.5,
            pattern="iso",
            polarization="V",
        )
        RX_ARRAY_CONFIG = TX_ARRAY_CONFIG

        # 如果沒有設備，回傳錯誤
        if not tx_list:
            logger.error("沒有活動的發射器或干擾器，無法生成延遲多普勒圖")
            return False

        PATHSOLVER_ARGS = dict(
            max_depth=3,
            los=True,
            specular_reflection=True,
            diffuse_reflection=False,
            refraction=False,
            synthetic_array=False,
            seed=41,
        )

        # OFDM 參數
        N_SUBCARRIERS = 1024
        SUBCARRIER_SPACING = 30e3
        num_ofdm_symbols = 1024

        # 建立場景與天線配置
        scene_xml_path = get_scene_xml_file_path(scene_name)
        logger.info(f"從 {scene_xml_path} 加載場景")
        scene = load_scene(scene_xml_path)
        scene.tx_array = PlanarArray(**TX_ARRAY_CONFIG)
        scene.rx_array = PlanarArray(**RX_ARRAY_CONFIG)

        # 移除現有發射機和接收機
        for tx_name in list(scene.transmitters.keys()):
            scene.remove(tx_name)
        for rx_name in list(scene.receivers.keys()):
            scene.remove(rx_name)

        # 確認清空
        if len(scene.transmitters) > 0 or len(scene.receivers) > 0:
            logger.warning("無法完全清空場景中的發射機和接收機")

        # 新增發射機
        def add_tx(scene, name, pos, ori, role, power_dbm):
            tx = SionnaTransmitter(
                name=name, position=pos, orientation=ori, power_dbm=power_dbm
            )
            tx.role = role
            scene.add(tx)
            return tx

        for name, pos, ori, role, p_dbm in tx_list:
            add_tx(scene, name, pos, ori, role, p_dbm)

        # 新增接收機
        rx_name, rx_pos = rx_config
        logger.info(f"添加接收器 '{rx_name}' 在位置 {rx_pos}")
        scene.add(SionnaReceiver(name=rx_name, position=rx_pos))

        # 分組索引
        tx_names = list(scene.transmitters.keys())
        all_txs = [scene.get(n) for n in tx_names]
        idx_des = [
            i for i, tx in enumerate(all_txs) if getattr(tx, "role", None) == "desired"
        ]
        idx_jam = [
            i for i, tx in enumerate(all_txs) if getattr(tx, "role", None) == "jammer"
        ]

        # 計算 CFR
        logger.info("計算 CFR")
        freqs = subcarrier_frequencies(N_SUBCARRIERS, SUBCARRIER_SPACING)
        for name in scene.transmitters:
            scene.get(name).velocity = [30, 0, 0]

        # 使用 PathSolver
        solver = PathSolver()
        try:
            paths = solver(scene, **PATHSOLVER_ARGS)
        except RuntimeError as e:
            logger.error(f"PathSolver 错误: {e}")
            logger.error(
                "嘗試減少 max_depth, max_num_paths_per_src, 或使用更簡單的場景。"
            )
            return False

        ofdm_symbol_duration = 1 / SUBCARRIER_SPACING
        delay_resolution = ofdm_symbol_duration / N_SUBCARRIERS
        doppler_resolution = SUBCARRIER_SPACING / num_ofdm_symbols

        # 計算 CFR
        H_unit = paths.cfr(
            frequencies=freqs,
            sampling_frequency=1 / ofdm_symbol_duration,
            num_time_steps=num_ofdm_symbols,
            normalize_delays=False,
            normalize=False,
            out_type="numpy",
        ).squeeze()

        # 處理功率加權
        tx_p_lin = 10 ** (np.array([tx.power_dbm for tx in all_txs]) / 10) / 1e3
        tx_p_lin = np.squeeze(tx_p_lin)
        sqrtP = np.sqrt(tx_p_lin)[:, None, None]
        H_unit = H_unit * sqrtP

        # 計算 Delay-Doppler 圖
        def to_delay_doppler(H_tf):
            Hf = np.fft.fftshift(H_tf, axes=1)
            h_delay = np.fft.ifft(Hf, axis=1, norm="ortho")
            h_dd = np.fft.fft(h_delay, axis=0, norm="ortho")
            h_dd = np.fft.fftshift(h_dd, axes=0)
            return h_dd

        # 計算每個發射機的延遲多普勒圖
        Hdd_list = [np.abs(to_delay_doppler(H_unit[i])) for i in range(H_unit.shape[0])]

        # 動態組合網格
        grids = []
        labels = []
        doppler_bins = np.arange(
            -num_ofdm_symbols / 2 * doppler_resolution,
            num_ofdm_symbols / 2 * doppler_resolution,
            doppler_resolution,
        )
        delay_bins = (
            np.arange(0, N_SUBCARRIERS * delay_resolution, delay_resolution) / 1e-9
        )
        x, y = np.meshgrid(delay_bins, doppler_bins)

        offset = 20
        x_start = int(N_SUBCARRIERS / 2) - offset
        x_end = int(N_SUBCARRIERS / 2) + offset
        y_start = 0
        y_end = offset
        x_grid = x[x_start:x_end, y_start:y_end]
        y_grid = y[x_start:x_end, y_start:y_end]

        # Desired 個別 - 使用原始索引 i 而非 k+1
        for k, i in enumerate(idx_des):
            Zi = Hdd_list[i][x_start:x_end, y_start:y_end]
            grids.append(Zi)
            labels.append(f"Des Tx{i}")  # 使用 i 而非 k+1

        # Jammer 個別 - 使用原始索引 i 而非 k+1
        for k, i in enumerate(idx_jam):
            Zi = Hdd_list[i][x_start:x_end, y_start:y_end]
            grids.append(Zi)
            labels.append(f"Jam Tx{i}")  # 使用 i 而非 k+1

        # Desired All
        if idx_des:
            Z_des_all = np.sum([Hdd_list[i] for i in idx_des], axis=0)
            grids.append(Z_des_all[x_start:x_end, y_start:y_end])
            labels.append("Des ALL")

        # Jammer All
        if idx_jam:
            Z_jam_all = np.sum([Hdd_list[i] for i in idx_jam], axis=0)
            grids.append(Z_jam_all[x_start:x_end, y_start:y_end])
            labels.append("Jam ALL")

        # All Tx
        Z_all = np.sum(Hdd_list, axis=0)
        grids.append(Z_all[x_start:x_end, y_start:y_end])
        labels.append("ALL Tx")

        # 統一 Z 軸
        z_min = 0
        z_max = max(g.max() for g in grids) * 1.05

        # 自動排版
        n_plots = len(grids)
        cols = 3
        rows = int(np.ceil(n_plots / cols))

        # 調整圖像大小使其擴展到容器寬度 - 使用與原始相同的圖像大小計算
        figsize = (cols * 4.5, rows * 4.5)

        # 繪製單一的統一圖
        logger.info(f"繪製統一的延遲多普勒圖")
        fig = plt.figure(figsize=figsize)
        fig.suptitle("Delay-Doppler Plots")  # 標題使用原始設置

        for idx, (Z, label) in enumerate(zip(grids, labels), start=1):
            ax = fig.add_subplot(rows, cols, idx, projection="3d")
            # 使用與原始相同的色彩映射 viridis
            ax.plot_surface(x_grid, y_grid, Z, cmap="viridis", edgecolor="none")
            ax.set_title(f"Delay–Doppler |{label}|", pad=8)
            ax.set_xlabel("Delay (ns)")
            ax.set_ylabel("Doppler (Hz)")
            ax.set_zlabel("|H|")
            ax.set_zlim(z_min, z_max)
            # 移除自定義視角設置，使用默認視角

        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

        # 檢查文件是否生成成功
        return verify_output_file(output_path)

    except Exception as e:
        logger.exception(f"生成延遲多普勒圖時發生錯誤: {e}")
        # 確保關閉所有打開的圖表
        plt.close("all")
        return False


# 新增函數: 整合 tf.py 的通道響應圖功能
async def generate_channel_response_plots(
    session: AsyncSession,
    output_path: str = str(CHANNEL_RESPONSE_IMAGE_PATH),
    scene_name: str = "nycu",
) -> bool:
    """
    生成通道響應圖 (H_des, H_jam, H_all)，基於 tf.py 中的功能。
    從資料庫獲取接收器、發射器和干擾器參數。
    """
    logger.info("開始生成通道響應圖...")

    try:
        # 準備輸出檔案
        prepare_output_file(output_path, "通道響應圖檔")

        # 創建設備服務和儲存庫
        device_repository = SQLModelDeviceRepository(session)
        device_service = DeviceService(device_repository)

        # 從資料庫獲取活動的發射器 (desired)
        logger.info("從數據庫獲取活動的發射器...")
        active_desired = await device_service.get_devices(
            skip=0, limit=100, role=DeviceRole.DESIRED.value, active_only=True
        )

        # 從資料庫獲取活動的干擾器 (jammer)
        logger.info("從數據庫獲取活動的干擾器...")
        active_jammers = await device_service.get_devices(
            skip=0, limit=100, role=DeviceRole.JAMMER.value, active_only=True
        )

        # 從資料庫獲取活動的接收器
        logger.info("從數據庫獲取活動的接收器...")
        active_receivers = await device_service.get_devices(
            skip=0, limit=100, role=DeviceRole.RECEIVER.value, active_only=True
        )

        # 檢查是否有足夠的設備進行模擬
        if not active_desired:
            logger.error("沒有活動的發射器，無法生成通道響應圖")
            return False

        if not active_receivers:
            logger.error("沒有活動的接收器，無法生成通道響應圖")
            return False

        # 構建 TX_LIST
        tx_list = []

        # 添加從資料庫獲取的發射器
        for tx in active_desired:
            tx_name = tx.name
            tx_position = [tx.position_x, tx.position_y, tx.position_z]
            tx_orientation = [tx.orientation_x, tx.orientation_y, tx.orientation_z]
            tx_power = tx.power_dbm

            tx_list.append((tx_name, tx_position, tx_orientation, "desired", tx_power))
            logger.info(
                f"添加發射器: {tx_name}, 位置: {tx_position}, 方向: {tx_orientation}, 功率: {tx_power} dBm"
            )

        # 添加從資料庫獲取的干擾器 (如果有)
        for jammer in active_jammers:
            jammer_name = jammer.name
            jammer_position = [
                jammer.position_x,
                jammer.position_y,
                jammer.position_z,
            ]
            jammer_orientation = [
                jammer.orientation_x,
                jammer.orientation_y,
                jammer.orientation_z,
            ]
            jammer_power = jammer.power_dbm

            tx_list.append(
                (
                    jammer_name,
                    jammer_position,
                    jammer_orientation,
                    "jammer",
                    jammer_power,
                )
            )
            logger.info(
                f"添加干擾器: {jammer_name}, 位置: {jammer_position}, 方向: {jammer_orientation}, 功率: {jammer_power} dBm"
            )

        # 接收器設置
        receiver = active_receivers[0]  # 已確認有接收器
        rx_config = (
            receiver.name,
            [receiver.position_x, receiver.position_y, receiver.position_z],
        )
        logger.info(f"使用接收器 '{rx_config[0]}' 在位置 {rx_config[1]}")

        # 從 config.py 取得場景路徑
        scene_xml_path = get_scene_xml_file_path(scene_name)
        logger.info(f"從 {scene_xml_path} 加載場景")

        # 參數設置 (從 tf.py 移植)
        tx_array_config = {
            "num_rows": 1,
            "num_cols": 1,
            "vertical_spacing": 0.5,
            "horizontal_spacing": 0.5,
            "pattern": "iso",
            "polarization": "V",
        }
        rx_array_config = tx_array_config

        pathsolver_args = {
            "max_depth": 10,
            "los": True,
            "specular_reflection": True,
            "diffuse_reflection": False,
            "refraction": False,
            "synthetic_array": False,
            "seed": 41,
        }

        n_subcarriers = 1024
        subcarrier_spacing = 30e3
        num_ofdm_symbols = 1024

        # 場景設置
        logger.info("設置場景")
        scene = load_scene(scene_xml_path)
        scene.tx_array = PlanarArray(**tx_array_config)
        scene.rx_array = PlanarArray(**rx_array_config)

        # 清除現有的發射器和接收器
        for name in list(scene.transmitters.keys()) + list(scene.receivers.keys()):
            scene.remove(name)

        # 添加發射器
        logger.info("添加發射器和干擾器")

        def add_tx(scene, name, pos, ori, role, power_dbm):
            tx = SionnaTransmitter(
                name=name, position=pos, orientation=ori, power_dbm=power_dbm
            )
            tx.role = role
            scene.add(tx)
            return tx

        for name, pos, ori, role, p_dbm in tx_list:
            add_tx(scene, name, pos, ori, role, p_dbm)

        # 添加接收器
        rx_name, rx_pos = rx_config
        logger.info(f"添加接收器 '{rx_name}' 在位置 {rx_pos}")
        scene.add(SionnaReceiver(name=rx_name, position=rx_pos))

        # 為所有發射器分配速度
        for name, tx in scene.transmitters.items():
            tx.velocity = [30, 0, 0]

        # 按角色分組發射器
        tx_names = list(scene.transmitters.keys())
        all_txs = [scene.get(n) for n in tx_names]
        idx_des = [
            i for i, tx in enumerate(all_txs) if getattr(tx, "role", None) == "desired"
        ]
        idx_jam = [
            i for i, tx in enumerate(all_txs) if getattr(tx, "role", None) == "jammer"
        ]

        # 計算路徑
        logger.info("計算路徑")
        solver = PathSolver()
        try:
            paths = solver(scene, **pathsolver_args)
        except RuntimeError as e:
            logger.error(f"PathSolver 錯誤: {e}")
            logger.error(
                "嘗試減少 max_depth, max_num_paths_per_src, 或使用更簡單的場景。"
            )
            return False

        # 計算 CFR
        logger.info("計算 CFR")
        freqs = subcarrier_frequencies(n_subcarriers, subcarrier_spacing)
        ofdm_symbol_duration = 1 / subcarrier_spacing

        H_unit = paths.cfr(
            frequencies=freqs,
            sampling_frequency=1 / ofdm_symbol_duration,
            num_time_steps=num_ofdm_symbols,
            normalize_delays=True,
            normalize=False,
            out_type="numpy",
        ).squeeze()  # shape: (num_tx, T, F)

        # 計算 H_all, H_des, H_jam
        logger.info("計算 H_all, H_des, H_jam")
        H_all = H_unit.sum(axis=0)

        # 安全檢查：確保有所需的發射器和干擾器
        H_des = np.zeros_like(H_all)
        if idx_des:
            H_des = H_unit[idx_des].sum(axis=0)

        H_jam = np.zeros_like(H_all)
        if idx_jam:
            H_jam = H_unit[idx_jam].sum(axis=0)

        # 準備繪圖網格
        logger.info("準備繪圖")
        T, F = H_des.shape
        t_axis = np.arange(T)
        f_axis = np.arange(F)
        T_mesh, F_mesh = np.meshgrid(t_axis, f_axis, indexing="ij")

        # 創建圖片並保存
        logger.info("繪製通道響應圖")
        fig = plt.figure(figsize=(18, 5))

        # 子圖 1: H_des
        ax1 = fig.add_subplot(131, projection="3d")
        ax1.plot_surface(
            F_mesh, T_mesh, np.abs(H_des), cmap="viridis", edgecolor="none"
        )
        ax1.set_xlabel("子載波")
        ax1.set_ylabel("OFDM 符號")
        ax1.set_title("‖H_des‖")

        # 子圖 2: H_jam
        ax2 = fig.add_subplot(132, projection="3d")
        ax2.plot_surface(
            F_mesh, T_mesh, np.abs(H_jam), cmap="viridis", edgecolor="none"
        )
        ax2.set_xlabel("子載波")
        ax2.set_ylabel("OFDM 符號")
        ax2.set_title("‖H_jam‖")

        # 子圖 3: H_all
        ax3 = fig.add_subplot(133, projection="3d")
        ax3.plot_surface(
            F_mesh, T_mesh, np.abs(H_all), cmap="viridis", edgecolor="none"
        )
        ax3.set_xlabel("子載波")
        ax3.set_ylabel("OFDM 符號")
        ax3.set_title("‖H_all‖")

        plt.tight_layout()

        # 保存圖片
        logger.info(f"保存通道響應圖到 {output_path}")
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close(fig)

        # 檢查文件是否生成成功
        return verify_output_file(output_path)

    except Exception as e:
        logger.exception(f"生成通道響應圖時發生錯誤: {e}")
        # 確保關閉所有打開的圖表
        plt.close("all")
        return False


# --- 主服務類 ---
class SionnaSimulationService(SimulationServiceInterface):
    """Sionna模擬服務實現"""

    def __init__(self):
        """初始化服務"""
        # 可根據需要在這裡添加初始化邏輯
        pass

    # --- 實現接口定義的方法 ---

    async def generate_empty_scene_image(self, output_path: str) -> bool:
        """生成空場景圖像"""
        logger.info(
            f"SionnaSimulationService: Generating empty scene image at {output_path}"
        )

        # 準備輸出文件
        # For empty scene, the output_path passed from API is relative,
        # and prepare_output_file and subsequent functions handle it.
        prepare_output_file(output_path, "空場景圖像")

        # 嘗試設置 GPU
        _setup_gpu()

        # 設置 pyrender 場景
        pr_scene = _setup_pyrender_scene_from_glb()
        if not pr_scene:
            logger.error("無法設置 pyrender 場景")
            return False

        # 渲染並保存場景
        result = _render_crop_and_save(
            pr_scene,
            output_path,  # Uses the output_path as received
            bg_color_float=SCENE_BACKGROUND_COLOR_RGB,
            render_width=1200,
            render_height=858,
            padding_y=20,
            padding_x=20,
        )

        return verify_output_file(output_path) if result else False

    async def generate_cfr_plot(
        self, session: AsyncSession, output_path: str, scene_name: str = "nycu"
    ) -> bool:
        """生成通道頻率響應(CFR)圖像"""
        logger.info(
            f"SionnaSimulationService: Calling global generate_cfr_plot, output_path: {output_path}, scene: {scene_name}"
        )
        return await generate_cfr_plot(
            session=session, output_path=output_path, scene_name=scene_name
        )

    async def generate_sinr_map(
        self,
        session: AsyncSession,
        output_path: str,  # This is an absolute path from config
        scene_name: str = "nycu",
        sinr_vmin: float = -40.0,
        sinr_vmax: float = 0.0,
        cell_size: float = 1.0,
        samples_per_tx: int = 10**7,
    ) -> bool:
        """生成SINR地圖"""
        logger.info(
            f"SionnaSimulationService: Calling global generate_sinr_map, output_path: {output_path}, scene: {scene_name}"
        )
        return await generate_sinr_map(
            session=session,
            output_path=output_path,
            scene_name=scene_name,
            sinr_vmin=sinr_vmin,
            sinr_vmax=sinr_vmax,
            cell_size=cell_size,
            samples_per_tx=samples_per_tx,
        )

    async def generate_doppler_plots(
        self, session: AsyncSession, output_path: str, scene_name: str = "nycu"
    ) -> bool:
        """生成延遲多普勒圖"""
        logger.info(
            f"SionnaSimulationService: Calling global generate_doppler_plots, output_path: {output_path}, scene: {scene_name}"
        )
        return await generate_doppler_plots(
            session=session, output_path=output_path, scene_name=scene_name
        )

    async def generate_channel_response_plots(
        self, session: AsyncSession, output_path: str, scene_name: str = "nycu"
    ) -> bool:
        """生成通道響應圖"""
        logger.info(
            f"SionnaSimulationService: Calling global generate_channel_response_plots, output_path: {output_path}, scene: {scene_name}"
        )
        return await generate_channel_response_plots(
            session=session, output_path=output_path, scene_name=scene_name
        )

    async def run_simulation(
        self, session: AsyncSession, params: SimulationParameters
    ) -> Dict[str, Any]:
        """執行通用模擬"""
        logger.info(f"Running simulation of type: {params.simulation_type}")

        result = {"success": False, "result_path": None, "error_message": None}

        try:
            # 根據模擬類型執行不同的模擬
            if params.simulation_type == "cfr":
                output_path = str(CFR_PLOT_IMAGE_PATH)
                success = await self.generate_cfr_plot(session, output_path)
                result["result_path"] = output_path
                result["success"] = success

            elif params.simulation_type == "sinr_map":
                output_path = str(SINR_MAP_IMAGE_PATH)
                success = await self.generate_sinr_map(
                    session,
                    output_path,
                    params.sinr_vmin or -40.0,
                    params.sinr_vmax or 0.0,
                    params.cell_size or 1.0,
                    params.samples_per_tx or 10**7,
                )
                result["result_path"] = output_path
                result["success"] = success

            elif params.simulation_type == "doppler":
                output_path = str(DOPPLER_IMAGE_PATH)
                success = await self.generate_doppler_plots(session, output_path)
                result["result_path"] = output_path
                result["success"] = success

            elif params.simulation_type == "channel_response":
                output_path = str(CHANNEL_RESPONSE_IMAGE_PATH)
                success = await self.generate_channel_response_plots(
                    session, output_path
                )
                result["result_path"] = output_path
                result["success"] = success

            else:
                logger.error(f"不支援的模擬類型: {params.simulation_type}")
                result["error_message"] = f"不支援的模擬類型: {params.simulation_type}"

        except Exception as e:
            logger.error(f"執行模擬時發生錯誤: {str(e)}", exc_info=True)
            result["error_message"] = f"執行模擬時發生錯誤: {str(e)}"

        return result


# 創建服務實例
sionna_service = SionnaSimulationService()
