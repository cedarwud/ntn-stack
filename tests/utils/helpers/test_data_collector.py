"""
測試結果數據收集器
Test Data Collector for various test frameworks and formats
"""

import json
import xml.etree.ElementTree as ET
import csv
import re
import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import pandas as pd
import yaml


@dataclass
class TestResult:
    """測試結果數據結構"""
    test_name: str
    test_type: str
    status: str  # passed, failed, skipped, error
    duration: float
    timestamp: datetime
    error_message: Optional[str] = None
    failure_type: Optional[str] = None
    test_file: Optional[str] = None
    test_class: Optional[str] = None
    test_method: Optional[str] = None
    build_number: Optional[str] = None
    branch: Optional[str] = None
    commit_hash: Optional[str] = None
    environment: Optional[str] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PerformanceMetrics:
    """性能指標數據結構"""
    test_name: str
    timestamp: datetime
    response_time: float
    throughput: float
    error_rate: float
    cpu_usage: float
    memory_usage: float
    network_io: float
    disk_io: float
    concurrent_users: int = 0
    transactions_per_second: float = 0.0
    percentiles: Dict[str, float] = None
    
    def __post_init__(self):
        if self.percentiles is None:
            self.percentiles = {}


@dataclass
class TestSuite:
    """測試套件結果"""
    name: str
    timestamp: datetime
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration: float
    success_rate: float
    tests: List[TestResult]
    performance_metrics: List[PerformanceMetrics] = None
    
    def __post_init__(self):
        if self.performance_metrics is None:
            self.performance_metrics = []
        if self.total_tests == 0 and self.tests:
            self.total_tests = len(self.tests)
        self.success_rate = (self.passed / self.total_tests) * 100 if self.total_tests > 0 else 0


class DataCollector(ABC):
    """數據收集器抽象基類"""
    
    @abstractmethod
    def collect(self, source_path: str) -> List[TestSuite]:
        """收集測試數據"""
        pass


