FROM python:3.11-slim

LABEL maintainer="Felipe Fernandes"
LABEL description="Iara AI Code Reviewer"

# Install git, curl, jq (needed for diff generation and GitHub API)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl jq && \
    rm -rf /var/lib/apt/lists/*

# Set working directory first
WORKDIR /app

# Copy the package (zero external dependencies - no pip install needed)
COPY iara/ /app/iara/
COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md
COPY entrypoint.sh /app/entrypoint.sh

# Install Iara with RAG dependencies
# We need to install the package to get the [rag] extra dependencies
RUN pip install --no-cache-dir ".[rag]"

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
