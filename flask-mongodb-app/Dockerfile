# Stage 1: Builder
FROM python:3.8-slim as builder

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt


# Stage 2: Runtime
FROM python:3.8-slim

WORKDIR /app

# Copy only the necessary files from the builder stage
COPY --from=builder /root/.local /root/.local

# Copy the application code
COPY app.py .

# Set environment variables
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

# Expose port 5000
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Run the Flask application
CMD ["python", "app.py"]
