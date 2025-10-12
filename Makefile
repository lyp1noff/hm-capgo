format:
	poetry run black . && poetry run isort .

lint:
	poetry run flake8 . && poetry run mypy .

test:
	poetry run pytest

dev:
	poetry install && poetry run alembic upgrade head && poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

docker-dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env up --build; docker compose down

# Combined
commit: format lint
