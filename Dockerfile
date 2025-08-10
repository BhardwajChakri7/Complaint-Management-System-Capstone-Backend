# Use an official lightweight Python image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the entire project
COPY . .

# Expose port
EXPOSE 6969

# Start the app with Gunicorn (optimized for stability and performance)
CMD ["gunicorn", "-b", "0.0.0.0:6969", "--workers", "1", "--timeout", "180", "--keep-alive", "5", "--max-requests", "200", "--max-requests-jitter", "20", "--preload", "server:app"]