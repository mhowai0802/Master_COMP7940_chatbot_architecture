# Use Python 3.12 as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /app/venv

# Set environment to use the virtual environment
ENV PATH="/app/venv/bin:$PATH"

# Copy requirements file first (for better caching)
COPY requirements.txt .

# Install dependencies in the virtual environment
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all files at once
COPY . .

# Create a non-root user
RUN useradd -m botuser && \
    chown -R botuser:botuser /app
USER botuser

# Expose the port for the web server
EXPOSE 8080

# Run both the web server and the bot
CMD python webserver.py & python main.py