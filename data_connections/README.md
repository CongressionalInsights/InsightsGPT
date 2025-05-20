# Data Connections

This directory primarily houses API specification files and related examples that provide context for the data sources used by or potentially usable with the InsightsGPT project.

## OpenAPI Specifications (`*.yaml` files)

The following YAML files are OpenAPI (Swagger) specifications, offering detailed descriptions of various U.S. government APIs:

-   `GovInfo_openapi.yaml`
-   `congressgov_openapi.yaml`
-   `federalregistergov_openapi.yaml`
-   `github_openapi.yaml` (Note: For GitHub API, potentially used for repository metrics or integrations)
-   `ldasenategov_openapi.yaml` (Senate Lobbying Disclosure Act Data)
-   `openFECgov_openapi.yaml` (Federal Election Commission Data)
-   `regulationsgov_openapi.yaml`

These files can be used with tools like Swagger Editor, Postman, or various code generation utilities to understand API endpoints, request/response schemas, and to help generate client code for interacting with these services.

## `endpoints.txt`

-   `endpoints.txt`: This file may contain a list or notes about specific API endpoints that were under consideration or used during development.

## `apps/` Directory

The `apps/` subdirectory contains example applications or components that demonstrate the usage of these APIs.

-   **`federalregister_searchapp.js`**:
    -   **Purpose**: This is a proof-of-concept React component demonstrating how one might build a simple user interface to search Federal Register documents using its API.
    -   **Status**: This is a standalone example and is not actively integrated into the main Python data processing workflows found in the `scripts/` directory of this repository. It serves as a conceptual demonstration.

## Overall Note

The contents of this `data_connections/` directory are mainly for reference, API exploration, and providing context for the project's data sources. They are generally not core operational components of the Python scripts located in the `scripts/` directory, which handle the primary data fetching and processing logic.
