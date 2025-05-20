# Contributing to InsightsGPT

Thank you for considering contributing to Congressional Insights GPT! We welcome contributions of all kinds, from bug reports to new feature implementations. Here's how you can get involved:

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/CongressionalInsights/InsightsGPT.git
cd InsightsGPT
```

### 2. Install Dependencies
Ensure you have Python installed. For a full development setup, including all tools for testing, linting, and formatting, use the following command:

```bash
pip install -r requirements-dev.txt
```
This command installs all runtime dependencies (from `requirements.txt`, which is included by `requirements-dev.txt`) as well as development-specific tools. If you only need to set up a runtime environment (e.g., for deployment, not development), you can use `pip install -r requirements.txt`.

### 3. Understand the Project

- **Key Components:**
  - **Data Sources:** Integrates with Congress.gov, FEC, and Regulations.gov API.
  - **AI Capabilities:** Uses GPT models for advanced data analysis and accessibility.
  - **Key Features:** Provides civic tech insights through open-source tools.

### 4. Test Your Environment
Ensure your basic Python environment is working. Specific scripts for connection testing may be added later if needed.

## Contribution Guidelines

### Reporting Bugs

If you encounter a bug, please help us by reporting it:

1.  **Search Existing Issues:** Before submitting a new issue, please check the [Issues page](https://github.com/CongressionalInsights/InsightsGPT/issues) to see if the bug has already been reported.
2.  **Open a New Issue:** If you're unable to find an open issue addressing the problem, open a new one.
3.  **Provide Detailed Information:** Be sure to include:
    *   A clear and descriptive title.
    *   A detailed description of the issue.
    *   Steps to reproduce the bug.
    *   What you expected to happen versus what actually happened.
    *   A code sample or an executable test case demonstrating the expected behavior that is not occurring, if possible.
    *   Details about your environment (e.g., Python version, Operating System, version of the library if applicable).

### Coding Style

To maintain consistency across the project, please adhere to the following coding styles:

-   **Python:** Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines.
-   **Docstrings:** Use [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for all modules, classes, and functions. Example:
    ```python
    def example_function(param1, param2):
        """Example function with Google-style docstring.

        Args:
            param1 (int): The first parameter.
            param2 (str): The second parameter.

        Returns:
            bool: True if successful, False otherwise.
        """
        # ... function body ...
        return True
    ```
-   **Comments:** Write clear and concise comments to explain complex logic or non-obvious parts of your code.
-   **Formatting:** Consider using an automated code formatter like Black, which is included in `requirements.txt`. You can run `black .` from the project root.

### Running Tests

This project uses `pytest` for testing. To run the test suite:

1.  **Install Test Dependencies:** Ensure all development dependencies are installed by running `pip install -r requirements-dev.txt`. This includes `pytest` and other necessary tools.
2.  **Run Tests:** Execute the following command from the project root:
    ```bash
    python -m pytest tests/
    ```
    Alternatively, you can often just run:
    ```bash
    pytest tests/
    ```
3.  **Ensure All Tests Pass:** Before submitting changes, make sure all tests pass successfully.

### Proposing Changes (Pull Requests)

We welcome contributions in the form of Pull Requests (PRs). Here’s the general workflow:

1.  **Fork the Repository:** Create your own fork of the [InsightsGPT repository](https://github.com/CongressionalInsights/InsightsGPT) on GitHub.
2.  **Create a New Branch:** From your fork, create a new branch for your feature or bug fix. Use a descriptive name, for example:
    ```bash
    git checkout -b feature/NewApiIntegration
    # or for a bug fix
    git checkout -b fix/Issue123-FixDataParsing
    ```
3.  **Make Your Changes:** Implement your feature or fix the bug.
4.  **Commit Your Changes:** Commit your changes with clear, descriptive commit messages. Follow conventional commit message formats if possible (e.g., `feat: Add new data source for X`, `fix: Correct parsing error in Y`).
    ```bash
    git add .
    git commit -m "feat: Implement user authentication feature"
    ```
5.  **Ensure Code Quality:**
    *   **Linting:** Run `flake8 .` from the project root to check for linting errors and fix them.
    *   **Formatting:** Run `black .` to format your code.
    *   **Tests:** Ensure all tests pass by running `pytest tests/`.
6.  **Push to Your Fork:** Push your changes to your branch on your forked repository:
    ```bash
    git push origin feature/NewApiIntegration
    ```
7.  **Open a Pull Request:** Go to the original InsightsGPT repository and open a new Pull Request from your branch to the `main` branch of the InsightsGPT repository.
8.  **Describe Your PR:**
    *   Provide a clear title and a detailed description of the changes you've made.
    *   If your PR addresses an existing issue, link to it in the description (e.g., "Closes #123").
    *   Explain the reasoning behind your changes and any relevant context.

Once your PR is submitted, project maintainers will review it. You may be asked to make further changes before it can be merged. Thank you for your contribution!
