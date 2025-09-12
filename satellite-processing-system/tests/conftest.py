# pytest 全局配置和共享 fixtures
# TDD/BDD 架構重構 - 全局測試配置

import pytest
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
import tempfile

# 測試數據路徑
TEST_DATA_DIR = Path(__file__).parent / "fixtures"
# TLE數據實際路徑 - 與TLETestDataLoader一致
PROJECT_ROOT = Path(__file__).parent.parent  # satellite-processing-system 根目錄
STARLINK_TLE_DIR = PROJECT_ROOT / "data" / "tle_data" / "starlink" / "tle"
ONEWEB_TLE_DIR = PROJECT_ROOT / "data" / "tle_data" / "oneweb" / "tle"
TLE_DATA_DIR = TEST_DATA_DIR / "tle_data"  # 保持向後相容性
EXPECTED_OUTPUTS_DIR = TEST_DATA_DIR / "expected_outputs"
PERFORMANCE_BASELINES_DIR = TEST_DATA_DIR / "performance_baselines"

# =============================================================================
# 全局 Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def test_config():
    """測試配置"""
    return {
        "test_mode": True,
        "data_dir": str(TEST_DATA_DIR),
        "tle_data_dir": str(TLE_DATA_DIR),
        "timeout_seconds": 30,
        "precision_tolerance": 1e-6
    }

@pytest.fixture(scope="session")
def ntpu_observer():
    """NTPU 觀測點配置 - 真實座標"""
    return {
        "name": "NTPU",
        "latitude": 24.9441667,   # 24°56'39"N
        "longitude": 121.3713889,  # 121°22'17"E
        "altitude_m": 35,
        "timezone": "Asia/Taipei"
    }

@pytest.fixture(scope="session") 
def test_tle_epoch():
    """測試用的TLE epoch時間 - 使用2025-09-08的數據"""
    return datetime(2025, 9, 8, 12, 0, 0, tzinfo=timezone.utc)

@pytest.fixture
def temp_dir():
    """臨時目錄 fixture"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def mock_tle_data():
    """模擬TLE數據 - 僅用於結構測試，不用於算法驗證"""
    return {
        "line0": "STARLINK-1234",
        "line1": "1 44713U 19074A   25251.50000000  .00001000  00000-0  67960-4 0  9990",
        "line2": "2 44713  53.0000 339.0000 0001000   0.0000 280.0000 15.06000000123456",
        "epoch_year": 2025,
        "epoch_day": 251.5,
        "satellite_number": 44713,
        "classification": "U",
        "international_designator": "19074A"
    }

# =============================================================================
# 測試標記處理
# =============================================================================

def pytest_configure(config):
    """pytest 配置鉤子"""
    # 確保報告目錄存在
    reports_dir = Path(__file__).parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    # 設置測試環境變量
    os.environ["PYTEST_RUNNING"] = "1"
    os.environ["TDD_TEST_MODE"] = "1"

def pytest_collection_modifyitems(config, items):
    """動態添加測試標記"""
    for item in items:
        # 為SGP4相關測試添加標記
        if "sgp4" in item.name or "orbital" in item.name:
            item.add_marker(pytest.mark.sgp4)
            
        # 為信號相關測試添加標記  
        if "signal" in item.name or "rsrp" in item.name or "rsrq" in item.name:
            item.add_marker(pytest.mark.signal)
            
        # 為可見性相關測試添加標記
        if "visibility" in item.name or "elevation" in item.name:
            item.add_marker(pytest.mark.visibility)
            
        # 為使用真實數據的測試添加標記
        if "real_data" in item.keywords or "real_tle" in item.name:
            item.add_marker(pytest.mark.real_data)

# =============================================================================
# 性能測試支援
# =============================================================================

@pytest.fixture
def performance_baseline():
    """性能基準數據載入器"""
    def _load_baseline(test_name: str):
        baseline_file = PERFORMANCE_BASELINES_DIR / f"{test_name}.json"
        if baseline_file.exists():
            with open(baseline_file, 'r') as f:
                return json.load(f)
        return None
    return _load_baseline

@pytest.fixture
def performance_recorder():
    """性能數據記錄器"""
    def _record_performance(test_name: str, metrics: dict):
        baseline_file = PERFORMANCE_BASELINES_DIR / f"{test_name}.json"
        baseline_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 添加時間戳
        metrics["recorded_at"] = datetime.now(timezone.utc).isoformat()
        
        with open(baseline_file, 'w') as f:
            json.dump(metrics, f, indent=2)
            
    return _record_performance

# =============================================================================
# 學術合規檢查
# =============================================================================

@pytest.fixture
def academic_compliance_checker():
    """學術合規性檢查器"""
    def _check_compliance(data_source: str, algorithm_used: str):
        """檢查是否符合學術標準"""
        forbidden_patterns = [
            "mock", "fake", "random", "simulated", 
            "simplified", "estimated", "假設", "模擬"
        ]
        
        for pattern in forbidden_patterns:
            assert pattern.lower() not in data_source.lower(), \
                f"🚨 學術合規失敗: 檢測到禁用模式 '{pattern}' 在數據來源中"
            assert pattern.lower() not in algorithm_used.lower(), \
                f"🚨 學術合規失敗: 檢測到禁用模式 '{pattern}' 在算法中"
        
        return True
    
    return _check_compliance

# =============================================================================
# 錯誤處理和清理
# =============================================================================

@pytest.fixture(autouse=True)
def cleanup_environment():
    """自動清理測試環境"""
    # Setup: 測試前清理
    yield
    
    # Teardown: 測試後清理
    # 這裡可以添加清理邏輯，如臨時文件、緩存等

def pytest_runtest_makereport(item, call):
    """測試報告生成鉤子"""
    if call.when == "call":
        # 記錄測試執行時間
        duration = call.duration
        if duration > 10:  # 超過10秒的測試
            item.add_marker(pytest.mark.slow)

# =============================================================================  
# 測試跳過條件
# =============================================================================

def pytest_runtest_setup(item):
    """測試設置鉤子 - 檢查跳過條件"""
    # 如果標記為需要真實數據，檢查數據可用性
    if item.get_closest_marker("real_data"):
        # 檢查實際TLE數據路徑
        if not (STARLINK_TLE_DIR.exists() and any(STARLINK_TLE_DIR.glob("*.tle"))):
            pytest.skip("真實TLE數據不可用，跳過此測試")
            
    # 如果是慢速測試且在快速模式下，跳過
    if item.get_closest_marker("slow") and item.config.getoption("--fast", default=False):
        pytest.skip("快速模式下跳過慢速測試")