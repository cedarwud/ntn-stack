#!/usr/bin/env python3
"""
衛星覆蓋驗證腳本
Satellite Coverage Validation Script

驗證衛星預處理系統是否能持續提供8-12顆可見衛星
確保LEO衛星換手研究所需的連續覆蓋品質

使用方法:
    python validate_satellite_coverage.py --constellation starlink --count 120
    python validate_satellite_coverage.py --constellation oneweb --count 80 --output report.json
"""

import asyncio
import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
import aiohttp
import numpy as np
from pathlib import Path

# 添加netstack路徑
sys.path.append('/home/sat/ntn-stack/netstack')

class SatelliteCoverageValidator:
    """衛星覆蓋驗證器"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = None
        
        # 驗證標準
        self.coverage_standards = {
            'min_visible_satellites': 8,
            'max_visible_satellites': 12, 
            'target_visible_satellites': 10,
            'min_coverage_percentage': 95.0,  # 95%時間內滿足要求
            'min_elevation_deg': 10.0,
            'evaluation_duration_hours': 24,
            'sampling_interval_minutes': 10
        }
        
        # NTPU觀測點
        self.observer_location = {
            'lat': 24.9441667,
            'lon': 121.3713889,
            'alt': 24  # 米
        }
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def test_api_connectivity(self) -> bool:
        """測試API連接"""
        try:
            async with self.session.get(f"{self.base_url}/api/v1/satellite-ops/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ API健康檢查通過: {health_data.get('healthy', False)}")
                    return True
                else:
                    print(f"❌ API健康檢查失敗: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"❌ API連接失敗: {e}")
            return False
    
    async def get_visible_satellites_at_time(self, timestamp: str, constellation: str, count: int = 20) -> Dict[str, Any]:
        """獲取指定時間的可見衛星"""
        params = {
            'count': min(count, 100),  # API限制最大100
            'constellation': constellation,
            'min_elevation_deg': self.coverage_standards['min_elevation_deg'],
            'observer_lat': self.observer_location['lat'],
            'observer_lon': self.observer_location['lon'],
            'observer_alt': self.observer_location['alt'],
            'utc_timestamp': timestamp,
            'global_view': 'false'
        }
        
        try:
            url = f"{self.base_url}/api/v1/satellite-ops/visible_satellites"
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    print(f"⚠️ 時間點 {timestamp} API調用失敗: HTTP {response.status}, 錯誤: {error_text[:200]}")
                    return {'total_count': 0, 'satellites': []}
        except Exception as e:
            print(f"⚠️ 時間點 {timestamp} API調用異常: {e}")
            return {'total_count': 0, 'satellites': []}
    
    async def validate_continuous_coverage(self, constellation: str, count: int) -> Dict[str, Any]:
        """驗證連續覆蓋品質"""
        print(f"\n🔍 驗證 {constellation} 星座連續覆蓋 (預處理 {count} 顆衛星)")
        print(f"📍 觀測點: NTPU ({self.observer_location['lat']:.4f}, {self.observer_location['lon']:.4f})")
        print(f"⏱️ 評估時長: {self.coverage_standards['evaluation_duration_hours']} 小時")
        print(f"📊 採樣間隔: {self.coverage_standards['sampling_interval_minutes']} 分鐘")
        print("-" * 60)
        
        # 生成時間採樣點
        start_time = datetime.now(timezone.utc)
        duration = timedelta(hours=self.coverage_standards['evaluation_duration_hours'])
        interval = timedelta(minutes=self.coverage_standards['sampling_interval_minutes'])
        
        time_points = []
        current_time = start_time
        while current_time < start_time + duration:
            time_points.append(current_time)
            current_time += interval
        
        print(f"📋 總計採樣點: {len(time_points)} 個")
        
        # 並行查詢所有時間點
        coverage_results = []
        batch_size = 3  # 減少批處理大小
        
        for i in range(0, len(time_points), batch_size):
            batch = time_points[i:i + batch_size]
            tasks = []
            
            for timestamp in batch:
                timestamp_str = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
                task = self.get_visible_satellites_at_time(timestamp_str, constellation, count)
                tasks.append((timestamp_str, task))
            
            # 並行執行當前批次
            batch_results = await asyncio.gather(*[task for _, task in tasks])
            
            for j, (timestamp_str, result) in enumerate(zip([ts for ts, _ in tasks], batch_results)):
                visible_count = result.get('total_count', 0)
                coverage_results.append({
                    'timestamp': timestamp_str,
                    'visible_count': visible_count,
                    'satellites': result.get('satellites', [])
                })
                
                # 即時反饋
                status = "✅" if self.coverage_standards['min_visible_satellites'] <= visible_count <= self.coverage_standards['max_visible_satellites'] else "❌"
                print(f"  {status} {timestamp_str}: {visible_count} 顆衛星")
            
            # 避免API限流
            if i + batch_size < len(time_points):
                await asyncio.sleep(2)  # 增加間隔時間
        
        return self.analyze_coverage_results(coverage_results, constellation, count)
    
    def analyze_coverage_results(self, results: List[Dict], constellation: str, count: int) -> Dict[str, Any]:
        """分析覆蓋結果"""
        if not results:
            return {'error': '無有效數據'}
        
        visible_counts = [r['visible_count'] for r in results]
        total_samples = len(results)
        
        # 基本統計
        stats = {
            'min_visible': min(visible_counts),
            'max_visible': max(visible_counts),
            'mean_visible': np.mean(visible_counts),
            'median_visible': np.median(visible_counts),
            'std_visible': np.std(visible_counts)
        }
        
        # 覆蓋品質分析
        min_threshold = self.coverage_standards['min_visible_satellites']
        max_threshold = self.coverage_standards['max_visible_satellites']
        target = self.coverage_standards['target_visible_satellites']
        
        # 計算各種覆蓋率
        adequate_coverage = sum(1 for count in visible_counts if count >= min_threshold)
        optimal_coverage = sum(1 for count in visible_counts if min_threshold <= count <= max_threshold)
        target_coverage = sum(1 for count in visible_counts if count == target)
        
        coverage_analysis = {
            'adequate_coverage_percentage': (adequate_coverage / total_samples) * 100,
            'optimal_coverage_percentage': (optimal_coverage / total_samples) * 100,
            'target_coverage_percentage': (target_coverage / total_samples) * 100,
            'zero_coverage_samples': sum(1 for count in visible_counts if count == 0),
            'excess_coverage_samples': sum(1 for count in visible_counts if count > max_threshold)
        }
        
        # 連續性分析
        gaps = self.find_coverage_gaps(results)
        continuity_analysis = {
            'total_gaps': len(gaps),
            'max_gap_duration_minutes': max([g['duration_minutes'] for g in gaps], default=0),
            'total_gap_time_minutes': sum(g['duration_minutes'] for g in gaps)
        }
        
        # 總體評估
        is_adequate = coverage_analysis['adequate_coverage_percentage'] >= self.coverage_standards['min_coverage_percentage']
        is_optimal = coverage_analysis['optimal_coverage_percentage'] >= 80.0  # 80%時間在最佳範圍
        
        assessment = {
            'overall_grade': 'A' if is_optimal else 'B' if is_adequate else 'C',
            'meets_requirements': is_adequate,
            'recommendation': self.generate_recommendation(stats, coverage_analysis, continuity_analysis)
        }
        
        print(f"\n📊 覆蓋分析結果:")
        print(f"  📈 可見衛星統計: {stats['mean_visible']:.1f}±{stats['std_visible']:.1f} (範圍: {stats['min_visible']}-{stats['max_visible']})")
        print(f"  ✅ 足夠覆蓋率: {coverage_analysis['adequate_coverage_percentage']:.1f}%")
        print(f"  🎯 最佳覆蓋率: {coverage_analysis['optimal_coverage_percentage']:.1f}%")
        print(f"  🔄 連續性: {len(gaps)} 個間隙, 最長 {continuity_analysis['max_gap_duration_minutes']} 分鐘")
        print(f"  🏆 總體評級: {assessment['overall_grade']}")
        print(f"  💡 建議: {assessment['recommendation']}")
        
        return {
            'constellation': constellation,
            'preprocessed_count': count,
            'evaluation_period': {
                'start_time': results[0]['timestamp'],
                'end_time': results[-1]['timestamp'],
                'total_samples': total_samples,
                'sampling_interval_minutes': self.coverage_standards['sampling_interval_minutes']
            },
            'statistics': stats,
            'coverage_analysis': coverage_analysis,
            'continuity_analysis': continuity_analysis,
            'assessment': assessment,
            'coverage_gaps': gaps,
            'raw_data': results if len(results) <= 50 else results[::len(results)//50]  # 採樣原始數據
        }
    
    def find_coverage_gaps(self, results: List[Dict]) -> List[Dict]:
        """找出覆蓋間隙"""
        gaps = []
        gap_start = None
        min_threshold = self.coverage_standards['min_visible_satellites']
        
        for i, result in enumerate(results):
            if result['visible_count'] < min_threshold:
                if gap_start is None:
                    gap_start = i
            else:
                if gap_start is not None:
                    gap_duration = (i - gap_start) * self.coverage_standards['sampling_interval_minutes']
                    gaps.append({
                        'start_index': gap_start,
                        'end_index': i - 1,
                        'start_timestamp': results[gap_start]['timestamp'],
                        'end_timestamp': results[i-1]['timestamp'],
                        'duration_minutes': gap_duration,
                        'min_satellites_in_gap': min(r['visible_count'] for r in results[gap_start:i])
                    })
                    gap_start = None
        
        # 處理以間隙結尾的情況
        if gap_start is not None:
            gap_duration = (len(results) - gap_start) * self.coverage_standards['sampling_interval_minutes']
            gaps.append({
                'start_index': gap_start,
                'end_index': len(results) - 1,
                'start_timestamp': results[gap_start]['timestamp'],
                'end_timestamp': results[-1]['timestamp'],
                'duration_minutes': gap_duration,
                'min_satellites_in_gap': min(r['visible_count'] for r in results[gap_start:])
            })
        
        return gaps
    
    def generate_recommendation(self, stats: Dict, coverage: Dict, continuity: Dict) -> str:
        """生成改進建議"""
        recommendations = []
        
        if coverage['adequate_coverage_percentage'] < self.coverage_standards['min_coverage_percentage']:
            recommendations.append("增加預處理衛星數量")
        
        if stats['mean_visible'] < self.coverage_standards['min_visible_satellites']:
            recommendations.append("優化衛星選擇算法")
        
        if continuity['max_gap_duration_minutes'] > 30:
            recommendations.append("改善相位分散策略")
        
        if coverage['zero_coverage_samples'] > 0:
            recommendations.append("檢查軌道預計算準確性")
        
        if coverage['excess_coverage_samples'] / len(stats) > 0.2:
            recommendations.append("可適度減少衛星數量以優化資源")
        
        if not recommendations:
            return "覆蓋品質優秀，建議保持現有配置"
        
        return "; ".join(recommendations)
    
    async def test_preprocessing_apis(self, constellation: str, count: int) -> Dict[str, Any]:
        """測試預處理相關API"""
        print(f"\n🧪 測試預處理API: {constellation}")
        
        api_tests = {}
        
        # 測試最佳時間窗口API
        try:
            url = f"{self.base_url}/api/v1/satellite-ops/optimal_time_window"
            params = {'constellation': constellation}
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    api_tests['optimal_time_window'] = {
                        'status': 'success',
                        'quality_score': data.get('quality_score', 0),
                        'window_duration': data.get('end_time', '') 
                    }
                    print(f"  ✅ optimal_time_window: 品質分數 {data.get('quality_score', 0):.2f}")
                else:
                    api_tests['optimal_time_window'] = {'status': 'failed', 'http_code': response.status}
                    print(f"  ❌ optimal_time_window: HTTP {response.status}")
        except Exception as e:
            api_tests['optimal_time_window'] = {'status': 'error', 'error': str(e)}
            print(f"  ❌ optimal_time_window: {e}")
        
        # 測試預處理池API
        try:
            url = f"{self.base_url}/api/v1/satellite-ops/preprocess_pool"
            params = {
                'constellation': constellation,
                'target_count': count,
                'optimization_mode': 'event_diversity'
            }
            async with self.session.post(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    selected_count = len(data.get('selected_satellites', []))
                    api_tests['preprocess_pool'] = {
                        'status': 'success',
                        'selected_count': selected_count,
                        'processing_time': data.get('processing_performance', {}).get('processing_time_seconds', 0)
                    }
                    print(f"  ✅ preprocess_pool: 選擇 {selected_count} 顆衛星")
                else:
                    api_tests['preprocess_pool'] = {'status': 'failed', 'http_code': response.status}
                    print(f"  ❌ preprocess_pool: HTTP {response.status}")
        except Exception as e:
            api_tests['preprocess_pool'] = {'status': 'error', 'error': str(e)}
            print(f"  ❌ preprocess_pool: {e}")
        
        return api_tests

async def main():
    parser = argparse.ArgumentParser(description='驗證衛星覆蓋品質')
    parser.add_argument('--constellation', '-c', default='starlink', 
                       choices=['starlink', 'oneweb', 'kuiper'],
                       help='星座名稱')
    parser.add_argument('--count', '-n', type=int, default=120,
                       help='預處理衛星數量')
    parser.add_argument('--output', '-o', help='輸出報告文件路徑')
    parser.add_argument('--base-url', default='http://localhost:8080',
                       help='NetStack API基礎URL')
    parser.add_argument('--quick', '-q', action='store_true',
                       help='快速模式 (1小時評估)')
    
    args = parser.parse_args()
    
    print("🛰️  LEO衛星覆蓋驗證系統")
    print("=" * 60)
    print(f"星座: {args.constellation}")
    print(f"預處理數量: {args.count}")
    print(f"API地址: {args.base_url}")
    
    async with SatelliteCoverageValidator(args.base_url) as validator:
        # 快速模式調整
        if args.quick:
            validator.coverage_standards['evaluation_duration_hours'] = 1
            validator.coverage_standards['sampling_interval_minutes'] = 5
        
        # 1. API連接測試
        if not await validator.test_api_connectivity():
            print("❌ API連接失敗，請檢查NetStack服務狀態")
            sys.exit(1)
        
        # 2. API功能測試
        api_tests = await validator.test_preprocessing_apis(args.constellation, args.count)
        
        # 3. 覆蓋驗證
        coverage_report = await validator.validate_continuous_coverage(args.constellation, args.count)
        
        # 4. 生成完整報告
        full_report = {
            'validation_metadata': {
                'script_version': '1.0.0',
                'validation_time': datetime.now(timezone.utc).isoformat(),
                'validator_config': validator.coverage_standards,
                'observer_location': validator.observer_location
            },
            'api_tests': api_tests,
            'coverage_validation': coverage_report,
            'overall_status': 'PASS' if coverage_report['assessment']['meets_requirements'] else 'FAIL'
        }
        
        # 5. 輸出報告
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(full_report, f, indent=2, ensure_ascii=False)
            print(f"\n💾 詳細報告已儲存至: {args.output}")
        
        print(f"\n🎯 驗證結果: {full_report['overall_status']}")
        if full_report['overall_status'] == 'FAIL':
            print("💡 建議執行系統優化或增加衛星數量")
            sys.exit(1)
        else:
            print("✅ 衛星覆蓋品質符合研究需求")

if __name__ == "__main__":
    asyncio.run(main())