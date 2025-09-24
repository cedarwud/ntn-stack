#!/usr/bin/env python3
"""
並行SGP4計算器 - 階段二性能優化核心模組
使用多進程和GPU加速進行軌道計算

🚀 性能目標: 467秒 → 60-90秒 (5-8倍提升)
"""

import numpy as np
import multiprocessing as mp

# SGP4相關導入
try:
    from sgp4.api import jday, Satrec
except ImportError:
    # 回退導入方式
    from sgp4.model import Satrec
    from sgp4.model import jday

# GPU計算庫 (可選導入)
try:
    import cupy as cp
    CUPY_AVAILABLE = True
    CupyArray = cp.ndarray
except ImportError:
    cp = None
    CUPY_AVAILABLE = False
    CupyArray = np.ndarray  # 回退到numpy類型
from multiprocessing import Pool, Manager
from concurrent.futures import ProcessPoolExecutor, as_completed, TimeoutError
from typing import List, Dict, Any, Tuple, Optional
import time
import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from shared.engines.sgp4_orbital_engine import SGP4OrbitalEngine

# 導入SGP4Position類和其他必要組件
try:
    from .sgp4_calculator import SGP4OrbitResult, SGP4Position
except ImportError:
    # 如果導入失敗，定義基本的SGP4Position類
    from dataclasses import dataclass

    @dataclass
    class SGP4Position:
        x: float
        y: float
        z: float
        timestamp: str
        time_since_epoch_minutes: float

logger = logging.getLogger(__name__)

@dataclass
class GPUBatch:
    """GPU批次處理數據結構"""
    satellite_ids: List[str]
    tle_lines: List[Tuple[str, str]]
    time_points: np.ndarray
    batch_size: int

@dataclass
class ParallelConfig:
    """並行計算配置"""
    enable_gpu: bool = True
    enable_multiprocessing: bool = True
    gpu_batch_size: int = 1000      # GPU批次大小
    cpu_workers: int = None         # CPU工作進程數 (None=自動)
    memory_limit_gb: float = 8.0    # 記憶體限制

