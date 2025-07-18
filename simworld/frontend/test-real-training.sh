#!/bin/bash

# 測試真實訓練功能的腳本
# 驗證 NetStack API 連接和真實數據獲取

echo "🔍 測試 NetStack RL 訓練功能"
echo "================================"

# 檢查 NetStack 服務狀態
echo "1. 檢查 NetStack 服務健康狀態..."
curl -s http://localhost:8080/health | jq '.overall_status' || echo "❌ NetStack 服務未運行"

# 檢查可用算法
echo -e "\n2. 檢查可用的 RL 算法..."
curl -s http://localhost:8080/api/v1/rl/algorithms | jq '.algorithms[]' || echo "❌ 無法獲取算法列表"

# 檢查當前訓練狀態
echo -e "\n3. 檢查 DQN 訓練狀態..."
DQN_STATUS=$(curl -s http://localhost:8080/api/v1/rl/training/status/dqn)
echo $DQN_STATUS | jq '.'

IS_TRAINING=$(echo $DQN_STATUS | jq -r '.is_training // false')
echo "DQN 訓練狀態: $IS_TRAINING"

# 如果沒有在訓練，啟動一個測試訓練
if [ "$IS_TRAINING" = "false" ]; then
    echo -e "\n4. 啟動 DQN 測試訓練..."
    START_RESULT=$(curl -s -X POST -H "Content-Type: application/json" \
        -d '{"algorithm": "dqn", "total_episodes": 100, "learning_rate": 0.001}' \
        http://localhost:8080/api/v1/rl/training/start/dqn)
    echo $START_RESULT | jq '.'
    
    SESSION_ID=$(echo $START_RESULT | jq -r '.session_id')
    echo "訓練會話 ID: $SESSION_ID"
    
    # 等待幾秒讓訓練開始
    echo "等待訓練開始..."
    sleep 5
    
    # 再次檢查狀態
    echo -e "\n5. 檢查訓練進度..."
    curl -s http://localhost:8080/api/v1/rl/training/status/dqn | jq '.'
    
    # 停止測試訓練
    echo -e "\n6. 停止測試訓練..."
    STOP_RESULT=$(curl -s -X POST -H "Content-Type: application/json" \
        -d '{"algorithm": "dqn"}' \
        http://localhost:8080/api/v1/rl/training/stop-by-algorithm/dqn)
    echo $STOP_RESULT | jq '.'
else
    echo -e "\n4. DQN 正在訓練中，檢查進度..."
    PROGRESS=$(echo $DQN_STATUS | jq -r '.training_progress.progress_percentage // 0')
    EPISODE=$(echo $DQN_STATUS | jq -r '.training_progress.current_episode // 0')
    REWARD=$(echo $DQN_STATUS | jq -r '.training_progress.current_reward // 0')
    
    echo "進度: ${PROGRESS}%"
    echo "當前 Episode: $EPISODE"
    echo "當前獎勵: $REWARD"
fi

# 測試其他算法狀態
echo -e "\n7. 檢查其他算法狀態..."
echo "PPO 狀態:"
curl -s http://localhost:8080/api/v1/rl/training/status/ppo | jq '.status // "未知"'

echo "SAC 狀態:"
curl -s http://localhost:8080/api/v1/rl/training/status/sac | jq '.status // "未知"'

# 檢查訓練會話列表
echo -e "\n8. 檢查所有訓練會話..."
curl -s http://localhost:8080/api/v1/rl/training/sessions | jq '.' || echo "❌ 無法獲取會話列表"

echo -e "\n✅ 測試完成！"
echo "================================"
echo "如果看到真實的訓練數據，說明系統正常工作"
echo "如果看到錯誤，請檢查 NetStack 服務是否正確運行"
