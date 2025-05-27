.PHONY: up down down-v clean build

up: build
	docker compose up -d

down:
	docker compose down
	docker network prune -f

down-v:
	docker compose down -v
	docker volume prune -f
	docker network prune -f

clean:
	docker compose down --rmi all --volumes --remove-orphans
	docker volume prune -f
	docker network prune -f

build:
	docker compose build

no-cache:
	docker compose build --no-cache

re-b:
	docker compose restart backend
