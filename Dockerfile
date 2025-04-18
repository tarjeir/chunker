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

# Install pipx and ensure its path is available
RUN pip install --no-cache-dir pipx && pipx ensurepath
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY . /app

# Install your project in editable mode using pipx
RUN pipx install --editable .

# Default command (change as needed)
CMD ["chunker", "--help"]
