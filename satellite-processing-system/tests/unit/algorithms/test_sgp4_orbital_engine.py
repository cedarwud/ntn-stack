# SGP4 軌道引擎測試 - TDD 實施
# 🚨 關鍵：防止TLE時間基準錯誤再次發生！

import pytest
import time
from datetime import datetime, timezone, timedelta
from typing import List, Dict
import math

# 導入待測試的模組
import sys
sys.path.append('/home/sat/ntn-stack/satellite-processing-system/src')

from shared.engines.sgp4_orbital_engine import SGP4OrbitalEngine
from tests.fixtures.tle_data_loader import load_test_tle_data, get_tle_epoch_time

class TestSGP4OrbitalEngine:
    """
    SGP4軌道引擎測試套件
    
    測試重點：
    1. 🚨 時間基準正確性 (防止使用當前時間)
    2. 軌道計算精度驗證
    3. 批量處理性能測試  
    4. 學術標準合規性
    """
    
    @pytest.fixture
    def sgp4_engine(self):
        """SGP4軌道引擎 fixture"""
        return SGP4OrbitalEngine()
    
    @pytest.fixture
    def real_starlink_tle(self):
        """真實的Starlink TLE數據"""
        tle_data = load_test_tle_data(constellation='starlink', count=1)
        assert len(tle_data) > 0, "無法載入真實TLE數據"
        return tle_data[0]
    
    @pytest.fixture
    def real_tle_batch(self):
        """真實TLE數據批次"""
        return load_test_tle_data(constellation='mixed', count=5)
    
    # =========================================================================
    # 🚨 時間基準正確性測試 - 最重要的測試！
    # =========================================================================
    
    @pytest.mark.sgp4
    @pytest.mark.real_data
    def test_tle_epoch_time_usage_mandatory(self, sgp4_engine, real_starlink_tle, academic_compliance_checker):
        """
        🚨 強制測試：必須使用TLE epoch時間，不得使用當前時間
        
        這個測試防止8000+顆衛星→0顆可見的問題再次發生
        """
        # Given: 真實TLE數據
        tle_data = real_starlink_tle
        tle_epoch_time = get_tle_epoch_time(tle_data)
        current_time = datetime.now(timezone.utc)
        
        # 驗證學術合規性
        academic_compliance_checker(
            tle_data['data_source'], 
            "SGP4 orbital propagation"
        )
        
        # When: 使用TLE epoch時間計算 (正確方式)
        correct_result = sgp4_engine.calculate_position(tle_data, tle_epoch_time)
        
        # Then: 計算必須成功
        assert correct_result is not None, "使用TLE epoch時間的計算必須成功"
        assert hasattr(correct_result, 'position'), "結果必須包含位置信息"
        assert hasattr(correct_result, 'calculation_base_time'), "結果必須包含計算基準時間"
        
        # 🚨 關鍵驗證：計算基準時間必須是TLE epoch時間
        assert correct_result.calculation_base_time == tle_epoch_time, \
            f"🚨 時間基準錯誤！使用了 {correct_result.calculation_base_time}，應該是 {tle_epoch_time}"
        
        # When: 檢查是否會錯誤使用當前時間
        time_diff_days = abs((current_time - tle_epoch_time).days)
        
        if time_diff_days > 3:
            # 時間差超過3天，應該發出警告或拒絕計算
            with pytest.warns(UserWarning, match="TLE數據時間差.*天"):
                warning_result = sgp4_engine.calculate_position(tle_data, current_time)
                
            # 或者應該拒絕使用過期的時間基準
            # with pytest.raises(ValueError, match="TLE數據過期.*使用epoch時間"):
            #     sgp4_engine.calculate_position(tle_data, current_time)
        
        print(f"✅ 時間基準驗證通過：TLE epoch ({tle_epoch_time}) vs 當前時間 ({current_time})")
        print(f"   時間差: {time_diff_days} 天")
    
    @pytest.mark.sgp4
    def test_current_time_usage_detection(self, sgp4_engine, real_starlink_tle):
        """
        測試系統是否能檢測到錯誤的當前時間使用
        """
        # Given: TLE數據和當前時間
        tle_data = real_starlink_tle
        current_time = datetime.now(timezone.utc)
        tle_epoch_time = get_tle_epoch_time(tle_data)
        
        # When & Then: 檢查時間基準使用
        result = sgp4_engine.calculate_position(tle_data, current_time)
        
        # 應該能夠計算，但必須記錄使用的時間基準
        assert result.calculation_base_time == current_time, "必須記錄實際使用的計算時間"
        
        # 如果時間差太大，應該有警告標記
        time_diff = abs((current_time - tle_epoch_time).days)
        if time_diff > 3:
            assert hasattr(result, 'time_warning') or hasattr(result, 'accuracy_warning'), \
                "時間差過大時應該有準確度警告"
    
    # =========================================================================
    # 軌道計算精度測試
    # =========================================================================
    
    @pytest.mark.sgp4
    @pytest.mark.real_data
    def test_orbital_calculation_accuracy_with_real_tle(self, sgp4_engine, real_starlink_tle):
        """
        測試使用真實TLE數據的軌道計算精度
        """
        # Given: 真實TLE數據和正確的epoch時間
        tle_data = real_starlink_tle
        calculation_time = get_tle_epoch_time(tle_data)  # 🚨 使用TLE epoch時間
        
        # When: 計算衛星位置
        result = sgp4_engine.calculate_position(tle_data, calculation_time)
        
        # Then: 驗證計算結果
        assert result is not None, "軌道計算結果不能為空"
        assert hasattr(result, 'position'), "結果必須包含位置信息"
        assert hasattr(result, 'velocity'), "結果必須包含速度信息"
        
        # 位置合理性檢查 (LEO衛星高度範圍)
        position = result.position
        altitude_km = math.sqrt(position.x**2 + position.y**2 + position.z**2) - 6371  # 地球半徑
        assert 200 <= altitude_km <= 2000, f"衛星高度不合理: {altitude_km:.2f} km"
        
        # 速度合理性檢查 (LEO衛星速度範圍)
        velocity = result.velocity
        speed_kmh = math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2) * 3600  # km/s -> km/h
        assert 15000 <= speed_kmh <= 35000, f"衛星速度不合理: {speed_kmh:.2f} km/h"
        
        # 算法標準檢查
        assert result.algorithm_used == "SGP4", "必須使用SGP4算法"
        assert "simplified" not in result.algorithm_used.lower(), "禁止使用簡化算法"
    
    @pytest.mark.sgp4
    def test_sgp4_vs_simplified_model_rejection(self, sgp4_engine, real_starlink_tle):
        """
        🚨 測試拒絕簡化軌道模型，強制使用完整SGP4
        """
        # Given: 真實TLE數據
        tle_data = real_starlink_tle
        calculation_time = get_tle_epoch_time(tle_data)
        
        # When: 計算軌道
        result = sgp4_engine.calculate_position(tle_data, calculation_time)
        
        # Then: 必須使用完整SGP4算法
        assert "SGP4" in result.algorithm_used, "必須使用SGP4算法"
        assert "simplified" not in result.algorithm_used.lower(), "禁止使用簡化模型"
        assert "kepler" not in result.algorithm_used.lower(), "禁止使用簡化開普勒模型"
        
        # 必須包含攝動效應
        if hasattr(result, 'perturbation_effects_included'):
            assert result.perturbation_effects_included == True, "必須包含攝動效應"
        
        print(f"✅ 算法驗證通過：{result.algorithm_used}")
    
    # =========================================================================
    # 批量處理和性能測試
    # =========================================================================
    
    @pytest.mark.sgp4
    @pytest.mark.performance
    def test_batch_calculation_performance(self, sgp4_engine, real_tle_batch, performance_recorder):
        """
        測試批量衛星軌道計算的性能
        """
        # Given: 多顆衛星的TLE數據
        tle_list = real_tle_batch
        calculation_times = [get_tle_epoch_time(tle) for tle in tle_list]
        
        # When: 執行批量計算
        start_time = time.perf_counter()
        
        results = []
        for i, tle_data in enumerate(tle_list):
            result = sgp4_engine.calculate_position(tle_data, calculation_times[i])
            results.append(result)
        
        total_time = time.perf_counter() - start_time
        
        # Then: 性能驗證
        assert len(results) == len(tle_list), "必須計算所有衛星"
        assert all(r is not None for r in results), "所有計算都必須成功"
        
        # 性能基準檢查
        avg_time_per_satellite = total_time / len(tle_list)
        assert avg_time_per_satellite < 0.05, f"平均計算時間過長: {avg_time_per_satellite:.4f}s"  # < 50ms
        
        # 記錄性能數據
        performance_metrics = {
            'total_satellites': len(tle_list),
            'total_time_seconds': total_time,
            'avg_time_per_satellite': avg_time_per_satellite,
            'calculations_per_second': len(tle_list) / total_time
        }
        performance_recorder('sgp4_batch_calculation', performance_metrics)
        
        print(f"✅ 性能測試通過: {len(tle_list)}顆衛星, {total_time:.3f}秒, 平均{avg_time_per_satellite*1000:.1f}ms/顆")
    
    @pytest.mark.sgp4
    @pytest.mark.performance
    def test_sgp4_calculation_performance(self, sgp4_engine, real_starlink_tle):
        """
        SGP4計算性能測試 (無需benchmark依賴)
        """
        # Given: 真實TLE數據
        tle_data = real_starlink_tle
        calculation_time = get_tle_epoch_time(tle_data)
        
        # When: 測量計算時間
        import time
        start_time = time.time()
        result = sgp4_engine.calculate_position(tle_data, calculation_time)
        end_time = time.time()
        
        # Then: 驗證性能和結果
        calculation_time_ms = (end_time - start_time) * 1000
        assert calculation_time_ms < 50, f"SGP4計算過慢: {calculation_time_ms:.2f}ms"
        
        # 驗證結果正確性
        assert result is not None, "性能測試結果不能為空"
        assert result.algorithm_used == "SGP4", "性能測試必須使用SGP4算法"
    
    # =========================================================================
    # 邊界條件和錯誤處理測試
    # =========================================================================
    
    @pytest.mark.sgp4
    def test_invalid_tle_data_handling(self, sgp4_engine):
        """
        測試無效TLE數據的錯誤處理 (SGP4引擎返回錯誤結果對象，不拋出異常)
        """
        # Given: 無效的TLE數據 (空的line1和line2)
        invalid_tle = {
            'line1': '',
            'line2': '',
            'epoch_datetime': datetime.now(timezone.utc),
            'satellite_name': 'TEST'
        }
        
        # When: 嘗試計算無效TLE數據的位置
        result = sgp4_engine.calculate_position(invalid_tle, datetime.now(timezone.utc))
        
        # Then: 應該返回失敗結果
        assert result is not None, "應該返回錯誤結果對象，不是None"
        assert not result.calculation_successful, "計算不應該成功"
        assert result.position is None, "位置信息應該為空"
        assert result.velocity is None, "速度信息應該為空"
        assert "TLE數據不完整" in result.error_message, "錯誤訊息應包含TLE數據不完整"
    
    @pytest.mark.sgp4
    def test_future_time_calculation(self, sgp4_engine, real_starlink_tle):
        """
        測試未來時間的軌道預測
        """
        # Given: TLE數據和未來時間
        tle_data = real_starlink_tle
        tle_epoch = get_tle_epoch_time(tle_data)
        future_time = tle_epoch + timedelta(hours=2)  # 2小時後
        
        # When: 預測未來位置
        result = sgp4_engine.calculate_position(tle_data, future_time)
        
        # Then: 計算應該成功
        assert result is not None, "未來時間預測必須成功"
        
        # 預測時間應該準確記錄
        assert result.calculation_base_time == future_time, "預測時間必須準確"
        
        # 軌道應該有所變化 (衛星在移動)
        # 這裡可以添加更詳細的軌道變化驗證
    
    # =========================================================================
    # 學術合規和數據真實性測試
    # =========================================================================
    
    @pytest.mark.compliance
    @pytest.mark.real_data
    def test_academic_data_standards_compliance(self, sgp4_engine, real_tle_batch, academic_compliance_checker):
        """
        測試學術級數據使用標準合規性
        """
        for tle_data in real_tle_batch:
            # Given: 真實TLE數據
            assert tle_data.get('is_real_data', False), "必須使用真實TLE數據"
            
            # 學術合規檢查
            academic_compliance_checker(
                tle_data['data_source'],
                "SGP4 orbital propagation with real TLE data"
            )
            
            # When: 計算軌道
            calculation_time = get_tle_epoch_time(tle_data)
            result = sgp4_engine.calculate_position(tle_data, calculation_time)
            
            # Then: 結果必須可追溯和可重現
            assert hasattr(result, 'data_lineage'), "結果必須包含數據血統信息"
            assert result.data_source_verified == True, "數據來源必須已驗證"
    
    @pytest.mark.compliance
    def test_no_mock_data_usage_detection(self, sgp4_engine):
        """
        🚨 檢測系統是否使用了模擬數據
        """
        # Given: 檢查是否有使用模擬數據的跡象
        test_data = load_test_tle_data(constellation='starlink', count=3)
        
        for tle_data in test_data:
            # 檢查數據來源
            data_source = tle_data['data_source'].lower()
            
            # 禁用的模擬數據關鍵字
            forbidden_patterns = [
                'mock', 'fake', 'random', 'generated', 'simulated',
                'test', 'sample', '模擬', '假設', '隨機'
            ]
            
            for pattern in forbidden_patterns:
                assert pattern not in data_source, \
                    f"🚨 檢測到禁用的數據模式 '{pattern}' 在數據來源 '{data_source}' 中"
            
            # 必須標記為真實數據
            assert tle_data.get('is_real_data', False), \
                f"數據必須標記為真實數據: {tle_data.get('satellite_name', 'Unknown')}"
    
    # =========================================================================
    # 整合測試
    # =========================================================================
    
    @pytest.mark.integration
    @pytest.mark.sgp4
    def test_sgp4_engine_full_workflow(self, sgp4_engine, real_tle_batch):
        """
        測試SGP4引擎的完整工作流程
        """
        # Given: 真實TLE數據批次
        tle_batch = real_tle_batch
        
        results = []
        processing_times = []
        
        for tle_data in tle_batch:
            # When: 使用正確的時間基準計算
            start_time = time.perf_counter()
            calculation_time = get_tle_epoch_time(tle_data)  # 🚨 正確時間基準
            
            result = sgp4_engine.calculate_position(tle_data, calculation_time)
            
            processing_time = time.perf_counter() - start_time
            
            # Then: 驗證每個結果
            assert result is not None, f"計算失敗: {tle_data.get('satellite_name')}"
            assert result.algorithm_used == "SGP4", "必須使用SGP4算法"
            assert result.calculation_base_time == calculation_time, "時間基準必須正確"
            
            results.append(result)
            processing_times.append(processing_time)
        
        # 整體驗證
        assert len(results) == len(tle_batch), "必須處理所有TLE數據"
        assert all(r.calculation_successful for r in results), "所有計算都必須成功"
        
        # 性能統計
        total_time = sum(processing_times)
        avg_time = total_time / len(processing_times)
        
        print(f"✅ 完整工作流程測試通過:")
        print(f"   處理衛星數量: {len(tle_batch)}")
        print(f"   總處理時間: {total_time:.3f}秒") 
        print(f"   平均處理時間: {avg_time*1000:.1f}ms/顆")
        print(f"   處理效率: {len(tle_batch)/total_time:.1f}顆/秒")