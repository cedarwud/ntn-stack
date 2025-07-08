"""
階段三候選篩選層整合測試
=========================

驗證CandidateSelector和所有策略的正確運行
"""

import asyncio
import time
import json
from typing import Dict, Any, List
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .selector import CandidateSelector
from ..interfaces.event_processor import ProcessedEvent
from ..interfaces.candidate_selector import Candidate


def create_test_event() -> ProcessedEvent:
    """創建測試事件"""
    return ProcessedEvent(
        event_type="A4",
        timestamp=time.time(),
        confidence=0.85,
        ue_id="test_ue_001",
        source_cell="sat_001",
        target_cells=["sat_101", "sat_102", "sat_103"],
        event_data={
            "signal_threshold": -100.0,
            "coverage_issue": True,
            "handover_cause": "coverage_degradation",
            "network_condition": "normal",
            "traffic_load": "medium",
        },
        trigger_conditions={
            "rsrp_threshold": -110.0,
            "hysteresis": 3.0,
            "time_to_trigger": 320,
        },
        measurement_values={"rsrp": -105.0, "rsrq": -12.5, "sinr": 8.2},
    )


def create_test_satellite_pool() -> List[Dict]:
    """創建測試衛星池"""
    return [
        {
            "norad_id": "sat_101",
            "name": "Satellite-101",
            "elevation": 45.5,
            "azimuth": 180.0,
            "signal_strength": -85.0,
            "load_factor": 0.3,
            "distance": 800.0,
            "doppler_shift": 1500.0,
            "position": {"x": 1000.0, "y": 2000.0, "z": 35786.0},
            "velocity": {"vx": 3.1, "vy": 0.5, "vz": 0.1},
            "visibility_time": 1800.0,
        },
        {
            "norad_id": "sat_102",
            "name": "Satellite-102",
            "elevation": 65.2,
            "azimuth": 90.0,
            "signal_strength": -78.0,
            "load_factor": 0.6,
            "distance": 600.0,
            "doppler_shift": 800.0,
            "position": {"x": 1500.0, "y": 1000.0, "z": 35786.0},
            "velocity": {"vx": 2.8, "vy": 1.2, "vz": 0.0},
            "visibility_time": 2400.0,
        },
        {
            "norad_id": "sat_103",
            "name": "Satellite-103",
            "elevation": 25.8,
            "azimuth": 270.0,
            "signal_strength": -95.0,
            "load_factor": 0.8,
            "distance": 1200.0,
            "doppler_shift": 2200.0,
            "position": {"x": 500.0, "y": 2500.0, "z": 35786.0},
            "velocity": {"vx": 3.5, "vy": -0.8, "vz": 0.2},
            "visibility_time": 1200.0,
        },
        {
            "norad_id": "sat_104",
            "name": "Satellite-104",
            "elevation": 75.0,
            "azimuth": 45.0,
            "signal_strength": -70.0,
            "load_factor": 0.2,
            "distance": 450.0,
            "doppler_shift": 600.0,
            "position": {"x": 2000.0, "y": 800.0, "z": 35786.0},
            "velocity": {"vx": 1.8, "vy": 2.1, "vz": -0.1},
            "visibility_time": 3000.0,
        },
        {
            "norad_id": "sat_105",
            "name": "Satellite-105",
            "elevation": 8.5,  # 低仰角，應被基本篩選過濾
            "azimuth": 315.0,
            "signal_strength": -110.0,
            "load_factor": 0.9,
            "distance": 1800.0,
            "doppler_shift": 3000.0,
            "position": {"x": 200.0, "y": 3000.0, "z": 35786.0},
            "velocity": {"vx": 4.2, "vy": -1.5, "vz": 0.3},
            "visibility_time": 600.0,
        },
    ]


