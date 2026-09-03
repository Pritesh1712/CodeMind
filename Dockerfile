# ==============================================================================
# CodeMind — Multi-Stage Production Dockerfile (Optimized for Low-RAM Cloud Tiers)
# Builds the React frontend and packages the lightweight FastAPI Python backend
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

# 1. Install lightweight CPU-only PyTorch (reduces RAM from 600MB+ to <120MB, prevents OOM 137)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 2. Install other Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# 3. Pre-download embedding model into the Docker image so cold starts and requests are instant
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# 4. Copy backend code
COPY backend/ ./backend/

# 5. Copy built frontend from Stage 1 into /app/frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Set working directory to backend
WORKDIR /app/backend

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV ANONYMIZED_TELEMETRY=False
ENV PORT=8000
ENV HOST=0.0.0.0

EXPOSE 8000

# Start FastAPI application immediately binding to PORT
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
