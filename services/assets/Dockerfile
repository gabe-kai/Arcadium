FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create storage directory
RUN mkdir -p /storage

# Expose port
EXPOSE 8004

# Run the application
CMD ["flask", "run", "--host", "0.0.0.0", "--port", "8004"]
