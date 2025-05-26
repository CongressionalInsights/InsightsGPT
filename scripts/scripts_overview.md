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
  - `member`: Fetches member data based on various optional filters. At least one filter argument must be provided.
    - Arguments:
      - `--bioguide-id` (str, optional): Filter by Biographical Directory ID of the member (e.g., `B001288`).
      - `--congress` (int, optional): Filter by Congress number (e.g., 117).
      - `--state-code` (str, optional): Filter by state code (e.g., `CA`, `TX`).
      - `--district` (int, optional): Filter by congressional district number.
      - `--sponsorship` (flag, optional): Include member's bill sponsorship information.
      - `--cosponsorship` (flag, optional): Include member's bill cosponsorship information.
    - Example Usage:
      ```bash
      python scripts/fetch_congress.py member --bioguide-id B001288
      python scripts/fetch_congress.py member --congress 117 --state-code CA --sponsorship
      python scripts/fetch_congress.py member --state-code NY
      ```
  - `bills`: Fetches a list of bills based on specified filters. At least one filter argument is required.
    - Arguments:
      - `--congress` (int, optional): Filter by Congress number (e.g., 117).
      - `--bill-type` (str, optional): Filter by type of bill (e.g., `hr`, `s`).
      - `--introduced-date` (str, optional): Filter by introduced date (YYYY-MM-DD).
    - Example Usage:
      ```bash
      python scripts/fetch_congress.py bills --congress 117 --bill-type s
      ```
  - `committee`: Fetches committee data based on specified filters. At least one filter argument is required.
    - Arguments:
      - `--chamber` (str, optional): Filter by chamber (e.g., `house`, `senate`).
      - `--congress` (int, optional): Filter by Congress number (e.g., 117).
      - `--committee-code` (str, optional): Filter by committee code (e.g., `HSAP`, `SSAF`).
    - Example Usage:
      ```bash
      python scripts/fetch_congress.py committee --chamber house --congress 117 --committee-code HSAP
      ```
  - `amendment`: Fetches a list of amendments based on specified filters. Can be called without filters to fetch all amendments, though this may result in a large dataset.
    - Arguments:
      - `--congress` (int, optional): Filter by Congress number (e.g., 117).
      - `--amendment-type` (str, optional): Filter by amendment type (e.g., `hamdt`, `samdt`).
    - Example Usage:
      ```bash
      python scripts/fetch_congress.py amendment --congress 117 --amendment-type samdt
      python scripts/fetch_congress.py amendment # Fetches all amendments
      ```
  - `committee-report`: Fetches a list of committee reports. Can be filtered by Congress. Calling without filters may result in a large dataset.
    - Arguments:
      - `--congress` (int, optional): Filter by Congress number (e.g., 117).
    - Example Usage:
      ```bash
      python scripts/fetch_congress.py committee-report --congress 117
      python scripts/fetch_congress.py committee-report # Fetches all committee reports
      ```
  - `treaty`: Fetches a list of treaties. Can be filtered by Congress. Calling without filters may result in a large dataset.
    - Arguments:
      - `--congress` (int, optional): Filter by Congress number (e.g., 116).
    - Example Usage:
      ```bash
      python scripts/fetch_congress.py treaty --congress 116
      python scripts/fetch_congress.py treaty # Fetches all treaties
      ```
  - `nomination`: Fetches a list of nominations for a specific Congress.
    - Arguments:
      - `--congress` (int, **required**): Specify the Congress number (e.g., 117).
    - Example Usage:
      ```bash
      python scripts/fetch_congress.py nomination --congress 117
      ```
  - `congressional-record`: Fetches Congressional Record data. Can be filtered by Congress and/or date. Calling without filters may result in a large dataset.
    - Arguments:
      - `--congress` (int, optional): Filter by Congress number (e.g., 117).
      - `--date` (str, optional): Filter by date (YYYY-MM-DD).
    - Example Usage:
      ```bash
      python scripts/fetch_congress.py congressional-record --congress 117 --date 2023-01-15
      python scripts/fetch_congress.py congressional-record --congress 117
      python scripts/fetch_congress.py congressional-record # Fetches all records
      ```
  - `senate-communication`: Fetches Senate Communication data. Can be filtered by Congress, communication type (Executive Communication 'ec' or Presidential Message 'pm'), and/or date range. Calling without filters may result in a large dataset.
    - Arguments:
      - `--congress` (int, optional): Filter by Congress number (e.g., 117).
      - `--type` (str, optional, choices: `ec`, `pm`): Filter by communication type.
      - `--from-date` (str, optional): Filter by start date (YYYY-MM-DD).
      - `--to-date` (str, optional): Filter by end date (YYYY-MM-DD).
    - Example Usage:
      ```bash
      python scripts/fetch_congress.py senate-communication --congress 117 --type ec --from-date 2023-01-01 --to-date 2023-01-31
      python scripts/fetch_congress.py senate-communication --congress 117 --type pm
      python scripts/fetch_congress.py senate-communication # Fetches all senate communications
      ```