class JUnitCollector(DataCollector):
    """JUnit XML格式數據收集器"""
    
    def collect(self, source_path: str) -> List[TestSuite]:
        """收集JUnit XML測試結果"""
        test_suites = []
        
        try:
            tree = ET.parse(source_path)
            root = tree.getroot()
            
            # 處理testsuite或testsuites
            if root.tag == 'testsuite':
                test_suites.append(self._parse_testsuite(root))
            elif root.tag == 'testsuites':
                for testsuite in root.findall('testsuite'):
                    test_suites.append(self._parse_testsuite(testsuite))
                    
        except Exception as e:
            print(f"Error parsing JUnit XML {source_path}: {e}")
            
        return test_suites
    
    def _parse_testsuite(self, testsuite_elem) -> TestSuite:
        """解析testsuite元素"""
        name = testsuite_elem.get('name', 'Unknown')
        timestamp = self._parse_timestamp(testsuite_elem.get('timestamp'))
        tests = int(testsuite_elem.get('tests', 0))
        failures = int(testsuite_elem.get('failures', 0))
        errors = int(testsuite_elem.get('errors', 0))
        skipped = int(testsuite_elem.get('skipped', 0))
        time = float(testsuite_elem.get('time', 0))
        
        passed = tests - failures - errors - skipped
        
        test_results = []
        for testcase in testsuite_elem.findall('testcase'):
            test_results.append(self._parse_testcase(testcase, timestamp))
        
        return TestSuite(
            name=name,
            timestamp=timestamp,
            total_tests=tests,
            passed=passed,
            failed=failures,
            skipped=skipped,
            errors=errors,
            duration=time,
            success_rate=(passed / tests) * 100 if tests > 0 else 0,
            tests=test_results
        )
    
    def _parse_testcase(self, testcase_elem, suite_timestamp: datetime) -> TestResult:
        """解析testcase元素"""
        name = testcase_elem.get('name', 'Unknown')
        classname = testcase_elem.get('classname', '')
        time = float(testcase_elem.get('time', 0))
        
        # 確定測試狀態
        status = 'passed'
        error_message = None
        failure_type = None
        
        failure_elem = testcase_elem.find('failure')
        error_elem = testcase_elem.find('error')
        skipped_elem = testcase_elem.find('skipped')
        
        if failure_elem is not None:
            status = 'failed'
            error_message = failure_elem.text
            failure_type = failure_elem.get('type', 'Failure')
        elif error_elem is not None:
            status = 'error'
            error_message = error_elem.text
            failure_type = error_elem.get('type', 'Error')
        elif skipped_elem is not None:
            status = 'skipped'
            error_message = skipped_elem.text
        
        return TestResult(
            test_name=name,
            test_type='junit',
            status=status,
            duration=time,
            timestamp=suite_timestamp,
            error_message=error_message,
            failure_type=failure_type,
            test_class=classname
        )
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> datetime:
        """解析時間戳"""
        if not timestamp_str:
            return datetime.now()
        
        try:
            # 嘗試多種時間格式
            formats = [
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%SZ'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
                    
            return datetime.now()
        except Exception:
            return datetime.now()


class JSONCollector(DataCollector):
    """JSON格式數據收集器"""
    
    def collect(self, source_path: str) -> List[TestSuite]:
        """收集JSON格式測試結果"""
        test_suites = []
        
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                # 多個測試套件
                for suite_data in data:
                    test_suites.append(self._parse_json_suite(suite_data))
            else:
                # 單個測試套件
                test_suites.append(self._parse_json_suite(data))
                
        except Exception as e:
            print(f"Error parsing JSON {source_path}: {e}")
            
        return test_suites
    
    def _parse_json_suite(self, suite_data: Dict[str, Any]) -> TestSuite:
        """解析JSON測試套件數據"""
        name = suite_data.get('name', 'Unknown')
        timestamp = self._parse_json_timestamp(suite_data.get('timestamp'))
        
        tests = []
        if 'tests' in suite_data:
            for test_data in suite_data['tests']:
                tests.append(self._parse_json_test(test_data, timestamp))
        
        # 統計結果
        total_tests = len(tests)
        passed = sum(1 for t in tests if t.status == 'passed')
        failed = sum(1 for t in tests if t.status == 'failed')
        skipped = sum(1 for t in tests if t.status == 'skipped')
        errors = sum(1 for t in tests if t.status == 'error')
        duration = sum(t.duration for t in tests)
        
        # 處理性能指標
        performance_metrics = []
        if 'performance' in suite_data:
            for perf_data in suite_data['performance']:
                performance_metrics.append(self._parse_performance_metrics(perf_data))
        
        return TestSuite(
            name=name,
            timestamp=timestamp,
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration=duration,
            success_rate=(passed / total_tests) * 100 if total_tests > 0 else 0,
            tests=tests,
            performance_metrics=performance_metrics
        )
    
    def _parse_json_test(self, test_data: Dict[str, Any], suite_timestamp: datetime) -> TestResult:
        """解析JSON測試數據"""
        return TestResult(
            test_name=test_data.get('name', 'Unknown'),
            test_type=test_data.get('type', 'json'),
            status=test_data.get('status', 'unknown'),
            duration=test_data.get('duration', 0.0),
            timestamp=self._parse_json_timestamp(test_data.get('timestamp')) or suite_timestamp,
            error_message=test_data.get('error_message'),
            failure_type=test_data.get('failure_type'),
            test_file=test_data.get('file'),
            test_class=test_data.get('class'),
            test_method=test_data.get('method'),
            build_number=test_data.get('build_number'),
            branch=test_data.get('branch'),
            commit_hash=test_data.get('commit_hash'),
            environment=test_data.get('environment'),
            tags=test_data.get('tags', []),
            metadata=test_data.get('metadata', {})
        )
    
    def _parse_performance_metrics(self, perf_data: Dict[str, Any]) -> PerformanceMetrics:
        """解析性能指標數據"""
        return PerformanceMetrics(
            test_name=perf_data.get('test_name', 'Unknown'),
            timestamp=self._parse_json_timestamp(perf_data.get('timestamp')),
            response_time=perf_data.get('response_time', 0.0),
            throughput=perf_data.get('throughput', 0.0),
            error_rate=perf_data.get('error_rate', 0.0),
            cpu_usage=perf_data.get('cpu_usage', 0.0),
            memory_usage=perf_data.get('memory_usage', 0.0),
            network_io=perf_data.get('network_io', 0.0),
            disk_io=perf_data.get('disk_io', 0.0),
            concurrent_users=perf_data.get('concurrent_users', 0),
            transactions_per_second=perf_data.get('tps', 0.0),
            percentiles=perf_data.get('percentiles', {})
        )
    
    def _parse_json_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """解析JSON時間戳"""
        if not timestamp_str:
            return None
        
        try:
            if isinstance(timestamp_str, (int, float)):
                return datetime.fromtimestamp(timestamp_str)
            
            # ISO格式
            if 'T' in timestamp_str:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except Exception:
            return None


class CSVCollector(DataCollector):
    """CSV格式數據收集器"""
    
    def collect(self, source_path: str) -> List[TestSuite]:
        """收集CSV格式測試結果"""
        test_suites = []
        
        try:
            df = pd.read_csv(source_path)
            
            # 按測試套件分組（如果有suite_name列）
            if 'suite_name' in df.columns:
                for suite_name, group in df.groupby('suite_name'):
                    test_suites.append(self._parse_csv_group(suite_name, group))
            else:
                # 單個測試套件
                suite_name = Path(source_path).stem
                test_suites.append(self._parse_csv_group(suite_name, df))
                
        except Exception as e:
            print(f"Error parsing CSV {source_path}: {e}")
            
        return test_suites
    
    def _parse_csv_group(self, suite_name: str, df: pd.DataFrame) -> TestSuite:
        """解析CSV分組數據"""
        tests = []
        
        for _, row in df.iterrows():
            test = TestResult(
                test_name=row.get('test_name', 'Unknown'),
                test_type=row.get('test_type', 'csv'),
                status=row.get('status', 'unknown'),
                duration=row.get('duration', 0.0),
                timestamp=pd.to_datetime(row.get('timestamp', datetime.now())),
                error_message=row.get('error_message'),
                failure_type=row.get('failure_type'),
                test_file=row.get('test_file'),
                test_class=row.get('test_class'),
                test_method=row.get('test_method')
            )
            tests.append(test)
        
        # 統計結果
        total_tests = len(tests)
        passed = sum(1 for t in tests if t.status == 'passed')
        failed = sum(1 for t in tests if t.status == 'failed')
        skipped = sum(1 for t in tests if t.status == 'skipped')
        errors = sum(1 for t in tests if t.status == 'error')
        duration = sum(t.duration for t in tests)
        
        return TestSuite(
            name=suite_name,
            timestamp=min(t.timestamp for t in tests) if tests else datetime.now(),
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            duration=duration,
            success_rate=(passed / total_tests) * 100 if total_tests > 0 else 0,
            tests=tests
        )


class TestDataManager:
    """測試數據管理器"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or "/home/sat/ntn-stack/tests/data/test_results.db"
        self.collectors = {
            '.xml': JUnitCollector(),
            '.json': JSONCollector(),
            '.csv': CSVCollector()
        }
        self._init_database()
    
    def _init_database(self):
        """初始化數據庫"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 創建測試套件表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_suites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    total_tests INTEGER,
                    passed INTEGER,
                    failed INTEGER,
                    skipped INTEGER,
                    errors INTEGER,
                    duration REAL,
                    success_rate REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 創建測試結果表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    suite_id INTEGER,
                    test_name TEXT NOT NULL,
                    test_type TEXT,
                    status TEXT,
                    duration REAL,
                    timestamp DATETIME,
                    error_message TEXT,
                    failure_type TEXT,
                    test_file TEXT,
                    test_class TEXT,
                    test_method TEXT,
                    build_number TEXT,
                    branch TEXT,
                    commit_hash TEXT,
                    environment TEXT,
                    tags TEXT,
                    metadata TEXT,
                    FOREIGN KEY (suite_id) REFERENCES test_suites (id)
                )
            ''')
            
            # 創建性能指標表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    suite_id INTEGER,
                    test_name TEXT NOT NULL,
                    timestamp DATETIME,
                    response_time REAL,
                    throughput REAL,
                    error_rate REAL,
                    cpu_usage REAL,
                    memory_usage REAL,
                    network_io REAL,
                    disk_io REAL,
                    concurrent_users INTEGER,
                    transactions_per_second REAL,
                    percentiles TEXT,
                    FOREIGN KEY (suite_id) REFERENCES test_suites (id)
                )
            ''')
            
            conn.commit()
    
    def collect_from_path(self, source_path: str) -> List[TestSuite]:
        """從路徑收集測試數據"""
        path = Path(source_path)
        all_suites = []
        
        if path.is_file():
            # 單個文件
            collector = self.collectors.get(path.suffix.lower())
            if collector:
                all_suites.extend(collector.collect(str(path)))
        elif path.is_dir():
            # 目錄遞歸搜索
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    collector = self.collectors.get(file_path.suffix.lower())
                    if collector:
                        all_suites.extend(collector.collect(str(file_path)))
        
        return all_suites
    
    def store_test_suites(self, test_suites: List[TestSuite]):
        """存儲測試套件到數據庫"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for suite in test_suites:
                # 插入測試套件
                cursor.execute('''
                    INSERT INTO test_suites 
                    (name, timestamp, total_tests, passed, failed, skipped, errors, duration, success_rate)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    suite.name, suite.timestamp, suite.total_tests, suite.passed,
                    suite.failed, suite.skipped, suite.errors, suite.duration, suite.success_rate
                ))
                
                suite_id = cursor.lastrowid
                
                # 插入測試結果
                for test in suite.tests:
                    cursor.execute('''
                        INSERT INTO test_results 
                        (suite_id, test_name, test_type, status, duration, timestamp, 
                         error_message, failure_type, test_file, test_class, test_method,
                         build_number, branch, commit_hash, environment, tags, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        suite_id, test.test_name, test.test_type, test.status, test.duration,
                        test.timestamp, test.error_message, test.failure_type, test.test_file,
                        test.test_class, test.test_method, test.build_number, test.branch,
                        test.commit_hash, test.environment, json.dumps(test.tags),
                        json.dumps(test.metadata)
                    ))
                
                # 插入性能指標
                for perf in suite.performance_metrics:
                    cursor.execute('''
                        INSERT INTO performance_metrics 
                        (suite_id, test_name, timestamp, response_time, throughput, error_rate,
                         cpu_usage, memory_usage, network_io, disk_io, concurrent_users,
                         transactions_per_second, percentiles)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        suite_id, perf.test_name, perf.timestamp, perf.response_time,
                        perf.throughput, perf.error_rate, perf.cpu_usage, perf.memory_usage,
                        perf.network_io, perf.disk_io, perf.concurrent_users,
                        perf.transactions_per_second, json.dumps(perf.percentiles)
                    ))
            
            conn.commit()
    
    def get_test_data(self, 
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      test_type: Optional[str] = None,
                      status: Optional[str] = None) -> pd.DataFrame:
        """獲取測試數據"""
        query = '''
            SELECT ts.name as suite_name, tr.* 
            FROM test_results tr
            JOIN test_suites ts ON tr.suite_id = ts.id
            WHERE 1=1
        '''
        params = []
        
        if start_date:
            query += ' AND tr.timestamp >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND tr.timestamp <= ?'
            params.append(end_date)
        
        if test_type:
            query += ' AND tr.test_type = ?'
            params.append(test_type)
        
        if status:
            query += ' AND tr.status = ?'
            params.append(status)
        
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params)
    
    def get_performance_data(self,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> pd.DataFrame:
        """獲取性能數據"""
        query = '''
            SELECT ts.name as suite_name, pm.* 
            FROM performance_metrics pm
            JOIN test_suites ts ON pm.suite_id = ts.id
            WHERE 1=1
        '''
        params = []
        
        if start_date:
            query += ' AND pm.timestamp >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND pm.timestamp <= ?'
            params.append(end_date)
        
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=params)
    
    def cleanup_old_data(self, retention_days: int = 30):
        """清理舊數據"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 刪除舊的測試結果
            cursor.execute('DELETE FROM test_results WHERE timestamp < ?', (cutoff_date,))
            cursor.execute('DELETE FROM performance_metrics WHERE timestamp < ?', (cutoff_date,))
            cursor.execute('DELETE FROM test_suites WHERE timestamp < ?', (cutoff_date,))
            
            conn.commit()


if __name__ == "__main__":
    # 示例使用
    manager = TestDataManager()
    
    # 收集測試數據
    test_suites = manager.collect_from_path("/home/sat/ntn-stack/tests/reports")
    
    # 存儲到數據庫
    if test_suites:
        manager.store_test_suites(test_suites)
        print(f"Collected and stored {len(test_suites)} test suites")
    
    # 獲取最近的測試數據
    recent_data = manager.get_test_data(
        start_date=datetime.now() - timedelta(days=7)
    )
    print(f"Recent test data: {len(recent_data)} records")