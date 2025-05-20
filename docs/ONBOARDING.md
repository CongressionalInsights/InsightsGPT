
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
Ensure you have Python installed, then run:
```bash
pip install -r requirements.txt
```

### Step 3: Set Up Environment Variables
For certain workflows, you may need API keys. Add them to a `.env` file in the root directory:
```plaintext
FEDERAL_REGISTER_API_KEY=your_api_key_here
CONGRESS_API_KEY=your_api_key_here
```

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
