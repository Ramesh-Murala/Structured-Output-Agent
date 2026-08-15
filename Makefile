.PHONY: install dev test lint run docker

install:
	python -m pip install -r requirements.txt

dev:
	python -m pip install -r requirements-dev.txt

test:
	pytest -q

lint:
	ruff check .

run:
	uvicorn app.main:app --reload

docker:
	docker compose up --build
