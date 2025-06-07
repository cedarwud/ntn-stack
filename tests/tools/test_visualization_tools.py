#!/usr/bin/env python3
"""
測試可視化工具的基本功能
Test basic functionality of visualization tools
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# 添加當前目錄到Python路徑
sys.path.insert(0, str(Path(__file__).parent))

def test_config_manager():
    """測試配置管理器"""
    print("🔧 Testing Configuration Manager...")
    
    try:
        from visualization_config import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        print(f"   ✅ Config loaded successfully")
        print(f"   📊 Charts configured: {len(config.charts)}")
        print(f"   🎨 Dashboard theme: {config.dashboard.theme}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_data_manager():
    """測試數據管理器"""
    print("📥 Testing Data Manager...")
    
    try:
        from test_data_collector import TestDataManager
        
        data_manager = TestDataManager()
        
        # 測試數據庫初始化
        print(f"   ✅ Database initialized at: {data_manager.db_path}")
        
        # 測試數據查詢
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        test_data = data_manager.get_test_data(start_date=start_date, end_date=end_date)
        performance_data = data_manager.get_performance_data(start_date=start_date, end_date=end_date)
        
        print(f"   📊 Test records found: {len(test_data)}")
        print(f"   ⚡ Performance records found: {len(performance_data)}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_visualization_engine():
    """測試可視化引擎"""
    print("📈 Testing Visualization Engine...")
    
    try:
        from visualization_config import ConfigManager
        from visualization_engine import VisualizationEngine
        import pandas as pd
        import numpy as np
        
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        engine = VisualizationEngine(config)
        
        # 創建示例數據
        sample_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10, freq='D'),
            'success_rate': np.random.uniform(80, 100, 10),
            'category': ['Test Suite A'] * 5 + ['Test Suite B'] * 5
        })
        
        # 測試圖表生成
        chart = engine.generate_chart('test_results_trend', sample_data)
        
        if chart and chart.figure:
            print(f"   ✅ Chart generated: {chart.title}")
            print(f"   📊 Chart type: {chart.config.chart_type}")
            return True
        else:
            print(f"   ❌ Chart generation failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_coverage_analyzer():
    """測試覆蓋率分析器"""
    print("📊 Testing Coverage Analyzer...")
    
    try:
        from coverage_analyzer import CoverageReportGenerator, FileCoverage, ModuleCoverage, CoverageReport
        
        generator = CoverageReportGenerator()
        
        # 創建示例覆蓋率數據
        sample_files = [
            FileCoverage(
                file_path="src/main.py",
                file_name="main.py",
                total_lines=100,
                covered_lines=85,
                coverage_percentage=85.0,
                uncovered_lines=[10, 15, 20],
                functions=[]
            )
        ]
        
        sample_module = ModuleCoverage(
            module_name="main",
            module_path="src",
            files=sample_files,
            total_lines=100,
            covered_lines=85,
            coverage_percentage=85.0,
            function_coverage=90.0,
            branch_coverage=75.0
        )
        
        sample_report = CoverageReport(
            project_name="Test Project",
            generated_at=datetime.now(),
            overall_coverage=85.0,
            line_coverage=85.0,
            function_coverage=90.0,
            branch_coverage=75.0,
            modules=[sample_module],
            summary_stats={'total_files': 1}
        )
        
        # 測試分析
        analysis = generator.generate_comprehensive_analysis([sample_report])
        
        print(f"   ✅ Coverage analysis completed")
        print(f"   📈 Overall coverage: {analysis['summary']['overall_coverage']:.1f}%")
        print(f"   📁 Total files: {analysis['summary']['total_files']}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_trend_analysis():
    """測試趨勢分析"""
    print("📈 Testing Trend Analysis...")
    
    try:
        from test_analysis_engine import TestAnalysisEngine, StatisticalAnalyzer
        from test_data_collector import TestDataManager
        from datetime import datetime
        
        data_manager = TestDataManager()
        analysis_engine = TestAnalysisEngine(data_manager)
        
        # 測試統計分析器
        analyzer = StatisticalAnalyzer()
        
        # 示例數據
        test_data = [85.0, 87.5, 83.2, 89.1, 86.8, 88.9, 91.2, 87.5, 85.9, 90.1]
        timestamps = [datetime.now() - timedelta(days=i) for i in range(9, -1, -1)]
        
        slope, r_squared, p_value, std_error = analyzer.calculate_trend(test_data, timestamps)
        
        print(f"   ✅ Trend analysis completed")
        print(f"   📊 Slope: {slope:.4f}")
        print(f"   📈 R-squared: {r_squared:.4f}")
        print(f"   📉 P-value: {p_value:.4f}")
        
        # 測試異常檢測
        anomalies = analyzer.detect_anomalies(test_data)
        print(f"   🔍 Anomalies detected: {len(anomalies)}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_report_generator():
    """測試報告生成器"""
    print("📄 Testing Report Generator...")
    
    try:
        from advanced_report_generator import AdvancedReportGenerator
        from test_data_collector import TestSuite
        from visualization_config import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        report_generator = AdvancedReportGenerator(config)
        
        # 創建示例測試套件
        sample_suite = TestSuite(
            name="Sample Test Suite",
            timestamp=datetime.now(),
            total_tests=100,
            passed=85,
            failed=10,
            skipped=5,
            errors=0,
            duration=120.5,
            success_rate=85.0,
            tests=[]
        )
        
        # 生成報告
        report = report_generator.generate_report([sample_suite])
        
        print(f"   ✅ Report generated: {report.title}")
        print(f"   📊 Success rate: {report.summary.overall_success_rate:.1f}%")
        print(f"   📋 Sections: {len(report.sections)}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def create_test_directories():
    """創建測試所需的目錄"""
    print("📁 Creating test directories...")
    
    directories = [
        "/home/sat/ntn-stack/tests/data",
        "/home/sat/ntn-stack/tests/reports",
        "/home/sat/ntn-stack/tests/reports/coverage"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Created: {directory}")

def main():
    """主測試函數"""
    print("🧪 Testing NTN Stack Visualization Tools")
    print("=" * 50)
    
    # 創建測試目錄
    create_test_directories()
    
    # 運行測試
    tests = [
        ("Configuration Manager", test_config_manager),
        ("Data Manager", test_data_manager),
        ("Visualization Engine", test_visualization_engine),
        ("Coverage Analyzer", test_coverage_analyzer),
        ("Trend Analysis", test_trend_analysis),
        ("Report Generator", test_report_generator)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print()
        except Exception as e:
            print(f"   💥 Test crashed: {e}")
            results.append((test_name, False))
            print()
    
    # 結果摘要
    print("📊 Test Results Summary")
    print("-" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! The visualization tools are ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())