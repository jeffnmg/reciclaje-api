FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# ⬇️ NUEVO: Pre-descargar el modelo DURANTE EL BUILD
RUN python -c "from transformers import pipeline; pipeline('image-classification', model='microsoft/resnet-50', device=-1)"

# Copiar código
COPY app.py .

# Cloud Run usa variable PORT
ENV PORT=8080
EXPOSE 8080

# Iniciar aplicación
CMD uvicorn app:app --host 0.0.0.0 --port $PORT --workers 1
