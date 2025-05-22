setup:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt

quickstart-test:
	. .venv/bin/activate && python scripts/validate_data.py --folder data && pytest
