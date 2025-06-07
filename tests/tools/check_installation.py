#!/usr/bin/env python3
"""
檢查可視化工具安裝狀態
Check visualization tools installation status
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """檢查Python版本"""
    print("🐍 Python Environment Check")
    print("-" * 30)
    
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version >= (3, 7):
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python 3.7+ required")
        return False

def check_required_files():
    """檢查必需文件"""
    print("\n📁 File Structure Check")
    print("-" * 30)
    
    required_files = [
        "visualization_main.py",
        "visualization_config.py", 
        "test_data_collector.py",
        "visualization_engine.py",
        "advanced_report_generator.py",
        "dashboard_server.py",
        "test_analysis_engine.py",
        "coverage_analyzer.py",
        "visualization_requirements.txt",
        "README.md"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = Path(__file__).parent / file
        if file_path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - Missing")
            missing_files.append(file)
    
    return len(missing_files) == 0

def check_dependencies():
    """檢查依賴包"""
    print("\n📦 Dependencies Check")
    print("-" * 30)
    
    required_packages = [
        ("pandas", "Data processing"),
        ("numpy", "Numerical computing"),
        ("plotly", "Interactive charts"),
        ("flask", "Web framework"),
        ("jinja2", "Template engine"),
        ("pyyaml", "Configuration files"),
        ("scipy", "Scientific computing"),
        ("sklearn", "Machine learning")
    ]
    
    available_packages = []
    missing_packages = []
    
    for package, description in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - {description}")
            available_packages.append(package)
        except ImportError:
            print(f"❌ {package} - {description} (Not installed)")
            missing_packages.append(package)
    
    return len(missing_packages) == 0, missing_packages

def check_directories():
    """檢查必需目錄"""
    print("\n📂 Directory Structure Check")
    print("-" * 30)
    
    required_dirs = [
        "/home/sat/ntn-stack/tests/data",
        "/home/sat/ntn-stack/tests/reports", 
        "/home/sat/ntn-stack/tests/reports/coverage"
    ]
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✅ {dir_path}")
        else:
            print(f"⚠️  {dir_path} - Will be created automatically")
            # 創建目錄
            path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created {dir_path}")

def get_installation_commands(missing_packages):
    """獲取安裝命令"""
    if not missing_packages:
        return None
    
    print("\n🛠️ Installation Commands")
    print("-" * 30)
    
    print("To install missing dependencies, run:")
    print(f"pip install {' '.join(missing_packages)}")
    print("\nOr install all dependencies at once:")
    print("pip install -r visualization_requirements.txt")
    
    return missing_packages

def check_basic_functionality():
    """檢查基本功能（不依賴外部包）"""
    print("\n🔧 Basic Functionality Check")
    print("-" * 30)
    
    try:
        # 測試配置管理（不依賴外部包）
        sys.path.insert(0, str(Path(__file__).parent))
        from visualization_config import ConfigManager
        
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        print("✅ Configuration management works")
        print(f"   📊 Charts configured: {len(config.charts)}")
        print(f"   🎨 Dashboard theme: {config.dashboard.theme}")
        
        # 檢查配置文件
        if config_manager.config_path.exists():
            print(f"✅ Configuration file created: {config_manager.config_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality error: {e}")
        return False

def main():
    """主檢查函數"""
    print("🔍 NTN Stack Visualization Tools Installation Check")
    print("=" * 60)
    
    checks = []
    
    # Python版本檢查
    checks.append(("Python Version", check_python_version()))
    
    # 文件結構檢查
    checks.append(("Required Files", check_required_files()))
    
    # 依賴包檢查
    deps_ok, missing_packages = check_dependencies()
    checks.append(("Dependencies", deps_ok))
    
    # 目錄結構檢查
    check_directories()
    
    # 基本功能檢查
    checks.append(("Basic Functionality", check_basic_functionality()))
    
    # 結果摘要
    print("\n📊 Installation Status Summary")
    print("=" * 40)
    
    passed_checks = 0
    total_checks = len(checks)
    
    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {check_name}")
        if result:
            passed_checks += 1
    
    print(f"\n🎯 Overall Status: {passed_checks}/{total_checks} checks passed")
    
    if passed_checks == total_checks:
        print("\n🎉 Installation complete! All systems ready.")
        print("\nNext steps:")
        print("1. Start dashboard: python visualization_main.py dashboard")
        print("2. Generate report: python visualization_main.py generate-report")
        print("3. Analyze trends: python visualization_main.py analyze-trends")
        return 0
    else:
        print(f"\n⚠️  Installation incomplete. {total_checks - passed_checks} issues found.")
        
        if not deps_ok:
            get_installation_commands(missing_packages)
        
        print("\nAfter installing dependencies, run this check again:")
        print("python check_installation.py")
        return 1

if __name__ == "__main__":
    sys.exit(main())