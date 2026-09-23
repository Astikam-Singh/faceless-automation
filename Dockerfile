# Use slim Python base
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment
ENV PYTHONPATH="/app"

# Setup cron job
RUN echo "0 0 * * * cd /app && python -m src.main >> /var/log/cron.log 2>&1" > /etc/cron.d/pipeline-cron
RUN chmod 0644 /etc/cron.d/pipeline-cron
RUN crontab /etc/cron.d/pipeline-cron

# Run cron
CMD ["cron", "-f"]
