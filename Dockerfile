FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add psutil for /status command
RUN pip install --no-cache-dir psutil

# Copy application code
COPY . .

# Create directories
RUN mkdir -p logs generated_images

CMD ["python", "-m", "src.main"]
