# ==============================================================================
# CodeMind — Multi-Stage Production Dockerfile
# Builds the React frontend and packages the FastAPI Python backend
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

# Install Python dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Pre-download embedding model into the Docker image so cold starts and requests are instant
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend from Stage 1 into /app/frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Set working directory to backend
WORKDIR /app/backend

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV HOST=0.0.0.0

EXPOSE 8000

# Start FastAPI application
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
