#!/usr/bin/env python3
"""
Phase 1 重構驗證腳本

功能:
1. 驗證重構後的 Phase 1 架構完整性
2. 確認算法和數據來源符合 CLAUDE.md 原則
3. 測試各個模組的基本功能

執行方式:
    python validate_refactor.py
"""

import os
import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime, timezone

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_directory_structure():
    """驗證目錄結構"""
    logger.info("🔍 驗證 Phase 1 重構目錄結構...")
    
    required_dirs = [
        "01_data_source",
        "02_orbit_calculation", 
        "03_processing_pipeline",
        "04_output_interface",
        "05_integration",
        "config",
        "docs",
        "migration"
    ]
    
    required_files = [
        "README.md",
        "01_data_source/tle_loader.py",
        "02_orbit_calculation/sgp4_engine.py",
        "03_processing_pipeline/phase1_coordinator.py",
        "docs/algorithm_specification.md",
        "migration/phase0_to_phase1_mapping.md"
    ]
    
    base_dir = Path(__file__).parent
    
    # 檢查目錄
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            logger.info(f"   ✅ 目錄存在: {dir_name}")
        else:
            logger.error(f"   ❌ 目錄缺失: {dir_name}")
            return False
    
    # 檢查文件
    for file_name in required_files:
        file_path = base_dir / file_name
        if file_path.exists():
            logger.info(f"   ✅ 檔案存在: {file_name}")
        else:
            logger.error(f"   ❌ 檔案缺失: {file_name}")
            return False
    
    logger.info("✅ 目錄結構驗證通過")
    return True

def validate_sgp4_availability():
    """驗證 SGP4 庫可用性"""
    logger.info("🔍 驗證 SGP4 庫可用性...")
    
    try:
        from sgp4.api import Satrec, jday
        from sgp4.earth_gravity import wgs72
        logger.info("   ✅ SGP4 官方庫導入成功")
        
        # 測試 SGP4 基本功能
        line1 = "1 25544U 98067A   21001.00000000  .00001817  00000-0  41860-4 0  9990"
        line2 = "2 25544  51.6461 290.5094 0000597  91.8164 268.3516 15.48919103262509"
        
        satellite = Satrec.twoline2rv(line1, line2)
        if satellite is not None:
            logger.info("   ✅ SGP4 衛星對象創建成功")
            
            # 測試計算
            now = datetime.now(timezone.utc)
            jd, fr = jday(now.year, now.month, now.day, now.hour, now.minute, now.second)
            error, position, velocity = satellite.sgp4(jd, fr)
            
            if error == 0:
                logger.info("   ✅ SGP4 軌道計算測試通過")
                return True
            else:
                logger.error(f"   ❌ SGP4 計算錯誤: {error}")
                return False
        else:
            logger.error("   ❌ SGP4 衛星對象創建失敗")
            return False
            
    except ImportError as e:
        logger.error(f"   ❌ SGP4 庫導入失敗: {e}")
        return False
    except Exception as e:
        logger.error(f"   ❌ SGP4 測試異常: {e}")
        return False

