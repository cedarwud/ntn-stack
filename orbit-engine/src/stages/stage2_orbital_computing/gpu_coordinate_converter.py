#!/usr/bin/env python3
"""
GPU座標轉換器 - 並行TEME→ITRF→WGS84轉換
使用GPU加速座標系統轉換，大幅提升階段二性能

🎯 目標: 1,744,160次座標轉換從~100秒降至~15秒
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional

# GPU計算庫 (可選導入)
try:
    import cupy as cp
    CUPY_AVAILABLE = True
    CupyArray = cp.ndarray
except ImportError:
    cp = None
    CUPY_AVAILABLE = False
    CupyArray = np.ndarray  # 回退到numpy類型
import time
import logging
from datetime import datetime, timezone
from multiprocessing import Pool, cpu_count
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CoordinateConversionBatch:
    """座標轉換批次數據"""
    positions_teme: np.ndarray  # TEME座標 (N, 3)
    times: np.ndarray          # 時間戳
    batch_id: int
    size: int

class GPUCoordinateConverter:
    """GPU加速座標轉換器"""

    def __init__(self, gpu_batch_size: int = 5000):
        self.gpu_batch_size = gpu_batch_size
        self.gpu_available = self._check_gpu_capability()
        self.cpu_workers = cpu_count()

        # 預計算常用參數
        self._precompute_constants()

        logger.info(f"🌐 GPU座標轉換器初始化:")
        logger.info(f"  - GPU可用: {self.gpu_available}")
        logger.info(f"  - 批次大小: {self.gpu_batch_size}")
        logger.info(f"  - CPU回退進程: {self.cpu_workers}")

    def _check_gpu_capability(self) -> bool:
        """檢查GPU計算能力"""
        if not CUPY_AVAILABLE:
            logger.warning("⚠️ CuPy未安裝，將使用CPU並行")
            return False

        try:
            device = cp.cuda.Device()
            compute_capability = device.compute_capability
            memory_gb = device.mem_info[1] / (1024**3)

            logger.info(f"✅ 檢測到GPU: 計算能力 {compute_capability}, 記憶體 {memory_gb:.1f}GB")
            return memory_gb >= 2.0  # 至少需要2GB顯存

        except Exception as e:
            logger.warning(f"⚠️ GPU不可用，將使用CPU並行: {e}")
            return False

    def _precompute_constants(self):
        """預計算地球參數常數"""
        # WGS84橢球參數
        self.WGS84_A = 6378137.0         # 半長軸 (米)
        self.WGS84_F = 1/298.257223563   # 扁率
        self.WGS84_E2 = 2*self.WGS84_F - self.WGS84_F**2  # 第一偏心率平方

        # 地球自轉參數 (簡化)
        self.EARTH_ROTATION_RATE = 7.2921159e-5  # rad/s

    def batch_convert_coordinates(self, orbital_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        批次座標轉換主函數

        輸入: SGP4計算結果 (TEME座標)
        輸出: 轉換後的結果 (WGS84座標)
        """
        start_time = time.time()
        total_positions = sum(len(result.get('positions', [])) for result in orbital_results.values())

        logger.info(f"🌐 開始批次座標轉換:")
        logger.info(f"  - 衛星數: {len(orbital_results)}")
        logger.info(f"  - 總位置數: {total_positions:,}")

        if self.gpu_available and total_positions > 10000:
            converted_results = self._gpu_batch_convert(orbital_results)
            method = "GPU加速"
        else:
            converted_results = self._cpu_parallel_convert(orbital_results)
            method = "CPU並行"

        elapsed_time = time.time() - start_time
        conversions_per_second = total_positions / elapsed_time

        logger.info(f"✅ 座標轉換完成 ({method}):")
        logger.info(f"  - 耗時: {elapsed_time:.2f}秒")
        logger.info(f"  - 轉換速度: {conversions_per_second:,.0f} 次/秒")

        return converted_results

    def _gpu_batch_convert(self, orbital_results: Dict[str, Any]) -> Dict[str, Any]:
        """GPU批次座標轉換"""
        logger.info("🔥 使用GPU加速座標轉換...")

        # 準備GPU批次
        batches = self._prepare_conversion_batches(orbital_results)
        converted_results = {}

        for i, (batch_data, satellite_mapping) in enumerate(batches):
            logger.info(f"🎯 處理GPU批次 {i+1}/{len(batches)} "
                       f"({batch_data.size}個位置)")

            # GPU轉換
            converted_batch = self._process_gpu_conversion_batch(batch_data)

            # 重新組裝結果
            self._reassemble_batch_results(converted_batch, satellite_mapping, converted_results)

        return converted_results

    def _prepare_conversion_batches(self, orbital_results: Dict[str, Any]) -> List[Tuple[CoordinateConversionBatch, Dict]]:
        """準備座標轉換批次"""
        batches = []
        current_positions = []
        current_times = []
        current_mapping = []  # (satellite_id, position_index)

        position_count = 0

        for sat_id, result in orbital_results.items():
            positions = np.array(result.get('positions', []))
            times = result.get('times', [])

            if len(positions) == 0:
                continue

            for i, (pos, time_val) in enumerate(zip(positions, times)):
                current_positions.append(pos)
                current_times.append(time_val)
                current_mapping.append((sat_id, i))
                position_count += 1

                # 當達到批次大小時創建批次
                if position_count >= self.gpu_batch_size:
                    batch = self._create_conversion_batch(
                        current_positions, current_times, len(batches)
                    )
                    mapping = dict(enumerate(current_mapping))

                    batches.append((batch, mapping))

                    # 重置
                    current_positions = []
                    current_times = []
                    current_mapping = []
                    position_count = 0

        # 處理最後一個批次
        if current_positions:
            batch = self._create_conversion_batch(
                current_positions, current_times, len(batches)
            )
            mapping = dict(enumerate(current_mapping))
            batches.append((batch, mapping))

        return batches

    def _create_conversion_batch(self, positions: List, times: List, batch_id: int) -> CoordinateConversionBatch:
        """創建座標轉換批次"""
        positions_array = np.array(positions)
        times_array = np.array(times)

        return CoordinateConversionBatch(
            positions_teme=positions_array,
            times=times_array,
            batch_id=batch_id,
            size=len(positions)
        )

    def _process_gpu_conversion_batch(self, batch: CoordinateConversionBatch) -> np.ndarray:
        """處理GPU座標轉換批次"""
        if not CUPY_AVAILABLE:
            return self._cpu_teme_to_wgs84_batch(batch.positions_teme, batch.times)

        try:

            # 將數據傳輸到GPU
            gpu_positions = cp.array(batch.positions_teme)  # (N, 3)
            gpu_times = cp.array(batch.times)

            # GPU並行座標轉換
            gpu_results = self._gpu_teme_to_wgs84(gpu_positions, gpu_times)

            # 轉回CPU
            results_cpu = cp.asnumpy(gpu_results)

            return results_cpu

        except Exception as e:
            logger.error(f"❌ GPU座標轉換失敗: {e}")
            # 回退到CPU
            return self._cpu_teme_to_wgs84_batch(batch.positions_teme, batch.times)

    def _gpu_teme_to_wgs84(self, positions: CupyArray, times: CupyArray) -> CupyArray:
        """
        GPU並行TEME→WGS84座標轉換

        注意: 這是簡化實現，實際需要完整的地球自轉和極移參數
        """
        # 批次大小
        N = positions.shape[0]

        # Step 1: TEME → ITRF (簡化地球自轉)
        # 計算格林威治恆星時 (簡化)
        gst_rad = self._gpu_compute_gst(times)  # (N,)

        # 創建旋轉矩陣
        cos_gst = cp.cos(gst_rad)  # (N,)
        sin_gst = cp.sin(gst_rad)  # (N,)

        # 旋轉矩陣應用 (Z軸旋轉)
        x_itrf = cos_gst * positions[:, 0] + sin_gst * positions[:, 1]
        y_itrf = -sin_gst * positions[:, 0] + cos_gst * positions[:, 1]
        z_itrf = positions[:, 2]

        itrf_positions = cp.stack([x_itrf, y_itrf, z_itrf], axis=1)  # (N, 3)

        # Step 2: ITRF → WGS84地理座標
        wgs84_coords = self._gpu_cartesian_to_geodetic(itrf_positions)

        return wgs84_coords

    def _gpu_compute_gst(self, times: CupyArray) -> CupyArray:
        """GPU計算格林威治恆星時 (簡化版本)"""
        # 注意: 這是高度簡化的實現，實際需要IAU標準算法

        # 假設times是Julian Day
        # 簡化GST計算
        t_ut1 = times - 2451545.0  # 自J2000.0的天數

        # 簡化公式 (實際需要更精確的計算)
        gst_hours = 18.697374558 + 24.06570982441908 * t_ut1
        gst_rad = (gst_hours % 24.0) * (cp.pi / 12.0)

        return gst_rad

    def _gpu_cartesian_to_geodetic(self, positions: CupyArray) -> CupyArray:
        """GPU並行笛卡爾座標→大地座標轉換"""
        x = positions[:, 0]
        y = positions[:, 1]
        z = positions[:, 2]

        # 經度 (簡單)
        longitude = cp.arctan2(y, x) * 180.0 / cp.pi

        # 距離計算
        p = cp.sqrt(x*x + y*y)

        # 緯度迭代計算 (簡化版本)
        # 實際需要更精確的迭代算法
        latitude = cp.arctan2(z, p) * 180.0 / cp.pi

        # 高度 (簡化)
        altitude = cp.sqrt(x*x + y*y + z*z) - self.WGS84_A

        # 返回 [latitude, longitude, altitude]
        result = cp.stack([latitude, longitude, altitude], axis=1)
        return result

    def _cpu_parallel_convert(self, orbital_results: Dict[str, Any]) -> Dict[str, Any]:
        """CPU並行座標轉換"""
        logger.info(f"💻 使用CPU並行座標轉換 ({self.cpu_workers}進程)...")

        # 將衛星分組
        satellite_items = list(orbital_results.items())
        chunk_size = max(1, len(satellite_items) // self.cpu_workers)
        chunks = [
            satellite_items[i:i + chunk_size]
            for i in range(0, len(satellite_items), chunk_size)
        ]

        all_results = {}

        with ProcessPoolExecutor(max_workers=self.cpu_workers) as executor:
            future_to_chunk = {
                executor.submit(self._process_cpu_conversion_chunk, chunk): chunk
                for chunk in chunks
            }

            for future in as_completed(future_to_chunk):
                try:
                    chunk_results = future.result()
                    all_results.update(chunk_results)
                except Exception as e:
                    logger.error(f"❌ CPU座標轉換批次失敗: {e}")

        return all_results

    @staticmethod
    def _process_cpu_conversion_chunk(satellite_chunk: List[Tuple[str, Dict]]) -> Dict[str, Any]:
        """CPU處理座標轉換塊"""
        results = {}

        for sat_id, result in satellite_chunk:
            try:
                positions = np.array(result.get('positions', []))
                times = result.get('times', [])

                if len(positions) == 0:
                    results[sat_id] = result
                    continue

                # 進行座標轉換
                converted_positions = []
                for pos, time_val in zip(positions, times):
                    wgs84_coord = GPUCoordinateConverter._cpu_teme_to_wgs84(pos, time_val)
                    converted_positions.append(wgs84_coord)

                # 更新結果
                updated_result = result.copy()
                updated_result['positions_wgs84'] = converted_positions
                updated_result['coordinate_system'] = 'WGS84'
                results[sat_id] = updated_result

            except Exception as e:
                logger.warning(f"⚠️ 衛星 {sat_id} 座標轉換失敗: {e}")
                results[sat_id] = result  # 保留原始結果

        return results

    @staticmethod
    def _cpu_teme_to_wgs84(position: np.ndarray, time_val: Any) -> List[float]:
        """CPU單點座標轉換 (簡化實現)"""
        # 這是簡化的座標轉換，實際需要使用完整的座標轉換庫

        x, y, z = position

        # 簡化的地理座標計算
        longitude = np.arctan2(y, x) * 180.0 / np.pi
        latitude = np.arctan2(z, np.sqrt(x*x + y*y)) * 180.0 / np.pi
        altitude = np.sqrt(x*x + y*y + z*z) - 6378137.0  # WGS84半徑

        return [latitude, longitude, altitude]

    @staticmethod
    def _cpu_teme_to_wgs84_batch(positions: np.ndarray, times: np.ndarray) -> np.ndarray:
        """CPU批次座標轉換"""
        results = []
        for pos, time_val in zip(positions, times):
            wgs84 = GPUCoordinateConverter._cpu_teme_to_wgs84(pos, time_val)
            results.append(wgs84)
        return np.array(results)

    def _reassemble_batch_results(self, converted_batch: np.ndarray,
                                 satellite_mapping: Dict, results: Dict[str, Any]):
        """重新組裝批次結果"""
        for batch_idx, (sat_id, pos_idx) in satellite_mapping.items():
            if sat_id not in results:
                results[sat_id] = {
                    'satellite_id': sat_id,
                    'positions_wgs84': [],
                    'coordinate_system': 'WGS84'
                }

            # 添加轉換後的座標
            wgs84_coord = converted_batch[batch_idx].tolist()
            results[sat_id]['positions_wgs84'].append(wgs84_coord)


def create_gpu_coordinate_converter(gpu_batch_size: int = 5000) -> GPUCoordinateConverter:
    """建立GPU座標轉換器"""
    return GPUCoordinateConverter(gpu_batch_size=gpu_batch_size)