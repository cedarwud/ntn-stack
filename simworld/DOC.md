docker compose down --rmi all --volumes --remove-orphans

docker compose up > log.txt 2>&1

docker compose up -d --force-recreate backend

更新座標為 24°56'38"N、121°22'15"E

- 後端配置文件：更新 config.py 中的 DEFAULT_OBSERVER_LAT/LON
- 座標服務：更新 coordinate_service.py 中的 ORIGIN_LATITUDE/LONGITUDE_GLB
- 精確轉換：24°56'38"N = 24.943889°, 121°22'15"E = 121.370833