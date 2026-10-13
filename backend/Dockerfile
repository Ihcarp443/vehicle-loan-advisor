
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/backend:/app

WORKDIR /app

# Install shared Python dependencies from the repository root.
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend application code.
COPY backend/ /app/backend/

# Copy runtime resources used by the application.
COPY models/ /app/models/
COPY data/documents/ /app/data/documents/
COPY data/processed/ /app/data/processed/
COPY vectorstore/ /app/vectorstore/

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
