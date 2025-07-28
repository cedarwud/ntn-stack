#!/usr/bin/env python3
"""
外部環境 CelesTrak 測試腳本
用於在有正常網路連接的環境中測試 CelesTrak URL

使用方法：
1. 將此腳本複製到有網路連接的環境
2. 安裝依賴：pip install aiohttp aiofiles
3. 運行：python test_celestrak_external.py
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timezone

async def test_celestrak_urls():
    """測試所有 CelesTrak URL"""
    print("🚀 CelesTrak TLE 數據源測試")
    print("=" * 50)
    
    # 正確的 CelesTrak URL
    test_urls = [
        {
            "name": "Starlink TLE (標準格式)",
            "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle",
            "format": "tle",
            "expected_count": "5000+"
        },
        {
            "name": "Starlink JSON (結構化數據)",
            "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=json",
            "format": "json",
            "expected_count": "5000+"
        },
        {
            "name": "OneWeb TLE",
            "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=oneweb&FORMAT=tle",
            "format": "tle",
            "expected_count": "600+"
        },
        {
            "name": "GPS TLE",
            "url": "https://celestrak.org/NORAD/elements/gp.php?GROUP=gps-ops&FORMAT=tle",
            "format": "tle",
            "expected_count": "30+"
        },
        {
            "name": "高精度 SupGP 數據",
            "url": "https://celestrak.org/NORAD/elements/supplemental/?FORMAT=json",
            "format": "json",
            "expected_count": "1000+"
        }
    ]
    
    results = []
    timeout = aiohttp.ClientTimeout(total=30)
    
    for test_case in test_urls:
        print(f"\n🔍 測試: {test_case['name']}")
        print(f"📍 URL: {test_case['url']}")
        
        start_time = time.time()
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = {
                    'User-Agent': 'NTN-Stack-Research/1.0 (LEO Satellite Handover Research)'
                }
                
                async with session.get(test_case['url'], headers=headers) as response:
                    download_time = time.time() - start_time
                    
                    if response.status == 200:
                        content = await response.text()
                        
                        result = {
                            "name": test_case['name'],
                            "url": test_case['url'],
                            "status": "SUCCESS",
                            "http_status": response.status,
                            "content_length": len(content),
                            "download_time": round(download_time, 2),
                            "satellite_count": 0,
                            "sample_data": ""
                        }
                        
                        # 分析數據內容
                        if test_case['format'] == 'tle':
                            lines = content.strip().split('\n')
                            tle_count = len([l for l in lines if l.strip().startswith('1 ')])
                            result["satellite_count"] = tle_count
                            
                            # 提取前3顆衛星作為樣本
                            sample_satellites = []
                            tle_lines = [l.strip() for l in lines if l.strip()]
                            
                            for i in range(0, min(9, len(tle_lines)), 3):
                                if i + 2 < len(tle_lines):
                                    name = tle_lines[i]
                                    line1 = tle_lines[i+1]
                                    line2 = tle_lines[i+2]
                                    if line1.startswith('1 ') and line2.startswith('2 '):
                                        norad_id = line1[2:7].strip()
                                        sample_satellites.append(f"{name} (ID: {norad_id})")
                            
                            result["sample_data"] = "; ".join(sample_satellites[:3])
                            
                        elif test_case['format'] == 'json':
                            try:
                                data = json.loads(content)
                                if isinstance(data, list):
                                    result["satellite_count"] = len(data)
                                    if data:
                                        first_item = data[0]
                                        if 'OBJECT_NAME' in first_item:
                                            sample_names = [item.get('OBJECT_NAME', 'Unknown')[:20] 
                                                          for item in data[:3]]
                                            result["sample_data"] = "; ".join(sample_names)
                                        else:
                                            result["sample_data"] = f"JSON keys: {list(first_item.keys())[:5]}"
                            except json.JSONDecodeError:
                                result["sample_data"] = "非標準JSON格式"
                        
                        print(f"✅ 成功！")
                        print(f"   📊 衛星數量: {result['satellite_count']}")
                        print(f"   📦 數據大小: {result['content_length']:,} 字符")
                        print(f"   ⏱️ 下載時間: {result['download_time']} 秒")
                        print(f"   📝 樣本數據: {result['sample_data'][:100]}...")
                        
                    else:
                        result = {
                            "name": test_case['name'],
                            "url": test_case['url'],
                            "status": "HTTP_ERROR",
                            "http_status": response.status,
                            "download_time": round(download_time, 2),
                            "error": f"HTTP {response.status}"
                        }
                        print(f"❌ HTTP錯誤: {response.status}")
                    
                    results.append(result)
                    
        except asyncio.TimeoutError:
            result = {
                "name": test_case['name'],
                "url": test_case['url'],
                "status": "TIMEOUT",
                "download_time": round(time.time() - start_time, 2),
                "error": "請求超時"
            }
            print(f"⏰ 超時")
            results.append(result)
            
        except Exception as e:
            result = {
                "name": test_case['name'],
                "url": test_case['url'],
                "status": "ERROR",
                "download_time": round(time.time() - start_time, 2),
                "error": str(e)
            }
            print(f"❌ 錯誤: {e}")
            results.append(result)
    
    # 生成測試報告
    print("\n" + "=" * 50)
    print("📋 測試報告總結")
    print("=" * 50)
    
    successful_tests = [r for r in results if r["status"] == "SUCCESS"]
    total_satellites = sum(r.get("satellite_count", 0) for r in successful_tests)
    
    print(f"✅ 成功測試: {len(successful_tests)}/{len(results)}")
    print(f"📊 總衛星數量: {total_satellites:,}")
    print(f"🕒 測試時間: {datetime.now(timezone.utc).isoformat()}")
    
    if successful_tests:
        print(f"\n🎯 **Phase 0 目標達成評估**:")
        starlink_result = next((r for r in successful_tests if "starlink" in r["name"].lower()), None)
        if starlink_result:
            starlink_count = starlink_result.get("satellite_count", 0)
            print(f"   Starlink 衛星數量: {starlink_count}")
            if starlink_count >= 5000:
                print(f"   ✅ 超過 Phase 0 目標 (~6000顆)！")
            else:
                print(f"   ⚠️ 少於預期，但仍是大量真實數據")
    
    # 保存結果到文件
    with open("celestrak_test_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "test_time": datetime.now(timezone.utc).isoformat(),
            "total_tests": len(results),
            "successful_tests": len(successful_tests),
            "total_satellites": total_satellites,
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 詳細結果已保存到: celestrak_test_results.json")
    
    return results

async def main():
    """主函數"""
    print("🌟 CelesTrak 外部環境測試工具")
    print("   用於驗證 NTN Stack Phase 0 的數據源可用性")
    print()
    
    results = await test_celestrak_urls()
    
    # 如果有成功的結果，顯示如何在 NTN Stack 中使用
    successful_results = [r for r in results if r["status"] == "SUCCESS"]
    if successful_results:
        print("\n🚀 **在 NTN Stack 中的使用建議**:")
        print("1. 將這些 URL 更新到 TLE 下載器配置中")
        print("2. 在有網路連接的環境中運行 Phase 0 測試")
        print("3. 下載的數據可以緩存供後續使用")
        print()
        print("📝 **正確的 URL 列表**:")
        for result in successful_results:
            print(f"   ✅ {result['name']}")
            print(f"      {result['url']}")

if __name__ == "__main__":
    asyncio.run(main())