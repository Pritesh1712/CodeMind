# ==============================================================================
# CodeMind — Multi-Stage Production Dockerfile (Ultra-Lightweight & Fast)
# Builds the React frontend and packages the low-memory FastAPI Python backend
# ==============================================================================

# ── Stage 1: Build React Frontend ─────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ── Stage 2: Production Python Backend ────────────────────────────────────────
FROM python:3.11-slim

# Install system dependencies (Git is required for cloning repositories)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Install Python dependencies (using FastEmbed for ONNX embeddings without PyTorch)
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# 2. Pre-download FastEmbed ONNX model into Docker image (<35MB RAM, instant boot)
RUN python -c "from fastembed import TextEmbedding; list(TextEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2').embed(['warmup']))"

# 3. Copy backend code
COPY backend/ ./backend/

# 4. Copy built frontend from Stage 1 into /app/frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Set working directory to backend
WORKDIR /app/backend

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV ANONYMIZED_TELEMETRY=False
ENV PORT=8000
ENV HOST=0.0.0.0

EXPOSE 8000

# Start FastAPI application
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
