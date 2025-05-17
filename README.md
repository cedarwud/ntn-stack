docker compose down --rmi all --volumes --remove-orphans

( 0, 0) 24°47'12"N 120°59'49"E 89m
( 100, 100) 24°47'09"N 120°59'52"E 92m

curl -X GET "http://localhost:8000/api/v1/satellite-ops/ground_stations/NYCU_gnb/visible_satellites?min_elevation_deg=5.0&top_n=1000" -H "accept: application/json"


分階段實作:
先完成 TLE 的自動獲取、儲存 (Redis + DB) 和 Skyfield 的可見性計算模組。確保這部分準確可靠。
接著，手動配置一個 UERANSIM gNB 和 UE，並讓它們與 Open5GS 通訊，熟悉其設定和運作。
然後，開始嘗試將 Skyfield 計算出的衛星位置資訊，用於動態配置一個 UERANSIM gNB (代表衛星)。
最後，整合 UE (無人機) 的動態位置，並思考如何模擬衛星 gNB 之間的 handover。