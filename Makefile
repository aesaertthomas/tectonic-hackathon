.PHONY: setup test seed

setup:
	python3 -m venv backend/.venv
	backend/.venv/bin/pip install -q -r backend/requirements.txt

test:
	cd backend && .venv/bin/pytest

seed:
	cd backend && .venv/bin/python -m app.seed