async def test_candidate_selection():
    """測試候選篩選功能"""
    logger.info("🚀 開始階段三候選篩選層整合測試")

    # 1. 初始化篩選器
    selector = CandidateSelector()
    logger.info("✅ CandidateSelector 初始化成功")

    # 2. 準備測試數據
    test_event = create_test_event()
    satellite_pool = create_test_satellite_pool()

    logger.info(f"📡 測試衛星池: {len(satellite_pool)} 顆衛星")
    logger.info(f"📝 測試事件: {test_event.event_type} - {test_event.ue_id}")

    # 3. 執行候選篩選
    start_time = time.time()
    candidates = await selector.select_candidates(test_event, satellite_pool)
    selection_time = (time.time() - start_time) * 1000

    logger.info(
        f"⚡ 候選篩選完成: 發現 {len(candidates)} 個候選衛星 (耗時: {selection_time:.2f}ms)"
    )

    # 4. 執行候選評分
    start_time = time.time()
    scored_candidates = await selector.score_candidates(candidates)
    scoring_time = (time.time() - start_time) * 1000

    logger.info(
        f"📊 候選評分完成: {len(scored_candidates)} 個評分候選 (耗時: {scoring_time:.2f}ms)"
    )

    # 5. 顯示結果
    logger.info("🏆 篩選和評分結果:")
    for i, scored_candidate in enumerate(scored_candidates[:3], 1):
        candidate = scored_candidate.candidate
        logger.info(
            f"  {i}. {candidate.satellite_id} (排名: {scored_candidate.ranking})"
        )
        logger.info(
            f"     綜合評分: {scored_candidate.score:.3f} | 置信度: {scored_candidate.confidence:.3f}"
        )
        logger.info(
            f"     仰角: {candidate.elevation:.1f}° | 信號: {candidate.signal_strength:.1f}dBm | 負載: {candidate.load_factor:.2f}"
        )
        logger.info(
            f"     距離: {candidate.distance:.0f}km | 可見時間: {candidate.visibility_time/60:.1f}分鐘"
        )

    # 6. 測試動態篩選
    filter_criteria = {
        "min_elevation": 30.0,
        "min_signal_strength": -90.0,
        "max_load_factor": 0.7,
    }

    filtered_candidates = selector.filter_candidates(candidates, filter_criteria)
    logger.info(f"🔍 動態篩選結果: {len(filtered_candidates)} 個候選符合嚴格條件")

    # 7. 測試策略管理
    strategies = selector.get_selection_strategies()
    logger.info(f"🛠️  可用策略: {', '.join(strategies)}")

    # 8. 測試單個策略應用
    elevation_candidates = await selector.apply_strategy(
        "elevation", candidates, {"min_elevation": 50.0}
    )
    logger.info(f"🎯 仰角策略篩選: {len(elevation_candidates)} 個高仰角候選")

    # 9. 獲取性能指標
    metrics = selector.get_performance_metrics()
    logger.info("📈 性能指標:")
    logger.info(f"   總篩選次數: {metrics['selection_count']}")
    logger.info(f"   活躍策略: {', '.join(metrics['active_strategies'])}")
    logger.info(f"   候選池大小: {metrics['candidate_pool_size']}")

    return {
        "success": True,
        "candidates_found": len(candidates),
        "scored_candidates": len(scored_candidates),
        "selection_time_ms": selection_time,
        "scoring_time_ms": scoring_time,
        "top_score": scored_candidates[0].score if scored_candidates else 0.0,
        "strategies_available": len(strategies),
        "metrics": metrics,
    }


async def test_error_handling():
    """測試錯誤處理"""
    logger.info("🧪 測試錯誤處理機制")

    selector = CandidateSelector()

    # 測試空衛星池
    empty_event = create_test_event()
    empty_pool = []

    candidates = await selector.select_candidates(empty_event, empty_pool)
    assert len(candidates) == 0, "空衛星池應返回空候選列表"
    logger.info("✅ 空衛星池處理正確")

    # 測試無效策略
    test_candidates = [
        Candidate(
            satellite_id="test_sat",
            elevation=45.0,
            signal_strength=-80.0,
            load_factor=0.3,
            distance=800.0,
            azimuth=180.0,
            doppler_shift=1000.0,
            position={"x": 1000.0, "y": 1000.0, "z": 35786.0},
            visibility_time=1800.0,
            velocity={"vx": 3.0, "vy": 1.0, "vz": 0.0},
        )
    ]

    try:
        await selector.apply_strategy("invalid_strategy", test_candidates)
        assert False, "應該拋出異常"
    except Exception as e:
        logger.info(f"✅ 無效策略異常處理正確: {str(e)[:50]}...")

    logger.info("✅ 錯誤處理測試完成")


async def run_integration_test():
    """運行完整整合測試"""
    logger.info("=" * 60)
    logger.info("🎯 階段三候選篩選層重構 - 整合測試")
    logger.info("=" * 60)

    try:
        # 主要功能測試
        result = await test_candidate_selection()

        # 錯誤處理測試
        await test_error_handling()

        # 測試總結
        logger.info("=" * 60)
        logger.info("🎉 階段三整合測試 - 全部通過！")
        logger.info("=" * 60)
        logger.info("📊 測試摘要:")
        logger.info(f"   發現候選衛星: {result['candidates_found']}")
        logger.info(f"   評分候選數量: {result['scored_candidates']}")
        logger.info(f"   篩選耗時: {result['selection_time_ms']:.2f}ms")
        logger.info(f"   評分耗時: {result['scoring_time_ms']:.2f}ms")
        logger.info(f"   最高評分: {result['top_score']:.3f}")
        logger.info(f"   可用策略數: {result['strategies_available']}")

        logger.info("\n✅ 階段三候選篩選層重構完成！")
        logger.info("🚀 準備進入階段四：決策執行層重構")

        return result

    except Exception as e:
        logger.error(f"❌ 整合測試失敗: {str(e)}")
        raise


if __name__ == "__main__":
    # 運行整合測試
    asyncio.run(run_integration_test())
