#!/usr/bin/env python3
"""
測試環境 Docker 設置驗證腳本
檢查測試相關的所有必要文件和配置是否正確
此腳本從 tests/ 目錄執行，驗證整個測試環境設置
"""

import os
import sys
import json
from pathlib import Path

def check_file_exists(file_path, description):
    """檢查文件是否存在"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (不存在)")
        return False

def check_directory_exists(dir_path, description):
    """檢查目錄是否存在"""
    if os.path.isdir(dir_path):
        print(f"✅ {description}: {dir_path}")
        return True
    else:
        print(f"❌ {description}: {dir_path} (不存在)")
        return False

def validate_docker_compose(file_path):
    """驗證 docker compose 文件的基本結構"""
    try:
        import yaml
        with open(file_path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
        
        required_services = ['ntn-stack-tester', 'netstack-api', 'simworld-backend']
        missing_services = []
        
        services = content.get('services', {})
        for service in required_services:
            if service not in services:
                missing_services.append(service)
        
        if missing_services:
            print(f"❌ Docker Compose 缺少服務: {missing_services}")
            return False
        else:
            print(f"✅ Docker Compose 服務配置完整")
            return True
            
    except ImportError:
        print("⚠️  無法驗證 Docker Compose 文件 (缺少 PyYAML)")
        return True
    except Exception as e:
        print(f"❌ Docker Compose 文件驗證失敗: {e}")
        return False

def main():
    """主要驗證流程"""
    print("🔍 NTN Stack 測試環境 Docker 設置驗證")
    print("=" * 50)
    
    all_checks_passed = True
    
    # 切換到項目根目錄（從 tests/ 目錄執行）
    root_dir = Path(__file__).parent.parent
    os.chdir(root_dir)
    
    # 檢查核心配置文件
    print("\n📁 核心配置文件:")
    checks = [
        ("docker-compose.test.yml", "測試環境 Docker Compose"),
        ("Makefile", "Make 配置文件"),
        ("requirements.txt", "Python 依賴"),
    ]
    
    for file_path, description in checks:
        if not check_file_exists(file_path, description):
            all_checks_passed = False
    
    # 檢查測試目錄結構
    print("\n📂 測試目錄結構:")
    test_dirs = [
        ("tests", "測試目錄"),
        ("test-reports", "測試報告目錄"),
    ]
    
    for dir_path, description in test_dirs:
        if not check_directory_exists(dir_path, description):
            # 創建缺少的目錄
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"✅ 已創建 {description}: {dir_path}")
            except Exception as e:
                print(f"❌ 無法創建 {description}: {e}")
                all_checks_passed = False
    
    # 檢查測試文件
    print("\n🧪 測試文件:")
    test_files = [
        ("tests/Dockerfile", "測試容器 Dockerfile"),
        ("tests/pytest.ini", "Pytest 配置"),
        ("tests/conftest.py", "測試配置和固件"),
        ("tests/test_netstack_api.py", "NetStack API 測試"),
        ("tests/test_simworld_api.py", "SimWorld API 測試"),
        ("tests/test_integration.py", "整合測試"),
        ("tests/nginx.conf", "測試報告 Nginx 配置"),
    ]
    
    for file_path, description in test_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False
    
    # 驗證 Docker Compose 配置
    print("\n🐳 Docker Compose 配置:")
    if os.path.exists("docker-compose.test.yml"):
        if not validate_docker_compose("docker-compose.test.yml"):
            all_checks_passed = False
    
    # 檢查項目結構
    print("\n📋 項目結構:")
    project_dirs = [
        ("netstack", "NetStack 項目"),
        ("simworld", "SimWorld 項目"),
    ]
    
    for dir_path, description in project_dirs:
        if not check_directory_exists(dir_path, description):
            all_checks_passed = False
    
    # 檢查 netstack 的測試文件
    print("\n🧪 NetStack 現有測試:")
    netstack_tests = [
        ("netstack/tests/quick_ntn_validation.sh", "NTN 快速驗證"),
        ("netstack/tests/e2e_netstack.sh", "E2E 測試"),
        ("netstack/tests/performance_test.sh", "性能測試"),
    ]
    
    for file_path, description in netstack_tests:
        check_file_exists(file_path, description)
    
    # 總結
    print("\n" + "=" * 50)
    if all_checks_passed:
        print("🎉 所有檢查通過！測試環境 Docker 化設置已完成")
        print("\n📝 使用說明:")
        print("1. 確保 Docker 和 Docker Compose 已安裝")
        print("2. 執行 'make test' 啟動完整測試")
        print("3. 查看測試報告: http://localhost:8090")
        
        # 生成使用範例
        print("\n💡 測試命令範例:")
        examples = [
            "# 執行完整測試套件",
            "make test",
            "",
            "# 執行特定測試",
            "make test-netstack",
            "make test-simworld", 
            "make test-integration",
            "",
            "# 查看測試報告",
            "make test-reports",
            "",
            "# 清理測試環境",
            "make test-clean",
        ]
        
        for example in examples:
            print(example)
        
        return 0
    else:
        print("❌ 部分檢查失敗，請檢查上述錯誤")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 