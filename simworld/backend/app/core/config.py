import os
import logging
from pathlib import Path  # 確保導入 Path

# --- Logging Setup ---
# (可以將 logging level 等也設為可配置)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# --- Environment Variables & Basic Config ---
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://user:password@postgis/app"
)  # 提供預設值以防萬一
if not DATABASE_URL:
    logger.critical(
        "DATABASE_URL environment variable not set and no default provided!"
    )
    raise ValueError("DATABASE_URL environment variable not set!")

# 檢查 URL 是否符合 asyncpg
if not DATABASE_URL.startswith("postgresql+asyncpg"):
    logger.warning(
        f"DATABASE_URL does not start with 'postgresql+asyncpg://'. Received: {DATABASE_URL}. Ensure it's correctly configured for async."
    )

# --- Path Configuration (using pathlib) ---
# 在容器內，/app 就是 backend 目錄的根
# config.py 位於 /app/app/core
CORE_DIR = Path(__file__).resolve().parent  # /app/app/core
APP_DIR = CORE_DIR.parent  # /app/app
# BACKEND_DIR = APP_DIR.parent              # 不需要再往上找，/app 就是後端根目錄
# PROJECT_ROOT = BACKEND_DIR.parent

# 靜態文件應該在 /app/app/static 下，因為 volume mount 是 ./backend:/app
STATIC_DIR = APP_DIR / "static"  # Correct path: /app/app/static
MODELS_DIR = STATIC_DIR / "models"  # Correct path: /app/app/static/models
STATIC_IMAGES_DIR = STATIC_DIR / "images"  # Correct path: /app/app/static/images
SCENE_DIR = STATIC_DIR / "scene"  # 新增: 場景總目錄路徑
NYCU_DIR = SCENE_DIR / "NYCU"  # 更新: NYCU 目錄現在在 scene 子目錄下

# 建立目錄
# STATIC_DIR.mkdir(parents=True, exist_ok=True) # 目錄應該由 volume mount 提供，不需在 config 創建
MODELS_DIR.mkdir(parents=True, exist_ok=True)  # 但確保子目錄存在是好的
STATIC_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
SCENE_DIR.mkdir(parents=True, exist_ok=True)  # 新增: 確保場景總目錄存在
NYCU_DIR.mkdir(parents=True, exist_ok=True)  # 確保 NYCU 場景目錄存在

# 定義 GLB 和 XML 路徑 (基於修正後的 SCENE_DIR 和 NYCU_DIR)
NYCU_GLB_PATH = NYCU_DIR / "NYCU.glb"
NYCU_XML_PATH = NYCU_DIR / "NYCU.xml"  # NYCU.xml 文件路徑


# 通用場景路徑函數，支援多種場景（如 'NYCU', 'Lotus' 等）
def get_scene_dir(scene_name: str) -> Path:
    return SCENE_DIR / scene_name


def get_scene_model_path(scene_name: str, model_name: str = None) -> Path:
    """獲取場景模型路徑，若未指定模型名稱則使用場景名稱作為模型名稱"""
    if model_name is None:
        model_name = scene_name
    return get_scene_dir(scene_name) / f"{model_name}.glb"


def get_scene_xml_path(scene_name: str, xml_name: str = None) -> Path:
    """獲取場景XML路徑，若未指定XML名稱則使用場景名稱作為XML名稱"""
    if xml_name is None:
        xml_name = scene_name
    return get_scene_dir(scene_name) / f"{xml_name}.xml"


# 舊版 OUTPUT_DIR，保持定義以兼容可能還在使用的地方，但指向新位置
OUTPUT_DIR = STATIC_IMAGES_DIR

# 圖片檔案完整路徑 (使用 Path 對象)
CFR_PLOT_IMAGE_PATH = OUTPUT_DIR / "cfr_plot.png"  # CFR 圖像路徑
SINR_MAP_IMAGE_PATH = OUTPUT_DIR / "sinr_map.png"  # SINR 地圖路徑
# 延遲多普勒圖路徑
DOPPLER_IMAGE_PATH = OUTPUT_DIR / "delay_doppler.png"  # 延遲多普勒圖路徑
# 通道響應圖路徑
CHANNEL_RESPONSE_IMAGE_PATH = OUTPUT_DIR / "channel_response_plots.png"
logger.info(f"Time-Frequency Image Path (in container): {CHANNEL_RESPONSE_IMAGE_PATH}")

# logger.info(f"Project Root (estimated): {PROJECT_ROOT}") # 不再需要
logger.info(f"Static Directory (in container): {STATIC_DIR}")
logger.info(f"Models Directory (in container): {MODELS_DIR}")
logger.info(f"Static Images Directory (in container): {STATIC_IMAGES_DIR}")
logger.info(f"NYCU Directory (in container): {NYCU_DIR}")  # 新增: 記錄 NYCU 目錄
logger.info(f"NYCU GLB Path (in container): {NYCU_GLB_PATH}")
logger.info(
    f"NYCU XML Path (in container): {NYCU_XML_PATH}"
)  # 新增: 記錄 NYCU.xml 路徑
logger.info(f"CFR Plot Image Path (in container): {CFR_PLOT_IMAGE_PATH}")
logger.info(f"SINR Map Image Path (in container): {SINR_MAP_IMAGE_PATH}")
logger.info(f"DOPPLER Image Path (in container): {DOPPLER_IMAGE_PATH}")


