"""
Phase 3.2.2.3: ML 驅動預測模型 API

提供機器學習預測模型的 RESTful API 接口，包括：
1. 模型管理和註冊
2. 模型訓練和更新
3. 預測請求和結果獲取
4. 集成預測和模型比較
5. 性能監控和指標查詢
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, UploadFile, File
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from enum import Enum
import logging
import asyncio
import numpy as np
import json
import tempfile
import os

from ...algorithms.ml.prediction_models import (
    MLPredictionEngine,
    MLPredictionModel,
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

logger = logging.getLogger(__name__)

# 全局ML預測引擎實例
_ml_engine: Optional[MLPredictionEngine] = None

router = APIRouter(prefix="/ml-prediction", tags=["ml-prediction"])


# === Pydantic 模型定義 ===

class ModelTypeEnum(str, Enum):
    """模型類型枚舉"""
    ORBIT_PREDICTION = "orbit_prediction"
    HANDOVER_DECISION = "handover_decision"
    QOS_PREDICTION = "qos_prediction"
    LOAD_PREDICTION = "load_prediction"
    ANOMALY_DETECTION = "anomaly_detection"
    RESOURCE_OPTIMIZATION = "resource_optimization"


class PredictionTargetEnum(str, Enum):
    """預測目標枚舉"""
    SIGNAL_STRENGTH = "signal_strength"
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    PACKET_LOSS = "packet_loss"
    HANDOVER_SUCCESS = "handover_success"
    SATELLITE_LOAD = "satellite_load"
    ORBITAL_POSITION = "orbital_position"
    DOPPLER_SHIFT = "doppler_shift"


class TrainingStatusEnum(str, Enum):
    """訓練狀態枚舉"""
    NOT_STARTED = "not_started"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"
    UPDATING = "updating"


class ModelCreateRequest(BaseModel):
    """模型創建請求"""
    model_id: Optional[str] = Field(None, description="模型ID（可選，自動生成）")
    model_type: ModelTypeEnum = Field(..., description="模型類型")
    prediction_target: PredictionTargetEnum = Field(..., description="預測目標")
    model_parameters: Dict[str, Any] = Field(default_factory=dict, description="模型參數")
    config_overrides: Dict[str, Any] = Field(default_factory=dict, description="配置覆蓋")


class ModelInfoResponse(BaseModel):
    """模型信息響應"""
    model_id: str = Field(..., description="模型ID")
    model_type: str = Field(..., description="模型類型")
    prediction_target: str = Field(..., description="預測目標")
    version: str = Field(..., description="模型版本")
    is_trained: bool = Field(..., description="是否已訓練")
    training_status: str = Field(..., description="訓練狀態")
    last_training_time: Optional[str] = Field(None, description="最後訓練時間")
    model_class: Optional[str] = Field(None, description="模型類別")
    config: Dict[str, Any] = Field(..., description="模型配置")
    stats: Dict[str, Any] = Field(..., description="統計信息")
    latest_metrics: Optional[Dict[str, Any]] = Field(None, description="最新指標")


class TrainingRequest(BaseModel):
    """訓練請求"""
    model_id: str = Field(..., description="模型ID")
    training_data_type: str = Field("qos", description="訓練數據類型（orbit/qos）")
    validation_split: float = Field(0.2, ge=0.0, le=0.5, description="驗證集比例")
    custom_data: Optional[Dict[str, Any]] = Field(None, description="自定義訓練數據")


class PredictionRequest(BaseModel):
    """預測請求"""
    model_id: str = Field(..., description="模型ID")
    features: Dict[str, Any] = Field(..., description="輸入特徵")
    use_cache: bool = Field(True, description="是否使用緩存")
    return_uncertainty: bool = Field(False, description="是否返回不確定性邊界")
    return_feature_importance: bool = Field(False, description="是否返回特徵重要性")


class EnsemblePredictionRequest(BaseModel):
    """集成預測請求"""
    model_type: ModelTypeEnum = Field(..., description="模型類型")
    prediction_target: PredictionTargetEnum = Field(..., description="預測目標")
    features: Dict[str, Any] = Field(..., description="輸入特徵")
    min_models: int = Field(1, ge=1, description="最少模型數量")


class PredictionResponse(BaseModel):
    """預測響應"""
    prediction_id: str = Field(..., description="預測ID")
    model_id: str = Field(..., description="模型ID")
    predicted_value: float = Field(..., description="預測值")
    confidence_score: float = Field(..., description="置信度分數")
    prediction_timestamp: str = Field(..., description="預測時間戳")
    model_version: str = Field(..., description="模型版本")
    input_features: Dict[str, Any] = Field(..., description="輸入特徵")
    feature_importance: Optional[Dict[str, float]] = Field(None, description="特徵重要性")
    uncertainty_bounds: Optional[List[float]] = Field(None, description="不確定性邊界")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元數據")


class ModelMetricsResponse(BaseModel):
    """模型指標響應"""
    model_id: str = Field(..., description="模型ID")
    mse: float = Field(..., description="均方誤差")
    mae: float = Field(..., description="平均絕對誤差")
    rmse: float = Field(..., description="均方根誤差")
    r2_score: float = Field(..., description="決定係數")
    training_time_ms: float = Field(..., description="訓練時間(毫秒)")
    inference_time_ms: float = Field(..., description="推理時間(毫秒)")
    model_size_bytes: int = Field(..., description="模型大小(字節)")
    last_updated: str = Field(..., description="最後更新時間")


class EngineStatusResponse(BaseModel):
    """引擎狀態響應"""
    engine_id: str = Field(..., description="引擎ID")
    is_running: bool = Field(..., description="是否運行中")
    total_models: int = Field(..., description="總模型數")
    active_models: int = Field(..., description="活躍模型數")
    total_predictions: int = Field(..., description="總預測次數")
    cache_hit_rate: float = Field(..., description="緩存命中率")
    prediction_cache_size: int = Field(..., description="預測緩存大小")
    registered_model_types: Dict[str, int] = Field(..., description="註冊的模型類型")
    stats: Dict[str, Any] = Field(..., description="統計信息")


class ModelComparisonResponse(BaseModel):
    """模型比較響應"""
    model_type: str = Field(..., description="模型類型")
    prediction_target: str = Field(..., description="預測目標")
    models: List[Dict[str, Any]] = Field(..., description="模型列表")
    best_model_id: Optional[str] = Field(None, description="最佳模型ID")
    comparison_metrics: Dict[str, Any] = Field(..., description="比較指標")


# === 依賴注入 ===

async def get_ml_engine() -> MLPredictionEngine:
    """獲取ML預測引擎實例"""
    global _ml_engine
    if _ml_engine is None:
        _ml_engine = create_ml_prediction_engine("api_ml_engine")
        await _ml_engine.start_engine()
    return _ml_engine


# === API 端點實現 ===

@router.post("/models", response_model=ModelInfoResponse)
async def create_model(
    request: ModelCreateRequest,
    engine: MLPredictionEngine = Depends(get_ml_engine)
):
    """創建新的ML模型"""
    if not SKLEARN_AVAILABLE:
        raise HTTPException(status_code=503, detail="scikit-learn不可用，無法創建ML模型")
    
    try:
        # 根據模型類型創建模型
        if request.model_type == ModelTypeEnum.ORBIT_PREDICTION:
            model = create_orbit_prediction_model(request.model_id)
        elif request.model_type == ModelTypeEnum.HANDOVER_DECISION:
            model = create_handover_prediction_model(request.model_id)
        elif request.model_type == ModelTypeEnum.QOS_PREDICTION:
            target = PredictionTarget(request.prediction_target.value)
            model = create_qos_prediction_model(request.model_id, target)
        else:
            # 通用模型創建
            model = MLPredictionModel(
                model_id=request.model_id,
                model_type=ModelType(request.model_type.value),
                prediction_target=PredictionTarget(request.prediction_target.value)
            )
            model.initialize_model(**request.model_parameters)
        
        # 應用配置覆蓋
        if request.config_overrides:
            model.config.update(request.config_overrides)
        
        # 註冊模型
        success = engine.register_model(model)
        if not success:
            raise HTTPException(status_code=500, detail="模型註冊失敗")
        
        # 返回模型信息
        model_info = model.get_model_info()
        return ModelInfoResponse(**model_info)
        
    except Exception as e:
        logger.error(f"創建模型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"創建模型失敗: {str(e)}")


@router.get("/models", response_model=List[ModelInfoResponse])
async def list_models(
    model_type: Optional[ModelTypeEnum] = None,
    prediction_target: Optional[PredictionTargetEnum] = None,
    is_trained: Optional[bool] = None,
    engine: MLPredictionEngine = Depends(get_ml_engine)
):
    """列出所有模型"""
    try:
        models = []
        
        for model_id, model in engine.models.items():
            # 應用過濾條件
            if model_type and model.model_type.value != model_type.value:
                continue
            if prediction_target and model.prediction_target.value != prediction_target.value:
                continue
            if is_trained is not None and model.is_trained != is_trained:
                continue
            
            model_info = model.get_model_info()
            models.append(ModelInfoResponse(**model_info))
        
        return models
        
    except Exception as e:
        logger.error(f"列出模型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"列出模型失敗: {str(e)}")


@router.get("/models/{model_id}", response_model=ModelInfoResponse)
async def get_model_info(
    model_id: str,
    engine: MLPredictionEngine = Depends(get_ml_engine)
):
    """獲取指定模型信息"""
    try:
        if model_id not in engine.models:
            raise HTTPException(status_code=404, detail="模型未找到")
        
        model = engine.models[model_id]
        model_info = model.get_model_info()
        return ModelInfoResponse(**model_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取模型信息失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取模型信息失敗: {str(e)}")


@router.delete("/models/{model_id}")
async def delete_model(
    model_id: str,
    engine: MLPredictionEngine = Depends(get_ml_engine)
):
    """刪除模型"""
    try:
        success = engine.unregister_model(model_id)
        if not success:
            raise HTTPException(status_code=404, detail="模型未找到")
        
        return {
            "model_id": model_id,
            "status": "deleted",
            "message": "模型已成功刪除"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除模型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"刪除模型失敗: {str(e)}")


@router.post("/models/{model_id}/train", response_model=ModelMetricsResponse)
async def train_model(
    model_id: str,
    request: TrainingRequest,
    background_tasks: BackgroundTasks,
    engine: MLPredictionEngine = Depends(get_ml_engine)
):
    """訓練模型"""
    if not SKLEARN_AVAILABLE:
        raise HTTPException(status_code=503, detail="scikit-learn不可用，無法訓練模型")
    
    try:
        if model_id not in engine.models:
            raise HTTPException(status_code=404, detail="模型未找到")
        
        # 獲取或創建訓練數據
        if request.custom_data:
            # 使用自定義數據
            training_data = TrainingData(
                feature_data=np.array(request.custom_data['features']),
                target_data=np.array(request.custom_data['targets']),
                feature_names=request.custom_data.get('feature_names', []),
                target_name=request.custom_data.get('target_name', 'target'),
                timestamp=datetime.now(timezone.utc),
                data_source='custom'
            )
        else:
            # 使用示例數據
            training_data = create_sample_training_data(request.training_data_type)
        
        # 訓練模型
        metrics = await engine.train_model(model_id, training_data)
        
        return ModelMetricsResponse(
            model_id=model_id,
            mse=metrics.mse,
            mae=metrics.mae,
            rmse=metrics.rmse,
            r2_score=metrics.r2_score,
            training_time_ms=metrics.training_time_ms,
            inference_time_ms=metrics.inference_time_ms,
            model_size_bytes=metrics.model_size_bytes,
            last_updated=metrics.last_updated.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"訓練模型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"訓練模型失敗: {str(e)}")


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    request: PredictionRequest,
    engine: MLPredictionEngine = Depends(get_ml_engine)
):
    """進行預測"""
    try:
        if request.model_id not in engine.models:
            raise HTTPException(status_code=404, detail="模型未找到")
        
        model = engine.models[request.model_id]
        if not model.is_trained:
            raise HTTPException(status_code=400, detail="模型尚未訓練")
        
        # 進行預測
        result = await engine.predict(
            request.model_id,
            request.features,
            use_cache=request.use_cache
        )
        
        # 構建響應
        response_data = {
            "prediction_id": result.prediction_id,
            "model_id": result.model_id,
            "predicted_value": result.predicted_value,
            "confidence_score": result.confidence_score,
            "prediction_timestamp": result.prediction_timestamp.isoformat(),
            "model_version": result.model_version,
            "input_features": result.input_features,
            "metadata": result.metadata
        }
        
        # 可選字段
        if request.return_feature_importance and result.feature_importance:
            response_data["feature_importance"] = result.feature_importance
        
        if request.return_uncertainty and result.uncertainty_bounds:
            response_data["uncertainty_bounds"] = list(result.uncertainty_bounds)
        
        return PredictionResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"預測失敗: {e}")
        raise HTTPException(status_code=500, detail=f"預測失敗: {str(e)}")


@router.post("/predict/ensemble", response_model=PredictionResponse)
async def predict_ensemble(
    request: EnsemblePredictionRequest,
    engine: MLPredictionEngine = Depends(get_ml_engine)
):
    """進行集成預測"""
    try:
        # 檢查是否有足夠的模型
        model_type = ModelType(request.model_type.value)
        prediction_target = PredictionTarget(request.prediction_target.value)
        
        available_models = [
            model for model in engine.models.values()
            if (model.model_type == model_type and 
                model.prediction_target == prediction_target and
                model.is_trained)
        ]
        
        if len(available_models) < request.min_models:
            raise HTTPException(
                status_code=400, 
                detail=f"可用模型數量不足: {len(available_models)} < {request.min_models}"
            )
        
        # 進行集成預測
        result = await engine.predict_with_ensemble(
            model_type,
            prediction_target,
            request.features
        )
        
        return PredictionResponse(
            prediction_id=result.prediction_id,
            model_id=result.model_id,
            predicted_value=result.predicted_value,
            confidence_score=result.confidence_score,
            prediction_timestamp=result.prediction_timestamp.isoformat(),
            model_version=result.model_version,
            input_features=result.input_features,
            metadata=result.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"集成預測失敗: {e}")
        raise HTTPException(status_code=500, detail=f"集成預測失敗: {str(e)}")


@router.get("/models/compare", response_model=ModelComparisonResponse)
async def compare_models(
    model_type: ModelTypeEnum,
    prediction_target: PredictionTargetEnum,
    engine: MLPredictionEngine = Depends(get_ml_engine)
):
    """比較同類型模型的性能"""
    try:
        # 獲取同類型的已訓練模型
        target_type = ModelType(model_type.value)
        target_prediction = PredictionTarget(prediction_target.value)
        
        relevant_models = []
        for model in engine.models.values():
            if (model.model_type == target_type and 
                model.prediction_target == target_prediction and
                model.is_trained and model.metrics_history):
                relevant_models.append(model)
        
        if not relevant_models:
            raise HTTPException(status_code=404, detail="未找到可比較的已訓練模型")
        
        # 收集模型信息和指標
        models_data = []
        best_model = None
        best_r2_score = -float('inf')
        
        for model in relevant_models:
            latest_metrics = model.metrics_history[-1]
            model_data = {
                "model_id": model.model_id,
                "model_class": type(model.model).__name__ if model.model else "Unknown",
                "is_trained": model.is_trained,
                "training_sessions": model.stats['training_sessions'],
                "predictions_made": model.stats['predictions_made'],
                "metrics": {
                    "mse": latest_metrics.mse,
                    "mae": latest_metrics.mae,
                    "rmse": latest_metrics.rmse,
                    "r2_score": latest_metrics.r2_score,
                    "training_time_ms": latest_metrics.training_time_ms,
                    "model_size_bytes": latest_metrics.model_size_bytes
                }
            }
            models_data.append(model_data)
            
            # 找到最佳模型
            if latest_metrics.r2_score > best_r2_score:
                best_r2_score = latest_metrics.r2_score
                best_model = model
        
        # 計算比較指標
        r2_scores = [m["metrics"]["r2_score"] for m in models_data]
        training_times = [m["metrics"]["training_time_ms"] for m in models_data]
        
        comparison_metrics = {
            "total_models": len(models_data),
            "best_r2_score": max(r2_scores),
            "average_r2_score": sum(r2_scores) / len(r2_scores),
            "r2_score_std": np.std(r2_scores),
            "average_training_time_ms": sum(training_times) / len(training_times),
            "total_predictions": sum(m["predictions_made"] for m in models_data)
        }
        
        return ModelComparisonResponse(
            model_type=model_type.value,
            prediction_target=prediction_target.value,
            models=models_data,
            best_model_id=best_model.model_id if best_model else None,
            comparison_metrics=comparison_metrics
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"模型比較失敗: {e}")
        raise HTTPException(status_code=500, detail=f"模型比較失敗: {str(e)}")


@router.get("/status", response_model=EngineStatusResponse)
async def get_engine_status(
    engine: MLPredictionEngine = Depends(get_ml_engine)
):
    """獲取ML預測引擎狀態"""
    try:
        status = engine.get_engine_status()
        
        return EngineStatusResponse(
            engine_id=status['engine_id'],
            is_running=status['is_running'],
            total_models=status['total_models'],
            active_models=status['active_models'],
            total_predictions=status['total_predictions'],
            cache_hit_rate=status['cache_hit_rate'],
            prediction_cache_size=status['prediction_cache_size'],
            registered_model_types=status['registered_model_types'],
            stats=status['stats']
        )
        
    except Exception as e:
        logger.error(f"獲取引擎狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取狀態失敗: {str(e)}")


@router.post("/models/{model_id}/save")
async def save_model(
    model_id: str,
    engine: MLPredictionEngine = Depends(get_ml_engine)
):
    """保存模型到文件"""
    try:
        if model_id not in engine.models:
            raise HTTPException(status_code=404, detail="模型未找到")
        
        model = engine.models[model_id]
        
        # 創建保存路徑
        save_dir = "/tmp/ml_models"
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, f"{model_id}.pkl")
        
        # 保存模型
        success = model.save_model(file_path)
        if not success:
            raise HTTPException(status_code=500, detail="模型保存失敗")
        
        return {
            "model_id": model_id,
            "file_path": file_path,
            "status": "saved",
            "message": "模型已成功保存"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存模型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"保存模型失敗: {str(e)}")


@router.get("/health")
async def health_check(
    engine: MLPredictionEngine = Depends(get_ml_engine)
):
    """健康檢查"""
    try:
        status = engine.get_engine_status()
        
        # 健康狀態評估
        health_score = 1.0
        issues = []
        
        # 檢查引擎運行狀態
        if not status['is_running']:
            health_score -= 0.5
            issues.append("引擎未運行")
        
        # 檢查模型可用性
        if status['active_models'] == 0:
            health_score -= 0.3
            issues.append("沒有可用的已訓練模型")
        
        # 檢查緩存命中率
        if status['cache_hit_rate'] < 0.5 and status['total_predictions'] > 100:
            health_score -= 0.2
            issues.append("緩存命中率較低")
        
        # 檢查scikit-learn可用性
        if not SKLEARN_AVAILABLE:
            health_score -= 0.4
            issues.append("scikit-learn不可用")
        
        health_status = "healthy" if health_score >= 0.8 else "degraded" if health_score >= 0.5 else "unhealthy"
        
        return {
            "status": health_status,
            "health_score": round(health_score, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "engine_id": status['engine_id'],
            "is_running": status['is_running'],
            "sklearn_available": SKLEARN_AVAILABLE,
            "issues": issues,
            "summary": {
                "total_models": status['total_models'],
                "active_models": status['active_models'],
                "total_predictions": status['total_predictions'],
                "cache_hit_rate": status['cache_hit_rate']
            }
        }
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return {
            "status": "unhealthy",
            "health_score": 0.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }


# === 測試端點 ===

@router.post("/test/create-sample-models")
async def create_sample_models(
    engine: MLPredictionEngine = Depends(get_ml_engine)
):
    """創建示例模型並訓練（用於測試）"""
    if not SKLEARN_AVAILABLE:
        raise HTTPException(status_code=503, detail="scikit-learn不可用")
    
    try:
        created_models = []
        
        # 創建QoS吞吐量預測模型
        throughput_model = create_qos_prediction_model("sample_throughput", PredictionTarget.THROUGHPUT)
        engine.register_model(throughput_model)
        qos_data = create_sample_training_data("qos")
        await engine.train_model(throughput_model.model_id, qos_data)
        created_models.append(throughput_model.model_id)
        
        # 創建QoS延遲預測模型
        latency_model = create_qos_prediction_model("sample_latency", PredictionTarget.LATENCY)
        engine.register_model(latency_model)
        await engine.train_model(latency_model.model_id, qos_data)
        created_models.append(latency_model.model_id)
        
        # 創建軌道預測模型
        orbit_model = create_orbit_prediction_model("sample_orbit")
        engine.register_model(orbit_model)
        orbit_data = create_sample_training_data("orbit")
        await engine.train_model(orbit_model.model_id, orbit_data)
        created_models.append(orbit_model.model_id)
        
        return {
            "status": "success",
            "message": "示例模型創建並訓練完成",
            "created_models": created_models,
            "model_count": len(created_models)
        }
        
    except Exception as e:
        logger.error(f"創建示例模型失敗: {e}")
        raise HTTPException(status_code=500, detail=f"創建示例模型失敗: {str(e)}")


@router.post("/test/predict-sample")
async def predict_sample(
    model_id: str = "sample_throughput",
    engine: MLPredictionEngine = Depends(get_ml_engine)
):
    """使用示例數據進行預測測試"""
    try:
        # 示例特徵
        sample_features = {
            'signal_strength_dbm': -95.0,
            'elevation_angle': 30.0,
            'distance_km': 1200.0,
            'satellite_load': 0.5,
            'user_count': 50,
            'available_bandwidth_mbps': 500.0,
            'current_throughput_mbps': 30.0,
            'current_latency_ms': 150.0
        }
        
        # 進行預測
        result = await engine.predict(model_id, sample_features)
        
        return {
            "status": "success",
            "message": "示例預測完成",
            "prediction_result": {
                "prediction_id": result.prediction_id,
                "predicted_value": result.predicted_value,
                "confidence_score": result.confidence_score,
                "input_features": result.input_features,
                "inference_time_ms": result.metadata.get('inference_time_ms', 0)
            }
        }
        
    except Exception as e:
        logger.error(f"示例預測失敗: {e}")
        raise HTTPException(status_code=500, detail=f"示例預測失敗: {str(e)}")


# 路由包含函數
def include_ml_prediction_router(app):
    """包含ML預測路由到應用"""
    app.include_router(router)
    logger.info("✅ ML驅動預測模型 API 路由已註冊")