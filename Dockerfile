# Use a slim Python base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy necessary files for installation and execution
COPY pyproject.toml ./
COPY README.md ./
COPY LICENSE ./

# Copy the application-specific directories
COPY src/insightsgpt_cli/ ./src/insightsgpt_cli/
COPY scripts/ ./scripts/

# Install the package
# This will read pyproject.toml and install insightsgpt and its dependencies
RUN pip install --no-cache-dir .

# Set the entrypoint for the container
ENTRYPOINT ["insightsgpt"]

# Default command (optional, can be used to show help by default)
# CMD ["--help"]
