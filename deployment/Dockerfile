FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose the API port
EXPOSE 8000

# Default: run the REST API server
CMD ["python", "main.py", "--mode", "api", "--host", "0.0.0.0", "--port", "8000"]
