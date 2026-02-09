FROM python:3.11-slim

LABEL maintainer="Felipe Fernandes"
LABEL description="Iara AI Code Reviewer"

# Install git, curl, jq (needed for diff generation and GitHub API)
RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl jq && \
    rm -rf /var/lib/apt/lists/*

# Copy the package (zero external dependencies - no pip install needed)
COPY iara/ /app/iara/
COPY entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

WORKDIR /app

ENTRYPOINT ["/app/entrypoint.sh"]
