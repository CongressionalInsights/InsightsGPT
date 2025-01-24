# InsightsGPT

## Making Government Data Accessible and Actionable

**InsightsGPT** is an open-source project designed to provide transparent, easy-to-access insights into U.S. legislative, regulatory, and campaign finance activities. By leveraging the power of generative AI, InsightsGPT bridges the gap between complex datasets and the people who need them most. Whether you're a journalist, researcher, activist, or curious citizen, InsightsGPT empowers you to explore government data with ease.

---

## **Key Features**

### **GitHub Actions Workflows**

InsightsGPT employs robust GitHub Actions workflows to maintain high code quality, data accessibility, and security. The workflows include:

- **Linting** with `flake8`.
- **Security Scanning** with `bandit`.
- **Code Formatting** with `black`.
- **Test Coverage** with `pytest-cov`.
- **Fetch Federal Register Data Fetching** via embedded Python script.

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
  python scripts/validate_data.py --folder data

  ---

### **Dependencies**

The `requirements.txt` file includes the following tools to support the workflows:

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
