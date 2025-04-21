FROM python:3.9-slim

# Install required system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libreoffice-common \
    libreoffice-writer \
    img2pdf \
    file \
    poppler-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set up Python environment
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

EXPOSE 5000
CMD ["python", "app.py"]
