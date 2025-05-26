# Scripts Overview

This document provides an overview of all scripts available in the repository, their purposes, inputs, and outputs.

---

## **Available Scripts**

### **1. `fetch_fr.py`**
- **Purpose**: Fetch data from the Federal Register API.
- **Inputs**:
  - `--subcommand`: API endpoint (e.g., `documents-search`).
  - Additional parameters: `--term`, `--doc_number`, etc.
- **Outputs**: Saves JSON files to `data/`.

### **2. `validate_data.py`**
- **Purpose**: Validates JSON files for structure and required fields.
- **Inputs**:
  - `--folder`: Folder containing JSON files to validate.
  - `--schema` (optional): JSON schema file for validation.
- **Outputs**: Logs validation results to the console.

### **3. `fetch_congress.py`**
- **Purpose**: Fetches data from the [Congress.gov API](https://api.congress.gov/) for U.S. Congressional bills and members.
- **Environment Variables**:
  - `CONGRESS_API_KEY`: **Required**. Your API key for the Congress.gov API. The script will exit if this is not set.
- **Subcommands**:
  - `bill`: Fetches details for a specific bill.
    - Arguments:
      - `--congress` (int, required): The Congress number (e.g., 117, 118).
      - `--bill-type` (str, required): The type of bill (e.g., `hr`, `s`, `hres`, `sres`, `hjres`, `sjres`, `hconres`, `sconres`).
      - `--bill-number` (int, required): The number of the bill.
    - Example Usage:
      ```bash
      python scripts/fetch_congress.py bill --congress 117 --bill-type hr --bill-number 1
      ```
  - `member`: Fetches details for a specific member of Congress.
    - Arguments:
      - `--bioguide-id` (str, required): The Biographical Directory ID of the member (e.g., `B001288`).
    - Example Usage:
      ```bash
      python scripts/fetch_congress.py member --bioguide-id B001288
      ```
- **Outputs**:
  - Saves JSON files to the `data/congress/` directory.
  - Filenames are structured based on the subcommand and input parameters (e.g., `data/congress/bill_117_hr_1.json`, `data/congress/member_B001288.json`).
- **Logging**:
  - Logs API requests, successful saves, and errors to standard output.

### **4. `generate_visualizations.py`**
- **Purpose**: Creates visualizations from datasets.
- **Inputs**:
  - `--input_folder`: Folder containing datasets.
  - `--output_folder`: Folder to save visualizations.
- **Outputs**: Saves charts in `visualizations/`.

### **5. `monitor_keywords.py`**
- **Purpose**: Flags documents containing specified keywords.
- **Inputs**:
  - `--keywords`: JSON file with keywords.
  - `--input_folder`: Folder containing JSON files to search.
  - `--output_folder`: Folder to save flagged results.
- **Outputs**: Saves flagged results to `alerts/`.

---

## **Workflows**

### **1. Data Validation Workflow**
- **Purpose**: Ensures data integrity in `data/`.
- **Trigger**: Runs on new commits to `data/`.
- **Script Used**: `validate_data.py`

### **2. Visualization Workflow**
- **Purpose**: Generates visual summaries from datasets.
- **Trigger**: Runs on new commits to `datasets/`.
- **Script Used**: `generate_visualizations.py`

### **3. Keyword Monitoring Workflow**
- **Purpose**: Flags documents with specific keywords.
- **Trigger**: Runs daily.
- **Script Used**: `monitor_keywords.py`
