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

### **3. `generate_visualizations.py`**
- **Purpose**: Creates visualizations from datasets.
- **Inputs**:
  - `--input_folder`: Folder containing datasets.
  - `--output_folder`: Folder to save visualizations.
- **Outputs**: Saves charts in `visualizations/`.

### **4. `monitor_keywords.py`**
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
