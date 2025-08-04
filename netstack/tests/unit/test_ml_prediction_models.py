"""
Phase 3.2.2.3 ML 驅動預測模型單元測試

測試ML驅動預測模型的完整實現，包括：
1. 機器學習模型的創建和訓練
2. 預測功能和置信度計算
3. 模型管理和版本控制
4. 集成預測和性能優化
5. 在線學習和模型更新
"""

import pytest
import pytest_asyncio
import asyncio
import numpy as np
import time
import tempfile
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch

# 導入待測試的模組
import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from src.algorithms.ml.prediction_models import (
    MLPredictionModel,
    MLPredictionEngine,
    TrainingData,
    ModelMetrics,
    PredictionResult,
    ModelType,
    PredictionTarget,
    TrainingStatus,
    create_ml_prediction_engine,
    create_orbit_prediction_model,
    create_handover_prediction_model,
    create_qos_prediction_model,
    create_sample_training_data,
    SKLEARN_AVAILABLE
)


class TestTrainingData:
    """測試訓練數據"""
    
    def test_training_data_creation(self):
        """測試訓練數據創建"""
        feature_data = np.random.rand(100, 5)
        target_data = np.random.rand(100)
        
        training_data = TrainingData(
            feature_data=feature_data,
            target_data=target_data,
            feature_names=['f1', 'f2', 'f3', 'f4', 'f5'],
            target_name='target',
            timestamp=datetime.now(timezone.utc),
            data_source='test'
        )
        
        assert training_data.feature_data.shape == (100, 5)
        assert training_data.target_data.shape == (100,)
        assert len(training_data.feature_names) == 5
        assert training_data.target_name == 'target'
        assert training_data.data_source == 'test'
        assert training_data.quality_score == 1.0


class TestModelMetrics:
    """測試模型指標"""
    
    def test_model_metrics_creation(self):
        """測試模型指標創建"""
        metrics = ModelMetrics(
            mse=0.05,
            mae=0.15,
            rmse=0.22,
            r2_score=0.85,
            training_time_ms=1500.0,
            model_size_bytes=1024000
        )
        
        assert metrics.mse == 0.05
        assert metrics.mae == 0.15
        assert metrics.rmse == 0.22
        assert metrics.r2_score == 0.85
        assert metrics.training_time_ms == 1500.0
        assert metrics.model_size_bytes == 1024000
        assert isinstance(metrics.last_updated, datetime)


class TestPredictionResult:
    """測試預測結果"""
    
    def test_prediction_result_creation(self):
        """測試預測結果創建"""
        result = PredictionResult(
            prediction_id="pred_001",
            model_id="model_001",
            input_features={'signal_strength': -95.0, 'elevation': 30.0},
            predicted_value=50.5,
            confidence_score=0.85,
            prediction_timestamp=datetime.now(timezone.utc),
            model_version="1.0.0"
        )
        
        assert result.prediction_id == "pred_001"
        assert result.model_id == "model_001"
        assert result.predicted_value == 50.5
        assert result.confidence_score == 0.85
        assert result.model_version == "1.0.0"
        assert len(result.input_features) == 2


