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

# Create a virtual environment
RUN python -m venv /app/venv

# Create start script
RUN echo '#!/bin/bash\n\
source /app/venv/bin/activate\n\
python webserver.py & python main.py\n\
wait' > /app/start.sh && \
    chmod +x /app/start.sh

# Install dependencies in the virtual environment
RUN /app/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY main.py ./
COPY webserver.py ./
COPY telegram_handlers.py ./
COPY config.py ./

# Create a non-root user
RUN useradd -m botuser && \
    chown -R botuser:botuser /app
USER botuser

# Expose the port for the web server
EXPOSE 8080

# Run the start script
CMD ["/app/start.sh"]