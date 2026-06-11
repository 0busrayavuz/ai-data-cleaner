FROM python:3.11-slim

WORKDIR /app

# PDF reports use DejaVu Sans for complete Turkish character support.
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy backend requirements if available, then install
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for volumes
RUN mkdir -p /app/backend/uploads
RUN mkdir -p /app/backend/outputs

# Copy backend code
COPY backend/ /app/backend/

# Expose port
EXPOSE 8000

# Set Python path so `import backend...` works
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Command to run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
