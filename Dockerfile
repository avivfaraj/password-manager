# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install build dependencies and runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tk8.6 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user
RUN useradd -m -u 1000 appuser

# Copy application code
COPY . .

# Change ownership of app directory to the new user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set the entry point
ENTRYPOINT ["python", "run.py"]
