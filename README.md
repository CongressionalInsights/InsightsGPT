
# InsightsGPT

### Making Government Data Accessible and Actionable

**InsightsGPT** is an open-source project designed to provide transparent, easy-to-access insights into U.S. legislative, regulatory, and campaign finance activities. By leveraging the power of generative AI, InsightsGPT bridges the gap between complex datasets and the people who need them most. Whether you're a journalist, researcher, activist, or curious citizen, InsightsGPT empowers you to explore government data with ease.

---

## **Key Features**

### **GitHub Actions Workflow**

InsightsGPT employs a robust GitHub Actions workflow to maintain high code quality and security. The workflow includes:
- **Linting** with `flake8`.
- **Security Scanning** with `bandit`.
- **Code Formatting** with `black`.
- **Test Coverage** with `pytest-cov`.

The workflow is triggered automatically on code pushes and pull requests to the `main` branch, ensuring every change is thoroughly validated.

### **Dependencies**

The `requirements.txt` file includes the following tools to support the workflow:
- `requests`
- `flake8`
- `pytest`
- `pytest-cov`
- `bandit`
- `black`

### **Dependabot Enabled**

Dependabot is enabled for this repository, ensuring that all dependencies are automatically kept up-to-date to minimize vulnerabilities.

---

## **How to Run the Workflow**

1. Navigate to the **Actions** tab in the GitHub repository.
2. Select the workflow titled "Code Quality, Security Scan, and Coverage."
3. Click **Run workflow** to execute the workflow manually.
