#!/usr/bin/env python3
"""
健康檢查腳本 - 獨立衛星處理系統
檢查系統基本功能和依賴項是否正常
"""

import os
import sys
from pathlib import Path
import json

def check_python_environment():
    """檢查 Python 環境和模組導入"""
    try:
        # 添加 src 到路徑
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root / 'src'))
        
        # 測試核心模組導入
        from stages.stage1_orbital_calculation.tle_orbital_calculation_processor import Stage1TLEProcessor
        from shared.base_processor import BaseStageProcessor
        
        return True, "Python 環境和模組導入正常"
    except Exception as e:
        return False, f"Python 環境檢查失敗: {e}"

def check_data_directories():
    """檢查必要的數據目錄是否存在"""
    required_dirs = [
        'data/tle_data',
        'data/validation_snapshots', 
        'data/logs',
        'data/intelligent_filtering_outputs',
        'data/signal_analysis_outputs',
        'data/data_integration_outputs'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        return False, f"缺少必要目錄: {', '.join(missing_dirs)}"
    
    return True, "所有必要數據目錄存在"

def check_tle_data():
    """檢查 TLE 數據是否存在"""
    tle_data_dir = Path('data/tle_data')
    if not tle_data_dir.exists():
        return False, "TLE 數據目錄不存在"
    
    # 檢查是否有星座數據
    constellations = [d for d in tle_data_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    if not constellations:
        return False, "未找到星座數據"
    
    return True, f"找到 {len(constellations)} 個星座數據目錄: {[c.name for c in constellations]}"

def check_scripts():
    """檢查核心執行腳本是否存在"""
    required_scripts = [
        'scripts/run_six_stages_with_validation.py',
        'scripts/final_build_validation.py'
    ]
    
    missing_scripts = []
    for script_path in required_scripts:
        if not Path(script_path).exists():
            missing_scripts.append(script_path)
    
    if missing_scripts:
        return False, f"缺少核心腳本: {', '.join(missing_scripts)}"
    
    return True, "所有核心執行腳本存在"

def main():
    """執行所有健康檢查"""
    checks = [
        ("Python 環境", check_python_environment),
        ("數據目錄", check_data_directories), 
        ("TLE 數據", check_tle_data),
        ("執行腳本", check_scripts)
    ]
    
    health_status = {
        "timestamp": str(Path(__file__).stat().st_mtime),
        "checks": {},
        "overall_healthy": True
    }
    
    print("🔍 獨立衛星處理系統健康檢查")
    print("=" * 50)
    
    for check_name, check_func in checks:
        try:
            is_healthy, message = check_func()
            status = "✅" if is_healthy else "❌"
            print(f"{status} {check_name}: {message}")
            
            health_status["checks"][check_name] = {
                "healthy": is_healthy,
                "message": message
            }
            
            if not is_healthy:
                health_status["overall_healthy"] = False
                
        except Exception as e:
            print(f"❌ {check_name}: 檢查失敗 - {e}")
            health_status["checks"][check_name] = {
                "healthy": False,
                "message": f"檢查失敗: {e}"
            }
            health_status["overall_healthy"] = False
    
    print("=" * 50)
    
    if health_status["overall_healthy"]:
        print("🎉 系統健康檢查通過")
        exit_code = 0
    else:
        print("⚠️ 系統健康檢查發現問題")
        exit_code = 1
    
    # 保存健康檢查結果
    try:
        os.makedirs('data/logs', exist_ok=True)
        with open('data/logs/health_check.json', 'w') as f:
            json.dump(health_status, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ 無法保存健康檢查結果: {e}")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()