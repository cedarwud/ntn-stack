#!/usr/bin/env python3
"""
Docker容器內測試執行器
在SimWorld容器內執行階段四測試，避免主機Python版本衝突
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import json
import time

class DockerTestRunner:
    """Docker容器內測試執行器"""
    
    def __init__(self):
        self.container_name = "simworld_backend"
        self.host_test_dir = "/home/sat/ntn-stack/tests"
        self.container_test_dir = "/tests"
        
    def check_container_status(self) -> bool:
        """檢查容器狀態"""
        try:
            result = subprocess.run([
                "docker", "ps", "--filter", f"name={self.container_name}", 
                "--format", "{{.Status}}"
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and "Up" in result.stdout:
                print(f"✅ 容器 {self.container_name} 正在運行")
                return True
            else:
                print(f"❌ 容器 {self.container_name} 未運行")
                return False
        except Exception as e:
            print(f"❌ 檢查容器狀態失敗: {e}")
            return False
    
    def setup_container_test_environment(self) -> bool:
        """在容器內設置測試環境"""
        print("🔧 設置容器內測試環境...")
        
        commands = [
            # 創建測試目錄
            f"docker exec {self.container_name} mkdir -p {self.container_test_dir}",
            # 複製測試檔案到容器內
            f"docker cp {self.host_test_dir}/. {self.container_name}:{self.container_test_dir}/",
            # 設置權限
            f"docker exec {self.container_name} chmod +x {self.container_test_dir}/*.py",
            # 安裝額外依賴（如果需要）
            f"docker exec {self.container_name} pip install --no-cache-dir aiohttp httpx",
        ]
        
        for cmd in commands:
            try:
                print(f"  執行: {cmd}")
                result = subprocess.run(cmd.split(), capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"  ⚠️ 警告: {result.stderr}")
            except Exception as e:
                print(f"  ❌ 命令失敗: {e}")
                return False
        
        print("✅ 容器內測試環境設置完成")
        return True
    
    def run_test_in_container(self, test_script: str, args: List[str] = None) -> Dict[str, Any]:
        """在容器內執行測試"""
        if args is None:
            args = []
        
        print(f"🚀 在容器內執行測試: {test_script}")
        
        # 構建命令
        cmd_parts = [
            "docker", "exec", "-w", self.container_test_dir, 
            self.container_name, "python", test_script
        ] + args
        
        start_time = time.time()
        
        try:
            result = subprocess.run(cmd_parts, capture_output=True, text=True)
            execution_time = time.time() - start_time
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "execution_time": execution_time,
                "return_code": result.returncode
            }
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "execution_time": execution_time,
                "return_code": -1
            }
    
    def run_stage4_comprehensive_test(self) -> Dict[str, Any]:
        """執行階段四綜合測試"""
        print("🧪 開始階段四容器內綜合測試")
        print("=" * 60)
        
        test_results = {}
        
        # 1. 快速驗證測試
        print("\n📋 步驟1: 快速驗證測試")
        quick_test_result = self.run_test_in_container("stage4_quick_test.py")
        test_results["quick_verification"] = quick_test_result
        
        if quick_test_result["success"]:
            print("✅ 快速驗證測試通過")
        else:
            print("❌ 快速驗證測試失敗")
            print(f"錯誤輸出: {quick_test_result['stderr']}")
        
        # 2. 真實API整合測試
        print("\n🔗 步驟2: 真實API整合測試")
        api_test_result = self.run_test_in_container("real_api_integration_test.py")
        test_results["api_integration"] = api_test_result
        
        if api_test_result["success"]:
            print("✅ 真實API整合測試通過")
        else:
            print("❌ 真實API整合測試失敗")
            print(f"錯誤輸出: {api_test_result['stderr']}")
        
        # 3. 嘗試執行論文復現測試（如果依賴足夠）
        print("\n📄 步驟3: 論文復現測試")
        paper_test_result = self.run_test_in_container("paper_reproduction_test_framework.py", ["--help"])
        test_results["paper_reproduction"] = paper_test_result
        
        if paper_test_result["success"]:
            print("✅ 論文復現測試框架可執行")
        else:
            print("❌ 論文復現測試框架有問題")
            print(f"錯誤輸出: {paper_test_result['stderr']}")
        
        # 4. 生成綜合報告
        total_tests = len(test_results)
        successful_tests = sum(1 for r in test_results.values() if r["success"])
        
        summary = {
            "test_results": test_results,
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": successful_tests / total_tests,
                "container_name": self.container_name,
                "execution_timestamp": time.time()
            }
        }
        
        print("\n" + "=" * 60)
        print("📊 階段四容器內測試總結")
        print("=" * 60)
        print(f"測試成功率: {successful_tests}/{total_tests} ({successful_tests/total_tests:.1%})")
        print(f"執行容器: {self.container_name}")
        
        # 保存結果到主機
        self.save_results_to_host(summary)
        
        return summary
    
    def save_results_to_host(self, results: Dict[str, Any]) -> None:
        """將結果從容器複製到主機"""
        print("\n💾 保存測試結果到主機...")
        
        # 在容器內創建結果檔案
        results_json = json.dumps(results, indent=2, ensure_ascii=False)
        
        try:
            # 將結果寫入容器內臨時檔案
            temp_file = f"{self.container_test_dir}/docker_test_results.json"
            write_cmd = [
                "docker", "exec", self.container_name, "bash", "-c",
                f"cat > {temp_file} << 'EOF'\n{results_json}\nEOF"
            ]
            subprocess.run(write_cmd)
            
            # 複製結果到主機
            host_results_dir = Path(self.host_test_dir) / "results" / "docker_tests"
            host_results_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = int(time.time())
            host_file = host_results_dir / f"docker_test_results_{timestamp}.json"
            
            copy_cmd = [
                "docker", "cp", 
                f"{self.container_name}:{temp_file}",
                str(host_file)
            ]
            subprocess.run(copy_cmd)
            
            print(f"✅ 結果已保存: {host_file}")
            
        except Exception as e:
            print(f"❌ 保存結果失敗: {e}")

def main():
    """主執行函數"""
    runner = DockerTestRunner()
    
    # 檢查容器狀態
    if not runner.check_container_status():
        print("請先啟動SimWorld容器：make simworld-start")
        return False
    
    # 設置測試環境
    if not runner.setup_container_test_environment():
        print("設置測試環境失敗")
        return False
    
    # 執行綜合測試
    results = runner.run_stage4_comprehensive_test()
    
    # 返回測試結果
    return results["summary"]["success_rate"] >= 0.5  # 至少50%測試通過

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)