# --- Default Observer Configuration ---
# Helper function to get float from env or return None
def get_float_env(var_name):
    value = os.getenv(var_name)
    if value is not None:
        try:
            return float(value)
        except ValueError:
            logger.warning(
                f"Environment variable {var_name} ('{value}') is not a valid float. Ignoring."
            )
    return None


# Observer Latitude
DEFAULT_OBSERVER_LAT = get_float_env("OBSERVER_LAT")
if DEFAULT_OBSERVER_LAT is None:
    # TODO: Replace with actual database lookup if OBSERVER_LAT is not in env
    logger.info(
        "OBSERVER_LAT not found in environment variables. Using placeholder/database fallback."
    )
    DEFAULT_OBSERVER_LAT = 24.785_278  # Example: NYCU, replace with DB lookup
    # Example DB lookup: default_observer_lat = db_service.get_default_observer_lat()

# Observer Longitude
DEFAULT_OBSERVER_LON = get_float_env("OBSERVER_LON")
if DEFAULT_OBSERVER_LON is None:
    # TODO: Replace with actual database lookup if OBSERVER_LON is not in env
    logger.info(
        "OBSERVER_LON not found in environment variables. Using placeholder/database fallback."
    )
    DEFAULT_OBSERVER_LON = 120.997_222  # Example: NYCU, replace with DB lookup
    # Example DB lookup: default_observer_lon = db_service.get_default_observer_lon()

# Observer Altitude (in meters, defaults to 0 if not specified)
DEFAULT_OBSERVER_ALT = get_float_env("OBSERVER_ALT")
if DEFAULT_OBSERVER_ALT is None:
    # TODO: Replace with actual database lookup if OBSERVER_ALT is not in env
    logger.info(
        "OBSERVER_ALT not found in environment variables. Using placeholder/database fallback (0.0m)."
    )
    DEFAULT_OBSERVER_ALT = 0.0  # Default to sea level if not specified or found in DB
    # Example DB lookup: default_observer_alt = db_service.get_default_observer_alt(default_value=0.0)

logger.info(
    f"Default Observer: LAT={DEFAULT_OBSERVER_LAT}, LON={DEFAULT_OBSERVER_LON}, ALT={DEFAULT_OBSERVER_ALT}m"
)


# --- GPU/CPU Configuration ---
# (這部分邏輯也可以放在這裡，或在需要時執行)
def configure_gpu_cpu():
    import tensorflow as tf

    os.environ["TF_CPP_MIN_LOG_LEVEL"] = os.getenv("TF_CPP_MIN_LOG_LEVEL", "3")
    tf.get_logger().setLevel("ERROR")  # Keep TF logs quiet unless necessary
    cuda_visible_devices = os.getenv("CUDA_VISIBLE_DEVICES")
    force_cpu = cuda_visible_devices == "-1"
    logger.info(f"Detected CUDA_VISIBLE_DEVICES='{cuda_visible_devices}'")
    if force_cpu:
        logger.info("CPU usage forced by CUDA_VISIBLE_DEVICES=-1.")
        # Explicitly disable GPU visibility in TensorFlow
        tf.config.set_visible_devices([], "GPU")
    else:
        gpus = tf.config.list_physical_devices("GPU")
        if gpus:
            try:
                # Prefer setting memory growth on all visible GPUs if possible
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                logger.info(
                    f"Configured Visible GPU(s): {[gpu.name for gpu in gpus]} with memory growth."
                )
            except RuntimeError as e:
                logger.error(
                    f"Error configuring GPU memory growth: {e}. Check TensorFlow/CUDA setup.",
                    exc_info=True,
                )
            except Exception as e:
                logger.error(
                    f"An unexpected error occurred during GPU configuration: {e}",
                    exc_info=True,
                )

        else:
            logger.info("No compatible GPU detected by TensorFlow, will use CPU.")
            # Ensure TF doesn't see any GPUs if none are intended
            tf.config.set_visible_devices([], "GPU")


# --- Matplotlib Backend ---
# (也可以放在這裡或在使用前設定)
def configure_matplotlib():
    import matplotlib

    try:
        matplotlib.use("Agg")
        logger.info("Matplotlib backend set to Agg.")
    except Exception as e:
        logger.warning(f"Failed to set Matplotlib backend to Agg: {e}", exc_info=True)


# 在需要時呼叫設定函數，例如在 lifespan 或 main.py 頂部
# configure_gpu_cpu()
# configure_matplotlib()
