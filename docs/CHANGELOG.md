
# CHANGELOG

This document serves as a changelog, detailing recent updates, improvements, and new features implemented in the repository.

---

## [1.1.0] - 2024-07-24

### Added
- Python packaging support (`pyproject.toml`), allowing the project to be installed as a wheel.
- Command-Line Interface (CLI): `insightsgpt` tool with subcommands (`fetch`, `validate`, `keywords`, `visualize`) to run project scripts. Includes a `--version` flag.
- Docker Image: Published to `ghcr.io/congressionalinsights/insightsgpt` for easy, containerized execution of CLI commands.
- CI/CD Workflow for Publishing: Automated building and publishing of the Python package to GitHub Releases and the Docker image to GHCR when version tags (e.g., `v1.1.0`) are pushed.
- CI/CD Workflow for Documentation: Automated deployment of the MkDocs site to GitHub Pages (Static Dashboard).
- Enhanced CI Triggers: Workflows now run on Pull Requests to `main` to validate changes before merging.

### Changed
- Project structure: Migrated `insightsgpt_cli` to an `src/` layout for better packaging standards.
- `README.md`: Overhauled with comprehensive installation instructions (wheel, Docker), CLI usage examples, status badges, and de-emphasis on direct script execution.
- `.gitignore`: Updated to be more comprehensive, including patterns for build artifacts, cache files, coverage reports, virtual environments, and OS-specific files.

### Removed
- Deleted `patch.diff` (an accidentally committed file) from the repository.

## Recent Updates

## [1.0.4] - YYYY-MM-DD

- **Code Quality and Script Refinements**:
  - Consolidated Federal Register data fetching logic into the primary `scripts/fetch_fr.py` script, removing redundant scripts for better maintainability.
  - Refactored `scripts/fetch_fr.py` to remove redundant `pass` statements, improving code clarity.
  - Removed placeholder functions (`fetch_bill_details`, `collect_public_sentiment_data`) from `scripts/sentiment_analysis_tool.py` to streamline the script.
  - Enabled `flake8` linting for the entire `scripts/` directory by updating the `.flake8` configuration. All identified linting issues within the `scripts/` directory were subsequently fixed.
  - Updated `scripts/fetch_fr.py` to use Python's `logging` module for output and status messages, replacing previous `print()` calls.
  - Introduced a comprehensive suite of unit tests for `scripts/fetch_fr.py` using `pytest` and `unittest.mock`, enhancing test coverage and code reliability.

### Version 1.0.3

- **Performance Improvements**:
  - Removed latency in `fetch_fr.py` via caching mechanisms.
  - Updated `monitor_keywords.py` to accommodate multi-keyword searches.
  - Expanded visualization options, including geographic mapping.
  - Added Senate Lobbying Disclosure API support with `data_connections/ldasenategov_openapi.yaml`

### Version 1.0.2

- **Fetch Federal Register Integration**:
  - Refactored `scripts/fetch_fr.py` for better data fetching from the Federal Register API.
  - Added manual capability to trigger workflows.
  - Adjusted the requirements with new workflow integrations.

### Version 1.0.1

- Added workflows for testing, linting, and deployment:
  - Testing and linting workflows ensure code quality.
  - Deployment workflows streamline updates to scripts.
