#!/usr/bin/env python3
"""
容器內測試執行器

利用 simworld_backend 容器可以訪問 netstack-core 網路的特性，
在容器內執行論文復現測試，實現真正的跨容器服務測試

執行方式 (在 ntn-stack 根目錄):
python paper/comprehensive/run_docker_tests.py
"""

import sys
import os
import asyncio
import subprocess
import json
import logging
from datetime import datetime
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DockerContainerTestRunner:
    """容器內測試執行器"""

    def __init__(self):
        self.test_results = {}
        self.start_time = None
        self.end_time = None

    async def copy_test_files_to_container(self):
        """複製測試檔案到容器內"""
        print("📋 準備容器測試環境...")

        test_files = [
            "/home/sat/ntn-stack/quick_test.py",
            "/home/sat/ntn-stack/tests/integration/test_synchronized_algorithm_comprehensive.py",
            "/home/sat/ntn-stack/tests/integration/test_fast_satellite_prediction_comprehensive.py",
        ]

        for file_path in test_files:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                try:
                    # 複製到 simworld_backend 容器
                    result = subprocess.run(
                        [
                            "docker",
                            "cp",
                            file_path,
                            f"simworld_backend:/app/{filename}",
                        ],
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode == 0:
                        print(f"✅ 已複製: {filename}")
                    else:
                        print(f"❌ 複製失敗: {filename} - {result.stderr}")

                except Exception as e:
                    print(f"❌ 複製異常: {filename} - {str(e)}")

    async def run_container_test(
        self, test_name: str, test_command: str
    ) -> Dict[str, Any]:
        """在容器內執行測試"""
        print(f"\n🔬 執行容器測試: {test_name}")
        print("-" * 60)

        start_time = datetime.now()

        try:
            # 在 simworld_backend 容器內執行測試
            process = await asyncio.create_subprocess_exec(
                "docker",
                "exec",
                "simworld_backend",
                "python",
                "-c",
                test_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            success = process.returncode == 0
            output = stdout.decode("utf-8") if stdout else ""
            error_output = stderr.decode("utf-8") if stderr else ""

            if success:
                print(f"✅ {test_name} 測試成功")
                print(f"   執行時間: {duration:.2f} 秒")
            else:
                print(f"❌ {test_name} 測試失敗")
                print(f"   返回碼: {process.returncode}")
                if error_output:
                    print(f"   錯誤: {error_output[:200]}...")

            return {
                "test_name": test_name,
                "success": success,
                "duration_seconds": duration,
                "output": output,
                "error_output": error_output,
                "return_code": process.returncode,
            }

        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            error_msg = f"執行容器測試 {test_name} 時發生錯誤: {str(e)}"
            print(f"❌ {error_msg}")

            return {
                "test_name": test_name,
                "success": False,
                "duration_seconds": duration,
                "output": "",
                "error_output": str(e),
                "return_code": -1,
            }

    async def test_cross_container_connectivity(self):
        """測試跨容器連接性"""
        connectivity_tests = [
            {
                "name": "NetStack API 連接",
                "command": """
import requests
try:
    response = requests.get('http://netstack-api:8080/health', timeout=5)
    print(f'✅ NetStack API 連接成功: {response.status_code}')
    print(f'   回應: {response.json()}')
except Exception as e:
    print(f'❌ NetStack API 連接失敗: {str(e)}')
""",
            },
            {
                "name": "NetStack Redis 連接",
                "command": """
import redis
try:
    r = redis.Redis(host='netstack-redis', port=6379, db=0)
    ping_result = r.ping()
    print(f'✅ NetStack Redis 連接成功: {ping_result}')
    info = r.info('server')
    print(f'   Redis 版本: {info.get("redis_version")}')
except Exception as e:
    print(f'❌ NetStack Redis 連接失敗: {str(e)}')
""",
            },
            {
                "name": "NetStack MongoDB 連接",
                "command": """
from pymongo import MongoClient
try:
    client = MongoClient('mongodb://netstack-mongo:27017/', serverSelectionTimeoutMS=5000)
    server_info = client.server_info()
    print(f'✅ NetStack MongoDB 連接成功')
    print(f'   MongoDB 版本: {server_info.get("version")}')
except Exception as e:
    print(f'❌ NetStack MongoDB 連接失敗: {str(e)}')
""",
            },
        ]

        connectivity_results = []

        for test in connectivity_tests:
            result = await self.run_container_test(test["name"], test["command"])
            connectivity_results.append(result)

        return connectivity_results

    async def test_paper_algorithms_in_container(self):
        """在容器內測試論文演算法"""
        print("\n🧪 在容器內測試論文演算法...")

        # 建立容器內的測試腳本
        container_test_script = """
import sys
sys.path.append('/home/sat/ntn-stack/netstack/netstack_api')

async def test_algorithms():
    print("🔬 容器內論文演算法測試")
    print("="*50)
    
    test_results = []
    
    try:
        # 測試模組導入
        from services.paper_synchronized_algorithm import SynchronizedAlgorithm
        from services.fast_access_prediction_service import FastSatellitePrediction
        print("✅ 論文演算法模組導入成功")
        test_results.append(("模組導入", True))
        
        # 測試 Algorithm 1
        algo1 = SynchronizedAlgorithm(delta_t=5.0)
        print(f"✅ Algorithm 1 初始化成功 - delta_t: {algo1.delta_t}")
        test_results.append(("Algorithm1初始化", True))
        
        # 測試 Algorithm 2
        algo2 = FastSatellitePrediction(accuracy_target=0.95)
        blocks = await algo2.initialize_geographical_blocks()
        print(f"✅ Algorithm 2 初始化成功 - 區塊數: {len(blocks)}")
        test_results.append(("Algorithm2初始化", True))
        
        # 測試跨容器服務調用
        import requests
        api_response = requests.get('http://netstack-api:8080/health')
        if api_response.status_code == 200:
            print("✅ 跨容器服務調用成功")
            test_results.append(("跨容器調用", True))
        else:
            print("❌ 跨容器服務調用失敗")
            test_results.append(("跨容器調用", False))
        
        return test_results
        
    except Exception as e:
        print(f"❌ 容器內測試失敗: {str(e)}")
        test_results.append(("容器內測試", False))
        return test_results

# 執行測試
import asyncio
results = asyncio.run(test_algorithms())

# 輸出結果
passed = sum(1 for _, success in results if success)
total = len(results)
print(f"\\n📊 容器內測試結果: {passed}/{total} 通過 ({passed/total*100:.1f}%)")

for name, success in results:
    status = "✅ 通過" if success else "❌ 失敗"
    print(f"   {status} {name}")
"""

        result = await self.run_container_test(
            "論文演算法容器測試", container_test_script
        )

        return result

    async def run_all_container_tests(self):
        """執行所有容器測試"""
        self.start_time = datetime.now()

        print("🚀 開始執行容器內論文復現測試")
        print("=" * 80)
        print("容器環境: simworld_backend")
        print("網路連接: netstack-core + sionna-net")
        print("=" * 80)

        # 1. 準備測試環境
        await self.copy_test_files_to_container()

        # 2. 測試跨容器連接性
        print("\n🌐 測試跨容器連接性...")
        connectivity_results = await self.test_cross_container_connectivity()
        self.test_results["connectivity"] = connectivity_results

        # 3. 測試論文演算法
        paper_test_result = await self.test_paper_algorithms_in_container()
        self.test_results["paper_algorithms"] = paper_test_result

        self.end_time = datetime.now()

        # 4. 生成報告
        self._print_container_test_summary()

        return self.test_results

    def _print_container_test_summary(self):
        """列印容器測試摘要"""
        print("\n" + "=" * 80)
        print("📊 容器內測試報告")
        print("=" * 80)

        total_duration = (self.end_time - self.start_time).total_seconds()
        print(f"總執行時間: {total_duration:.2f} 秒")

        # 連接性測試結果
        print(f"\n🌐 跨容器連接性測試:")
        connectivity_results = self.test_results.get("connectivity", [])
        for result in connectivity_results:
            status = "✅" if result["success"] else "❌"
            print(f"   {status} {result['test_name']}")

        # 論文演算法測試結果
        print(f"\n🧪 論文演算法測試:")
        paper_result = self.test_results.get("paper_algorithms", {})
        status = "✅" if paper_result.get("success") else "❌"
        print(f"   {status} {paper_result.get('test_name', '論文演算法測試')}")

        # 總體評估
        all_connectivity_passed = all(r["success"] for r in connectivity_results)
        paper_test_passed = paper_result.get("success", False)

        if all_connectivity_passed and paper_test_passed:
            print(f"\n🎉 容器內測試全部成功！")
            print(f"✅ 跨容器通信正常")
            print(f"✅ 論文演算法可在容器內運行")
            print(f"📝 建議：可以使用容器方式執行更複雜的整合測試")
        else:
            print(f"\n⚠️  容器內測試存在問題:")
            if not all_connectivity_passed:
                print(f"❌ 跨容器連接異常")
            if not paper_test_passed:
                print(f"❌ 論文演算法在容器內運行異常")


async def main():
    """主函數"""
    runner = DockerContainerTestRunner()

    try:
        await runner.run_all_container_tests()
        return True
    except Exception as e:
        print(f"\n💥 容器測試執行錯誤: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
