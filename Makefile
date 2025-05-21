# Variables
PYTHON = python3
VENV_DIR = .venv
VENV_PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip
REQUIREMENTS = requirements.txt
SAMPLE_DATA_DIR = sample_data
SAMPLE_OUTPUT_VALIDATION = validation_results.json
# Get the name of the first json file in SAMPLE_DATA_DIR to use as an example input for validate_data
# This assumes there will be at least one .json file in sample_data/ for the test.
# If not, this part might need adjustment or the test will fail (which is okay).
SAMPLE_INPUT_FILE = $(firstword $(wildcard $(SAMPLE_DATA_DIR)/*.json))


.PHONY: setup quickstart-test docs-check clean

# Target to set up the virtual environment and install dependencies
setup: $(VENV_DIR)/touchfile

$(VENV_DIR)/touchfile: $(REQUIREMENTS)
	@echo "Creating virtual environment in $(VENV_DIR)..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Installing dependencies from $(REQUIREMENTS)..."
	$(PIP) install -r $(REQUIREMENTS)
	@echo "Setup complete."
	touch $(VENV_DIR)/touchfile

# Target to run the quickstart test (validate_data.py on sample data)
# Depends on setup to ensure venv and dependencies are ready.
quickstart-test: setup
	@echo "Running quickstart test: validating sample data..."
	@if [ -z "$(SAMPLE_INPUT_FILE)" ]; then \
		echo "Error: No JSON files found in $(SAMPLE_DATA_DIR). Cannot run quickstart-test."; \
		echo "Please ensure sample_data/sample_document.json (or similar) exists."; \
		exit 1; \
	fi
	$(VENV_PYTHON) scripts/validate_data.py --input_folder $(SAMPLE_DATA_DIR) --output_file $(SAMPLE_OUTPUT_VALIDATION) --required_fields title publication_date agency
	@echo "Quickstart test complete. Results in $(SAMPLE_OUTPUT_VALIDATION)."
	@echo "To check results, you might want to inspect $(SAMPLE_OUTPUT_VALIDATION) and ensure no errors were reported for the sample data."

# Target for local documentation/onboarding check
docs-check: setup quickstart-test
	@echo "Docs check (setup and quickstart-test) completed."

# Target to clean up the virtual environment and temporary files
clean:
	@echo "Cleaning up..."
	rm -rf $(VENV_DIR)
	rm -f $(SAMPLE_OUTPUT_VALIDATION)
	@echo "Cleanup complete."
