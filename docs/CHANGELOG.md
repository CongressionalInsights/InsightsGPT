
# CHANGELOG

This document serves as a changelog, detailing recent updates, improvements, and new features implemented in the repository.

---

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
