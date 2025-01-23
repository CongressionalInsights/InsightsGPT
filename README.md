# InsightsGPT

### Making Government Data Accessible and Actionable

**InsightsGPT** is an open-source project designed to provide transparent, easy-to-access insights into U.S. legislative, regulatory, and campaign finance activities. By leveraging the power of generative AI, InsightsGPT bridges the gap between complex datasets and the people who need them most. Whether you're a journalist, researcher, activist, or curious citizen, InsightsGPT empowers you to explore government data with ease.

---

## **Key Features**

### **GitHub Actions Workflow**

InsightsGPT employs robust GitHub Actions workflows to maintain high code quality, data accessibility, and security. The workflows include:
- **Linting** with `flake8`.
- **Security Scanning** with `bandit`.
- **Code Formatting** with `black`.
- **Test Coverage** with `pytest-cov`.
- **Federal Register Data Fetching** via custom scripts.

The workflows are triggered automatically on code pushes and pull requests to the `main` branch, ensuring every change is thoroughly validated.

### **Dependencies**

The `requirements.txt` file includes the following tools to support the workflows:
- `requests`
- `flake8`
- `pytest`
- `pytest-cov`
- `bandit`
- `black`

### **Dependabot Enabled**

Dependabot is enabled for this repository, ensuring that all dependencies are automatically kept up-to-date to minimize vulnerabilities.

---

## **Federal Register Workflow**

### Overview
The **"Fetch Federal Register Data"** workflow fetches data from the Federal Register API using the `fetch_fr.py` script. This workflow supports dynamic querying of all major Federal Register endpoints (e.g., documents, agencies, public inspection).

### How to Run the Workflow

1. Navigate to the **Actions** tab in the GitHub repository.
2. Select the workflow titled **"Fetch Federal Register Data"**.
3. Provide the necessary inputs:
   - `subcommand`: The desired action (e.g., `documents-search`, `agency-single`, `issues`).
   - Additional parameters as required by the subcommand.
4. Click **Run workflow** to execute the workflow manually.

### Supported Subcommands

| Subcommand                 | Description                                | Parameters                                                                 |
|----------------------------|--------------------------------------------|---------------------------------------------------------------------------|
| `documents-search`         | Search published FR documents             | `--term`, `--per_page`, `--pub_date_year`, `--agency_slug`, `--doc_type`  |
| `documents-single`         | Fetch a single document by number         | `--doc_number`                                                           |
| `public-inspection-search` | Search public inspection documents         | `--term`, `--per_page`                                                   |
| `public-inspection-current`| Fetch all currently available inspection docs | None                                                                 |
| `agencies`                 | List all agencies                         | None                                                                     |
| `agency-single`            | Fetch a single agency by slug             | `--slug`                                                                 |
| `issues`                   | Fetch a Federal Register issue's table of contents | `--publication_date` (YYYY-MM-DD)                                 |
| `suggested-searches`       | List all suggested searches               | Optional: `--section`                                                   |
| `suggested-search`         | Fetch a single suggested search by slug   | `--slug`                                                                 |

### Output

- All results are saved as JSON files in the `data/` folder.
- Filenames include the subcommand and parameters (e.g., `documents_search_term_climate.json`).

---

## **How to Run the Code Quality Workflow**

1. Navigate to the **Actions** tab in the GitHub repository.
2. Select the workflow titled **"Code Quality, Security Scan, and Coverage"**.
3. Click **Run workflow** to execute the workflow manually.

---

## **Changelog**

### Version 1.0.1
- Added GitHub Actions workflows for code quality, data fetching, and automation.
- Unified `fetch_fr.py` script to handle all Federal Register endpoints.
- Enhanced README with workflow instructions and examples.
- Implemented Dependabot for automated dependency updates.

---

## **Repository Structure**

- **`scripts/`**: Contains Python scripts for interacting with government APIs, including `fetch_fr.py` for Federal Register data.
- **`docs/`**: Reference files, guides, and structured metadata to help users and contributors.
- **`.github/workflows/`**: Workflow files for testing, deploying, and data fetching.

This repository combines automation, generative AI, and open-source collaboration to make U.S. government data accessible and actionable for everyone.
