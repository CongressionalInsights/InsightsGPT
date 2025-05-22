.PHONY: setup run quickstart-test

# Default Python interpreter
PYTHON ?= python3

# Virtual environment directory
VENV_DIR ?= .venv

setup:
	@echo "Creating virtual environment in $(VENV_DIR)..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Activating virtual environment and installing dependencies..."
	@$(VENV_DIR)/bin/pip install -r requirements.txt
	@$(VENV_DIR)/bin/pip install -r requirements-dev.txt
	@echo "Installing pre-commit hooks..."
	@$(VENV_DIR)/bin/pre-commit install
	@echo "Setup complete. To activate the venv, run: source $(VENV_DIR)/bin/activate"

run:
	@echo "Running insightsgpt.cli..."
	@$(VENV_DIR)/bin/python -m insightsgpt.cli $(filter-out $@,$(MAKECMDGOALS))

quickstart-test:
	@echo "Running sample validation (scripts/validate_data.py)..."
	@mkdir -p logs
	@$(VENV_DIR)/bin/python scripts/validate_data.py --input_folder data/ --output_file logs/validation_results.json
	@echo "Sample validation complete. Results are in logs/validation_results.json"
