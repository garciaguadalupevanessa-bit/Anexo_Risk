FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# ML artifacts
COPY ml/artifacts/ ml/artifacts/

# Env
ENV PYTHONUNBUFFERED=1
ENV ML_MODEL_DIR=ml/artifacts
ENV ML_VERSION_FILE=ml/artifacts/current_version.json

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
