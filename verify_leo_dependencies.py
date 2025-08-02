#!/usr/bin/env python3
"""
LEO衛星換手研究系統 - 依賴包驗證腳本
===========================================

驗證所有必要的依賴包是否正確安裝並可用
"""

import sys
import subprocess

def check_package_import(package_name, import_name=None):
    """檢查套件是否可以正常導入"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        return True, "已安裝"
    except ImportError as e:
        return False, f"未安裝: {e}"

def install_package(package_name):
    """安裝缺失的套件"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("🛰️ LEO衛星換手研究系統 - 依賴包驗證")
    print("=" * 60)
    
    # 必要依賴包清單 (package_name, import_name, description)
    required_packages = [
        ("sgp4", "sgp4", "SGP4軌道傳播算法 - 多普勒補償系統"),
        ("ntplib", "ntplib", "NTP時間同步客戶端 - 時間同步系統"),
        ("numpy", "numpy", "數值計算基礎 - 所有系統"),
        ("scipy", "scipy", "科學計算 - 動態鏈路預算(Rayleigh/Rice分布)"),
        ("requests", "requests", "HTTP客戶端 - 外部數據獲取"),
        ("psycopg2-binary", "psycopg2", "PostgreSQL數據庫連接"),
    ]
    
    # 檢查套件狀態
    missing_packages = []
    installed_packages = []
    
    for package_name, import_name, description in required_packages:
        success, message = check_package_import(package_name, import_name)
        
        if success:
            print(f"✅ {import_name:15} - {message}")
            print(f"   └─ {description}")
            installed_packages.append(package_name)
        else:
            print(f"❌ {import_name:15} - {message}")
            print(f"   └─ {description}")
            missing_packages.append(package_name)
        print()
    
    print("=" * 60)
    print(f"📊 統計結果:")
    print(f"   ✅ 已安裝: {len(installed_packages)}")
    print(f"   ❌ 缺失: {len(missing_packages)}")
    
    if missing_packages:
        print(f"\n🚨 需要安裝的套件:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        
        print(f"\n📝 安裝命令:")
        print(f"   pip install {' '.join(missing_packages)}")
        
        # 詢問是否自動安裝
        try:
            response = input("\n❓ 是否要自動安裝缺失的套件? (y/N): ").lower()
            if response in ['y', 'yes']:
                print("\n🔄 開始安裝缺失的套件...")
                failed_installs = []
                
                for package in missing_packages:
                    print(f"   安裝 {package}...")
                    if install_package(package):
                        print(f"   ✅ {package} 安裝成功")
                    else:
                        print(f"   ❌ {package} 安裝失敗")
                        failed_installs.append(package)
                
                if failed_installs:
                    print(f"\n⚠️ 以下套件安裝失敗:")
                    for pkg in failed_installs:
                        print(f"   - {pkg}")
                    return 1
                else:
                    print(f"\n🎉 所有套件安裝完成！")
                    return 0
        except KeyboardInterrupt:
            print(f"\n\n❌ 用戶取消安裝")
            return 1
        
        return 1
    else:
        print(f"\n🎉 所有必要依賴包都已正確安裝！")
        print(f"✅ LEO衛星換手研究系統可以正常運行")
        return 0

if __name__ == "__main__":
    sys.exit(main())