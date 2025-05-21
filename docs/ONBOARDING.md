
# Onboarding Tool

This document helps new contributors quickly set up and navigate the repository.

---

## Getting Started

### Step 1: Clone the Repository
Run the following command to clone the repository to your local machine:
```bash
git clone https://github.com/CongressionalInsights/InsightsGPT.git
cd InsightsGPT
```

### Step 2: Install Dependencies
Ensure you have Python installed. For a full development setup, including all tools for testing, linting, and development tasks, run:
```bash
pip install -r requirements-dev.txt
```
This installs all runtime dependencies (from `requirements.txt`) plus additional development tools.

### Step 3: Environment Setup and API Keys

Many scripts and automated workflows within this project interact with external APIs to fetch data or perform actions (e.g., submitting comments). To enable these functionalities, you'll need to set up your local environment with the necessary API keys.

**Using `.env` for Environment Variables:**

This project uses a `.env` file to manage API keys and other sensitive configuration details. This file is kept local to your development environment and is not committed to the repository (it's listed in `.gitignore`).

1.  **Create your `.env` file:**
    In the root directory of the project, you'll find an example file named `.env.example`. Copy this file to create your own `.env` file:
    ```bash
    cp .env.example .env
    ```

2.  **Edit your `.env` file:**
    Open the newly created `.env` file with your preferred text editor (e.g., `nano .env`, `vim .env`, or using a graphical editor). You will need to replace the placeholder values with your actual API keys.

**API Key Information:**

The `.env.example` file lists several API keys. Here's how to obtain them and their purpose:

*   **`FEDERAL_REGISTER_API_KEY=""`**
    *   **Purpose:** Used for accessing data from the Federal Register. While much of the API is public, an API key might grant higher rate limits or access to specific features if you register for one.
    *   **Obtain:** Visit [https://www.federalregister.gov/developers/api/v1] for API documentation. Key registration details, if available, would be found there. For now, it can often be left blank for basic access.

*   **`REGULATIONS_API_KEY=""`**
    *   **Purpose:** Required for interacting with the Regulations.gov API, which is essential for tasks like fetching specific dockets or submitting comments (e.g., by `scripts/Submit_Regulation_Comment.py`).
    *   **Obtain:** Request an API key from [https://regulations.gov/developers].

*   **`CONGRESS_API_KEY=""`**
    *   **Purpose:** Used for fetching legislative data from Congress.gov, including bill statuses, summaries, and member information.
    *   **Obtain:** Register for an API key at [https://api.congress.gov/].

*   **`SENATE_LDA_API_KEY=""`**
    *   **Purpose:** For accessing Senate Legislative Data (LDA) services. This API provides detailed information about Senate legislative activities.
    *   **Obtain:** Access to the Senate LDA API typically requires specific registration or adherence to Senate IT policies. Consult official Senate resources or relevant IT contacts for information on obtaining an API key. A direct public link for key requests is not commonly available.

**Important:**
*   Ensure your `.env` file is correctly populated with your keys before running scripts that depend on them.
*   Scripts like `scripts/Submit_Regulation_Comment.py` rely on `python-dotenv` to load these variables. If a required key (e.g., `REGULATIONS_API_KEY`) is missing or empty in your `.env` file, the script may not function correctly.

---

## Workflows Overview

### Common Workflows
1. **Fetch Federal Register Data**:
   - Automates queries and stores results in the `data/` folder.
   - Trigger via GitHub Actions or run locally.

2. **Validate Data**:
   - Ensures all JSON files are schema-compliant.

3. **Keyword Monitoring**:
   - Flags documents containing predefined terms.

### Running Locally
Scripts can be tested locally for quicker iteration. Example:
```bash
python scripts/validate_data.py --input_folder data/ --output_file logs/validation_results.json
```

---

## Need Help?

If you have any questions, please reach out to the maintainers through issue reviews or open a discussion:
- **Repository Discussions**: [GitHub Discussions](https://github.com/CongressionalInsights/InsightsGPT/discussions)

---

## Contribution Guidelines
1. Create a new branch for each feature or bug fix:
   ```bash
   git checkout -b feature/new-feature
   ```
2. Submit a pull request with a clear description of your changes.

Thank you for contributing to **InsightsGPT**!