- **Outputs**:
  - Saves JSON files to the `data/congress/` directory.
  - Filenames are structured based on the subcommand and input parameters (e.g., `data/congress/bill_117_hr_1.json`, `data/congress/member_data_bioguide_id_B001288.json`, `data/congress/member_data_congress_117_state_code_CA_sponsorship_true.json`, `data/congress/bills_list_congress_117_bill_type_s.json`, `data/congress/committee_data_chamber_house_congress_117_committee_code_HSAP.json`, `data/congress/amendment_data_congress_117_amendment_type_samdt.json`, `data/congress/amendment_data_all.json`, `data/congress/committee_report_data_congress_117.json`, `data/congress/committee_report_data_all.json`, `data/congress/treaty_data_congress_116.json`, `data/congress/treaty_data_all.json`, `data/congress/nomination_data_117.json`, `data/congress/congressional_record_data_congress_117_date_2023-01-15.json`, `data/congress/congressional_record_data_all.json`, `data/congress/senate_communication_data_congress_117_type_ec.json`, `data/congress/senate_communication_data_all.json`).
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

### **7. `fetch_regulations.py`**
- **Purpose**: Fetches data from the [Regulations.gov API](https://www.regulations.gov/developers).
- **Environment Variables**:
  - `REGULATIONS_API_KEY`: **Required**. Your API key for the Regulations.gov API. The script will exit if this is not set.
- **Subcommands**:
  - `documents`: Fetches a list of documents, with optional filters.
    - Arguments:
      - `--search-term` (str, optional): Search for documents containing this term.
      - `--docket-id` (str, optional): Filter documents by a specific docket ID.
      - `--title-filter` (str, optional): Filter documents by words in the title.
      - `--page-size` (int, optional, default: 25): Number of results per page (1-100).
      - `--page-number` (int, optional, default: 1): Page number to retrieve.
    - Example Usage:
      ```bash
      python scripts/fetch_regulations.py documents --search-term "environmental justice" --page-size 10
      ```
  - `document`: Fetches a specific document by its ID, optionally including attachments.
    - Arguments:
      - `--document-id` (str, **required**): The ID of the document (e.g., `EPA-HQ-OAR-2021-0295-0001`).
      - `--include-attachments` (flag, optional): Include attachment details in the response.
    - Example Usage:
      ```bash
      python scripts/fetch_regulations.py document --document-id EPA-HQ-OAR-2021-0295-0001 --include-attachments
      ```
  - `dockets`: Fetches a list of dockets, with optional filters.
    - Arguments:
      - `--search-term` (str, optional): Search for dockets containing this term.
      - `--page-size` (int, optional, default: 25): Number of results per page (1-250).
      - `--page-number` (int, optional, default: 1): Page number to retrieve.
    - Example Usage:
      ```bash
      python scripts/fetch_regulations.py dockets --search-term "renewable energy"
      ```
  - `docket`: Fetches a specific docket by its ID.
    - Arguments:
      - `--docket-id` (str, **required**): The ID of the docket (e.g., `EPA-HQ-OAR-2021-0295`).
    - Example Usage:
      ```bash
      python scripts/fetch_regulations.py docket --docket-id EPA-HQ-OAR-2021-0295
      ```
  - `comments`: Fetches a list of comments, with optional filters.
    - Arguments:
      - `--search-term` (str, optional): Search for comments containing this term.
      - `--page-size` (int, optional, default: 10): Number of results per page (1-100).
      - `--page-after` (str, optional): Cursor for the next page of results.
    - Example Usage:
      ```bash
      python scripts/fetch_regulations.py comments --search-term "public health" --page-size 15
      ```
  - `comment`: Fetches a specific comment by its ID, optionally including attachments.
    - Arguments:
      - `--comment-id` (str, **required**): The ID of the comment (e.g., `EPA-HQ-OAR-2021-0295-0002`).
      - `--include-attachments` (flag, optional): Include attachment details in the response.
    - Example Usage:
      ```bash
      python scripts/fetch_regulations.py comment --comment-id EPA-HQ-OAR-2021-0295-0002
      ```
- **Outputs**:
  - Saves JSON files to the `data/regulations/` directory.
  - List results are saved in subdirectories named after the entity type (e.g., `data/regulations/documents/documents_list_searchTerm_xyz.json`).
  - Specific item details are saved in a subdirectory named after the item's ID (e.g., `data/regulations/documents/EPA-XYZ-123/document_details_documentId_EPA-XYZ-123.json`, `data/regulations/dockets/ABC-123/docket_details_docket_id_ABC-123.json`, `data/regulations/comments/DEF-456/comment_details_commentId_DEF-456.json`).
- **Logging**:
  - Logs API requests, successful saves, and errors to standard output.

---

### **6. `fetch_govinfo.py`**
- **Purpose**: Fetches data from the [GovInfo.gov API](https://api.govinfo.gov/).
- **Environment Variables**:
  - `GOVINFO_API_KEY`: **Required**. Your API key for the GovInfo.gov API. The script will exit if this is not set.
- **Subcommands**:
  - `collections`: Fetches the list of all available GovInfo collections.
    - Arguments: None.
    - Example Usage:
      ```bash
      python scripts/fetch_govinfo.py collections
      ```
  - `packages`: Fetches a list of packages, with optional filters.
    - Arguments:
      - `--collection` (str, optional): Filter by collection code(s), comma-separated for multiple (e.g., `BILLS`, `FR`).
      - `--start-date` (str, optional): Filter by start date for `dateIssued` (YYYY-MM-DD).
      - `--end-date` (str, optional): Filter by end date for `dateIssued` (YYYY-MM-DD).
      - `--modified-since` (str, optional): Filter by modified date (ISO8601 format, e.g., `2023-01-01T00:00:00Z`).
      - `--page-size` (int, optional, default: 100): Number of results per page.
      - `--offset-mark` (str, optional, default: `*`): Offset mark for pagination.
    - Example Usage:
      ```bash
      python scripts/fetch_govinfo.py packages --collection FR --start-date 2023-01-01 --end-date 2023-01-05
      ```
  - `package-summary`: Fetches the summary for a specific package.
    - Arguments:
      - `--package-id` (str, **required**): The ID of the package (e.g., `FR-2023-01-03-0001`).
    - Example Usage:
      ```bash
      python scripts/fetch_govinfo.py package-summary --package-id FR-2023-01-03-0001
      ```
- **Outputs**:
  - Saves JSON files to the `data/govinfo/` directory.
  - `collections` data is saved as `data/govinfo/collections_list.json`.
  - `packages` data is saved under `data/govinfo/packages/` with filenames reflecting the filters (e.g., `data/govinfo/packages/packages_list_collection_FR_start_date_2023-01-01.json`).
  - `package-summary` data is saved in a subdirectory named after the package ID under `data/govinfo/summaries/` (e.g., `data/govinfo/summaries/FR-2023-01-03-0001/package_summary_FR_2023_01_03_0001.json`).
- **Logging**:
  - Logs API requests, successful saves, and errors to standard output.

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
