docker compose down --rmi all --volumes --remove-orphans

docker compose up > log.txt 2>&1

docker compose up -d --force-recreate backend

( 0, 0) 24°47'12"N 120°59'49"E 89m
( 100, 100) 24°47'09"N 120°59'52"E 92m

performance_test.sh
test_monitor_system.sh
test_ntn_simulator.sh
test_subscriber_management.sh
test_network_diagnostic.sh
test_open5gs_config.sh
test_system_integration.sh