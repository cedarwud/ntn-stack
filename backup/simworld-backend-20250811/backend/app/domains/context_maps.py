"""
領域上下文映射 (Context Maps)

定義各個領域間的關係和邊界。此文件作為領域間的協作指南，
幫助開發者理解各領域的職責範圍和相互依賴關係。
"""

CONTEXT_MAPS = {
    # 衛星領域：負責衛星軌道計算、位置追蹤等
    "satellite": {
        "depends_on": ["coordinates"],  # 依賴坐標轉換領域
        "used_by": ["simulation"],  # 被模擬領域使用
        "shared_models": ["SatelliteOrbit", "SatelliteTLE"],  # 與其他領域共享的模型
    },
    # 模擬領域：負責無線通信模擬
    "simulation": {
        "depends_on": [
            "satellite",
            "device",
            "coordinates",
        ],  # 依賴衛星、設備和坐標領域
        "used_by": [],  # 無被依賴關係
        "shared_models": ["PropagationModel", "ChannelModel"],  # 與其他領域共享的模型
    },
    # 設備領域：負責設備管理
    "device": {
        "depends_on": ["coordinates"],  # 依賴坐標轉換領域
        "used_by": ["simulation"],  # 被模擬領域使用
        "shared_models": ["Device", "DeviceLocation"],  # 與其他領域共享的模型
    },
    # 坐標轉換領域：負責各類座標系轉換
    "coordinates": {
        "depends_on": [],  # 無依賴關係
        "used_by": ["satellite", "device", "simulation"],  # 被衛星、設備和模擬領域使用
        "shared_models": [
            "GeoCoordinate",
            "CartesianCoordinate",
        ],  # 與其他領域共享的模型
    },
}

# 定義共享內核 (Shared Kernel)
# 這些模型/概念被多個領域共享，需特別注意保持一致性
SHARED_KERNEL = [
    "GeoCoordinate",  # 地理座標
    "TimeReference",  # 時間參考
    "DeviceIdentifier",  # 設備識別符
]

# 定義上下文邊界 (Bounded Context)
# 描述每個領域的責任範圍
BOUNDED_CONTEXTS = {
    "satellite": "負責衛星軌道計算、位置預測和TLE數據處理",
    "simulation": "負責無線通信仿真、信道模型和傳播模型",
    "device": "負責設備管理、狀態追蹤和配置",
    "coordinates": "負責不同座標系統間的轉換與計算",
}
