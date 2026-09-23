FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/apt/lists/*

# Copy dependency definition and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt uvicorn fastapi

# Copy code, database, and logs
COPY ./src ./src
COPY ./chroma_db ./chroma_db
COPY api.py .

EXPOSE 8080

CMD ["python", "api.py"]