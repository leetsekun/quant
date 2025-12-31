# Use official Python runtime as base image
FROM python:3.14-slim

# Set working directory in container
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ src/
COPY templates/ templates/
COPY spx500.csv .

# Create data directory
RUN mkdir -p data

# Expose port 5000
EXPOSE 5000

# Set environment variables
ENV PYTHONAPP=src.app:app
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Run the application using gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "src.app:app"]