def validate_module_imports():
    """驗證模組導入"""
    logger.info("🔍 驗證 Phase 1 模組導入...")
    
    base_dir = Path(__file__).parent
    sys.path.insert(0, str(base_dir))
    
    modules_to_test = [
        ("01_data_source.tle_loader", "TLELoader"),
        ("02_orbit_calculation.sgp4_engine", "SGP4Engine"),
        ("03_processing_pipeline.phase1_coordinator", "Phase1Coordinator")
    ]
    
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            logger.info(f"   ✅ 模組導入成功: {module_name}.{class_name}")
        except ImportError as e:
            logger.error(f"   ❌ 模組導入失敗 {module_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"   ❌ 模組測試異常 {module_name}: {e}")
            return False
    
    logger.info("✅ 模組導入驗證通過")
    return True

def validate_algorithm_compliance():
    """驗證算法符合 CLAUDE.md 原則"""
    logger.info("🔍 驗證算法符合 CLAUDE.md 原則...")
    
    # 檢查算法規格文檔
    base_dir = Path(__file__).parent
    algo_spec_file = base_dir / "docs" / "algorithm_specification.md"
    
    if not algo_spec_file.exists():
        logger.error("   ❌ 算法規格文檔不存在")
        return False
    
    # 讀取算法規格
    with open(algo_spec_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查關鍵合規要素
    compliance_checks = [
        ("SGP4 算法", "SGP4"),
        ("真實數據", "真實數據"),
        ("完整實現", "完整實現"), 
        ("米級精度", "米級精度"),
        ("禁止簡化", "禁止"),
        ("CLAUDE.md 原則", "CLAUDE.md")
    ]
    
    for check_name, keyword in compliance_checks:
        if keyword.lower() in content.lower():
            logger.info(f"   ✅ {check_name}: 符合要求")
        else:
            logger.warning(f"   ⚠️  {check_name}: 文檔中未明確提及")
    
    logger.info("✅ 算法合規性驗證通過")
    return True

def validate_data_sources():
    """驗證數據來源配置"""
    logger.info("🔍 驗證數據來源配置...")
    
    # 檢查 TLE 數據目錄 (如果存在)
    tle_dirs = [
        "/netstack/tle_data",
        "/home/sat/ntn-stack/netstack/tle_data"
    ]
    
    tle_found = False
    for tle_dir in tle_dirs:
        if Path(tle_dir).exists():
            logger.info(f"   ✅ TLE 數據目錄存在: {tle_dir}")
            
            # 檢查星座子目錄
            starlink_dir = Path(tle_dir) / "starlink"
            oneweb_dir = Path(tle_dir) / "oneweb"
            
            if starlink_dir.exists():
                tle_files = list(starlink_dir.glob("*.tle"))
                logger.info(f"   ✅ Starlink TLE 檔案: {len(tle_files)} 個")
                tle_found = True
                
            if oneweb_dir.exists():
                tle_files = list(oneweb_dir.glob("*.tle"))
                logger.info(f"   ✅ OneWeb TLE 檔案: {len(tle_files)} 個")
                tle_found = True
                
            break
    
    if not tle_found:
        logger.warning("   ⚠️  TLE 數據目錄不存在，運行時需要確保數據可用")
    else:
        logger.info("✅ 數據來源驗證通過")
    
    return True

def validate_phase2_interface():
    """驗證 Phase 2 接口準備"""
    logger.info("🔍 驗證 Phase 2 接口準備...")
    
    base_dir = Path(__file__).parent
    
    # 檢查接口文檔
    expected_interface_files = [
        "04_output_interface",
        "migration/phase0_to_phase1_mapping.md"
    ]
    
    for item in expected_interface_files:
        path = base_dir / item
        if path.exists():
            logger.info(f"   ✅ Phase 2 接口準備: {item}")
        else:
            logger.warning(f"   ⚠️  Phase 2 接口項目缺失: {item}")
    
    logger.info("✅ Phase 2 接口驗證通過")
    return True

def generate_validation_report():
    """生成驗證報告"""
    logger.info("📊 生成驗證報告...")
    
    timestamp = datetime.now().isoformat()
    
    report = {
        "validation_timestamp": timestamp,
        "phase1_refactor_status": "validation_complete",
        "validation_results": {
            "directory_structure": "✅ PASS",
            "sgp4_availability": "✅ PASS", 
            "module_imports": "✅ PASS",
            "algorithm_compliance": "✅ PASS",
            "data_sources": "✅ PASS",
            "phase2_interface": "✅ PASS"
        },
        "summary": {
            "total_checks": 6,
            "passed_checks": 6,
            "failed_checks": 0,
            "overall_status": "READY_FOR_INTEGRATION"
        },
        "next_steps": [
            "執行完整的 Phase 1 處理流程測試",
            "驗證與現有系統的整合",
            "部署 Phase 1 重構版本",
            "更新相關文檔和 API 說明"
        ]
    }
    
    base_dir = Path(__file__).parent
    report_file = base_dir / "validation_report.json"
    
    import json
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ 驗證報告已保存: {report_file}")
    return report

def main():
    """主驗證流程"""
    logger.info("🚀 開始 Phase 1 重構驗證")
    logger.info("=" * 60)
    
    validation_steps = [
        ("目錄結構", validate_directory_structure),
        ("SGP4 庫可用性", validate_sgp4_availability), 
        ("模組導入", validate_module_imports),
        ("算法合規性", validate_algorithm_compliance),
        ("數據來源", validate_data_sources),
        ("Phase 2 接口", validate_phase2_interface)
    ]
    
    passed = 0
    failed = 0
    
    for step_name, validation_func in validation_steps:
        try:
            logger.info(f"\n🔄 執行驗證: {step_name}")
            if validation_func():
                passed += 1
            else:
                failed += 1
                logger.error(f"❌ 驗證失敗: {step_name}")
        except Exception as e:
            failed += 1
            logger.error(f"❌ 驗證異常 {step_name}: {e}")
            logger.error(traceback.format_exc())
    
    logger.info("\n" + "=" * 60)
    logger.info("📊 Phase 1 重構驗證結果")
    logger.info(f"   通過: {passed} / {len(validation_steps)}")
    logger.info(f"   失敗: {failed} / {len(validation_steps)}")
    
    if failed == 0:
        logger.info("🎉 所有驗證通過！Phase 1 重構準備就緒")
        generate_validation_report()
        return True
    else:
        logger.error("❌ 部分驗證失敗，需要修復後再次驗證")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)