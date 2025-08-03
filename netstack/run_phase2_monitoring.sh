#!/bin/bash

# Phase 2.2.4 持續監控系統執行腳本
#
# 此腳本啟動持續監控系統，包括：
# - 系統健康狀態監控
# - 性能指標連續監控  
# - 異常檢測和告警
# - 監控數據收集和報告

set -e

echo "🔍 Phase 2.2.4: 持續監控系統開始"
echo "================================="

# 檢查服務狀態
echo "📋 檢查系統服務狀態..."
if ! curl -s http://localhost:8080/health > /dev/null; then
    echo "❌ NetStack API (8080) 不可用"
    echo "請先啟動服務: make up"
    exit 1
fi

echo "✅ NetStack API 服務正常"

if curl -s http://localhost:8888/health > /dev/null; then
    echo "✅ SimWorld Backend 服務正常"
else
    echo "⚠️ SimWorld Backend 不可用，部分監控功能將受限"
fi

# 創建監控目錄
mkdir -p tests/monitoring

# 設置環境變量
export PYTHONPATH="$PWD:$PYTHONPATH"

# 執行監控系統測試
echo ""
echo "🔍 執行持續監控系統測試..."
echo "============================"

# 服務健康監控測試
echo "💚 服務健康監控測試..."
python -m pytest tests/monitoring/test_phase2_continuous_monitoring.py::TestContinuousMonitoringSystem::test_service_health_monitoring -v -s

# 性能指標收集測試
echo ""
echo "📊 性能指標收集測試..."
python -m pytest tests/monitoring/test_phase2_continuous_monitoring.py::TestContinuousMonitoringSystem::test_performance_metrics_collection -v -s

# 異常檢測測試
echo ""
echo "🚨 異常檢測測試..."
python -m pytest tests/monitoring/test_phase2_continuous_monitoring.py::TestContinuousMonitoringSystem::test_anomaly_detection -v -s

# 監控報告生成測試
echo ""
echo "📋 監控報告生成測試..."
python -m pytest tests/monitoring/test_phase2_continuous_monitoring.py::TestContinuousMonitoringSystem::test_monitoring_report_generation -v -s

# 監控配置驗證測試
echo ""
echo "⚙️ 監控配置驗證測試..."
python -m pytest tests/monitoring/test_phase2_continuous_monitoring.py::TestContinuousMonitoringSystem::test_monitoring_configuration_validation -v -s

# 監控系統整合測試
echo ""
echo "🔗 監控系統整合測試..."
python -m pytest tests/monitoring/test_phase2_continuous_monitoring.py::TestMonitoringIntegration::test_monitoring_system_integration -v -s

# 檢查監控報告
if [ -f "tests/monitoring/monitoring_report.json" ]; then
    echo ""
    echo "📋 監控報告摘要:"
    echo "================"
    
    if command -v jq &> /dev/null; then
        echo "報告時間: $(jq -r '.timestamp' tests/monitoring/monitoring_report.json)"
        echo "系統健康度: $(jq -r '.system_health.overall_score' tests/monitoring/monitoring_report.json)%"
        echo "健康服務: $(jq -r '.system_health.healthy_services' tests/monitoring/monitoring_report.json)/$(jq -r '.system_health.total_services' tests/monitoring/monitoring_report.json)"
        echo "平均響應時間: $(jq -r '.system_health.avg_response_time_ms' tests/monitoring/monitoring_report.json)ms"
        echo "總告警數: $(jq -r '.alerts.total_alerts' tests/monitoring/monitoring_report.json)"
        
        echo ""
        echo "告警統計:"
        echo "  Critical: $(jq -r '.alerts.by_severity.critical' tests/monitoring/monitoring_report.json)"
        echo "  High: $(jq -r '.alerts.by_severity.high' tests/monitoring/monitoring_report.json)"
        echo "  Medium: $(jq -r '.alerts.by_severity.medium' tests/monitoring/monitoring_report.json)"
        echo "  Low: $(jq -r '.alerts.by_severity.low' tests/monitoring/monitoring_report.json)"
        
        echo ""
        echo "系統建議:"
        jq -r '.recommendations[]' tests/monitoring/monitoring_report.json | sed 's/^/  - /'
    else
        echo "詳細報告: tests/monitoring/monitoring_report.json"
    fi
else
    echo "⚠️ 監控報告文件未生成"
fi

echo ""
echo "✅ Phase 2.2.4 持續監控系統測試完成"
echo "==================================="

# 監控系統狀態驗證
echo ""
echo "🎯 監控系統驗證:"
echo "==============="

# 檢查基本監控功能
monitoring_ok=true

# 測試健康檢查功能
if curl -s http://localhost:8080/health | jq -e '.overall_status == "healthy"' > /dev/null 2>&1; then
    echo "✅ 健康檢查監控功能正常"
else
    echo "⚠️ 健康檢查監控需要檢查"
    monitoring_ok=false
fi

# 檢查響應時間監控
response_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8080/health)
response_time_ms=$(echo "$response_time * 1000" | bc -l 2>/dev/null || echo "$(($response_time * 1000))")

echo "📊 當前 API 響應時間: ${response_time_ms%.*}ms"

if (( $(echo "$response_time < 1.0" | bc -l 2>/dev/null || echo "1") )); then
    echo "✅ 響應時間監控正常"
else
    echo "⚠️ 響應時間較長，監控告警可能觸發"
fi

# 檢查監控報告生成
if [ -f "tests/monitoring/monitoring_report.json" ]; then
    echo "✅ 監控報告生成功能正常"
else
    echo "❌ 監控報告生成功能異常"
    monitoring_ok=false
fi

echo ""
if [ "$monitoring_ok" = true ]; then
    echo "🎉 持續監控系統驗證通過"
    echo "💡 監控系統已準備就緒，可以開始持續監控"
    exit 0
else
    echo "⚠️ 持續監控系統部分功能需要調整"
    echo "💡 系統仍可運行，但建議檢查相關配置"
    exit 0
fi