# Use official Python 3.11 slim image as base
# Slim variant reduces image size by excluding unnecessary packages
FROM python:3.11-slim

# Set metadata labels for image documentation
LABEL maintainer="LibTracker DevOps"
LABEL description="Production-ready container for LibTracker application"
LABEL version="1.0"

# Set working directory for all subsequent commands
WORKDIR /app

# Set environment variables
# PYTHONUNBUFFERED: Forces Python to run in unbuffered mode (logs stream directly)
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files (reduces image size)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies (if needed for psycopg2, cryptography, etc.)
# This is done before copying requirements to leverage layer caching
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt FIRST to leverage Docker layer caching
# If requirements.txt hasn't changed, this layer will be cached
COPY backend/requirements.txt .

# Install Python dependencies
# Using --no-cache-dir reduces image size by not storing pip cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
# Placed after requirements installation to maximize cache efficiency
COPY backend/ ./backend/

# Copy frontend static files
# These are served by the Flask app (assuming static file serving is configured)
COPY frontend/ ./frontend/

# Expose port 5000 for local development
# Note: Render will dynamically assign a port via the PORT environment variable
# Ensure your app listens on $PORT for Render compatibility
EXPOSE 5000

# Default command to start the application
CMD ["python", "backend/app.py"]
