# Scripts Overview

This document provides an overview of all scripts available in the repository, their purposes, inputs, and outputs.

---

## **Available Scripts**

### **1. `fetch_fr.py`**
- **Purpose**: A command-line interface (CLI) tool to fetch data from the Federal Register API (api.federalregister.gov/v1/). It supports various subcommands for different API endpoints and utilizes shared client utilities from `fr_client.py` for API communication, including retry logic, optional caching for synchronous requests, and schema validation.
- **Global Options**:
    - `--api-key YOUR_API_KEY`: Specifies the API key for authentication. Can also be set via the `FEDREG_API_KEY` environment variable.
    - `--output-dir path/to/dir`: Sets the directory for saving output files. Defaults to the value of `FEDREG_DATA_DIR` environment variable or `./data` if not set.
    - `--verbose`: Enables INFO level logging for the script.
    - `--debug`: Enables DEBUG level logging for the script and underlying libraries like `requests` and `httpx`.
- **Environment Variables**:
    - `FEDREG_API_KEY`: API key for the Federal Register.
    - `FEDREG_API_BASE`: Base URL for the API (defaults to `https://www.federalregister.gov/api/v1`).
    - `FEDREG_DATA_DIR`: Default directory for saving data (defaults to `./data`).

#### **Subcommands for `fetch_fr.py`:**

**a. `documents`**
- **Purpose**: Fetches documents by a specific Docket ID. Supports pagination, asynchronous fetching, and schema validation for the responses.
- **Usage Example**:
  ```bash
  python scripts/fetch_fr.py documents \
    --docket-id DOCKET_ID \
    [--api-key YOUR_API_KEY] \
    [--output-dir ./data] \
    [--page-size 250] \
    [--fetch-all] \
    [--max-pages 0] \
    [--schema path/to/schema.json] \
    [--use-async] \
    [--dry-run]
  ```
- **Key Arguments/Options**:
    - `--docket-id DOCKET_ID`: (Required) The Docket ID to fetch documents for (e.g., `USTR-2023-0001`).
    - `--page-size NUM`: Number of documents per page (default: 250).
    - `--fetch-all`: If set, retrieves all available pages of results.
    - `--max-pages NUM`: Maximum number of pages to fetch when `--fetch-all` is active (0 means no limit).
    - `--schema FILE_PATH`: Path to a JSON schema file to validate individual page responses against.
    - `--use-async`: Enables asynchronous fetching for potentially faster downloads (experimental).
    - `--dry-run`: Simulates the fetching process and prints parameters without making actual API calls.

**b. `search`** (Replaces original `documents-search`)
- **Purpose**: Searches documents on the Federal Register using various filter criteria.
- **Usage Example**:
  ```bash
  python scripts/fetch_fr.py search \
    --term "climate change" \
    --per-page 50 \
    --agency-slugs environmental-protection-agency \
    [--order newest] \
    [--output-dir ./search_results]
  ```
- **Key Arguments/Options**:
    - `--term "SEARCH_TERM"`: (Required) The term(s) to search for.
    - `--per-page NUM`: Number of results per page (default: 20).
    - `--page NUM`: Page number to retrieve (default: 1).
    - `--order {relevance|newest|oldest}`: Sort order of results.
    - `--pub-date-year YYYY`: Filter by publication year.
    - `--pub-date-gte YYYY-MM-DD`: Filter for publication date greater than or equal to.
    - `--pub-date-lte YYYY-MM-DD`: Filter for publication date less than or equal to.
    - `--pub-date-is YYYY-MM-DD`: Filter for a specific publication date.
    - `--agency-slugs SLUG [SLUG ...]`: Filter by one or more agency slugs.
    - `--doc-type TYPE [TYPE ...]`: Filter by one or more document types (e.g., `RULE`, `NOTICE`).
    - `--topics TOPIC [TOPIC ...]`: Filter by topics.
    - `--sections SECTION [SECTION ...]`: Filter by sections.
    - `--presidential-document-type TYPE [TYPE ...]`: Filter by presidential document type.
    - `--presidential-document-subtype SUBTYPE [SUBTYPE ...]`: Filter by presidential document subtype.
    - `--schema FILE_PATH`: Path to JSON schema for validating the response.
    - `--dry-run`: Simulate fetching.

**c. `get-single`** (Replaces original `documents-single`)
- **Purpose**: Fetches a single document by its unique document number.
- **Usage Example**:
  ```bash
  python scripts/fetch_fr.py get-single --doc-number 2023-12345
  ```
- **Key Arguments/Options**:
    - `--doc-number DOC_NUM`: (Required) The document number (e.g., `2023-12345`).
    - `--schema FILE_PATH`: Path to JSON schema for validating the response.
    - `--dry-run`: Simulate fetching.

**d. `issues`**
- **Purpose**: Lists Federal Register issues, filterable by date or date range.
- **Usage Example**:
  ```bash
  python scripts/fetch_fr.py issues --date-is 2023-10-26
  ```
- **Key Arguments/Options**:
    - `--date-is YYYY-MM-DD`: List issues for a specific date.
    - `--date-gte YYYY-MM-DD`: List issues on or after this date.
    - `--date-lte YYYY-MM-DD`: List issues on or before this date.
    - `--schema FILE_PATH`: Path to JSON schema for validating the response.
    - `--dry-run`: Simulate fetching.

**e. `agencies`**
- **Purpose**: Lists all agencies that publish in the Federal Register.
- **Usage Example**:
  ```bash
  python scripts/fetch_fr.py agencies
  ```
- **Key Arguments/Options**:
    - `--schema FILE_PATH`: Path to JSON schema for validating the response.
    - `--dry-run`: Simulate fetching.

**f. `public-inspection`** (Replaces original `public-inspection-documents`)
- **Purpose**: Fetches documents available for public inspection, filterable by date and other criteria.
- **Usage Example**:
  ```bash
  python scripts/fetch_fr.py public-inspection --date-is 2023-10-26
  ```
- **Key Arguments/Options**:
    - `--date-is YYYY-MM-DD`: Filter by specific filing date.
    - `--date-gte YYYY-MM-DD`: Filter by filing date greater than or equal to.
    - `--date-lte YYYY-MM-DD`: Filter by filing date less than or equal to.
    - `--agency-slugs SLUG [SLUG ...]`: Filter by one or more agency slugs.
    - `--doc-type TYPE [TYPE ...]`: Filter by one or more document types.
    - `--schema FILE_PATH`: Path to JSON schema for validating the response.
    - `--dry-run`: Simulate fetching.

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
