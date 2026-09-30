.PHONY: setup test seed dev

setup:
	python3 -m venv backend/.venv
	backend/.venv/bin/pip install -q -r backend/requirements.txt
	cd frontend && npm install

test:
	cd backend && .venv/bin/pytest

seed:
	cd backend && .venv/bin/python -m app.seed

dev:
	@trap 'kill 0' EXIT; \
	(cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000) & \
	(cd frontend && npm run dev); \
	wait
