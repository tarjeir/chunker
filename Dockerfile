# Use an official Python base image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv (replace pipx)
RUN pip install --no-cache-dir uv

# Copy project files
COPY . /app
COPY deployment/tests/testproject /app/deployment/tests/testproject

# Install your project in editable mode using uv
RUN uv pip install --system -e .

# Default command (change as needed)
CMD ["python", "chunker.py", "--help"]
