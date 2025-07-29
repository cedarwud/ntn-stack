#!/usr/bin/env python3
"""
Phase 3: RL 訓練數據集生成器
基於 Phase 0 預計算結果生成標準化的 RL 訓練數據
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import logging
import sys

# 添加路徑
sys.path.append('/app/src')
sys.path.append('/app')

logger = logging.getLogger(__name__)

class RLDatasetGenerator:
    """RL 訓練數據集生成器"""
    
    def __init__(self, precomputed_orbit_data: Dict):
        self.orbit_data = precomputed_orbit_data
        self.observer_location = precomputed_orbit_data.get('observer_location', {})
        self.constellations = precomputed_orbit_data.get('constellations', {})
        
        # RL 環境參數
        self.state_dim = 12  # 狀態空間維度
        self.action_dim = 3  # 動作空間維度 (目標衛星選擇、換手時機、功率控制)
        self.episode_length = 96  # 96分鐘軌道週期，每分鐘一個決策點
        
        # 獎勵函數權重
        self.reward_weights = {
            'handover_success': 10.0,
            'service_continuity': 5.0,
            'signal_quality': 3.0,
            'handover_frequency_penalty': -2.0,
            'energy_efficiency': 1.0
        }
    
    def extract_satellite_trajectories(self, constellation: str) -> Dict[str, List[Dict]]:
        """提取衛星軌跡數據"""
        if constellation not in self.constellations:
            logger.error(f"星座 {constellation} 不存在於預計算數據中")
            return {}
        
        constellation_data = self.constellations[constellation]
        orbit_data = constellation_data.get('orbit_data', {})
        
        trajectories = {}
        
        for sat_id, sat_data in orbit_data.items():
            if 'trajectory' in sat_data:
                trajectory = sat_data['trajectory']
                
                # 標準化軌跡數據格式
                standardized_trajectory = []
                
                for i, timestamp in enumerate(trajectory.get('timestamps', [])):
                    if i < len(trajectory.get('positions', [])) and i < len(trajectory.get('elevations', [])):
                        point = {
                            'timestamp': timestamp,
                            'position': trajectory['positions'][i],
                            'elevation': trajectory['elevations'][i],
                            'azimuth': trajectory.get('azimuths', [0])[i] if i < len(trajectory.get('azimuths', [])) else 0,
                            'range_km': trajectory.get('ranges', [1000])[i] if i < len(trajectory.get('ranges', [])) else 1000,
                            'is_visible': trajectory['elevations'][i] > 10.0,  # 10度仰角閾值
                            'signal_strength': self.calculate_signal_strength(trajectory['elevations'][i], trajectory.get('ranges', [1000])[i] if i < len(trajectory.get('ranges', [])) else 1000)
                        }
                        standardized_trajectory.append(point)
                
                trajectories[sat_id] = standardized_trajectory
        
        logger.info(f"✅ 提取 {constellation} 星座 {len(trajectories)} 顆衛星軌跡")
        return trajectories
    
    def calculate_signal_strength(self, elevation: float, range_km: float) -> float:
        """計算信號強度 (簡化模型)"""
        if elevation < 10.0:
            return 0.0
        
        # 基於自由空間路徑損耗的簡化計算
        # FSPL = 20*log10(d) + 20*log10(f) + 32.45
        # 假設 Ku 頻段 (12 GHz)
        frequency_ghz = 12.0
        fspl_db = 20 * np.log10(range_km) + 20 * np.log10(frequency_ghz) + 32.45
        
        # 考慮仰角增益 (仰角越高，信號越強)
        elevation_gain = min(elevation / 90.0, 1.0) * 10  # 最大 10dB 增益
        
        # 假設發射功率 40dBm，接收天線增益 35dBi
        tx_power_dbm = 40
        rx_gain_dbi = 35
        
        received_power = tx_power_dbm + rx_gain_dbi - fspl_db + elevation_gain
        
        # 轉換為 0-1 範圍的信號強度
        # -100dBm 為最低可用信號，-50dBm 為優秀信號
        normalized_strength = max(0, min(1, (received_power + 100) / 50))
        
        return normalized_strength
    
    def generate_handover_episodes(self, constellation: str = 'starlink') -> List[Dict]:
        """生成換手決策 episode"""
        logger.info(f"🎯 生成 {constellation} 星座換手決策 episodes")
        
        trajectories = self.extract_satellite_trajectories(constellation)
        if not trajectories:
            return []
        
        episodes = []
        satellite_ids = list(trajectories.keys())
        
        # 為每個可見衛星窗口生成 episode
        for primary_sat_id in satellite_ids[:10]:  # 限制處理數量以避免過多數據
            primary_trajectory = trajectories[primary_sat_id]
            
            # 找到可見窗口
            visible_windows = self.find_visibility_windows(primary_trajectory)
            
            for window_start, window_end in visible_windows:
                episode = self.generate_single_episode(
                    primary_sat_id, 
                    primary_trajectory[window_start:window_end],
                    trajectories,
                    satellite_ids
                )
                
                if episode:
                    episodes.append(episode)
        
        logger.info(f"✅ 生成 {len(episodes)} 個換手決策 episodes")
        return episodes
    
    def find_visibility_windows(self, trajectory: List[Dict]) -> List[Tuple[int, int]]:
        """找到可見性窗口"""
        windows = []
        start_idx = None
        
        for i, point in enumerate(trajectory):
            if point['is_visible'] and start_idx is None:
                start_idx = i
            elif not point['is_visible'] and start_idx is not None:
                if i - start_idx > 5:  # 至少 5 分鐘的可見窗口
                    windows.append((start_idx, i))
                start_idx = None
        
        # 處理最後一個窗口
        if start_idx is not None and len(trajectory) - start_idx > 5:
            windows.append((start_idx, len(trajectory)))
        
        return windows
    
    def generate_single_episode(self, primary_sat_id: str, primary_trajectory: List[Dict], 
                               all_trajectories: Dict[str, List[Dict]], 
                               satellite_ids: List[str]) -> Optional[Dict]:
        """生成單個 episode"""
        if len(primary_trajectory) < 10:
            return None
        
        episode = {
            'episode_id': f"{primary_sat_id}_{datetime.now().timestamp()}",
            'primary_satellite': primary_sat_id,
            'duration_minutes': len(primary_trajectory),
            'states': [],
            'actions': [],
            'rewards': [],
            'next_states': [],
            'done': []
        }
        
        current_satellite = primary_sat_id
        handover_count = 0
        
        for i, current_point in enumerate(primary_trajectory[:-1]):
            # 構建狀態向量
            state = self.build_state_vector(
                current_point, 
                current_satellite,
                all_trajectories,
                satellite_ids,
                i
            )
            
            # 決定動作 (簡化的貪心策略作為示例)
            action, target_satellite = self.generate_action(
                current_point,
                all_trajectories,
                satellite_ids,
                i
            )
            
            # 計算獎勵
            next_point = primary_trajectory[i + 1]
            reward = self.calculate_reward(
                current_point,
                next_point,
                action,
                target_satellite,
                handover_count
            )
            
            # 構建下一狀態
            next_state = self.build_state_vector(
                next_point,
                target_satellite if action[1] > 0.5 else current_satellite,
                all_trajectories,
                satellite_ids,
                i + 1
            )
            
            episode['states'].append(state.tolist())
            episode['actions'].append(action.tolist())
            episode['rewards'].append(reward)
            episode['next_states'].append(next_state.tolist())
            episode['done'].append(i == len(primary_trajectory) - 2)
            
            # 更新當前衛星
            if action[1] > 0.5:  # 執行換手
                current_satellite = target_satellite
                handover_count += 1
        
        episode['total_handovers'] = handover_count
        episode['average_reward'] = np.mean(episode['rewards'])
        
        return episode
    
    def build_state_vector(self, current_point: Dict, current_satellite: str,
                          all_trajectories: Dict[str, List[Dict]], 
                          satellite_ids: List[str], time_idx: int) -> np.ndarray:
        """構建狀態向量"""
        state = np.zeros(self.state_dim)
        
        # 當前衛星狀態 (0-5)
        state[0] = current_point['elevation'] / 90.0  # 歸一化仰角
        state[1] = current_point['azimuth'] / 360.0   # 歸一化方位角
        state[2] = min(current_point['range_km'] / 2000.0, 1.0)  # 歸一化距離
        state[3] = current_point['signal_strength']
        state[4] = 1.0 if current_point['is_visible'] else 0.0
        state[5] = time_idx / 96.0  # 歸一化時間進度
        
        # 候選衛星狀態 (6-11) - 選擇信號最強的候選衛星
        best_candidate = self.find_best_candidate(
            current_point, all_trajectories, satellite_ids, current_satellite, time_idx
        )
        
        if best_candidate:
            state[6] = best_candidate['elevation'] / 90.0
            state[7] = best_candidate['azimuth'] / 360.0
            state[8] = min(best_candidate['range_km'] / 2000.0, 1.0)
            state[9] = best_candidate['signal_strength']
            state[10] = 1.0 if best_candidate['is_visible'] else 0.0
            state[11] = best_candidate['signal_strength'] - current_point['signal_strength']  # 信號差異
        
        return state
    
    def find_best_candidate(self, current_point: Dict, all_trajectories: Dict[str, List[Dict]],
                           satellite_ids: List[str], current_satellite: str, time_idx: int) -> Optional[Dict]:
        """找到最佳候選衛星"""
        best_candidate = None
        best_signal = 0.0
        
        for sat_id in satellite_ids:
            if sat_id == current_satellite:
                continue
            
            trajectory = all_trajectories.get(sat_id, [])
            if time_idx < len(trajectory):
                candidate_point = trajectory[time_idx]
                
                if candidate_point['is_visible'] and candidate_point['signal_strength'] > best_signal:
                    best_signal = candidate_point['signal_strength']
                    best_candidate = candidate_point
        
        return best_candidate
    
    def generate_action(self, current_point: Dict, all_trajectories: Dict[str, List[Dict]],
                       satellite_ids: List[str], time_idx: int) -> Tuple[np.ndarray, str]:
        """生成動作 (簡化策略)"""
        action = np.zeros(self.action_dim)
        
        # 找到最佳候選衛星
        best_candidate = self.find_best_candidate(
            current_point, all_trajectories, satellite_ids, "current", time_idx
        )
        
        if best_candidate:
            # 動作 0: 目標衛星選擇 (0-1, 1表示選擇最佳候選)
            action[0] = 1.0
            
            # 動作 1: 換手時機 (0-1, 基於信號強度差異)
            signal_diff = best_candidate['signal_strength'] - current_point['signal_strength']
            action[1] = 1.0 if signal_diff > 0.1 else 0.0
            
            # 動作 2: 功率控制 (0-1)
            action[2] = min(1.0, max(0.0, 1.0 - current_point['signal_strength']))
            
            return action, "best_candidate"
        
        # 沒有好的候選衛星，保持當前連接
        action[0] = 0.0  # 不選擇新衛星
        action[1] = 0.0  # 不執行換手
        action[2] = min(1.0, max(0.0, 1.0 - current_point['signal_strength']))
        
        return action, "current"
    
    def calculate_reward(self, current_point: Dict, next_point: Dict, 
                        action: np.ndarray, target_satellite: str, handover_count: int) -> float:
        """計算獎勵"""
        reward = 0.0
        
        # 服務連續性獎勵
        if next_point['is_visible'] and next_point['signal_strength'] > 0.3:
            reward += self.reward_weights['service_continuity']
        
        # 信號品質獎勵
        reward += self.reward_weights['signal_quality'] * next_point['signal_strength']
        
        # 換手成功獎勵
        if action[1] > 0.5:  # 執行了換手
            if next_point['signal_strength'] > current_point['signal_strength']:
                reward += self.reward_weights['handover_success']
            else:
                reward -= self.reward_weights['handover_success'] * 0.5  # 換手失敗懲罰
        
        # 換手頻率懲罰
        if handover_count > 5:  # 過於頻繁的換手
            reward += self.reward_weights['handover_frequency_penalty']
        
        # 能效獎勵 (功率控制)
        power_efficiency = 1.0 - action[2]  # 功率越低越好
        reward += self.reward_weights['energy_efficiency'] * power_efficiency
        
        return reward
    
    def export_ml_format(self, episodes: List[Dict], format_type: str = "pytorch", 
                        output_dir: str = "rl_datasets") -> Dict[str, str]:
        """導出 ML 框架適用格式"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        exported_files = {}
        
        if format_type == "pytorch":
            exported_files.update(self.export_pytorch_format(episodes, output_path))
        elif format_type == "tensorflow":
            exported_files.update(self.export_tensorflow_format(episodes, output_path))
        elif format_type == "csv":
            exported_files.update(self.export_csv_format(episodes, output_path))
        elif format_type == "json":
            exported_files.update(self.export_json_format(episodes, output_path))
        else:
            logger.error(f"不支援的格式: {format_type}")
            return {}
        
        logger.info(f"✅ 數據集已導出為 {format_type} 格式")
        return exported_files
    
    def export_pytorch_format(self, episodes: List[Dict], output_path: Path) -> Dict[str, str]:
        """導出 PyTorch 格式"""
        try:
            import torch
            
            # 合併所有 episodes 的數據
            all_states = []
            all_actions = []
            all_rewards = []
            all_next_states = []
            all_done = []
            
            for episode in episodes:
                all_states.extend(episode['states'])
                all_actions.extend(episode['actions'])
                all_rewards.extend(episode['rewards'])
                all_next_states.extend(episode['next_states'])
                all_done.extend(episode['done'])
            
            # 轉換為 PyTorch tensors
            states_tensor = torch.FloatTensor(all_states)
            actions_tensor = torch.FloatTensor(all_actions)
            rewards_tensor = torch.FloatTensor(all_rewards)
            next_states_tensor = torch.FloatTensor(all_next_states)
            done_tensor = torch.BoolTensor(all_done)
            
            # 保存
            torch_file = output_path / "handover_dataset.pt"
            torch.save({
                'states': states_tensor,
                'actions': actions_tensor,
                'rewards': rewards_tensor,
                'next_states': next_states_tensor,
                'done': done_tensor,
                'metadata': {
                    'state_dim': self.state_dim,
                    'action_dim': self.action_dim,
                    'num_episodes': len(episodes),
                    'total_transitions': len(all_states)
                }
            }, torch_file)
            
            return {'pytorch': str(torch_file)}
            
        except ImportError:
            logger.warning("PyTorch 未安裝，跳過 PyTorch 格式導出")
            return {}
    
    def export_csv_format(self, episodes: List[Dict], output_path: Path) -> Dict[str, str]:
        """導出 CSV 格式"""
        # 展平所有數據
        rows = []
        
        for episode in episodes:
            episode_id = episode['episode_id']
            
            for i in range(len(episode['states'])):
                row = {
                    'episode_id': episode_id,
                    'step': i,
                    'reward': episode['rewards'][i],
                    'done': episode['done'][i]
                }
                
                # 添加狀態特徵
                for j, state_val in enumerate(episode['states'][i]):
                    row[f'state_{j}'] = state_val
                
                # 添加動作特徵
                for j, action_val in enumerate(episode['actions'][i]):
                    row[f'action_{j}'] = action_val
                
                # 添加下一狀態特徵
                for j, next_state_val in enumerate(episode['next_states'][i]):
                    row[f'next_state_{j}'] = next_state_val
                
                rows.append(row)
        
        # 保存為 CSV
        df = pd.DataFrame(rows)
        csv_file = output_path / "handover_dataset.csv"
        df.to_csv(csv_file, index=False)
        
        return {'csv': str(csv_file)}
    
    def export_json_format(self, episodes: List[Dict], output_path: Path) -> Dict[str, str]:
        """導出 JSON 格式"""
        json_file = output_path / "handover_dataset.json"
        
        dataset = {
            'metadata': {
                'generation_date': datetime.now().isoformat(),
                'state_dim': self.state_dim,
                'action_dim': self.action_dim,
                'num_episodes': len(episodes),
                'reward_weights': self.reward_weights
            },
            'episodes': episodes
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        return {'json': str(json_file)}
