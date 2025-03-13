# Use Python 3.12 as the base image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . .

# Make the launch script executable
COPY start.sh .
RUN chmod +x start.sh

# Create a non-root user and switch to it
RUN useradd -m botuser && \
    chown -R botuser:botuser /app
USER botuser

# Expose the port for the web server
EXPOSE 8080

# Run the launch script
CMD ["./start.sh"]