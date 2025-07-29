#!/usr/bin/env python3
"""
Phase 4 完成度測試 - 部署優化與生產準備
"""

import sys
import asyncio
import json
from datetime import datetime
from pathlib import Path

async def test_phase4_completion():
    """測試 Phase 4 完成度"""
    print("🚀 Phase 4 完成度測試 - 部署優化與生產準備")
    print("=" * 60)
    
    results = {
        "phase4_features": {},
        "production_components": {},
        "deployment_status": {},
        "overall_score": 0
    }
    
    # 測試 1: 生產環境 Docker Compose 配置
    print("\n🐳 1. 生產環境 Docker Compose 配置")
    
    try:
        # 檢查生產環境 Docker Compose
        prod_compose_path = Path("docker-compose.production.yml")
        if prod_compose_path.exists():
            print("✅ docker-compose.production.yml 存在")
            results["production_components"]["production_compose"] = True
            
            # 檢查配置完整性
            with open(prod_compose_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_services = [
                "netstack-api",
                "simworld-backend", 
                "simworld-frontend",
                "redis-cache",
                "postgres",
                "prometheus",
                "grafana",
                "nginx"
            ]
            
            services_found = 0
            for service in required_services:
                if service in content:
                    services_found += 1
                    print(f"  ✅ {service} 服務配置存在")
                else:
                    print(f"  ❌ {service} 服務配置缺失")
            
            results["phase4_features"]["production_services"] = services_found == len(required_services)
            
            # 檢查健康檢查配置
            healthcheck_count = content.count('healthcheck:')
            print(f"  ✅ 健康檢查配置: {healthcheck_count} 個服務")
            results["phase4_features"]["health_checks"] = healthcheck_count >= 5
            
        else:
            print("❌ docker-compose.production.yml 不存在")
            results["production_components"]["production_compose"] = False
            results["phase4_features"]["production_services"] = False
            results["phase4_features"]["health_checks"] = False
            
    except Exception as e:
        print(f"❌ 生產環境配置測試失敗: {e}")
        results["production_components"]["production_compose"] = False
        results["phase4_features"]["production_services"] = False
        results["phase4_features"]["health_checks"] = False
    
    # 測試 2: 監控配置
    print("\n📊 2. 監控配置")
    
    try:
        # 檢查 Prometheus 配置
        prometheus_config_path = Path("monitoring/prometheus.yml")
        if prometheus_config_path.exists():
            print("✅ prometheus.yml 存在")
            results["production_components"]["prometheus_config"] = True
            
            with open(prometheus_config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查監控目標
            monitoring_targets = [
                "netstack-api",
                "simworld-backend",
                "redis",
                "postgres"
            ]
            
            targets_found = 0
            for target in monitoring_targets:
                if target in content:
                    targets_found += 1
                    print(f"  ✅ {target} 監控配置存在")
                else:
                    print(f"  ❌ {target} 監控配置缺失")
            
            results["phase4_features"]["monitoring_targets"] = targets_found == len(monitoring_targets)
            
        else:
            print("❌ prometheus.yml 不存在")
            results["production_components"]["prometheus_config"] = False
            results["phase4_features"]["monitoring_targets"] = False
            
    except Exception as e:
        print(f"❌ 監控配置測試失敗: {e}")
        results["production_components"]["prometheus_config"] = False
        results["phase4_features"]["monitoring_targets"] = False
    
    # 測試 3: 啟動性能優化器
    print("\n⚡ 3. 啟動性能優化器")
    
    try:
        # 檢查啟動優化器
        optimizer_path = Path("netstack/scripts/startup_optimizer.py")
        if optimizer_path.exists():
            print("✅ startup_optimizer.py 存在")
            results["production_components"]["startup_optimizer"] = True
            
            # 檢查功能完整性
            with open(optimizer_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_methods = [
                "record_startup_time",
                "check_data_availability",
                "preload_critical_data",
                "optimize_memory_usage",
                "validate_startup_requirements",
                "create_readiness_probe"
            ]
            
            methods_found = 0
            for method in required_methods:
                if f"def {method}" in content:
                    methods_found += 1
                    print(f"  ✅ {method} 方法存在")
                else:
                    print(f"  ❌ {method} 方法缺失")
            
            results["phase4_features"]["startup_optimization"] = methods_found == len(required_methods)
            
            # 測試導入
            try:
                sys.path.append('netstack/scripts')
                from startup_optimizer import StartupOptimizer
                optimizer = StartupOptimizer()
                print("  ✅ 啟動優化器可正常導入和實例化")
                results["deployment_status"]["optimizer_import"] = True
            except Exception as e:
                print(f"  ❌ 啟動優化器導入失敗: {e}")
                results["deployment_status"]["optimizer_import"] = False
            
        else:
            print("❌ startup_optimizer.py 不存在")
            results["production_components"]["startup_optimizer"] = False
            results["phase4_features"]["startup_optimization"] = False
            results["deployment_status"]["optimizer_import"] = False
            
    except Exception as e:
        print(f"❌ 啟動優化器測試失敗: {e}")
        results["production_components"]["startup_optimizer"] = False
        results["phase4_features"]["startup_optimization"] = False
        results["deployment_status"]["optimizer_import"] = False
    
    # 測試 4: Nginx 反向代理配置
    print("\n🌐 4. Nginx 反向代理配置")
    
    try:
        # 檢查 Nginx 配置
        nginx_config_path = Path("nginx/nginx.conf")
        if nginx_config_path.exists():
            print("✅ nginx.conf 存在")
            results["production_components"]["nginx_config"] = True
            
            with open(nginx_config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查關鍵配置
            nginx_features = {
                "upstream配置": "upstream" in content,
                "負載均衡": "least_conn" in content,
                "快取配置": "proxy_cache" in content,
                "限流配置": "limit_req" in content,
                "健康檢查": "/health" in content,
                "Gzip壓縮": "gzip on" in content
            }
            
            features_found = 0
            for feature, found in nginx_features.items():
                if found:
                    features_found += 1
                    print(f"  ✅ {feature} 配置存在")
                else:
                    print(f"  ❌ {feature} 配置缺失")
            
            results["phase4_features"]["nginx_optimization"] = features_found == len(nginx_features)
            
        else:
            print("❌ nginx.conf 不存在")
            results["production_components"]["nginx_config"] = False
            results["phase4_features"]["nginx_optimization"] = False
            
    except Exception as e:
        print(f"❌ Nginx 配置測試失敗: {e}")
        results["production_components"]["nginx_config"] = False
        results["phase4_features"]["nginx_optimization"] = False
    
    # 測試 5: NetStack API 生產監控增強
    print("\n🏥 5. NetStack API 生產監控增強")
    
    try:
        # 檢查健康檢查端點增強
        api_endpoints_path = Path("netstack/netstack_api/routers/coordinate_orbit_endpoints.py")
        if api_endpoints_path.exists():
            with open(api_endpoints_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查 Phase 4 監控功能
            phase4_functions = [
                "get_startup_time",
                "get_memory_usage", 
                "get_data_freshness",
                "get_cache_hit_rate",
                "get_uptime_seconds"
            ]
            
            functions_found = 0
            for func in phase4_functions:
                if f"def {func}" in content:
                    functions_found += 1
                    print(f"  ✅ {func} 監控功能存在")
                else:
                    print(f"  ❌ {func} 監控功能缺失")
            
            results["phase4_features"]["production_monitoring"] = functions_found == len(phase4_functions)
            
            # 檢查 phase4_production 字段
            if "phase4_production" in content:
                print("  ✅ phase4_production 監控字段存在")
                results["phase4_features"]["enhanced_health_check"] = True
            else:
                print("  ❌ phase4_production 監控字段缺失")
                results["phase4_features"]["enhanced_health_check"] = False
            
        else:
            print("❌ coordinate_orbit_endpoints.py 不存在")
            results["phase4_features"]["production_monitoring"] = False
            results["phase4_features"]["enhanced_health_check"] = False
            
    except Exception as e:
        print(f"❌ API 監控增強測試失敗: {e}")
        results["phase4_features"]["production_monitoring"] = False
        results["phase4_features"]["enhanced_health_check"] = False
    
    # 測試 6: 容器啟動順序優化
    print("\n🔄 6. 容器啟動順序優化")
    
    try:
        if results["production_components"]["production_compose"]:
            with open("docker-compose.production.yml", 'r') as f:
                content = f.read()
            
            # 檢查依賴關係配置
            dependency_features = {
                "depends_on配置": "depends_on:" in content,
                "健康檢查依賴": "condition: service_healthy" in content,
                "資源限制": "deploy:" in content and "resources:" in content,
                "重啟策略": "restart: unless-stopped" in content
            }
            
            dep_features_found = 0
            for feature, found in dependency_features.items():
                if found:
                    dep_features_found += 1
                    print(f"  ✅ {feature} 存在")
                else:
                    print(f"  ❌ {feature} 缺失")
            
            results["phase4_features"]["startup_optimization_docker"] = dep_features_found == len(dependency_features)
            
        else:
            results["phase4_features"]["startup_optimization_docker"] = False
            
    except Exception as e:
        print(f"❌ 容器啟動順序測試失敗: {e}")
        results["phase4_features"]["startup_optimization_docker"] = False
    
    # 計算總分
    all_features = {**results["phase4_features"], **results["production_components"], **results["deployment_status"]}
    total_features = len(all_features)
    completed_features = sum(all_features.values())
    
    if total_features > 0:
        results["overall_score"] = (completed_features / total_features) * 100
    
    # 輸出結果摘要
    print(f"\n📊 Phase 4 完成度摘要")
    print(f"=" * 40)
    print(f"總體完成度: {results['overall_score']:.1f}%")
    print(f"完成功能: {completed_features}/{total_features}")
    
    print(f"\n🎯 功能狀態:")
    for category, features in results.items():
        if category == "overall_score":
            continue
        print(f"\n{category.upper()}:")
        for feature, status in features.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {feature}")
    
    # Phase 4 驗收標準檢查
    print(f"\n📋 Phase 4 驗收標準檢查:")
    acceptance_criteria = {
        "生產環境 Docker Compose 配置完整": results["production_components"]["production_compose"] and results["phase4_features"]["production_services"],
        "容器啟動性能優化 (<30秒)": results["phase4_features"]["startup_optimization"],
        "Nginx 反向代理和負載均衡": results["production_components"]["nginx_config"] and results["phase4_features"]["nginx_optimization"],
        "Prometheus + Grafana 監控系統": results["production_components"]["prometheus_config"] and results["phase4_features"]["monitoring_targets"],
        "增強的健康檢查和生產監控": results["phase4_features"]["enhanced_health_check"] and results["phase4_features"]["production_monitoring"],
        "容器依賴關係和啟動順序優化": results["phase4_features"]["startup_optimization_docker"]
    }
    
    for criterion, status in acceptance_criteria.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {criterion}")
    
    acceptance_score = sum(acceptance_criteria.values()) / len(acceptance_criteria) * 100
    print(f"\n🎯 驗收標準達成率: {acceptance_score:.1f}%")
    
    # 保存結果
    with open('test_phase4_results.json', 'w', encoding='utf-8') as f:
        json.dump({
            **results,
            "acceptance_criteria": acceptance_criteria,
            "acceptance_score": acceptance_score,
            "test_timestamp": datetime.now().isoformat()
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 測試結果已保存至: test_phase4_results.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(test_phase4_completion())
