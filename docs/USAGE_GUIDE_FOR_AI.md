
# AI Usage Guide

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
  python scripts/validate_data.py --input_folder data/ --output_file logs/validation_results.json
  ```

---

## How-to Guide for Senate Lobbying Disclosure Act (LDA) Data

Below is a structured guide to **understand** and **work** with the Senate LDA REST API. By following these steps, Congressional Insights GPT (or any LLM-based agent) can reliably query the API.

1. **Include the Final OpenAPI YAML**  
   - Make sure your plugin or agent references the `openapi.yaml` v1.0.3 file.  
   - For ChatGPT Plugins: In the `ai-plugin.json`, point to the OpenAPI doc under `"api": { "url": "<path_to_openapi.yaml>" }`.  
   - Confirm the plugin manifest sets `"auth": { "type": "none" }` (if you handle the Authorization header separately) **or** a custom scheme.

2. **Supply an Authorization Header**  
   - LLM calls **must** include `Authorization: Token eed953f7e2b4f53834f6a804215226660aaef55c` (or your valid key).  
   - For ChatGPT plugins specifically, you can inject the header in your plugin’s server code or specify in the OpenAPI `securitySchemes`.

3. **Respect Filings & Contributions Pagination**  
   - If the LLM tries to retrieve `page=2` or beyond for `/filings/` or `/contributions/`, it **must** supply a query parameter (e.g., `filing_year=2024`). Otherwise, a 400 error occurs.  

4. **Rate Limits**  
   - Maximum 120 requests/min for authenticated keys, 15/min for anonymous.  
   - If a 429 occurs, your LLM can parse the `Retry-After` header to wait before retrying.

5. **Suggested Usage Patterns**  
   - **Search Filings**: Provide `filing_year`, plus `registrant_id` or other filters.  
   - **View Single Filing**: Grab the `filing_uuid` from search results to retrieve `/filings/{filing_uuid}/`.  
   - **List Registrants**: Filter by `registrant_name` or just page through to find potential matches.  
   - **Constants**: For validated or enumerated fields (e.g., government entities, states, countries, etc.), call the relevant `/constants/` endpoints.

6. **Example LLM Query**  
   - “Find the 2024 Filings for ‘CTIA’”  
     - The LLM would:  
       1. Call `/filings/?filing_year=2024&client_name=CTIA&page_size=5` (if `client_name` were a valid filter—some advanced filters might differ).  
       2. Retrieve `filing_uuid` from results.  
       3. Possibly call `/filings/{filing_uuid}/` for more detail.  

7. **Potential Errors**  
   - **401** “Invalid token” if the key is missing or incorrect.  
   - **429** “Too Many Requests” if you exceed rate limits.

- This House-to-Guide ensures LLM-based tools can properly navigate the LDA Senate API by referencing the `openapi.yaml` (v1.0.3) specification, applying the required authentication, and respecting pagination rules.
- Keep your API key secret—**never** commit it in public repos or logs.  

---

This guide empowers AI and contributors to collaborate effectively, ensuring robust data analysis and seamless workflow execution.
