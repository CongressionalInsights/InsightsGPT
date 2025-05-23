[![Documentation Status](https://img.shields.io/website?url=https%3A%2F%2Fcongressionalinsights.github.io%2FInsightsGPT%2F&label=Docs&style=for-the-badge)](https://congressionalinsights.github.io/InsightsGPT/)
[![CI Build Status](https://img.shields.io/github/actions/workflow/status/CongressionalInsights/InsightsGPT/publish-package.yml?branch=main&label=CI&style=for-the-badge)](https://github.com/CongressionalInsights/InsightsGPT/actions/workflows/publish-package.yml)

# InsightsGPT

## Making Government Data Accessible and Actionable

**InsightsGPT** is an open-source project designed to provide transparent, easy-to-access insights into U.S. legislative, regulatory, and campaign finance activities. By leveraging the power of generative AI, InsightsGPT bridges the gap between complex datasets and the people who need them most. Whether you're a journalist, researcher, activist, or curious citizen, InsightsGPT empowers you to explore government data with ease.

---

## Prerequisites

-   Python 3.9 or higher.
-   `pip` (Python package installer) for installing dependencies.

---

## Quick Start

**InsightsGPT** provides a command-line interface (CLI) to access its features. This allows you to fetch data, validate it, monitor keywords, and generate visualizations.

1.  **Installation:**
    First, please ensure `insightsgpt` is installed. Refer to the [Installation](#installation) section below for detailed instructions (e.g., via Docker or building from source).

2.  **Basic Usage:**
    Once installed, you can use the `insightsgpt` command:
    ```sh
    insightsgpt --help  # See available commands
    insightsgpt --version # Check the installed version
    ```
    For example, to get help for the `fetch` subcommand:
    ```sh
    insightsgpt fetch --help
    ```

For more detailed command examples, see the [CLI Usage](#cli-usage) section. For advanced scenarios and understanding the data, consult our [Sample Workflows Guide](docs/Sample_Workflows.md) and the [Full Usage Guide](docs/USAGE_GUIDE_FOR_AI.md).

---

## Installation

### From Local Wheel (Development/Testing)
You can build and install `insightsgpt` from the source code:
1. Clone the repository:
   ```sh
   git clone https://github.com/CongressionalInsights/InsightsGPT.git
   cd InsightsGPT
   ```
2. Build the wheel:
   ```sh
   python -m build
   ```
3. Install the built wheel (the exact filename in `dist/` may vary depending on the version):
   ```sh
   # Example for version 1.1.0
   pip install dist/insightsgpt-1.1.0-py3-none-any.whl 
   ```

### Using Docker
A Docker image is available on GitHub Container Registry (GHCR).
1. Pull the latest image:
   ```sh
   docker pull ghcr.io/congressionalinsights/insightsgpt:latest
   ```
2. Run commands using the image. 
   - To see the help menu:
     ```sh
     docker run --rm ghcr.io/congressionalinsights/insightsgpt:latest --help
     ```
   - To run commands that require access to local data (e.g., for validation or visualization input), mount your local data directory into the container. For example, to validate data in a local `./my_data` directory:
     ```sh
     # Assuming your data is in ./my_data relative to your current path
     docker run --rm -v "$(pwd)/my_data":/app/data ghcr.io/congressionalinsights/insightsgpt:latest validate --input_folder /app/data
     ```
     Replace `$(pwd)/my_data` with the actual absolute path to your data directory. The scripts inside the Docker container expect input paths relative to `/app/` (e.g. `/app/data`, `/app/datasets`).

### From PyPI (Python Package Index)
*Future Goal:* We aim to publish `insightsgpt` to PyPI. Once available, you will be able to install it using:
```sh
pip install insightsgpt
```

---

## CLI Usage

Once installed, you can use the `insightsgpt` command:

```sh
insightsgpt --help
insightsgpt --version
```

**Subcommands:**

InsightsGPT uses subcommands to perform different actions. You can get help for any subcommand by running `insightsgpt <subcommand> --help`.

-   **Fetch data:**
    The `fetch` subcommand is used to retrieve data from various sources.
    ```sh
    insightsgpt fetch [options_for_fetch_script]
    # Example: insightsgpt fetch documents-search --term "artificial intelligence" --days 7
    ```
    Refer to `insightsgpt fetch --help` for specific options for the fetch script.

-   **Validate data:**
    The `validate` subcommand checks the integrity and format of your data files.
    ```sh
    insightsgpt validate --input_folder path/to/your/data
    # Example: insightsgpt validate --input_folder data/
    ```
    If using Docker, ensure the `path/to/your/data` is accessible inside the container (e.g., `/app/data` if volume mounted).
    Refer to `insightsgpt validate --help` for specific options.

-   **Monitor keywords:**
    The `keywords` subcommand monitors documents or data for specific keywords.
    ```sh
    insightsgpt keywords [options_for_keywords_script]
    # Example: insightsgpt keywords --keywords "climate,policy" --output_folder alerts/
    ```
    Refer to `insightsgpt keywords --help` for specific options.

-   **Generate visualizations:**
    The `visualize` subcommand creates charts and visual summaries from your datasets.
    ```sh
    insightsgpt visualize [options_for_visualize_script]
    # Example: insightsgpt visualize --input_folder datasets/ --output_folder visualizations/
    ```
    Refer to `insightsgpt visualize --help` for specific options.

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
- **Fetch Federal Register Data** via embedded Python script.

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

The core logic for the CLI subcommands is located in the `scripts/` directory. While you can still run these scripts directly (e.g., `python scripts/fetch_fr.py ...`), using the `insightsgpt` CLI tool is the recommended approach for most users as it provides a unified interface and handles pathing correctly.

#### 1. `validate_data.py`
- **Purpose**: Validates JSON data for structure and required fields.
- **CLI Usage**: `insightsgpt validate --input_folder data/ --output_file logs/validation_results.json`
- **Direct Script Usage (if needed)**: `python scripts/validate_data.py --input_folder data/ --output_file logs/validation_results.json`

  ---

### **Dependencies**

Project dependencies are managed via `pyproject.toml` and installed when you build the package or use the Docker image. For local development, you might still use `requirements.txt` or `requirements-dev.txt`:
The `requirements.txt` file includes the following tools to support the workflows and core functionality:

- `requests`
- `flake8`
- `pytest`
- `pytest-cov`
- `bandit`
- `black`

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

#### Version 1.1.0 (Current)
- **Packaging & Distribution**:
  - Introduced `pyproject.toml` for PEP 517/518 packaging.
  - `insightsgpt` is now installable as a Python package (wheel).
  - Added `insightsgpt` command-line tool with subcommands (`fetch`, `validate`, `keywords`, `visualize`).
  - Docker image published to `ghcr.io/congressionalinsights/insightsgpt`.
  - CI/CD enhancements for automated build, test, and publishing of the Python package and Docker image.
- **Documentation**:
  - Updated `README.md` with installation instructions for package and Docker, CLI usage, and status badges.
  - Updated `CHANGELOG.md` for v1.1.0.
  - Added MkDocs static site for dashboard/documentation, deployable to GitHub Pages.
- **Workflows**:
  - Configured workflows (`publish-package`, `publish-docs`, `code_quality`, `data-validation`, `test_and_lint`, `visualization`) to trigger on pull requests to `main`.
- **Code Structure**:
  - Moved CLI application code to `src/insightsgpt_cli/`.
  - Added `src/insightsgpt_cli/__init__.py` to ensure package recognition.
- **`.gitignore`**:
  - Standardized and enhanced `.gitignore` for common Python, build, and OS files.

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
