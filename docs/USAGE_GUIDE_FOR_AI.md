
# AI_USAGE_GUIDE

This document provides specific instructions for using the AI system, focusing on tasks and workflows related to code quality, security, and government data analysis.

## Toolchain System Overview

This system employs GitHub Actions workflows to streamline tasks related to code quality and security. This section details:

- **Code Quality Assurance**: The workflow ensures that all pushes and pull requests automatically validate the code before merging.
- **Security Scanning**: This is achieved using `bandit`. It identifies potential security risks in the code.
- **Code Formatting**: Using `black` ensures style consistency across the repository.
- **Test Coverage**: With `pytest-cov`, the system measures test coverage and validates functionality.

### Workflow Execution

1. Navigate to the **Actions** tab in the repository.
2. Select the workflow titled **Code Quality, Security Scan, and Coverage**.
3. Click **Run workflow** to execute it manually, or wait for it to trigger on new pushes or pull requests.

## Key Features

- **Dependabot Enabled**: Automatic updates to dependencies are managed to ensure the repository stays current and secure.
- **LSTM Model Enhancements**: Apply AI insights into tasks like preprocessing data, validating workflows, and analyzing codebase trends.
- **Federal Register API Integration**: Query documents, agencies, and other data dynamically.
- **Automated Data Validation**: Ensures JSON files adhere to required schema and field standards.
- **Visualization Generation**: Produces charts and summaries from datasets.
- **Keyword Monitoring**: Flags documents containing predefined terms.
- **CI/CD Workflows**: Automates data quality checks, visualization creation, and keyword alerts.

---

## Federal Register Data Integration

#### Supported Subcommands
The `fetch_fr.py` script interacts with Federal Register API endpoints. Available subcommands include:

- **`documents-search`**: Query published documents with filters like `--term`, `--pub_date_year`, and `--doc_type`.
- **`documents-single`**: Fetch a single document by number (`--doc_number`).
- **`public-inspection-search`**: Search public inspection documents (`--term`, `--per_page`).
- **`issues`**: Fetch an issue's table of contents (`--publication_date`).
- **`agencies`**: List all agencies.
- **`agency-single`**: Retrieve details of a single agency (`--slug`).

---

## How to Trigger Workflows

1. **Navigate to GitHub Actions**:
   - Go to the repository's **Actions** tab.
   - Select **Fetch Federal Register Data**.

2. **Input Parameters**:
   - Required: `subcommand` (e.g., `documents-search`, `agency-single`).
   - Optional: Parameters like `term`, `doc_number`, or `slug`.

3. **Run the Workflow**:
   - Click **Run workflow**. The data will be saved in the `data/` folder.

---

### Example Queries

#### Search Documents About Climate Policy
- **Workflow**: `documents-search`
- **Parameters**: 
  - `--term="climate policy"`
  - `--pub_date_year=2025`
- **Output**: `data/documents_search_term_climate_policy.json`

#### Fetch Public Inspection Documents
- **Workflow**: `public-inspection-search`
- **Parameters**:
  - `--term="solar energy"`
  - `--per_page=10`
- **Output**: `data/public_inspection_search_term_solar_energy.json`

---

## Dependencies

Ensure the following dependencies are installed:
- `requests`
- `argparse`

These tools support querying and automation for workflows.

---

### Workflows

#### 1. **Data Validation Workflow**
- **Purpose**: Validates JSON data for structure, completeness, and schema compliance.
- **Trigger**: Automatically runs when files are added or updated in the `data/` folder.
- **Script Used**: `validate_data.py`
- **Output**: Logs validation results and highlights errors.

#### 2. **Visualization Workflow**
- **Purpose**: Generates visual charts from datasets.
- **Trigger**: Runs on changes to the `datasets/` folder.
- **Script Used**: `generate_visualizations.py`
- **Output**: Saves visualizations to the `visualizations/` folder.

#### 3. **Keyword Monitoring Workflow**
- **Purpose**: Flags documents containing specific terms.
- **Trigger**: Runs on a scheduled basis (daily).
- **Script Used**: `monitor_keywords.py`
- **Output**: Saves flagged results to the `alerts/` folder.

---

## Scripts Overview

### `fetch_fr.py`
- **Purpose**: Fetches data from the Federal Register API.
- **Key Subcommands**:
  - `documents-search`: Searches documents based on terms, agencies, or dates.
  - `documents-single`: Fetches a specific document by its ID.
  - `agencies`: Lists all agencies.

### `validate_data.py`
- **Purpose**: Validates JSON data for structural integrity and required fields.
- **Usage**:
  ```bash
  python scripts/validate_data.py --folder data

---

This guide empowers AI and contributors to collaborate effectively, ensuring robust data analysis and seamless workflow execution.
