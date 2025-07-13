"""
RL System Integration E2E Tests

端到端測試統一後的RL系統功能
"""

import pytest
import asyncio
import httpx
from typing import Dict, Any
import json
import time


class TestRLIntegrationE2E:
    """RL系統整合端到端測試"""

    @pytest.fixture(scope="class")
    def api_client(self):
        """創建API客戶端"""
        return httpx.AsyncClient(base_url="http://localhost:8080", timeout=30.0)

    @pytest.mark.asyncio
    async def test_health_check(self, api_client):
        """測試健康檢查"""
        response = await api_client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_rl_training_endpoints_available(self, api_client):
        """測試RL訓練端點是否可用"""
        # 測試獲取可用算法
        response = await api_client.get("/api/v1/rl/algorithms")
        assert response.status_code == 200

        data = response.json()
        assert "algorithms" in data
        assert len(data["algorithms"]) > 0

    @pytest.mark.asyncio
    async def test_rl_training_start_stop_flow(self, api_client):
        """測試RL訓練開始-停止流程"""
        # 1. 開始訓練
        training_request = {
            "algorithm": "dqn",
            "environment": "CartPole-v1",
            "config": {"total_episodes": 5, "step_time": 0.1},
        }

        response = await api_client.post(
            "/api/v1/rl/training/start", json=training_request
        )
        assert response.status_code == 200

        start_data = response.json()
        assert "session_id" in start_data
        assert start_data["status"] == "started"

        session_id = start_data["session_id"]

        # 2. 等待訓練開始
        await asyncio.sleep(2)

        # 3. 檢查訓練狀態
        response = await api_client.get(f"/api/v1/rl/training/status/{session_id}")
        assert response.status_code == 200

        status_data = response.json()
        assert status_data["session_id"] == session_id
        assert status_data["status"] in ["running", "training"]

        # 4. 停止訓練
        response = await api_client.post(f"/api/v1/rl/training/stop/{session_id}")
        assert response.status_code == 200

        stop_data = response.json()
        assert stop_data["status"] == "stopped"

        # 5. 等待停止完成
        await asyncio.sleep(1)

        # 6. 驗證訓練已停止
        response = await api_client.get(f"/api/v1/rl/training/status/{session_id}")
        assert response.status_code == 200

        final_status = response.json()
        assert final_status["status"] in ["stopped", "completed"]

    @pytest.mark.asyncio
    async def test_rl_training_sessions_list(self, api_client):
        """測試獲取訓練會話列表"""
        response = await api_client.get("/api/v1/rl/training/sessions")
        assert response.status_code == 200

        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)

    @pytest.mark.asyncio
    async def test_multiple_algorithm_support(self, api_client):
        """測試多種算法支援"""
        # 獲取可用算法
        response = await api_client.get("/api/v1/rl/algorithms")
        assert response.status_code == 200

        algorithms_data = response.json()
        algorithms = algorithms_data["algorithms"]

        # 測試每種算法
        for algorithm in algorithms[:2]:  # 只測試前2個算法以節省時間
            training_request = {
                "algorithm": algorithm,
                "environment": "CartPole-v1",
                "config": {"total_episodes": 3, "step_time": 0.1},
            }

            # 開始訓練
            response = await api_client.post(
                "/api/v1/rl/training/start", json=training_request
            )
            assert response.status_code == 200

            start_data = response.json()
            session_id = start_data["session_id"]

            # 等待一段時間
            await asyncio.sleep(1)

            # 停止訓練
            response = await api_client.post(f"/api/v1/rl/training/stop/{session_id}")
            assert response.status_code == 200

            # 等待停止完成
            await asyncio.sleep(1)

    @pytest.mark.asyncio
    async def test_unified_engine_flag(self, api_client):
        """測試統一引擎標誌"""
        # 開始訓練
        training_request = {
            "algorithm": "dqn",
            "environment": "CartPole-v1",
            "config": {"total_episodes": 3, "step_time": 0.1},
        }

        response = await api_client.post(
            "/api/v1/rl/training/start", json=training_request
        )
        assert response.status_code == 200

        data = response.json()
        # 驗證統一引擎標誌
        assert data.get("unified_engine") == True

        session_id = data["session_id"]

        # 停止訓練
        await api_client.post(f"/api/v1/rl/training/stop/{session_id}")

        # 等待停止完成
        await asyncio.sleep(1)

    @pytest.mark.asyncio
    async def test_error_handling(self, api_client):
        """測試錯誤處理"""
        # 測試無效算法
        training_request = {
            "algorithm": "invalid_algorithm",
            "environment": "CartPole-v1",
            "config": {"total_episodes": 3, "step_time": 0.1},
        }

        response = await api_client.post(
            "/api/v1/rl/training/start", json=training_request
        )
        # 應該返回錯誤或者回退到默認算法
        assert response.status_code in [200, 400, 422]

        # 測試無效會話ID
        response = await api_client.get("/api/v1/rl/training/status/invalid_session_id")
        assert response.status_code in [404, 400]

        # 測試停止無效會話
        response = await api_client.post("/api/v1/rl/training/stop/invalid_session_id")
        assert response.status_code in [404, 400]

    @pytest.mark.asyncio
    async def test_performance_baseline(self, api_client):
        """測試性能基準"""
        # 測試API響應時間
        start_time = time.time()

        response = await api_client.get("/api/v1/rl/algorithms")

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 5.0  # 響應時間應該小於5秒

        # 測試訓練啟動時間
        start_time = time.time()

        training_request = {
            "algorithm": "dqn",
            "environment": "CartPole-v1",
            "config": {"total_episodes": 3, "step_time": 0.1},
        }

        response = await api_client.post(
            "/api/v1/rl/training/start", json=training_request
        )

        end_time = time.time()
        start_response_time = end_time - start_time

        assert response.status_code == 200
        assert start_response_time < 10.0  # 啟動時間應該小於10秒

        # 清理
        if response.status_code == 200:
            session_id = response.json()["session_id"]
            await api_client.post(f"/api/v1/rl/training/stop/{session_id}")
            await asyncio.sleep(1)

    @pytest.mark.asyncio
    async def test_mongodb_integration(self, api_client):
        """測試MongoDB整合"""
        # 開始訓練以觸發MongoDB存儲
        training_request = {
            "algorithm": "dqn",
            "environment": "CartPole-v1",
            "config": {"total_episodes": 3, "step_time": 0.1},
        }

        response = await api_client.post(
            "/api/v1/rl/training/start", json=training_request
        )
        assert response.status_code == 200

        session_id = response.json()["session_id"]

        # 等待訓練進行一段時間
        await asyncio.sleep(2)

        # 停止訓練
        response = await api_client.post(f"/api/v1/rl/training/stop/{session_id}")
        assert response.status_code == 200

        # 等待停止完成
        await asyncio.sleep(1)

        # 驗證會話數據被保存
        response = await api_client.get("/api/v1/rl/training/sessions")
        assert response.status_code == 200

        sessions_data = response.json()
        sessions = sessions_data["sessions"]

        # 應該能找到剛創建的會話
        session_found = any(session["session_id"] == session_id for session in sessions)
        assert session_found, f"Session {session_id} not found in sessions list"

    @pytest.mark.asyncio
    async def test_system_stability_after_integration(self, api_client):
        """測試整合後系統穩定性"""
        # 連續進行多次訓練測試系統穩定性
        for i in range(3):
            training_request = {
                "algorithm": "dqn",
                "environment": "CartPole-v1",
                "config": {"total_episodes": 2, "step_time": 0.1},
            }

            # 開始訓練
            response = await api_client.post(
                "/api/v1/rl/training/start", json=training_request
            )
            assert response.status_code == 200

            session_id = response.json()["session_id"]

            # 等待一段時間
            await asyncio.sleep(1)

            # 停止訓練
            response = await api_client.post(f"/api/v1/rl/training/stop/{session_id}")
            assert response.status_code == 200

            # 等待停止完成
            await asyncio.sleep(1)

        # 驗證系統健康狀態
        response = await api_client.get("/api/v1/health")
        assert response.status_code == 200

        health_data = response.json()
        assert health_data["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
