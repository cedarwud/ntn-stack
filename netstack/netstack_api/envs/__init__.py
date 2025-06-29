"""
NetStack Gymnasium 環境包

提供標準化的強化學習環境接口，用於：
- 干擾檢測與緩解
- 網路優化
- UAV 編隊管理
- 自動化決策
"""

from gymnasium.envs.registration import register

# 註冊干擾緩解環境
register(
    id='netstack/InterferenceMitigation-v0',
    entry_point='netstack_api.envs.interference_env:InterferenceMitigationEnv',
    max_episode_steps=1000,
)

# 註冊網路優化環境
register(
    id='netstack/NetworkOptimization-v0', 
    entry_point='netstack_api.envs.optimization_env:NetworkOptimizationEnv',
    max_episode_steps=500,
)

# 註冊 UAV 編隊管理環境
register(
    id='netstack/UAVFormation-v0',
    entry_point='netstack_api.envs.uav_env:UAVFormationEnv', 
    max_episode_steps=2000,
)

# 註冊 LEO 衛星切換環境
register(
    id='netstack/LEOSatelliteHandover-v0',
    entry_point='netstack_api.envs.handover_env_fixed:LEOSatelliteHandoverEnv',
    max_episode_steps=1000,
)

# 註冊優化版環境
register(
    id='netstack/LEOSatelliteHandover-v1',
    entry_point='netstack_api.envs.optimized_handover_env_fixed:OptimizedLEOSatelliteHandoverEnv',
    max_episode_steps=1000,
)

# 註冊極速版環境 (用於基準測試)
register(
    id='netstack/LEOSatelliteHandover-Ultra',
    entry_point='netstack_api.envs.optimized_handover_env_fixed:UltraFastLEOEnv',
    max_episode_steps=1000,
)