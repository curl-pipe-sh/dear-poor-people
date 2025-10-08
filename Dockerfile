FROM python:3.14-slim

# Build argument for version information
ARG GIT_COMMIT_SHA=unknown
ENV POOR_TOOLS_VERSION=${GIT_COMMIT_SHA}

WORKDIR /app

# Copy all source files first
COPY . .

# Install the package using pip with editable mode to ensure data files are included
# hadolint ignore=DL3013
RUN pip install --no-cache-dir -e .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Environment variables
ENV BIND_HOST=0.0.0.0
ENV BIND_PORT=7667

# Expose port
EXPOSE 7667

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://localhost:{os.getenv(\"BIND_PORT\", \"7667\")}/health')"

# Run the application
CMD ["poor-installer-web"]
