# ==============================================================================
# EcoBite Backend - Production container image (slim)
# Build : docker build -t ecobite-backend .
# Run   : docker run -p 8000:8000 --env-file .env ecobite-backend
# ==============================================================================

FROM python:3.11-slim

# No bytecode on disk, unbuffered stdout for real-time container logs.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependency layer first - cached when only source code changes.
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Source code layer.
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