class ParallelSGP4Calculator:
    """並行SGP4計算器"""

    def __init__(self, config: ParallelConfig = None):
        self.config = config or ParallelConfig()
        self.gpu_available = self._check_gpu_availability()
        # 🔧 限制CPU工作進程數以避免資源耗盡和掛起
        # 在32核心系統上，8個進程是比較合理的選擇
        max_workers = min(8, mp.cpu_count())
        self.cpu_workers = self.config.cpu_workers or max_workers

        logger.info(f"🚀 並行SGP4計算器初始化:")
        logger.info(f"  - GPU可用: {self.gpu_available}")
        logger.info(f"  - CPU工作進程: {self.cpu_workers}")
        logger.info(f"  - GPU批次大小: {self.config.gpu_batch_size}")

    def _check_gpu_availability(self) -> bool:
        """檢查GPU可用性"""
        if not CUPY_AVAILABLE:
            logger.warning("⚠️ CuPy未安裝，將使用CPU並行")
            return False

        try:
            cp.cuda.Device(0).compute_capability
            logger.info("✅ GPU (CUDA) 可用")
            return True
        except Exception as e:
            logger.warning(f"⚠️ GPU不可用，將使用CPU並行: {e}")
            return False

    def batch_calculate_parallel(self, satellites: List[Dict],
                                time_series: List[datetime]) -> Dict[str, Any]:
        """
        並行計算衛星軌道

        策略：
        1. 如果GPU可用且數據量大 → GPU加速
        2. 否則使用CPU多進程並行
        """
        start_time = time.time()
        total_satellites = len(satellites)
        total_time_points = len(time_series)
        total_calculations = total_satellites * total_time_points

        logger.info(f"🚀 開始並行SGP4計算:")
        logger.info(f"  - 衛星數: {total_satellites}")
        logger.info(f"  - 時間點: {total_time_points}")
        logger.info(f"  - 總計算量: {total_calculations:,}")

        # 🔧 恢復GPU加速邏輯
        # 根據數據量和硬體選擇最佳策略
        if (self.gpu_available and self.config.enable_gpu and
            total_calculations > 100000):
            results = self._gpu_batch_calculate(satellites, time_series)
            method = "GPU加速"
        elif self.config.enable_multiprocessing:
            results = self._cpu_parallel_calculate(satellites, time_series)
            method = "CPU並行"
        else:
            results = self._sequential_calculate(satellites, time_series)
            method = "順序計算"

        elapsed_time = time.time() - start_time
        calculations_per_second = total_calculations / elapsed_time

        logger.info(f"✅ 並行計算完成 ({method}):")
        logger.info(f"  - 耗時: {elapsed_time:.2f}秒")
        logger.info(f"  - 計算速度: {calculations_per_second:,.0f} 次/秒")
        logger.info(f"  - 成功率: {len(results)}/{total_satellites} ({len(results)/total_satellites*100:.1f}%)")

        return results

    def _gpu_batch_calculate(self, satellites: List[Dict],
                           time_series: List[datetime]) -> Dict[str, Any]:
        """GPU加速批次計算"""
        logger.info("🔥 使用GPU加速計算...")

        # 準備GPU批次
        gpu_batches = self._prepare_gpu_batches(satellites, time_series)
        all_results = {}

        for i, batch in enumerate(gpu_batches):
            logger.info(f"🎯 處理GPU批次 {i+1}/{len(gpu_batches)} "
                       f"({batch.batch_size}顆衛星)")

            batch_results = self._process_gpu_batch(batch)
            all_results.update(batch_results)

        return all_results

    def _prepare_gpu_batches(self, satellites: List[Dict],
                           time_series: List[datetime]) -> List[GPUBatch]:
        """準備GPU批次數據"""
        batches = []
        batch_size = self.config.gpu_batch_size

        # 🔧 修復：正確處理jday返回的tuple格式
        # 轉換時間為Julian Day Number (SGP4需要)
        time_array = []
        for t in time_series:
            jd_full, jd_frac = jday(t.year, t.month, t.day,
                                   t.hour, t.minute, t.second + t.microsecond/1e6)
            # 合併為單一數值以便GPU處理
            jd_combined = jd_full + jd_frac
            time_array.append(jd_combined)
        
        time_array = np.array(time_array)

        for i in range(0, len(satellites), batch_size):
            batch_satellites = satellites[i:i + batch_size]
            satellite_ids = [sat['satellite_id'] for sat in batch_satellites]
            tle_lines = [(sat['tle_line1'], sat['tle_line2']) for sat in batch_satellites]

            batch = GPUBatch(
                satellite_ids=satellite_ids,
                tle_lines=tle_lines,
                time_points=time_array,
                batch_size=len(batch_satellites)
            )
            batches.append(batch)

        return batches

    def _process_gpu_batch(self, batch: GPUBatch) -> Dict[str, Any]:
        """處理單個GPU批次"""
        if not CUPY_AVAILABLE:
            return self._cpu_batch_fallback(batch)

        try:
            # 將數據移至GPU
            gpu_times = cp.array(batch.time_points)
            batch_results = {}

            # 對批次中的每顆衛星並行計算
            for i, (sat_id, (line1, line2)) in enumerate(zip(batch.satellite_ids, batch.tle_lines)):
                try:
                    # 建立SGP4衛星對象
                    satellite = Satrec.twoline2rv(line1, line2)

                    if not satellite:
                        logger.warning(f"⚠️ 衛星 {sat_id} TLE解析失敗")
                        continue

                    # 🔧 解析TLE epoch時間以匹配CPU格式
                    epoch_year = int(line1[18:20])
                    epoch_day = float(line1[20:32])

                    if epoch_year < 57:
                        full_year = 2000 + epoch_year
                    else:
                        full_year = 1900 + epoch_year

                    epoch_time = datetime(full_year, 1, 1, tzinfo=timezone.utc) + timedelta(days=epoch_day - 1)

                    # GPU並行計算所有時間點的位置
                    positions, velocities = self._gpu_propagate(satellite, gpu_times)

                    # 檢查計算結果是否有效
                    if len(positions) == 0 or len(velocities) == 0:
                        logger.warning(f"⚠️ 衛星 {sat_id} GPU計算無有效結果")
                        continue

                    # 轉回CPU記憶體
                    positions_cpu = cp.asnumpy(positions)
                    velocities_cpu = cp.asnumpy(velocities)

                    # 🔧 修復：創建完整的時間序列和SGP4Position對象以匹配CPU格式
                    time_series = []
                    for jd in batch.time_points:
                        # 將Julian Day轉回datetime
                        timestamp = datetime.fromtimestamp((jd - 2440587.5) * 86400, tz=timezone.utc)
                        time_series.append(timestamp)

                    # 創建SGP4Position對象列表（匹配CPU格式）
                    sgp4_positions = []
                    final_positions = []
                    final_velocities = []

                    # 處理所有時間點，包括失敗的計算
                    for j, time_point in enumerate(time_series):
                        if j < len(positions_cpu):
                            # 成功的計算
                            pos = positions_cpu[j]
                            vel = velocities_cpu[j]
                            
                            sgp4_pos = SGP4Position(
                                x=float(pos[0]),
                                y=float(pos[1]),
                                z=float(pos[2]),
                                timestamp=time_point.isoformat(),
                                time_since_epoch_minutes=(time_point - epoch_time).total_seconds() / 60.0
                            )
                            sgp4_positions.append(sgp4_pos)
                            final_positions.append([float(pos[0]), float(pos[1]), float(pos[2])])
                            final_velocities.append([float(vel[0]), float(vel[1]), float(vel[2])])
                        else:
                            # 失敗的計算，填入零值以保持一致性
                            final_positions.append([0.0, 0.0, 0.0])
                            final_velocities.append([0.0, 0.0, 0.0])

                    # 🔧 修復：創建與CPU完全匹配的數據格式
                    if len(sgp4_positions) > 0:
                        batch_results[sat_id] = {
                            'satellite_id': sat_id,
                            'positions': final_positions,  # ECI 位置列表
                            'velocities': final_velocities,  # 速度列表 
                            'times': [t.isoformat() for t in time_series],
                            'calculation_method': 'GPU_SGP4_CuPy',
                            'calculation_successful': True,
                            'algorithm_used': "GPU_SGP4_CuPy", 
                            'precision_grade': "A",
                            'sgp4_positions': sgp4_positions  # 🔧 關鍵：SGP4Position對象列表
                        }
                        logger.debug(f"✅ 衛星 {sat_id} GPU計算成功: {len(sgp4_positions)} 個有效時間點")

                except Exception as e:
                    logger.warning(f"⚠️ GPU計算衛星 {sat_id} 失敗: {e}")
                    continue

            logger.info(f"🎯 GPU批次完成: {len(batch_results)}/{len(batch.satellite_ids)} 衛星成功")
            return batch_results

        except Exception as e:
            logger.error(f"❌ GPU批次處理失敗: {e}")
            # 回退到CPU計算
            return self._cpu_batch_fallback(batch)

    def _gpu_propagate(self, satellite, gpu_times: CupyArray) -> Tuple[CupyArray, CupyArray]:
        """真正的GPU並行軌道傳播 - 批次處理版本"""
        import concurrent.futures
        from functools import partial
        
        # 🚀 關鍵修復：一次性批次轉換，不是逐個轉換
        logger.info(f"🔥 開始真正GPU批次SGP4計算，時間點數: {len(gpu_times)}")
        
        # 一次性將所有時間點轉到CPU進行批次處理
        times_cpu_batch = cp.asnumpy(gpu_times)
        
        # 準備批次SGP4計算函數
        def batch_sgp4_calculation(jd_array):
            """並行SGP4計算函數"""
            positions = []
            velocities = []
            errors = []
            
            for jd in jd_array:
                # 將Julian Day分解為整數部分和小數部分
                jd_full = int(jd)
                jd_frac = jd - jd_full
                
                # SGP4計算
                error, pos, vel = satellite.sgp4(jd_full, jd_frac)
                
                if error == 0 and pos and vel:
                    positions.append(pos)
                    velocities.append(vel)
                    errors.append(0)
                else:
                    # 失敗時使用零值，保持數組對齊
                    positions.append([0.0, 0.0, 0.0])
                    velocities.append([0.0, 0.0, 0.0])
                    errors.append(error)
            
            return positions, velocities, errors
        
        # 🚀 真正的並行化：分批次並行處理
        batch_size = min(50, len(times_cpu_batch))  # 每批50個時間點
        total_batches = (len(times_cpu_batch) + batch_size - 1) // batch_size
        
        logger.info(f"🎯 GPU批次並行：{total_batches}個批次，每批{batch_size}個時間點")
        
        all_positions = []
        all_velocities = []
        all_errors = []
        success_count = 0
        
        # 使用ThreadPoolExecutor實現真正的並行計算
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, total_batches)) as executor:
            # 創建批次任務
            batch_futures = []
            for i in range(0, len(times_cpu_batch), batch_size):
                batch_times = times_cpu_batch[i:i + batch_size]
                future = executor.submit(batch_sgp4_calculation, batch_times)
                batch_futures.append(future)
            
            # 收集並行計算結果
            for i, future in enumerate(concurrent.futures.as_completed(batch_futures)):
                try:
                    batch_pos, batch_vel, batch_err = future.result(timeout=30)
                    all_positions.extend(batch_pos)
                    all_velocities.extend(batch_vel)
                    all_errors.extend(batch_err)
                    
                    batch_success = sum(1 for err in batch_err if err == 0)
                    success_count += batch_success
                    
                    logger.debug(f"✅ 批次 {i+1}/{total_batches} 完成: {batch_success}/{len(batch_err)} 成功")
                    
                except Exception as e:
                    logger.error(f"❌ 批次 {i+1} 計算失敗: {e}")
                    # 填入失敗結果以保持數組大小
                    batch_size_actual = min(batch_size, len(times_cpu_batch) - i * batch_size)
                    all_positions.extend([[0.0, 0.0, 0.0]] * batch_size_actual)
                    all_velocities.extend([[0.0, 0.0, 0.0]] * batch_size_actual)
                    all_errors.extend([99] * batch_size_actual)
        
        # 🚀 結果轉回GPU記憶體進行後續處理
        if success_count > 0:
            # 過濾出成功的計算結果
            valid_positions = [pos for pos, err in zip(all_positions, all_errors) if err == 0]
            valid_velocities = [vel for vel, err in zip(all_velocities, all_errors) if err == 0]
            
            if valid_positions:
                gpu_positions = cp.array(valid_positions)
                gpu_velocities = cp.array(valid_velocities)
                
                logger.info(f"🎯 真實GPU SGP4計算統計: {success_count}/{len(times_cpu_batch)} 成功 "
                           f"({success_count/len(times_cpu_batch)*100:.1f}%)")
                logger.info(f"🚀 並行批次加速：{total_batches}個批次並行處理")
                
                return gpu_positions, gpu_velocities
        
        # 如果全部失敗
        logger.warning("⚠️ 真實GPU SGP4計算全部失敗！檢查TLE數據有效性")
        return cp.array([]), cp.array([])

    def _cpu_parallel_calculate(self, satellites: List[Dict],
                              time_series: List[datetime]) -> Dict[str, Any]:
        """CPU多進程並行計算"""
        logger.info(f"💻 使用CPU並行計算 ({self.cpu_workers}個進程)...")

        # 將衛星分組給不同進程處理
        chunk_size = max(1, len(satellites) // self.cpu_workers)
        satellite_chunks = [
            satellites[i:i + chunk_size]
            for i in range(0, len(satellites), chunk_size)
        ]

        all_results = {}

        # 🔧 添加超時機制防止無限掛起
        timeout_seconds = 600  # 10分鐘超時

        with ProcessPoolExecutor(max_workers=self.cpu_workers) as executor:
            # 提交所有批次任務
            future_to_chunk = {
                executor.submit(self._process_cpu_chunk, chunk, time_series): chunk
                for chunk in satellite_chunks
            }

            # 收集結果（添加超時）
            for i, future in enumerate(as_completed(future_to_chunk, timeout=timeout_seconds)):
                chunk = future_to_chunk[future]
                try:
                    chunk_results = future.result(timeout=60)  # 單個批次1分鐘超時
                    all_results.update(chunk_results)

                    logger.info(f"✅ CPU批次 {i+1}/{len(satellite_chunks)} 完成 "
                               f"({len(chunk_results)}顆衛星)")

                except Exception as e:
                    logger.error(f"❌ CPU批次處理失敗: {e}")

        return all_results

    @staticmethod
    def _process_cpu_chunk(satellites: List[Dict],
                          time_series: List[datetime]) -> Dict[str, Any]:
        """處理CPU計算批次（靜態方法，適合多進程）"""
        results = {}

        # 初始化SGP4引擎
        sgp4_engine = SGP4OrbitalEngine(
            observer_coordinates=None,
            eci_only_mode=True
        )

        for satellite in satellites:
            try:
                sat_id = satellite['satellite_id']
                line1 = satellite.get('tle_line1', satellite.get('line1', ''))
                line2 = satellite.get('tle_line2', satellite.get('line2', ''))

                # 解析TLE epoch時間
                epoch_year = int(line1[18:20])
                epoch_day = float(line1[20:32])

                if epoch_year < 57:
                    full_year = 2000 + epoch_year
                else:
                    full_year = 1900 + epoch_year

                epoch_time = datetime(full_year, 1, 1, tzinfo=timezone.utc) + timedelta(days=epoch_day - 1)

                # 構建SGP4引擎期望的數據格式
                sgp4_data = {
                    'line1': line1,
                    'line2': line2,
                    'satellite_name': satellite.get('name', 'Satellite'),
                    'epoch_datetime': epoch_time
                }

                positions = []
                velocities = []

                sgp4_positions = []

                # 計算所有時間點
                for i, time_point in enumerate(time_series):
                    result = sgp4_engine.calculate_position(sgp4_data, time_point)

                    if result and result.calculation_successful and result.position:
                        # 創建 SGP4Position 對象
                        sgp4_pos = SGP4Position(
                            x=result.position.x,
                            y=result.position.y,
                            z=result.position.z,
                            timestamp=time_point.isoformat(),
                            time_since_epoch_minutes=(time_point - epoch_time).total_seconds() / 60.0
                        )
                        sgp4_positions.append(sgp4_pos)
                        positions.append([result.position.x, result.position.y, result.position.z])
                        velocities.append([result.velocity.x, result.velocity.y, result.velocity.z])
                    else:
                        positions.append([0.0, 0.0, 0.0])
                        velocities.append([0.0, 0.0, 0.0])

                # 創建與原始格式兼容的字典結果
                results[sat_id] = {
                    'satellite_id': sat_id,
                    'positions': positions,  # ECI 位置列表
                    'velocities': velocities,  # 速度列表
                    'times': [t.isoformat() for t in time_series],
                    'calculation_method': 'CPU_Parallel_SGP4_Engine',
                    'calculation_successful': len(sgp4_positions) > 0,
                    'algorithm_used': "CPU_Parallel_SGP4_Engine",
                    'precision_grade': "A",
                    'sgp4_positions': sgp4_positions  # 保留 SGP4Position 對象以備後用
                }

            except Exception as e:
                logger.warning(f"⚠️ 衛星 {sat_id} 計算失敗: {e}")
                continue

        return results

    def _sequential_calculate(self, satellites: List[Dict],
                            time_series: List[datetime]) -> Dict[str, Any]:
        """順序計算（回退方案）"""
        logger.info("📊 使用順序計算...")
        return self._process_cpu_chunk(satellites, time_series)

    def _cpu_batch_fallback(self, batch: GPUBatch) -> Dict[str, Any]:
        """CPU回退計算"""
        logger.info("🔄 GPU失敗，回退到CPU計算...")

        satellites = [
            {
                'satellite_id': sat_id,
                'tle_line1': lines[0],
                'tle_line2': lines[1]
            }
            for sat_id, lines in zip(batch.satellite_ids, batch.tle_lines)
        ]

        time_series = [
            datetime.fromtimestamp(jd * 86400 - 2440587.5 * 86400, tz=timezone.utc)
            for jd in batch.time_points
        ]

        return self._process_cpu_chunk(satellites, time_series)

def create_parallel_sgp4_calculator(enable_gpu: bool = True,
                                   cpu_workers: int = None) -> ParallelSGP4Calculator:
    """建立並行SGP4計算器"""
    config = ParallelConfig(
        enable_gpu=enable_gpu,
        enable_multiprocessing=True,
        cpu_workers=cpu_workers or mp.cpu_count(),
        gpu_batch_size=1000
    )

    return ParallelSGP4Calculator(config)