# Use official Python 3.11 image
FROM python:3.11-slim

# Install system dependencies for pylibdmtx
RUN apt-get update && apt-get install -y \
    libdmtx0a \
    libdmtx-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Expose port
EXPOSE 10000

# Start app using gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]