
# CHANGELOG

This document serves as a changelog, detailing recent updates, improvements, and new features implemented in the repository.

---

## Recent Updates

### Version 1.0.3

- **Performance Improvements**:
  - Removed latency in `fetch_fr.py` via caching mechanisms.
  - Updated `monitor_keywords.py` to accommodate multi-keyword searches.
  - Expanded visualization options, including geographic mapping.
  - Added Senate Lobbying Disclosure API support with  `data_connections/ldasenategov_openapi.yaml`

### Version 1.0.2

- **Fetch Federal Register Integration**:
  - Refactored `scripts/fetch_fr.py` for better data fetching from the Federal Register API.
  - Added manual capability to trigger workflows.
  - Adjusted the requirements with new workflow integrations.

### Version 1.0.1

- Added workflows for testing, linting, and deployment:
  - Testing and linting workflows ensure code quality.
  - Deployment workflows streamline updates to scripts.