@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not available")
class TestMLPredictionModel:
    """測試ML預測模型"""
    
    @pytest_asyncio.fixture
    async def prediction_model(self):
        """創建測試用預測模型"""
        model = MLPredictionModel(
            model_id="test_model",
            model_type=ModelType.QOS_PREDICTION,
            prediction_target=PredictionTarget.THROUGHPUT
        )
        model.initialize_model(n_estimators=10, max_depth=3)  # 小參數用於測試
        return model
    
    def test_model_initialization(self):
        """測試模型初始化"""
        model = MLPredictionModel(
            model_id="init_test",
            model_type=ModelType.ORBIT_PREDICTION,
            prediction_target=PredictionTarget.ORBITAL_POSITION
        )
        
        assert model.model_id == "init_test"
        assert model.model_type == ModelType.ORBIT_PREDICTION
        assert model.prediction_target == PredictionTarget.ORBITAL_POSITION
        assert model.version == "1.0.0"
        assert model.is_trained is False
        assert model.training_status == TrainingStatus.NOT_STARTED
        assert model.model is None
    
    def test_model_initialization_with_sklearn(self):
        """測試模型初始化（使用scikit-learn）"""
        model = MLPredictionModel(
            model_id="sklearn_test",
            model_type=ModelType.QOS_PREDICTION,
            prediction_target=PredictionTarget.THROUGHPUT
        )
        
        model.initialize_model(n_estimators=50, max_depth=5)
        
        assert model.model is not None
        assert hasattr(model.model, 'fit')
        assert hasattr(model.model, 'predict')
    
    @pytest.mark.asyncio
    async def test_model_training(self, prediction_model):
        """測試模型訓練"""
        # 創建訓練數據
        training_data = create_sample_training_data("qos")
        
        # 訓練模型
        metrics = await prediction_model.train(training_data, validation_split=0.2)
        
        assert prediction_model.is_trained is True
        assert prediction_model.training_status == TrainingStatus.COMPLETED
        assert prediction_model.last_training_time is not None
        assert isinstance(metrics, ModelMetrics)
        assert metrics.mse >= 0
        assert metrics.mae >= 0
        assert metrics.rmse >= 0
        assert metrics.training_time_ms > 0
        assert len(prediction_model.training_history) == 1
        assert len(prediction_model.metrics_history) == 1
    
    @pytest.mark.asyncio
    async def test_model_prediction(self, prediction_model):
        """測試模型預測"""
        # 先訓練模型
        training_data = create_sample_training_data("qos")
        await prediction_model.train(training_data)
        
        # 進行預測
        features = {
            'signal_strength_dbm': -95.0,
            'elevation_angle': 30.0,
            'distance_km': 1200.0,
            'satellite_load': 0.5,
            'user_count': 50,
            'available_bandwidth_mbps': 500.0
        }
        
        result = await prediction_model.predict(features)
        
        assert isinstance(result, PredictionResult)
        assert result.model_id == prediction_model.model_id
        assert isinstance(result.predicted_value, float)
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.prediction_timestamp is not None
        assert result.input_features == features
        assert 'inference_time_ms' in result.metadata
    
    @pytest.mark.asyncio
    async def test_prediction_without_training(self, prediction_model):
        """測試未訓練模型的預測"""
        features = {'test': 1.0}
        
        with pytest.raises(RuntimeError, match="尚未訓練"):
            await prediction_model.predict(features)
    
    def test_feature_vectorization(self, prediction_model):
        """測試特徵向量化"""
        features = {
            'signal_strength_dbm': -95.0,
            'elevation_angle': 30.0,
            'distance_km': 1200.0,
            'satellite_load': 0.5
        }
        
        vector = prediction_model._vectorize_features(features)
        
        assert isinstance(vector, np.ndarray)
        assert len(vector) == 10  # 默認10個特徵
        assert vector[0] == -95.0  # signal_strength_dbm
        assert vector[1] == 30.0   # elevation_angle
        assert vector[2] == 1200.0 # distance_km
        assert vector[3] == 0.5    # satellite_load
    
    def test_confidence_calculation(self, prediction_model):
        """測試置信度計算"""
        features = {
            'signal_strength_dbm': -95.0,
            'elevation_angle': 30.0,
            'distance_km': 1200.0
        }
        
        confidence = prediction_model._calculate_confidence(features, 50.0)
        
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
    
    def test_feature_quality_assessment(self, prediction_model):
        """測試特徵質量評估"""
        # 高質量特徵
        good_features = {
            'signal_strength_dbm': -95.0,
            'elevation_angle': 30.0,
            'distance_km': 1200.0
        }
        quality_good = prediction_model._assess_feature_quality(good_features)
        
        # 低質量特徵
        bad_features = {
            'signal_strength_dbm': float('nan'),
            'elevation_angle': -999.0,  # 無效仰角
            'unknown_field': 'invalid'
        }
        quality_bad = prediction_model._assess_feature_quality(bad_features)
        
        assert 0.0 <= quality_good <= 1.0
        assert 0.0 <= quality_bad <= 1.0
        assert quality_good > quality_bad
    
    def test_prediction_reasonableness_assessment(self, prediction_model):
        """測試預測合理性評估"""
        # 合理的信號強度預測
        if prediction_model.prediction_target == PredictionTarget.SIGNAL_STRENGTH:
            reasonable = prediction_model._assess_prediction_reasonableness(-95.0)
            unreasonable = prediction_model._assess_prediction_reasonableness(-10.0)
            
            assert reasonable > unreasonable
        
        # 合理的吞吐量預測
        if prediction_model.prediction_target == PredictionTarget.THROUGHPUT:
            reasonable = prediction_model._assess_prediction_reasonableness(50.0)
            unreasonable = prediction_model._assess_prediction_reasonableness(-10.0)
            
            assert reasonable > unreasonable
    
    @pytest.mark.asyncio
    async def test_model_update(self, prediction_model):
        """測試模型更新"""
        # 先訓練模型
        training_data = create_sample_training_data("qos")
        await prediction_model.train(training_data)
        
        # 啟用在線學習
        prediction_model.config['online_learning_enabled'] = True
        
        # 創建新的訓練數據
        new_training_data = create_sample_training_data("qos")
        
        # 更新模型
        success = await prediction_model.update_model(new_training_data)
        
        assert success is True
        assert len(prediction_model.training_history) >= 1
    
    def test_model_save_load(self, prediction_model):
        """測試模型保存和加載"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # 保存模型
            save_success = prediction_model.save_model(tmp_path)
            assert save_success is True
            assert os.path.exists(tmp_path)
            
            # 創建新模型並加載
            new_model = MLPredictionModel(
                model_id="load_test",
                model_type=ModelType.QOS_PREDICTION,
                prediction_target=PredictionTarget.THROUGHPUT
            )
            
            load_success = new_model.load_model(tmp_path)
            assert load_success is True
            assert new_model.model_id == prediction_model.model_id
            assert new_model.model_type == prediction_model.model_type
            assert new_model.prediction_target == prediction_model.prediction_target
            
        finally:
            # 清理臨時文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_model_info(self, prediction_model):
        """測試模型信息獲取"""
        info = prediction_model.get_model_info()
        
        assert isinstance(info, dict)
        assert info['model_id'] == 'test_model'
        assert info['model_type'] == ModelType.QOS_PREDICTION.value
        assert info['prediction_target'] == PredictionTarget.THROUGHPUT.value
        assert info['version'] == '1.0.0'
        assert info['is_trained'] is False
        assert info['training_status'] == TrainingStatus.NOT_STARTED.value
        assert 'config' in info
        assert 'stats' in info


@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not available")
class TestMLPredictionEngine:
    """測試ML預測引擎"""
    
    @pytest_asyncio.fixture
    async def prediction_engine(self):
        """創建測試用預測引擎"""
        engine = create_ml_prediction_engine("test_engine")
        await engine.start_engine()
        yield engine
        await engine.stop_engine()
    
    @pytest_asyncio.fixture
    async def trained_model(self):
        """創建已訓練的模型"""
        model = create_qos_prediction_model("trained_model", PredictionTarget.THROUGHPUT)
        training_data = create_sample_training_data("qos")
        await model.train(training_data)
        return model
    
    @pytest.mark.asyncio
    async def test_engine_initialization(self):
        """測試引擎初始化"""
        engine = create_ml_prediction_engine("init_engine")
        
        assert engine.engine_id == "init_engine"
        assert len(engine.models) == 0
        assert len(engine.model_registry) == 0
        assert engine.is_running is False
        assert len(engine.prediction_cache) == 0
    
    @pytest.mark.asyncio
    async def test_engine_start_stop(self):
        """測試引擎啟動和停止"""
        engine = create_ml_prediction_engine("start_stop_engine")
        
        # 啟動引擎
        await engine.start_engine()
        assert engine.is_running is True
        assert engine.maintenance_task is not None
        
        # 停止引擎
        await engine.stop_engine()
        assert engine.is_running is False
    
    @pytest.mark.asyncio
    async def test_model_registration(self, prediction_engine):
        """測試模型註冊"""
        model = create_qos_prediction_model("reg_model")
        
        success = prediction_engine.register_model(model)
        
        assert success is True
        assert "reg_model" in prediction_engine.models
        assert "reg_model" in prediction_engine.model_registry[ModelType.QOS_PREDICTION]
        assert prediction_engine.stats['total_models'] == 1
    
    @pytest.mark.asyncio
    async def test_model_unregistration(self, prediction_engine):
        """測試模型註銷"""
        model = create_qos_prediction_model("unreg_model")
        prediction_engine.register_model(model)
        
        success = prediction_engine.unregister_model("unreg_model")
        
        assert success is True
        assert "unreg_model" not in prediction_engine.models
        assert "unreg_model" not in prediction_engine.model_registry[ModelType.QOS_PREDICTION]
        assert prediction_engine.stats['total_models'] == 0
    
    @pytest.mark.asyncio
    async def test_prediction(self, prediction_engine, trained_model):
        """測試預測"""
        # 註冊已訓練的模型
        prediction_engine.register_model(trained_model)
        
        features = {
            'signal_strength_dbm': -95.0,
            'elevation_angle': 30.0,
            'distance_km': 1200.0,
            'satellite_load': 0.5
        }
        
        result = await prediction_engine.predict(trained_model.model_id, features)
        
        assert isinstance(result, PredictionResult)
        assert result.model_id == trained_model.model_id
        assert isinstance(result.predicted_value, float)
        assert 0.0 <= result.confidence_score <= 1.0
        assert prediction_engine.stats['total_predictions'] == 1
    
    @pytest.mark.asyncio
    async def test_prediction_with_cache(self, prediction_engine, trained_model):
        """測試帶緩存的預測"""
        prediction_engine.register_model(trained_model)
        prediction_engine.config['prediction_cache_enabled'] = True
        
        features = {
            'signal_strength_dbm': -95.0,
            'elevation_angle': 30.0
        }
        
        # 第一次預測（緩存未命中）
        result1 = await prediction_engine.predict(trained_model.model_id, features)
        assert prediction_engine.stats['cache_misses'] == 1
        assert prediction_engine.stats['cache_hits'] == 0
        
        # 第二次預測（緩存命中）
        result2 = await prediction_engine.predict(trained_model.model_id, features)
        assert prediction_engine.stats['cache_hits'] == 1
        assert result1.predicted_value == result2.predicted_value
    
    @pytest.mark.asyncio
    async def test_ensemble_prediction(self, prediction_engine):
        """測試集成預測"""
        # 創建並註冊多個相同類型的模型
        models = []
        for i in range(3):
            model = create_qos_prediction_model(f"ensemble_model_{i}", PredictionTarget.THROUGHPUT)
            training_data = create_sample_training_data("qos")
            await model.train(training_data)
            prediction_engine.register_model(model)
            models.append(model)
        
        features = {
            'signal_strength_dbm': -95.0,
            'elevation_angle': 30.0,
            'distance_km': 1200.0
        }
        
        result = await prediction_engine.predict_with_ensemble(
            ModelType.QOS_PREDICTION, 
            PredictionTarget.THROUGHPUT, 
            features
        )
        
        assert isinstance(result, PredictionResult)
        assert result.model_id.startswith("ensemble_")
        assert result.model_version == "ensemble_1.0"
        assert 'ensemble_size' in result.metadata
        assert result.metadata['ensemble_size'] == 3
        assert 'individual_predictions' in result.metadata
        assert 'model_ids' in result.metadata
    
    @pytest.mark.asyncio
    async def test_model_training(self, prediction_engine):
        """測試模型訓練"""
        model = create_qos_prediction_model("train_model")
        prediction_engine.register_model(model)
        
        training_data = create_sample_training_data("qos")
        
        metrics = await prediction_engine.train_model(model.model_id, training_data)
        
        assert isinstance(metrics, ModelMetrics)
        assert metrics.mse >= 0
        assert model.is_trained is True
        assert prediction_engine.stats['model_training_sessions'] == 1
        assert prediction_engine.stats['active_models'] == 1
    
    @pytest.mark.asyncio
    async def test_best_model_selection(self, prediction_engine):
        """測試最佳模型選擇"""
        # 創建並訓練多個模型
        models = []
        for i in range(3):
            model = create_qos_prediction_model(f"best_model_{i}", PredictionTarget.THROUGHPUT)
            training_data = create_sample_training_data("qos")
            await model.train(training_data)
            prediction_engine.register_model(model)
            models.append(model)
        
        best_model = prediction_engine.get_best_model(
            ModelType.QOS_PREDICTION, 
            PredictionTarget.THROUGHPUT
        )
        
        assert best_model is not None
        assert best_model in models
        assert best_model.is_trained is True
    
    @pytest.mark.asyncio
    async def test_prediction_with_nonexistent_model(self, prediction_engine):
        """測試使用不存在的模型進行預測"""
        features = {'test': 1.0}
        
        with pytest.raises(ValueError, match="模型未找到"):
            await prediction_engine.predict("nonexistent_model", features)
    
    @pytest.mark.asyncio
    async def test_ensemble_with_no_models(self, prediction_engine):
        """測試沒有模型時的集成預測"""
        features = {'test': 1.0}
        
        with pytest.raises(ValueError, match="沒有可用的模型"):
            await prediction_engine.predict_with_ensemble(
                ModelType.QOS_PREDICTION,
                PredictionTarget.THROUGHPUT,
                features
            )
    
    def test_engine_status(self, prediction_engine):
        """測試引擎狀態獲取"""
        status = prediction_engine.get_engine_status()
        
        assert isinstance(status, dict)
        assert status['engine_id'] == prediction_engine.engine_id
        assert status['is_running'] is True
        assert 'total_models' in status
        assert 'active_models' in status
        assert 'total_predictions' in status
        assert 'cache_hit_rate' in status
        assert 'prediction_cache_size' in status
        assert 'registered_model_types' in status
        assert 'config' in status
        assert 'stats' in status


class TestHelperFunctions:
    """測試輔助函數"""
    
    def test_create_ml_prediction_engine(self):
        """測試創建ML預測引擎"""
        engine = create_ml_prediction_engine("helper_engine")
        
        assert isinstance(engine, MLPredictionEngine)
        assert engine.engine_id == "helper_engine"
        assert engine.is_running is False
    
    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not available")
    def test_create_orbit_prediction_model(self):
        """測試創建軌道預測模型"""
        model = create_orbit_prediction_model("orbit_model")
        
        assert isinstance(model, MLPredictionModel)
        assert model.model_id == "orbit_model"
        assert model.model_type == ModelType.ORBIT_PREDICTION
        assert model.prediction_target == PredictionTarget.ORBITAL_POSITION
        assert model.model is not None
    
    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not available")
    def test_create_handover_prediction_model(self):
        """測試創建切換預測模型"""
        model = create_handover_prediction_model("handover_model")
        
        assert isinstance(model, MLPredictionModel)
        assert model.model_id == "handover_model"
        assert model.model_type == ModelType.HANDOVER_DECISION
        assert model.prediction_target == PredictionTarget.HANDOVER_SUCCESS
        assert model.model is not None
    
    @pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not available")
    def test_create_qos_prediction_model(self):
        """測試創建QoS預測模型"""
        model = create_qos_prediction_model("qos_model", PredictionTarget.LATENCY)
        
        assert isinstance(model, MLPredictionModel)
        assert model.model_id == "qos_model"
        assert model.model_type == ModelType.QOS_PREDICTION
        assert model.prediction_target == PredictionTarget.LATENCY
        assert model.model is not None
    
    def test_create_sample_training_data_orbit(self):
        """測試創建軌道訓練數據"""
        training_data = create_sample_training_data("orbit")
        
        assert isinstance(training_data, TrainingData)
        assert training_data.feature_data.shape[1] == 6  # 6個特徵
        assert training_data.feature_data.shape[0] == 1000  # 1000個樣本
        assert len(training_data.target_data) == 1000
        assert len(training_data.feature_names) == 6
        assert training_data.target_name == 'future_lat'
        assert training_data.data_source == 'simulation'
    
    def test_create_sample_training_data_qos(self):
        """測試創建QoS訓練數據"""
        training_data = create_sample_training_data("qos")
        
        assert isinstance(training_data, TrainingData)
        assert training_data.feature_data.shape[1] == 8  # 8個特徵
        assert training_data.feature_data.shape[0] == 800  # 800個樣本
        assert len(training_data.target_data) == 800
        assert len(training_data.feature_names) == 8
        assert training_data.target_name == 'predicted_throughput'
        assert training_data.data_source == 'simulation'
        
        # 檢查數據範圍
        features = training_data.feature_data
        targets = training_data.target_data
        
        # 信號強度範圍
        assert np.all(features[:, 0] >= -120) and np.all(features[:, 0] <= -80)
        # 仰角範圍
        assert np.all(features[:, 1] >= 10) and np.all(features[:, 1] <= 60)
        # 目標值範圍
        assert np.all(targets >= 0) and np.all(targets <= 100)
    
    def test_create_sample_training_data_invalid_type(self):
        """測試創建無效類型的訓練數據"""
        with pytest.raises(ValueError, match="未知的數據類型"):
            create_sample_training_data("invalid_type")


@pytest.mark.skipif(not SKLEARN_AVAILABLE, reason="scikit-learn not available")
class TestIntegrationWorkflow:
    """測試完整工作流程"""
    
    @pytest.mark.asyncio
    async def test_complete_ml_workflow(self):
        """測試完整的ML工作流程"""
        # 1. 創建預測引擎
        engine = create_ml_prediction_engine("workflow_engine")
        await engine.start_engine()
        
        try:
            # 2. 創建多個不同類型的模型
            orbit_model = create_orbit_prediction_model("orbit_workflow")
            handover_model = create_handover_prediction_model("handover_workflow")
            qos_model = create_qos_prediction_model("qos_workflow", PredictionTarget.THROUGHPUT)
            
            # 3. 註冊模型
            engine.register_model(orbit_model)
            engine.register_model(handover_model)
            engine.register_model(qos_model)
            
            assert engine.stats['total_models'] == 3
            
            # 4. 訓練模型
            orbit_data = create_sample_training_data("orbit")
            qos_data = create_sample_training_data("qos")
            
            await engine.train_model(orbit_model.model_id, orbit_data)
            await engine.train_model(qos_model.model_id, qos_data)
            
            assert engine.stats['active_models'] >= 2
            assert engine.stats['model_training_sessions'] == 2
            
            # 5. 進行預測
            features = {
                'signal_strength_dbm': -95.0,
                'elevation_angle': 30.0,
                'distance_km': 1200.0,
                'satellite_load': 0.5,
                'user_count': 50,
                'available_bandwidth_mbps': 500.0
            }
            
            qos_result = await engine.predict(qos_model.model_id, features)
            
            assert isinstance(qos_result, PredictionResult)
            assert qos_result.confidence_score > 0
            assert engine.stats['total_predictions'] == 1
            
            # 6. 測試集成預測（如果有多個相同類型的模型）
            qos_model2 = create_qos_prediction_model("qos_workflow2", PredictionTarget.THROUGHPUT)
            await qos_model2.train(qos_data)
            engine.register_model(qos_model2)
            
            ensemble_result = await engine.predict_with_ensemble(
                ModelType.QOS_PREDICTION,
                PredictionTarget.THROUGHPUT,
                features
            )
            
            assert isinstance(ensemble_result, PredictionResult)
            assert ensemble_result.model_id.startswith("ensemble_")
            assert 'ensemble_size' in ensemble_result.metadata
            
            # 7. 檢查引擎狀態
            status = engine.get_engine_status()
            assert status['total_models'] == 4
            assert status['active_models'] >= 3
            assert status['total_predictions'] >= 2
            
        finally:
            await engine.stop_engine()
    
    @pytest.mark.asyncio
    async def test_model_performance_comparison(self):
        """測試模型性能比較"""
        engine = create_ml_prediction_engine("performance_engine")
        await engine.start_engine()
        
        try:
            # 創建多個QoS預測模型
            models = []
            for i in range(3):
                model = create_qos_prediction_model(f"perf_model_{i}", PredictionTarget.THROUGHPUT)
                
                # 使用不同參數訓練
                if i == 0:
                    model.initialize_model(n_estimators=50, max_depth=5)
                elif i == 1:
                    model.initialize_model(n_estimators=100, max_depth=8)
                else:
                    model.initialize_model(n_estimators=20, max_depth=3)
                
                training_data = create_sample_training_data("qos")
                await model.train(training_data)
                engine.register_model(model)
                models.append(model)
            
            # 比較模型性能
            best_model = engine.get_best_model(ModelType.QOS_PREDICTION, PredictionTarget.THROUGHPUT)
            
            assert best_model is not None
            assert best_model in models
            
            # 檢查最佳模型有最高的R²分數
            best_r2 = best_model.metrics_history[-1].r2_score
            for model in models:
                if model != best_model:
                    model_r2 = model.metrics_history[-1].r2_score
                    assert best_r2 >= model_r2
            
        finally:
            await engine.stop_engine()
    
    @pytest.mark.asyncio
    async def test_prediction_caching_performance(self):
        """測試預測緩存性能"""
        engine = create_ml_prediction_engine("cache_engine")
        engine.config['prediction_cache_enabled'] = True
        engine.config['prediction_cache_ttl_seconds'] = 60
        await engine.start_engine()
        
        try:
            # 創建並訓練模型
            model = create_qos_prediction_model("cache_model", PredictionTarget.THROUGHPUT)
            training_data = create_sample_training_data("qos")
            await model.train(training_data)
            engine.register_model(model)
            
            features = {
                'signal_strength_dbm': -95.0,
                'elevation_angle': 30.0,
                'distance_km': 1200.0
            }
            
            # 第一次預測（無緩存）
            start_time = time.time()
            result1 = await engine.predict(model.model_id, features, use_cache=True)
            first_prediction_time = time.time() - start_time
            
            # 第二次預測（有緩存）
            start_time = time.time()
            result2 = await engine.predict(model.model_id, features, use_cache=True)
            cached_prediction_time = time.time() - start_time
            
            # 緩存預測應該更快
            assert cached_prediction_time < first_prediction_time
            assert result1.predicted_value == result2.predicted_value
            assert engine.stats['cache_hits'] == 1
            assert engine.stats['cache_misses'] == 1
            
        finally:
            await engine.stop_engine()


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v", "--tb=short", "-s"])