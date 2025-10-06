FROM python:3.13-slim

WORKDIR /app

# Copy all source files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir .

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
CMD ["python", "main.py"]
