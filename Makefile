run-dev:
	docker-compose --env-file=secrets/.env -f docker-compose.yaml -f docker-compose.override.yaml up

run-prod:
	docker-compose --env-file=secrets/.env -f docker-compose.yaml up

build:
	docker-compose --env-file=secrets/.env build --no-cache
