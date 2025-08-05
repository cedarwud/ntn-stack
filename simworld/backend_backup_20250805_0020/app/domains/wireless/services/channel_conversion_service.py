"""
Channel Conversion Service
負責將 Sionna 通道響應轉換為 UERANSIM 可用的 RAN 參數
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import numpy as np
import math

from ..models.channel_models import (
    SionnaChannelResponse,
    UERANSIMChannelParams,
    ChannelToRANConversionResult,
    BatchChannelConversionRequest,
    ChannelUpdateEvent,
)

logger = logging.getLogger(__name__)


class ChannelToRANConversionService:
    """通道到 RAN 參數轉換服務"""

    def __init__(self, conversion_cache_size: int = 1000):
        self.conversion_cache: Dict[str, ChannelToRANConversionResult] = {}
        self.conversion_cache_size = conversion_cache_size
        self.conversion_history: List[ChannelToRANConversionResult] = []

        # 轉換參數設定
        self.noise_floor_dbm = -104  # 標準噪音基底
        self.thermal_noise_power_dbm = -174  # dBm/Hz
        self.implementation_margin_db = 2.0  # 實現損失

        # CQI 映射表 (根據 3GPP TS 36.213)
        self.cqi_table = [
            {"cqi": 1, "min_sinr_db": -6.7, "efficiency": 0.1523, "modulation": "QPSK"},
            {"cqi": 2, "min_sinr_db": -4.7, "efficiency": 0.2344, "modulation": "QPSK"},
            {"cqi": 3, "min_sinr_db": -2.3, "efficiency": 0.3770, "modulation": "QPSK"},
            {"cqi": 4, "min_sinr_db": 0.2, "efficiency": 0.6016, "modulation": "16QAM"},
            {"cqi": 5, "min_sinr_db": 2.4, "efficiency": 0.8770, "modulation": "16QAM"},
            {"cqi": 6, "min_sinr_db": 4.3, "efficiency": 1.1758, "modulation": "16QAM"},
            {"cqi": 7, "min_sinr_db": 5.9, "efficiency": 1.4766, "modulation": "16QAM"},
            {"cqi": 8, "min_sinr_db": 8.1, "efficiency": 1.9141, "modulation": "64QAM"},
            {
                "cqi": 9,
                "min_sinr_db": 10.3,
                "efficiency": 2.4063,
                "modulation": "64QAM",
            },
            {
                "cqi": 10,
                "min_sinr_db": 11.9,
                "efficiency": 2.7305,
                "modulation": "64QAM",
            },
            {
                "cqi": 11,
                "min_sinr_db": 14.1,
                "efficiency": 3.3223,
                "modulation": "64QAM",
            },
            {
                "cqi": 12,
                "min_sinr_db": 16.3,
                "efficiency": 3.9023,
                "modulation": "256QAM",
            },
            {
                "cqi": 13,
                "min_sinr_db": 18.7,
                "efficiency": 4.5234,
                "modulation": "256QAM",
            },
            {
                "cqi": 14,
                "min_sinr_db": 21.0,
                "efficiency": 5.1152,
                "modulation": "256QAM",
            },
            {
                "cqi": 15,
                "min_sinr_db": 22.7,
                "efficiency": 5.5547,
                "modulation": "256QAM",
            },
        ]

        # 快取命中率統計
        self.cache_hits = 0
        self.cache_misses = 0

    async def convert_channel_to_ran(
        self,
        channel_response: SionnaChannelResponse,
        ue_id: str,
        gnb_id: str,
        noise_figure_db: float = 7.0,
        antenna_gain_db: float = 15.0,
    ) -> ChannelToRANConversionResult:
        """將單一通道響應轉換為 RAN 參數"""

        conversion_start = datetime.utcnow()
        conversion_id = f"conv_{uuid.uuid4().hex[:8]}"

        try:
            logger.debug(
                f"開始通道轉換: {conversion_id}, 通道: {channel_response.channel_id}"
            )

            # 計算接收功率
            rsrp_dbm = await self._calculate_rsrp(channel_response, antenna_gain_db)

            # 計算 SINR
            sinr_db = await self._calculate_sinr(
                channel_response, rsrp_dbm, noise_figure_db
            )

            # 計算 RSRQ
            rsrq_db = await self._calculate_rsrq(sinr_db, channel_response)

            # 計算 CQI
            cqi = await self._calculate_cqi(sinr_db)

            # 計算吞吐量
            throughput_mbps = await self._estimate_throughput(
                cqi, channel_response.bandwidth_hz
            )

            # 計算延遲
            latency_ms = await self._estimate_latency(channel_response)

            # 計算錯誤率
            error_rate = await self._estimate_error_rate(sinr_db)

            # 計算參數有效期
            valid_duration = await self._calculate_validity_duration(channel_response)
            valid_until = datetime.utcnow() + valid_duration

            # 建立 UERANSIM 參數
            ran_params = UERANSIMChannelParams(
                ue_id=ue_id,
                gnb_id=gnb_id,
                sinr_db=sinr_db,
                rsrp_dbm=rsrp_dbm,
                rsrq_db=rsrq_db,
                cqi=cqi,
                throughput_mbps=throughput_mbps,
                latency_ms=latency_ms,
                error_rate=error_rate,
                valid_until=valid_until,
            )

            # 計算轉換品質
            conversion_time_ms = (
                datetime.utcnow() - conversion_start
            ).total_seconds() * 1000
            conversion_accuracy = await self._assess_conversion_accuracy(
                channel_response, ran_params
            )
            confidence_level = await self._calculate_confidence_level(channel_response)

            # 除錯資訊
            debug_info = {
                "conversion_time_ms": conversion_time_ms,
                "path_count": len(channel_response.paths),
                "dominant_path_power_db": max(
                    (p.power_db for p in channel_response.paths), default=0
                ),
                "frequency_ghz": channel_response.frequency_hz / 1e9,
                "distance_km": self._estimate_distance(channel_response) / 1000,
                "environment_assessment": await self._assess_environment(
                    channel_response
                ),
            }

            result = ChannelToRANConversionResult(
                conversion_id=conversion_id,
                source_channel=channel_response,
                ran_parameters=ran_params,
                conversion_accuracy=conversion_accuracy,
                confidence_level=confidence_level,
                debug_info=debug_info,
            )

            # 快取結果
            await self._cache_conversion_result(result)

            logger.debug(
                f"通道轉換完成: {conversion_id}, "
                f"SINR: {sinr_db:.1f}dB, CQI: {cqi}, 吞吐量: {throughput_mbps:.1f}Mbps"
            )

            return result

        except Exception as e:
            logger.error(f"通道轉換失敗: {conversion_id}, 錯誤: {e}")
            raise

    async def _calculate_rsrp(
        self, channel_response: SionnaChannelResponse, antenna_gain_db: float
    ) -> float:
        """計算 RSRP (Reference Signal Received Power)"""

        # 基本傳輸功率 (假設 gNodeB 傳輸功率)
        tx_power_dbm = 43.0  # 20W = 43dBm (典型 macro cell)

        # 路徑損耗
        path_loss_db = channel_response.path_loss_db

        # 陰影衰落
        shadowing_db = channel_response.shadowing_db

        # 多路徑增益 (考慮建設性干涉)
        multipath_gain_db = await self._calculate_multipath_gain(channel_response.paths)

        # RSRP 計算
        rsrp_dbm = (
            tx_power_dbm
            + antenna_gain_db
            - path_loss_db
            - shadowing_db
            + multipath_gain_db
        )

        return float(rsrp_dbm)

    async def _calculate_sinr(
        self,
        channel_response: SionnaChannelResponse,
        rsrp_dbm: float,
        noise_figure_db: float,
    ) -> float:
        """計算 SINR (Signal-to-Interference-plus-Noise Ratio)"""

        # 噪音功率計算
        bandwidth_hz = channel_response.bandwidth_hz
        noise_power_dbm = (
            self.thermal_noise_power_dbm
            + 10 * math.log10(bandwidth_hz)
            + noise_figure_db
        )

        # 干擾功率 (簡化模型，實際應考慮同頻干擾)
        interference_dbm = noise_power_dbm - 10  # 假設干擾比噪音低 10dB

        # 總噪音+干擾功率
        total_noise_interference_dbm = 10 * math.log10(
            10 ** (noise_power_dbm / 10) + 10 ** (interference_dbm / 10)
        )

        # SINR 計算
        sinr_db = rsrp_dbm - total_noise_interference_dbm

        return float(sinr_db)

    async def _calculate_rsrq(
        self, sinr_db: float, channel_response: SionnaChannelResponse
    ) -> float:
        """計算 RSRQ (Reference Signal Received Quality)"""

        # RSRQ 主要反映信號品質，與 SINR 相關但考慮更多因素
        # 簡化模型：RSRQ ≈ SINR - 載波間干擾修正

        # 載波間干擾估計 (基於多路徑延遲擴散)
        ici_penalty_db = min(3.0, channel_response.rms_delay_spread_ns / 100)

        # 頻率選擇性衰落影響
        frequency_selectivity_penalty = min(
            2.0,
            (channel_response.coherence_bandwidth_hz / channel_response.bandwidth_hz)
            * 2,
        )

        rsrq_db = sinr_db - ici_penalty_db - frequency_selectivity_penalty

        # RSRQ 通常在 -19.5 到 -3 dB 範圍內
        rsrq_db = max(-19.5, min(-3.0, rsrq_db))

        return float(rsrq_db)

    async def _calculate_cqi(self, sinr_db: float) -> int:
        """計算 CQI (Channel Quality Indicator)"""

        # 根據 SINR 查找對應的 CQI
        for i in range(len(self.cqi_table) - 1, -1, -1):
            if sinr_db >= self.cqi_table[i]["min_sinr_db"]:
                return self.cqi_table[i]["cqi"]

        # 如果 SINR 太低，返回最低 CQI
        return 1

    async def _estimate_throughput(self, cqi: int, bandwidth_hz: float) -> float:
        """估計吞吐量"""

        # 獲取 CQI 對應的頻譜效率
        efficiency = next(
            (item["efficiency"] for item in self.cqi_table if item["cqi"] == cqi),
            0.1523,  # 預設最低效率
        )

        # 頻寬轉換為 MHz
        bandwidth_mhz = bandwidth_hz / 1e6

        # 理論吞吐量 = 頻譜效率 × 頻寬
        theoretical_throughput_mbps = efficiency * bandwidth_mhz

        # 考慮實際因素 (協議開銷、控制通道等)
        overhead_factor = 0.75  # 25% 開銷

        actual_throughput_mbps = theoretical_throughput_mbps * overhead_factor

        return float(actual_throughput_mbps)

    async def _estimate_latency(self, channel_response: SionnaChannelResponse) -> float:
        """估計延遲"""

        # 基本傳播延遲
        distance_m = self._estimate_distance(channel_response)
        propagation_delay_ms = distance_m / 3e8 * 1000

        # 多路徑延遲擴散的影響
        delay_spread_penalty_ms = channel_response.rms_delay_spread_ns / 1e6

        # 處理延遲 (基於通道品質)
        processing_delay_ms = 1.0  # 基本處理延遲

        # 如果通道品質差，需要更多重傳和錯誤修正
        if channel_response.path_loss_db > 150:
            processing_delay_ms += 2.0

        total_latency_ms = (
            propagation_delay_ms + delay_spread_penalty_ms + processing_delay_ms
        )

        return float(total_latency_ms)

    async def _estimate_error_rate(self, sinr_db: float) -> float:
        """估計錯誤率"""

        # 簡化的 AWGN 通道 BER 模型
        # 實際應根據調製方式和編碼使用更精確的模型

        if sinr_db > 20:
            ber = 1e-6  # 極低錯誤率
        elif sinr_db > 15:
            ber = 1e-5
        elif sinr_db > 10:
            ber = 1e-4
        elif sinr_db > 5:
            ber = 1e-3
        elif sinr_db > 0:
            ber = 1e-2
        else:
            ber = 1e-1  # 高錯誤率

        return float(ber)

    def _estimate_distance(self, channel_response: SionnaChannelResponse) -> float:
        """估計傳輸距離"""

        tx_pos = channel_response.tx_position
        rx_pos = channel_response.rx_position

        distance = math.sqrt(sum((tx_pos[i] - rx_pos[i]) ** 2 for i in range(3)))
        return distance

    async def _calculate_multipath_gain(self, paths: List) -> float:
        """計算多路徑增益"""

        if not paths:
            return 0.0

        # 相干合成的功率增益 (簡化模型)
        total_power_linear = sum(10 ** (path.power_db / 10) for path in paths)
        multipath_gain_db = 10 * math.log10(total_power_linear)

        # 限制最大增益
        return min(6.0, multipath_gain_db)

    async def _calculate_validity_duration(
        self, channel_response: SionnaChannelResponse
    ) -> timedelta:
        """計算參數有效時間"""

        # 基於相干時間決定有效期
        coherence_time_ms = channel_response.coherence_time_ms

        if coherence_time_ms > 1000:  # 慢衰落
            validity_seconds = min(300, coherence_time_ms / 1000 * 0.5)  # 50% 相干時間
        else:  # 快衰落
            validity_seconds = min(60, coherence_time_ms / 1000 * 0.3)  # 30% 相干時間

        return timedelta(seconds=validity_seconds)

    async def _assess_conversion_accuracy(
        self, channel_response: SionnaChannelResponse, ran_params: UERANSIMChannelParams
    ) -> float:
        """評估轉換準確度"""

        # 基於通道品質和複雜度評估準確度
        accuracy = 1.0

        # 路徑損耗太高會降低準確度
        if channel_response.path_loss_db > 160:
            accuracy *= 0.8

        # 延遲擴散太大會降低準確度
        if channel_response.rms_delay_spread_ns > 500:
            accuracy *= 0.9

        # 多路徑過於複雜會降低準確度
        if len(channel_response.paths) > 10:
            accuracy *= 0.85

        return accuracy

    async def _calculate_confidence_level(
        self, channel_response: SionnaChannelResponse
    ) -> float:
        """計算信心度"""

        confidence = 1.0

        # 基於測量數據的完整性
        if not channel_response.paths:
            confidence *= 0.5

        # 基於頻率範圍的適用性
        frequency_ghz = channel_response.frequency_hz / 1e9
        if frequency_ghz < 1 or frequency_ghz > 100:  # 超出常用範圍
            confidence *= 0.8

        return confidence

    async def _assess_environment(self, channel_response: SionnaChannelResponse) -> str:
        """評估環境類型"""

        path_loss = channel_response.path_loss_db
        delay_spread = channel_response.rms_delay_spread_ns
        path_count = len(channel_response.paths)

        if path_loss > 160:
            return "deep_indoor_or_blocked"
        elif path_loss > 140 and delay_spread > 200:
            return "dense_urban"
        elif path_loss > 130 and delay_spread > 100:
            return "urban"
        elif path_loss > 120:
            return "suburban"
        else:
            return "rural_or_los"

    async def _cache_conversion_result(self, result: ChannelToRANConversionResult):
        """快取轉換結果"""

        # 如果快取已滿，移除最舊的項目
        if len(self.conversion_cache) >= self.conversion_cache_size:
            oldest_key = min(
                self.conversion_cache.keys(),
                key=lambda k: self.conversion_cache[k].timestamp,
            )
            del self.conversion_cache[oldest_key]

        self.conversion_cache[result.conversion_id] = result
        self.conversion_history.append(result)

        # 限制歷史記錄長度
        if len(self.conversion_history) > 10000:
            self.conversion_history = self.conversion_history[-5000:]

    async def batch_convert_channels(
        self, request: BatchChannelConversionRequest
    ) -> List[ChannelToRANConversionResult]:
        """批次轉換通道"""

        logger.info(
            f"開始批次轉換: {request.batch_id}, 通道數: {len(request.channels)}"
        )

        # 平行處理轉換
        tasks = []
        for i, channel in enumerate(request.channels):
            ue_id = request.target_ue_ids[i % len(request.target_ue_ids)]
            gnb_id = f"gnb_{i // len(request.target_ue_ids) + 1}"

            task = self.convert_channel_to_ran(channel, ue_id, gnb_id)
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 過濾成功的結果
        successful_results = [
            r for r in results if isinstance(r, ChannelToRANConversionResult)
        ]

        logger.info(
            f"批次轉換完成: {request.batch_id}, 成功: {len(successful_results)}/{len(request.channels)}"
        )

        return successful_results

    async def get_conversion_history(
        self, limit: int = 100, since: Optional[datetime] = None
    ) -> List[ChannelToRANConversionResult]:
        """獲取轉換歷史"""

        history = self.conversion_history

        if since:
            history = [r for r in history if r.timestamp >= since]

        return history[-limit:]

    def get_cache_hit_rate(self) -> float:
        """獲取快取命中率"""
        if self.cache_hits + self.cache_misses == 0:
            return 0.0
        return self.cache_hits / (self.cache_hits + self.cache_misses)
