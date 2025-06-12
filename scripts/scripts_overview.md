# Scripts Overview

This document provides an overview of all scripts available in the repository, their purposes, inputs, and outputs.

---

## **Available Scripts**

### **1. `fetch_fr.py`**
- **Purpose**: A command-line interface (CLI) tool with multiple subcommands for interacting with various endpoints of the Federal Register API. It utilizes shared client utilities from `fr_client.py` for features like API key management, request sessions with caching/retries, and optional schema validation.
- **Global Options**:
    - `--api-key YOUR_API_KEY`: Federal Register API key (overrides `FEDREG_API_KEY` env var).
    - `--output-dir path/to/output`: Directory to save output files (defaults to value from `FEDREG_DATA_DIR` or `./data`).
    - `--verbose` or `-v`: Enable verbose (DEBUG level) logging.
    - `--no-cache`: Disable caching for synchronous requests.
- **Environment Variables**:
    - `FEDREG_API_KEY`: API key for the Federal Register.
    - `FEDREG_API_BASE`: Base URL for the API (e.g., `https://www.federalregister.gov/api/v1`).
    - `FEDREG_DATA_DIR`: Default directory for saving data.

#### **Subcommands for `fetch_fr.py`:**

**a. `documents`**
- **Purpose**: Fetches documents by a specific Docket ID. Supports advanced features like asynchronous fetching, pagination, caching for synchronous requests, and optional JSON schema validation.
- **Usage Example**:
  ```bash
  python scripts/fetch_fr.py documents \
    --docket-id YOUR_DOCKET_ID \
    [--output-dir ./my_data] \
    [--page-size 100] \
    [--fetch-all] \
    [--max-pages 5] \
    [--schema path/to/schema.json] \
    [--use-async] \
    [--dry-run]
  ```
- **Key Arguments/Options**:
    - `--docket-id DOCKET_ID`: (Required) The Docket ID to fetch documents for.
    - `--page-size PAGE_SIZE`: Number of documents per page (default: 100).
    - `--fetch-all`: Retrieve all pages for the docket.
    - `--max-pages MAX_PAGES`: Maximum pages to fetch if using `--fetch-all` (0 for no limit, default: 0).
    - `--schema SCHEMA`: Path to a JSON Schema file for response validation.
    - `--use-async`: Enable asynchronous fetching for this subcommand.
    - `--dry-run`: Show actions without making HTTP requests.

**b. `search`**
- **Purpose**: Searches documents based on keyword terms.
- **Usage Example**:
  ```bash
  python scripts/fetch_fr.py search --term "climate change" [--page-size 20] [--fetch-all]
  ```
- **Key Arguments/Options**:
    - `--term TERM`: (Required) Keyword search terms.
    - `--page-size PAGE_SIZE`: Number of results per page (default: 20).
    - `--fetch-all`: Retrieve all pages for the search.
    - `--max-pages MAX_PAGES`: Maximum search result pages to fetch (0 for no limit, default: 0).
    - `--schema SCHEMA`: Path to a JSON Schema file for response validation.
    - `--dry-run`: Show actions without making HTTP requests.

**c. `get-single`**
- **Purpose**: Retrieves a single document by its Federal Register document number.
- **Usage Example**:
  ```bash
  python scripts/fetch_fr.py get-single --doc-number 2023-12345
  ```
- **Key Arguments/Options**:
    - `--doc-number DOC_NUMBER`: (Required) Federal Register document number.
    - `--schema SCHEMA`: Path to a JSON Schema file for response validation.
    - `--dry-run`: Show actions without making HTTP requests.

**d. `issues`**
- **Purpose**: Lists regulatory issues from the Federal Register.
- **Usage Example**:
  ```bash
  python scripts/fetch_fr.py issues [--page-size 50]
  ```
- **Key Arguments/Options**:
    - `--page-size PAGE_SIZE`: Number of issues to fetch per page (default: 100).
    - `--schema SCHEMA`: Path to a JSON Schema file for response validation.
    - `--dry-run`: Show actions without making HTTP requests.
    *(Note: Date filtering options like `--date-is`, `--date-gte`, `--date-lte` are available as shown by `issues --help`)*

**e. `agencies`**
- **Purpose**: Lists federal agencies available in the Federal Register.
- **Usage Example**:
  ```bash
  python scripts/fetch_fr.py agencies [--page-size 50]
  ```
- **Key Arguments/Options**:
    - `--page-size PAGE_SIZE`: Number of agencies to fetch per page (default: 100).
    - `--schema SCHEMA`: Path to a JSON Schema file for response validation.
    - `--dry-run`: Show actions without making HTTP requests.

**f. `public-inspection`**
- **Purpose**: Retrieves documents currently on public inspection.
- **Usage Example**:
  ```bash
  python scripts/fetch_fr.py public-inspection [--date YYYY-MM-DD]
  ```
- **Key Arguments/Options**:
    - `--date DATE`: Filter by filing date (YYYY-MM-DD).
    - `--page-size PAGE_SIZE`: Number of documents to fetch (default: 100).
    - `--schema SCHEMA`: Path to a JSON Schema file for response validation.
    - `--dry-run`: Show actions without making HTTP requests.
    *(Note: Additional filters like `--agency-slugs` and `--doc-type` are available as shown by `public-inspection --help`)*

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

### **5. `bill_similarity.py`**

```bash
Usage: python bill_similarity.py \
  --bill1 path/to/first_bill.txt \
  --bill2 path/to/second_bill.txt \
  [--threshold 0.8] \
  [--segment_size 100] \
  [--overlap 20] \
  [--output results.json]

Arguments:
	•	--bill1 – Path to the first bill text file.
	•	--bill2 – Path to the second bill text file.
	•	--threshold – Similarity cutoff between 0 and 1 (default: 0.8).
	•	--segment_size – Number of words per segment (default: 100).
	•	--overlap – Overlap in words between segments (default: 20).
	•	--output – (Optional) JSON file to save the match results.
```

### **6. `Submit_Regulation_Comment.py`**
- **Purpose**: Submits a public comment to Regulations.gov for a specified docket.
- **Usage Example**:
  ```bash
  python scripts/Submit_Regulation_Comment.py \
    --docket-id DOCKET_ID \
    [--comment "Your comment text"] \
    [--comment-file path/to/comment.txt] \
    [--api-key YOUR_API_KEY] \
    [--dry-run] \
    [--output response.json]
  ```
- **Key Arguments/Options**:
    - `--docket-id`: (Required) The ID of the docket to comment on (e.g., `NOAA-NMFS-2024-0001`).
    - `--comment`: Text of the comment. (Mutually exclusive with `--comment-file`)
    - `--comment-file`: Path to a text file containing the comment. (Mutually exclusive with `--comment`)
    - `--api-key`: Regulations.gov API key. If not provided, the script attempts to use the `REGGOV_API_KEY` environment variable.
    - `--dry-run`: If included, the script will print the request details (endpoint, headers, payload) and exit without actually sending the comment.
    - `--output`: (Optional) Path to a JSON file where the API response will be saved. If not provided, the response is printed to the console.
- **Environment Variables**:
    - `REGGOV_API_KEY`: Can be used to provide the Regulations.gov API key.

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
