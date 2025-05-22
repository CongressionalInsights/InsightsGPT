# InsightsGPT

[![Build/CI](https://img.shields.io/badge/Build/CI-passing-brightgreen?style=flat-square)](https://github.com/CongressionalInsights/InsightsGPT/actions)
[![Documentation](https://img.shields.io/badge/Docs-available-blue?style=flat-square)](https://congressionalinsights.github.io/InsightsGPT/) 
[![Coverage](https://img.shields.io/badge/Coverage-100%25-green?style=flat-square)](https://coveralls.io/github/CongressionalInsights/InsightsGPT)
[![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)](LICENSE)

## Making Government Data Accessible and Actionable

**InsightsGPT** is an open-source project designed to provide transparent, easy-to-access insights into U.S. legislative, regulatory, and campaign finance activities. By leveraging the power of generative AI, InsightsGPT bridges the gap between complex datasets and the people who need them most. Whether you're a journalist, researcher, activist, or curious citizen, InsightsGPT empowers you to explore government data with ease.

---

## Prerequisites

-   Python 3.9 or higher.
-   `pip` (Python package installer) for installing dependencies.

---

## Quick Start

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/CongressionalInsights/InsightsGPT.git
    cd InsightsGPT
    ```
2.  **Set up the development environment and install dependencies:**
    This command will create a virtual environment, install all necessary dependencies, and set up pre-commit hooks.
    ```bash
    make setup
    ```
    After setup, activate the virtual environment:
    ```bash
    source .venv/bin/activate 
    ```
    *(On Windows, use `.venv\Scripts\activate`)*

3.  **Run the application:**
    To run the command-line interface (once `insightsgpt.cli` is executable via the `pyproject.toml` script definition):
    ```bash
    make run -- --help 
    ```
    Or, to run a specific script directly (example):
    Fetch recent Federal Register documents related to "climate change":
    ```bash
    .venv/bin/python scripts/fetch_fr.py documents-search --term "climate change" --per_page 5 --order newest
    ```

    **Example Output (stdout):**
    ```
    INFO: GET https://www.federalregister.gov/api/v1/documents.json?per_page=5&order=newest&conditions%5Bterm%5D=climate+change
    INFO: Saved JSON to data/documents_search_term_climate_change_per_page_5_order_newest.json
    ```
    (A new file `data/documents_search_term_climate_change_per_page_5_order_newest.json` will be created containing the search results).

4.  **Run a sample data validation test:**
    After generating some data (e.g., by running the `fetch_fr.py` script example above), you can validate the contents of the `data/` directory:
    ```bash
    make quickstart-test
    ```
    This will run `scripts/validate_data.py` and save the validation report to `logs/validation_results.json`.

For more detailed examples and advanced usage, please see our [Sample Workflows Guide](docs/Sample_Workflows.md) and the [Full Usage Guide](docs/USAGE_GUIDE_FOR_AI.md).

---

## Configuration

For local development, API keys (if required by specific scripts in the future) and other configurable parameters can be managed using a `.env` file in the project root.

1.  **Create your `.env` file:**
    Copy the example file to `.env`:
    ```bash
    cp .env.example .env
    ```
2.  **Edit `.env`:**
    Open the `.env` file and add any necessary environment variables. For example:
    ```env
    # FEDERAL_REGISTER_API_KEY=your_actual_api_key_if_needed
    # OTHER_CONFIG_PARAM=some_value
    ```
    Currently, `scripts/fetch_fr.py` does not require an API key for the Federal Register API it uses. However, `python-dotenv` has been integrated to support environment-specific configurations easily if needed in the future.

**Important:** The `.env` file should **not** be committed to version control and is listed in `.gitignore`. Ensure you keep any sensitive information like API keys in your local `.env` file only.

---

## **Key Features**

### **GitHub Actions Workflows**

InsightsGPT employs robust GitHub Actions workflows to maintain high code quality, data accessibility, and security. The workflows include:

- **Linting** with `flake8`.
- **Security Scanning** with `bandit`.
- **Code Formatting** with `black`.
- **Test Coverage** with `pytest-cov`.
- **Fetch Federal Register Data** using the `scripts/fetch_fr.py` script.

---

### **Data Validation Workflow**
- **Purpose**: Ensures the integrity of JSON files in the `data/`.
- **Trigger**: Runs on new commits to `data/`.
- **Script Used**: `validate_data.py`
- **Output**: Logs validation results and flags issues.

### **Visualization Workflow**
- **Purpose**: Automatically generates charts and visual summaries from datasets.
- **Trigger**: Runs on new commits to `datasets/`.
- **Script Used**: `generate_visualizations.py`
- **Output**: Saves visualizations to `visualizations/`.

### **Keyword Monitoring Workflow**
- **Purpose**: Flags documents containing specific keywords.
- **Trigger**: Runs daily (schedule: midnight UTC).
- **Script Used**: `monitor_keywords.py`
- **Output**: Saves flagged results to `alerts/`.

The workflows are triggered automatically on code pushes, pull requests, and now also manually via `workflow_dispatch` events, ensuring every change is thoroughly validated.

---

### **Scripts**

#### 1. `validate_data.py`
- **Purpose**: Validates JSON data for structure and required fields.
- **Usage**:
  ```bash
  python scripts/validate_data.py --input_folder data/ --output_file logs/validation_results.json
  ```

  ---

### **Dependencies**

The project's dependencies are managed in two files:
- `requirements.txt`: Contains runtime dependencies necessary for the core functionality of the application (e.g., `requests`, `python-dotenv`).
- `requirements-dev.txt`: Includes development tools for linting, testing, and formatting (e.g., `flake8`, `pytest`, `black`).

The `make setup` command installs dependencies from both files.

---

### **Fetch Federal Register Workflow**

#### Overview

The **"Fetch Federal Register Data"** workflow fetches data from the Federal Register API using an embedded Python script. This workflow dynamically queries Federal Register endpoints (e.g., documents, agencies, public inspection).

#### How to Run the Workflow

1. Navigate to the **Actions** tab in the GitHub repository.
2. Select the workflow titled **"Fetch Federal Register Data"**.
3. Click **Run workflow** to execute the workflow manually via `workflow_dispatch`.

#### Embedded Logic

The embedded Python script fetches data using pre-configured parameters:

- **Search Term**: `education`
- **Publication Date**: From `2023-01-01` onwards.
- **Result Fields**: `title`, `document_number`, `url`, `publication_date`

#### Output

- Results are saved as JSON files in the `data/` folder.
- Example file name: `federal_register_education.json`

---

### **How to Run the Code Quality Workflow**

1. Navigate to the **Actions** tab in the GitHub repository.
2. Select the workflow titled **"Code Quality, Security Scan, and Coverage"**.
3. Click **Run workflow** to execute the workflow manually.

---

### **ChangeLog**

#### Version 1.0.2

- Replaced `fetch_fr.py` logic with embedded Python script in the Federal Register workflow.
- Enabled `workflow_dispatch` for manual workflow triggering.
- Updated README to reflect new workflows and triggers.

#### Version 1.0.1

- Added GitHub Actions workflows for code quality, data fetching, and automation.
- Unified `fetch_fr.py` script to handle all Federal Register endpoints.
- Enhanced README with workflow instructions and examples.
- Implemented Dependabot for automatic dependency updates.

---

### **Repository Structure**

- **`scripts/`**: Contains Python scripts for interacting with government APIs, including `validate_data.py` and `monitor_keywords.py`.
- **`docs/`**: Reference files, guides, and structured metadata to help users and contributors.
- **`.github/workflows/`**: Workflow files for testing, deploying, and data fetching.

This repository combines automation, generative AI, and open-source collaboration to make U.S. government data accessible and actionable for everyone.
