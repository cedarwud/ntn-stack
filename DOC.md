docker compose down --rmi all --volumes --remove-orphans

( 0, 0) 24°47'12"N 120°59'49"E 89m
( 100, 100) 24°47'09"N 120°59'52"E 92m

curl -X GET "http://localhost:8000/api/v1/satellite-ops/ground_stations/NYCU_gnb/visible_satellites?min_elevation_deg=5.0&top_n=1000" -H "accept: application/json"