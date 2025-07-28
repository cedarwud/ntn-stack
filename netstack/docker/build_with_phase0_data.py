#!/usr/bin/env python3
"""
Docker 建置時預處理功能 - Phase 0 增強版
支援手動收集的 TLE 歷史數據預處理
"""

import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Phase0DataPreprocessor:
    """Phase 0 數據預處理器"""
    
    def __init__(self, tle_data_dir: str = "/app/tle_data", output_dir: str = "/app/data"):
        """
        初始化預處理器
        
        Args:
            tle_data_dir: TLE 數據根目錄
            output_dir: 輸出目錄
        """
        self.tle_data_dir = Path(tle_data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.supported_constellations = ['starlink', 'oneweb']
        
        logger.info(f"Phase0DataPreprocessor 初始化")
        logger.info(f"  TLE 數據目錄: {self.tle_data_dir}")
        logger.info(f"  輸出目錄: {self.output_dir}")
    
    def scan_available_data(self) -> Dict[str, Any]:
        """掃描可用的數據"""
        scan_result = {
            'total_constellations': 0,
            'total_files': 0,
            'total_satellites': 0,
            'constellations': {},
            'overall_date_range': {
                'start': None,
                'end': None
            }
        }
        
        all_dates = []
        
        for constellation in self.supported_constellations:
            tle_dir = self.tle_data_dir / constellation / "tle"
            json_dir = self.tle_data_dir / constellation / "json"
            
            constellation_data = {
                'name': constellation,
                'files': 0,
                'satellites': 0,
                'dates': [],
                'dual_format_count': 0,
                'data_quality': 'unknown'
            }
            
            if tle_dir.exists():
                import glob
                import re
                
                # 掃描 TLE 文件
                tle_files = glob.glob(str(tle_dir / f"{constellation}_*.tle"))
                
                for tle_file in tle_files:
                    match = re.search(r'(\d{8})\.tle$', tle_file)
                    if match:
                        date_str = match.group(1)
                        file_path = Path(tle_file)
                        
                        if file_path.exists() and file_path.stat().st_size > 0:
                            constellation_data['files'] += 1
                            constellation_data['dates'].append(date_str)
                            all_dates.append(date_str)
                            
                            # 計算衛星數量（估算：每3行一顆衛星）
                            try:
                                with open(file_path, 'r') as f:
                                    lines = len([l for l in f if l.strip()])
                                satellite_count = lines // 3
                                constellation_data['satellites'] += satellite_count
                            except:
                                pass
                            
                            # 檢查是否有對應的 JSON 文件
                            json_file = json_dir / f"{constellation}_{date_str}.json"
                            if json_file.exists() and json_file.stat().st_size > 0:
                                constellation_data['dual_format_count'] += 1
                
                # 排序日期
                constellation_data['dates'].sort()
                
                # 評估數據品質
                if constellation_data['files'] > 0:
                    dual_format_rate = (constellation_data['dual_format_count'] / 
                                      constellation_data['files']) * 100
                    
                    if dual_format_rate >= 80 and constellation_data['files'] >= 1:
                        constellation_data['data_quality'] = 'excellent'
                    elif dual_format_rate >= 50:
                        constellation_data['data_quality'] = 'good'
                    elif constellation_data['files'] >= 1:
                        constellation_data['data_quality'] = 'fair'
                    else:
                        constellation_data['data_quality'] = 'poor'
                else:
                    constellation_data['data_quality'] = 'missing'
            
            scan_result['constellations'][constellation] = constellation_data
            scan_result['total_constellations'] += 1 if constellation_data['files'] > 0 else 0
            scan_result['total_files'] += constellation_data['files']
            scan_result['total_satellites'] += constellation_data['satellites']
        
        # 計算整體日期範圍
        if all_dates:
            all_dates.sort()
            scan_result['overall_date_range']['start'] = all_dates[0]
            scan_result['overall_date_range']['end'] = all_dates[-1]
        
        return scan_result
    
    def generate_build_time_config(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成建置時配置"""
        config = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'build_environment': 'docker',
            'phase0_version': '1.0.0',
            'data_source': 'local_manual_collection',
            'scan_result': scan_result,
            'runtime_settings': {
                'default_constellation': 'starlink',
                'data_validation_level': 'strict',
                'cache_enabled': True,
                'precomputed_data_available': True
            }
        }
        
        # 根據可用數據調整設置
        if scan_result['total_constellations'] >= 2:
            config['runtime_settings']['multi_constellation_support'] = True
        
        if scan_result['overall_date_range']['start']:
            config['runtime_settings']['historical_data_range'] = scan_result['overall_date_range']
        
        return config
    
    def generate_rl_training_dataset(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成 RL 訓練數據集metadata"""
        rl_dataset = {
            'dataset_type': 'satellite_handover_rl_training',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'constellations': {},
            'training_parameters': {
                'observation_space_size': 0,
                'action_space_size': 0,
                'episode_length_minutes': 45,
                'reward_function': 'handover_efficiency'
            }
        }
        
        total_episodes = 0
        
        for constellation, data in scan_result['constellations'].items():
            if data['files'] > 0:
                # 每天可以生成多個訓練episode
                episodes_per_day = 24  # 每小時一個episode
                constellation_episodes = data['files'] * episodes_per_day
                
                rl_dataset['constellations'][constellation] = {
                    'available_days': data['files'],
                    'satellite_count': data['satellites'],
                    'episodes_count': constellation_episodes,
                    'data_quality': data['data_quality']
                }
                
                total_episodes += constellation_episodes
        
        rl_dataset['training_parameters']['total_episodes'] = total_episodes
        
        # 根據可用數據調整observation space
        if scan_result['total_satellites'] > 0:
            # 假設每次觀測最多追蹤10顆衛星
            max_tracked_satellites = min(10, scan_result['total_satellites'])
            features_per_satellite = 6  # lat, lon, elevation, azimuth, distance, signal_strength
            rl_dataset['training_parameters']['observation_space_size'] = max_tracked_satellites * features_per_satellite
            
            # 動作空間：選擇目標衛星 + 是否切換
            rl_dataset['training_parameters']['action_space_size'] = max_tracked_satellites + 1
        
        return rl_dataset
    
    def export_build_artifacts(self, scan_result: Dict[str, Any]) -> List[str]:
        """導出建置產物"""
        artifacts = []
        
        try:
            # 1. 生成建置配置
            build_config = self.generate_build_time_config(scan_result)
            config_path = self.output_dir / "phase0_build_config.json"
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(build_config, f, indent=2, ensure_ascii=False)
            
            artifacts.append(str(config_path))
            logger.info(f"✅ 建置配置已生成: {config_path}")
            
            # 2. 生成 RL 訓練數據集metadata
            rl_dataset = self.generate_rl_training_dataset(scan_result)
            rl_path = self.output_dir / "phase0_rl_dataset_metadata.json"
            
            with open(rl_path, 'w', encoding='utf-8') as f:
                json.dump(rl_dataset, f, indent=2, ensure_ascii=False)
            
            artifacts.append(str(rl_path))
            logger.info(f"✅ RL 數據集metadata已生成: {rl_path}")
            
            # 3. 生成數據摘要報告
            summary_report = {
                'phase0_data_summary': {
                    'total_constellations': scan_result['total_constellations'],
                    'total_files': scan_result['total_files'],
                    'total_satellites': scan_result['total_satellites'],
                    'date_range': scan_result['overall_date_range'],
                    'constellation_details': scan_result['constellations']
                },
                'build_recommendations': []
            }
            
            # 添加建議
            if scan_result['total_constellations'] < 2:
                summary_report['build_recommendations'].append("Consider collecting data for both Starlink and OneWeb")
            
            if scan_result['total_files'] < 5:
                summary_report['build_recommendations'].append("More historical data days recommended for better RL training")
            
            for const, data in scan_result['constellations'].items():
                if data['data_quality'] in ['poor', 'missing']:
                    summary_report['build_recommendations'].append(f"Improve data quality for {const}")
            
            summary_path = self.output_dir / "phase0_data_summary.json"
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary_report, f, indent=2, ensure_ascii=False)
            
            artifacts.append(str(summary_path))
            logger.info(f"✅ 數據摘要報告已生成: {summary_path}")
            
            # 4. 生成環境變數文件（供 Docker 使用）
            env_vars = {
                'PHASE0_DATA_AVAILABLE': 'true',
                'PHASE0_TOTAL_CONSTELLATIONS': str(scan_result['total_constellations']),
                'PHASE0_TOTAL_FILES': str(scan_result['total_files']),
                'PHASE0_TOTAL_SATELLITES': str(scan_result['total_satellites']),
                'PHASE0_DATE_START': scan_result['overall_date_range']['start'] or '',
                'PHASE0_DATE_END': scan_result['overall_date_range']['end'] or '',
                'PHASE0_BUILD_TIMESTAMP': datetime.now(timezone.utc).isoformat()
            }
            
            env_path = self.output_dir / "phase0.env"
            
            with open(env_path, 'w') as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            
            artifacts.append(str(env_path))
            logger.info(f"✅ 環境變數文件已生成: {env_path}")
            
        except Exception as e:
            logger.error(f"導出建置產物失敗: {e}")
            raise
        
        return artifacts
    
    def run_build_preprocessing(self) -> Dict[str, Any]:
        """執行完整的建置預處理"""
        logger.info("🚀 開始 Phase 0 建置預處理...")
        
        try:
            # 1. 掃描數據
            logger.info("📊 掃描可用數據...")
            scan_result = self.scan_available_data()
            
            logger.info("📋 掃描結果:")
            logger.info(f"  - 星座數: {scan_result['total_constellations']}")
            logger.info(f"  - 文件數: {scan_result['total_files']}")
            logger.info(f"  - 衛星數: {scan_result['total_satellites']}")
            logger.info(f"  - 日期範圍: {scan_result['overall_date_range']['start']} - {scan_result['overall_date_range']['end']}")
            
            # 2. 生成建置產物
            logger.info("📦 生成建置產物...")
            artifacts = self.export_build_artifacts(scan_result)
            
            # 3. 生成處理結果
            processing_result = {
                'success': True,
                'scan_result': scan_result,
                'artifacts': artifacts,
                'processing_time': datetime.now(timezone.utc).isoformat(),
                'recommendations': []
            }
            
            # 添加建議
            if scan_result['total_files'] == 0:
                processing_result['recommendations'].append("No TLE data files found - container will use fallback data")
            elif scan_result['total_files'] < 3:
                processing_result['recommendations'].append("Limited historical data - consider collecting more days")
            
            logger.info("✅ Phase 0 建置預處理完成")
            return processing_result
            
        except Exception as e:
            logger.error(f"建置預處理失敗: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_time': datetime.now(timezone.utc).isoformat()
            }

def main():
    """主程序"""
    print("🐳 Phase 0 Docker 建置預處理系統")
    print("=" * 50)
    
    # 從環境變數或命令行參數獲取配置
    tle_data_dir = os.environ.get('TLE_DATA_DIR', '/app/tle_data')
    output_dir = os.environ.get('OUTPUT_DIR', '/app/data')
    
    # 檢查命令行參數
    if len(sys.argv) > 1:
        if '--tle-data-dir' in sys.argv:
            idx = sys.argv.index('--tle-data-dir')
            if idx + 1 < len(sys.argv):
                tle_data_dir = sys.argv[idx + 1]
        
        if '--output-dir' in sys.argv:
            idx = sys.argv.index('--output-dir')
            if idx + 1 < len(sys.argv):
                output_dir = sys.argv[idx + 1]
    
    print(f"📂 TLE 數據目錄: {tle_data_dir}")
    print(f"📁 輸出目錄: {output_dir}")
    
    # 初始化預處理器
    preprocessor = Phase0DataPreprocessor(tle_data_dir, output_dir)
    
    # 執行預處理
    result = preprocessor.run_build_preprocessing()
    
    # 顯示結果
    if result['success']:
        print("\n🎉 建置預處理成功完成")
        print(f"📊 掃描到 {result['scan_result']['total_files']} 個數據文件")
        print(f"🛰️ 總計 {result['scan_result']['total_satellites']} 顆衛星")
        print(f"📦 生成 {len(result['artifacts'])} 個建置產物")
        
        if result['recommendations']:
            print("\n💡 建議:")
            for rec in result['recommendations']:
                print(f"  - {rec}")
    else:
        print(f"\n❌ 建置預處理失敗: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()