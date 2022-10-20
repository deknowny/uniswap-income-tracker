run-dev:
	docker-compose --env-file=secrets/.env -f docker-compose.yaml -f docker-compose.override.yaml up

run-prod:
	docker-compose --env-file=secrets/.env -f docker-compose.yaml up -d

build:
	docker-compose --env-file=secrets/.env build --no-cache

format-bot:
	black bot/src
